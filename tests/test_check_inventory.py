"""The required-check list has one owner (AGENTS.md) and CI executes it."""

from __future__ import annotations

import ast
import json
import re
import shlex
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
AGENTS = PROJECT_ROOT / "AGENTS.md"
CI = PROJECT_ROOT / ".github" / "workflows" / "ci.yml"
SECONDARY_DOCS = ("docs/development.md", "docs/testing.md")
ROOT_REFERENCES = {
    "README.md": {
        "Contract": ("AGENTS.md#execution-contract",),
        "Source of truth": ("AGENTS.md#source-of-truth",),
        "Development checks": ("AGENTS.md#required-checks",),
    },
    "SPEC.md": {
        "Execution modes": (
            "AGENTS.md#execution-contract",
            "AGENTS.md#source-of-truth",
        ),
        "Validation": ("AGENTS.md#execution-contract", "AGENTS.md#required-checks"),
    },
    "HANDOFF.md": {
        "Canonical ownership": (
            "AGENTS.md#source-of-truth",
            "AGENTS.md#execution-contract",
        ),
        "Reproduction commands": ("AGENTS.md#required-checks",),
    },
}

#: AGENTS.md commands CI does not execute verbatim. Empty on purpose: a
#: required check that hosted CI never runs is a drifted contract. Add an entry
#: only with the reason a command is local-only.
LOCAL_ONLY: dict[str, str] = {}

#: Commands CI runs that the "Required checks" block deliberately omits.
#: Normalised form -> why. Generation (non-``--check``) steps materialise
#: inputs for later gates; the rest are hosted-only orchestration whose
#: inputs (JUnit files, per-OS interpreters) do not exist on a workstation.
HOSTED_ONLY = {
    "python scripts/build_formalism_atlas.py": "render-deps: generates the atlas",
    "python scripts/build_formal_kernel_dashboard.py": "render-deps: generates it",
    "fep-lean --project-root . methods export --output-root "
    "docs/mathematical-positioning": "render-deps: generates the methods export",
    "python scripts/build_render_fonts.py": "render: generates the font record",
    "python scripts/render_publication.py": "render: the publication render itself",
    "pytest tests/test_distribution.py -q -s --no-cov": "distribution matrix cell",
    "pytest specs/openai-math-methods/test_distribution_methods.py -q -s --no-cov": (
        "distribution matrix cell"
    ),
    "pytest tests/test_browser_capture.py::"
    "test_live_chrome_blocks_and_records_a_delayed_outbound_request "
    "tests/test_browser_capture.py::"
    "test_live_chrome_replay_terminates_every_profile_writer -q -n 0 --cov=src "
    "--cov-append --cov-report=xml --cov-fail-under=89 "
    "--junitxml=output/live-chrome-acceptance.xml -W always --color=no": (
        "isolated live Chrome component with measured warning visibility"
    ),
    "python specs/publication-browser-acceptance/validate_acceptance.py "
    "--collection output/python-acceptance-collection.json "
    "--parallel-junit output/python-acceptance.xml "
    "--chrome-junit output/live-chrome-acceptance.xml --coverage coverage.xml "
    "--output output/python-acceptance-summary.json": "needs the hosted JUnit files",
}

_TRACKED_PREFIXES = ("uv run", "lake ", "git diff", "uv lock", "uv pip")


def _shell_tokens(command: str) -> list[str]:
    """Lex comments/operators while retaining quotes for later normalisation.

    This inventory supports quoted arguments, ``&&`` chains, a parenthesised
    ``cd`` prefix, pipelines and ``2>&1``; it does not evaluate shell syntax.
    Non-POSIX lexing keeps a quoted ``'&&'`` distinct from the operator.
    """
    lexer = shlex.shlex(command, posix=False, punctuation_chars="&|")
    lexer.whitespace_split = True
    return list(lexer)


def normalise(command: str) -> str:
    """Drop runner prefixes, redirections and unquoted shell comments."""
    raw = _shell_tokens(command)
    for index, token in enumerate(raw):
        if token in {"|", "||"} or raw[index : index + 3] == ["2>", "&", "1"]:
            raw = raw[:index]
            break
    # Quotes must survive the split stage: stripping them earlier would turn a
    # literal hash or ampersand into shell syntax in this second lexical pass.
    tokens = shlex.split(" ".join(raw).strip().strip("()").strip(), comments=False)
    if tokens[:2] == ["uv", "run"]:
        tokens = tokens[2:]
        if tokens and tokens[0] == "--locked":
            tokens = tokens[1:]
    if tokens[:3] == ["python", "-m", "pytest"]:
        tokens = ["pytest", *tokens[3:]]
    return " ".join(tokens)


