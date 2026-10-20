# `fep_lean.methods`

Portable, offline mathematical positioning of the FEP_Formal catalogue. The
package validates the canonical topic, maturity, relation, and positioning
inputs, then answers exact queries and renders deterministic artifacts: a JSON
and Markdown projection, a visual model, SVG panels, and a self-contained
`mathematical-map.html`.

```text
installed data or explicit checkout → validated MathematicalPositioning
                                    → queries (CLI / API)
                                    → positioning.json / .md, visual-model.json,
                                      mathematical-map.html, panels/*.svg
```

`build_mathematical_positioning(project_root=None)` uses the installed package
data; passing a checkout root reads the canonical owners instead. The result
records its `SourceOrigin` and the SHA-256 of every byte read. Queries
(`inspect_topic`, `inspect_family`, `inspect_theorem`, `analyze_topic`,
`positioning_neighbors`, `cross_corpus_embedding`) return detached copies.

`load_packaged_formalism_query()` returns that same immutable model after
checking its consumed resources and package Python files against the installed
wheel's `RECORD` hashes/sizes, before and after analysis. It rejects missing or
unverifiable metadata and changed members, including coherent relation edits.
It requires a real wheel installation; use the explicit checkout builder while
authoring. Integrity is relative to trusted installation metadata, and does not
authenticate replacement of the entire distribution. No extra query registry,
subprocess, network operation or native receipt is introduced. See the
[installed query API](../../../docs/api.md#mathematical-methods).

Use `uv run fep-lean methods --help`. `inspect`, `neighbors`, `probe`, `gibbs`,
`analyze`, `theorem`, `embedding`, and `check` perform no writes; `export`
writes the artifact tree under `--output-root` (default
`output/mathematical-methods`). Failures print a JSON error and exit 1.

`probes.py` owns finite diagnostic examples (Bernoulli Fisher interior,
KL support boundary, Fisher chart degeneracy, descent without identification)
and a deterministic two-dimensional classical MDS over binary feature vectors,
computed with its declared fixed-precision `Decimal` contract so artifact bytes
do not depend on LAPACK or platform libm.

The same owner exposes `finite_expectation`, `log_partition`,
`exponential_tilt` and `gibbs_duality_diagnostics` for arbitrary finite inputs.
The expectation accumulates products exactly before rounding. Gibbs weights
use supported, centered high-precision arithmetic; diagnostics distinguish
reference zeros from numerical underflow and report normalization explicitly.
The `gibbs` CLI accepts three required JSON arrays and works without loading a
catalogue model. See the [numerical API guide](../../../docs/mathematical-methods.md#reusable-finite-variational-methods)
for conventions, examples and range boundaries.

Everything here is explanatory context, not proof. Source validation is text
analysis, not Lean elaboration; family domains are editorial unions; feature
distance and MDS coordinates compare authored assignments and create no
theorem relation. No native receipt, Hermes/OpenGauss execution, or upstream
code execution is involved.

```python
from fep_lean.methods import build_mathematical_positioning, inspect_topic

model = build_mathematical_positioning()
print(inspect_topic(model, "fep-038")["primary_theorem_qualified"])
```

See the [guide](../../../docs/mathematical-methods.md), the
[slice README](../../../specs/openai-math-methods/README.md), and the
[generated outputs](../../../docs/mathematical-positioning/positioning.md).
