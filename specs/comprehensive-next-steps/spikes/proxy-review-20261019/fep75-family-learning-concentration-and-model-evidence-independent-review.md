# Issue75 independent semantic review: learning-concentration-and-model-evidence

Source epoch `ef2c99a7ca9b8bd11508c252ec55d01fe9c36699`. Seven exact rows reviewed; cumulative scope120/168. Current narrowed dispositions retained. No repository edit or Lean execution.

## fep-114: Sub-Gaussian Empirical-Mean Tail Bound

Current `formalized` retained; primary `fep114_subGaussian_empiricalMean_tail`.

The pinned Mathlib independent sub-Gaussian sum theorem gives the one-sided probability upper bound at threshold n*deviation. The sample mean is separately defined as sum/n; n>0 is required to rewrite the event as an ordinary mean event.

iIndepFun carries probability normalization: pinned proof explicitly obtains IsProbabilityMeasure from independence. MGF certificates supply all-t exponential integrability/bound, not a consequence of arbitrary finite samples or IID assumptions. Proxy sum0 totalizes the displayed division and can make bound1; n0 also gives a trivial boundary. Non-IID independent variables are allowed.

036 deterministic smoothed-rate identities and actual statistical_convergence SLLN foundations are already present;114 adds an actual finite-sample MGF/independence probability bound. Its relation to036 is only a pairing with smoothed-rate positivity.

Unexecuted positive specification: Use independent centered bounded Bernoulli indicators via the pinned Hoeffding MGF lemma and positive proxy variances; for n>0 rewrite threshold to the centered empirical-mean event.

Unexecuted adverse specification: Dependent identical copies lack iIndepFun. Uncentered bounded observations do not satisfy this zero-centered MGF contract without centering; n0/zero-proxy displayed exponent cannot be interpreted as a nontrivial rate.

## fep-115: Simultaneous Finite-Alphabet Frequency Bound

Current `formalized` retained; primary `fep115_simultaneous_frequency_bound`.

The actual normalized count deviation events are union-bounded over the finite alphabet from supplied per-symbol probability bounds. Nonzero sample count is explicit; no statistical concentration rate or independence is derived.

Neither measurability nor true-distribution identity of target is an explicit input; measureReal union bound applies as stated. For a probability/empirical-frequency interpretation, provide measurable samples and a target law separately. Multi-symbol alphabets do not guarantee distinct deviation events: normalized Boolean frequencies around a matching Boolean target have equal absolute deviations.

042 counts factorize Bernoulli likelihood;115 uses counts as actual deviation sets. Its composition with042 does not derive per-symbol probability budgets.

Unexecuted positive specification: For alphabet Fin3, one uniform observed symbol and target mass1/3 at each symbol, deviation1/2: the three events are distinct singleton outcomes, each probability1/3 and union probability1.

Unexecuted adverse specification: For Bool with complementary normalized target masses, true/false absolute deviations are identical, so union-bound factor2 can be loose and events are not distinct. With per-symbol budget1 the bound may exceed1 and be statistically uninformative.

## fep-116: Finite-Hypothesis PAC-Bayes Loss-Gap Bound

Current `formalized` retained; primary `fep116_finitePACBayes_with_confidence`.

A Gibbs certificate with potential lambda*(populationLoss-empiricalLoss), prior reference and logPartition<=log(1/confidence) gives the finite posterior loss bound via variational duality. It is deterministic conditional on the log-MGF budget.

The theorem contains no sampled-data measure/event or probability>=1-confidence conclusion. Full prior support is carried by the certificate; posterior may have zeros. Positive lambda and confidence in(0,1) are essential for the stated interpretation. Existing058/059 DV identity and actual empirical-risk/Dirichlet count results are separate delivered facts, not a derivation of high-probability PAC generalization.

001 measure-native variational upper bound and059 finite Gibbs/DV bound are neighbors; current116→001 relation deliberately pairs them without identifying native extended and finite real KL.

Unexecuted positive specification: Choose a genuine positive finite Gibbs certificate for explicit losses, verify potential identity and partition budget, and consume the posterior inequality; include a data-independent constant-gap case.

Unexecuted adverse specification: Arbitrary population/empirical losses need not meet the partition budget; without it the confidence expression is not guaranteed. Data-dependent prior or arbitrary lambda selection requires additional probabilistic/selection control.

## fep-117: Posterior-Odds Multiplicative Recursion

Current `formalized` retained; primary `fep117_posteriorOdds_recursion`.

At positive total evidence, positive reference prior and likelihood, Bayes posterior odds equal prior odds times the likelihood ratio. A zero prior remains zero after positive-evidence conditioning.

Favored prior or favored likelihood may vanish and then ordinary odds are0. Unequal positive likelihoods only change initially nonzero favored odds; a zero favored prior remains0. This is a one-evidence recursion, not consistency, learning of missing support or an iterated-data independence theorem.

017 native posterior reconstruction and053 finite Bayes atom reconstruction are distinct scales. Current117→017 is a pairing; it does not prove finite/native posterior equality.

Unexecuted positive specification: Positive equal priors with favored likelihood3/4 and reference1/4 update odds1 to3; an additional zero-prior hypothesis stays absent.

Unexecuted adverse specification: Take favored prior0 and both likelihoods positive unequal: posterior/prior favored odds both0. If reference evidence factor is0, ordinary finite odds interpretation fails even though real division is totalized.

## fep-118: Exponential Posterior Concentration from a Likelihood Gap

Current `formalized` retained; primary `fep118_posteriorGap_concentration`.

