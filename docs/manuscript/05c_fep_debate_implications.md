## Implications for the FEP Debate {#sec:implications_for_the_fep_debate}

Formalization can locate a disagreement more sharply, but it cannot decide which formal object best represents a biological system. The catalogue therefore treats the critical literature as a source of proof obligations, not as a set of objections already answered by compilation. Its semantic audit asks, for every row, what is actually invariant, which assumptions do the work, whether the statement has a non-vacuous witness, and what stronger theorem would have to compile before the advertised interpretation was justified.

### Blanket Conditions (Biehl et al.) → fep-005 Response {#sec:blanket_conditions_biehl_et_al}

Biehl, Pollock, and Kanai [@biehl2021critique] challenge the generic use of Markov blankets in stochastic dynamics. At least three claims must be distinguished:

1. a finite set can be assigned to disjoint named blocks;
2. the random variables associated with those blocks satisfy a conditional-independence relation; and
3. a target dynamical system admits and preserves the relevant partition.

fep-005 proves the first claim exactly. Given `assign : Fin 20 → Fin 4`, it defines each block by filtering the finite universe, proves blocks with unequal labels are disjoint, characterizes membership, and proves that every state belongs to one and only one block. The assignment remains an input. No probability measure, conditional distribution, transition kernel, or dynamical invariance appears in the theorem type.

The row is consequently a complete finite-partition theorem rather than a rebuttal to Biehl et al. The maintained `FEP.MarkovBlanket` foundation addresses the next bounded layer with new objects: it constructs a normalized law $P(b)P(i\mid b)P(e\mid b)$, proves positive-mass internal--external factorization and zero conditional mutual information, and defines a nontrivial one-step transition whose allowed dependencies are enforced by kernel source types. This evidence satisfies the deliberately finite blanket capability, while the fep-005-to-fep-009 edge remains conceptual because no theorem identifies that finite factorization with the generic measure-theoretic conditional-independence predicate. H1 goes one bounded step further on a different shared carrier: the full-support uniform law on sixteen Boolean $(I,S,A,E)$ states factorizes as $P(S,A)P(I\mid S,A)P(E\mid S,A)$, and the exact positive-time refresh kernel selected by the emitted `true` action preserves that same law. This is a concrete model-specific factorization and invariance theorem, not a derivation from every fep-005 assignment, a blanket-existence theorem for arbitrary stochastic dynamics, causal identification, or a biological-boundary result.

### Particular Partitions (Aguilera et al.) → fep-025 Response {#sec:particular_partitions_aguilera_et_al}

Aguilera et al. [@aguilera2022particular] question whether the “particular partition” and NESS constructions used in Bayesian mechanics apply generically. A typical informal decomposition invokes a stationary density, a drift decomposition, positive diffusion, an antisymmetric solenoidal operator, and regularity/divergence conditions. Proving an elementary fact about one of those ingredients does not prove the conjunction.

fep-025 now formalizes a finite continuity-equation instance. It defines forward-minus-reverse probability current and node divergence, proves antisymmetry and global conservation, and derives zero divergence from normalized transition rows and a stationary mass vector. A directed three-state cycle has a uniform stationary law, zero divergence, and nonzero current, proving that finite stationarity need not imply detailed balance. It does not:

- construct a stationary density;
- prove existence or uniqueness of a NESS;
- express a state-dependent diffusion or solenoidal field;
- derive a Fokker--Planck or continuity equation; or
- establish that a physical flow admits the asserted decomposition.

This is a deliberate boundary. The row is a genuine finite NESS witness under its stated transition-matrix model, but it is not the continuous Helmholtz/Ao decomposition challenged in the literature. That stronger target must quantify the continuous state space, generator or SDE, stationary measure, boundary and regularity assumptions, and every term in the decomposition in one shared model.

### Math and Territorialism (Andrews) → Type System Response {#sec:math_and_territorialism_andrews}

Andrews [@andrews2021math] criticizes mathematical notation that shifts meaning or hides assumptions. Lean addresses part of this problem mechanically: a `Measure α`, a density, an `ℝ`-valued objective, and an `ℝ≥0∞` divergence cannot be silently identified. Hypotheses are explicit inputs, and theorem names resolve to concrete declarations at a pinned library revision.

Two examples show both the benefit and the limit.

