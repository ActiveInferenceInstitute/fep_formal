# Horizon 2 implementation handoff

Status: **H2.0--H2.3b, H2.4a/b, H2.5a/b/c/d, H2.5b-R0, H2.5d-R0,
H2.6a/b/c, H2.6a-R0, H2.7-R0, and H2.7 accepted; only read-only H3.G0
eligibility is open, with H3.0--H3.7 closed**.

Read [`README.md`](README.md),
[`slices/03a-posterior-martingale.md`](slices/03a-posterior-martingale.md),
[`slices/05a-scalar-ou.md`](slices/05a-scalar-ou.md),
[`readiness/matrix.yaml`](readiness/matrix.yaml), and the canonical
[`readiness/acceptance.json`](readiness/acceptance.json) receipt. The
[Horizon 2 design](../../docs/design/fep-research-program/horizon-2-smooth-stochastic.md)
owns mathematical intent; this spec owns execution state and reviewed
divergences.

## Current acceptance and next boundary

The [terminal receipt](readiness/terminal-acceptance.json) validates 328 mandatory
cases, the enabled Fin4 supplement, 180 source hashes, independent numerical
diagnostics, and three fresh reviews. Its retained evidence lives under
`readiness/evidence/20260904-wave2/`. Revalidate before downstream use; source
changes invalidate acceptance.

The [H3.G0 validator](../h3-reference-study/README.md) requires actual recorded
pre-outcome study metadata. No dataset, license, units, sampling, intervention
selection, or study approval was invented. Optional H2.2b stays closed.

The terminal audit retains explicit non-transfers: no singular covariance,
arbitrary recognition family, global statistical geometry or natural-gradient
ODE, nonparametric rates, unbounded-observable convergence, continuous-path
density, entropy production, physical dissipation, causal blanket, empirical
adequacy, or universal FEP result. Recognition variance is fixed to posterior
variance; descent is at time zero. Native posterior agreement is only
evidence-almost-everywhere, including when a closed version is evaluated at
datum zero. The Fin4 terminal is separate; its counterexample diagnostic uses
a separate fixed Fin2 model.

## H2.3a evidence

- `FEP.PosteriorConvergence` samples one Boolean Gaussian mean once and uses
  the matching prior-predictive joint law over its infinite i.i.d. real
  trajectory. Stage `n` observes exactly the `n + 1` coordinates in
  `Set.Iic n`.
- The finite-prefix process is defined from Mathlib's native posterior, not
  from conditional expectation. Posterior reconstruction and conditional-
  distribution uniqueness prove the mass of `{true}` equals the indicator's
  conditional expectation almost everywhere under the same joint law.
- Strong adaptation, integrability, bounds, and martingale status are derived.
  Lévy upward convergence reaches the conditional expectation under
  `⨆ n, observationFiltration n`; it does not identify that endpoint with the
  hidden mean or invoke the Kolmogorov tail sigma-field.
- At the H2.3a exit, direct compilation and all fourteen standard-axiom probes
  were clean. The slice passed 13 tests, the integrated H2/formal matrix passed
  129, and Lake built 8,754 jobs. Those figures are the H2.3a historical exit,
  not the current integrated barrier recorded below.
- Fresh independent review returned `APPROVE`. H1 posterior contraction stays
  a same-signature regression on its separate Boolean trajectory carrier.
  Only H2.3b opened at that boundary.

## H2.3b evidence

- The selected variance-one Gaussian observation laws are separated by their
  distinct means, and the fair Boolean prior assigns positive mass to both
  truth branches.
- Branchwise Gaussian strong laws construct an explicit statistic measurable
  under `\bigvee_n observationFiltration n`. It identifies the H2.3a limiting
  conditional expectation with the sampled Boolean parameter almost everywhere
  without naming or equating a Kolmogorov tail sigma-field.
- Posterior consistency is proved both under the selected joint law and under
  each fixed-truth trajectory law. The native parameter `ProbabilityMeasure`
  converges weakly to the sampled-parameter Dirac law; bounded continuous
  expectations and the genuine bounded zero-one Bayes risk transfer, while the
  same-law countermodel keeps the posterior equal to the prior only
  predictive-law almost everywhere.
- Exact direct compilation is warning-free. The focused suite passes 25 tests;
  all 26 public theorem reports are non-vacuously parsed and use only standard
  axioms. An exact 64-declaration environment census, typed consumers for all
  twelve H2.3b theorems, and mutation tests fail closed on hidden declarations,
  extra premises, or forbidden axioms.
