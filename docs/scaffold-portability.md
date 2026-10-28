# Scaffold portability

The [checkout kit](getting-started.md#portable-checkout-kit) carries the
locked Python environment, pinned Lean/Mathlib acquisition, repeated setup,
and generated local gate inputs. It builds on the
[lock-preserving setup contract](lean4.md#lock-preserving-setup). No Herdr,
omp, sibling checkout, donor cache, or provider credentials are required for
that kit. A prepared environment and a passing gate battery are separate
results; receipt freshness depends on the exact checked-out sources.

## Off-host inventory

The inventory below names the maintained owners and entry points for each
execution surface. A search of `scripts/*.py` and `scripts/*.sh` for `/Users/`,
`/home/`, and `/opt/` finds no hard-coded host checkout paths. Paths passed
through arguments or environment variables still need local substitutions.

| Surface and evidence | What the kit leaves out; what to substitute |
| --- | --- |
| [OpenGauss installer](../scripts/00b_install_opengauss_cli.sh) | Uses `$HOME/.gauss_src` and pulls the service's current main. It is outside the locked kit. Install/configure the service separately for the external full-mode tier. |
| [Publication template resolver](../scripts/render_publication.py) (`resolve_template`) | Requires `--template` or `FEP_FORMAL_TEMPLATE_DIR`. Supply a real local template checkout and register this checkout as its active project, following the render runbook. |
| [Browser wrapper](../scripts/capture_browser_acceptance.py) (`build_parser`, `main`) | Browser acceptance needs a local Chrome/Chromium executable; pass `--browser` when discovery is unsuitable. The kit does not capture browser evidence. |
| [Manuscript identifier audit](../scripts/render_manuscript.py) (`main`) | Reads `lean/.lake/packages/mathlib`. Let guarded setup materialize the manifest's exact revisions at that layout; an arbitrary relocated or rsynced package tree is not a substitute. |
| [Lean setup](../src/fep_formal/verification/environment.py) (`setup_workspace`) | `FEP_FORMAL_DIR`, `ELAN_HOME`, `XDG_CACHE_HOME`, and `MATHLIB_CACHE_DIR` can redirect state. Remove stale overrides or supply writable local locations. Keep the intended checkout's pin triple together. |
| [Tool discovery](../src/fep_formal/verification/_toolchain.py) (`find_executable`) | `FEP_FORMAL_LAKE_EXE` and `FEP_FORMAL_LEAN_EXE` override discovery. Remove paths to another host/worktree; setup verifies the actual compiler identity. Cold setup also accepts `FEP_FORMAL_ELAN_EXE`. |
| [Service configuration](../src/fep_formal/llm/hermes.py) (`HermesConfig.from_settings`) | Full mode needs local service configuration and credentials, optionally read from `$GAUSS_HOME/.env`. Supply them privately; copying a home directory is not part of setup. |
| [Bridge CLI](../src/fep_formal/bridge/cli.py) (`add_arguments`, `run`) | Live bridge checks require an explicitly selected `--gnn-root` with matching custody pins. Normal standalone tests need no sibling checkout. Do not repin to make a local check pass. |
| [Collection summary parser](../src/fep_formal/output/manuscript.py) (`parse_pytest_collection_stdout`) | Slow hosts can collect tests for over a minute; pytest then appends `H:MM:SS`. The parser accepts that duration suffix while retaining the exact roster and final-summary checks. Collection still has its existing 120-second timeout; a timeout is a failure, not permission to invent a test count. |
| [Render runbook](../scripts/README.md#local-render-runbook) | XeLaTeX, pandoc, mermaid, fonts, template registration, and fresh publication receipts remain the publication tier. The kit only generates catalog and rasterized figure inputs. |

Herdr pane IDs, `.herdr-project` briefs/receipts, omp skills, and private PAI
bootstrap paths belong to the coordinator environment, not the installed
package or kit. A standalone user substitutes a terminal and their own log
directory. Keep private coordinator state out of public artifacts. The kit
does not reproduce a developer's PATH, `.venv`, `.lake`, service state, or
15 GB package-tree rsync; it acquires pinned dependencies instead.

## Fresh-checkout acceptance

Install the prerequisites from getting started first. Clone into a new
directory; do not copy `.venv`, `output`, or `.lake` from another checkout.
Record the checked-out commit and run with a new home and empty caches.
For example, from the new clone, replace the two executable locations with
your installed uv and elan locations (the elan executable may be reused;
its toolchains and settings must start empty):

```bash
kit_root="$PWD"
acceptance_root="$(mktemp -d)"
mkdir -p "$acceptance_root/home" "$acceptance_root/bin"
ln -s /path/to/uv "$acceptance_root/bin/uv"
ln -s /path/to/elan "$acceptance_root/bin/elan"
# Add Git and rsvg-convert to this bin directory if absent from /usr/bin:/bin.
env -i HOME="$acceptance_root/home" \
  PATH="$acceptance_root/bin:/usr/bin:/bin" \
  ELAN_HOME="$acceptance_root/elan" \
  XDG_CACHE_HOME="$acceptance_root/cache" \
  UV_CACHE_DIR="$acceptance_root/uv-cache" \
  UV_PYTHON_INSTALL_DIR="$acceptance_root/python" \
  MATHLIB_CACHE_DIR="$acceptance_root/mathlib-cache" \
  bash "$kit_root/scripts/setup_checkout.sh"
```

Run from outside the clone too, preferably with spaces in its path. Retain
the command, exit code, platform/architecture, commit, and full output. Hash
`uv.lock`, `lean/lean-toolchain`, `lean/lakefile.lean`, and
`lean/lake-manifest.json` before and after; require identical hashes and a
clean tracked tree. Confirm the materialized dependency HEADs match every
manifest revision. Run the kit again under the same isolated environment and
retain that exit code as well. The two internal setup passes exercise both
guarded entry points, while the second whole-kit run also exercises Python
and generated-input idempotency.

Use that environment for the [required gates](testing.md) and an exact-topic
smoke (`uv run --locked fep-formal verify --topic fep-001 --fail-on-warnings`).
An exact-topic smoke is not a full native receipt. Missing native evidence or
stale committed render/custody evidence must remain explicit failing gates;
the kit never manufactures acceptance. Record gates requiring live services
or an explicitly named GNN pair separately. For Linux container acceptance,
use native container storage, as required by the t-0058 filesystem finding.

Q7 candidate scaffold portability has a separate
[reviewed serialization protocol](../specs/gnn-bridge-q7-continuous-ou-proof/scaffold-serialization.md)
and five-runtime byte-parity record. Its strict validator remains CPython 3.14;
the serializer change requires fresh source-bound native/custody evidence.
This checkout kit continues to use Python 3.14. Prepared dependencies,
candidate serialization parity, and publication receipts are separate results.
