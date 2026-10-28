"""Synthetic acceptance fixtures exercise fail-closed evidence, never real approval."""

from __future__ import annotations

import ast
import hashlib
import json
import os
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

from fep_formal.verification import horizon_acceptance as acceptance
from fep_formal.verification.numerical_witnesses import NumericalCheck
from tests._support.custody_fixture_knobs import fixture_root

REFERENCE_ROOT = Path(
    os.environ.get("FEP_ACCEPTANCE_REFERENCE_ROOT", Path(__file__).resolve().parents[1])
)


@dataclass(frozen=True)
class _SyntheticWitness:
    id: str
    checks: tuple[NumericalCheck, ...]
    scope: str = "horizon2"
    boundary_observed: bool = True
    evidence_kind: str = acceptance.NON_PROOF_EVIDENCE


def _write(root: Path, name: str, value: Any) -> dict[str, str]:
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    data = (
        value
        if isinstance(value, bytes)
        else json.dumps(value, sort_keys=True).encode()
    )
    path.write_bytes(data)
    return {"path": name, "sha256": hashlib.sha256(data).hexdigest()}


def _xml(nodes: list[str], skipped: set[str] | None = None) -> bytes:
    skipped = skipped or set()
    tree = ET.Element("testsuites")
    suite = ET.SubElement(
        tree,
        "testsuite",
        tests=str(len(nodes)),
        errors="0",
        failures="0",
        skipped=str(len(skipped)),
        time="1.0",
    )
    for node in nodes:
        parts = node.split("::")
        classname = parts[0].removesuffix(".py").replace("/", ".")
        if len(parts) > 2:
            classname += "." + ".".join(parts[1:-1])
        case = ET.SubElement(
            suite, "testcase", classname=classname, name=parts[-1], time="0.01"
        )
        if node in skipped:
            ET.SubElement(
                case, "skipped", type="pytest.skip", message="unit fixture skip"
            )
    return ET.tostring(tree)


@pytest.fixture
def evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, dict[str, Any]]:
    """Fabricate a consistent source epoch and clearly synthetic test evidence."""
    root = fixture_root(tmp_path, monkeypatch)
    witnesses = tuple(
        _SyntheticWitness(name, (NumericalCheck("unit-check", "eq", 1, 1, 0.0),))
        for name in acceptance.DIAGNOSTIC_IDS
    )
    monkeypatch.setattr(acceptance, "evaluate_numerical_witnesses", lambda _: witnesses)
    nodes = []
    for name in acceptance.MANDATORY_TEST_FILES:
        tree = ast.parse((root / name).read_text())
        for node in tree.body:
            if isinstance(
                node, (ast.FunctionDef, ast.AsyncFunctionDef)
            ) and node.name.startswith("test_"):
                nodes.append(name + "::" + node.name)
            elif isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
                nodes.extend(
                    name + "::" + node.name + "::" + child.name
                    for child in node.body
                    if isinstance(child, ast.FunctionDef)
                    and child.name.startswith("test_")
                )
    nodes.append("tests/test_optional.py::test_optional")
    native = acceptance.source_snapshot(
        root, list(acceptance.native_source_paths(root))
    )
    current = acceptance.source_snapshot(root, list(acceptance.CURRENT_FILES))
    reviews = []
    for role in ("lean", "domain", "skeptical"):
        reviews.append(
            _write(
                root,
                f"output/review-{role}.json",
                {
                    "schema_version": 1,
                    "role": role,
                    "reviewer_id": f"SYNTHETIC-UNIT-FIXTURE-{role}",
                    "decision": "approve",
                    "source_sha256": native | current,
                    "findings": "Synthetic approval solely for validator unit testing; no actual horizon accepted.",
                },
            )
        )
    receipt = {
        "schema_version": 1,
        "gate": "H2.7",
        "decision": "accepted",
        "native_evidence": {
            "collection": _write(
                root,
                "output/collection.json",
                {
                    "schema_version": 1,
                    "nodeids": nodes,
                    "markers": {
                        n: ["skipif"] if n == acceptance.HEAVY_NODE else []
                        for n in nodes
                    },
                },
            ),
            "junit": _write(root, "output/tests.xml", _xml(nodes, {nodes[-1]})),
            "source_before": native,
            "source_after": native,
            "pytest_exit_code": 0,
            "heavy_probe_supplement": None,
        },
        "current_sources": current,
        "predecessors": acceptance.PREDECESSORS,
        "reviews": reviews,
        "diagnostics": _write(
            root, "output/diagnostics.json", acceptance.diagnostic_record(root)
        ),
        "downstream": acceptance.DOWNSTREAM,
    }
    # Synthetic fixtures never reuse the production collection attestation.
    monkeypatch.setattr(
        acceptance,
        "CAPTURED_COLLECTION_SHA256",
        receipt["native_evidence"]["collection"]["sha256"],
    )
    _write(root, acceptance.TERMINAL_RECEIPT, receipt)
    return root, receipt


