# Getting started

These commands are checkout workflows: the generated catalogue is packaged in
the wheel, but configuration, the pinned Lean tree, manuscript sources, and
publication outputs have one canonical source checkout. When invoking an
installed `fep-lean` entry point outside that checkout, put
`--project-root /path/to/fep_lean` before the subcommand.

```bash
uv sync --locked --extra dev
uv run fep-lean catalogue
uv run pytest tests/ -q
```

Validate the maintained formal kernel and its two offline views without
provider credentials:

```bash
uv run python scripts/_maint_build_formal_modules.py --check
(cd lean && lake build FepSketches)
uv run python scripts/audit_formalisms.py \
  --receipt output/formalism-audit.json
uv run fep-lean atlas --check
uv run fep-lean dashboard --check
```

The Lake build type-checks the projected formal modules. The audit separately
resolves reviewed declarations and parses their axiom reports. The atlas and
dashboard are structural and numerical views, respectively; neither replaces
the native checks. See [formal-kernel methods](formal-kernel-methods.md).

For strict verification, install the pinned Lean workspace and OpenGauss,
configure `OPENROUTER_API_KEY` or an Anthropic-compatible Hermes endpoint, then
run:

```bash
uv run fep-lean setup
uv run fep-lean verify
uv run fep-lean preflight
uv run fep-lean run
```

`verify` compiles the topic catalogue with Lean only and needs no Hermes
credentials; the formalism audit covers the shared-kernel declarations.
`preflight` is read-only. `setup` is the only command that downloads or builds
Lean dependencies. A failed full run returns a non-zero exit status and does
not create a successful report. Full success requires every selected result to
compile with no `sorry` and no warnings; `review` additionally requires its
prose-review stage to finish.
