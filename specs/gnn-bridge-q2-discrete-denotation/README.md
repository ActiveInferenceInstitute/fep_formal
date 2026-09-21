# GNN bridge Q2 — discrete-family denotation over the finite carriers

Status: **complete; Q2 accepted; the denotation module
`gnn_denotation.lean` is registered, the exemplar isomorphism-class statement
is proved warning-free with no `sorry` and no new axioms, and the slice is
verified end-to-end; see [REPORT.md](REPORT.md) for the evidence record**.
Last updated: 2026-09-04.

This slice opens Direction 2 stage Q2 of the [GNN bridge
program](../../docs/design/gnn-bridge/README.md) under the [bridge
contract](../../docs/design/gnn-bridge/bridge-contract.md) (section 6 stage
S4, section 7 evidence firewall, section 9 no-go registry). Phase definition
and acceptance: [direction-2-gnn-to-lean.md](../../docs/design/gnn-bridge/direction-2-gnn-to-lean.md)
(Q2 row and alignment statement 1).

Q1 — the document AST and decidable well-formedness — is accepted under
[`specs/gnn-bridge-q1-syntax-ast/`](../gnn-bridge-q1-syntax-ast/README.md)
(module `src/fep_lean/formal/gnn_document.lean`, namespace `FEP.GnnDocument`).
This slice reuses that AST and its cross-section extractors (`stateSpaceDecls`,
`parameterizationEntries`, `ontologyBindings`, `WellFormed`) without modifying
them.

## What this slice formalizes

A **denotational semantics** of the discrete POMDP family: a well-formed
discrete-family GNN document, read under the frozen conventions below, denotes
an instance of the `active_inference.lean` `GenerativeModel`. This realizes
[alignment statement 1](../../docs/design/gnn-bridge/direction-2-gnn-to-lean.md):

> `A` ↔ likelihood, `B` ↔ policy-indexed transition ordered
> `(next_state, previous_state, action)`, `C` ↔ preferences, `D` ↔ initial
> prior, `E` ↔ habit prior.

The five matrix variables are bound to `GenerativeModel` fields by the frozen
field convention, the declared dimensions are checked against the carrier
cardinalities, the `InitialParameterization` entries are checked present, and
the `ActInfOntologyAnnotation` field bindings are checked against the frozen
ontology convention. The numeric payload supplies the mass functions; the
denotation assembles them into `FiniteLaw` / `FiniteKernel` carriers and thence
the `GenerativeModel`.

## Frozen Q2 conventions (the document cannot pin these down)

These are the conventions the GNN document's syntax cannot determine; they are
fixed once here and named, not silently resolved. Each is grounded in the
bridge contract's model-kind table (section 3) and the P1 exemplar's own
parameterization comments.

1. **Field binding (A/B/C/D/E → GenerativeModel field).** The bridge contract
   fixes the discrete-family shape and `B` ordering. The field assignment is:
   `A` → `likelihood`, `B` → `transition`, `C` → `preferences`,
   `D` → `initialState`, `E` → `policyPrior`. This is read off the document's
   `ActInfOntologyAnnotation` bindings (`A=LikelihoodMatrix`,
   `B=TransitionMatrix`, `C=Preferences`, `D=PriorOverHiddenStates`, `E=Habit`)
   and the contract; conformance requires each of those five bindings present.
2. **`B` dim order.** `B` payload slots are indexed
   `(next_state, previous_state, action)` exactly as the contract's model-kind
   table states. The carrier `transition : Policy → FiniteKernel State State`
   has `mass prev next`, so the denotation transposes the first two payload
   indices: `transition policy prev next = payload[next, prev, policy]`.