- Fresh independent statistical review returned `APPROVE`. The result does not
  transfer entropy, log loss, rates, total variation, or another unbounded
  observable, and it does not generalize to arbitrary priors, continuous
  parameters, or latent-state filtering.

## H2.5b-R0 evidence

- `FEP.TransitionCovarianceR0` is a non-maintained generic finite-axis spike,
  not a new formal-resource owner. It stores only raw precision input and
  derives covariance as its inverse.
- Pinned spectral decomposition proves zero covariance at time zero, PSD at
  every nonnegative time, PD at positive time, and chronological covariance
  addition in the same later-on-left order as H2.4b/H2.5a.
- Direct compilation is warning-free; all four theorem axiom probes are
  parsed non-vacuously and standard only; the exact Fin4 consumer uses no
  numeric diagonalization; and the seven-test focused suite passes.
- The append-only repair receipt records `go` while preserving the historical
  H2.0 `blocking_no_go` row and receipt. Fresh independent linear-algebra
  review approved the result. At this gate, only H2.5b implementation was
  opened; its maintained exit is recorded below.

## H2.5b evidence

- `FEP.LinearGaussianSemigroup` stores only raw symmetric positive-definite
  precision and center. Covariance is the inverse; matrix-exponential
  evolution, dynamic covariance, zero/PSD/positive-time-PD boundaries, and
  chronological addition are derived.
- The state-plus-noise native kernel is measurable and Markov. It satisfies
  normalization, later-on-left Chapman--Kolmogorov, invariant Gaussian laws,
  exact means/covariances, full `NNReal` weak convergence, and
  bounded-continuous expectation convergence.
- The exact transported `Fin 1` kernel is H2.5a with diffusion variance rate
  two. Direct compile is warning-free and all 25 public theorem axiom blocks
  are nonempty and standard only.
- Symmetric precision is not promoted to a detailed-balance/native
  reversibility theorem. Fresh independent review returned `APPROVE`; at that
  predecessor exit, only H2.5c was opened.

## H2.5c evidence

- `FEP.Fin4GaussianSemigroup` instantiates H2.5b on the named
  external--sensory--active--internal axis. It stores the preregistered
  precision matrix; covariance remains its derived inverse.
- Exact entries and inverse identities, positive definiteness, four independent
  nonzero eigenmodes with eigenvalues `2`, `4`, `4`, and `6`, the native
  semigroup/invariant/weak-limit surface, and the exact normalized all-ones
  projection to H2.5a rate `2`/diffusion variance rate `2` all compile.
- The exact public surface is 18 definitions and 42 theorems. A syntax-agnostic
  Lean environment census closes declaration escapes, a typed terminal
  consumer pins the full export, and every theorem's axiom report is standard
  only.
- Source, manifest, workspace projection, aggregate, and formal declaration
  owner agree. Fresh independent algebra/science review returned `APPROVE`.
  H2.5c alone proves no conditioning theorem; the later accepted H2.5d-R0
  native repair is the separate evidence that now opens maintained H2.5d.

## H2.6a-R0 evidence

- The non-maintained spike reuses H2.1a's fixed-variance Gaussian family and
  H2.5a's exact OU prediction. It stores only raw dynamics, duration, and
  positive observation-noise input; gain, evidence, and posterior parameters
  are derived.
- Pointwise Gaussian completion of the square is lifted through exact
  `withDensity` joint laws. The actual evidence law is identified as a
  marginal before Mathlib's posterior uniqueness theorem yields the required
  evidence-almost-everywhere equality.
- Evidence density is strictly positive everywhere while every singleton has
  zero mass. Zero observation noise and totalized zero-denominator updates
  remain excluded.
- Direct compilation is warning-free; all fourteen public theorem axiom probes
  are standard only; the eight-test source-bound suite passes; and fresh
  independent probability review approved the result.
- The append-only repair receipt records `go` while preserving the historical
  H2.0 `blocking_no_go` row and receipt. At this gate, only H2.6a
  implementation was opened; its maintained exit is recorded below.

## H2.6a evidence

- `FEPComposed.GaussianFilter` consumes H2.5a's exact OU prediction and H2.1a's
  Gaussian observation family. The closed update is proved equal to Mathlib's
  native posterior only evidence almost everywhere under the same joint law.
- Prediction, innovation, gain, evidence, posterior mean/variance, and the
  closed posterior are derived from raw dynamics, duration, prior, and
  positive observation noise. Evidence density is positive, singleton mass is
  zero, and posterior rows normalize.
