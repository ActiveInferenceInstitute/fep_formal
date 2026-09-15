# `fep_lean`

The installable Python namespace for the FEP Lean catalogue and verification
pipeline.

- `catalogue/`: family-owned canonical bodies, validated registry, typed
  semantic review, package data, and deterministic coverage projections
- `formal/`: packaged foundations, leaf cross-topic compositions, import
  aggregate, and exact Lake projection
- `verification/`: pinned Lean/Lake checks, native compilation, and
  declaration/axiom auditing
- `llm/`: Hermes provider client
- `gauss/`: SQLite session storage and per-topic runner
- `pipeline/`: catalogue and strict full-mode orchestration
- `output/`: evidence receipts, reports, figures, manuscript variables,
  fail-closed rendering, the offline formalism atlas, and the formal-kernel
  validation dashboard

Use public imports such as:

```python
from fep_lean.catalogue import FEPTopicCatalogue
from fep_lean.output import (
    build_formal_kernel_dashboard,
    build_formalism_atlas,
    validate_native_lean_receipt,
)
from fep_lean.verification import LeanVerifier, run_formalism_audit
```

The wheel intentionally provides no obsolete top-level compatibility modules.

## Interpreter contract

`requires-python = ">=3.10"` declares the packaging floor, but the current
dev/evidence reality is narrower and pinned: `.python-version` pins CPython
3.14 for development and CI, mypy models 3.12 (`[tool.mypy] python_version`),
and the runtime test suite runs under 3.14 only. The declared 3.10/3.11 floor
is evidentially unsupported: `scaffold_digest` freezes `ast.dump` output,
which differs across CPython minor versions, so a scaffold accepted under one
interpreter cannot be re-validated under another. The Q7 module now enforces
this in code: `scaffold_digest` refuses to run before parsing under any
interpreter outside the accepted set — exactly CPython 3.14, the
`.python-version` pin — raising a `ContinuousArtifactError` naming the
accepted set and the running interpreter. The pinned `runner_ast_sha256`
digest is interpreter-contract-pinned to that set and is unchanged by the
guard. The guard does not relax the 3.14-only rule: a version-stable
serialization or an explicit multi-interpreter acceptance record still lands
as a new reviewed scaffold via `FEP-SCAFFOLD-PORTABILITY` with a coordinated
custody re-pin.
