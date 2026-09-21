"""H1.5 finite constrained-entropy certificate contracts."""

from __future__ import annotations

import re
from pathlib import Path

from fep_lean.lean_source import lean_code_without_comments

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FOUNDATION = PROJECT_ROOT / "src" / "fep_lean" / "formal" / "variational_duality.lean"


def _declaration(source: str, name: str) -> str:
    uncommented = lean_code_without_comments(source)
    match = re.search(
        rf"(?:theorem|lemma|def|noncomputable def)\s+{re.escape(name)}\b"
        rf"(?P<body>.*?)(?=\n(?:theorem|lemma|def|noncomputable def|end)\b|\Z)",
        uncommented,
        flags=re.DOTALL,
    )
    assert match is not None, f"missing declaration {name}"
    return match.group(0)


def test_constrained_entropy_extends_the_existing_owner_without_new_imports() -> None:
    source = FOUNDATION.read_text(encoding="utf-8")

    assert tuple(re.findall(r"(?m)^import (\S+)$", source)) == (
        "FepSketches.finite_information",
        "Mathlib.Analysis.Convex.SpecificFunctions.Basic",
    )
    assert "namespace FEP.VariationalDuality\n" in source
    assert source.rstrip().endswith("end FEP.VariationalDuality")
    assert "structure AffineMomentConstraint" in source
    assert "structure ConstrainedEntropyCertificate" in source
    assert not re.search(
        r"\b(?:sorry|admit|axiom|opaque)\b|unsafe\s+(?:def|theorem)|:\s*True\b",
        source,
    )


def test_certificate_proves_existence_and_uniqueness_only_from_supplied_data() -> None:
    source = FOUNDATION.read_text(encoding="utf-8")
    result = _declaration(source, "constrainedEntropy_existsUnique_of_certificate")

    assert "(certificate : ConstrainedEntropyCertificate α)" in result
    assert "SatisfiesMomentConstraints certificate.gibbs.optimizer" in result
    assert "∀ candidate : FiniteLaw α" in result
    assert "SatisfiesMomentConstraints candidate certificate.constraints →" in result
    assert "entropy candidate ≤ entropy certificate.gibbs.optimizer" in result
    assert "entropy candidate = entropy certificate.gibbs.optimizer ↔" in result
    assert "candidate = certificate.gibbs.optimizer" in result
    assert "dvObjective_le_logPartition" in result
    assert "dvObjective_eq_logPartition_iff" in result
    assert "strongDuality" not in source
    assert "slater" not in lean_code_without_comments(source).lower()


def test_temperature_reference_and_full_support_boundaries_are_explicit() -> None:
    source = lean_code_without_comments(FOUNDATION.read_text(encoding="utf-8"))
    certificate = source.split("structure ConstrainedEntropyCertificate", maxsplit=1)[
        1
    ].split("theorem constrainedEntropy_existsUnique_of_certificate", maxsplit=1)[0]
    zero_temperature = _declaration(source, "zeroTemperature_not_certified")

    assert "temperature_pos : 0 < temperature" in certificate
    assert "reference_eq_uniform : gibbs.reference = FiniteLaw.uniform" in certificate
    assert "gibbs.potential x =" in certificate
    assert "constraintPotential constraints multipliers x / temperature" in certificate
    assert "gibbs : GibbsCertificate α" in certificate
    assert "certificate.temperature ≠ 0" in zero_temperature
    assert "certificate.temperature_pos" in zero_temperature


def test_fin3_two_moment_interior_problem_has_a_concrete_unique_certificate() -> None:
    source = FOUNDATION.read_text(encoding="utf-8")
    constraints = _declaration(source, "fin3InteriorMomentConstraints")
    certificate = _declaration(source, "fin3InteriorMomentCertificate")
    result = _declaration(source, "fin3InteriorMoment_uniqueEntropyMaximizer")

    assert "![0, 1, 2]" in source
    assert "![0, 1, 4]" in source
    assert "target := 1" in constraints
    assert "target := 5 / 3" in constraints
    assert "multipliers _ := 0" in certificate
    assert "temperature := 1" in certificate
    assert "uniformZeroPotentialGibbs" in certificate
    assert "∀ x, 0 < fin3InteriorMomentCertificate.gibbs.optimizer x" in result
    assert "constrainedEntropy_existsUnique_of_certificate" in result
    assert "entropy candidate ≤" in result
    assert "candidate = fin3InteriorMomentCertificate.gibbs.optimizer" in result


def test_boundary_optimizer_is_support_forced_without_a_gibbs_claim() -> None:
    source = FOUNDATION.read_text(encoding="utf-8")
    characterization = _declaration(source, "fin3Boundary_feasible_iff_pointMassZero")
    maximum = _declaration(source, "fin3Boundary_uniqueEntropyMaximizer")

    assert "SatisfiesMomentConstraints law fin3BoundaryConstraints ↔" in (
        characterization
    )
    assert "law = FiniteLaw.pointMass (0 : Fin 3)" in characterization
    assert "GibbsCertificate" not in characterization
    assert "FiniteLaw.pointMass (0 : Fin 3)" in maximum
    assert "SatisfiesMomentConstraints candidate fin3BoundaryConstraints →" in maximum
    assert "candidate = FiniteLaw.pointMass (0 : Fin 3)" in maximum
    assert "GibbsCertificate" not in maximum


def test_infeasible_fin3_constraint_is_rejected_before_optimization() -> None:
    source = FOUNDATION.read_text(encoding="utf-8")
    result = _declaration(source, "fin3Infeasible_no_feasibleLaw")

    assert "¬ ∃ law : FiniteLaw (Fin 3)" in result
    assert "SatisfiesMomentConstraints law fin3InfeasibleConstraints" in result
    assert "law.mass_le_one (0 : Fin 3)" in result
    assert "GibbsCertificate" not in result
    assert "entropy" not in result


def test_duplicate_moment_constraint_is_proved_redundant() -> None:
    source = FOUNDATION.read_text(encoding="utf-8")
    constraints = _declaration(source, "fin3RedundantConstraints")
    result = _declaration(source, "fin3Redundant_feasible_iff")

    assert constraints.count("fin3MeanOneConstraint") == 2
    assert "SatisfiesMomentConstraints law fin3RedundantConstraints ↔" in result
    assert "expectation law fin3FirstMoment = 1" in result
    assert "entropy" not in result
    assert "strongDuality" not in result


def test_horizon15_public_theorem_roster_is_exact() -> None:
    source = FOUNDATION.read_text(encoding="utf-8")
    section = source.split("## Finite constrained maximum entropy", maxsplit=1)[
        1
    ].split("## Rate--distortion weak duality", maxsplit=1)[0]
    section = lean_code_without_comments(section)

    assert tuple(re.findall(r"(?m)^theorem ([A-Za-z0-9_']+)", section)) == (
        "zeroTemperature_not_certified",
        "constrainedEntropy_existsUnique_of_certificate",
        "fin3InteriorMoment_uniqueEntropyMaximizer",
        "fin3Boundary_feasible_iff_pointMassZero",
        "fin3Boundary_uniqueEntropyMaximizer",
        "fin3Infeasible_no_feasibleLaw",
        "fin3Redundant_feasible_iff",
    )
