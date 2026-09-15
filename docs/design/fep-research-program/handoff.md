# Research-program handoff

## Current barrier

Horizon 1 has exited. Its completed implementation and evidence record lives in
the [Horizon 1 handoff](../../../specs/done/horizon-1-finite-synthesis/HANDOFF.md),
and its audited design decisions—including the preserved first carrier
no-go—live in the [choices ledger](../../../specs/done/horizon-1-finite-synthesis/choices.md).
H2.0--H2.3b, H2.4a/b, H2.5a/b/c/d, H2.5b-R0, H2.5d-R0, H2.6a/b/c,
H2.6a-R0, and H2.7-R0 have exited with explicit boundaries. H2.7 is the sole
legal implementation slice; Horizon 3 remains closed.

The accepted H1 terminal result is deliberately narrow. Starting from the
selected Boolean sampling model, it reuses the exact two-observation posterior,
one further Bayes update, and an attained asymmetric one-step decision. The
emitted action is definitionally connected through `ActionInterface` to the
generative transition and the selected positive-time refresh-semigroup kernel.
On the same sixteen-state carrier, a full-support sensory--active blanket gives
genuine internal--external conditional factorization, the selected kernel
preserves the same stationary law, and finite/native KL strictly decrease for
the same lifted updated posterior.

The first H1.8 merge remains public and uninhabited: a non-Dirac posterior is not
a Boolean point-mass belief, and a two-state policy carrier is not equivalent to
the sixteen-state blanket carrier. The repaired theorem changes those carriers
and proves exact bridges; it does not contradict or erase the no-go.

## Fixed claim boundary

- The H1 decision is posterior-dependent and one-step. The policy-tree model
  has no transition field, so H1 does not prove transition-aware planning,
  EFE-optimal control, reward--EFE equivalence, or action selection for future
  kernel consequences.
- The stationary law proves finite
  `Internal ⟂ External | (Sensory, Active)` factorization. It does not prove
  blanket existence for arbitrary dynamics, rowwise blanket preservation,
  causal identification, or biological interpretation.
- Strict decrease is for repository-real finite KL and Mathlib-native KL to a
  full-support invariant law. It is not measured heat, physical entropy
  production, or universal free-energy dissipation.
- The model is finite and synthetic. It supplies no empirical calibration,
  biological mechanism, or universal Free Energy Principle.
- H1.5 is an accepted optional constrained-entropy certificate and is not a
  hidden dependency of the terminal theorem.

## Evidence at exit

- `lake build FepSketches.fep_all FepSketches.composed`: 8,745 jobs, success.
- H1/formal focused matrix: 117 passed, 16 opt-in skips.
- H1.8 independent Lean review: direct compile warning-free; all five public
  theorems use only `propext`, `Classical.choice`, and `Quot.sound`; projection
  bytes match canonical source.
- Independent domain review: approved the one-step posterior--decision--action,
  genuine sensory--active blanket, and KL orientation/support claims.
- Independent skeptical review found the original singleton-conditioner defect;
  the final theorem replaces it with a nontrivial full-support blanket and was
  re-reviewed.
- Formal module, coverage, atlas, and dashboard projections are current for the
  39-module, 24-foundation roster.
- GitNexus was unavailable for the nested checkout; source/`rg` fallback reduces
  graph-derived blast-radius confidence but not compiler or focused-test
  evidence.

The coordinated refresh that re-binds the broader native, Python, browser,
manuscript, and release-bundle receipts completed deterministically on
2026-09-12 (recorded in [CHANGELOG.md](../../../CHANGELOG.md)). H1 exit
evidence does not claim that the final
publication bundle is current after subsequent H2/H3 work.

## H2.0 exit

The source-bound readiness matrix records 25 `go`, 13 `optional_no_go`, three
`blocking_no_go`, and one `upstream_required` decision. Thirty-four focused tests
compile ten Lean probes warning-free, replay six bounded declaration searches,
and reject matrix, receipt, probe, and premature-resource tampering. The
validator also binds the exact Lean/Mathlib pin, probe bytes, test bytes, and
toolchain owners.

The accepted surface includes scalar Gaussian density/Radon--Nikodym laws,
moments, parameter-measurable Markov kernels, affine/convolution identities,
one nonzero-shift native-KL formula, local coordinate calculus, weak
convergence, posterior/martingale APIs, native kernel composition and KL DPI,
  exact H1 finite-kernel embedding, the fixed `Fin 4` precision/covariance
