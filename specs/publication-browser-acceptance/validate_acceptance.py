"""Prove exact split-pytest membership and retain bounded acceptance evidence.

Collection executes pytest collection only; validation never executes tests.
The two live Chrome tests are a separate, once-only execution component. This
topology does not diagnose the cause of earlier hosted startup failures.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import io
import json
import os
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from collections import Counter
from contextlib import redirect_stderr, redirect_stdout, suppress
from decimal import ROUND_HALF_EVEN, Context, Decimal, InvalidOperation, localcontext
from pathlib import Path
from typing import Any

LIVE_NODE_IDS = (
    (
        "tests/test_browser_capture.py::"
        "test_live_chrome_blocks_and_records_a_delayed_outbound_request"
    ),
    (
        "tests/test_browser_capture.py::"
        "test_live_chrome_replay_terminates_every_profile_writer"
    ),
)
CONTROL_NODE_IDS = (
    "tests/test_browser_capture.py::test_startup_stderr_diagnostics_bound_and_decode_tail",
    (
        "tests/test_browser_capture.py::"
        "test_startup_diagnostics_retain_stderr_without_hiding_launch_failure"
    ),
    (
        "tests/test_browser_capture.py::"
        "test_live_chrome_grouping_requires_xdist_and_exact_node_ids[False]"
    ),
    (
        "tests/test_browser_capture.py::"
        "test_live_chrome_grouping_requires_xdist_and_exact_node_ids[True]"
    ),
    (
        "tests/test_browser_capture.py::"
        "test_loadgroup_workers_require_grouping_before_xdist_node_ids[False]"
    ),
    (
        "tests/test_browser_capture.py::"
        "test_loadgroup_workers_require_grouping_before_xdist_node_ids[True]"
    ),
)
COLLECTION_ARGS = (
    "tests/",
    "--collect-only",
    "-q",
    "-n",
    "0",
    "--no-cov",
    "-p",
    "no:cacheprovider",
    "-m",
    "not serial_lean",
)
MAX_XML_BYTES = 32 * 1024 * 1024


class AcceptanceError(ValueError):
    """An input cannot establish the declared split-suite acceptance."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AcceptanceError(message)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _regular_path(root: Path, value: Path, *, output: bool = False) -> Path:
    """Refuse path escape and symlink components before reading or writing."""
    path = value if value.is_absolute() else root / value
    _require(".." not in path.parts, f"parent traversal is not allowed: {value}")
    boundary = root / "output" if output else root
    try:
        path.relative_to(boundary)
    except ValueError as exc:
        raise AcceptanceError(f"path is outside {boundary.name}/: {value}") from exc
    current = path
    while current != root:
        _require(not current.is_symlink(), f"symlink path is not allowed: {value}")
        current = current.parent
    if path.exists():
        _require(path.is_file(), f"expected a regular file: {value}")
    elif not output:
        raise AcceptanceError(f"missing input: {value}")
    return path


def _output_path(root: Path, value: Path, protected: tuple[Path, ...]) -> Path:
    path = _regular_path(root, value, output=True)
    for input_path in protected:
        selected = input_path if input_path.is_absolute() else root / input_path
        _require(
            path.resolve() != selected.resolve(), "output aliases an acceptance input"
        )
        if path.exists() and selected.exists():
            _require(
                not path.samefile(selected), "output hardlinks an acceptance input"
            )
    return path


def _write(
    root: Path,
    value: Path,
    payload: dict[str, Any],
    *,
    protected: tuple[Path, ...] = (),
) -> None:
    """Atomic replacement avoids writing through an existing source hardlink."""
    path = _output_path(root, value, protected)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=".acceptance-",
            delete=False,
        ) as stream:
            temporary = Path(stream.name)
            stream.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        _output_path(root, path, protected)
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def source_live_node_ids(root: Path) -> tuple[str, ...]:
    """Read the existing reviewed selectors as syntax, without importing them."""
    path = _regular_path(root, Path("tests/conftest.py"))
    tree = ast.parse(path.read_text(encoding="utf-8"))
    values = []
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "_LIVE_CHROME_NODE_IDS"
            for target in node.targets
        ):
            value = node.value
            _require(
                isinstance(value, ast.Call)
                and isinstance(value.func, ast.Name)
                and value.func.id == "frozenset"
                and len(value.args) == 1
                and not value.keywords,
                "live Chrome selector syntax changed",
            )
            values.append(ast.literal_eval(value.args[0]))
    _require(
        len(values) == 1, "expected one canonical live Chrome selector declaration"
    )
    _require(values[0] == set(LIVE_NODE_IDS), "canonical live Chrome selectors changed")
    return LIVE_NODE_IDS


