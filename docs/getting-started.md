# Getting started

These are checkout workflows. Keep `.python-version`, `pyproject.toml`,
`uv.lock`, `config/`, the canonical and projected formal resources, and the
`lean/` pin triple together. The wheel packages the catalog but still needs
an explicit source checkout for configuration, verification, and publication.
Outside that checkout, put the global option before the subcommand:

```bash
fep-lean --project-root /path/to/fep_formal catalogue
```

## Portable mathematical inspection

The installed package can inspect and export mathematical contracts without a
checkout. Start with `fep-lean methods inspect --topic fep-001` and
`fep-lean methods export --output-root ./mathematical-methods`. The
[mathematical methods guide](mathematical-methods.md) explains the API, offline
explorer, numerical boundaries and canonical-source option. Native verification
and publication still require the checkout assets described below.

## Portable checkout kit

On macOS or Linux, install Bash, Git, uv, elan (the pinned installer below),
and `rsvg-convert` (the `librsvg` package on Homebrew or `librsvg2-bin` on
Debian/Ubuntu). Then, from a fresh clone of the intended reviewed commit:

```bash
bash scripts/setup_checkout.sh
```

The kit resolves its own checkout root, including paths containing spaces.
It runs `uv sync --locked --extra dev` with `.python-version`, checks the
validator interpreter and locked environment, runs guarded `fep-lean setup`
twice through the two existing entry points, and generates the catalog and
manuscript figures. Python can be acquired by uv; Lean and the Mathlib cache
are acquired by setup. Allow network access, several gigabytes for downloads,
and tens of gigabytes of free space for the expanded toolchain and workspace.
Use the same command again after an interrupted acquisition or to check
idempotency. Each setup pass has its own `FEP_LEAN_SETUP_TIMEOUT_SEC` deadline.
The kit stops at the first failed command and prints each command it runs.

This prepares the local Python/native gate environment; it does not assert
that the [gate battery](testing.md) passed. Run catalog generation before
projection-dependent manuscript checks, and native verification before the
strict manuscript-render check, which requires a current native receipt.
Committed evidence may already be stale at the chosen commit; setup must not
repair it. Publication rendering and live services retain their separate
tiers below. For catalog-only use, without elan or the SVG rasterizer:

```bash
bash scripts/setup_checkout.sh --catalogue-only
```

The [off-host inventory](scaffold-portability.md) lists machine dependencies,
substitutions, and a clean-environment acceptance recipe. The kit delegates
all Lean pin/cache validation to the existing setup implementation; it never
copies a donor `.lake` tree or invokes `lake update`.

## Catalog-only tier

Install uv and use Python 3.14, the validator version in `.python-version`.
The packaging floor in `pyproject.toml` is not the validator contract. From
the checkout root:

```bash
uv sync --locked --extra dev
uv run --locked fep-lean catalogue
uv run --locked fep-lean atlas --check
uv run --locked fep-lean dashboard --check
```

Dependency installation requires network access unless already cached. Once
installed, catalog mode is offline and needs no Lean, Hermes, OpenGauss,
provider credentials, donor cache, or coordinator tooling. Its report records
zero verified topics. The atlas is a structural view; the dashboard is
numerical, non-proof evidence.

## Native Lean tier

Add elan, Git, and access to the pinned Lean release and Mathlib cache hosts.
The following installer source is pinned to the same commit as CI; elan then
acquires the exact Lean toolchain recorded in the checkout:

```bash
curl -sSf https://raw.githubusercontent.com/leanprover/elan/0e36a07b9bbcc5381fa6250df109f9a4f94d7bac/elan-init.sh -o elan-init.sh
sh elan-init.sh -y --default-toolchain none
export PATH="$HOME/.elan/bin:$PATH"
uv run --locked fep-lean setup
uv run --locked fep-lean verify --topic fep-001 --fail-on-warnings
```