3. **`A` layout (pymdp convention, per P1 exemplar).** The `A` payload is
   `A[observation_outcomes, hidden_states]` — rows are outcomes, columns are
   hidden states — matching the P1 exemplar's parameterization comments
   ("Rows are observations, columns are hidden states"). The carrier
   `likelihood : FiniteKernel State Outcome` has `mass state outcome`, so the
   denotation transposes: `likelihood state outcome = payload[outcome, state]`.
   The exemplar is symmetric, so this convention is numerically inert there;
   it is recorded here because it is a genuine choice the contract makes.
4. **Index enumeration (payload slot ↔ carrier element).** Payload slots are
   positions `0, 1, …`; the carrier elements are the finite type's canonical
   enumeration. For the fixed exemplar the carriers are `Bool` and the P1
   parameterization comments fix the enumeration `Bool: false, true` (slot 0
   ↔ `false`, slot 1 ↔ `true`). The exemplar payload record is typed directly
   over the carrier `Bool`, so this enumeration is baked into the exemplar's
   payload tables; a different enumeration would yield the transported model.
   This is the isomorphism-class caveat of the acceptance statement.
5. **Numeric payload domain.** The semantic domain of the payload masses is
   `ℝ`. Per the P1 rounding policy (exact Lean rationals emitted as shortest
   exact terminating decimal strings), the exemplar payload carries exact
   rational values (`1/2`, `1/4`, `3/4`); non-terminating expansions are a
   no-go, never rounded. Conformance requires nonnegativity and the
   normalization the carrier needs (`A` column-stochastic over outcomes per
   state; `B` row-stochastic over next-states per `(policy, previous)`; `C`,
   `D`, `E` unit-sum vectors).

## Payload-string → typed-table interpretation (the Q1 deferral, here applied)

Q1 deferred `InitialParameterization` value semantics and brace-block shape to
a later slice. This slice does **not** implement a payload-string parser. The
transcription step from the document's verbatim brace-block payload strings
(e.g. `E={(0.25, 0.75)}`) to the typed `ℝ` tables that the denotation consumes
is the P1 rounding policy in action: each decimal literal is read as its exact
rational value and placed at its payload position under the index enumeration
above. For this slice that interpretation is **applied** — the exemplar's typed
payload tables (`symBoolPayload`) carry the exact transcribed values — and the
interpretation boundary is named here, in the slice README, as a finding for
the GNN side. A full payload-string parser (brace-block shape, nested-tensor
flattening, decimal-to-`ℝ`) is an explicit follow-up; it is out of scope here
and is not needed to prove the exemplar statement.

## Fixed exemplar

The fixed exemplar is the accepted P1 artifact
[`specs/gnn-bridge-p1-finite-spike/gnn-input/FepLeanSymmetricBool.md`](../gnn-bridge-p1-finite-spike/gnn-input/FepLeanSymmetricBool.md)
(read-only): the deterministic projection of
`FEP.ActiveInference.symmetricBoolModel trueBiasedPolicyPrior`
(`lean/FepSketches/active_inference.lean:743-749`). It is transcribed into a
`GnnDocument` value `symBoolDoc` in the module, exercising the full section
inventory (all thirteen section kinds in canonical order), the `F[π]` / `G[π]`
forward-reference dimensions, the nine plain connection edges, the five
parameterization entries, the eleven ontology bindings, and the four model
parameters.

The exemplar's carriers are all `Bool`: `State = Bool`, `Outcome = Bool`,
`Policy = Bool` (two hidden states, two observations, two policies). Its exact
literals are `1/2` everywhere for `A`, `B`, `C`, `D` and `1/4`/`3/4` for `E`
(true-biased policy prior).

## Acceptance

- [x] Bounded spec slice opened before any Lean code landed.
- [x] Formal module `src/fep_lean/formal/gnn_denotation.lean` (namespace
  `FEP.GnnDenotation`) defines the discrete-family denotation over the
  existing carriers (`FiniteLaw`, `FiniteKernel`, `GenerativeModel` from
  `active_inference.lean`); registered in `src/fep_lean/formal/manifest.py`.
