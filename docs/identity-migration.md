# FEP_Formal identity migration

Status: canonical cutover implemented locally, authorized October 27, 2026.
The [status record](identity-migration-status.md) distinguishes current local
native/software evidence from outstanding coordinated source-pair, hosted and
publication gates. This remains an unreleased source migration;
no new software version, package upload or scientific result is implied.

## Canonical interfaces and deprecated compatibility

| Interface | Canonical | Deprecated compatibility |
| --- | --- | --- |
| Project | FEP_Formal | Historical titles retain their original names |
| Repository and Python imports | `fep_formal` | `fep_lean` imports |
| Distribution | `fep-formal` | Separate metadata-only `fep-lean` dependency alias |
| Executable | `fep-formal` | `fep-lean` |
| Package execution | `python -m fep_formal` | `python -m fep_lean`; old `.cli` execution |
| Public environment settings | `FEP_FORMAL_` | Matching `FEP_LEAN_` settings |
| Base exception | `FepFormalError` | Identical `FepLeanError` alias |

Use canonical names in all new maintained code, instructions, and integrations.
Keep deprecated interfaces through the 2.x release line. Removal requires a
separately announced major release, at least two published minor releases with
the migration notice, a reviewed downstream inventory, and successful
canonical-only downstream acceptance. Elapsed time alone does not remove them.

```python
from fep_formal.catalogue import FEPTopicCatalogue

catalogue = FEPTopicCatalogue.default()
```

```bash
uv sync --locked --extra dev
uv run fep-formal catalogue
```

Catalog mode is offline and reports zero verified topics. It does not refresh
Lean, Hermes/OpenGauss, browser, or publication acceptance.

## Compatibility design

`src/fep_formal/` is the only implementation and resource owner. The legacy
import package redirects descendants to canonical module objects. Classes,
exceptions, context state, lazy exports, and imported source snapshots retain
one identity when both spellings are used. Importing an old name emits
`FutureWarning`; the old executable warns on stderr and preserves canonical
stdout and exit codes. Canonical-only use emits no deprecation notice.

Ordinary public settings resolve at call time. An explicit argument or caller
context retains its existing precedence. The canonical environment key wins
when present, including an empty value; the selected value then follows the
option's existing parsing rules. Only an absent canonical key permits legacy
fallback. Legacy-only or conflicting dual values produce warnings naming the
keys without disclosing their values. Resolution never writes to `os.environ`.

The private process-supervision protocol names
`FEP_LEAN_PROCESS_OWNER_SOCKET` and `FEP_LEAN_PROCESS_OWNER_TOKEN` remain
unchanged. They are internal lease capabilities, not public settings. Their
atomic-pair validation and the compiler's narrow child environment allowlist
remain intact. Do not invent independently mixed-prefix supervision aliases.

## Dependency and environment migration

The canonical wheel owns both import surfaces and both command entrypoints.
`compat/fep-lean/` builds a separate metadata-only wheel whose exact-version
dependency selects the canonical distribution. It owns no Python modules or
commands; uninstalling it cannot remove the canonical implementation.

The import adapter preserves module and class identity. It does not counterfeit
the old filesystem layout or distribution file roster. Callers that hardcode
`src/fep_lean/...` paths or inspect the old distribution's resource ownership
must migrate to canonical paths and `importlib.metadata.distribution("fep-formal")`.
Old `importlib.resources` package queries resolve the canonical resources.

A package rename alone does not satisfy an old `Requires-Dist: fep-lean`
constraint. Publish the transition wheel alongside the next canonical release
and update maintained downstream requirements. A dependency pinned to the old
2.1.0 code distribution still selects that historical version; the transition
does not override incompatible exact constraints. Review extras explicitly.

Existing old code wheels own paths now used by the shim and old command.
Use a fresh environment, or uninstall the old distribution **before** installing
the canonical wheel and transition wheel. Installing the new wheel first and
later uninstalling an old overlapping wheel can delete newly installed files.
Do not upgrade a shared environment without coordinating its active owner.

Restart long-lived Python processes after updating; an interpreter that already
loaded the old implementation cannot be converted safely by replacing files.

For a checkout, rebuild the editable installation with `uv sync --locked
--extra dev` in its declared Python 3.14 environment. Verify the actual resolved
interpreter, installed distribution, both command targets, and package origins;
do not rely on a directory name or a cached shell command.

Release preparation must update the canonical version, compatibility version,
and its exact dependency together with all existing release-version owners.
The source remains at the current development version until that coordinated
release operation. Do not upload a changed artifact under an already published
version. Retain the project's Python packaging floor and validator pin.

## Implementation plan and completion criteria

1. Establish baseline custody: clean initial HEAD, actual interpreter prefixes,
   current imports/commands, maintained downstream consumers, and retained-file
   hashes. Keep baseline failures and subsequent results separately.
2. Move the implementation and resources to `src/fep_formal/`. Migrate internal
   imports and paths; add lazy descendant aliases and both command forms.
   Prove object identity, lazy behavior, reload behavior, resource access,
   exception compatibility, missing-module refusal, and machine-readable output.
3. Centralize public environment aliases. Test canonical-only, legacy-only,
   equal/conflicting values, empty values, runtime changes after import, explicit
   caller context and child propagation. Preserve supervision and secret filters.
4. Update distribution metadata, package resources, typing, lock metadata,
   wheel/import tests, package coverage names, CI commands and source custody.
   Check the runtime adapter explicitly with mypy so its adjacent typing stub
   cannot hide implementation errors. Build real wheels; exercise fresh installs, explicit old-code migration,
   dependency resolution and uninstall ownership. No duplicate implementation.
5. Migrate maintained documentation and instructions; regenerate projections
   through their owners and run freshness checks. Preserve authored scientific
   statements and receipt-bound captures. Record exact residual legacy uses.