def split_commands(script: str) -> list[str]:
    """Split a shell snippet into commands, joining ``\\`` continuations.

    Comments, heredoc bodies and control flow are skipped; ``a && b`` is two
    commands and ``(cd d && c)`` is ``c``.
    """
    commands: list[str] = []
    heredoc_end: str | None = None
    joined = re.sub(r"\\\n\s*", " ", script)
    for raw in joined.splitlines():
        line = raw.strip()
        if heredoc_end is not None:
            if line == heredoc_end:
                heredoc_end = None
            continue
        if not line or line.startswith("#"):
            continue
        heredoc = re.search(r"<<-?\s*'?(\w+)'?\s*$", line)
        if heredoc:
            heredoc_end = heredoc.group(1)
            continue  # inline python is not a repository command
        pending: list[str] = []
        for token in [*_shell_tokens(line), "&&"]:
            if token != "&&":
                pending.append(token)
                continue
            part = " ".join(pending).strip().strip("()").strip()
            pending = []
            if part.startswith("cd "):
                continue
            if part.startswith(_TRACKED_PREFIXES):
                commands.append(part)
    return commands


def agents_commands() -> list[str]:
    text = AGENTS.read_text(encoding="utf-8")
    section = text.split("## Required checks", 1)[1].split("\n## ", 1)[0]
    blocks = re.findall(r"```bash\n(.*?)```", section, flags=re.DOTALL)
    assert blocks, "AGENTS.md 'Required checks' has no bash block"
    return [normalise(c) for block in blocks for c in split_commands(block)]


def ci_commands() -> list[str]:
    workflow = yaml.safe_load(CI.read_text(encoding="utf-8"))
    commands: list[str] = []
    for job in workflow["jobs"].values():
        for step in job.get("steps", []):
            if isinstance(step.get("run"), str):
                commands += [normalise(c) for c in split_commands(step["run"])]
    return commands


def _covers(ci: str, required: str) -> bool:
    """CI runs ``required`` verbatim; pytest may add options (xdist, junit)."""
    if ci == required:
        return True
    ci_tokens, required_tokens = ci.split(), required.split()
    return (
        required_tokens[0] == ci_tokens[0] == "pytest"
        and required_tokens[1] == ci_tokens[1]
        and all(token in ci_tokens for token in required_tokens)
    )


def _assert_unique_commands(commands: list[str]) -> None:
    duplicates = sorted(c for c, count in Counter(commands).items() if count > 1)
    assert not duplicates, f"AGENTS.md repeats required checks: {duplicates}"


def _assert_root_references(relative: str, text: str, required: set[str]) -> None:
    """Keep designated reference sections as links, leaving usage examples alone.

    Structured definitions (lists, tables, subheadings, fenced examples) belong
    to AGENTS.md. This is a scoped ownership guard, not a natural-language audit
    of historical observations or every command example in the repository.
    """
    for heading, owners in ROOT_REFERENCES[relative].items():
        marker = f"## {heading}\n"
        assert marker in text, f"{relative} is missing reference section {heading!r}"
        section = text.split(marker, 1)[1].split("\n## ", 1)[0]
        for owner in owners:
            assert re.search(rf"\]\({re.escape(owner)}\)", section), (
                f"{relative} {heading!r} must link to {owner}"
            )
        for block in re.findall(r"```bash\n(.*?)```", section, flags=re.DOTALL):
            shared = [normalise(c) for c in split_commands(block)]
            shared = [c for c in shared if c in required]
            assert not shared, (
                f"{relative} {heading!r} copies required checks: {shared}"
            )
        assert not re.search(r"(?m)^\s*(?:[-*+] |\||#{3,} |```|~~~)", section), (
            f"{relative} {heading!r} duplicates a structured definition; link to AGENTS.md"
        )


