# GNN bridge program

This document defines the design and operation of the bridge with
`GeneralizedNotationNotation` (GNN). The package command surface is maintained
in [`src/fep_formal/bridge/cli.py`](../../../src/fep_formal/bridge/cli.py); owner
selection, emission, and receipt checks are maintained in
[`src/fep_formal/bridge/operations.py`](../../../src/fep_formal/bridge/operations.py).
The [bridge contract](bridge-contract.md) owns the shared scientific and custody
boundaries. Current open acceptance work belongs in
[`TODO.md`](../../../TODO.md), not a completed-stage checklist.

FEP_Formal is this repository's current project name; `fep_formal` remains its
Python namespace, serialized custody key and historical GNN mirror identity.
The mirrored version-0.6 contract retains its 2026-09-06 source epoch and
155-topic baseline. Use the [current source owners](../../../AGENTS.md#source-of-truth)
for the live catalog; changing that shared contract requires coordinated
review and publication on both sides.

The [design lifecycle](../README.md) governs bounded implementation slices. The
active catalog program lives in
[FEP research horizons](../fep-research-program/README.md); this bridge adds no
topics, formalism relations, atlas edges, or reserved `fep-NNN` identifiers.
Implemented artifacts include Q1–Q4 foundation modules, Q5–Q7 slice-local proof
probes, and the package bridge operations. Their existence is not a claim that
their retained receipts are current for a changed source pair.

## Why this program exists

GNN is a text-based notation for Active Inference generative models. Its
`docs/gnn/gnn_syntax.md` and `src/gnn/pipeline/step_registry.py` define its
syntax and processing surface. FEP_Formal states and proves invariants about
the same objects in Lean 4. The comparative manuscript chapter names the gap:

> Executable Active-Inference tools and notations such as pymdp or GNN
> occupy a different layer. They specify and run model instances; Lean
> states and proves invariants. A useful bridge would translate a typed
> model representation into a common Lean probability/kernel structure,
> generate proof obligations for normalization and conditional independence,
> and retain a provenance link back to executable parameters.

(citation markers removed; `manuscript/05d_comparative_analysis.md:37`.) The
same chapter adds that a numerical implementation can be tested on data while
a theorem is checked for deductive correctness, and that "neither subsumes
the other" (`manuscript/05d_comparative_analysis.md:39`). This program keeps
both layers and makes their agreement checkable instead of asserted.

## Parties and authority

| Party | Role in the bridge |
| --- | --- |
| FEP_Formal | Lean 4 semantic authority: laws, kernels, blankets, free-energy and decision quantities, and their proofs; the pinned workspace is the compilation authority |
| GNN | Notation and tooling authority: GNN document syntax, the pipeline step registry, render targets, and execution semantics |
| Interchange artifact | GNN document files carrying mandatory provenance back to the Lean source |

## North star

```text
named Lean generative-model definition
  -> deterministic projection (variables, index types, dependencies, parameters)
  -> GNN document with provenance
  -> GNN validate / ontology / render / execute (steps 3, 5, 10, 11, 12)
  -> execution artifacts (render and execution summaries)
  -> certificate: execution-derived quantities vs Lean-witnessed properties
```

and the reverse direction:

```text
GNN syntax and step inventory (docs/gnn/gnn_syntax.md; src/gnn/pipeline/step_registry.py)
  -> Lean AST and decidable well-formedness
  -> static and dynamic semantics
  -> denotations reusing FEP_Formal carriers (FiniteLaw, FiniteKernel, FiniteHMM, LinearGaussianParameters)
  -> FEP instantiation and renderer-preservation statements
```

Every arrow must be deterministic and name its evidence plane. An arrow that
requires judgment calls is a finding to resolve, not a pipeline stage.

## The two directions

- [Direction 1 — render and execute Lean-expressed generative models](direction-1-lean-to-gnn.md):
  from a Lean expression of a generative model to a GNN document the GNN
  toolchain renders and executes, with certificates back to Lean.
- [Direction 2 — formalize GNN steps and methods](direction-2-gnn-to-lean.md):
  from the frozen GNN syntax surface and step registry to Lean ASTs, decidable
  well-formedness, dynamic semantics, and alignment theorems on FEP_Formal
  carriers.
- [Bridge contract](bridge-contract.md): the shared, mirrored agreement both
  sides edit and honor.

## Model-kind alignment

The bridge aligns the two supported model kinds on each side:

| GNN model kind | FEP_Formal counterpart |
| --- | --- |
| Discrete POMDP family: `A` likelihood, `B` transition ordered `(next_state, previous_state, action)`, `C` preferences, `D` initial prior, optional `E` habit, `F[1]` variational-free-energy readout | finite carrier family: `lean/FepSketches/active_inference.lean` (`GenerativeModel`), `lean/FepSketches/finite_probability.lean` (`FiniteLaw`, `FiniteKernel`), `lean/FepSketches/temporal_inference.lean` (`FiniteHMM`) |
| Continuous linear-Gaussian family: `F/H/Q/R` with `prior_mean`/`prior_cov`, `x_t = F x_{t-1} + u_{t-1} + N(0,Q)`, `y_t = H x_t + N(0,R)` | smooth/stochastic carrier family: `lean/FepSketches/linear_gaussian_semigroup.lean`, `lean/FepSketches/scalar_gaussian_semigroup.lean`, `lean/FepSketches/continuous_time_markov.lean` |

Blanket structure and the ontology bindings `s=HiddenState`, `o=Observation`,
`π=PolicyVector`, `u=Action` correspond to
`lean/FepSketches/markov_blanket.lean` and `lean/FepSketches/native_blanket.lean`.

## Decisions fixed by this design

1. **One interchange artifact.** GNN document files only. Any typed
   intermediate projection stays private to the emitter.
2. **Provenance is mandatory.** Every emitted document records source
   repository, commit digest, Lean module and definition, and generator
   identity in a provenance section.
3. **Deterministic projection or nothing.** No heuristic or model-based
   extraction sits inside the emitter; judgment belongs to the mapping
   review, not the pipeline.
4. **Evidence planes stay distinct.** Lean native compilation, semantic
   review, numerical witnesses, and GNN pipeline execution remain separate
   evidence classes. A GNN run never promotes a Lean claim, and a Lean claim
   never substitutes for an executed artifact.
5. **Two model kinds only.** Discrete/categorical and continuous
   linear-Gaussian. Anything else is out of scope until the contract is
   reopened.
6. **Misfit is reported, not repaired.** Where a projected model exceeds a
   backend, the GNN `unsupported` render status applies; the bridge never
   distorts a model to force a fit.
7. **No catalog or relation claims.** This program adds no topics, no
   formalism relations, no atlas edges, and reserves no `fep-NNN`
   identifiers. Future rows arrive only through the existing novelty and
   semantic-review gates.
8. **Inline-code cross-references only.** Cross-repo paths are written as
   code, never as markdown links, because each repository validates links
   independently and relative links across repositories would break on
   either side's hosting.
9. **Mirrored contract.** The canonical contract lives in this directory;
   the mirror lives at
   `GeneralizedNotationNotation/docs/other/fep_lean/bridge-contract.md`.
   Contract edits land in both checkouts in the same working session.
10. **Spec-first lifecycle.** A bounded spec under `specs/` precedes any
    code: no projection module, emitter, or Lean AST lands without an opened
    slice, and the slice's acceptance record owns implementation status.

## Evidence and acceptance

Source pinning binds reviewed owner bytes on the explicitly selected pair. It
does not establish renderer correctness or refresh an older native or execution
receipt. Generated probes are static artifacts; native compilation establishes
their exact Lean statements under the pinned compiler and assumptions. Numerical
agreement and runner execution remain separate evidence planes.

The [Q5](../../../specs/gnn-bridge-q5-artifact-proof/README.md),
[Q6](../../../specs/gnn-bridge-q6-activeinference-artifact/README.md), and
[Q7](../../../specs/gnn-bridge-q7-continuous-ou-proof/README.md) contracts own
their distinct table, embedded-input, and scalar-OU coefficient claims. Select
the exact receipt and validate its source pair, manifest, toolchain, and outputs
before making a current claim. A fresh Q7 capture does not refresh Q5 or Q6.

The documented [continuous extraction boundary](../../../specs/gnn-bridge-p4-continuous-spike/REPORT.md)
and other dated slice reports remain scientific provenance. New model kinds,
extraction policies, or semantic claims require a bounded slice and explicit
review under the [design lifecycle](../README.md).

## Reading order

1. This README.
2. [Bridge contract](bridge-contract.md) — the shared rules both sides honor.
3. [Direction 1](direction-1-lean-to-gnn.md) and
   [Direction 2](direction-2-gnn-to-lean.md).
4. Background: [FEP background](../../fep-background.md) and
   [formal-kernel methods](../../formal-kernel-methods.md); on the GNN side,
   the mirror folder `GeneralizedNotationNotation/docs/other/fep_lean/`.

## Operating the bridge

[W2 source custody](../../../specs/gnn-bridge-w2-source-custody/README.md)
describes the package operations contract, whose current implementation is
defined by the CLI and operations sources linked above. For the re-pin order, see
[Re-pin runbook (canonical order)](#re-pin-runbook-canonical-order) below.

Run from the FEP_Formal checkout, replacing `GNN_PATH` with the explicit GNN root:

```bash
uv run fep-formal bridge pin --gnn-root GNN_PATH
uv run fep-formal bridge emit --gnn-root GNN_PATH --model finite
uv run fep-formal bridge emit --gnn-root GNN_PATH --model continuous
uv run fep-formal bridge status --gnn-root GNN_PATH
uv run fep-formal bridge emit --gnn-root GNN_PATH --model finite --check
uv run fep-formal bridge emit --gnn-root GNN_PATH --model continuous --check
uv run fep-formal bridge verify-document --gnn-root GNN_PATH --model MODEL \
  --document PATH --fail-on-warnings
```

Pin only after reviewing the settled owner changes — on BOTH sides of the
pair: any `src/fep_formal/**` owner-file change (this repo) invalidates an
existing seal exactly as a GNN owner-file change does, so land FEP_Formal
owner edits BEFORE starting the pin cycle, or the cycle must re-run after
them (a pin sealed pre-change fails `bridge status` with
"owner content changed" on the touched files). Pin and emit are explicit
writes; status and `--check` never emit. A provenance-only migration uses
`emit --refresh-digests`; content drift is rejected, not repaired. The pin
records actual owner bytes separately from descriptive commit references.

Use `bridge certify --gnn-root GNN_PATH --results PATH` to compare one
identified result without writing. Add `--receipt PATH` for explicit JSON and
Markdown output, then use `bridge verify-certificate --gnn-root GNN_PATH
--receipt PATH`. Agreement does not establish that the current source produced
an older execution artifact, and never establishes native Lean proof.

Concrete artifact acceptance follows the selected slice's render, probe,
native, and current-source checks. Use the applicable Q5, Q6, or Q7 contract
linked above, the explicitly named source pair, and its exact receipt. A fresh
render invalidates dependent probe and native receipts; reproduce and validate
that evidence in dependency order.

P3 `certify.py` is a read-only historical numerical comparator
unless `--output PATH` is supplied. Its retained reports are not silently
rewritten by status. Package regression tests run without an adjacent GNN
checkout; live bridge checks require the explicitly named pair.

## Re-pin runbook (canonical order)

Settle and review the relevant owner edits on both sides before re-pinning.
The CLI performs one pair-wide pin; `--model` selects emission and document
verification, not a separate source-owner seal.

1. Inspect the explicit pair with
   `uv run fep-formal bridge status --gnn-root GNN_PATH`. A drift result identifies
   changes requiring review; status never repairs them.
2. Seal the settled pair once:

   ```bash
   uv run fep-formal bridge pin --gnn-root GNN_PATH
   ```

3. Emit both reviewed model documents:

   ```bash
   uv run fep-formal bridge emit --gnn-root GNN_PATH --model finite
   uv run fep-formal bridge emit --gnn-root GNN_PATH --model continuous
   ```

   For a provenance-only change, `--refresh-digests` permits only Signature
   custody updates; it rejects content drift. `certify` consumes `--results`
   and optionally writes `--receipt`; `verify-certificate` checks `--receipt`.
   `verify-document` consumes `--document` and supports `--receipt` and
   `--fail-on-warnings`. Emission does not consume these inputs.
4. Check both emitted documents and the pair without writes:

   ```bash
   uv run fep-formal bridge emit --gnn-root GNN_PATH --model finite --check
   uv run fep-formal bridge emit --gnn-root GNN_PATH --model continuous --check
   uv run fep-formal bridge status --gnn-root GNN_PATH
   ```

5. Complete any required fresh artifact/native acceptance under its selected
   slice contract. Publish the reviewed source and evidence changes through the
   repository's normal process; owner hashes and descriptive commit references
   remain distinct.
6. Update `.github/fep-lean-pair.json` in the GNN repository only after the
   intended FEP_Formal publication SHA is settled. Its pair reference is the final
   GNN publication change; it does not promote old evidence.

Any GNN contract-owner edit (`pyproject.toml`, `uv.lock`, `src/gnn/main.py`,
the contract mirror, `docs/gnn/gnn_syntax.md`,
`src/gnn/pipeline/step_registry.py`) after sealing re-drifts the pair — land
all GNN content edits BEFORE re-pinning. The `src/gnn/**/*.py` implementation
tree is GNN-owned and is not pinned.

Mirror rule: `GeneralizedNotationNotation/docs/other/fep_lean/bridge-contract.md`
(the GNN side) and `docs/design/gnn-bridge/bridge-contract.md` on this side
must have matching normalized contract bodies. The status comparison splits
lines and excludes only rows starting with `| Canonical copy |` or
`| Mirror copy |`, which describe the two locations. Other body divergence
rejects; matching bodies do not waive either file's pinned source-byte checks.
