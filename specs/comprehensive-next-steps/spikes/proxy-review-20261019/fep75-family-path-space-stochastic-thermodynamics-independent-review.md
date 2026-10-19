# Issue75 independent semantic review: path-space-stochastic-thermodynamics

Exact source epoch `ef2c99a7ca9b8bd11508c252ec55d01fe9c36699`. Seven rows reviewed; cumulative scope106/168. All current narrowed dispositions retained. No repository edits or compilation.

## fep-093: Forward and Reverse Finite Path-Law Ratio

Current disposition `formalized` retained; primary `fep093_forward_reverse_pathLaw_ratio`.

A supported denominator reconstructs forward mass by division cancellation; normalization and involution are explicit carrier fields. Forward support is not needed for this primary identity. The reversal need not exchange laws.

FinitePathProtocol by itself supplies two arbitrary normalized laws and an independent involution. Actual homogeneous Markov path masses, normalized laws, finite reversal and endpoint marginal identities are already implemented in path_thermodynamics; do not label them absent. No continuous-path existence or microscopic reverse-process identification follows.

010 is native reversible-kernel stationarity;025 oriented currents. The093 relation pairs the finite ratio with native identity reversibility, not an equivalence of dynamic carriers.

Unexecuted positive specification: Boolean masses forward(1/4,3/4), reverse(3/4,1/4), with Bool.not reversal produce ratios1/3 and3 and a genuine swap.

Unexecuted adverse specification: Identity reversal and unequal laws are permitted; this does not imply exchange or entropy-production antisymmetry. At zero reverse mass the totalized ratio is0 and reconstructing positive forward mass fails.

## fep-094: Entropy Production as Path KL

Current disposition `structural_proxy` retained; primary `fep094_entropyProduction_as_pathKL`.

Entropy production equals finiteKL by definition; nonnegativity is proved for that finite carrier. Under full support it equals the forward expected natural-log likelihood ratio. Retain structural_proxy.

finiteKL is the project's totalized real expression, not native extended KL on singular laws. Entropy production/log ratios are dimensionless nats unless additional physical constants/units are supplied. Existing Markov expected edge-affinity and boundary entropy decompositions, reversible endpoint-KL drop and explicit irreversible3-cycle are delivered extra content.

049 is a supplied conductance/force quadratic;014 native extended KL. The current relation is a pairing and does not identify either with arbitrary physical entropy production.

Unexecuted positive specification: Use unequal full-support Boolean protocol and consume strict positivity plus expected-log-ratio equality.

Unexecuted adverse specification: Disjoint point masses expose finite totalized KL versus native infinite divergence; unsupported real log-ratio identities must not be applied. A physical heat interpretation additionally needs local detailed balance with declared units.

## fep-095: Detailed Fluctuation Symmetry

Current disposition `conditional_proxy` retained; primary `fep095_detailedFluctuation_symmetry`.

For positive forward/reverse masses, exp(log ratio) reconstructs the forward mass. Reversal antisymmetry further requires both exchange laws; involution alone is insufficient.

The main identity is likelihood-ratio algebra, not a derived law of microscopic reversibility. The stored irreversibleBoolProtocol has identity reversal and unequal laws; it proves positive production but does not satisfy the exchange hypotheses. A separate swapped-law protocol can.

093 adds ratio reconstruction without forward positivity;095 adds supported exponential identity and optional exchange-specific antisymmetry. Native010 stationarity is only paired, not used to derive exchange.

Unexecuted positive specification: Use forward true3/4,false1/4, reverse masses swapped and Bool.not reversal; sigma(true)=log3 and sigma(false)=-log3.

Unexecuted adverse specification: Take the same unequal masses with identity reversal: sigma at a point is nonzero and does not become its negative on reversal.

## fep-096: Integral Fluctuation Theorem

Current disposition `formalized` retained; primary `fep096_integralFluctuation_theorem`.

Finite forward expectation of exp(-log(forward/reverse)) is reverse-law total mass1. Both strict-support hypotheses are explicit and sufficient; reversal does not enter the proof.

This is a normalized finite change-of-measure identity, not singular-path or continuous-time stochastic-process existence. Full support is stronger than necessary but cannot be silently removed from the current theorem.

095 is pointwise reconstruction;096 sums the inverse reweighting.049 flux/force expression remains an independent pairing.

Unexecuted positive specification: The swapped unequal Boolean laws yield forward-weighted exponentials1/4+3/4=1.

Unexecuted adverse specification: With forward point mass at true and reverse uniform, the totalized forward expectation is1/2, not1; null forward atoms carry reverse mass omitted by the expectation.

## fep-097: Finite Jarzynski Equality

Current disposition `conditional_proxy` retained; primary `fep097_finiteJarzynski_equality`.

The primary extracts exponentialWorkAverage=exp(-beta*deltaF) from an explicitly assumed normalization with beta>0. This is accurately conditional_proxy, not a derivation of that physical premise.

The foundation already derives normalization and Jarzynski from the per-path HasCrooksRelation, constructs a nonconstant Boolean work witness and proves normalization without Crooks is possible. Defining work=deltaF+sigma/beta supplies a formal Crooks instance but does not identify mechanical work. Beta has inverse-energy meaning only with explicit unit convention; beta0 is zero inverse temperature, conventionally an infinite-temperature limit, not zero temperature.

