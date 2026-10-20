# Issue75 independent semantic review: closed-loop-policy-trees-and-efe

Exact source epoch `ef2c99a7ca9b8bd11508c252ec55d01fe9c36699`; seven rows reviewed, cumulative scope134/168. Current narrowed dispositions retained. No repository edits or compilation.

## fep-128: Observation-Contingent Policy-Tree Recursion

Current `formalized` retained; primary `fep128_policyTreeValue_node`.

A depth-indexed tree chooses an action then a distinct continuation per observation; node value is stageCost at remaining depth plus observation-weighted continuation, leaf value0. Primary recursion is definitional but exposes an actual contingent carrier.

PolicyTreeModel supplies normalized observation laws, arbitrary deterministic belief updates and arbitrary real stage costs. It does not require Bayesian update soundness or physically derived observations/costs. Finiteness is explicit; no discount/stationarity is assumed.

071 already supplies sophisticated observation-contingent recursion;128 additionally makes the depth-indexed tree object explicit. The current bridge conjoins two supplied models rather than asserting their equality.

Unexecuted positive specification: Use boolFeedbackTree depth2: its continuation picks the observed Bool; compare leaf0 and terminal mismatch costs.

Unexecuted adverse specification: An update ignoring observations satisfies generic PolicyTreeModel, so generic recursion cannot imply Bayesian filtering. Missing observations/empty action at positive depth is a carrier boundary, not an infinite planning theorem.

## fep-129: Finite Policy-Tree Bellman Minimum

Current `formalized` retained; primary `fep129_optimalTreeValue_eq_min`.

finiteArgmin selects an action attaining the stage-plus-weighted-optimal-continuation objective; supporting inequality compares it to every action. This is actual finite Bellman minimization, not just an argmin name.

Actions finite/nonempty; observation weights nonnegative normalized; belief/update/costs supplied. Stage index is remaining depth, not automatically elapsed time. Neither Bellman contraction nor infinite-horizon stationary policy is proved, and minimizers need not be unique.

033 is deterministic discounted ENNReal rollout,071 a real sophisticated recursion.129 is finite action minimization in the explicit tree setting; current relations keep these value carriers separate.

Unexecuted positive specification: One-stage Boolean actions with costs0 and1 give selected value0 and alternative comparison; tied costs permit any minimizing action.

Unexecuted adverse specification: An empty action type cannot meet the existence contract. Negative stage costs are allowed at finite depth and do not by themselves invalidate minimization, but no infinite-horizon boundedness follows.

## fep-130: Optimal Finite Policy-Tree Existence

Current `formalized` retained; primary `fep130_exists_optimalPolicyTree`.

The recursively built optimalPolicyTree attains optimalTreeValue and is below every alternative at equal finite depth. Tree carrier finiteness is separately established. This is a real attaining existence result.

Construction is noncomputable finiteArgmin/classical choice, not a certified efficient executable planner. No uniqueness, infinite-depth optimum, complete continuous-belief simplex enumeration or empirical plan adequacy follows. The theorem does not just assert a supplied optimum.

008 is a fixed finite one-step argmin;130 lifts finite selection through every observation branch and compares all finite trees.

Unexecuted positive specification: For boolFeedbackModel at depth2, the explicit feedback tree value0 and nonnegative mismatch cost provide a nontrivial attaining minimum; generic theorem compares all same-depth trees.

Unexecuted adverse specification: Tied action costs allow multiple distinct optimal trees. Unbounded horizon with negative per-step costs has no finite real minimum promised by this theorem.

## fep-131: Open-Loop Plan Embedding into Policy Trees

Current `formalized` retained; primary `fep131_openLoopEmbedding_value`.

OpenLoopPlan embeds by reusing one continuation across all observation branches; its recursive value equals the corresponding tree value at the same model, belief and depth.

Actions ignore observation history, but the model's belief update and expectation still follow observations during evaluation; open-loop does not mean freeze belief. Same-depth/model hypotheses matter.

033 rollout is not automatically this open-loop expected-belief recursion; current relation pairs it, whereas131 gives an actual embedding into128 carrier.

Unexecuted positive specification: Use a two-action depth2 plan and at least two observations; show identical action continuation on both branches while belief-dependent costs remain evaluated.

Unexecuted adverse specification: A feedback tree choosing opposite second actions for different observations is not the image of a single fixed second-action plan. It may nevertheless have equal value in an observation-irrelevant model.

## fep-132: Closed-Loop Policy-Tree Dominance over Open Loop

Current `formalized` retained; primary `fep132_optimalTree_le_openLoop`.

The globally minimizing finite tree is no worse than any value-preserving embedded same-depth open-loop plan. This follows from inclusion of that plan in the larger policy class.

This is weak dominance for one cost/observation/update model; strict advantage is possible, not universal. Finitely many actions and finite horizon remain; the depth<depth+1 supporting theorem merely records natural-depth arithmetic and adds no planning evidence.

071 also had finite feedback-vs-fixed-plan content;132 now has a universal same-depth plan embedding/optimal-tree dominance, not an infinite-horizon POMDP claim.

