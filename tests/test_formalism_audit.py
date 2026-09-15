"""Declaration and axiom audits fail closed independently of topic receipts."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from fep_lean.catalogue.registry import BODIES
from fep_lean.formal.manifest import FORMAL_MODULES
from fep_lean.verification import formalism_audit

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LEAN_VERSION = (
    "Lean (version "
    + (PROJECT_ROOT / "lean" / "lean-toolchain")
    .read_text()
    .strip()
    .rsplit(":", 1)[-1]
    .lstrip("v")
    + ", x86_64-unknown-linux-gnu, commit fixture, Release)"
)


@pytest.fixture(autouse=True)
def _stable_actual_lean_version(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        formalism_audit,
        "_probe_lean_version",
        lambda *_args, **_kwargs: (LEAN_VERSION, ""),
    )


def _complete_axiom_stdout(*, first_axiom: str = "propext") -> str:
    declarations, _ = formalism_audit._declaration_sources(PROJECT_ROOT)
    lines = [
        f"'{declaration}' depends on axioms: [{first_axiom if index == 0 else 'propext'}]"
        for index, declaration in enumerate(declarations)
    ]
    return "\n".join(lines) + "\n"


def test_axiom_parser_accepts_lean_hard_wrapped_output() -> None:
    declaration = "fep_fep012.FEP012.fep012_entropyRegularizedCost_le_expectedCost"
    output = (
        f"'{declaration}' depends on axioms: [propext,\n"
        " Classical.choice,\n"
        " Quot.sound]\n"
    )
    assert formalism_audit._axioms_by_declaration(output) == {
        declaration: ("propext", "Classical.choice", "Quot.sound")
    }


def test_axiom_parser_preserves_primed_declaration_names() -> None:
    declaration = "FEPComposed.posterior_predictive'"
    output = f"'{declaration}' depends on axioms: [propext]\n"
    parsed, errors = formalism_audit._parse_axiom_output(
        output,
        expected=(declaration,),
    )
    assert parsed == {declaration: ("propext",)}
    assert errors == ()


@pytest.mark.parametrize(
    ("output", "expected_error"),
    [
        (
            (
                "'FEP.a' depends on axioms: [propext]\n"
                "'FEP.a' depends on axioms: [Classical.choice]\n"
            ),
            "duplicate axiom evidence for FEP.a",
        ),
        (
            (
                "'FEP.a' depends on axioms: [propext]\n"
                "'FEP.unknown' does not depend on any axioms\n"
            ),
            "unexpected axiom evidence for FEP.unknown",
        ),
        (
            "'FEP.a' depends on axioms: [propext\n",
            "unterminated axiom list for FEP.a",
        ),
        (
            "'FEP.a' depends on axioms: [propext, ???]\n",
            "malformed axiom name for FEP.a: ???",
        ),
    ],
)
def test_axiom_parser_rejects_ambiguous_or_malformed_evidence(
    output: str,
    expected_error: str,
) -> None:
    _, errors = formalism_audit._parse_axiom_output(output, expected=("FEP.a",))
    assert expected_error in errors


def test_native_audit_rejects_duplicate_and_unknown_axiom_records(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stdout = _complete_axiom_stdout()
    stdout += "'FEP.unknown' depends on axioms: [propext]\n"
    declaration = formalism_audit._declaration_sources(PROJECT_ROOT)[0][0]
    stdout += f"'{declaration}' depends on axioms: [propext]\n"
    monkeypatch.setattr(formalism_audit, "find_executable", lambda *_: "/bin/lake")
    monkeypatch.setattr(
        formalism_audit,
        "run_process_group",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args=args[0], returncode=0, stdout=stdout, stderr=""
        ),
    )
    result = formalism_audit.run_formalism_audit(PROJECT_ROOT)
    assert result.complete is False
    assert "duplicate axiom evidence" in result.failure_reason
    assert "unexpected axiom evidence" in result.failure_reason
    assert result.axiom_parse_errors


def test_probe_resolves_primaries_and_prints_evidence_axioms() -> None:
    probe, primary, evidence = formalism_audit.build_formalism_probe(PROJECT_ROOT)
    imports = formalism_audit.formal_module_imports()
    assert probe.startswith(f"import {imports[0]}\n")
    assert imports[0] == "FepSketches.finite_probability"
    assert imports[-1] == "FepSketches.composed"
    assert imports == tuple(module.lean_module for module in FORMAL_MODULES)
    assert len(primary) == len(BODIES)
    assert "fep_fep009.FEP009.fep009_condIndep_symm" in primary
    assert "FEPComposed.fep002_vfe_compProd_chain_rule" in evidence
    assert "FEPComposed.fep031_zeroBeta_binary_maxEntropy" in evidence
    assert "FEP.ActiveInference.expectedFreeEnergy_eq_risk_add_ambiguity" in evidence
    assert "FEP.InformationGeometry.pullbackMetric_pos" in evidence
    assert probe.count("#check ") == len(set(primary) | set(evidence))
    assert probe.count("#print axioms ") == len(set(primary) | set(evidence))


@pytest.mark.parametrize(
    ("variant", "returncode", "complete", "sorry_ax", "warning_count", "resolved"),
    [
        ("clean", 0, True, False, 0, True),
        ("sorry", 0, False, True, 0, True),
        ("warning", 0, False, False, 1, True),
        ("missing_axioms", 0, False, False, 0, False),
        ("unapproved_axiom", 0, False, False, 0, True),
        ("error", 1, False, False, 0, False),
    ],
)
def test_native_audit_evaluation_is_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
    variant: str,
    returncode: int,
    complete: bool,
    sorry_ax: bool,
    warning_count: int,
    resolved: bool,
) -> None:
    first_axiom = {
        "sorry": "sorryAx",
        "unapproved_axiom": "Unsafe.customAxiom",
    }.get(variant, "propext")
    stdout = _complete_axiom_stdout(first_axiom=first_axiom)
    if variant == "warning":
        stdout += "audit.lean:1:0: warning: probe warning\n"
    elif variant == "missing_axioms":
        stdout = ""
    elif variant == "error":
        stdout = "unknown constant\n"
    monkeypatch.setattr(formalism_audit, "find_executable", lambda *_: "/bin/lake")
    monkeypatch.setattr(
        formalism_audit,
        "run_process_group",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args=args[0], returncode=returncode, stdout=stdout, stderr=""
        ),
    )
    result = formalism_audit.run_formalism_audit(PROJECT_ROOT)
    assert result.complete is complete
    assert result.sorry_ax_detected is sorry_ax
    assert len(result.warnings) == warning_count
    assert result.declaration_count >= len(BODIES)
    assert result.evidence_count >= 2
    assert result.schema_version == 4
    assert len(result.declaration_evidence) == result.declaration_count
    assert all(record.resolved is resolved for record in result.declaration_evidence)
    assert result.declarations_resolved == (result.declaration_count if resolved else 0)


def test_missing_lake_is_an_explicit_audit_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(formalism_audit, "find_executable", lambda *_: None)
    result = formalism_audit.run_formalism_audit(PROJECT_ROOT)
    assert not result.complete
    assert result.failure_reason == "pinned lake executable is unavailable"


def test_missing_mathlib_revision_is_an_explicit_audit_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(formalism_audit, "find_executable", lambda *_: "/bin/lake")
    monkeypatch.setattr(formalism_audit, "_mathlib_revision", lambda *_: "")
    result = formalism_audit.run_formalism_audit(PROJECT_ROOT)
    assert not result.complete
    assert result.failure_reason == (
        "resolved Mathlib revision is unavailable from lake-manifest.json"
    )


def test_lean_version_probe_failure_is_an_explicit_audit_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(formalism_audit, "find_executable", lambda *_: "/bin/lake")
    monkeypatch.setattr(
        formalism_audit,
        "_probe_lean_version",
        lambda *_args, **_kwargs: ("", "resolved compiler probe failed"),
    )
    result = formalism_audit.run_formalism_audit(PROJECT_ROOT)
    assert not result.complete
    assert result.failure_reason == "resolved compiler probe failed"


def test_mismatched_lean_version_is_an_explicit_audit_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(formalism_audit, "find_executable", lambda *_: "/bin/lake")
    monkeypatch.setattr(
        formalism_audit,
        "_probe_lean_version",
        lambda *_args, **_kwargs: (
            "Lean (version 4.28.0, fixture, Release)",
            "",
        ),
    )
    result = formalism_audit.run_formalism_audit(PROJECT_ROOT)
    assert not result.complete
    assert result.failure_reason == (
        "resolved Lean compiler version does not match the pinned toolchain"
    )


def test_audit_rejects_stale_whole_catalogue_projection(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """A same-named stale topic body must fail before any Lean subprocess."""
    aggregate = tmp_path / "lean" / "FepSketches" / "fep_all.lean"
    aggregate.parent.mkdir(parents=True)
    aggregate.write_text("namespace fep_fep001\nend fep_fep001\n", encoding="utf-8")
    monkeypatch.setattr(
        formalism_audit,
        "build_formalism_probe",
        lambda _root: ("", ("fep_fep001.FEP001.primary",), ()),
    )
    monkeypatch.setattr(formalism_audit, "formal_projection_drift", lambda _root: ())
    monkeypatch.setattr(
        formalism_audit, "_declaration_records", lambda *args, **kwargs: ()
    )
    monkeypatch.setattr(
        formalism_audit,
        "run_process_group",
        lambda *args, **kwargs: pytest.fail("Lean must not run against stale bytes"),
    )

    result = formalism_audit.run_formalism_audit(tmp_path)

    assert result.complete is False
    assert result.failure_reason == "whole-catalogue Lean projection is stale"


def test_declaration_evidence_records_preserve_semantic_source_roles(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(formalism_audit, "find_executable", lambda *_: "/bin/lake")
    monkeypatch.setattr(
        formalism_audit,
        "run_process_group",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args=args[0], returncode=0, stdout=_complete_axiom_stdout(), stderr=""
        ),
    )

    result = formalism_audit.run_formalism_audit(PROJECT_ROOT)
    records = {record.declaration: record for record in result.declaration_evidence}

    primary = records["fep_fep017.FEP017.fep017_posterior_joint_reconstruction"]
    assert primary.source_roles == ("topic_primary",)
    assert primary.source_ids == ("fep-017",)
    assert primary.formal_module == "FepSketches.fep_all"
    composed = records["FEPComposed.fep002_vfe_compProd_chain_rule"]
    assert composed.source_roles == ("formal_module", "formal_relation")
    assert composed.source_ids == (
        "FepSketches.compositions.core",
        "fep-002->fep-014",
    )
    assert composed.formal_module == "FepSketches.compositions.core"
    pairing = records["FEPComposed.fep038_fisherRao_separation"]
    assert pairing.source_roles == (
        "capability_evidence",
        "formal_module",
        "formal_pairing",
    )
    assert pairing.source_ids == (
        "cap-statistical-manifold",
        "FepSketches.compositions.core",
        "fep-038->fep-018",
    )
    assert pairing.formal_module == "FepSketches.compositions.core"
    foundation = records["FEP.ActiveInference.expectedFreeEnergy_eq_risk_add_ambiguity"]
    assert foundation.source_roles == (
        "capability_evidence",
        "capability_evidence",
        "formal_module",
    )
    assert foundation.formal_module == "FepSketches.active_inference"


def test_audit_receipt_validator_recomputes_digest_and_declaration_closure(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(formalism_audit, "find_executable", lambda *_: "/bin/lake")
    monkeypatch.setattr(
        formalism_audit,
        "run_process_group",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args=args[0], returncode=0, stdout=_complete_axiom_stdout(), stderr=""
        ),
    )
    result = formalism_audit.run_formalism_audit(PROJECT_ROOT)
    receipt = formalism_audit.write_formalism_audit_receipt(
        tmp_path / "formalism-audit.json", result
    )
    assert formalism_audit.validate_formalism_audit_receipt(receipt, PROJECT_ROOT) == ()

    payload = json.loads(receipt.read_text(encoding="utf-8"))
    payload["source_sha256"] = "0" * 64
    payload["declaration_evidence"].pop()
    receipt.write_text(json.dumps(payload), encoding="utf-8")
    errors = formalism_audit.validate_formalism_audit_receipt(receipt, PROJECT_ROOT)
    assert "receipt source_sha256 does not match canonical owners" in errors
    assert "receipt declaration evidence does not match canonical closure" in errors


def test_audit_receipt_validator_returns_structured_error_for_incomplete_root(
    tmp_path: Path,
) -> None:
    receipt = tmp_path / "formalism-audit.json"
    receipt.write_text("{}\n", encoding="utf-8")
    incomplete_root = tmp_path / "incomplete-project"
    incomplete_root.mkdir()

    errors = formalism_audit.validate_formalism_audit_receipt(receipt, incomplete_root)

    assert len(errors) == 1
    assert errors[0].startswith("live formalism owners cannot be loaded:")


def test_audit_receipt_validator_rejects_fail_open_evidence_fields(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(formalism_audit, "find_executable", lambda *_: "/bin/lake")
    monkeypatch.setattr(
        formalism_audit,
        "run_process_group",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args=args[0], returncode=0, stdout=_complete_axiom_stdout(), stderr=""
        ),
    )
    result = formalism_audit.run_formalism_audit(PROJECT_ROOT)
    receipt = formalism_audit.write_formalism_audit_receipt(
        tmp_path / "formalism-audit.json", result
    )
    payload = json.loads(receipt.read_text(encoding="utf-8"))
    payload["returncode"] = 1
    payload["warnings"] = ["warning: tampered"]
    payload["lean_toolchain"] = "leanprover/lean4:v0.0.0"
    payload["failure_reason"] = "tampered failure"
    payload["declaration_evidence"][0]["resolved"] = False
    payload["declaration_evidence"][1]["uses_sorry_ax"] = True
    payload["axiom_output"].pop()
    receipt.write_text(json.dumps(payload), encoding="utf-8")

    errors = formalism_audit.validate_formalism_audit_receipt(receipt, PROJECT_ROOT)

    expected = (
        "receipt returncode must be 0",
        "receipt warnings must be empty",
        "receipt lean_toolchain does not match the live pin",
        "receipt declarations_resolved does not match resolved evidence",
        "receipt contains unresolved declaration evidence",
        "receipt declaration evidence reports sorryAx",
        "receipt axiom output does not cover the declaration closure",
        "receipt failure_reason must be empty",
    )
    assert all(message in errors for message in expected), errors


def test_audit_receipt_rejects_unapproved_axiom_even_when_surfaces_agree(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(formalism_audit, "find_executable", lambda *_: "/bin/lake")
    monkeypatch.setattr(
        formalism_audit,
        "run_process_group",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args=args[0], returncode=0, stdout=_complete_axiom_stdout(), stderr=""
        ),
    )
    result = formalism_audit.run_formalism_audit(PROJECT_ROOT)
    receipt = formalism_audit.write_formalism_audit_receipt(
        tmp_path / "formalism-audit.json", result
    )
    payload = json.loads(receipt.read_text(encoding="utf-8"))
    declaration = payload["declaration_evidence"][0]["declaration"]
    payload["declaration_evidence"][0]["axioms"] = ["Unsafe.customAxiom"]
    payload["axiom_output"][0] = (
        f"'{declaration}' depends on axioms: [Unsafe.customAxiom]"
    )
    receipt.write_text(json.dumps(payload), encoding="utf-8")

    errors = formalism_audit.validate_formalism_audit_receipt(receipt, PROJECT_ROOT)

    assert f"receipt axioms violate policy for {declaration}" in errors
    assert "receipt axiom output violates the trusted policy" in errors


def test_audit_receipt_validation_rejects_live_projection_drift(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(formalism_audit, "find_executable", lambda *_: "/bin/lake")
    monkeypatch.setattr(
        formalism_audit,
        "run_process_group",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args=args[0], returncode=0, stdout=_complete_axiom_stdout(), stderr=""
        ),
    )
    result = formalism_audit.run_formalism_audit(PROJECT_ROOT)
    receipt = formalism_audit.write_formalism_audit_receipt(
        tmp_path / "formalism-audit.json", result
    )
    monkeypatch.setattr(
        formalism_audit,
        "fep_all_projection_drift",
        lambda _root: (PROJECT_ROOT / "lean" / "FepSketches" / "fep_all.lean",),
    )
    monkeypatch.setattr(
        formalism_audit,
        "formal_projection_drift",
        lambda _root: (PROJECT_ROOT / "lean" / "FepSketches" / "composed.lean",),
    )
    monkeypatch.setattr(
        formalism_audit,
        "formal_aggregate_drift",
        lambda _root: (PROJECT_ROOT / "src" / "fep_lean" / "formal" / "composed.lean",),
    )

    errors = formalism_audit.validate_formalism_audit_receipt(receipt, PROJECT_ROOT)

    assert "live whole-catalogue Lean projection is stale" in errors
    assert "live formal composition aggregate is stale" in errors
    assert "live formal Lean workspace projection is stale" in errors
