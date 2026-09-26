# Horizon 2: smooth and stochastic lifting

## Outcome

Horizon 2 lifts only the reusable parts of the H1 finite theorem chain to one
shared Gaussian location-family carrier, native probability measures, a native
action-indexed Markov-semigroup interface, and explicit
Ornstein--Uhlenbeck transition laws. The scalar law remains the shared carrier
for the H2 vertical theorem. A four-coordinate symmetric-precision Gaussian
extension is a required H2.5 export and H2.7 merge prerequisite so H3 never
develops that carrier after the fact. H2 ends with a single smooth/stochastic
terminal theorem and a precise list of results that did not transfer.

It does not attempt to build all of stochastic calculus or differential
geometry. The case-study shortlist inherited from H1 determines which general
lemmas are worth proving.

The mainline intentionally chooses a Gaussian location exponential family with
fixed positive variance/covariance. A general finite-outcome vector exponential
family remains optional. The multidimensional OU lift is not optional: H2.5
must construct it on the exact symmetric-precision `Fin 4` carrier and H2.7
must verify it as an accepted export alongside the scalar terminal theorem.
H3.G0 is therefore a post-H2, read-only acceptance and branch-selection gate.
It may accept the H2 evidence or select the finite H1 fallback; it may not
extend `fin4_gaussian_semigroup.lean` under an H3 work package.

## Implementation authority and refined owner map

The [active H2 spec](../../../specs/done/horizon-2-smooth-stochastic/README.md)
owns implementation state, refined slice dependencies, exact probe evidence,
provisional imports, and package-level stop/go decisions. This design owns the
mathematical targets and scientific firewalls. If the two disagree, dependent
implementation stops until both documents are reconciled.

H2.0 has frozen the pinned external API routes. Exact project direct imports
remain provisional until each maintained slice starts. The
[readiness matrix](../../../specs/done/horizon-2-smooth-stochastic/readiness/matrix.yaml)
and each active slice freeze the source-true import tuple before its maintained
resource opens.

| Slice | Canonical owner | Role and declaration namespace | Solid predecessors |
| --- | --- | --- | --- |
| H2.0 | accepted spec readiness probes; no maintained Lean resource | none | accepted H1 |
| H2.1a/b | `gaussian_information_geometry.lean` | foundation; `FEP.GaussianInformationGeometry` | H2.0; H2.1b additionally requires H2.1a |
| H2.2a/b | `smooth_information_geometry.lean` | foundation; `FEP.SmoothInformationGeometry` | H2.1b; H2.2b is optional after H2.2a |
| H2.3a/b | `posterior_convergence.lean` | foundation; `FEP.PosteriorConvergence` | H2.1a and H1.2/H1.3; H2.3b additionally requires H2.3a |
| H2.4a | existing `native_blanket.lean` embedding owner | existing foundation; no new manifest tuple | H2.0 and H1.2/H1.7 |
| H2.4b | `markov_semigroup.lean` | foundation; `FEP.MarkovSemigroup` | H2.4a |
| H2.5a | `scalar_gaussian_semigroup.lean` | foundation; `FEP.ScalarGaussianSemigroup` | H2.1a and H2.4b |
| H2.5b-R0 | source-bound dynamic-covariance spike/decision; no maintained Lean resource | none | H2.5a |
| H2.5b | `linear_gaussian_semigroup.lean` | foundation; `FEP.LinearGaussianSemigroup` | H2.5b-R0 |
| H2.5c | `fin4_gaussian_semigroup.lean` | foundation; `FEP.Fin4GaussianSemigroup` | H2.5b |
| H2.5d-R0 | source-bound fixed-Fin4 native-conditioning spike/decision | no maintained resource | H2.5c |
| H2.5d | `gaussian_precision_conditioning.lean` | foundation; `FEP.GaussianPrecisionConditioning` | H2.5d-R0 |
| H2.6a-R0 | source-bound native-posterior spike/decision; no maintained Lean resource | none | H2.1a and H2.5a |
| H2.6a | `compositions/gaussian_filter.lean` | composition; `FEPComposed.GaussianFilter` | H2.6a-R0 |
| H2.6b | `compositions/gaussian_control.lean` | composition; `FEPComposed.GaussianControl` | H2.4b, H2.6a, and accepted H1.4 |
| H2.6c | `compositions/gaussian_grid_path.lean` | composition; `FEPComposed.GaussianGridPath` | H2.4b and H2.5a |
| H2.7 | `compositions/smooth_reference_kernel.lean` | composition; `FEPComposed.SmoothReferenceKernel` | every solid predecessor named in the active H2 DAG |