def _seal(root: Path, receipt: dict[str, Any]) -> None:
    _write(root, acceptance.TERMINAL_RECEIPT, receipt)


def test_terminal_validation_is_read_only_and_does_not_promote_h3(
    evidence: tuple[Path, dict[str, Any]],
) -> None:
    root, _ = evidence
    before = {
        p: (p.stat().st_mtime_ns, p.read_bytes())
        for p in root.rglob("*")
        if p.is_file()
    }
    result = acceptance.validate_terminal_acceptance(root)
    assert result.opened == "H3.G0 read-only continuous eligibility"
    assert len(result.reviewed_by) == 3
    assert result.mandatory_nodeids
    assert {p: (p.stat().st_mtime_ns, p.read_bytes()) for p in before} == before


def test_terminal_rejects_actual_roster_growth_after_capture(
    evidence: tuple[Path, dict[str, Any]],
) -> None:
    root, _ = evidence
    for owner in ("src/fep_formal/formal", "lean/FepSketches"):
        (root / owner / "unit_after_capture.lean").write_text(
            "-- synthetic added formal resource, no execution\n"
        )
    with pytest.raises(ValueError, match="native source capture stale or changed"):
        acceptance.validate_terminal_acceptance(root)


@pytest.mark.parametrize(
    "mutation",
    [
        "source",
        "mirror",
        "prior",
        "missing_review",
        "duplicate_reviewer",
        "review_source",
        "downstream",
        "boolean_exit",
        "claimed_diagnostic",
        "native_before",
    ],
)
def test_terminal_rejects_source_claim_and_review_tampering(
    evidence: tuple[Path, dict[str, Any]], mutation: str
) -> None:
    root, receipt = evidence
    if mutation in {"source", "mirror", "prior"}:
        name = {
            "source": "src/fep_formal/formal/fin4_gaussian_semigroup.lean",
            "mirror": "lean/FepSketches/fin4_gaussian_semigroup.lean",
            "prior": next(iter(acceptance.PREDECESSORS)),
        }[mutation]
        path = root / name
        path.write_bytes(path.read_bytes() + b"\n")
    elif mutation == "missing_review":
        receipt["reviews"].pop()
    elif mutation in {"duplicate_reviewer", "review_source"}:
        ref = receipt["reviews"][1]
        review = json.loads((root / ref["path"]).read_text())
        if mutation == "duplicate_reviewer":
            review["reviewer_id"] = "SYNTHETIC-UNIT-FIXTURE-lean"
        else:
            review["source_sha256"] = {}
        receipt["reviews"][1] = _write(root, ref["path"], review)
    elif mutation == "downstream":
        receipt["downstream"] = {"opened": ["H3.1"], "closed": []}
    elif mutation == "boolean_exit":
        receipt["native_evidence"]["pytest_exit_code"] = False
    elif mutation == "native_before":
        receipt["native_evidence"]["source_before"] = {}
    else:
        record = json.loads((root / receipt["diagnostics"]["path"]).read_text())
        record["passed"] = True
        receipt["diagnostics"] = _write(root, receipt["diagnostics"]["path"], record)
    _seal(root, receipt)
    with pytest.raises(ValueError):
        acceptance.validate_terminal_acceptance(root)


