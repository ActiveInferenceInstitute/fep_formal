# FEP background and formalization boundary

This page supplies conceptual orientation for the catalogue. It does not claim
that every displayed scientific object has been constructed in Lean. For the
exact proposition proved by each row, use the
[formalism coverage report](../formalism-coverage.md) and canonical family body.

## Variational free energy

For an approximate posterior \(q(s)\), generative joint \(p(o,s)\), and the
usual density, integrability, and conditioning assumptions, variational free
energy is commonly written

```text
F(q) = E_q[log q(s) - log p(o,s)]
     = KL(q || p(.|o)) - log p(o).
```

KL nonnegativity then yields \(F(q) \ge -\log p(o)\). The current fep-002 row
formalizes a deliberately narrower, extended-nonnegative-real core: surprisal
plus Mathlib's native `InformationTheory.klDiv`, its upper bound, and exactness
at self-divergence under the library's stated instance. It does not construct
the posterior from a joint law or turn an infinite KL value into a real one.

fep-014 separately reuses native KL self/zero results and the
composition-product chain rule for finite measures and Markov kernels. The
pinned revision also exposes native measure-KL data processing under a Markov
kernel as `InformationTheory.klDiv_comp_right_le`. That upstream theorem is not
part of fep-014's maintained theorem surface, and it does not identify native
extended KL with the project's totalized real finite KL.

The maintained finite active-inference kernel supplies the complementary
real-valued construction. A normalized generative model derives a positive-
evidence posterior and defines posterior-form VFE as finite KL plus surprisal.
Lean proves the surprisal bound, the equivalent evidence lower bound, exact-
posterior attainment, and uniqueness even when the posterior has zero-mass
states. This is a finite theorem under the package's explicitly totalized real
KL convention, not an automatic bridge to every measure-valued or physical
free-energy convention.

## Active inference and expected free energy

Active-Inference models evaluate future policies with an Expected Free Energy
objective whose decompositions depend on the selected predictive and
preference model. Moving between risk/ambiguity and
epistemic/pragmatic formulations requires real probabilistic hypotheses; an
algebraic rearrangement alone is not enough.

The catalogue provides finite pragmatic-cost sums, minimizer existence,
support-aware normalized softmax weights, entropy-regularized policy costs,
Bellman recursion, and matrix--vector message propagation. fep-021 defines EFE
as pragmatic cost minus epistemic information in `ENNReal`, proves exact
reconstruction under the visible value-at-most-cost premise, and composes with
fep-041's native KL information gain. The maintained finite kernel now adds one
shared policy-conditioned predictive/preference model and proves both
pragmatic-minus-epistemic and risk-plus-ambiguity decompositions, support-aware
nonnegativity, normalized prior-weighted policy selection, action pushforward,
chronological finite-horizon rollout, and recursive stage-dependent cumulative
EFE with an exact concatenation law. Its action interface also proves that the
selected action recovers the policy transition and that the infer--select--act
joint's action marginal equals the advertised action law. A two-policy Boolean
model proves that changing the policy prior changes the posterior even when all
policies have equal EFE. The controlled-Markov expansion additionally gives a
two-stage Boolean witness where observation-dependent feedback strictly beats
every open-loop alternative in that carrier. The later finite policy-tree
family defines observation-contingent trees at arbitrary finite depth, proves
Bellman minima and optimizer existence, embeds open-loop plans, and proves
closed-loop weak dominance plus a treewise EFE decomposition. It is not an
infinite-horizon, continuous-belief, or universal EFE-equivalence theorem.

The H1 terminal composition closes one deliberately smaller chain through
shared values. In the selected Boolean sampling model, two `true` observations
give posterior masses `1/10` and `9/10`; one further `true` update is lifted to
the sixteen-state Boolean internal--sensory--active--external carrier. Under a
false-positive report cost four times the false-negative cost, the
posterior-dependent continuation selects `true` and strictly beats either
fixed report. Its action interface identifies that emitted action with the
generative transition and the exact positive-time refresh kernel. This is a
model-specific one-step posterior--decision--action certificate, not
transition-aware planning, EFE-optimal control, or a claim about how future
transition consequences determine the report. The exact theorem lives in
[`finite_reference_agent.lean`](../../src/fep_lean/formal/compositions/finite_reference_agent.lean).

## Bayesian mechanics and Markov blankets

A Markov-blanket claim combines at least two different structures:

1. a partition of states into internal, sensory, active, and external blocks;
2. a conditional-independence statement for a particular joint law or
   dynamics.