H2.3 parameter learning and H2.6a latent-state filtering are distinct lanes.
Neither is a substitute for the other; they meet only at H2.7. The live
generated aggregate directly imports the three accepted H2 composition leaves.
The prospective H2 end state adds `smooth_reference_kernel.lean` as the fourth
only after H2.7 passes; explicit imports provide the foundation closure.

## H2.0 — pinned-library readiness matrix

**Depends on:** H1 exit.

**Single owner:** the active H2 spec owns exact probe files; stable pin claims
remain in [`docs/lean4.md`](../../lean4.md).

**Accepted result:** 25 `go`, 13 optional no-go, three historical blocking
no-go rows, and one historical upstream-required row. H2.5b-R0/H2.5b now
replace the dynamic `K_star` covariance blocker, and H2.6a-R0/H2.6a replace the
closed-form native-filter blocker on their selected carriers. H2.5d-R0 and
maintained H2.5d now replace the native Gaussian precision-conditioning
blocker. The scalar-to-Fin4 row remains a
historical `upstream_required` decision, while accepted H2.5c now proves its
exact maintained specialization. Only currently green incoming edges may open
a dependent slice.

### Positive probes required

At the exact supported pin, compile examples for:

- Fréchet derivatives of finite sums, `Real.exp`, `Real.log`, and matrix-valued
  maps;
- finite-dimensional inner-product and matrix invertibility APIs;
- Riemannian vector bundles, covariant derivatives, torsion, and metric
  compatibility;
- `ProbabilityMeasure` weak convergence and its bounded-continuous expectation
  characterization;
- posterior kernels, conditional expectation, martingale convergence, and
  Bayes estimators;
- multivariate Gaussian measures and Brownian finite-dimensional laws;
- Ionescu--Tulcea trajectory kernels; and
- symmetric and positive-definite matrix APIs, inversion, Gaussian
  conditioning, and matrix-exponential semigroup identities needed by the
  selected `Fin 4` carrier.

The pinned tree contains Riemannian and covariant-derivative modules, so H2 may
probe coordinate dual connections. Their presence does not imply that the
project's desired information-geometric construction is already available.

### Negative or blocking probes

Search and compile-check named interfaces for stochastic integration, Itô's
formula, SDE solution existence/uniqueness, Fokker--Planck PDE solutions,
Girsanov transformation, and general Markov semigroups. Any missing interface
becomes either:

1. a narrowly scoped upstream Mathlib contribution;
2. an explicit supplied interface with no existence claim; or
3. a no-go boundary that narrows H2.

No local homonym may be introduced merely to make a planned theorem typecheck.

### Exit gate

The readiness matrix names the declaration, import, compiled probe, intended
use, missing lemma, and no-go action for every H2 dependency. A package opens
only when its probe rows and every solid upstream DAG dependency are green.

## H2.1 — Gaussian location exponential family

**Depends on:** H2.0.

**Single owner:** new foundation `formal/gaussian_information_geometry.lean`.
The existing finite `exponential_family.lean` remains unchanged and supplies
algebraic orientation/regression examples; it is not the Gaussian measure
carrier.

**Implementation status:** H2.1 is accepted. The maintained owner derives the
fixed-positive-variance scalar law, density, normalization, full support,
Radon--Nikodym equality, mutual absolute continuity, and the oriented native-KL
formula for arbitrary source/reference means. It also derives inverse
natural/mean coordinates, density-ratio scores and centering, coordinate-
qualified Fisher/covariance and pullback identities, oriented Bregman equality,
and fixed-variance law injectivity. Singular, multivariate, global-manifold,
and process claims remain excluded; H2.2a has subsequently exited.

### Carrier

For the mainline use a scalar Gaussian location family with:

- a mean coordinate \(\mu\) in an explicit open Euclidean domain and a
  separately named natural coordinate \(\eta = \mu / \sigma^2\), with every
  derivative theorem stating which coordinate it uses;
- an explicit strictly positive variance \(\sigma^2\) held fixed when
  differentiating in either location coordinate;
