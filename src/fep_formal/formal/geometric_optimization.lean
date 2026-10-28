module
public import FepSketches.information_geometry

@[expose] public section

/-!
# Information geometry and geometric optimization

The constructions below extend `FEP.InformationGeometry.ScoreModel` and its
Fisher carrier.  A categorical certificate records the exact bridge from a
simplex tangent to the inherited Fisher metric and lowering map; it does not
introduce a second, unrelated metric.  Rank, support, unbiasedness, score
regularity, chart invertibility, and affine-projection assumptions remain
visible at every boundary where they are needed.
-/

namespace FEP.GeometricOptimization

open FEP FEP.InformationGeometry Finset
open scoped BigOperators Matrix

variable {Outcome : Type*} [Fintype Outcome]
variable {d k : ℕ}

/-! ## Categorical simplex tangents on the existing Fisher carrier -/

/-- Tangent space of the affine probability simplex. -/
def IsSimplexTangent (tangent : Fin d → ℝ) : Prop :=
  ∑ coordinate, tangent coordinate = 0

/-- A certificate that the inherited `ScoreModel` Fisher geometry has the
categorical simplex representation.  The two representation fields are the
explicit bridge to `fisherMetric` and `lowerTangent`. -/
structure CategoricalFisherCarrier (d : ℕ) where
  law : FiniteLaw (Fin d)
  law_pos : ∀ outcome, 0 < law outcome
  model : ScoreModel (Fin d) d
  model_law : model.law = law
  metric_on_tangent : ∀ tangent,
    IsSimplexTangent tangent →
      fisherMetric model tangent tangent =
        ∑ coordinate, tangent coordinate ^ 2 / law coordinate
  lower_on_tangent : ∀ tangent,
    IsSimplexTangent tangent →
      lowerTangent model tangent =
        fun coordinate ↦ tangent coordinate / law coordinate

/-- The categorical Fisher quadratic form is strictly positive on every
nonzero simplex tangent under full support. -/
theorem categoricalFisher_pos
    (carrier : CategoricalFisherCarrier d)
    (tangent : Fin d → ℝ) (hTangent : IsSimplexTangent tangent)
    (hNonzero : tangent ≠ 0) :
    0 < fisherMetric carrier.model tangent tangent := by
  classical
  rw [carrier.metric_on_tangent tangent hTangent]
  have hExists : ∃ coordinate, tangent coordinate ≠ 0 := by
    by_contra hNoCoordinate
    push Not at hNoCoordinate
    apply hNonzero
    funext coordinate
    exact hNoCoordinate coordinate
  obtain ⟨coordinate, hCoordinate⟩ := hExists
  exact Finset.sum_pos'
    (fun index _ ↦
      div_nonneg (sq_nonneg (tangent index)) (carrier.law.nonneg index))
    ⟨coordinate, Finset.mem_univ coordinate,
      div_pos (sq_pos_of_ne_zero hCoordinate) (carrier.law_pos coordinate)⟩

/-! ### A genuine two-outcome categorical carrier -/

/-- Uniform interior law on the two-outcome categorical simplex. -/
noncomputable def twoCategoricalLaw : FiniteLaw (Fin 2) where
  mass _ := 1 / 2
  nonneg _ := by norm_num
  sum_one := by norm_num [Fin.sum_univ_two]

/-- Centered two-coordinate categorical score: `+1` on the matching outcome
and `-1` on the other outcome. -/
def twoCategoricalScore (outcome coordinate : Fin 2) : ℝ :=
  if outcome = coordinate then 1 else -1

/-- The two-outcome score model has two ambient coordinates and a
one-dimensional simplex tangent subspace. -/
noncomputable def twoCategoricalScoreModel : ScoreModel (Fin 2) 2 where
  law := twoCategoricalLaw
  score := twoCategoricalScore
  centered coordinate := by
    fin_cases coordinate <;>
      norm_num [twoCategoricalLaw, twoCategoricalScore, Fin.sum_univ_two]

