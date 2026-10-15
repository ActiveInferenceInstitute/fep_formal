"""The required-check list has one owner (AGENTS.md) and CI executes it."""

from __future__ import annotations

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
    "--junitxml=output/live-chrome-acceptance.xml": "isolated live Chrome component",
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
