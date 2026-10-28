"""Canonical Lean bodies for finite scalar exponential-family geometry."""

from __future__ import annotations

BODIES: dict[str, str] = {
    "fep-142": """import FepSketches.exponential_family

namespace FEP142

open FEP FEP.ExponentialFamily Finset
open scoped BigOperators

variable {Outcome : Type*} [Fintype Outcome] [Nonempty Outcome]

/-- Positive finite base weights normalize to a probability law at every
natural parameter. -/
theorem fep142_exponentialFamily_sum_one
    (family : ScalarExponentialFamily Outcome) (parameter : ℝ) :
    ∑ outcome, family.law parameter outcome = 1 :=
  (family.law parameter).sum_one

/-- Strictly positive base weights give pointwise full support. -/
theorem fep142_exponentialFamily_pointwise_pos
    (family : ScalarExponentialFamily Outcome) (parameter : ℝ)
    (outcome : Outcome) :
    0 < family.law parameter outcome :=
  family.law_pos parameter outcome

end FEP142
""",
    "fep-143": """import FepSketches.exponential_family

namespace FEP143

open FEP FEP.ExponentialFamily

variable {Outcome : Type*} [Fintype Outcome] [Nonempty Outcome]

/-- The supported log-density ratio is affine in the sufficient statistic. -/
theorem fep143_logDensityRatio_eq
    (family : ScalarExponentialFamily Outcome)
    (left right : ℝ) (outcome : Outcome) :
    Real.log
        (family.law left outcome / family.law right outcome) =
      (left - right) * family.statistic outcome -
        (family.logPartition left - family.logPartition right) :=
  family.logDensityRatio_eq left right outcome

end FEP143
""",
    "fep-144": """import FepSketches.exponential_family

namespace FEP144

open FEP FEP.ExponentialFamily

variable {Outcome : Type*} [Fintype Outcome] [Nonempty Outcome]

/-- The derivative of the finite log-partition function is the expected
sufficient statistic. -/
theorem fep144_logPartition_hasDerivAt
    (family : ScalarExponentialFamily Outcome) (parameter : ℝ) :
    HasDerivAt family.logPartition (family.mean parameter) parameter :=
  family.logPartition_hasDerivAt parameter

end FEP144
""",
    "fep-145": """import FepSketches.exponential_family

namespace FEP145

open FEP FEP.ExponentialFamily Finset
open scoped BigOperators

variable {Outcome : Type*} [Fintype Outcome] [Nonempty Outcome]

omit [Nonempty Outcome] in
/-- Differentiating log density centers the sufficient statistic. -/
theorem fep145_score_eq_statistic_sub_mean
    (family : ScalarExponentialFamily Outcome) (parameter : ℝ)
    (outcome : Outcome) :
    family.score parameter outcome =
      family.statistic outcome - family.mean parameter :=
  family.score_eq_statistic_sub_mean parameter outcome

/-- The normalized finite score has zero expectation. -/
theorem fep145_score_mean_zero
    (family : ScalarExponentialFamily Outcome) (parameter : ℝ) :
    ∑ outcome,
      family.law parameter outcome * family.score parameter outcome = 0 :=
  family.mean_score_zero parameter

end FEP145
""",
    "fep-146": """import FepSketches.exponential_family

namespace FEP146

open FEP FEP.ExponentialFamily

variable {Outcome : Type*} [Fintype Outcome] [Nonempty Outcome]

/-- Since the first log-partition derivative is the mean coordinate, its
second derivative is the sufficient-statistic variance. -/
theorem fep146_logPartition_secondDeriv_eq_variance
    (family : ScalarExponentialFamily Outcome) (parameter : ℝ) :
    HasDerivAt family.mean (family.variance parameter) parameter :=
  family.mean_hasDerivAt parameter

/-- Scalar Fisher information is exactly the same centered variance. -/
theorem fep146_fisher_eq_variance
    (family : ScalarExponentialFamily Outcome) (parameter : ℝ) :
    family.fisher parameter = family.variance parameter :=
  family.fisher_eq_variance parameter

/-- The explicit nonconstant three-state statistic has strictly positive
variance at the origin. -/
theorem fep146_threeState_variance_positive :
    0 < ScalarExponentialFamily.threeStateFamily.variance 0 :=
  ScalarExponentialFamily.threeState_variance_zero_pos

/-- A constant statistic is the exact zero-Fisher boundary. -/
theorem fep146_constantStatistic_zero_boundary
    (base : Outcome → ℝ) (hBase : ∀ outcome, 0 < base outcome)
    (constant parameter : ℝ) :
    (ScalarExponentialFamily.constantStatisticFamily base hBase constant).fisher
        parameter = 0 := by
  rw [ScalarExponentialFamily.fisher_eq_variance,
    ScalarExponentialFamily.constantStatistic_variance_zero]

end FEP146
""",
    "fep-147": """import FepSketches.exponential_family

namespace FEP147

open FEP FEP.ExponentialFamily FEP.FiniteInformation

variable {Outcome : Type*} [Fintype Outcome] [Nonempty Outcome]

/-- Full-support finite KL equals the Bregman divergence of the
log-partition potential. -/
theorem fep147_exponentialFamily_KL_eq_bregman
    (family : ScalarExponentialFamily Outcome) (left right : ℝ) :
    finiteKL (family.law left) (family.law right) =
      family.logPartitionBregman left right :=
  family.finiteKL_eq_logPartitionBregman left right

/-- The support premise used by the logarithmic KL representation is
constructively available at every atom. -/
theorem fep147_exponentialFamily_fullSupport
    (family : ScalarExponentialFamily Outcome) (parameter : ℝ)
    (outcome : Outcome) :
    0 < family.law parameter outcome :=
  family.law_pos parameter outcome

end FEP147
""",
    "fep-148": """import FepSketches.exponential_family

namespace FEP148

open FEP FEP.ExponentialFamily

variable {Outcome : Type*} [Fintype Outcome] [Nonempty Outcome]

/-- Positive variance throughout a closed interval makes the natural-to-mean
coordinate map strictly monotone there. -/
theorem fep148_meanParameter_strictMono
    (family : ScalarExponentialFamily Outcome) {lower upper : ℝ}
    (hVariance : ∀ parameter ∈ Set.Icc lower upper,
      0 < family.variance parameter) :
    StrictMonoOn family.mean (Set.Icc lower upper) :=
  family.meanParameter_strictMono hVariance

/-- Hence the mean coordinate is injective on the same stated interval. -/
theorem fep148_meanParameter_injective
    (family : ScalarExponentialFamily Outcome) {lower upper : ℝ}
    (hVariance : ∀ parameter ∈ Set.Icc lower upper,
      0 < family.variance parameter) :
    Set.InjOn family.mean (Set.Icc lower upper) :=
  family.meanParameter_injectiveOn hVariance

end FEP148
""",
}