/-- Exact Fisher quadratic representation for the two-outcome model on the
simplex tangent subspace. -/
theorem twoCategorical_metric_on_tangent
    (tangent : Fin 2 → ℝ) (hTangent : IsSimplexTangent tangent) :
    fisherMetric twoCategoricalScoreModel tangent tangent =
      ∑ coordinate, tangent coordinate ^ 2 / twoCategoricalLaw coordinate := by
  have hSum : tangent 0 + tangent 1 = 0 := by
    simpa [IsSimplexTangent, Fin.sum_univ_two] using hTangent
  simp only [fisherMetric, scorePairing, Fin.sum_univ_two]
  norm_num [twoCategoricalScoreModel, twoCategoricalLaw,
    twoCategoricalScore]
  nlinarith

/-- Exact Fisher lowering representation for the same simplex tangent. -/
theorem twoCategorical_lower_on_tangent
    (tangent : Fin 2 → ℝ) (hTangent : IsSimplexTangent tangent) :
    lowerTangent twoCategoricalScoreModel tangent =
      fun coordinate ↦ tangent coordinate / twoCategoricalLaw coordinate := by
  have hSum : tangent 0 + tangent 1 = 0 := by
    simpa [IsSimplexTangent, Fin.sum_univ_two] using hTangent
  funext coordinate
  fin_cases coordinate <;>
    simp only [lowerTangent, fisherMatrix, Fin.sum_univ_two] <;>
    norm_num [twoCategoricalScoreModel, twoCategoricalLaw,
      twoCategoricalScore] <;>
    linarith

/-- Concrete dimension-two carrier for the categorical Fisher geometry. -/
noncomputable def twoCategoricalFisherCarrier : CategoricalFisherCarrier 2 where
  law := twoCategoricalLaw
  law_pos _ := by norm_num [twoCategoricalLaw]
  model := twoCategoricalScoreModel
  model_law := rfl
  metric_on_tangent := twoCategorical_metric_on_tangent
  lower_on_tangent := twoCategorical_lower_on_tangent

/-- Explicit nonzero tangent of the two-outcome simplex. -/
def twoCategoricalTangent : Fin 2 → ℝ :=
  fun coordinate ↦ if coordinate = 0 then 1 else -1

/-- The explicit tangent lies in the affine simplex tangent space. -/
theorem twoCategoricalTangent_isSimplexTangent :
    IsSimplexTangent twoCategoricalTangent := by
  norm_num [IsSimplexTangent, twoCategoricalTangent, Fin.sum_univ_two]

/-- The explicit simplex tangent is nonzero. -/
theorem twoCategoricalTangent_ne_zero : twoCategoricalTangent ≠ 0 := by
  intro hZero
  have hCoordinate := congrFun hZero (0 : Fin 2)
  norm_num [twoCategoricalTangent] at hCoordinate

/-- Every two-outcome simplex tangent is a scalar multiple of the explicit
`(1, -1)` direction, so the tangent carrier is genuinely one-dimensional. -/
theorem twoCategoricalTangent_spans
    (tangent : Fin 2 → ℝ) (hTangent : IsSimplexTangent tangent) :
    tangent = fun coordinate ↦ tangent 0 * twoCategoricalTangent coordinate := by
  have hSum : tangent 0 + tangent 1 = 0 := by
    simpa [IsSimplexTangent, Fin.sum_univ_two] using hTangent
  funext coordinate
  fin_cases coordinate
  · norm_num [twoCategoricalTangent]
  · norm_num [twoCategoricalTangent]
    linarith