def test_normaliser_handles_continuations_chains_and_prefixes() -> None:
    script = (
        "uv lock --check && uv pip check\n"
        "# comment\n"
        "uv run --locked python -m pytest a.py \\\n  -q --no-cov\n"
        "(cd lean && lake build FepSketches) 2>&1 | tee log\n"
        "uv run python - <<'PY'\nuv run python hidden.py\nPY\n"
    )
    assert [normalise(c) for c in split_commands(script)] == [
        "uv lock --check",
        "uv pip check",
        "pytest a.py -q --no-cov",
        "lake build FepSketches",
    ]


@pytest.mark.parametrize(
    ("script", "expected"),
    [
        ("uv run harmless # note && uv run mypy src", ["harmless"]),
        (
            "uv run python -c 'print(\"# literal\")' && uv run mypy src",
            ['python -c print("# literal")', "mypy src"],
        ),
        (
            "uv run python -c 'print(\"&& literal\")' && uv run mypy src",
            ['python -c print("&& literal")', "mypy src"],
        ),
        (
            "uv run python -c \"print('# && literal')\" # note && uv run mypy src",
            ["python -c print('# && literal')"],
        ),
    ],
)
def test_command_inventory_preserves_quoted_literals_and_ignores_comment_chains(
    script: str, expected: list[str]
) -> None:
    assert [normalise(command) for command in split_commands(script)] == expected


def test_required_check_inventory_has_no_duplicate_commands() -> None:
    _assert_unique_commands(agents_commands())


def test_duplicate_canonical_gate_is_rejected() -> None:
    required = agents_commands()
    with pytest.raises(AssertionError, match="repeats required checks"):
        _assert_unique_commands([*required, required[0]])


def test_every_required_check_is_executed_by_ci_or_explicitly_local() -> None:
    required, ci = agents_commands(), ci_commands()
    assert len(required) > 25, "AGENTS.md required-check parse looks truncated"
    missing = [
        command
        for command in required
        if command not in LOCAL_ONLY and not any(_covers(c, command) for c in ci)
    ]
    assert not missing, f"AGENTS.md checks that ci.yml never runs: {missing}"


def test_every_ci_gate_is_listed_in_agents_or_explicitly_hosted_only() -> None:
    required = agents_commands()
    unlisted = sorted(
        {
            command
            for command in ci_commands()
            if command not in HOSTED_ONLY
            and not any(_covers(command, r) for r in required)
        }
    )
    assert not unlisted, (
        f"ci.yml gates missing from AGENTS.md 'Required checks': {unlisted}"
    )


def test_allow_lists_carry_no_dead_entries() -> None:
    ci = set(ci_commands())
    stale = [c for c in HOSTED_ONLY if c not in ci]
    assert not stale, f"HOSTED_ONLY entries CI no longer runs: {stale}"
    agents = set(agents_commands())
    assert not [c for c in LOCAL_ONLY if c not in agents]


def test_package_line_floor_gate_consumes_complete_split_coverage() -> None:
    workflow = yaml.safe_load(CI.read_text(encoding="utf-8"))
    steps = workflow["jobs"]["python"]["steps"]
    parallel = next(
        i for i, step in enumerate(steps) if step.get("id") == "python_remainder"
    )
    chrome = next(i for i, step in enumerate(steps) if step.get("id") == "live_chrome")
    floor = next(
        i
        for i, step in enumerate(steps)
        if step.get("name") == "Require measured package line coverage floors"
    )
    membership = next(
        i
        for i, step in enumerate(steps)
        if step.get("name")
        == "Require complete Python membership and all live Chrome controls"
    )
    assert parallel < chrome < floor < membership
    command = "python docs/check_coverage_floors.py --coverage coverage.xml"
    assert command in agents_commands() and command in ci_commands()
    assert "pipefail" in steps[floor]["run"]
    assert "output/coverage-floor-summary.json" in steps[floor]["run"]
    assert "steps.python_remainder.outcome != 'skipped'" in steps[floor]["if"]
    assert "steps.live_chrome.outcome != 'skipped'" in steps[floor]["if"]
    for index in (parallel, chrome):
        assert "--cov=src" in steps[index]["run"]
        assert "--cov-report=xml" in steps[index]["run"]
        assert "--cov-fail-under=89" in steps[index]["run"]
        assert "--cov-branch" not in steps[index]["run"]
    assert "--cov-append" not in steps[parallel]["run"]
    assert "--cov-append" in steps[chrome]["run"]
    assert steps[parallel]["env"]["FEP_LEAN_COVERAGE_FLOOR_EVIDENCE"] == "1"
    retained = next(
        step
        for step in steps
        if step.get("name") == "Retain actual Python acceptance results and coverage"
    )
    assert "output/coverage-floor-summary.json" in retained["with"]["path"].splitlines()
    for mode in ("one", "both"):
        assert (
            f"output/coverage-floor-control-{mode}.log"
            in retained["with"]["path"].splitlines()
        )


