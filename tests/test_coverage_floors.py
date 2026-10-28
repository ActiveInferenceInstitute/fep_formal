"""Measured line floors reject package regressions hidden by aggregate coverage."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from decimal import Decimal
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
import tomllib

from fep_formal._paths import resolve_environment

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def checker() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "docs_coverage_floors", PROJECT_ROOT / "docs/check_coverage_floors.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _policy(*, empty: tuple[str, ...] = ()) -> bytes:
    return json.dumps(
        {
            "schema_version": 1,
            "kind": "package-line-coverage-floors",
            "metric": "line",
            "aggregate_line_floor": 89,
            "baseline": {"scope": "synthetic checker control; no project acceptance"},
            "packages": {
                name: {
                    "line_floor": floor,
                    "baseline_lines_covered": floor,
                    "baseline_lines_valid": 100,
                }
                for name, floor in (("fep_formal", 92), ("fep_formal.custody", 93))
            },
            "empty_packages": list(empty),
        }
    ).encode()


def _rate(covered: int, valid: int) -> str:
    return str(
        (Decimal(covered) / valid if valid else Decimal(1)).quantize(Decimal(".0001"))
    )


def _xml(counts: dict[str, tuple[int, int]] | None = None) -> bytes:
    if counts is None:
        counts = {"fep_formal": (1000, 1000), "fep_formal.custody": (94, 100)}
    covered, valid = (
        sum(c for c, _ in counts.values()),
        sum(v for _, v in counts.values()),
    )
    root = ET.Element(
        "coverage",
        {
            "lines-covered": str(covered),
            "lines-valid": str(valid),
            "line-rate": _rate(covered, valid),
            "branches-valid": "0",
            "branches-covered": "0",
        },
    )
    packages = ET.SubElement(root, "packages")
    for name, (covered, valid) in counts.items():
        package = ET.SubElement(
            packages, "package", {"name": name, "line-rate": _rate(covered, valid)}
        )
        classes = ET.SubElement(package, "classes")
        cls = ET.SubElement(
            classes,
            "class",
            {
                "filename": name.replace(".", "/") + "/sample.py",
                "line-rate": _rate(covered, valid),
            },
        )
        lines = ET.SubElement(cls, "lines")
        for number in range(1, valid + 1):
            ET.SubElement(
                lines,
                "line",
                {"number": str(number), "hits": str(int(number <= covered))},
            )
    return ET.tostring(root)


def test_clean_report_and_exact_floor_boundary_pass(checker: ModuleType) -> None:
    result = checker.evaluate(
        _xml({"fep_formal": (1000, 1000), "fep_formal.custody": (93, 100)}), _policy()
    )
    assert result["status"] == "passed"
    assert result["metric"] == "line" and result["aggregate"]["floor"] == 89
    assert len(result["coverage_sha256"]) == len(result["policy_sha256"]) == 64


def test_package_regression_cannot_hide_in_aggregate(checker: ModuleType) -> None:
    result = checker.evaluate(
        _xml({"fep_formal": (1000, 1000), "fep_formal.custody": (92, 100)}), _policy()
    )
    assert result["aggregate"]["passed"] is True
    assert result["status"] == "failed"
    assert result["violations"] == ["fep_formal.custody: 92/100 lines below 93%"]


def test_package_passes_cannot_replace_the_global_line_gate(
    checker: ModuleType,
) -> None:
    policy = json.loads(_policy())
    for name, floor in (("fep_formal", 86), ("fep_formal.custody", 83)):
        policy["packages"][name]["line_floor"] = floor
        policy["packages"][name]["baseline_lines_covered"] = floor
    result = checker.evaluate(
        _xml({"fep_formal": (860, 1000), "fep_formal.custody": (83, 100)}),
        json.dumps(policy).encode(),
    )
    assert all(row["status"] == "passed" for row in result["packages"])
    assert result["aggregate"]["passed"] is False
    assert result["status"] == "failed"
    assert result["violations"] == ["aggregate: 943/1100 lines below 89%"]


def test_unrounded_ratio_cannot_pass_by_display_rounding(checker: ModuleType) -> None:
    result = checker.evaluate(
        _xml({"fep_formal": (1000, 1000), "fep_formal.custody": (18599, 20000)}),
        _policy(),
    )
    assert (
        result["status"] == "failed"
    )  # XML displays .9300, but the exact ratio is lower.


def test_empty_package_is_explicit_and_must_stay_empty(checker: ModuleType) -> None:
    counts = {
        "fep_formal": (1000, 1000),
        "fep_formal.custody": (94, 100),
        "fep_formal.data": (0, 0),
    }
    result = checker.evaluate(_xml(counts), _policy(empty=("fep_formal.data",)))
    assert result["packages"][-1]["status"] == "empty-no-executable-lines"
    counts["fep_formal.data"] = (1, 1)
    with pytest.raises(ValueError, match="formerly empty package"):
        checker.evaluate(_xml(counts), _policy(empty=("fep_formal.data",)))


@pytest.mark.parametrize(
    "counts",
    [
        {"fep_formal": (1000, 1000)},
        {
            "fep_formal": (1000, 1000),
            "fep_formal.custody": (94, 100),
            "fep_formal.extra": (1, 1),
        },
    ],
)
def test_missing_or_unreviewed_package_fails(
    checker: ModuleType, counts: dict[str, tuple[int, int]]
) -> None:
    with pytest.raises(ValueError, match="package inventory differs"):
        checker.evaluate(_xml(counts), _policy())


@pytest.mark.parametrize(
    "tamper",
    [
        "duplicate-package",
        "duplicate-class",
        "duplicate-line",
        "negative-hits",
        "path-escape",
        "package-path-disagreement",
        "aggregate-count",
        "aggregate-rate",
        "class-rate",
        "missing-lines",
        "nonfinite-rate",
    ],
)
def test_malformed_or_incoherent_xml_fails(checker: ModuleType, tamper: str) -> None:
    tree = ET.fromstring(_xml())
    packages = tree.find("packages")
    assert packages is not None
    package = packages[0]
    classes = package.find("classes")
    assert classes is not None
    cls = classes[0]
    lines = cls.find("lines")
    assert lines is not None
    if tamper == "duplicate-package":
        packages.append(package)
    elif tamper == "duplicate-class":
        classes.append(cls)
    elif tamper == "duplicate-line":
        lines.append(lines[0])
    elif tamper == "negative-hits":
        lines[0].set("hits", "-1")
    elif tamper == "path-escape":
        cls.set("filename", "../fep_formal/sample.py")
    elif tamper == "package-path-disagreement":
        cls.set("filename", "fep_formal/custody/sample.py")
    elif tamper == "aggregate-count":
        tree.set("lines-covered", "1095")
    elif tamper == "aggregate-rate":
        tree.set("line-rate", ".9000")
    elif tamper == "class-rate":
        cls.set("line-rate", ".8000")
    elif tamper == "missing-lines":
        cls.remove(lines)
    else:
        tree.set("line-rate", "NaN")
    with pytest.raises(ValueError):
        checker.evaluate(ET.tostring(tree), _policy())


def test_dtd_and_entity_declarations_are_rejected(checker: ModuleType) -> None:
    with pytest.raises(ValueError, match="XML declarations forbidden"):
        checker.evaluate(
            b'<!DOCTYPE coverage [<!ENTITY x "hello">]>' + _xml(), _policy()
        )


@pytest.mark.parametrize(
    "change",
    [
        "duplicate-key",
        "nonfinite",
        "overflow-in-baseline",
        "finite-float-in-baseline",
        "metric",
        "floor",
        "baseline",
        "empty-overlap",
    ],
)
def test_unreviewed_policy_shapes_and_unmeasured_thresholds_fail(
    checker: ModuleType, change: str
) -> None:
    payload = json.loads(_policy())
    if change == "duplicate-key":
        data = _policy().replace(
            b'"metric": "line"', b'"metric": "line", "metric": "line"'
        )
    elif change == "nonfinite":
        data = _policy().replace(
            b'"aggregate_line_floor": 89', b'"aggregate_line_floor": NaN'
        )
    elif change in {"overflow-in-baseline", "finite-float-in-baseline"}:
        token = b"1e9999" if change == "overflow-in-baseline" else b"1.0"
        data = _policy().replace(
            b'"baseline": {', b'"baseline": {"workflow_run_id": ' + token + b", "
        )
    else:
        if change == "metric":
            payload["metric"] = "branch"
        elif change == "floor":
            payload["packages"]["fep_formal.custody"]["line_floor"] = 92
        elif change == "baseline":
            payload["packages"]["fep_formal.custody"]["baseline_lines_valid"] = 0
        else:
            payload["empty_packages"] = ["fep_formal.custody"]
        data = json.dumps(payload).encode()
    with pytest.raises(ValueError):
        checker.evaluate(_xml(), data)


def _real_conditional_coverage(
    checker: ModuleType, tmp_path: Path, *, both_arms: bool
) -> dict[str, Any]:
    """Trace an isolated copy of the real model with a marked injected arm.

    No production source is changed. Padding is an explicit aggregate masking
    control, not additional custody coverage or a full-suite measurement.
    """
    original_path = PROJECT_ROOT / "src/fep_formal/custody/model.py"
    original = original_path.read_bytes()
    original_sha = hashlib.sha256(original).hexdigest()
    if (
        original_sha
        != "49c9a714a64687b0d7830e2de58df8e17d29c6b58ac9fc6d7dc6991cfcf71bce"
    ):
        raise ValueError("custody model changed: review the isolated mutation control")
    anchor = b'        """The recorded status for one surface, or ``None`` if not censused."""\n'
    if original.count(anchor) != 1:
        raise ValueError("custody status_of injection anchor is not unique")
    injection = (
        b"        # P09_ISOLATED_COPY_UNTESTED_ARM_BEGIN: never production source.\n"
        b'        if path == "__P09_ISOLATED_UNTESTED_ARM__":\n'
        b'            p09_markers = ["isolated"]\n'
        + b"".join(
            f'            p09_markers.append("{n:02}")\n'.encode() for n in range(1, 12)
        )
        + b'            return "/".join(p09_markers)\n'
        b"        # P09_ISOLATED_COPY_UNTESTED_ARM_END\n"
    )
    mutant = original.replace(anchor, anchor + injection, 1)
    arm_lines = [
        number
        for number, line in enumerate(mutant.decode("utf-8").splitlines(), 1)
        if line.startswith("            p09_markers")
        or line == '            return "/".join(p09_markers)'
    ]
    policy_source = (PROJECT_ROOT / "docs/coverage-floors.json").read_bytes()
    policy = checker.load_policy(policy_source)
    control_policy = {
        **policy,
        "baseline": {
            "scope": "Two-package isolated real-source-copy sensitivity control",
            "reviewed_policy_sha256": hashlib.sha256(policy_source).hexdigest(),
        },
        "packages": {
            name: policy["packages"][name]
            for name in ("fep_formal", "fep_formal.custody")
        },
        "empty_packages": [],
    }
    control_policy_bytes = json.dumps(control_policy, sort_keys=True).encode()
    source = tmp_path / "src"
    custody = source / "fep_formal/custody"
    custody.mkdir(parents=True)
    (source / "fep_formal/__init__.py").write_text("", encoding="utf-8")
    (custody / "__init__.py").write_text("", encoding="utf-8")
    copied_model = custody / "model.py"
    copied_model.write_bytes(mutant)
    (source / "fep_formal/padding.py").write_text(
        "\n".join(f"value_{n} = {n}" for n in range(150)) + "\n", encoding="utf-8"
    )
    report = tmp_path / "coverage.xml"
    child = """
