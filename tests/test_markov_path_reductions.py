"""Actual finite-path marginal reductions and reversible endpoint KL contracts."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from fep_lean.lean_source import lean_code_without_comments
from tests._support.lake import lake_executable
from tests._support.lean_runner import run_lean_compile_probe

ROOT = Path(__file__).resolve().parents[1]
FOUNDATION = ROOT / "src/fep_lean/formal/path_thermodynamics.lean"
COMPOSITION = ROOT / "src/fep_lean/formal/compositions/thermo_geometry.lean"
NEW_FOUNDATION_THEOREMS = (
    "markovPathLaw_sum_snoc",
    "markovPathLaw_sum_coordinate",
    "markovPathLaw_sum_stage",
    "markovPathLaw_map_coordinate",
    "markovPathLaw_map_stage",
    "entropyProduction_markov_marginal_decomposition",
    "kernelPower_predictive_pos",
    "entropyProduction_markov_stationary_horizon",
    "pathwiseEntropyProduction_markov_reversible",
    "entropyProduction_markov_reversible_KL_drop",
    "biasedCycle_entropyProduction_horizon",
    "biasedCycle_entropyProduction_horizon_pos",
)
BRIDGE = "fep099_markov_path_KL_drop_reduction"


def _declaration(source: str, name: str) -> str:
    code = lean_code_without_comments(source)
    match = re.search(
        rf"(?ms)^theorem {re.escape(name)}\b.*?(?=^theorem |^private theorem |^end |\Z)",
        code,
    )
    assert match is not None, name
    return match[0]


def test_actual_marginals_use_existing_path_law_and_kernel_powers() -> None:
    source = FOUNDATION.read_text()
    for name in NEW_FOUNDATION_THEOREMS:
        assert len(re.findall(rf"(?m)^theorem {name}\b", source)) == 1
    coordinate = _declaration(source, "markovPathLaw_map_coordinate")
    stage = _declaration(source, "markovPathLaw_map_stage")
    assert ".map (fun path => path t)" in coordinate
    assert "(kernelPower kernel t.val).predictive initial" in coordinate
    assert "(fun path => (path t.castSucc, path t.succ))" in stage
    assert "kernel.joint ((kernelPower kernel t.val).predictive initial)" in stage
    for statement in (coordinate.partition(":= by")[0], stage.partition(":= by")[0]):
        assert "(h" not in statement
        assert "FiniteLaw S" in statement
    snoc = _declaration(source, "markovPathLaw_sum_snoc")
    assert "markovPathMass_snoc" in snoc
    assert "Fin.snocEquiv" in snoc
    assert "induction n" in _declaration(source, "markovPathLaw_sum_coordinate")
    assert "induction n" in _declaration(source, "markovPathLaw_sum_stage")


def test_mean_production_reduces_to_actual_endpoint_and_stage_laws() -> None:
    source = FOUNDATION.read_text()
    reduction = _declaration(source, "entropyProduction_markov_marginal_decomposition")
    assert (
        "crossEntropy ((kernelPower kernel n).predictive initial) final - entropy initial"
        in reduction
    )
    assert "∑ t : Fin n, ∑ source, ∑ target," in reduction
    assert "Real.log (kernel source target / reverse target source)" in reduction
    assert "entropyProduction_markov_decomposition" in reduction
    assert "markovPathLaw_sum_coordinate" in reduction
    assert "markovPathLaw_sum_stage" in reduction
    assert all(
        premise in reduction
        for premise in ("hInitial", "hFinal", "hKernel", "hReverse")
    )


def test_reversible_drop_requires_the_actual_forward_endpoint() -> None:
    source = FOUNDATION.read_text()
    drop = _declaration(source, "entropyProduction_markov_reversible_KL_drop")
    statement = drop.partition(":= by")[0]
    assert "(actual stationary : FiniteLaw S)" in statement
    assert "(hReversible : IsReversible stationary kernel)" in statement
    assert "((kernelPower kernel n).predictive actual) n)" in statement
    assert "finiteKL actual stationary -" in statement
    assert "finiteKL ((kernelPower kernel n).predictive actual) stationary" in statement
    assert "(final :" not in statement
    assert "kernelPower_predictive_pos" in drop
    assert "pathwiseEntropyProduction_markov_reversible" in drop
    assert "markovPathLaw_sum_coordinate" in drop
    pathwise = _declaration(source, "pathwiseEntropyProduction_markov_reversible")
    assert "markovReverseMass_reversedKernel" in pathwise
    assert "reversedKernel_eq_of_reversible" in pathwise


def test_arbitrary_horizon_witness_and_qualified_fep099_bridge() -> None:
    source = FOUNDATION.read_text()
    witness = _declaration(source, "biasedCycle_entropyProduction_horizon")
    positive = _declaration(source, "biasedCycle_entropyProduction_horizon_pos")
    assert "(n : ℝ) * (Real.log 2 / 4)" in witness
    assert "entropyProduction_markov_stationary_horizon" in witness
    assert "(hn : 0 < n)" in positive
    assert "biasedCycle_entropyProduction_horizon" in positive
    bridge = _declaration(COMPOSITION.read_text(), BRIDGE)
    assert "(kernel.predictive actual) 1)" in bridge
    assert "entropyProduction_markov_reversible_KL_drop" in bridge
    assert "fep_fep099.FEP099.fep099_reversibleChain_oneStep_KL_dissipation" in bridge
    for path in (FOUNDATION, COMPOSITION):
        code = lean_code_without_comments(path.read_text())
        assert code.startswith("module\npublic import ")
        assert "@[expose] public section" in code
        assert not re.search(r"\b(?:sorry|admit|axiom|opaque)\b", code)


_WRONG_ENDPOINT_PROBE = r"""
noncomputable def resetKernel : FiniteKernel Bool Bool where
  mass _ state := irreversibleReverse state
  nonneg _ state := irreversibleReverse.nonneg state
  sum_one _ := irreversibleReverse.sum_one

