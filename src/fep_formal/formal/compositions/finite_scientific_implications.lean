module
public import FepSketches.finite_probability
public import FepSketches.causal_dynamics
public import FepSketches.finite_markov_dynamics
public import FepSketches.active_inference
public import FepSketches.information_geometry

@[expose] public section

/-!
# Finite scientific implication boundaries

This composition leaf separates blanket, stationarity, recognition,
free-energy descent, Fisher alignment, and causal identification.  Its finite
countermodels reject implications between those predicates; the positive
result derives only a local directional derivative under every additional
posterior and Fisher-geometric premise.
-/

namespace FEPComposed.FiniteScientificImplications

open FEP FEP.ActiveInference FEP.CausalDynamics FEP.InformationGeometry Finset
open scoped BigOperators

/-! ## Cross-carrier predicates

Intrinsic stationarity, blanket factorization, local coupling, and intervention
equalities stay stated in the vocabulary of their foundation owners.  This
leaf names only posterior agreement and descent predicates that cross those
carriers.
-/

/-- The recognition law agrees with the exact posterior for each blanket. -/
def RecognitionMatchesPosterior
    {Blanket Policy State Outcome : Type*}
    [Fintype Blanket] [Fintype Policy] [Fintype State] [Fintype Outcome]
    (model : GenerativeModel Policy State Outcome)
    (policyOf : Blanket → Policy) (outcomeOf : Blanket → Outcome)
    (evidence : ∀ blanket,
      0 < predictedOutcome model (policyOf blanket) (outcomeOf blanket))
    (recognition : Blanket → FiniteLaw State) : Prop :=
  ∀ blanket,
    recognition blanket =
      posteriorState model (policyOf blanket) (outcomeOf blanket)
        (evidence blanket)

/-- Strict descent is only a derivative fact at one named point. -/
def LocalFreeEnergyDescent (objective : ℝ → ℝ) (point : ℝ) : Prop :=
  ∃ derivative, HasDerivAt objective derivative point ∧ derivative < 0

/-! ## Positive blanket-mixture and invariance boundary -/

/-- Componentwise invariance is a sufficient condition for a factorized
stationary product blanket under the paired transition.  The unit conditioner
is explicit, so this does not substitute rowwise transition factorization for
stationary-law conditional independence. -/
theorem factorizedProduct_invariant_under_pairedKernel
    {Internal External : Type*} [Fintype Internal] [Fintype External]
    (internalLaw : FiniteLaw Internal) (externalLaw : FiniteLaw External)
    (internalKernel : FiniteKernel Internal Internal)
    (externalKernel : FiniteKernel External External)
    (hInternal :
      FEP.FiniteMarkovDynamics.IsInvariant internalLaw internalKernel)
    (hExternal :
      FEP.FiniteMarkovDynamics.IsInvariant externalLaw externalKernel) :
    FEP.FiniteMarkovDynamics.IsInvariant
        (internalLaw.product externalLaw)
        (pairedKernel internalKernel externalKernel) ∧
      ∃ blanketModel : ConditionalBlanketModel Unit Internal External,
        blanketModel.conditional () = internalLaw.product externalLaw ∧
          FEP.CausalDynamics.Factorizes blanketModel ∧
          blanketModel.blanketLaw () = 1 := by
  constructor
  · unfold FEP.FiniteMarkovDynamics.IsInvariant at *
    rw [pairedKernel_predictive_product, hInternal, hExternal]
  · let blanketModel : ConditionalBlanketModel Unit Internal External :=
      { blanketLaw := FiniteLaw.pointMass ()
        conditional := fun _ => internalLaw.product externalLaw }
    refine ⟨blanketModel, rfl, ?_, ?_⟩
    · intro blanket
      change
        internalLaw.product externalLaw =
          (internalLaw.product externalLaw).fstMarginal.product
            (internalLaw.product externalLaw).sndMarginal
      rw [FiniteLaw.product_fstMarginal, FiniteLaw.product_sndMarginal]
    · simp [blanketModel, FiniteLaw.pointMass]

/-! ## Rational Boolean countermodels -/

/-- The two Boolean coordinates both persist, with no cross-coordinate
coupling. -/
def pairIdentityKernel :
    FiniteKernel (Bool × Bool) (Bool × Bool) :=
  pairedKernel
    (FiniteKernel.identity : FiniteKernel Bool Bool)
    (FiniteKernel.identity : FiniteKernel Bool Bool)

