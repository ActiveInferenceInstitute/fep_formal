## Lean 4: A Primer for Active Inference Researchers {#sec:lean_4_a_primer_for_active_inference_researchers}

### Why Formal Verification Matters for the FEP {#sec:why_formal_verification_matters_for_the_fep}

The Free Energy Principle [@friston2010free; @parr2022active] rests on deep intersections of measure theory, stochastic calculus, differential geometry, and information theory. Informal mathematical proofs in this space — written in natural language with $\forall$ and $\exists$ symbols — are powerful but can harbor subtle errors: interchanging limits and expectations without justification, conflating almost-sure and sure convergence, or silently assuming absolute continuity of measures. When the FEP community claims that "variational free energy upper-bounds surprise," every step of the derivation must be airtight — yet in practice verification depends on peer review by a small number of domain experts.

**Lean 4** is an interactive theorem prover (ITP) that makes this bottleneck explicit. Every elaborated inference step is checked by Lean's kernel against declared axioms and definitions. Acceptance therefore certifies the exact formal statement under the recorded toolchain and trust base; it does not by itself certify that the statement faithfully represents the intended scientific claim. That second obligation is why this project records a separate semantic disposition and assumption review.

For Active Inference, this yields:

- **Verifiable variational bounds.** The claim $F \geq -\log p(s|m)$ is checked all the way down to the axiom level.
- **Dimension safety.** Type-checking prevents integrating over the wrong measure space or mixing distributions over incompatible state spaces.
- **Compositional scaling.** Proven lemmas compose into larger theorems without re-verification.
- **Reproducibility.** A Lean proof file is itself a reproducible artifact, unlike a journal PDF.

Throughout this primer — and the full {{total_topics}}-topic catalogue — the pinned toolchain is **Lean 4 `{{lean_toolchain}}`** with **Mathlib4 `{{mathlib_tag}}`**. Every lemma name, module path, and tactic behavior cited resolves against that exact pin; version drift is prevented by the `lean/lean-toolchain` and `lean/lakefile.lean` files in the repository.

### Propositions as Types: The Curry-Howard Correspondence {#sec:propositions_as_types_the_curry_howard_correspondence}

Lean 4 is built on a deep correspondence between logic and computation called the **Curry-Howard isomorphism**. The slogan — **propositions as types, proofs as programs** — captures the whole design: every mathematical proposition is reified as a type, every proof of that proposition is reified as a term (a program) inhabiting that type, and the compiler's type-checker *is* the proof-checker. Verifying "theorem $T$ is correct" reduces mechanically to verifying "the program `t` has type `T`".

| Logic | Type Theory (Lean 4) |
|-------|---------------------|
| Proposition $P$ | Type `P` |
| Proof of $P$ | Term `p : P` (a program of type `P`) |
| $P \implies Q$ | Function type `P → Q` (a program that transforms proofs) |
| $\forall x, P(x)$ | Dependent function `(x : α) → P x` |
| $P \land Q$ | Product type `P × Q` |
| $P \lor Q$ | Disjunction `Or P Q` (proof-irrelevant; `P ⊕ Q` is the data-level analogue) |
| Modus ponens | Function application `f a : Q` given `f : P → Q`, `a : P` |
| $\bot$ (false) | Empty type `False` |
: The Curry-Howard correspondence: each logical connective and the Lean 4 type that represents it.

In Lean 4, proving a theorem is equivalent to constructing a program whose type is the proposition being proved. If the program type-checks, the theorem is proven. This is fundamentally different from computer algebra systems (Mathematica, SymPy) which *compute* with symbols but cannot *prove* that a result holds for all inputs universally. The Curry-Howard lens is also what justifies the FEP verifier treating `lake env lean` exit code 0 as *proof*: successful type-checking of the proof term is, by construction, a checked proof of the stated theorem.

### Universe Polymorphism and Dependent Types {#sec:universe_polymorphism_and_dependent_types}

Standard type systems distinguish `Int`, `Float`, `String`. Lean 4 supports **dependent types** where types can depend on *values*:

```lean
-- A vector of exactly n elements
def Vector (α : Type) (n : Nat) : Type := ...

-- A probability measure on a measurable space
structure ProbMeasure (α : Type) [MeasurableSpace α] where
  μ : Measure α
  total : μ Set.univ = 1
```

For Active Inference, dependent types naturally encode:

- **Parameterized distributions.** `Distrib (S ω)` — distributions indexed by world-states.
- **Transition kernels.** `(s : State) → Measure (Action s)` — action distributions whose type depends on the current state.
- **Finite policy spaces.** `Fin n → Action` — a policy over exactly $n$ time steps.

