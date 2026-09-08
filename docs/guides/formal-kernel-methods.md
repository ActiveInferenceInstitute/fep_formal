# Formal-kernel methods and validation

The maintained formal kernel turns recurring finite probability structures into
shared Lean objects instead of re-encoding them independently in topic rows.
Its purpose is not to make every formulation of the Free Energy Principle
(FEP) definitionally identical. It provides a checked common language in which
specific variational-free-energy, expected-free-energy, Bayesian-inversion,
control, temporal, causal, predictive-coding, path-thermodynamic,
information-geometric, collective, and learning claims can meet under visible
hypotheses.

The authoritative module set and dependency order live in
[`src/fep_lean/formal/manifest.py`](../../src/fep_lean/formal/manifest.py). The
files under [`src/fep_lean/formal/`](../../src/fep_lean/formal/) are canonical;
their copies under `lean/FepSketches/` are generated Lake inputs. The
[formalism coverage report](../formalism-coverage.md) is the generated declaration
inventory, not an authoring surface.

## Two theorem planes

The project intentionally has two related theorem planes:

- A **topic plane** gives every stable catalogue row a reviewed theorem proxy,
  a primary declaration, assumptions, non-vacuity evidence, and a semantic
  disposition. Topic bodies remain independently inspectable and compile as
  one generated aggregate.
- A **shared-kernel plane** supplies normalized carriers and laws that several
  topics can reuse. Manifested leaf composition modules are the only places
  where one stable topic namespace may establish a formal scientific relation
  with another; `composed.lean` only imports those leaves.

An import between modules is an implementation dependency, not a scientific
claim. A cross-topic relation becomes formal only when
[`config/formalism_relations.yaml`](../../config/formalism_relations.yaml) names a
qualified Lean declaration as its witness. The atlas therefore renders module
imports in a separate dependency layer rather than silently treating them as
theorem edges.

## Layered mathematical contracts

### Normalized finite probability

The probability foundation starts with a finite law whose masses are
nonnegative and sum to one. A finite kernel has the same contract in every
input row. Products, marginals, deterministic maps, joints, prediction,
posterior construction, and kernel composition preserve that normalization.

The algebra includes identity and associativity laws for kernel composition,
compatibility of prediction with composition, product-marginal recovery, and a
Bayes reconstruction equation. Posterior construction requires the observed
outcome to have positive predictive mass; the condition is a theorem argument,
not an implicit fallback for zero evidence.

This layer is deliberately finite and real-valued. It complements Mathlib's
measure-and-kernel results in the topic plane without claiming that the two
representations are interchangeable without a proved bridge.

### Finite information theory

Entropy uses the continuous zero-mass convention, while finite Kullback--Leibler
(KL) divergence uses Mathlib's nonnegative `klFun` integrand. This supports
unconditional nonnegativity and self-divergence, including laws with zero-mass
atoms. Normalization is strong enough to make zero KL separate arbitrary finite
laws, including reference laws with zero-mass atoms. Conditional KL separates
kernel rows when the input law has positive mass on every row; no positivity of
the reference rows is needed for that conclusion.

The layer relates entropy, cross-entropy, KL divergence, conditional entropy,
conditional KL divergence, and mutual information. It proves chain rules for
finite prior-kernel joints and additive laws for independent products. These
are normalized finite identities; they do not erase the distinction between a
real-valued totalization and Mathlib's extended-valued measure KL. Positive
reference support remains necessary for the proved logarithmic cross-entropy
identity and the chain laws derived through it. The boundary is executable:
for disjoint Boolean point masses the totalized cross-entropy is zero and the
totalized KL is one, rather than the positive infinity of extended-valued KL.

### Model-derived active inference

One finite generative-model carrier owns the initial state law,
policy-conditioned transition kernels, observation likelihood, outcome
preferences, and policy prior. From that carrier, the formalization derives
state predictions, state-outcome joints, outcome predictions, positive-evidence
posteriors, and chronological open-loop rollouts.

Posterior-form variational free energy is defined from finite KL divergence and
outcome surprisal. The checked laws show that it upper-bounds surprisal, that
the exact posterior attains the bound, and that attainment uniquely identifies
that posterior even when some posterior states have zero mass. The equivalent
evidence lower bound is therefore a theorem about this explicit finite model,
not a slogan imported from prose.