private theorem pairIdentity_rowwise :
    ∀ current,
      pairIdentityKernel.row current =
        (pairIdentityKernel.row current).fstMarginal.product
          (pairIdentityKernel.row current).sndMarginal := by
  intro current
  apply FiniteLaw.ext_mass
  funext next
  rcases current with ⟨currentInternal, currentExternal⟩
  rcases next with ⟨nextInternal, nextExternal⟩
  cases currentInternal <;> cases currentExternal <;>
    cases nextInternal <;> cases nextExternal <;>
      norm_num [pairIdentityKernel, pairedKernel, FiniteKernel.row,
        FiniteKernel.identity, FiniteKernel.deterministic,
        FiniteLaw.fstMarginal, FiniteLaw.sndMarginal, FiniteLaw.product,
        Fintype.sum_bool]

private theorem pairIdentity_invariant (law : FiniteLaw (Bool × Bool)) :
    FEP.FiniteMarkovDynamics.IsInvariant law pairIdentityKernel := by
  unfold FEP.FiniteMarkovDynamics.IsInvariant
  apply FiniteLaw.ext_mass
  funext next
  rcases next with ⟨nextInternal, nextExternal⟩
  cases nextInternal <;> cases nextExternal <;>
    simp [FiniteKernel.predictive_mass, pairIdentityKernel, pairedKernel,
      FiniteKernel.identity, FiniteKernel.deterministic,
      Fintype.sum_prod_type]

private theorem correlatedBoolBlanket_not_independent :
    correlatedBoolBlanket ≠
      correlatedBoolBlanket.fstMarginal.product
        correlatedBoolBlanket.sndMarginal :=
  correlatedBoolBlanket_not_factorized

/-- The diagonal joint is the conditional internal-external law at the sole
blanket value.  This makes the conditional meaning explicit without adding a
second blanket-factorization predicate. -/
noncomputable def correlatedStationaryBlanketModel :
    ConditionalBlanketModel Unit Bool Bool where
  blanketLaw := FiniteLaw.pointMass ()
  conditional _ := correlatedBoolBlanket

private theorem correlatedStationaryBlanket_not_factorizes :
    ¬FEP.CausalDynamics.Factorizes correlatedStationaryBlanketModel := by
  intro hFactorizes
  apply correlatedBoolBlanket_not_independent
  simpa [correlatedStationaryBlanketModel] using hFactorizes ()

private theorem correlatedStationaryBlanket_unit_mass :
    correlatedStationaryBlanketModel.blanketLaw () = 1 := by
  simp [correlatedStationaryBlanketModel, FiniteLaw.pointMass]

/-- Row factorization and stationarity do not force the stationary law itself
to factorize.  The diagonal law gives both rational nonzero atoms. -/
theorem rowwiseBlanket_doesNotImply_stationaryBlanket :
    ∃ kernel : FiniteKernel (Bool × Bool) (Bool × Bool),
      ∃ law : FiniteLaw (Bool × Bool),
        ∃ blanketModel : ConditionalBlanketModel Unit Bool Bool,
          (∀ current,
            kernel.row current =
              (kernel.row current).fstMarginal.product
                (kernel.row current).sndMarginal) ∧
            FEP.FiniteMarkovDynamics.IsInvariant law kernel ∧
            blanketModel.conditional () = law ∧
            ¬(FEP.FiniteMarkovDynamics.IsInvariant law kernel ∧
              FEP.CausalDynamics.Factorizes blanketModel) ∧
            blanketModel.blanketLaw () = 1 ∧
            law (false, false) = 1 / 2 ∧
            law (true, true) = 1 / 2 := by
  refine ⟨pairIdentityKernel, correlatedBoolBlanket,
    correlatedStationaryBlanketModel, pairIdentity_rowwise,
    pairIdentity_invariant correlatedBoolBlanket, rfl, ?_,
    correlatedStationaryBlanket_unit_mass,
    correlatedBoolBlanket_diagonal.1,
    correlatedBoolBlanket_diagonal.2⟩
  intro hStationaryBlanket
  exact correlatedStationaryBlanket_not_factorizes hStationaryBlanket.2

/-- A transition with no cross-coordinate coupling can preserve a correlated
stationary law, so sparse coupling is not stationary-law independence. -/
theorem sparseCoupling_doesNotImply_condIndep :
    ∃ internalKernel : FiniteKernel Bool Bool,
      ∃ externalKernel : FiniteKernel Bool Bool,
        ∃ kernel : FiniteKernel (Bool × Bool) (Bool × Bool),
          ∃ law : FiniteLaw (Bool × Bool),
            ∃ blanketModel : ConditionalBlanketModel Unit Bool Bool,
              kernel = pairedKernel internalKernel externalKernel ∧
                FEP.FiniteMarkovDynamics.IsInvariant law kernel ∧
                blanketModel.conditional () = law ∧
                ¬FEP.CausalDynamics.Factorizes blanketModel ∧
                blanketModel.blanketLaw () = 1 ∧
                law (false, false) = 1 / 2 ∧
                law (true, true) = 1 / 2 := by
  exact
    ⟨(FiniteKernel.identity : FiniteKernel Bool Bool),
      (FiniteKernel.identity : FiniteKernel Bool Bool), pairIdentityKernel,
      correlatedBoolBlanket, correlatedStationaryBlanketModel, rfl,
      pairIdentity_invariant correlatedBoolBlanket,
      rfl, correlatedStationaryBlanket_not_factorizes,
      correlatedStationaryBlanket_unit_mass,
      correlatedBoolBlanket_diagonal.1,
      correlatedBoolBlanket_diagonal.2⟩

