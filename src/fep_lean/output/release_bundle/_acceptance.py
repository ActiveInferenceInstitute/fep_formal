"""Python acceptance runner, receipt validation, and numerical witnesses."""

import importlib.metadata
import math
import os
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from collections import Counter
from collections.abc import (
    Mapping,
    Sequence,
)
from pathlib import (
    Path,
    PurePosixPath,
)
from typing import Any

import yaml

from fep_lean.output import release_bundle as bundle
from fep_lean.output.formalism_presentation import RELEASE_SEAL
from fep_lean.output.fsutil import (
    atomic_write_bytes,
    sha256_bytes,
    sha256_file,
)
from fep_lean.output.manuscript import (
    parse_pytest_collection_stdout,
    pytest_collection_command,
    pytest_collection_environment,
)
from fep_lean.output.release_bundle._constants import (
    _PYTHON_ACCEPTANCE_ARGUMENTS,
    _PYTHON_ACCEPTANCE_DISTRIBUTIONS,
    _PYTHON_ACCEPTANCE_EXPLICIT_PLUGINS,
    _PYTHON_ACCEPTANCE_EXTERNAL_TOOLS,
    _PYTHON_ACCEPTANCE_TIMEOUT_SECONDS,
    _PYTHON_ACCEPTANCE_USER_FONT_DIRECTORIES,
    NUMERICAL_RECEIPT,
    PYTEST_RECEIPT,
    PYTHON_ACCEPTANCE_RECEIPT,
    PYTHON_COVERAGE_RECEIPT,
)
from fep_lean.output.release_bundle._core import (
    ReleaseBundleError,
    _canonical_json,
    _digest_named_bytes,
    _json_object,
    _relative_file_bytes,
)
from fep_lean.verification.numerical_witnesses import (
    NON_PROOF_EVIDENCE,
    evaluate_numerical_witnesses,
)


def _junit_identity_from_node_id(node_id: str) -> tuple[str, str]:
    address, parameter_open, parameters = node_id.partition("[")
    path, *scopes = address.split("::")
    names = [
        PurePosixPath(path).with_suffix("").as_posix().replace("/", "."),
        *scopes,
    ]
    names[-1] += parameter_open + parameters
    return ".".join(names[:-1]), names[-1]


def _canonical_python_source_records(
    project_root: Path,
) -> tuple[tuple[str, bytes], ...]:
    root = Path(project_root).resolve()
    source_root = root / "src"
    if source_root.is_symlink() or not source_root.is_dir():
        raise ReleaseBundleError("canonical Python source tree is missing or a symlink")
    records: list[tuple[str, bytes]] = []
    for path in sorted(source_root.rglob("*.py")):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink() or not path.is_file():
            raise ReleaseBundleError(
                f"canonical Python source is not a regular file: {relative}"
            )
        records.append((relative, _relative_file_bytes(root, relative)))
    if not records:
        raise ReleaseBundleError("canonical Python source tree is empty")
    return tuple(records)


def _canonical_coverage_path(filename: str) -> str | None:
    if "\\" in filename:
        return None
    path = PurePosixPath(filename)
    if path.is_absolute() or not path.parts or ".." in path.parts:
        return None
    if path.parts[0] != "src":
        path = PurePosixPath("src") / path
    return path.as_posix()