fep-005 proves an exact four-label finite partition with unique membership.
fep-009 uses Mathlib's `CondIndep` predicate to prove symmetry and conditional
independence from the trivial σ-algebra. The maintained blanket foundation
adds a normalized finite law of the form `P(b)P(i|b)P(e|b)`, proves exact
positive-mass conditional factorization and zero conditional mutual
information, and constructs a typed four-component transition with a
nontrivial Boolean witness. Each transition row is identified with a derived
static blanket model and inherits factorization and zero conditional mutual
information. The finite-to-native family embeds the laws and kernels as
Mathlib measures and kernels, proves singleton/expectation/prediction transfer,
derives native `CondIndepFun` for the static joint, preserves it under
measurable endpoint coarsening, and proves it rowwise for factorized
transitions. It does not prove that prior mixtures retain the factorization or
that arbitrary dynamics admit a blanket.

H1 adds one selected invariant instance without changing that generic
boundary. Its full-support uniform law on the sixteen Boolean `(I,S,A,E)`
states factorizes as `P(S,A)P(I|S,A)P(E|S,A)`, and the refresh kernel selected
by the emitted `true` action preserves that same law. The result does not infer
causal direction from observational factorization, identify a blanket in an
arbitrary dynamics, or supply a biological interpretation.

fep-010 proves that a reversible Markov kernel leaves its reference measure
invariant and supplies the identity kernel as a concrete witness. That row
alone does not prove irreducibility, convergence to equilibrium, or a
continuous-time process. The later path-space family constructs normalized
finite forward/reverse laws and proves detailed/integral fluctuation and
Jarzynski identities under explicit support and work-normalization premises.

fep-025 defines finite forward-minus-reverse current and divergence, derives
zero divergence from transition normalization and stationarity, and exhibits a
directed three-state cycle with nonzero divergence-free current. This is an
exact finite NESS witness. It does not imply a continuous Fokker--Planck law,
state-dependent Helmholtz/Ao decomposition, or NESS existence for a diffusion.

## Information geometry

The full Fisher geometry of a family \(p_\theta\) requires a differentiable
parameterized family, score functions, expectations, regularity conditions,
and a tangent-space metric. The natural gradient additionally requires a
nondegenerate inverse metric and coordinate transformation laws.

The topic rows close one family deeply, and the maintained geometry foundation
adds a reusable multidimensional finite score carrier:

- fep-038 differentiates the normalized Bernoulli mass, derives zero expected
  score and Fisher information `1 / (p * (1-p))`, proves metric positivity,
  defines its natural gradient, and proves the coordinate-pullback law;
- fep-004 abstracts a finite positive-weight diagonal Fisher metric and an
  authored theorem identifies its one-coordinate specialization with fep-038;
- fep-018 defines the Bernoulli Fisher--Rao coordinate distance and proves
  nonnegativity, symmetry, triangle inequality, and point separation;
- fep-029 directly defines the scalar Bregman divergence generated by
  \(\phi(x)=x^2\), proves it equals \((x-y)^2\), proves nonnegativity, and proves
  point separation;
- fep-044 defines Bernoulli squared Hellinger divergence and proves
  nonnegativity, symmetry, separation, and relabeling invariance; and
- fep-014 and fep-024 provide native measure-KL and KL-regularization laws.

For any finite parameter dimension, the foundation proves Fisher-matrix
symmetry, Gram-metric positive semidefiniteness, positive definiteness under
full-support identifiability, positive pullbacks along injective Jacobians, and
existence and uniqueness of inverse-Fisher natural-gradient raising when the
matrix is invertible. The premises are concretely sharp: an interior Bernoulli
family has Fisher entry `1 / (p * (1-p))` and an executable natural gradient,
whereas a two-parameter duplicated-score family has a nonzero null tangent,
zero Fisher norm, and fails identifiability.

The categorical expansion further proves tangent-space Fisher positivity,
scalar Cramér--Rao, invertible-chart natural-gradient equivariance, a
mirror-descent three-point identity, affine Bregman projection, and
replicator--natural-gradient equivalence, with explicit full-rank and null
directions. The later scalar exponential-family foundation adds positive
normalization, the affine log-density ratio, log-partition gradient and
Hessian, centered score, Fisher--variance equality, KL--Bregman duality, and
mean-coordinate injection on intervals of positive variance. These remain
finite chart-level results, not a general smooth statistical manifold with
dual connections, curvature, or geodesic existence.

## Thermodynamic analogies