/-- Independent fair Boolean coordinates, used only as a stationary blanket
law in the no-flow countermodel. -/
noncomputable def independentFairBlanket : FiniteLaw (Bool × Bool) :=
  fairBoolLaw.product fairBoolLaw

private theorem independentFairBlanket_independent :
    independentFairBlanket =
      independentFairBlanket.fstMarginal.product
        independentFairBlanket.sndMarginal := by
  unfold independentFairBlanket
  rw [FiniteLaw.product_fstMarginal, FiniteLaw.product_sndMarginal]

/-- The independent fair law as the conditional law at one explicit blanket
value. -/
noncomputable def independentStationaryBlanketModel :
    ConditionalBlanketModel Unit Bool Bool where
  blanketLaw := FiniteLaw.pointMass ()
  conditional _ := independentFairBlanket

private theorem independentStationaryBlanket_factorizes :
    FEP.CausalDynamics.Factorizes independentStationaryBlanketModel := by
  intro blanket
  simpa [independentStationaryBlanketModel] using
    independentFairBlanket_independent

private theorem independentStationaryBlanket_unit_mass :
    independentStationaryBlanketModel.blanketLaw () = 1 := by
  simp [independentStationaryBlanketModel, FiniteLaw.pointMass]

theorem symmetricFalseEvidence :
    0 < predictedOutcome (symmetricBoolModel fairBoolLaw) false false := by
  rw [symmetricBoolModel_predictedOutcome]
  norm_num [fairBoolLaw]

private theorem symmetricPosterior_false_eq_fair
    (hEvidence :
      0 < predictedOutcome (symmetricBoolModel fairBoolLaw) false false) :
    posteriorState (symmetricBoolModel fairBoolLaw) false false hEvidence =
      fairBoolLaw := by
  apply FiniteLaw.ext_mass
  funext state
  change
    predictedState (symmetricBoolModel fairBoolLaw) false state *
          (symmetricBoolModel fairBoolLaw).likelihood state false /
        predictedOutcome (symmetricBoolModel fairBoolLaw) false false =
      fairBoolLaw state
  rw [symmetricBoolModel_predictedState,
    symmetricBoolModel_predictedOutcome]
  norm_num [symmetricBoolModel, fairBoolKernel, fairBoolLaw]

private theorem independentBlanket_internal_eq_predictedState :
    independentFairBlanket.fstMarginal =
      predictedState (symmetricBoolModel fairBoolLaw) false := by
  rw [independentFairBlanket, FiniteLaw.product_fstMarginal,
    symmetricBoolModel_predictedState]

private theorem symmetricPosterior_eq_independentBlanket_internal :
    posteriorState (symmetricBoolModel fairBoolLaw) false false
        symmetricFalseEvidence = independentFairBlanket.fstMarginal := by
  rw [symmetricPosterior_false_eq_fair, independentFairBlanket,
    FiniteLaw.product_fstMarginal]

/-- Posterior-form VFE held fixed along a curve.  The stationary blanket gives
no rule selecting a nonconstant flow. -/
noncomputable def stationaryPosteriorFreeEnergy (_ : ℝ) : ℝ :=
  variationalFreeEnergy (symmetricBoolModel fairBoolLaw) false false
    symmetricFalseEvidence
    (posteriorState (symmetricBoolModel fairBoolLaw) false false
      symmetricFalseEvidence)

private theorem stationaryPosteriorFreeEnergy_not_descent :
    ¬LocalFreeEnergyDescent stationaryPosteriorFreeEnergy 0 := by
  intro hDescent
  rcases hDescent with ⟨derivative, hDerivative, hNegative⟩
  have hZero : HasDerivAt stationaryPosteriorFreeEnergy 0 0 := by
    change HasDerivAt
      (fun _ : ℝ =>
        variationalFreeEnergy (symmetricBoolModel fairBoolLaw) false false
          symmetricFalseEvidence
          (posteriorState (symmetricBoolModel fairBoolLaw) false false
            symmetricFalseEvidence)) 0 0
    exact hasDerivAt_const (0 : ℝ) _
  have hDerivativeZero : derivative = 0 := hDerivative.unique hZero
  linarith

