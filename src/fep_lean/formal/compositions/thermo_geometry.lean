module
public import FepSketches.families.core_active_inference
public import FepSketches.families.core_bayesian_mechanics
public import FepSketches.families.core_information_geometry
public import FepSketches.families.core_thermodynamics
public import FepSketches.families.geometric_optimization
public import FepSketches.families.path_thermodynamics
public import FepSketches.path_thermodynamics
public import FepSketches.geometric_optimization

@[expose] public section

/-!
# Path-thermodynamic and geometric topic compositions

The path-space theorems retain finite support and reversal assumptions instead
of identifying their entropy production with a continuous physical process.
The geometric theorems reuse the established score/Fisher layer and keep
finite-coordinate certificates distinct from measure-native KL objectives.
-/

namespace FEPComposed

open FEP FEP.FiniteInformation FEP.FiniteMarkovDynamics
open FEP.GeometricOptimization FEP.InformationGeometry FEP.PathThermodynamics
open MeasureTheory ProbabilityTheory Finset
open scoped BigOperators ENNReal Matrix MeasureTheory ProbabilityTheory

/-- The supported forward/reverse ratio reconstructs path mass, while the
identity kernel supplies the original catalogue's concrete reversibility
witness on an arbitrary measure carrier. -/
theorem fep093_path_ratio_extends_fep010_reversal
    {Path Native : Type*} [Fintype Path] [MeasurableSpace Native]
    (protocol : FinitePathProtocol Path)
    (hReverse : ∀ path, 0 < protocol.reverseAligned path) (path : Path)
    (nativeLaw : Measure Native) :
    pathRatio protocol path * protocol.reverseAligned path =
        protocol.forward path ∧
      Kernel.IsReversible (Kernel.id : Kernel Native Native) nativeLaw := by
  exact
    ⟨fep_fep093.FEP093.fep093_forward_reverse_pathLaw_ratio
        protocol hReverse path,
      fep_fep010.FEP010.fep010_identity_reversible nativeLaw⟩

/-- Path entropy production is exactly finite KL, alongside the original
nonnegative quadratic entropy-production certificate. -/
theorem fep094_path_kl_refines_fep049_entropy_production
    {Path Edge : Type*} [Fintype Path] [Fintype Edge]
    (protocol : FinitePathProtocol Path)
    (conductance force : Edge → ℝ)
    (hConductance : ∀ edge, 0 ≤ conductance edge) :
    entropyProduction protocol =
        finiteKL protocol.forward protocol.reverseAligned ∧
      0 ≤ fep_fep049.FEP049.fep049_entropyProduction conductance force := by
  exact
    ⟨fep_fep094.FEP094.fep094_entropyProduction_as_pathKL protocol,
      fep_fep049.FEP049.fep049_entropyProduction_nonneg
        conductance force hConductance⟩

/-- Detailed finite fluctuation symmetry and native kernel reversibility each
recover their corresponding forward or invariant law. -/
theorem fep095_fluctuation_symmetry_extends_fep010_reversibility
    {Path Native : Type*} [Fintype Path] [MeasurableSpace Native]
    (protocol : FinitePathProtocol Path)
    (hForward : ∀ path, 0 < protocol.forward path)
    (hReverse : ∀ path, 0 < protocol.reverseAligned path) (path : Path)
    (kernel : Kernel Native Native) (nativeLaw : Measure Native)
    [IsMarkovKernel kernel] (hReversible : Kernel.IsReversible kernel nativeLaw) :
    (protocol.reverseAligned path *
        Real.exp (pathwiseEntropyProduction protocol path) =
      protocol.forward path) ∧
      Kernel.Invariant kernel nativeLaw := by
  exact
    ⟨fep_fep095.FEP095.fep095_detailedFluctuation_symmetry
        protocol hForward hReverse path,
      fep_fep010.FEP010.fep010_reversible_invariant
        kernel nativeLaw hReversible⟩

/-- The integral fluctuation normalization is paired with the original exact
flux--force representation of nonnegative entropy production. -/
theorem fep096_integral_fluctuation_refines_fep049
    {Path Edge : Type*} [Fintype Path] [Fintype Edge]
    (protocol : FinitePathProtocol Path)
    (hForward : ∀ path, 0 < protocol.forward path)
    (hReverse : ∀ path, 0 < protocol.reverseAligned path)
    (conductance force : Edge → ℝ) :
    (∑ path, protocol.forward path *
        Real.exp (-pathwiseEntropyProduction protocol path) = 1) ∧
      ((∑ edge,
          force edge *
            fep_fep049.FEP049.fep049_linearFlux conductance force edge) =
        fep_fep049.FEP049.fep049_entropyProduction conductance force) := by
  exact
    ⟨fep_fep096.FEP096.fep096_integralFluctuation_theorem
        protocol hForward hReverse,
      fep_fep049.FEP049.fep049_flux_force_identity conductance force⟩

