"""Support and signed-precision boundaries of the existing finite Gibbs laws."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from fep_lean.formal import formal_theorem_modules
from fep_lean.lean_source import lean_code_without_comments
from tests._support.lake import lake_executable
from tests._support.lean_runner import run_lean_compile_probe

ROOT = Path(__file__).resolve().parents[1]
FORMAL = ROOT / "src" / "fep_lean" / "formal"
CONTROLLED_NEW = {
    "boltzmannPosterior_eq_zero_iff",
    "boltzmannPosterior_pos_iff",
    "log_boltzmannPosterior",
}
EFE_NEW = {
    "controlPosterior_relativeSupport",
    "efeControl_scaled_objective_eq_kl_sub_logPartition",
    "efeControlObjective_eq_kl_sub_logPartition_of_relativeSupport",
    "efeControlObjective_optimizer_value",
    "efeControlObjective_sub_eq_kl_of_relativeSupport",
    "efeControlObjective_eq_optimizer_iff_of_relativeSupport",
    "boltzmann_control_posterior_minimizes_efe_of_relativeSupport",
    "efeControlObjective_optimizer_lt_of_relativeSupport",
    "boltzmann_control_posterior_maximizes_efe_of_negative_precision",
    "efeControlObjective_lt_optimizer_of_negative_precision",
    "sparseGibbs_partition",
    "sparseGibbs_posterior_mass",
    "sparseGibbs_supported_strict_gap",
    "sparseGibbs_negative_precision_strict_gap",
    "zeroReference_unsupported_candidate_beats_posterior",
    "zeroPrecision_prior_not_minimizer",
}
CONTROLLED_RELEASED = {
    "controlledKernel_sum_one",
    "actionBeliefUpdate_reconstruction",
    "actionBeliefUpdate_sum_one",
    "actionEvidence_zero_boundary",
    "reachableBelief_policyValue_eq",
    "boltzmannPartition_pos",
    "boltzmannPosterior_mul_partition",
    "boltzmannPosterior_zero_energy",
    "controlPosterior_sum_one",
    "controlPosterior_zero_cost",
    "softBellmanPartition_pos",
    "softBellmanValue_succ",
    "softBellmanValue_partition_pos",
    "softBellmanValue_le_actionEnergy",
    "desirabilityStep_nonneg",
    "desirabilityStep_zero_cost_one",
    "exists_finite_minimizer",
    "finiteArgmin_le",
    "sophisticatedEFEValue_succ",
    "sophisticatedEFEAction_le",
    "bool_actionPrediction_eq",
    "bool_actionEvidence_eq",
    "bool_positiveEvidence_observation_eq_action",
    "bool_actionBeliefUpdate_eq",
    "boolReachablePOMDP_update_sound",
    "twoStageFeedback_eq_observation",
    "twoStageFeedback_changes_action",
    "twoStageFeedbackExpectedCost_zero",
    "twoStageOpenLoopExpectedCost_eq_half",
    "twoStageFeedback_beats_openLoop",
}
EFE_RELEASED = {
    "efeControlObjective_eq_gibbsFreeEnergy",
    "efeControlObjective_eq_kl_sub_logPartition",
    "efeControlObjective_sub_eq_kl",
    "boltzmann_control_posterior_minimizes_efe",
    "boltzmann_control_posterior_minimal_value",
    "argminEFE_eq_risk_add_ambiguity",
    "finiteArgminEFE_minimizes_risk_add_ambiguity",
    "exists_EFE_minimizing_policy",
    "policyTree_value_agreement",
}


def _source(module: str) -> str:
    return lean_code_without_comments((FORMAL / f"{module}.lean").read_text())


def _declaration(source: str, name: str) -> tuple[str, str]:
    match = re.search(
        rf"(?m)^theorem {re.escape(name)}\b(?P<body>.*?)"
        r"(?=\n(?:theorem|noncomputable def|end)\b|\Z)",
        source,
        re.DOTALL,
    )
    assert match is not None, name
    signature, proof = match.group(0).split(" := by", maxsplit=1)
    return signature, proof


def test_support_extension_preserves_owners_imports_and_exact_public_rosters():
    owners = formal_theorem_modules(ROOT)
    for module, namespace, released, added, imports in (
        (
            "controlled_markov",
            "FEP.ControlledMarkov",
            CONTROLLED_RELEASED,
            CONTROLLED_NEW,
            ("FepSketches.active_inference",),
        ),
        (
            "efe_policy_selection",
            "FEP.EFEPolicy",
            EFE_RELEASED,
            EFE_NEW,
            (
                "FepSketches.controlled_markov",
                "FepSketches.policy_tree",
                "FepSketches.variational_duality",
            ),
        ),
    ):
        source = _source(module)
        assert tuple(re.findall(r"(?m)^public import (\S+)$", source)) == imports
        assert f"namespace {namespace}\n" in source
        assert source.rstrip().endswith(f"end {namespace}")
        assert {
            name for name, owner in owners.items() if owner == f"FepSketches.{module}"
        } == {f"{namespace}.{name}" for name in released | added}
        assert not re.search(r"\b(?:sorry|admit|axiom|opaque)\b", source)
        assert not re.search(
            r"(?m)^structure\s+(?:FiniteLaw|GibbsCertificate)\b", source
        )


@pytest.mark.parametrize("module", ["controlled_markov", "efe_policy_selection"])
def test_support_extension_workspace_projection_is_exact(module):
    assert (FORMAL / f"{module}.lean").read_bytes() == (
        ROOT / "lean" / "FepSketches" / f"{module}.lean"
    ).read_bytes()


def test_zero_support_is_preserved_and_logarithm_is_atomwise_supported():
    source = _source("controlled_markov")
    zero, _ = _declaration(source, "boltzmannPosterior_eq_zero_iff")
    positive, _ = _declaration(source, "boltzmannPosterior_pos_iff")
    logarithm, _ = _declaration(source, "log_boltzmannPosterior")
    assert "= 0 ↔ prior action = 0" in zero
    assert "↔ 0 < prior action" in positive
    assert "(hprior : 0 < prior action)" in logarithm
    assert "∀" not in logarithm
    assert "Real.log (prior action) - energy action -" in logarithm


def test_scaled_gap_is_derived_for_all_real_precisions_with_relative_support():
    signature, proof = _declaration(
        _source("efe_policy_selection"),
        "efeControl_scaled_objective_eq_kl_sub_logPartition",
    )
    assert "(γ : ℝ)" in signature
    assert "hγ" not in signature
    assert "Q policy ≠ 0 → 0 < prior policy" in signature
    assert "γ * expectation Q cost + finiteKL Q prior" in signature
    assert "GibbsCertificate" not in signature
    assert "finiteKL_eq_crossEntropy_sub_entropy_of_relativeSupport" in proof
    assert "by_cases hmass : Q policy = 0" in proof
    assert "Q.sum_one" in proof


def test_divided_gap_and_optimization_keep_distinct_precision_contracts():
    source = _source("efe_policy_selection")
    for name in (
        "efeControlObjective_eq_kl_sub_logPartition_of_relativeSupport",
        "efeControlObjective_sub_eq_kl_of_relativeSupport",
        "efeControlObjective_eq_optimizer_iff_of_relativeSupport",
    ):
        signature, _ = _declaration(source, name)
        assert "(hγ : γ ≠ 0)" in signature
        assert "Q policy ≠ 0 → 0 < prior policy" in signature
    minimum, _ = _declaration(
        source, "boltzmann_control_posterior_minimizes_efe_of_relativeSupport"
    )
    maximum, _ = _declaration(
        source, "boltzmann_control_posterior_maximizes_efe_of_negative_precision"
    )
    assert "(hγ : 0 < γ)" in minimum
    assert "(hγ : γ < 0)" in maximum
    assert "Q = controlPosterior prior γ cost" in minimum
    assert "Q = controlPosterior prior γ cost" in maximum
    for name in (
        "efeControlObjective_optimizer_lt_of_relativeSupport",
        "efeControlObjective_lt_optimizer_of_negative_precision",
    ):
        signature, _ = _declaration(source, name)
        assert "(hne : Q ≠ controlPosterior prior γ cost)" in signature


def test_released_full_support_results_consume_stronger_supported_results():
    source = _source("efe_policy_selection")
    for name in (
        "efeControlObjective_eq_kl_sub_logPartition",
        "efeControlObjective_sub_eq_kl",
        "boltzmann_control_posterior_minimizes_efe",
    ):
        signature, proof = _declaration(source, name)
        assert "(prior_pos : ∀ policy, 0 < prior policy)" in signature
        assert "(hγ : 0 < γ)" in signature
        assert f"{name}_of_relativeSupport" in proof


def test_sparse_and_failed_stronger_claims_have_explicit_witnesses():
    source = _source("efe_policy_selection")
    assert "mass := ![1 / 2, 1 / 2, 0]" in source
    assert "![0, -Real.log 3, -7]" in source
    partition, _ = _declaration(source, "sparseGibbs_partition")
    masses, _ = _declaration(source, "sparseGibbs_posterior_mass")
    strict, _ = _declaration(source, "sparseGibbs_supported_strict_gap")
    assert "= 2" in partition
    assert "![1 / 4, 3 / 4, 0] policy" in masses
    assert "sparseGibbsCost 2 = 0" in strict
    unsupported, proof = _declaration(
        source, "zeroReference_unsupported_candidate_beats_posterior"
    )
    assert "prior true = 0 ∧ candidate true = 1" in unsupported
    assert "efeControlObjective prior 1 cost candidate <" in unsupported
    assert "finiteKL_disjoint_pointMass_totalized" in proof
    zero, _ = _declaration(source, "zeroPrecision_prior_not_minimizer")
    assert "∀ policy, 0 < prior policy" in zero
    assert "controlPosterior prior 0 cost = prior" in zero
    assert "efeControlObjective prior 0 cost (FiniteLaw.pointMass false) <" in zero


@pytest.mark.serial_lean
def test_support_aware_gibbs_downstream_examples_compile_warning_free(tmp_path):
    probe = tmp_path / "SupportAwareGibbs.lean"
    probe.write_text(
        """import FepSketches.efe_policy_selection