/-- Even an independent stationary blanket supplies no flow law and therefore
does not imply descent of the exact-posterior variational free energy. -/
theorem stationaryBlanket_doesNotImply_freeEnergyDescent :
    FEP.FiniteMarkovDynamics.IsInvariant independentFairBlanket
        pairIdentityKernel ∧
      FEP.CausalDynamics.Factorizes independentStationaryBlanketModel ∧
      independentStationaryBlanketModel.conditional () =
        independentFairBlanket ∧
      independentStationaryBlanketModel.blanketLaw () = 1 ∧
      independentFairBlanket.fstMarginal =
        predictedState (symmetricBoolModel fairBoolLaw) false ∧
      posteriorState (symmetricBoolModel fairBoolLaw) false false
        symmetricFalseEvidence = independentFairBlanket.fstMarginal ∧
      ¬LocalFreeEnergyDescent stationaryPosteriorFreeEnergy 0 ∧
      independentFairBlanket (false, false) = 1 / 4 ∧
      independentFairBlanket (true, true) = 1 / 4 := by
  refine ⟨pairIdentity_invariant independentFairBlanket,
    independentStationaryBlanket_factorizes, rfl,
    independentStationaryBlanket_unit_mass,
    independentBlanket_internal_eq_predictedState,
    symmetricPosterior_eq_independentBlanket_internal,
    stationaryPosteriorFreeEnergy_not_descent, ?_, ?_⟩ <;>
    norm_num [independentFairBlanket, fairBoolLaw, FiniteLaw.product]

/-! ## Positive local recovery theorem -/

/-- Exact recognition, posterior support, score identifiability, a nonzero
tangent, Fisher-natural-gradient alignment, and a separately proved derivative
identity imply only strict local directional descent. -/
theorem blanketPosterior_and_flowAlignment_imply_localDescent
    {Blanket Policy State Outcome : Type*}
    [Fintype Blanket] [Fintype Policy] [Fintype State] [Fintype Outcome]
    {dimension : ℕ}
    (generativeModel : GenerativeModel Policy State Outcome)
    (recognition : Blanket → FiniteLaw State)
    (policyOf : Blanket → Policy) (outcomeOf : Blanket → Outcome)
    (evidence : ∀ blanket,
      0 < predictedOutcome generativeModel (policyOf blanket)
        (outcomeOf blanket))
    (blanket : Blanket)
    (scoreModel : ScoreModel State dimension)
    (covector tangent : Fin dimension → ℝ)
    (objective : ℝ → ℝ) (point derivative : ℝ)
    (hPosterior : RecognitionMatchesPosterior generativeModel policyOf
      outcomeOf evidence recognition)
    (hScoreLaw : scoreModel.law = recognition blanket)
    (hPosteriorSupport : ∀ state,
      0 < posteriorState generativeModel (policyOf blanket)
        (outcomeOf blanket) (evidence blanket) state)
    (hIdentifiable : Identifiable scoreModel)
    (hTangent : tangent ≠ 0)
    (hNatural : IsNaturalGradient scoreModel covector tangent)
    (hDerivative : HasDerivAt objective derivative point)
    (hDerivativeIdentity :
      derivative = -(∑ coordinate, tangent coordinate * covector coordinate)) :
    RecognitionMatchesPosterior generativeModel policyOf outcomeOf evidence
        recognition ∧
      LocalFreeEnergyDescent objective point := by
  have hScoreSupport : ∀ state, 0 < scoreModel.law state := by
    intro state
    rw [hScoreLaw, hPosterior blanket]
    exact hPosteriorSupport state
  have hMetricPositive : 0 < fisherMetric scoreModel tangent tangent :=
    fisherMetric_pos scoreModel hScoreSupport hIdentifiable hTangent
  have hMetricIdentity :
      fisherMetric scoreModel tangent tangent =
        ∑ coordinate, tangent coordinate * covector coordinate := by
    rw [fisherMetric_eq_dot_lowerTangent, hNatural]
  refine ⟨hPosterior, derivative, hDerivative, ?_⟩
  rw [hDerivativeIdentity, ← hMetricIdentity]
  linarith

private theorem fairBernoulliScoreModel_law_eq_fairBoolLaw :
    fairBernoulliScoreModel.law = fairBoolLaw := by
  apply FiniteLaw.ext_mass
  funext outcome
  cases outcome <;>
    norm_num [fairBernoulliScoreModel, bernoulliScoreModel,
      bernoulliLaw, fairBoolLaw]

/-! ### An actual interior-Bernoulli evidence/VFE direction -/