/-- The finite Jarzynski normalization and the original Helmholtz difference
identity are retained as separate assumptions, avoiding a microscopic-energy
identification that neither theorem proves. -/
theorem fep097_jarzynski_extends_fep013_helmholtz
    {Path : Type*} [Fintype Path]
    (law : FiniteLaw Path) (beta deltaFreeEnergy : ℝ) (work : Path → ℝ)
    (hNormalization :
      HasJarzynskiNormalization law beta deltaFreeEnergy work)
    (internalInitial internalFinal temperature entropyInitial entropyFinal : ℝ) :
    exponentialWorkAverage law beta work =
        Real.exp (-beta * deltaFreeEnergy) ∧
      (fep_fep013.FEP013.fep013_helmholtz
          internalFinal temperature entropyFinal -
        fep_fep013.FEP013.fep013_helmholtz
          internalInitial temperature entropyInitial =
        (internalFinal - internalInitial) -
          temperature * (entropyFinal - entropyInitial)) := by
  exact
    ⟨fep_fep097.FEP097.fep097_finiteJarzynski_equality
        law beta deltaFreeEnergy work hNormalization,
      fep_fep013.FEP013.fep013_delta_F
        internalInitial internalFinal temperature entropyInitial entropyFinal⟩

/-- Finite detailed balance cancels local current, while the original matrix
current remains antisymmetric on every oriented edge. -/
theorem fep098_local_current_refines_fep025
    {State : Type*} [Fintype State]
    (law : FiniteLaw State) (kernel : FiniteKernel State State)
    (hReversible : IsReversible law kernel) (source target : State)
    {size : ℕ} (flow : Matrix (Fin size) (Fin size) ℝ)
    (left right : Fin size) :
    probabilityCurrent law kernel source target = 0 ∧
      fep_fep025.FEP025.fep025_probabilityCurrent flow left right =
        -fep_fep025.FEP025.fep025_probabilityCurrent flow right left := by
  exact
    ⟨fep_fep098.FEP098.fep098_localDetailedBalance_currentCancellation
        law kernel hReversible source target,
      fep_fep025.FEP025.fep025_probabilityCurrent_antisymm
        flow left right⟩

/-- Reversible finite-channel KL dissipation is accompanied by both native KL
nonnegativity and the native reversible-kernel stationarity consequence. -/
theorem fep099_reversible_kl_dissipation_links_fep010_fep014
    {State Native : Type*} [Fintype State] [Nonempty State]
    [MeasurableSpace Native]
    (actual stationary : FiniteLaw State)
    (kernel : FiniteKernel State State)
    (hActual : ∀ state, 0 < actual state)
    (hStationary : ∀ state, 0 < stationary state)
    (hKernel : ∀ source target, 0 < kernel source target)
    (hReversible : IsReversible stationary kernel)
    (nativeActual nativeStationary : Measure Native)
    (nativeKernel : Kernel Native Native) [IsMarkovKernel nativeKernel]
    (hNativeReversible : Kernel.IsReversible nativeKernel nativeStationary) :
    finiteKL (kernel.predictive actual) stationary ≤
        finiteKL actual stationary ∧
      0 ≤ InformationTheory.klDiv nativeActual nativeStationary ∧
      Kernel.Invariant nativeKernel nativeStationary := by
  exact
    ⟨fep_fep099.FEP099.fep099_reversibleChain_oneStep_KL_dissipation
        actual stationary kernel hActual hStationary hKernel hReversible,
      fep_fep014.FEP014.fep014_kl_nonneg nativeActual nativeStationary,
      fep_fep010.FEP010.fep010_reversible_invariant
        nativeKernel nativeStationary hNativeReversible⟩