def _pytest_receipt_errors(
    project_root: Path,
    *,
    expected_node_ids: Sequence[str] | None = None,
) -> tuple[str, ...]:
    root_path = Path(project_root)
    path = root_path / PYTEST_RECEIPT
    try:
        junit_root = ET.fromstring(path.read_bytes())
    except (OSError, ET.ParseError) as exc:
        return (f"cannot read Python test receipt: {exc}",)
    suites = (
        [junit_root]
        if junit_root.tag == "testsuite"
        else list(junit_root.findall("testsuite"))
    )
    if not suites:
        return ("Python test receipt contains no test suites",)
    try:
        tests = sum(int(suite.get("tests", "0")) for suite in suites)
        failures = sum(int(suite.get("failures", "0")) for suite in suites)
        errors = sum(int(suite.get("errors", "0")) for suite in suites)
        skipped = sum(int(suite.get("skipped", "0")) for suite in suites)
    except ValueError:
        return ("Python test receipt contains non-integer counters",)
    receipt_errors: list[str] = []
    if tests <= 0:
        receipt_errors.append("Python test receipt contains no tests")
    if failures or errors:
        receipt_errors.append(
            f"Python test receipt is not green: failures={failures}, errors={errors}",
        )
    if skipped >= tests:
        receipt_errors.append("Python test receipt contains no executed tests")
    testcases = list(junit_root.iter("testcase"))
    testcase_failures = sum(
        testcase.find("failure") is not None for testcase in testcases
    )
    testcase_errors = sum(testcase.find("error") is not None for testcase in testcases)
    testcase_skipped = sum(
        testcase.find("skipped") is not None for testcase in testcases
    )
    if (
        len(testcases),
        testcase_failures,
        testcase_errors,
        testcase_skipped,
    ) != (tests, failures, errors, skipped):
        receipt_errors.append(
            "Python test receipt testcase records disagree with suite counters"
        )
    for testcase in testcases:
        classname = testcase.get("classname")
        name = testcase.get("name")
        try:
            duration = float(testcase.get("time", "nan"))
        except ValueError:
            duration = math.nan
        if (
            not isinstance(classname, str)
            or not classname
            or not isinstance(name, str)
            or not name
            or not math.isfinite(duration)
            or duration < 0
        ):
            receipt_errors.append("Python test receipt contains an invalid testcase")
            break
    if expected_node_ids is not None:
        expected_testcases = Counter(
            _junit_identity_from_node_id(node_id) for node_id in expected_node_ids
        )
        observed_testcases = Counter(
            (testcase.get("classname", ""), testcase.get("name", ""))
            for testcase in testcases
        )
        if observed_testcases != expected_testcases:
            receipt_errors.append(
                "Python test receipt testcase roster differs from live collection"
            )
    try:
        manuscript_vars = yaml.safe_load(
            (root_path / "manuscript" / "manuscript_vars.yaml").read_text(
                encoding="utf-8"
            )
        )
        expected_tests = manuscript_vars["tests"]["collected"]
    except (KeyError, OSError, TypeError, yaml.YAMLError):
        receipt_errors.append("cannot resolve the canonical collected-test count")
    else:
        if type(expected_tests) is not int or expected_tests <= 0:
            receipt_errors.append("canonical collected-test count must be positive")
        elif tests != expected_tests:
            receipt_errors.append(
                "Python test receipt count differs from the canonical test roster: "
                f"receipt={tests}, canonical={expected_tests}"
            )

    coverage_path = root_path / PYTHON_COVERAGE_RECEIPT
    try:
        coverage = ET.fromstring(coverage_path.read_bytes())
        line_rate = float(coverage.get("line-rate", "nan"))
        lines_valid = int(coverage.get("lines-valid", "0"))
        lines_covered = int(coverage.get("lines-covered", "0"))
    except (OSError, ET.ParseError, TypeError, ValueError) as exc:
        receipt_errors.append(f"cannot read Python coverage receipt: {exc}")
    else:
        if coverage.tag != "coverage":
            receipt_errors.append("Python coverage receipt root must be coverage")
        if not (0.0 <= line_rate <= 1.0):
            receipt_errors.append("Python coverage line-rate must be finite in [0, 1]")
        elif line_rate < 0.89:
            receipt_errors.append(
                f"Python coverage line-rate {line_rate:.4f} is below 0.8900"
            )
        if lines_valid <= 0 or lines_covered < 0 or lines_covered > lines_valid:
            receipt_errors.append("Python coverage line counters are invalid")
        else:
            counter_rate = lines_covered / lines_valid
            if counter_rate < 0.89:
                receipt_errors.append(
                    "Python coverage counter-derived line-rate is below 0.8900"
                )
            if abs(counter_rate - line_rate) > 0.0001:
                receipt_errors.append(
                    "Python coverage line-rate disagrees with its line counters"
                )
        coverage_classes = list(coverage.iter("class"))
        coverage_lines = list(coverage.iter("line"))
        if not coverage_classes or not coverage_lines:
            receipt_errors.append(
                "Python coverage receipt contains no executable line records"
            )
        else:
            try:
                observed_lines = len(coverage_lines)
                observed_covered = sum(
                    int(line.get("hits", "-1")) > 0 for line in coverage_lines
                )
                invalid_lines = any(
                    int(line.get("number", "0")) <= 0 or int(line.get("hits", "-1")) < 0
                    for line in coverage_lines
                )
            except ValueError:
                invalid_lines = True
                observed_lines = -1
                observed_covered = -1
            if invalid_lines:
                receipt_errors.append(
                    "Python coverage receipt contains an invalid line record"
                )
            elif (observed_lines, observed_covered) != (
                lines_valid,
                lines_covered,
            ):
                receipt_errors.append(
                    "Python coverage line records disagree with aggregate counters"
                )
        try:
            source_records = _canonical_python_source_records(root_path)
        except ReleaseBundleError as exc:
            receipt_errors.append(str(exc))
        else:
            expected_sources = {name for name, _data in source_records}
            observed_sources = [
                _canonical_coverage_path(node.get("filename", ""))
                for node in coverage_classes
            ]
            if (
                None in observed_sources
                or len(observed_sources) != len(set(observed_sources))
                or set(observed_sources) != expected_sources
            ):
                receipt_errors.append(
                    "Python coverage source roster differs from canonical Python sources"
                )
            source_by_name = dict(source_records)
            for node, relative in zip(coverage_classes, observed_sources, strict=True):
                if relative not in source_by_name:
                    continue
                line_count = len(source_by_name[relative].splitlines())
                try:
                    line_numbers = [
                        int(line.get("number", "0")) for line in node.iter("line")
                    ]
                except ValueError:
                    receipt_errors.append(
                        "Python coverage receipt contains an invalid line record"
                    )
                    break
                if len(line_numbers) != len(set(line_numbers)) or any(
                    number > line_count for number in line_numbers
                ):
                    receipt_errors.append(
                        "Python coverage line records do not belong to canonical sources"
                    )
                    break
    return tuple(receipt_errors)


