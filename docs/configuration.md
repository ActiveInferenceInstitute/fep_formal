# Configuration

The runtime source is [`config/settings.yaml`](../config/settings.yaml).
Environment variables override secrets and operational limits.

| Setting | Purpose |
| --- | --- |
| `gauss.home` / `GAUSS_HOME` | SQLite state, exported artifacts, and logs |
| `gauss.default_model` | YAML policy value cross-checked against `hermes.model` by `docs/pin_audit.py`; not a runtime input. The separate `GAUSS_DEFAULT_MODEL` environment variable is a runtime model fallback. |
| Lean verification | Not settings-driven: a fixed full-mode pipeline stage (`Gauss Sessions`); catalogue mode never verifies. `FEP_LEAN_VERIFY_TIMEOUT` bounds it |
| `output.root` / `FEP_LEAN_OUTPUT_ROOT` | Generated figures and reports root; explicit API argument wins, then a nonblank environment override, then settings, then `project_root/output` |
| `hermes.model` | Primary Hermes model: a nonempty `HERMES_MODEL` overrides YAML; a truthy YAML `hermes.model` wins over `GAUSS_DEFAULT_MODEL`; otherwise a nonempty `GAUSS_DEFAULT_MODEL` is used before the built-in default. See [`HermesConfig.from_settings`](../src/fep_lean/llm/hermes.py) |
| `hermes.fallback_models` | Ordered configured model chain; `HERMES_FALLBACK_MODELS` supplies a strict nonempty JSON list of exact model names |
| `hermes.timeout_s` | Request deadline |
| `hermes.cache_ttl_hours` | SQLite response-cache lifetime |

Important environment variables include `OPENROUTER_API_KEY`,
`ANTHROPIC_API_KEY`, `HERMES_API_BASE`, `HERMES_MODEL`, `HERMES_FALLBACK_MODELS`,
`FEP_LEAN_LAKE_EXE`, `FEP_LEAN_LEAN_EXE`, `FEP_LEAN_VERIFY_TIMEOUT`,
`FEP_LEAN_MAX_TOPICS`, and `FEP_LEAN_OUTPUT_ROOT`.

