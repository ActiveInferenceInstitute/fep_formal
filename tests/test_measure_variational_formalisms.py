"""Native boundaries for the measure-Bayes and variational-duality families."""

from __future__ import annotations

import hashlib
import json
import os
import re
import runpy
import subprocess
from pathlib import Path

import pytest

from fep_lean.verification import formalism_audit
from tests._support.lake import lake_executable
from tests._support.lean_runner import run_lean_compile_probe

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LEAN_ROOT = PROJECT_ROOT / "lean"
FORMAL_ROOT = PROJECT_ROOT / "src" / "fep_lean" / "formal"
BODIES_ROOT = PROJECT_ROOT / "src" / "fep_lean" / "catalogue" / "bodies"

pytestmark = pytest.mark.serial_lean


def _compile(source: Path) -> subprocess.CompletedProcess[str]:
    return run_lean_compile_probe(
        source,
        cwd=LEAN_ROOT,
        timeout_s=300,
        executable=lake_executable(),
    )


def _bodies(module_name: str) -> dict[str, str]:
    namespace = runpy.run_path(BODIES_ROOT / f"{module_name}.py")
    return namespace["BODIES"]


def _compile_with_foundation(
    tmp_path: Path, *, foundation: str, topic_id: str, body: str
) -> subprocess.CompletedProcess[str]:
    import_line = f"import FepSketches.{foundation}\n"
    assert body.startswith(import_line)
    combined = tmp_path / f"{topic_id}.lean"
    combined.write_text(
        (FORMAL_ROOT / f"{foundation}.lean").read_text(encoding="utf-8")
        + "\n"
        + body.removeprefix(import_line),
        encoding="utf-8",
    )
    return _compile(combined)


def test_measure_bayes_foundation_compiles_warning_free() -> None:
    result = _compile(FORMAL_ROOT / "measure_bayes.lean")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "warning:" not in (result.stdout + result.stderr).lower()


def test_variational_duality_foundation_compiles_warning_free() -> None:
    result = _compile(FORMAL_ROOT / "variational_duality.lean")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "warning:" not in (result.stdout + result.stderr).lower()


