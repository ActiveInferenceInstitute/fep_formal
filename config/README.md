# fep_lean/config — Configuration Reference

**Version**: v1.2.0 | **Status**: Active | **Last Updated**: September 2026

## Files

| File | Purpose |
| ---- | ------- |
| `settings.yaml` | Hermes block + project metadata (read by `HermesConfig.from_settings`); `gauss.*` / `orchestration.*` are mostly defaults or notes—see [`../docs/configuration.md`](../docs/configuration.md) |
| `catalogue_metadata.yaml` | Schema-2 roster seal, family membership, title, area, Mathlib hints, and compile-maturity fields |
| `theorem_maturity.yaml` | Maintained semantic review and primary theorem for every topic |
| `formalism_novelty.yaml` | Maintained novelty contract for expansion rows and their required composition bridges |
| `formalism_relations.yaml` | Maintained typed topic relations plus retained capability status/evidence history |
| `topics.yaml` | Generated join of metadata, semantic review, canonical Lean bodies, and equation signatures; regenerate via `scripts/_maint_build_topics_catalogue.py` |

## settings.yaml

Authoritative fields live in the checked-in file. Highlights:

- `project.version` should match `pyproject.toml` and `manuscript/config.yaml`.
- `hermes.*` is loaded by `HermesConfig.from_settings()` in `fep_lean/llm/hermes.py` (env overrides apply).
- `GAUSS_HOME` and API keys come from the environment or `~/.gauss/.env`; SQLite paths use `fep_lean/gauss/client.py` (defaults described in [`../docs/opengauss.md`](../docs/opengauss.md)).

## Config override examples

```bash
# From the project root

GAUSS_HOME=/tmp/test-gauss uv run python scripts/01_fep_catalogue_and_figures.py

OPENROUTER_API_KEY="" uv run python scripts/01_fep_catalogue_and_figures.py

GAUSS_LOG_LEVEL=DEBUG uv run python scripts/02_run_single_topic.py fep-001
```

## topics.yaml — Topic format

Every topic must include:

```yaml
- id: fep-NNN           # unique and ordered within the maintained roster seal
  title: ...
  area: FEP             # FEP | ActiveInference | BayesianMechanics | InfoGeometry | Thermodynamics
  family: ...
  mathlib_modules: [...]
  mathlib_status: ...   # real | partial | aspirational
  primary_theorem: ...
  supporting_theorems: [...]
  boundary_theorems: [...]
  semantic_disposition: ...
  nl: ...
  assumption_review: ...
  non_vacuity: ...
  acceptance_probe: ...
  lean_sketch: |
    ...
  latex_equations: [...]
```

Do not hand-edit generated topic rows. Edit `catalogue_metadata.yaml`,
`theorem_maturity.yaml`, the applicable `formalism_novelty.yaml` row, or the
appropriate module under `src/fep_lean/catalogue/bodies/`, then run the
generator and its `--check` mode. `src/fep_lean/catalogue/registry.py` is the
validated merger; `src/fep_lean/catalogue/latex.py` derives theorem
signatures.

`formalism_relations.yaml` is independent maintained review data. Its
`conceptual`, `formal`, and `formal_pairing` topic edges and `blocked_by`
capability edges must carry rationales. Both theorem-backed kinds name a
qualified Lean witness; `formal_pairing` explicitly does not assert that one
endpoint follows from the other. Capability status is `open`, `partial`, or `satisfied`; non-open
statuses require declaration evidence, and satisfied nodes remain in the file
as resolution history. The coverage builder resolves evidence/witness
declarations, validates targets, rejects derivational-formal cycles, and
requires every semantic gap row to identify at least one blocker.

`formalism_novelty.yaml` covers rows added after the original core roster. Each
record names earlier nearest topics, states the invariant and carrier delta,
and requires a stable `FEPComposed` theorem in a manifested leaf composition
module. It is an authored semantic ledger, not a generated similarity score.

## Navigation

- **AGENTS.md**: [AGENTS.md](AGENTS.md)
- **Parent project**: [../README.md](../README.md)
- **Source layout**: [../src/README.md](../src/README.md)