Project-root selection uses explicit CLI `--project-root`, then the current
`project_root_context(root)`, then `FEP_LEAN_PROJECT_ROOT`, then the installed
package's checkout fallback. Context selection does not change `os.environ`
and resets after errors. New threads and OS processes require explicit roots;
the publication-capture owner copies its selected root into child environments.
See [the public caller-root API](api.md#explicit-caller-roots-and-native-operations).

Relative `output.root` settings are resolved from the project checkout. Relative
explicit API paths and `FEP_LEAN_OUTPUT_ROOT` paths retain their caller working
directory semantics. The selected output directory, or its nearest existing
ancestor, must be writable and searchable. Capability inspection reads that
exact target without creating directories; an occupied file or dangling link
rejects. Authored manuscript projections remain paired under `manuscript/`;
their run-bound evidence is selected from the resolved output root.

`fep-lean preflight` performs no download, build, database write, or report
write. Use `fep-lean setup` when dependency acquisition is required.

Full-mode credential inspection uses the same allowlisted OpenGauss dotenv,
process-environment precedence and endpoint-affinity rules as Hermes execution.
It also accepts `OPENAI_API_KEY` for a configured compatible endpoint. Inspection
uses `HermesConfig.from_settings(..., hydrate_environment=False)` and does not
hydrate process variables or authenticate with a provider. Existing execution
callers retain the default environment hydration behavior.

For primary-only execution, set `HERMES_FALLBACK_MODELS` to a JSON list
containing only the primary model. An absent override preserves the configured
chain; an empty or malformed list rejects. `HermesConfig.runtime_policy()`
projects a safe allowlist of configured nonsecret settings. It does not freeze
retry/attempt limits; record `HERMES_NETWORK_MAX_RETRIES`,
`HERMES_429_MAX_RETRIES` and `HERMES_MAX_MODEL_ATTEMPTS` separately when capturing
an execution policy. OpenRouter batch variants require the asynchronous Batch
API and must not be treated as synchronous fallback completions.

## Operator options, defaults and precedence

The global `fep-lean` options are `--project-root PATH` and `--verbose`
(default false). Root and output precedence are defined above; select global
options before the command. The render entry point is a script with its own
checkout root, rather than a `fep-lean render` verb.

| Operation | Public options and defaults | Selection and effects |
| --- | --- | --- |
| `catalogue` | `--area` and repeated `--topic`; omitted filters select all topics | `FEP_LEAN_MAX_TOPICS` blank means unlimited; a positive integer bounds the selected set. Writes generated artifacts; no provider or native verification. Raster tools may run. |
| `status` | Optional `--gnn-root PATH` | Read-only, process/provider-free composition. Omitted GNN leaves that side unverified. Exit 0 means composition, including stale or missing evidence. |
| `verify` | `--area`, repeated `--topic`, optional `--receipt PATH`; `--fail-on-warnings` defaults false | Omitted filters select all topics. Empty/unknown selection refuses. Uses existing pinned Lean/Mathlib and temporary compiler probes; only an explicit receipt path requests a receipt write. |
| `bridge` | Required operation and `--gnn-root`; `--model` defaults `finite`; `--check` and `--refresh-digests` are mutually exclusive and default false; `--results`, `--receipt`, `--document` default absent; `--fail-on-warnings` defaults false | Applicability is listed below and in the [support table](cli-reference.md#operator-support-and-exit-contracts). Inspection, emission, certificate checks and native document checks have distinct effects. |
| `run` | `--area`, repeated `--topic`; `--workflow` defaults `verify`, with `draft`, `prove`, `review` alternatives | Full-mode service checks, model policy, topic/output selection and `FEP_LEAN_MAX_TOPICS` apply. Calls providers, compiler, database and artifact owners. Catalogue mode must be selected explicitly in the Python API. |
| `python scripts/render_publication.py` | Optional `--template`; `--accept-only`, `--skip-font-probe`, `--require-release-stamp` default false; `--lock-timeout` defaults 1800 seconds | Uses the script checkout. First valid template wins: explicit path, then nonblank `FEP_LEAN_TEMPLATE_DIR`. An invalid explicit path falls back to a valid environment path. Both invalid refuse. `DOCXOLOGY_RENDER_LOCK` selects the shared lock path. Acceptance remains required when the font probe is skipped. |
| `publication-capture` | Required `--template`; `--journal` required except with `--plan`; `--plan` and `--resume` default false and cannot combine; `--source-date-epoch` defaults 0; `--timeout` defaults 21600 seconds | Plan construction writes no journal and starts no subprocess. Execution is POSIX-only, copies the explicit root/template into bounded stages and writes journals/artifacts. Resume revalidates source and journal before reuse. |

Render `--accept-only` delegates directly to existing-artifact acceptance; it
skips template resolution, the shared render lock and source hydration.
`--template`, `--lock-timeout`, `--skip-font-probe` and
`--require-release-stamp` do not affect that branch. Acceptance still inspects
the existing manuscript/PDF inputs and writes its receipt.

For `verify`, the import-time timeout fallback captures
`FEP_LEAN_VERIFY_TIMEOUT`, defaulting to 1800 seconds. Each native invocation
rereads the environment variable, falling back to that captured value when it
is absent. Set it before starting Python for a consistent process-wide policy.
See the [native API](api.md) for its exact interfaces. The output-root hierarchy
above applies to catalogue and full pipeline generation; there is no global
`--output-root` CLI option.

Bridge option applicability preserves the shared parser's compatibility:
`--model` affects `emit` and `verify-document`; `--results` is required by
`certify`; `--receipt` is certificate input for `verify-certificate` and optional
output for `certify` and `verify-document`; `--document` is required by
`verify-document`; `--fail-on-warnings` affects `verify-document`. Outside these
operations, those flags are accepted and ignored, including their file paths;
they do not request additional work. `--check` and `--refresh-digests` instead
refuse outside `emit`. Use only the options of the intended operation when
constructing an invocation; unsupported option names remain parser errors.