@pytest.mark.parametrize("relative", SECONDARY_DOCS)
def test_secondary_docs_link_to_the_owner_instead_of_copying_the_list(
    relative: str,
) -> None:
    text = (PROJECT_ROOT / relative).read_text(encoding="utf-8")
    assert "AGENTS.md#required-checks" in text
    required = set(agents_commands())
    for block in re.findall(r"```bash\n(.*?)```", text, flags=re.DOTALL):
        shared = [c for c in split_commands(block) if normalise(c) in required]
        assert len(shared) < 4, f"{relative} re-lists required checks: {shared}"


def test_readme_points_at_the_owner_and_no_dangling_heading() -> None:
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    assert "AGENTS.md#required-checks" in readme
    assert "Required release gates" not in readme


@pytest.mark.parametrize("relative", ROOT_REFERENCES)
def test_root_reference_sections_use_canonical_owners(relative: str) -> None:
    text = (PROJECT_ROOT / relative).read_text(encoding="utf-8")
    _assert_root_references(relative, text, set(agents_commands()))


@pytest.mark.parametrize(
    ("relative", "heading", "addition", "message"),
    [
        (
            "README.md",
            "Development checks",
            "```bash\nuv run mypy src scripts docs # copied gate\n```\n",
            "copies required checks",
        ),
        (
            "HANDOFF.md",
            "Canonical ownership",
            "| Static topic metadata | `config/catalogue_metadata.yaml` | rows |\n",
            "duplicates a structured definition",
        ),
        (
            "SPEC.md",
            "Execution modes",
            "### `catalogue`\n\nOffline mode writes a report.\n",
            "duplicates a structured definition",
        ),
    ],
)
def test_root_reference_guard_rejects_restored_definitions(
    relative: str, heading: str, addition: str, message: str
) -> None:
    text = (PROJECT_ROOT / relative).read_text(encoding="utf-8")
    marker = f"## {heading}\n"
    text = text.replace(marker, f"{marker}\n{addition}", 1)
    with pytest.raises(AssertionError, match=message):
        _assert_root_references(relative, text, set(agents_commands()))


@pytest.mark.parametrize("relative", ROOT_REFERENCES)
def test_root_reference_guard_rejects_missing_owner_links(relative: str) -> None:
    text = (PROJECT_ROOT / relative).read_text(encoding="utf-8")
    owner = next(iter(ROOT_REFERENCES[relative].values()))[0]
    text = text.replace(f"]({owner})", "](AGENTS.md)")
    with pytest.raises(AssertionError, match="must link to"):
        _assert_root_references(relative, text, set(agents_commands()))


def test_setup_examples_outside_reference_sections_remain_allowed() -> None:
    text = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    assert "uv sync --locked --extra dev\nuv run fep-lean catalogue" in text
    _assert_root_references("README.md", text, set(agents_commands()))


