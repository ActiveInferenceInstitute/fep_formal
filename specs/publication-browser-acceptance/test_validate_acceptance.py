"""Real collection and adversarial split-JUnit/coverage contracts."""

from __future__ import annotations

import copy
import importlib.util
import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

HELPER = Path(__file__).with_name("validate_acceptance.py")
SPEC = importlib.util.spec_from_file_location("publication_acceptance", HELPER)
assert SPEC is not None and SPEC.loader is not None
acceptance = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(acceptance)


@pytest.fixture(scope="module")
def project(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root = tmp_path_factory.mktemp("split-acceptance")
    tests = root / "tests"
    tests.mkdir()
    (root / "output").mkdir()
    (root / "uv.lock").write_text("fixture-lock\n")
    (root / "pyproject.toml").write_text(
        "[tool.pytest.ini_options]\nmarkers=['serial_lean: fixture']\n"
    )
    (tests / "conftest.py").write_text(
        "_LIVE_CHROME_NODE_IDS = frozenset("
        + repr(set(acceptance.LIVE_NODE_IDS))
        + ")\n"
    )
    browser = "import pytest\n"
    for nodeid in acceptance.LIVE_NODE_IDS + acceptance.CONTROL_NODE_IDS[:2]:
        browser += f"def {nodeid.split('::')[1]}(): pass\n"
    for prefix in (
        "test_live_chrome_grouping_requires_xdist_and_exact_node_ids",
        "test_loadgroup_workers_require_grouping_before_xdist_node_ids",
    ):
        browser += (
            f"@pytest.mark.parametrize('flag',[False,True])\ndef {prefix}(flag): pass\n"
        )
    (tests / "test_browser_capture.py").write_text(browser)
    (tests / "test_other.py").write_text(
        "import pytest\n"
        "@pytest.mark.parametrize('value',[1,2],ids=['URL::part@tag','@@template@@'])\n"
        "def test_parameter(value): pass\n"
        "class TestCalls:\n"
        "    def test_class(self): pass\n"
        "@pytest.mark.serial_lean\n"
        "def test_excluded(): raise RuntimeError('must not execute or collect')\n"
    )
    return root


@pytest.fixture(scope="module")
def collection(project: Path) -> dict:
    return acceptance.collect(project)


def junit(nodeids: list[str], outcomes: dict[str, str] | None = None) -> bytes:
    outcomes = outcomes or {}
    suite = ET.Element("testsuite")
    counts = {key: 0 for key in ("failures", "errors", "skipped")}
    for nodeid in nodeids:
        classname, name = acceptance.junit_identity(nodeid)
        case = ET.SubElement(
            suite, "testcase", classname=classname, name=name, time="0.001"
        )
        outcome = outcomes.get(nodeid, "passed")
        if outcome != "passed":
            ET.SubElement(
                case, outcome, message="fixture evidence"
            ).text = "fixture detail"
            counts[
                {"failure": "failures", "error": "errors", "skipped": "skipped"}[
                    outcome
                ]
            ] += 1
    suite.attrib.update(
        {
            "tests": str(len(nodeids)),
            **{key: str(value) for key, value in counts.items()},
        }
    )
    return ET.tostring(suite)


def coverage(covered: int = 90, valid: int = 100, rate: str = "0.90") -> bytes:
    return ET.tostring(
        ET.Element(
            "coverage",
            {
                "lines-covered": str(covered),
                "lines-valid": str(valid),
                "line-rate": rate,
            },
        )
    )


def parts(collection: dict) -> tuple[list[str], list[str]]:
    return (
        [
            nodeid
            for nodeid in collection["nodeids"]
            if nodeid not in acceptance.LIVE_NODE_IDS
        ],
        list(acceptance.LIVE_NODE_IDS),
    )


def test_real_collection_has_exact_selection_and_junit_identity(
    collection: dict,
) -> None:
    assert len(collection["nodeids"]) == 11
    assert not any("test_excluded" in nodeid for nodeid in collection["nodeids"])
    assert set(acceptance.LIVE_NODE_IDS + acceptance.CONTROL_NODE_IDS) <= set(
        collection["nodeids"]
    )
    assert acceptance.junit_identity("tests/test_other.py::TestCalls::test_class") == (
        "tests.test_other.TestCalls",
        "test_class",
    )
    assert acceptance.junit_identity(
        "tests/test_other.py::test_parameter[URL::part@tag]"
    ) == ("tests.test_other", "test_parameter[URL::part@tag]")
    assert acceptance.junit_identity(
        "tests/test_other.py::test_parameter[@@template@@]"
    ) == ("tests.test_other", "test_parameter[@@template@@]")


def test_valid_union_discloses_optional_skip(collection: dict) -> None:
    parallel, chrome = parts(collection)
    optional = next(nodeid for nodeid in parallel if "test_parameter" in nodeid)
    result = acceptance.validate_payloads(
        collection,
        collection,
        junit(parallel, {optional: "skipped"}),
        junit(chrome),
        coverage(),
    )
    assert result["status"] == "passed"
    assert result["total_cases"] == 11
    assert result["chrome_cases"] == 2
    assert result["required_eight_passed_no_skip"]
    assert result["counts"] == {"passed": 10, "failure": 0, "error": 0, "skipped": 1}
    assert len(result["skipped_cases"]) == 1


@pytest.mark.parametrize(
    "mutation",
    [
        "empty",
        "missing",
        "duplicate",
        "unknown",
        "wrong_route",
        "group_suffix",
        "declared_count",
        "class_changed",
    ],
)
def test_junit_membership_refuses_structural_mutations(
    collection: dict, mutation: str
) -> None:
    parallel, chrome = parts(collection)
    if mutation == "empty":
        chrome = []
    elif mutation == "missing":
        parallel.pop()
    elif mutation == "duplicate":
        parallel.append(parallel[0])
    elif mutation == "unknown":
        parallel.append("tests/test_other.py::test_unknown")
    elif mutation == "wrong_route":
        parallel.append(chrome.pop())
    elif mutation == "group_suffix":
        chrome[0] += "@live_chrome"
    p, c = junit(parallel), junit(chrome)
    if mutation == "declared_count":
        tree = ET.fromstring(p)
        tree.set("tests", "0")
        p = ET.tostring(tree)
    if mutation == "class_changed":
        tree = ET.fromstring(p)
        tree.find("testcase").set("classname", "tests.foreign")
        p = ET.tostring(tree)
    with pytest.raises(acceptance.AcceptanceError):
        acceptance.validate_payloads(collection, collection, p, c, coverage())


@pytest.mark.parametrize(
    "mutation",
    [
        "nested_failure",
        "suite_error",
        "root_case",
        "nested_case",
        "conflicting_outcomes",
    ],
)
def test_junit_refuses_misplaced_evidence(collection: dict, mutation: str) -> None:
    parallel, chrome = parts(collection)
    tree = ET.fromstring(junit(parallel))
    case = tree.find("testcase")
    if mutation == "nested_failure":
        ET.SubElement(ET.SubElement(case, "wrapper"), "failure")
    elif mutation == "suite_error":
        ET.SubElement(tree, "error")
    elif mutation == "root_case":
        outer = ET.Element("testsuites")
        outer.append(case)
        outer.append(tree)
        tree = outer
    elif mutation == "nested_case":
        ET.SubElement(ET.SubElement(case, "properties"), "testcase")
    else:
        ET.SubElement(case, "failure")
        ET.SubElement(case, "skipped")
    with pytest.raises(acceptance.AcceptanceError):
        acceptance.validate_payloads(
            collection, collection, ET.tostring(tree), junit(chrome), coverage()
        )


@pytest.mark.parametrize(
    "nodeid", acceptance.LIVE_NODE_IDS + acceptance.CONTROL_NODE_IDS
)
@pytest.mark.parametrize("outcome", ["skipped", "failure", "error"])
def test_every_required_signal_refuses_every_nonpass(
    collection: dict, nodeid: str, outcome: str
) -> None:
    parallel, chrome = parts(collection)
    result = acceptance.validate_payloads(
        collection,
        collection,
        junit(parallel, {nodeid: outcome}),
        junit(chrome, {nodeid: outcome}),
        coverage(),
    )
    assert result["status"] == "failed"
    assert not result["required_eight_passed_no_skip"]
    assert (
        next(row for row in result["required_signals"] if row["nodeid"] == nodeid)[
            "outcome"
        ]
        == outcome
    )


@pytest.mark.parametrize(
    "covered,valid,rate",
    [
        (-1, 100, "0"),
        (101, 100, "1"),
        (0, 0, "0"),
        (90, 100, "NaN"),
        (90, 100, "Infinity"),
        (90, 100, "0.91"),
        (90, 100, "1.01"),
    ],
)
def test_coverage_refuses_invalid_or_incoherent_counts(
    covered: int, valid: int, rate: str
) -> None:
    with pytest.raises(acceptance.AcceptanceError):
        acceptance.coverage_evidence(coverage(covered, valid, rate))


def test_coverage_floor_has_exact_integer_boundary(collection: dict) -> None:
    parallel, chrome = parts(collection)
    for covered, expected in [(8899, "failed"), (8900, "passed")]:
        result = acceptance.validate_payloads(
            collection,
            collection,
            junit(parallel),
            junit(chrome),
            coverage(covered, 10000, f"0.{covered}"),
        )
        assert result["status"] == expected


def test_coherently_edited_cached_collection_is_refused(collection: dict) -> None:
    changed = copy.deepcopy(collection)
    changed["nodeids"].pop()
    parallel, chrome = parts(changed)
    with pytest.raises(acceptance.AcceptanceError, match="fresh current collection"):
        acceptance.validate_payloads(
            changed, collection, junit(parallel), junit(chrome), coverage()
        )


@pytest.mark.parametrize("mutation", ["empty", "duplicate", "required_missing"])
def test_malformed_membership_is_explicitly_refused(
    collection: dict, mutation: str
) -> None:
    changed = copy.deepcopy(collection)
    if mutation == "empty":
        changed["nodeids"] = []
    elif mutation == "duplicate":
        changed["nodeids"].append(changed["nodeids"][0])
    else:
        changed["nodeids"].remove(acceptance.CONTROL_NODE_IDS[0])
    parallel, chrome = parts(collection)
    with pytest.raises(acceptance.AcceptanceError):
        acceptance.validate_payloads(
            changed, changed, junit(parallel), junit(chrome), coverage()
        )


def test_source_selector_drift_is_refused(project: Path) -> None:
    path = project / "tests/conftest.py"
    original = path.read_bytes()
    try:
        path.write_text(
            "_LIVE_CHROME_NODE_IDS = frozenset({'tests/test_other.py::test_class'})\n"
        )
        with pytest.raises(acceptance.AcceptanceError, match="selectors changed"):
            acceptance.source_live_node_ids(project)
    finally:
        path.write_bytes(original)


def test_safe_outputs_refuse_source_write_and_symlink(project: Path) -> None:
    with pytest.raises(acceptance.AcceptanceError, match="outside output"):
        acceptance._write(project, Path("tests/forbidden.json"), {})
    link = project / "output/link"
    link.symlink_to(project / "tests", target_is_directory=True)
    with pytest.raises(acceptance.AcceptanceError, match="symlink"):
        acceptance._write(project, Path("output/link/forbidden.json"), {})
    assert not (project / "tests/forbidden.json").exists()


def test_real_cli_fresh_collection_union_nonmutation_and_coherent_omission(
    project: Path, collection: dict
) -> None:
    before = acceptance.source_hashes(project)
    parallel, chrome = parts(collection)
    out = project / "output"
    for name, data in [
        ("parallel.xml", junit(parallel)),
        ("chrome.xml", junit(chrome)),
        ("coverage.xml", coverage()),
    ]:
        (out / name).write_bytes(data)
    command = [sys.executable, str(HELPER), "--project-root", str(project)]
    result = subprocess.run(
        command + ["--collect", "output/collection.json"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    args = [
        "--collection",
        "output/collection.json",
        "--parallel-junit",
        "output/parallel.xml",
        "--chrome-junit",
        "output/chrome.xml",
        "--coverage",
        "output/coverage.xml",
        "--output",
        "output/summary.json",
    ]
    input_paths = [
        out / name
        for name in ("collection.json", "parallel.xml", "chrome.xml", "coverage.xml")
    ]
    input_before = [
        (path.read_bytes(), path.stat().st_mtime_ns) for path in input_paths
    ]
    result = subprocess.run(command + args, capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
    assert json.loads((out / "summary.json").read_text())["status"] == "passed"
    assert [
        (path.read_bytes(), path.stat().st_mtime_ns) for path in input_paths
    ] == input_before
    assert acceptance.source_hashes(project) == before
    changed = json.loads((out / "collection.json").read_text())
    omitted = next(nodeid for nodeid in parallel if "test_parameter" in nodeid)
    changed["nodeids"].remove(omitted)
    (out / "collection.json").write_text(json.dumps(changed))
    (out / "parallel.xml").write_bytes(
        junit([nodeid for nodeid in parallel if nodeid != omitted])
    )
    result = subprocess.run(command + args, capture_output=True, text=True, check=False)
    assert result.returncode == 1
    assert "fresh current collection" in result.stderr
    assert json.loads((out / "summary.json").read_text())["status"] == "failed"
    assert acceptance.source_hashes(project) == before


@pytest.mark.parametrize(
    "input_name", ["collection.json", "parallel.xml", "chrome.xml", "coverage.xml"]
)
@pytest.mark.parametrize("hardlink", [False, True])
def test_real_cli_output_alias_refusal_preserves_all_inputs(
    project: Path, collection: dict, input_name: str, hardlink: bool
) -> None:
    parallel, chrome = parts(collection)
    out = project / "output/alias-controls"
    out.mkdir(exist_ok=True)
    payloads = {
        "collection.json": (json.dumps(collection) + "\n").encode(),
        "parallel.xml": junit(parallel),
        "chrome.xml": junit(chrome),
        "coverage.xml": coverage(),
    }
    for name, data in payloads.items():
        (out / name).write_bytes(data)
    chosen = out / input_name
    output = chosen
    if hardlink:
        output = out / "hardlinked-output.json"
        output.unlink(missing_ok=True)
        os.link(chosen, output)
    before = {
        name: ((out / name).read_bytes(), (out / name).stat().st_mtime_ns)
        for name in payloads
    }
    command = [
        sys.executable,
        str(HELPER),
        "--project-root",
        str(project),
        "--collection",
        str(out / "collection.json"),
        "--parallel-junit",
        str(out / "parallel.xml"),
        "--chrome-junit",
        str(out / "chrome.xml"),
        "--coverage",
        str(out / "coverage.xml"),
        "--output",
        str(output),
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    assert result.returncode == 1
    assert "acceptance input" in result.stderr
    assert {
        name: ((out / name).read_bytes(), (out / name).stat().st_mtime_ns)
        for name in payloads
    } == before
    if hardlink:
        assert output.samefile(chosen)
        assert output.read_bytes() == payloads[input_name]


def test_real_collection_output_replaces_source_hardlink_without_writing_through(
    project: Path,
) -> None:
    source = project / "tests/test_other.py"
    before = (source.read_bytes(), source.stat().st_mtime_ns, source.stat().st_ino)
    output = project / "output/source-hardlink.json"
    os.link(source, output)
    result = subprocess.run(
        [
            sys.executable,
            str(HELPER),
            "--project-root",
            str(project),
            "--collect",
            str(output),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert (
        source.read_bytes(),
        source.stat().st_mtime_ns,
        source.stat().st_ino,
    ) == before
    assert not output.samefile(source)
    assert json.loads(output.read_text())["status"] == "collected"


# These controls execute the actual CI guards with real Git repositories.
# The source-stamp producer remains unfiltered; placement fixes the dependency
# layout rather than relabeling a dirty source checkout.
_RENDER_GUARD_STEPS = (
    "Require a clean source checkout before catalogue projection",
    "Render the publication and accept it fail-closed",
)


def _init_render_fixture_repository(root: Path) -> None:
    subprocess.run(
        ["git", "-c", "core.fsmonitor=false", "init", "-q", str(root)],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(root), "config", "--local", "core.fsmonitor", "false"],
        check=True,
        capture_output=True,
    )


def _render_source_fixture(tmp_path: Path) -> Path:
    root = (tmp_path / "publication").resolve()
    root.mkdir()
    _init_render_fixture_repository(root)
    # A cached prior-directory listing can survive the control's rename.
    # Configure this disposable fixture before any status query; the actual
    # source stamp and CI guards still inspect unfiltered Git status.
    subprocess.run(
        ["git", "config", "--local", "core.untrackedCache", "false"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    project_root = HELPER.parents[2]
    (root / ".gitignore").write_bytes((project_root / ".gitignore").read_bytes())
    (root / "README.md").write_text("Committed publication source.\n")
    (root / "docs").mkdir()
    (root / "docs/render-acceptance.json").write_text("{}\n")
    subprocess.run(["git", "add", "."], cwd=root, check=True, capture_output=True)
    subprocess.run(
        ["git", "-c", "commit.gpgsign=false", "commit", "-qm", "fixture source"],
        cwd=root,
        env={
            **os.environ,
            "GIT_AUTHOR_NAME": "Test",
            "GIT_AUTHOR_EMAIL": "test@example.invalid",
            "GIT_COMMITTER_NAME": "Test",
            "GIT_COMMITTER_EMAIL": "test@example.invalid",
        },
        check=True,
        capture_output=True,
    )
    return root


def _actual_render_guard(root: Path, step_name: str) -> subprocess.CompletedProcess:
    import yaml

    workflow = yaml.safe_load(
        (HELPER.parents[2] / ".github/workflows/ci.yml").read_text()
    )
    step = next(
        step
        for step in workflow["jobs"]["render"]["steps"]
        if step.get("name") == step_name
    )
    guard = step["run"].split("<<'PY'\n", 1)[1].rsplit("\nPY", 1)[0]
    return subprocess.run(
        [sys.executable, "-B", "-c", guard],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
        timeout=90,
    )


@pytest.mark.parametrize("step_name", _RENDER_GUARD_STEPS)
def test_ci_template_placement_preserves_actual_clean_source_stamp(
    tmp_path: Path, step_name: str
) -> None:
    import yaml

    from fep_lean.output.manuscript import _source_stamp_vars

    root = _render_source_fixture(tmp_path)
    source_commit = _source_stamp_vars(root)["commit"]
    assert _source_stamp_vars(root)["dirty"] == "false"
    legacy_template = root / "render-template"
    legacy_template.mkdir()
    _init_render_fixture_repository(legacy_template)
    (legacy_template / "README.md").write_text("Acquired template dependency.\n")
    assert _source_stamp_vars(root)["dirty"] == "true"
    rejected = _actual_render_guard(root, step_name)
    assert rejected.returncode == 1
    assert "source checkout is not clean" in rejected.stderr

    workflow = yaml.safe_load(
        (HELPER.parents[2] / ".github/workflows/ci.yml").read_text()
    )
    steps = workflow["jobs"]["render"]["steps"]
    checkout = next(
        step
        for step in steps
        if step.get("name")
        == "Check out the shared rendering template at its pinned ref"
    )
    assert checkout["with"]["path"] == "output/render-template"
    assert checkout["with"]["ref"] == "5b3c0f43940f0322fbc6205b3be4c2854f99329d"
    template = root / checkout["with"]["path"]
    template.parent.mkdir()
    legacy_template.rename(template)
    registration = next(
        step
        for step in steps
        if step.get("name")
        == "Register this repository as the template's active project"
    )
    registered = subprocess.run(
        ["bash", "-e", "-c", registration["run"]],
        cwd=root,
        env={**os.environ, "GITHUB_WORKSPACE": str(root)},
        capture_output=True,
        text=True,
        check=False,
    )
    assert registered.returncode == 0, registered.stderr
    assert (template / "projects/active/fep_lean").resolve() == root
    render = next(step for step in steps if step.get("name") == _RENDER_GUARD_STEPS[1])
    assert render["env"]["FEP_LEAN_TEMPLATE_DIR"] == (
        "${{ github.workspace }}/output/render-template"
    )
    source = _source_stamp_vars(root)
    assert source["commit"] == source_commit
    assert source["dirty"] == "false"
    assert "uncommitted changes" not in source["stamp"]
    accepted = _actual_render_guard(root, step_name)
    assert accepted.returncode == 0, accepted.stderr
    assert "source checkout is clean" in accepted.stdout


@pytest.mark.parametrize("step_name", _RENDER_GUARD_STEPS)
@pytest.mark.parametrize(
    "mutation",
    [
        "tracked_source",
        "staged_source",
        "untracked_source",
        "tracked_receipt",
        "staged_receipt",
        "legacy_template",
        "untracked_whitespace",
    ],
)
def test_ci_hydration_guards_refuse_unfiltered_git_drift_without_path_disclosure(
    tmp_path: Path, step_name: str, mutation: str
) -> None:
    from fep_lean.output.manuscript import _source_stamp_vars

    root = _render_source_fixture(tmp_path)
    if mutation in {"tracked_source", "staged_source"}:
        changed = root / "README.md"
        changed.write_text("Uncommitted scientific source.\n")
    elif mutation in {"tracked_receipt", "staged_receipt"}:
        changed = root / "docs/render-acceptance.json"
        changed.write_text('{"uncommitted":true}\n')
    elif mutation == "legacy_template":
        changed = root / "render-template"
        changed.mkdir()
        _init_render_fixture_repository(changed)
        (changed / "README.md").write_text("Untracked dependency.\n")
    else:
        changed = root / (
            "untracked DO-NOT-DISCLOSE source.txt"
            if mutation == "untracked_whitespace"
            else "untracked-DO-NOT-DISCLOSE-source.txt"
        )
        changed.write_text("Untracked source.\n")
    if mutation.startswith("staged_"):
        subprocess.run(
            ["git", "add", str(changed.relative_to(root))],
            cwd=root,
            check=True,
            capture_output=True,
        )
    before = subprocess.check_output(["git", "status", "--porcelain"], cwd=root)
    assert before and _source_stamp_vars(root)["dirty"] == "true"
    result = _actual_render_guard(root, step_name)
    assert result.returncode == 1
    assert "source checkout is not clean before manuscript hydration" in result.stderr
    assert not result.stdout
    assert changed.name not in result.stderr
    assert "DO-NOT-DISCLOSE" not in result.stderr
    assert subprocess.check_output(["git", "status", "--porcelain"], cwd=root) == before
    assert _source_stamp_vars(root)["dirty"] == "true"


@pytest.mark.parametrize(
    "sealed,actual,matched",
    [
        ([3, 14, 9], [3, 14, 9], True),
        ([3, 14, 8], [3, 14, 9], False),
        ([3, 14, 9], [3, 14, 8], False),
        (None, [3, 14, 9], False),
        ([3, 14], [3, 14, 9], False),
        ([3, 14, True], [3, 14, 1], False),
    ],
    ids=["exact", "newer-runtime", "older-runtime", "missing", "short", "boolean"],
)
def test_sealed_validator_python_diagnostic(sealed, actual, matched):
    approved = {"validator_python": sealed}
    before = copy.deepcopy(approved)
    message = acceptance._validator_python_diagnostic(approved, actual)
    assert (message is None) == matched
    assert approved == before
    if message is not None:
        assert "sealed validator_python=" in message
        assert "actual validator_python=" in message
        assert "only difference" in message


def _diagnostic_inputs(root):
    out = root / "output"
    out.mkdir()
    approved = {
        "validator_python": list(sys.version_info[:3]),
        "nodeids": sorted(acceptance.LIVE_NODE_IDS + acceptance.CONTROL_NODE_IDS),
        "source_sha256": {"fixture": "a" * 64},
    }
    parallel = junit(list(acceptance.CONTROL_NODE_IDS))
    chrome = junit(list(acceptance.LIVE_NODE_IDS))
    payloads = {
        "collection.json": json.dumps(approved).encode(),
        "parallel.xml": parallel,
        "chrome.xml": chrome,
        "coverage.xml": coverage(),
    }
    for name, raw in payloads.items():
        (out / name).write_bytes(raw)
    argv = [
        "--project-root",
        str(root),
        "--collection",
        str(out / "collection.json"),
        "--parallel-junit",
        str(out / "parallel.xml"),
        "--chrome-junit",
        str(out / "chrome.xml"),
        "--coverage",
        str(out / "coverage.xml"),
        "--output",
        str(out / "summary.json"),
    ]
    return argv, approved, payloads


@pytest.mark.parametrize(
    "mode", ["matching", "patch-mismatch", "source-mismatch", "bad-junit"]
)
def test_cli_retains_fresh_collection_without_acceptance_waiver(
    tmp_path, monkeypatch, capsys, mode
):
    argv, approved, payloads = _diagnostic_inputs(tmp_path)
    fresh = copy.deepcopy(approved)
    if mode == "patch-mismatch":
        approved["validator_python"][-1] += 1
    elif mode == "source-mismatch":
        fresh["source_sha256"]["fixture"] = "b" * 64
    elif mode == "bad-junit":
        (tmp_path / "output/parallel.xml").write_bytes(b"not XML")
    (tmp_path / "output/collection.json").write_text(json.dumps(approved))

    def collect(root, **kwargs):
        assert root == tmp_path and kwargs["observation"].name.endswith(
            ".collection-worker.json"
        )
        # The version diagnostic must already be visible before this expensive seam.
        captured = capsys.readouterr()
        assert ("sealed validator_python=" in captured.err) == (
            mode == "patch-mismatch"
        )
        return fresh

    monkeypatch.setattr(acceptance, "collect", collect)
    code = acceptance.main(argv)
    out = tmp_path / "output"
    assert json.loads((out / "summary.json.fresh-collection.json").read_text()) == fresh
    summary = json.loads((out / "summary.json").read_text())
    if mode == "matching":
        assert code == 0 and summary["status"] == "passed"
        expected = acceptance.validate_payloads(
            approved,
            fresh,
            payloads["parallel.xml"],
            payloads["chrome.xml"],
            payloads["coverage.xml"],
        )
        expected["input_sha256"]["collection"] = acceptance._sha(
            (out / "collection.json").read_bytes()
        )
        assert summary == expected
    else:
        assert code == 1 and summary["status"] == "failed"
        if mode == "patch-mismatch":
            assert "sealed validator_python=" in summary["errors"][0]
        if mode == "source-mismatch":
            assert "fresh current collection" in summary["errors"][0]


@pytest.mark.parametrize(
    "mode", ["worker-nonzero", "malformed-worker-json", "pytest-collection-failed"]
)
def test_failed_collection_retains_actual_worker_observation(
    tmp_path, monkeypatch, mode
):
    from types import SimpleNamespace

    (tmp_path / "output").mkdir()
    raw = json.dumps(
        {"exit_code": 2, "nodeids": [], "collection_log": "fixture diagnostic"}
    )
    if mode == "malformed-worker-json":
        raw = "not JSON"
    result = SimpleNamespace(
        returncode=1 if mode == "worker-nonzero" else 0,
        stdout=raw,
        stderr="actual fake-worker stderr",
    )
    monkeypatch.setattr(acceptance, "source_live_node_ids", lambda root: ())
    monkeypatch.setattr(acceptance, "source_hashes", lambda root: {})
    monkeypatch.setattr(acceptance.subprocess, "run", lambda *args, **kwargs: result)
    path = tmp_path / "output/worker.json"
    with pytest.raises((acceptance.AcceptanceError, json.JSONDecodeError)):
        acceptance.collect(tmp_path, observation=path)
    observed = json.loads(path.read_text())
    assert observed["status"] == "collection-worker-observed"
    assert observed["returncode"] == result.returncode
    assert observed["stdout"] == raw and observed["stderr"] == result.stderr


def test_fresh_collection_sidecar_alias_is_refused_before_collection(
    tmp_path, monkeypatch
):
    argv, _, _ = _diagnostic_inputs(tmp_path)
    output = tmp_path / "output"
    original = (output / "collection.json").read_bytes()
    aliased = output / "summary.json.fresh-collection.json"
    (output / "collection.json").rename(aliased)
    argv[argv.index("--collection") + 1] = str(aliased)

    def forbidden(*args, **kwargs):
        raise AssertionError("collection must not start on output/input alias")

    monkeypatch.setattr(acceptance, "collect", forbidden)
    assert acceptance.main(argv) == 1
    assert aliased.read_bytes() == original
    assert json.loads((output / "summary.json").read_text())["status"] == "failed"
