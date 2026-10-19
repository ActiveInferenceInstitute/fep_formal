# Issue75 independent semantic review: causal-blankets-and-interventions

Source epoch `ef2c99a7ca9b8bd11508c252ec55d01fe9c36699`. Seven exact rows reviewed; cumulative reviewed scope92/168. Retain each current narrowed disposition. No compilation or repository edits performed.

## fep-079: Blanket Factorization and Conditional-Mutual-Information Equivalence

Current disposition: `conditional_proxy`; retained. Primary: `fep079_blanketFactorization_iff_conditionalMutualInformation_zero`.

The weighted sum of finite row mutual informations vanishes iff every row factorizes when every blanket atom is positive. StaticModel already constructs product rows; its specialization remains zero on null blanket atoms. This is not causal identification.

The finite real mutual-information carrier and full blanket support matter; dropping full support permits arbitrary nonfactorizing zero-weight rows. Existing native static-blanket transfer in topics138/139 is real additional content, not absent.

009 is native conditional independence symmetry; this finite zero-CMI characterization is distinct. The declared edge is a pairing with product-mass nonnegativity, not an equivalence to the native predicate.

Unexecuted positive specification: Use a full-support Boolean blanket with independent conditional rows; contrast a positive-weight correlated diagonal row.

Unexecuted adverse specification: Use a point-mass blanket and a correlated conditional row at its null atom: average CMI is zero but pointwise Factorizes fails.

## fep-080: Shared-Conditional Mixture Preservation

Current disposition: `formalized`; retained. Primary: `fep080_sharedConditional_mixture_preservation`.

Joint formation is affine in the input law for one fixed normalized conditional kernel. The weight bounds construct a probability mixture; the algebraic equality itself is distributivity.

Sharing a conditional mechanism is substantive. Arbitrary mixtures of product distributions need not factorize; causal_dynamics already proves the diagonal-Boolean adverse example and shared-left/right sufficient conditions.

019 is native sequential prediction associativity. This new statement concerns convex mixing, and its relation remains a conjunction, not a finite/native embedding proof.

Unexecuted positive specification: Mix distinct Boolean point masses with weight1/2 through a deterministic identity kernel; both input and joint are genuinely mixed.

Unexecuted adverse specification: Mix the two matched Boolean product point masses: the resulting diagonal law has positive mutual information and is not product.

## fep-081: Coupled-Subsystem Blanket Composition

Current disposition: `structural_proxy`; retained. Primary: `fep081_coupledSubsystem_blanketComposition`.

A constructed paired StaticModel has independent paired internal/external conditional rows even when the joint blanket distribution is correlated. The diagonal blanket witness has strictly positive blanket MI.

The paired internal and paired external kernels are authored products across subsystem coordinates. This proves the maintained structural composition, not arbitrary subsystem coupling or marginal subsystem independence.

079 characterizes general finite conditional rows;081 supplies a particular product-row composition allowing correlated blanket coordinates. Retain structural_proxy.

Unexecuted positive specification: Use the supplied correlatedBoolBlanket and nonconstant deterministic subsystem kernels; retain blanket dependence while checking row product.

Unexecuted adverse specification: Let internal and external variables both copy the common correlated blanket: marginal dependence persists although their conditional rows factorize.

## fep-082: Finite Intervention-Kernel Normalization

Current disposition: `formalized`; retained. Primary: `fep082_interventionKernel_normalization`.

The deterministic context-ignoring kernel assigns chosen value mass1 and alternatives0, and normalizes. It is a bounded do-assignment primitive.

A chosen value inhabits the value carrier; a context is needed to evaluate a row. No graph surgery, observational identification or confounder exclusion follows from kernel normalization.

023 is normalization of a supplied reachable native measure. Pairing two normalized objects does not identify their semantics.

Unexecuted positive specification: Bool values and Bool contexts, choose true, exercise true/false masses for both contexts.

Unexecuted adverse specification: An observational conditional can depend on context whereas this kernel cannot; normalization alone does not imply it is an empirically justified intervention.

## fep-083: Non-Descendant Intervention Invariance

Current disposition: `conditional_proxy`; retained. Primary: `fep083_nonDescendant_intervention_invariance`.

Replacing rootLaw by a point mass in OrderedFourNodeModel preserves the independent named non-descendant root law, while the Boolean mediator changes from0 to1.

The authored parent structure has independent root/non-descendant laws, mediator depending only on root and outcome only on non-descendant/mediator. This is a genuine finite intervention calculation conditional on that structure, not inferred from observational CI.

