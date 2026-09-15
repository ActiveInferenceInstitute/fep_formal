# From 120 to 155: Risk, Feedback, Native Blankets, Dual Geometry, and Continuous Time {#sec:formalism_catalogue_155}

The second catalogue expansion adds thirty-five stable rows, `fep-121` through
`fep-155`, in five seven-topic families. Its purpose is not numerical growth.
Each family closes a boundary that was explicit in the preceding 120-topic
snapshot: finite-sample control for the Laplace estimator, genuinely
observation-contingent policy trees, a bridge from finite blanket factors to
Mathlib's native conditional-independence predicate, a differentiable scalar
exponential family with dual identities, and an exact continuous-time Markov
semigroup. The maintained novelty ledger requires every new row to consume at
least one earlier topic through a named `FEPComposed` theorem. The result is a
directed extension of the existing kernel rather than a second list of
similarly named lemmas.

The five carriers remain deliberately narrow. Sampling laws, action spaces,
blanket coordinates, and exponential-family outcomes are finite. The
continuous-time family is an exact Boolean chain rather than a generic
continuous-state diffusion. These restrictions are theorem hypotheses and
scope boundaries, not implementation accidents.

## Toolchain and evidence identity {#sec:catalogue_155_evidence_identity}

The authoring workspace pins **`leanprover/lean4:v4.34.0`** and Mathlib
**`v4.34.0`**, with the exact dependency revision recorded in
`lean/lake-manifest.json`. Lean 4.33.0 introduced the relevant release line
[@lean4330release], while the package uses the subsequent stable Lean patch
[@lean4331release] and matching Mathlib release [@mathlib4331release]. A release
tag, source file, or successful one-file probe is not a catalogue receipt. A
native claim for this expansion requires a fresh exact-roster receipt whose
ordered IDs, source digests, actual compiler version, resolved Mathlib
revision, warnings, and `sorry` count all reconcile against the live 155-topic
source.

Four evidence planes must therefore be read separately:

| Plane | What it can establish | What it cannot establish |
| --- | --- | --- |
| Semantic review | The maintained invariant, assumptions, non-vacuity argument, and disposition for each topic | Kernel acceptance or empirical adequacy |
| Native Lean and declaration receipts | Acceptance of the exact propositions at the pinned compiler; declaration resolution and trusted-axiom closure when the corresponding receipt validates | That hypotheses hold in a biological system, that a numerical plot is representative, or that a provider ran |
| Deterministic numerical witnesses | Exact finite evaluations of named theorem instances and boundary checks | Deductive proof, stochastic calibration on data, or extension beyond the sampled carrier |
| Provider-backed full execution | Hermes/OpenGauss execution for the exact source only when a complete report independently validates | A stronger theorem, physical truth of the FEP, or evidence for any later source snapshot |
: The four evidence planes, and the boundary of what each can and cannot establish.

The v1.1.0 release-snapshot declaration/axiom, native, Python, and Chrome
receipts bind the frozen 155-topic source that they hash. Active Horizon work
changes formal resources, tests, manuscript inputs, and the source-owner
roster, so those retained receipts are historical rather than evidence for the
live checkout until all corresponding validators accept coordinated
replacements. The retained provider report binds an earlier 50-topic snapshot
and is not silently promoted to live 155-topic
provider evidence. At render time, `{{verify.claim_ready}}` and
`{{full.claim_ready}}` report the independently validated native and full
evidence states; unavailable evidence remains unavailable rather than being
filled from an older run.

## Finite-sample risk and calibration (`fep-121`--`fep-127`) {#sec:catalogue_155_risk_calibration}

Let $K$ be the number of successes in a positive sample of size $n$, let
$\widehat p=K/n$, and let the add-one estimate be
$\widetilde p=(K+1)/(n+2)$. The `FEP.EmpiricalRisk` foundation exposes the
exact error decomposition

