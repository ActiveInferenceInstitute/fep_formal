# Issue75 independent semantic review: information-geometry-and-geometric-optimization

Exact source epoch `ef2c99a7ca9b8bd11508c252ec55d01fe9c36699`. Seven rows reviewed; cumulative scope106/168. All current narrowed dispositions retained. No repository edits or compilation.

## fep-100: Categorical Fisher Positivity on Simplex Tangents

Current disposition `conditional_proxy` retained; primary `fep100_categoricalFisher_simplexTangent_positivity`.

Full-support categorical metric/lowering representations certify positivity on every nonzero zero-sum tangent. The genuine Fin2 construction proves the entire one-dimensional simplex tangent is spanned by(1,-1), with energy4; duplicated scores separately exhibit a null direction.

The general carrier assumes representation fields, and ScoreModel supplies centered score data rather than automatically differentiable likelihoods. The concrete Fin2 metric is full rank on the simplex tangent, not on the ambient2-space: scores have normal null direction(1,1). Do not use its tangent positivity as the ambient matrix Invertible premise for103.

004 is supplied diagonal geometry and038 interior Bernoulli scalar scores.100 certifies the inherited ScoreModel metric on categorical tangents, not an independent metric or automatic all-dimensional construction.

Unexecuted positive specification: Consume explicit twoCategoricalTangent, its nonzero certificate, energy4 and tangent-spanning theorem.

Unexecuted adverse specification: For the same concrete model, ambient tangent(1,1) has zero score pairing; for duplicated-score model the supplied nonzero null tangent defeats arbitrary-score full rank.

## fep-101: Fisher Pullback under Reparameterization

Current disposition `formalized` retained; primary `fep101_fisherPullback_reparameterization`.

PullbackMetric for matrix composition is successive pullback and remains positive semidefinite. No invertibility is assumed; outer d-by-k and inner k-by-d map back to d, rather than the maximally general three-independent-dimension signature.

The matrices are supplied linear maps, called Jacobians by interpretation; no actual derivative of a coordinate chart is certified. Positive definiteness requires separate injectivity and score-identifiability support. The appropriate bilinear pullback is J-transpose*F*J; do not replace it by J*F*J-transpose.

038 has an algebraic scalar candidate-Jacobian factorization with a previously identified missing coordinate derivative bridge.101 generalizes matrix pullback algebra but does not repair that missing derivative fact.

Unexecuted positive specification: Use a nonscalar rectangular outer and inner with compatible dimensions; evaluate the same inherited Fisher bilinear form after composition.

Unexecuted adverse specification: A zero or rank-deficient Jacobian gives null pullback even if the original metric is positive definite. Actual nonlinear coordinate maps require a HasFDerivAt/chain-rule bridge.

## fep-102: Unbiased Scalar Cramér–Rao Bound under Score Regularity

Current disposition `formalized` retained; primary `fep102_unbiasedScalar_cramerRao`.

Weighted Cauchy–Schwarz and the supplied unit estimator-score covariance imply variance*Fisher>=1. The certificate includes unbiasedness, scoreRegularity=1 and positive Fisher; the proof uses the latter two, while unbiasedness makes the squared centered error a variance interpretation.

ScoreModel is centered score data. Parameterized-family differentiation, estimator independence of the parameter and interchange regularity are not derived. The stated product bound is well-defined finite real algebra; positive Fisher allows dividing to a reciprocal bound.

038 expected-score centering is weaker than the differentiated unbiasedness identity. Current bridge conjoins generic CR bound with Bernoulli centering, not a constructed Bernoulli certificate.

Unexecuted positive specification: Interior Bernoulli p=1/2, indicator estimator, target1/2 and score±2 give variance1/4,Fisher4 and covariance1, saturating the bound.

Unexecuted adverse specification: A constant estimator can be unbiased at one point but has covariance0 and variance0; unbiasedness alone cannot imply the bound. A supplied non-log-derivative score is not automatically a statistical score family.

## fep-103: Natural-Gradient Equivariance under an Invertible Full-Rank Chart

Current disposition `formalized` retained; primary `fep103_naturalGradient_equivariance`.

With both ambient Fisher matrix and square chart matrix invertible, inverse-vector transport and transpose-covector transport satisfy pulled-back lowering. Weighted Cauchy–Schwarz is an independently supplied supporting proof.

The vector is J-inverse*v; covector J-transpose*c; lowering is J-transpose*F*J. These orientations are essential. An arbitrary supplied covector need not be an actual derivative of an objective. No Hessian transformation or nonlinear global-chart theorem follows; Hessian pullback would need objective/chart differentiability and generally second-derivative terms.

100 tangent full rank does not imply ambient inverse exists;038 scalar interior duality gives a valid full-rank example. Keep formalized for exact linear algebra.

Unexecuted positive specification: Use fairBernoulli one-coordinate positive Fisher and nonidentity scalar chart2; vector coordinates divide by2 while covector multiplies by2.

Unexecuted adverse specification: Singular Fisher/duplicated score or singular chart cannot meet the invertibility contracts. For a nonsymmetric invertible2D chart, omitting transpose changes covector transport.

## fep-104: Mirror-Descent Three-Point Identity

Current disposition `formalized` retained; primary `fep104_mirrorDescent_threePoint_identity`.

For arbitrary supplied potential and vector field, expanding the defined Bregman expression gives the exact three-point pairing identity. No derivative, convexity, optimizer or descent is asserted.

The name gradient is data only unless a derivative witness is supplied. Negative Bregman values are permitted for concave potential or inconsistent vector field. Distinct points/nonconstant gradient do not guarantee a nonzero pairing in multiple dimensions, so nonvacuity should give a concrete instance.

