# Issue75 independent semantic review: standalone-efe-formalizations

Exact EF source epoch; family roster verified. 6 rows reviewed. Static family coverage now168/168, without broad acceptance. Current dispositions retained for exact statements; listed metadata corrections remain required.

## fep-156: Planning as Inference: the EFE Policy-Selection Bridge

Primary `fep156_boltzmann_control_posterior_minimizes_efe`; current `formalized` retained for exact narrowed statement.

For full-support finite prior and precision gamma>0, the Boltzmann law is the unique minimizer over probability laws of expected supplied cost plus KL(Q||prior)/gamma; optimum value is-logZ/gamma. Separate declarations establish deterministic EFE argmin/risk+ambiguity agreement and finite tree value agreement.

The main cost is an arbitrary real function, not automatically derived EFE. Deterministic finiteArgmin of EFE is not the Boltzmann probability law and does not attain the same KL-regularized objective value. The owner already has supported sparse-prior extensions, negative-precision maximum and zero/unsupported controls; released row is the full-support positive-precision case.

008 deterministic finite minimization,028 normalized softmax and059 Gibbs/DV objective are distinct operations linked here under explicit premises;133 tree agreement remains finite/model-derived.

UNEXECUTED positive specification: Uniform two-policy prior with costs0,1 and gamma1 gives a nondegenerate Boltzmann law; compare its regularized optimum-log((1+exp(-1))/2) with deterministic zero-cost selection penaltylog2.

UNEXECUTED adverse specification: Negative precision reverses divided-objective optimization and unsupported candidates can exploit totalized KL; actual source controls already show these boundaries. Zero precision removes the KL penalty and does not have the same unique minimum reading.

## fep-157: The Perception-Action Loop as a Closed-Loop Active-Inference Theorem

Primary `fep157_loop_invariant_surprisal_bound`; current `formalized` retained for exact narrowed statement.

Primary is a single positive-evidence outcome surprisal bound by perceptionVFE, exact VFE=surprisal+KL to its filtered belief, plus selected-policy EFE=risk+ambiguity at the filtered model. Supporting finite KL chain decomposition bounds an observation-averaged posterior KL, native DPI bounds predictive KL, and Dobrushin bounds TV under an explicit coefficient.

There is no declared trajectory sum or theorem that each realized observation reduces surprisal/KL. The named fixed-point theorem only states that flat EFE across policies makes policyPosterior=prior; no iterated-loop fixed-point convergence is proved. Dobrushin strict contraction needs coefficient<1, not merely a supplied bound. Existing Bayesian planning/update and exact feedback specializations are real additional content, but do not establish the stronger metadata claims.

017 posterior/forward filter and021/071 model-derived policy planning are genuinely connected through actual operations; aggregate loop monotonicity and accumulated expected-EFE accounting require a new trajectory-level theorem, not compilation.

UNEXECUTED positive specification: Use a full-support likelihood/prior instance to consume the exact averaged chain rule and one-step VFE gap; separately take constant policy EFE for posterior=prior.

UNEXECUTED adverse specification: Individual observations can increase posterior KL even when its predictive average is bounded. An identity transition admits coefficient1 and no strict TV decrease. Flat policy EFE is not proof of a dynamical fixed point.

## fep-158: Bayesian Model Reduction

Primary `fep158_reduction_free_energy_monotone`; current `formalized` retained for exact narrowed statement.

For weights<=1 and positive maskedEvidence, the unnormalized masked evidence is<=full predictive evidence, hence its negative log free energy is>=the full one. Normalizing the masked prior instead yields maskedEvidence/Z, a different quantity that can exceed full evidence. Posterior reweighting/reconstruction and Gibbs optimizer gap are separately proved.

Posterior clauses require nonnegative weights, positive prior mask normalizer and positive conditioned evidence; the primary free-energy inequality itself only assumes upper weight bound plus positive masked evidence. Finite carriers are used, not arbitrary finite measure spaces. Gaussian fixed-variance log ratio and Gibbs free-energy/KL gap do not identify reduction with general DV/statistical model selection.

