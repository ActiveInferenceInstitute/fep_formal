# Identity migration status

The canonical cutover is implemented across FEP_Formal, GNN and GEO_INFER.
This page records dated source checkpoints; hosted results belong to the exact
workflow run and revision, and package publication remains separate. The [migration guide](identity-migration.md)
owns the compatibility policy and remaining integration plan; the
[local evidence packet](../specs/identity-cutover/evidence/public-integration-20261028/README.md)
indexes the local results, original failures and scoped reviews by hash. Full
private execution records remain preserved locally.

## Implemented

- One implementation/resource owner, `src/fep_formal/`; canonical distribution
  and command `fep-formal`, import `fep_formal`, public settings `FEP_FORMAL_`.
- Deprecated imports and commands share canonical identity. The metadata-only
  `fep-lean` transition wheel owns no code or scripts. Compatibility remains
  through 2.x, with explicit major-release removal criteria.
- Call-time environment precedence, name-only warnings, generated legacy typing
  aliases, sealed owner manifest v27, package resources, CI, tooling, maintained
  prose and owner-generated projections are migrated.
- GNN uses canonical discovery and execution with FEP's pinned uv/Python and
  environment. GEO_INFER's maintained references are current; its seven changed
  ACT executable ASTs are unchanged. Existing pair pins remain historical.
- Strict bridge verification now preserves actual compiler warnings and rejects
  them in strict mode. Real warning probes failed before this fix and pass after it.

## Premerge local checkpoint (2026-10-27)

The measurements in this section bind the premerge source digest below; they
do not substitute for qualification of a later source checkpoint.

| Plane | Result and boundary |
| --- | --- |
| Python nonserial selection | 4065 cases: 0 failures, 0 errors, 12 skips; 91.98% line coverage passes the aggregate 89% gate |
| Isolated Chrome and joined coverage | Both actual Chrome controls pass without skips; combined 92.49% measured line coverage passes aggregate and all package floors; the original pre-Chrome output-package floor failure remains retained |
| Serial Lean tests | 479 cases: 0 failures, 0 errors, 2 skips; exact skip reasons remain in JUnit |
| Strict native CLI | 168/168 current-source topics pass; zero errors, warnings or sorry; independent typed validation is source-bound and native-claim-ready |
| Native library and audit | `lake build FepSketches` succeeds; fresh audit records 2,060 declarations, no sorryAx; diagnostic/product-law positive and false controls pass |
| Installed distribution | Real wheel/sdist, isolated install, old-code uninstall-before-upgrade, both command forms, type rejection and both uninstall orders pass; three acceptance cases |
| Static/source | Strict mypy, explicit runtime-shim mypy, Ruff, format, lock/dependencies, owner generators, pin/link/hygiene/reference and retained-artifact checks pass; initial red checks remain retained |
| Render | Fresh PDF/HTML render and strict standing receipt pass against pinned template and final native measurements; local dirty/unreleased version is visible |
| GNN | 72 discovery cases and 38 runtime cases pass; actual final backend invokes both CLI names and compiles a finite syntax/WellFormed document without warnings |
| GEO_INFER | 87 ACT cases, four selector controls and 50 broader generator cases pass; all 1,620 generated guides current; four initial import timeouts remain recorded |
| Independent review | Bounded source approval plus separate final-fixes approval; earlier blocking reports retained; neither review grants release acceptance |

Premerge executable source digest:
`dd5e950c504b8f0cf0c5f2ba8ac26f66dbd5a9fcf9d3b451f1dc64822b3cb782`.
Lean is pinned to 4.35.0 and Mathlib revision
`56a005855ea17e0b0958f73ec801ae140b0a1679`.
The native receipt and copied validation bind those exact local owners, rather
than the unchanged baseline Git HEAD. At that premerge checkpoint, full-suite-2 ended with a coverage database
open error and missing XML; it is retained as failed. Full-suite-3 was stopped
to avoid exhausting GitVault after 827 passes and two skips; it is not a full
pass. The fresh complete retry
supplies the Python result above; no partial run is counted as a full pass.
The first serial run retained one continuous-parser failure and was stopped
after 48 passes: the environment lacked the already declared `defusedxml`
development dependency. Locked development sync installed exactly that package,
real continuous extraction then succeeded, and the fresh complete serial rerun
supplies the serial result above. No source or timeout was changed to repair it.
The second complete serial run retained 88 historical-fixture failures,
389 passes and two skips. Its failures mixed sealed legacy path keys with live
canonical paths, or compared current helper bytes with a historical digest.
The corrected test-only projections preserve exact historical keys/digests,
guard the real live owners and leave production receipt validation unchanged.
Their focused negative controls, independent review and final full serial
rerun are retained separately. No mathematical body or sealed record changed.

The final custody ledger retains 1272 byte-identical historical files,
72 byte-identical formal resources and unchanged Lean literals in
23 topic-body modules. 22 generated family changes are source-path
comments only; 4 maintained historical indexes receive link-only repairs.

## Postmerge local checkpoint (2026-10-28)

The canonical implementation and the newly merged main fixes have passed a
fresh strict native CLI run for all 168 topic bodies, 4,086 Python cases
(with 10 documented skips), and both real isolated Chrome controls. Joined
line coverage is 92.50% and every package floor passes. Strict mypy, runtime
adapter mypy, Ruff, and a fresh pinned-template render/receipt check pass.
These are scoped local measurements, not full-mode or release acceptance.

Source-owner digest: `020c9930f1756ef98bbd496d49329e37d6b70b35b26f89a0e3dd759522e7c275`.

The exhaustive local serial rerun and orphan-module sweep were interrupted
and retained as incomplete. Fresh mandatory hosted native acceptance remains
required before main integration; earlier complete serial results above
remain bound to their earlier checkpoint. The initial skipped Chrome attempt
and failed package-floor result remain retained separately from the subsequent
real Chrome run.

The dispatch-only [source-pair qualification workflow](../.github/workflows/source-pair-qualification.yml)
captures shareable source pins, emissions, canonical rendering, five real
parser observations and native static Q7 evidence for two explicit source
commits. The workflow revision, selected source revisions and compiler
platform remain distinct identities. Its artifacts supply their stated
source/static-proof scope; full catalog, full mode, publication and release
use their own acceptance gates.

## Additional qualification boundaries

Source commits and coordinated integration are in progress. Package publication
is separate from these source changes.
The next release must bump both distribution versions and their exact dependency;
changed artifacts must never be uploaded as the already published 2.1.0.

The [postmerge checkpoint](../specs/identity-cutover/evidence/public-integration-20261028/postmerge-local.json)
records fresh source-pair/Q7 qualification. Full hosted PR/main contexts, the
15-cell wheel matrix and publication visual/browser gates establish their
own acceptance; these local and Q7 records do not replace them. Historical custody transitions that require old physical
source owners still refuse this checkout; they require a versioned successor
checkpoint. Local render acceptance does not close those gates. The serial
whole-catalog pytest producer is deliberately skipped locally because the
separate strict CLI already compiled all 168 bodies; no CI producer execution
is claimed. Heavy opt-in probes retain their existing selection rules.

No Hermes/OpenGauss full run, new scientific result, general semantic
equivalence or release acceptance follows from this migration. Preserved Lean
namespaces, receipt keys, database source tags, renderer registrations and
published artifact stems remain deliberate compatibility identities.