@pytest.mark.parametrize(
    "mutation",
    [
        "skip",
        "xfail",
        "xpass_marker",
        "duplicate_node",
        "missing_node",
        "hidden_failure",
        "hidden_namespaced_failure",
        "nan_time",
        "bad_count",
        "bad_root_count",
    ],
)
def test_test_evidence_rejects_nonpassing_or_inconsistent_reports(
    evidence: tuple[Path, dict[str, Any]], mutation: str
) -> None:
    root, receipt = evidence
    collection_ref = receipt["native_evidence"]["collection"]
    collection = json.loads((root / collection_ref["path"]).read_text())
    nodes = collection["nodeids"]
    if mutation == "xpass_marker":
        collection["markers"][nodes[0]] = ["xfail"]
        receipt["native_evidence"]["collection"] = _write(
            root, collection_ref["path"], collection
        )
    xml_ref = receipt["native_evidence"]["junit"]
    tree = ET.fromstring((root / xml_ref["path"]).read_bytes())
    suite = tree.find("testsuite")
    assert suite is not None
    case = suite.find("testcase")
    assert case is not None
    if mutation in {"skip", "xfail"}:
        ET.SubElement(
            case,
            "skipped",
            type="pytest.xfail" if mutation == "xfail" else "pytest.skip",
        )
        suite.set("skipped", "2")
    elif mutation == "duplicate_node":
        suite.append(ET.fromstring(ET.tostring(case)))
        suite.set("tests", str(len(nodes) + 1))
    elif mutation == "missing_node":
        suite.remove(case)
        suite.set("tests", str(len(nodes) - 1))
    elif mutation == "hidden_failure":
        ET.SubElement(tree, "error").text = "collection failed outside a testcase"
    elif mutation == "hidden_namespaced_failure":
        ET.SubElement(tree, "{urn:hidden}failure").text = "concealed failure"
    elif mutation == "nan_time":
        case.set("time", "nan")
    elif mutation == "bad_count":
        suite.set("tests", "-1")
    elif mutation == "bad_root_count":
        tree.set("failures", "1")
    receipt["native_evidence"]["junit"] = _write(
        root, xml_ref["path"], ET.tostring(tree)
    )
    _seal(root, receipt)
    with pytest.raises(ValueError):
        acceptance.validate_terminal_acceptance(root)


def test_heavy_probe_skip_requires_exact_source_identical_passing_supplement(
    evidence: tuple[Path, dict[str, Any]],
) -> None:
    root, receipt = evidence
    native = receipt["native_evidence"]
    collection = json.loads((root / native["collection"]["path"]).read_text())
    nodes = collection["nodeids"]
    collection["markers"][acceptance.HEAVY_NODE] = ["skipif"]
    native["collection"] = _write(root, native["collection"]["path"], collection)
    native["junit"] = _write(
        root, native["junit"]["path"], _xml(nodes, {acceptance.HEAVY_NODE, nodes[-1]})
    )
    _seal(root, receipt)
    with pytest.raises(ValueError, match="skipped"):
        acceptance.validate_terminal_acceptance(root)
    native["heavy_probe_supplement"] = {
        "junit": _write(root, "output/heavy.xml", _xml([acceptance.HEAVY_NODE])),
        "source_before": native["source_before"],
        "source_after": native["source_after"],
        "pytest_exit_code": 0,
        "environment": {"FEP_HEAVY_LEAN_PROBES": "1"},
    }
    _seal(root, receipt)
    assert acceptance.validate_terminal_acceptance(root)
    native["heavy_probe_supplement"]["source_before"] = {}
    _seal(root, receipt)
    with pytest.raises(ValueError, match="supplement native source"):
        acceptance.validate_terminal_acceptance(root)