open FEP FEP.ControlledMarkov FEP.EFEPolicy FEP.VariationalDuality
  FEP.FiniteInformation

example (policy : Fin 3) :
    (boltzmannPosterior sparseGibbsPrior sparseGibbsCost policy = 0 ↔
      sparseGibbsPrior policy = 0) :=
  boltzmannPosterior_eq_zero_iff _ _ _

example : controlPosterior sparseGibbsPrior 1 sparseGibbsCost 0 = 1 / 4 := by
  simpa using sparseGibbs_posterior_mass 0

example : controlPosterior sparseGibbsPrior 1 sparseGibbsCost 2 = 0 :=
  sparseGibbs_supported_strict_gap.2

example (γ : ℝ) :
    γ * expectation (controlPosterior sparseGibbsPrior γ sparseGibbsCost)
        sparseGibbsCost +
      finiteKL (controlPosterior sparseGibbsPrior γ sparseGibbsCost)
        sparseGibbsPrior =
      finiteKL (controlPosterior sparseGibbsPrior γ sparseGibbsCost)
          (controlPosterior sparseGibbsPrior γ sparseGibbsCost) -
        Real.log (efeControlPartition sparseGibbsPrior γ sparseGibbsCost) :=
  efeControl_scaled_objective_eq_kl_sub_logPartition _ _ _ _
    (controlPosterior_relativeSupport _ _ _)