/-- A globally interior Bernoulli probability whose derivative at zero is one.
The scale factor four converts the logistic coordinate to the ordinary
Bernoulli probability coordinate at the fair point. -/
noncomputable def scaledLogisticProbability (parameter : ℝ) : ℝ :=
  Real.exp (4 * parameter) / (1 + Real.exp (4 * parameter))

theorem scaledLogisticProbability_pos (parameter : ℝ) :
    0 < scaledLogisticProbability parameter := by
  exact div_pos (Real.exp_pos _) (by positivity)

theorem scaledLogisticProbability_lt_one (parameter : ℝ) :
    scaledLogisticProbability parameter < 1 := by
  apply (div_lt_one (by positivity)).2
  linarith [Real.exp_pos (4 * parameter)]

/-- The parameterized state and evidence law remains a genuine interior
Bernoulli law for every real chart coordinate. -/
noncomputable def scaledLogisticLaw (parameter : ℝ) : FiniteLaw Bool :=
  bernoulliLaw (scaledLogisticProbability parameter)
    (scaledLogisticProbability_pos parameter)
    (scaledLogisticProbability_lt_one parameter)

private theorem scaledLogisticLaw_fullSupport (parameter : ℝ)
    (outcome : Bool) : 0 < scaledLogisticLaw parameter outcome := by
  cases outcome <;>
    simp [scaledLogisticLaw, bernoulliLaw,
      scaledLogisticProbability_pos,
      sub_pos.mpr (scaledLogisticProbability_lt_one parameter)]

private theorem scaledLogisticLaw_zero_eq_fair :
    scaledLogisticLaw 0 = fairBoolLaw := by
  apply FiniteLaw.ext_mass
  funext outcome
  cases outcome <;>
    norm_num [scaledLogisticLaw, scaledLogisticProbability,
      bernoulliLaw, fairBoolLaw]

/-- Every likelihood row is the same parameterized Bernoulli evidence law. -/
noncomputable def scaledLogisticKernel (parameter : ℝ) :
    FiniteKernel Bool Bool where
  mass _ outcome := scaledLogisticLaw parameter outcome
  nonneg _ outcome := (scaledLogisticLaw parameter).nonneg outcome
  sum_one _ := (scaledLogisticLaw parameter).sum_one

/-- A parameterized generative model whose state law, exact posterior, and
outcome evidence law are the same interior Bernoulli family.  The likelihood
is state-independent, so observing `true` does not distort the state posterior. -/
noncomputable def bernoulliEvidenceModel (parameter : ℝ) :
    GenerativeModel Unit Bool Bool where
  initialState := scaledLogisticLaw parameter
  transition _ := FiniteKernel.identity
  likelihood := scaledLogisticKernel parameter
  preferences := fairBoolLaw
  policyPrior := FiniteLaw.pointMass ()

private theorem bernoulliEvidenceModel_predictedState (parameter : ℝ) :
    predictedState (bernoulliEvidenceModel parameter) () =
      scaledLogisticLaw parameter := by
  simpa [predictedState, bernoulliEvidenceModel] using
    FiniteKernel.predictive_identity (scaledLogisticLaw parameter)

private theorem bernoulliEvidenceModel_predictedOutcome (parameter : ℝ) :
    predictedOutcome (bernoulliEvidenceModel parameter) () =
      scaledLogisticLaw parameter := by
  apply FiniteLaw.ext_mass
  funext outcome
  change
    (∑ state : Bool,
      predictedState (bernoulliEvidenceModel parameter) () state *
        scaledLogisticLaw parameter outcome) =
      scaledLogisticLaw parameter outcome
  rw [← Finset.sum_mul,
    (predictedState (bernoulliEvidenceModel parameter) ()).sum_one,
    one_mul]

private theorem bernoulliTrueEvidence (parameter : ℝ) :
    0 < predictedOutcome (bernoulliEvidenceModel parameter) () true := by
  rw [bernoulliEvidenceModel_predictedOutcome]
  exact scaledLogisticLaw_fullSupport parameter true

private theorem bernoulliEvidenceModel_posterior (parameter : ℝ)
    (hEvidence :
      0 < predictedOutcome (bernoulliEvidenceModel parameter) () true) :
    posteriorState (bernoulliEvidenceModel parameter) () true hEvidence =
      scaledLogisticLaw parameter := by
  apply FiniteLaw.ext_mass
  funext state
  change
    predictedState (bernoulliEvidenceModel parameter) () state *
          scaledLogisticLaw parameter true /
        predictedOutcome (bernoulliEvidenceModel parameter) () true =
      scaledLogisticLaw parameter state
  rw [bernoulliEvidenceModel_predictedState,
    bernoulliEvidenceModel_predictedOutcome]
  field_simp [ne_of_gt (scaledLogisticLaw_fullSupport parameter true)]