example : IsReversible irreversibleReverse resetKernel := by
  intro source target
  change irreversibleReverse source * irreversibleReverse target =
    irreversibleReverse target * irreversibleReverse source
  ring

-- At horizon zero the actual endpoint is the initial law. Even for a
-- reversible reset kernel, substituting its stationary law gives positive
-- production, whereas the claimed initial-minus-initial KL drop is zero.
example : ¬ entropyProduction (markovPathProtocol resetKernel irreversibleForward
    resetKernel irreversibleReverse 0) =
    finiteKL irreversibleForward irreversibleReverse -
      finiteKL irreversibleForward irreversibleReverse := by
  have hInitial : ∀ state, 0 < irreversibleForward state := by
    intro state; cases state <;> norm_num [irreversibleForward]
  have hFinal : ∀ state, 0 < irreversibleReverse state := by
    intro state; cases state <;> norm_num [irreversibleReverse]
  have hKernel : ∀ source target, 0 < resetKernel source target := by
    intro source target; exact hFinal target
  rw [entropyProduction_markov_marginal_decomposition resetKernel resetKernel
    irreversibleForward irreversibleReverse hInitial hFinal hKernel hKernel 0]
  simp only [kernelPower_zero, FiniteKernel.predictive_identity,
    Fin.sum_univ_zero, add_zero, sub_self]
  rw [← finiteKL_eq_crossEntropy_sub_entropy irreversibleForward irreversibleReverse hFinal]
  exact ne_of_gt irreversibleBool_entropyProduction_pos
"""


@pytest.mark.serial_lean
def test_native_path_reductions_have_exact_types_and_standard_axioms(
    tmp_path: Path,
) -> None:
    names = tuple(f"FEP.PathThermodynamics.{name}" for name in NEW_FOUNDATION_THEOREMS)
    names += (f"FEPComposed.{BRIDGE}",)
    probe = tmp_path / "MarkovPathReductions.lean"
    probe.write_text(
        "module\nimport FepSketches.compositions.thermo_geometry\n"
        "open FEP FEP.PathThermodynamics FEP.FiniteMarkovDynamics FEP.FiniteInformation\n"
        "example (K : FiniteKernel Bool Bool) (p : FiniteLaw Bool)\n"
        "    (hp : ∀ state, 0 < p state) (hK : ∀ a b, 0 < K a b)\n"
        "    (hRev : IsReversible p K) (n : ℕ) :\n"
        "    entropyProduction (markovPathProtocol K p K p n) = 0 := by\n"
        "  rw [entropyProduction_markov_stationary_horizon K p hp hK\n"
        "    (isInvariant_of_isReversible p K hRev) n,\n"
        "    entropyProduction_markov_reversible_zero K p hRev, mul_zero]\n"
        "example : entropyProduction (markovPathProtocol biasedCycleKernel "
        "FiniteLaw.uniform biasedCycleKernel FiniteLaw.uniform 0) = 0 := by\n"
        "  simpa using biasedCycle_entropyProduction_horizon 0\n"
        "example : 0 < entropyProduction (markovPathProtocol biasedCycleKernel "
        "FiniteLaw.uniform biasedCycleKernel FiniteLaw.uniform 3) :=\n"
        "  biasedCycle_entropyProduction_horizon_pos 3 (by decide)\n"
        "example (K : FiniteKernel Bool Bool) (p : FiniteLaw Bool) :\n"
        "    (markovPathLaw K p 2).map (fun path => path (1 : Fin 3)) =\n"
        "      (kernelPower K 1).predictive p :=\n"
        "  markovPathLaw_map_coordinate K p 2 1\n"
        "example (K : FiniteKernel Bool Bool) (p : FiniteLaw Bool) :\n"
        "    (markovPathLaw K p 2).map (fun path => (path (1 : Fin 3), path 2)) =\n"
        "      K.joint ((kernelPower K 1).predictive p) :=\n"
        "  markovPathLaw_map_stage K p 2 1\n"
        + _WRONG_ENDPOINT_PROBE
        + "".join(f"#check {name}\n#print axioms {name}\n" for name in names)
    )
    result = run_lean_compile_probe(
        probe,
        cwd=ROOT / "lean",
        executable=lake_executable(missing="raise", context="finite path reductions"),
        timeout_s=300,
    )
    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "warning:" not in output.lower()
    assert "sorryAx" not in output
    for name in names:
        assert f"'{name}'" in output
    axiom_lists = re.findall(r"depends on axioms:\s*\[([^\]]*)\]", output)
    for axioms in axiom_lists:
        assert {name.strip() for name in axioms.split(",")} <= {
            "propext",
            "Classical.choice",
            "Quot.sound",
        }