def test_native_entropy_mathlib_only_consumers_compile(tmp_path: Path) -> None:
    """Compile the authored proof once without FEP imports, plus native controls."""
    foundation_path = FORMAL_ROOT / "variational_duality.lean"
    foundation_bytes = foundation_path.read_bytes()
    foundation = foundation_bytes.decode("utf-8")
    begin = "/- L06_MATHLIB_ONLY_BEGIN -/"
    end = "/- L06_MATHLIB_ONLY_END -/"
    assert foundation.count(begin) == foundation.count(end) == 1
    proof = foundation.split(begin, 1)[1].split(end, 1)[0]
    assert "FEP" not in proof
    declarations = (
        "nativeKL_tilted_gap",
        "nativeEntropy_le_klDiv",
        "nativeCgf_le_klDiv",
    )
    consumer = tmp_path / "native_entropy_mathlib_only.lean"
    consumer.write_text(
        "import Mathlib.InformationTheory.KullbackLeibler.Basic\n"
        "import Mathlib.Probability.Moments.Basic\n"
        "import Mathlib.Tactic\n"
        + proof
        + """
namespace NativeEntropyConsumer
open MeasureTheory InformationTheory
open scoped ENNReal

noncomputable def fair : Measure Bool :=
  (1 / 2 : ℝ≥0) • Measure.dirac true +
    (1 / 2 : ℝ≥0) • Measure.dirac false

instance : IsProbabilityMeasure fair where
  measure_univ := by norm_num [fair]

def potential (b : Bool) : ℝ := if b then Real.log 3 else 0

theorem fair_integral (g : Bool → ℝ) :
    (∫ b, g b ∂fair) = (g true + g false) / 2 := by
  rw [fair, integral_add_measure (Integrable.of_finite) (Integrable.of_finite)]
  norm_num [integral_smul_nnreal_measure, smul_eq_mul] <;> ring

theorem normalizer : (∫ b, Real.exp (potential b) ∂fair) = 2 := by
  rw [fair_integral]
  norm_num [potential, Real.exp_log (by norm_num : (0 : ℝ) < 3)]

noncomputable instance : IsProbabilityMeasure (fair.tilted potential) :=
  isProbabilityMeasure_tilted (Integrable.of_finite)

theorem tilted_true : fair.tilted potential {true} = 3 / 4 := by
  rw [tilted_apply' _ _ (MeasurableSet.singleton true), lintegral_singleton, normalizer]
  norm_num [potential, fair, Real.exp_log (by norm_num : (0 : ℝ) < 3)]

theorem tilted_false : fair.tilted potential {false} = 1 / 4 := by
  rw [tilted_apply' _ _ (MeasurableSet.singleton false), lintegral_singleton, normalizer]
  norm_num [potential, fair]

theorem tilted_ne_fair : fair.tilted potential ≠ fair := by
  intro h
  have hmass := congrArg (fun μ : Measure Bool => μ {true}) h
  rw [tilted_true] at hmass
  norm_num [fair] at hmass

theorem tilted_potential :
    (∫ b, potential b ∂fair.tilted potential) = 3 / 4 * Real.log 3 := by
  rw [integral_tilted, normalizer, fair_integral]
  norm_num [potential, Real.exp_log (by norm_num : (0 : ℝ) < 3), smul_eq_mul] <;> ring

theorem attained_real_gap :
    (klDiv (fair.tilted potential) fair).toReal =
      3 / 4 * Real.log 3 - Real.log 2 := by
  have h := nativeKL_tilted_gap (fair.tilted potential) fair
    (tilted_absolutelyContinuous fair potential) (Integrable.of_finite)
    (Integrable.of_finite) (Integrable.of_finite)
  rw [klDiv_self, ENNReal.toReal_zero, tilted_potential, normalizer] at h
  linarith

theorem attained_native_bound :
    ENNReal.ofReal (3 / 4 * Real.log 3 - Real.log 2) =
      klDiv (fair.tilted potential) fair := by
  rw [← attained_real_gap]
  exact ENNReal.ofReal_toReal (klDiv_ne_top
    (tilted_absolutelyContinuous fair potential) (Integrable.of_finite))

theorem cgf_bound :
    ENNReal.ofReal ((∫ b, potential b ∂fair.tilted potential) -
      ProbabilityTheory.cgf potential fair 1) ≤
        klDiv (fair.tilted potential) fair := by
  simpa only [one_mul] using nativeCgf_le_klDiv
    (fair.tilted potential) fair 1 (Integrable.of_finite) (Integrable.of_finite)

theorem clipped_equality_without_tilt :
    ENNReal.ofReal ((∫ b, potential b ∂fair) -
        Real.log (∫ b, Real.exp (potential b) ∂fair)) = klDiv fair fair ∧
      fair ≠ fair.tilted potential ∧
      (∫ b, potential b ∂fair) - Real.log (∫ b, Real.exp (potential b) ∂fair) ≠
        (klDiv fair fair).toReal := by
  have hlogFour : Real.log (4 : ℝ) = 2 * Real.log 2 := by
    rw [show (4 : ℝ) = 2 * 2 by norm_num,
      Real.log_mul (by norm_num) (by norm_num)]
    ring
  have hlog : Real.log (3 : ℝ) < 2 * Real.log 2 := by
    rw [← hlogFour]
    exact Real.log_lt_log (by norm_num) (by norm_num)
  have hnegative : (∫ b, potential b ∂fair) -
      Real.log (∫ b, Real.exp (potential b) ∂fair) < 0 := by
    rw [fair_integral, normalizer]
    norm_num [potential]
    linarith
  refine ⟨?_, Ne.symm tilted_ne_fair, ?_⟩
  · rw [klDiv_self]
    exact ENNReal.ofReal_eq_zero.mpr hnegative.le
  · simpa only [klDiv_self, ENNReal.toReal_zero] using hnegative.ne

theorem singular_kl :
    klDiv (Measure.dirac true : Measure Bool) (Measure.dirac false) = ∞ := by
  apply klDiv_of_not_ac
  intro h
  have hzero : (Measure.dirac false : Measure Bool) {true} = 0 := by simp
  have hactual := h hzero
  simpa using hactual

theorem singular_extended_bound :
    ENNReal.ofReal (Real.log 3) ≤
      klDiv (Measure.dirac true : Measure Bool) (Measure.dirac false) := by
  simpa [potential] using nativeEntropy_le_klDiv
    (Measure.dirac true : Measure Bool) (Measure.dirac false)
    (f := potential) (Integrable.of_finite) (Integrable.of_finite)

theorem singular_real_bound_fails :
    ¬ Real.log 3 ≤
      (klDiv (Measure.dirac true : Measure Bool) (Measure.dirac false)).toReal := by
  rw [singular_kl, ENNReal.toReal_top]
  exact not_le_of_gt (Real.log_pos (by norm_num))

end NativeEntropyConsumer
"""
        + "\n".join(f"#print axioms {name}" for name in declarations)
        + "\n",
        encoding="utf-8",
    )
    consumer_bytes = consumer.read_bytes()
    result = run_lean_compile_probe(
        consumer,
        cwd=LEAN_ROOT,
        timeout_s=300,
        executable=lake_executable(
            missing="raise", context="the Mathlib-only native entropy acceptance probe"
        ),
    )
    if os.environ.get("FEP_LEAN_NATIVE_ENTROPY_EVIDENCE") == "1":
        evidence = PROJECT_ROOT / "output" / "native-entropy-consumer.log"
        evidence.parent.mkdir(parents=True, exist_ok=True)
        evidence.write_text(
            json.dumps(
                {
                    "schema": "fep-formal.native-entropy-consumer.v1",
                    "canonical_source": foundation_path.relative_to(
                        PROJECT_ROOT
                    ).as_posix(),
                    "canonical_source_sha256": hashlib.sha256(
                        foundation_bytes
                    ).hexdigest(),
                    "canonical_proof_block_sha256": hashlib.sha256(
                        proof.encode("utf-8")
                    ).hexdigest(),
                    "consumer_source_sha256": hashlib.sha256(
                        consumer_bytes
                    ).hexdigest(),
                    "consumer_source": consumer_bytes.decode("utf-8"),
                    "expected_axiom_declarations": declarations,
                    "argv": result.args,
                    "cwd": str(LEAN_ROOT),
                    "timeout_sec": 300,
                    "returncode": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "warning:" not in output.lower()
    parsed, errors = formalism_audit.parse_axiom_output(output, expected=declarations)
    assert errors == ()
    assert tuple(parsed) == declarations
    for declaration, axioms in parsed.items():
        assert set(axioms) <= {"propext", "Classical.choice", "Quot.sound"}, (
            declaration,
            axioms,
        )


def test_measure_bayesian_inversion_family_owns_ordered_standalone_bodies() -> None:
    bodies = _bodies("measure_bayesian_inversion")

    assert tuple(bodies) == tuple(f"fep-{number:03d}" for number in range(51, 58))
    for number, body in zip(range(51, 58), bodies.values(), strict=True):
        assert body.startswith("import FepSketches.measure_bayes\n")
        assert f"namespace FEP{number:03d}\n" in body
        assert f"end FEP{number:03d}\n" in body
        assert f"theorem fep{number:03d}_" in body
        assert "sorry" not in body
        assert "axiom " not in body


def test_standard_borel_disintegration_topic_compiles_at_native_boundary(
    tmp_path: Path,
) -> None:
    body = _bodies("measure_bayesian_inversion")["fep-056"]
    result = _compile_with_foundation(
        tmp_path,
        foundation="measure_bayes",
        topic_id="fep-056",
        body=body,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "warning:" not in (result.stdout + result.stderr).lower()


def test_variational_duality_family_owns_ordered_standalone_bodies() -> None:
    bodies = _bodies("variational_duality")

    assert tuple(bodies) == tuple(f"fep-{number:03d}" for number in range(58, 65))
    for number, body in zip(range(58, 65), bodies.values(), strict=True):
        assert body.startswith("import FepSketches.variational_duality\n")
        assert f"namespace FEP{number:03d}\n" in body
        assert f"end FEP{number:03d}\n" in body
        assert f"theorem fep{number:03d}_" in body
        assert "sorry" not in body
        assert "axiom " not in body


def test_donsker_varadhan_topic_compiles_with_full_support_visible(
    tmp_path: Path,
) -> None:
    body = _bodies("variational_duality")["fep-059"]
    result = _compile_with_foundation(
        tmp_path,
        foundation="variational_duality",
        topic_id="fep-059",
        body=body,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "warning:" not in (result.stdout + result.stderr).lower()


def test_finite_channel_data_processing_compiles_with_support_boundary(
    tmp_path: Path,
) -> None:
    body = _bodies("variational_duality")["fep-063"]
    result = _compile_with_foundation(
        tmp_path,
        foundation="variational_duality",
        topic_id="fep-063",
        body=body,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "warning:" not in (result.stdout + result.stderr).lower()


@pytest.mark.parametrize(
    ("module_name", "foundation"),
    [
        ("measure_bayesian_inversion", "measure_bayes"),
        ("variational_duality", "variational_duality"),
    ],
)
def test_family_body_closure_compiles_warning_free(
    tmp_path: Path, module_name: str, foundation: str
) -> None:
    import_line = f"import FepSketches.{foundation}\n"
    combined = tmp_path / f"{module_name}.lean"
    bodies = _bodies(module_name)
    combined.write_text(
        (FORMAL_ROOT / f"{foundation}.lean").read_text(encoding="utf-8")
        + "\n"
        + "\n".join(body.removeprefix(import_line) for body in bodies.values()),
        encoding="utf-8",
    )

    result = _compile(combined)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "warning:" not in (result.stdout + result.stderr).lower()


def test_iwae_topic_fixes_a_positive_sample_count_and_iid_product_law() -> None:
    foundation = (FORMAL_ROOT / "variational_duality.lean").read_text(encoding="utf-8")
    body = _bodies("variational_duality")["fep-062"]

    assert "def iidProductLaw" in foundation
    assert "def sampleMeanWeight" in foundation
    assert "theorem fixedSampleImportanceJensen" in foundation
    assert "[NeZero sampleCount]" in foundation
    assert "theorem fep062_iidProduct_importanceJensen" in body


def test_gibbs_certificate_has_a_compiled_nonvacuity_witness() -> None:
    foundation = (FORMAL_ROOT / "variational_duality.lean").read_text(encoding="utf-8")
    body = _bodies("variational_duality")["fep-058"]

    assert "def uniformZeroPotentialGibbs" in foundation
    assert "theorem uniformZeroPotentialGibbs_objective" in foundation
    assert "theorem fep058_uniformGibbs_nonvacuity" in body


def test_family_declaration_names_are_unique_stable_and_topic_scoped() -> None:
    expected = {
        "fep-051": (
            "fep051_likelihoodRatio_reconstruction",
            "fep051_reconstruction_iff_absoluteContinuous",
        ),
        "fep-052": (
            "fep052_posterior_density_tilt",
            "fep052_countable_posterior_density_tilt",
        ),
        "fep-053": (
            "fep053_kernelBayes_joint_reconstruction",
            "fep053_finiteBayes_atom_reconstruction",
        ),
        "fep-054": (
            "fep054_bayes_involution",
            "fep054_posterior_reconstructs_prior",
        ),
        "fep-055": (
            "fep055_compositeKernel_bayesInversion",
            "fep055_compositePredictive_associativity",
        ),
        "fep-056": (
            "fep056_standardBorel_condKernel_reconstruction",
            "fep056_standardBorel_condKernel_mass_one",
        ),
        "fep-057": (
            "fep057_conditionalExpectation_tower",
            "fep057_conditionalLIntegral_tower",
        ),
        "fep-058": (
            "fep058_gibbsVariational_lower_bound",
            "fep058_gibbsVariational_optimizer",
            "fep058_uniformGibbs_nonvacuity",
        ),
        "fep-059": (
            "fep059_donskerVaradhan_upper_bound",
            "fep059_donskerVaradhan_optimizer",
            "fep059_donskerVaradhan_equality_iff",
        ),
        "fep-060": (
            "fep060_coordinateELBO_decomposition",
            "fep060_coordinateKL_nonnegative",
        ),
        "fep-061": (
            "fep061_meanFieldCoordinate_reduction",
            "fep061_meanFieldCoordinate_optimum_iff",
        ),
        "fep-062": (
            "fep062_iidProduct_importanceJensen",
            "fep062_fixedSample_importanceJensen",
            "fep062_expectedImportanceWeight_positive",
        ),
        "fep-063": (
            "fep063_finiteChannel_klDataProcessing",
            "fep063_referencePredictive_fullSupport",
            "fep063_identityChannel_preservesKL",
            "fep063_constantChannel_strict",
        ),
        "fep-064": (
            "fep064_rateDistortion_weakDuality",
            "fep064_zeroMultiplier_boundary",
            "fep064_rateDistortion_exists_minimizer",
            "fep064_rateDistortion_dual_lower_bound",
            "fep064_dual_zeroMultiplier",
            "fep064_negativeBudget_infeasible",
            "fep064_quarterBudget_informative_optimum",
            "fep064_halfBudget_nonunique",
            "fep064_zeroBudget_unique",
        ),
    }
    bodies = {
        **_bodies("measure_bayesian_inversion"),
        **_bodies("variational_duality"),
    }

    actual = {
        topic_id: tuple(
            re.findall(r"^theorem\s+([A-Za-z][A-Za-z0-9_]*)", body, re.MULTILINE)
        )
        for topic_id, body in bodies.items()
    }
    assert actual == expected
    names = [name for topic_names in actual.values() for name in topic_names]
    assert len(names) == len(set(names))


def test_rate_distortion_optimization_consumers_compile(tmp_path: Path) -> None:
    """Exercise informative, infeasible, unique, and nonunique budget faces."""
    consumer = tmp_path / "rate_distortion_consumers.lean"
    consumer.write_text(
        (FORMAL_ROOT / "variational_duality.lean").read_text(encoding="utf-8")
        + """
namespace RateDistortionConsumer
open FEP FEP.FiniteInformation FEP.VariationalDuality

example : ¬ ∃ joint, RateDistortionFeasible (FiniteLaw.uniform : FiniteLaw Bool)
    boolHammingDistortion (-1) joint :=
  rateDistortion_infeasible_of_negativeBudget _ _ _ boolHammingDistortion_nonneg (by norm_num)

example : RateDistortionFeasible FiniteLaw.uniform boolHammingDistortion (1 / 4)
    boolQuarterDistortionJoint := boolQuarterDistortionJoint_feasible

example : ∃ optimizer : FiniteLaw (Bool × Bool),
    RateDistortionFeasible FiniteLaw.uniform boolHammingDistortion (1 / 4) optimizer ∧
      0 < mutualInformation optimizer ∧
        ∀ candidate, RateDistortionFeasible FiniteLaw.uniform boolHammingDistortion
          (1 / 4) candidate → mutualInformation optimizer ≤ mutualInformation candidate :=
  boolQuarterBudget_exists_positive_minimizer

example : rateDistortionDualValue (FiniteLaw.uniform : FiniteLaw Bool)
    boolHammingDistortion (1 / 4) 2 ≤ mutualInformation boolQuarterDistortionJoint :=
  rateDistortionDual_le_feasible_information _ _ _ _ boolHammingDistortion_nonneg
    (by norm_num) _ boolQuarterDistortionJoint_feasible

example : rateDistortionDualValue (FiniteLaw.uniform : FiniteLaw Bool)
    boolHammingDistortion (-1) 0 = 0 := rateDistortionDual_zeroMultiplier _ _ _

example (joint : FiniteLaw (Bool × Bool))
    (hjoint : RateDistortionFeasible FiniteLaw.uniform boolHammingDistortion 0 joint) :
    joint = boolZeroDistortionJoint := boolZeroBudget_unique_feasible joint hjoint

example : ∃ left right : FiniteLaw (Bool × Bool), left ≠ right ∧
    (RateDistortionFeasible FiniteLaw.uniform boolHammingDistortion (1 / 2) left ∧
      ∀ candidate, RateDistortionFeasible FiniteLaw.uniform boolHammingDistortion
        (1 / 2) candidate → mutualInformation left ≤ mutualInformation candidate) ∧
    (RateDistortionFeasible FiniteLaw.uniform boolHammingDistortion (1 / 2) right ∧
      ∀ candidate, RateDistortionFeasible FiniteLaw.uniform boolHammingDistortion
        (1 / 2) candidate → mutualInformation right ≤ mutualInformation candidate) :=
  boolHalfBudget_distinct_minimizers
end RateDistortionConsumer
""",
        encoding="utf-8",
    )
    result = _compile(consumer)
    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "warning:" not in output.lower()