/-- Outcome surprisal along the named parameterized generative model. -/
noncomputable def bernoulliEvidenceFreeEnergy (parameter : ℝ) : ℝ :=
  outcomeSurprisal (bernoulliEvidenceModel parameter) () true

/-- At exact recognition the named objective is literally posterior-form VFE,
not an unrelated scalar surrogate. -/
private theorem bernoulliEvidenceFreeEnergy_eq_variationalFreeEnergy
    (parameter : ℝ) :
    bernoulliEvidenceFreeEnergy parameter =
      variationalFreeEnergy (bernoulliEvidenceModel parameter) () true
        (bernoulliTrueEvidence parameter)
        (posteriorState (bernoulliEvidenceModel parameter) () true
          (bernoulliTrueEvidence parameter)) := by
  exact (variationalFreeEnergy_posterior
    (bernoulliEvidenceModel parameter) () true
    (bernoulliTrueEvidence parameter)).symm

private theorem scaledLogisticProbability_hasDerivAt_zero :
    HasDerivAt scaledLogisticProbability 1 0 := by
  have hExp : HasDerivAt (fun parameter : ℝ => Real.exp (4 * parameter)) 4 0 := by
    simpa using ((hasDerivAt_id (0 : ℝ)).const_mul 4).exp
  have hDenominator :
      HasDerivAt (fun parameter : ℝ => 1 + Real.exp (4 * parameter)) 4 0 := by
    exact hExp.const_add 1
  have hQuotient := hExp.div hDenominator (by norm_num)
  norm_num only [Real.exp_zero] at hQuotient
  apply hQuotient.congr_of_eventuallyEq
  filter_upwards [] with parameter
  rfl

/-- The maintained fair-Bernoulli score is the log-law derivative of this same
parameterized generative family at its fair base point. -/
private theorem parameterizedBernoulli_score_eq_logDeriv (outcome : Bool) :
    HasDerivAt
      (fun parameter : ℝ => Real.log (scaledLogisticLaw parameter outcome))
      (fairBernoulliScoreModel.score outcome 0) 0 := by
  cases outcome
  · have hComplement :
        HasDerivAt (fun parameter : ℝ =>
          1 - scaledLogisticProbability parameter) (-1) 0 := by
      exact HasDerivAt.const_sub 1
        scaledLogisticProbability_hasDerivAt_zero
    have hLog := hComplement.log (by norm_num [scaledLogisticProbability])
    norm_num [scaledLogisticProbability] at hLog
    rw [fairBernoulliScoreModel_scores.1]
    apply hLog.congr_of_eventuallyEq
    filter_upwards [] with parameter
    simp [scaledLogisticLaw, bernoulliLaw, scaledLogisticProbability]
  ·
    have hLog := scaledLogisticProbability_hasDerivAt_zero.log
      (by norm_num [scaledLogisticProbability])
    norm_num [scaledLogisticProbability] at hLog
    rw [fairBernoulliScoreModel_scores.2]
    apply hLog.congr_of_eventuallyEq
    filter_upwards [] with parameter
    simp [scaledLogisticLaw, bernoulliLaw, scaledLogisticProbability]

private theorem bernoulliEvidenceFreeEnergy_hasDerivAt :
    HasDerivAt bernoulliEvidenceFreeEnergy (-2) 0 := by
  change HasDerivAt
    (fun parameter : ℝ =>
      -Real.log
        (predictedOutcome (bernoulliEvidenceModel parameter) () true))
    (-2) 0
  simp_rw [bernoulliEvidenceModel_predictedOutcome]
  have hNegative := (parameterizedBernoulli_score_eq_logDeriv true).neg
  rw [fairBernoulliScoreModel_scores.2] at hNegative
  apply hNegative.congr_of_eventuallyEq
  filter_upwards [] with parameter
  rfl

private def bernoulliEvidenceCovector : Fin 1 → ℝ := fun _ => -2

noncomputable def bernoulliNaturalTangent : Fin 1 → ℝ :=
  fun _ => -(1 / 2)

private theorem bernoulliNaturalTangent_ne_zero :
    bernoulliNaturalTangent ≠ 0 := by
  intro hZero
  have hCoordinate := congrFun hZero (0 : Fin 1)
  norm_num [bernoulliNaturalTangent] at hCoordinate

private theorem bernoulliNatural_alignment :
    IsNaturalGradient fairBernoulliScoreModel bernoulliEvidenceCovector
      bernoulliNaturalTangent := by
  change lowerTangent fairBernoulliScoreModel bernoulliNaturalTangent =
    bernoulliEvidenceCovector
  funext coordinate
  have hCoordinate : coordinate = 0 := Fin.eq_zero coordinate
  subst coordinate
  norm_num [lowerTangent, bernoulliEvidenceCovector,
    bernoulliNaturalTangent, fairBernoulli_fisherMatrix_entry]