Expected free energy is derived from the same predictive joint and preference
law. Its pragmatic-minus-epistemic definition and its risk-plus-ambiguity
decomposition agree under explicit full-support assumptions. Those assumptions
also reject a preferred-outcome law that assigns zero mass to an outcome before
the policy posterior is formed. Policy weights combine the prior with
precision-scaled expected free energy; normalization produces a posterior
policy law, finite minimizers and maximum-a-posteriori policies exist, and a
policy-to-action map pushes that law forward to actions. An `ActionInterface`
additionally requires the action-indexed transition to recover the selected
policy transition. The resulting infer--select--act joint is normalized, has
the policy posterior as its policy marginal, factors pointwise, and has exactly
the advertised action law as its action marginal.

A two-policy, two-state, two-observation Boolean model makes these contracts
non-vacuous. It has uniform predictions, zero preference risk, ambiguity and
EFE equal to the uniform Boolean entropy, and a policy posterior equal to its
prior. Replacing a three-quarters prior on `true` with a one-quarter prior
changes the posterior mass of `true` from `3/4` to `1/4` at every precision,
pinning the prior factor that a normalization-only test could miss.

The original rollout theory is open-loop: it composes a chronological list of
policy-indexed transitions and predicts the terminal state and outcome laws.
A second recursion updates the predicted state law at every stage, accumulates
stage-dependent expected free energy, proves exact prefix--suffix
decomposition, and derives nonnegativity from a recursive full-support
contract. The controlled-Markov foundation first added a finite two-stage
feedback policy and a strict witness against its open-loop alternatives. The
later `FEP.PolicyTrees` foundation generalizes that seam to arbitrary finite
depth on finite belief/action/observation carriers: it defines
observation-contingent trees, proves finite Bellman minima and optimizer
existence, embeds open-loop plans, proves closed-loop weak dominance, and lifts
the maintained EFE decomposition treewise. This still does not establish
online optimality on an unrestricted belief simplex, infinite horizon, or
learning a distribution over trees.

### Finite Markov blankets

The blanket foundation separates state partitioning from probabilistic
factorization. Its normalized static law has the form
`P(blanket) P(internal | blanket) P(external | blanket)`. From that carrier,
Lean proves the positive-mass conditional factorization and zero conditional
mutual information of internal and external states given the blanket.

A typed dynamics carrier additionally separates internal, sensory, active, and
external transition components and supplies a nontrivial finite witness. Every
transition row is proved equal to the static joint of a current-state-indexed
`nextStaticModel`; positive-mass rows therefore inherit exact conditional
factorization and zero conditional mutual information. This is a row-wise
dynamic seam, not a claim that arbitrary mixtures preserve blanket
factorization or that the law is stationary. The later
`FEP.NativeBlanket` foundation proves the missing finite-to-native seam: a
weighted-Dirac embedding preserves singleton masses, expectations, prediction,
and the static rectangle factorization; the embedded joint satisfies
Mathlib's native `CondIndepFun`; measurable endpoint coarsening preserves that
predicate; and every supplied factorized transition row inherits it. This does
not make all measure-theoretic conditional-independence formulations
definitionally identical or prove blanket existence for arbitrary dynamics.

### Multidimensional information geometry

A finite score model carries a normalized outcome law, a score field in any
finite parameter dimension, and the centered-score identity. Its Fisher matrix
and bilinear metric are derived from the probability-weighted score Gram form.
The metric is symmetric and positive semidefinite without hidden regularity
assumptions.

Full support and score identifiability yield positive definiteness. Pullback
along a Jacobian preserves semidefiniteness, and an injective Jacobian preserves
positive definiteness. When the Fisher matrix is invertible, inverse-matrix
raising constructs the natural gradient and proves its defining matrix and
metric dualities, Fisher-energy identity, and uniqueness. Pullback through a
composite Jacobian also agrees exactly with successive pullback.

Two concrete families expose both sides of the nondegeneracy premise. An
interior one-parameter Bernoulli score model has Fisher entry
`1 / (p * (1 - p))`, an invertible one-by-one matrix, and natural-gradient
scaling by `p * (1 - p)`; at `p = 1/2` its scores are exactly `±2` and its
Fisher entry is four. A two-parameter model with duplicated scores has an
all-four Fisher matrix and an explicit nonzero tangent with zero score pairing
and zero Fisher norm, so identifiability fails. Positive definiteness and
invertibility are therefore witnessed hypotheses, not vacuous interfaces.