def test_repository_lint_rejects_an_active_spec_unused_import(
    tmp_path: Path,
) -> None:
    """Exercise the actual root scan and exclusions without editing real owners."""
    (tmp_path / "pyproject.toml").write_bytes(
        (PROJECT_ROOT / "pyproject.toml").read_bytes()
    )
    protected = [
        tmp_path / "specs/done/prior/check.py",
        tmp_path / "specs/current/evidence/capture/check.py",
        tmp_path / "specs/current/gnn_output_run1/check.py",
        tmp_path / "specs/current/gnn-input/check.py",
        tmp_path / "specs/current/fixtures/check.py",
    ]
    for path in protected:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("import os\n", encoding="utf-8")
    active = tmp_path / "specs/capture-roster-guard/check.py"
    active.parent.mkdir(parents=True)
    active.write_text("value = 1\n", encoding="utf-8")
    before = {path: path.read_bytes() for path in protected}
    command = [
        sys.executable,
        "-I",
        "-B",
        "-m",
        "ruff",
        "check",
        ".",
        "--no-cache",
        "--output-format",
        "json",
    ]
    valid = subprocess.run(
        command, cwd=tmp_path, capture_output=True, text=True, timeout=30, check=False
    )
    assert valid.returncode == 0, valid.stdout + valid.stderr
    assert json.loads(valid.stdout) == []

    active.write_text("import os\n", encoding="utf-8")
    invalid = subprocess.run(
        command, cwd=tmp_path, capture_output=True, text=True, timeout=30, check=False
    )
    assert invalid.returncode == 1, invalid.stdout + invalid.stderr
    findings = json.loads(invalid.stdout)
    assert len(findings) == 1
    assert findings[0]["code"] == "F401"
    assert Path(findings[0]["filename"]) == active
    assert {path: path.read_bytes() for path in protected} == before


# Existing debt only. Ruff's per-file escape hatch is narrowed here to these
# exact functions and ceilings; additions, renamed exceptions and growth fail.
_STATEMENT_DEBT = {
    ("specs/h3-reference-study/bundle_study.py", "reproduce"): 141,
    ("specs/h3-reference-study/export_native.py", "export_native"): 114,
    ("src/fep_lean/catalogue/latex.py", "_convert_lean_expr"): 114,
    ("src/fep_lean/output/evidence.py", "validate_native_lean_receipt"): 131,
    (
        "src/fep_lean/output/release_bundle/_acceptance.py",
        "_pytest_receipt_errors",
    ): 111,
    (
        "src/fep_lean/output/release_bundle/_identity.py",
        "_license_metadata_errors",
    ): 137,
    ("src/fep_lean/output/reporter.py", "_validate_full_completion"): 146,
    ("src/fep_lean/verification/_subprocess.py", "_Broker.run"): 168,
    (
        "src/fep_lean/verification/formalism_audit.py",
        "validate_formalism_audit_receipt",
    ): 118,
    ("tests/test_distribution.py", "_exercise_render_artifact_staging"): 247,
    (
        "tests/test_distribution_supplemental.py",
        "_exercise_render_artifact_staging",
    ): 247,
    (
        "tests/test_h3_reference_study.py",
        "test_export_attempt_retains_real_child_failure_and_rejects_source_race",
    ): 166,
    (
        "tests/test_h3_study_bundle.py",
        "test_reproduction_parent_snapshots_and_final_seal_fail_closed",
    ): 114,
}
_FUNCTION_SPAN_OWNERS = (
    "catalogue/coverage.py",
    "gauss/runner.py",
    "output/formal_kernel_dashboard.py",
    "output/release_bundle/_browser.py",
    "output/release_bundle/_core.py",
    "output/release_bundle/_validate.py",
    "verification/numerical_witnesses.py",
)


def test_refactored_function_spans_remain_bounded() -> None:
    violations = []
    for owner in _FUNCTION_SPAN_OWNERS:
        tree = ast.parse((PROJECT_ROOT / "src/fep_lean" / owner).read_text())
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                assert node.end_lineno is not None
                span = node.end_lineno - node.lineno + 1
                if span > 200:
                    violations.append((owner, node.name, span))
    assert not violations, violations


def _qualified_function_names(tree: ast.AST) -> dict[int, str]:
    names: dict[int, str] = {}

    def visit(node: ast.AST, parents: tuple[str, ...]) -> None:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            parents = (*parents, node.name)
            if not isinstance(node, ast.ClassDef):
                names[node.lineno] = ".".join(parents)
        for child in ast.iter_child_nodes(node):
            visit(child, parents)

    visit(tree, ())
    return names


def test_statement_debt_names_distinguish_unrelated_methods() -> None:
    tree = ast.parse(
        "def retained(): pass\nclass Unrelated:\n    def retained(self): pass\n"
    )
    assert _qualified_function_names(tree) == {
        1: "retained",
        3: "Unrelated.retained",
    }