/-- VFE along the negative natural-gradient direction in the evidence-model
parameter, based at the fair point. -/
noncomputable def bernoulliDirectionalVFE (step : ℝ) : ℝ :=
  bernoulliEvidenceFreeEnergy (-step * bernoulliNaturalTangent 0)

private theorem bernoulliDirectionalVFE_hasDerivAt :
    HasDerivAt bernoulliDirectionalVFE (-1) 0 := by
  have hDirection :
      HasDerivAt (fun step : ℝ => -step * bernoulliNaturalTangent 0)
        (1 / 2) 0 := by
    have hScaled := (hasDerivAt_id (0 : ℝ)).neg.mul_const (-(1 / 2))
    norm_num only [neg_mul, one_mul, neg_neg] at hScaled
    apply hScaled.congr_of_eventuallyEq
    filter_upwards [] with step
    norm_num [bernoulliNaturalTangent]
  have hOuter :
      HasDerivAt bernoulliEvidenceFreeEnergy (-2)
        (-0 * bernoulliNaturalTangent 0) := by
    simpa only [neg_zero, zero_mul] using
      bernoulliEvidenceFreeEnergy_hasDerivAt
  change HasDerivAt
    (bernoulliEvidenceFreeEnergy ∘
      fun step : ℝ => -step * bernoulliNaturalTangent 0) (-1) 0
  have hComposed := hOuter.comp 0 hDirection
  norm_num only [mul_div_cancel_left] at hComposed
  exact hComposed

/-- The recovery theorem is inhabited by the interior fair-Bernoulli score
model and exact-posterior recognition.  Strict descent is in the generative
evidence parameter, while the recognition-coordinate VFE remains at its
posterior optimum. -/
private theorem interiorBernoulli_localDescent_nonvacuous :
    RecognitionMatchesPosterior (bernoulliEvidenceModel 0)
        (fun _ : Unit => ()) (fun _ : Unit => true)
        (fun _ => bernoulliTrueEvidence 0) (fun _ => fairBoolLaw) ∧
      LocalFreeEnergyDescent bernoulliDirectionalVFE 0 := by
  have hPosterior :
      RecognitionMatchesPosterior (bernoulliEvidenceModel 0)
        (fun _ : Unit => ()) (fun _ : Unit => true)
        (fun _ => bernoulliTrueEvidence 0) (fun _ => fairBoolLaw) := by
    intro blanket
    rw [bernoulliEvidenceModel_posterior, scaledLogisticLaw_zero_eq_fair]
  have hPosteriorSupport : ∀ state : Bool,
      0 < posteriorState (bernoulliEvidenceModel 0) () true
        (bernoulliTrueEvidence 0) state := by
    intro state
    rw [bernoulliEvidenceModel_posterior,
      scaledLogisticLaw_zero_eq_fair]
    norm_num [fairBoolLaw]
  have hDerivativeIdentity :
      (-1 : ℝ) =
        -(∑ coordinate,
          bernoulliNaturalTangent coordinate *
            bernoulliEvidenceCovector coordinate) := by
    simp [bernoulliNaturalTangent, bernoulliEvidenceCovector]
  exact blanketPosterior_and_flowAlignment_imply_localDescent
    (bernoulliEvidenceModel 0) (fun _ : Unit => fairBoolLaw)
    (fun _ => ()) (fun _ => true) (fun _ => bernoulliTrueEvidence 0) ()
    fairBernoulliScoreModel bernoulliEvidenceCovector
    bernoulliNaturalTangent bernoulliDirectionalVFE 0 (-1)
    hPosterior fairBernoulliScoreModel_law_eq_fairBoolLaw
    hPosteriorSupport
    (bernoulliScoreModel_identifiable (1 / 2 : ℝ) (by norm_num)
      (by norm_num))
    bernoulliNaturalTangent_ne_zero bernoulliNatural_alignment
    bernoulliDirectionalVFE_hasDerivAt hDerivativeIdentity

/-! ## Observational equivalence without causal identification -/

/-- A hidden fair root is copied into the mediator blanket. -/
noncomputable def observationalCopyModel :
    OrderedFourNodeModel Bool Unit Bool Unit where
  rootLaw := fairBoolLaw
  nonDescendantLaw := FiniteLaw.pointMass ()
  mediatorGivenRoot := FiniteKernel.deterministic id
  outcomeGivenParents := FiniteKernel.deterministic (fun _ => ())