/-- The actual one-step reversible path production is the endpoint KL drop;
the existing fep-099 theorem supplies the qualified dissipation inequality. -/
theorem fep099_markov_path_KL_drop_reduction
    {State : Type*} [Fintype State] [DecidableEq State] [Nonempty State]
    (actual stationary : FiniteLaw State) (kernel : FiniteKernel State State)
    (hActual : ∀ state, 0 < actual state)
    (hStationary : ∀ state, 0 < stationary state)
    (hKernel : ∀ source target, 0 < kernel source target)
    (hReversible : IsReversible stationary kernel) :
    entropyProduction (markovPathProtocol kernel actual kernel
        (kernel.predictive actual) 1) =
        finiteKL actual stationary - finiteKL (kernel.predictive actual) stationary ∧
      finiteKL (kernel.predictive actual) stationary ≤ finiteKL actual stationary := by
  constructor
  · simpa [kernelPower, FiniteKernel.predictive_comp, FiniteKernel.predictive_identity] using
      entropyProduction_markov_reversible_KL_drop kernel actual stationary
        hActual hStationary hKernel hReversible 1
  · exact fep_fep099.FEP099.fep099_reversibleChain_oneStep_KL_dissipation
      actual stationary kernel hActual hStationary hKernel hReversible

/-- Full-support categorical Fisher positivity strengthens the original
diagonal Fisher metric's positive-semidefinite certificate. -/
theorem fep100_categorical_fisher_refines_fep004
    {dimension : ℕ} (carrier : CategoricalFisherCarrier dimension)
    (tangent : Fin dimension → ℝ) (hTangent : IsSimplexTangent tangent)
    (hNonzero : tangent ≠ 0)
    (information oldTangent : Fin dimension → ℝ)
    (hInformation : ∀ coordinate, 0 ≤ information coordinate) :
    0 < fisherMetric carrier.model tangent tangent ∧
      0 ≤ fep_fep004.FEP004.fep004_fisherMetric
        information oldTangent oldTangent := by
  exact
    ⟨fep_fep100.FEP100.fep100_categoricalFisher_simplexTangent_positivity
        carrier tangent hTangent hNonzero,
      fep_fep004.FEP004.fep004_fisherMetric_nonneg
        information oldTangent hInformation⟩

/-- Finite-matrix Fisher pullback composition extends the original scalar
Bernoulli pullback identity without asserting a global chart theorem. -/
theorem fep101_fisher_pullback_extends_fep038
    {Outcome : Type*} [Fintype Outcome] {dimension chartDimension : ℕ}
    (model : ScoreModel Outcome dimension)
    (outer : Matrix (Fin dimension) (Fin chartDimension) ℝ)
    (inner : Matrix (Fin chartDimension) (Fin dimension) ℝ)
    (left right : Fin dimension → ℝ)
    {parameter leftScalar rightScalar : ℝ}
    (hParameterPositive : 0 < parameter)
    (hParameterBelowOne : parameter < 1) :
    (pullbackMetric model (outer * inner) left right =
      pullbackMetric model outer (inner.mulVec left) (inner.mulVec right)) ∧
      (fep_fep038.FEP038.fep038_fisherMetric
          parameter leftScalar rightScalar =
        (fep_fep038.FEP038.fep038_coordinateJacobian parameter * leftScalar) *
          (fep_fep038.FEP038.fep038_coordinateJacobian parameter *
            rightScalar)) := by
  exact
    ⟨fep_fep101.FEP101.fep101_fisherPullback_reparameterization
        model outer inner left right,
      fep_fep038.FEP038.fep038_fisherMetric_pullback
        hParameterPositive hParameterBelowOne⟩

/-- The finite scalar Cramér--Rao certificate includes explicit score
regularity, while fep-038 supplies its concrete centered Bernoulli score case. -/
theorem fep102_cramer_rao_uses_fep038_score_geometry
    {Outcome : Type*} [Fintype Outcome]
    (model : ScoreModel Outcome 1) (estimator : Outcome → ℝ)
    (target : ℝ)
    (certificate : ScalarCramerRaoCertificate model estimator target)
    {parameter : ℝ} (hParameterPositive : 0 < parameter)
    (hParameterBelowOne : parameter < 1) :
    1 ≤ estimatorVariance model.law estimator target * scalarFisher model ∧
      (∑ outcome : Bool,
        fep_fep038.FEP038.fep038_bernoulliMass parameter outcome *
          fep_fep038.FEP038.fep038_score parameter outcome = 0) := by
  exact
    ⟨fep_fep102.FEP102.fep102_unbiasedScalar_cramerRao
        model estimator target certificate,
      fep_fep038.FEP038.fep038_expectedScore_zero
        hParameterPositive hParameterBelowOne⟩

