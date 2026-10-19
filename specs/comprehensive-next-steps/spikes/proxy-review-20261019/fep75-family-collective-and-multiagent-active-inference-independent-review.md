# Issue75 independent semantic review: collective-and-multiagent-active-inference

Source epoch `ef2c99a7ca9b8bd11508c252ec55d01fe9c36699`. Seven exact rows reviewed; cumulative scope120/168. Current narrowed dispositions retained. No repository edit or Lean execution.

## fep-107: Product-Agent Generative Law

Current `formalized` retained; primary `fep107_productAgent_generative_mass`.

The product prior and coordinatewise product observation kernel give pointwise product generative mass and normalized observation rows. This is a genuine finite product construction, not an empirically inferred independence fact.

Independence is authored at both prior and conditional mechanism. No actions, interacting beliefs, shared observations, communication or empirical collective agency are present in this row. Correlated priors can break the generative factorization even if both kernels remain product.

027 is native hierarchical law construction and019 native sequential prediction; the current bridge pairs product mass with native hierarchy normalization, not an embedding equality.

Unexecuted positive specification: Use two fair Boolean priors with deterministic identity observation kernels; each matching four-coordinate atom has mass1/4 and observation rows normalize.

Unexecuted adverse specification: Replace the product prior by a diagonal correlated Boolean joint: the two matched generative factors no longer reconstruct its mass1/2 using marginal products1/4.

## fep-108: Additive Collective Variational Free Energy

Current `formalized` retained; primary `fep108_collectiveVFE_additive`.

Finite KL of product actual/reference laws plus the expectation of an additive cost equals the sum of individual objectives. Actual laws may have zeros; the reference factors must have full support.

The named VFE is defined as KL(actual||reference)+expected supplied cost. No posterior/surprisal relation, physical energy units or optimization process follows without another bridge. Arbitrary real costs may be negative and cost offsets can cancel KL.

039 is arbitrary four-block scalar additivity;001 is measure-native variational upper bound. This row proves product KL/expectation additivity, with no identity to001 implied by naming.

Unexecuted positive specification: Use nonuniform actual Boolean factors, uniform positive references and positive nonconstant costs with positive actual support, so both component KL and expectation terms are nonzero.

Unexecuted adverse specification: A correlated diagonal actual joint against a uniform product reference has extra dependence KL that is absent from the sum of marginal KLs. A cross-coordinate interaction cost also defeats the additive formula.

## fep-109: Independent-Agent Expected-Free-Energy Additivity

Current `formalized` retained; primary `fep109_independentEFE_additive`.

The defined risk-plus-expected-supplied-ambiguity objective is additive for product predictive/preference laws and additive ambiguity. Full preference support enables ordinary finite KL product decomposition.

Ambiguity is an arbitrary real statewise function here, not proved to be an observation-kernel conditional entropy. The foundation active_inference already has actual model-derived risk/ambiguity and epistemic identities; those require a separate model-specific common-carrier integration before attaching them to these supplied functions.

021 is ENNReal truncated pragmatic-minus-epistemic balance and041 native posterior information gain. The current relation pairs the real additivity identity with021 under its own balance premise, not equality of the objectives.

Unexecuted positive specification: Use distinct positive predictive/preference factors and explicitly nonnegative nonconstant ambiguity costs positive on predictive support.

Unexecuted adverse specification: Correlated predictive joint against product preferences includes dependence risk; nonadditive ambiguity creates an interaction expectation. A supplied negative ambiguity need not have an entropy interpretation.

## fep-110: Unit-Weight Product-of-Experts Pool Normalization

Current `formalized` retained; primary `fep110_unitWeightProductOfExpertsPool_normalized`.

A strictly positive pointwise-product normalizer defines a normalized law with masses proportional to left*right. The exponents are1 and1; this differs from equal-weight logarithmic pooling with exponents1/2,1/2.

Positive overlap excludes disjoint supports but does not force the pool to differ from both inputs. Existing linearPool and logPool KL decompositions, minima and uniqueness are delivered in the same foundation under their explicit support/weight contracts. The logPool exp(sum weighted logs) definition has totalized behavior at zero expert mass; its geometric/KL interpretation requires the theorem full-support premises.

028 softmax and031 Gibbs normalization are nearby normalizers, not equivalences or external Bayesian pooling. Keep unit-weight product distinct from the separately available normalized weighted log-pool.

Unexecuted positive specification: Bool true masses3/4 and2/3 yield product true1/2,false1/12,Z7/12 and pooled true6/7, different from both inputs.

Unexecuted adverse specification: Uniform left with nonuniform right produces pool=right despite distinct overlapping laws. Disjoint opposite point masses give Z0 and cannot construct this pool.

