# `FepSketches` — generated Lean library

The Lake library named `FepSketches`. Every `.lean` file here is a generated
projection; none is an authoring surface.

## Build and check

Run these from the repository root; only the `lake build` step changes
directory.

```bash
uv run fep-formal setup            # acquire and build the pinned toolchain and Mathlib once
(cd lean && lake build FepSketches)  # aggregate build
uv run fep-formal verify --fail-on-warnings --receipt output/native-verification.json
```

`setup` is the only command that acquires dependencies. `lake build` on its own
does not validate pins, and an editor compile does not run this build. See the
[workspace guide](../README.md) and [root required checks](../../AGENTS.md#required-checks).

## Entry points

| Path | Role |
| --- | --- |
| [fep_all.lean](fep_all.lean) | Import-only aggregate over every canonical topic body. |
| [composed.lean](composed.lean) | Import-only aggregate over the cross-topic composition leaves. |
| [families/](families/) | One generated module per reviewed catalog family. |
| [compositions/](compositions/) | Generated projection of the hand-written leaves in `src/fep_formal/formal/compositions/`. |

Foundation modules at this level are named by
[`src/fep_formal/formal/manifest.py`](../../src/fep_formal/formal/manifest.py).

## Ownership

- Topic bodies: [`src/fep_formal/catalogue/bodies/`](../../src/fep_formal/catalogue/bodies/).
- Foundations and composition leaves: [`src/fep_formal/formal/`](../../src/fep_formal/formal/).
- `families/` and `fep_all.lean`: `scripts/_maint_build_fep_all_lean.py`.
- Manifested resources and `compositions/`: `scripts/_maint_build_formal_modules.py`.

Change the owner, regenerate, and inspect the diff. Never repair a workspace
copy by hand. The local contract is [AGENTS.md](AGENTS.md).