import importlib.util, runpy, sys
from pathlib import Path
from coverage import Coverage
source = Path(sys.argv[1])
cov = Coverage(source=[str(source)], branch=False, data_file=None, config_file=False)
cov.start()
spec = importlib.util.spec_from_file_location(
    'p09_isolated_custody_model', source / 'fep_formal/custody/model.py')
assert spec is not None and spec.loader is not None
model = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = model
spec.loader.exec_module(model)
records = (
    model.CensusRecord('intact', model.INTACT, 'unchanged'),
    model.CensusRecord('stale', model.STALE, 'predates source'),
    model.CensusRecord('red', model.LIVE_RED, 'structural break'),
)
census = model.Census(records)
for record in records:
    assert census.status_of(record.path) == record.status
assert census.status_of('absent') is None
assert census.stale() == (records[1],)
assert census.live_red() == (records[2],)
assert census.is_gated()
assert not model.Census((records[0],)).is_gated()
assert not model.Census(()).is_gated()
assert model.Census(()).status_of('absent') is None
for args in (
    ('', model.INTACT, 'detail'), (17, model.INTACT, 'detail'),
    ('p', 'unknown', 'detail'), ('p', model.INTACT, ''),
    ('p', model.INTACT, 17),
):
    try:
        model.CensusRecord(*args)
    except ValueError:
        pass
    else:
        raise AssertionError('real CensusRecord rejected no invalid field')