First, fep-014 uses `InformationTheory.klDiv μ ν` with the order of its measure arguments fixed by syntax. It proves non-negativity in the native extended codomain, self-divergence under `SigmaFinite`, the zero/equality characterization under finite-measure instances, and Mathlib's composition-product chain rule for finite measures and Markov kernels. This is substantially stronger than a theorem about unrelated measure monotonicity. It still does not say that a particular pair of FEP distributions satisfies the intended generative-model interpretation.

Second, fep-031 proves `0 < exp (-βE)` without assumptions because the exponential is always positive, while its monotonicity theorem requires the explicit hypothesis `0 < β`. On any explicitly nonempty finite support, it also proves the partition sum positive and the normalized weights sum to one. These signatures expose both the support and positive-inverse-temperature conditions that prose often leaves implicit; they do not derive the Gibbs law from a maximum-entropy principle.

Type discipline therefore blocks some category errors and makes assumptions inspectable. It does not prove that the chosen types capture the target science, and it does not rescue a theorem whose conclusion merely repeats a hypothesis.

### Colombo & Seriès and the Empirical-Adequacy Critique {#sec:colombo_series}

Empirical-adequacy critiques ask whether an FEP model rules out observations or predicts specific neural/behavioral phenomena. Lean has no access to those observations. It can help by fixing the mathematical content of a model, exposing auxiliary assumptions, and making alternative formal readings comparable. The empirical step still requires an observation model, data provenance, parameter-identification procedure, and a falsifiable statistical test outside the proof kernel.

### Falsifiability and Precision {#sec:falsifiability_precision}

Formalization improves three forms of auditability:

1. **Syntactic precision:** every symbol has a type and every cited theorem has a resolvable identifier.
2. **Deductive auditability:** the kernel checks that the conclusion follows from the stated hypotheses.
3. **Assumption localization:** competing readings can be compared by diffing their types and hypotheses.

It does not automatically improve empirical falsifiability. A theorem can be perfectly proved yet vacuous, conditional on the desired conclusion, or disconnected from measurable data. That is why the semantic disposition and non-vacuity fields are co-equal with the native compile result.

### Theorems That Address Contested Claims {#sec:theorems_addressing_contested_claims}

The most informative current rows occupy different maturity levels:

- **fep-002** directly formalizes a narrow KL-remainder variational bound in `ℝ≥0∞`, including exactness when the approximation equals the posterior. The finite active-inference foundation separately constructs evidence and posterior from one normalized joint and proves posterior VFE attainment. H1's support-qualified composition identifies one finite recognition-to-posterior VFE gap with Mathlib-native KL; a general bridge across carriers and support regimes remains open.
- **fep-009** directly wraps generic conditional-independence symmetry and supplies conditional independence from the trivial σ-algebra as a non-vacuity witness. The finite blanket foundation supplies a nontrivial factorized law and zero conditional mutual information; fep-135--141 add a weighted-Dirac embedding and one native `CondIndepFun` transfer. Neither result turns every fep-005 assignment or arbitrary dynamics into a blanket.
- **fep-010** directly proves that a reversible Markov kernel preserves its reference measure and witnesses the contract with the identity kernel. Exact two-state relaxation, finite path-law fluctuation and reversible-dissipation identities, and empirical-law strong laws exist elsewhere, but generic ergodic convergence for fep-010's measure-kernel carrier and continuous path-space theory remain absent.
- **fep-014** directly wraps native KL non-negativity, self-zero, zero characterization, and the composition-product chain rule.
- **fep-030/fep-031** prove a binary entropy maximum and normalized finite Gibbs weights, with a composed theorem showing that the two-state zero-inverse-temperature Gibbs law attains the binary maximum.
- **fep-035** directly proves strict two-point Jensen for the logarithm under positive, nondegenerate weights; it does not discharge expectation-level integrability obligations.
- **fep-048** wraps native contraction uniqueness, supplies a concrete halving-map contraction witness, identifies its unique fixed point, and proves convergence of all iterates to zero.
- **fep-005** supplies a finite partition substrate but not probabilistic blanket independence.
- **fep-017/fep-034** use Mathlib's posterior kernel to prove normalized Bayesian inversion and a one-step transition--observation filter with joint reconstruction and prior recovery.
- **fep-018/fep-038/fep-044** provide a complete Bernoulli geometry instance: Fisher information, natural gradient, Fisher--Rao distance, and Hellinger separation. fep-100--106 extend the finite score carrier with categorical tangent positivity, rank/null witnesses, pullback, scalar Cramér--Rao, invertible-chart equivariance, mirror and affine Bregman identities, and replicator equivalence. fep-142--148 add a finite scalar exponential family with log-partition derivatives, Fisher--variance and KL--Bregman identities, and local mean-coordinate injection.
- **fep-025/fep-049** provide a finite non-detailed-balance stationary current and nonnegative current dissipation under an explicit diagonal resistance law.
- **fep-021** defines expected free energy as pragmatic cost minus epistemic information in `ENNReal`, proves exact reconstruction under the visible value-at-most-cost premise, and composes with native KL information gain. The maintained real-valued finite carrier separately derives both pragmatic-minus-epistemic and risk-plus-ambiguity forms under full support; equivalence to every literature convention and the truncating real-to-`ENNReal` bridge remain explicit limitations.
- **fep-028/fep-012** prove a full support-aware stochastic policy law and connect it to an entropy-regularized objective; optimality and sampling dynamics remain separate claims.
- **fep-121--127** prove exact Laplace error and bias decompositions, finite-law squared/Brier-risk transfer, and bad-event containment, with a nonzero-bias boundary; they do not prove posterior contraction or empirical calibration for their Laplace estimator. H1's separate selected Boolean sampling model does prove posterior bad-mass contraction, but that result does not transfer automatically to fep-036 or fep-121--127.
- **fep-128--134** prove arbitrary finite-depth policy-tree recursion, Bellman minimization, optimal-tree existence, open-loop embedding and dominance, treewise EFE, and a strict Boolean feedback witness; they do not define distributions or learning over trees.
- **fep-149--155** construct an exact positive-rate two-state continuous-time semigroup, master equation, detailed-balance stationary law, exponential relaxation, and strict Lyapunov witness; they do not construct a continuous-state SDE or Fokker--Planck PDE.