026 scalar log complexity and058/059 Gibbs duality are bounded neighboring facts.158 supports exact finite reweighting and specified evidence comparisons, not the reversed sentence that masking never lowers evidence.

UNEXECUTED positive specification: Uniform two-parameter prior and likelihood(.9,.1), mask(1,0): full evidence.5, masked unnormalized.45 (lower), normalized reduced-prior evidence.9 (higher). This separates the two meanings.

UNEXECUTED adverse specification: No universal monotonic direction for normalized reduced-model evidence follows from mask<=1. A mask eliminating all evidence fails positivity and cannot support ordinary logarithmic posterior reconstruction.

## fep-159: EFE and Entropy-Production Time-Scale Separation

Primary `fep159_epistemic_gain_bounded_by_affinity`; current `formalized` retained for exact narrowed statement.

For full-support Bool belief, KL to the two-state invariant law is bounded by productionRate/decayRate; a specific perfect-observation, policy-independent semigroup model has EFE equal to the evolved information gap. The gap has an explicit squared-exponential upper bound, and a supported positive-time source-target slice has exact production(1-rho)*productionRate/decayRate.

epistemicGain here is KL(evolved belief||stationary), not generic epistemic mutual information. Every policy shares the same transition; likelihood is identity and preferences stationary. The declared fastRelaxation theorem proves for each positive tolerance there exists one positive epsilon attaining the bound, not a forall sufficiently-small epsilon/Tendsto statement. The exponential envelope makes such a stronger result feasible but it has not been stated in these declarations.

149–155 exact semigroup and094 finite path production are actually instantiated. This is one-slice reweighting, not arbitrary horizon path action, physical time-scale separation or generic policy-dependent information gain.

UNEXECUTED positive specification: Choose full-support nonstationary belief for positive current-affinity production; use exact scaling bound and one-slice identity. Stationary belief gives equality0=0 only.

UNEXECUTED adverse specification: At stationarity generic perfect-observation mutual information can be positive although the KL gap/production are0; thus universal MI<=production/decay is false. Existence of one good epsilon is weaker than a right-limit theorem.

## fep-160: Helmholtz–Ao Decomposition of Nonequilibrium Steady Currents

Primary `fep160_aoDecomposition`; current `formalized` retained for exact narrowed statement.

Every real rate field splits algebraically relative to a positive law into reversible symmetricPart and law-weighted skew circulationPart. Current=2*law*circulation, reversible current0 and detailed-balance iff circulation0 are proved. Actual finite-generator stationarity gives zero node divergence; directed3-cycle is a nonzero-current stationary witness.

Stationarity is not needed for algebraic splitting but is needed for stationary divergence. Law-weighted skewness is not ordinary matrix skewness except with uniform law. ForceSplit requires positive opposing rates and positive law; one-way cycle does not instantiate its log-affinity premise. Circulation entries need not be nonnegative generator rates;166 explicitly shows a negative entry. No continuum SDE/PDE or physical Helmholtz identity follows.

013 Helmholtz U-TS is deliberately distinct from Ao potential-log stationary mass;161 plain skew algebra and160 weighted reversible split require exact carrier identification before combination.

UNEXECUTED positive specification: Reuse stationary directed3-cycle current1/3 and circulation1/2; separately use bidirectional supported rates for forceSplit.

UNEXECUTED adverse specification: A positive-law arbitrary rate field can fail stationarity; then current divergence need not vanish. Do not apply ordinary Q-transpose=-Q cancellation to an unscaled law-weighted-skew field.

## fep-166: Uniqueness of the Law-Weighted Reversible/Circulation Split

Primary `fep166_split_unique`; current `formalized` retained for exact narrowed statement.

Given a positive finite law and any competing split rate=S+A with weighted-reversible S and weighted-skew A, both parts equal the canonical split. A concrete2-state field exercises all predicates with circulation1/2 and-1/4.

No stationarity, row-sum-zero generator or nonnegative circulation is assumed. This is uniqueness of a weighted linear algebra decomposition, not uniqueness of a stochastic dynamics/NESS/physical Ao ansatz. Negative circulation makes a sum-of-independent-Markov-generators reading invalid.

