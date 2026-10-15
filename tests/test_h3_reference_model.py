"""Frozen H3 intrinsic carrier, dimensional boundary and native export contracts."""

from __future__ import annotations

import hashlib
import json
import re
from fractions import Fraction
from pathlib import Path

import pytest
import yaml

from fep_lean.lean_source import lean_code_without_comments
from tests._support.lake import lake_executable
from tests._support.lean435_migration import historical_carrier_bytes
from tests._support.lean_runner import run_lean_compile_probe

ROOT = Path(__file__).resolve().parents[1]
FOUNDATION = ROOT / "src/fep_lean/formal/h3_reference_model.lean"
PROJECTION = ROOT / "lean/FepSketches/h3_reference_model.lean"
PROTOCOL = ROOT / "specs/h3-reference-study/preregistration.yaml"
FREEZE = ROOT / "specs/h3-reference-study/freeze.json"
ALLOWED_AXIOMS = {"propext", "Classical.choice", "Quot.sound"}


def test_h3_foundation_owns_intrinsic_imports_and_preserves_frozen_carrier() -> None:
    source = lean_code_without_comments(FOUNDATION.read_text())
    assert source.startswith("module\n")
    assert "\n@[expose] public section\n" in source
    assert re.findall(r"(?m)^public import (\S+)$", source) == [
        "FepSketches.fin4_gaussian_semigroup",
        "FepSketches.markov_semigroup",
    ]
    assert "namespace FEP.H3ReferenceModel\n" in source
    assert source.rstrip().endswith("end FEP.H3ReferenceModel")
    assert FOUNDATION.read_bytes() == PROJECTION.read_bytes()
    assert not re.search(r"\b(?:sorry|admit|axiom|opaque)\b|unsafe\s+", source)

    freeze = json.loads(FREEZE.read_text())
    assert (
        hashlib.sha256(PROTOCOL.read_bytes()).hexdigest()
        == freeze["protocol"]["sha256"]
    )
    # Compare original source bytes without renewing the immutable freeze.
    for path, digest in freeze["carrier_sources"].items():
        historical = historical_carrier_bytes(path, (ROOT / path).read_bytes())
        assert hashlib.sha256(historical).hexdigest() == digest, path