## fep-111: Consensus Mass Conservation

Current `formalized` retained; primary `fep111_consensus_pointwise_mass_conserved`.

The fixed symmetric stochastic mixing matrix[[3/4,1/4],[1/4,3/4]] preserves the sum of two agent masses at every state. Each output is a FiniteLaw, hence combined total2.

Normalization alone does not establish pointwise two-agent conservation; doubly stochastic structure of this specified matrix does. It does not itself prove convergence, correctness of beliefs or arbitrary-network conservation.

025 antisymmetric total divergence conservation and046 stick-breaking allocation are different conservation carriers; the present bridge is a pairing with025, not a dynamical equivalence.

Unexecuted positive specification: Opposite Boolean point masses become true masses3/4 and1/4, preserving initial combined true mass1 and moving mass between agents.

Unexecuted adverse specification: A merely row-stochastic matrix with both rows copying agent1 normalizes both output laws but generally changes the combined pointwise mass.

## fep-112: Contractive Belief-Consensus Convergence

Current `formalized` retained; primary `fep112_consensus_converges`.

Under the fixed synchronous two-agent operator, every absolute atomwise difference is multiplied by1/2, so its nth iterate equals(1/2)^n times its initial value and tends0. The opposite-Boolean witness remains positive after one step.

This row proves disagreement convergence, not that the shared limit is a true external-state belief. Existing foundation Dobrushin spread contraction, asymmetric3-agent positive-scrambling witness and identity noncontraction control already extend beyond the fixed matrix; do not call all general finite mixing absent. A theorem for arbitrary time-varying networks/agent belief laws still needs normalization and uniform mixing hypotheses.

048 half-map convergence and020 symmetric two-state recurrence share scalar contraction structure. Current edge conjoins these instances rather than proving a general network theorem.

Unexecuted positive specification: Reuse the actual opposite-Boolean strict witness; combine conserved pointwise sums with vanishing gaps to specify convergence of each agent to the initial arithmetic mean.

Unexecuted adverse specification: Identity mixing is already proved not to contract; a swap matrix can perpetually alternate. Row stochasticity alone cannot imply convergence.

## fep-113: Coupled-Agent Potential Descent

Current `formalized` retained; primary `fep113_coupledPotential_strict_descent`.

The atomwise squared difference contracts by1/4 under the same fixed consensus step and is strictly smaller precisely at an explicitly separated atom.

This is a quadratic disagreement potential, not a general coupled VFE or game potential. Equal mass at one atom has0 potential there even if agents differ elsewhere; no empirical multiagent performance follows.

112 is absolute gap convergence;113 is squared-gap one-step strict descent.032 scalar quadratic energy descent is paired at its own stable-step range, not a new collective objective derivation.

Unexecuted positive specification: Opposite Boolean point masses have potential1 at true and post-step1/4, with both values positive.

Unexecuted adverse specification: Identical laws give equality0. Arbitrary noncontractive coupling can conserve total mass without decreasing disagreement.

## Concrete wording corrections

- P3 fep-110 `non_vacuity`: Distinct overlapping laws can pool to one input, e.g. one input uniform. Proposed text: For Boolean laws with true masses3/4 and2/3, the product normalizer is7/12 and the pool true mass is6/7, different from both inputs. Disjoint opposite point masses have zero normalizer and are excluded. Distinct overlap alone does not guarantee both inputs change.

## Ranked bounded follow-ups

1. 110 concrete pooling/source bindings: Reuse existing positive-normalizer unit-weight pool and weighted KL-optimal linear/log-pool theorems. Add typed6/7 and uniform-input/disjoint-support consumers, retaining exponents and full-support requirements; do not duplicate existing variational pooling. Estimate: 0.5–1 day.

2. 112 consensus limit law/global finite metric: Combine pointwise sum conservation and exact gap recurrence to prove each agent converges to arithmetic mean; sum finite atomwise gaps to obtain a named finite L1/TV rate. Existing Dobrushin spread inequality and3-agent example are already present. Estimate: 1–2 days.

3. 109 actual model-derived ambiguity specialization: Use existing active_inference generative-model ambiguity/risk and actual product kernels; prove ambiguity additivity/identify supplied cost functions on matching state-observation carriers. Explicit finite support remains; no empirical multiagent dynamics. Estimate: 2–4 days.

## Source bindings and limits

Adjacent JSON records all exact primary/support/boundary statements, canonical body and file hashes, complete current maturity and novelty records, touching relations and limitations. These14 additional rows do not establish broad Issue75/scientific/terminal acceptance. Remaining48 topics and active acceptance dependencies remain open.
