# FEP_Formal configuration

## Files

| File | Purpose |
| ---- | ------- |
| `settings.yaml` | Hermes block + project metadata (read by `HermesConfig.from_settings`); `gauss.default_model` is only a `docs/pin_audit.py` cross-check (must equal `hermes.model`), and orchestration is pipeline code (`src/fep_lean/pipeline/`), not config—see [`../docs/configuration.md`](../docs/configuration.md) |
| `catalogue_metadata.yaml` | Schema-2 roster seal, family membership, title, area, Mathlib hints, and compile-maturity fields |
| `theorem_maturity.yaml` | Maintained semantic review and primary theorem for every topic |
| `formalism_novelty.yaml` | Maintained novelty contract for expansion rows and their required composition bridges |
| `formalism_relations.yaml` | Maintained typed topic relations plus retained capability status/evidence history |
| `topics.yaml` | Generated join of metadata, semantic review, canonical Lean bodies, and equation signatures; regenerate via `scripts/_maint_build_topics_catalogue.py` |

## settings.yaml

Authoritative fields live in the checked-in file. Highlights:

- `project.version` should match `pyproject.toml` and `manuscript/config.yaml`.
- `hermes.*` is loaded by `HermesConfig.from_settings()` in `fep_lean/llm/hermes.py` (env overrides apply).
- SQLite state uses `resolve_gauss_home()` in `fep_lean/gauss/client.py`:
  `GAUSS_HOME` takes precedence over checkout `gauss.home`, then the caller's
  default. Hermes separately reads allowlisted keys from the environment or
  `$GAUSS_HOME/.env` (`~/.gauss/.env` when unset), independently of the checkout
  `gauss.home` setting. See [configuration](../docs/configuration.md)
  and [OpenGauss](../docs/opengauss.md) for those distinct resolution paths.
- `output.root` belongs to `resolve_output_root()` in `fep_lean/_paths.py`.
  An explicit API `output_root` takes precedence over `FEP_LEAN_OUTPUT_ROOT`,
  the checkout setting and the default. Methods projection `--output-root`
  selects its own export destination; ordinary catalogue/run commands use
  the environment or checkout setting.

Project-facing documentation uses FEP_Formal. Existing package, CLI and runtime
configuration identifiers remain as declared in their owners.

## Config override examples

```bash
# From the project root; explicit offline artifact generation
FEP_LEAN_OUTPUT_ROOT=/tmp/fep-formal-catalogue uv run fep-lean catalogue
```

## topics.yaml — Topic format

The complete row fields and validation rules live in
[`schema.py`](../src/fep_lean/catalogue/schema.py),
[`semantics.py`](../src/fep_lean/catalogue/semantics.py) and
[`topics.py`](../src/fep_lean/catalogue/topics.py). The generated `lean_sketch`
field keeps its compatibility name; its content comes from canonical topic
bodies. Compilation maturity and semantic disposition remain separate fields.

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

- [Authoring contract](AGENTS.md) and [configuration specification](SPEC.md)
- [Required checks](../AGENTS.md#required-checks)
- [Source layout](../src/README.md) and [project overview](../README.md)