Unexecuted positive specification: Use134 to show0<1/2 strict advantage for the explicit feedback example.

Unexecuted adverse specification: At depth0, constant costs or observation-irrelevant continuation, equality holds. Altering model/horizon between sides breaks the comparison guarantee.

## fep-133: Treewise Expected-Free-Energy Decomposition

Current `formalized` retained; primary `fep133_policyTree_efe_eq_risk_add_ambiguity`.

Stage costs are actual finite generative-model expectedFreeEnergy and actual risk+ambiguity, with predictedOutcome observation laws and full support. The existing one-step equality is lifted branchwise; all tree values and corresponding minima agree.

EFEPolicyTreeModel generative is supplied separately for each belief and update is arbitrary. FullSupport does not require the next generative model to be the Bayesian posterior of the previous one. Existing BayesianBeliefModel/update_filtered and bayesEFETree_eq_pomdpTree, bayesSophisticatedValue_eq_optimalTree, bayesRiskAmbiguity_eq_sophisticated provide a genuine supported specialization; do not claim that bridge absent.

021 ENNReal truncated EFE is only paired via ofReal with explicit balance;133 uses a real, model-derived EFE identity and true finite tree induction. No scientific adequacy follows.

Unexecuted positive specification: Use an explicitly full-support finite generative family at every reachable belief and a nontrivial contingent tree; consume equality for the same tree then equal optima. Separately instantiate the existing Bayesian carrier theorem with its full-support premise.

Unexecuted adverse specification: Keeping the prior after informative observations is allowed by the generic update field but is rejected as Bayesian by the existing boolKeepPrior_not_bayesian control. Support alone cannot certify Bayes soundness. The sparse Boolean mismatch witness does not automatically satisfy this full-support EFE contract.

## fep-134: Strict Boolean Feedback Advantage

Current `formalized` retained; primary `fep134_boolFeedback_strictlyBetter`.

The concrete depth2 Bool feedback continuation changes its second action with the first observation, giving value0 against1/2 for each fixed second action in boolOpenLoopPlan. This is exact nonvacuous possible feedback advantage.

The fair first observation and terminal mismatch objective are authored; generic boolFeedbackModel is a supplied belief/update model. Existing boolBayes_rederives_feedbackWitness separately realizes the same values via an actual finite Bayesian filter, with support/scope specific to that construction. Do not describe all content as merely an unsupported toy, or identify it with every full-support EFE policy.

071 supplied feedback example is a neighbor;134 owns the explicit tree and continuation-change fact. The Bayesian perception-action foundation adds a substantive actual carrier bridge without proving empirical benefit.

Unexecuted positive specification: Consume actual continuation inequality and0 versus1/2 values; reuse the existing filtered Boolean witness and update-agreement theorem as a separate source-qualified specialization.

Unexecuted adverse specification: If observation conveys no useful variable for terminal cost or both actions have equal cost, strict feedback advantage disappears. A keep-prior update fails the delivered Bayes agreement control.

## Concrete wording corrections

- P3 fep-133 `assumption_review`: The generic full-support EFE model still permits arbitrary belief updates; the existing Bayesian specialization should be named separately. Proposed text: Every belief-indexed generative model satisfies FullSupport and supplies actual model-derived EFE, risk and ambiguity. The generic update is an arbitrary function and need not be the preceding model's Bayesian posterior. The separate BayesianBeliefModel/update_filtered specialization and its policy-tree/POMDP/risk-ambiguity bridges establish that stronger filtered interpretation under their explicit support premises. All horizons/carriers remain finite; empirical adequacy is not established.

## Ranked bounded follow-ups

1. 133/134 current Bayesian consumer renewal: Reuse existing bayesEFETree_eq_pomdpTree, bayesSophisticatedValue_eq_optimalTree, bayesRiskAmbiguity_eq_sophisticated and boolBayes_rederives_feedbackWitness; no duplicate carrier or missing-bridge claim. Keep full-support EFE specialization separate from sparse Boolean filtered mismatch witness. Estimate: 0.5–1.5 days.

2. finite tree minimizer/embedding boundary consumers: Instantiate nontrivial tied/strict action objectives; preserve tree depth and same model in comparisons. An actual efficient executable algorithm/complexity certificate would be a separate addition to noncomputable finiteArgmin construction. Estimate: 0.5–1.5 days consumers; runtime algorithm scope separate.

3. continuous belief or infinite horizon research boundary: Requires actual reachable-belief or measurable policy carrier and matching value bridge; infinite horizon needs discounted/other convergence and boundedness hypotheses. Finite existence does not supply these. Existing finite Bayesian reachable-belief machinery must be reused before proposing a new carrier. Estimate: bounded finite specialization1–3 days; continuous/infinite extension requires a separate library feasibility spike.

## Bindings and limits

Adjacent JSON retains exact primary/support/boundary statements, complete maturity and novelty records, touching relations, canonical body hashes and source-file SHA256 values. These14 rows do not establish broad Issue75/scientific/terminal acceptance. Remaining34 topics and active dependencies stay open.
