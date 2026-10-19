# Issue75 independent core-information-geometry audit

Exactly7rows;retaincurrentnarrowdispositionswithprecisioncorrections. Combinedoriginalfamilyreviewsnow50rows,notall168.

## fep-004 — Finite Diagonal Fisher Metric

Supplied finite diagonalweights give symmetry/nonnegativepairing and strictlypositiveweights givezeroiffzerovector.

StatisticalFisheroriginnotderived; degeneratezero/negativeweightsnotpositivegeometry.

Positive/adverse(unexecuted): weights(1,2),tangent(1,0)positive; zerooneweightandnonzerotangentinnullcoordinate giveszero.

Nearesttopics: 038suppliesBernoulliweight;101pullbacks/100simplexgeometrydifferentmodels.

## fep-014 — KL Divergence: Non-Negativity, Identity, and Chain Rule

NativeENNRealKLchainrule forfiniteμν andMarkovκη;selfzeroSigmaFinite,separationfinite exact.

Notbarefiniteprobabilitysumwithoutsupport;singularactual/reference can∞; noownedDPIwrapperthoughpinnednativeDPIexists.

Positive/adverse(unexecuted): Equalmeasureszero,unequalfinitepositive,singularDirac∞; productMarkovkernelconditionalKLtermnontrivial.

Nearesttopics: 001/002/024/041reuseKL;063finiteDPIseparate;110genericweightedDiracproposalnotyetintegrated.

## fep-018 — Bernoulli Fisher–Rao Coordinate Distance

Absolute differenceof2arcsin(sqrt p) givesnonnegative/symmetric/triangleunconditionally;separation[0,1] via injectivesqrt/arcsin.

Metricdistanceonclosedprobabilityintervalisproved; notvariationalpathlength/geodesicminimality. Derivativeidentificationwith038candidateJacobianmissing.

Positive/adverse(unexecuted): p0,q1distancepi;equalzero;p-1,q-2bothsqrt0collapseoutsideinterval.

Nearesttopics: 038statisticalmetriclocalinformationvs018globalcoordinateformula;044Hellingerchordaldistance distinct.

## fep-024 — KL Regularization in Objectives

NativeKLweightedobjectiveexactatmatchingSigmaFiniteprior;upperbound/zeroweight/weightmonotonicity exactENNReal.

Nooptimizer/differentiability/proximalalgorithm. 0*∞=0 is explicitENNRealconvention; base∞canhideanyregularizationchange.

Positive/adverse(unexecuted): finitebase,weight1,distinctlawsnonzerogap; weight0singularKLstillbase;prior=approxzeroKL.

Nearesttopics: 026pointnegative-logdensitynotexpectedrelativeKL;014nativeKL;001/002surprisalplusgapdifferentbaseinterpretation.

## fep-029 — Quadratic Bregman Divergence

Explicitφ=x²Bregman is(x-y)²,nonnegative,separating; elementaryconvexcombinationendpointbounds exact.

No generalconvexfunctionBregman/triangle/projectionconvergence. secantlemmahasnospecificconvexfunctiondespitecomment.

Positive/adverse(unexecuted): x1,y0divergence1; squared-distancefailsordinarytriangleat0,1,2:4>1+1.

Nearesttopics: 104genericthreepointcompositionexactd1identification;044Hellinger/alphadivergence notsamefamilygeneraltheorem.

## fep-038 — Bernoulli Fisher Information and Natural Gradient

DifferentiatedBernoullimass,expectedscore0,expectedscore²=1/(p(1-p)),positiveinteriormetric,inversemetricduality exact. CandidateJacobian²=informationandpairingfactorization arealgebraic.

NoactualHasDerivAt018coordinate=038candidateJacobian declaration. Callingthisalreadyprovedcoordinatepullbackoverstatescurrenttypedcontract;endpointtotalizedscoreisnotlimitFisher.

Positive/adverse(unexecuted): p1/2information4,tangent1metric4,naturalgradient1/4; p0totalizedscoreyieldsinformation1notinfinityandexpectedscore-1not0.

Nearesttopics: 004supplieddiagonalmetric vs038computedstatisticalweight;018actualcoordinatefunction needsderivativebridge;101/102generalpullback/CramerRao scopesdistinct.

## fep-044 — Bernoulli Squared Hellinger Divergence

DefinedBernoulliHellinger²withfactor1/2,nonnegative/symmetric/complementinvariant;separation[0,1]exact.

Notallalpha-divergences; squaredHellingerisnotitselftrianglemetric,ordinaryHellingersqrtneedsseparatetheorem.

Positive/adverse(unexecuted): p0,q1divergence1;equalzero; p0,r1,q1/2has1>twoHellinger²legs,so squaredtrianglefalse.

Nearesttopics: 018arc-lengthcoordinatevs044chordalformula,029quadraticBregmanonly; noautomaticmetric/geodesic/alphaparametergeneralization.

## Findings

fep-038: Currentcoordinatepullbackwordinghasnoprovenderivativeidentificationof018coordinate; candidateJacobianisdefineddirectly. The supplied coordinate-Jacobian expression squares to Fisher information and factorizes the metric. Its identification with the derivative of 2*arcsin(sqrt p) requires an additional interior HasDerivAt bridge; no path-length theorem is asserted.

fep-029: Elementaryendpointconvexcombinationlowerbounddoesnotproveconvexfunctionsecantinequality. A convex combination of ordered real endpoints is at least the lower endpoint for nonnegative weight; no general convex function is involved.

## Ranked followups

1. 018/038actualcoordinateJacobianderivative: HasDerivAt (2arcsin(sqrt p)) (1/sqrt(p*(1-p))) for0<p<1,thenactualtypedmetricpullback. No newstatisticalmanifoldneeded. Seam: Real.hasDerivAt_arcsin in Trigonometric/InverseDeriv,Real.hasDerivAt_sqrt in SpecialFunctions/Sqrt,chainrule,sqrt_mul. Estimate: 0.5-1.5daysincludingexactconsumer/rawaxioms.

2. 014ownednativeDPI: NarrowwrapperactualpinnedklDiv_comp_right_lewithitsrealhypotheses;do notassumemissingMathlibDPI. Seam: InformationTheory.klDiv_comp_right_le; inspectexactpinnedcontractbeforeauthoring. Estimate: 0.5-1daywithsourceboundconsumers.

3. 044Hellingermetric/018relation: DefineordinarysqrtHellingerdistanceandprovetriangleorBernoullichord-angleboundusingactualsqrtprobabilityembedding. Squaredtrianglefalse. Seam: Euclideannormtriangle,existingBernoullirootembedding; noallalphaextension. Estimate: 1-3daysboundedcarrierproof.

Exactperrowstatements/hashes/nearestrecordsareinJSON. No S editsorcompilation.
