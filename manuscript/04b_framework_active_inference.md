## Intermediate Dynamics: Active Inference ({{areas.ActiveInference.count}} topics) {#sec:intermediate_dynamics_active_inference}

Transitioning into temporally extended behavior, Active Inference [@friston2017active; @friston2016active] introduces action policies and predicted consequences, including motor-control accounts in which prediction errors drive action [@adams2013predictions]. A common discrete formulation has an inner inference problem for variational free energy and an outer policy problem for expected free energy [@dacosta2023bayesian]. The {{areas.ActiveInference.count}} catalogue rows map finite-sum, update, policy-selection, controlled-kernel, finite-belief, policy-tree, collective, and consensus substrates for that formulation. The maintained kernel composes the central objects in one `GenerativeModel`: policy-conditioned prediction, evidence and posterior, posterior-form VFE, one-stage and cumulative EFE, prior-weighted policy selection, action pushforward, and open-loop rollout. Separate foundations add normalized controlled kernels, positive-evidence belief updates, reachable finite-belief reduction, soft Bellman and desirability recursions, a prior-weighted control posterior, arbitrary finite-depth observation-contingent policy trees with optimality and open-loop dominance, a strict feedback witness, and product-agent and consensus laws. The H1 terminal composition now connects a deliberately selected finite synthetic model from posterior learning through one posterior-dependent decision to one emitted action and its exact transition. That certificate is not a refinement proof for executable code, an infinite-horizon or continuous-belief theorem, a posterior over policy trees, or a theorem for arbitrary agents or multiagent networks.

### Generative Model, Variational Inference, and Policy Evaluation {#sec:ai_generative_model}

Active Inference begins with the same generative model that underwrites the static FEP, but partitioned into observation and latent components with an explicit decomposition into likelihood and prior:

$$
p(o, s) \;=\; p(o \mid s)\,p(s),
$$ {#eq:ai_generative_model}

and extended to sequences $(o_{1:T}, s_{1:T})$ under a (possibly time-varying) transition kernel $p(s_{t+1} \mid s_t, a_t)$ with action $a_t$. Writing out the full sequential generative model,

$$
p(o_{1:T}, s_{1:T} \mid a_{0:T-1}) \;=\; p(s_1)\,\prod_{t=1}^{T} p(o_t \mid s_t)\,\prod_{t=1}^{T-1} p(s_{t+1} \mid s_t, a_t),
$$ {#eq:ai_sequential_gm}

makes the *factor graph* structure of the problem explicit. Inference is often performed by local message passing. fep-007 proves positivity and exact normalization of one finite local sum-product message; fep-047 packages a full finite forward pass as `Matrix.mulVec` and proves exact two-pass composition; fep-017 supplies Mathlib's posterior kernel and joint-reconstruction law; and fep-034 composes transition and observation kernels into a normalized filter. These results still do not define graph topology or a loopy update schedule, so tree exactness and iterative convergence are not inferred.

The agent's variational posterior $q(s)$ approximates the true posterior $p(s \mid o)$ by minimizing the standard variational free energy ([@eq:eq_VFE_functional]); under mean-field or structured factorizations this motivates message-passing updates. The catalogue distinguishes three exact layers: finite normalized local messages (fep-007), algebraically compositional finite propagation (fep-047), and measure-valued Bayesian posterior/filter kernels (fep-017/fep-034). `FEPComposed.fep034_filter_is_fep017_posterior` proves that the filter is precisely the native posterior at the transition-predicted prior. The finite kernel adds a policy-conditioned normalized state--outcome joint and exact posterior reconstruction. What remains absent is a typed factor-graph topology with loopy-message schedules and a theorem equating those schedules to the kernel posterior, not a shared finite generative model itself.

### Expected Free Energy and Policy Selection {#sec:ai_expected_free_energy}

Many discrete Active-Inference formulations evaluate candidate policies with an **expected free energy** $G(\pi)$ over predicted states and outcomes. Because several inequivalent conventions appear in the literature [@millidge2021whence; @champion2026reframing], we fix the convention used by the maintained finite kernel. Let $q_\pi(s)$ be the predicted state law, $\ell(o\mid s)$ a normalized likelihood, $q_\pi(s,o)=q_\pi(s)\ell(o\mid s)$ the predictive joint, $q_\pi(s\mid o)$ its positive-evidence posterior, and $p_C(o)$ a positive preferred-outcome law. Then

$$
G(\pi)
\;=\; \mathbb{E}_{q_\pi(s,o)}\!\left[
\log q_\pi(s)-\log q_\pi(s\mid o)-\log p_C(o)
\right].
$$ {#eq:ai_efe_log_ratio}

The first two logarithms have expectation $-I_{q_\pi}(S;O)$, while the last contributes preference cross-entropy. Thus [@eq:ai_efe_log_ratio] is exactly the pragmatic-minus-epistemic convention formalized by the finite carrier. For a horizon, a common stage-additive extension is

$$
G_{1:T}(\pi) \;=\; \sum_{\tau=1}^{T} G_\tau(\pi),
$$ {#eq:ai_efe_total}

where each $G_\tau$ is evaluated after replacing the model's initial law by the state prediction from the preceding stage. `cumulativeExpectedFreeEnergyFrom` implements this recursion. Lean proves exact decomposition at every prefix--suffix boundary and nonnegativity under a recursive stagewise full-support contract. That carrier remains open loop. fep-071 uses a separate finite belief/action/observation carrier to reoptimize after each observation-dependent update and proves a two-stage Boolean case where feedback strictly beats every fixed open-loop second action. The `fep-128`--`fep-134` family then defines observation-indexed policy trees at every finite depth, proves recursive Bellman minimization and optimal-tree existence, embeds open-loop plans, proves weak closed-loop dominance, transports the risk--ambiguity EFE identity under full support, and supplies a strict Boolean feedback witness [@friston2020sophisticated].

The terminal theorem `FEPComposed.FiniteReferenceAgent.finiteReferenceAgent_terminal` closes one narrower shared-carrier chain. In its selected Boolean sampling model, two `true` observations yield the exact learned posterior masses $1/10$ on `false` and $9/10$ on `true`; one further `true` observation performs one exact Bayes update, which is lifted to the sixteen-state Boolean internal--sensory--active--external carrier. With false-positive report loss four times false-negative loss, the posterior-dependent continuation selects the `true` report and strictly improves on either fixed second-stage report. The action interface then identifies that emitted `true` action with the generative transition and with the `true` slice of the action-indexed semigroup, namely the selected positive-time refresh kernel. This is an attained one-step posterior--decision--action certificate. The decision objective is posterior report risk, not EFE, and the policy-tree carrier has no transition field; the result therefore does not prove transition-aware planning, EFE-optimal control, reward--EFE equivalence, or optimization for future kernel consequences.

#### Risk--Ambiguity Decomposition {#sec:ai_risk_ambiguity}

Using $q_\pi(s,o)=q_\pi(s)\ell(o\mid s)$, the entropy identity $I(S;O)=H(O)-H(O\mid S)$, and the cross-entropy identity $\mathrm{CE}(q_\pi(o),p_C)=H(q_\pi(o))+D_{\mathrm{KL}}(q_\pi(o)\Vert p_C)$ yields the **risk--ambiguity** decomposition:

$$
G(\pi) \;=\;
\underbrace{D_{\mathrm{KL}}\!\left(q_\pi(o)\,\middle\|\,p_C(o)\right)}_{\text{preference risk}}
\;+\;
\underbrace{\mathbb{E}_{q_\pi(s)}\!\left[H\!\left(\ell(\cdot\mid s)\right)\right]}_{\text{ambiguity}},
$$ {#eq:ai_risk_ambiguity}

where $H[\ell(\cdot\mid s)]= -\sum_o \ell(o\mid s)\log\ell(o\mid s)$. Risk is a divergence between predicted and preferred outcomes, not merely expected preference surprise; the latter is the pragmatic cross-entropy and differs from risk by the predicted-outcome entropy. Ambiguity is the expected entropy of the observation channel: a high-ambiguity policy favors states whose likelihood is dispersed. In the finite kernel, both terms are nonnegative, so this decomposition also proves $G(\pi)\ge 0$ under the stated full-support contract.

#### Epistemic--Pragmatic Decomposition {#sec:ai_epistemic_pragmatic}

The defining rearrangement is the **epistemic--pragmatic** form:

$$
G(\pi) \;=\;
\underbrace{\operatorname{CE}\!\left(q_\pi(o),p_C(o)\right)}_{\text{pragmatic cost}}
\;-\;
\underbrace{I_{q_\pi}(S;O)}_{\text{epistemic value}}.
$$ {#eq:ai_epistemic_pragmatic}

Here mutual information measures anticipated information gain about the hidden state, and cross-entropy measures expected negative log preference. Expanding the two finite sums gives

$$
G(\pi)
= \sum_o q_\pi(o)\bigl[-\log p_C(o)\bigr]
- \sum_{s,o}q_\pi(s,o)
  \log\!\frac{q_\pi(s,o)}{q_\pi(s)q_\pi(o)}.
$$ {#eq:ai_efe_epi_prag}

The maintained finite information layer defines the second sum as KL divergence from the joint to the product of its marginals. Under full support, Lean proves that [@eq:ai_risk_ambiguity] and [@eq:ai_epistemic_pragmatic] agree exactly. Topic fep-021 remains a distinct `ENNReal` convention: pragmatic cost truncated-subtract epistemic value. It proves $G+\mathrm{IG}=C$ under the visible premise $\mathrm{IG}\le C$, monotonicity in cost, antitonicity in information value, and the zero boundary; `FEPComposed.fep021_informationGain_balance` instantiates its information input with fep-041's native measure KL. The finite real-to-`ENNReal` bridge uses `ENNReal.ofReal`, so negative real values would be truncated rather than silently identified.

#### Softmax Policy Selection with Precision {#sec:ai_softmax_policy}

Policies are then selected via a **Boltzmann/softmax posterior** over $G$:

$$
q(\pi) \;=\; \frac{p_0(\pi)\exp(-\gamma\, G(\pi))}{\sum_{\pi'} p_0(\pi')\exp(-\gamma\, G(\pi'))}, \qquad \gamma \ge 0,
$$ {#eq:ai_softmax_policy}

with prior policy law $p_0$ and precision $\gamma$ controlling the exploration--exploitation balance. At $\gamma=0$, the posterior equals $p_0$ rather than being uniformly distributed unless the prior is uniform. In a finite policy space, the large-precision limit concentrates on prior-supported EFE minimizers, with relative mass among tied minimizers inherited from $p_0$. The maintained kernel proves finite normalization for the one-stage EFE posterior, existence of MAP and EFE-minimizing policies, antitone ordering by EFE for equal priors and nonnegative precision, and exact pushforward of policy mass to an action law. fep-070 separately normalizes a prior-weighted exponential action score for finite control. The later policy-tree family proves deterministic finite-tree optimality but does not define a probability posterior over trees or infer precision.

Some Active-Inference models infer precision $\gamma$ rather than treating it as fixed. That hierarchical precision update is not present in fep-028. The row defines a support-aware finite softmax for any real $\gamma$, proves nonnegativity and a unit upper bound, proves exact zero outside the selected support, and proves that the complete finite policy vector sums to one. `FEPComposed.fep012_softmax_entropyRegularizedCost_le` then feeds this law into fep-012's Shannon-entropy-regularized objective. Neither theorem proves precision learning or the asymptotic temperature limits stated informally above.

#### Exploration Bonus and Information Gain {#sec:ai_exploration_bonus}

[@eq:ai_information_gain] motivates **fep-041**, which now defines information gain directly as Mathlib's measure-valued `InformationTheory.klDiv`:

$$
\mathrm{IG}(\pi) \;=\; \mathbb{E}_{q(o\mid\pi)}\!\bigl[\mathrm{KL}\bigl[q(s \mid o, \pi) \,\big\|\, q(s \mid \pi)\bigr]\bigr] \;=\; I(s; o \mid \pi) \;\ge\; 0.
$$ {#eq:ai_information_gain}

fep-041 proves nonnegativity, finite-measure separation, and vanishing expected information gain when a posterior kernel equals the prior almost everywhere under the predictive observation measure. The maintained finite carrier now builds the policy-conditioned predictive joint and defines epistemic value as its mutual information. The remaining bridge is a theorem identifying that finite joint-KL definition with fep-041's measure-valued posterior-averaged KL under matched embeddings and support assumptions. Claims about epistemic foraging also require a behavioral or dynamical model beyond either information identity.

#### Markov Decision Processes as a Special Case {#sec:ai_mdp_limit}

A common comparison recovers reward-like policy objectives from log prior preferences. If the prior over preferred outcomes is written as

$$
p(o \mid C) \;=\; \begin{cases} \exp(r(o))/Z & o \in \mathcal{G}, \\ 0 & o \notin \mathcal{G}, \end{cases}
$$ {#eq:ai_mdp_indicator_prior}

or more generally $\log p(o \mid C) = r(o) - \log Z$, the pragmatic term resembles negative expected reward up to a constant. fep-033 now defines a deterministic transition-aware finite-horizon value in `ENNReal` and proves its exact Bellman recursion, monotonicity in stage/terminal costs, and zero-cost and zero-discount boundaries. This is a genuine dynamic-programming contract, but without a shared reward/preference transformation and stochastic policy model it still does **not** prove that Active Inference contains finite-horizon MDPs.

### Perception vs Action in the Catalogue {#sec:ai_perception_action_topics}

The rows used in this section can be grouped heuristically along a perception/action interface; fep-017 and fep-034 are Bayesian-Mechanics rows included here as cross-area dependencies:

- **Perception-side topics**: fep-007 and fep-047 provide normalized local messages and compositional finite propagation; fep-017 and fep-034 provide native posterior and transition--observation filter kernels.
- **Action-side topics**: fep-003 (discounted pragmatic cost), fep-008 (finite minimizer), fep-012/fep-028 (entropy-regularized and softmax policies), fep-021 (explicit EFE convention), fep-023 (policy-indexed reachable laws), fep-033 (Bellman recursion), fep-041 (native KL information gain), fep-065--071 (controlled kernels, belief updates, soft control, and sophisticated EFE), and fep-128--134 (finite policy-tree recursion, optimality, open-loop embedding, treewise EFE, and strict feedback).
- **Collective topics**: fep-107--113 cover independent product-agent laws, additive VFE/EFE, unit-weight product-of-experts pooling, consensus mass conservation and contraction, and coupled-potential descent under their explicit independence, overlap, and fixed-mixing premises.
- **Optimization bridge**: fep-032 and fep-043 prove exact quadratic gradient dynamics and criticality; fep-048 supplies a general contraction contract and convergence witness.

#### Belief Propagation on Factor Graphs (fep-007) {#sec:ai_belief_propagation}

The sequential generative model of [@sec:ai_generative_model] admits a canonical factor-graph representation: variable nodes for each $s_t$ and $o_t$, factor nodes for the prior $p(s_1)$, each transition $p(s_{t+1} \mid s_t, a_t)$, and each emission $p(o_t \mid s_t)$. The *sum--product* (belief propagation) algorithm computes the marginal $q(s_t) \approx p(s_t \mid o_{1:T})$ by local message passing on this graph: forward messages $\alpha_t(s_t) = \sum_{s_{t-1}} p(s_t \mid s_{t-1}, a_{t-1})\,\alpha_{t-1}(s_{t-1})\,p(o_{t-1} \mid s_{t-1})$ and backward messages $\beta_t(s_t)$ combine into the posterior $q(s_t) \propto \alpha_t(s_t)\,\beta_t(s_t)$. In the linear-Gaussian case this reduces exactly to the Kalman filter/smoother.

**fep-007** retains the local product/order lemmas and adds a support-aware normalized message. Strictly positive factors and incoming values over a nonempty support give a positive normalizer, pointwise nonnegative output, and support mass exactly one. Exactness on a tree and convergence on a loopy graph still require a formal graph and update schedule rather than follow from local normalization.

#### Categorical Belief Updates (fep-034) {#sec:ai_categorical_update}

For discrete state and observation spaces, the single-step Bayesian update has the canonical form

$$
q(s \mid o) \;\propto\; p(o \mid s)\,q(s), \qquad q(s \mid o) \;=\; \frac{p(o \mid s)\,q(s)}{\sum_{s'} p(o \mid s')\,q(s')},
$$ {#eq:ai_categorical_bayes}

where the denominator is the evidence. **fep-034** now defines the transition-predicted prior as kernel--measure composition and applies Mathlib's posterior construction to the observation kernel. It proves predictive and posterior mass one, reconstruction of the transition-prediction/observation joint law, and recovery of the predicted prior. The composition theorem identifies it definitionally with fep-017's posterior at that predicted prior.

The normalization assumptions are carried by Mathlib's finite/Markov-kernel typeclasses rather than by a manually divided finite vector. This supplies an exact one-step Bayesian filter, not a numerical filtering algorithm or approximation theorem. The maintained finite kernel separately composes policy transitions into an open-loop rollout, accumulates EFE against each successive predicted state law, and reconstructs a terminal posterior at positive evidence. The general `PolicyTree` carrier remains separate and does not identify every intermediate tree belief with this native posterior kernel. H1 closes exactly one exception: a finite belief index interprets its root as the selected two-observation posterior and proves that its single reachable successor commutes with one further `posteriorUpdate`; later updates are deliberately outside that carrier.

### Policies, Optimality, and Affordances {#sec:ai_policies_affordances}

#### Affordances and Reachability (fep-023) {#sec:ai_affordances}

The term *affordance*, borrowed from ecological psychology [@gibson1979ecological], has a precise formal meaning within Active Inference: the set of outcomes that an agent can render accessible through some choice of policy. Given a family of admissible policies $\Pi$ and a predictive distribution $q(\cdot \mid \pi)$ over outcomes for each $\pi \in \Pi$, the *affordance set* is

$$
\mathcal{A}(\Pi, q) \;=\; \{\, o : \exists \pi \in \Pi,\; q(o \mid \pi) > 0 \,\} \;=\; \bigcup_{\pi \in \Pi} \operatorname{supp}\!\bigl(q(\cdot \mid \pi)\bigr).
$$ {#eq:ai_affordance_set}

**fep-023** encodes reachability as the set of probability laws generated by an allowed finite policy set. It proves membership for an allowed policy, monotonicity under policy-set inclusion, and transfer of probability normalization to every reachable law. It does not define outcome support, optimize over the reachable-law set, or connect that set to fep-041's policy-conditioned information gain, so curiosity and niche-construction interpretations remain outside the row.

#### Optimal Policy Existence (fep-008) {#sec:ai_optimal_policy_existence}

Policy selection reduces to minimization of $G$ over the finite policy set. **fep-008** certifies that such a minimizer exists and that all minimizers share a common EFE value. The proof invokes `Finset.exists_min_image` to obtain an explicit minimizer $\pi^\star$ with $G(\pi^\star) \le G(\pi)$ for every $\pi \in \Pi$, and then `min_agrees_on_value` plus `le_antisymm` to show that any two minimizers $\pi^\star_1, \pi^\star_2$ satisfy $G(\pi^\star_1) = G(\pi^\star_2)$. The discrete, finite setting matches real Active-Inference implementations that enumerate a finite policy horizon; fep-008 is thus the small but essential existence theorem that downstream results (commitment to a specific action, deterministic policy extraction, value iteration on the EFE lattice) rely upon.

#### Mathlib Footprint and Verification Status {#sec:ai_mathlib_table}

| Topic | Actual Lean content | Semantic disposition | Mathlib navigation hint | `sorry` count |
|-------|---------|----------|--------------------|--------------|
| fep-003 | Discounted `ENNReal` pragmatic cost with exact horizon increment | `{{topics.fep-003.semantic_disposition}}` | `Data.ENNReal.Inv` | 0 |
| fep-007 | Positive, support-normalized finite sum-product message | `{{topics.fep-007.semantic_disposition}}` | `Algebra.BigOperators` | 0 |
| fep-008 | Finite nonempty-set minimizer existence and value agreement | `{{topics.fep-008.semantic_disposition}}` | `Data.Finset` | 0 |
| fep-020 | Normalized two-state transition, stationarity, exact iterates, convergence | `{{topics.fep-020.semantic_disposition}}` | `Analysis.SpecificLimits.Normed` | 0 |
| fep-021 | Explicit `ENNReal` EFE convention with balance and order laws | `{{topics.fep-021.semantic_disposition}}` | `Data.ENNReal.Inv` | 0 |
| fep-023 | Policy-indexed reachable probability laws and normalization transfer | `{{topics.fep-023.semantic_disposition}}` | `MeasureTheory.Measure.Typeclasses.Probability` | 0 |
| fep-028 | Support-aware full finite softmax probability law | `{{topics.fep-028.semantic_disposition}}` | `Analysis.SpecialFunctions.Exp` | 0 |
| fep-033 | Deterministic transition-aware Bellman recursion | `{{topics.fep-033.semantic_disposition}}` | `Data.ENNReal.Inv` | 0 |
| fep-034 | Native normalized transition--observation posterior filter | `{{topics.fep-034.semantic_disposition}}` | `Probability.Kernel.Posterior` | 0 |
| fep-041 | Native measure-KL information gain and zero-expectation law | `{{topics.fep-041.semantic_disposition}}` | `InformationTheory.KullbackLeibler.Basic` | 0 |
| fep-047 | `Matrix.mulVec` sum-product propagation with exact composition | `{{topics.fep-047.semantic_disposition}}` | `Data.Matrix.Mul` | 0 |
: Active Inference topics: the Lean content each row actually states, its semantic disposition, a Mathlib navigation hint, and its `sorry` count.

**Representative formalization** — *Expected Free Energy (fep-003, [@eq:eq_4])*: On the maintained finite policy-conditioned carrier, EFE decomposes into pragmatic cost minus epistemic value:

$$
\EFE(\pi)
=
\underbrace{\operatorname{CE}\!\bigl(q_\pi(o),p_C(o)\bigr)}_{\text{pragmatic cost}}
-
\underbrace{I_{q_\pi}(S;O)}_{\text{epistemic value}} .
$$

The production fep-003 sketch defines finite-horizon discounted pragmatic cost directly in `ENNReal`, proves its exact successor-horizon increment, and establishes monotonicity in both stage costs and horizon. fep-021 then combines that cost with an epistemic value under the package's explicit sign convention, and the composed theorem checks the balance. Those topic rows do not derive the probabilistic expression above; the maintained finite carrier does so separately for a real-valued one-step policy-conditioned joint under full support. See [@sec:finite_kernel_efe], [@sec:catalogue-fep-003] in Appendix B, and [@sec:eqs-fep-003] in [@sec:appendix_c_latex_equations].

**Representative formalization** — *Optimal Policy Existence (fep-008)*: On a nonempty finite policy set, EFE achieves its minimum. The sketch invokes `Finset.exists_min_image` (producing a certified minimizer) and then proves that any two minimizers agree on $G$ via `le_antisymm`. This turns the *soft* statement "some policy is best under $G$" into a compiler-verifiable existence theorem — a small but important piece of machinery for downstream results where the agent commits to a specific action. Note the discrete setting matches real active-inference implementations that enumerate a finite policy horizon. Typeset statements: [@sec:eqs-fep-008] in [@sec:appendix_c_latex_equations]; Lean: [@sec:catalogue-fep-008] in Appendix B.

**Representative formalization** — *Affordances as Reachable Laws (fep-023)*: The sketch maps policies to probability measures and defines the reachable set as the image of an allowed finite policy set. It proves set monotonicity and that every reachable law inherits probability normalization. Inclusion is weak: added policies may induce an already-reachable law, so strict growth is not claimed. See [@sec:eqs-fep-023] in [@sec:appendix_c_latex_equations] and [@sec:catalogue-fep-023] in Appendix B.

**Depth landmarks.** fep-028 is a complete finite softmax law; fep-008 is a finite-set minimizer theorem; fep-021 fixes an explicit `ENNReal` EFE convention; fep-034 is a normalized posterior filter; and fep-041 uses native measure KL. The finite kernel supplies their missing shared model at a distinct real-valued finite layer and adds stage-updated cumulative EFE. fep-071 adds exact observation-dependent reoptimization; fep-128--134 add arbitrary finite-depth policy trees, optimality, open-loop dominance, treewise EFE, and a strict feedback witness; and fep-107--113 add independent-product and fixed two-agent collective laws. H1 then connects one exact learned posterior, one further update, one asymmetric optimal report, and the emitted action's exact transition on a selected finite model. Remaining limitations include the explicit real/`ENNReal` bridge, broader measure-level EFE equivalence, probabilistic selection or learning over policy trees, transition-aware planning on the H1 carrier, infinite or continuous carriers, arbitrary network topologies, and refinement to executable agents. Syntactic `mathlib_status`, semantic disposition, and current native evidence are reported separately in generated coverage and receipts.

**Mathlib4 module footprint (Active Inference).** Finite aggregation routes through `Algebra.BigOperators.Group.Finset`, while finite policy indices and images use `Data.Fin` and `Data.Finset`. The generated coverage report owns the exact topic-to-import incidence table. Conceptually, these modules supply the finite sums, support sets, minimizer existence, and image constructions on which the discrete policy layer depends; they do not by themselves establish a probabilistic EFE interpretation.

### What the Active Inference Theorems Collectively Establish {#sec:ai_synthesis}

The {{areas.ActiveInference.count}} rows can be grouped by intended role. At topic level they remain local facts; the maintained finite kernel composes their central probabilistic counterparts into one bounded agent model:

1. **EFE inputs and convention** — fep-003 provides discounted pragmatic cost, fep-041 provides native KL information gain, and fep-021 composes them under one explicit `ENNReal` sign convention.
2. **Inference operators** — fep-007 provides normalized local messages, fep-047 exact finite operator composition, and fep-017/fep-034 native posterior/filter kernels.
3. **Policy selection** — fep-008 and fep-028 cover deterministic finite argmin existence and stochastic softmax normalization; fep-012 adds the finite Shannon entropy regularizer.
4. **Multi-step planning** — fep-033 proves an exact deterministic Bellman recursion and boundary laws in `ENNReal`; the finite kernel composes policy-conditioned transitions, updates the predicted state law stage by stage, accumulates real-valued EFE, and proves prefix--suffix decomposition and support-qualified nonnegativity.
5. **Information value** — fep-041 proves KL nonnegativity, finite-measure separation, and a zero expected-information boundary; the finite kernel defines policy-conditioned mutual information, while equivalence to the native posterior-averaged KL remains bridge work.
6. **Optimization dynamics** — fep-032/fep-043 provide exact stable quadratic gradient dynamics, while fep-048 packages a global contraction interface.
7. **Stochastic dynamics** — fep-020 gives a normalized two-state Markov evolution with stationarity, exact iterates, and convergence.
8. **Distributional reachability** — fep-023 makes policies reach probability laws and transfers normalization, without yet supplying embodiment or an optimization theorem over that set.
9. **Controlled decisions and sophisticated planning substrates** — fep-065--071 add controlled-kernel normalization, positive-evidence belief updates, reachable finite-belief value preservation, soft Bellman/desirability recursion, a control posterior, and a strict two-stage feedback advantage; fep-128--134 extend this to arbitrary finite-depth observation-contingent trees, prove optimal-tree existence and open-loop dominance, and preserve an explicit strict-feedback boundary. H1 uses those substrates for one attained posterior-report decision and transition-consistent action, without upgrading that decision to EFE-optimal or transition-aware planning.
10. **Collective inference** — fep-107--113 prove independent-agent VFE/EFE additivity, positive-normalizer unit-weight product-of-experts pooling, mass conservation, fixed-matrix consensus contraction, and coupled-potential descent without inferring emergent agency.

No single theorem in this list proves Active Inference as a universal theory. The H1 terminal theorem does certify one particular synthetic discrete one-step chain: exact posterior learning, a posterior-dependent asymmetric report decision, and the emitted action's matching transition. It is not a certificate for an MDP implementation or a general active-inference agent. The broader package provides normalized updates, native posterior kernels, a shared finite policy-conditioned generative model, posterior VFE, both central EFE decompositions, prior-weighted policy/action selection, state-updating cumulative open-loop EFE, native information gain, controlled finite-belief recursion, arbitrary finite-depth observation-contingent policy trees with deterministic optimality, a strict feedback witness, and scoped collective laws. The remaining high-level obligations are distributions and learning over policy trees, transition-aware and EFE-optimal control on the shared H1 carrier, infinite-horizon or continuous-carrier planning, comparison across alternative EFE conventions, a finite-to-measure conditional-information bridge, arbitrary multiagent interaction structures, and a refinement relation to executable code.

All {{areas.ActiveInference.count}} rows carry **`mathlib_status: real`**, a source classification that is distinct from semantic maturity. The current native area rate, when backed by a claim-ready native receipt, is **`{{compile_rate.by_area.ActiveInference}}`**. Reproduce it with `uv run fep-lean verify --fail-on-warnings --receipt output/native-verification.json`; full Hermes/OpenGauss evidence remains a separate contract.
