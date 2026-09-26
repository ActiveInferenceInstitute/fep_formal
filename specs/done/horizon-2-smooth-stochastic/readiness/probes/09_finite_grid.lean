import Mathlib.Probability.Distributions.Gaussian.Real
import Mathlib.Probability.Kernel.IonescuTulcea.PartialTraj

open MeasureTheory ProbabilityTheory

abbrev ReadinessGridState : ℕ -> Type := fun _ => ℝ

noncomputable def readinessStepKernel (n : ℕ) :
    Kernel
      (Π i : Finset.Iic n, ReadinessGridState i)
      (ReadinessGridState (n + 1)) :=
  Kernel.const _ (gaussianReal 0 1)

instance (n : ℕ) : IsMarkovKernel (readinessStepKernel n) := by
  rw [readinessStepKernel]
  infer_instance

-- H2-READINESS-ROW: finite_grid_trajectory
example :
    IsMarkovKernel (Kernel.partialTraj readinessStepKernel 0 3) ∧
      Kernel.partialTraj readinessStepKernel 1 3 ∘ₖ
          Kernel.partialTraj readinessStepKernel 0 1 =
        Kernel.partialTraj readinessStepKernel 0 3 ∧
      (Kernel.partialTraj readinessStepKernel 0 3
          (fun _ => (0 : ℝ))) Set.univ = 1 := by
  constructor
  · infer_instance
  constructor
  · exact Kernel.partialTraj_comp_partialTraj (by norm_num) (by norm_num)
  · exact measure_univ