160 constructs the split;166 proves competing-pair uniqueness, a substantive addition.161 ordinary skew and167 Frobenius projection remain distinct weight/metric contracts.

UNEXECUTED positive specification: Consume the actual p(1/3,2/3) datum, canonical uniqueness and both signed circulation entries.

UNEXECUTED adverse specification: Without positive law, division-based uniqueness need not hold at zero-weight states. A different normalization/weighting changes the decomposition, and circulation alone need not be a generator.

## Exact field corrections

### P2 fep-156 / non_vacuity

Deterministic finite argmin and the regularized Boltzmann distribution are conflated.

Complete replacement field text: A full-support finite prior, positive precision and nonconstant finite cost give a nondegenerate Boltzmann probability law attaining the unique KL-regularized objective minimum -gamma^-1 log Z. Separately, a nonempty finite policy carrier has a deterministic EFE argmin and the treewise declarations preserve finite optimal values; that deterministic argmin is not identified with the Boltzmann law or its regularized objective value.

### P2 fep-156 / assumption_review

Main theorem requires full prior support and positive precision, while cost is supplied; these must remain explicit.

Complete replacement field text: The primary Boltzmann-law minimization assumes a normalized finite full-support prior and gamma>0 and minimizes expected supplied real cost plus gamma^-1 KL to the prior over normalized candidate laws. Identifying that cost with model-derived EFE is a separate specialization. Deterministic finite-policy and finite-tree EFE/risk-ambiguity argmin statements are separate declarations. No continuous-action or general planning algorithm is claimed; supported sparse-prior and negative/zero-precision boundaries remain separately scoped foundation results.

### P2 fep-157 / invariant

Current invariant claims realized-step surprisal monotonicity, an accumulated trajectory bound and a dynamical fixed point that its declarations do not state.

Complete replacement field text: For one positive-evidence observation, outcome surprisal is bounded by perception VFE, whose exact gap is finite KL from the belief to its filtered posterior; the selected filtered-model policy has EFE equal to risk plus ambiguity under FullSupport. Supporting declarations give the finite observation-averaged posterior-KL chain bound, native predictive KL data processing, a Dobrushin total-variation bound under an explicit coefficient, Bayesian-filter/kernel reconstruction and selected-policy minimization. Flat policy EFE makes the policy posterior equal its prior. No realized-observation monotonicity, accumulated trajectory bound or dynamical fixed-point/convergence theorem is asserted.

### P2 fep-157 / assumption_review

Average KL and coefficient-dependent TV facts do not imply strict realized-step loop decrease.

Complete replacement field text: All belief, policy, state and outcome carriers are finite. The primary needs positive observation evidence and FullSupport at the filtered model; finite posterior-KL decomposition additionally needs a positive reference law and full likelihood support. The native predictive DPI is separately stated on discrete measurable carriers. Prediction uses an explicit HasDobrushinBound; strict TV contraction additionally needs a coefficient below one and a nonzero initial distance. The flat-EFE posterior identity is algebraic and is not an iterated-loop fixed-point theorem.

### P2 fep-157 / non_vacuity

No concrete strict loop/surprisal trajectory witness is supplied by these thirteen declarations.

Complete replacement field text: Nonuniform supported beliefs and informative likelihoods can instantiate the exact VFE gap and the observation-averaged KL decomposition. The selected-policy and filter/kernel equalities are actual finite operations. The flat-EFE case yields posterior=prior, an algebraic boundary; these declarations do not supply a strict realized-step surprisal-decrease or dynamical fixed-point witness.

### P2 fep-158 / invariant

Masking evidence direction is reversed and normalized reduced-prior evidence must be distinguished.

Complete replacement field text: Weights bounded above by one make positive unnormalized masked evidence no greater than full predictive evidence, so its negative-log evidence free energy is no smaller. For a nonnegative mask with positive prior normalizer, the normalized reduced-prior predictive equals maskedEvidence divided by that normalizer; no universal direction relative to full predictive evidence is claimed for this normalized quantity. Supported reduced posteriors obey exact weighted reconstruction and cross-multiplied odds identities. Separately, the Gibbs objective gap to its optimizer equals finite KL, and the fixed-variance Gaussian natural-chart log ratio is explicit.