024 is native extended KL regularization. The104 bridge deliberately pairs it without identifying Bregman with KL or deriving a mirror-descent algorithm.

Unexecuted positive specification: Fin1 potential x↦x0^2/2, gradient x↦x0; left2,middle1,right0 gives divergences2,1/2,1/2 and pairing1.

Unexecuted adverse specification: Take concave potential-x0^2/2 with its true gradient-x0: divergence is negative for unequal points although the identity still holds. Orthogonal gradient/point differences can also give zero pairing despite distinct vectors.

## fep-105: Bregman Pythagorean Law for an Affine Information Projection

Current disposition `conditional_proxy` retained; primary `fep105_affineProjection_bregmanPythagorean`.

Projection membership plus supplied orthogonality for every candidate in the named set yields exact splitting. Residual nonnegativity gives a pointwise comparison; a minimizer statement over the whole set needs that premise for every candidate.

AffineBregmanProjection does not require IsAffine/convexity or derivative/convex potential data; affineSet is merely a Set. The theorem is valid more generally because it assumes full setwise orthogonality. It neither constructs a projection nor proves existence/uniqueness. Hellinger nonnegativity in the relation does not supply this residual Bregman nonnegativity.

044 squared Hellinger is a separate nonnegative object, not established as this Bregman divergence. Retain conditional_proxy for supplied projection/orthogonality/nonnegative residual.

Unexecuted positive specification: Quadratic Euclidean potential with true gradient in Fin2, set{x:x1=0}, base(0,1),projection(0,0),candidate(2,0): exact squared-distance splitting with positive residual.

Unexecuted adverse specification: Without orthogonality the equality need not hold; concave potential can give negative residual so comparison reverses. Finite nonaffine sets can still satisfy the supplied orthogonality certificate, demonstrating no affineness is encoded.

## fep-106: Replicator–Natural-Gradient Equivalence

Current disposition `conditional_proxy` retained; primary `fep106_replicator_naturalGradient_equivalence`.

For a certified categorical Fisher carrier the replicator vector p_i*(fitness_i-mean) lowers to the centered-fitness covector, and sums to0. Concrete uniform Fin2 fitness(1,-1) yields vector(1/2,-1/2), nonzero.

This is instantaneous natural-gradient ascent of the supplied fitness covector, not a time-integrated flow, global optimum, positivity-preserving Euler step or proof that arbitrary fitness is an objective derivative. Full-support representation makes division by p legitimate; mass conservation alone does not preserve nonnegativity.

028 softmax normalization and038 scalar duality are neighboring pairings; no equivalence of softmax and replicator trajectories.100 is tangent metric support;103 ambient inverse is not needed for the predicate proof.

Unexecuted positive specification: Consume the actual Fin2 nonconstant fitness, exact nonzero vector and IsNaturalGradient predicate.

Unexecuted adverse specification: For uniform Fin2 and fitness(1,-1), Euler step2 gives(3/2,-1/2) with mass1 but negative probability. Constant fitness produces0; boundary-zero masses lie outside the certified full-support carrier.

## Concrete wording corrections

- P3 fep-104 `non_vacuity`: Distinct vectors and a nonconstant gradient need not have nonzero pairing; give a concrete compatible instance. Proposed text: For Fin1 quadratic potential x0^2/2 and true gradient x0, the points left=2,middle=1,right=0 give divergence difference 2-1/2-1/2=1 and pairing1. This exercises the identity without asserting convexity or derivative compatibility for arbitrary supplied data.

- P3 fep-105 `assumption_review`: The certificate name does not encode actual affineness of its Set; comparison is candidate-wise unless nonnegativity is quantified over the set. Proposed text: AffineBregmanProjection supplies membership and gradient-difference orthogonality for every candidate in a named Set; no IsAffine or convexity predicate is required. Splitting holds under that certificate. The minimization comparison additionally assumes residual Bregman nonnegativity for the selected candidate; obtaining a minimizer over the whole set requires this for all candidates. Existence, uniqueness, derivative compatibility and convexity are not derived.

## Ranked bounded follow-ups

1. concrete CR certificate and chart consumers: Instantiate existing Bernoulli score model, indicator estimator and target p to prove unbiasedness/unit covariance and equality in CR. Instantiate nonidentity invertible chart with correctly transposed covector; keep categorical tangent positivity separate from ambient invertibility. Estimate: 1–2 days.

2. certified convex Bregman specialization: Use actual derivative/convexity certificate for an existing potential, prove residual nonnegativity and instantiate orthogonal Euclidean projection before attempting entropy/KL on an interior simplex. No new production owner needed. Estimate: 1–3 days Euclidean specialization; entropy boundary requires a separate support probe.

3. nonlinear chart or integrated replicator scope: A true chart-Jacobian interpretation requires HasFDerivAt and chain rule. Hessian transformations additionally require second derivatives and nonlinear chart terms. Replicator ODE/simplex positivity needs an actual solution/flow contract; mass-zero instantaneous vector alone is insufficient. Start with explicit finite-dimensional analytic probes, retaining boundaries. Estimate: 2–5 days chart derivative bridge; ODE general flow requires separate spike.

## Bindings and limits

The adjacent JSON binds exact canonical body and source-file hashes, all primary/support/boundary statements, current complete maturity and novelty records, and touching relations. No general physical, causal, state-estimation, terminal or full Issue75 acceptance follows. Remaining62 topics and active integration/acceptance dependencies remain open.