algebra, a genuine state-dependent multivariate Gaussian kernel, and
finite-grid trajectory laws.

The H2.0 decision rows remain immutable historical evidence; their current
downstream disposition is:

- `transition_covariance_psd` remains recorded as `blocking_no_go` in H2.0,
  while accepted H2.5b-R0 and maintained H2.5b now prove the selected dynamic
  covariance package;
- `native_filter_posterior` likewise remains historical in H2.0, while
  accepted H2.6a-R0 and maintained H2.6a prove the selected closed Gaussian
  posterior equality evidence-almost-everywhere;
- `gaussian_conditioning_precision` remains historical `blocking_no_go` in
  H2.0. Accepted H2.5d-R0 now proves the bounded centered-Fin4 native joint
  factorization, blanket-a.e. conditional product, and `CondIndepFun`; its
  append-only receipt opens maintained H2.5d only; and
- `fin4_scalar_specialization` remains historical `upstream_required` in H2.0,
  while accepted H2.5c now proves the exact H2.5a specialization.

The optional manifold, covariant, torsion, Bayes-estimator, Brownian, and
unsupported stochastic-calculus/path APIs do not block the row-green lanes.
No maintained H2 theorem resource existed when the H2.0 receipt was captured.
That absence is receipt-bound rather than a permanent validator rule, so the
accepted readiness evidence remains valid when H2.1a creates its first formal
resource.

## H2.1a exit

The first maintained H2 foundation is
`FEP.GaussianInformationGeometry.FixedVarianceGaussian`. It stores one
strictly positive variance and derives the scalar Gaussian law, native density,
normalization, full support, Radon--Nikodym equality, mutual absolute
continuity, and source-to-reference native KL. For arbitrary means at the same
variance, KL is the `ENNReal.ofReal` embedding of their squared displacement
divided by twice the variance. Equal means give zero, distinct means give
strict positivity, and the carrier excludes zero variance.

The direct source compile is warning-free. All eleven public theorems use only
`propext`, `Classical.choice`, and `Quot.sound`; six slice tests, 39 focused
integration tests, 62 manifest-consumer tests, and 128 release/subpackage
consumer tests pass. Formal workspace, coverage, atlas, and dashboard
projections are current. Independent scientific review accepted the theorem's
orientation, support boundary, native codomain, and exclusions. This exit does
not claim singular or multivariate Gaussian KL, coordinate geometry, an OU
process, or empirical evidence.

## H2.1b exit

The same owner now derives inverse mean/natural coordinate maps, its quadratic
natural log partition, and coordinate-labeled scores as derivatives of the
actual Gaussian log-density ratio. Both scores are centered. Natural Fisher is
the fixed variance and literal identity-statistic covariance; mean Fisher is
reciprocal variance and the proved two-Jacobian-factor pullback. The oriented
natural Bregman divergence is the same squared mean displacement as H2.1a's
native KL theorem. The natural-to-mean map and fixed-variance law are
injective.

The direct source compile is warning-free, all twenty new public theorems use
only standard axioms, five slice tests and eleven combined H2.1 tests pass, and
the module builds through 3,124 Lake jobs. Central owner, formalism-consumer,
release/import, and generated-projection checks are green. Independent review
returned GO after tightening covariance to the literal `cov[...]` surface and
allowlisting only its natural-coordinate theorem name. The implementation adds
no finite score carrier, multivariate result, global Legendre chart, manifold,
or process claim.

## H2.2a exit

The new `FEP.SmoothInformationGeometry` foundation derives natural- and
mean-coordinate Fisher pairings from H2.1, proves the two-factor coordinate
pullback and same-coordinate flat product rule, carries affine natural paths
into affine mean paths, and restates the accepted native KL/Bregman identity.
Its duplicated two-coordinate mean map has a proved continuous-linear Fréchet
derivative; the nonzero `(1, -1)` null tangent makes the mapped-point Fisher
pullback fail positive definiteness.

The direct compile is warning-free, all sixteen public theorems use only
standard axioms, six slice tests and 95 integrated formal/presentation tests
pass, and Lake builds all 8,750 jobs. Independent preflight required the
derivative and mapped-point repairs before accepting the scalar result. No
manifold, connection, Christoffel, curvature, global dual-flatness, or physical
geometry claim was introduced.

## H2.3a exit