@pytest.mark.parametrize("mutation", ["finite", "outcomes", "consider_finite"])
def test_g0_rejects_branch_or_outcome_substitution(
    evidence: tuple[Path, dict[str, Any]], mutation: str
) -> None:
    root, _ = evidence
    metadata = {
        "schema_version": 1,
        "branch": "continuous",
        "outcomes_accessed": False,
        "pre_outcome_basis": "Synthetic unit-fixture metadata only",
        "finite_branch_considered": False,
    }
    path = "output/g0-metadata.json"
    _write(root, path, metadata)
    result = acceptance.validate_continuous_eligibility(root, path)
    assert result["protocol_frozen"] is False
    assert result["closed"] == ["H3.1--H3.7"]
    if mutation == "finite":
        metadata["branch"] = "finite"
    elif mutation == "outcomes":
        metadata["outcomes_accessed"] = True
    else:
        metadata["finite_branch_considered"] = True
    _write(root, path, metadata)
    with pytest.raises(ValueError):
        acceptance.validate_continuous_eligibility(root, path)


def test_explicit_output_cannot_overwrite_inputs_or_existing_files(
    tmp_path: Path,
) -> None:
    path = tmp_path / "input.json"
    path.write_text("original")
    with pytest.raises(ValueError):
        acceptance.write_explicit_output(tmp_path, path, {}, inputs=(path,))
    assert path.read_text() == "original"
    output = tmp_path / "output/new.json"
    output.parent.mkdir()
    acceptance.write_explicit_output(tmp_path, output, {"only": "G0"}, inputs=(path,))
    with pytest.raises(ValueError):
        acceptance.write_explicit_output(tmp_path, output, {}, inputs=())


def test_diagnostic_recomputes_checks_instead_of_trusting_passed(
    evidence: tuple[Path, dict[str, Any]], monkeypatch: pytest.MonkeyPatch
) -> None:
    root, _ = evidence
    failed = tuple(
        _SyntheticWitness(name, (NumericalCheck("bad-check", "eq", 1, 2, 0.0),))
        for name in acceptance.DIAGNOSTIC_IDS
    )
    monkeypatch.setattr(acceptance, "evaluate_numerical_witnesses", lambda _: failed)
    with pytest.raises(ValueError, match="diagnostic check failed"):
        acceptance.diagnostic_record(root)


def test_terminal_rejects_input_mtime_change_during_validation(
    evidence: tuple[Path, dict[str, Any]], monkeypatch: pytest.MonkeyPatch
) -> None:
    root, _ = evidence
    original = acceptance.diagnostic_record

    def touch_input(project_root: Path) -> dict[str, Any]:
        result = original(project_root)
        path = root / "src/fep_formal/formal/fin4_gaussian_semigroup.lean"
        before = path.stat()
        os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns + 1))
        return result

    monkeypatch.setattr(acceptance, "diagnostic_record", touch_input)
    with pytest.raises(ValueError, match="input changed during validation"):
        acceptance.validate_terminal_acceptance(root)


def test_diagnostics_reject_source_change_during_evaluation(
    evidence: tuple[Path, dict[str, Any]], monkeypatch: pytest.MonkeyPatch
) -> None:
    root, _ = evidence
    original = acceptance.evaluate_numerical_witnesses

    def mutate_source(project_root: Path) -> Any:
        result = original(project_root)
        path = root / "src/fep_formal/verification/numerical_witnesses.py"
        path.write_bytes(path.read_bytes() + b"\n")
        return result

    monkeypatch.setattr(acceptance, "evaluate_numerical_witnesses", mutate_source)
    with pytest.raises(ValueError, match="diagnostic source changed"):
        acceptance.diagnostic_record(root)