This is multidimensional finite linear algebra. The later geometric-
optimization foundation adds categorical simplex tangents, scalar
Cramér--Rao, invertible-chart natural-gradient equivariance, mirror descent,
affine Bregman projection, and replicator equivalence. Neither layer constructs
arbitrary smooth connections, curvature, general geodesic existence, or an
infinite-dimensional statistical manifold. A separate finite scalar
exponential-family foundation now supplies a differentiable family with
positive support, log-partition gradient and Hessian, centered score,
Fisher--variance equality, KL--Bregman duality, and mean-coordinate injection
on intervals of positive variance. It closes a concrete dual-geometric family,
not the general manifold and connection theory.

### Strong-law consistency

The convergence foundation instantiates Mathlib's almost-sure real strong law
for Boolean observations without importing a topic namespace. It extends the
argument to every atom of a finite-valued process, intersects the finite family
of almost-sure events, and derives
whole-law convergence in finite `L¹` distance. On that same almost-sure event,
the empirical expectation and absolute expectation error converge for every
real observable on the finite state space.

The topic-specific transfer through fep-036's Laplace-smoothing identity lives
in `FEPComposed.fep036_smoothedRate_strongLaw`, preserving the rule that a
foundation supplies generic mathematics while a composition leaf owns
cross-topic bridges.

Integrability, pairwise independence, and identical distribution are explicit
premises for the indicator processes. These theorems are asymptotic and
almost-sure. The learning foundation separately supplies sub-Gaussian and
finite-alphabet concentration, PAC-Bayes, posterior-gap, mixture-regret, and
Bayes-factor laws under their own premises. The later empirical-risk foundation
uses the exact fep-036 Laplace estimator to prove finite-law squared-risk and
Brier-risk transfer and containment of the smoothed bad event in a supplied raw
event. Those results still do not turn the carrier into an empirical guarantee
for a particular data set, a posterior-contraction theorem, or a calibration
study.

### Expansion foundations and boundaries

The expanded manifest adds mathematically distinct carriers rather than aliases
for the original finite kernel:

- measure-valued Radon--Nikodym reconstruction, posterior-kernel swapping, and
  finite Bayesian inversion with explicit positive-evidence boundaries;
- finite Gibbs variational duality, coordinate ELBO/IWAE bounds, data
  processing on a named channel carrier, and rate--distortion weak duality;
- controlled kernels, reachable finite belief models, soft Bellman and
  desirability recursions, finite feedback, filtering, smoothing, hierarchy,
  and model averaging;
- ordered finite causal factorization, intervention kernels, non-descendant
  invariance witnesses, and precision-weighted generalized prediction errors;
- normalized forward/reverse path laws, fluctuation and Jarzynski identities,
  local-current cancellation, and reversible one-step KL dissipation;
- product-agent VFE/EFE laws, unit-weight product-of-experts pooling, consensus
  contraction, coupled potential descent, concentration, a conditional
  PAC-Bayes loss-gap bound, and model-evidence updates;
- Laplace error, finite squared/Brier risk, and concentration-event transfer;
- arbitrary finite-depth observation-contingent policy trees, open-loop
  embedding, Bellman optimality, treewise EFE, and a strict feedback witness;
- finite-law and finite-kernel embedding into native measures/kernels, native
  blanket `CondIndepFun`, endpoint coarsening, and rowwise transition closure;
- a full-support finite scalar exponential family with log-partition,
  score/Fisher, KL/Bregman, and mean-coordinate laws; and
- an exact positive-rate two-state continuous-time kernel with semigroup,
  master-equation, detailed-balance, relaxation, and Lyapunov laws.

Each result retains its support, normalization, rank, independence, or
nonzero-denominator hypotheses. Composition bridges document reuse across
topic namespaces; they do not identify the carriers beyond the theorem stated.

## Authoring method

Start with a mathematical contract rather than a desired topic label:

1. State the carrier, codomain, support assumptions, and zero-mass convention.
2. State the law at the narrowest useful level and supply a nontrivial witness
   or boundary case.
3. Put reusable carrier laws in the relevant foundation module. Put a theorem
   that genuinely consumes multiple stable topic namespaces in the appropriate
   manifested composition leaf, and record the required novelty or relation
   bridge. Do not use imports alone as evidence of composition.
4. Add behavior tests that inspect declarations, projection identity, module
   dependencies, and the mathematical contract rather than only checking file
   existence.
5. Project the canonical source into Lake, compile the aggregate, and run the
   declaration/axiom audit.
6. Update authored capability evidence only after the qualified declaration
   exists. Regenerate coverage and both visual projections from their canonical
   owners.
7. Align manuscript prose with the theorem's exact assumptions and retained
   limitations.