The new `FEP.PosteriorConvergence` foundation fixes one static Boolean mean
parameter with variance-one Gaussian observations, embeds the accepted H1 fair
prior, and constructs the matching infinite-trajectory prior-predictive joint
law. Its finite-prefix process is defined from Mathlib's native posterior.
Posterior reconstruction and conditional-distribution uniqueness identify its
`{true}` mass with the hidden-parameter indicator's conditional expectation
almost everywhere under that same joint law.

Strong adaptation, integrability, pointwise probability bounds, and martingale
status are derived. Lévy upward convergence reaches the conditional
expectation under `⨆ n, observationFiltration n`; no theorem identifies that
endpoint with the hidden parameter or calls it the Kolmogorov tail sigma-field.
The H1 contraction theorem remains a same-signature regression on its separate
Boolean trajectory carrier.

At the H2.3a exit, direct compilation and all fourteen standard-axiom probes
were clean. The focused suite passed 13 tests, the integrated H2/formal matrix
passed 129, and Lake built 8,754 jobs. Fresh independent review returned
`APPROVE` after exact-statement mutation ratchets and terminology were
tightened. Only H2.3b opened at that boundary.

## H2.3b exit

The accepted extension separates the selected variance-one Gaussian laws by
their means and proves both fair-prior atoms positive. Branchwise Gaussian
strong laws construct an explicit statistic measurable under
`⨆ n, observationFiltration n`; almost-everywhere congruence then identifies
the H2.3a limiting conditional expectation with the sampled Boolean parameter.
No theorem calls that finite-observation supremum a Kolmogorov tail field.

Consistency is exported both under the selected joint law and under each
fixed-truth trajectory law. The native parameter `ProbabilityMeasure`
converges weakly to the sampled-parameter Dirac law; bounded continuous
expectations and the bounded Boolean zero-one Bayes risk converge. A native
same-law countermodel retains posterior-equals-prior only predictive-law almost
everywhere.

Direct compilation is warning-free, the focused suite passes 25 tests, and all
26 theorem axiom reports are non-vacuous and standard-only. A 64-declaration
Lean environment census, exact typed consumers for all twelve H2.3b theorems,
and adversarial mutations reject hidden declarations, extra premises, or
forbidden axioms. Fresh independent statistical review returned `APPROVE`.

## H2.4a exit

The existing `FEP.NativeBlanket` owner now proves that `embeddedKernel`
preserves the finite identity kernel and ordered finite-kernel composition.
The composition proof reuses the maintained predictive-embedding theorem;
it introduces no second integration lemma or native semigroup interface. A
noncommutative Boolean regression pins the composition order. The direct Lean
compile is warning-free, both new theorems use only standard axioms, the six
slice tests and 52-test embedding/readiness matrix pass, and the wider formal
integration sweep passes 113 tests with 16 expected opt-in skips.

## H2.4b exit

The new `FEP.MarkovSemigroup` foundation certifies zero and ordered addition
for an already-Markov native kernel family, then derives reversible-to-
invariant transfer and KL monotonicity from `earlier` to
`earlier + increment`. Its exact finite and action-indexed lifts preserve the
H1 time, action, right-associated 16-state blanket carrier, and
`embeddedKernel`; native hold is identity and native refresh is distinct.

All 10 public theorems use only standard axioms. The H2.4 suite passes 12
tests, focused integration passes 119 with 16 expected opt-in skips,
presentation passes 55, and Lake builds all 8,751 jobs. Formal workspace,
coverage, atlas, and dashboard projections are current at 42 maintained
modules, 27 foundations, and 1,259 total theorem declarations. Independent
review returned `APPROVE`. The directed H1 three-cycle remains only a
generator/current witness, not a falsely claimed semigroup instance.

## H2.5a exit

The new `FEP.ScalarGaussianSemigroup` foundation constructs the native scalar
OU transition directly from positive mean-reversion rate, center, and positive
diffusion variance rate. The stationary variance, transition mean, and
transition variance are derived. Time zero is exactly identity/Dirac, while
every positive-time slice is exactly the H2.1 fixed-variance Gaussian.

A private affine-Gaussian bind theorem proves chronological
Chapman--Kolmogorov and supplies the exact H2.4 native semigroup. The derived
stationary Gaussian is invariant; exact moments hold; probability measures
converge weakly over the full `NNReal` at-top filter; real
bounded-continuous expectations converge; and native KL to the invariant law
is nonincreasing between certified times.