/-- Positive definiteness on all nonzero simplex tangents is the full-rank
certificate for the one-dimensional tangent geometry. -/
theorem twoCategorical_simplexMetric_fullRank
    (tangent : Fin 2 → ℝ) (hTangent : IsSimplexTangent tangent)
    (hNonzero : tangent ≠ 0) :
    0 < fisherMetric twoCategoricalFisherCarrier.model tangent tangent :=
  categoricalFisher_pos twoCategoricalFisherCarrier tangent hTangent hNonzero

/-- The explicit nonzero tangent has Fisher energy exactly four. -/
theorem twoCategorical_nonzeroTangent_metric :
    IsSimplexTangent twoCategoricalTangent ∧
      twoCategoricalTangent ≠ 0 ∧
      fisherMetric twoCategoricalFisherCarrier.model
        twoCategoricalTangent twoCategoricalTangent = 4 := by
  refine ⟨twoCategoricalTangent_isSimplexTangent,
    twoCategoricalTangent_ne_zero, ?_⟩
  norm_num [twoCategoricalFisherCarrier, twoCategoricalScoreModel,
    twoCategoricalLaw, twoCategoricalScore, twoCategoricalTangent,
    fisherMetric, scorePairing, Fin.sum_univ_two]

/-- The inherited one-coordinate fair-Bernoulli Fisher model supplies an
explicit full-rank, positive-metric example. -/
theorem fairBernoulli_fullRank_example :
    0 < fisherMetric fairBernoulliScoreModel (fun _ ↦ 1) (fun _ ↦ 1) := by
  apply bernoulli_fisherMetric_pos (1 / 2 : ℝ) (by norm_num) (by norm_num)
  intro hZero
  have hCoordinate := congrFun hZero (0 : Fin 1)
  norm_num at hCoordinate

/-- The inherited duplicated-score model supplies an explicit nonzero null
direction, pinning the rank-deficient boundary. -/
theorem duplicatedScore_nullDirection_example :
    duplicatedScoreNullTangent ≠ 0 ∧
      fisherMetric duplicatedFairBernoulliScoreModel
        duplicatedScoreNullTangent duplicatedScoreNullTangent = 0 :=
  ⟨duplicatedScoreNullTangent_ne_zero,
    duplicatedScore_fisherMetric_eq_zero⟩

/-! ## Fisher pullback and natural-gradient chart transport -/

/-- Pullback through a composite chart agrees with successive pullback on the
existing score-model metric. -/
theorem fisherPullback_comp
    (model : ScoreModel Outcome d)
    (outer : Matrix (Fin d) (Fin k) ℝ)
    (inner : Matrix (Fin k) (Fin d) ℝ)
    (left right : Fin d → ℝ) :
    pullbackMetric model (outer * inner) left right =
      pullbackMetric model outer (inner.mulVec left) (inner.mulVec right) :=
  pullbackMetric_comp model outer inner left right

/-- Lowering in chart coordinates by the pulled-back Fisher matrix. -/
def chartPullbackLower (model : ScoreModel Outcome d)
    (jacobian : Matrix (Fin d) (Fin d) ℝ)
    (tangent : Fin d → ℝ) : Fin d → ℝ :=
  jacobian.transpose.mulVec
    (lowerTangent model (jacobian.mulVec tangent))

/-- Pull a covector back through a chart Jacobian. -/
def chartCovector (jacobian : Matrix (Fin d) (Fin d) ℝ)
    (covector : Fin d → ℝ) : Fin d → ℝ :=
  jacobian.transpose.mulVec covector

/-- Coordinate representation of a tangent under an invertible chart. -/
noncomputable def chartCoordinates
    (jacobian : Matrix (Fin d) (Fin d) ℝ) [Invertible jacobian]
    (tangent : Fin d → ℝ) : Fin d → ℝ :=
  jacobian⁻¹ *ᵥ tangent