Topic-local work follows the additional semantic-review workflow in the
[formalism authorship guide](../authorship-guide.md). Shared-kernel changes must
also preserve the dependency order in the manifest and must not introduce an
import cycle merely to reuse a downstream result.

Coverage generation enforces the composition rule: both a derivational
`formal` edge and a non-implicational `formal_pairing` must resolve to a theorem
in a manifested composition leaf, and that theorem's checked declaration block
must reference both endpoint topic namespaces. A merely qualified but
unrelated theorem name fails the build. Only `formal` participates in the
directed dependency acyclicity check.

## Validation ladder

No single green command answers every validation question:

| Question | Required evidence | What it does not establish |
| --- | --- | --- |
| Are generated Lean files exact copies of canonical sources? | Formal-module projection `--check` | Type correctness or theorem meaning |
| Do the maintained modules type-check together? | `lake build FepSketches` with no warnings or proof holes | Scientific adequacy or external execution |
| Do every reviewed declaration and relation witness resolve without `sorryAx`? | Formalism declaration/axiom audit receipt | Assumption realism or empirical truth |
| Do catalogue rows compile from current bytes? | Validated native exact-roster receipt | Hermes/OpenGauss execution or shared-kernel audit |
| Do semantic claims match theorem scope? | Maturity records, assumption review, non-vacuity review, and human review | Provider execution |
| Are the graph and numerical views current? | Atlas and dashboard drift checks plus renderer tests | New deductive evidence |
| Did the provider-backed workflow complete? | Independently validated complete full-mode report | A broader theorem than the compiled source states |

Run the deterministic formal and visual checks from the repository root:

```bash
uv run python scripts/_maint_build_formal_modules.py --check
uv run python scripts/build_formalism_coverage.py --check
uv run fep-lean atlas --check
uv run fep-lean dashboard --check
uv run pytest \
  tests/test_formal_foundations.py \
  tests/test_formalism_coverage.py \
  tests/test_formalism_atlas.py \
  tests/test_formal_kernel_dashboard.py \
  -q --no-cov
```

Run native acceptance separately:

```bash
(cd lean && lake build FepSketches)
uv run python scripts/audit_formalisms.py \
  --receipt output/formalism-audit.json
uv run fep-lean verify --fail-on-warnings \
  --receipt output/native-verification.json
```

The first receipt covers the maintained declarations, actual compiler identity,
resolved Mathlib revision, and reported axioms under the versioned trusted
policy. The second covers the stable catalogue roster, actual compiler
identity, resolved dependency revision, and current topic source digests.
Publication claims that depend on both planes must cite both evidence classes
rather than substituting one for the other.

## Validation visualizations

The [formalism atlas](../formalism-atlas.html) answers a structural question:
which topic, capability, and maintained-module relationships are authored, and
which qualified declarations witness the formal ones? Its static
[SVG projection](../formalism-atlas.svg) preserves the same graph for publication.

The [formal-kernel dashboard](../formal-kernel-dashboard.html) answers a different
question: do deterministic numerical witnesses exhibit the qualitative shape
of selected checked laws? Its fifteen panels cover one diagnostic for each
expansion family: finite posterior reconstruction, Gibbs variational duality,
soft Bellman/desirability consistency, forward--backward smoothing,
intervention invariance, generalized prediction-error descent, a finite
fluctuation identity, categorical Fisher rank, consensus contraction, a
sub-Gaussian envelope, Laplace/Brier risk transfer, policy-tree feedback,
native blanket transfer, exponential-family KL/Bregman duality, and a
two-state master equation. The static
[dashboard SVG](../formal-kernel-dashboard.svg) is the manuscript-safe projection.

Dashboard values come from closed finite formulas and coverage-derived summary
metrics. Each witness owns typed equality, inequality, or predicate checks with
individual tolerances, and acceptance is their conjunction plus the boundary
observation. They are explanatory examples, not Monte Carlo calibration,
empirical data, or proof receipts. A plotted curve can expose a sign error or
projection drift; it cannot replace the corresponding Lean declaration or
validate a general theorem outside the sampled domain.

Regenerate and then drift-check the dashboard with either the public command or
its deterministic maintenance adapter:

```bash
uv run fep-lean dashboard
uv run fep-lean dashboard --check
uv run python scripts/build_formal_kernel_dashboard.py --check
```

Keep the evidence boundary visible in every downstream use: the atlas is a
provenance view, the dashboard is a numerical witness view, Lean receipts are
deductive evidence, and a full-mode report is execution evidence.