def test_terminal_rejects_jointly_rewritten_collection_and_junit(
    evidence: tuple[Path, dict[str, Any]],
) -> None:
    root, receipt = evidence
    collection_ref = receipt["native_evidence"]["collection"]
    collection = json.loads((root / collection_ref["path"]).read_text())
    # Even consistent rewritten XML cannot erase a case from the captured run.
    removed = collection["nodeids"].pop()
    del collection["markers"][removed]
    receipt["native_evidence"]["collection"] = _write(
        root, collection_ref["path"], collection
    )
    receipt["native_evidence"]["junit"] = _write(
        root, receipt["native_evidence"]["junit"]["path"], _xml(collection["nodeids"])
    )
    _seal(root, receipt)
    with pytest.raises(ValueError, match="frozen captured roster"):
        acceptance.validate_terminal_acceptance(root)


@pytest.mark.parametrize("mutation", ["duplicate", "boundary"])
def test_diagnostic_evaluation_rejects_ambiguous_or_failed_boundary(
    evidence: tuple[Path, dict[str, Any]],
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
) -> None:
    root, _ = evidence
    witnesses = tuple(
        _SyntheticWitness(
            name,
            (NumericalCheck("unit-check", "eq", 1, 1, 0.0),),
            boundary_observed=mutation != "boundary",
        )
        for name in acceptance.DIAGNOSTIC_IDS
    )
    if mutation == "duplicate":
        witnesses += witnesses[:1]
    monkeypatch.setattr(acceptance, "evaluate_numerical_witnesses", lambda _: witnesses)
    with pytest.raises(ValueError, match="duplicate diagnostic|boundary failed"):
        acceptance.diagnostic_record(root)


@pytest.mark.parametrize(
    "relative",
    [
        "src/fep_formal/catalogue/registry.py",
        "src/fep_formal/catalogue/bodies/measure_bayesian_inversion.py",
        "src/fep_formal/formal/declarations.py",
    ],
)
def test_diagnostic_dependency_drift_invalidates_acceptance(
    evidence: tuple[Path, dict[str, Any]], relative: str
) -> None:
    root, _ = evidence
    assert relative in acceptance.CURRENT_FILES
    path = root / relative
    path.write_text(path.read_text() + "\n# changed dependency\n")
    with pytest.raises(
        ValueError, match="current validator/diagnostic source mismatch"
    ):
        acceptance.validate_terminal_acceptance(root)


def test_project_output_cannot_escape_through_parent_symlink(tmp_path: Path) -> None:
    root = tmp_path / "project"
    (root / "output").mkdir(parents=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    (root / "output/link").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink"):
        acceptance.write_explicit_output(
            root, root / "output/link/record.json", {}, inputs=()
        )
    assert not (outside / "record.json").exists()


def test_project_alias_does_not_bypass_output_symlink_guard(tmp_path: Path) -> None:
    root = tmp_path / "project"
    (root / "output").mkdir(parents=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    alias = tmp_path / "project-alias"
    alias.symlink_to(root, target_is_directory=True)
    (root / "output/link").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink"):
        acceptance.write_explicit_output(
            root, alias / "output/link/record.json", {}, inputs=()
        )
    assert not (outside / "record.json").exists()
    acceptance.write_explicit_output(
        root, alias / "output/valid.json", {"accepted": True}, inputs=()
    )
    assert json.loads((root / "output/valid.json").read_text()) == {"accepted": True}


def test_invalid_output_payload_does_not_leave_empty_file(tmp_path: Path) -> None:
    (tmp_path / "output").mkdir()
    path = tmp_path / "output/invalid.json"
    with pytest.raises(ValueError):
        acceptance.write_explicit_output(
            tmp_path, path, {"value": float("nan")}, inputs=()
        )
    assert not path.exists()