/-- An invertible chart transports every Fisher-dual tangent to the pulled-back
covector. -/
theorem naturalGradient_chart_transport
    (model : ScoreModel Outcome d)
    (jacobian : Matrix (Fin d) (Fin d) ℝ) [Invertible jacobian]
    (covector tangent : Fin d → ℝ)
    (hNatural : IsNaturalGradient model covector tangent) :
    chartPullbackLower model jacobian
        (chartCoordinates jacobian tangent) =
      chartCovector jacobian covector := by
  change lowerTangent model tangent = covector at hNatural
  unfold chartPullbackLower chartCoordinates chartCovector
  rw [Matrix.mulVec_mulVec, Matrix.mul_inv_of_invertible,
    Matrix.one_mulVec, hNatural]

/-- Natural gradients are equivariant under an invertible chart when the
inherited Fisher metric is full rank. -/
theorem naturalGradient_equivariant
    (model : ScoreModel Outcome d) [Invertible (fisherMatrix model)]
    (jacobian : Matrix (Fin d) (Fin d) ℝ) [Invertible jacobian]
    (covector : Fin d → ℝ) :
    chartPullbackLower model jacobian
        (chartCoordinates jacobian (naturalGradient model covector)) =
      chartCovector jacobian covector :=
  naturalGradient_chart_transport model jacobian covector
    (naturalGradient model covector)
    (naturalGradient_isNaturalGradient model covector)

/-! ## A finite weighted Cauchy--Schwarz proof and Cramér--Rao -/

/-- Finite variance of a scalar estimation error. -/
def estimatorVariance (law : FiniteLaw Outcome)
    (estimator : Outcome → ℝ) (target : ℝ) : ℝ :=
  ∑ outcome, law outcome * (estimator outcome - target) ^ 2

/-- Scalar score covariance for a one-coordinate score model. -/
def scalarScoreCovariance (model : ScoreModel Outcome 1)
    (estimator : Outcome → ℝ) (target : ℝ) : ℝ :=
  ∑ outcome, model.law outcome *
    (estimator outcome - target) * model.score outcome 0

/-- Scalar Fisher information, computed on the inherited score field. -/
def scalarFisher (model : ScoreModel Outcome 1) : ℝ :=
  ∑ outcome, model.law outcome * model.score outcome 0 ^ 2

/-- The scalar definition is exactly the inherited Fisher self-metric on the
unit coordinate tangent. -/
theorem scalarFisher_eq_fisherMetric (model : ScoreModel Outcome 1) :
    scalarFisher model =
      fisherMetric model (fun _ ↦ 1) (fun _ ↦ 1) := by
  simp only [scalarFisher, fisherMetric, scorePairing, Fin.sum_univ_one,
    mul_one, pow_two]
  apply Finset.sum_congr rfl
  intro outcome _
  ring

/-- Finite weighted Cauchy--Schwarz with a strictly positive right quadratic
factor.  The proof expands a nonnegative weighted residual square. -/
theorem weightedCauchySchwarz_of_right_pos
    (law : FiniteLaw Outcome) (left right : Outcome → ℝ)
    (hRight : 0 < ∑ outcome, law outcome * right outcome ^ 2) :
    (∑ outcome, law outcome * left outcome * right outcome) ^ 2 ≤
      (∑ outcome, law outcome * left outcome ^ 2) *
        ∑ outcome, law outcome * right outcome ^ 2 := by
  let leftEnergy := ∑ outcome, law outcome * left outcome ^ 2
  let rightEnergy := ∑ outcome, law outcome * right outcome ^ 2
  let covariance := ∑ outcome, law outcome * left outcome * right outcome
  have hResidual :
      0 ≤ ∑ outcome, law outcome *
        (rightEnergy * left outcome - covariance * right outcome) ^ 2 :=
    Finset.sum_nonneg fun outcome _ ↦
      mul_nonneg (law.nonneg outcome) (sq_nonneg _)
  have hExpansion :
      (∑ outcome, law outcome *
        (rightEnergy * left outcome - covariance * right outcome) ^ 2) =
        rightEnergy * (leftEnergy * rightEnergy - covariance ^ 2) := by
    calc
      (∑ outcome, law outcome *
          (rightEnergy * left outcome - covariance * right outcome) ^ 2) =
          ∑ outcome, (
            (rightEnergy ^ 2) * (law outcome * left outcome ^ 2) -
              (2 * rightEnergy * covariance) *
                (law outcome * left outcome * right outcome) +
              (covariance ^ 2) * (law outcome * right outcome ^ 2)) := by
        apply Finset.sum_congr rfl
        intro outcome _
        ring
      _ = rightEnergy ^ 2 * leftEnergy -
            (2 * rightEnergy * covariance) * covariance +
            covariance ^ 2 * rightEnergy := by
        rw [Finset.sum_add_distrib, Finset.sum_sub_distrib]
        simp_rw [← Finset.mul_sum]
        rfl
      _ = rightEnergy * (leftEnergy * rightEnergy - covariance ^ 2) := by
        ring
  rw [hExpansion] at hResidual
  change 0 < rightEnergy at hRight
  change covariance ^ 2 ≤ leftEnergy * rightEnergy
  nlinarith

