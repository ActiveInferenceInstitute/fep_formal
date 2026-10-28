# Q6 — concrete Julia embedded-input proof

Status: historical native and delivery observations, dated 2026-09-04.
Both positive probes and the normalized wrong-axis rejection passed at their
recorded epoch. The [retained native receipt](native_receipt.json) remains
unchanged and historical after the W2 re-pin; new Q7 evidence does not refresh
Q6. See [the delivery report](REPORT.md) for dated and actual retained hashes.

The accepted artifact family is the canonical single-agent Boolean Julia
runner emitted by the GNN `activeinference_jl` render route. The runner embeds
one base64-encoded JSON document. Q6 reads that document without executing
Julia and proves the five embedded input tables agree with an independently
authored Lean payload. The symmetric oracle is Q2's `symBoolPayload`; the
asymmetric oracle is a separately authored fixed Lean record.

This is embedded-input equality. The actual runner applies `softmax(C)` and
does not use E in its action selector. Q4's `Statement5ActiveInferenceJl` is
an abstract conditional matrix statement; instantiating it with embedded
tables does not identify consumed runtime C with a preference probability,
establish EFE equivalence, or prove ActiveInference.jl agent behavior. No
runner execution, general renderer/compiler correctness, physical, or H3
claim is made.

## Acceptance contract

- Retain a symmetric runner produced through strict GNN extraction,
  `POMDPRenderProcessor._pomdp_to_gnn_spec`, and public `render_gnn_spec`.
- Retain a second runner produced by the same public renderer from a separately
  authored asymmetric canonical input. Distinguish this input construction
  from the symmetric GNN-file extraction route in provenance.
- Freeze the entire approved symmetric runner skeleton with exactly one
  `@@GNN_SPEC_JSON_B64@@` slot. Both artifacts must match it byte for byte
  outside that one quoted payload; arbitrary Julia syntax is not accepted.
- Decode canonical base64 and strict UTF-8 JSON. Reject duplicate keys,
  nonfinite/Boolean/nonnumeric leaves, non-dyadic or excessively large values,
  missing E, malformed Boolean dimensions, alternative B order, unknown table
  keys, ragged arrays, and non-normalized input tables. The finite C-vector
  normalization is this selected input contract, not a Julia utility convention.
- Freeze `false,true` as JSON indices `0,1` and Julia indices `1,2`;
  `A[outcome][state]`, `B[next][previous][action]`, `C[outcome]`, `D[state]`, `E[action]`.
- Emit independently auditable raw input tables and exact native claims.
  The asymmetric oracle must not be constructed from extracted values.
- Reject all five nonidentity B-axis permutations against that oracle,
  including the normalization-preserving previous/action exchange.
- Run native positive probes, standard-axiom census, and a normalized negative
  proof before acceptance. Compilation is serialized by the parent workflow.
- Bind actual renderer input/output/owner bytes separately from generated probe
  custody and native transcripts. Draft provenance records are not acceptance.

## Independent asymmetric oracle

```text
A = [[1/4,1/2],[3/4,1/2]]
B(false) = [[1/4,3/4],[3/4,1/4]]
B(true)  = [[1/2,1/8],[1/2,7/8]]
C = [1/4,3/4]; D = [5/8,3/8]; E = [3/8,5/8]
```

All vectors distinguish index reversal; C/D/E differ from each other.

## Ownership and verification

`gnn_julia_artifact_proof.py` owns restricted extraction, exact input-table
validation, probe generation, and fixed backend metadata. It reuses Q5's
immutable table representation, not Q5's Python syntax or runtime claims.
`generate_probe.py --check` compares retained artifacts with current source
without Julia, Lean, a renderer, or writes. After the package identity cutover,
the retained historical source hashes are intentionally stale for this check.
Generate a current-source projection with `--output-root PATH`, then check that
same fresh directory with `--check --output-root PATH`. Generation refuses an
existing output directory; it never renews historical manifests in place. Parent-owned shared native receipt tooling must
bind this extractor, generator, skeleton, fixtures, oracles, and recursive
formal imports; Q6 does not clone or reconfigure the Q5 verifier.

Focused tests: `tests/test_gnn_julia_artifact_proof.py`. Native acceptance
requires the independently validated receipt even when every Python test passes.

Draft verification on 2026-09-04: 51 Python tests passed, with three
`serial_lean` tests deliberately deselected. Ruff and separate strict mypy
checks of the extractor and generator passed. Both fixtures were actually
rendered into temporary directories; `draft_render_provenance.json` records
the two distinct input routes and unchanged hashes of five directly involved
GNN owners. This limited draft record is not the parent's complete sealed
source-custody receipt. No Julia runner or Lean/Lake process was executed.

The three native regression tests compile each positive probe with its complete
axiom roster, then require the normalized previous/action-axis mutation to
fail against the unchanged asymmetric oracle. Run them serially against the shared native workspace.

For a separately coordinated current recapture, refresh the exact selected
render/probe owners first, then use a fresh candidate path and explicitly name
the same GNN root for capture and validation:

```bash
GNN_ROOT=/absolute/path/to/GeneralizedNotationNotation
uv run python specs/gnn-bridge-q6-activeinference-artifact/verify_native.py \
  --compile --gnn-root "$GNN_ROOT" --receipt output/bridge/q6-native-candidate.json
uv run python specs/gnn-bridge-q6-activeinference-artifact/verify_native.py \
  --check --gnn-root "$GNN_ROOT" --receipt output/bridge/q6-native-candidate.json
```

Never overwrite the historical `native_receipt.json`. Its retained success
flags do not establish current source custody. Current H2/H3 gates belong to
the maintained [root handoff](../../HANDOFF.md).