- The finite `List ℝ` recursion is chronological under one fixed-duration
  model. Direct compile is warning-free and all 16 public theorems use only
  standard axioms.
- Fresh independent probability review returned `APPROVE`. At that predecessor
  exit, only H2.6b was opened, under the separately reviewed one-step
  quadratic-risk contract.

## H2.6b evidence

- `FEPComposed.GaussianControl` derives one-step quadratic risk from the actual
  selected H2.5a transition composed with the H2.6a Gaussian belief. The
  Gaussian expected-square identity follows from integrability and moments;
  it is not a stored surrogate.
- Finite attainment reuses `finiteArgmin`. Risk and selector agreement with
  Mathlib's native posterior retain evidence-almost-everywhere scope.
- The strict Boolean witness selects the lower-risk transition and derives
  kernel inequality from strict risk separation. A separate equal-dynamics
  witness preserves the tie/nonuniqueness boundary.
- The exact public surface is one raw structure, 17 definitions, and 19
  theorems. Source, manifest, workspace projection, and aggregate agree;
  direct compilation is warning-free; all theorem axiom reports are standard
  only; and fresh independent control/science review returned `APPROVE`.
- No global Bayes-estimator, policy-tree, reward--EFE, multi-step, HJB, or
  infinite-horizon claim is licensed.

## H2.5d evidence

- `FEP.GaussianPrecisionConditioning` reuses the accepted H2.5c Fin4 carrier,
  precision, derived covariance, and stationary Gaussian for every center.
- It reconstructs the actual blanket/endpoints stationary joint as
  `blanketLaw center ⊗ₘ endpointConditionalKernel center`, identifies pair and
  scalar Mathlib conditional distributions blanket-marginal almost everywhere,
  and proves native external--internal `CondIndepFun` given sensory--active.
- The two conditional means retain the distinct external/internal center
  offsets and both variances are exactly `1 / 4`. Actual stationary endpoint
  covariance is `1 / 24`, so marginal correlation is not confused with failure
  of conditional independence.
- A separate fixed `Fin 2` diagnostic has precision `[[4, 1], [1, 4]]`, derived
  covariance `[[4 / 15, -1 / 15], [-1 / 15, 4 / 15]]`, actual cross-covariance
  `-1 / 15`, and native non-independence. It is not a perturbed Fin4 model or a
  generic converse.
- The exact public surface is 3 abbreviations, 15 definitions, 5 named
  instances, and 25 theorems. Direct and projected-module compilation are
  warning-free; every theorem reports standard axioms only; both independent
  reviews returned `APPROVE`; and the append-only lifecycle amendment records
  the sole non-scientific R0 test correction without changing the spike or
  historical readiness decision.

## Last accepted integrated formal baseline

- At the accepted H2.6c/H2.5d baseline, the canonical graph had 50 maintained
  modules: 32 foundations, 17
  compositions, and one declaration-free aggregate. It contains 1,437 total
  theorem declarations.
- Manifest and workspace projection drift were empty; coverage, atlas, and
  dashboard projections were current; and the default Lake build completed
  8,759 jobs.
- The all-H2 plus formal manifest/declaration matrix passed 201 tests. The
  formal coverage/atlas/dashboard projection matrix separately passed 65.
- These counts are historical baseline evidence and do not validate in-flight
  H2.7-R0/H2.7 bytes.

## H2.6c evidence

- `FEPComposed.GaussianGridPath` builds the native real-valued finite path law
  from H2.5a's exact scalar OU kernel and Mathlib `Kernel.partialTraj`.
- A public monotone `TimeGrid` rejects descending timestamps before `NNReal`
  subtraction can silently truncate them to zero. Equal timestamps remain
  explicit identity steps.
- The forward stationary-initialized law and its coordinate-reversed map are
  normalized. Reversal is measurable and involutive; bounded-continuous
  observables transfer exactly.
- Native KL is oriented forward-to-reverse-aligned. The real expected-log-ratio
  identity requires forward absolute continuity and integrability; either
  failure yields `∞`. The RN ratio is explicitly reverse-law almost everywhere.
- Direct compile and all eleven axiom probes are clean; eight focused tests and
  the 124-pass/19-skip all-H2/formal/thermodynamic matrix are green. The default
  Lean build completes 8,753 jobs. Projections are current at 44 modules, 28
  foundations, and 1,284 theorem declarations.
- Fresh unprimed scientific and code reviewers both approved. No reverse
  dynamics, reversibility, continuous path, Girsanov, or physical
  entropy-production claim ships.

## H2.5a evidence