### P2 fep-158 / assumption_review

Finite-law masking is not a generic finite-measure/DV model reduction theorem.

Complete replacement field text: Parameters and evidence use finite normalized law/kernel carriers. The primary free-energy comparison assumes weight<=1 pointwise and positive masked evidence. Normalized masked-prior/posterior statements additionally require nonnegative weights, positive prior mask normalizer and positive relevant evidence; ordinary log/ratio clauses retain their support assumptions. GibbsCertificate optimizer-gap identities and the fixed-variance Gaussian log Bayes factor are separate statements, with no general asymptotic model-selection or automatic full/reduced evidence monotonicity claim.

### P3 fep-158 / non_vacuity

Use a concrete mask that separates unnormalized and normalized evidence meanings.

Complete replacement field text: With prior masses(1/2,1/2), likelihoods(9/10,1/10) and mask(1,0), full evidence is1/2, unnormalized masked evidence9/20, mask normalizer1/2 and normalized reduced-prior evidence9/10. Positive support permits exact posterior reweighting. This exercises both evidence notions without reversing the proved comparison.

### P2 fep-159 / invariant

The declared fast-relaxation result supplies one good epsilon per tolerance, not a right-limit quantifier; quantity is KL gap, not generic MI.

Complete replacement field text: For a full-support two-state belief, its finite KL gap to the invariant law is at most productionRate/decayRate. A specific policy-independent perfect-observation model has EFE equal to the semigroup-evolved gap; that gap is bounded by the explicit squared exponential relaxation factor times the initial chi-square expression. At positive time the supported source-target slice production equals(1-rho)*productionRate/decayRate. Under inverse-epsilon rate scaling, the retained theorem gives, for each positive tolerance, existence of one positive epsilon achieving it; a forall-sufficiently-small-epsilon or Tendsto theorem is not asserted by that declaration.

### P3 fep-159 / non_vacuity

Stationary equality is a zero-gap boundary, not a positive time-scale separation witness.

Complete replacement field text: At the stationary law the gap and production rate both vanish, providing an equality boundary. A full-support nonstationary belief supplies nonzero deviation and current-affinity production for the positive rates, and the explicit rate-scaling envelope gives arbitrarily small attainable gap values at a fixed positive time. The retained declarations do not separately state the full right-limit quantifier.

## Ranked bounded follow-ups

1. metadata corrections156–159: Apply exact replacement fields with unchanged dispositions, preserve original historical metadata and fail-closed epoch normalization. No stronger theorem may be inferred from theorem names. Estimate: 0.5–1 day plus source-owner projections/seal controls.

2. 159 actual epsilon-right-limit theorem: Use existing scaled exponential envelope plus positivity/nonnegativity to prove forall epsilon in(0,epsilon0), gap<=delta, or Tendsto at nhdsWithin0(Ioi0). Current exists-one-epsilon theorem is weaker. Estimate: 1–2 days.

3. 157 trajectory invariant only if separately intended: Define an actual repeated observation/action path and conditional probability law, then prove an expected telescope or supermartingale with exact policy/transition assumptions. Existing single-step averaged KL does not imply realized-step monotonicity or accumulated EFE accounting. Preserve existing Bayesian model/tree bridges. Estimate: 3–7 day feasibility spike, not a routine metadata acceptance.

4. 160/166 weighted split consumers: Reuse actual signed circulation and stationary cycle witnesses. Any identification with plain skew algebra needs law weighting/similarity-transform bridge; do not assume circulation itself a nonnegative generator. Estimate: 0.5–2 days.

## Bindings and limits

Adjacent JSON binds all exact declaration statements, complete maturity/novelty records, touching relations, canonical body hashes and source-file SHA256 values. All168 rows now have static family audits; metadata corrections, dependency acceptance, independent evidence renewal and integration/publication remain open. No empirical, full scientific or terminal human acceptance is inferred.