/-- Exact assumptions for the scalar Cramér--Rao proxy: ordinary
unbiasedness, the differentiated-unbiasedness/score-regularity identity, and
strictly positive Fisher information. -/
structure ScalarCramerRaoCertificate
    (model : ScoreModel Outcome 1) (estimator : Outcome → ℝ)
    (target : ℝ) : Prop where
  unbiased :
    ∑ outcome, model.law outcome * (estimator outcome - target) = 0
  scoreRegularity : scalarScoreCovariance model estimator target = 1
  fisher_pos : 0 < scalarFisher model

/-- Unbiased scalar Cramér--Rao inequality under finite score regularity and
positive Fisher information. -/
theorem scalarCramerRao
    (model : ScoreModel Outcome 1) (estimator : Outcome → ℝ)
    (target : ℝ)
    (certificate : ScalarCramerRaoCertificate model estimator target) :
    1 ≤ estimatorVariance model.law estimator target * scalarFisher model := by
  have hCauchy := weightedCauchySchwarz_of_right_pos model.law
    (fun outcome ↦ estimator outcome - target)
    (fun outcome ↦ model.score outcome 0) certificate.fisher_pos
  change (scalarScoreCovariance model estimator target) ^ 2 ≤
    estimatorVariance model.law estimator target * scalarFisher model at hCauchy
  rw [certificate.scoreRegularity] at hCauchy
  simpa [estimatorVariance, scalarFisher] using hCauchy

/-! ## Mirror descent and affine Bregman projection -/

/-- Finite coordinate pairing. -/
def coordinatePairing (left right : Fin d → ℝ) : ℝ :=
  ∑ coordinate, left coordinate * right coordinate

/-- Algebraic Bregman divergence associated with supplied potential values
and a supplied gradient field. -/
def bregmanDivergence (potential : (Fin d → ℝ) → ℝ)
    (gradient : (Fin d → ℝ) → Fin d → ℝ)
    (left right : Fin d → ℝ) : ℝ :=
  potential left - potential right -
    coordinatePairing (gradient right)
      (fun coordinate ↦ left coordinate - right coordinate)