$$
\widetilde p-p
=\frac{n}{n+2}(\widehat p-p)+\frac{1-2p}{n+2}.
$$ {#eq:catalogue_155_laplace_error}

For $p\in[0,1]$, the offset has absolute value at most $1/(n+2)$. Squaring
with the explicit factor-two inequality and integrating under any normalized
finite law gives

$$
\mathbb E[(\widetilde p-p)^2]
\le 2\left(\frac{n}{n+2}\right)^2
       \mathbb E[(\widehat p-p)^2]
   +\frac{2}{(n+2)^2}.
$$ {#eq:catalogue_155_laplace_risk}

For a Bernoulli target, the Brier score has the exact excess-risk identity

$$
\operatorname{BS}(p,q)-\operatorname{BS}(p,p)=(q-p)^2,
$$ {#eq:catalogue_155_brier}

which specializes [@eq:catalogue_155_laplace_risk] to finite-law
Brier excess risk. This formal target follows the proper probabilistic scoring
rule introduced by Brier [@brier1950verification], while making no empirical
forecast-calibration claim.

| Topic | Primary and boundary declarations | Explicit assumptions and non-vacuity |
| --- | --- | --- |
| `fep-121` | `fep121_laplaceError_identity`; `fep121_shrinkage_mem_unitInterval` | $n>0$, $K\le n$, and $p\in[0,1]$. The shrinkage coefficient is in the unit interval; the identity is algebraic, not a consistency theorem. |
| `fep-122` | `fep122_laplaceBias_abs_le`; `fep122_nonzero_boundary_witness` | $p\in[0,1]$. At $n=2,p=0$, the offset is exactly $1/4\ne0$, so smoothing is not mislabeled as unbiased. |
| `fep-123` | `fep123_laplaceAbsoluteError_le`; `fep123_error_nonnegative` | A raw absolute-error certificate is supplied in addition to the positive-sample and unit-interval hypotheses. The theorem transfers that certificate; it does not derive a tail rate. |
| `fep-124` | `fep124_laplaceSquaredError_le`; `fep124_laplaceSquaredRisk_le` | A normalized finite sampling law and bounded success counts. Both raw error and the pseudo-count offset can contribute positively to the bound. |
| `fep-125` | `fep125_brierExcess_eq_sqError`; `fep125_brierExcess_self` | The polynomial identity is real-valued; its probability interpretation additionally uses $p,q\in[0,1]$. Unequal forecasts have positive squared excess, while $q=p$ is the zero boundary. |
| `fep-126` | `fep126_laplaceBrierRisk_le`; `fep126_sampling_mass_one` | The same finite-law, count, positivity, and target hypotheses as the squared-risk theorem. A nondegenerate law yields a genuine weighted risk rather than a single substituted value. |
| `fep-127` | `fep127_laplaceBadEvent_subset`; `fep127_laplaceBadEvent_probability_le` | A raw event-probability bound is supplied. Event containment transfers the bound monotonically; it does not manufacture a concentration inequality or posterior-contraction rate. |
: Finite-sample risk and calibration topics (fep-121 to fep-127), with each row's declarations and the explicit assumptions that keep it non-vacuous.

The family closes a finite risk-transfer gap for the exact Laplace estimator.
It does **not** prove minimax optimality, frequentist calibration from observed
data, posterior contraction, or a marginal-likelihood optimum. Those would
require a sampling model and theorem target beyond the finite-law transfer
proved here.

## Closed-loop policy trees and expected free energy (`fep-128`--`fep-134`) {#sec:catalogue_155_policy_trees}

A depth-indexed `PolicyTree Action Observation d` chooses an action at each
node and an observation-indexed continuation tree. Given a finite
`PolicyTreeModel`, its recursive value is

$$
V_{d+1}(b;(a,\tau))
=c_d(b,a)+\sum_o P(o\mid b,a)
  V_d\!\left(u(b,a,o);\tau(o)\right).
$$ {#eq:catalogue_155_policy_tree}

Finite nonempty actions make the Bellman minimizer concrete at every node.
Open-loop plans embed by using the same continuation after every observation,
so the optimal policy-tree value is no greater than the value of any embedded
open-loop plan. The treewise EFE row lifts the package's existing one-step
risk-plus-ambiguity identity under its full-support contract. This is the
finite recursive structure motivated by sophisticated active inference
[@friston2020sophisticated], not a claim about every planning algorithm or EFE
convention.

| Topic | Primary and supporting declarations | Explicit assumptions and non-vacuity |
| --- | --- | --- |
| `fep-128` | `fep128_policyTreeValue_node`; `fep128_policyTreeValue_leaf` | Finite belief, action, and observation carriers and a finite natural-number depth. Observation laws and deterministic updates are supplied. Distinct observation branches may select distinct continuations. |
| `fep-129` | `fep129_optimalTreeValue_eq_min`; `fep129_optimalTreeAction_le` | The finite action carrier is nonempty. The selected action is proved no worse than every alternative, not merely named as an optimizer. |
| `fep-130` | `fep130_exists_optimalPolicyTree`; `fep130_policyTree_carrier_finite` | All carriers and the horizon are finite. The witness is a concrete depth-indexed tree attaining the recursive optimum. |
| `fep-131` | `fep131_openLoopEmbedding_value`; `fep131_openLoopEmbedding_leaf` | Both sides share one model, belief, and depth. Positive-depth embedding repeats one continuation across all observation branches; the zero-depth carriers agree at the leaf. |
| `fep-132` | `fep132_optimalTree_le_openLoop`; `fep132_finite_horizon_depth` | Finite nonempty actions and a common finite cost model. The theorem proves weak dominance for every embedded plan; strictness is supplied separately by `fep-134`. |
| `fep-133` | `fep133_policyTree_efe_eq_risk_add_ambiguity`; `fep133_optimalValues_agree` | Every belief-indexed generative model satisfies the maintained `FullSupport` contract. The result transports an existing identity; it does not validate the EFE model empirically. |
| `fep-134` | `fep134_boolFeedback_strictlyBetter`; `fep134_feedback_continuation_changes` | A fair Boolean observation and mismatch terminal cost. Feedback has value $0$, each fixed second action has value $1/2$, and the continuation action differs across the two observations. |
: Closed-loop policy-tree and expected-free-energy topics (fep-128 to fep-134), with each row's declarations and non-vacuity assumptions.

The Boolean witness rules out a vocabulary-only notion of feedback: its two
continuations are propositionally unequal and its value gap is exactly one
half. The remaining planning frontier is not finite policy-tree existence. It
is inference or learning over policy-tree distributions, infinite or
continuous belief spaces, uncertain model parameters, alternative EFE
equivalence conditions, and refinement to an executable online agent.

## Finite-to-native blanket transfer (`fep-135`--`fep-141`) {#sec:catalogue_155_native_blankets}

For a normalized finite law $p$, `FEP.NativeBlanket.embeddedLaw` constructs
the native measure

$$
\mu_p=\sum_x \operatorname{ofReal}(p(x))\,\delta_x.
$$ {#eq:catalogue_155_embedded_law}

Singleton evaluation reflects the original mass, equality of embedded
measures is injective back to finite laws, native integration agrees with the
finite weighted sum, and finite prediction agrees with Mathlib
measure--kernel composition. For a static blanket model, the embedded joint
retains the rectangle factorization

$$
\mu(b,i,e)=p_B(b)\,p_I(i\mid b)\,p_E(e\mid b).
$$ {#eq:catalogue_155_blanket_factorization}

The key step is not a zero-mutual-information proxy. The theorem
`fep139_staticJoint_condIndepFun` states Mathlib's native `CondIndepFun` for the
internal and external coordinate maps conditioned on the blanket coordinate.

| Topic | Primary and supporting declarations | Explicit assumptions and non-vacuity |
| --- | --- | --- |
| `fep-135` | `fep135_embeddedLaw_apply_singleton`; `fep135_embeddedLaw_normalized` | A finite discrete carrier and a normalized nonnegative finite law. A nonuniform law preserves distinct native singleton masses while total mass remains one. |
| `fep-136` | `fep136_embeddedLaw_injective`; `fep136_embeddedLaw_expectation` | A finite discrete carrier and real observable. Distinct point masses remain distinguishable, and a nonconstant observable yields a nontrivial transferred expectation. |
| `fep-137` | `fep137_embeddedPredictive_eq_comp` | Finite discrete input/output carriers and normalized kernel rows. A nondegenerate prior with state-dependent rows yields a genuine mixture on both carriers. |
| `fep-138` | `fep138_staticJoint_rectangle_factorization` | Finite blanket, internal, and external coordinates with normalized conditional rows. The correlated Boolean model has two distinct positive blanket/joint atoms. |
| `fep-139` | `fep139_staticJoint_condIndepFun`; `fep139_correlatedBlanket_nonvacuous` | Finite discrete standard-Borel carriers, nonempty internal/external types, and exact factorized rows. The Boolean witness has two positive correlated blanket regimes, so independence is not obtained by collapsing the entire law to one point. |
| `fep-140` | `fep140_condIndepFun_measurableImages` | Measurable maps of internal and external coordinates. Identity maps recover `fep-139`; noninjective coarsenings can merge endpoint states without changing the conditional-independence conclusion. |
| `fep-141` | `fep141_prediction_preserves_nativeBlanket` | A finite factorized dynamics row and one supplied current state. Multiple positive next-blanket regimes and nonconstant endpoint laws are permitted. Arbitrary mixtures over uncertain current states are not covered. |
: Finite-to-native blanket-transfer topics (fep-135 to fep-141), with each row's declarations and non-vacuity assumptions.

This family closes one concrete finite-to-native conditional-independence seam.
It does not prove that every system admits a blanket, that arbitrary mixtures
preserve rowwise factorization, that a blanket is stationary or attracting, or
that the authored finite coordinates identify a biological boundary.

## Finite exponential-family dual geometry (`fep-142`--`fep-148`) {#sec:catalogue_155_exponential_geometry}

For a finite nonempty outcome carrier, positive base weights $h(x)>0$, and a
real sufficient statistic $T(x)$, the scalar family is

$$
p_\theta(x)=\frac{h(x)e^{\theta T(x)}}{Z(\theta)},
\qquad
A(\theta)=\log Z(\theta).
$$ {#eq:catalogue_155_exponential_family}

The maintained source proves normalization and full support, the affine
log-density ratio, $A'(\theta)=\mathbb E_\theta[T]$, the centered-score
identity, and

$$
A''(\theta)=\operatorname{Var}_\theta[T]
=I(\theta),
\qquad
D_{\mathrm{KL}}(p_\theta\Vert p_\eta)
=A(\eta)-A(\theta)-A'(\theta)(\eta-\theta).
$$ {#eq:catalogue_155_dual_geometry}

These are the finite scalar counterparts of the metric and affine structures
that motivate information geometry [@amari1983foundation]. They do not by
themselves construct the full manifold, dual affine connections, or curvature
described in the general theory.

| Topic | Primary and supporting/boundary declarations | Explicit assumptions and non-vacuity |
| --- | --- | --- |
| `fep-142` | `fep142_exponentialFamily_sum_one`; `fep142_exponentialFamily_pointwise_pos` | Finite nonempty outcomes and strictly positive base weights. A maintained nonconstant three-state family has unequal positive masses away from zero. |
| `fep-143` | `fep143_logDensityRatio_eq` | Full support makes every logarithm finite. Distinct parameters with a nonconstant statistic produce outcome-dependent ratios. |
| `fep-144` | `fep144_logPartition_hasDerivAt` | A finite sum of positive exponential weights. No infinite-sum interchange or arbitrary-manifold differentiability is inferred. |
| `fep-145` | `fep145_score_eq_statistic_sub_mean`; `fep145_score_mean_zero` | The scalar natural-parameter score is defined on the full-support family. A nonconstant statistic yields positive and negative scores whose weighted mean cancels. |
| `fep-146` | `fep146_logPartition_secondDeriv_eq_variance`; `fep146_fisher_eq_variance`; `fep146_threeState_variance_positive`; `fep146_constantStatistic_zero_boundary` | The finite scalar family and the proved first derivative. For statistic $(0,1,2)$ with unit bases, variance at zero is $2/3>0$; a constant statistic has exactly zero variance and Fisher information. |
| `fep-147` | `fep147_exponentialFamily_KL_eq_bregman`; `fep147_exponentialFamily_fullSupport` | Two members of the same supported scalar family. Equal parameters give the zero-KL boundary through the shared finite-KL separation theorem. The companion three-state family has variance $2/3$, while the constant-statistic family has zero variance; this row does not add a separate strict-KL witness for unequal parameters. |
| `fep-148` | `fep148_meanParameter_strictMono`; `fep148_meanParameter_injective` | Variance is explicitly positive throughout a stated closed interval. The theorem is interval-local and does not infer positivity for degenerate statistics. |
: Finite exponential-family dual-geometry topics (fep-142 to fep-148), with each row's declarations and non-vacuity assumptions.

The three-state and constant-statistic witnesses make the rank premise visible:
strict mean-coordinate monotonicity is supported by positive variance, while a
constant statistic supplies an exact zero-information boundary.

## Two-state continuous-time thermodynamics (`fep-149`--`fep-155`) {#sec:catalogue_155_continuous_time}

Let $a>0$ be the false-to-true rate and $b>0$ the true-to-false rate. The
generator and stationary law are

$$
Q=\begin{pmatrix}-a&a\\ b&-b\end{pmatrix},
\qquad
\pi=\left(\frac{b}{a+b},\frac{a}{a+b}\right).
$$ {#eq:catalogue_155_generator}

Using $\rho(t)=e^{-(a+b)t}$, the source defines the four entries of an exact
transition matrix $P_t$. For nonnegative time the rows are nonnegative and
normalized; for all real $s,t$, the closed form satisfies

$$
P_{s+t}=P_sP_t,
\qquad
\frac{\mathrm d}{\mathrm dt}P_t=QP_t=P_tQ.
$$ {#eq:catalogue_155_semigroup_master}

The stationary law is invariant and obeys detailed balance. If $m_t$ is the
true-state mass from an arbitrary initial finite law, then

$$
m_t-\pi_1=e^{-(a+b)t}(m_0-\pi_1),
\qquad
L(t)=(m_t-\pi_1)^2=e^{-2(a+b)t}L(0),
\qquad
L'(t)=-2(a+b)L(t).
$$ {#eq:catalogue_155_relaxation}

| Topic | Primary and supporting declarations | Explicit assumptions and non-vacuity |
| --- | --- | --- |
| `fep-149` | `fep149_twoStateSemigroup_rowSum`; `fep149_twoStateSemigroup_nonnegative`; `fep149_benchmarkRates_exact` | Positive rates and nonnegative time for stochasticity. Rates $0.7$ and $0.3$ give decay rate one and a nonuniform stationary law. |
| `fep-150` | `fep150_twoStateSemigroup_zero` | Positive rates. All four Boolean entries distinguish the identity boundary: diagonal one, off-diagonal zero. |
| `fep-151` | `fep151_twoStateSemigroup_add` | Positive rates; the stochastic interpretation uses nonnegative times. Unequal rates and positive times give nonidentity kernels whose product is still exact. |
| `fep-152` | `fep152_twoStateSemigroup_hasDerivAt` | The maintained explicit Boolean generator and transition formulas. Both left and right generator products are proved entrywise; no general CTMC existence theorem is inferred. |
| `fep-153` | `fep153_twoStateSemigroup_stationary`; `fep153_twoStateSemigroup_detailedBalance` | Positive rates and nonnegative time for the kernel. Unequal rates give a nonuniform stationary law while opposing fluxes balance exactly. |
| `fep-154` | `fep154_twoStateRelaxation_exact`; `fep154_benchmarkInitial_nonstationary` | An arbitrary normalized Boolean initial law. The false point mass differs from the benchmark stationary law, so the relaxed coordinate starts nonzero. |
| `fep-155` | `fep155_twoStateLyapunov_exact`; `fep155_twoStateLyapunov_hasDerivAt`; `fep155_benchmarkLyapunov_strictlyDecreasing` | The scalar squared stationary deviation for the exact two-state chain. At the nonstationary benchmark, the derivative at time zero is strictly negative. |
: Two-state continuous-time thermodynamics topics (fep-149 to fep-155), with each row's declarations and non-vacuity assumptions.

This family adds genuine continuous time, a semigroup, and a master equation at
one exact finite-state scope. It is not a Langevin SDE, a Fokker--Planck PDE, a
generic finite-state CTMC construction, a nonequilibrium driven steady state,
or an identification of the quadratic Lyapunov function with thermodynamic or
variational free energy.

## Composition ledger for the thirty-five rows {#sec:catalogue_155_composition_ledger}

Each new row has a manifested leaf theorem that consumes the new topic and at
least one earlier endpoint. The bridge names below are part of the novelty
contract; their existence prevents an import graph from being reported as a
scientific derivation.

| New topics | Manifested composition declarations |
| --- | --- |
| `fep-121`--`fep-127` | `fep121_laplaceError_extends_fep036`; `fep122_laplaceBias_extends_fep036`; `fep123_laplaceAbsoluteError_extends_fep036`; `fep124_laplaceSquaredRisk_combines_fep036_fep114`; `fep125_brierExcess_refines_fep022`; `fep126_laplaceBrierRisk_combines_fep022_fep036`; `fep127_laplaceConcentration_combines_fep036_fep114` |
| `fep-128`--`fep-134` | `fep128_policyTreeRecursion_extends_fep071`; `fep129_policyTreeBellman_extends_fep033`; `fep130_optimalPolicyTree_extends_fep008`; `fep131_openLoopEmbedding_extends_fep033`; `fep132_closedLoopDominance_extends_fep071`; `fep133_treewiseEFE_extends_fep021`; `fep134_feedbackWitness_extends_fep071` |
| `fep-135`--`fep-141` | `fep135_embeddedLaw_extends_fep017`; `fep136_embeddedExpectation_extends_fep015`; `fep137_embeddedPredictive_extends_fep019`; `fep138_rectangleFactorization_extends_fep079`; `fep139_nativeCondIndep_connects_fep009_fep079`; `fep140_measurableCoarsening_extends_fep009`; `fep141_blanketTransition_extends_fep080` |
| `fep-142`--`fep-148` | `fep142_exponentialNormalization_extends_fep031`; `fep143_logDensityRatio_extends_fep026`; `fep144_logPartitionGradient_extends_fep040`; `fep145_centeredScore_extends_fep038`; `fep146_fisherVariance_extends_fep100`; `fep147_KLBregman_connects_fep014_fep104`; `fep148_meanCoordinate_extends_fep103` |
| `fep-149`--`fep-155` | `fep149_continuousKernel_extends_fep020`; `fep150_semigroupZero_extends_fep006`; `fep151_semigroupAdd_extends_fep006`; `fep152_masterEquation_extends_fep020`; `fep153_continuousDetailedBalance_extends_fep010`; `fep154_continuousRelaxation_extends_fep020`; `fep155_lyapunovDecay_extends_fep032` |
: Composition ledger: the manifested declarations that tie each group of new topics back to the established core.

These bridges are primarily `formal_pairing` witnesses: they preserve both
endpoint laws in one checked conclusion without claiming that one topic follows
from the other. A derivational `formal` edge is reserved for a theorem that
actually derives or identifies its target.

## Validation and visualization contract {#sec:catalogue_155_validation_visualization}

The dashboard now supplies one typed deterministic witness for each of the
fifteen expansion families. The five new witnesses are not generic plots:

| Witness | Exact checks and boundary |
| --- | --- |
| `laplace-brier-risk` | finite sampling mass equals one; Brier risk is below the transferred bound; the $n=2,p=0$ bias equals $1/4\ne0$ |
| `policy-tree-feedback` | feedback value equals zero; fixed plans equal one half; feedback is no worse; the two continuation actions differ |
| `native-blanket-transfer` | the two positive regimes sum to one; rectangle factorization is exact; the off-regime has zero mass; every conditional product row is present |
| `exponential-family-duality` | both laws normalize; the score is centered; finite KL equals log-partition Bregman divergence; three-state variance is $2/3$; the constant-statistic boundary is zero |
| `two-state-master-equation` | row normalization, semigroup addition, master equation, detailed balance, and relaxation all close numerically; the benchmark Lyapunov derivative is negative |
: The numerical witnesses added for the expansion families, with the exact check each performs and the boundary of what it certifies.

Each check has a typed relation (`eq`, `le`, `ge`, or `predicate`), explicit
operands, and its own tolerance. Acceptance is the conjunction of all checks
and the named boundary observation. This representation avoids hiding a failed
inequality behind an unrelated small residual. The static SVG and interactive
HTML are projections of the same immutable witness model; the HTML retains
the exact check table for screen-reader and nonvisual inspection.

The formalism atlas answers a different question. It separates authored
scientific relations from module-import dependencies, preserves capability
status, and names every formal witness. Agreement between the atlas and the
dashboard is useful diagnostic evidence, but neither replaces an exact-roster
native receipt or declaration/axiom audit.

## Residual frontier after 155 topics {#sec:catalogue_155_residual_frontier}

The expansion changes the location of the open boundary. It is no longer
accurate to say that the package has no finite-sample Laplace risk theorem, no
finite policy-tree carrier, no native blanket conditional-independence bridge,
no differentiable exponential family, or no continuous-time Markov example.
The remaining claims are broader and materially harder:

1. posterior contraction, minimax or calibration guarantees, and empirical
   marginal-likelihood objectives on a shared sampling model;
2. policy-tree distributions, parameter learning, alternative EFE equivalence,
   continuous beliefs, infinite horizon, and executable-agent refinement;
3. blanket existence, stationarity, and preservation under arbitrary prior
   mixtures or general stochastic dynamics;
4. multidimensional exponential families, dual affine connections, curvature,
   geodesics, and general constrained maximum entropy; and
5. generic CTMC construction, continuous-state SDE/PDE existence, driven
   nonequilibrium steady states, and an explicit physical free-energy model.

Progress on these targets requires new carriers and witnessed seams, not a
stronger gloss on the five finite families above.