- [x] The P1 exemplar's document is transcribed (`symBoolDoc`) and its
  well-formedness is proved (`WellFormed symBoolDoc`, by `decide`).
- [x] The exemplar denotation isomorphism-class statement is proved:
  `denoteDiscrete symBoolDoc symBoolPayload symBoolConforms =
    symmetricBoolModel trueBiasedPolicyPrior` — up to the exact literals,
  warning-free, no `sorry`, no new axioms.
- [x] A downstream corollary connects the denoted model to the carrier's
  derived quantities (`predictedState`, `predictedOutcome`, `FullSupport`)
  via the existing `active_inference.lean` theorems, demonstrating the
  denotation drops into the carrier's theorem environment.
- [x] `cd lean && lake build FepSketches` — zero errors, zero warnings.
- [x] `uv run python scripts/_maint_build_formal_modules.py --check` and
  `uv run python scripts/_maint_build_fep_all_lean.py --check` green after
  registration.
- [x] Gate parity: `uv run python docs/check_links.py --strict --include-root`
  and `uv run python docs/md_hygiene.py --strict`.

## Mathlib dependency

The denotation module imports the finite carriers (`FepSketches.active_inference`
and, transitively, `FepSketches.finite_probability`) and `Mathlib` for the
`Fintype.card Bool` reduction and `Finset` sum lemmas used in the exemplar
proof. `Init`-only is impossible here: the carriers themselves are
Mathlib-based (`finite_probability.lean` opens with `import Mathlib`). This is
the genuine, recorded Mathlib requirement; the Q1 AST module stays `Init`-only
because it carries no semantics.

## No-go and risk register

| Trigger | Disposition in this slice |
| --- | --- |
| Exemplar conventions require semantic interpretation beyond syntax | The five conventions above are named and frozen in this README, not resolved silently; the payload-string → typed-table step is applied (not parsed) and recorded as a finding for the GNN side. |
| `InitialParameterization` brace-block shape and full decimal parser | Deferred (Q1 deferral carried forward); out of scope for the exemplar statement. |
| Non-terminating-decimal payloads | No-go per the P1 rounding policy; the exemplar's payloads are all exact terminating decimals. |
| `F[π]` / `G[π]` reference-dimension numeric reading | Q1 deferral; the matrix variables `A`–`E` all use literal dimensions in the exemplar, so the denotation requires literal dimensions for the five fields and records reference dimensions on the readout variables `F`/`G` as out of scope for this slice. |
| A different index enumeration than `Bool: false, true` | Would yield the transported model; recorded as the isomorphism-class caveat. The exemplar fixes the canonical enumeration. |
| Continuous (linear-Gaussian) family | Out of scope here; Q3 opens a separate slice (`specs/gnn-bridge-q3-continuous-denotation/`) only if Q2 lands cleanly. |
| Mathlib/API blocker | None encountered; recorded Mathlib requirement (see above). |

## Boundaries

- The formal module is additive: one new foundation resource, no edits to the
  accepted Q1 AST module or to any existing Lean carrier, no catalogue topics,
  no relation or atlas claims, no `fep-NNN` identifier.
- `composed.lean` stays the import-only aggregate over composition leaves; a
  foundation module is not imported there, and `fep_all.lean` is
  catalogue-body-driven and does not list this module.
- Cross-repo references are inline code paths, never markdown links
  (bridge contract decision 8).

## Mirror-folder finding for the GNN side

The interpretation step from the P1 exemplar's verbatim `InitialParameterization`
brace-block strings to typed `ℝ` tables is the P1 rounding policy applied by
hand in this slice (no parser). The GNN-side mirror folder
(`GeneralizedNotationNotation/doc/other/fep_lean/`) is the right place to
record that the discrete-family payload shape `( (…), (…) )` for a matrix and
`(…)` for a vector is the convention the bridge relies on, so a future
payload-string parser has a frozen target.
