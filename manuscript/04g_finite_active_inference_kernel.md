## A Checked Finite FEP and Active-Inference Kernel {#sec:finite_active_inference_kernel}

The catalogue's {{total_topics}} topic bodies are deliberately heterogeneous. To test whether their central ideas can inhabit coherent formal substrates, the package maintains an explicit resource manifest containing reusable foundations, leaf cross-topic compositions, and an import-only aggregate. The foundations contribute {{formalism.metrics.foundation_theorems}} checked declarations, while all maintained formal resources contribute {{formalism.metrics.formal_resource_theorems}} declarations. These declarations are counted separately from the {{formalism.metrics.topic_theorems}} topic theorems, so the reported total of {{formalism.metrics.theorems}} cannot hide duplication between generated examples and the reusable kernel.

The kernel follows the finite-state presentation common in discrete active inference [@dacosta2023bayesian], but it does not treat finiteness as evidence for an unrestricted FEP. Every probability carrier records nonnegativity and normalization; every logarithmic identity states its support hypotheses; every posterior states positive evidence; every asymptotic result states its integrability and independence assumptions. This is also a response to critiques that blanket, stationarity, and inference claims can become stronger than their premises [@biehl2021critique].

![One deterministic numerical witness for each expanded formal family. The panels exercise reconstruction, normalization, update, rank, contraction, and concentration boundaries, but they are explanatory projections rather than proof receipts.](../output/figures/formal-kernel-dashboard.png){#fig:formal_kernel_dashboard height=80%}

[Open the offline interactive validation dashboard.]({{publication.repository_url}}/blob/{{source.published_ref}}/docs/formal-kernel-dashboard.html) Its filters expose all fifteen family diagnostics, while accessible tables retain the exact parameters, theorem mirrors, typed per-check relations and tolerances, and boundary observations without requiring a network connection.

### Probability and information carriers {#sec:finite_kernel_probability_information}

`FEP.FiniteLaw α` stores a real mass function with proofs of

$$
p(x)\ge 0,\qquad \sum_{x\in\alpha}p(x)=1.
$$ {#eq:kernel_carrier_axioms}

Point masses, uniform laws, independent products, marginals, and deterministic pushforwards preserve this carrier. `FEP.FiniteKernel α β` similarly stores normalized rows. Its identity kernel and sequential composition satisfy left identity, right identity, and associativity, while predictive propagation satisfies the matching identity and composition laws. Consequently, multi-step prediction is not a fresh normalization argument at each horizon; it is inherited from a checked kernel algebra.

The information layer uses Mathlib's zero-safe `Real.negMulLog` and `InformationTheory.klFun`. It proves entropy nonnegativity, KL nonnegativity, support-free separation for normalized finite laws, conditional KL separation under positive input-law support but without reference-row support, cross-entropy identities, exact prior--kernel KL chain rules, marginal KL domination, independent-product KL additivity, entropy chain and product laws, and support-free mutual-information separation. The logarithmic identities and chain laws retain the positive-reference assumptions used by their derivations. This matters because the real-valued definition is totalized: for disjoint Boolean point masses its cross-entropy is zero and its KL value is one, not positive infinity. In particular, for finite laws $p$ and $q$,

$$
I(p\otimes q)=0
$$ {#eq:kernel_mi_separation}

The separation in [@eq:kernel_mi_separation] holds without adding artificial positivity assumptions at zero-mass atoms.

### Variational inference and the evidence bound {#sec:finite_kernel_vfe}

A single `GenerativeModel Policy State Outcome` owns the initial state law, policy-conditioned transition, likelihood, preferred-outcome law, and policy prior. From that carrier the library derives predicted states, predicted state--outcome joints, predicted outcomes, and exact posterior states. Bayes reconstruction is an equation, not a prose contract:

$$
Q(s\mid o,\pi)P(o\mid\pi)
=Q(s\mid\pi)P(o\mid s).
$$ {#eq:kernel_bayes_reconstruction}

For any recognition law $R$ and positive-evidence outcome, posterior-form variational free energy is

$$
F[R,o,\pi]
=D_{\mathrm{KL}}\!\left(R\,\middle\|\,P(s\mid o,\pi)\right)
-\log P(o\mid\pi).
$$ {#eq:kernel_vfe_posterior}

The checked theorems prove, from the definition in [@eq:kernel_vfe_posterior], $-\log P(o\mid\pi)\le F[R,o,\pi]$, equivalently $-F[R,o,\pi]\le\log P(o\mid\pi)$. The exact posterior attains the bound, and equality is equivalent to $R=P(s\mid o,\pi)$ even when the posterior has zero-mass states. Thus the package contains a genuine variational minimization result rather than only a definition named “free energy.”

### Expected free energy, policy selection, and planning {#sec:finite_kernel_efe}

The same model defines preference risk, likelihood ambiguity, epistemic value as mutual information, pragmatic cost, and real-valued expected free energy. Under the explicit `FullSupport` contract it proves both central decompositions

$$
G(\pi)=\text{pragmaticCost}(\pi)-\text{epistemicValue}(\pi)
=\text{risk}(\pi)+\text{ambiguity}(\pi),
$$ {#eq:kernel_efe_decomposition}

and hence nonnegativity in this finite convention. The literature contains several EFE formulations whose equivalence depends on modeling assumptions [@millidge2021whence; @champion2026reframing]; the theorem therefore fixes its sign and support conventions in the type-checked statement rather than relying on terminology.

A prior-weighted Boltzmann law

$$
Q(\pi)\propto P(\pi)\exp[-\gamma G(\pi)]
$$ {#eq:kernel_boltzmann_policy}

The law in [@eq:kernel_boltzmann_policy] has a strictly positive partition and a normalized posterior under full model support; a zero-mass preferred outcome is explicitly rejected before this surface is available. Equal-prior policies are ordered antitonically by EFE for nonnegative precision, a finite MAP policy exists, and an EFE minimizer exists. An action interface requires each emitted action to recover its policy's transition. The resulting infer--select--act joint is normalized, factors into posterior policy mass and action-state kernel mass, and has exactly the advertised policy and action marginals. A symmetric two-policy, two-state, two-observation model has uniform predictions, zero preference risk, and EFE equal to uniform Boolean entropy. Because both policies have equal EFE, changing the prior changes the posterior mass of `true` from $3/4$ to $1/4$ at every precision, pinning the prior term numerically.

For temporal depth, a list of policies composes the transition kernels chronologically. Empty plans preserve the initial law; concatenated plans obey prefix--suffix prediction; and a positive-mass terminal observation yields an exact planned posterior reconstruction. A second recursion updates the predicted state law after every stage and accumulates stage-dependent EFE. Its value decomposes exactly at every plan concatenation and is nonnegative under a recursive stagewise support contract. This carrier is finite-horizon and open-loop. The controlled-Markov foundation first adds an exact two-stage observation-dependent feedback witness. The later `FEP.PolicyTrees` foundation defines arbitrary finite-depth observation-contingent trees on finite carriers, proves recursive Bellman optimality and optimizer existence, embeds open-loop plans, proves closed-loop weak dominance, and lifts the EFE decomposition treewise. It does not supply an infinite-horizon partially observed stochastic game or learn a posterior over trees.

### Blanket factorization and dynamics {#sec:finite_kernel_blankets}

The static blanket carrier constructs

$$
P(b,i,e)=P(b)P(i\mid b)P(e\mid b).
$$ {#eq:kernel_blanket_factorization}

At positive blanket mass, division by $P(b)$ yields the exact conditional product. Independently, the blanket-indexed conditional law has zero internal--external mutual information. This gives a concrete finite conditional-independence witness and strengthens the catalogue-level bridge between blanket partitions and conditional independence. The later `FEP.NativeBlanket` foundation embeds this carrier into native measures and kernels, transfers singleton masses, expectations, and prediction, and proves Mathlib's `CondIndepFun` for the embedded static joint plus measurable endpoint coarsening and rowwise factorized transitions. It still does not prove that arbitrary dynamics admit or preserve a blanket under arbitrary mixtures.

The dynamic carrier makes the permitted dependency graph part of the transition type: internal and active updates see the current internal--sensory pair, while sensory and external updates see the current external--active pair. Their product is a normalized four-component transition with an exact factorization theorem. Every transition row is equal to a static joint derived from the current state; under positive next-blanket mass it therefore inherits conditional factorization and zero conditional mutual information. A Boolean witness changes state with probability one, ruling out a vacuous identity-only realization. These are row-wise results and do not assert stationarity or preservation after an arbitrary prior mixture.

### Geometry and asymptotics {#sec:finite_kernel_geometry_asymptotics}

A $d$-dimensional centered score field induces a symmetric Fisher matrix and a Gram metric. Positive semidefiniteness is unconditional; positive definiteness requires full support and score identifiability; pullback positivity additionally requires an injective Jacobian; and composite Jacobians obey a functorial pullback law. Matrix lowering is proved equal to the original expected-score metric. When the Fisher matrix is invertible, the library constructs the inverse-Fisher natural gradient and proves its matrix duality, metric duality, Fisher-energy identity, and uniqueness. An interior Bernoulli model realizes the one-dimensional case with Fisher entry $1/[p(1-p)]$ and natural-gradient scaling $p(1-p)$; at $p=1/2$ its scores are $\pm2$ and its Fisher entry is four. A duplicated-score two-parameter model supplies the opposite witness: an all-four Fisher matrix, a nonzero null tangent, zero Fisher norm, and failed identifiability. The nondegeneracy premises are therefore mathematically active.

For data, the topic-independent foundation instantiates Mathlib's almost-sure strong law for Boolean indicators and finite-atom indicators. Integrability, pairwise independence, and identical distribution remain theorem premises. It proves raw empirical-rate convergence, simultaneous convergence of every atom outside one null set, convergence of the whole finite empirical law in $L^1$, and convergence of empirical expectations and their absolute errors for every real observable on the finite carrier. The Laplace-smoothing transfer is separately proved in a composition leaf because it consumes fep-036. These are asymptotic consistency results. The learning family adds scoped finite-sample concentration and regret statements; the later empirical-risk family connects the exact Laplace estimator to finite-law squared/Brier-risk transfer and concentration-event containment. Neither surface proves posterior contraction, minimax optimality, empirical calibration, or empirical adequacy for an observed data set.

### What the kernel proves—and what it does not {#sec:finite_kernel_boundary}

The kernel makes several high-value seams executable in one carrier: Bayes reconstruction, the variational evidence bound, both EFE decompositions, policy normalization and action pushforward, horizon composition, blanket conditional information, Fisher raising/lowering, and strong-law consistency. The numerical dashboard above complements this deductive surface with one diagnostic for each later expansion family; it is not a sample-based proof of every seam in this chapter. The formalism atlas shows the generated module-dependency graph separately from authored scientific relations: purple import arrows describe code reuse, while teal edges require named theorem witnesses.

The remaining boundary is deliberate. State spaces and policy-tree carriers are finite; logarithmic EFE identities and treewise decomposition require stated full support even though finite-KL and VFE separation do not; the real-to-`ENNReal` bridge truncates negative values through `ENNReal.ofReal`; native blanket transfer is rowwise rather than a generic existence theorem; Fisher inversion and mean-coordinate injection retain nondegeneracy premises; finite Laplace risk is not posterior contraction; and the exact continuous-time family is Boolean rather than an SDE/PDE model. These constraints are acceptance conditions for future extensions, not footnotes that disappear from the formal claims.