def test_statement_exceptions_cannot_expand() -> None:
    config = (PROJECT_ROOT / "pyproject.toml").read_text()
    exceptions = re.findall(r'^"([^"\n]+)" = \["PLR0915"\]$', config, re.MULTILINE)
    assert set(exceptions) == {owner for owner, _name in _STATEMENT_DEBT}
    assert config.count('"PLR0915"') == len(exceptions) + 1
    assert "max-statements = 100" in config
    # Isolated lint deliberately bypasses the configured per-file ignores.
    command = [
        sys.executable,
        "-I",
        "-B",
        "-m",
        "ruff",
        "check",
        "--isolated",
        "--select",
        "PLR0915",
        "--config",
        "lint.pylint.max-statements=100",
        "--output-format",
        "json",
        *sorted({owner for owner, _name in _STATEMENT_DEBT}),
    ]
    result = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode in (0, 1), result.stdout + result.stderr
    for finding in json.loads(result.stdout):
        path = Path(finding["filename"])
        owner = path.relative_to(PROJECT_ROOT).as_posix()
        names = _qualified_function_names(ast.parse(path.read_text()))
        name = names.get(finding["location"]["row"])
        assert name is not None, finding
        key = (owner, name)
        count = re.search(r"\((\d+) >", finding["message"])
        assert count is not None, finding
        assert key in _STATEMENT_DEBT, key
        assert int(count[1]) <= _STATEMENT_DEBT[key], finding


def test_native_single_producer_and_explicit_dual_shadow_workflow_contract():
    workflow = yaml.safe_load(CI.read_text())
    _assert_render_dependencies_barrier_contract(workflow)
    steps = workflow["jobs"]["lean"]["steps"]
    serial = next(
        s for s in steps if s.get("name") == "Run the serial_lean acceptance lane"
    )
    assert serial["env"]["FEP_LEAN_CI_NATIVE_RECEIPT"] == "1"
    assert (
        "test_all_catalogue_bodies_compile" not in serial["run"]
    )  # complete serial lane, no narrow selection
    native = next(
        s
        for s in steps
        if s.get("name")
        == "Validate the strict serial producer and optionally compare the CLI"
    )
    body = native["run"]
    assert body.index("validate_native_catalogue_producer(") < body.index(
        'if [ "$FEP_LEAN_NATIVE_SHADOW" = "1" ]; then'
    )
    conditional = body.split('if [ "$FEP_LEAN_NATIVE_SHADOW" = "1" ]; then', 1)[
        1
    ].split("\nfi", 1)[0]
    assert "uv run fep-lean verify" in conditional
    assert body.count("uv run fep-lean verify") == 1
    uploads = [
        s for s in steps if s.get("uses", "").startswith("actions/upload-artifact@")
    ]
    standard = next(s for s in uploads if s["with"]["name"] == "native-formal-evidence")
    assert "output/native-catalogue-producer.intent.json" in standard["with"]["path"]
    assert "output/native-catalogue-producer.json" in standard["with"]["path"]
    # Local default still reaches its direct LeanVerifier branch unless explicit CI flag is present.
    source = (PROJECT_ROOT / "tests/test_catalogue_bodies_compile.py").read_text()
    assert "if CI_NATIVE_RECEIPT_ENV in os.environ:" in source
    assert "verifier.verify_batch(items)" in source


def _full_profile_distribution_cells(workflow):
    """Closed full matrix for automatic PR/default push and manual shadow profiles."""
    matrix = workflow["jobs"]["distribution"]["strategy"]["matrix"]
    assert set(matrix) == {"os", "python"}
    assert matrix["os"] == ["ubuntu-latest", "macos-latest", "windows-latest"]
    assert matrix["python"] == ["3.10", "3.11", "3.12", "3.13", "3.14"]
    cells = [
        (os_name, version) for os_name in matrix["os"] for version in matrix["python"]
    ]
    assert len(cells) == len(set(cells)) == 15
    return cells


def test_full_pr15_distribution_matrix_is_event_independent():
    workflow = yaml.safe_load(CI.read_text())
    assert len(_full_profile_distribution_cells(workflow)) == 15
    # A literal matrix applies equally to automatic PR, push and explicit manual shadow.
    assert isinstance(
        workflow["jobs"]["distribution"]["strategy"]["matrix"]["python"], list
    )