def build_numerical_witness_receipt(project_root: Path) -> bytes:
    """Serialize the live typed numerical checks as explanatory evidence."""
    root = Path(project_root).resolve()
    witnesses = evaluate_numerical_witnesses(project_root=root, scope="catalogue")
    records: list[dict[str, Any]] = []
    for witness in witnesses:
        records.append(
            {
                "id": witness.id,
                "family": witness.family,
                "title": witness.title,
                "theorem_mirrors": list(witness.theorem_mirrors),
                "invariant": witness.invariant,
                "parameters": [
                    {"name": name, "value": value} for name, value in witness.parameters
                ],
                "columns": [
                    {"key": column.key, "label": column.label}
                    for column in witness.columns
                ],
                "rows": [list(row.values) for row in witness.rows],
                "checks": [
                    {
                        "id": check.id,
                        "relation": check.relation,
                        "lhs": check.lhs,
                        "rhs": check.rhs,
                        "tolerance": check.tolerance,
                        "residual": check.residual,
                        "accepted": check.accepted,
                    }
                    for check in witness.checks
                ],
                "boundary_behavior": witness.boundary_behavior,
                "boundary_observed": witness.boundary_observed,
                "plot": {
                    "kind": witness.plot.kind,
                    "x_key": witness.plot.x_key,
                    "y_keys": list(witness.plot.y_keys),
                },
                "formal_alignment": witness.formal_alignment,
                "evidence_kind": witness.evidence_kind,
                "accepted": witness.accepted,
            }
        )
    payload = {
        "schema_version": 1,
        "kind": "numerical-witness-receipt",
        "evidence_kind": NON_PROOF_EVIDENCE,
        "complete": bool(records) and all(record["accepted"] for record in records),
        "witness_count": len(records),
        "check_count": sum(len(record["checks"]) for record in records),
        "source_sha256": bundle.report_source_digest(root),
        "config_sha256": bundle.report_config_digest(root),
        "witnesses": records,
    }
    if (
        payload["witness_count"] != RELEASE_SEAL["witnesses"]
        or payload["complete"] is not True
    ):
        raise ReleaseBundleError(
            f"the live numerical witness closure is not the accepted "
            f"{RELEASE_SEAL['witnesses']}-witness release"
        )
    return _canonical_json(payload)