Lean also leans heavily on **universe polymorphism** (`Type u`, `Type v`). In measure theory this prevents Russell's paradox by ensuring that the collection of all measurable spaces lives strictly above any individual space. FEP researchers encounter this most often as `{α : Type*}` in theorem signatures; the `*` simply means the type can live in any universe.

### Tactics: How Proofs Are Constructed {#sec:tactics_how_proofs_are_constructed}

Lean 4 proofs are written using **tactics**—commands that transform proof goals step by step. Key tactics used in FEP formalizations:

| Tactic | What it does | FEP usage |
|--------|-------------|-----------|
| `exact h` | Close goal exactly with term `h` | Apply `measure_union_le`, `measure_mono` directly |
| `rw [h]` | Rewrite goal using equation `h` | Substitute `IsProbabilityMeasure.measure_univ` |
| `apply f` | Apply function/lemma `f`, leaving subgoals | Apply `Real.exp_le_exp.mpr` for Gibbs monotonicity |
| `simp [h]` | Simplify using `h` and simp lemmas | Reduce `Finset.sum_div`, `Finset.card_range` |
| `intro x` | Introduce $\forall$/implication hypothesis into context | Start proofs of `∀ x, P x` or `P → Q` goals |
| `constructor` | Split a goal into its structural pieces | Build `And`/`Iff`/structure goals (e.g., softmax normalization $\land$ non-negativity) |
| `linarith` | Linear arithmetic over ordered fields | Derive bounds from KL ≥ 0 by rearranging |
| `nlinarith [h₁, h₂]` | Nonlinear arithmetic with hints | Prove quadratic contraction in gradient flow |
| `positivity` | Prove `0 ≤ e` or `0 < e` automatically | Non-negativity of sum of squares, `Real.sqrt` |
| `ring` | Prove equalities in commutative rings | Algebraic identities in free energy decompositions |
| `norm_num` | Evaluate numeric expressions | Verify `(2 : ℝ) > 0` or specific constants |
| `have h : P := ...` | Introduce intermediate lemma `h : P` | Build step-by-step proofs for complex bounds |
| `calc` | Chain transitivity steps | $a \leq b \leq c$ derivations in energy bounds |
| `sorry` | Admit goal without proof | Mark aspirational proof steps (compile flag) |
: Lean 4 tactics used in the catalogue bodies, with the goal transformation each performs and where it appears in the FEP formalizations.

The catalogue's {{total_topics}} Lean bodies collectively exercise the major tactic families enumerated above. `exact`, `simp`, `rw`, `linarith`, `positivity`, and `have` dominate by frequency, while `nlinarith`, `ring`, `norm_num`, `intro`, `constructor`, and `calc` appear in specific topic families — for example, `calc` anchors fep-021's energy-bound derivation, and `constructor` structures fep-028's softmax lemma. The exhaustiveness claim is intentionally conservative: a small handful of niche tactics (e.g. `omega` and `decide`) are used opportunistically rather than uniformly.

**How `lake env lean` verification works in the pipeline.**

`LeanVerifier` writes each sketch to its own temporary file under `lean/FepSketches/`, created by `tempfile.mkstemp` with the prefix `_verify_<topic-id>_` and the suffix `.lean`, and unlinked once the subprocess returns. Before the subprocess call, `_wrap_lean_code` prepends `import Mathlib`, the fixed `open MeasureTheory ProbabilityTheory Real Nat Finset Set` line, and `open scoped BigOperators` — but only to a body that does not already begin with `import`, and all {{total_topics}} catalogue bodies do. For every row in `config/topics.yaml` the wrapper therefore returns the body unchanged, and the imports, the opens, and the `namespace FEP<NNN> … end FEP<NNN>` block, where `<NNN>` is the topic's three-digit identifier, are the ones the body itself declares. With `lean/` as the working directory, the verifier then invokes `lake env lean FepSketches/_verify_<topic-id>_<suffix>.lean`. That file exists only for the duration of the call, so the reproducible form of one topic's verification is the entry point that creates it:

```bash
uv run fep-lean verify --topic fep-001
```

