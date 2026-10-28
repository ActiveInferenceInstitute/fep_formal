# Lean 4 workspace

The workspace pins `leanprover/lean4:v4.35.0` and the matching Mathlib
`v4.35.0` release, with `lean/lake-manifest.json` recording the exact Mathlib
revision those pins resolve to. These are exact reproducibility pins for the
newest stable Lean/Mathlib release pair, not floating aliases: release
candidates and nightlies do not replace the stable line. The networked pin
audit re-derives the newest valid pair from the live ecosystem against that
manifest: it checks Lean's stable releases in descending order and accepts
only the newest release with a validated matching Mathlib tag, so the audited
pins stay in step with what the workspace actually builds with. A newer Lean
release without that tag is reported as pending ecosystem support rather
than installed into an incompatible workspace.

The [v4.35.0 release notes](https://lean-lang.org/doc/reference/latest/releases/v4.35.0/)
describe the selected stable release. The workspace pairs it with the matching
[Mathlib4 v4.35.0 release](https://github.com/leanprover-community/mathlib4/releases/tag/v4.35.0)
which is available at the same version. A pin change alone does not establish
native verification; rebuild and refresh receipts as described below.

```bash
uv run fep-formal setup
uv run python docs/pin_audit.py --check-latest
uv run fep-formal verify --fail-on-warnings --receipt output/native-verification.json
uv run python scripts/audit_formalisms.py --receipt output/formalism-audit.json
cd lean
lake build
lake build FepSketches
```

## Lean 4.35 migration boundary

The migration introduces explicit modules, public imports and exposed public
sections in maintained formal sources and generated probes. Supporting
constants that occur in exported definitions are public. Mathematical theorem
statements retain their original scope. Native compilation checks the current
sources against the pinned Mathlib API.

Historical scientific freezes and custody receipts retain their original
source and toolchain digests. Test-only reversal of enumerated formatting,
import and visibility edits checks the historical byte contracts without
renewing those approvals. The current H3 study remains rejected by its frozen
source guard until a separately governed successor epoch is accepted.

Catalog generation changes the appendix when proof bodies change. The
retained publication render receipt then fails its freshness check, even when
Lean validation passes. Follow the real render procedure in
[scripts/README.md](../scripts/README.md#3-render-and-accept) before renewing
publication acceptance; do not replace receipt hashes by hand.

## Lock-preserving setup

From a checkout synchronized with `uv sync --locked --extra dev`, use
`uv run --locked fep-formal setup` or
`bash scripts/_maint_bootstrap_lean_toolchain.sh`. Both use the same bounded
implementation. It validates the toolchain, Mathlib tag, and committed
manifest before acquisition, and checks that the pin triple and `uv.lock`
remain byte-identical after each subprocess. An explicit Lake executable
must report the pinned compiler version. Without Lake, setup uses elan to
install exactly the checkout's toolchain; set `FEP_FORMAL_ELAN_EXE` if elan is
not on PATH. `ELAN_HOME` may point to a new empty directory. Set
`XDG_CACHE_HOME` or `MATHLIB_CACHE_DIR` to isolate downloaded cache artifacts
as well; setup forwards these locations to its acquisition subprocesses.

The underlying acquisition sequence is:

```bash
elan toolchain install "$(cat lean/lean-toolchain)"
cd lean
lake exe cache get
lake build FepSketches
```

Pinned Lake reads existing manifest revisions for these commands. It has no
uv-style `--locked` option. The guarded setup entry points are preferred over
running the commands by hand: Lake can generate a missing manifest, so setup
rejects missing/corrupt pins before Lake runs. It never invokes `lake update`
or ignores a failed cache acquisition. The setup deadline covers installation,
cache acquisition, and build together; timeout kills the subprocess group.
A cache failure is a failure, not authorization for an unbudgeted source build.

On a pin error, inspect `git diff -- lean/lean-toolchain lean/lakefile.lean
lean/lake-manifest.json uv.lock`. Preserve intentional edits, then restore
these files together from the intended reviewed commit and rerun setup. Do
not repair ordinary setup with `lake update`. If a consistent reviewed pin
set still fails, retain the command log and diagnose the acquisition/toolchain
failure before changing dependencies. Setup reports unexpected pin drift
and stops; it does not overwrite user changes to hide drift.

### Repeatability check

In a clean disposable checkout after `uv sync --locked --extra dev`, isolate
the toolchain and artifact cache, then compare SHA-256 hashes across both
entry points. Elan must already be installed as described above.

```bash
export ELAN_HOME="$(mktemp -d)"
export XDG_CACHE_HOME="$(mktemp -d)"
uv run --locked python - <<'PYTHON'
import hashlib
from pathlib import Path
import subprocess

pins = ["lean/lean-toolchain", "lean/lakefile.lean", "lean/lake-manifest.json", "uv.lock"]
def hashes():
    return {name: hashlib.sha256(Path(name).read_bytes()).hexdigest() for name in pins}

before = hashes()
print("before:", before, flush=True)
for command in (["uv", "run", "--locked", "fep-formal", "setup"],
                ["bash", "scripts/_maint_bootstrap_lean_toolchain.sh"]):
    subprocess.run(command, check=True)
    after = hashes()
    print("after:", after, flush=True)
    assert after == before, "setup changed a checked-in pin"
subprocess.run(["git", "diff", "--exit-code", "--", *pins], check=True)
PYTHON
uv run --locked fep-formal verify --topic fep-001 --fail-on-warnings
(cd lean && lake env lean --version && git -C .lake/packages/mathlib rev-parse HEAD)
```

Retain the command output and elapsed times as separate Linux and macOS
receipts. A platform result covers the tested architecture and filesystem;
for container acceptance, use a native container filesystem for the checkout,
ELAN_HOME, and cache to avoid shared-filesystem file-handle limits during
parallel Lean compilation. One platform's result does not establish the
other's. This smoke does not replace full native receipt validation.

## Deliberate toolchain upgrades

The 4.35 workspace uses module headers and explicit public imports in the
formal kernel and generated aggregates. Some Mathlib lemmas now require
direct imports because their earlier transitive dependencies are private.
The verifier converts module-less topic input to equivalent exposed module source;
explicit module input keeps its declared visibility. Theorems and assumptions
remain authored in their canonical owners, and projections must be regenerated.

When a newer compatible stable pair appears, update both canonical pins, run
`lake update` and the Mathlib cache acquisition, migrate every warning or
compiler error in canonical sources, and regenerate the native and formalism
receipts. CI and the scheduled latest-stable workflow reject a stale compatible
pair; they do not silently select a different compiler.

Canonical topic bodies live in family modules under
[`src/fep_formal/catalogue/bodies/`](../src/fep_formal/catalogue/bodies/).
[`registry.py`](../src/fep_formal/catalogue/registry.py) validates and merges them,
and [`latex.py`](../src/fep_formal/catalogue/latex.py) projects theorem signatures.
The tracked aggregate
[`lean/FepSketches/fep_all.lean`](../lean/FepSketches/fep_all.lean) is regenerated with
[`scripts/_maint_build_fep_all_lean.py`](../scripts/_maint_build_fep_all_lean.py).
CI rejects regeneration drift, proof holes, and Lean warnings in the aggregate.

Reusable foundations and cross-topic theorems have separate canonical owners
under [`src/fep_formal/formal/`](../src/fep_formal/formal/); the exact module set
and roles are declared in `manifest.py`. Leaf modules under `compositions/` own
proofs that consume multiple stable topic namespaces, while `composed.lean` is
their import-only aggregate.
[`scripts/_maint_build_formal_modules.py`](../scripts/_maint_build_formal_modules.py)
projects every manifested Lean source byte-for-byte into `lean/FepSketches/`.
For a dependency-ordered navigation map of the formal modules, see
[`lean-landscape.md`](lean-landscape.md), generated by
[`scripts/_maint_build_lean_landscape.py`](../scripts/_maint_build_lean_landscape.py)
(with a `--check` freshness gate).
Formal
relations in `config/formalism_relations.yaml` must name a qualified declaration
from this or another canonical module. The formalism audit resolves all primary
and semantic-evidence declarations and runs `#print axioms` over every one. A
zero exit code is insufficient: the receipt requires one parsed axiom result
per declaration, normalizes hard-wrapped Lean messages, binds actual Lean and
the resolved Mathlib revision, and rejects missing output, stale projections,
warnings, `sorryAx`, or axioms outside the versioned trusted set (`propext`,
`Classical.choice`, `Quot.sound`).

The [formal-kernel methods](formal-kernel-methods.md) page explains the
probability, information, active-inference, blanket, geometry, and convergence
contracts and why projection, build, audit, native receipt, visualization, and
full-run evidence remain distinct.

## Catalog source of truth {#catalogue-source-of-truth}

Metadata, semantic review, novelty records, and the family body registry are
maintained separately and joined strictly by the schema-2 roster seal.
`config/topics.yaml` and packaged `src/fep_formal/data/topics.yaml` must be
byte-identical. The strict loader checks the generated schema before execution.

## Cursor Lean 4 commands {#cursor-lean4-commands}

Use the canonical local commands above. Editor integrations should invoke the
same pinned Lake workspace rather than a separately discovered compiler.

## Mathlib4 modules used in FEP_Formal {#mathlib4-modules-used-in-fep_formal}

Each canonical body declares the narrow Mathlib modules it needs; the generated
coverage map records distinct modules and topic-to-import edges. The metadata
`mathlib` field is a navigation hint and is not accepted as import evidence.

`LeanVerifier` writes only transient `_verify_*.lean` files beneath
`lean/FepSketches/`; these are removed after each compilation.

## Gaussian conditioning against Mathlib {#gaussian-conditioning-gap-memo}

Gap memo for LEAN-14, probed against the pinned Mathlib under
`lean/.lake/packages/mathlib`. Verdict: the algebraic (precision and
covariance) route is feasible and is implemented in
`gaussian_precision_conditioning.lean`; the generic measure-level conditional
statement is a Mathlib gap.

| Need | Status in pinned Mathlib |
| --- | --- |
| Multivariate Gaussian law `multivariateGaussian μ S`, covariance entries, marginal restriction | Present (`Gaussian/Multivariate.lean`) |
| Uncorrelated jointly Gaussian coordinates are independent | Present (`HasGaussianLaw/Independence.lean`), unconditional only |
| Block inverses, `det_fromBlocks₁₁/₂₂`, `invOf_fromBlocks₁₁_eq/₂₂_eq`, `inv_fromBlocks_zero₂₁_of_isUnit_iff` | Present (`SchurComplement.lean`) |
| `PosSemidef.fromBlocks₁₁/₂₂` (positivity iff Schur complement) | Present (`PosDef.lean`), semidefinite only |
| Principal submatrix and inverse of a `PosDef` matrix are `PosDef` | Present (`PosDef.submatrix`, `PosDef.inv`) |
| `condIndepFun` and `condDistrib` characterisations | Present (`Independence/Conditional.lean`) |
| Schur complement of the inverse equals inverse of the principal block (`Σ_xx - Σ_xb Σ_bb⁻¹ Σ_bx = (K_xx)⁻¹`) | Missing; proved here, about 40 lines |
| Gaussian conditional kernel (`condDistrib` of a Gaussian given a coordinate block is Gaussian with Schur-complement covariance) | Missing; estimate several hundred lines (disintegration plus affine-shift decomposition) |
| Gaussian conditional independence from block-sparse precision | Missing; follows from the previous row, same size class |
| Block-diagonal covariance of a Gaussian gives independence of blocks (vector-valued) | Partly present (`diagonalStrongDualProd`); not stated for conditionals |

FORM-S14 therefore proves the dimension-generic statement at the algebraic
level (conditional precision is the interior principal block, conditional
covariance is its inverse, and its external--internal cross block vanishes
exactly when `K_{ei} = 0`), recovers the fixed Fin4 theorem as an instance next
to the existing measure-level `external_condIndep_internal_given_blanket`, and
supplies a non-sparse countermodel. The measure-level generic theorem waits on
the Gaussian conditional kernel rows above. These declarations live in
`FEPComposed.GaussianBlanket` inside `compositions/native_blanket_transfer.lean`,
because the Gaussian carrier modules they build on are hash-frozen by the H3
custody record.

The topic projection is split into manifest-owned modules under
`lean/FepSketches/families/`. Their public topic names are unchanged;
`fep_all.lean` is an import-only compatibility aggregate. Composition leaves
import the families they actually reference. The generator's `--check` covers
every shard as well as the aggregate and rejects unexpected or unsafe outputs.

The [family-shard scope and local measurement](../specs/lean-family-shards/README.md)
records the reversible public-declaration experiment and its limits.