def write_numerical_witnesses(project_root: Path) -> Path:
    """Build the live numerical-witness receipt and atomically retain it."""
    root = Path(project_root).resolve()
    destination = root / NUMERICAL_RECEIPT
    if (root / "output").is_symlink():
        raise ReleaseBundleError("numerical witness output directory is a symlink")
    if destination.is_symlink() or (destination.exists() and not destination.is_file()):
        raise ReleaseBundleError("numerical witness destination is not a regular file")
    try:
        data = bundle.build_numerical_witness_receipt(root)
    except OSError as exc:
        raise ReleaseBundleError(
            f"cannot build numerical witness receipt: {exc}"
        ) from exc
    try:
        atomic_write_bytes(destination, data)
    except OSError as exc:
        raise ReleaseBundleError(
            f"cannot write numerical witness receipt: {exc}"
        ) from exc
    return destination


def _python_test_records(project_root: Path) -> tuple[tuple[str, bytes], ...]:
    """Capture the complete maintained test tree without generated caches."""
    root = Path(project_root).resolve()
    test_root = root / "tests"
    if test_root.is_symlink() or not test_root.is_dir():
        raise ReleaseBundleError("canonical Python test tree is missing or a symlink")
    records: list[tuple[str, bytes]] = []
    for path in sorted(test_root.rglob("*")):
        relative = path.relative_to(root)
        if path.is_symlink():
            raise ReleaseBundleError(
                f"canonical Python test tree contains a symlink: {relative.as_posix()}"
            )
        if "__pycache__" in relative.parts or path.suffix in {".pyc", ".pyo"}:
            continue
        if path.is_file():
            name = relative.as_posix()
            records.append((name, _relative_file_bytes(root, name)))
    if not records:
        raise ReleaseBundleError("canonical Python test tree is empty")
    return tuple(records)


def _distribution_fingerprint(distribution_name: str) -> dict[str, str]:
    try:
        distribution = importlib.metadata.distribution(distribution_name)
    except importlib.metadata.PackageNotFoundError as exc:
        raise ReleaseBundleError(
            f"required Python acceptance distribution is missing: {distribution_name}"
        ) from exc
    selected: list[tuple[str, bytes]] = []
    for relative in distribution.files or ():
        relative_path = PurePosixPath(str(relative))
        if relative_path.suffix not in {
            ".py",
            ".so",
            ".pyd",
        } and relative_path.name not in {
            "METADATA",
            "entry_points.txt",
        }:
            continue
        path = Path(str(distribution.locate_file(relative)))
        if not path.is_file():
            raise ReleaseBundleError(
                "Python acceptance distribution file is missing: "
                f"{distribution_name}:{relative_path.as_posix()}"
            )
        selected.append((relative_path.as_posix(), path.read_bytes()))
    if not selected:
        raise ReleaseBundleError(
            f"Python acceptance distribution has no fingerprinted files: {distribution_name}"
        )
    return {
        "version": distribution.version,
        "files_sha256": _digest_named_bytes(selected),
    }


def _normalized_python_acceptance_command() -> list[str]:
    return [
        sys.executable,
        "-m",
        "pytest",
        *(
            argument
            for plugin in _PYTHON_ACCEPTANCE_EXPLICIT_PLUGINS
            for argument in ("-p", plugin)
        ),
        "-o",
        "cache_dir=<temporary>",
        *_PYTHON_ACCEPTANCE_ARGUMENTS,
    ]


def _python_acceptance_command(cache_dir: Path) -> list[str]:
    command = _normalized_python_acceptance_command()
    command[command.index("cache_dir=<temporary>")] = f"cache_dir={cache_dir}"
    return command


def _python_acceptance_external_executable(name: str) -> dict[str, str]:
    found = shutil.which(name)
    if found is None:
        raise ReleaseBundleError(
            f"required Python acceptance executable is missing: {name}"
        )
    path = Path(found).resolve()
    if not path.is_file():
        raise ReleaseBundleError(
            f"Python acceptance executable is not a regular file: {name}"
        )
    return {"path": path.as_posix(), "sha256": sha256_file(path)}