The generated `docs/formalism-coverage.md` is the canonical row-by-row account; prose examples are illustrative rather than an alternate maturity registry.

Beyond individual rows, `FEPComposed.FiniteReferenceAgent.finiteReferenceAgent_terminal` is the strongest current H1 composition. Two `true` observations produce the exact posterior $(1/10,9/10)$; one further `true` update is lifted to the sixteen-state blanket carrier. Under a four-to-one false-positive/false-negative report loss, the posterior-dependent continuation selects `true` and strictly beats either fixed report. The emitted action selects the exact refresh kernel described above, and that kernel strictly lowers both repository-real finite KL and Mathlib-native KL to the same invariant stationary law for the same lifted updated posterior. This is a single finite synthetic one-step certificate, not an aggregation of unrelated endpoint witnesses.

### Synthesis: What Formalization Reveals {#sec:synthesis_what_formalization_reveals}

The critical lines converge on a dependency problem. The maintained finite carrier discharges the first part of that order: a common probabilistic model produces posterior/evidence identities and both EFE decompositions; the policy-tree carrier supplies finite observation-contingent control; and the blanket carrier exposes an exact factorized joint, typed one-step dynamics, and one native conditional-independence transfer. H1 now discharges one deliberately selected connection across those interfaces: posterior learning, one further update, one asymmetric decision, one emitted action, a factorized invariant stationary law, and strict finite/native KL decrease share exact intermediate values. The next layers still require probability laws or learning over trees, EFE comparison and transition-aware planning on a shared carrier, blanket existence or invariance under broader dynamics and mixtures, and observation/refinement bridges before any of this becomes empirically discriminating. Proving downstream algebra without those upstream objects would still produce valid lemmas rather than the advertised system-level theory.

This dependency order is a constructive result of formalization. It turns “more rigor is needed” into specific interfaces and theorem obligations, and it prevents compiler success at a shallow layer from being mistaken for closure at a deeper one.

### Concrete Formalization Vignettes {#sec:concrete_vignettes}

**Native KL (fep-014).** The central zero characterization is:

```lean
theorem fep014_kl_eq_zero_iff (μ ν : Measure α)
    [IsFiniteMeasure μ] [IsFiniteMeasure ν] :
    InformationTheory.klDiv μ ν = 0 ↔ μ = ν :=
  InformationTheory.klDiv_eq_zero_iff
```

The theorem is strong and non-vacuous at its stated measure-theoretic scope. Its instances are not decoration: removing finite-measure assumptions changes the available result.