/-- Exact mirror-descent three-point identity. -/
theorem mirrorDescent_threePoint_identity
    (potential : (Fin d → ℝ) → ℝ)
    (gradient : (Fin d → ℝ) → Fin d → ℝ)
    (left middle right : Fin d → ℝ) :
    bregmanDivergence potential gradient left right -
        bregmanDivergence potential gradient left middle -
        bregmanDivergence potential gradient middle right =
      coordinatePairing
        (fun coordinate ↦
          gradient middle coordinate - gradient right coordinate)
        (fun coordinate ↦ left coordinate - middle coordinate) := by
  have hSplit :
      coordinatePairing (gradient right)
          (fun coordinate ↦ left coordinate - right coordinate) =
        coordinatePairing (gradient right)
            (fun coordinate ↦ left coordinate - middle coordinate) +
          coordinatePairing (gradient right)
            (fun coordinate ↦ middle coordinate - right coordinate) := by
    unfold coordinatePairing
    rw [← Finset.sum_add_distrib]
    apply Finset.sum_congr rfl
    intro coordinate _
    ring
  have hDifference :
      coordinatePairing
          (fun coordinate ↦
            gradient middle coordinate - gradient right coordinate)
          (fun coordinate ↦ left coordinate - middle coordinate) =
        coordinatePairing (gradient middle)
            (fun coordinate ↦ left coordinate - middle coordinate) -
          coordinatePairing (gradient right)
            (fun coordinate ↦ left coordinate - middle coordinate) := by
    unfold coordinatePairing
    rw [← Finset.sum_sub_distrib]
    apply Finset.sum_congr rfl
    intro coordinate _
    ring
  rw [bregmanDivergence, bregmanDivergence, bregmanDivergence,
    hSplit, hDifference]
  ring

/-- Affine information-projection certificate.  Orthogonality is stated on
the complete maintained affine set rather than inferred from convexity. -/
structure AffineBregmanProjection
    (potential : (Fin d → ℝ) → ℝ)
    (gradient : (Fin d → ℝ) → Fin d → ℝ)
    (affineSet : Set (Fin d → ℝ))
    (base projection : Fin d → ℝ) : Prop where
  projection_mem : projection ∈ affineSet
  orthogonal : ∀ candidate ∈ affineSet,
    coordinatePairing
      (fun coordinate ↦
        gradient projection coordinate - gradient base coordinate)
      (fun coordinate ↦ candidate coordinate - projection coordinate) = 0

/-- Bregman Pythagorean equality for an affine information projection. -/
theorem affineProjection_bregmanPythagorean
    (potential : (Fin d → ℝ) → ℝ)
    (gradient : (Fin d → ℝ) → Fin d → ℝ)
    (affineSet : Set (Fin d → ℝ))
    (base projection candidate : Fin d → ℝ)
    (hProjection : AffineBregmanProjection potential gradient affineSet
      base projection)
    (hCandidate : candidate ∈ affineSet) :
    bregmanDivergence potential gradient candidate base =
      bregmanDivergence potential gradient candidate projection +
        bregmanDivergence potential gradient projection base := by
  have hThree := mirrorDescent_threePoint_identity potential gradient
    candidate projection base
  rw [hProjection.orthogonal candidate hCandidate] at hThree
  linarith

/-- If the residual Bregman term is nonnegative, the affine projection is an
actual minimizer of divergence to the base point over the affine set. -/
theorem affineProjection_minimizes
    (potential : (Fin d → ℝ) → ℝ)
    (gradient : (Fin d → ℝ) → Fin d → ℝ)
    (affineSet : Set (Fin d → ℝ))
    (base projection candidate : Fin d → ℝ)
    (hProjection : AffineBregmanProjection potential gradient affineSet
      base projection)
    (hCandidate : candidate ∈ affineSet)
    (hNonnegative :
      0 ≤ bregmanDivergence potential gradient candidate projection) :
    bregmanDivergence potential gradient projection base ≤
      bregmanDivergence potential gradient candidate base := by
  rw [affineProjection_bregmanPythagorean potential gradient affineSet base
    projection candidate hProjection hCandidate]
  linarith

/-! ## Replicator dynamics as categorical natural gradient -/

/-- Mean fitness under a finite categorical law. -/
def meanFitness (law : FiniteLaw (Fin d)) (fitness : Fin d → ℝ) : ℝ :=
  ∑ coordinate, law coordinate * fitness coordinate

