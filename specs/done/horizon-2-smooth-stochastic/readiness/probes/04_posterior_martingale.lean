import Mathlib.MeasureTheory.Function.ConditionalExpectation.Basic
import Mathlib.Probability.Decision.BayesEstimator
import Mathlib.Probability.Kernel.Posterior
import Mathlib.Probability.Martingale.Convergence

open Filter MeasureTheory ProbabilityTheory
open scoped MeasureTheory ProbabilityTheory Topology

-- H2-READINESS-ROW: posterior_kernel
example :
    IsMarkovKernel
      (ProbabilityTheory.posterior
        (Kernel.id : Kernel Bool Bool)
        (Measure.dirac false)) := by
  infer_instance

-- H2-READINESS-ROW: conditional_expectation
example {Omega E : Type*} {m : MeasurableSpace Omega}
    [NormedAddCommGroup E] [NormedSpace Real E] [CompleteSpace E]
    {mu : Measure Omega} {f : Omega -> E} :
    Integrable (mu[f | m]) mu := by
  exact integrable_condExp

-- H2-READINESS-ROW: martingale_convergence
example {Omega : Type*} {m0 : MeasurableSpace Omega} {mu : Measure Omega}
    {filtration : Filtration Nat m0} {g : Omega -> Real}
    [IsFiniteMeasure mu]
    (hg : Integrable g mu)
    (hgmeas : StronglyMeasurable[⨆ n, filtration n] g) :
    ∀ᵐ x ∂mu,
      Tendsto (fun n => (mu[g | filtration n]) x) atTop (𝓝 (g x)) := by
  exact hg.tendsto_ae_condExp hgmeas

-- H2-READINESS-OPTIONAL: bayes_estimator
#check ProbabilityTheory.IsBayesEstimator
#check ProbabilityTheory.IsArgminEstimator.isBayesEstimator