`setup` preserves the checked-in pins and uses a total deadline of 1800
seconds, configurable with `FEP_LEAN_SETUP_TIMEOUT_SEC`. The shell entry point
`bash scripts/_maint_bootstrap_lean_toolchain.sh` delegates to the same setup
implementation. Neither entry point updates the manifest. See
[the pinned acquisition and repair procedure](lean4.md#lock-preserving-setup).
An empty `ELAN_HOME` is supported; elan must already be installed or supplied
via `FEP_LEAN_ELAN_EXE`. Cache acquisition can require several gigabytes and
several minutes. Do not copy another checkout's `.lake/packages` as a recipe.

After setup, the maintained formal kernel and catalog have distinct checks:

```bash
uv run --locked python scripts/_maint_build_formal_modules.py --check
(cd lean && lake build FepSketches)
uv run --locked python scripts/audit_formalisms.py --receipt output/formalism-audit.json
uv run --locked fep-lean verify --fail-on-warnings --receipt output/native-verification.json
```

The build checks projected formal modules; the audit resolves declarations
and their axioms; `verify` compiles canonical topic bodies. A one-topic smoke
is evidence for that topic only. Full native receipt validation belongs to a
settled source snapshot. None of these requires Hermes or OpenGauss. See
[formal-kernel methods](formal-kernel-methods.md).

### Fast repeated local verification

Repeat `verify` runs in the same worktree (and after branch switches back to a
pin you have already built) can reuse the compiled Lake state instead of
rebuilding Mathlib from source:

```bash
uv run python specs/ci-velocity-local-cache/lean_cache.py -- uv run --locked fep-lean verify --fail-on-warnings
```

The wrapper validates the toolchain/Mathlib/manifest pins before invoking
Lake, restores a content-keyed snapshot of `lean/.lake` from
`~/.cache/fep-lean/lean-build` (override with `--store DIR` or
`FEP_LEAN_CACHE_DIR`) when one exists for the current pins, and refreshes
that snapshot after a successful run. Unless `--skip-build` is passed it also
runs `lake --wfail build FepSketches` first — the same cache-get, aggregate
build, verify sequence CI's lean lane runs, and the prerequisite that makes
verify-class commands resolvable at all (`lake env lean` resolves
`FepSketches.*` imports only through the built library). Add `--no-cache` to
skip both restore and refresh, and `--key-print` to inspect the cache key.
The store holds only derived Lake build outputs: custody
receipts are never cached, and every run still recompiles changed sources
through Lake's own traces, so reuse cannot mask drift. CI mirrors this with
an `actions/cache` restore/save pair that restores `lean/.lake/build` under
a key derived from the same pin files.

## Publication-render tier

Add the shared rendering-template checkout, its matching project registration,
XeLaTeX/TeX packages, pandoc, `rsvg-convert`, the mermaid CLI, and the fonts
selected by `manuscript/preamble.md`. Pass a real template path explicitly;
a symlink into a deleted worktree is not a portable dependency.

```bash
uv run --locked fep-lean catalogue
uv run --locked python scripts/build_manuscript_figures.py
uv run --locked python scripts/build_render_fonts.py --probe
uv run --locked python scripts/render_publication.py --template /path/to/template
```

Follow the
[local render runbook](../scripts/README.md#local-render-runbook) for template
registration, font diagnostics, acceptance, and diagnosing a local
`check_render_log.py --verify-receipt` failure without paying for an
unnecessary render: it separates missing generated inputs from real
manuscript-source drift. A successful native build is not render acceptance,
and generated manuscript values are not native proof.

## External full-mode tier

Add configured Hermes and OpenGauss, including the provider credentials for
`OPENROUTER_API_KEY` or the configured Anthropic-compatible Hermes endpoint.
Keep credentials outside the checkout. Native setup alone does not provide
these services.

```bash
uv run --locked fep-lean preflight
uv run --locked fep-lean run
```

`preflight` is read-only. `setup` acquires Lean dependencies; normal verification
does not install them. A failed full run returns nonzero and creates no
successful report. Full success requires every selected result to compile
without `sorry` or warnings; `review` also requires its prose-review stage.
A complete selected-topic run is not automatically a full-catalog,
publication-ready receipt.

Checkout portability does not resolve Q7's interpreter-dependent scaffold
serialization: its Python 3.14 guard and custody contract remain unchanged.
