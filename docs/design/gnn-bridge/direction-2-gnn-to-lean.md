# Direction 2 — formalize GNN steps and methods in Lean

Status: **research program; Q1–Q4 accepted** — Q1 (document AST and
decidable well-formedness) under `specs/gnn-bridge-q1-syntax-ast/`
(module `src/fep_lean/formal/gnn_document.lean`, `FEP.GnnDocument`);
Q2 (discrete denotation, `src/fep_lean/formal/gnn_denotation.lean`,
`FEP.GnnDenotation`) under `specs/gnn-bridge-q2-discrete-denotation/`;
Q3 (continuous denotation,
`src/fep_lean/formal/gnn_denotation_continuous.lean`,
`FEP.GnnContinuous`) under
`specs/gnn-bridge-q3-continuous-denotation/`; Q4 (renderer and execution
statements, `src/fep_lean/formal/gnn_render_statements.lean`,
`FEP.GnnRenderStatements`) under
`specs/gnn-bridge-q4-renderer-execution-statements/`. Alignment
statements 1, 3, and 5 (matrix fragment plus the kernel-power execution
semantics) are landed declarations; statement 2, statement 4, the
full program-denotation fragments, and the jax continuous / bnlearn CPT
fragments remain prospective targets with recorded reopen conditions.
Parent program:
[GNN bridge README](README.md). Shared rules:
[bridge contract](bridge-contract.md).

## Goal

Give GNN's parse → validate → render → execute contract machine-checked
semantics: the GNN document language, its well-formedness rules, and the
dynamic meaning of its two supported model families become Lean definitions
and theorems, hosted in this catalogue's formal workspace and reusing its
existing carriers.

The syntax surface and the step inventory are owned by GNN and frozen per
slice:

- normative syntax: `GeneralizedNotationNotation/docs/gnn/gnn_syntax.md`
  (sectioned Markdown documents; sections `GNNSection`, `GNNVersionAndFlags`,
  `ModelName`, `StateSpaceBlock`, `Connections`, `ModelAnnotation`,
  `InitialParameterization`, `Equations`, `Time`, `ActInfOntologyAnnotation`,
  `ModelParameters`, `Footer`, `Signature`);
- pipeline steps: the canonical registry at
  `GeneralizedNotationNotation/src/pipeline/step_registry.py` — parse
  (step 3, `src/gnn/`), type check (step 5, `src/type_checker/`),
  validation (step 6, `src/validation/`), export (step 7), ontology
  (step 10, `src/ontology/`), render (step 11, `src/render/`), execute
  (step 12, `src/execute/`).

## Formalization targets

| GNN method | GNN-side owner | Lean target (prospective) |
| --- | --- | --- |
| Sectioned document grammar | step 3 parse (`src/gnn/`) | document AST as inductive types: sections, typed state-space blocks over string indices, connection lists |
| Connection grammar (`A>B`, `A-B`, `:label`) | step 3 parse | directed/undirected edge predicates; decidable well-formedness of the edge set |
| State-space typing (`NAME[dims, key=value]`) | step 5 type checker (`src/type_checker/`) | typed block formation; dimension consistency with `ModelParameters` |
| Ontology binding validity | step 10 (`src/ontology/`, vocabulary `src/ontology/act_inf_ontology_terms.json`) | binding predicate parameterized by the frozen vocabulary; exemplar bindings decide |
| Validation and consistency rules | step 6 (`src/validation/`) | propositions mirroring each maintained validation rule |
| Render (step 11, nine targets) | `src/render/` | semantics-preservation statements per target (statements first; proofs are later slices) |
| Execute (step 12, eight targets) | `src/execute/` | denotational semantics of the two supported families (below) |

Free-text sections (`ModelAnnotation`) and the `Footer`/`Signature` sections
carry provenance and prose, not semantics; they stay outside the formal
object language rather than receiving arbitrary meaning.

## Alignment statements (prospective)

Each statement below is a target for a future slice; none is an existing
declaration, and none reserves a catalogue identifier:

1. **Discrete denotation.** A well-formed discrete-family GNN document
   denotes an instance of the `active_inference.lean` `GenerativeModel`:
   `A` ↔ likelihood, `B` ↔ policy-indexed transition ordered
   `(next_state, previous_state, action)`, `C` ↔ preferences,
   `D` ↔ initial prior, `E` ↔ habit prior.
2. **Free-energy readouts.** The `F[1]` variational-free-energy readout
   corresponds to `variationalFreeEnergy`; the `G=ExpectedFreeEnergy`
   ontology binding corresponds to
   `expectedFreeEnergy_eq_risk_add_ambiguity` and
   `epistemicValue_eq_entropy_sub_ambiguity`.
3. **Continuous denotation.** A well-formed continuous-family document
   denotes a `LinearGaussianParameters` instance (`F/H/Q/R`,
   `prior_mean`/`prior_cov`), matching
   `linear_gaussian_semigroup.lean` transition laws.
4. **Filtering agreement.** Executing the discrete family's inference loop
   realizes forward filtering whose reconstruction agrees with
   `temporal_inference.lean` (`forwardFilter_reconstruction`,
   `forward_backward_evidence_agree`) on the same carrier.
5. **Renderer preservation.** For each render target, the rendered program's
   denotation equals the document's denotation (statement per target; proofs
   follow only where a target has a formal semantics to state against).

## Phases

| Phase | Outcome | Acceptance | No-go |
| --- | --- | --- | --- |
| Q1 — AST and well-formedness | Lean AST over the frozen syntax surface plus decidable well-formedness | all GNN exemplars under `input/gnn_files/` decide correctly; compiles warning-free in the pinned workspace | if the syntax surface drifts mid-slice, freeze a pinned snapshot and reopen explicitly |
| Q2 — discrete denotation | denotational semantics of the discrete family over `FiniteLaw`/`FiniteKernel`/`FiniteHMM`; alignment statement 1 | one proved isomorphism-class statement on a fixed exemplar | if exemplar conventions require semantic interpretation (not syntax), the ambiguity is filed to the GNN side instead of being resolved silently |
| Q3 — continuous denotation | alignment statement 3 over `LinearGaussianParameters` | one proved statement on the continuous exemplar family | same ambiguity rule |
| Q4 — renderer and execution statements | statements 5 per render target; execution semantics composed from kernel machinery (`kernelPower`, `transition_add`, semigroup laws) | statements accepted in a slice; proofs scheduled or explicitly deferred | a target with no statable semantics gets a documented no-go, not a fake statement |

## Packaging and lifecycle

- Lean work follows the standard lifecycle: a bounded spec under `specs/`
  precedes any code; modules project into `lean/FepSketches/` through
  `scripts/_maint_build_formal_modules.py` per `src/fep_lean/formal/manifest.py`;
  `composed.lean` remains the import-only aggregate.
- No second research registry is introduced; this directory owns prospective
  goals only, and implementation status belongs to the opened spec while
  active and to its archived acceptance record after exit.
- GNN-side companions to each slice (exemplar curation, syntax-surface
  freezes, vocabulary questions) are tracked in the mirror folder
  `GeneralizedNotationNotation/docs/other/fep_lean/`.

## Open problems

- **Parser versions and leniency.** GNN documents carry
  `GNNVersionAndFlags` (`GNN v1`, `v1.0`, `v1.1`) with evolving optional
  sections; each slice pins exactly one syntax version.
- **Float dimensions.** `type=float` state-space blocks denote approximate
  numerics; the formal object should carry the rounding boundary explicitly
  rather than pretend exactness.
- **Parameterization conformance.** `InitialParameterization` conformance to
  declared dimensions is checkable; conformance to the Lean-defined law
  (up to rounding) is a stronger statement needing its own slice.
- **Families beyond the first two.** Dirichlet pseudo-count families,
  per-level/per-agent hierarchical variants, and multi-agent extensions are
  out of scope until the two base families are formalized.