@pytest.mark.parametrize(
    "versions",
    [
        ["3.10", "3.12", "3.14"],
        ["3.10", "3.11", "3.12", "3.13"],
        ["3.10", "3.11", "3.12", "3.13", "3.13"],
        ["3.10", "3.11", "3.12", "3.13", "3.14", "3.15"],
    ],
)
def test_full_pr15_matrix_refuses_reduced_missing_duplicate_extra_versions(versions):
    workflow = yaml.safe_load(CI.read_text())
    workflow["jobs"]["distribution"]["strategy"]["matrix"]["python"] = versions
    with pytest.raises(AssertionError):
        _full_profile_distribution_cells(workflow)


@pytest.mark.parametrize(
    "key,value", [("os", ["ubuntu-latest", "macos-latest"]), ("exclude", [])]
)
def test_full_pr15_matrix_refuses_platform_loss_or_filter(key, value):
    workflow = yaml.safe_load(CI.read_text())
    workflow["jobs"]["distribution"]["strategy"]["matrix"][key] = value
    with pytest.raises(AssertionError):
        _full_profile_distribution_cells(workflow)


def test_producer_context_observes_original_paths_after_success_before_optional_cli():
    steps = yaml.safe_load(CI.read_text())["jobs"]["lean"]["steps"]
    body = next(
        s["run"]
        for s in steps
        if s.get("name")
        == "Validate the strict serial producer and optionally compare the CLI"
    )
    assert body.index("validate_native_catalogue_producer(") < body.index(
        'print("FEP_NATIVE_PRODUCER_CONTEXT '
    )
    assert body.index('print("FEP_NATIVE_PRODUCER_CONTEXT ') < body.index(
        'if [ "$FEP_LEAN_NATIVE_SHADOW" = "1" ]; then'
    )
    for token in [
        "Path.cwd().resolve(strict=True)",
        '"git_head"',
        '"receipt"',
        '"GITHUB_REPOSITORY"',
        '"GITHUB_RUN_ID"',
        '"GITHUB_RUN_ATTEMPT"',
        '"GITHUB_SHA"',
    ]:
        assert token in body


def _assert_native_shadow_selection_is_explicit(workflow):
    expected = "${{ github.event_name == 'workflow_dispatch' && inputs.native_producer_shadow && '1' || '0' }}"
    steps = workflow["jobs"]["lean"]["steps"]
    for name in [
        "Run the serial_lean acceptance lane",
        "Validate the strict serial producer and optionally compare the CLI",
    ]:
        step = next(s for s in steps if s.get("name") == name)
        assert step["env"]["FEP_LEAN_NATIVE_SHADOW"] == expected
    events = workflow.get("on", workflow.get(True))
    selection = events["workflow_dispatch"]["inputs"]["native_producer_shadow"]
    assert selection["type"] == "boolean"
    assert selection["default"] is False
    assert selection["required"] is False


def test_native_shadow_selection_requires_manual_explicit_boolean():
    _assert_native_shadow_selection_is_explicit(yaml.safe_load(CI.read_text()))


@pytest.mark.parametrize(
    "name",
    [
        "Run the serial_lean acceptance lane",
        "Validate the strict serial producer and optionally compare the CLI",
    ],
)
@pytest.mark.parametrize(
    "value",
    [
        "1",
        "0",
        "${{ inputs.native_producer_shadow && '1' || '0' }}",
        "${{ github.event_name == 'pull_request' && '1' || '0' }}",
    ],
)
def test_native_shadow_selection_refuses_forced_or_wrong_event_mutants(name, value):
    workflow = yaml.safe_load(CI.read_text())
    step = next(s for s in workflow["jobs"]["lean"]["steps"] if s.get("name") == name)
    step["env"]["FEP_LEAN_NATIVE_SHADOW"] = value
    with pytest.raises(AssertionError):
        _assert_native_shadow_selection_is_explicit(workflow)


@pytest.mark.parametrize(
    "field,value",
    [("default", True), ("default", "false"), ("required", True), ("type", "string")],
)
def test_native_shadow_selection_refuses_nonboolean_or_default_enabled_input(
    field, value
):
    workflow = yaml.safe_load(CI.read_text())
    events = workflow.get("on", workflow.get(True))
    events["workflow_dispatch"]["inputs"]["native_producer_shadow"][field] = value
    with pytest.raises(AssertionError):
        _assert_native_shadow_selection_is_explicit(workflow)


