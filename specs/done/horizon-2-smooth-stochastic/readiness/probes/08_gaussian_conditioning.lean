import Mathlib.LinearAlgebra.Matrix.PosDef
import Mathlib.LinearAlgebra.Matrix.SchurComplement
import Mathlib.Probability.Distributions.Gaussian.Multivariate
import Mathlib.Probability.Distributions.Gaussian.Real
import Mathlib.Probability.Kernel.CondDistrib
import Mathlib.Probability.Kernel.Posterior

open Matrix MeasureTheory ProbabilityTheory
open scoped ProbabilityTheory

noncomputable def readinessGaussianObservation : Kernel ℝ ℝ :=
  { toFun := fun state => gaussianReal state 1
    measurable' :=
      measurable_gaussianReal.comp (measurable_id.prodMk measurable_const) }

noncomputable instance readinessGaussianObservation_isMarkov :
    IsMarkovKernel readinessGaussianObservation :=
  ⟨fun state => by
    change IsProbabilityMeasure (gaussianReal state 1)
    infer_instance⟩

-- H2-READINESS-BLOCKING: gaussian_conditioning_precision
example {m n : Type*} [Fintype m] [Fintype n]
    [DecidableEq m] [DecidableEq n]
    {A : Matrix m m ℝ} (B : Matrix m n ℝ) (D : Matrix n n ℝ)
    (hA : A.PosDef) [Invertible A] :
    (Matrix.fromBlocks A B Bᴴ D).PosSemidef ↔
      (D - Bᴴ * A⁻¹ * B).PosSemidef :=
  Matrix.PosDef.fromBlocks₁₁ B D hA

-- This compiles the native posterior owner and its disintegration law.  It
-- deliberately does not claim a Gaussian closed form or precision-zero
-- conditional independence: the pinned source exposes neither theorem.
-- H2-READINESS-BLOCKING: native_filter_posterior
example :
    let observation : Kernel ℝ ℝ := readinessGaussianObservation
    let prior : Measure ℝ := gaussianReal 0 1
    IsMarkovKernel (ProbabilityTheory.posterior observation prior) ∧
      (observation ∘ₘ prior) ⊗ₘ
          ProbabilityTheory.posterior observation prior =
        (prior ⊗ₘ observation).map Prod.swap := by
  dsimp only
  exact ⟨inferInstance, compProd_posterior_eq_map_swap⟩
