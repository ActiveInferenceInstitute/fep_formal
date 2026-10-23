# `fep_lean.verification`

Lean compilation and read-only capability validation for FEP_Formal's Python
package. Ordinary package import does not load the pipeline. Full-mode
credential inspection lazily reads Hermes configuration without making a
provider request. Validation never downloads or builds dependencies.

## Modules

| Module | Owner |
| --- | --- |
| `environment.py` | Mode-aware `run_validation_checks(project_root, mode=...)` |
| `lean_verifier.py` | `LeanVerifier` and structured `VerifyResult` |
| `formalism_audit.py` | declaration resolution, evidence axiom inspection, and typed audit receipt |
| `_toolchain.py` | Exact pinned executable resolution shared by validation and verification |
| `preflight.py` | Adapter behind `fep-lean preflight` |
| `numerical_witnesses.py` | Typed catalog and horizon diagnostic registry |
| `_horizon_numerical_witnesses.py` | Scalar terminal and Fin4 numerical calculations |
| `horizon_acceptance.py` | Source-bound H2 terminal and H3.G0 eligibility validation |
| `gnn_artifact_receipt.py` | Immutable backend contracts and retained native receipts |
| `gnn_artifact_proof.py` | Restricted PyMDP artifact extraction |
| `gnn_julia_artifact_proof.py` | Restricted Julia embedded-input extraction |
| `gnn_continuous_artifact_proof.py` | Scalar OU binary64 coefficient extraction |

## Public boundary

```python
from fep_lean.verification import (
    FormalismAuditResult,
    LeanVerifier,
    VerifyResult,
    run_formalism_audit,
    run_validation_checks,
)
```

`LeanVerifier.verify_sketch(topic_id, lean_code)` writes a bounded temporary
file under the Lake workspace, invokes `lake env lean`, parses errors and
warnings, records `sorry`, and removes the temporary source before returning.
`verify_batch(items)` is deliberately serial because every item shares the same
Lake build tree.

`check_mathlib_built()` returns `(ok, message)`, not compilation evidence. The
native CLI receipt is the full-catalog evidence boundary. Its invocation and
the independent axiom audit are owned by the
[root required-check inventory](../../../AGENTS.md#required-checks).

The native catalog receipt and formalism audit answer different questions.
The former compiles all exact topic bodies; the latter resolves every primary
and graph-evidence declaration through the topic aggregate and manifest-selected
foundation/composition imports, and
requires a parsed `#print axioms` result for each declaration. Process success
without complete axiom output, actual compiler/pin parity, an exact resolved
Mathlib revision, or live projection parity makes the audit incomplete.
Warnings, `sorryAx`, and any axiom outside the versioned trusted set
(`propext`, `Classical.choice`, `Quot.sound`) also fail the audit.

`run_validation_checks` returns named rows appropriate to `catalogue` or
`full` mode. Full mode adds Gauss, writable state, exact toolchain, workspace,
Mathlib, and credential requirements. Callers must inspect the returned status
and rows; the number of checks is not an API constant.

Dependency acquisition belongs to explicit `fep-lean setup`; `fep-lean preflight`
only inspects capabilities. The [Lean workspace guide](../../../lean/README.md)
explains the pins, setup and generated-resource ownership.

See the local [agent contract](AGENTS.md) and the package-level
[API reference](../../../docs/api.md).

## Scoped numerical diagnostics

`evaluate_numerical_witnesses(project_root, scope=None)` evaluates the shared
typed registry. `scope="catalogue"` selects the registered family witnesses;
`scope="horizon2"` selects the scalar terminal and Fin4 blanket diagnostics.
The atlas/dashboard and release witness receipt explicitly select catalog
scope. H2 acceptance consumes the two horizon witnesses through the same
`NumericalCheck` validation and declaration resolver.

The scalar diagnostic follows the selected stationary prior, posterior
variance one half, the local straight natural-gradient line and the finite
one-step diffusion-risk comparison. The Fin4 diagnostic computes its exact
rational covariance from the precision, conditional/perturbed covariance,
and spectral transition identities. These are explanatory numerical checks;
they are not native proofs or empirical FEP validation.

## Concrete artifact receipts

`gnn_artifact_receipt.ArtifactContract` fixes one backend's input, probe and
theorem roster. `ArtifactVerifier` checks content-bound generation and native
transcripts for that contract. Q5/Q6/Q7 slice entry points keep their source
and scientific boundaries explicit. Retained checks do not invoke Lean, a
renderer or a generated runner; `--compile` and render refresh are explicit
operations. Receipt schema 2 also binds the engine, full contract and actual
native command arguments. Extractors imported during retained regeneration
execute their checked source buffers without replacing cached application
modules. Source, toolchain and compiled imports are checked before and after.

The receipt assumes a trusted local checkout and toolchain. It records the
resolved compiler paths, binary hashes and pinned version; it does not
authenticate the host or compiler vendor. Checked local Python generators are
not an execution sandbox for arbitrary programs. Render transcripts retain
captured output, while the verifier independently checks the command, input
and artifact bindings.


Full-mode preflight always checks every required capability, including OpenGauss.
Use `run_preflight(root=...)` or `fep-lean preflight`; capability inspection
does not change the process environment. Workspace setup remains explicit.