@pytest.mark.serial_lean
def test_h3_native_dimensional_contract_axioms_and_computable_export(
    tmp_path: Path,
) -> None:
    source = FOUNDATION.read_text()
    code = lean_code_without_comments(source)
    names = re.findall(r"(?<!private )\btheorem\s+([A-Za-z_][A-Za-z0-9_]*)", code)
    assert len(names) >= 25
    assert len(names) == len(set(names))
    prints = "\n".join(f"#print axioms FEP.H3ReferenceModel.{name}" for name in names)
    consumers = r"""
open MeasureTheory ProbabilityTheory
open FEP.H3ReferenceModel FEP.H3ReferenceModel.Axis

example (center : StandardState) (left right : ℝ≥0) :
    transition center (left+right) = transition center right ∘ₖ transition center left :=
  transition_add center left right

example (center : StandardState) (time : ℝ≥0) :
    transition center time ∘ₘ stationaryLaw center = stationaryLaw center :=
  stationaryLaw_invariant center time

example (raw : RawState) :
    destandardize frozenCalibration (standardize frozenCalibration raw) = raw :=
  destandardize_standardize frozenCalibration raw

example (row column : Fin 4) :
    (precisionRat row column : ℝ) =
      FEP.Fin4GaussianSemigroup.K (axisFin.symm row) (axisFin.symm column) := by
  rw [precisionRat_eq_native, K_eq_carrier]

example : ¬ ∃ calibration : PositiveCalibration, calibration.scale external = 0 := by
  rintro ⟨calibration, hZero⟩
  have hPositive := calibration.scale_pos external
  rw [hZero] at hPositive
  exact (lt_irrefl 0) hPositive

-- Mixed raw units cannot silently enter the native state or each other's slots.
#check_failure (fun (raw : RawReading external) => (raw : RawReading sensory))
#check_failure (fun (raw : RawState) => (raw : StandardState))
#check_failure (fun (model : ContinuousReferenceModel) => model.stationaryCovariance)
#check_failure (fun (model : ContinuousReferenceModel) => model.blanketCertificate)

#eval IO.println ("H3_PARAMETERS=" ++ parameterExport.compress)
"""
    probe = tmp_path / "H3ReferenceModelAcceptance.lean"
    probe.write_text(source + "\n" + consumers + "\n" + prints)
    result = run_lean_compile_probe(
        probe,
        cwd=ROOT / "lean",
        import_root=tmp_path,
        output_path=tmp_path / "H3ReferenceModelAcceptance.olean",
        timeout_s=300,
        executable=lake_executable(missing="raise", context="H3 intrinsic acceptance"),
    )
    (tmp_path / "H3ReferenceModelAcceptance.stdout.txt").write_text(result.stdout)
    (tmp_path / "H3ReferenceModelAcceptance.stderr.txt").write_text(result.stderr)
    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "warning:" not in output.lower(), output
    assert "sorryAx" not in output
    reports = dict(
        re.findall(
            r"'FEP\.H3ReferenceModel\.(\w+)' depends on axioms: \[([^\]]*)\]",
            output,
        )
    )
    no_axioms = set(
        re.findall(
            r"'FEP\.H3ReferenceModel\.(\w+)' does not depend on any axioms", output
        )
    )
    assert set(names) == reports.keys() | no_axioms, output
    for axioms in reports.values():
        assert {name.strip() for name in axioms.split(",") if name.strip()} <= (
            ALLOWED_AXIOMS
        )

    exports = [
        line.removeprefix("H3_PARAMETERS=")
        for line in output.splitlines()
        if line.startswith("H3_PARAMETERS=")
    ]
    assert len(exports) == 1, output
    exported = json.loads(exports[0])
    protocol = yaml.safe_load(PROTOCOL.read_text())
    assert (
        exported["protocol_sha256"] == hashlib.sha256(PROTOCOL.read_bytes()).hexdigest()
    )
    assert exported["axes"] == protocol["carrier"]["axes"]
    assert exported["axis_fin_order"] == protocol["carrier"]["axis_fin_order"]
    assert exported["raw_units"] == protocol["carrier"]["raw_unit_bridge"]["units"]

    def rational(value: dict[str, int]) -> Fraction:
        assert set(value) == {"numerator", "denominator"}
        assert value["denominator"] > 0
        return Fraction(value["numerator"], value["denominator"])

    precision = [[rational(value) for value in row] for row in exported["precision"]]
    covariance = [[rational(value) for value in row] for row in exported["covariance"]]
    assert precision == protocol["carrier"]["precision"]
    for row in range(4):
        for column in range(4):
            assert sum(precision[row][k] * covariance[k][column] for k in range(4)) == (
                row == column
            )
    assert covariance[0][3] == Fraction(1, 24)
    modes = [[rational(value) for value in row] for row in exported["mode_columns"]]
    rates = [rational(value) for value in exported["rates"]]
    assert (
        rates
        == protocol["synthetic_acceptance"]["recovery_estimators"]["named_modes"][
            "rates"
        ]
    )
    assert modes == [[1, 1, 0, 1], [1, 0, 1, -1], [1, 0, -1, -1], [1, -1, 0, 1]]
    squared_norms = [rational(value) for value in exported["mode_squared_norms"]]
    assert squared_norms == [4, 2, 2, 4]
    for column in range(4):
        assert sum(modes[row][column] ** 2 for row in range(4)) == squared_norms[column]
        assert squared_norms[column] > 0
        for row in range(4):
            assert (
                sum(precision[row][k] * modes[k][column] for k in range(4))
                == rates[column] * modes[row][column]
            )
        for other in range(column):
            assert sum(modes[row][column] * modes[row][other] for row in range(4)) == 0
    assert [rational(value) for value in exported["scales"]] == protocol["carrier"][
        "raw_unit_bridge"
    ]["scales"]
    assert [rational(value) for value in exported["offsets"]] == protocol["carrier"][
        "raw_unit_bridge"
    ]["offsets"]
    assert (
        rational(exported["rate"]) == protocol["carrier"]["dynamic_observable"]["rate"]
    )
    assert (
        rational(exported["diffusion_variance_rate"])
        == protocol["carrier"]["dynamic_observable"]["diffusion_variance_rate"]
    )
    assert [rational(value) for value in exported["recognition_coefficients"]] == [
        Fraction(1, 4)
    ] * 2
    assert rational(exported["recognition_variance"]) == Fraction(1, 4)
    assert (
        exported["recognition_boundary"]
        == "precision_block_algebra_only_native_conditioning_owned_by_composition"
    )
    for actual, expected in zip(
        exported["settings"], protocol["synthetic_acceptance"]["settings"], strict=True
    ):
        assert actual["id"] == expected["id"]
        for key in ("center", "observation_noise_variance", "delta"):
            assert rational(actual[key]) == Fraction(str(expected[key]))
    expected_witnesses = {
        "precisionRat_eq_native",
        "covarianceRat_eq_native",
        "scaleRat_eq_native",
        "offsetRat_eq_native",
        "scalarRateRat_eq_native",
        "diffusionVarianceRateRat_eq_native",
        "recognitionRat_eq_precision",
        "settingRat_eq_native",
        "modeRat_eq_native",
        "modeRateRat_eigenpair",
        "modeVector_nonzero",
        "modeVector_gram",
    }
    assert set(exported["witnesses"]) == {
        "FEP.H3ReferenceModel." + name for name in expected_witnesses
    }
    assert expected_witnesses <= set(names)