def _controlled_python_acceptance_path(uv_path: str, tool_bin: str = "") -> str:
    directories = [Path(sys.executable).resolve().parent.as_posix()]
    directories.append(Path(uv_path).parent.as_posix())
    if tool_bin:
        directories.append(tool_bin)
    directories.extend(os.defpath.split(os.pathsep))
    return os.pathsep.join(dict.fromkeys(path for path in directories if path))


def _python_acceptance_tool_bin(temporary_root: Path) -> Path:
    """Materialize the allowlisted external tools under the temporary root.

    One symlink per allowlisted executable keeps the carried set exact: adding
    an upstream bin directory wholesale would expose every other tool it
    holds. The links point at the resolved real executable, so the recorded
    identity is stable while the temporary directory is not.
    """
    tool_bin = temporary_root / "acceptance-tool-bin"
    tool_bin.mkdir(exist_ok=True)
    for name in _PYTHON_ACCEPTANCE_EXTERNAL_TOOLS:
        link = tool_bin / name
        if link.is_symlink() or link.exists():
            link.unlink()
        os.symlink(_python_acceptance_external_executable(name)["path"], link)
    return tool_bin


def _python_acceptance_home_font_mirrors(temporary_root: Path) -> None:
    """Mirror the host's user font directories under the redirected HOME.

    The collection policy redirects HOME for isolation, and the host's
    fontconfig configuration resolves user fonts under ``$HOME`` (``~/.fonts``,
    ``~/.local/share/fonts``, ``~/Library/Fonts``). Left alone, the redirected
    HOME would make every user-installed face invisible to the face-coverage
    lanes exactly when they must verify this render host. System font
    directories are absolute in the host's configuration and need no mirror.
    """
    home = temporary_root / "home"
    real_home = Path.home()
    for relative in _PYTHON_ACCEPTANCE_USER_FONT_DIRECTORIES:
        source = real_home / relative
        if not source.is_dir():
            continue
        target = home / relative
        if target.is_symlink() or target.exists():
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        os.symlink(source, target)


def _python_acceptance_tool_identity() -> dict[str, dict[str, str]]:
    return {
        name: _python_acceptance_external_executable(name)
        for name in ("uv", *_PYTHON_ACCEPTANCE_EXTERNAL_TOOLS)
    }


def _python_acceptance_environment(temporary_root: Path) -> dict[str, str]:
    environment = pytest_collection_environment(temporary_root)
    environment["COVERAGE_FILE"] = str(temporary_root / ".coverage")
    _python_acceptance_home_font_mirrors(temporary_root)
    uv_identity = _python_acceptance_external_executable("uv")
    tool_bin = _python_acceptance_tool_bin(temporary_root)
    environment["PATH"] = _controlled_python_acceptance_path(
        uv_identity["path"], tool_bin.as_posix()
    )
    return environment


def _python_acceptance_runtime_identity() -> dict[str, Any]:
    collection_identity = bundle.collection_runtime_identity()
    identity: dict[str, Any] = {
        "environment": {
            **collection_identity["environment"],
            "COVERAGE_FILE": "<temporary>/.coverage",
            "PATH": _controlled_python_acceptance_path(
                _python_acceptance_external_executable("uv")["path"],
                "<temporary>/acceptance-tool-bin",
            ),
        },
        "external_executables": _python_acceptance_tool_identity(),
        "explicit_plugins": list(_PYTHON_ACCEPTANCE_EXPLICIT_PLUGINS),
        "interpreter": collection_identity["interpreter"],
        "plugin_distributions": {
            name: _distribution_fingerprint(name)
            for name in _PYTHON_ACCEPTANCE_DISTRIBUTIONS
        },
        "pytest_arguments": _normalized_python_acceptance_command()[3:],
    }
    identity["fingerprint_sha256"] = sha256_bytes(_canonical_json(identity))
    return identity


