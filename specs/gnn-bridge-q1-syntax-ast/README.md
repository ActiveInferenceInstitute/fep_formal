# GNN bridge Q1 — syntax AST and decidable well-formedness

Status: **complete; Q1 accepted; the Q1 syntax surface is frozen below, the
formal module `gnn_document.lean` is registered, and the slice is verified
end-to-end; see [REPORT.md](REPORT.md) for the evidence record**. Last
updated: 2026-09-03.

This slice opens Direction 2 stage Q1 of the [GNN bridge
program](../../docs/design/gnn-bridge/README.md) under the [bridge
contract](../../docs/design/gnn-bridge/bridge-contract.md) (section 6 stages,
section 7 evidence firewall, section 9 no-go registry). Phase definition and
acceptance: [direction-2-gnn-to-lean.md](../../docs/design/gnn-bridge/direction-2-gnn-to-lean.md).

## Frozen Q1 syntax surface

Normative base: `GeneralizedNotationNotation/doc/gnn/gnn_syntax.md` (GNN v1.1
syntax specification), evidenced by the four canonical exemplars
`GeneralizedNotationNotation/input/gnn_files/discrete/actinf_pomdp_agent.md`,
`input/gnn_files/discrete/simple_mdp.md`,
`input/gnn_files/continuous/continuous_navigation.md`, and
`input/gnn_files/continuous/predictive_coding_agent.md`. The freeze is one
surface, valid across `GNN v1`, `v1.0`, and `v1.1` version tokens:

1. **Sections.** Required: `GNNSection`, `GNNVersionAndFlags`, `ModelName`,
   `StateSpaceBlock`, `Connections`. Optional (each observed in the four
   exemplars): `ModelAnnotation`, `InitialParameterization`, `Equations`,
   `Time`, `ActInfOntologyAnnotation`, `ModelParameters`, `Footer`,
   `Signature`. Freeze decision: each section appears **at most once**, and
   the document order is the canonical exemplar order listed above (required
   kinds first, then optional kinds in syntax-doc order). Every optional
   section is carried as a **typed wrapper**; free-text wrappers
   (`ModelName` prose, `ModelAnnotation`, `Equations`, `Footer`, `Signature`)
   carry no constraint, matching direction-2's rule that prose sections stay
   outside the formal object language.
2. **State-space declarations.** `NAME[dims..., key=value...]`; names are
   nonempty strings over alphanumeric plus `_`, `π`, `'` (case-sensitive);
   dimensions are positive integer literals or name references (forward
   references allowed — `F[π,type=float]` precedes `π`'s declaration in
   `actinf_pomdp_agent.md`); `type=<type>` is `float` (default), `int`, or
   `bool`; v1.1 `default=<value>` is stored verbatim and not validated
   (per syntax doc §2).
3. **Connections.** `A>B` (directed), `A-B` (undirected), optional
   `:label` annotation with label characters alphanumeric plus `_`
   (syntax doc §3).
4. **Decidable well-formedness (this slice's predicate set).** Required
   section presence; canonical order with at-most-once per kind; section
   identifier is a valid name; declaration names valid and duplicate-free
   (GNN-E004); dimension literals positive; dimension references resolve to a
   declared variable or a `ModelParameters` key; connection endpoints are
   declared variables (GNN-E003, strict here); labels and parameterization /
   ontology / parameter keys are valid names; parameterization variables are
   declared (GNN-W003, strict here); ontology binding variables are declared.
5. **Explicitly deferred (Q2+ boundaries).** Numeric dimension /
   `ModelParameters`-value agreement (positional mapping is convention, not
   syntax); `InitialParameterization` value semantics and brace-block shape;
   version-gated feature enforcement (whether `default=` and labels require a
   `v1.1` token); ontology **term** vocabulary validation (parameterized by
   the frozen GNN vocabulary); model-kind detection; all dynamic semantics.
   The evidence firewall holds: compiling the AST proves nothing about GNN
   runtime behavior.

## Acceptance checklist

- [x] Syntax surface frozen (this file, section above).
- [x] Bounded spec slice opened before any Lean code landed.
- [x] Formal module `src/fep_lean/formal/gnn_document.lean` (namespace
  `FEP.GnnDocument`) defines the sectioned-document AST, state-space block
  declarations (name, dims, `type`, `default`), connections (directed /
  undirected / `:label`), and decidable well-formedness for the frozen
  surface; registered in `src/fep_lean/formal/manifest.py`.
- [x] Exemplar smoke: excerpts of all four canonical exemplars decide
  well-formed (`decide`-true), and deliberately malformed variants (missing
  required section, out-of-order sections, undeclared connection endpoint,
  bad annotation label, duplicate declaration, nonpositive dimension,
  unresolvable dimension reference, invalid section identifier, undeclared
  parameterization variable, undeclared ontology variable) decide false.
- [x] `cd lean && lake build FepSketches` — zero errors, zero warnings, no
  `sorry`, no new axioms.
- [x] `uv run python scripts/_maint_build_formal_modules.py --check` and
  `uv run python scripts/_maint_build_fep_all_lean.py --check` green after
  the manifest registration (projection regenerated, never hand-edited).
- [ ] Full `input/gnn_files/` corpus transcription and decision — explicit
  follow-up slice, out of scope here.

## No-go and risk register

| Trigger | Disposition in this slice |
| --- | --- |
| Syntax surface drift in `doc/gnn/gnn_syntax.md` | Surface frozen above per contract section 9; a drift requires an explicit re-freeze here before any AST extension. |
| Version-gated features (`default=`, `:label` under `GNN v1` vs `v1.1`) | Not frozen by the syntax doc; recorded as a deferred decision, not resolved silently. |
| Positional dimension-to-parameter-value consistency | Requires A/B/C/D- and F/H/Q/R-convention knowledge (semantic, not syntactic); deferred to the state-space-typing slice. |
| `F[π]`-style dimension reference resolution semantics | Name resolvability is decidable and frozen; the numeric reading of a variable reference is deferred. |
| Mathlib/API blocker | None encountered; the module compiles on Lean core alone (no Mathlib imports), which also keeps it self-contained. |

## Boundaries

- The formal module is additive: one new foundation resource, no edits to
  existing Lean carriers, no catalogue topics, no relation or atlas claims.
- `composed.lean` stays the import-only aggregate over composition leaves;
  a foundation module is not imported there.
- Cross-repo references are inline code paths, never markdown links
  (bridge contract decision 8).
