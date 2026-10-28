# `fep_formal.gauss`

SQLite session storage and the strict per-topic Hermes-to-Lean runner. This is
the only package that owns `{GAUSS_HOME}/fep_lean_state.db`.

`OpenGaussClient` stores sessions, turns, artifacts, logs, and the Hermes cache
with WAL mode and foreign keys enabled. `GaussRunner` records one
`TopicRunResult` per selected topic and supports `verify`, `draft`, `prove`, and
`review` prompt workflows. `FEP_FORMAL_PREFETCH=1` may overlap provider work for
the next topic with current-topic verification.

`review` is a strict two-turn workflow. The first turn must return a Lean block;
after that exact source compiles, the second turn receives it under a
prose-only prompt. Both turns are stored, separately cached, and required for
workflow success. Compiler warnings remain explicit topic failures even when
Lean returns zero.

`check_gauss_cli(project_root, require=...)` runs a bounded `gauss --version`
with a fresh temporary `GAUSS_HOME` and update checks disabled. Missing or
unrecognized CLI output is advisory when `require=False` and fatal when
`require=True`; full pipeline mode always requires it. CLI availability does
not establish provider or session health. Automatic preflight avoids upstream
`doctor`, which can read or refresh managed account credentials. Separate Hermes,
SQLite and pinned Lean checks remain strict. There is no environment switch that
turns a requested full run into an offline run—select `mode="catalogue"`
explicitly for offline artifact generation.

```python
from fep_formal.gauss import GaussRunner, OpenGaussClient, TopicRunResult
```

Hermes, refined Lean, fallback, token, model, cache, compiler, `sorry`, warning,
and review-stage outcomes stay separate in `TopicRunResult`; reporters must not
infer success from a partial subset of those fields.
