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


## E4-IG1: independent Gaussian product replay

The additive [slice-local adapter](audit_composition.py) accepts only
`gnn-semantic-witness-v3` for exactly two source-declared independent, passive,
stationary Gaussian agents. Each has a complete F/H/Q/R/prior block; the shared
horizon has at most eight times and at most four total state and observation
axes. Coupling, shared noise, controls, smoothing and unrecognized source
sections or parameters refuse admission. The released v2 package API and
`bridge audit-semantic` command remain unchanged.

The adapter independently reads the retained authored source without importing
GNN. It applies FEP's existing single-agent source admission to blocks rebuilt
from those raw assignments, then replays each agent using recursive
Kalman/Joseph updates. It checks GNN's joint-prefix reference, the complete native
child records and exact projections, parameters, seeds, timing, axes, precision,
artifact digests, comparison inventory and assumption boundaries. The first
observation consumes the declared prior. Within-agent covariance remains full;
cross-agent zero covariance is a consequence of the explicitly declared reference
product model, not a measured native cross-agent quantity.

With the accepted Python validator environment available, run the focused
controls and separately audit a retained GNN-produced witness into a fresh path:

```bash
uv run --frozen --no-sync pytest specs/gnn-semantic-witness-v1/test_composition.py -q -n 0 --no-cov
uv run --frozen --no-sync python specs/gnn-semantic-witness-v1/audit_composition.py \
  --witness /absolute/path/to/gaussian-product-semantic-witness-v3.json \
  --receipt /absolute/path/to/new-composition-audit.json
```

The tests use asymmetric dimensions and a separate full-trajectory Gaussian
conditioning oracle, preserve agent permutation and prefix isolation, and reject
altered identities, quantities and source contracts. Synthetic reported results
exercise the reader, not native execution. An actual emitted-program result
requires its separate producer/execution acceptance. Neither a passing numerical
audit nor supplied program bytes authenticates execution or upgrades a proof.

The new [finite product laws](composition_laws.lean) are a separate algebraic
seam. For explicit finite post-evidence weights `w(s,t) = u(s) * v(t)`, the joint
normalizer factors. Nonzero factor masses give normalized factorization and
joint sum one; nonnegative weights with positive masses give nonnegativity.
Independence of priors alone does not imply this post-evidence factorization.
The slice includes a correlated normalized joint with uniform normalized
marginals whose joint weight differs from the product of its marginals.
These laws prove no Gaussian measure, conditional kernel, covariance-block
identity, matrix-conditioning implementation or universal translation theorem.

Compile the finite laws and false zero-mass/omitted-factorization controls
serially, with the existing ready Lean/Mathlib workspace and no dependency
acquisition:

```bash
FEP_LEAN_VERIFY_TIMEOUT=60 uv run --frozen --no-sync python \
  specs/gnn-semantic-witness-v1/verify_composition_native.py \
  --output /absolute/path/to/new-composition-native
```

An optional `--lean-dir /absolute/path/to/ready/lean` selects an existing cache
only when its toolchain, Lake configuration and resolved manifest are
byte-identical to this checkout's pins. Every positive/negative compiler result,
source digest, compiler identity, warnings and axiom output is retained. Native
acceptance requires the positive law file to compile without warnings or proof
holes and each false control to fail by tactic failure. This narrow native
receipt remains separate from the numerical replay, catalogue/native rosters,
Q7 execution, source-pair custody and published historical receipts.
