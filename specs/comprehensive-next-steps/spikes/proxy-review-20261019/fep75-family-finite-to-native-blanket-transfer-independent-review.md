# Issue75 independent semantic review: finite-to-native-blanket-transfer

Exact source epoch `ef2c99a7ca9b8bd11508c252ec55d01fe9c36699`. Roster verified against catalogue_metadata.yaml. Seven rows reviewed; cumulative scope148/168. Current narrowed dispositions retained. No S edits or compilation.

## fep-135: Finite-Law Measure Embedding

Current `formalized` retained; primary `fep135_embeddedLaw_apply_singleton`.

The finite law is embedded as a finite sum of ENNReal.ofReal(mass) scaled Dirac measures. Singleton equality preserves each atom, and total mass1 gives an actual IsProbabilityMeasure instance.

Discrete measurability and finite nonnegative normalized masses are essential for faithful singleton semantics. This is an exact finite measure embedding, not approximation of arbitrary continuous measures or a statement about physical blanket discovery.

017 native posterior and027 native hierarchical law are earlier native consumers.135 supplies an actual probability carrier map rather than authoring an unrelated native law; its named endpoint relation remains a pairing with017.

Unexecuted positive specification: Embed a Boolean law true3/4,false1/4; obtain distinct native singleton masses and native mass1.

Unexecuted adverse specification: Embedding arbitrary signed unnormalized weights through ofReal would discard negatives and fail the finite-law contract; that operation is not this API.

## fep-136: Finite-Law Embedding Injectivity and Expectation Transfer

Current `formalized` retained; primary `fep136_embeddedLaw_injective`.

Equal embedded measures imply equal finite laws by real singleton recovery; every real observable integrates exactly to its finite weighted sum. Finiteness/discrete structure supplies integrability.

The proof does not merely compare two unrelated expectations: it uses the exact same law and observable. A nonconstant observable can still have expectation0, so nontriviality should be demonstrated by chosen values rather than implied universally. No arbitrary continuous integration equivalence is proved.

015 only measurable energy ingredients and057 native tower expectations are distinct claims.136 closes a real finite/native integration seam on the shared discrete carrier.

Unexecuted positive specification: Boolean true3/4,false1/4 and indicator true have native and finite expectation3/4; distinct point masses are separated by that observable/singleton.

Unexecuted adverse specification: Constant observables cannot distinguish distinct probability laws, although equality of the entire measures does. Equality of one expectation alone is weaker than embedding injectivity.

## fep-137: Embedded Finite-Kernel Composition

Current `formalized` retained; primary `fep137_embeddedPredictive_eq_comp`.

Embedding kernel.predictive(prior) equals native embeddedKernel composition with embeddedLaw(prior). Row normalization supplies a native Markov kernel; singleton calculations prove the measure equality.

Both finite input/output spaces are discrete. This is a genuine commuting square, not merely conjunction with a native associativity statement. The foundation also already proves embeddedKernel composition and finite joint=compProd, so those transport seams are delivered.

019 native prediction and055 reversed posterior composition are neighbors.137 identifies finite prediction with native composition; it does not automatically identify posterior versions at null evidence.

Unexecuted positive specification: A nonuniform Boolean prior and state-dependent noisy kernel give a nontrivial mixture; evaluate both native composite singleton masses.

Unexecuted adverse specification: A coarse/non-discrete measurable structure would not preserve singleton recovery under the current contract. This does not imply a general disintegration approximation theorem.

## fep-138: Markov-Blanket Rectangle Factorization

Current `formalized` retained; primary `fep138_staticJoint_rectangle_factorization`.

The embedded static joint mass on the actual blanket/internal/external singleton rectangle equals blanket mass times the two conditional masses, all converted to ENNReal. This directly transports authored static product rows.

The row itself is atomic rectangle factorization, not CondIndepFun. The foundation additionally proves complete joint=blanket marginal compProd product kernels, which139 uses; do not say only atomic evidence exists. Null blanket rows have0 joint mass and need not determine unique conditional versions.

079 finite CMI characterization has full-support requirements for its general iff.138 proves the embedded structural factorization, and its paired finite zero-CMI statement is not used as a substitute for native conditional-distribution proof.

Unexecuted positive specification: Reuse correlatedBlanketModel: two diagonal blanket/joint atoms have mass1/2, off-diagonal blanket atoms0.

Unexecuted adverse specification: Without product conditional rows, a correlated internal/external row at positive blanket mass fails the factorization. Full-support blanket law is not required for the constructed static model.

## fep-139: Native Markov-Blanket Conditional Independence