- `FEP.ScalarGaussianSemigroup` owns a native scalar OU transition with raw
  parameters `rate`, `center`, and positive diffusion variance rate. The
  stationary variance and transition covariance are derived.
- Time zero is exactly Dirac/native identity. Positive time is exactly the
  accepted H2.1 fixed-variance Gaussian. The private affine-Gaussian bind proof
  yields chronological Chapman--Kolmogorov, which is packaged through H2.4's
  `NativeKernelSemigroup` rather than duplicated.
- The derived invariant Gaussian is preserved. Exact mean and variance hold,
  probability measures converge weakly over the full `NNReal` at-top filter,
  bounded-continuous expectations converge, and native KL to the invariant law
  is nonincreasing from an earlier time to an earlier-plus-increment time.
- Direct Lean compilation is warning-free; all fourteen public theorems use
  only standard axioms; the nine slice tests and 95-test integrated H2/formal
  matrix pass; the actual default `lake build` target completes all 8,752
  jobs. Formal workspace, coverage,
  atlas, and dashboard projections are current at 43 maintained modules, 28
  foundations, and 1,273 theorem declarations. The exact
  `ouTransition_comp_gaussian` endpoint lets H2.6a reuse the affine-Gaussian
  prediction result instead of repeating its private bind calculation.
- Fresh independent scientific review returned `APPROVE` with no critical,
  high, or medium finding. No SDE, Itô, Fokker--Planck, generator,
  reversibility, continuous-path, or unbounded-observable conclusion ships.

## H2.4b evidence

- `FEP.MarkovSemigroup` owns one native certificate over an already-Markov
  kernel family. Only zero and ordered addition are structure fields;
  stationarity, reversibility, KL contraction, and H1 embedding are derived.
- Native KL is monotone from `earlier` to `earlier + increment`, not merely
  bounded against time zero. The invariant-reference corollary consumes the
  same semigroup law and native invariant measure.
- The exact H1 lift preserves time, action, and the right-associated 16-state
  blanket carrier. False is native identity; true is the embedded positive
  refresh kernel; the two remain distinct.
- The directed H1 three-cycle remains a nonreversible generator/current
  regression only. It is not mislabeled as a certified semigroup.
- The H2.4 file passes 12 tests; focused integration passes 119 with 16
  expected opt-in skips; presentation passes 55; all 10 public theorems use
  standard axioms; and the complete Lean workspace builds 8,751 jobs.
- Formal workspace, coverage, atlas, and dashboard projections are current at
  42 maintained modules, 27 foundations, and 1,259 total theorems. Independent
  source review returned `APPROVE` after all scope and parity findings closed.

## H2.4a evidence

- The existing `FEP.NativeBlanket` owner now proves exactly two additive laws:
  finite identity embeds as native `Kernel.id`, and chronological
  `FiniteKernel.comp later earlier` embeds as `embeddedKernel later` composed
  after `embeddedKernel earlier`.
- The composition proof reuses the existing predictive-law embedding theorem;
  no second integration derivation, embedding definition, structure, manifest
  row, or semigroup field was added.
- The red owner/import and missing-theorem tracers are green. A noncommutative
  Boolean regression distinguishes the two composition orders. Both new
  theorems compile warning-free and use only standard axioms.
- Six slice tests, 52 embedding/readiness tests, 113 wider H1/H2 formal tests
  with 16 expected opt-in skips, and the complete 8,750-job Lake build pass.
  Formal workspace, coverage, atlas, and dashboard projections are current.

## H2.2a evidence

- Canonical owner: `smooth_information_geometry.lean`, module
  `FepSketches.smooth_information_geometry`, foundation namespace
  `FEP.SmoothInformationGeometry`.
- Exact imports: the accepted Gaussian owner plus Mathlib `Deriv.Mul` and
  `FDeriv.Pi`; no finite-geometry or manifold hierarchy is imported.
- Public result: coordinate-qualified natural/mean Fisher pairings, the
  two-Jacobian pullback, same-point flat duality product rule, constant metric
  coefficients, affine natural paths and their mean image, native KL/Bregman
  restatement, and a genuine Fréchet-derived duplicated-coordinate pullback
  with a nonzero null tangent.
- Native evidence: direct compile warning-free; all sixteen public theorems use
  only standard axioms; six slice tests and 95 integrated H2/formal/
  presentation tests pass; Lake builds all 8,750 jobs.
- Review: independent scientific preflight required and then verified the
  bundled Jacobian, mapped-point pullback, same-coordinate metric identity, and
  rank-deficiency boundary. No general connection, manifold, curvature,
  global dual-flatness, or physical-geometry claim was introduced.