013 algebraic Helmholtz difference and097 exponential work remain separate in the bridge; no equality of deltaF with that Helmholtz difference is proved.

Unexecuted positive specification: Reuse irreversibleBool_crooks at beta1,deltaF0 and work ±log3, then finiteJarzynski_of_crooks.

Unexecuted adverse specification: Reuse jarzynski_without_crooks (zero work normalizes but fails pathwise relation) and irreversibleForward_unitWork_not_jarzynski. Do not assume arbitrary supplied work satisfies normalization.

## fep-098: Local Detailed Balance and Current Cancellation

Current disposition `formalized` retained; primary `fep098_localDetailedBalance_currentCancellation`.

Detailed balance law(i)K(i,j)=law(j)K(j,i) makes every oriented current0. A zero reverse transition makes localAffinity0 under Lean's totalized real division/logarithm.

This is finite detailed-balance current cancellation, not generic local thermodynamic heat balance, PDE Fokker–Planck existence or a meaningful finite physical affinity at a one-way edge. Positive flux support is needed for ordinary log-affinity interpretation.

025 is arbitrary antisymmetric matrix flow;098 instantiates current from a normalized law/kernel and assumes detailed balance. Existing current/affinity path decomposition is already implemented.

Unexecuted positive specification: Use a full-support symmetric two-state chain and uniform law; both oriented currents vanish.

Unexecuted adverse specification: Use the existing positive stationary biased3-cycle: it is invariant but not reversible and has nonzero edge current. A one-way edge yields the explicitly labeled totalized affinity0 rather than extended +infinity.

## fep-099: Reversible-Chain One-Step KL Dissipation

Current disposition `formalized` retained; primary `fep099_reversibleChain_oneStep_KL_dissipation`.

Full-support finite-channel DPI plus detailed-balance stationarity proves a one-step KL nonincrease. The identity equality theorem is separate and imposes no strict transition support. A distinct supplied unequal path-law witness has positive production.

On a state space with at least2 elements identity has zero off-diagonal entries and does not instantiate hKernel. Positive path production alone does not certify a nonreversible transition process; the separate biasedCycleKernel supplies that stronger finite-chain witness. Existing entropyProduction_markov_reversible_KL_drop and composed one-step reduction identify actual path production with endpoint KL loss at every supported finite horizon.

010 provides stationarity;014 nativeKL. The original composition is a conjunction, whereas the separate fep099_markov_path_KL_drop_reduction is a genuine same-carrier reduction. No strict contraction, rate or infinite-time entropy result is claimed.

Unexecuted positive specification: Use a strictly positive symmetric Boolean mixing kernel with stationary uniform and nonuniform positive actual law; compare one-step KL. For actual nonreversibility reuse biasedCycle_not_reversible and horizon-positive production.

Unexecuted adverse specification: Identity equality lies outside the main theorem support class for multi-state spaces. At actual=stationary even a strictly positive nonidentity kernel has equality, so nonidentity alone does not yield strict dissipation.

## Concrete wording corrections

- P3 fep-097 `non_vacuity`: Zero beta means zero inverse temperature, not zero physical temperature. Proposed text: The actual nonconstant Boolean Crooks work witness satisfies the normalization at beta=1 and deltaFreeEnergy=0. Positive beta excludes the zero inverse-temperature parameter boundary; no physical temperature or unit identification is inferred without an explicit convention.

- P3 fep-099 `non_vacuity`: The identity kernel equality boundary is outside the strictly positive-transition main theorem on multi-state carriers; unequal arbitrary path laws alone do not certify irreversible transition dynamics. Proposed text: A strictly positive symmetric mixing kernel supplies an instance of the main dissipation theorem. The separately proved identity equality lies outside its positive-transition class on multi-state carriers. Unequal full-support Boolean path laws prove positive path divergence; the existing stationary biased three-cycle separately proves nonreversibility and positive production at every positive finite horizon.

## Ranked bounded follow-ups

1. source-bound positive/adverse consumer renewal: Reuse existing Markov path normalization, Crooks witness, reversible endpoint KL drop and stationary biased-cycle horizon theorems. No missing finite-path implementation should be invented. Estimate: 0.5–1.5 days.

2. support-sensitive finite path expectation: Existing relative-support finiteKL identity is already used by ErasureModel. A new supported likelihood identity may weaken full-support to actual forward support, with reverse lost mass accounted explicitly for the integral fluctuation identity. Estimate: 1–3 days.

3. native extended path-KL embedding: Reuse existing finite/native weighted-Dirac ownership rather than creating another probability carrier; prove finite path KL agrees with native KL only with explicit support and conversion hypotheses. Continuous path/PDE limits need a separate measure/process construction, not a routine completion of093–099. Estimate: 2–5 days bounded embedding; continuous-path work requires separate research spike.

## Bindings and limits

The adjacent JSON binds exact canonical body and source-file hashes, all primary/support/boundary statements, current complete maturity and novelty records, and touching relations. No general physical, causal, state-estimation, terminal or full Issue75 acceptance follows. Remaining62 topics and active integration/acceptance dependencies remain open.