def _assert_render_dependencies_barrier_contract(workflow):
    jobs = workflow["jobs"]
    lean = jobs["lean"]
    assert lean["needs"] == "changes"
    assert lean["permissions"] == {"contents": "read", "actions": "read"}
    assert (
        lean["if"]
        == "needs.changes.outputs.docs_only != 'true' && (github.event_name != 'workflow_dispatch' || inputs.run_lean)"
    )
    assert jobs["render"]["needs"] == ["lean", "render-deps"]
    steps = lean["steps"]
    by_name = {
        row.get("name"): index for index, row in enumerate(steps) if row.get("name")
    }
    barrier_index = by_name["Require current-attempt publication figure producer"]
    barrier = steps[barrier_index]
    assert barrier["id"] == "render-figures-barrier"
    assert barrier["timeout-minutes"] == 22
    assert barrier["env"] == {"GH_TOKEN": "${{ github.token }}"}
    assert barrier["run"] == (
        "python specs/publication-browser-acceptance/wait_render_dependencies.py"
    )
    static_runs = [step.get("run", "") for step in workflow["jobs"]["static"]["steps"]]
    assert (
        "uv run mypy src scripts docs "
        "specs/publication-browser-acceptance/wait_render_dependencies.py"
    ) in static_runs
    required = AGENTS.read_text(encoding="utf-8")
    assert "uv run ruff check specs/publication-browser-acceptance" in required
    assert "uv run ruff format --check specs/publication-browser-acceptance" in required
    assert (
        "uv run mypy src scripts docs "
        "specs/publication-browser-acceptance/wait_render_dependencies.py"
    ) in required
    download_index = by_name[
        "Download the publication figure assets the render-deps job produced"
    ]
    assert (
        by_name["Compile orphaned formal modules"]
        < barrier_index
        < download_index
        < by_name["Run the serial_lean acceptance lane"]
    )
    assert steps[download_index]["with"] == {
        "artifact-ids": "${{ steps.render-figures-barrier.outputs.artifact_id }}",
        "path": ".",
    }
    expected_name = "render-figures-${{ github.run_id }}-${{ github.run_attempt }}"
    producer = next(
        row
        for row in jobs["render-deps"]["steps"]
        if row.get("name") == "Upload the publication figure assets"
    )
    consumer = next(
        row
        for row in jobs["render"]["steps"]
        if row.get("name")
        == "Download the publication figure assets the render-deps job produced"
    )
    assert producer["with"]["name"] == consumer["with"]["name"] == expected_name


@pytest.mark.parametrize(
    "mutant",
    [
        "legacy_upload",
        "legacy_render_download",
        "lean_by_name",
        "wrong_barrier_command",
        "missing_actions_read",
        "restore_serial_needs",
        "bypass_skip_condition",
        "barrier_after_serial",
    ],
)
def test_render_dependency_contract_refuses_gate_or_identity_drift(mutant):
    workflow = yaml.safe_load(CI.read_text())
    jobs = workflow["jobs"]
    lean = jobs["lean"]
    steps = lean["steps"]
    barrier = next(row for row in steps if row.get("id") == "render-figures-barrier")
    download = next(
        row
        for row in steps
        if row.get("name")
        == "Download the publication figure assets the render-deps job produced"
    )
    if mutant == "legacy_upload":
        next(
            row
            for row in jobs["render-deps"]["steps"]
            if row.get("name") == "Upload the publication figure assets"
        )["with"]["name"] = "render-figures"
    if mutant == "legacy_render_download":
        next(
            row
            for row in jobs["render"]["steps"]
            if row.get("name")
            == "Download the publication figure assets the render-deps job produced"
        )["with"]["name"] = "render-figures"
    if mutant == "lean_by_name":
        download["with"] = {"name": "render-figures", "path": "."}
    if mutant == "wrong_barrier_command":
        barrier["run"] = "true"
    if mutant == "missing_actions_read":
        del lean["permissions"]["actions"]
    if mutant == "restore_serial_needs":
        lean["needs"] = ["changes", "render-deps"]
    if mutant == "bypass_skip_condition":
        lean["if"] = "true"
    if mutant == "barrier_after_serial":
        steps.remove(barrier)
        steps.append(barrier)
    with pytest.raises(AssertionError):
        _assert_render_dependencies_barrier_contract(workflow)
