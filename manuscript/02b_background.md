# Background and Related Work {#sec:background_and_related_work}

## The Free Energy Principle and Its Mathematical Structure {#sec:the_free_energy_principle_and_its_mathematical_structure}

A strong reading of the Free Energy Principle (FEP) holds that a bounded dynamical system that persists over time can be interpreted, under suitable assumptions, as performing approximate Bayesian inference [@friston2006free]. This proposal, developed by Karl Friston [@friston2010free] and extended into a physics-of-self-organization program [@friston2019free], has been applied from single-cell homeostasis to human cognition through Active Inference [@friston2017active; @parr2022active]. Behind the strongest claim lie at least two mathematical obligations: a specified variational free-energy functional and a theorem connecting the selected system dynamics to a gradient flow or related descent on that functional. Neither persistence nor the name “free energy” supplies that connection automatically.

### Variational Free Energy as an Evidence Lower Bound (ELBO) {#sec:vfe_as_elbo}

The machine learning literature [@blei2017variational] introduces the same quantity under the name *evidence lower bound* (ELBO). For a latent variable $z$, observation $x$, generative model $p(x, z)$, and variational posterior $q(z)$,

$$
\text{ELBO}(q) = \mathbb{E}_{q(z)}[\log p(x, z) - \log q(z)] = \log p(x) - \KL[q(z) \,\|\, p(z \mid x)].
$$ {#eq:bg_elbo}

In [@eq:bg_elbo], after identifying $z \leftrightarrow \psi$, $x \leftrightarrow s$, and matching the joint, posterior, support, and integrability assumptions, the associated variational free energy is the negative ELBO. This correspondence is central, but it is not automatic: Mathlib4 results about KL divergence and expectations become reusable only after their typed measures, codomains, and finiteness hypotheses have been connected to the chosen FEP model.

### Formal Definition: Variational Free Energy {#sec:formal_definition_variational_free_energy}

The variational free energy $\FE$ for an agent with recognition density $q(\psi \mid m)$, generative model $p(s, \psi \mid m)$, and sensory observations $s$ is defined as:

$$
\FE[q, p] \;=\; \underbrace{\KL\!\bigl[q(\psi \mid m) \,\|\, p(\psi \mid s, m)\bigr]}_{\geq\, 0} \;-\; \underbrace{\log p(s \mid m)}_{\text{log-evidence}}
$$ {#eq:eq_1}

Because KL divergence is non-negative by Gibbs' inequality, this immediately yields the **variational bound**:

$$
\FE[q, p] \;\geq\; -\log p(s \mid m) \;=\; \text{surprise}
$$ {#eq:eq_2}

Equivalently, the free energy admits an **energy-entropy decomposition**:

$$
\FE[q, p] \;=\; \underbrace{\E_q\!\bigl[-\log p(s, \psi \mid m)\bigr]}_{\text{energy}} \;-\; \underbrace{\Ent\!\bigl[q(\psi \mid m)\bigr]}_{\text{entropy}}
$$ {#eq:eq_3}

These dual decompositions—(1) as KL plus log-evidence and (3) as energy minus entropy—are the starting point for all subsequent formalisms in this paper. In Mathlib4 parlance, [@eq:eq_3] is a statement about `∫ (fun ψ => -Real.log (p (s,ψ))) ∂(q)` together with `MeasureTheory.entropy q`; the mere act of writing this expression forces declaration of a measurable space `α` and an integrability hypothesis, neither of which typically appears in journal papers.

#### Three Equivalent Decompositions of Variational Free Energy {#sec:three_equivalent_decompositions}

Before proceeding to Active Inference, it is worth exhibiting three forms of $\FE$ that are algebraically equivalent when the displayed densities, posterior, support, and integrability conditions exist, since each form motivates a different slice of the Lean 4 catalogue. Let $o$ denote observations (written $s$ elsewhere), $s$ the hidden (latent) states (written $\psi$ elsewhere), $p(o, s)$ the generative model, and $q(s)$ the recognition density.

**(1) Surprise bound (posterior-tracking form).** Starting from Bayes' rule $p(s \mid o) = p(o, s)/p(o)$ and adding and subtracting $\log q(s)$ inside an expectation under $q$,

$$
F[q] \;=\; -\log p(o) \;+\; \KL\!\bigl[q(s)\,\|\,p(s \mid o)\bigr] \;\geq\; -\log p(o).
$$ {#eq:eq_F_surprise}

This is the "free energy bounds surprise" identity: the first term is the (negative log) model evidence—the Shannon surprise $-\log p(o)$ that the agent cannot change by rearranging beliefs—and the second is a non-negative KL gap that vanishes iff $q = p(\cdot \mid o)$.

**(2) Energy–entropy form.** Multiplying out the logarithm gives
$$
F[q] \;=\; \E_{q(s)}\!\bigl[-\log p(o, s)\bigr] \;+\; \E_{q(s)}\!\bigl[\log q(s)\bigr] \;=\; U_q \;-\; H[q],
$$ {#eq:eq_F_energyentropy}
where $U_q := \E_{q}[-\log p(o, s)]$ is the (cross-)energy under the joint generative model and $H[q] := -\E_q[\log q(s)]$ is the Shannon entropy of the recognition density. This is the form most directly connected to statistical-mechanical free energy (Helmholtz $F = U - T S$, with $T = 1$ in natural units).

**(3) ELBO form.** Because $F[q] = \E_q[\log q(s) - \log p(o, s)]$, one has
$$
F[q] \;=\; -\text{ELBO}(q), \qquad \text{ELBO}(q) \;=\; \E_{q(s)}\!\bigl[\log p(o, s) - \log q(s)\bigr].
$$ {#eq:eq_F_elbo}
This identity is what licenses the direct reuse of the machine-learning ELBO apparatus: variational Bayes, amortized inference, and the reparameterization trick all minimize $-\text{ELBO}$, which is exactly $F$.

**Why $F$ is useful to minimize.** [@eq:eq_F_surprise] exhibits $F$ as surprise plus a nonnegative KL gap. With the generative model fixed and the recognition family rich enough to contain the posterior, minimizing over $q$ attains the exact posterior. Model-parameter learning is more delicate because the posterior and KL term generally change with those parameters; evidence maximization follows directly only after optimizing the variational family exactly, or under a separately justified coordinate-ascent argument. A single gradient step therefore cannot be described unconditionally as both exact perception and evidence accumulation. The maintained finite kernel proves the posterior-attainment statement and its support-qualified uniqueness, while parameter-learning and marginal-likelihood optimization remain distinct obligations.

### Predictive Coding as Precision-Weighted Prediction Error {#sec:predictive_coding_as_precision_weighted_prediction_error}

The FEP additionally predicts a specific microscopic form for belief updates. Assuming a generative model whose likelihood is a nonlinear Gaussian $p(x \mid s) = \mathcal{N}(x;\,g(s),\,\Sigma_\varepsilon)$ with precision $\Pi_\varepsilon = \Sigma_\varepsilon^{-1}$, a point-mass or Laplace recognition density concentrated at $\mu$, and differentiable $g$, the gradient of $F$ with respect to the mean takes the canonical precision-weighted prediction-error form
$$
\dot{\mu} \;=\; -\frac{\partial F}{\partial \mu} \;=\; \bigl(\partial_\mu g(\mu)\bigr)^{\!\top} \Pi_\varepsilon\, \varepsilon \;-\; \Pi_s\,(\mu - \mu_{\text{prior}}),
\qquad \varepsilon := x - g(\mu),
$$ {#eq:eq_PC_update}
where $\varepsilon$ is the sensory prediction error, $\Pi_s$ is the prior precision on $\mu$, and $\mu_{\text{prior}}$ is the prior expectation. Here $\Pi_\varepsilon \cdot \varepsilon$ is the precision-weighted prediction error: each component of the error is rescaled by how confident the model is about that channel, so that more reliable sensory dimensions drive belief updates more aggressively. The first term on the right drives $\mu$ to reduce sensory prediction error; the second term anchors $\mu$ to its prior.

This equation ties three separate strands of the catalogue together. (i) It is a **gradient flow** on $F$ and therefore shares the contraction structure formalized for quadratic descents in **fep-032** (`fep032_quadraticEnergy_descent`, `fep032_quadraticUpdate_fixed`, `fep032_quadraticUpdate_tendsto`). (ii) Under the Laplace approximation introduced next, the energy $U_q$ reduces to a sum of quadratics in $\varepsilon$ weighted by the precisions $\Pi$; this is exactly the quadratic-minimum structure formalized in **fep-016** (`fep016_quadratic_min`, `fep016_quadratic_at_mode`, `fep016_precision_weighted`). (iii) Message passing across hierarchical layers of a predictive-coding network [@friston2018deep] propagates the same form recursively, which is the structural content of **fep-045** (`fep045_bernoulli_posterior_closed`, `fep045_posterior_mass_one`) and the monotone-composition lemmas in **fep-048** (`fep048_halfUpdate_contracts`, `fep048_halfUpdate_unique_fixed_point`). A reader who wants to know where in the Lean 4 catalogue the "prediction error" half of the FEP lives should therefore look at the intersection of these four rows.

### The Laplace Approximation and the Quadratic Form of $F$ {#sec:laplace_approximation}

The FEP in its most widely used form does not carry a fully nonparametric $q$; it typically employs the **Laplace assumption**—that $q$ is Gaussian, fully parameterized by its mean $\mu$ and covariance $\Sigma$:
$$
q(s) \;=\; \mathcal{N}\!\bigl(s;\,\mu,\,\Sigma\bigr).
$$ {#eq:eq_laplace_q}
When $F$ is the negative log posterior and $H_F(\mu) := \partial^2 F / \partial \mu \partial \mu^{\!\top}$ is positive definite at the mode, the local Laplace covariance is

$$
\Sigma^{*} \;=\; H_F(\mu^{*})^{-1}
\;=\; \bigl[-\nabla^2 \log p(\mu,o)\rvert_{\mu^{*}}\bigr]^{-1}.
$$ {#eq:eq_laplace_cov}

Thus $\Sigma^{*}$ is the inverse observed information at the MAP estimate. Substituting this local Gaussian approximation back into [@eq:eq_F_energyentropy] gives an entropy log-determinant and a second-order energy expansion. In common Gaussian observation models this yields a **precision-weighted quadratic** in the prediction errors,
$$
F_{\text{Laplace}}(\mu) \;\approx\; \tfrac{1}{2}\, \varepsilon^{\!\top} \Pi_\varepsilon\, \varepsilon \;+\; \tfrac{1}{2}\,(\mu - \mu_{\text{prior}})^{\!\top}\Pi_s\,(\mu - \mu_{\text{prior}}) \;-\; \tfrac{1}{2}\log\det\bigl(\Pi_\varepsilon\,\Pi_s\bigr) \;+\; \text{const},
$$ {#eq:eq_laplace_quadratic}
plus terms that vanish at $\mu^{*}$. Precision-weighted quadratic objectives are common in Laplace and predictive-coding implementations, but **fep-016** formalizes only their scalar algebraic substrate: square nonnegativity, the value zero at $x=\mu$, nonnegativity after multiplication by a nonnegative precision, symmetry, and expansion of $(x-\mu)^2$. It does not prove uniqueness when the precision may be zero, derive the quadratic from a likelihood or Hessian, or assemble the matrix expression in [@eq:eq_laplace_quadratic]. The catalogue keeps this scaffolding separate from claims about the full $F$ functional.

### The Active Inference Perception–Action Loop {#sec:ai_perception_action_loop}

Active Inference extends the FEP by positing that agents minimize not only present free energy but *expected* free energy under each available policy $\pi$:

$$
\EFE(\pi)
= \underbrace{\mathbb{E}_{q(o \mid \pi)}[-\log p_C(o)]}_{\text{pragmatic cost}}
- \underbrace{\mathbb{E}_{q(o,s \mid \pi)}\!\left[\log q(s \mid o,\pi)-\log q(s \mid \pi)\right]}_{\text{epistemic value}}
$$ {#eq:eq_4}

where $o$ are predicted observations, $s$ are hidden states, and $p_C$ is a normalized preferred-outcome law. The second term is the mutual information $I_q(s;o\mid\pi)$ and therefore rewards information gain by lowering $G$; the first is preference cross-entropy and rewards policies that predict preferred outcomes. This sign convention is one among several used in the literature [@millidge2021whence]. The maintained finite kernel fixes it explicitly and derives the equivalent risk--ambiguity form under full-support hypotheses. Policies are then selected by a softmax:

$$
P(\pi) \propto \exp(-\gamma \cdot \EFE(\pi)),
$$ {#eq:bg_softmax_policy}

[@eq:bg_softmax_policy] uses precision parameter $\gamma > 0$. Formalizing this loop in Lean 4 requires a `Fin n → Action` policy type, a measurable space of observations, and a summation over the (finite) policy set—all of which are available in `Algebra.BigOperators.Group.Finset` and `Data.Fin`.

### The Theoretical Landscape {#sec:the_theoretical_landscape}

The FEP ecosystem is heavily stratified mathematically, progressing from foundational variational calculus to cutting-edge stochastic physics. Each stratum is anchored by a distinguished mathematical object, and each object demands a different slice of Mathlib4:

1. **Foundational Variational Bounds** ([@eq:eq_1]--[@eq:eq_3]): Built upon Kullback--Leibler (KL) divergence and the Evidence Lower Bound (ELBO) originating in machine learning. Variational free energy $\FE$ serves as a tractable upper bound on surprise under the associated variational construction [@friston2007variational; @friston2008variational], and generalized free energy extends the objective to accommodate model uncertainty [@parr2019generalised]. A Boltzmann--Gibbs density $p^{*}(\Gamma)\propto\exp[-F(\Gamma)]$ becomes a bridge to statistical mechanics only after an energy map, units, normalization, and temperature convention are fixed; an equilibrium law and a Bayesian posterior are not identical merely because both can be written in exponential form.

2. **Active Inference** (EFE and policy objectives; [@eq:eq_4]): Introduces temporal policies in which organisms take physical action to minimize Expected Free Energy [@friston2015epistemic], decomposed into epistemic and pragmatic terms [@sajid2021active]. The relationship between VFE and EFE, and the hypotheses needed to move among published EFE decompositions, are nontrivial [@millidge2021whence]. Champion et al. [@champion2026reframing] compare four formulations and give conditions for a unifying likelihood mapping. Topic fep-021 fixes an extended-nonnegative-real convention, $G=C\mathbin{\dot-}\mathrm{IG}$, while the maintained finite carrier derives real-valued pragmatic-minus-epistemic and risk-plus-ambiguity identities and stage-updated open-loop EFE. The controlled expansion adds finite soft-control recursions and one exact two-stage observation-dependent feedback witness; the later policy-tree family defines observation-contingent trees at arbitrary finite depth, finite Bellman optima, open-loop embedding and dominance, and a treewise EFE decomposition [@friston2020sophisticated]. The collective expansion adds explicitly independent product-agent and fixed-consensus laws. None establishes equivalence to every published EFE formulation, infinite-horizon or continuous-belief planning, or emergent collective agency. Central informal object: a policy selector $\pi^{*} = \arg\min_{\pi}\,\E[G(\pi)]$.

3. **Information Geometry** ([@sec:information_geometry_results], [@sec:mathlib4_and_measure_theoretic_probability]): Models belief updates as traversal of statistical manifolds governed by the Fisher Information Metric and natural gradients [@amari1983foundation; @amari2016information]. The space of probability distributions becomes a Riemannian manifold whose geometry encodes local statistical distinguishability. The Fisher Information Metric is defined as

$$
g_{ij}(\theta) = \mathbb{E}_{p(x \mid \theta)}\!\left[\frac{\partial \log p(x \mid \theta)}{\partial \theta^i} \cdot \frac{\partial \log p(x \mid \theta)}{\partial \theta^j}\right],
$$ {#eq:bg_fisher_metric}

Given [@eq:bg_fisher_metric], natural gradient descent replaces $\nabla F$ by $g^{-1}\nabla F$. Under the regularity, nondegeneracy, and transformation assumptions that make the statistical manifold and inverse metric well-defined, this vector field is coordinate-covariant and represents metric steepest descent. The catalogue constructs the complete one-parameter Bernoulli instance and a finite categorical score carrier with explicit full-rank and null directions. It proves simplex-tangent Fisher positivity, pullback, scalar Cramér--Rao, invertible-chart natural-gradient equivariance, mirror and affine Bregman identities, and replicator equivalence. The later full-support scalar exponential family adds log-partition gradient/Hessian, centered score, Fisher--variance equality, KL--Bregman duality, and interval-local mean-coordinate injection. It does not yet define arbitrary smooth atlases, affine connections, curvature, or general geodesic existence.

4. **Bayesian Mechanics** ([@sec:bayesian_mechanics_results]): Develops inference-related dynamics using Fokker–Planck equations, non-equilibrium steady states (NESS), and decompositions with skew components [@parr2018markov; @friston2021stochastic]. Sakthivadivel [@sakthivadivel2023bayesian] frames this as "a physics of and by beliefs," while Friston et al. [@friston2024path] develop a path-integral treatment of particular kinds. The catalogue formalizes measure and finite Bayesian inversion, filtering and smoothing, hierarchy and model averaging, finite blanket and intervention laws, and finite stationary currents. It does not derive the general stochastic-analytic Fokker--Planck construction or causal identification from observational data.

5. **Thermodynamic Foundations**: Relates FEP language to thermodynamic potentials, finite path-law fluctuation and Jarzynski identities [@jarzynski1997nonequilibrium], Landauer's principle [@landauer1961irreversibility], and nonequilibrium thermodynamics [@prigogine1977nature; @pavliotis2014stochastic]. The standard Helmholtz relation $\mathcal F=-k_{\mathrm B}T\log Z$ and the variational identity $F_{\mathrm{var}}=\mathrm{KL}(q\Vert p(\cdot\mid o))-\log p(o)$ live in different modeling layers. Identifying them requires an explicit Boltzmann generative model, units, normalization, and temperature scaling; the present catalogue proves scoped finite identities but does not prove that physical identification.

### The Formalization Gap {#sec:the_formalization_gap}

This project addresses a narrower, directly inspectable **verification gap**: familiar FEP labels often sit several definitions and hypotheses away from the Lean propositions that can currently be stated against the pinned library. It does not claim priority over every earlier formal-methods treatment. The table below reports the present catalogue's scope, rather than attempting an unbounded census of prior work or numerical software.

| Topic-facing concept | Current formal object | Semantic disposition |
|----------------------|-----------------------|----------------------|
| Variational free-energy bound (fep-002) | Surprisal plus native `ℝ≥0∞` KL; bound and posterior self-case | `formalized` at this narrowed abstraction |
| KL laws (fep-014) | Native KL self/zero laws and composition-product chain rule | `formalized` |
| EFE convention (fep-021) | Explicit `ENNReal` pragmatic-cost-minus-epistemic-value convention with monotonicity and balance | `formalized` at that convention |
| Four-block partition (fep-005) | Pairwise-disjoint finite fibers with unique state membership; no blanket independence claim | `formalized` at partition scope |
| Nonequilibrium current (fep-025) | Transition-induced antisymmetric current, stationarity conservation, and a nonzero three-cycle witness | `formalized` in finite state space |
| Fisher metric (fep-004/fep-038) | Positive-definite finite weighted metric and an exact Bernoulli statistical-family specialization | `formalized` at finite/Bernoulli scope |
| Finite softmax (fep-028) | Support-aware full finite probability vector with exact zero off-support and global normalization | `formalized` |
| Conjugate update (fep-045) | Exact normalized Bernoulli posterior closure and parameter update under positive binary evidence | `formalized` at binary scope |

_Current semantic status of representative catalogue rows. The generated coverage report is authoritative for all {{total_topics}} rows._

## Interactive Theorem Proving: Lean 4 and Mathlib {#sec:interactive_theorem_proving_lean_4_and_mathlib}

Lean 4 is a functional programming language and interactive theorem prover (ITP) based on dependent type theory [@moura2021lean]. Machine-checked projects such as CompCert [@leroy2009compcert], the perfectoid-spaces development [@buzzard2020], the Liquid Tensor Experiment [@scholze2022liquid], and the polynomial Freiman--Ruzsa proof [@pfr2023lean] illustrate different scales and styles of formal verification. This work targets **Mathlib4** [@mathlib2020] through the pinned **`{{lean_toolchain}}`** toolchain and Mathlib **`{{mathlib_tag}}`** revision recorded in `lean/lean-toolchain` and `lean/lakefile.lean`; it does not rely on mutable upstream declaration counts.

### Type Theory Foundations and Tactic Mode {#sec:type_theory_foundations}

Lean 4 rests on the Calculus of Inductive Constructions (CIC), a dependent type theory in which propositions and types are the same kind of object. A proof of proposition `P` is a term of type `P`; consequently, the kernel that type-checks terms is the same kernel that verifies proofs. Writing a proof in Lean is therefore identical to writing a program whose type is the statement of the theorem. Users rarely write proof terms directly; instead, they invoke *tactics*—metaprograms that incrementally build the term. A proof in tactic mode takes the following shape:

```lean
theorem kl_nonneg {α : Type*} [MeasurableSpace α] (μ ν : Measure α)
    : 0 ≤ InformationTheory.klDiv μ ν := by
  exact zero_le _
```

Here `by` enters tactic mode and `zero_le` discharges non-negativity because Mathlib's native divergence takes values in the nonnegative extended reals. The type, rather than an informal convention, rules out a negative result. This style is introduced in depth in [@sec:lean_4_a_primer_for_active_inference_researchers].

### Why Lean 4 for Physical Theories? {#sec:why_lean_4_for_physical_theories}

Lean 4 offers four properties critical for formalizing the FEP:

1. **Dependent types with universe polymorphism**: Types can depend on values, enabling precise encoding of parameterized families of probability measures, finite policy spaces, and transition kernels across the universes used by Mathlib.

2. **Mathlib4's measure-theoretic and information-theoretic stack**: The pinned library provides Bochner integration, Radon--Nikodym derivatives (`MeasureTheory.Measure.rnDeriv`), sigma-algebra constructions, finite and probability measures, Markov kernels, and `InformationTheory.klDiv : Measure α → Measure α → ℝ≥0∞`. It also supplies self-divergence, a zero characterization for finite measures, Gibbs' inequality, and a composition-product chain rule. The extended codomain preserves infinite divergence; any real-valued FEP identity still needs explicit finiteness before applying `.toReal`.

3. **Advanced proof automation**: The pinned Lean 4 `{{lean_toolchain}}` toolchain and Mathlib4 `{{mathlib_tag}}` supply automation including the `grind` tactic (SMT-style), `positivity`, and related solvers. These capabilities expand the range of FEP theorems that can be verified without manual proof construction; newer releases add further improvements.

4. **Available LLM–ITP tooling**: LeanDojo [@yang2024leandojo], Lean Copilot [@song2025copilot], and LEGO-Prover [@xin2024lego] provide relevant examples of Lean-facing proof-search or assistance. Their existence motivates the optional review stage; it supplies no correctness evidence for this catalogue.

Modern physical theories, however, often outpace formalized repositories. The catalogue and maintained foundations now cover finite Markov dynamics, a one-parameter smooth statistical instance, arbitrary finite-dimensional score geometry, native posterior kernels, generic conditional-independence laws, and a concrete finite blanket factorization with typed dynamics. Full continuous Bayesian mechanics still requires stochastic processes, Fokker--Planck evolution, smooth manifold structure, and system-specific blanket-existence arguments. Rows are therefore narrowed to the strongest exact theorem supported by their objects instead of adding local axioms solely to obtain a green compiler result.

### Lean 4 Release Cadence and Tactic Evolution {#sec:lean4_release_cadence}

Lean 4 has maintained a rapid release cadence. The repository pins **`{{lean_toolchain}}`** in `lean/lean-toolchain`; later releases add further automation and ergonomics beyond what this paper's lemmas rely on.

This evolution shapes maintenance, but tactic availability is not the semantic maturity criterion. A row can be warning-free and `sorry`-free while proving only a weak proxy. Upgrades therefore require both a native compile and a renewed semantic review of the theorem's relation to its advertised FEP claim.

### Prior Formalization Work in Adjacent Domains {#sec:prior_formalization_work}

A range of prior efforts have formalized parts of cognitive science, statistical mechanics, or information theory in interactive theorem provers. None targets the FEP directly, but each offers methodological lessons:

| Project | System | Domain | Scope | Relevance to FEP |
|---------|--------|--------|-------|------------------|
| Hammers for Helmholtz [@avigad2017] | Lean 3 | Real analysis / measure theory | Foundational | Provides the measure-theoretic backbone reused in Mathlib4 |
| Information-theoretic inequalities [@mehtaMetaIT2021] | Isabelle/HOL | Classical information theory | Shannon entropy, mutual information | Complementary to KL-based FEP work |
| Formalized statistical mechanics [@paulson2022thermo] | Isabelle/HOL | Classical thermodynamics | Partition functions, entropy | Thermodynamic catalogue rows build on analogous ideas |
| LeanDojo [@yang2024leandojo] | Lean 4 | Proof search benchmarks | Retrieval-augmented LLM | Demonstrates tractability of LLM ↔ Lean interfaces |
| Mathlib information theory [@mathlib2020] | Lean 4 | Measure-theoretic information theory | Native KL divergence and chain rules | Direct library substrate for fep-002 and fep-014 |
| Categorical ontology / classical simulation [@namjoshi2026fundamentals] | Lean 4 | Foundations | Definitions of classical / quantum systems | Adjacent formalization of physical theories |

The landscape shows that adjacent domains have proven tractable. We have not conducted the systematic, date-bounded search needed to establish whether this is the first catalogue-scale FEP formalization, so we make no priority claim. The inspectable contribution is the particular versioned catalogue, semantic audit, and receipt boundary reported here.

## The LLM–ITP Bridge {#sec:the_llm_itp_bridge}

Recent systems illustrate several ways to connect language models with interactive theorem provers:

| System | Year | Approach | Benchmark | Key innovation |
|--------|------|----------|-----------|----------------|
| LeanDojo [@yang2024leandojo] | 2024 | Retrieval-augmented | LeanDojo Benchmark | Grounded tactic suggestion via premise retrieval |
| Baldur [@first2023draft] | 2023 | Whole-proof generation | miniF2F | End-to-end proof generation + repair |
| LEGO-Prover [@xin2024lego] | 2024 | Modular growing libraries | miniF2F | Reusable lemma construction |
| DeepSeek-Prover [@deepseek2024prover] | 2024 | RL from proof feedback | miniF2F | RLPAF — reinforcement learning from proof assistant feedback |
| AlphaGeometry [@trinh2024alphageometry] | 2024 | Neuro-symbolic | IMO Geometry | Synthetic data + symbolic deduction |
| AlphaProof [@alphaproof2024] | 2024 | Gemini + AlphaZero | IMO 2024 | Silver-medal level problem solving |
| Lean Copilot [@song2025copilot] | 2025 | Editor integration | N/A | Real-time tactic suggestion in VSCode |
| DeepSeek-Prover-V2 [@deepseek2025proverv2] | 2025 | RL + subgoal decomposition | miniF2F, ProofNet | Reinforcement learning for structured proof planning |

These systems largely begin with already formalized targets and concentrate on proof search. Translating a physical theory adds an earlier modeling burden: choosing definitions, types, scope, and assumptions for concepts such as Markov blankets, solenoidal flows, and Expected Free Energy decompositions. The maintained kernel in this work emphasizes that translation and review problem. The optional Hermes path can explain or refine candidate Lean, but it supplies no correctness or authorship claim without subsequent compilation and a claim-ready full receipt.

### The Axiomatization vs. Problem-Solving Distinction {#sec:the_axiomatization_vs_problem_solving_distinction}

The distinction between proof search and theory axiomatization is worth making precise:

- **Proof search** (LeanDojo, DeepSeek-Prover): given a well-typed theorem statement, find a proof term. The statement already exists in a formal language; the challenge is navigating the proof space.
- **Theory axiomatization** (this work): given an informal mathematical theory (published in journals, written in natural language with embedded LaTeX), produce well-typed theorem statements, definitions, and structural lemmas. The challenge is _translation from informal to formal_, not proof search.

This distinction explains why the pipeline reports statement design, proof completion, and semantic adequacy separately. Every shipped body is `sorry`-free at its reviewed scope, but proving a narrowed proposition does not validate the modeling choice that produced it. The contribution is therefore both executable mathematics and an auditable translation process, rather than a benchmark whose only outcome is proof-completion rate.

## The FEP Debate and the Case for Formalization {#sec:the_fep_debate_and_the_case_for_formalization}

The mathematical status of the FEP has been actively debated in the literature, along three principal lines of critique:

1. **Blanket conditions.** The partition of states into internal, external, sensory, and active components is not always well-defined for arbitrary dynamical systems ([@biehl2021critique]). Specifically, Biehl et al. demonstrate that *"various definitions of the 'Markov blanket' proposed in different works are not equivalent"* and that crucial vector-field rewritings are not generally correct absent previously unstated assumptions. The canonical Markov-blanket claim is that the state space admits a factorization $X = \Psi \times B \times H$ (external, blanket, internal) such that the blanket $b = (s, a)$ renders external and internal states conditionally independent,
$$
p(\psi, \eta \mid b) \;=\; p(\psi \mid b)\,p(\eta \mid b)\qquad\text{(conditional independence given the blanket)}.
$$ {#eq:eq_markov_blanket}
[@eq:eq_markov_blanket] is a *statistical* condition about a specific family of joint densities, and whether a given dynamical system satisfies it depends on the system's drift, diffusion, and steady-state structure—properties that are not determined by the choice of state-space partition alone. The blanket partition sits at the intersection of two very different objects: an algebraic/set-theoretic decomposition of the state space, and a probabilistic conditional-independence statement about its dynamics. Conflating the two is precisely the locus of Biehl et al.'s critique. Accordingly, **fep-005** formalizes only the algebraic side: a four-part disjoint cover with unique membership. The maintained `FEP.MarkovBlanket` foundation adds a separate normalized finite joint of the form $P(b)P(i\mid b)P(e\mid b)$, proves positive-mass conditional factorization and zero internal--external mutual information, and constructs a nontrivial transition whose allowed dependencies are encoded in its types. These results settle a concrete finite instance; they neither derive the blanket from fep-005's arbitrary labels nor prove that generic stochastic dynamics admit or preserve such a structure.

2. **Particular partitions.** The broader applicability of the "particular physics" framework has been questioned, with arguments that certain assumptions about steady-state densities are unduly restrictive ([@aguilera2022particular]). Concretely, the "particular-physics" construction assumes that a stochastic system with dynamics $\mathrm{d}x = f(x)\mathrm{d}t + \sigma\,\mathrm{d}W_t$ admits a non-equilibrium steady-state (NESS) density $p^{*}(x)$ such that the probability current decomposes as
$$
J(x) \;=\; -\bigl(D + Q(x)\bigr)\,\nabla F(x),\qquad F(x) := -\log p^{*}(x),
$$ {#eq:eq_helmholtz_current}
with $D$ symmetric positive-semidefinite (the dissipative component), $Q(x)$ **antisymmetric**, i.e. $Q(x)^{\!\top} = -Q(x)$ (the solenoidal component), and the steady-state divergence condition $\nabla \cdot J(x) = 0$. Establishing these conditions simultaneously requires both algebraic hypotheses and analytic/stochastic results about the density and current. **fep-025** now proves a finite continuity-equation instance instead: forward-minus-reverse edge current is antisymmetric and globally conserved, a normalized transition with a stationary mass vector has zero node divergence, and a directed three-cycle has nonzero current despite stationarity. This separates finite stationarity from detailed balance, but it does not construct $Q(x)$, a stationary density on a continuous space, or the SDE/PDE decomposition above.

3. **Math and territorialism** (a deliberate nod to the classic "map and territory" distinction and to the "territorialism" of notational regionalisms across fields). It has been argued that FEP derivations sometimes conflate distinct mathematical objects—using the same notation for different quantities in different contexts ([@andrews2021math]). Lean's type system makes many such conflations visible: for example, a `Measure ℝ` cannot be passed where an $\mathbb{R}$-valued function is required without an explicit bridge. It cannot prevent a modeler from choosing an inadequate definition or assigning the same underlying type to semantically different quantities.

These debates motivate the present work: formal verification in Lean 4 does not adjudicate the underlying semantic disagreements. It makes statement-level hypotheses and proof dependencies inspectable, while the separate semantic audit records whether those formal objects reach the motivating claim.

## Recent Developments (2024–2026) {#sec:recent_developments_20242026}

Recent FEP work includes path-integral and geometric treatments of Bayesian mechanics [@sakthivadivel2023bayesian; @friston2024path] and a comparison and unification of Expected Free Energy formulations [@champion2026reframing]. Translating such claims into Lean requires more than proof search: the modeler must choose probability spaces, codomains, finiteness conditions, stochastic-process interfaces, and a semantic acceptance target. This catalogue makes those choices reviewable one row at a time. Compiler acceptance answers derivability of the stated proposition; the disposition and assumption review answer the separate question of how far that proposition reaches toward its topic label.