The direct source compile is warning-free, all fourteen public theorems use
only standard axioms, and the nine slice tests plus 95-test integrated
H2/formal matrix pass. The actual default `lake build` target, whose library
glob includes standalone foundations, completes all 8,752 jobs. Formal workspace,
coverage, atlas, and dashboard projections are current at 43 maintained
modules, 28 foundations, and 1,273 theorem declarations. The public
`ouTransition_comp_gaussian` endpoint supplies the exact arbitrary-Gaussian
prediction seam needed by H2.6a without duplicating the affine bind proof.
Fresh independent
scientific review returned `APPROVE` with no critical, high, or medium
finding. The result is a transition-law semigroup, not an SDE solution,
Fokker--Planck theorem, generator theorem, continuous-path construction,
reversibility theorem, or unbounded-observable limit.

## H2.6c exit

`FEPComposed.GaussianGridPath` constructs the native real-valued finite path
law from the accepted scalar OU transition and Mathlib `Kernel.partialTraj`.
Its typed monotone `TimeGrid` excludes descending timestamps before truncated
`NNReal` subtraction could change a step into identity; repeated equal times
remain explicit identity transitions.

The maintained leaf proves chronological partial-trajectory composition,
normalization of the forward and coordinate-reversed laws, measurable
involutive reversal, bounded-continuous observable transfer, the RN ratio
reverse-law almost everywhere, and forward-oriented native KL/real
expected-log-ratio identities with explicit absolute-continuity and
integrability failure boundaries. It does not construct reverse dynamics or
infer reversibility from stationarity.

Direct compilation and all eleven standard-axiom probes are clean. Eight slice
tests and the 124-pass/19-skip all-H2/formal/thermodynamic matrix pass; the
default Lean build completes 8,753 jobs. Formal projections are current at 44
modules, 28 foundations, and 1,284 theorem declarations. Fresh unprimed
scientific and code reviews both returned `APPROVE`.

## H2.5b exit

`FEP.LinearGaussianSemigroup` stores only finite-axis symmetric
positive-definite precision and a center. Covariance is the inverse; dynamic
covariance zero/PSD/positive-time-PD boundaries, chronological addition, a
measurable native Markov kernel, Chapman--Kolmogorov, invariant Gaussian,
moments, full `NNReal` weak convergence, and bounded-continuous expectation
convergence are derived.

The transported `Fin 1` kernel equals H2.5a with diffusion variance rate two.
Direct compile is warning-free and all 25 public theorem axiom blocks are
nonempty and standard only. The source, manifest, projection, and declaration
roster have one owner. Invariance is proved; detailed balance and native
reversibility are not claimed. Fresh independent review returned `APPROVE` and
opened the now-accepted H2.5c slice.

## H2.5c exit

`FEP.Fin4GaussianSemigroup` instantiates H2.5b on the fixed named
external--sensory--active--internal axis. It stores the preregistered precision
matrix and derives covariance as its inverse. Exact entries/inverses,
positive definiteness, four independent nonzero eigenmodes with eigenvalues
two, four, four, and six, the native transition/semigroup/invariant/weak-limit
surface, and the exact normalized all-ones projection to H2.5a all compile.

The public surface is 18 definitions and 42 theorems. A Lean environment
census fails closed on extra declarations, a typed consumer pins the complete
export proposition, and every theorem's axiom report is standard only. Source,
manifest, projection, aggregate, and declaration ownership agree. Fresh
independent review returned `APPROVE`. This H2.5c exit itself proves no
Gaussian conditioning, precision-based conditional independence,
reversibility, SDE, or H3 claim; the later accepted H2.5d-R0 repair is the
separate evidence that now opens maintained H2.5d.

## H2.6a exit

`FEPComposed.GaussianFilter` reuses the exact H2.5a OU prediction and H2.1a
Gaussian observation family. Completion-square, joint-law, and evidence-
marginal identities prove the closed Gaussian update equals Mathlib's native
posterior evidence almost everywhere. Density is everywhere positive while
singleton mass is zero, and posterior rows normalize.

The finite `List ℝ` recursion applies the head observation before the tail
under one fixed-duration model. Direct compile is warning-free, all 16 public
theorems use only standard axioms, and fresh independent probability review
returned `APPROVE` and opened the now-accepted H2.6b slice only as a one-step
posterior-predictive quadratic decision result; no EFE, reward equivalence, or
policy recursion is licensed.

## H2.6b exit

