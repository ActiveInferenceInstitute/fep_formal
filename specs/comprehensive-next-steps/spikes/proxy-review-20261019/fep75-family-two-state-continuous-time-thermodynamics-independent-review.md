# Issue75 independent semantic review: two-state-continuous-time-thermodynamics

Exact EF source epoch; family roster verified. 7 rows reviewed. Static family coverage now168/168, without broad acceptance. Current dispositions retained for exact statements; listed metadata corrections remain required.

## fep-149: Two-State Continuous-Time Markov Kernel

Primary `fep149_twoStateSemigroup_rowSum`; current `formalized` retained for exact narrowed statement.

Explicit positive Bool jump rates a,b give stationary masses b/(a+b),a/(a+b) and transition entries built from rho=exp(-(a+b)t). Row sums1 hold for all real t; nonnegativity requires t>=0. Benchmark a=.7,b=.3 has decay1 and stationary true mass.7.

The row is an exact two-state probability kernel for nonnegative time. The owner additionally already constructs a general finite-rate-generator matrix-exponential semigroup by uniformisation, proves nonnegativity/master equations, and identifies its two-state specialization with these formulas; do not call general finite-state semigroup construction absent. Continuous path-process existence is different.

010 native reversible kernels and finite149 explicit analytic transitions are distinct; its foundation now includes a proved general finite-generator identification, not a PDE theorem.

UNEXECUTED positive specification: At benchmark rates and t=log2, rho1/2: false→true7/20 and true→false3/20, with both rows normalized.

UNEXECUTED adverse specification: For t<0 rho>1 and off-diagonal entries become negative although row sums1 remain. Zero rates lie outside TwoStateRates even if some limiting chains exist.

## fep-150: Continuous-Time Identity at Zero

Primary `fep150_twoStateSemigroup_zero`; current `formalized` retained for exact narrowed statement.

All four transition entries at time0 are Kronecker identity: diagonals1,offdiagonals0.

This proves the semigroup identity element, not stationarity of every initial law at positive time or a full-support kernel at zero time. Rates remain strictly positive through TwoStateRates.

149 normalization/nonnegativity do not alone imply zero-time identity;150 explicitly certifies it.

UNEXECUTED positive specification: Evaluate both diagonal/offdiagonal Bool entries at benchmark rates.

UNEXECUTED adverse specification: The identity at0 has zero offdiagonals, so positive-time full-support theorems cannot be instantiated at0 on Bool.

## fep-151: Two-State Chapman–Kolmogorov Semigroup

Primary `fep151_twoStateSemigroup_add`; current `formalized` retained for exact narrowed statement.

The closed-form transition satisfies entrywise Chapman–Kolmogorov for all real left/right times; nonnegative times give the probability-kernel semigroup interpretation.

The current maturity assumption unnecessarily restricts the algebraic statement to nonnegative times. Negative times retain the matrix group identity but lose positivity. Existing certifiedSemigroup and uniformised_transition_eq bind the finite-generator semigroup; no sample-path or PDE inference follows.

006 discrete iterate semigroup and151 real-time analytic matrix law are different carriers; conversion must use actual semigroup/selected-time definitions.

UNEXECUTED positive specification: Benchmark rates at two positive times log2 have rho factors1/2,1/2 and summed-time rho1/4; actual nonidentity kernels compose.

UNEXECUTED adverse specification: A generic normalized family of kernels need not satisfy additive semigroup composition. Negative-time entries can be negative despite the identity.

## fep-152: Two-State Continuous-Time Master Equation

Primary `fep152_twoStateSemigroup_hasDerivAt`; current `formalized` retained for exact narrowed statement.

Each actual transition entry has HasDerivAt equal to both Q*P(t) and P(t)*Q, with the stated finite matrix index order. It holds for real t, including0.

These are explicit forward/backward master equations, not supplied symbolic vector fields. Row-generator convention and multiplication order must be preserved. The existing general matrix-exponential finite-generator owner supplies further actual content, but no continuous-state Fokker–Planck/PDE theorem is asserted.

043 scalar derivative certificates and152 matrix-entry analytic derivatives are related techniques, not a carrier-free equivalence.

UNEXECUTED positive specification: At time0, false→true derivative a=.7 and true→false derivative b=.3, diagonals their negative row rates.