For fixed repeated scalar likelihood weights, an assumed per-observation ratio bound yields inferior posterior weight <=priorBad/priorGood*exp(-n*gap). Explicit good weights keep the denominator positive. The exact2-observation witness gives1/10.

The theorem is deterministic algebra on nonnegative unnormalized two-model weights, not probabilistic independence or almost-sure posterior consistency. Gap>=0 permits gap0 with no decaying bound; strict exponential decay as n grows requires gap>0. Repeated identical factors are authored; a heterogeneous data sequence needs product-specific hypotheses.

045 Bernoulli scalar update and117 finite odds supply neighboring identities. Existing Stage1 Dirichlet/Pólya count update, normalization, exchangeability and update consumers are delivered in empirical_risk; this row neither replaces nor completes measure-level Dirichlet conjugacy.

Unexecuted positive specification: Use equal priors, good3/4,bad1/4,gap log3 and n2: actual1/10 while upper bound1/9.

Unexecuted adverse specification: Gap0 and equal likelihoods leave posterior odds unchanged; priorGood0 is excluded. A varying sequence containing adverse likelihood ratios does not meet the fixed repeated factor model.

## fep-119: Bayesian-Mixture Log-Loss Regret Bound

Current `formalized` retained; primary `fep119_mixtureLogLoss_regret`.

Nonnegative mixture evidence contains every component contribution; a positive selected component permits monotonicity of ordinary logarithm, giving component log loss plus -log prior.

Likelihood weights need only be nonnegative, not normalized probability masses or<=1, so loss can be negative for densities or arbitrary weights>1. A selected sequence likelihood can instantiate the bound, but a sequential cumulative-loss equality needs chain-rule factorization and positive conditional evidence. No calibration or asymptotic optimality follows.

026 negative-log product complexity is genuinely connected through the same selected positive factors in the witness.058 variational duality is not needed for this elementary mixture dominance proof.

Unexecuted positive specification: Two models prior1/2 each, likelihood3/4 and1/4 give mixture1/2; selected component penaltylog2 is explicit and finite.

Unexecuted adverse specification: Selected prior0 or likelihood0 excludes the logarithmic theorem even though component lower bound still holds. A positive density>1 yields negative log loss without violating the algebra.

## fep-120: Bayes-Factor Multiplicativity and Model-Evidence Update

Current `formalized` retained; primary `fep120_bayesFactor_multiplicative_update`.

Real-field factorization of two evidence ratios yields multiplicativity and identical sequential versus product-evidence odds update; reference factors are assumed nonzero. Exact3:1 and zero-denominator controls are present.

Numerators and priorOdds may be arbitrary real values in the theorem, and negative reference factors are allowed by nonzero hypotheses. Calling them probabilistic odds requires nonnegative weights and positive denominators. Product factorization may represent conditional sequential evidence; it does not establish unconditional independence.

019 native predictive associativity is only paired with this scalar algebra.117 provides the actual finite posterior-odds operation from which a supported sequential model could be constructed.

Unexecuted positive specification: Use both supported3:1 evidence updates with initial odds1 to obtain final odds9; alternatively specify second evidence conditional on the first.

Unexecuted adverse specification: Zero reference evidence returns0 under totalized division, not infinite odds; negative evidence still satisfies algebra but cannot be probability mass. Correlated evidence is not justified by multiplying unconditional likelihoods.

## Concrete wording corrections

- P3 fep-115 `non_vacuity`: Multiple alphabet symbols do not guarantee distinct deviation events; complementary Boolean normalized frequencies give equal absolute-deviation events. Proposed text: With one uniform Fin3 observation, target mass1/3 at each symbol and deviation1/2, the three count-deviation events are distinct singletons, each with probability1/3, and their union has probability1. Boolean complementary frequencies can instead have identical deviation events; union-bound distinctness is not assumed by the theorem.

- P3 fep-117 `non_vacuity`: Unequal positive likelihoods do not change favored odds when favored prior is zero. Proposed text: Positive equal favored/reference prior masses and likelihoods3/4 versus1/4 update odds1 to3. A separate zero-prior favored hypothesis remains absent despite unequal positive likelihoods. Reference-prior/reference-likelihood and total-evidence support remain explicit.

## Ranked bounded follow-ups

1. 114→115 actual finite frequency concentration: Center measurable indicator observations, instantiate pinned hasSubgaussianMGF_of_mem_Icc with independent samples, obtain both tails then finite union. Existing114 one-sided theorem and115 union theorem are delivered; the missing content is their common-sample supported specialization. Estimate: 1–3 days.

2. 116 sampled-data confidence theorem: Introduce explicit sample probability law and measurable losses, prove an expectation/exponential budget, use Markov inequality for an event with failure<=confidence and derive simultaneous posterior bound on that event. Preserve prior independence/data-dependence restrictions. Existing conditional theorem alone is not high-probability generalization. Estimate: 2–5 days bounded finite setting after pinned API probe.

3. 117/118/120 sequential supported model: Use existing finite posterior/kernel operations to connect scalar repeated/product evidence updates to actual conditional likelihoods; allow heterogeneous positive factors with product gap bounds. Existing Dirichlet count Stage1 and empirical-risk bridges remain intact, not reimplemented. Estimate: 1–3 days.

## Source bindings and limits

Adjacent JSON records all exact primary/support/boundary statements, canonical body and file hashes, complete current maturity and novelty records, touching relations and limitations. These14 additional rows do not establish broad Issue75/scientific/terminal acceptance. Remaining48 topics and active acceptance dependencies remain open.