def _collect_python_node_ids(
    project_root: Path, temporary_root: Path
) -> tuple[str, ...]:
    command = pytest_collection_command(temporary_root / "pytest-cache")
    try:
        completed = subprocess.run(
            command,
            cwd=project_root,
            env=pytest_collection_environment(temporary_root),
            check=False,
            capture_output=True,
            text=True,
            timeout=_PYTHON_ACCEPTANCE_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise ReleaseBundleError(
            f"cannot collect canonical Python tests: {exc}"
        ) from exc
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()
        raise ReleaseBundleError(
            "canonical Python test collection failed"
            + (f": {detail}" if detail else "")
        )
    try:
        return parse_pytest_collection_stdout(completed.stdout)
    except ValueError as exc:
        raise ReleaseBundleError(
            f"canonical Python test collection is invalid: {exc}"
        ) from exc


def _python_input_snapshot(project_root: Path) -> dict[str, Any]:
    root = Path(project_root).resolve()
    test_records = _python_test_records(root)
    test_count_owner = _relative_file_bytes(root, "manuscript/manuscript_vars.yaml")
    snapshot: dict[str, Any] = {
        "source_sha256": bundle.report_source_digest(root),
        "config_sha256": bundle.report_config_digest(root),
        "test_tree_sha256": _digest_named_bytes(test_records),
        "test_file_count": len(test_records),
        "test_count_owner_sha256": sha256_bytes(test_count_owner),
    }
    snapshot["fingerprint_sha256"] = sha256_bytes(_canonical_json(snapshot))
    return snapshot


def _python_evidence_summary(project_root: Path) -> dict[str, Any]:
    """Summarize already validated JUnit and Cobertura evidence."""
    root = Path(project_root).resolve()
    junit_data = _relative_file_bytes(root, PYTEST_RECEIPT.as_posix())
    coverage_data = _relative_file_bytes(root, PYTHON_COVERAGE_RECEIPT.as_posix())
    junit_root = ET.fromstring(junit_data)
    suites = (
        [junit_root]
        if junit_root.tag == "testsuite"
        else list(junit_root.findall("testsuite"))
    )
    tests = sum(int(suite.get("tests", "0")) for suite in suites)
    failures = sum(int(suite.get("failures", "0")) for suite in suites)
    receipt_errors = sum(int(suite.get("errors", "0")) for suite in suites)
    skipped = sum(int(suite.get("skipped", "0")) for suite in suites)
    duration = sum(float(suite.get("time", "0")) for suite in suites)
    coverage = ET.fromstring(coverage_data)
    source_by_name = dict(_canonical_python_source_records(root))
    coverage_records: list[dict[str, Any]] = []
    for node in coverage.iter("class"):
        relative = _canonical_coverage_path(node.get("filename", ""))
        if relative not in source_by_name:
            raise ReleaseBundleError(
                "Python coverage source roster differs from canonical Python sources"
            )
        coverage_records.append(
            {
                "path": relative,
                "source_sha256": sha256_bytes(source_by_name[relative]),
                "lines": [
                    {
                        "number": int(line.get("number", "0")),
                        "hits": int(line.get("hits", "-1")),
                    }
                    for line in node.iter("line")
                ],
            }
        )
    coverage_records.sort(key=lambda record: str(record["path"]))
    return {
        "tests": {
            "collected": tests,
            "passed": tests - failures - receipt_errors - skipped,
            "skipped": skipped,
            "failures": failures,
            "errors": receipt_errors,
            "duration_seconds": duration,
            "junit_path": PYTEST_RECEIPT.as_posix(),
            "junit_sha256": sha256_bytes(junit_data),
        },
        "coverage": {
            "line_rate": float(coverage.get("line-rate", "nan")),
            "floor": 0.89,
            "lines_valid": int(coverage.get("lines-valid", "0")),
            "lines_covered": int(coverage.get("lines-covered", "0")),
            "path": PYTHON_COVERAGE_RECEIPT.as_posix(),
            "sha256": sha256_bytes(coverage_data),
            "source_records": coverage_records,
        },
    }


def _python_acceptance_receipt_errors(project_root: Path) -> tuple[str, ...]:
    root = Path(project_root).resolve()
    errors: list[str] = []
    live_node_ids: tuple[str, ...] | None = None
    current_collection: dict[str, Any] | None = None
    current_executor: dict[str, Any] | None = None
    try:
        with tempfile.TemporaryDirectory(
            prefix="fep-lean-pytest-check-"
        ) as raw_directory:
            live_node_ids = bundle._collect_python_node_ids(root, Path(raw_directory))
        current_collection = bundle.collection_runtime_identity()
        current_executor = bundle._python_acceptance_runtime_identity()
    except (OSError, TypeError, ValueError, ReleaseBundleError) as exc:
        errors.append(f"Python acceptance runtime cannot be validated: {exc}")
    errors.extend(
        bundle._pytest_receipt_errors(root, expected_node_ids=live_node_ids)
        if live_node_ids is not None
        else bundle._pytest_receipt_errors(root)
    )
    path = root / PYTHON_ACCEPTANCE_RECEIPT
    payload, error = _json_object(path, "Python acceptance receipt")
    if payload is None:
        errors.append(error or "Python acceptance receipt is invalid")
        return tuple(dict.fromkeys(errors))
    try:
        receipt_data = _relative_file_bytes(root, PYTHON_ACCEPTANCE_RECEIPT.as_posix())
        current_inputs = bundle._python_input_snapshot(root)
        summary = bundle._python_evidence_summary(root)
    except (OSError, TypeError, ValueError, ET.ParseError) as exc:
        errors.append(f"Python acceptance receipt cannot be validated: {exc}")
        return tuple(dict.fromkeys(errors))
    if receipt_data != _canonical_json(payload):
        errors.append("Python acceptance receipt is not canonical sorted JSON")
    if payload.get("schema_version") != 3:
        errors.append("Python acceptance receipt schema_version must be 3")
    if payload.get("kind") != "python-acceptance-receipt":
        errors.append("Python acceptance receipt kind is invalid")
    if payload.get("complete") is not True or payload.get("returncode") != 0:
        errors.append("Python acceptance receipt is not complete and green")
    if payload.get("command") != _normalized_python_acceptance_command():
        errors.append("Python acceptance receipt command is not canonical")
    if current_executor is not None and payload.get("executor") != current_executor:
        errors.append("Python acceptance receipt executor identity is stale")
    collection = payload.get("collection")
    if not isinstance(collection, dict):
        errors.append("Python acceptance receipt collection evidence is invalid")
    else:
        if current_collection is not None and collection.get("command") != [
            sys.executable,
            "-m",
            "pytest",
            *current_collection["pytest_arguments"],
        ]:
            errors.append(
                "Python acceptance receipt collection command is not canonical"
            )
        if live_node_ids is not None and collection.get("node_ids") != list(
            live_node_ids
        ):
            errors.append("Python acceptance receipt collected node IDs are stale")
    inputs = payload.get("inputs")
    if not isinstance(inputs, dict) or set(inputs) != {"before", "after", "stable"}:
        errors.append("Python acceptance receipt input snapshots are invalid")
    else:
        before = inputs.get("before")
        after = inputs.get("after")
        if inputs.get("stable") is not True or before != after:
            errors.append("Python acceptance receipt input snapshots are not stable")
        if after != current_inputs:
            errors.append("Python acceptance receipt input snapshot is stale")
    if payload.get("tests") != summary["tests"]:
        errors.append("Python acceptance receipt JUnit summary or hash is stale")
    if payload.get("coverage") != summary["coverage"]:
        errors.append("Python acceptance receipt coverage summary or hash is stale")
    try:
        if current_inputs != bundle._python_input_snapshot(root):
            errors.append("Python acceptance inputs changed during validation")
        if current_executor != bundle._python_acceptance_runtime_identity():
            errors.append("Python acceptance executor changed during validation")
    except (OSError, TypeError, ValueError, ReleaseBundleError) as exc:
        errors.append(f"Python acceptance runtime cannot be revalidated: {exc}")
    return tuple(dict.fromkeys(errors))


def build_python_acceptance_receipt(project_root: Path) -> bytes:
    """Return the current receipt created by :func:`run_python_acceptance`."""
    root = Path(project_root).resolve()
    errors = _python_acceptance_receipt_errors(root)
    if errors:
        raise ReleaseBundleError(
            "Python acceptance receipts are not claim-ready:\n" + "\n".join(errors)
        )
    return _relative_file_bytes(root, PYTHON_ACCEPTANCE_RECEIPT.as_posix())


def _restore_python_acceptance_files(
    prior: Mapping[Path, bytes | None],
) -> tuple[str, ...]:
    errors: list[str] = []
    for path, data in prior.items():
        try:
            if data is None:
                path.unlink(missing_ok=True)
            else:
                atomic_write_bytes(path, data)
        except OSError as exc:
            errors.append(f"{path}: {exc}")
    return tuple(errors)


def run_python_acceptance(project_root: Path) -> Path:
    """Run the canonical suite once and atomically retain its bound receipts."""
    root = Path(project_root).resolve()
    output_root = root / "output"
    if output_root.is_symlink():
        raise ReleaseBundleError("Python acceptance output directory is a symlink")
    output_root.mkdir(parents=True, exist_ok=True)
    if not output_root.resolve().is_relative_to(root):
        raise ReleaseBundleError(
            "Python acceptance output directory escapes project root"
        )
    owned_paths = tuple(
        root / relative
        for relative in (
            PYTEST_RECEIPT,
            PYTHON_COVERAGE_RECEIPT,
            PYTHON_ACCEPTANCE_RECEIPT,
        )
    )
    for path in owned_paths:
        if path.is_symlink() or (path.exists() and not path.is_file()):
            raise ReleaseBundleError(
                "Python acceptance destination is not a regular file: "
                f"{path.relative_to(root).as_posix()}"
            )
    prior = {
        path: path.read_bytes() if path.is_file() else None for path in owned_paths
    }
    before = bundle._python_input_snapshot(root)
    try:
        executor_before = bundle._python_acceptance_runtime_identity()
        collection_identity = bundle.collection_runtime_identity()
        with tempfile.TemporaryDirectory(prefix="fep-lean-pytest-") as raw:
            temporary_root = Path(raw)
            node_ids = bundle._collect_python_node_ids(root, temporary_root)
            command = _python_acceptance_command(temporary_root / "pytest-cache")
            completed = subprocess.run(
                command,
                cwd=root,
                env=bundle._python_acceptance_environment(temporary_root),
                check=False,
                capture_output=True,
                text=True,
                timeout=_PYTHON_ACCEPTANCE_TIMEOUT_SECONDS,
            )
            if completed.returncode != 0:
                detail = (completed.stderr or completed.stdout).strip()
                raise ReleaseBundleError(
                    "canonical Python acceptance command failed"
                    + (f": {detail}" if detail else "")
                )
        receipt_errors = bundle._pytest_receipt_errors(root, expected_node_ids=node_ids)
        if receipt_errors:
            raise ReleaseBundleError(
                "canonical Python acceptance evidence is invalid:\n"
                + "\n".join(receipt_errors)
            )
        after = bundle._python_input_snapshot(root)
        if before != after:
            raise ReleaseBundleError(
                "Python source, configuration, or tests changed during acceptance"
            )
        executor_after = bundle._python_acceptance_runtime_identity()
        if executor_before != executor_after:
            raise ReleaseBundleError(
                "Python acceptance executor changed during acceptance"
            )
        summary = bundle._python_evidence_summary(root)
        payload = {
            "schema_version": 3,
            "kind": "python-acceptance-receipt",
            "complete": True,
            "returncode": completed.returncode,
            "command": _normalized_python_acceptance_command(),
            "collection": {
                "command": [
                    sys.executable,
                    "-m",
                    "pytest",
                    *collection_identity["pytest_arguments"],
                ],
                "node_ids": list(node_ids),
            },
            "executor": executor_after,
            "inputs": {"before": before, "after": after, "stable": True},
            **summary,
        }
        atomic_write_bytes(root / PYTHON_ACCEPTANCE_RECEIPT, _canonical_json(payload))
        validation_errors = _python_acceptance_receipt_errors(root)
        if validation_errors:
            raise ReleaseBundleError(
                "generated Python acceptance receipt is invalid:\n"
                + "\n".join(validation_errors)
            )
    except BaseException as exc:
        rollback_errors = _restore_python_acceptance_files(prior)
        if rollback_errors:
            raise ReleaseBundleError(
                "cannot restore Python acceptance receipts: "
                + "; ".join(rollback_errors)
            ) from exc
        if isinstance(exc, ReleaseBundleError):
            raise
        if isinstance(exc, (OSError, subprocess.SubprocessError)):
            raise ReleaseBundleError(f"cannot run Python acceptance: {exc}") from exc
        raise
    return root / PYTHON_ACCEPTANCE_RECEIPT