- one canonical probability measure and, where needed, its density with
  respect to a named reference measure;
- the natural-coordinate log partition and sufficient statistic derived for
  that same measure, together with the explicit \(\mu \leftrightarrow \eta\)
  coordinate change; and
- support and absolute-continuity premises visible in KL statements.

### Target declarations

- normalization and nondegenerate support;
- Gaussian log-density-ratio affine identity;
- in natural coordinate \(\eta\), \(A'(\eta)=\mu\) and
  \(A''(\eta)=\sigma^2\);
- score centering in each explicitly named coordinate;
- natural-coordinate Fisher information
  \(I_\eta=\sigma^2=\operatorname{Cov}(X)\);
- mean-coordinate Fisher information \(I_\mu=1/\sigma^2\), derived either
  directly from the mean-coordinate score or by the proved coordinate
  pullback, never relabeled as covariance;
- positivity of both coordinate representations under \(\sigma^2>0\);
- KL equals the oriented log-partition Bregman divergence; and
- injectivity of the scalar mean map.

Global mean-coordinate bijection, essential smoothness, and boundary behavior
are separate stretch goals and must not be inferred from local invertibility.

### Stop/go spike

Prove the full one-dimensional fixed-variance Gaussian chain, including the
measure/density identity needed by native KL. The spike must prove the
coordinate map \(\eta=\mu/\sigma^2\), the natural-coordinate identities
\(A''(\eta)=I_\eta=\sigma^2\), and the pulled-back mean-coordinate identity
\(I_\mu=1/\sigma^2\) as distinct declarations. Go only if all
reference-measure, normalization, coordinate, and differentiability
obligations stay theorem-visible. If the pin lacks a clean multivariate density
route, keep the mainline scalar rather than assuming a finite-dimensional
generalization.

### Optional finite-vector capability

Separately, an active spec may extend `formal/exponential_family.lean` from its
scalar finite-outcome API to a vector statistic. Its two-parameter,
three-outcome gradient/Hessian spike and redundant-statistic boundary do not
gate H2.7 and are never substituted for the Gaussian carrier.

### Acceptance

- A nonzero location shift and the zero-shift KL boundary both compile.
- The exported constructor exposes its state type, reference measure, mean,
  variance, density, and native-KL bridge without a downstream import.
- Every derivative and Fisher theorem names \(\eta\) or \(\mu\), states its
  domain and differentiability premise, and has the exact value
  \(I_\eta=\sigma^2\) or \(I_\mu=1/\sigma^2\), respectively.
- A focused negative check rejects any unqualified
  "Fisher equals covariance" theorem on the mean-coordinate surface.

## H2.2 — dual information geometry

**Depends on:** H2.1 and the H2.0 coordinate-duality/Fréchet-derivative probes.

**Single owner:** one new foundation `formal/smooth_information_geometry.lean`
owns the smooth statistical-domain construction. H2.2a imports H2.1 and only
the Mathlib scalar/Fréchet calculus owners it uses. Existing
`information_geometry.lean` continues to own the distinct finite Bernoulli
score carrier; H2.2a neither imports nor re-encodes it.

**Implementation status:** H2.2a is accepted. H2.2b remains optional and
unopened.

### Mainline target

On H2.1's global scalar natural/mean coordinate bijection:

- make the selected coordinate representation explicit when bundling the
  Fisher metric: \(I_\eta=\sigma^2\) in the natural chart and its
  mean-coordinate pullback \(I_\mu=1/\sigma^2\);
- prove a same-coordinate flat product rule for natural/mean dual fields with
  both Fisher pairings explicit;
- prove constant metric coefficients and affine-path/zero-acceleration laws;
- identify KL/Bregman divergence as the local canonical dual-coordinate
  divergence;
- state geodesic results only for the explicit affine coordinate paths that are
  constructed.

H2.2a also proves a genuine rank boundary: the continuous-linear Fréchet
derivative of the duplicated map `(theta0, theta1) -> theta0 + theta1`
annihilates `(1, -1)`, so the Fisher pullback is not positive definite.

### Stop/go ladder

1. Prove all required identities as scalar coordinate equations. **Accepted.**
2. Bundle existing equations into Mathlib's manifold API only if a separate
   red-first usefulness test shows net proof compression. **Optional H2.2b.**
3. Generalize connection or curvature claims only behind their own scientific
   target and proof gates. **Not part of H2.2a or H2.7.**

H2.1 already proves the global scalar natural/mean coordinate inverse laws.
That one-dimensional bijection does not by itself justify a general manifold
connection, curvature classification, global canonical-divergence framework,
or arbitrary affine-geodesic claim; each remains separately gated.

If bundling requires a large independent theory of affine connections or
curvature, H2 exits with coordinate duality and records the upstream gap. It
must not ship a project-specific second manifold hierarchy.

### Acceptance

- The metric is derived from H2.1's law and score, not supplied as arbitrary
  weights.
- Duality, flatness, and rank assumptions are theorem-visible.
- A deliberately duplicated two-coordinate parameterization of one mean
  remains a local rank-deficiency witness.
- No global completeness or arbitrary statistical-manifold claim is made.

## H2.3 — selected Gaussian posterior and decision convergence

**Depends on:** H2.3a depends on H2.0, H2.1a, and accepted H1.3. H2.3b
additionally depends on H2.3a and the H2.0 bounded/weak convergence rows.

**Implementation status:** H2.3a and H2.3b are accepted. H2.3a samples one Boolean mean
parameter once, uses the variance-one H2.1 Gaussian family for conditionally
i.i.d. observations, and defines its finite-prefix probability from Mathlib's
native posterior. On the matching prior-predictive joint law, that probability
is almost everywhere the hidden-parameter indicator's conditional
expectation, forms a strongly adapted integrable martingale, and converges by
Lévy upward to the conditional expectation under the sigma-algebra generated
by all finite observations. H2.3b derives selected-model identification,
joint-law and fixed-truth consistency, weak convergence, bounded-continuous
transfer, bounded zero-one risk convergence, and the nonidentifiable boundary.

**Single owner:** `formal/posterior_convergence.lean` is the one foundation.
The shared owner directly imports the accepted Gaussian owner, H1 finite posterior
learning, the existing measure-Bayes posterior owner, and exact pinned Mathlib
conditional-expectation/product/posterior/martingale/strong-law APIs. It does not import
decision risk, statistical convergence, OU, filtering, path, or control
owners, and it does not redefine posterior kernels or weak convergence.

### Accepted H2.3a declarations

- one static two-mean Gaussian prior-predictive joint law and exact
  `Set.Iic n` finite-prefix laws;
- a native finite-prefix posterior-to-conditional-expectation equality almost
  everywhere under that same joint law;
- strong adaptation, integrability, probability bounds, and martingale status;
- Lévy-upward convergence to the limiting-observation conditional
  expectation, with no identification premise; and
- retention of the H1 finite separated-in-law result as a regression instance
  on its own Boolean trajectory carrier.

### Accepted H2.3b declarations

- identification of the limiting-observation endpoint with the hidden
  parameter for the selected distinct-mean Gaussian model through a statistic
  measurable under the supremum of the finite observation filtrations;
- posterior consistency under both the selected joint law and each positive-
  prior fixed-truth trajectory law;
- weak convergence of the native parameter `ProbabilityMeasure` to the
  sampled-parameter Dirac law and convergence of bounded continuous posterior
  expectations;
- convergence of the bounded Boolean zero-one Bayes risk; and
- a same-law nonidentifiable native model whose posterior remains the prior
  predictive-law almost everywhere.

The accepted H2.3b gate does not equate the finite-observation supremum with a
Kolmogorov tail sigma-field and is not a latent-state filtering result. It keeps
identification, consistency, weak convergence, and risk transfer as separately
named steps and transfers no entropy, logarithm, rate, total-variation, or
other unbounded-observable claim.

### Acceptance

- “Posterior converges” specifies topology and quantifiers.
- Identifiability is not inferred from a martingale limit.
- Almost-everywhere equality is not promoted to pointwise equality.
- A non-identifiable mixture is retained as a boundary theorem.

Generic posterior-contraction rates over nonparametric models remain outside
H2 unless supported by an independent active spec and upstream probability
infrastructure.

## H2.4 — Markov semigroup and native KL dissipation

**Depends on:** H1.2, H1.7, and H2.0.

**Implementation status:** H2.4a and H2.4b are accepted. The existing native
embedding owner proves exact preservation of identity and finite-kernel
composition, including a noncommutative order regression. The new native
semigroup owner consumes those laws, proves KL monotonicity between arbitrary
certified times, and lifts the exact H1 action/time/carrier. It adds no
generator-existence or physical-dissipation claim.

**Single owners:** H2.4a extends `FEP.NativeBlanket`, the existing owner of
`embeddedKernel`, with exact identity and composition-preservation theorems.
H2.4b introduces `formal/markov_semigroup.lean` and owns
`NativeKernelSemigroup` and `NativeActionIndexedKernelSemigroup`.
`continuous_time_markov.lean` retains the finite generator,
`FiniteMarkovSemigroup`, and
`FEP.ContinuousTimeMarkov.ActionIndexedSemigroup`.

### Target interface

A `NativeKernelSemigroup` supplies an `ℝ≥0`-indexed native kernel family,
identity at zero, and the additive composition law. A
`NativeActionIndexedKernelSemigroup` supplies an action-indexed family of
those semigroups, a nonnegative sample time, and its sampled native kernel.
These names describe narrow project interfaces; they do not impersonate a
missing upstream `MarkovSemigroup` API.

Invariant-law, reversibility, and generator relations remain separate
predicates or theorems. Generator results additionally require proved
time-measurability and continuity; an arbitrary indexed family has no
generator claim.

The H1 bridge is an equality, not a similarity convention. For every H1
`ActionIndexedSemigroup` and action, the lift must prove both

```text
lifted.kernel action time
  = FEP.NativeBlanket.embeddedKernel
      ((h1.semigroup action).kernel time hTime)

lifted.sampledKernel action
  = FEP.NativeBlanket.embeddedKernel (h1.sampledKernel action)
```

with the same action and H1 sample time on both sides. When the H1 carrier is
`FEP.MarkovBlanket.DynamicState Internal Sensory Active External`, the bridge
uses that exact right-associated type. It does not coerce, reassociate, or
replace it with a merely equinumerous carrier.

Prove:

- sampling at a positive interval gives a discrete Markov kernel;
- invariant laws remain invariant at every time;
- native KL to an invariant law is nonincreasing in time by kernel DPI;
- exact hold/refresh endpoint equality and kernel distinctness for the selected
  Boolean action model; H1's strict finite/native KL theorem remains in its H1
  owner;
- H1's certified finite-semigroup construction instantiates
  `NativeKernelSemigroup`;
- H1's action-indexed construction instantiates
  `NativeActionIndexedKernelSemigroup`; and
- its native sampled kernel is exactly the embedded H1 sampled kernel.

The semigroup laws may be interface fields; stochasticity and generator
construction may not be described as derived unless their constructor theorem
proves them.

### Stop/go spike

Wrap the existing certified finite semigroup and its action-indexed sampling in
the native interfaces, prove both embedding equalities above, and derive
invariance plus KL nonincrease by `klDiv_comp_right_le`. Go only if the sampling
and composition orientations are shared with H2.5. Otherwise retain the finite
interface and remove the measure-semigroup edge to H2.5--H2.7.

### Acceptance

- The H1 certified two-state semigroup and Boolean hold/refresh action model are
  instances. The nonreversible three-state object is only a generator/current
  witness, so its existing regression must stay green but it is not presented
  as a native-semigroup instance.
- The action-indexed native sampled kernel reduces by theorem to H1's
  `embeddedKernel`; no parallel action-transition field is accepted.
- KL dissipation is a theorem from native DPI and invariance.
- “Thermodynamic free energy” is not used for this relative entropy without a
  separate constitutive bridge.

## H2.5 — explicit Gaussian/Ornstein--Uhlenbeck transition laws

**Depends on:** H2.0, H2.1a, and H2.4b.

**Single owners:** H2.5a owns the scalar OU kernel in
`scalar_gaussian_semigroup.lean`; H2.5b owns reusable symmetric-precision
linear-Gaussian algebra in `linear_gaussian_semigroup.lean`; H2.5c owns the
exact `Fin 4` export in `fin4_gaussian_semigroup.lean`; H2.5d-R0 owns only the
source-bound native-conditioning decision; and H2.5d owns the maintained native
conditioning/precision theorem in
`gaussian_precision_conditioning.lean`. No owner supplies a general SDE
library.

### Scalar regression slice

Construct the scalar mean-reverting OU transition directly for
\(a>0\), diffusion variance rate \(q>0\), stationary mean \(m\), transition mean
\(m + e^{-at}(x-m)\), and transition variance
\(q(1-e^{-2at})/(2a)\). In the alternative diffusion-amplitude notation,
\(q=\sigma^2\); the formal owner stores only \(q\). Prove:

- measurability, normalization, and positive-variance boundaries;
- the Chapman--Kolmogorov/semigroup identity;
- the Gaussian invariant law;
- `ouTransition_eq_gaussianLocation` for every positive time, tying this
  constructor to H2.1 rather than merely sharing the word “Gaussian”;
- exact mean and covariance evolution;
- weak convergence toward stationarity.

A generator or weak-forward integral identity is optional. It opens only when
H2.0 identifies an explicit bounded smooth test-function class and proves the
required differentiation-under-integral interface. Its absence does not block
H2.5 or H2.7 and licenses no `FokkerPlanckSolution`, SDE, or Itô declaration.

The scalar slice is both a regression gate and the H2.7 vertical carrier. The
four-coordinate slice below is a separate required export; the two are related
by an exact scalar-specialization theorem, not conflated into one carrier.

**Implementation status:** H2.5a is accepted. Its native scalar OU family
proves the zero/positive-time split, chronological semigroup law, invariant
Gaussian, exact moments, full `NNReal`-time weak convergence,
bounded-continuous expectation convergence, and invariant-reference native-KL
monotonicity. H2.5b and H2.6a now have this source dependency; H2.6c is
accepted. H2.5b-R0 is also accepted:
its generic finite-axis spectral spike derives the actual transition-covariance
zero, PSD, positive-time PD, and chronological addition laws from raw
positive-definite precision. The accepted H2.5b maintained owner reuses that
route, constructs the native Markov semigroup, proves invariant moments and
full-time weak convergence, and specializes exactly to H2.5a on `Fin 1`.
Accepted H2.5c instantiates the preregistered named `Fin 4` carrier, proves the
exact inverse/eigensystem, inherits the native semigroup, invariant law, and
weak limit, and identifies its normalized all-ones projection exactly with
H2.5a at rate two and diffusion variance rate two. It does not prove Gaussian
conditioning, precision-based conditional independence, or reversibility.
H2.6a-R0 is accepted:
its scalar spike proves density factorization, exact joint-law and evidence
marginal identities, and evidence-a.e. equality to Mathlib's native posterior.
The accepted H2.6a maintained owner reuses that proof route and adds the
chronological finite observation recursion. Accepted H2.6b derives the actual
one-step posterior-predictive quadratic risk under the selected transition,
finite attainment, and evidence-a.e. native selector agreement. Its strict and
tie witnesses do not imply policy-tree, reward--EFE, global Bayes-estimator, or
infinite-horizon control.

### Required symmetric-precision `Fin 4` slice

Use standardized dimensionless coordinates in the fixed order external,
sensory, active, internal. The exact positive-definite symmetric precision
witness is

\[
K_\star =
\begin{pmatrix}
4 & -1 & -1 & 0 \\
{-1} & 4 & 0 & -1 \\
{-1} & 0 & 4 & -1 \\
0 & -1 & -1 & 4
\end{pmatrix},
\qquad
\Sigma_\star = K_\star^{-1}
=
\begin{pmatrix}
7/24 & 1/12 & 1/12 & 1/24 \\
1/12 & 7/24 & 1/24 & 1/12 \\
1/12 & 1/24 & 7/24 & 1/12 \\
1/24 & 1/12 & 1/12 & 7/24
\end{pmatrix}.
\]

The implementation proves symmetry, positive definiteness, both inverse
identities, eigenvalues `2, 4, 4, 6`, leading principal minors
`4, 15, 56, 192`, and the exact displayed entries. `Sigma` is defined from
`K`; it is not an independently supplied covariance field.

For mean \(m\), construct the transition directly with mean
\(m + \exp(-tK)(x-m)\) and covariance
\(\Sigma - \exp(-tK)\Sigma\exp(-tK)^{\mathsf T}\). With symmetric \(K\),
\(\Sigma=K^{-1}\), and diffusion covariance \(2I\), derive the Lyapunov
identity, transition normalization, Chapman--Kolmogorov law, invariant
Gaussian, and weak convergence. This transition-law statement does not assert
an SDE solution. Time zero is the identity/Dirac kernel; positive time owns the
nondegenerate Gaussian covariance proof. The exact witness also exposes the
external--internal precision zeros while retaining nonzero external--internal
covariance. H2.5d owns only the resulting observational native conditional
factorization; H3.2, not H2.5, owns any scientific, causal, or interventional
blanket interpretation.

### Stop/go slices

1. **H2.5a — scalar regression:** prove the scalar transition, native
   semigroup, invariant law, weak convergence, and exact H2.1 constructor
   equality. Failure retains H2.4 and closes H2.5b--H2.7.
2. **H2.5b — symmetric-precision linear Gaussian:** prove generic inverse,
   matrix-exponential, transition-covariance, measurable-kernel, semigroup, and
   scalar-regression laws. Failure blocks H2.5c/d, H2.7, and continuous H3
   eligibility; independently green scalar H2.6 work may continue.
3. **H2.5c — exact four-coordinate carrier:** instantiate the displayed
   `Fin 4` matrices and export the native transition, semigroup, invariant law,
   weak convergence, and exact scalar-specialization theorem. Failure blocks
   H2.5d, H2.7, and continuous H3 eligibility.
4. **H2.5d-R0 — native conditioning repair:** on the fixed centered Fin4
   stationary law, reconstruct the actual blanket/endpoints joint as a
   `compProd`, identify Mathlib's conditional distribution blanket-marginal
   almost everywhere, and prove the endpoint `CondIndepFun` theorem. A PDF or
   Schur-complement identity alone is not acceptance. Failure keeps H2.5d,
   H2.7, and continuous H3 closed.
5. **H2.5d — maintained conditioning/precision:** promote the accepted R0
   route to arbitrary centers in the maintained owner and add the exact bounded
   endpoint-precision perturbation/non-independence witness. This is not a
   generic converse. This slice is accepted; its exact declarations are solid
   H2.7 inputs. Failure would have blocked H2.7 and continuous H3 eligibility.

All four maintained resources and the R0 decision land before H2.7. H3.G0 may inspect their accepted
declarations and source-bound evidence; it may not prove, patch, extend, or
replace them.

### Brownian representation branch

An optional theorem may identify the finite-dimensional laws with an affine
transformation of a pre-Brownian process. Go only if it reuses Mathlib's
Brownian-law APIs and does not require a locally invented stochastic integral.

### No-go boundary

If either transition-law semigroup does not compile cleanly, retain H2.4 and
stop. Do not write an `SDE`, `ItoIntegral`, `FokkerPlanckSolution`, covariance,
or invariance structure whose fields merely assume the missing mathematics.

## H2.6 — Gaussian filtering, control, and finite-grid path laws

**Dependencies:** H2.6a depends on H2.1a and H2.5a. H2.6b depends on H2.4b,
H2.6a, and accepted H1.4. H2.6c depends on H2.4b and H2.5a. H2.3 parameter
learning is a separate lane and meets these results only at H2.7.

**Single owners:** `compositions/gaussian_filter.lean` owns the scalar native
filter; `compositions/gaussian_control.lean` owns finite filter-consuming
control; and `compositions/gaussian_grid_path.lean` owns finite-grid path-law
results. Existing temporal, policy, and path modules retain their generic laws.

**Implementation status:** H2.6a-R0 and H2.6a/b/c are accepted. The R0 spike
derives the selected closed Gaussian posterior from H2.1a/H2.5a, proves the
exact joint-law and evidence-marginal identities, and reaches Mathlib's native
posterior evidence almost everywhere. The maintained filter owner consumes
that route, derives the exact posterior parameters and normalization, and
recurses chronologically over finite observation lists. The maintained H2.6b
owner derives one-step transition-consuming quadratic risk and finite
attainment, with native-posterior selector agreement only evidence almost
everywhere. H2.6c's typed monotone `TimeGrid`
prevents descending timestamps from being silently truncated to zero-duration
steps; repeated timestamps explicitly denote identity steps. The maintained
composition proves exact `partialTraj` order, normalized forward and
coordinate-reversed laws, measurable involutive reversal, bounded-continuous
observable transfer, a reverse-law-a.e. RN ratio, forward-oriented native KL
and real expected-log-ratio identities under explicit support/integrability,
and `∞` at either failure boundary. It does not construct reverse OU dynamics,
prove reversibility, or make continuous-path or physical-entropy claims.

### Target declarations

- exact one-step and finite-recursion Gaussian filtering;
- an `observationKernel_eq_gaussianLocation` theorem for the fixed-noise
  observation model used by H2.1 and H2.3;
- a Kalman update as a native posterior identity;
- prediction/update covariance and zero-evidence boundaries;
- one-step finite-action posterior-predictive quadratic decision risk on the
  exact H2.6a posterior and exact H2.4b/H2.5a transition, with finite
  attainment and evidence-almost-everywhere native-posterior agreement; no
  EFE, reward equivalence, or policy recursion is claimed;
- finite-grid forward and reversed path laws;
- supported finite-grid density-ratio and path-law KL identities, never
  physical entropy production without a separate constitutive theorem; and
- convergence of bounded-continuous grid observables when H2.5 supplies weak
  convergence.

Entropy, log path ratios, and other unbounded or support-sensitive observables
require common support plus a separately proved uniform-integrability,
entropy-convergence, or domination hypothesis. Weak convergence alone does not
transfer them.

Continuous-time Kalman--Bucy optimality, Girsanov path densities, and continuous
path entropy production are stretch goals blocked on their own API spikes.

### Acceptance

- Filtering and control consume the same transition and observation kernels.
- Finite-grid path claims remain finite-grid claims.
- Preference, reward, physical energy, and information terms are separately
  typed or separately named.

## H2.7 — smooth/stochastic terminal theorem

**Depends on:** accepted H2.7-R0 plus H2.1b, H2.2a, H2.3b, H2.4b,
H2.5a, H2.5c, H2.5d, H2.6a, H2.6b, and H2.6c. H2.2b is optional.

H2.7-R0 is the source-bound proof gate for the previously missing continuous
Gaussian seam. It must derive density-relative evidence surprisal, the
recognition-to-exact-posterior native-KL VFE gap, its mean-coordinate
differential, the Fisher-metric-dual natural-gradient tangent, and strict local
descent away from the posterior mean. H1 finite-law VFE and H2.2a coordinate
duality are not substitutes.

**Single owner:** one manifested composition leaf
`formal/compositions/smooth_reference_kernel.lean`, namespace
`FEPComposed.SmoothReferenceKernel`.

### Terminal certificate

On the one H2.1 Gaussian location-family/H2.5 OU model, prove a connected chain:

1. transition and observation kernels are normalized;
2. the chosen law is invariant or evolves by the proved semigroup;
3. the latent-state filter is the native Bayesian update for the H2.6
   observation kernel;
4. the H2.3 posterior over the selected Gaussian mean parameter converges under
   stated identifiability, and its bounded-continuous risk consequence is
   separate from latent-state filtering;
5. density-relative VFE/KL uses the H2.7-R0 continuous Gaussian bridge, while
   decision risk remains the H2.6b one-step quadratic objective;
6. the Fisher metric and derived local natural-gradient statement use that
   same H2.1 posterior Gaussian family;
7. the finite-horizon control result consumes the same filtered state; and
8. native KL or an explicitly named Lyapunov functional dissipates.

The theorem docstring must list the H1 clauses that did not transfer. In
particular, a finite log-mass identity is not automatically a continuous
density identity.

### Horizon 2 exit gate

- Every mainline target compiles against the exact stable pin with no warning or
  unapproved axiom.
- At least one smooth full-rank witness and one degeneracy countermodel exist.
- The Gaussian semigroup is constructed, not assumed.
- H2.5's scalar and exact symmetric-precision `Fin 4` constructors, their
  scalar-specialization theorem, and the displayed `K`/`Sigma` witness are
  accepted before the H2.7 merge; H3 is not their implementation owner.
- H2.3 uses H2.1's exact observation law; every positive-time H2.5 transition
  instantiates H2.1's Gaussian location constructor at the proved variance;
  H2.6 uses both equalities rather than name-level similarity.
- Unsupported Itô/SDE/path-measure statements are absent from declarations and
  scientific prose.
- The terminal theorem receives formal, domain, and skeptical review under the
  [research contract](research-contract.md).

Horizon 3 remains closed until this gate and its claim review pass.