**Variational remainder (fep-002).** The project defines variational free energy as surprisal plus native KL and proves that it is at least surprisal. Exactness follows when both measure arguments are the same posterior under `SigmaFinite`. The proof does not smuggle a real-valued KL through `.toReal`, so infinite divergence remains visible.

**Global contraction (fep-048).** Mathlib's `ContractingWith c f` quantifies over every pair of real inputs and packages the strict coefficient bound. The concrete map `x ↦ x/2` witnesses the contract, has zero as its unique fixed point, and its iterates tend to zero from every real start. This repairs the common vacuity pattern in which a “contraction” premise applied only to two already fixed points or was never shown realizable, while keeping the claim narrower than general variational-dynamics convergence.

**Witnessed composition.** Both derivational graph edges and formal pairings require a qualified Lean declaration, not just prose. The {{formalism.metrics.theorem_witnessed_relations}} current witnesses span posterior filtering and Bayesian inversion, variational duality, controlled and temporal inference, causal blankets and interventions, predictive coding, finite path thermodynamics, Fisher and geometric optimization, collective inference, learning/model evidence, and the original entropy, policy, Gaussian, convergence, and partition-energy seams. Only {{formalism.metrics.formal_relation_witnesses}} assert a derivation or identification; the other {{formalism.metrics.formal_pairing_witnesses}} deliberately place separately proved endpoint laws together without implication. The maintained foundations add deeper within-carrier chains; these are counted separately from authored topic-to-topic edges. Conceptual edges remain visibly non-proof evidence, and the graph schema retains an explicit blocker kind for any future gap.

These vignettes also explain why **{{semantic_dispositions.formalized}}** catalogue rows currently carry the `formalized` disposition: directness, assumption quality, and a non-vacuity witness are required in addition to compilation. For fep-036, posterior closure was insufficient until an explicit finite binomial law, outcome-indexed estimator, shrinkage identity, and consistency-transfer theorem were added. The generated coverage projection is authoritative if that count changes.

### Limitations: What Formalization Does Not Do {#sec:what_formalisation_does_not_do}

The current contribution does not:

- validate the FEP empirically;
- establish a general Markov-blanket theorem for stochastic dynamics;
- derive causal identification from the H1 stationary factorization;
- turn H1's posterior-risk decision into transition-aware planning or EFE-optimal control;
- identify H1's strict KL-to-stationarity decrease with measured heat, physical entropy production, or thermodynamic free-energy dissipation;
- construct a continuous-state NESS or derive Fokker--Planck evolution;
- lift the finite scalar exponential-family and categorical Fisher carriers to multidimensional smooth statistical manifolds with dual connections and curvature;
- establish equivalence across broader EFE conventions and probability laws or learning over the finite policy-tree carrier;
- make an LLM response trustworthy without independent compilation and review; or
- make every warning-free theorem semantically representative of its topic title.

The catalogue's breadth is therefore a map of formalization surfaces, not {{total_topics}} end-to-end domain theorems. Its value lies partly in refusing to erase that distinction.

### Future: Machine-Verifiable Proofs in Journals {#sec:future_journal_verification}

A publication-ready formal theory should grow in dependency order:

1. connect the finite Laplace risk-transfer and learning-family concentration laws to posterior contraction for that empirical-Bayes estimator, minimax or empirical calibration, or an empirical marginal-likelihood theorem on one shared sampling model, without extrapolating from H1's Boolean witness;
2. add probability laws or learning over the finite policy-tree carrier and compare alternative EFE formulations under explicit equivalence hypotheses;
3. generalize H1's selected factorized invariant blanket to blanket existence, a reusable invariance interface, and arbitrary-mixture closure for a concrete stochastic dynamics;
4. lift the finite scalar exponential-family and categorical Fisher carriers to a multidimensional smooth family with dual connections and curvature;
5. generalize the exact two-state continuous-time chain and add one continuous-state stochastic/PDE model with existence, invariant-law, and NESS obligations; and
6. bind formal parameters to an auditable empirical model and falsification protocol.

Each step should land with a narrowed theorem, a non-vacuity witness or concrete model, a semantic review, native evidence, and manuscript references that resolve to the exact declaration. That workflow would let proponents and critics contribute competing formal statements without confusing “the kernel accepts this implication” with “nature satisfies these hypotheses.”