/-- Natural-gradient equivariance under an invertible chart extends the
original one-dimensional Fisher/natural-gradient duality. -/
theorem fep103_natural_gradient_extends_fep038
    {Outcome : Type*} [Fintype Outcome] {dimension : ℕ}
    (model : ScoreModel Outcome dimension) [Invertible (fisherMatrix model)]
    (jacobian : Matrix (Fin dimension) (Fin dimension) ℝ)
    [Invertible jacobian] (covector : Fin dimension → ℝ)
    {parameter gradient : ℝ} (hParameterPositive : 0 < parameter)
    (hParameterBelowOne : parameter < 1) :
    (chartPullbackLower model jacobian
        (chartCoordinates jacobian (naturalGradient model covector)) =
      chartCovector jacobian covector) ∧
      (fep_fep038.FEP038.fep038_fisherInformation parameter *
        fep_fep038.FEP038.fep038_naturalGradient parameter gradient =
          gradient) := by
  exact
    ⟨fep_fep103.FEP103.fep103_naturalGradient_equivariance
        model jacobian covector,
      fep_fep038.FEP038.fep038_naturalGradient_duality
        hParameterPositive hParameterBelowOne⟩

/-- The mirror-descent three-point identity is paired with the original native
KL-regularized lower bound without identifying Bregman and KL divergences. -/
theorem fep104_mirror_descent_refines_fep024
    {dimension : ℕ}
    (potential : (Fin dimension → ℝ) → ℝ)
    (gradient : (Fin dimension → ℝ) → Fin dimension → ℝ)
    (left middle right : Fin dimension → ℝ)
    {Native : Type*} [MeasurableSpace Native]
    (base weight : ENNReal) (approximation prior : Measure Native) :
    (bregmanDivergence potential gradient left right -
        bregmanDivergence potential gradient left middle -
        bregmanDivergence potential gradient middle right =
      coordinatePairing
        (fun coordinate => gradient middle coordinate - gradient right coordinate)
        (fun coordinate => left coordinate - middle coordinate)) ∧
      base ≤ fep_fep024.FEP024.fep024_klRegularizedObjective
        base weight approximation prior := by
  exact
    ⟨fep_fep104.FEP104.fep104_mirrorDescent_threePoint_identity
        potential gradient left middle right,
      fep_fep024.FEP024.fep024_klRegularizedObjective_ge
        base weight approximation prior⟩

/-- The affine Bregman projection satisfies its exact Pythagorean identity,
while fep-044 records nonnegativity for the concrete Bernoulli Hellinger case. -/
theorem fep105_bregman_projection_extends_fep044
    {dimension : ℕ}
    (potential : (Fin dimension → ℝ) → ℝ)
    (gradient : (Fin dimension → ℝ) → Fin dimension → ℝ)
    (affineSet : Set (Fin dimension → ℝ))
    (base projection candidate : Fin dimension → ℝ)
    (hProjection : AffineBregmanProjection potential gradient affineSet
      base projection)
    (hCandidate : candidate ∈ affineSet) (left right : ℝ) :
    (bregmanDivergence potential gradient candidate base =
      bregmanDivergence potential gradient candidate projection +
        bregmanDivergence potential gradient projection base) ∧
      0 ≤ fep_fep044.FEP044.fep044_hellingerSq left right := by
  exact
    ⟨fep_fep105.FEP105.fep105_affineProjection_bregmanPythagorean
        potential gradient affineSet base projection candidate
        hProjection hCandidate,
      fep_fep044.FEP044.fep044_hellingerSq_nonneg left right⟩

/-- Replicator dynamics is a categorical natural gradient; the original
Bernoulli natural-gradient duality and finite softmax normalization remain
visible as its scalar and discrete-selection neighbors. -/
theorem fep106_replicator_links_fep028_fep038
    {dimension : ℕ} (carrier : CategoricalFisherCarrier dimension)
    (fitness : Fin dimension → ℝ)
    {parameter scalarGradient : ℝ}
    (hParameterPositive : 0 < parameter)
    (hParameterBelowOne : parameter < 1)
    (gamma : ℝ) (cost : Fin 10 → ℝ) (policies : Finset (Fin 10))
    (hPolicies : policies.Nonempty) :
    IsNaturalGradient carrier.model
          (fun coordinate => fitness coordinate - meanFitness carrier.law fitness)
          (replicatorVector carrier.law fitness) ∧
      (fep_fep038.FEP038.fep038_fisherInformation parameter *
        fep_fep038.FEP038.fep038_naturalGradient parameter scalarGradient =
          scalarGradient) ∧
      (∑ policy ∈ policies,
        fep_fep028.FEP028.fep028_softmax gamma cost policies policy = 1) := by
  exact
    ⟨fep_fep106.FEP106.fep106_replicator_naturalGradient_equivalence
        carrier fitness,
      fep_fep038.FEP038.fep038_naturalGradient_duality
        hParameterPositive hParameterBelowOne,
      fep_fep028.FEP028.fep028_softmax_probs_sum_one
        gamma cost policies hPolicies⟩

end FEPComposed