/-- The same observational mediator law can instead ignore the hidden root. -/
noncomputable def observationalIndependentModel :
    OrderedFourNodeModel Bool Unit Bool Unit where
  rootLaw := fairBoolLaw
  nonDescendantLaw := FiniteLaw.pointMass ()
  mediatorGivenRoot := fairBoolKernel
  outcomeGivenParents := FiniteKernel.deterministic (fun _ => ())

private theorem observationalBlankets_equivalent :
    mediatorMarginal (orderedJoint observationalCopyModel) =
      mediatorMarginal (orderedJoint observationalIndependentModel) := by
  apply FiniteLaw.ext_mass
  funext mediator
  cases mediator <;>
    norm_num [mediatorMarginal, orderedJoint, outcomeLift, mediatorLift,
      observationalCopyModel, observationalIndependentModel,
      FiniteKernel.joint, FiniteLaw.fstMarginal, FiniteLaw.sndMarginal,
      FiniteLaw.product, FiniteLaw.pointMass, fairBoolLaw, fairBoolKernel,
      FiniteKernel.deterministic, Fintype.sum_prod_type, Fintype.sum_bool]

private theorem observationalCopy_true_intervention :
    mediatorMarginal (interventionalJoint observationalCopyModel true) true = 1 := by
  norm_num [mediatorMarginal, interventionalJoint, outcomeLift, mediatorLift,
    observationalCopyModel, FiniteKernel.joint, FiniteLaw.fstMarginal,
    FiniteLaw.sndMarginal, FiniteLaw.product, FiniteLaw.pointMass, fairBoolLaw,
    FiniteKernel.deterministic, Fintype.sum_prod_type, Fintype.sum_bool]

private theorem observationalIndependent_true_intervention :
    mediatorMarginal
        (interventionalJoint observationalIndependentModel true) true = 1 / 2 := by
  norm_num [mediatorMarginal, interventionalJoint, outcomeLift, mediatorLift,
    observationalIndependentModel, FiniteKernel.joint,
    FiniteLaw.fstMarginal, FiniteLaw.sndMarginal, FiniteLaw.product,
    FiniteLaw.pointMass, fairBoolLaw, fairBoolKernel,
    FiniteKernel.deterministic, Fintype.sum_prod_type, Fintype.sum_bool]

private theorem observationalBlankets_not_causallyEquivalent :
    ¬(∀ root,
      mediatorMarginal (interventionalJoint observationalCopyModel root) =
        mediatorMarginal
          (interventionalJoint observationalIndependentModel root)) := by
  intro hCausal
  have hLaw := hCausal true
  have hAtom := congrArg (fun law : FiniteLaw Bool => law true) hLaw
  rw [observationalCopy_true_intervention,
    observationalIndependent_true_intervention] at hAtom
  norm_num at hAtom

/-- Marginalizing the hidden fair root gives the same rational observational
blanket law, while `do(root=true)` distinguishes copying from independence. -/
theorem observationalBlanket_doesNotIdentify_causalBlanket :
    mediatorMarginal (orderedJoint observationalCopyModel) =
        mediatorMarginal (orderedJoint observationalIndependentModel) ∧
      ¬(∀ root,
        mediatorMarginal (interventionalJoint observationalCopyModel root) =
          mediatorMarginal
            (interventionalJoint observationalIndependentModel root)) ∧
      mediatorMarginal (orderedJoint observationalCopyModel) true = 1 / 2 ∧
      mediatorMarginal
          (orderedJoint observationalIndependentModel) true = 1 / 2 ∧
      mediatorMarginal
          (interventionalJoint observationalCopyModel true) true = 1 ∧
      mediatorMarginal
          (interventionalJoint observationalIndependentModel true) true = 1 / 2 := by
  refine ⟨observationalBlankets_equivalent,
    observationalBlankets_not_causallyEquivalent, ?_, ?_,
    observationalCopy_true_intervention,
    observationalIndependent_true_intervention⟩
  · norm_num [mediatorMarginal, orderedJoint, outcomeLift, mediatorLift,
      observationalCopyModel, FiniteKernel.joint, FiniteLaw.fstMarginal,
      FiniteLaw.sndMarginal, FiniteLaw.product, FiniteLaw.pointMass,
      fairBoolLaw, FiniteKernel.deterministic, Fintype.sum_prod_type,
      Fintype.sum_bool]
  · norm_num [mediatorMarginal, orderedJoint, outcomeLift, mediatorLift,
      observationalIndependentModel, FiniteKernel.joint,
      FiniteLaw.fstMarginal, FiniteLaw.sndMarginal, FiniteLaw.product,
      FiniteLaw.pointMass, fairBoolLaw, fairBoolKernel,
      FiniteKernel.deterministic, Fintype.sum_prod_type, Fintype.sum_bool]

end FEPComposed.FiniteScientificImplications
