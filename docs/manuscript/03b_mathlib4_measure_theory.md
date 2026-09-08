## Mathlib4 and Measure-Theoretic Probability {#sec:mathlib4_and_measure_theoretic_probability}

### What Is Mathlib4? A Short Orientation {#sec:what_is_mathlib4}

Mathlib4 [@mathlib2020] is Lean 4's community mathematical library. This project treats the pinned source as the authority on available definitions and theorem signatures. Lean `{{lean_toolchain}}` and Mathlib `{{mathlib_tag}}` are fixed by the Lake workspace so a later upstream addition cannot be cited as though it existed at the publication pin.

### Core Measure Theory and Stochastic Foundations {#sec:core_measure_theory}

The relevant substrate includes measurable spaces, extended-nonnegative-real-valued measures, probability-measure type classes, Radon--Nikodym derivatives, kernels, integrals, and information-theoretic KL divergence. Preconditions are part of theorem types: finiteness, sigma-finiteness, measurability, and Markov-kernel instances cannot be elided by prose.

At the pin, KL divergence is the native `InformationTheory.klDiv : Measure α → Measure α → ℝ≥0∞`. The extended codomain preserves infinite divergence. A conversion through `.toReal` would map infinity to zero unless finiteness is separately established, so the strengthened catalogue statements stay in `ℝ≥0∞`.

### Key Mathlib4 Lemmas Referenced by the Catalogue {#sec:key_mathlib4_lemmas_referenced}

The generated coverage report derives the exact import surface. Representative direct dependencies include measure monotonicity and subadditivity, probability mass of the universe, finite-sum order laws, real log/exp facts, metric inequalities, matrix transpose laws, and the following KL declarations:

- `InformationTheory.klDiv_self`;
- `InformationTheory.klDiv_eq_zero_iff` for finite measures;
- `InformationTheory.klDiv_compProd_eq_add` for finite measures and Markov kernels.

The catalogue wraps these declarations in topic-local theorems rather than copying their proofs.

The project-local finite information layer goes further at its explicitly finite, full-support scope. It proves conditional entropy and conditional KL definitions, a joint/channel KL chain rule, the resulting prior-marginal KL bound, independent-product additivity, and the entropy identity and cardinality bound for mutual information. These are finite-sum theorems over the shared generative carrier; they are not presented as generic measure-theoretic data-processing or disintegration results.

### Coverage Map and Dependency Graph {#sec:coverage_map_and_dependency_graph}

`docs/formalism-coverage.md` reports the area/disposition matrix, per-topic theorem and definition counts, exact imports, and open semantic obligations. Shared imports are library-incidence edges, not proof dependencies among the independently namespaced topics.

#### Coverage by FEP Area {#sec:coverage_by_fep_area}

FEP and Bayesian rows use the measure/probability stack; Active Inference relies heavily on finite sums and order; Information Geometry combines native KL with elementary inner-product and metric facts; Thermodynamics uses real log/exp and ordered algebra. The semantic audit shows where those library facts remain only substrates for the advertised domain concept.

#### FEP and Active Inference ({{areas.FEP.count}} + {{areas.ActiveInference.count}} topics across areas) {#sec:fep_and_active_inference_coverage}

Finite-policy existence, nonnegative aggregation, and basic probability normalization are well supported. The maintained finite carrier now supplies a common probabilistic model, mutual-information epistemic value, both central expected-free-energy decompositions, and support-explicit nonnegativity. The remaining scope boundary is equivalence to alternative measure-valued or generalized-coordinate EFE formulations, not absence of a shared finite model.

#### Geometry, Mechanics, and Thermodynamics ({{areas.InfoGeometry.count}} + {{areas.BayesianMechanics.count}} + {{areas.Thermodynamics.count}} topics) {#sec:geometry_mechanics_thermodynamics_coverage}

Native KL and posterior laws are direct, and the Bernoulli family has an exact Fisher metric, natural gradient, Fisher--Rao distance, and Hellinger divergence. Finite categorical score geometry supplies tangent positivity, full-rank and null witnesses, pullback, scalar Cramér--Rao, chart-equivariant natural gradients, mirror descent, Bregman projection, and replicator equivalence. The later scalar exponential family adds full-support normalization, log-partition derivatives, Fisher--variance equality, KL--Bregman duality, and interval-local mean-coordinate injection. Finite NESS current, path-law fluctuation identities, Jarzynski normalization, reversible KL dissipation, and an exact two-state continuous-time semigroup/master equation are direct at their stated finite scopes. The remaining frontier is general smooth-manifold structure, generic CTMC and continuous stochastic path measures, and PDE-level stationarity.

### The Import Pattern Strategy {#sec:the_import_pattern_strategy}

Each canonical topic body declares the narrow Mathlib modules it uses. Narrow imports make missing APIs and accidental dependencies visible and keep generated coverage meaningful. `LeanVerifier` passes a body with leading imports through as an independent source unit.

### A Worked Example: KL Divergence and the ELBO {#sec:worked_example_kl_elbo}

For a generative model and variational posterior, the familiar ELBO identity is:

$$
\mathrm{ELBO}(q)=\log p(o)-\KL\!\left(q\,\middle\|\,p(\cdot\mid o)\right).
$$ {#eq:mathlib_elbo}

Equivalently,

$$
F(q)=-\mathrm{ELBO}(q)= -\log p(o)+\KL\!\left(q\,\middle\|\,p(\cdot\mid o)\right).
$$ {#eq:mathlib_vfe_kl}

fep-002 formalizes the algebraic KL remainder in the native extended codomain: surprisal plus `klDiv` is at least surprisal, and equality holds at the posterior under `SigmaFinite`. That row does not derive `p(o)` or the posterior from a joint measure. fep-014 separately proves KL nonnegativity, self-zero, zero characterization, and the composition-product chain rule. The maintained finite model closes the corresponding discrete bridge by constructing predicted evidence and a posterior from normalized kernels, then proving VFE attainment and a support-qualified equality characterization. This layered design avoids pretending that a library theorem alone supplies the generative-model interpretation or that the finite real-valued result automatically lifts to arbitrary measures.

### Gap Analysis: What Mathlib4 Does Not Yet Provide {#sec:gap_analysis}

At this pin, Mathlib exposes generic measure-KL data processing under a Markov kernel as `InformationTheory.klDiv_comp_right_le`. That upstream theorem is not part of fep-014's maintained theorem surface, and fep-063 remains the project's support-qualified, strictly positive finite-channel theorem over totalized real KL rather than an unconditional bridge to native extended KL. The project does provide native measure-KL information gain; finite entropy, KL, and mutual information; both EFE decompositions on a shared policy-conditioned carrier; a complete Bernoulli Fisher--Rao instance; arbitrary finite-dimensional Fisher score geometry; a scalar exponential family; and a normalized finite blanket factorization whose weighted-Dirac embedding satisfies native `CondIndepFun`. The remaining gaps are a general finite-to-measure conditional-information equivalence, smooth manifold and connection theory, generic blanket existence or invariance, and Itô/Langevin and Fokker--Planck developments beyond the exact Boolean continuous-time chain. The coverage audit distinguishes these project obligations from confirmed upstream-library limitations.
