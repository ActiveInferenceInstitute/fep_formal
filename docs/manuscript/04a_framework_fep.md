# Formalisms, Model Specifications, and Results {#sec:formalisms_and_results}

The core artifact is a generated catalogue of {{total_topics}} topic-scoped Lean bodies plus semantic review metadata, accompanied by reusable maintained foundations. Canonical topic bodies live in the family modules under `fep_lean.catalogue.bodies`; generated YAML and the unified appendix are projections. Native evidence is `{{verify.evidence_kind}}` with rate `{{compile_rate.total}}`. This section discusses mathematical scope; it does not infer full-pipeline evidence from catalogue generation.

## Foundational Dynamics: Free Energy Principle ({{areas.FEP.count}} topics) {#sec:foundational_dynamics_free_energy_principle}

A common variational identity writes free energy as surprisal plus a KL remainder:

$$
F[q] = -\log p(o) + \KL\!\left[q\,\middle\|\,p(\cdot\mid o)\right].
$$ {#eq:eq_VFE_functional}

The catalogue now represents the nonnegative-extended-real core of this identity directly. `fep002_variationalFreeEnergy` defines surprisal plus `InformationTheory.klDiv`; `fep002_vfe_ge_surprisal` proves the upper bound; and `fep002_vfe_exact_at_posterior` uses Mathlib's self-divergence theorem under `SigmaFinite`. This is a meaningful strengthening over a theorem that merely assumed an unnamed nonnegative scalar remainder.

The topic result is deliberately narrower than the displayed FEP equation: it does not construct the observation marginal, conditional posterior, or real logarithmic evidence term from a joint generative model. The maintained finite kernel supplies exactly that discrete construction on normalized finite laws, proves Bayes reconstruction, and shows that posterior-form VFE bounds outcome surprisal, with exact-posterior attainment and support-qualified uniqueness. A bridge from this finite real carrier to the topic row's general measure-valued `ENNReal` statement remains intentionally explicit rather than being inferred from matching notation.

### Core Mathematical Formalisms and Theoretical Definitions {#sec:core_formalisms}

The FEP-area rows provide heterogeneous substrates: measure operations and measurability, strict concavity of the logarithm, finite sums, quadratic bounds, minima, conjugate updates, contraction fixed-point theory, and finite-law risk transfer for the outcome-indexed Laplace estimator. They should not be read as one already-composed proof. The generated coverage report gives the exact primary theorem, disposition, assumptions, and imports for each row; the appendix gives the statements and proofs.

The familiar Jensen route to an ELBO remains useful context:

$$
\log p(o)
= \log \mathbb{E}_{q(s)}\!\left[\frac{p(o,s)}{q(s)}\right]
\geq \mathbb{E}_{q(s)}\!\left[\log \frac{p(o,s)}{q(s)}\right]
= -F[q].
$$ {#eq:eq_jensen_elbo}

No catalogue theorem currently proves this whole chain with its integrability and almost-everywhere conditions. fep-035 now imports Mathlib's strict-concavity result for `Real.log` and proves the exact two-point strict Jensen inequality for distinct positive inputs and positive weights summing to one. That theorem is a genuine finite convexity fact, but it is not the expectation-level Jensen step above. fep-002 supplies a native KL remainder identity at a narrower abstraction boundary.

Likewise, the elementary quadratic update used as a local descent model is:

$$
x_1^2=(1-\eta)^2x_0^2\leq x_0^2 \qquad\text{when } |1-\eta|\leq 1.
$$ {#eq:eq_gradient_contraction}

fep-032 now proves more than the one-step inequality: for the centered scalar quadratic it derives the exact $n$-step displacement $(1-\eta)^n(x_0-x^\star)$, proves energy descent for $0\leq\eta\leq2$, and proves convergence to the center for $0<\eta<2$. `FEPComposed.fep032_update_is_fep043_gradientStep` identifies that update with a gradient step on fep-043's positive-curvature quadratic, whose unique minimizer, critical-point equivalence, and Hessian are independently checked. fep-048 supplies the complementary general Banach-style contract and a concrete halving witness. None of these results establishes convergence for an arbitrary variational objective.

Cross-topic composition is now an explicit proof surface. `FEPComposed.fep002_vfe_compProd_chain_rule` expands fep-002 variational free energy through fep-014's native KL chain rule; `FEPComposed.fep024_regularizer_is_fep014_kl` pins the regularizer convention to the same divergence; and the quadratic theorem above connects landscape, gradient, iteration, and convergence without copied definitions. These are among **{{formalism.metrics.formal_relation_witnesses}}** declaration-backed seams. The finite foundation additionally supplies a generative-model-to-evidence theorem on one discrete real-valued carrier; the stronger open target is a measure-valued bridge for the full displayed FEP equation, not the absence of any constructed model.

The `fep-121`--`fep-127` family closes a different finite boundary. On the
same add-one estimator introduced by fep-036, it proves the exact error and
bias decompositions, absolute- and squared-error transfer, a normalized
finite-law risk bound, the Bernoulli Brier excess-risk identity, a Laplace
Brier-risk bound, and bad-event containment. A nonzero-bias boundary and a
nondegenerate sampling law keep those implications from being vacuous. These
are finite sampling-risk theorems, not posterior contraction, minimax
optimality, empirical calibration, or marginal-likelihood optimization; the
exact declarations and hypotheses are tabulated in
[@sec:catalogue_155_risk_calibration].

The FEP rows therefore establish exact local facts, not the Free Energy Principle as a theorem of self-organization. Their scientific value lies in exposing which bridges—generative model to posterior, posterior to KL objective, objective to dynamics, dynamics to steady state, and finite risk to asymptotic or empirical guarantees—still require formal statements.
