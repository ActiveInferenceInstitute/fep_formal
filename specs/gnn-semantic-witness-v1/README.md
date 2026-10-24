# Source-bound numerical semantic seams

This bounded extension independently reads the declared GNN E4 source subset
and replays finite forward filtering or Gaussian Kalman/Joseph updates. GNN's
references use complete path enumeration or joint Gaussian conditioning. The
two algorithms retain the same authored axes, first-observation prior, ordered
actions, observations, parameters, precision and conditioning horizons.

The existing `fep_lean.bridge.certificates` owner provides the replay. The
`fep-lean bridge audit-semantic --gnn-root PATH --results WITNESS.json` operation
accepts `gnn-semantic-witness-v2` receipts and optionally writes an audit using
`--receipt NEW.json`. It does not execute a generated program, compile Lean,
refresh historical source pins or establish universal translation equivalence.
Live source hashes and historical pair currency are reported separately.

The [slice-local laws](semantic_laws.lean) prove normalization and reconstruction
of finite real weights under a nonzero normalizer, nonnegativity under positive
mass, and scalar arbitrary-observation-slope Joseph/Schur and mean identities.
The scalar measurement step consumes its supplied prior directly. This is
algebraic Gaussian update evidence, with explicit positive-variance premises;
it is not a measure-level conditional-kernel theorem or a matrix algorithm proof.
General matrix Gaussian comparisons retain `structural_analogue` alignment to
the existing scalar OU formal kernel and list its unmatched assumptions.

Compile the positive laws and the false zero-normalizer/omitted-noise controls
serially in the pinned workspace, into a fresh output directory:

```bash
FEP_LEAN_VERIFY_TIMEOUT=60 .venv/bin/python specs/gnn-semantic-witness-v1/verify_native.py --output output/semantic-native-NEW
```

The compiler result and axiom output are retained separately from numerical
audits. Existing historical receipts and their original accepted claims remain
unchanged. The [repository contract](../../AGENTS.md) owns all wider acceptance.