/-- Replicator vector field in finite categorical coordinates. -/
def replicatorVector (law : FiniteLaw (Fin d))
    (fitness : Fin d → ℝ) : Fin d → ℝ :=
  fun coordinate ↦
    law coordinate * (fitness coordinate - meanFitness law fitness)

/-- The replicator vector conserves simplex mass. -/
theorem replicatorVector_isSimplexTangent
    (law : FiniteLaw (Fin d)) (fitness : Fin d → ℝ) :
    IsSimplexTangent (replicatorVector law fitness) := by
  simp only [IsSimplexTangent, replicatorVector, meanFitness, mul_sub]
  rw [Finset.sum_sub_distrib, ← Finset.sum_mul, law.sum_one, one_mul,
    sub_self]

/-- On a certified categorical Fisher carrier, the replicator vector is the
natural gradient of centered fitness. -/
theorem replicator_naturalGradient_equivalence
    (carrier : CategoricalFisherCarrier d) (fitness : Fin d → ℝ) :
    IsNaturalGradient carrier.model
      (fun coordinate ↦ fitness coordinate - meanFitness carrier.law fitness)
      (replicatorVector carrier.law fitness) := by
  change lowerTangent carrier.model (replicatorVector carrier.law fitness) = _
  rw [carrier.lower_on_tangent (replicatorVector carrier.law fitness)
    (replicatorVector_isSimplexTangent carrier.law fitness)]
  funext coordinate
  simp only [replicatorVector]
  field_simp [ne_of_gt (carrier.law_pos coordinate)]

/-! ### Concrete nonstationary categorical replicator witness -/

/-- Antisymmetric fitness on the two-outcome carrier. -/
def twoCategoricalFitness : Fin 2 → ℝ := twoCategoricalTangent

/-- The antisymmetric fitness has zero mean under the uniform categorical
law. -/
theorem twoCategorical_meanFitness_zero :
    meanFitness twoCategoricalLaw twoCategoricalFitness = 0 := by
  norm_num [meanFitness, twoCategoricalLaw, twoCategoricalFitness,
    twoCategoricalTangent, Fin.sum_univ_two]

/-- The resulting replicator field moves positive mass toward the fitter
outcome and away from the less-fit outcome. -/
theorem twoCategorical_replicator_values :
    replicatorVector twoCategoricalLaw twoCategoricalFitness 0 = 1 / 2 ∧
      replicatorVector twoCategoricalLaw twoCategoricalFitness 1 = -(1 / 2) := by
  simp only [replicatorVector]
  rw [twoCategorical_meanFitness_zero]
  norm_num [twoCategoricalLaw, twoCategoricalFitness,
    twoCategoricalTangent]

/-- The concrete replicator vector is nonzero. -/
theorem twoCategorical_replicator_ne_zero :
    replicatorVector twoCategoricalLaw twoCategoricalFitness ≠ 0 := by
  intro hZero
  have hCoordinate := congrFun hZero (0 : Fin 2)
  rw [twoCategorical_replicator_values.1] at hCoordinate
  norm_num at hCoordinate

/-- A closed, nonstationary natural-gradient witness on the genuine
two-outcome categorical carrier. -/
theorem twoCategorical_replicator_nonzero_witness :
    twoCategoricalFitness 0 ≠ twoCategoricalFitness 1 ∧
      replicatorVector twoCategoricalLaw twoCategoricalFitness ≠ 0 ∧
      IsNaturalGradient twoCategoricalFisherCarrier.model
        (fun coordinate ↦
          twoCategoricalFitness coordinate -
            meanFitness twoCategoricalLaw twoCategoricalFitness)
        (replicatorVector twoCategoricalLaw twoCategoricalFitness) := by
  exact
    ⟨by norm_num [twoCategoricalFitness, twoCategoricalTangent],
      twoCategorical_replicator_ne_zero,
      replicator_naturalGradient_equivalence
        twoCategoricalFisherCarrier twoCategoricalFitness⟩

end FEP.GeometricOptimization