This executes inside the Lake build environment rooted at `lean/`, which provides access to the pre-compiled Mathlib4 `{{mathlib_tag}}` `.olean` files. Exit code 0 signals compilation success. The verifier captures `stdout` and `stderr`, sets `compiles` to `True` or `False`, detects a `sorry` tactic in the source text, and returns the resulting `VerifyResult`; `--receipt` writes it into the typed native receipt, and native mode persists nothing in SQLite, whose session store belongs to full OpenGauss mode ([@sec:sqlite_schema_five_tables]). Elapsed time is hardware- and cache-dependent, so it is quoted only from the selected receipt rather than as a range: across the {{verify.topics_with_result}} results of `{{verify.run_id}}` the per-topic minimum is {{verify.min_topic_s}} s, the median {{verify.median_topic_s}} s, the mean {{verify.mean_topic_s}} s, and the maximum {{verify.max_topic_s}} s.

> **Namespace isolation.** The `namespace FEP<NNN> ... end FEP<NNN>` wrapper prevents theorem-name collisions during the {{total_topics}}-topic aggregate compilation: when sketches are concatenated into `fep_all.lean` for the batch build, identically named helpers (for example two topics both declaring `aux_lemma`) live in disjoint namespaces and never clash. Every row in `config/topics.yaml` follows this pattern.

**Mathlib4 module map for FEP topics:**

| Topic Area | Key Mathlib4 Modules |
|-----------|---------------------|
| FEP / measure theory | `MeasureTheory.Measure.MeasureSpace`, `MeasureTheory.Measure.NullMeasurable` |
| Probability | `Probability.Notation`, `MeasureTheory.Measure.ProbabilityMeasure` |
| Special functions | `Analysis.SpecialFunctions.Log.Basic`, `Analysis.SpecialFunctions.Exp` |
| Linear algebra | `LinearAlgebra.Matrix.Transpose`, `Analysis.InnerProductSpace.Basic` |
| Finite sums | `Algebra.BigOperators.Group.Finset`, `Data.Finset.Basic` |
| Metric spaces | `Topology.MetricSpace.Basic`, `Topology.MetricSpace.PseudoMetric` |
| Real arithmetic | `Analysis.SpecialFunctions.Pow.Real`, `Mathlib.Tactic` |
: Mathlib4 modules each catalogue topic area draws on.

### From Informal Bound to Lean Statement: A Minimal Walk-Through {#sec:informal_to_formal_walkthrough}

Before the full ELBO, consider the simplest FEP-flavoured informal claim and its literal translation into Lean.

**Informal (textbook):**

> *Claim.* For any two events $A, B$ in the state space of an agent, the probability that the world is in $A \cup B$ is at most the sum of the individual probabilities: $\mu(A \cup B) \leq \mu(A) + \mu(B)$. *(This is the countable-subadditivity bound that underwrites the union step in most FEP surprise-minimization arguments.)*

**Formalization, step by step:**

1. *Name the space.* Informal "state space" becomes `{α : Type*} [MeasurableSpace α]` — a type equipped with a σ-algebra.
2. *Name the measure.* Informal "probability" becomes `(μ : Measure α)` — a Mathlib4 `Measure` over that space.
3. *Name the events.* Informal "events $A, B$" become `(s t : Set α)`.
4. *State the inequality.* `μ (s ∪ t) ≤ μ s + μ t`.
5. *Discharge the proof.* Invoke the Mathlib4 lemma `measure_union_le` via the `exact` tactic.

**Formal (Lean 4, Mathlib4 `{{mathlib_tag}}`) — a primer illustration, not a catalogue row:**

```lean
import Mathlib.MeasureTheory.Measure.MeasureSpace

open MeasureTheory

namespace PrimerUnionBound

theorem union_bound {α : Type*} [MeasurableSpace α]
    (μ : Measure α) (s t : Set α) :
    μ (s ∪ t) ≤ μ s + μ t := by
  exact measure_union_le s t

end PrimerUnionBound
```

Every implicit assumption of the informal claim has been made explicit (the type, its σ-algebra, and the two sets), and the inequality is discharged by a single pre-verified Mathlib4 lemma. Three structural conventions carry over to every catalogue body: a namespace, so names cannot collide in the {{total_topics}}-topic aggregate build; targeted imports rather than the whole of Mathlib4; and an `open` block that brings the needed names into scope without fully-qualified paths.

What the illustration does not carry over is scale. Catalogue rows state the FEP quantity itself rather than a Mathlib4 lemma restated under a new name. Row `fep-001`, the variational free-energy bound, declares two definitions and three theorems over `InformationTheory.klDiv`:

```lean
import Mathlib.InformationTheory.KullbackLeibler.Basic

namespace FEP001

variable {α : Type*} [MeasurableSpace α]

open MeasureTheory
open scoped ENNReal

/-- Native variational gap between an approximate and exact posterior law. -/
noncomputable def fep001_variationalGap
    (approximation posterior : Measure α) : ENNReal :=
  InformationTheory.klDiv approximation posterior

/-- Surprisal plus the native KL variational gap. -/
noncomputable def fep001_variationalUpperBound
    (approximation posterior : Measure α) (surprisal : ENNReal) : ENNReal :=
  surprisal + fep001_variationalGap approximation posterior

/-- The KL remainder makes the variational quantity an upper bound. -/
theorem fep001_variationalUpperBound_ge
    (approximation posterior : Measure α) (surprisal : ENNReal) :
    surprisal ≤
      fep001_variationalUpperBound approximation posterior surprisal := by
  exact le_add_right (le_refl _)

end FEP001
```

The row also proves `fep001_variationalGap_eq_zero_iff` — the gap vanishes exactly at the posterior for finite measures — and `fep001_variationalUpperBound_eq_iff`, its consequence at finite surprisal. The complete body, and every other row's, is reproduced in the generated catalogue appendix.

### Concrete Example: Informal vs Formal ELBO {#sec:concrete_example_informal_vs_formal_elbo}

**Informal (journal paper)**:

> *Theorem*. The Evidence Lower Bound maximizes model evidence: $\log p(s) \geq -F[q, p]$.
> *Proof*. By definition, $F = \KL[q \| p(\psi|s)] - \log p(s)$. Since KL divergence is non-negative, the result follows immediately by rearranging terms. ∎

**Formal kernel used by fep-002 (Lean 4 with Mathlib4 `{{mathlib_tag}}`)**:

```lean
import Mathlib.InformationTheory.KullbackLeibler.Basic

namespace FEP002
variable {α : Type*} [MeasurableSpace α]
open MeasureTheory
open scoped ENNReal

noncomputable def fep002_variationalFreeEnergy
    (q posterior : Measure α) (surprisal : ENNReal) : ENNReal :=
  surprisal + InformationTheory.klDiv q posterior

theorem fep002_vfe_ge_surprisal
    (q posterior : Measure α) (surprisal : ENNReal) :
    surprisal ≤ fep002_variationalFreeEnergy q posterior surprisal := by
  simp only [fep002_variationalFreeEnergy]
  exact le_add_right (le_refl surprisal)
end FEP002
```

The topic-row version fixes the measurable space, both measures, the order of KL arguments, and the nonnegative extended-real codomain. Its inequality is deliberately narrower than the informal theorem: it treats surprisal and posterior as inputs rather than constructing them from a joint model. The separate finite `GenerativeModel` foundation closes that bridge for one normalized finite carrier by constructing evidence and posterior, proving Bayes reconstruction, and deriving posterior-form VFE and its evidence bound. Keeping the two declarations separate makes the difference between a native measure-level remainder theorem and a finite model theorem visible in their types.

**Catalogue note.** The {{total_topics}} committed bodies in the family modules under `src/fep_lean/catalogue/bodies/` carry targeted `import Mathlib.…` lines. The validated registry fixes their order and source identity. [`LeanVerifier._wrap_lean_code`]({{publication.repository_url}}/blob/{{source.published_ref}}/src/fep_lean/verification/lean_verifier.py) preserves a body with leading imports and supplies the shared preamble only when imports are absent ([@sec:native_lean_4_compilation_and_zero_direct_verification]; Appendix B).

### Reading Type Error Messages {#sec:reading_type_error_messages}

When translating FEP physics into Lean, compilation errors typically fall into three categories:

1. **Type mismatch.** `application type mismatch: expected 'Measure ℝ', got 'ℝ'` — raised when passing a scalar prediction error into a function expecting a full belief distribution.
2. **Missing instance.** `failed to synthesize instance 'MeasurableSpace α'` — Lean refuses to integrate over a space that has not been declared measurable.
3. **Unsolved goal.** `unsolved goals: ⊢ q ≪ p` — the theorem requires absolute continuity, but no proof or hypothesis supplies it.

`LeanVerifier.classify_failure_kind` maps these patterns (plus `missing_import`, `renamed_identifier`, `timeout`, and the `killed` class — SIGKILL-style process death and out-of-memory kills, matched only after the timeout-specific patterns and kept distinct from the generic killed/OOM fallback) onto the `FailureKind` enum carried inside every `VerifyResult`. These errors are not bugs in the pipeline; they are the compiler enforcing mathematical rigor.
