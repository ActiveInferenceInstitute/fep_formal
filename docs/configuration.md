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
