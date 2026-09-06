# GNN Bridge: FepLean Continuous OU Linear-Gaussian Model
# GNN Version: 1.0
# Deterministic projection of the compiled Lean scalar-OU
#   instance (fep_lean,
#   lean/FepSketches/compositions/smooth_reference_kernel.lean:49-75).
# Contract v0.2 rounding: F and Q are non-terminating exact
#   Lean reals emitted as float64 (shortest round-trip repr);
#   their exact formulas are recorded in Signature. Terminating
#   values emit exactly.

## GNNSection
FepLeanContinuousOU continuous

## GNNVersionAndFlags
GNN v1

## ModelName
FepLean Continuous OU Linear-Gaussian Model

## ModelAnnotation
Bridge P4b slice: the fep_lean scalar OU filter instance
(rate=1, center=0, diffusionVarianceRate=2, stepDuration=1,
observation noise variance=1) projected deterministically to
GNN v1 continuous linear-Gaussian syntax under contract v0.2
rounding. Extraction record (file:line in the fep_lean
checkout at the commit recorded under Signature):
- F one-step decay = exp(-rate*t) = exp(-1)
  [scalar_gaussian_semigroup.lean:42-43]
- Q one-step transition covariance = rate^-1*(1 - exp(-2*rate*t))
  = 1 - exp(-2) [linear_gaussian_semigroup.lean:1217-1233]
- H identity readout [gaussian_filter.lean:46-49]
- R observation noise variance = 1
  [posterior_convergence.lean:38-40]
- prior_mean = 0, prior_cov = stationary variance = 1 (proved)
  [smooth_reference_kernel.lean:66-68, 96-101]

## StateSpaceBlock
# Linear-Gaussian state-space (continuous family)
x[1,1,type=float]      # latent scalar state
y[1,1,type=float]      # observation
F[1,1,type=float]      # one-step transition (drift decay)
Q[1,1,type=float]      # process noise covariance
H[1,1,type=float]      # observation matrix (identity readout)
R[1,1,type=float]      # observation noise covariance
prior_mean[1,1,type=float]   # x_1 mean
prior_cov[1,1,type=float]    # x_1 covariance
u[1,1,type=float]      # control input (passive: zero)
# Time
t[1,type=int]          # discrete step index

## Connections
F>x
Q>x
x-H
H>y
R>y
prior_mean>x
prior_cov>x

## InitialParameterization
# Contract v0.2 rounding: terminating decimals exact;
# non-terminating exact Lean reals as float64 shortest
# round-trip repr, exact formula in Signature.
# F: one-step decay, exact Lean value exp(-1) [Real.exp(-1),
#    scalar_gaussian_semigroup.lean:42-43]; float64 emission.
F={
  ((0.36787944117144233))
}

# Q: one-step transition covariance, exact Lean value
#    1 - exp(-2) [linear_gaussian_semigroup.lean:1217-1233];
#    float64 emission.
Q={
  ((0.8646647167633873))
}

# H: identity readout, exact.
H={
  ((1.0))
}

# R: observation noise variance, exact.
R={
  ((1.0))
}

# prior_mean: exact vector (n=1).
prior_mean={
  (0.0)
}

# prior_cov: proved stationary variance, exact matrix (n=1).
prior_cov={
  ((1.0))
}

## Equations
# Lean-defined one-step linear-Gaussian dynamics (file:line in
# lean/FepSketches/):
# decay(model, t) = Real.exp(-rate*t)
#   [scalar_gaussian_semigroup.lean:42-43]
# transitionVariance(t) = rate^-1 * (1 - Real.exp(-2*rate*t))
#   [linear_gaussian_semigroup.lean:1217-1233]
# x_t = F x_{t-1} + u_{t-1} + N(0, Q)
# y_t = H x_t + N(0, R)

## Time
Time=t
Dynamic
Continuous
ModelTimeHorizon=1

## ActInfOntologyAnnotation
F=StateTransitionMatrix
H=ObservationMatrix
Q=ProcessNoiseCovariance
R=ObservationNoiseCovariance
prior_mean=PriorMean
prior_cov=PriorCovariance
x=ContinuousHiddenState
y=ContinuousObservation
t=Time

## ModelParameters
ou_rate: 1             # selectedDynamics.rate
ou_center: 0           # selectedDynamics.center
diffusion_variance_rate: 2  # selectedDynamics.diffusionVarianceRate
step_duration: 1       # selectedFilter.stepDuration
observation_noise_variance: 1  # selectedGaussianFamily.variance
num_timesteps: 1

## Footer
FepLean bridge P4b slice: scalar OU linear-Gaussian model
projected from fep_lean smooth_reference_kernel.lean
selectedDynamics/selectedPrior/selectedFilter under contract
v0.2 rounding. One-step horizon, passive (no control input).

## Signature
source_repository: fep_lean
source_commit: 5f1bb25a5c5f66584addd109df7b7868b4c7cdb4
pipeline_repository: GeneralizedNotationNotation
pipeline_commit: d55c7323fdf2f25c9b60db3fe16472ce5f6ba05c
lean_module: lean/FepSketches/compositions/smooth_reference_kernel.lean
lean_structure: FEP.SmoothReferenceKernel composition instance
lean_instance: selectedDynamics/selectedPrior/selectedFilter
exact_formulas: F = exp(-1); Q = 1 - exp(-2)  # recorded verbatim per contract v0.2
projection_tool: specs/gnn-bridge-p4b-continuous-emission/projection_continuous.py (bridge P4b, contract v0.2)
target_syntax: GNN v1 (doc/gnn/gnn_syntax.md v1.1 surface)
rounding_policy: contract v0.2: terminating decimals emit exactly; non-terminating exact Lean reals emit as float64 (shortest round-trip repr) with the exact formula recorded verbatim in provenance; consumers treat the float as an approximation, never as the Lean value
source_owners_sha256: dc47b2deec8ea3a0958aa3ba20cab4d338af098275a514f74b9606c0a2e6ed9a
pipeline_owners_sha256: d0a13c1e1a783c59018108de0311203ef144d7dbad2dbafe9c62f01818caaa33
