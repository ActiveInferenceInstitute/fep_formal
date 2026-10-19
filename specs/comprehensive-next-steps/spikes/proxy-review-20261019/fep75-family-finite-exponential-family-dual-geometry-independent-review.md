# Issue75 independent semantic review: finite-exponential-family-dual-geometry

Exact source epoch `ef2c99a7ca9b8bd11508c252ec55d01fe9c36699`. Roster verified against catalogue_metadata.yaml. Seven rows reviewed; cumulative scope148/168. Current narrowed dispositions retained. No S edits or compilation.

## fep-142: Finite Exponential-Family Normalization and Support

Current `formalized` retained; primary `fep142_exponentialFamily_sum_one`.

Positive base weights times exp(theta*statistic) normalize by a finite positive partition function to a full-support law for every real natural parameter.

Outcome finite/nonempty and base strictly positive; the base need not sum1. Statistic may be constant, so normalization/full support alone implies neither parameter identifiability nor positive Fisher. No multidimensional family or continuous base measure is constructed.

031 Gibbs normalizes on a selected support, whereas142 uses full carrier positive base weights. Current bridge pairs normalizations without identifying base/energy/parameter conventions.

Unexecuted positive specification: Unit-base Fin3 statistic(0,1,2) at theta log2 has masses1/7,2/7,4/7; at theta0 it is uniform.

Unexecuted adverse specification: A constant statistic gives the same normalized law for every theta. Zero/negative base weights fall outside the family contract; empty outcomes cannot form a normalized law.

## fep-143: Affine Exponential-Family Log-Density Ratio

Current `formalized` retained; primary `fep143_logDensityRatio_eq`.

For the same positive-base family, log(p_left/p_right)=(left-right)*statistic-(A(left)-A(right)); the base cancels exactly.

Both laws use the same base and statistic. Different families need not satisfy this ratio formula. Strict support makes logs finite and ordinary; no singular-density or extended-log convention is used.

026 ordinary positive log quotient is a neighbor;058 Gibbs identity is broader finite certificate.143 derives its affine ratio from the explicit parametric family.

Unexecuted positive specification: Unit-base Fin3 at left log2,right0 has distinct outcome-dependent ratios3/7,6/7,12/7 and supported logarithms.

Unexecuted adverse specification: Changing base between the two laws introduces an additional log base ratio; equal parameters or constant statistic make the ratio trivial.

## fep-144: Finite Log-Partition Gradient

Current `formalized` retained; primary `fep144_logPartition_hasDerivAt`.

Actual HasDerivAt for the positive finite log-partition A has derivative mean statistic, via finite exponential-sum differentiation and the log chain rule.

This is a genuine analytic derivative, not a symbolic gradient field or a supplied derivative certificate. It is scalar and finite; no infinite-sum differentiation, vector Hessian, chart or manifold theorem follows.

040 Gaussian entropy derivative and043 quadratic derivative are separate exact derivative examples. Current144 relation pairs derivatives rather than identifying their potentials.

Unexecuted positive specification: Three-state family at0 has mean1, so A'(0)=1; differentiating its mean later yields variance2/3.

Unexecuted adverse specification: Constant statistic c makes mean constant c, despite A varying affinely if c is nonzero; nonconstant A alone does not imply nondegenerate geometry.

## fep-145: Centered Exponential-Family Score Identity

Current `formalized` retained; primary `fep145_score_eq_statistic_sub_mean`.

score is defined as statistic-mean and the topic primary is rfl; the weighted score mean is proved0. The foundation law_hasDerivAt actually proves p_theta'=p_theta*score, and positive mass permits a direct log-derivative consumer.

Do not describe the primary rfl as itself differentiating log density; the substantive derivative support is the foundation law_hasDerivAt plus positivity. The existing identities justify the scalar score interpretation, but arbitrary supplied ScoreModel centering elsewhere is a weaker contract. A direct HasDerivAt(log law) wrapper is a bounded presentation improvement.

038 derives Bernoulli score behavior;145 explicit exponential-family law supplies centered score and a genuine derivative bridge in its owner. It does not establish score regularity for arbitrary likelihood families.

Unexecuted positive specification: Three-state family at0 has scores(-1,0,1), positive masses1/3 and mean score0; use actual mass derivative to verify score interpretation.

Unexecuted adverse specification: A constant statistic yields all scores0. Centered arbitrary score data need not equal a log derivative without a parameterized law and derivative bridge.

## fep-146: Log-Partition Hessian–Variance–Fisher Identity

Current `formalized` retained; primary `fep146_logPartition_secondDeriv_eq_variance`.

HasDerivAt mean variance is the derivative of144 first-derivative coordinate; Fisher is defined as that same expected squared centered score, so Fisher=variance is rfl. Named Fin3 variance at0 equals2/3 and constant-statistic Fisher0 are real boundaries.

This is scalar second-derivative content, not a matrix Hessian/covariance transformation. The general theorem does not prove strict variance for every nonconstant family at every theta, though that is feasible from full support and the finite sum of squares. The score interpretation is supported by actual law derivative.

