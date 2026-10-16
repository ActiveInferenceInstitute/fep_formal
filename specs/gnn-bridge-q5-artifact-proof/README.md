# Q5 — concrete PyMDP artifact proof

Status: **historical native proof and Python/coverage observations**.
Evidence date: 2026-09-04. The W2 source re-pin makes the retained native and
delivery observations historical; a fresh Q7 receipt does not refresh Q5.
See the [delivery report](REPORT.md) for dated reported hashes, actual retained
file hashes and the separate current-currency requirement.

Q5 connects the five literal tables in one retained, canonically rendered
PyMDP runner to the accepted Q2 Boolean denotation and Q4 matrix statement.
A second, handcrafted asymmetric fixture exercises the same static proof
construction. The [GNN bridge contract](../../docs/design/gnn-bridge/bridge-contract.md)
continues to separate source custody, rendering, static extraction, native
proof, numerical comparisons, and runtime execution.

## What the proof establishes

For the retained symmetric runner, the extracted `A_data`, `B_data`,
`C_data`, `D_data`, and `E_data` tables equal the independently authored
`FEP.GnnDenotation.symBoolPayload`. Their entries equal the corresponding
carrier masses of its denotation. The likelihood entries also recover the
original `symmetricBoolModel trueBiasedPolicyPrior` through the accepted
`symBoolDoc_denotation` theorem.

The Q4 `Statement5Pymdp` theorem is an implication from table faithfulness
to the matrix statement. Q5 separately proves that faithfulness and applies
the implication in `symArtifact_carrierMasses`; the implication alone is
not evidence that an arbitrary runner has correct tables.

The asymmetric proof establishes equality to its separately authored,
fixed `asymExpectedPayload`, together with named differences from the
symmetric payload. These two concrete results do not prove correctness of
the extractor, renderer, arbitrary models, or a Python-to-Lean compiler.
Neither retained runner is imported or executed by Q5 verification. There
is no C/EFE equivalence, runtime behavior, physical, or H3 claim.

## Artifacts and evidence

| Artifact | Role |
| --- | --- |
| [Symmetric runner](fixtures/pymdp_symmetric_runner.py) | Actual canonical GNN render output at its retained source epoch |
| [Asymmetric runner](fixtures/pymdp_asymmetric_runner.py) | Handcrafted normalized dyadic control, not a second live-render result |
| [Render provenance](render_provenance.json) | Actual renderer command/output, input/output digests, and unchanged before/after owner bindings |
| [Generated manifest](generated/artifact_proof_manifest.json) | Extracted rational table summary and fixture/extractor/probe digests |
| [Symmetric probe](generated/probe_symmetric.lean) | Four concrete theorems on the Boolean carrier |
| [Asymmetric probe](generated/probe_asymmetric.lean) | Two concrete theorems for the control fixture |
| [Historical native receipt](native_receipt.json) | Retained native transcripts, six axiom reports, historical source bindings, and compiled-import hashes |

The retained fixtures support sibling-independent static tests. Checking
current renderer/source custody additionally requires the explicitly
selected GNN checkout and the current
[source pin](../gnn-bridge-w2-source-custody/source-pin.json).
That check must validate the exact selected receipt against the selected source
pair; retained success flags cannot establish currency after re-pinning.

## Frozen layout and restricted extraction

The extractor reads Python AST without executing the runner. The contract
fixes `Bool` order to `false, true`, `A[outcome][state]`, and
`B[next][previous][policy]`. `C`, `D`, and `E` index outcomes, states, and
policies respectively. The Boolean shapes are explicitly supplied/defaulted
as `2×2`, `2×2×2`, and length-two vectors; they are not inferred from runtime
`ModelParameters` behavior.

The accepted syntax has exactly one top-level, non-async `main` containing
one straight-line literal assignment to each table name. Numeric leaves
must be finite, non-Boolean constants whose exact decimal rational is dyadic.
Nested lists/tuples must be rectangular and match the declared shapes.
Exact arithmetic checks nonnegativity, each A outcome-column sum, each B
next-state-column sum, and each C/D/E vector sum against one. C normalization
is this finite model's convention, not a claim about arbitrary PyMDP utility
vectors.