Helmholtz free energy \(U-TS\), variational free energy, and a negative log
density are different mathematical objects until a model supplies an energy
map, units, normalization, temperature, and compatible probability law.
fep-013 differentiates \(U(T)-T S(T)\) exactly and derives \(F'=-S\) from the
explicit equilibrium premise \(U'=TS'\). An authored theorem instantiates it
with fep-040's native Gaussian law and thermal entropy. No theorem identifies
this object with fep-002's variational free energy.

fep-031 is stronger at a finite algebraic boundary: positive exponential
weights have a positive partition sum on nonempty support, and division by
that sum yields nonnegative weights summing to one. fep-030 proves Mathlib's
binary entropy is at most `log 2`, with equality exactly at one half, and also
retains the explicit uniform finite entropy calculation. A composed theorem
shows that a two-state Gibbs law at zero inverse temperature—therefore the
infinite-temperature limit—attains that binary maximum. The project still
does not derive the general constrained Gibbs form from maximum entropy or
prove arbitrary finite-simplex maximality.

The finite thermodynamic layer is also direct at its stated scope. fep-037
proves two-state autocorrelation and response decay; fep-049 proves nonnegative
quadratic and edge-flux entropy production with equality characterizations;
and fep-050 derives Landauer heat and work bounds from explicit second-law and
work-transfer premises. The path-space expansion supplies finite path laws,
reversal ratios, fluctuation identities, a finite Jarzynski equality, local
current cancellation, and reversible KL dissipation. It does not construct
continuous path measures, general cross-coupled Onsager dynamics, or a
microscopic erasure protocol.

The two-state continuous-time family adds a different exact layer: positive
Boolean jump rates determine a normalized transition kernel for nonnegative
time, the kernels form a Chapman--Kolmogorov semigroup, every entry solves both
master equations, the explicit stationary law is reversible, and arbitrary
initial true-state mass relaxes exponentially with an exact quadratic Lyapunov
derivative. This is a genuine continuous-time Markov example, not a general
CTMC constructor, a driven nonequilibrium steady state, or a continuous-state
SDE/Fokker--Planck theory.

The H1 refresh semigroup is another finite continuous-time instance. For the
same lifted posterior produced by the further `true` update, its selected
positive-time kernel strictly decreases both the repository's real `finiteKL`
and Mathlib-native `InformationTheory.klDiv` to the full-support invariant
uniform law. Those are probability-divergence inequalities. They are not
measured heat, physical entropy production, or thermodynamic free-energy
dissipation.

The offline [formalism atlas](../formalism-atlas.html) distinguishes such
conceptual frontiers from checked formal seams; imports never create an
automatic scientific edge. fep-036 closes its reviewed finite empirical-Bayes
capability with a binomial model and deterministic consistency transfer, while
the statistical-convergence foundation derives Boolean, finite-atom,
simultaneous, and whole-law `L¹` strong-law limits under explicit hypotheses.
The learning family adds separate finite-sample concentration and
model-evidence theorems. The later empirical-risk family composes the exact
fep-036 Laplace estimator with finite-law squared/Brier-risk bounds and
concentration-event transfer. H1 separately proves posterior bad-mass
contraction for its selected identifiable Boolean model. Posterior contraction
for the Laplace empirical-Bayes estimator or broader model classes, empirical
calibration, minimax risk, and a generic marginal-likelihood optimum remain out
of scope.

## What Lean acceptance establishes

A warning-free, `sorry`-free native receipt establishes that the exact stated
propositions are accepted by the pinned Lean kernel and current imports. It
does not establish:

- that the formal definitions are the uniquely correct interpretation of an
  FEP paper;
- that theorem hypotheses hold for a biological or physical system;
- that separate topic rows compose into one theory;
- that the FEP is empirically true; or
- that an optional LLM or OpenGauss workflow ran.

In particular, acceptance of the H1 terminal theorem establishes its finite
synthetic one-step implication only. It does not establish transition-aware or
EFE-optimal control, causal identification, physical dissipation, empirical
adequacy, or a universal Free Energy Principle.

Those boundaries are first-class project data: semantic dispositions, authored
relations, retained capability nodes, native receipts, and full-run receipts
remain separate.

## Primary routes for deeper reading

- [Manuscript background](../manuscript/02b_background.md)
- [Pinned Mathlib surface](lean4.md)
- [Theorem maturity policy](../generated/theorem-maturity-audit.md)
- [Formalism coverage and retained capabilities](../formalism-coverage.md)
- [Formal-kernel methods and validation](formal-kernel-methods.md)
- [Deterministic formal-kernel dashboard](../formal-kernel-dashboard.html)
- [Topic inspection and reproduction](../topics-reference.md)