082 is the deterministic intervention primitive;083 integrates a replacement root law into a normalized causal carrier. The009 relation is only a pairing with event monotonicity. Retain conditional_proxy.

Unexecuted positive specification: Consume boolOrderedModel under false/true interventions and compare mediator and non-descendant marginals.

Unexecuted adverse specification: The retained finite_scientific_implications countermodel has equal observational mediator marginals but unequal intervention mediator marginals. Its observed equality is this marginal, not equality of the complete four-node joint.

## fep-084: Ordered Finite Causal Factorization

Current disposition: `formalized`; retained. Primary: `fep084_orderedFiniteCausal_factorization`.

The normalized ordered joint expands exactly to the product of two root laws and the two prescribed parent kernels. The factorization is definitional; normalization follows constructed law/kernel contracts.

This is one four-node ordering with independent exogenous root laws, not a general DAG factorization or discovery theorem. Nonconstant off-support mechanisms alone do not guarantee observed dependence.

027 provides native hierarchical associativity. The current bridge pairs it with this finite factorization; no automatic carrier identification. Retain formalized for the named finite statement.

Unexecuted positive specification: Use independent fair roots, mediator copying root, and XOR outcome; the joint is normalized and has actual dependency.

Unexecuted adverse specification: Allow correlated exogenous roots: the current product-root carrier cannot represent that law without changing the model contract.

## fep-085: Local Markov Property from Ordered Factorization

Current disposition: `conditional_proxy`; retained. Primary: `fep085_localMarkov_factorization_from_ordered`.

localMarkovConditional is defined as the root posterior product the outcome parent-row; primary factorization is rfl and MI zero follows product MI. Importantly the existing reconstruction theorem multiplies by nonDescendantLaw(n)*mediatorEvidence(m) and recovers the actual ordered joint atom.

Positive mediator evidence is required. The named non-descendant value may have zero probability: the construction still specifies a normalized structural row there, but the joint parent event is null. Calling it a uniquely identified conditional distribution requires positive nonDescendantLaw(n) as well. No general d-separation, faithfulness or native CI follows.

079 concerns all rows/full blanket support;085 specializes a prescribed ordered local parent structure. The009 pairing uses trivial-sigma-algebra CI, not an embedding equivalence. Retain conditional_proxy.

Unexecuted positive specification: Use boolOrderedModel at n=false,m=true, each parent factor1/2, total parent mass1/4; consume reconstruction and zero MI.

Unexecuted adverse specification: Choose nonDescendantLaw a point mass, evaluate the other n. Mediator evidence remains positive while joint parent evidence is0; reconstruction is0=0 and cannot identify a unique conditional at that event.

## Wording corrections

- P3 fep-085 `assumption_review`: Positive mediator evidence does not imply positive joint parent evidence; nonDescendantLaw may vanish at the selected parent. Reconstruction is available but vacuous on that null event. Proposed text: All carriers are finite and mediator evidence must be strictly positive. The authored local product row is defined even at a null non-descendant value; interpreting it as an identified conditional on the joint parent event additionally requires positive non-descendant mass. Existing reconstruction recovers the ordered joint atom after multiplying by both parent-evidence factors. This is one maintained ordering, not general d-separation, faithfulness or native measurable conditional independence.

## Ranked bounded follow-ups

1. 085 positive-parent-event consumer: Use existing localMarkovConditional_reconstruction and positive nonDescendantLaw to prove a ratio/uniqueness statement on the actual joint parent event; no new carrier. Estimate: 0.5–1.5 days including typed positive/null controls.

2. 079 support-sensitive characterization: Prove weighted CMI zero iff Factorizes on positive blanket atoms using existing finite sum nonnegativity; full-support theorem becomes a corollary. Existing static/native transfer is already present. Estimate: 0.5–1.5 days.

3. causal claim preservation: Reuse existing observational mediator-marginal countermodel; do not propose an unneeded duplicate or claim equality of complete observed joint laws. Any stronger identifiability theorem needs explicitly observed variables and structural hypotheses. Estimate: review/typed consumer0.5–1 day; general DAG extension is separate research scope.

## Source bindings and limits

The adjacent JSON retains all exact primary/support/boundary statements, complete current maturity and novelty records, touching relations, body hashes and source-file SHA256 values. All examples above are specifications rather than claimed executions. No broad Issue75/scientific/terminal acceptance is granted. Remaining76 topics and dependency gates remain open.
