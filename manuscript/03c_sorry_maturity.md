## The `sorry` Mechanism and Formalization Maturity {#sec:the_sorry_mechanism_and_formalization_maturity}

### What `sorry` Does {#sec:what_sorry_does}

Lean's `sorry` closes an arbitrary proof goal by introducing an admitted placeholder. The file may still compile, but Lean emits a warning and the declaration depends on a generated axiom. Compilation with `sorry` is therefore not proof completion.

```lean
theorem expected_free_energy_decomposition (π : Policy) :
    EFE π = risk π + ambiguity π := by
  sorry
```

The project scans source text and compiler diagnostics because an exit code alone cannot distinguish a complete declaration from one accepted with `sorry`.

### Three Maturity Levels {#sec:three_maturity_levels}

`mathlib_status` records syntactic/proof completion of a row, with values `real`, `partial`, or `aspirational`. All {{total_topics}} shipped rows are tagged `real`; no shipped canonical body contains `sorry`. This field is intentionally **not** the semantic maturity verdict.

A second axis, `semantic_disposition`, records whether the primary theorem directly captures its narrowed claim or is a proxy/gap. The current generated counts include {{semantic_dispositions.formalized}} `formalized`, {{semantic_dispositions.conditional_proxy}} `conditional_proxy`, and {{semantic_dispositions.structural_proxy}} `structural_proxy` rows. A row can therefore be `mathlib_status: real` without being semantically direct; the schema and firewall preserve that distinction rather than promoting it from compilation.

#### Level 1 — `real` (Kernel-Complete at the Stated Scope) {#sec:level_real}

A `real` body has no admitted proof and is accepted by the pinned Lean/Mathlib environment. Illustrated on the primer's union bound rather than on a catalogue row, so that the shape is visible in ten lines:

```lean
import Mathlib.MeasureTheory.Measure.MeasureSpace

namespace PrimerUnionBound
open MeasureTheory

theorem union_bound {α : Type*} [MeasurableSpace α]
    (μ : Measure α) (s t : Set α) :
    μ (s ∪ t) ≤ μ s + μ t :=
  measure_union_le s t
end PrimerUnionBound
```

This proves exactly the measure union bound. The topic title may motivate an FEP interpretation, but the kernel does not transfer that interpretation into the theorem type. Semantic review must do that separately.

#### Level 2 — `partial` (Typed Statement With Admitted Subgoals) {#sec:level_partial}

A `partial` row would contain one or more localized `sorry` terms. Such a row can be useful on a research branch because Lean checks the surrounding types, but it is excluded from the shipped catalogue and from claim-ready evidence. The preferred publication behavior is either to prove the missing lemma or to narrow the statement to an honest complete theorem and record the remaining gap in the semantic audit.

#### Level 3 — `aspirational` (Target Signature Only) {#sec:level_aspirational}

An `aspirational` row documents a desired signature whose proof is not present. The project keeps such targets in prose or coverage-roadmap fields rather than in the verified catalogue. This prevents a compilable file containing an admitted axiom from resembling a completed result.

### The Zero-`sorry` Policy {#sec:zero_sorry_policy}

The canonical catalogue, generated aggregate, native receipt, and publication variables all enforce zero `sorry`. A native receipt is claim-ready only when it covers the exact ordered roster of {{total_topics}} topics and independently reports zero warnings and zero admitted bodies. A filtered or stale receipt cannot satisfy the full-catalogue predicate.

Zero `sorry` is necessary but not sufficient. The semantic audit additionally checks the exact primary theorem, assumption quality, non-vacuity rationale, and acceptance probe. This blocks the common failure mode of replacing a difficult domain theorem with an easy tautology while retaining the stronger title.

### The Compilation Gate: How Zero-Sorry Is Enforced {#sec:compilation_gate}

The enforcement layers are complementary:

1. `FEPTopicCatalogue` rejects malformed or incomplete generated rows and theorem/signature count drift.
2. `LeanVerifier` detects non-comment `sorry`, invokes the real pinned compiler, and retains warnings/errors in a structured result.
3. `uv run fep-lean verify --fail-on-warnings --receipt output/native-verification.json` requires clean per-topic results and atomically writes a source-digest-bound receipt.
4. `lake build FepSketches` checks the topic aggregate and manifested maintained formal modules together, exposing namespace collisions, broken dependencies, and declaration warnings.
5. `scripts/_maint_build_fep_all_lean.py --check` and `scripts/_maint_build_formal_modules.py --check` reject projection drift without rewriting tracked files.
6. The receipt validator recomputes roster, counts, digests, toolchain, and claim readiness instead of trusting stored booleans.
7. The formalism declaration/axiom audit, semantic audit, and theorem-reference audit reject unresolved evidence names, `sorryAx`, missing primary declarations, and stale manuscript theorem names.

These checks distinguish proof completeness, compiler cleanliness, source freshness, and semantic fidelity rather than collapsing them into one “green” status.

#### ✓ `real` (What It Does and Does Not Mean) {#sec:real_fully_verified}

For a canonical row, `real` means:

- the statement and proof term are accepted at the pinned toolchain;
- the body contains no `sorry`;
- imported declarations resolve; and
- the generated source/signature projections agree.

It does **not** mean that the topic title is proved at its broadest reading, that assumptions hold in a biological system, or that the theorem is empirically adequate. For example, fep-028 directly proves finite softmax normalization, while fep-005 proves only properties of a supplied finite label assignment. Both are kernel-complete; their semantic reach differs.

![Syntactic proof-status distribution across the {{total_topics}} catalogue rows. This figure reports `mathlib_status`, not semantic disposition; the separate coverage report supplies the semantic matrix.](../output/figures/status_distribution.png)

### Migration From `partial` to `real`: A Worked Example {#sec:migration_partial_to_real}

The important migration is not merely “make the compiler green.” fep-014 previously used generic measure-set inequalities as a proxy for KL behavior. Inspection of the pinned Mathlib source showed that native `InformationTheory.klDiv`, self-zero, finite-measure zero characterization, and the composition-product chain rule were already available. The row was replaced with direct wrappers of those declarations and its semantic disposition was upgraded only after the theorem type, assumptions, and non-vacuity were reviewed.

The workflow for such a migration is:

```bash
uv run python scripts/_maint_build_topics_catalogue.py
uv run python scripts/_maint_build_fep_all_lean.py
uv run fep-lean verify --topic fep-014 --fail-on-warnings
uv run python scripts/theorem_maturity_audit.py
uv run python scripts/build_formalism_coverage.py
```

This sequence updates the authoring graph, proves the focused row, and refreshes the semantic projection. A full receipt is generated only after the entire catalogue passes.

### Maturity by FEP Area {#sec:maturity_by_area}

Per-area `mathlib_status` is uniform in this release and therefore not very informative. The generated area-by-`semantic_disposition` matrix in `docs/formalism-coverage.md` is the meaningful comparison: it distinguishes {{semantic_dispositions.formalized}} direct rows from {{semantic_dispositions.conditional_proxy}} conditional and {{semantic_dispositions.structural_proxy}} structural proxies. The fep-036 topic adds a finite binomial PMF, an outcome-indexed Laplace estimator, exact shrinkage, and deterministic consistency transfer. The statistical-convergence module discharges its asymptotic premise, the learning family separately proves finite concentration and model-evidence laws, and `fep-121`--`fep-127` add finite-law Laplace squared/Brier-risk and bad-event transfer. These results still do not supply posterior contraction, minimax or empirical calibration, or a marginal-likelihood optimum for the estimator.

### Why Aspirational Proofs Are Rejected {#sec:why_aspirational_proofs_are_rejected}

Shipping admitted targets would blur three distinct activities: specifying a desirable theorem, proving it, and showing it represents the scientific claim. The project instead keeps the executable corpus axiom-free with respect to `sorry`, records stronger targets as explicit gaps, and permits narrow complete proxies only when their reduced scope is visible in the catalogue and manuscript. This produces fewer headline theorems, but a much clearer evidentiary boundary.