## H2.1a evidence

- Canonical owner: `gaussian_information_geometry.lean`, module
  `FepSketches.gaussian_information_geometry`, foundation namespace
  `FEP.GaussianInformationGeometry`.
- Exact imports at H2.1a exit: native KL and scalar Gaussian Mathlib owners;
  H2.1b adds only `Mathlib.Analysis.Calculus.Deriv.Mul`.
- Public result: normalized full-support fixed-positive-variance scalar
  Gaussian laws, Radon--Nikodym density, mutual absolute continuity, and
  source-to-reference native KL equal to the embedded squared mean gap over
  twice the variance.
- Native evidence: direct compile warning-free; all eleven public theorems use
  only standard axioms; six slice tests, 39 focused integration tests, 62
  manifest-consumer tests, and 128 release/subpackage consumer tests pass.
- Projection evidence: formal workspace bytes, coverage, atlas, and dashboard
  are current; H2.0 readiness still validates.
- Independent scientific review: accepted with no blocker; singular,
  multivariate, coordinate, and process claims remain excluded.

## H2.1b evidence

- Same canonical owner and carrier; no second manifest row or project-local
  finite geometry import.
- Public result: inverse mean/natural coordinates, actual-density-ratio score
  derivatives, centered scores, `A'`, `A''`, coordinate-qualified Fisher,
  literal covariance, two-factor pullback, oriented KL/Bregman, and
  injectivity.
- Native evidence: direct compile warning-free; all twenty coordinate theorems
  use only standard axioms; five slice tests and eleven combined H2.1 tests
  pass; the module builds through 3,124 Lake jobs.
- Integration evidence: 23 central formal-owner tests, 62 formalism consumers,
  and 128 release/subpackage consumers pass; every deterministic formal
  projection is current.
- Independent review: GO, with the mean-coordinate covariance mislabel
  mechanically forbidden. No global Legendre/manifold claim was introduced.

## H2.0 evidence

- Exact pin at acceptance (historical): the Lean/Mathlib pair pinned at the
  time of the H2.0 run, Mathlib revision
  `0df444a360eaa60ab8c11dca51a86af692955474` (superseded by the v4.34.0
  program).
- Decision distribution: 25 `go`, 13 `optional_no_go`, three
  `blocking_no_go`, and one `upstream_required`.
- Canonical focused command: `uv run pytest -q
  tests/test_horizon2_readiness.py --no-cov --no-header --no-summary`.
- Static check: `uv run python
  specs/horizon-2-smooth-stochastic/readiness/validate.py --check`.
- The validator binds toolchain/probe/test/validator bytes and rejects row,
  receipt, probe, source, and premature-H2-resource tampering.
- H2.0 created no maintained formal resource, manifest row, projection,
  catalogue claim, or publication claim.

## Historical H2.0 blockers and current disposition

- `transition_covariance_psd` remains a historical H2.0 `blocking_no_go` row;
  the accepted H2.5b-R0 spike and maintained H2.5b owner now supply its
  replacement proof evidence.
- `native_filter_posterior` likewise remains historical in the frozen H2.0
  matrix; accepted H2.6a-R0 and maintained H2.6a now prove the selected native
  posterior equals the closed scalar Gaussian update evidence-almost-everywhere.
- `gaussian_conditioning_precision` remains historical `blocking_no_go` in the
  frozen H2.0 matrix. Accepted H2.5d-R0 now supplies the centered native joint
  reconstruction; maintained H2.5d supplies the accepted arbitrary-center
  blanket-a.e. conditional product, endpoint `CondIndepFun`, and bounded
  non-independence diagnostic. The historical row remains unchanged.
- `fin4_scalar_specialization` remains historical `upstream_required` in the
  frozen H2.0 matrix; accepted H2.5c now proves the exact maintained
  specialization and closes that current implementation seam.

The manifold/covariant/torsion, Bayes-estimator, Brownian finite-dimensional,
and six unsupported stochastic/path API rows are optional no-go decisions.
They do not block H2.1b.

## Frozen claim boundary

Preserve the H1 carrier and KL boundaries, the natural/mean Fisher-coordinate
distinction, the scalar/four-coordinate split, and H3.G0's read-only role. No
Itô, SDE, Fokker--Planck, Girsanov, continuous-path thermodynamics, physical
dissipation, empirical, or universal-FEP claim may enter through a name-only
interface. A row may change only through a new source-bound red-to-green proof
and a reviewed matrix/DAG update.