for invalid in ([], (object(),), (records[0], records[0])):
    try:
        model.Census(invalid)
    except ValueError:
        pass
    else:
        raise AssertionError('real Census rejected no invalid record inventory')
if sys.argv[3] == 'both':
    expected = '/'.join(['isolated', *(f'{n:02}' for n in range(1, 12))])
    assert census.status_of('__P09_ISOLATED_UNTESTED_ARM__') == expected
runpy.run_path(str(source / 'fep_formal/padding.py'))
cov.stop()
cov.xml_report(outfile=sys.argv[2])
"""
    environment = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(("COVERAGE_", "COV_CORE_"))
    }
    mode = "both" if both_arms else "one"
    command = [sys.executable, "-B", "-c", child, str(source), str(report), mode]
    process: dict[str, Any] = {"argv": command, "cwd": str(tmp_path), "timeout_sec": 30}
    try:
        completed = subprocess.run(
            command,
            cwd=tmp_path,
            env=environment,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        process.update(
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )
    except subprocess.TimeoutExpired as exc:
        process.update(
            returncode=None,
            error="timeout",
            stdout=str(exc.stdout or ""),
            stderr=str(exc.stderr or ""),
        )
    except OSError as exc:
        process.update(returncode=None, error=str(exc), stdout="", stderr="")
    data = report.read_bytes() if report.is_file() else b""
    result: dict[str, Any] | None = None
    evaluation_error: str | None = None
    try:
        result = checker.evaluate(data, control_policy_bytes)
    except (ValueError, ET.ParseError) as exc:
        evaluation_error = str(exc)
    arm_hits = {}
    if result is not None:
        arm_hits = {
            int(line.attrib["number"]): int(line.attrib["hits"])
            for line in ET.fromstring(data).findall(
                "./packages/package/classes/class[@filename='fep_formal/custody/model.py']/lines/line"
            )
            if int(line.attrib["number"]) in arm_lines
        }
    evidence = {
        "schema": "fep-formal.coverage-floor-control.v1",
        "mode": mode,
        "expected_status": "passed" if both_arms else "failed",
        "canonical_source": original_path.relative_to(PROJECT_ROOT).as_posix(),
        "original_source_sha256": original_sha,
        "original_source": original.decode("utf-8"),
        "mutant_source_sha256": hashlib.sha256(mutant).hexdigest(),
        "mutant_source": mutant.decode("utf-8"),
        "injected_arm": injection.decode("utf-8"),
        "injected_arm_lines": arm_lines,
        "injected_arm_line_hits": arm_hits,
        "copied_model_path": str(copied_model),
        "copied_model_sha256_after_child": hashlib.sha256(
            copied_model.read_bytes()
        ).hexdigest(),
        "canonical_source_sha256_after_child": hashlib.sha256(
            original_path.read_bytes()
        ).hexdigest(),
        "reviewed_policy_sha256": hashlib.sha256(policy_source).hexdigest(),
        "control_policy": control_policy_bytes.decode("utf-8"),
        "test_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "checker_source_sha256": hashlib.sha256(
            (PROJECT_ROOT / "docs/check_coverage_floors.py").read_bytes()
        ).hexdigest(),
        "child": process,
        "coverage_xml": data.decode("utf-8"),
        "coverage_xml_sha256": hashlib.sha256(data).hexdigest(),
        "result": result,
        "evaluation_error": evaluation_error,
        "scope": "Isolated copy of the actual custody model with one injected arm; line-only tracing and explicit aggregate padding. No production source mutation, full-suite mutation, branch-arc, native, custody or scientific acceptance.",
    }
    if resolve_environment("FEP_FORMAL_COVERAGE_FLOOR_EVIDENCE") == "1":
        output = PROJECT_ROOT / "output" / f"coverage-floor-control-{mode}.log"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    return evidence


@pytest.mark.parametrize("both_arms", [False, True])
def test_real_uncovered_custody_arm_fails_its_line_floor_while_global_passes(
    checker: ModuleType,
    tmp_path: Path,
    both_arms: bool,
) -> None:
    evidence = _real_conditional_coverage(checker, tmp_path, both_arms=both_arms)
    assert evidence["child"]["returncode"] == 0, evidence["child"]
    assert evidence["evaluation_error"] is None
    assert (
        evidence["original_source_sha256"]
        == evidence["canonical_source_sha256_after_child"]
    )
    assert (
        evidence["mutant_source_sha256"] == evidence["copied_model_sha256_after_child"]
    )
    result = evidence["result"]
    assert result is not None
    assert len(evidence["injected_arm_lines"]) == 13
    assert set(evidence["injected_arm_line_hits"]) == set(
        evidence["injected_arm_lines"]
    )
    assert all(
        (hits > 0) is both_arms for hits in evidence["injected_arm_line_hits"].values()
    )
    assert result["aggregate"]["passed"] is True
    assert result["status"] == ("passed" if both_arms else "failed")
    custody = next(
        row for row in result["packages"] if row["package"] == "fep_formal.custody"
    )
    padding = next(row for row in result["packages"] if row["package"] == "fep_formal")
    assert padding["status"] == "passed"
    assert custody["floor"] == 93
    assert (custody["covered"] * 100 >= custody["valid"] * 93) is both_arms
    assert int(ET.fromstring(evidence["coverage_xml"]).get("branches-valid", "0")) == 0


def test_cli_fails_closed_and_reports_exact_input_hashes(
    checker: ModuleType,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    report, policy = tmp_path / "coverage.xml", tmp_path / "policy.json"
    report.write_bytes(_xml())
    policy.write_bytes(_policy())
    args = ["--coverage", str(report), "--policy", str(policy)]
    assert checker.main(args) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "passed"
    report.write_bytes(b"not XML")
    assert checker.main(args) == 1
    assert json.loads(capsys.readouterr().out)["status"] == "error"
    report.unlink()
    report.symlink_to(policy)
    assert checker.main(args) == 1
    assert (
        "not a regular input" in json.loads(capsys.readouterr().out)["failure_reason"]
    )


def test_committed_policy_preserves_global_floor_and_baseline_math(
    checker: ModuleType,
) -> None:
    policy = checker.load_policy(
        (PROJECT_ROOT / "docs/coverage-floors.json").read_bytes()
    )
    with (PROJECT_ROOT / "pyproject.toml").open("rb") as handle:
        configuration = tomllib.load(handle)
    assert (
        policy["aggregate_line_floor"]
        == configuration["tool"]["coverage"]["report"]["fail_under"]
        == 89
    )
    baseline = policy["baseline"]
    assert (
        sum(
            row["baseline_lines_covered"]
            for name, row in policy["packages"].items()
            if name != "fep_lean"
        )
        == baseline["lines_covered"]
        == 17197
    )
    assert (
        sum(
            row["baseline_lines_valid"]
            for name, row in policy["packages"].items()
            if name != "fep_lean"
        )
        == baseline["lines_valid"]
        == 18765
    )
    assert len(policy["packages"]) == 15 and policy["empty_packages"] == [
        "fep_formal.data"
    ]


def test_default_policy_is_anchored_to_script_not_working_directory(
    checker: ModuleType,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    policy_data = (PROJECT_ROOT / "docs/coverage-floors.json").read_bytes()
    policy = json.loads(policy_data)
    counts = {
        name: (row["baseline_lines_covered"], row["baseline_lines_valid"])
        for name, row in policy["packages"].items()
    }
    counts.update({name: (0, 0) for name in policy["empty_packages"]})
    (tmp_path / "coverage.xml").write_bytes(_xml(counts))
    monkeypatch.chdir(tmp_path)
    assert checker.main(["--coverage", "coverage.xml"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "passed"
    assert result["aggregate"]["covered"] == 17197 + 32
    assert result["aggregate"]["valid"] == 18765 + 32


def test_compatibility_adapter_has_its_own_floor_and_cannot_hide_descendants(
    checker: ModuleType,
) -> None:
    policy = json.loads(_policy())
    policy["packages"]["fep_lean"] = {
        "line_floor": 100,
        "baseline_lines_covered": 32,
        "baseline_lines_valid": 32,
    }
    data = json.dumps(policy).encode()
    counts = {
        "fep_formal": (1000, 1000),
        "fep_formal.custody": (94, 100),
        "fep_lean": (32, 32),
    }
    assert checker.evaluate(_xml(counts), data)["status"] == "passed"
    counts["fep_lean"] = (31, 32)
    assert checker.evaluate(_xml(counts), data)["violations"] == [
        "fep_lean: 31/32 lines below 100%"
    ]
    del counts["fep_lean"]
    with pytest.raises(ValueError, match="package inventory differs"):
        checker.evaluate(_xml(counts), data)
    counts["fep_lean.unexpected"] = (1, 1)
    with pytest.raises(ValueError, match="invalid or duplicate coverage package"):
        checker.evaluate(_xml(counts), data)
