# fep_formal — canonical backlog

Rescoped on 2026-10-06. Only open work belongs here; completed delivery and
dated acceptance belong in [CHANGELOG.md](CHANGELOG.md) and retained history.
Each linked GitHub Issue contains its owner, detailed scope, dependencies,
positive acceptance, failure controls and claim boundary. Size means
implementation scope, not a version or schedule promise.

The [current assessment](ISA.md#current-assessment) owns the accepted
software/proof-component checkpoint and exact-source evidence;
[CHANGELOG.md](CHANGELOG.md) owns completed delivery and acceptance history.
The [complete issue review](specs/comprehensive-next-steps/open-issue-review-20261016.md)
retains scope-specific evidence and remaining acceptance. Rows below remain
open until their exact scope is accepted; software delivery supplies no
production-capture, primary scientific or optional-provider acceptance.

The table below is the estate's canonical six-column grammar. Every row is one
linked Issue, and the repo's own closure rule makes the Issue state the probe:
an item leaves this backlog only after its exact-current-source acceptance is
retained, which is when the Issue closes. The Issue body remains the full scope;
size and predecessors are carried in the columns below.

| ID | Outcome | Acceptance probe | Dependencies | Priority | Evidence source |
| --- | --- | --- | --- | --- | --- |

As of 2026-11-16 no GitHub Issue is open, so the table has no rows. Issue #97
(FORM-S14) closed as completed; Issues #50, #55, #56, #57, #59, #66, #67, #70, #71, #72, #100
and #102 closed as not planned because their scope predates the `v2.1.0` release
and was stale; #244 (CUSTODY-GNN-1) closed as completed with
the 2026-11-16 pair-wide GNN source re-freeze recorded in
[CHANGELOG.md](CHANGELOG.md). A future item re-enters as a new linked Issue and row.

## Release gate

Releases follow the short [release procedure](docs/release.md): one version
and date across version-bearing files, a dated changelog section, and a
successful hosted `ci.yml` run on the exact `main` commit, all checked by
`docs/release_check.py`. The untagged `1.4.0` candidate shipped in
`v1.5.0` (2026-10-06). Nothing above blocks a release.

Hosted acceptance itself is currently unobtainable, and that is the one release
blocker this backlog does not own. GitHub Actions is billing-locked for the
organisation: the `ci.yml` run on `main` at `0cf22ab` concluded `failure` in four
seconds with `The job was not started because your account is locked due to a
billing issue` ([run 43258439685](https://github.com/ActiveInferenceInstitute/fep_formal/actions/runs/43258439685)),
and `docs/release_check.py --hosted` reports `hosted ci.yml run for
0cf22ab7abfb496192045159dcb9e06ace57af28: failure` while the same check without
`--hosted` passes `release v2.1.0 (2026-10-24)`. No local arm substitutes for the
hosted matrix, so the gate stays red until an organisation billing administrator
restores Actions — outside this repository.

## Retired production-capture dependencies

The original #52/#53 contracts remain historical evidence, not satisfied
predecessors. Their retirement does not supply a package or scientific receipt.
Issue #54 closed its bounded exact-source software gate at accepted main
`e8cea5b87857df94038a104fdb72459efdb783a6` ([attempt 2](https://github.com/ActiveInferenceInstitute/fep_formal/actions/runs/39877928982/attempts/2)); later source changes require fresh qualification.
Issues #68/#75 closed their bounded primary-alignment and all-168 review/ranking
scopes without promoting dispositions or implementing every roadmap proof.
Issues #55–#57 keep current
export, three proof-role reviews, the frozen sole-primary and outcome/archive
requirements. #59 keeps its independent nine-criterion audit and must report
retired criteria honestly. #66/#67 retain actual custody, containment and
fresh/resumed capture acceptance; they cannot inherit a successful capture
from the retirement. Before activating one of these dependent lanes, review
its prospective source/package prerequisite explicitly. No original freeze,
seed, failed capture or historical receipt is changed by this scope decision.
Issues #55–#57, #59, #66 and #67 closed on 2026-11-16 as not planned; their
requirements are unaccepted, not satisfied, and reopening one is a new Issue.

## Upcoming minor, medium and major scopes

The [maintained research scopes](docs/design/fep-research-program/next-improvements.md)
retain the eleven existing detailed proposals; the additional bounded issues
cover configuration, accessibility, catalog review and general finite duality.
Use the [work-package contract](docs/design/fep-research-program/research-contract.md)
before activating an implementation. Demonstrate a concrete gap first for
configuration and visualization work. New owners require a coordinated source
roster refresh; new topics are not implicitly reserved by this plan.

## Local maintenance findings (2026-11-11)

Found during the documentation completion pass and the 2026-11-12 backlog
review. These are local follow-ups, not release blockers, and are not yet linked
to a GitHub Issue; file one when the owner wants the work scheduled.

- **Ruff findings under the declared floor — resolved 2026-11-12.** `#254`
  (`cf20b97`) moved the lock's `ruff` from 0.16.1 to 0.17.3, and the gate's own
  lint commands now pass under it: `ruff check .` prints `All checks passed!` and
  `ruff format --check src tests scripts docs specs/openai-math-methods
  specs/cascadia-experiments specs/gnn-runner-execution
  specs/publication-browser-acceptance specs/identity-cutover` prints `581 files
  already formatted`. The dev extra still declares only `ruff>=0.15.0`, so the
  lock, not the floor, decides which default rule set runs. One residue: a
  whole-tree `ruff format --check .` still lists
  `specs/ci-velocity-local-cache/lean_cache.py`,
  `specs/gnn-bridge-p3-certificates/certify.py`,
  `specs/gnn-bridge-w1-bridge-operations/bridge_status.py` and
  `specs/h3-reference-study/bundle_study.py`, all outside the arm's directory
  list; widening that list would turn the arm red.
- **Coverage-table mapping corrected.** The [original requirement
  coverage](#original-requirement-coverage-and-closure) table now separates
  historical dependencies, accepted scope, and remaining owners/evidence.
  Retired CUR-03 / C02 and CUR-05 / C03 are not successful acceptance.
  Correcting this mapping does not accept any of the nine original criteria;
  their exact-current-source closure rule remains unchanged.
- **Sidecar provenance release.** `.aii/config.yaml` now records
  `provenance.current_release: v2.1.0`, matching the published 2.1.0 software
  release. The sidecar declares no `provenance.releases_manifest` because the
  repository commits no release-manifest file; add one only if the sidecar
  validator requires it.

## Original requirement coverage and closure

The owner rows this table names (CUR-08, CUR-09, CUR-10, CUR-14 and the
software/release owners) no longer have open Issues: they closed on 2026-11-16
as not planned, not as accepted. None of the nine original criteria is accepted
by that closure; each remains unmet or historical exactly as stated below until
a new Issue retains its exact-current-source evidence.

| Original criterion | Historical dependency / accepted scope | Remaining owner and exact closure evidence |
| --- | --- | --- |
| 1 — truthful static status | CUR-06 / C04 is historical provenance, not an open gate. | CUR-14 / C06 consumes current installed process, byte and mtime evidence; retain inspection-versus-execution boundaries. |
| 2 — actual package support | CUR-06 / C04 and CUR-07 / C05 retain their accepted source epochs. Historical five-local-runtime and 15-cell receipts do not certify the current matrix. | Current software/distribution owner: packaging floor >=3.11; fresh installed CPython 3.11–3.14 on Ubuntu, macOS and Windows (12 cells), exact wheel/sdist/resource membership and console behavior. CUR-14 audits the retained current-source evidence. |
| 3 — docs and accepted render | Closed CUR-07 / C05 is historical accepted scope, not an open gate. | Current documentation/render/release owner: exact-source PDF/render receipt, font and renderer identities, source/artifact manifests and applicable hosted acceptance; CUR-14 audits the evidence. |
| 4 — strict capture/archive parity | CUR-03 / C02 and CUR-05 / C03 were retired, not successfully accepted. Preserve frozen membership and failed/historical evidence. | Owner decision and evidence gap: retain the original criterion as unmet, or explicitly approve a prospective replacement and its acceptance owner. Ordinary package release and issue closure do not satisfy this criterion. CUR-14 records the resulting disposition. |
| 5 — information identity/coarsening | Historical CUR-07 / C05 evidence remains scoped to its source epoch; accepted mathematics is not reopened. | CUR-14 / C06: exact FORM-1 semantic statements, native consumers and axiom witnesses at final source, without broader scientific promotion. |
| 6 — relative-support/native information | Historical CUR-07 / C05 evidence remains provenance. | CUR-14 / C06: exact FORM-2 relative-support/native witnesses and current source identity; retain singular and support conventions. |
| 7 — genuine finite rate-distortion | Historical CUR-07 / C05 evidence and completed finite results retain their bounded scope. | CUR-14 / C06: exact FORM-3 witnesses, distinguishing feasibility, value equality, attainment and weak-dual claims rather than treating them as interchangeable. |
| 8 — frozen H3 full chain | Preserve the original freeze, carriers, protocol and unopened primary. | H00 epoch decision then CUR-08 / H01 export and distinct proof-role reviews -> CUR-09 / H02 exact-runtime inputs-only admission and one primary with all 42 arrays -> CUR-10 / H03 outcome reviews, archive parity and installed reproduction. |
| 9 — all checks/source/remote evidence | Historical CUR-07 / C05 acceptance is not current-source or remote acceptance. | CUR-14 / C06 plus the current software/release owner: exact-source checks, custody and actual required hosted acceptance. Retain the documented billing blockage until observed resolved; local success is not a substitute. |

An item leaves this backlog and its Issue closes only after its own
exact-current-source acceptance is retained and recorded in changelog/release
notes or accepted history. Missing, historical, partial or indirect evidence
keeps it open. Scientific null/rejection/no-go outcomes remain evidence under
their protocol; they do not authorize retries, changed gates or unsupported
success claims. Source-only approval, installation, local runtime, hosted
acceptance and live publication are separate states. Never close a broad
requirement on a subset.