def source_hashes(root: Path) -> dict[str, str]:
    """Bind collection-relevant source/test leaves, excluding Python caches."""
    paths = {Path("pyproject.toml"), Path("uv.lock"), Path("tests/conftest.py")}
    for directory in ("src", "tests"):
        base = root / directory
        if base.exists():
            for path in base.rglob("*"):
                relative = path.relative_to(root)
                if any(
                    part.startswith(".") or part == "__pycache__"
                    for part in relative.parts
                ):
                    continue
                if path.is_file() or path.is_symlink():
                    paths.add(relative)
    result = {
        path.as_posix(): _sha(_regular_path(root, path).read_bytes())
        for path in sorted(paths)
    }
    result["validator_source"] = _sha(Path(__file__).read_bytes())
    return result


def junit_identity(nodeid: str) -> tuple[str, str]:
    """Match pytest's default JUnit identity, retaining parameter text exactly."""
    _require(isinstance(nodeid, str) and "::" in nodeid, "malformed collected node ID")
    path, address = nodeid.split("::", 1)
    _require(
        path.startswith("tests/") and path.endswith(".py"), "unknown collected path"
    )
    _require(
        "\\" not in path and ".." not in Path(path).parts, "noncanonical collected path"
    )
    head, bracket, parameter = address.partition("[")
    parts = head.split("::")
    _require(all(parts), "empty collected address")
    classname = ".".join([path[:-3].replace("/", "."), *parts[:-1]])
    name = parts[-1] + (bracket + parameter if bracket else "")
    return classname, name


def _collection_worker(root: Path) -> dict[str, Any]:
    import pytest

    class Collector:
        def __init__(self) -> None:
            self.nodeids: list[str] = []

        def pytest_collection_finish(self, session: pytest.Session) -> None:
            self.nodeids = [item.nodeid for item in session.items]

    collector = Collector()
    captured = io.StringIO()
    os.chdir(root)
    with redirect_stdout(captured), redirect_stderr(captured):
        code = int(pytest.main(list(COLLECTION_ARGS), plugins=[collector]))
    return {
        "exit_code": code,
        "nodeids": collector.nodeids,
        "collection_log": captured.getvalue(),
    }


