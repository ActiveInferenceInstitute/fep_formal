import Mathlib.Analysis.Calculus.Deriv.Add
import Mathlib.Analysis.Calculus.FDeriv.Add
import Mathlib.Analysis.Calculus.FDeriv.Pi
import Mathlib.Analysis.SpecialFunctions.ExpDeriv
import Mathlib.Analysis.SpecialFunctions.Log.Deriv

open scoped BigOperators

-- H2-READINESS-ROW: finite_sum_derivatives
example {ι : Type*} (s : Finset ι)
    (f : ι → ℝ → ℝ) (f' : ι → ℝ) (x : ℝ)
    (h : ∀ i ∈ s, HasDerivAt (f i) (f' i) x) :
    HasDerivAt (fun y ↦ ∑ i ∈ s, f i y) (∑ i ∈ s, f' i) x := by
  exact HasDerivAt.fun_sum h

-- H2-READINESS-ROW: real_exp_log_derivatives
example (x : ℝ) (hx : x ≠ 0) :
    HasDerivAt (fun y ↦ Real.exp y + Real.log y)
      (Real.exp x + x⁻¹) x := by
  exact (Real.hasDerivAt_exp x).add (Real.hasDerivAt_log hx)

-- H2-READINESS-ROW: matrix_valued_frechet_derivative
example (x : ℝ) :
    HasFDerivAt
      (fun y : ℝ =>
        (fun _ : Fin 2 => fun _ : Fin 2 => y : Matrix (Fin 2) (Fin 2) ℝ))
      (ContinuousLinearMap.pi fun _ =>
        ContinuousLinearMap.pi fun _ => ContinuousLinearMap.id ℝ ℝ) x := by
  rw [hasFDerivAt_pi]
  intro _
  rw [hasFDerivAt_pi]
  intro _
  exact hasFDerivAt_id x
