# Supplement A: Mathematical Positioning and Result-Family Methods {#sec:math_positioning_supplement}

FEP Formal is best located as a collection of conditional mathematical results
about probability laws, information functionals, inference, and control, with
selected connections to stochastic mechanics. Its {{total_topics}} canonical
topic bodies provide theorem proxies; the maintained foundations and
compositions supply reusable mathematical objects and cross-domain results.
This is a many-to-many placement in mathematics. A topic's scientific title,
its carrier, the theorem actually proved, and the intended interpretation are
four different objects of review.

This supplement adopts the result-family organization of the OpenAI
mathematics collection, inspected at commit
`adc7f1241b42e322a6451854ab7e4b4c146bf78a` on 2026-10-06, with the
selected-result source review extended on 2026-10-07 [@openaiMath2026]. That upstream is a collection of manuscripts and supporting
proof artifacts, with results at different verification stages. It is not a
general numerical dependency. Its useful methodological pattern is to connect
a family, individual manuscripts, explicit formalization scope, and selected
challenge statements. The upstream authors' descriptions and deposited proofs
are source material for comparison, not scientific acceptance inherited by
FEP Formal.

## Mathematical objects before disciplinary labels {#sec:math_objects}

A reusable result passport has the following components:

$$
\mathcal R=(X,\mathcal P,\Theta,K,\Phi,A,T,W,B,E).
$$

Here $X$ is the state or outcome carrier; $\mathcal P$ the class of laws;
$\Theta$ a parameter space; $K$ a transition or observation kernel;
$\Phi$ an objective or information functional; $A$ the assumptions;
$T$ the fully quantified claim; $W$ its qualified formal witness;
$B$ the boundary examples; and $E$ the evidence needed to accept it.
Unused components should be marked absent. For example, a diagonal quadratic
form with input weights does not acquire a statistical model merely by being
named Fisher information. A statement about a measurable map does not acquire
a differentiable manifold, stochastic process, or generative interpretation.

This object-first approach places the major subparts as follows. The exact
family crosswalk and exact joined topic contracts are projected from canonical
metadata and semantic records in the accompanying methods slice. Family
domain labels give inherited editorial context, not a certification that each
topic proves a result in every assigned domain. The grouping
below explains the mathematical roles rather than introducing new catalogue
families.

| Subpart | Mathematical home and carrier | What connects it to FEP | Essential boundary |
| --- | --- | --- | --- |
| Variational free energy and Bayesian inversion | Measure-theoretic probability, finite probability, convex variational analysis | Posterior/evidence decompositions, KL remainder, normalized inference | Absolute continuity, finite evidence, and the chosen real or extended-real convention |
| Information geometry and exponential families | Differential geometry of statistical models, convex duality, linear algebra | Score/Fisher pairing, KL/Bregman identification, coordinate pullbacks | Identifiability and tangent constraints; a redundant parameterization may have a null metric |
| Planning, EFE, policy trees | Decision theory, finite dynamic programming, partially observed control | Policy-conditioned prediction, epistemic/pragmatic decomposition, observation-dependent continuation | Model-specific objective, finite horizon, admissible policy class, support assumptions |
| Blankets, interventions, native transfer | Conditional probability, graphical models, selected Gaussian conditioning | Conditional factorization, intervention invariants, finite/native identities | Conditional independence does not alone identify a causal graph or a causal effect |
| Predictive coding and generalized coordinates | Optimization, differential calculus, local dynamical systems | Prediction-error objectives and specified descent directions | Descent does not establish Bayesian correctness, stability of every trajectory, or biological realization |
| Temporal and hierarchical inference | Stochastic kernels, filtering/smoothing, probability on sequences | Chronological prediction/update and conditional inference | Zero evidence and almost-everywhere versions of conditional distributions |
| Collective inference | Product probability, consensus, graph-based averaging, coupled potentials | Additivity under independence, conserved mass, contraction | Independence and contraction hypotheses; no agency conclusion follows from a product law |
| Learning, concentration, calibration, risk | Mathematical statistics, decision theory, learning theory | Bayes-risk comparisons, finite-sample bounds, selected posterior limits | Convergence, calibration, identifiability, and empirical adequacy require different assumptions |
| Thermodynamics and path-space information | Markov processes, semigroups, information-theoretic irreversibility | Finite fluctuation identities, two-state evolution, selected Gaussian path KL | Physical energy units, heat, work, and constitutive laws need additional identification |
| Geometric-mechanics notation | Finite real matrix/skew/symmetric algebra, graph divergence, Frobenius projection, and remainder bounds | Makes proposed mechanics identities and omitted terms explicit | Skewness alone does not remove every divergence term; these results do not establish general symplectic or contact geometry |