100 categorical metric positivity is a separately certified tangent geometry. The146 bridge pairs those facts, not an identified all-dimensional Fisher matrix or Hessian.

Unexecuted positive specification: Use threeState_variance_zero=2/3 and law/score formulas at0; consume both HasDerivAt A mean and HasDerivAt mean variance.

Unexecuted adverse specification: Constant statistic c has variance/Fisher0 at all theta, so positive base alone cannot imply a nondegenerate parameter chart.

## fep-147: Exponential-Family KL–Bregman Identity

Current `formalized` retained; primary `fep147_exponentialFamily_KL_eq_bregman`.

The existing finiteKL(p_left||p_right) equals A(right)-A(left)-A'(left)*(right-left). This is the log-partition Bregman orientation B_A(right,left), reversed relative to the probability-law label order.

Both laws have full support in one finite scalar family, so totalized finiteKL reduces to ordinary expected log ratio. This does not automatically transport to native extended KL. Constant-statistic families have equal laws for distinct parameters and zero KL; unequal natural parameters alone do not imply positive divergence without identifiability.

014 native KL nonnegativity is paired, not identified;104 algebraic Bregman identity is a nearest concept but the current named bridge only invokes147 and014, not a same-carrier104 specialization.

Unexecuted positive specification: Unit-base Bool statistic0/1, left0,right log3 gives laws(1/2,1/2) and(1/4,3/4); KL equals log(2/sqrt3) and the oriented Bregman expression.

Unexecuted adverse specification: Swap left/right and the divergence generally changes; constant statistic with unequal parameters still gives0. A singular native pair lies outside this full-support family.

## fep-148: Natural-to-Mean Coordinate Injectivity

Current `formalized` retained; primary `fep148_meanParameter_strictMono`.

Strictly positive variance throughout Icc lower upper implies StrictMonoOn mean and hence injectivity there, using the exact mean derivative. It does not construct an inverse map or prove surjectivity.

There is no lower<upper premise: empty/singleton intervals permit vacuous/trivial results. A positive variance point at0 alone does not instantiate the theorem on a nontrivial interval without a continuity or global nonconstant-statistic positivity argument. Current three-state point witness does not by itself close that instance.

103 invertible ambient Fisher/chart transport is a distinct finite-matrix statement.148 gives scalar order/injectivity under explicit interval positivity, not global dual-flat coordinates or a multidimensional inverse-function theorem.

Unexecuted positive specification: Prove variance>0 for the supplied nonconstant Fin3 statistic at every theta from positive masses, then instantiate lower=-1,upper=1 and compare unequal parameters.

Unexecuted adverse specification: Constant statistics have0 variance and constant mean; removing variance positivity makes nontrivial-interval injectivity false. Empty/singleton intervals hide no genuine coordinate change.

## Concrete wording corrections

- P3 fep-145 `assumption_review`: The primary score equality is definitional; actual derivative support resides in law_hasDerivAt. Distinguish these while preserving the justified score interpretation. Proposed text: The centered score is defined on the finite full-support exponential family. The primary unfolds that definition and the supporting theorem proves zero mean. The existing law_hasDerivAt establishes mass derivative=mass*score, so positivity supports the natural-parameter log-derivative interpretation. This does not establish score regularity for arbitrary likelihoods.

- P3 fep-148 `non_vacuity`: Positive variance at one point alone does not instantiate positivity over a nontrivial closed interval. The current generic theorem is valid but its concrete interval instance remains unproved in these declarations. Proposed text: The three-state family has variance2/3 at0, and constant statistics show why positivity is required. A concrete nontrivial interval instance additionally needs variance positivity throughout that interval, derived either from continuity near0 or from full support and a nonconstant statistic; the retained point witness alone is not that interval certificate.

## Ranked bounded follow-ups

1. 148 actual nontrivial interval instance: Prove variance>0 iff statistic nonconstant using positive atom masses and finite sum of squares, then establish the three-state family positive for every parameter and apply148 on[-1,1]. This strengthens a genuine concrete instance rather than duplicating current conditional theorem. Estimate: 1–2 days.

2. 145 direct log-score and inherited ScoreModel consumer: Use actual law_hasDerivAt, law_pos and HasDerivAt.log to prove direct HasDerivAt(log law) score. Build the existing one-coordinate ScoreModel via mean_score_zero, and identify expected-score Fisher; no second metric or new owner needed. Estimate: 0.5–1.5 days.

3. 147 exact oriented Bregman specialization: Embed scalar parameters as Fin1 coordinates and identify logPartitionBregman(left,right) with104 divergence at(right,left), using144 true derivative. Preserve orientation and keep native KL identification separate until a supported weighted-Dirac theorem is proved. Estimate: 0.5–2 days.

## Source bindings and limits

Adjacent JSON binds complete current maturity/novelty records, exact primary/support/boundary statements, canonical body and source-file SHA256 values, and touching relations. These14 rows do not establish full Issue75/scientific/terminal acceptance. Remaining20 topics and active acceptance dependencies stay open.