Tests reject duplicate/reassigned tables, tracked-name shadowing, conditional
or nested assignments, method mutation, calls or computed expressions,
non-dyadic/nonfinite literals, and malformed shapes. This is a restricted
static acceptance contract, not complete Python dataflow analysis.

`generate_probe.py` emits the extracted tables as literal Boolean functions.
The symmetric Lean reference is the accepted Q2 payload; the asymmetric Lean
reference is a static, independently authored record in the generation
source. The manifest's `expected_payload` field is an extracted table
summary, **not** that independent proof oracle.

## Axis-sensitive control

The asymmetric fixture uses the following B policy slices, with rows for
next state and columns for previous state:

```text
B(false) = [[1/4, 3/4], [3/4, 1/4]]
B(true)  = [[1/2, 1/8], [1/2, 7/8]]
```

Each of the five nonidentity permutations of the three B axes changes at
least one entry. The tests enumerate all five. Swapping previous-state and
policy axes preserves normalization, so a separate native negative test
requires the generated proof against the unchanged independent payload to
fail. That native rejection test passed; exact results are recorded in the delivery report.

## Reproduction and retained checks

Run from the FEP_Formal repository root. Set `GNN_ROOT` to the actual GNN
checkout. An existing current source pin and finite input are prerequisites;
these commands do not silently re-pin or reinterpret stale inputs.

```bash
GNN_ROOT=/absolute/path/to/GeneralizedNotationNotation

uv run python specs/gnn-bridge-q5-artifact-proof/refresh_render.py \
  --gnn-root "$GNN_ROOT"
uv run python specs/gnn-bridge-q5-artifact-proof/generate_probe.py
uv run python specs/gnn-bridge-q5-artifact-proof/verify_native.py \
  --compile --gnn-root "$GNN_ROOT" \
  --receipt output/bridge/q5-native-candidate.json
```

`refresh_render.py` explicitly invokes the current GNN extractor
`extract_pomdp_from_file(strict_validation=True)`, then
`POMDPRenderProcessor._pomdp_to_gnn_spec`, then `render_gnn_spec`, in an
offline/no-sync GNN `uv` subprocess. It retains the emitted symmetric runner
and source provenance. This executes the renderer, not the generated runner.
A fresh render can change timestamp-bearing output bytes, invalidating old
probe and native receipts; regenerate and compile in that order.

`verify_native.py --compile` first builds the two imported Q2/Q4 targets,
then compiles each exact probe with six intended `#print axioms` requests
across the pair. Process-group-safe native calls are serialized. Successful
exit, no warnings or `sorry`, and complete parsed reports using only
`propext`, `Classical.choice`, and `Quot.sound` are required.

Use a fresh candidate path for each capture; preserve the historical
`native_receipt.json`. Check the same candidate with the same explicitly named
GNN root. For subsequent read-only checks:

```bash
uv run python specs/gnn-bridge-q5-artifact-proof/generate_probe.py --check
uv run python specs/gnn-bridge-q5-artifact-proof/verify_native.py \
  --check --gnn-root "$GNN_ROOT" \
  --receipt output/bridge/q5-native-candidate.json
```

The native CLI defaults to `--check` when neither mode is supplied. It
reparses retained transcripts, recomputes verdicts, and checks current source,
render provenance, fixtures, expected-payload manifest, generator, extractor,
probes, toolchain binaries, and recursive local compiled imports. It neither
launches Lean nor writes artifacts. The exact generator buffer is checked
against the retained digest before that same buffer is executed for in-memory
regeneration, including both validation snapshots. A stale numerical receipt
cannot supply missing native or renderer evidence. Receipts remain local
execution records, not cryptographically signed attestations.

## Tests and related audit

[Static artifact tests](../../tests/test_gnn_artifact_proof.py) cover the
restricted extractor, exact generation, all B-axis permutations, and native
positive/negative probes. [Receipt tests](../../tests/test_gnn_artifact_receipt.py)
cover tampering, stale owners, missing native evidence, read-only behavior,
output collisions, and generator-read races. Receipt tests use synthetic
transcripts and are not themselves native execution evidence.

The separate [H2.7 audit](../done/horizon-2-smooth-stochastic/readiness/07-terminal-audit-20260904.md)
records its terminal/custody work and scientific limitations. Q5 does not
accept the wider H2 horizon. The maintained [root handoff](../../HANDOFF.md)
owns current H2/H3 acceptance and remaining scientific gates.