def collect(
    root: Path,
    *,
    observation: Path | None = None,
    protected: tuple[Path, ...] = (),
) -> dict[str, Any]:
    source_live_node_ids(root)
    before = source_hashes(root)
    result = subprocess.run(
        [
            sys.executable,
            str(Path(__file__).resolve()),
            "--project-root",
            str(root),
            "--_collect-worker",
        ],
        cwd=root,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    if observation is not None:
        _write(
            root,
            observation,
            {
                "status": "collection-worker-observed",
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "validator_python": list(sys.version_info[:3]),
                "scope": "Raw collection observation, not acceptance.",
            },
            protected=protected,
        )
    _require(result.returncode == 0, "collection worker did not complete successfully")
    data = json.loads(result.stdout)
    _require(data["exit_code"] == 0, "pytest collection failed")
    nodeids = data["nodeids"]
    _require(isinstance(nodeids, list) and bool(nodeids), "empty pytest collection")
    _require(len(nodeids) == len(set(nodeids)), "duplicate collected node ID")
    identities = [junit_identity(nodeid) for nodeid in nodeids]
    _require(
        len(identities) == len(set(identities)), "ambiguous collected JUnit identity"
    )
    _require(
        set(LIVE_NODE_IDS + CONTROL_NODE_IDS) <= set(nodeids),
        "required eight cases absent from collection",
    )
    _require(source_hashes(root) == before, "source changed during collection")
    return {
        "schema_version": 1,
        "status": "collected",
        "collection_arguments": list(COLLECTION_ARGS),
        "nodeids": sorted(nodeids),
        "live_nodeids": list(LIVE_NODE_IDS),
        "control_nodeids": list(CONTROL_NODE_IDS),
        "source_sha256": before,
        "validator_python": list(sys.version_info[:3]),
        "scope": "Actual non-serial pytest collection; no test execution or browser acceptance.",
    }


def _load_json(data: bytes) -> dict[str, Any]:
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result = {}
        for key, value in items:
            _require(key not in result, f"duplicate JSON key: {key}")
            result[key] = value
        return result

    result = json.loads(data, object_pairs_hook=pairs)
    _require(isinstance(result, dict), "expected JSON object")
    return result


def _xml(data: bytes, label: str) -> ET.Element:
    _require(0 < len(data) <= MAX_XML_BYTES, f"empty or oversized {label}")
    try:
        return ET.fromstring(data)
    except ET.ParseError as exc:
        raise AcceptanceError(f"invalid {label} XML") from exc


def _cases(data: bytes, label: str) -> list[dict[str, Any]]:
    tree = _xml(data, label)
    _require(tree.tag in {"testsuite", "testsuites"}, f"unknown {label} root")
    suites = [tree] if tree.tag == "testsuite" else list(tree)
    _require(bool(suites), f"empty {label} suite list")
    _require(
        all(suite.tag == "testsuite" for suite in suites),
        f"invalid {label} suite placement",
    )
    for suite in suites:
        _require(
            all(
                child.tag in {"testcase", "properties", "system-out", "system-err"}
                for child in suite
            ),
            f"invalid {label} suite child",
        )
        for child in suite:
            if child.tag == "testcase":
                _require(
                    all(
                        grandchild.tag
                        in {
                            "failure",
                            "error",
                            "skipped",
                            "properties",
                            "system-out",
                            "system-err",
                        }
                        for grandchild in child
                    ),
                    f"invalid {label} testcase child",
                )
    parents = {child: parent for parent in tree.iter() for child in parent}
    for element in tree.iter():
        if element.tag in {"failure", "error", "skipped"}:
            _require(
                parents.get(element) is not None and parents[element].tag == "testcase",
                f"misplaced {label} outcome marker",
            )
        if element.tag == "testcase":
            _require(parents.get(element) in suites, f"misplaced {label} testcase")
        if element.tag in {"failure", "error", "skipped", "system-out", "system-err"}:
            _require(not list(element), f"nested {label} evidence markup")
        if element.tag == "properties":
            _require(
                all(child.tag == "property" and not list(child) for child in element),
                f"invalid {label} properties",
            )
    cases = []
    for case in tree.iter("testcase"):
        classname, name = case.get("classname"), case.get("name")
        _require(bool(classname) and bool(name), f"malformed {label} case identity")
        markers = [
            child for child in case if child.tag in {"failure", "error", "skipped"}
        ]
        _require(len(markers) <= 1, f"conflicting {label} case outcomes")
        cases.append(
            {
                "classname": classname,
                "name": name,
                "outcome": markers[0].tag if markers else "passed",
                "reason": markers[0].get("message", "") if markers else None,
                "details": markers[0].text if markers else None,
                "time": case.get("time"),
            }
        )
    _require(bool(cases), f"empty {label} JUnit")
    keys = [(case["classname"], case["name"]) for case in cases]
    _require(len(keys) == len(set(keys)), f"duplicate {label} JUnit identity")
    for suite in suites:
        children = list(suite.findall("testcase"))
        counts = {"tests": len(children)}
        counts.update(
            {
                plural: sum(case.find(singular) is not None for case in children)
                for plural, singular in (
                    ("failures", "failure"),
                    ("errors", "error"),
                    ("skipped", "skipped"),
                )
            }
        )
        for field, count in counts.items():
            _require(
                suite.get(field) == str(count),
                f"{label} declared {field} count disagrees",
            )
    return cases


def coverage_evidence(data: bytes) -> dict[str, Any]:
    tree = _xml(data, "coverage")
    _require(tree.tag == "coverage", "unknown coverage root")
    try:
        covered, valid = (
            int(tree.attrib["lines-covered"]),
            int(tree.attrib["lines-valid"]),
        )
        rate_text = tree.attrib["line-rate"]
        _require(len(rate_text) <= 80, "oversized coverage rate")
        rate = Decimal(rate_text)
        _require(valid > 0 and 0 <= covered <= valid, "invalid coverage counts")
        _require(rate.is_finite() and 0 <= rate <= 1, "invalid coverage rate")
        _require(
            -16 <= rate.as_tuple().exponent <= 0, "unsupported coverage serialization"
        )
        with localcontext(Context(prec=80, rounding=ROUND_HALF_EVEN)):
            expected = (Decimal(covered) / Decimal(valid)).quantize(
                Decimal(1).scaleb(rate.as_tuple().exponent)
            )
        _require(expected == rate, "coverage counts and declared rate disagree")
    except (KeyError, ValueError, InvalidOperation) as exc:
        raise AcceptanceError(f"invalid coverage: {exc}") from exc
    return {
        "covered": covered,
        "valid": valid,
        "line_rate": rate_text,
        "floor_passed": covered * 100 >= valid * 89,
    }


def _validator_python_diagnostic(
    approved: dict[str, Any], actual: list[int]
) -> str | None:
    """Report an exact sealed runtime mismatch without normalizing either input."""
    sealed = approved.get("validator_python")
    if (
        type(sealed) is list
        and len(sealed) == 3
        and all(type(value) is int for value in sealed)
        and sealed == actual
    ):
        return None
    return (
        f"sealed validator_python={json.dumps(sealed)} differs from "
        f"actual validator_python={json.dumps(actual)}; use the exact sealed "
        "interpreter. Fresh collection will still be retained; this diagnostic "
        "does not establish that runtime is the only difference."
    )


def validate_payloads(
    approved: dict[str, Any],
    fresh: dict[str, Any],
    parallel: bytes,
    chrome: bytes,
    coverage: bytes,
) -> dict[str, Any]:
    """Validate immutable payloads; tests exercise adversarial membership inputs."""
    _require(
        approved == fresh, "approved collection does not match fresh current collection"
    )
    nodeids = approved.get("nodeids")
    _require(
        isinstance(nodeids, list)
        and bool(nodeids)
        and all(isinstance(nodeid, str) for nodeid in nodeids),
        "empty or malformed approved membership",
    )
    _require(len(nodeids) == len(set(nodeids)), "duplicate approved node ID")
    _require(
        set(LIVE_NODE_IDS + CONTROL_NODE_IDS) <= set(nodeids),
        "required eight cases absent from approved membership",
    )
    expected = {junit_identity(nodeid): nodeid for nodeid in nodeids}
    _require(len(expected) == len(nodeids), "ambiguous approved membership")
    parallel_cases, chrome_cases = (
        _cases(parallel, "parallel"),
        _cases(chrome, "Chrome"),
    )
    live_keys = {junit_identity(nodeid) for nodeid in LIVE_NODE_IDS}
    parallel_keys = {(case["classname"], case["name"]) for case in parallel_cases}
    chrome_keys = {(case["classname"], case["name"]) for case in chrome_cases}
    _require(
        chrome_keys == live_keys,
        "Chrome component must contain exactly the two canonical cases",
    )
    _require(
        parallel_keys == set(expected) - live_keys,
        "parallel component has missing or unknown cases",
    )
    _require(not parallel_keys & chrome_keys, "case executed in both components")
    all_cases = parallel_cases + chrome_cases
    _require(
        len(all_cases) == len(nodeids),
        "split union count disagrees with approved membership",
    )
    outcomes = {(case["classname"], case["name"]): case for case in all_cases}
    signals = [
        {"nodeid": nodeid, **outcomes[junit_identity(nodeid)]}
        for nodeid in LIVE_NODE_IDS + CONTROL_NODE_IDS
    ]
    counts = Counter(case["outcome"] for case in all_cases)
    cover = coverage_evidence(coverage)
    required_passed = all(case["outcome"] == "passed" for case in signals)
    passed = (
        not counts["failure"]
        and not counts["error"]
        and required_passed
        and cover["floor_passed"]
    )
    return {
        "schema_version": 1,
        "status": "passed" if passed else "failed",
        "total_cases": len(all_cases),
        "parallel_cases": len(parallel_cases),
        "chrome_cases": len(chrome_cases),
        "counts": {
            key: counts[key] for key in ("passed", "failure", "error", "skipped")
        },
        "coverage": cover,
        "required_eight_passed_no_skip": required_passed,
        "required_signals": signals,
        "skipped_cases": [case for case in all_cases if case["outcome"] == "skipped"],
        "nonpass_cases": [
            case for case in all_cases if case["outcome"] in {"failure", "error"}
        ],
        "input_sha256": {
            "parallel_junit": _sha(parallel),
            "chrome_junit": _sha(chrome),
            "coverage": _sha(coverage),
        },
        "collection_source_sha256": approved["source_sha256"],
        "scope": "Exact split non-serial suite union and aggregate coverage data. Actual same-run commands/exits and coverage reset/append require reviewed CI provenance; hosted exact-main, production capture and prior startup causality remain separate.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument("--collect", type=Path)
    parser.add_argument("--collection", type=Path)
    parser.add_argument("--parallel-junit", type=Path)
    parser.add_argument("--chrome-junit", type=Path)
    parser.add_argument("--coverage", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--_collect-worker", action="store_true", help=argparse.SUPPRESS
    )
    args = parser.parse_args(argv)
    root = args.project_root.resolve()
    protected = tuple(
        value
        for value in (
            args.collection,
            args.parallel_junit,
            args.chrome_junit,
            args.coverage,
        )
        if value is not None
    )
    try:
        _require(
            sys.version_info[:2] == (3, 14), "Python 3.14 is the accepted validator"
        )
        if args._collect_worker:
            print(json.dumps(_collection_worker(root)))
            return 0
        validation_paths = (
            args.collection,
            args.parallel_junit,
            args.chrome_junit,
            args.coverage,
            args.output,
        )
        if args.collect:
            _require(
                not any(validation_paths),
                "collection and validation modes cannot be mixed",
            )
            _regular_path(root, args.collect, output=True)
            result = collect(root)
            _write(root, args.collect, result)
            print(f"Collected {len(result['nodeids'])} exact non-serial node IDs")
            return 0
        _require(
            all(validation_paths),
            "validation requires collection, both JUnit files, coverage and output",
        )
        _output_path(root, args.output, protected)
        paths = [_regular_path(root, path) for path in validation_paths[:-1]]
        inputs = [path.read_bytes() for path in paths]
        approved = _load_json(inputs[0])
        fresh_path = args.output.with_name(args.output.name + ".fresh-collection.json")
        worker_path = args.output.with_name(
            args.output.name + ".collection-worker.json"
        )
        _output_path(root, fresh_path, protected + (args.output, worker_path))
        _output_path(root, worker_path, protected + (args.output, fresh_path))
        version_error = _validator_python_diagnostic(
            approved, list(sys.version_info[:3])
        )
        if version_error is not None:
            print(version_error, file=sys.stderr)
        fresh = collect(
            root,
            observation=worker_path,
            protected=protected + (args.output, fresh_path),
        )
        _write(
            root,
            fresh_path,
            fresh,
            protected=protected + (args.output, worker_path),
        )
        _require(version_error is None, version_error or "")
        result = validate_payloads(approved, fresh, *inputs[1:])
        _require(
            all(
                path.read_bytes() == data
                for path, data in zip(paths, inputs, strict=True)
            ),
            "acceptance inputs changed during validation",
        )
        result["input_sha256"]["collection"] = _sha(inputs[0])
        _write(root, args.output, result, protected=protected)
        print(
            json.dumps(
                {
                    key: result[key]
                    for key in (
                        "status",
                        "total_cases",
                        "counts",
                        "required_eight_passed_no_skip",
                        "coverage",
                    )
                }
            )
        )
        return int(result["status"] != "passed")
    except (
        AcceptanceError,
        OSError,
        json.JSONDecodeError,
        subprocess.SubprocessError,
    ) as exc:
        failure = {"schema_version": 1, "status": "failed", "errors": [str(exc)]}
        if args.output:
            with suppress(AcceptanceError, OSError):
                _write(root, args.output, failure, protected=protected)
        print(json.dumps(failure), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
