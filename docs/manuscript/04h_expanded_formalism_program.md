# Expanded Formalism Program {#sec:expanded_formalism_program}

The first expansion from 50 to 120 topics is organized around ten theorem families rather than a
flat list of adjacent vocabulary. Each family has one reusable formal owner,
seven topic-scoped projections, a nontrivial finite or measure-theoretic
witness, and at least one bridge to an earlier declaration. This organization
matters mathematically: a normalization lemma, a variational equality, a
contraction theorem, and a path-space identity answer different questions even
when all four are described informally as "free-energy minimization."

## Bayesian inversion at two proof scales

The measure-theoretic layer starts from absolute continuity. For measures
$\mu\ll\nu$, the Radon--Nikodym derivative reconstructs the dominated measure,

$$
\nu\!\left[\frac{\mathrm d\mu}{\mathrm d\nu}\right]=\mu.
$$

Posterior kernels then reconstruct the swapped prior--likelihood joint and,
over standard Borel spaces, a conditional kernel disintegrates its joint
measure [@rokhlin1949fundamental]. These are almost-everywhere statements with explicit finiteness and
measurability premises. The finite layer has a different support boundary: at
an evidence atom $y$ with positive predictive mass,

$$
q(x\mid y)\,q(y)=p(x)\,k(y\mid x).
$$

The development keeps those two carriers connected without pretending that a
finite pointwise quotient proves unrestricted regular conditional probability.

## Variational duality and information bounds

For a finite reference law $p$ with full support and a bounded potential $f$,
the Gibbs variational identity has an explicit optimizer
$q_f(x)\propto p(x)e^{f(x)}$:

$$
\log\sum_x p(x)e^{f(x)}
=\sum_x q_f(x)f(x)-D_{\mathrm{KL}}(q_f\Vert p).
$$

This finite equality is the proof-relevant specialization of the variational
formula associated with Donsker and Varadhan [@donsker1975asymptotic]. It is
not an asymptotic large-deviation theorem. The same family treats coordinate
ELBO decomposition, mean-field coordinate minimization, channel data
processing, and rate--distortion weak duality. Its importance-weighted row
fixes a positive sample count and proves the Jensen lower bound for the product
proposal law; it does not inherit neural-network or estimator-quality claims
from the IWAE application [@burda2016importance].

## Control, planning, and temporal inference

The controlled-kernel family distinguishes a normalized action-conditioned
transition from a policy theorem. A finite belief index interprets each
reachable node as a normalized state law, so finite-horizon belief-state
reduction never asserts that the entire real probability simplex is finite.
The soft Bellman and desirability recursions expose the passive dynamics,
temperature, terminal value, and KL control cost used by linearly solvable
control [@todorov2006linearly] and path-integral control [@kappen2005path]. A
separate sophisticated expected-free-energy recursion permits future
observations to change a later action; an open-loop rollout is not accepted as
a substitute.

The temporal family proves forward filtering, backward information messages,
forward--backward smoothing, and smoothing normalization for a finite hidden
Markov model. These equations share the sum--product structure underlying the
classical finite-chain inference literature [@baum1970maximization], but the
formal statements concern exact finite recursions rather than parameter
learning or asymptotic identification. A one-step normalized variational
update, a two-level predictive factorization, and model-averaged prediction
complete the family.

## Causal blankets and predictive coding

Causal statements use an ordered finite factorization with named parent sets
and intervention kernels. The local Markov theorem is therefore proved for
that carrier only. An intervention witness changes a descendant while leaving
a named non-descendant invariant. It does not claim general graphical
d-separation or observational identifiability. This scoped construction is
kept distinct from causal blankets defined through dynamical sufficient
statistics [@rosas2020causal] and from the conditional-independence blanket
carrier used elsewhere in the catalogue. This distinction also prevents the
finite intervention carrier from inheriting the stationary-diffusion claims of
Bayesian mechanics [@dacosta2021stationary].

