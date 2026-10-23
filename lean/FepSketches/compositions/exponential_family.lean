module
public import FepSketches.families.core_bayesian_mechanics
public import FepSketches.families.core_free_energy
public import FepSketches.families.core_information_geometry
public import FepSketches.families.core_thermodynamics
public import FepSketches.families.exponential_family_geometry
public import FepSketches.families.geometric_optimization
public import FepSketches.exponential_family

@[expose] public section

/-!
# Finite exponential-family topic compositions

These bridges pair the finite scalar exponential-family laws with their
nearest established catalog endpoints.  Separate carriers stay visible in
conjunctions; no bridge claims an unproved identification between finite
real-valued geometry and Mathlib's measure-native information theory.
-/

namespace FEPComposed

open FEP FEP.ExponentialFamily FEP.FiniteInformation
  FEP.GeometricOptimization FEP.InformationGeometry
open MeasureTheory ProbabilityTheory Finset
open scoped BigOperators ENNReal Matrix MeasureTheory ProbabilityTheory

/-- Finite exponential-family normalization is paired with the original
finite Gibbs normalization, without identifying their parameterizations. -/
theorem fep142_exponentialNormalization_extends_fep031
    {Outcome : Type*} [Fintype Outcome] [Nonempty Outcome]
    (family : ScalarExponentialFamily Outcome) (parameter beta : ℝ)
    (size : ℕ) (energy : Fin size → ℝ) (support : Finset (Fin size))
    (hSupport : support.Nonempty) :
    (∑ outcome, family.law parameter outcome = 1) ∧
      (∑ state ∈ support,
        fep_fep031.FEP031.fep031_gibbsProbability
          beta size energy support state = 1) := by
  exact
    ⟨fep_fep142.FEP142.fep142_exponentialFamily_sum_one family parameter,
      fep_fep031.FEP031.fep031_gibbsProbability_sum_one
        beta size energy support hSupport⟩

/-- The exponential-family affine log-density ratio and the original positive
scalar logarithmic quotient rule remain explicit on their own carriers. -/
theorem fep143_logDensityRatio_extends_fep026
    {Outcome : Type*} [Fintype Outcome] [Nonempty Outcome]
    (family : ScalarExponentialFamily Outcome)
    (left right : ℝ) (outcome : Outcome)
    {numerator denominator : ℝ} (hNumerator : 0 < numerator)
    (hDenominator : 0 < denominator) :
    (Real.log (family.law left outcome / family.law right outcome) =
      (left - right) * family.statistic outcome -
        (family.logPartition left - family.logPartition right)) ∧
      Real.log (numerator / denominator) =
        Real.log numerator - Real.log denominator := by
  exact
    ⟨fep_fep143.FEP143.fep143_logDensityRatio_eq
        family left right outcome,
      fep_fep026.FEP026.fep026_log_div hNumerator hDenominator⟩

/-- The finite log-partition gradient and the original Gaussian entropy
gradient are paired as two genuine scalar derivative certificates. -/
theorem fep144_logPartitionGradient_extends_fep040
    {Outcome : Type*} [Fintype Outcome] [Nonempty Outcome]
    (family : ScalarExponentialFamily Outcome) (parameter : ℝ)
    {variance : ℝ} (hVariance : 0 < variance) :
    HasDerivAt family.logPartition (family.mean parameter) parameter ∧
      HasDerivAt fep_fep040.FEP040.fep040_gaussianEntropy
        (1 / (2 * variance)) variance := by
  exact
    ⟨fep_fep144.FEP144.fep144_logPartition_hasDerivAt family parameter,
      fep_fep040.FEP040.fep040_gaussianEntropy_hasDerivAt hVariance⟩

/-- Centering the exponential-family score is paired with the original
interior Bernoulli zero-mean score calculation. -/
theorem fep145_centeredScore_extends_fep038
    {Outcome : Type*} [Fintype Outcome] [Nonempty Outcome]
    (family : ScalarExponentialFamily Outcome) (parameter : ℝ)
    (outcome : Outcome) {probability : ℝ}
    (hProbabilityPositive : 0 < probability)
    (hProbabilityBelowOne : probability < 1) :
    (family.score parameter outcome =
      family.statistic outcome - family.mean parameter) ∧
      (∑ state : Bool,
        fep_fep038.FEP038.fep038_bernoulliMass probability state *
          fep_fep038.FEP038.fep038_score probability state = 0) := by
  exact
    ⟨fep_fep145.FEP145.fep145_score_eq_statistic_sub_mean
        family parameter outcome,
      fep_fep038.FEP038.fep038_expectedScore_zero
        hProbabilityPositive hProbabilityBelowOne⟩

/-- Scalar Fisher--variance equality and full-support categorical Fisher
positivity are retained as distinct finite geometric certificates. -/
theorem fep146_fisherVariance_extends_fep100
    {Outcome : Type*} [Fintype Outcome] [Nonempty Outcome]
    {dimension : ℕ}
    (family : ScalarExponentialFamily Outcome) (parameter : ℝ)
    (carrier : CategoricalFisherCarrier dimension)
    (tangent : Fin dimension → ℝ) (hTangent : IsSimplexTangent tangent)
    (hNonzero : tangent ≠ 0) :
    family.fisher parameter = family.variance parameter ∧
      0 < fisherMetric carrier.model tangent tangent := by
  exact
    ⟨fep_fep146.FEP146.fep146_fisher_eq_variance family parameter,
      fep_fep100.FEP100.fep100_categoricalFisher_simplexTangent_positivity
        carrier tangent hTangent hNonzero⟩

/-- Finite exponential-family KL is a log-partition Bregman divergence, while
the original measure-native KL retains its separate nonnegativity law. -/
theorem fep147_KLBregman_connects_fep014_fep104
    {Outcome Native : Type*} [Fintype Outcome] [Nonempty Outcome]
    [MeasurableSpace Native]
    (family : ScalarExponentialFamily Outcome) (left right : ℝ)
    (nativeLeft nativeRight : Measure Native) :
    finiteKL (family.law left) (family.law right) =
        family.logPartitionBregman left right ∧
      0 ≤ InformationTheory.klDiv nativeLeft nativeRight := by
  exact
    ⟨fep_fep147.FEP147.fep147_exponentialFamily_KL_eq_bregman
        family left right,
      fep_fep014.FEP014.fep014_kl_nonneg nativeLeft nativeRight⟩

/-- Injectivity of the natural-to-mean coordinate on a positive-variance
interval is paired with the established full-rank natural-gradient chart law. -/
theorem fep148_meanCoordinate_extends_fep103
    {Outcome Native : Type*} [Fintype Outcome] [Nonempty Outcome]
    [Fintype Native] {dimension : ℕ}
    (family : ScalarExponentialFamily Outcome) {lower upper : ℝ}
    (hVariance : ∀ parameter ∈ Set.Icc lower upper,
      0 < family.variance parameter)
    (model : ScoreModel Native dimension) [Invertible (fisherMatrix model)]
    (jacobian : Matrix (Fin dimension) (Fin dimension) ℝ)
    [Invertible jacobian] (covector : Fin dimension → ℝ) :
    Set.InjOn family.mean (Set.Icc lower upper) ∧
      chartPullbackLower model jacobian
          (chartCoordinates jacobian (naturalGradient model covector)) =
        chartCovector jacobian covector := by
  exact
    ⟨fep_fep148.FEP148.fep148_meanParameter_injective family hVariance,
      fep_fep103.FEP103.fep103_naturalGradient_equivariance
        model jacobian covector⟩

end FEPComposed