example (γ : ℝ) (hγ : γ < 0) :
    efeControlObjective sparseGibbsPrior γ sparseGibbsCost sparseGibbsPrior ≤
      efeControlObjective sparseGibbsPrior γ sparseGibbsCost
        (controlPosterior sparseGibbsPrior γ sparseGibbsCost) :=
  (boltzmann_control_posterior_maximizes_efe_of_negative_precision
    _ γ hγ _ _ (fun policy hmass =>
      lt_of_le_of_ne (sparseGibbsPrior.nonneg policy) hmass.symm)).1

example :
    efeControlObjective sparseGibbsPrior (-1) sparseGibbsCost
        (FiniteLaw.pointMass 0) <
      efeControlObjective sparseGibbsPrior (-1) sparseGibbsCost
        (controlPosterior sparseGibbsPrior (-1) sparseGibbsCost) :=
  sparseGibbs_negative_precision_strict_gap (-1) (by norm_num)

#check zeroReference_unsupported_candidate_beats_posterior
#check zeroPrecision_prior_not_minimizer
""",
        encoding="utf-8",
    )
    result = run_lean_compile_probe(
        probe,
        cwd=ROOT / "lean",
        executable=lake_executable(missing="raise"),
        timeout_s=300,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "warning:" not in (result.stdout + result.stderr).lower()