: Mathematical roles of FEP subparts, their carriers, connections, and essential scope boundaries. {#tbl:math_subpart_roles}

![Authored family-domain incidence. A filled cell records a selected mathematical context for the family and is inherited by its rows as editorial context; it does not certify that every row proves a result in that domain. The accompanying model retains each row's primary declaration and reviewed scope.](../output/figures/mathematical-family-domains.png){#fig:math_family_domains width=100%}

The formal setting is Lean's dependent type theory plus the declared imports,
definitions, assumptions, and allowed axioms. Scientific semantics is an
additional review obligation. A proof of $A\Rightarrow T$ does not assert
that a biological or physical system satisfies $A$. The same distinction
applies to a model-generated manuscript and to a hand-written proof.

![Maintained semantic dispositions shown by family. The panel copies the semantic review records and preserves the distinction between formalized, conditional, and structural proxies. These labels describe reviewed mathematical reach; this figure does not provide current native compilation or empirical acceptance.](../output/figures/mathematical-semantic-layers.png){#fig:math_semantic_layers width=100%}

The [interactive mathematical map](../docs/mathematical-positioning/mathematical-map.html)
provides the associated tables and boundary values. The family incidence and
semantic panels answer different questions: where a comparison may be useful,
and what the selected row's maintained review permits one to claim.

## Topology, geometry, and embedding spaces {#sec:math_topology_embedding}

There are at least four embedding questions, and answering one does not
answer the others: how finite laws become native measures; how statistical
laws are parameterized; how a full process is observed or reduced; and how
papers or topics are represented for retrieval.

### Faithful probability transfer and kernel composition

The weighted-Dirac map sends a normalized finite mass function to a native
probability measure. `FEP.NativeBlanket.embeddedLaw_injective` establishes
faithfulness on this carrier, while `embeddedLaw_integral_eq_sum` and
`embeddedLaw_map` establish exact expectation and mapping identities.
Representing a discrete law as a native measure does not make its support
continuous. Support-sensitive KL identities require their additional bridge
assumptions even when the map itself is injective.

Finite kernels also have identity and associative composition, with prediction
preserved by composition. These laws support a compositional reading in which
objects are finite carriers and arrows are stochastic maps. Native transfer
can then be assessed through preservation of identities and composition.
This is useful categorical structure to analyze; it is not a claim that the
repository implements a general Markov-category equivalence or a
prior-independent Bayesian-inversion functor. Inversion depends on the prior,
and native conditional laws may be determined only almost everywhere.

### Statistical model geometry

For $n$ outcomes, the probability simplex is

$$
\Delta_{n-1}=\{p\in\mathbb R^n:p_i\geq0,\ \sum_i p_i=1\}.
$$

Its relative interior has strictly positive masses and tangent vectors obey
$\sum_i v_i=0$. On that interior the categorical Fisher pairing is

$$
g_p(v,w)=\sum_i\frac{v_iw_i}{p_i}.
$$

The ambient coordinate count is $n$, whereas the simplex dimension is $n-1$.
A singular ambient representation can therefore coexist with a positive
metric on the actual tangent space. The maintained geometric-optimization
foundation supplies an exact two-outcome tangent-spanning and full-rank
example. The diagonal weighted quadratic form of `fep-004` and the Bernoulli
calculation of `fep-038` should be interpreted through their own assumptions
and the reviewed specialization, rather than as a universal Fisher manifold.

More generally, for an identifiable smooth family $p_\theta$, the score
Gram matrix is

$$
I_{ab}(\theta)=\mathbb E_\theta[
\partial_a\log p_\theta(X)\,\partial_b\log p_\theta(X)].
$$

On full support, differentiability and normalization center finite scores in an
$(n-1)$-dimensional space. Hence a $d$-parameter finite model has
$\operatorname{rank} I\leq\min(d,n-1)$. This is a mathematical derivation
proposed for a future general rank audit, not a newly proved Lean theorem in
this supplement. It explains why declaring extra coordinates cannot create
identifiable statistical dimensions. Natural-gradient interpretation requires
the metric on the admissible tangent, or an explicit quotient, to be suitable
for inversion [@amari1998natural; @amari2016information].

The continuous geometric evidence is stronger than an abstract weighted form,
but narrower than arbitrary manifold geometry. `FEP.GaussianInformationGeometry`
uses the fixed-variance Gaussian mean family and proves native KL, Fisher, and
Bregman identities. `FEP.SmoothInformationGeometry` proves the corresponding
coordinate pullback and constructs a duplicated mean parameterization whose
nonzero null tangent makes its pullback fail positive definiteness. These
results give both a positive instance and a formal non-identifiability
boundary. Multidimensional dual connections, a general statistical-manifold
atlas, and coordinate-invariant mechanics remain separate extensions, as
explained in [@sec:h2_information_geometry].

![Fisher geometry of explicit formula examples. The Bernoulli interior information is $1/(p(1-p))$. For the independent duplicated-mean Gaussian example with variance two, the pullback matrix has eigenvalues zero and one, so the direction $(1,-1)$ is unidentifiable. This explanatory Gaussian example is distinct from the source's duplicated Bernoulli matrix, and the plotted values are numerical analysis rather than a proof receipt.](../output/figures/mathematical-fisher-geometry.png){#fig:math_fisher_geometry width=100%}

### Boundary topology and optimization

The closed simplex includes lower-dimensional support faces. Compactness of
a closed feasible subset and continuity of the actual objective can give an attained
optimum without an interior optimizer or a Lagrange multiplier. The maintained
variational-duality foundation does exactly this for nonempty finite
fixed-source rate-distortion problems:
`FEP.VariationalDuality.isCompact_rateDistortionFeasibleMasses` and
`FEP.VariationalDuality.rateDistortion_exists_minimizer`.
This is substantive topology already present in FEP Formal. It is neither
general strong duality nor a sharp closed-form distortion curve.

Boundary conventions matter independently of compactness. In the maintained
finite information foundation, disjoint Boolean point masses have totalized
cross-entropy zero and totalized finite KL one. Native measure KL for those
disjoint laws is infinite. The bridge in `FEP.DecisionRisk` explicitly requires
relative support for its finite/native KL identity. Thus expressions valid on
the positive simplex must not be extended to its boundary by replacing
infinite divergence with a real number. Entropy can extend continuously to
faces even while a KL comparison becomes infinite.

Weak convergence of laws, convergence of moments, convergence in KL, and
almost-sure convergence along an observation filtration are also distinct.
For instance, $p_\varepsilon=(1-\varepsilon,\varepsilon)$ converges to the
first point mass even in total variation as $\varepsilon\downarrow0$,
but $\mathrm{KL}(p_\varepsilon\Vert\delta_0)=\infty$ for every
$0<\varepsilon<1$. A manuscript must name the topology or mode of convergence
proved. The selected Gaussian semigroup modules and the two-hypothesis
posterior-convergence module do so; their quantifiers must survive any
comparison with upstream probability results.

![Support and convergence on a two-atom carrier. For $p_\varepsilon=(1-\varepsilon,\varepsilon)$, total variation from the first point mass and the supported divergence $\mathrm{KL}(\delta_0\Vert p_\varepsilon)$ tend to zero. The reverse native divergence remains infinite for positive $\varepsilon$. Values illustrate exact finite formulas and an analytic support obstruction; they do not supply a general convergence theorem.](../output/figures/mathematical-support-convergence.png){#fig:math_support_convergence width=100%}

### Observation and process embeddings

An embedding $\iota:Z\to X$ and a projection $\pi:X\to Z$ with
$\pi\circ\iota=\mathrm{id}$ preserve represented states, but do not make
$\pi$ injective on all of $X$. Reduction of dynamics requires a separate
kernel-intertwining statement. For each full state $x$, the projected law of
$K_t(x,\cdot)$ must equal the selected reduced kernel at $\pi(x)$; otherwise
discarded coordinates may affect subsequent predictions.

The H2/H3 Gaussian constructions establish selected native/scalar projection
identities, chronological filtering, finite-grid path identities, and bounded
control comparisons. `FEPComposed.H3CaseStudy.hidden_mode_marginal_nonidentifiability`
also supplies two different full initial laws with the same observed one-time
marginal at every nonnegative time. The stronger
`FEPComposed.H3CaseStudy.hidden_mode_nonidentifiability` supplies identical
finite projected joint paths and noisy-observation joint laws. The full carrier retains the
hidden mode. Accurate projected prediction therefore does not identify the
full latent law. This is a direct answer to the embedding-space question:
the observation image is a smaller statistical experiment, and its fibers
contain distinctions that the selected observation cannot resolve.

![An independent elementary OU obstruction to latent identification. Independent coordinates have decay rates one and two, identity covariance, and initial means $(1,0)$ and $(1,3)$. Full one-time Gaussian KL is $4.5e^{-4t}$, while observation of the first coordinate has zero KL between the hypotheses. This explanatory model uses different coordinates and normalization from the native H3 construction and supplies no H3 receipt.](../output/figures/mathematical-hidden-projection.png){#fig:math_hidden_projection width=100%}

### Corpus representations

The methods slice gives each family an explicit binary incidence vector over
reviewed mathematical domains. Its Jaccard comparison is a deterministic
retrieval aid. Equal vectors mean equal assigned domains at that coarse
resolution; they do not mean equivalent theorem types. This is a feature
representation, not an injective mathematical embedding of the catalogue.

A future text embedding should freeze document units, exact source bytes,
model/tokenizer revision, normalization, distance, and preprocessing. Evaluate
retrieval against held-out human-reviewed associations and negative controls,
including shared terminology with incompatible carriers. Split by family to
avoid counting near-duplicate supporting results as independent tests. A
low-dimensional layout, neighborhood, or apparent cluster does not establish
the topology of a probability model, a theorem dependency, or a scientific
unification. The current methods require no model calls or vector service.
Likewise, cycles or neighborhoods in an authored topic-relation graph do not
establish process cycles or homology classes in a statistical manifold.
The common FEP/upstream coordinates and their projection are developed in
[@sec:math_cross_corpus_embedding], with exact statement analysis in
[@sec:math_statement_language].

## Statistical, dynamical, and physical interpretations {#sec:math_statistical_scope}

Variational inference is posterior approximation by optimization within a
chosen class of laws [@blei2017variational]. The free-energy decomposition
locates FEP Formal within this framework when the posterior, evidence, KL
orientation, and finite/infinite conventions are explicit. An identity defined
as surprisal plus KL should be distinguished from a derivation of that identity
from a generative joint law. The shared finite active-inference carrier makes
many such joins explicit; topic proxies retain their narrower contracts.
KL orientation must also survive the comparison: proper logarithmic risk is
truth-to-report, whereas variational free energy is recognition-to-posterior.
Reversing arguments changes the divergence and its support requirements.

Expected free energy adds a decision problem. Preferences, an observation
channel, policy-conditioned prediction, epistemic value, and admissible
feedback determine the objective. Comparing two EFE formulations requires
matching these objects and the signs and conditioning of every term. The
policy-tree and controlled-Markov results establish exact finite-horizon
instances, including strict feedback advantage. They do not supply arbitrary
continuous-belief or infinite-horizon control. The distinct formulations in
the literature remain a semantic comparison problem rather than an equation
matching exercise [@champion2026reframing].

Statistical conclusions should be reported along separate axes:

| Conclusion | What would support it | What remains separate |
| --- | --- | --- |
| Correct posterior recursion | Normalized joint, evidence law, conditional distribution identity, almost-everywhere boundary | Truth of the selected observation model |
| Posterior consistency | Identifiability, observation assumptions, specified probability law and convergence mode | Uniform rates or consistency under misspecification |
| Calibrated predictions | A declared calibration target and distributional or repeated-sampling argument | Low loss on one deterministic example |
| Better decisions | Same loss, admissible policies, observation budgets, and attained or bounded Bayes risk | Physical or biological utility |
| Causal identification | A causal model plus assumptions distinguishing observationally equivalent mechanisms | Conditional independence or predictive accuracy alone |

: Statistical conclusions require distinct evidence and leave separate interpretive obligations. {#tbl:math_statistical_conclusions}

The current two-hypothesis Gaussian consistency result is under its stated
sampled-parameter joint law. It should not silently become a uniform
fixed-truth consistency theorem or an empirical result. Selected H3 formal
case-study declarations also remain deductive content; the governed empirical
program has its own protocol and acceptance gates.

At the dynamical level, stationary laws, semigroup composition, relaxation,
Lyapunov descent, filtering, and control are different results. A decreasing
potential may justify a stability claim under stated hypotheses without
identifying its value as thermodynamic energy. At the physical level, a KL
value is dimensionless. Converting it to heat requires an energy-per-nat
parameter and a constitutive relation. The exact
`FEPComposed.H3CaseStudy.constitutive_nonidentification` witness holds the
probability and path-information laws fixed while changing hypothetical
assigned heat. Even a proved finite-grid irreversibility value cannot determine
measured heat from the probability model alone.

## Worked result passports and proof strategies {#sec:math_result_passports}

A disciplinary map becomes useful when it changes how a particular statement
is read. The passports below select exact maintained results and expose the
mathematical work each performs. The displayed statements are explanatory
restatements of the named declarations, with carrier assumptions written in
ordinary mathematical notation. They introduce no new canonical topic body,
Lean theorem, native receipt, or semantic disposition. The generated catalogue
appendix remains the authority for complete topic bodies; a rendered compile
status remains governed by [@sec:quantitative_execution_metrics].

### Passport: finite prediction survives native representation {#sec:math_passport_native}

Let $A$ and $B$ be finite carriers with their discrete measurable structures.
A finite law $p$ has nonnegative real masses summing to one, and a finite
kernel $K$ has a normalized law in each row. Write

$$
(K_*p)(b)=\sum_{a\in A}p(a)K(a,b),\qquad
\mathcal E_A(p)=\sum_{a\in A}p(a)\,\delta_a.
$$

The coefficients in the native measure are embedded into
$\mathbb R_{\geq0}\cup\{\infty\}$; the expression above abbreviates that
codomain conversion. The kernel embedding is rowwise:
$\mathcal E(K)(a,\cdot)=\mathcal E_B(K(a,\cdot))$. The substantive
commutation law is

$$
\mathcal E_B(K_*p)=\mathcal E(K)_*\mathcal E_A(p).
$$

`FEP.NativeBlanket.embeddedPredictive_eq_comp` proves this equality.
`embeddedLaw_apply_singleton` recovers every source mass, while
`embeddedLaw_injective` rules out collapse of distinct finite laws. For a real
observable $f$, `embeddedLaw_integral_eq_sum` proves

$$
\int_A f\,d\mathcal E_A(p)=\sum_{a\in A}p(a)f(a).
$$

The proof strategy reduces equality of finite discrete measures to equality
on singletons, expands the finite integral, and uses nonnegativity and
normalization to justify conversion of sums and products. It does not argue
that two implementations produce approximately similar output. The objects
on both sides are exactly the same measures after representation.

There is a second commuting law for chronological composition:

$$
\mathcal E(L\circ K)=\mathcal E(L)\circ\mathcal E(K),\qquad
\mathcal E(\mathrm{id}_A)=\mathrm{id}_A.
$$

Here $K$ acts first and $L$ second. The source witnesses are
`FEP.NativeBlanket.embeddedKernel_comp` and `embeddedKernel_identity`.
Together with `FEP.FiniteKernel.comp_assoc`, these laws make finite prediction
an appropriate candidate for compositional probability semantics. Markov
categories supply a broader published framework for such probability and
conditional-independence reasoning [@fritz2020markov]. The present declarations
provide particular preservation laws, not a completed categorical equivalence.

The boundary example is important: embedding a point mass yields a Dirac
measure, not a smooth Gaussian density. Preserving normalization, expectation,
and composition does not imply convergence of an approximation scheme or
increase the source carrier's dimensionality. Information preservation also
needs its own theorem. In particular,
`FEP.DecisionRisk.weightedDirac_klDiv_eq_finiteKL_of_relativeSupport`
requires that every positive actual mass has positive reference mass. The
probability embedding is unconditional on support; this KL identification is
not. One passport can therefore contain a successful representation transfer
and a refused information transfer at the same boundary.

### Passport: posterior exactness is an attained variational bound {#sec:math_passport_vfe}

The finite active-inference carrier combines an initial state law, a
policy-indexed transition, an observation kernel, preferences, and a policy
prior. For a fixed policy $\pi$, let $p_\pi$ be the predicted state law and
$L$ the observation kernel. A selected observation $o$ has evidence

$$
z_\pi(o)=\sum_s p_\pi(s)L(s,o)>0,
\qquad
r_\pi(s\mid o)=\frac{p_\pi(s)L(s,o)}{z_\pi(o)}.
$$

`FEP.ActiveInference.posteriorState_mul_evidence` proves the reconstruction
identity $r_\pi(s\mid o)z_\pi(o)=p_\pi(s)L(s,o)$. This connects the
posterior to the generative joint, rather than merely giving the symbol
"posterior" to a normalized input law.

For a recognition law $q$, the maintained posterior-form objective is

$$
F(q,o,\pi)=D_{\mathrm{fin}}(q\Vert r_\pi(\cdot\mid o))
           -\log z_\pi(o).
$$

The exact statement is

$$
F(q,o,\pi)\geq-\log z_\pi(o),\qquad
F(q,o,\pi)=-\log z_\pi(o)\ \Longleftrightarrow\
q=r_\pi(\cdot\mid o).
$$

The witnesses are
`FEP.ActiveInference.outcomeSurprisal_le_variationalFreeEnergy` and
`variationalFreeEnergy_eq_surprisal_iff`; `variationalFreeEnergy_posterior`
supplies the attaining law. The proof uses the already established
nonnegativity and zero-separation of the normalized finite divergence. It
does not require an optimizer-existence assumption because the posterior
itself is the explicit witness.

Two limits should be read directly into the statement. First, evidence is
positive: no posterior is constructed by this theorem at a zero-evidence
observation. Second, $D_{\mathrm{fin}}$ is the repository's totalized real
functional. Equality characterizes the posterior even when some posterior
atoms vanish, but a conventional native KL interpretation for an arbitrary
$q$ still needs relative support. A recognition law charging a
posterior-impossible state is exactly where the real and extended-real
interpretations separate.

This passport also separates mathematical exactness from approximation
quality. If a restricted recognition family $\mathcal Q$ excludes the exact
posterior, the displayed equality cannot be attained inside $\mathcal Q$.
Existence of a best element of $\mathcal Q$, convergence of an optimization
algorithm, and the size of its residual gap are further questions. None is
settled by writing $F$ as a KL remainder. This distinction is the bridge from
a formal variational identity to an actual inference method
[@blei2017variational].

### Passport: Fisher positivity identifies admissible directions {#sec:math_passport_fisher}

The finite score carrier stores a law $p$ and score covectors
$s(x)\in\mathbb R^d$ with $\sum_xp(x)s(x)=0$. It does not, by itself,
assert that $s$ was obtained by differentiating a statistical family. Its
Fisher matrix and tangent pairing are constructed from the scores:

$$
I=\sum_xp(x)s(x)s(x)^\mathsf T,\qquad
g(v,w)=\sum_xp(x)\langle s(x),v\rangle\langle s(x),w\rangle.
$$

This Gram form proves symmetry and $g(v,v)\geq0$ without a differentiability
or invertibility premise. Under full support,

$$
g(v,v)=0\ \Longleftrightarrow\
\langle s(x),v\rangle=0\quad\hbox{for every }x.
$$

`FEP.InformationGeometry.fisherMetric_eq_zero_iff` proves this
characterization by reducing a zero sum of nonnegative terms to zero at
every outcome. `fisherMetric_pos` then adds score identifiability: only the
zero vector can annihilate every score. This is why a positive matrix cannot
be inferred solely from the name "Fisher."

For the interior Bernoulli family, the maintained construction discharges
support and identifiability and derives

$$
I(p)=\frac{1}{p(1-p)},\qquad
\nabla^{\mathrm{nat}}F=p(1-p)\,\partial_pF.
$$

The declarations are
`FEP.InformationGeometry.bernoulli_fisherMatrix_entry` and
`bernoulli_naturalGradient_eq`. At $p=1/2$, the information is four. The
duplicated score construction instead has Fisher matrix
$\left(\begin{smallmatrix}4&4\\4&4\end{smallmatrix}\right)$ and a
nonzero null tangent $(1,-1)$. Its failure of identifiability is proved by
`duplicatedFairBernoulli_not_identifiable`, not merely observed in a numerical
eigensolver.

The categorical example explains an apparent discrepancy. Its ambient
two-coordinate score representation is redundant, yet on the simplex tangent
$\{(v_1,v_2):v_1+v_2=0\}$ the pairing is positive for every nonzero
tangent. `FEP.GeometricOptimization.twoCategoricalTangent_spans` proves
that all those tangents are multiples of $(1,-1)$;
`twoCategorical_simplexMetric_fullRank` proves positivity on that actual
one-dimensional carrier. An ambient null direction and an identifiable
statistical tangent are different tests.

The smooth fixed-variance Gaussian family provides a complementary passport.
For $v>0$, its mean-coordinate Fisher information is $1/v$ and

$$
D_{\mathrm{KL}}\bigl(N(m,v)\Vert N(m',v)\bigr)
 =\frac{(m-m')^2}{2v}.
$$

`FEP.GaussianInformationGeometry.FixedVarianceGaussian.klDiv_law_eq_meanSquare`
proves the native extended-real equality after establishing absolute
continuity and integrability of the log likelihood ratio. The source proof
then integrates an affine log ratio under the actual Gaussian law. Its
`meanFisher_eq_naturalFisher_pullback` relates the mean and natural coordinates.
Thus the smooth identity is grounded in density and integration, rather than
obtained by reusing a quadratic formula with a Gaussian label.

These examples motivate an identifiable quotient or tangent restriction for
redundant coordinates. They do not implement that construction for every
score model. A general quotient-compatible natural gradient is an explicit
research problem in [@sec:math_research_packets], where existence and
uniqueness must be stated on the quotient before interpreting a matrix
pseudoinverse as a geometric answer.

### Passport: topology derives a rate-distortion minimizer {#sec:math_passport_distortion}

Let $A$ and $B$ be finite alphabets, $p$ the fixed source law, $d(a,b)$ a
real distortion table, and $D$ a budget. A joint mass table $w$ is feasible
when

$$
w_{ab}\geq0,\qquad \sum_bw_{ab}=p(a),\qquad
\sum_{a,b}w_{ab}d(a,b)\leq D.
$$

The row-sum condition derives normalization of $w$; no second probability
carrier is introduced. Nonnegativity and the fixed source imply
$0\leq w_{ab}\leq p(a)\leq1$. Equalities and the distortion inequality
define a closed subset of this finite coordinate cube. Compactness follows.

The objective is represented by the entropy identity

$$
I_w(A;B)=H(w_A)+H(w_B)-H(w),\qquad
H(u)=-\sum_i u_i\log u_i,
$$

using the continuous zero-safe entropy function on the boundary. Continuity
is proved on the mass coordinates, and the source identifies this expression
with its finite mutual information. If the feasible set is nonempty,
compactness and continuity give

$$
\exists w^*\in\mathcal F_D\quad
\forall w\in\mathcal F_D:\ I_{w^*}(A;B)\leq I_w(A;B).
$$

`FEP.VariationalDuality.rateDistortion_exists_minimizer` is the exact
attainment witness. The proof first obtains a coordinate minimizer, then
reconstructs a normalized finite law and transfers feasibility and minimality.
Neither a preselected optimizer nor strictly positive atoms are supplied.

This supporting result is stronger than the primary structural-proxy
statement of `fep-064`, which combines separately certified component lower
bounds. Keeping both facts visible respects the maintained semantic review:
a strengthened supporting theorem does not silently change the primary
theorem or its disposition.

The Boolean Hamming examples further separate questions often conflated in
informal variational prose. At zero budget, the source derives the unique
perfect-reproduction joint. At half budget, distinct independent joints attain
zero information. At quarter budget, a feasible informative problem has an
attained strictly positive information minimum, proved by
`FEP.VariationalDuality.boolQuarterBudget_exists_positive_minimizer`.
This existence theorem alone does not identify the explicit quarter-crossover
witness as the optimizer. Separately,
`FEP.VariationalDuality.FairBoolean.boolean_closed_exact_minimum` derives
the fair-Boolean natural-log curve `log 2 - binEntropy D` for
$0\leq D\leq1/2$ and proves optimality against every feasible joint.
The general finite-law capability is stated below with its own hypotheses.
No general or interior optimizer uniqueness follows from these value results.

The native-information reading is nevertheless sound here: a joint law cannot
charge an atom where its product marginal is zero. Hence the mutual-information
comparison has the relative-support property even on sparse joints. This is
a useful example of deriving the correct support condition from the carrier
rather than banning all zero atoms.

### Passport: a policy class changes the optimization problem {#sec:math_passport_policy}

A depth-indexed policy tree chooses an action and, at each possible
observation, a continuation tree of one smaller depth. Write $b$ for the
finite belief index, $P(o\mid b,a)$ for the normalized observation law,
$U(b,a,o)$ for its authored update, and $c_h(b,a)$ for the stage cost. The
backward recursion is

$$
V_0(b)=0,\qquad
V_{h+1}(b)=\min_a\left\{
c_h(b,a)+\sum_oP(o\mid b,a)V_h(U(b,a,o))\right\}.
$$

All relevant carriers are finite and the action carrier is nonempty. The
minimum is therefore attained at each node. The proof constructs an optimal
tree recursively, proves its value equals $V_h$, and compares it with every
other tree on the same carrier. The declarations
`FEP.PolicyTrees.optimalPolicyTree_value`, `optimalTreeValue_le_tree`, and
`exists_optimalPolicyTree` encode these separate steps.

An open-loop plan embeds by repeating the same continuation on every
observation branch. `openLoopEmbedding_value` proves value preservation;
`optimalTree_le_openLoop` obtains weak dominance by evaluating the optimal
tree against an embedded plan. The embedding proves containment of one
policy class in another. It is not a statement about every possible feedback
controller or an approximation to an infinite tree.

The non-vacuity witness is exact. In the maintained Boolean two-stage model,
the observation-dependent continuation has value zero, while every fixed
second action in the authored comparison has value one half.
`FEP.PolicyTrees.boolFeedbackTree_value_zero`, `boolOpenLoop_value_half`,
and `boolFeedbackTree_strictlyBetter` make the gap explicit. The theorem
changes the admissible continuation, not the data budget or objective.

The EFE connection requires another layer. A generic real stage cost is not
automatically expected free energy. The generative-model interface and its
branchwise full-support conditions supply the risk/ambiguity identities used
by `FEP.PolicyTrees.policyTree_efe_eq_risk_add_ambiguity`. Similarly, the
policy posterior is not an action kernel until an action interface proves
that the selected action reproduces the policy transition.
`FEP.ActiveInference.actionPredictedState_eq_predictedState` and
`inferSelectActActionMarginal_eq_actionLaw` are the relevant exact seams.
These interfaces explain which mathematical subpart turns prediction into
policy evaluation and which turns selected policies into state transitions.

The selected H3 Gaussian control result extends one aspect of this picture:
observations are real-valued, actions are Boolean, and the second action is a
measurable function of the observation. Its `policy_attainment` result is an
attained two-step risk comparison for that continuous experiment. It does
not establish the finite-tree theorem on all measurable belief spaces.
Matching horizon, observation law, loss, and admissible policy class is part
of the correspondence, not something inferred from both proofs using a
minimum.

### Passport: policy inference minimizes a declared regularized objective {#sec:math_passport_policy_inference}

The one-step generative carrier specifies an outcome preference law $r$.
Under the model's full-support contract---strictly positive predicted state
masses, predicted outcome masses, and preference masses---the maintained EFE
identity is

$$
G(\pi)=H(p_\pi(O),r)-I_{p_\pi}(S;O)
      =D_{\mathrm{fin}}(p_\pi(O)\Vert r)+H_{p_\pi}(O\mid S).
$$

Here the first $H$ is cross-entropy, while the last is conditional entropy
under the policy's actual predicted state/observation joint.
`FEP.ActiveInference.expectedFreeEnergy_eq_risk_add_ambiguity` proves
the equality by combining the joint entropy chain rule with the
risk/cross-entropy identity. Its nonnegativity follows under the same
full-support convention. A zero preference atom is therefore a support
boundary for this interpretation, not permission to totalize the logarithm
and retain the same scientific statement.

Now let $a(\pi)>0$ be a normalized policy prior, let $\gamma>0$, and let
$c(\pi)$ be a finite real cost, which can be the matched EFE. The selected
policy law is

$$
Q^*(\pi)=\frac{a(\pi)e^{-\gamma c(\pi)}}{Z},\qquad
Z=\sum_\pi a(\pi)e^{-\gamma c(\pi)}.
$$

The formal objective over normalized candidate laws is

$$
\mathcal J(Q)=\mathbb E_Q[c]+\gamma^{-1}D_{\mathrm{fin}}(Q\Vert a).
$$

`FEP.EFEPolicy.efeControlObjective_sub_eq_kl` proves the exact gap

$$
\mathcal J(Q)-\mathcal J(Q^*)
 =\gamma^{-1}D_{\mathrm{fin}}(Q\Vert Q^*).
$$

The Gibbs certificate proves $Q^*$ is normalized and strictly positive;
the gap, nonnegativity, and zero-separation prove unique optimality.
`FEP.EFEPolicy.boltzmann_control_posterior_minimizes_efe` states that
conclusion, while `boltzmann_control_posterior_minimal_value` identifies
the minimum as $-\gamma^{-1}\log Z$. This is optimization of a policy law
with a prior penalty. It differs from selecting a single policy that minimizes
$c$, even though the same cost enters both problems.

The equal-cost boundary exposes the prior explicitly.
`FEP.ActiveInference.symmetricBoolModel_policyPosterior_eq_prior`
proves that the symmetric Boolean model returns the supplied policy prior at
every precision. Changing only that prior changes the posterior's selected
mass, as the source's explicit biased-prior witness shows. Thus inferred
policy preference cannot be attributed to epistemic advantage without
checking the costs, prior, and precision. The passport specifies the
normalization and the optimized functional before giving the result a
planning-as-inference interpretation.

### Passport: projection can preserve paths and lose identification {#sec:math_passport_projection}

For the selected Fin4 Gaussian carrier, let $\pi:X\to\mathbb R$ be the
all-ones scalar projection and $K_t$ the full native transition kernel.
The scalar transition $\overline K_t$ satisfies the rowwise relation

$$
\pi_*K_t(x,\cdot)=\overline K_t(\pi(x),\cdot)
\quad\hbox{for every full state }x.
$$

`FEPComposed.H3CaseStudy.arbitrary_state_projection_native` proves this
intertwining for arbitrary full states, including states outside the scalar
embedding image. Integrating the identity transfers an arbitrary initial
probability law to the reduced evolution. Recursively composing the kernels
then gives a stronger joint statement. If $\Pi$ projects every coordinate
of a finite path, `full_native_path_projection` proves

$$
\Pi_*\mathbb P^{\mu}_{t_0,\ldots,t_h}
 =\overline{\mathbb P}^{\pi_*\mu}_{t_0,\ldots,t_h}.
$$

The proof proceeds by finite-path induction, transporting each composition
product through the observation map. It does not infer equality of path laws
from equality of their one-time marginals. Repeated times are retained through
the actual zero-time kernels.

There is still no inverse identification of $\mu$ from the projected law.
The hidden-mode construction shifts the full Gaussian mean in a nonzero
direction annihilated by $\pi$. Its `hidden_mode_nonidentifiability`
theorem proves that two distinct native initial laws generate identical
projected finite joint paths and the selected noisy-observation joints.
Consequently, collecting those particular observations cannot distinguish
the two initial hypotheses, even though their full-state means differ.

This is an obstruction to a proposed inference task, not an obstruction to
all possible measurements. An added channel that observes the hidden mode
would define a different experiment. A valid extension would have to specify
that channel, prove its normalization, and show that the previously equal
observation laws now separate. Calling a learned low-dimensional vector a
"latent state" does not discharge those obligations.

### Passport: information along a selected Gaussian grid {#sec:math_passport_grid}

The same H3 source constructs an actual nonstationary full Gaussian law,
projects its chronological joint at a selected time grid, and compares that
law with its coordinate-reversed joint. The result is

$$
D_{\mathrm{KL}}(P_{\mathrm{grid}}\Vert P_{\mathrm{rev}})
 =2(1-e^{-1})>0.
$$

This expression restates
`FEPComposed.H3CaseStudy.finite_grid_kl` with the source's
$\mathtt{controlDecay}=e^{-1/2}$. The grid times are $0,1/4,1/2$ and
the initial law is the authored nonstationary Gaussian. The proof identifies
the native joint, transports KL through invertible measurable coordinates,
and computes Gaussian product KL in innovation coordinates. Thus the scalar
value is derived from the path law; it is not a supplied log-determinant
certificate.

`finite_grid_support` separately derives absolute continuity and log-ratio
integrability. Those premises are not automatic for every time grid. On the
repeated grid $0,0,1/4$, `singular_grid_infinite_kl` proves native KL is
infinite by an actual support obstruction. On the all-zero grid,
`all_zero_grid_kl` proves zero. Repetition alone therefore neither guarantees
finiteness nor forces infinity; the induced forward and reverse supports
must be compared.

A selected finite-grid law is a measure on a finite product of real state
spaces. It does not supply an unrestricted continuous-path density, a
Girsanov theorem, or a physical entropy-production rate. In particular,
`constitutive_nonidentification` keeps this probability comparison fixed
while changing hypothetical energy-per-nat assignments. A positive path KL
is evidence of the named distributional distinction; measured heat requires
more structure.

### Passport: a mechanics identity keeps its remainder {#sec:math_passport_mechanics}

The geometric-mechanics family provides a compact example of how a formal
manuscript should expose an attractive but incomplete cancellation. Let $Q$
be a finite skew-symmetric matrix, $H$ a symmetric matrix, $g$ a real vector,
and $DQ$ the explicitly supplied derivative-role data. The source's weighted
divergence expression expands as

$$
\mathcal D=\operatorname{tr}(QH)
          +(\operatorname{div}Q)\cdot g
          +(Qg)\cdot d\log p.
$$

Under the stated coupling $d\log p=-g$, skewness cancels the quadratic
term and skew/symmetric pairing cancels the trace term. What remains is

$$
\mathcal D=(\operatorname{div}Q)\cdot g.
$$

`FEP.GeometricMechanics.fep168_weightedDivergence_eq_remainderDot`
proves that identity. The data called $H$ and $DQ$ are finite matrix inputs;
this theorem does not independently derive them by differentiating a smooth
field. An additional orthogonality premise or the supplied condition $DQ=0$
(the source's constant-$Q$ input contract) makes the
remainder vanish. The source's two-node graph witness instead shows a
candidate current with nonzero node divergence, so plain skewness cannot
justify an unconditional solenoidal drop.

The residual can be controlled rather than erased. Writing
$r=\operatorname{div}Q$,
`FEP.GeometricMechanics.fep168_remainder_sq_budget` proves

$$
\mathcal D^2\leq(r\cdot r)(g\cdot g).
$$

The proof is finite Cauchy--Schwarz, and an aligned witness attains equality.
This yields a quantitative statement with observable premise slots: a bound
on the transport-divergence vector and a bound on the objective gradient.
It is stronger scientific guidance than assuming the omitted term is zero.

The same owner also separates a constructed Hessian-role matrix from a
smooth Hessian theorem. Symmetrization
$S(H)=(H+H^\mathsf T)/2$ is a deterministic projection. For symmetric
$M$, `FEP.GeometricMechanics.fep167_frobenius_pythagoras` proves

$$
\lVert H-M\rVert_F^2=\lVert H-S(H)\rVert_F^2+\lVert S(H)-M\rVert_F^2,
$$

and `fep167_projection_unique` identifies the unique Frobenius minimizer.
The proof splits the residual into orthogonal skew and symmetric parts.
Nothing in this minimization supplies a noise model or an estimator-risk
bound. A least-squares formula can be exact matrix geometry without being
a statistical guarantee.

## Transfer across finite, native, and smooth regimes {#sec:math_regime_transfer}

The passports show that "more general mathematics" is not a single ordered
scale. At least four transformations occur, and each preserves different
structure.

| Transformation | Preserved structure that needs a witness | Common failed inference |
| --- | --- | --- |
| Representation of a finite law as a native measure | Singleton mass, normalization, integration, mapping, kernel composition | Native syntax makes a discrete support continuous |
| Coordinate change in a statistical family | Law equality or injection, Jacobian transport, Fisher pullback, oriented divergence | Additional coordinates create additional identifiable parameters |
| Observation or coarse-graining | Pushforward law and, for dynamics, kernel/path intertwining | Exact reduced prediction identifies the full latent system |
| Limit of a family of experiments | Specified convergence mode, uniform or integrable control where required | Finite-grid identities imply a continuous-path or physical limit |

: Four mathematical transfers, the structure each must preserve, and a common failed inference. {#tbl:math_regime_transfers}

The first is an exact representation on the same atom carrier. The second
can be invertible, redundant, or many-to-one. The third intentionally loses
distinctions and must account for that loss. The fourth changes the problem
by introducing a limiting parameter. Their obligations should not be merged
under a generic "embedding" heading.

### Commuting statements before transport of conclusions {#sec:math_commuting_statements}

For deterministic maps $f:A\to B$, the finite/native square is the
identity

$$
\mathcal E_B(f_*p)=f_*\mathcal E_A(p).
$$

For statistical reparameterization $\theta=\psi(\eta)$, the geometric
square is expressed through its derivative:

$$
I_\eta=J_\psi^\mathsf T I_\theta J_\psi,
\qquad
g_\eta(u,v)=g_\theta(J_\psi u,J_\psi v).
$$

`FEP.InformationGeometry.pullbackMetric_comp` proves that successive
Jacobian pullbacks agree with the composite pullback. Positivity under an
injective Jacobian is a different theorem from nonnegativity under an
arbitrary Jacobian. Coordinate natural-gradient equivariance requires the
invertibility premises retained by `fep-103`; a rank-deficient map cannot
inherit an unrestricted inverse-metric statement.

For observation reduction, the square concerns stochastic transition rows:
$\pi_*K_t(x,\cdot)=\overline K_t(\pi(x),\cdot)$. The H3 proof shows
why the rowwise statement is useful: it is strong enough to derive finite
joint-path consistency for arbitrary initial probability laws. A fitted
agreement of one-time means is much weaker and cannot replace the square.

For Bayesian inversion, the relevant reconstruction is instead a joint
measure identity:

$$
P_O(do)\,P(ds\mid o)=P_S(ds)\,P(do\mid s),
$$

with coordinate order stated explicitly. A native inverse kernel is often
unique only under predictive-almost-everywhere equivalence. Composition of
Bayesian inverses must carry the intermediate prior induced by the first
prediction; it is not ordinary inversion of a bijective state map. The
measure-level compositions in the catalogue preserve these priors and
almost-everywhere qualifications.

### Quantifiers and clocks distinguish statistical results {#sec:math_quantifiers_clocks}

Several valid convergence statements occur in this project, but they concern
different sequences. An iteration index measures repeated application of an
authored update. A time parameter indexes a semigroup. A sample size indexes
an experiment. A filtration indexes the information acquired along a sampled
path. Substituting one clock for another changes a theorem.

For example, the exact scalar quadratic update has multiplier $1-\eta$.
The closed interval $0\leq\eta\leq2$ gives nonincreasing energy, while
$0<\eta<2$ gives scalar convergence. A constant unobserved coordinate can
remain arbitrary throughout that descent. The Gaussian semigroup instead
proves convergence of a selected state law under real time, and bounded
continuous observables have their own convergence statements.

The H3 finite known-prior batch experiments have an explicit posterior-mean
MSE:

$$
\mathbb E_n[(\widehat\theta_n-\theta)^2]
 =\frac{\sigma}{2\sigma+n},\qquad \sigma>0.
$$

Here $\sigma$ denotes the source's positive observation-noise variance
parameter, not a standard deviation. `FEPComposed.H3CaseStudy.consistency_mse`
proves the identity, `consistency_tail` transfers it to a Chebyshev bound,
and `consistency_limit` proves consistency in probability across the authored
finite experiments. The source explicitly makes no almost-sure or
changing-latent-state claim at this seam.

By contrast, `FEP.PosteriorConvergence.posteriorProbability_consistent_ae`
is an almost-everywhere statement on the sampled-parameter observation path
of a two-hypothesis Gaussian-mean model. Both are consistency results, but
their probability spaces, estimands, and quantifiers differ. Neither is
empirical acceptance of a recorded data set.

Even the word "uniform" needs an argument slot. Uniformity over finite
topic IDs, over outcomes at a fixed parameter, over parameters in a compact
set, and over all admissible data-generating laws are different requirements.
A source theorem quantified over one of them should never be summarized as
uniform over the others.

## Association, derivation, and theorem pairing {#sec:math_association_evidence}

The mathematical map is most useful as a typed relation system. A shared
carrier can motivate an adapter; a shared objective can motivate a comparison;
a shared keyword motivates retrieval only. Their evidential strengths depend
on the exact statement, not on visual proximity in an atlas.

A derivational relation consumes a result or identifies two mathematical
objects under explicit premises. A formal pairing gives both endpoint laws
in one checked theorem without proving an implication between them. A
conceptual relation records why a comparison is interesting. A blocker names
a missing capability. The maintained relation contract distinguishes these
four roles, and the methods preserve their labels.

An instructive example is
`FEPComposed.fep051_rn_reconstruction_refines_fep017`. Its conclusion
contains Radon--Nikodym reconstruction and posterior joint reconstruction as
a conjunction. Its proof invokes the two endpoint laws. That is useful
co-location of measure-level evidence, but it does not prove that
Radon--Nikodym reconstruction alone constructs a posterior kernel in every
measurable space. Standard-Borel and finite-kernel assumptions remain
visible on the posterior side.

Conversely, the finite/native prediction passport proves an actual
commuting equality. An information identity added on top requires relative
support, and a blanket transfer requires identification with the native
conditional-independence predicate. These are different bridges even when
they use the same embedding function.

This distinction changes graph analysis. Paths consisting of conceptual
edges cannot be composed as proofs. Pairing edges should not be treated as
directed implications. Formal edges still need compatible carriers and
assumptions before chaining. A transitive path in a drawing is therefore a
candidate proof route whose middle objects must be checked, not a new theorem
already certified by the graph.

![Authored formal derivations aggregated by family. Rows denote source families and columns denote target families; each count records maintained topic edges with qualified witnesses. The {{formalism.relation_counts.formal}} edges retain their exact endpoints in the accessible table. Family aggregation does not compose relations into new theorems.](../output/figures/mathematical-authored-relations-formal.png){#fig:math_formal_relations width=100%}

![Authored formal pairings aggregated by family. The recorded source and target orientation locates {{formalism.relation_counts.formal_pairing}} checked pairings; it does not turn a conjunction or co-location of endpoint results into a directed implication. Exact topic endpoints and qualified witnesses remain in the accessible edge table.](../output/figures/mathematical-authored-relations-formal-pairing.png){#fig:math_formal_pairings width=100%}

![Authored conceptual associations aggregated by family. Rows and columns retain the source and target orientation of {{formalism.relation_counts.conceptual}} maintained associations. These edges supply research context rather than theorem witnesses. Editorial upstream affinities remain separate from every maintained relation layer.](../output/figures/mathematical-authored-relations-conceptual.png){#fig:math_conceptual_relations width=100%}

The same discipline resolves several common FEP associations. A state
partition does not establish conditional independence. Rowwise blanket
factorization does not establish a factorized stationary law. A stationary
blanket does not select a recognition map or a descending objective flow.
Observational independence does not identify a causal intervention. The
finite scientific-implications owner includes explicit countermodels for
these transitions, and the H3 hidden-mode and preference counterexamples
extend the obstruction method to the selected smooth carrier.

## Relation to selected upstream result families {#sec:math_upstream_affinities}

An upstream result becomes useful when it exposes a missing mathematical
interface, not merely a shared word. The comparisons below use the pinned
manuscript statements and their deposited scope records [@openaiMath2026].
They distinguish a paper's theorem, a linked challenge specification, and
the acceptance evidence available here. No upstream solution closure was
compiled or Comparator-checked by this integration. A scope record therefore
reports what the upstream formalization is described as proving; it does not
supply an FEP native receipt or an imported cross-repository theorem.

A family is also not a single theorem. The logarithmic Sobolev theorem and
its transport corollary have different conclusions; Gaussian replica bounds
and streaming lower bounds have different quantifiers; finiteness of an
Ising variational value differs from convergence of spherical pressure.
These result units remain separate even when they share one family ID.

| Upstream family | Useful affinity | Required separation |
| --- | --- | --- |
| 093: logarithmic Sobolev inequalities | Entropy, gradients, log-concavity, Gaussian/OU relaxation, and uniform constants | The inspected family has no linked Lean scope record; an affinity supplies no imported entropy-dissipation theorem |
| 140: memory/sample bounds and Gaussian posterior replicas | Conditional information, observation fibers, Gaussian inference, computational limits of learning | High-dimensional noiseless finite-memory regression differs from the selected FEP Gaussian filtering and two-hypothesis carriers |
| 221: diluted spin-glass variational formulas | Gibbs laws, variational pressure, random systems, collective behavior | Thermodynamic-limit/random-disorder results do not follow from finite product-agent additivity |
| 222: perceptron free energies | Log-partition functionals, variational values, finite versus asymptotic systems | The Ising scope records supporting finiteness only; the spherical scope has different convergence claims and hypotheses |
| 360: weak MTW and transport geometry | Cost geometry and regularity of transport potentials | A KL/Fisher identity does not establish optimal-transport curvature or MTW conditions |
| 374: stability of Brenier maps | Sensitivity of transport maps to perturbations of laws | Posterior stability and transport-map stability use different objects, norms, and regularity |
| 131: mixing of degree-preserving graph switches | Finite Markov kernels, spectral gaps, quantitative convergence | A chain-specific polynomial mixing bound is stronger than a generic data-processing inequality and differs from an exact sampler |
| 139: log-concave sampling query complexity | Convex potentials, Gibbs measures, computational passports | Exact real oracle queries do not measure arithmetic, storage, or bit running time |
| 148: entropy-rate dimension of self-similar laws | Quotients of symbolic descriptions, overlapping representations, geometric dimension | Entropy of exact composed maps differs from entropy of their address labels; dimension one does not assert absolute continuity |
| 145: multiple mixing for one transformation | Temporal dependence, joint laws, conditional independence, inverse limits | Stationarity and one-time convergence differ from higher-order mixing; a qualitative mixing limit supplies no finite-sample rate |
| 327: Markov type and superreflexivity | Metric control of reversible walks, Banach geometry, equivalent norms | A bound for every finite chain and every map differs from one selected semigroup or a corpus projection |
| 332: metric Markov cotype of $\ell_1$ | Nonlinear smoothing of point configurations, cut representations, Lipschitz extension | Existence of modified points in the ambient space does not preserve an arbitrary subspace, probability simplex, or inference semantics |

: Selected pinned upstream result families, their editorial affinities, and the hypotheses separating them from FEP results. {#tbl:math_upstream_affinities}

These associations are editorial affinities. No row adds an upstream import,
checked cross-repository theorem edge, or accepted proof. In particular,
statistical-mechanical pressure, variational Bayesian free energy, and the
expected-free-energy policy objective can share algebraic motifs without
being the same functional. Temperature, normalization, scaling with system
size, and the underlying probability ensemble must be stated before moving
between them.

### Entropy inequalities: a quantitative route beyond monotonicity {#sec:math_upstream_lsi}

The selected family-093 manuscript, *A dimension-free logarithmic Sobolev
inequality for subgaussian log-concave measures* [@openaiMathLSI2026], states its main theorem for
a centered log-concave law $\mu$ with a Lebesgue density on $\mathbb R^n$,
$n\geq1$. For $X\sim\mu$, assume an $a>0$ such that every unit direction
$\theta$ satisfies

$$
\mathbb E\exp\!\left(\frac{\langle X,\theta\rangle^2}{a^2}\right)\leq2.
$$

Its statement `thm:main` supplies one absolute, dimension-independent
constant $C$ with

$$
\operatorname{Ent}_\mu(f^2)
 \leq Ca^2\int\lVert\nabla f\rVert^2\,d\mu,
 \qquad f\in C_c^\infty(\mathbb R^n).
$$

The hypothesis is stronger than a covariance bound: it controls the tails of
every linear functional. It does not require a smooth density or a strictly
positive lower bound on the potential Hessian. The separately stated
`cor:intro-transport` bounds $W_2(\nu,\mu)^2$ by $Ca^2H(\nu\mid\mu)$ for
every $\nu\in\mathcal P_2(\mathbb R^n)$, with native relative entropy that
can be infinite. The inspected catalogue has no linked Lean scope record
for this family. Both statements are compared as manuscript results.

The paper's proof route is substantially more than Gaussian integration.
It normalizes a hypothetical sequence violating the inequality, constructs
an extremal vector field, compares its prediction under independent Gaussian
observations, and derives near-equalities for a hierarchy of symmetric
tensors. A matrix-valued fluctuation law then produces incompatible upper
and lower information bounds. This route links analysis, probability,
spectral structure, and conditional information; copying a scalar Gaussian
normalizer from FEP would not reproduce the argument.

The precise FEP seam is entropy decay. The native declaration
`FEP.MarkovSemigroup.NativeKernelSemigroup.nativeKL_to_invariant_nonincrease`
obtains monotonicity from a Markov semigroup and an invariant reference.
Neither an entropy derivative nor a uniform decay rate is assumed there.
For a proposed smooth reversible diffusion adapter, write
$\nu_t=r_t\mu$ and $H_t=\int r_t\log r_t\,d\mu$. If the adapter separately
establishes the entropy-dissipation identity

$$
\frac{dH_t}{dt}=-\mathcal I_t,\qquad
\mathcal I_t=\int r_t\lVert\nabla\log r_t\rVert^2\,d\mu,
$$

and, for $L>0$, extends an inequality $\operatorname{Ent}_\mu(f^2)\leq L
\int\lVert\nabla f\rVert^2d\mu$ to $f=\sqrt{r_t}$, then

$$
H_t\leq\frac L4\mathcal I_t,
\qquad H_t\leq e^{-4t/L}H_0.
$$

This is a conditional derivation and a proposed proof obligation, not a new
repository theorem. It fixes the coefficient convention, the orientation
to the invariant law, and the finite-initial-entropy requirement. The
adapter must justify generator provenance, integration by parts or boundary
conditions, square-root approximation in the energy domain, and the
differential comparison. Monotonicity alone cannot supply the rate: the
identity Markov semigroup leaves every law unchanged. Likewise, a linear
subgaussian assumption cannot be replaced by an informal assertion of
"Gaussian-like" behavior in observations.

### Posterior replicas: information on observation fibers {#sec:math_upstream_replicas}

Family 140 makes the distinction between accurate inference and feasible
information retention especially sharp. In *Posterior replicas and
conditional information in Gaussian regression* [@openaiMathReplicas2026], the signal is a unit vector
$S\in S^{d-1}$, independent Gaussian rows form a matrix $A$, and exact
labels are $AS$. A finite message $W$ is produced from $(A,AS)$ by a
measurable kernel. An independent Gaussian matrix $B$ supplies side
information $(B,BS)$ to the analyst, not to the learner producing $W$.
For a prior $p=f\sigma_d$ with $0\leq f\leq L$, the named Gaussian block
theorem states, at its prescribed row and replica counts and for sufficiently
large dimension,

$$
I(S;W\mid B,BS)
 \leq\frac{H(W)}t+Cd+C\log(2+\log L),
$$

where $k=2\lfloor d/16\rfloor$, $t=k+1$, and $B$ has $4k$ rows. Entropy
is in nats. These counts are part of this result unit, rather than free
parameters of the displayed bound.

The proof resamples posterior replicas conditionally on the common data.
Each replica preserves the original signal-message pair law, while the
replicas remain correlated after the common data are forgotten. If $K$ is
their total correlation and $K'$ the conditional total correlation after
the independent projection, the key comparison is

$$
tI(S;W\mid B,BS)\leq H(W)+K-K'.
$$

The difference $K-K'$ is the information lost under that particular
observation map. Bounding $K$ alone would discard the useful dependence
remaining visible in the side information. The equal-label calculation
includes an inverse Gram-volume factor, then a projected comparison and a
dyadic integrability estimate. Exact fiber normalization and exceptional
sets are therefore central; an informal conditional-density expression at
an exact, probability-zero label cannot replace them.

The separate streaming statement assumes a uniform sphere prior,
$M(d)=o(d^2)$ bits of persistent memory, fresh independent Gaussian rows,
measurable randomized updates, a prescribed deterministic horizon, and
angular recovery with probability at least $2/3$. It concludes
$T(d)\geq c d\log(1/\epsilon(d))$ eventually for
$0<\epsilon(d)\leq1/10$. The companion *Memory and precision in noiseless
Gaussian regression* records a fixed-$A$ version for $M\leq Ad^2$, with a
constant depending on $A$. These are separate quantifier patterns. The
selected replicas challenge retains the subquadratic-memory streaming
statement; one should not silently substitute the fixed-$A$ result or a
different success threshold.

The inspected challenge declaration
`OAI.PosteriorReplicas.source_main` conjoins its separately defined
equal-label, replica-block, and streaming propositions. That conjunction
specifies several endpoints; it does not make a finite FEP posterior identity
imply the block or streaming bounds. The challenge's proof hole is part of
its specification role, not an accepted proof in this integration.

This comparison suggests two FEP extensions. First, posterior reconstruction
and prior-dependent inversion could support a general replica identity,
with an actual disintegration theorem and joint-law preservation. Second,
an observation-fiber information budget could quantify what a compressed
belief state retains. The current weighted-Dirac bridge, Gaussian
conditioning, and hidden-mode obstruction provide useful endpoint objects,
but not the sphere-prior equal-label measure, multi-replica determinant
estimate, finite-memory learner model, or streaming iteration. The current
H3 batch MSE formula averages over its sampled prior and noisy finite
experiment; it gives no memory lower bound. Conversely, without a storage
constraint, $d$ independent exact Gaussian rows determine the unit-vector
signal almost surely. Identifiability of a model and efficiency under a
memory constraint are distinct questions.

### Spin-glass pressure: finite Gibbs algebra versus a limit theorem {#sec:math_upstream_spin}

For family 221, *The Mézard--Parisi formula for diluted spin glasses*
uses an even interaction arity $p\geq2$, positive interaction density,
Poisson-distributed interactions, independent disorder and site indices,
and an integrable interaction/field envelope. Its factorization and
positivity assumptions are explicit Panchenko--Talagrand conditions, rather
than arbitrary dependence between agents [@openaiMathDilutedSpin2026]. With

$$
Z_N=\sum_{\sigma\in\{-1,1\}^N}e^{-H_N(\sigma)},
\qquad F_N=\frac1N\mathbb E\log Z_N,
$$

the manuscript's `main:theorem` identifies the limit of $F_N$ with an
infimum over finite hierarchy depths and trial laws. The associated
`OAI.DilutedSpinGlass.mezard_parisi` in the `DilutedSpin.lean` challenge
specifies the model, admissibility, and
variational equality. It does not require that the infimum be attained by
one finite hierarchy or describe a limiting infinite-depth Gibbs state.

The proof obtains an interpolation upper bound, selects cavity reservoirs
with vanishing pressure perturbations, uses finite probability trees to
control branching patterns and multioverlaps, then recovers independent
cavity messages for the lower bound. Removing boundedness requires estimates
uniform over trial laws. Product-agent additivity does not do this work:
the interacting Hamiltonian is not an independent sum of two agent models,
and the disorder expectation and $N^{-1}$ normalization survive every
comparison.

There is nevertheless an exact local algebraic connection. For a finite
state set, a positive normalized reference $a$, a real energy $E$, and
$\beta>0$, set $Z=\sum_xa(x)e^{-\beta E(x)}$ and
$g(x)=a(x)e^{-\beta E(x)}/Z$. In the supported regime, the FEP Gibbs
certificate yields

$$
\mathbb E_q[E]+\beta^{-1}D(q\Vert a)
 =-\beta^{-1}\log Z+\beta^{-1}D(q\Vert g).
$$

With the uniform reference on $\{-1,1\}^N$ and $\beta=1$, the normalized
partition is $2^{-N}Z_N$. Its minimum free-energy value is therefore
$-\log Z_N+N\log2$, not $F_N$. Division by $N$, a sign change, and a
disorder expectation relate the functionals. This calculation explains both
the common KL motif and the missing thermodynamic argument. A transfer
packet would construct the random finite certificate for each realization,
prove its measurable and integrable dependence on disorder, and then add the
interpolation and limit bounds. It would not infer the limit by calling two
objectives "free energy."

### Perceptrons: well-defined values and pressure convergence {#sec:math_upstream_perceptron}

The family-222 scope distinguishes two mathematical achievements. For the
Ising perceptron, the recorded supporting formalization proves that the
infimum over admissible overlap paths is a finite real value for
nonnegative pattern density and a bounded continuous log-potential. It does
not record convergence of the finite-system pressure or the paper's broader
bounded-Borel extension. For the spherical perceptron, the recorded scope
includes finiteness and pressure convergence in expectation and in
probability for positive pattern density, positive inverse temperature,
and bounded continuous single-pattern potential. These conclusions are
not interchangeable, and neither implies almost-sure convergence without
another argument.
The spherical manuscript is the selected primary result record
[@openaiMathSpherical2026].

The spherical declaration
`OAI.SphericalPerceptronFreeEnergy.main` also keeps its Brownian-law
interface and both convergence conclusions explicit. Its existential real
limit is identified with an extended-real variational value before the
expectation and probability statements. This is stronger than simply
storing a real-valued candidate formula, and narrower than replacing its
bounded continuous potential by every Borel potential.

The bounded-potential hypothesis supplies a basic comparison before any
limiting formula. If a normalized base law carries a sum of $m$ terms of
absolute value at most $\beta B$, then

$$
e^{-m\beta B}\leq Z\leq e^{m\beta B}.
$$

For an unnormalized counting measure, its total mass contributes an
additional log-normalization term. This bound explains why a finite
log-partition value is plausible under the chosen convention. It does not
prove convergence as $m,N\to\infty$, nor identify the variational formula.
The spherical proof treats the nonlinear pattern Hamiltonian through its
own structure rather than substituting a Gaussian-process covariance
formula. Perturbations establish overlap identities and a marked cascade
structure. The upper bound uses a density--field contact comparison; the
lower bound combines a two-pattern covariance calculation, tangential
spherical integration, cavity increments, and telescoping. Approximation
and concentration then complete the matching variational bounds. The
independent Gaussian remainder in the one-pattern evaluation remains even
when replicas share a leaf. An FEP adapter would need the spherical carrier and reference measure,
independent Gaussian patterns, exact size and temperature normalization,
and the overlap-path variational domain. A finite Gibbs optimizer or a
finite rate-distortion minimizer is a different object from this random
large-system limit.

### Transport geometry: curvature of a cost is additional structure {#sec:math_upstream_mtw}

Family 360 illustrates why information geometry and transport geometry
cannot be equated by a word match. The source fixes a smooth connected
compact Riemannian manifold without boundary, of dimension at least two,
and uses $c(x,y)=d(x,y)^2/2$. Its weak MTW condition controls a specified
mixed fourth derivative of this cost at smooth cost pairs, on orthogonal
tangent directions. The companion *Global Support and Convex Injectivity
Domains under Weak MTW* derives convex injectivity domains and global
supporting inequalities without adding prior convexity or nonfocality.
That geometric foundation is a separate result unit.
Its inspected declaration is
`OAI.WeakMTWGlobalSupport.current_main_convexity`; its carrier is a
Riemannian manifold with the stated geometric instances, not an arbitrary
finite Fisher matrix.

The transport result [@openaiMathBiHolder2026] then fixes density bounds $0<\lambda\leq\rho_i\leq
\Lambda$ almost everywhere. On this fixed manifold, it records a
homeomorphic representative of the almost-everywhere unique optimal map,
with a common Hölder exponent and constant for both the map and its inverse.
The constants may depend on the manifold and density bounds; the statement
does not supply an explicit exponent or uniformity across varying metrics.
Its proof controls lifted gap sections, compares spectral behavior near
conjugate pairs, and derives a class-wide oscillation bound before obtaining
the two continuity estimates. The geometric foundation and the density
argument have distinct hypotheses.

FEP's Fisher pullback is a quadratic form on statistical tangents. The MTW
condition is a fourth-order property of a transport cost coupling two points.
One does not determine the other. A proposed connection must first construct
a Riemannian statistical carrier with actual derivative provenance, specify
the transport cost, and prove its MTW and global support properties. Positive
Fisher information alone supplies none of those fourth-order estimates.
Moreover, an observation projection with a nontrivial hidden fiber is not a
homeomorphism and cannot inherit the inverse estimate. The H3 hidden-mode
example thus supplies an immediate obstruction to interpreting every belief
reduction as a regular transport coordinate.

### Brenier stability: laws, representations, and sharp exponents {#sec:math_upstream_brenier}

In family 374, *Sharp One-Third Stability of Brenier Maps* [@openaiMathBrenier2026] fixes a compact
convex body $K\subset\mathbb R^d$ with nonempty interior, $d\geq2$, a
uniform source $\rho$, and a nonempty compact target set $Y$. For arbitrary
Borel targets $\mu,\nu$ supported on $Y$, the manuscript's
`main:stability` states

$$
\lVert T_\mu-T_\nu\rVert_{L^2(\rho)}
 \leq C(K,Y)W_2(\mu,\nu)^{1/3}.
$$

The quadratic-cost optimal maps are defined up to source-null sets. Targets
may be atomic or singular, and the constant does not acquire dependence on
atom masses or separations. The separately specified sharpness result rules
out every larger uniform exponent, including $1/2$, already for a cube and
three-atom targets.

The proof first controls cell-mass and cell-moment variations for finite
maxima of affine functions. It obtains potential stability through a
weighted graph-Laplacian equation without a uniform inverse-Laplacian bound,
then interpolates convex gradients and passes to general targets by finite
approximation. The last balance has the form

$$
\lVert\nabla u-\nabla v\rVert_{L^2(\rho)}^2
 \leq C\left(h^{-2}\lVert u-v\rVert_{L^2(\rho)}^2+h\right).
$$

With a potential difference of order $W_2$, choosing $h$ of order
$W_2^{2/3}$ explains the final map exponent. The three-cell construction
tests the endpoint rather than merely illustrating a small perturbation.

This is stability of a particular *representation* of laws by optimal maps.
FEP's weighted-Dirac injection is a different representation, and its
Gaussian mean-coordinate injection uses a different source and support.
Neither already defines the Brenier map from a uniform convex source. A
useful finite-law bridge would instead realize catalogue laws as atomic
targets inside a fixed compact $Y$, construct their semi-discrete transport
maps, and compare the native target metric with a controlled map norm. Its
proof obligations include existence, source-null uniqueness, normalization,
and constants that remain valid as target atoms disappear. The sharpness
example blocks a blanket square-root stability promise. An unrestricted
Gaussian target family also violates the fixed compact-support hypothesis,
so Gaussian KL formulas cannot be substituted directly into this theorem.
The selected specifications are
`OAI.Problem358.one_third_stability` and
`OAI.Problem358.one_third_exponent_is_sharp` in `Brenier.lean`.
The family number and the qualified namespace differ in the source; a
numerical family label is therefore insufficient to resolve a theorem.

### Mixing, query budgets, and entropy dimension {#sec:math_upstream_complements}

Three further source results make the placement more discriminating.
Family 131 fixes the half-lazy degree-preserving switch chain on labeled
simple undirected graphs. For every graphical degree vector with $n\geq4$,
its main mixing result gives total-variation mixing time at tolerance $1/4$
at most $2n^8$ [@openaiMathSwitchMixing2026], and a gap of at least
$[24n^2\binom n4]^{-1}$ when more than one realization exists. The proof
compares conditional pair-resampling projections and bounds their squared
generator before comparing to the specified switches. This is a concrete
chain-specific convergence theorem. FEP's generic Markov data processing,
finite refresh chain, and two-state exact relaxation occupy different
levels of specificity. A bridge would preserve the switch proposal
probabilities, stationary uniform law, graph carrier, and time convention;
changing the host graph or update rule invalidates that transfer. The paper's
exact uniform sampling corollary further needs a correction algorithm and
expected bit-cost analysis, outside the recorded chain formalization scope.

Family 139 fixes a $C^2$ potential on $\mathbb R^d$ with
$V(0)=0$, $\nabla V(0)=0$, and
$I_d\preceq\nabla^2V(x)\preceq2I_d$ everywhere, and samples its normalized
Gibbs law. At fixed total-variation tolerance, its exact value-and-gradient
oracle complexity $Q(d)$ has an upper bound $C_\varepsilon d^\varepsilon$
for every $\varepsilon>0$ and an eventual lower bound $c\log d$.
The query budget is bounded on every execution, while computation between
queries is unrestricted. This determines a zero polynomial dimension
exponent, not a polylogarithmic upper bound or practical bit running time
[@openaiMathLogConcaveQuery2026].
The distinction applies directly to FEP's noncomputable finite minima and
compactness-based optimizers: existence, query complexity, storage, and
certified numerical cost require separate passports. A transport adapter
would preserve the oracle and error metric, not simply replace them by
"efficient inference."

Family 148 treats a different embedding problem: stationary self-similar
laws for signed nonzero affine contractions of the line with positive
weights, allowing exact overlaps. Its entropy rate counts the law of exact
composed affine maps. If several address sequences produce the same map,
their probabilities are combined before entropy is taken. The source's
dimension formula is

$$
\underline{\dim}_{\mathrm H}\mu
 =\min\!\left(1,\frac{h_{\mathrm{RW}}}{\chi}\right),
$$

with a common logarithm base and contraction exponent $\chi>0$.
It concerns measure Hausdorff dimension, not absolute continuity
[@openaiMathEntropyDimension2026]. The
structural lesson is close to the FEP distinctions between parameter labels,
laws, and observation fibers: entropy of descriptions can exceed entropy
of the mathematical objects they denote. This affinity provides no theorem
about learned FEP embeddings. A real transfer would first define the iterated
affine law, its quotient of descriptions, and its dimension invariant;
the binary corpus embedding below lives in a different mathematical space.

### Multiple mixing: asymptotic joint independence has its own carrier {#sec:math_upstream_multiple_mixing}

Family 145, *Rokhlin's multiple-mixing problem for one transformation*,
starts from an invertible measurable probability-preserving transformation
$T$, with measurable inverse, and ordinary two-set mixing. The pinned
main statement asserts mixing of every finite order [@openaiMathMultipleMixing2026]:
for fixed measurable sets $A_1,\ldots,A_k$, $k\geq3$,

$$
\mu\left(\bigcap_{i=1}^k T^{-t_i}A_i\right)
 \longrightarrow\prod_{i=1}^k\mu(A_i),
 \qquad\min_{i<k}(t_{i+1}-t_i)\longrightarrow\infty.
$$

All times are iterates of one transformation. No standardness or countable
generation of the original probability space is imposed in this main
statement. Its recorded formal scope retains the all-orders implication
for this carrier; extensions to endomorphisms and strongly continuous
flows are separate manuscript corollaries. The assertion is reported from
the pinned source, with no independent upstream compile or mathematical
acceptance claimed here.

The proof route reduces a least failing order to a finite-alphabet
zero-entropy process and builds ordered array joinings. Proper-marginal
independence does not already make the full joining a product. Sated
extensions, exact conditional-expectation operator identities, and a
measurable organization of multiplicatively matched function lines produce
the contradiction. The array category preserves specified conditional
product laws through countable inverse limits. This is a deeper
compositional obligation than associativity of finite stochastic kernels:
the conditional laws and limiting constructions must survive together.

For FEP, the relevance is the distinction between one-time, pairwise,
and higher-order dependence. A stationary law does not establish ordinary
mixing: a fair Boolean variable transported by the identity transformation
remains stationary, but its two-time self-event has probability $1/2$
rather than $1/4$. An observation projection preserving a selected law
also does not imply mixing of its full process. The H3 finite-grid
construction has a different path carrier and does not supply this
measure-preserving transformation. Even if a future adapter established
qualitative mixing, the displayed limit supplies no rate, summable
dependence coefficient, or finite-sample concentration bound. Applying the
current independent-sample concentration theorem would require its own
independence premise or a newly proved dependent-sample replacement.
Similarly, several independently indexed updates do not automatically
satisfy a theorem whose times are powers of one transformation.

### Markov type: testing the geometry of every reversible walk {#sec:math_upstream_markov_type}

Family 327, *Nontrivial Markov Type Forces Superreflexivity*, treats a
real Banach space $X$. Markov type $p$ means that one constant $K$ works
for every finite stationary reversible chain $(Z_t)$, every map from its
state set to $X$, and every positive integer time:

$$
\mathbb E\lVert f(Z_t)-f(Z_0)\rVert^p
 \leq K^p t\,\mathbb E\lVert f(Z_1)-f(Z_0)\rVert^p.
$$

The manuscript's main theorem asserts that existence of such a bound for
some $p>1$ forces an equivalent uniformly convex norm. Together with the
converse, the recorded scope characterizes superreflexivity
[@openaiMathMarkovType2026]. The exponent, constant, and equivalent norm
can depend on the space. The quantification over all finite chains is
essential; a well-behaved two-state walk is not a witness for the universal
property.

The proof uses finite representability to obtain an ordered spreading norm
from a hypothetical nonsuperreflexive space. It constructs reversible
walks with accumulated displacement linear in time at a fixed positive
probability. Their edge labels initially need not be differences of
state values. A finite lattice lift turns them into actual increments
away from a controlled boundary, preserving reversibility. This is the
critical adapter before the walk can be inserted into the defining
Markov-type inequality. It illustrates a general FEP discipline: supplied
directional or edge data must be connected to a genuine potential before
a theorem about potential differences can be applied.

The nearby FEP objects are law-weighted finite generators, Fisher
quadratic forms, and coarse-grained dynamics. A transfer would name a
Banach or metric target for belief states, show that its distance matches
the proposed inference discrepancy, and establish the bound uniformly
over the specified chain class. A single KL-contraction inequality does
not do this: KL is oriented and can be infinite, while the displayed
metric norm is symmetric and finite. Replacing KL by a norm, or replacing
one selected kernel by all stationary reversible kernels, is a new
mathematical claim. The binary corpus map has a Euclidean feature target
by construction; that geometry describes its annotations and provides no
superreflexivity conclusion about biological state spaces or arbitrary
families of probability laws.

### Metric Markov cotype: representation plus a nonlinear reconstruction {#sec:math_upstream_markov_cotype}

The family-332 manuscript *Metric Markov Cotype Two of $\ell_1$*, dated
5 October 2026, states $N_2(\ell_1)\leq12\sqrt{21}$
[@openaiMathMarkovCotype2026]. Its main assertion is a manuscript result
without a linked formalization record in the inspected corpus. For every
finite reversible stochastic matrix $A$, probability vector $\pi$, positive
integer $t$, and points $x_i$ in real $\ell_1$, it supplies modified points
$y_i$ with

$$
\sum_i\pi_i\lVert x_i-y_i\rVert_1^2
 +t\sum_{i,j}\pi_i a_{ij}\lVert y_i-y_j\rVert_1^2
 \leq C^2\sum_{i,j}\pi_i
 \left(\frac1t\sum_{s=1}^tA^s\right)_{ij}
 \lVert x_i-x_j\rVert_1^2,
 \qquad C=12\sqrt{21}.
$$

Zero stationary masses are allowed. The $y_i$ are existentially chosen
in the ambient space; they are not required to be specified linear
averages of the $x_i$. That freedom distinguishes metric Markov cotype
from the stronger linear averaging condition and from the Markov-type
bound on the original mapped walk. A separate consequence gives
Lipschitz extension from arbitrary subsets of real Hilbert space into
$\ell_1$ with a universal loss, rather than an isometric inverse for every
embedding.

The proof first represents the finite input configuration by weighted
binary cuts $z_i$, preserving
$\lVert z_i-z_j\rVert_H^2=\lVert x_i-x_j\rVert_1$, and retains a
reconstruction map into the original ambient $\ell_1$ that is contractive
for the weighted $\ell_1$ norm on cut coordinates. This contraction uses
a different norm from the Hilbert norm in the squared-distance identity.
Geometric stopping of the reversible walk yields averaged cut
coordinates. The cubic $3r^2-2r^3$ is applied before reconstruction;
its derivative vanishes at the binary endpoints, enabling a martingale
energy estimate that controls both modification and one-step variation.
A comparison converts the geometric endpoint cost to the required
Cesàro average. The resulting points also have an expected-median
interpretation. The cut map, nonlinear operation, and reconstruction
are each needed for the theorem.

This gives an especially useful contrast with a corpus embedding. Its
binary cuts are derived to preserve a previously specified metric and
come with an explicit reconstruction. The feature coordinates in
[@sec:math_cross_corpus_embedding] are authored annotations; no such map
recovers the source theorem or its meaning. Their squared Euclidean
distance equals a Hamming annotation distance, which is a precise but
different invariant. For an FEP belief-state application, a metric
cotype construction in ambient $\ell_1$ would also need to preserve or
restore normalization, nonnegativity, any required support, and the
inference meaning of the modified laws. The points $y_i$ need not lie
in an arbitrary subspace containing the original configuration. A
probability-simplex retraction and a controlled distortion bound would
therefore be separate proof obligations. Nonlinear smoothing of metric
data should not be interpreted as an automatically valid Bayesian
update.

### What an upstream integration would actually accept {#sec:math_upstream_acceptance}

The upstream challenge configuration provides another useful pattern: select
the challenge and solution modules, exact theorem names, and permitted axioms
explicitly. A challenge file may intentionally contain proof holes because
it is a specification. Acceptance instead concerns the solution closure and
the trusted challenge definitions. Upstream catalogue review is marked
unchecked in the inspected release. Here, the pinned metadata review does not
assert that upstream solutions were compiled or compared.

## Modular methods and acceptance {#sec:math_modular_methods}

The companion slice implements three immediately reusable operations:
canonical inventory joining, authored mathematical positioning, and
deterministic comparison/diagnostics. It projects the semantic invariant,
assumption review, non-vacuity, qualified primary theorem, and authored
relations for every topic. Existing `formal` and `formal_pairing` edges keep
their distinct meanings; conceptual associations remain conceptual. Generated
similarity never produces a proof edge. Maintained H2/H3 module scopes are
listed separately from catalogue family classifications.

For a substantial integration candidate, use the following sequence:

1. Select one named result and pin both repositories and source statements.
   State the mathematical carrier and what observation or parameter map is
   intended to relate them.
2. Compare quantifiers, support, measurability, normalization, integrability,
   smoothness, dimension, finite/asymptotic regime, constants, units, and allowed
   axioms. Record every extra assumption and every lost conclusion.
3. Write a definition-preserving adapter or commuting-diagram obligation.
   A pairing of two endpoint laws is recorded separately from a derivation.
4. Construct an attaining/nonzero instance and a boundary or counterexample.
   Test the proposed correspondence where support vanishes, parameters become
   redundant, observations discard a mode, or physical units change.
5. Run the relevant native proof and axiom checks on isolated, exact source
   slices. Same Lean and Mathlib pins reduce a version obstacle but do not
   establish namespace, transitive-dependency, or semantic compatibility.
6. Conduct a fresh statement and interpretation review. Only then add a
   maintained theorem-backed relation or revise a semantic disposition using
   the repository's coordinated acceptance process.

### Analysis modules with explicit inputs and outputs {#sec:math_analysis_modules}

Each operation should consume the smallest sufficient source contract and
produce an artifact whose interpretation is independently reviewable. The
inventory, authored positioning, typed relations, deterministic feature
comparison, and selected numerical diagnostics are implemented analysis
operations. The theorem-transport and research packets below specify further
mathematical work rather than claiming an automated prover implements them.

The **inventory join** takes the sealed roster, canonical body registry,
maintained maturity records, relation contract, and formal-module
manifest. Its output retains a topic's own primary declaration, invariant,
assumptions, semantic disposition, and source provenance. Resolving a
qualified declaration establishes that the named source exists. It is not a
substitute for elaborating its closure with the pinned compiler. A row's
reviewed disposition is copied from its authority, not recomputed from a
keyword match or a successful numerical probe.

The **positioning join** adds an authored family profile to each member row.
Its binary domain vector records the union of mathematical contexts selected
for that family. Consequently, a family containing a native-measure theorem
and a finite algebraic proxy can place both rows near measure theory without
asserting that both rows prove a native-measure statement. An adequate output
therefore displays inherited context and row-owned theorem scope separately.
Domain overlap is useful for finding a collaborator or a likely adapter; it
is unsuitable as an accepted-proof score.

The **relation analysis** consumes exact endpoint IDs and the maintained
relation kind. Family aggregation retains the underlying edge list so that
a reader can recover every counted connection. It keeps formal derivations,
formal pairings, conceptual edges, and blockers distinguishable. A diagram
that merges them into one unlabeled edge destroys the evidence needed to
interpret the result. A search for a composable proof route must additionally
unify the middle carriers and discharge the combined assumptions; graph
reachability alone does neither.

The **feature comparison** consumes the declared binary vector and produces
a reproducible set overlap, such as

$$
J(U,V)=\frac{\lvert U\cap V\rvert}{\lvert U\cup V\rvert}
$$

when the union is nonempty. Empty-union behavior is part of the declared
implementation. The comparison is deterministic editorial geometry. It
neither learns a manifold nor estimates semantic equivalence. If a future
learned embedding is evaluated, the task must be external to the labels used
to train it: held-out statement matching, hypothesis retrieval, or detecting
a known missing support condition are suitable targets. Recovering the same
family tags used to construct a vector would measure reconstruction of the
annotation, not mathematical understanding.

The **boundary diagnostics** consume named laws or matrix parameters and
return values together with their domains and failure reasons. A supported
finite KL probe checks normalization and relative support; an unsupported
probe distinguishes the repository's finite functional from native infinite
KL. A Bernoulli Fisher probe requires an interior parameter, then separately
checks floating-point representability of the displayed value. A valid real
number may exceed the numerical format even when the mathematical theorem
applies. Rejecting that input numerically must not be described as a failed
Fisher theorem, and silently clipping it would change the diagnostic.

The four explanatory publication grids use exact rational grid indices and
coefficients; their pi-dependent angles and logarithmic epsilon grid are
evaluated in an explicit 80-digit Decimal context. Logarithms, exponentials, square roots,
and range-reduced alternating trigonometric series produce the displayed
values; each series fails if its fixed cap is reached before the declared
first-omitted-term bound. The shared model discloses these truncation bounds
and their reconstruction factors, separately from rounded arithmetic error.
Derived grid values are quantized to 24 decimal places with half-even
rounding before finite JSON serialization. This publication rule removes
platform-dependent elementary-function low bits; it neither rounds arbitrary
probe inputs nor changes the arithmetic acceptance tolerance. Exact formulas
remain authoritative, and artifact freshness still compares exact bytes.
These computations provide reproducible explanatory values, not certified
interval enclosures or additional Lean proofs.

The **transport review** consumes two complete result passports and a
proposed map. It emits a commuting obligation, a premise comparison, and three
possible outcomes: an exact transfer with a qualified proof; a theorem
pairing with no claimed implication; or an editorial affinity with a concrete
missing obligation. The minimum premise comparison records carrier, support,
sigma-algebra, integrability, differentiability, identifiability, time or
sample regime, objective orientation, admissible policies, constants, and
physical units. Its negative controls are drawn from the passports rather
than invented after observing a desired agreement.

Finally, **artifact freshness** compares a deterministic projection against
the current named inputs. A non-mutating check reports drift and does not
repair it. A numerical figure, table, and accessible description should be
renderings of the same model values, rather than independent calculations
whose captions can diverge. Source hashes bind that projection to the source
bytes it used. They do not create a native receipt or establish currency of
an independently governed empirical or publication gate.

### From Lean statements to intelligible mathematical language {#sec:math_statement_language}

A natural-language analysis should explain a theorem's logical interface
before interpreting its scientific title. This is particularly important in
a catalogue where a familiar phrase can name a finite proxy, a supplied
identity, or a native measure theorem. The task is to reconstruct what a
reader may substitute into the declaration, what the declaration returns,
and where that interpretation stops. A readable explanation is a separate
artifact from the Lean proof term.

The analysis contract has three layers. The **source layer** retains the
qualified name, exact declaration, namespace and surrounding variable
context, source identity, selected lexical theorem mentions, and import
context. The **logical layer**
retains typed and instance binders and the conclusion, preserving binder
order and dependence. Reading those binders as mathematical inputs or
propositional premises remains an interpretation obligation; the extractor
does not claim to elaborate their types. The **interpretive
layer** attaches the maintained invariant, explicit assumptions,
non-vacuity example, and semantic disposition, with those records identified
as reviewed prose. `analyze_topic(model, topic_id)` joins the primary,
supporting, and boundary declarations to that maintained review;
`inspect_theorem(model, qualified_name)` returns an exact indexed declaration
and rejects an unknown or unqualified identity. Source extraction and maintained prose
provide traceability; they do not constitute a certified translation from
Lean to English or an independent elaboration of the theorem.

![Three layers of a theorem contract: exact primary declaration and syntactic binder information, maintained row-owned semantic review, and inherited family context. The distinction supports source-grounded explanation without treating binder counts or shared mathematical tags as proof strength or certified translation.](../output/figures/mathematical-theorem-contracts.png){#fig:math_theorem_contracts width=100%}

For example, the declaration
`FEP.ActiveInference.variationalFreeEnergy_eq_surprisal_iff` has finite
policy, state, and outcome types in its surrounding variable context. Its
inputs are a `GenerativeModel`, one policy, one outcome, a proof of strictly
positive predicted outcome mass, and a normalized nonnegative recognition
law. The evidence premise depends on the preceding model, policy, and
outcome: moving it to an unrelated context would change the statement. Its
conclusion is a biconditional between attaining the specified objective value
and equality with the model's posterior. A faithful explanation is therefore:
for every such finite model and positive-evidence observation, a recognition
law attains the posterior-form variational bound exactly when it equals the
constructed posterior. The converse is part of the result, and the carrier
includes sparse posteriors. This statement neither promises an optimizer in
an arbitrary restricted variational family nor asserts positive evidence for
every outcome.

The short proof also matters. It unfolds the posterior-form objective,
cancels its surprisal term, and invokes
`FEP.FiniteInformation.finiteKL_eq_zero_iff`. This is an exact reduction to a
previously established separation property of the declared finite
functional. An explanation that instead describes numerical gradient
descent, asymptotic approximation, or a general continuous ELBO has changed
the proof's mathematical task. Definition unfolding is not intrinsically a
weak proof; it is informative when the unfolded definition reveals precisely
which additional construction or analytic estimate is, and is not, needed.

A second example tests whether a language system respects orientation.
`FEP.DecisionRisk.weightedDirac_klDiv_eq_finiteKL_of_relativeSupport` accepts
two finite laws $p,q$ and the pointwise premise

$$
\forall x,\quad p(x)\ne0\ \Longrightarrow\ q(x)>0.
$$

It concludes an equality between native extended-real KL of their embedded
laws and `ENNReal.ofReal` of the finite functional. The English explanation
must preserve which law supplies mass and which supplies the reference.
Replacing the premise by $q(x)\ne0\Rightarrow p(x)>0$ yields a different
theorem. Suppressing the codomain conversion would hide the difference
between a finite real value and native infinity. The proof reconstructs the
Radon--Nikodym density and integrates it; resolving the theorem's name is
insufficient evidence that either argument can be exchanged.

Several forms of scope need their own language tests. An almost-everywhere
conclusion must name its governing measure; a limit must name its filter and
the sequence or time variable; an existence theorem must distinguish a
chosen mathematical witness from an executable algorithm. A matrix identity
must state whether the matrix is supplied or derived from a function. A
conjunction of two endpoints must preserve the conjunction rather than
become an implication. A theorem with a fixed Gaussian variance must not
become uniform over arbitrary covariance matrices. These are semantic
properties of the mathematical interface, not stylistic preferences.

Syntactic dependency roles are useful but limited. A symbol in a type, a
definition body, and a proof term plays a different visible role; a parser
can expose those occurrences and link them to source. It cannot infer every
elaborated implicit argument, typeclass resolution, definitional equality,
or mathematical entailment from a lexical match. The retained surrounding
context therefore remains essential. For canonical topic bodies, a
standalone excerpt must also retain the generated namespace in which the
body is placed. The maintained primary theorem is the entry point; other
declarations in the same topic can supply auxiliary results without silently
replacing that reviewed invariant.

Source coordinates also need an explicit convention. A canonical topic's
line number refers to the embedded Lean body literal, whereas a manifested
formal resource's line number refers to its physical `.lean` file. The
source owner and coordinate kind prevent a reader from treating the former
as a Python-file offset. Preceding `include` and `omit` directives are
retained as contextual syntax; this does not infer which context binders
Lean ultimately includes after elaboration.

An evaluation set should ask whether an explanation preserves a contract,
not whether it sounds fluent. Suitable negative controls exchange the two
KL arguments, drop positive evidence, replace a finite carrier by a smooth
one, change "almost everywhere" to "everywhere", or replace a finite-grid
law by a continuous-path law. Human reviewers should identify the exact
changed binder or conclusion before inspecting the generated explanation.
The assessment can record premise coverage, quantifier coverage, carrier
fidelity, objective orientation, and correct handling of counterexamples.
Each item has an exact source reference and an independently authored
expected distinction. These proposed tests evaluate mathematical language;
passing them would not prove the original theorem again.

No external language-model execution is required for the current
source-grounded analysis. A future model-assisted explanation would need its
own input provenance, versioned output, and reviewed error record. Its output
would remain an explanation until a separately checked formal construction
established any new equivalence or implication.

### Cross-corpus embeddings with an inspectable meaning {#sec:math_cross_corpus_embedding}

The cross-corpus map addresses retrieval and comparison of mathematical
contracts. It does not embed probability laws by weighted Dirac masses,
parameterize a statistical model, or reduce a stochastic state. Its points
are source-indexed research objects. On the FEP side, a point is an authored
family context joined to exact member rows; on the upstream side, a point
is a reviewed pinned result record with its selected statements and scope.
The units remain visible because a family union is broader than any one
theorem. The source passports above provide the detailed comparison needed
after a point is retrieved.

The implemented common coordinate registry distinguishes mathematical
domains, literal carrier contexts, and hypothesis or regime contexts. A
positive carrier coordinate such as finite-discrete, general-measurable,
or path-space records a selected source carrier. A hypothesis coordinate
such as full-support, independence, or compactness records an explicitly
selected contract context; asymptotic-limit records a regime, rather than a
logical premise. These annotations have source rationales. In a FEP family,
they are positive unions across selected owned declarations. A measure
theorem and a finite matrix theorem may contribute different coordinates
to the same family point. Neither coordinate is thereby added to every
member's theorem statement.

An absent feature means unassigned, not mathematically false. Normalization
does not imply full support; positive evidence does not imply full support
of every latent state; relative support is oriented and differs from the
positivity of both laws. Likewise, compactness of a finite-channel feasible
set does not make every probability space in the family compact. A binary
registry is useful only if these limitations accompany its interpretation.
Its zero entries allow a reproducible numerical comparison of annotations,
while preserving their epistemic status as unassigned contexts.

Write the shared binary incidence row as $z_i\in\{0,1\}^m$. The common
Euclidean distance is

$$
d_{ij}^2=\sum_{a=1}^m(z_{ia}-z_{ja})^2.
$$

For binary inputs this counts coordinates assigned to exactly one endpoint.
Each coordinate has unit weight. Domain, carrier, and hypothesis groups
with more coordinates can contribute more mismatches; the implementation
does not secretly normalize groups to equal weight.
Unlike Jaccard overlap, it does not normalize by union size. A broad family
with many assigned contexts can therefore be distant from a narrowly stated
result even when they share a useful core construction. Both statistics
must be interpreted through their explicit inputs. Neither is a metric on
mathematical truth, and choosing the larger similarity value cannot turn a
proposed adapter into a derivation.

![Inspectably authored cross-corpus coordinates. Domain, carrier, and hypothesis or regime assignments are positive source contexts; missing assignments are not negated hypotheses. FEP family rows are unions across selected owned statements, while pinned upstream records retain their own declared scope. This incidence display exposes what determines the accompanying distance map.](../output/figures/mathematical-cross-corpus-features.png){#fig:math_cross_corpus_features width=100%}

{{methods.cross_corpus.coordinate_key_table}}

: Printed coordinate key for the shared cross-corpus incidence. Codes identify authored domain, carrier, and hypothesis or regime contexts; an absent assignment is not a negated premise. {#tbl:math_cross_corpus_coordinate_keys}

The display uses classical multidimensional scaling. For $N$ indexed rows,
let $H=I_N-N^{-1}\mathbf1\mathbf1^{\mathsf T}$, and let $D^{(2)}$ be the
matrix whose entry is $d_{ij}^2$, not the matrix product $D D$. The centered
Gram matrix is

$$
B=-\frac12H D^{(2)}H.
$$

Since the input distances are Euclidean, exact $B$ is positive semidefinite
and equals the Gram matrix of the centered feature rows. Its positive
eigenvalues identify the rank of this finite annotation geometry. Retaining
the leading two eigenvectors gives a display, with coordinate scale set by
the square roots of their eigenvalues. The map is a projection of declared
binary data; it is not a learned semantic manifold or an estimate of the
dimension of FEP models.

The numerical producer preserves the binary rows and integer squared
distances as exact inputs. It computes the centered Gram matrix and its
spectral display through a fixed 80-digit Decimal Jacobi procedure, checks
an off-diagonal residual bound, and only then serializes derived publication
values with declared rounding. The reported numerical rank and repeated
eigenvalue groups use an explicit residual-based threshold. They are
diagnostics of this finite computation, rather than newly proved statements
about an exact mathematical spectrum. The model retains the eigenspectrum,
residual, threshold, iteration bound, and serialization convention so that
a regenerated projection can be compared without relying on a hidden
platform eigensolver.

The full distances remain authoritative for this comparison. The two-axis
display reports normalized stress

$$
\operatorname{stress}
 =\left(
 \frac{\sum_{i<j}(d_{ij}-\widehat d_{ij})^2}
      {\sum_{i<j}d_{ij}^2}
 \right)^{1/2},
$$

where $\widehat d_{ij}$ is distance in the two-axis projection. The numerical
stress uses the internal Decimal coordinates before publication rounding;
serialized point coordinates can differ by the declared rounding error.
The declared
zero-denominator case has stress zero because all feature rows coincide;
it contains no discriminating information. Rank, eigenvalues, and this
residual separate a useful display from a faithful reconstruction of every
distance. Apparent overlap of points in two dimensions can reflect projection
loss rather than identical feature rows.

Eigenvector signs, rotations inside repeated eigenspaces, and orientation
of the entire display have no mathematical interpretation. The producer
uses deterministic row ordering and a reproducible basis convention, while
retaining the ambiguity in its metadata. A named axis must therefore not be
called an intelligence, maturity, complexity, or verification axis.
Likewise, a close upstream/FEP pair may be a good reading recommendation
without being a better candidate for formal transfer than a more distant
pair with exactly matching carriers and support.

![Classical multidimensional scaling of the declared shared feature distances. Proximity denotes authored domain, carrier, and hypothesis or regime overlap. The plotted coordinates retain rank, eigenvalue, stress, and axis-ambiguity diagnostics in the shared model; they do not establish theorem equivalence, imported proofs, or scientific acceptance.](../output/figures/mathematical-cross-corpus-embedding.png){#fig:math_cross_corpus_embedding width=100%}

{{methods.cross_corpus.row_key_table}}

: Printed row and coincidence-group key for the cross-corpus figures. F and U codes retain exact family or pinned-result identities; G codes collect identical feature vectors, rather than equivalent theorems. {#tbl:math_cross_corpus_row_keys}

The printed coordinate and row keys in [@tbl:math_cross_corpus_coordinate_keys]
and [@tbl:math_cross_corpus_row_keys] make every displayed code recoverable
without the interactive explorer. Coincidence groups identify equal input
feature rows. Their source statements and maintained evidence scopes remain
distinct even when the plane assigns them one point.

The most informative visual workflow alternates between this coarse map
and exact source. Selecting an entropy-and-dynamics neighborhood should
reveal whether the endpoint supplies only data processing, a spectral gap,
an entropy-dissipation identity, or a quantitative rate. Selecting a
geometry neighborhood should expose whether its carrier is a supplied
Gram matrix, a differentiated law family, a transport cost, or an optimal
map representation. The paired incidence table and statement analysis make
these distinctions recoverable. A line drawn between two selected points
is labeled editorial affinity until an exact maintained relation supports
a stronger kind.

Several checks would make a future comparison scientifically evaluable.
First, hold out source families or manuscripts before selecting a retrieval
target; a second manuscript with an almost identical statement is not an
independent test. Second, keep native acceptance, semantic disposition, and
review outcome out of mathematical similarity coordinates so that the
retriever cannot predict its own evidence labels. Third, compare declared
baselines: domain-only, carrier-only, hypothesis-only, full incidence, and
source-text retrieval. Their errors reveal which representation supplies
useful information. Fourth, review an endpoint pair without seeing its
plot distance, then score whether retrieval found a compatible carrier,
identified the missing premise, or merely matched terminology.

Boundary controls should be drawn from actual contrasts. The same keyword
"free energy" connects Bayesian evidence, finite policy regularization,
and quenched pressure with different normalization and quantifiers. The
same word "embedding" connects faithful law representation, redundant
parameterization, information-losing observation, and corpus coordinates.
The same word "convergence" can mean a fixed scalar iteration, a weak
law limit, a finite-grid result, pressure convergence in probability, or a
worst-case mixing estimate. A representation that places these objects
nearby should still expose their different passports. Its success is
recovering a mathematically useful comparison and its obstruction, not
erasing the obstruction.

The present map implements deterministic annotation geometry and
source-grounded analysis. Held-out matching, theorem entailment, formal
adapter synthesis, and the proposed language evaluation remain separate
research tasks. New corpus points, coordinates, or reviewed correspondences
must retain their source identities and refresh the shared numerical model,
tables, accessible descriptions, and figures together.
`cross_corpus_embedding(model)` exposes this common model, including the
source-indexed rows, coordinate registry, full distances, and projection
diagnostics; it creates no relation edge from a neighborhood query.

### Mathematical existence and executable computation {#sec:math_existence_computation}

The methods also need a computational passport. A theorem constructing an
optimal policy tree by choosing a finite minimum is different from a
specified executable search with complexity and precision bounds. A compactness
proof of a rate-distortion minimizer is different from a certified numerical
solver. The maintained sources use noncomputable constructions where their
mathematical interfaces require them; replacing those constructions with a
solver is additional work.

For finite policy trees, an executable dynamic program would need a decidable
representation of the stage costs and comparison rule, a proof that its
recurrence realizes the existing tree value, and a complexity statement in
horizon and carrier sizes. For rate distortion, a numerical optimizer would
need a feasibility certificate, an upper bound from its reconstructed joint,
a justified lower bound from an admissible dual multiplier, and a controlled
gap. Merely returning a mass table with a small reported objective does not
establish optimality.

Even an exact real formula has a computational boundary. The Bernoulli
information diverges as an interior parameter approaches an endpoint; native
KL may be infinite because of support; numerical natural-gradient inversion
can be ill conditioned near redundancy. A computational module should expose
these cases as mathematical regimes, representability failures, or certified
approximation errors with distinct labels. The current explanatory probes
evaluate selected formulas; they do not supply general optimization or
conditioning guarantees.

## Next mathematical packets and precise proof obligations {#sec:math_research_packets}

The strongest research program follows the seams already exposed by exact
results. The packets below are proposed extensions. Each starts from a named
source capability, identifies a specific new statement, and includes an
obstruction that prevents an overly broad conclusion. None is counted as a
new canonical theorem in this supplement.

### Score rank, identifiable quotients, and natural gradients {#sec:math_packet_score_rank}

Start with the centered finite `FEP.InformationGeometry.ScoreModel`.
Let $S=\{x:p(x)>0\}$ and define a weighted score map
$A:\mathbb R^d\to\mathbb R^S$ by
$Av(x)=\sqrt{p(x)}\langle s(x),v\rangle$. Then $I=A^\mathsf TA$.
The prospective rank theorem is

$$
\operatorname{rank}I=\operatorname{rank}A
 \leq\min(d,\lvert S\rvert-1).
$$

The proof route is explicit: establish the Gram-kernel identity, then use
centering to show that the nonzero vector
$(\sqrt{p(x)})_{x\in S}$ lies in the left nullspace of $A$. This avoids
requiring positive masses at outcomes outside the actual support. In a
fixed-support smooth family the same bound constrains the statistical tangent;
at a changing-support boundary the score representation needs a separate
domain argument.

The quotient target is $\mathbb R^d/\ker I$ with the induced positive
pairing. For an objective covector $c$, solving $Iv=c$ requires that $c$
annihilate $\ker I$. A well specified theorem would give a unique quotient
class satisfying the metric duality, not a unique ambient vector. A chosen
complement or pseudoinverse adds a representative convention that must be
recorded separately. The duplicated Bernoulli null tangent and the
simplex-tangent example provide negative and positive controls. A claim of
coordinate invariance must prove independence from that representative choice
and compatibility with the intended parameter map.

### Support-safe information transfer and convergence {#sec:math_packet_support}

The exact weighted-Dirac KL bridge supplies the representation step. A useful
next theorem would package the relative-support premise and its behavior
under mapping, joint construction, and kernel composition, rather than ask
every application to rediscover it. The joint/product-marginal comparison is
an attaining example because support inclusion follows from marginalization;
a point mass compared with a reference assigning it zero mass is the refusal
case.

For limits, the desired statement must choose the topology. On a finite
alphabet with reference masses uniformly bounded below by $\delta>0$, the
ordinary KL formula is continuous in the actual masses, including actual
zero atoms. This proposed finite-dimensional theorem can be proved from the
zero-safe entropy term and continuity of the bounded reference logarithms.
Allowing reference masses to vanish removes that argument. Total-variation
convergence alone cannot substitute for the missing support and integrability
control.

The simplest control is $p_\varepsilon=(1-\varepsilon,\varepsilon)$
and $\delta_0=(1,0)$. Their total variation tends to zero, and
$D(\delta_0\Vert p_\varepsilon)=-\log(1-\varepsilon)$ tends to zero,
whereas $D(p_\varepsilon\Vert\delta_0)=\infty$ for every
$0<\varepsilon<1$. An accepted extension must retain orientation and show
which direction its conclusion covers. Passing a real totalized functional
through this limit does not prove the corresponding native extended-real
statement.

### From attained rate distortion to a sharp dual certificate {#sec:math_packet_distortion}

The retained capability now separates three conclusions. For finite alphabets,
a fixed source law, pointwise nonnegative real distortion and an actual
feasible joint, `FEP.VariationalDuality.rateDistortion_exists_minimizer_and_dual_supremum`
derives a primal minimizer whose information equals both the feasible primal
infimum and the supremum of the Lagrangian dual over nonnegative real
multipliers. Zero source atoms are permitted. Actual fixed-source information
convexity and closed upper-image separation derive equality; neither an
optimizer nor an equality certificate is supplied as a hypothesis.

The maintained fair-Boolean Hamming result already derives the natural-log
curve $\log 2-\operatorname{binEntropy}D$ on $0\leq D\leq1/2$,
including optimality against all feasible joints. The general dual-supremum
theorem recovers this closed curve. At zero budget the supremum statement
does not assert a finite maximizing multiplier. At half budget distinct
independent joints minimize information; an infeasible negative budget remains
infeasible.

Finite multiplier attainment is a separate result under actual strict
feasibility. `FEP.VariationalDuality.rateDistortion_exists_slater_dual_optimizer`
and `FEP.VariationalDuality.rateDistortion_primal_dual_extrema` construct a
nonnegative real multiplier, zero primal-dual gap and complementary slackness.
Strict feasibility is sufficient, not necessary: the zero-distortion,
zero-budget control has multiplier zero and no strictly feasible law.
These results assert neither a unique optimizer nor finite multiplier
attainment at every feasible boundary.

A later computational-certificate interface may compare an actual feasible
joint's objective with a proved dual lower bound and report their gap. It
would need its own executable representation, numerical-error contract and
source-bound validation; the proof alone is not an implementation or measured
performance result. Continuous alphabets, signed-distortion extensions,
general uniqueness and stronger boundary-attainment claims remain separate
questions. The supporting capability does not change the primary `fep-064`
structural-proxy theorem or its reviewed semantic disposition. Formal results
also supply no empirical or physical validation.

### Observation intertwining as a reusable theorem interface {#sec:math_packet_observation}

The H3 rowwise projection result suggests a generic interface comprising
measurable $\pi$, normalized kernels $K_t$ and $\overline K_t$, and the
intertwining equality for every state and time. The target is a reusable
finite-path pushforward theorem for arbitrary initial probability laws,
followed by composition with a separately normalized noisy observation
kernel. The existing selected proof supplies a model and an induction route;
a new abstraction must remove the selected Gaussian coordinates without
losing measurability or kernel normalizations.

Identification is a different packet. Define equivalence of full hypotheses
by equality of their induced observation laws, then ask whether the chosen
family is injective modulo that equivalence. The hidden-mode pair proves
that unrestricted injectivity fails in the present channel. An added channel
or restricted hypothesis family could restore it, but would need an exact
separation theorem. This formulation gives a mathematical meaning to sufficient
observations without presupposing that every latent coordinate is observable.

### Quantitative entropy decay beyond data processing {#sec:math_packet_entropy_decay}

`FEP.MarkovSemigroup.NativeKernelSemigroup.nativeKL_to_invariant_nonincrease` derives
nonincrease from semigroup composition, data processing, and an invariant
reference. Its conclusion is an extended-real inequality; it neither
differentiates KL nor supplies a convergence rate. A quantitative packet
should name a selected semigroup, an initial-law class with finite KL, and
constants $C,\lambda$ before seeking a bound such as
$D(\mu_t\Vert\rho)\leq C e^{-\lambda t}$.

For an entropy-dissipation route, the added obligations include a generator,
a density class preserved by the evolution, differentiation under the
integral, integration by parts, and the functional inequality with its
normalization. The upstream logarithmic-Sobolev family motivates this packet,
but an inspected manuscript does not provide these obligations in the FEP
namespace. Degenerate invariant laws and infinite initial KL are useful
boundary controls. A selected Gaussian closed-form decay result would be a
bounded first target; a general nonlinear theorem should not be inferred
from it.

### Continuous paths, singular grids, and constitutive calibration {#sec:math_packet_paths}

A continuous-path extension should first choose its target: a process law on
a product sigma-algebra, a measure supported on continuous trajectories, or
a finite-time path-space likelihood comparison. These are distinct objects.
The source's finite joint laws provide starting data, but consistency under
deleting grid coordinates must be proved before any extension theorem can
consume them. A continuous version needs additional regularity or moment
control. A path-space KL statement needs the appropriate absolute-continuity
and integrability hypotheses on that space.

The selected nonsingular, repeated-time singular, and all-zero H3 grids are
three compulsory controls. Any proposed continuous theorem must explain how
their different finite-dimensional supports are treated. A derivative of
finite-grid KL with respect to spacing is not, by itself, a physical
entropy-production rate. The constitutive counterexample further requires
that any physical interpretation name energy-per-nat, time and temperature
units, the observational calibration, and an independently justified
constitutive relation. Probabilistic extension and physical calibration
should have separate acceptance statements.

### Statistical identification, preferences, and decision losses {#sec:math_packet_decisions}

The selected Gaussian posterior proves parameter identification from an
infinite observation sequence by connecting conditional expectation,
martingale convergence, and a separating empirical statistic. The
nonidentifiable kernel instead leaves the posterior equal to its prior.
These results suggest a reusable packet with positive prior support, a
declared observation family, a statistic that separates its hypotheses, and
a convergence theorem on the specified probability space. A dynamic latent
filter, misspecified likelihood, or learned approximation would require new
premises and a different target statement.

Decision evaluation must then specify the loss. For a Bernoulli truth $p$
and report $q$, the scalar Brier expectation is
$p(1-p)+(q-p)^2$; it is minimized at the truth. A KL preference objective
$D(\operatorname{Bern}(q)\Vert\operatorname{Bern}(r))$ is instead
minimized at the preferred law $r$. This comparison explains why predictive
calibration and preference fulfillment cannot be identified merely because
both have minima. The Brier interpretation is grounded in its original
forecasting setting [@brier1950verification]; the exact excess-risk identity
is `FEP.EmpiricalRisk.brierExcess_eq_sqError`. The displayed KL preference
term is a selected surrogate, not a restatement of every EFE objective.

![Prediction and preference optimize different declared functions. For Bernoulli truth $0.7$, expected scalar Brier loss is minimized at report $0.7$. The selected preference surrogate $\mathrm{KL}(\operatorname{Bern}(q)\Vert\operatorname{Bern}(0.2))$ is minimized at $0.2$. This formula comparison distinguishes calibration from preference fulfillment; it is not a generic EFE identity or a simulated policy experiment.](../output/figures/mathematical-risk-preference.png){#fig:math_risk_preference width=100%}

A policy comparison additionally fixes the information budget and admissible
class. The finite open-loop embedding and H3 measurable two-step comparison
provide exact containment witnesses. A new claim about the value of sensing,
memory, or feedback should specify what is held fixed and prove either
containment, a strict gap, or non-comparability. This makes memory-limited
learning a concrete later correspondence problem with upstream family 140,
rather than a generic assertion that Bayesian inference solves computational
learning limits.

### Smooth derivative provenance and controlled mechanics remainders {#sec:math_packet_mechanics}

The finite mechanics identities suggest two separate extensions. First,
define actual differentiable fields $Q(x)$ and an objective $U(x)$, derive
$g=\nabla U$, $H=\nabla^2U$, and $DQ$ from them, and prove that the
analytic weighted divergence equals the finite expression. This supplies
derivative provenance rather than assuming the matrix-role inputs already
have it. Domain regularity and the equality of mixed partials belong in that
statement.

Second, quantify the residual. If a region has
$\lVert\operatorname{div}Q\rVert\leq\varepsilon$ and
$\lVert\nabla U\rVert\leq M$, the finite Cauchy--Schwarz identity suggests a
region-wise bound $\lvert\mathcal D\rvert\leq\varepsilon M$ after the analytic
bridge is established. The aligned equality witness checks sharpness; the
nonzero graph example checks that plain skewness still cannot erase the
remainder. An integrated or long-time consequence additionally needs
trajectory and integrability estimates. The matrix theorem supplies a
controlled local term, not an automatic global stability theorem.

The generated positioning artifacts and numerical boundary probes are analysis
evidence. A static upstream byte comparison establishes only that the selected
files match the pin. Neither operation establishes native upstream execution,
current FEP native acceptance, publication acceptance, or scientific validity.
Those evidence planes remain governed by their own receipts. This supplement
therefore supports a precise research program without promoting a geometric
analogy, an upstream research claim, or a source inspection into a theorem.