`FEPComposed.GaussianControl` derives the actual one-step expected squared loss
under the selected H2.5a transition composed with the H2.6a belief, then adds a
separately typed nonnegative action penalty. Finite attainment uses the existing
`finiteArgmin`; risk and selector agreement with Mathlib's posterior remain
evidence almost everywhere. The strict Boolean witness derives transition
inequality from certified risk separation, and an equal-dynamics witness
retains the tie boundary.

The public surface is one raw structure, 17 definitions, and 19 theorems.
Source, manifest, projection, aggregate, and declaration ownership agree;
direct compile is warning-free; all named theorem axiom reports are standard
only; and fresh independent review returned `APPROVE`. This is not a global
Bayes-estimator theorem, policy-tree planning, reward--EFE equivalence,
multi-step control, or HJB/infinite-horizon result.

The last accepted H2.6c/H2.5d integration baseline has 50 modules, 32
foundations, 17 compositions, one declaration-free aggregate, and 1,437
theorem declarations. Manifest/projection drift was empty,
coverage/atlas/dashboard projections were current, the all-H2/formal matrix
passed 201 tests, and the default Lean build completed 8,759 jobs. The formal
presentation-projection matrix separately passed 65 tests. Those are baseline
receipts, not a fresh validation of in-flight H2.7 bytes.

## H2.5d exit

Maintained `FEP.GaussianPrecisionConditioning` reuses the exact accepted Fin4
stationary Gaussian at every center. It proves the blanket/endpoints `compProd`,
pair/scalar blanket-a.e. conditional distributions, and native endpoint
`CondIndepFun`, while retaining actual marginal covariance `1 / 24`. A separate
fixed bivariate precision diagnostic derives covariance `-1 / 15` and native
non-independence; it is neither a perturbed Fin4 law nor a generic converse.

The source and projection are byte-identical, its 25 theorems use standard
axioms only, the packaged-module consumer resolves private kernel instances,
and two independent reviews returned `APPROVE`. The append-only lifecycle
amendment records the sole pre-receipt R0 owner-absence correction. H2.5d opens
only H2.7 and makes no transition-conditioning, causal-blanket, reversibility,
H2.7-terminal, or H3 claim.

## H2.5b-R0 exit

The append-only transition-covariance repair proves the actual generic
finite-axis matrix theorem that the historical H2.0 diagonal surrogate did not
establish. For raw symmetric positive-definite precision, covariance is the
derived inverse and the matrix-exponential transition covariance is zero at
time zero, PSD for all nonnegative times, PD for positive time, and additive
in exact chronological Chapman--Kolmogorov order.

The spike compiles warning-free, its four public theorems use only standard
axioms, the exact Fin4 consumer does not use numeric eigenvalue diagnostics,
and all six source-bound readiness tests pass. Fresh independent
linear-algebra review approved it. The historical H2.0 row remains
`blocking_no_go`; the versioned repair receipt alone records `go` and opens
only H2.5b implementation at that gate. The maintained H2.5b exit is recorded
above.

## H2.6a-R0 exit

The append-only native-filter repair proves the selected nondegenerate scalar
Gaussian posterior route that the historical H2.0 identity-kernel probe did
not establish. It reuses the accepted H2.1a Gaussian family and H2.5a OU
prediction, derives the completion-of-square density identity, lifts both
joints through `withDensity`, identifies the actual evidence marginal, and
uses Mathlib posterior uniqueness to prove evidence-a.e. equality.

The spike compiles warning-free, all fourteen public theorems use only
standard axioms, the eight source-bound readiness tests pass, and fresh
independent probability review approved it. Density is positive everywhere
while singleton mass is zero. The historical H2.0 row remains
`blocking_no_go`; the versioned repair receipt alone records `go` and opens
only H2.6a implementation at that gate. The maintained H2.6a exit is recorded
above.

## Next pickup

Implement only
[H2.7 smooth reference-kernel terminal merge](../../../specs/horizon-2-smooth-stochastic/slices/07-terminal-certificate.md).
H2.2b remains optional and closed pending a proof-compression usefulness test.
Connect exact accepted scalar predecessors and separately name the accepted
Fin4/H2.5d export; do not widen it into global geometry, stochastic calculus,
transition conditioning, or a causal blanket. H3 remains closed until H2.7's
theorem and independent-review gates pass.
H3.G0 remains read-only and post-H2-terminal: it may select continuous only
after H2.7 succeeds, or finite only after an explicit reviewed H2 terminal
no-go.

The scheduling authority is the [dependency map](dependency-map.md); evidence
and review rules remain in the [research contract](research-contract.md).