6. Update maintained GNN discovery, namespace, command and origin predicates;
   test canonical and legacy layouts and reject escaped/mixed origins. Change
   GEO_INFER only where a maintained consumer actually needs it. Preserve all
   companion source pins until a reviewed coordinated refresh.
7. Seal both implementation and shim with owner manifest v27. Prove new,
   deleted, or modified owners are detected, and old receipts cannot become
   current through aliasing. Preserve exact theorem bodies and Lean namespaces.
8. Run the [required checks](../AGENTS.md#required-checks), installed-wheel
   tests, downstream cases and negative controls. Obtain independent review.
   Record exact results, initial failures and blocked evidence planes in the
   [migration status](identity-migration-status.md).

Implementation and local software acceptance are separate from final source
pair, native and publication qualification. A required gate that has not run
remains outstanding. Integration, package publication and release acceptance
require their existing explicit source-bound workflows.

## Preserved identities and follow-through

| Retained identity | Reason and next action |
| --- | --- |
| `FepSketches`, `FEP`, `FEPComposed`, theorem/topic identifiers | Mathematical interfaces remain stable; no proof changes are required by Python naming |
| Bridge/pair JSON key `fep_lean` and companion `.github/fep-lean-pair.json` | Versioned interchange contract; new paths/hashes need explicit source-pair refresh |
| `docs/other/fep_lean/bridge-contract.md` in GNN | Companion contract location; relocate only with coordinated reader/writer change |
| Existing SQLite source tag `fep_lean` | Existing sessions must remain discoverable; a storage migration needs its own versioned policy |
| `fep-lean-evidence-bundle` and custody receipt kind strings | Historical schemas remain interpretable; changing them requires a schema migration |
| Template registration `projects/active/fep_lean` | External renderer contract; retained deliberately until a separately qualified template transition |
| `fep_lean_combined.pdf` and existing manuscript artifact stems | Published/renderer-bound artifact identities; preserve readers and retained captures |
| Retained specs, fixtures, reviews, captures and released changelog entries | Historical records retain their accepted bytes and names |

Source movement changes source digests even when mathematical statements stay
identical. Existing native, source-pair, render, browser and hosted receipts must
not be described as current for the migrated source. Obtain fresh receipts for
the exact final committed source and companion revisions; preserve old receipts
as historical. Never weaken a digest, origin predicate, coverage floor, warning
rule or acceptance roster to make a migration pass.

Reversal before integration is a reviewed reversal of this owned patch, without
resetting or overwriting unrelated work. After publication, use a forward
compatibility release and the existing release procedure. Do not rewrite
published packages, tags, proof evidence or archived receipts.


Historical custody-refresh transitions also bind physical source paths. Their
recorded old-layout owners are not aliases for the current bytes: a transition
that requires an absent historical owner refuses the migrated checkout. Do not
silently normalize those paths to make the old custody record pass. Before
using that transition for the canonical source, qualify a versioned successor
checkpoint against the final committed source, fresh native evidence and its
required render evidence. Preserve the old journals and checkpoint unchanged.
This historical transition remains a separate acceptance limitation; import
compatibility does not establish custody compatibility.


## Coordinated integration and eventual retirement

The remaining sequence has explicit dependencies:

1. Choose the next unpublished coordinated release version and update the
   canonical distribution, compatibility metadata, exact dependency, lock and
   other release owners together before sealing release evidence. Keep the
   already published 2.1.0 artifacts unchanged.
2. Review and integrate the owned changes in FEP_Formal, GNN and GEO_INFER.
   Record the exact accepted commits in each repository. Local source digests
   and unchanged baseline HEADs are not a substitute for those identities.
3. Qualify a versioned successor to any old-layout custody checkpoint before
   using its refresh transition. Preserve the historical checkpoint and decoder;
   new physical owners and fresh native/render evidence belong in a new record.
4. Refresh the explicitly named companion pairs through the
   [bridge contract](design/gnn-bridge/bridge-contract.md). Run both sides' current
   status/emission checks and the artifact-specific current-source/native
   validator. Retained Q5/Q6/Q7 evidence continues to describe its original pair.
5. Run full automatic PR and merged-main qualification plus the installed-wheel,
   publication, browser and visual gates required by the
   [release procedure](release.md). Local passing checks do not replace hosted
   role membership or independent publication acceptance. Publish only the
   exact qualified artifacts through that procedure. Any later source,
   configuration or artifact change reopens its affected gates.
6. Keep maintained consumers canonical during 2.x. In each release, recheck the
   shim's module identity, typing, resource access, warning behavior, environment
   precedence and install/uninstall ownership. Announce a future major removal
   only after the published-minor and downstream criteria above are satisfied.
7. At that major boundary, remove deprecated Python/CLI/public-environment
   adapters and the metadata transition package as one coordinated change.
   Historical receipt decoders, published filenames and Lean theorem namespaces
   require their own versioned decisions; they do not disappear automatically
   with the Python adapter.

Coordinate integration and source-pair updates through the repository process.
Package publication and historical evidence changes retain their separately
qualified release requirements.


## Hosted source-pair capture

The dispatch-only [source-pair qualification workflow](../.github/workflows/source-pair-qualification.yml)
takes explicit full `fep_revision` and `gnn_revision` SHAs. It produces
owner-generated bridge/Q7 projections, five real CPython parser observations,
and a native Q7 receipt validated on the producing host. Its execution context
records the workflow revision separately from both selected source commits.
Import its exact artifacts and verify their hashes and source binding before
committing them; retain previous receipts unchanged. Native receipts remain
bound to their recorded compiler environment. Local native currency uses a
fresh local capture and check rather than rewritten receipt paths.