Predictive coding is represented by an explicit precision-weighted quadratic
energy, its prediction-error gradient, a finite-jet shift, and a truncated
generalized-filtering correction equation. Under the maintained quadratic
curvature and step-size hypotheses, the correction decreases the energy. The
formal target is thus a named finite update, not the claim that every neural
implementation performs the hierarchical inference proposed in predictive
coding accounts [@friston2009predictive].

## Path thermodynamics and geometric optimization

The path-space family constructs normalized forward and reversed finite path
laws before defining entropy production as their KL divergence. Detailed and
integral fluctuation identities are then consequences of an explicit path-law
ratio, while the Jarzynski [@jarzynski1997nonequilibrium] and Crooks
[@crooks1999entropy] rows state the work, inverse-temperature, and normalization
assumptions needed for their finite forms. A reversible-chain one-step KL
dissipation theorem is deliberately narrower than a generic housekeeping--
excess decomposition for time-dependent nonequilibrium processes.

The geometric family moves from one-dimensional Bernoulli witnesses to a
finite categorical score model. Fisher positivity is restricted to simplex
tangents; Cramér--Rao states unbiasedness and score regularity; natural-gradient
equivariance requires an invertible full-rank chart; and the Bregman
Pythagorean law names its affine projection and minimizer. These hypotheses
are the formal content that a generic appeal to information geometry
[@amari1998natural; @amari2016information] would otherwise hide.

## Collective inference, dynamics, and learning

Collective inference begins with product generative laws and proves exactly
when VFE and EFE add. The unit-weight product-of-experts pool has its own
positive normalizer; it is not mislabeled as the half-exponent construction of
an equal-weight logarithmic opinion pool.
Consensus uses a stochastic averaging kernel with an explicit strict
contraction coefficient, so convergence follows from a geometric bound rather
than from the word "consensus." A shared finite-dynamics foundation proves
Chapman--Kolmogorov composition, invariance and reversibility under powers,
Dobrushin-bound multiplication, total-variation contraction, and
master-equation mass conservation for the same normalized carrier.
The collective interpretation is motivated by explicitly modeled multiagent
systems [@heins2022spin; @friston2024federated], while the contraction theorem
uses the narrower stochastic-consensus mathematics reviewed by
[@olfatisaber2007consensus]. The formal result therefore establishes neither
an emergent group agent nor a shared generative model unless those structures
are supplied as hypotheses.

The learning family separates concentration from Bayesian algebra. It proves
a sub-Gaussian empirical-mean tail bound, a simultaneous finite-alphabet
frequency bound, and a finite-hypothesis PAC-Bayes loss-gap bound in the
lineage of McAllester's PAC-Bayesian guarantees [@mcallester1999pac]. The last
result is deterministic conditional on a Gibbs loss-gap certificate and a
log-MGF confidence budget; it does not itself derive that budget with high
probability over sampled data. Its bounded-variable specialization is scoped by the
independence and range hypotheses of Hoeffding's inequality
[@hoeffding1963probability]. Posterior-odds recursion, likelihood-gap concentration,
mixture log-loss regret, and Bayes-factor multiplication then expose their
prior-support and likelihood premises. None of these results is empirical
evidence that an FEP model fits a biological system.

## Evidence boundary

For the preceding 120-topic snapshot, each family was assessed through four
independent checks: native Lean compilation with no `sorry`, a
trusted-axiom/declaration audit, a deterministic numerical witness, and
semantic review against the cited formulation. The current dashboard schema
expresses numerical acceptance through typed checks with per-check tolerances.
Those retained receipts remain historical for their exact source; this chapter
does not promote them to evidence for the 155-topic roster. A numerical witness can reveal a sign error,
normalization failure, rank boundary, or unstable parameter region. It cannot
upgrade a scoped finite theorem into a physical law, and it is never counted as
proof evidence.

The five families that extend this program from 120 to 155 topics are treated
in [@sec:formalism_catalogue_155]; their local evidence does not
retroactively change the receipts for this first expansion.