Current `formalized` retained; primary `fep139_staticJoint_condIndepFun`.

Actual Mathlib CondIndepFun holds for internal/external coordinate maps conditioned on the blanket sigma algebra under the embedded static joint. The proof identifies authored endpoint kernels with condDistrib almost everywhere, then applies native joint-product characterization.

Finite discrete carriers provide required standard-Borel/measurability facts; internal/external are explicitly nonempty. No positive blanket support is required because conditional distributions are identified only blanket-marginal almost everywhere. Null blanket kernels are authored versions, not identified pointwise by observations. Native CI does not establish causality or independence without conditioning.

009 is native symmetry;079 finite CMI.139 provides the substantive finite-factorized-static-model to native-predicate transfer without identifying arbitrary zero CMI with arbitrary native CI.

Unexecuted positive specification: The supplied two-regime Boolean model has two positive joint atoms, correlated internal/external marginals and native conditional independence given blanket.

Unexecuted adverse specification: Forget the blanket in that same correlated model: internal=external fair Bool are unconditionally dependent. Changing authored conditional versions only at null blanket atoms cannot be inferred from the measure.

## fep-140: Conditional Independence under Measurable Coarsening

Current `formalized` retained; primary `fep140_condIndepFun_measurableImages`.

Measurable images of the endpoint coordinate maps preserve139 native CondIndepFun via Mathlib composition. Image types need not be finite, because measurable maps from the finite source are used.

The conditioning blanket sigma algebra is held fixed. Noninjective endpoint coarsening is allowed; coarsening/removing the conditioning coordinate is a different and generally false inference. This does not assert retained information, invertibility or causal sufficiency of the images.

009 symmetry concerns swapping endpoints,140 concerns measurable endpoint maps. It is an actual native preservation law, not evidence that arbitrary blanket coarse-graining preserves a blanket.

Unexecuted positive specification: Identity endpoint images recover139; a noninjective finite map merges endpoint states while retaining the same blanket conditioning.

Unexecuted adverse specification: In correlatedBlanketModel, replacing blanket conditioning by a constant loses conditional separation and exposes the fair diagonal endpoint dependence.

## fep-141: Native Blanket-Transition Closure

Current `formalized` retained; primary `fep141_prediction_preserves_nativeBlanket`.

For each supplied current state, nextStaticModel has authored factorized next-state rows and embeds into a native law with internal/external CondIndepFun given next blanket. This follows the genuine static theorem139.

The conclusion is rowwise. A prior mixture over current states can create latent common-cause dependence between next endpoints even when every row factorizes. No closure for arbitrary uncertain-state prediction, invariant measure, repeated dynamics or physical intervention follows.

080 shared-conditional mixture and081 correlated blanket composition have additional compatibility structure.141→080 pairing does not silently supply those hypotheses to arbitrary mixtures.

Unexecuted positive specification: Choose a current state whose next blanket has multiple positive regimes and whose endpoint conditionals vary by blanket; apply139 to that exact nextStaticModel.

Unexecuted adverse specification: Use two equally likely current states, constant next blanket, and deterministic next internal=external=current-state bit. Each row is product and natively CI, but mixture is a fair diagonal law and not CI given constant blanket.

## Concrete wording corrections

No concrete current maturity wording correction required in these seven rows; retain the explicit rowwise, measurable-image and discrete-carrier boundaries.

## Ranked bounded follow-ups

1. 141 rowwise versus uncertain-state mixture control: Use existing embedding/native CI and finite shared-conditional mixture laws to prove closure only with compatible endpoint mechanisms. Author the constant-next-blanket diagonal-mixture countermodel for arbitrary-mixture refusal, without duplicating delivered rowwise transfer. Estimate: 1–3 days.

2. 136/137 exact-source consumer renewal: Reuse weighted Dirac integral, joint compProd, predictive composition and embeddedKernel_comp, with explicit nonuniform/noisy laws. Any later posterior/KL transport must separately bind support and version semantics. Estimate: 0.5–1.5 days.

3. 140 conditioning-coarsening boundary: Endpoint composition is already proved. A separate theorem for changing blanket conditioning needs sufficient-statistic/conditional-kernel invariance hypotheses; use correlatedBlanketModel to reject arbitrary removal of blanket information. Estimate: 0.5–1 day adverse consumer; positive sufficient-condition theorem1–3 days.

## Source bindings and limits

Adjacent JSON binds complete current maturity/novelty records, exact primary/support/boundary statements, canonical body and source-file SHA256 values, and touching relations. These14 rows do not establish full Issue75/scientific/terminal acceptance. Remaining20 topics and active acceptance dependencies stay open.