UNEXECUTED adverse specification: Transposing row-generator convention changes products/distribution evolution; arbitrary supplied Q/P do not satisfy these derivatives merely from row normalization.

## fep-153: Continuous-Time Stationarity and Detailed Balance

Primary `fep153_twoStateSemigroup_stationary`; current `formalized` retained for exact narrowed statement.

The explicit stationary law is invariant and satisfies detailed balance for every real-time transition formula; probability interpretation uses t>=0.

Positive rates imply unique nonzero stationary masses in this model. This is a reversible equilibrium family, not a driven NESS or arbitrary-generator detailed-balance theorem. Algebraic stationarity at negative t does not make a probability transition.

010 reversibility⇒invariance is generic native content;153 supplies an actual analytic two-state family and explicit invariant law.

UNEXECUTED positive specification: At benchmark rates, opposing stationary infinitesimal fluxes .3*.7 and .7*.3 agree, and both finite-time transitions balance.

UNEXECUTED adverse specification: A directed3-cycle generator elsewhere is stationary but not detailed balanced. Stationarity alone cannot imply these pairwise identities.

## fep-154: Exact Two-State Exponential Relaxation

Primary `fep154_twoStateRelaxation_exact`; current `formalized` retained for exact narrowed statement.

For any initial Bool law and real time, true-mass deviation from stationaryTrue equals rho(t) times its initial deviation. This is an exact relaxation identity; natively normalized prediction uses nonnegative time.

Positive decay gives forward-time exponential relaxation, not an arbitrary-chain mixing-rate result. At negative time the algebraic mass formula may leave[0,1]. The benchmark initial point mass is genuinely nonstationary.

020 discrete recurrence has a geometric iteration factor;154 gives the explicit continuous-time exponential factor on the same two-state-style scope without automatic timescale identification.

UNEXECUTED positive specification: Benchmark initial false point mass has initial deviation-7/10; at t=log2 deviation-7/20.

UNEXECUTED adverse specification: Initial=stationary gives zero deviation at every time. Negative time magnifies rather than relaxes deviation.

## fep-155: Exact Two-State Quadratic Lyapunov Decay

Primary `fep155_twoStateLyapunov_exact`; current `formalized` retained for exact narrowed statement.

Squared true-mass deviation equals rho(t)^2 times initial squared deviation and has derivative -2*(a+b)*V(t). Benchmark initial false point mass gives V0=49/100 and derivative-49/50.

The function is a quadratic Lyapunov diagnostic, not physical entropy, thermodynamic free energy or a universal entropy-production rate. At stationary initial law derivative0, so strictness needs nonstationarity.

032 quadratic discrete descent and155 analytic exact decay have related scalar geometry but distinct step/time contracts.

UNEXECUTED positive specification: Consume actual benchmark negative derivative; at t=log2 the value is49/400.

UNEXECUTED adverse specification: Stationary initial law gives constant0 and no strict decrease. A different potential cannot inherit this derivative without a chain-rule/identity proof.

## Exact field corrections

### P3 fep-151 / assumption_review

The exact semigroup identity is proved for all real times; positivity/probability interpretation is the nonnegative-time restriction.

Complete replacement field text: Rates are strictly positive. The entrywise additive matrix identity holds for arbitrary real times; restricting both times to be nonnegative supplies its probability-kernel interpretation. No continuous-path or PDE existence theorem is inferred from this identity.

## Ranked bounded follow-ups

1. finite-generator/two-state actual consumers: Reuse existing uniformisation nonnegativity, exponential semigroup, master equations and uniformised_transition_eq; do not duplicate delivered general finite generator construction. Typed positive/negative-time controls preserve probability boundaries. Estimate: 0.5–1.5 days.

2. 155 meaning/units specialization: Any proposed physical free-energy/entropy-production interpretation must prove a matching functional identity and scale convention. Existing quadratic decay alone does not supply one. Estimate: bounded functional-specific spike1–3 days.

## Bindings and limits

Adjacent JSON binds all exact declaration statements, complete maturity/novelty records, touching relations, canonical body hashes and source-file SHA256 values. All168 rows now have static family audits; metadata corrections, dependency acceptance, independent evidence renewal and integration/publication remain open. No empirical, full scientific or terminal human acceptance is inferred.
