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
| CUR-08 | Refresh the H3 native export (293 sources, 24 roles/33 supplements/12 witnesses) and obtain three independent proof-role reviews. | `gh issue view 55 --repo ActiveInferenceInstitute/fep_formal --json state -q .state` prints `CLOSED` | CUR-05, CUR-06, CUR-07 | P1 | [Issue #55](https://github.com/ActiveInferenceInstitute/fep_formal/issues/55); [`specs/comprehensive-science-improvement/NEXT.md`](specs/comprehensive-science-improvement/NEXT.md) |
| CUR-09 | Execute the frozen H3 primary exactly once and replay all 42 arrays and control results, including governed scientific rejection. | `gh issue view 56 --repo ActiveInferenceInstitute/fep_formal --json state -q .state` prints `CLOSED` | CUR-08 | P1 | [Issue #56](https://github.com/ActiveInferenceInstitute/fep_formal/issues/56); [`specs/comprehensive-science-improvement/PROTOCOL.md`](specs/comprehensive-science-improvement/PROTOCOL.md) |
| CUR-10 | Close outcome claims, study archive parity and clean installed 42-array reproduction across three outcome reviews. | `gh issue view 57 --repo ActiveInferenceInstitute/fep_formal --json state -q .state` prints `CLOSED` | CUR-09 | P1 | [Issue #57](https://github.com/ActiveInferenceInstitute/fep_formal/issues/57); [`specs/comprehensive-science-improvement/NEXT.md`](specs/comprehensive-science-improvement/NEXT.md) |
| CUR-12 | Refresh optional strict Hermes/OpenGauss evidence for all 168 topics under an authorized spend ceiling. | `gh issue view 50 --repo ActiveInferenceInstitute/fep_formal --json state -q .state` prints `CLOSED` | Secure current credential/model route and concrete spend boundary | P2 | [Issue #50](https://github.com/ActiveInferenceInstitute/fep_formal/issues/50); [`docs/configuration.md`](docs/configuration.md) |
| CUR-14 | Audit all nine original criteria and close the exact FORM-1–FORM-3 semantic/native/axiom boundaries at final source. | `gh issue view 59 --repo ActiveInferenceInstitute/fep_formal --json state -q .state` prints `CLOSED` | CUR-05, CUR-06, CUR-07, CUR-10 | P1 | [Issue #59](https://github.com/ActiveInferenceInstitute/fep_formal/issues/59); [`specs/comprehensive-science-improvement/SCOPE-2026-10-08.md`](specs/comprehensive-science-improvement/SCOPE-2026-10-08.md) |
| CUSTODY-GNN-1 | Re-freeze the FEP↔GNN source pair at GNN `v5.1.0` (`75c834bd`), re-emit both documents and dispatch the qualification workflow. The reader cutover is delivered: the pin's `gnn` record is sealed at `v5.1.0` and `bash scripts/gate.sh gnn` runs the shared `gnn.importers` check from that revision. Still open: the `fep_lean` record, whose `uv.lock` already failed `bridge status` before the cutover (on 2026-11-12 the other 318 `fep_lean` owner digests still matched and `uv.lock` alone did not), the emitted projections that remain those of `2778e65c`, and the dispatch. | `gh issue view 244 --repo ActiveInferenceInstitute/fep_formal --json state -q .state` prints `CLOSED` | GNN `v5.1.0` tag — met; remaining: one pair-wide `bridge pin`, `emit` for both models, then dispatch, which the organisation's Actions billing lock currently blocks before any job starts | P2 | [Issue #244](https://github.com/ActiveInferenceInstitute/fep_formal/issues/244); [`docs/design/gnn-bridge/README.md`](docs/design/gnn-bridge/README.md); [`.github/workflows/source-pair-qualification.yml`](.github/workflows/source-pair-qualification.yml) |
| FORM-D2 | State an explicit infinite fixed-truth law with prefix/native equality and an actual convergence proof, without disturbing the current H3 seeds. | `gh issue view 70 --repo ActiveInferenceInstitute/fep_formal --json state -q .state` prints `CLOSED` | CUR-10 | P2 | [Issue #70](https://github.com/ActiveInferenceInstitute/fep_formal/issues/70); [`docs/design/fep-research-program/next-improvements.md`](docs/design/fep-research-program/next-improvements.md) |
| CORE-J1 | Provide equivalent Windows capture custody and process supervision, with the seven-stage acceptance yielding identical valid archives. | `gh issue view 66 --repo ActiveInferenceInstitute/fep_formal --json state -q .state` prints `CLOSED` | CUR-05, CUR-06, CUR-07 | P2 | [Issue #66](https://github.com/ActiveInferenceInstitute/fep_formal/issues/66); [`docs/release.md`](docs/release.md) |
| CORE-J2 | Deliver measured incremental capture and a bounded resource lifecycle with exact dependency invalidation and closed-owned receipts. | `gh issue view 67 --repo ActiveInferenceInstitute/fep_formal --json state -q .state` prints `CLOSED` | CUR-05, CORE-D1 | P2 | [Issue #67](https://github.com/ActiveInferenceInstitute/fep_formal/issues/67); [`docs/release.md`](docs/release.md) |
| FORM-J1 | Establish observation-dependent finite-horizon control on one carrier with Bellman/native cost equality and exact two-step recovery. | `gh issue view 71 --repo ActiveInferenceInstitute/fep_formal --json state -q .state` prints `CLOSED` | CUR-10 | P2 | [Issue #71](https://github.com/ActiveInferenceInstitute/fep_formal/issues/71); [`docs/design/fep-research-program/next-improvements.md`](docs/design/fep-research-program/next-improvements.md) |
| FORM-J2 | Lift the generator to a path with an explicit library stop gate, semigroup compatibility and actual path construction. | `gh issue view 72 --repo ActiveInferenceInstitute/fep_formal --json state -q .state` prints `CLOSED` | CUR-10 | P2 | [Issue #72](https://github.com/ActiveInferenceInstitute/fep_formal/issues/72); [`docs/design/fep-research-program/research-contract.md`](docs/design/fep-research-program/research-contract.md) |
| FORM-S14 | Land the algebraic dimension-generic Gaussian Markov blanket statement with its Fin4 instance and countermodel on `main`. | `gh issue view 97 --repo ActiveInferenceInstitute/fep_formal --json state -q .state` prints `CLOSED` | Mathlib Gaussian conditional kernel ([gap memo](docs/lean4.md#gaussian-conditioning-gap-memo)), FORM-D3 | P2 | [Issue #97](https://github.com/ActiveInferenceInstitute/fep_formal/issues/97); [`docs/lean4.md`](docs/lean4.md) |
| LEAN-2 | Collapse the duplicate Gaussian Markov semigroup names to one interface while preserving `#print axioms` and the H3 declaration names. | `gh issue view 100 --repo ActiveInferenceInstitute/fep_formal --json state -q .state` prints `CLOSED` | Independent | P2 | [Issue #100](https://github.com/ActiveInferenceInstitute/fep_formal/issues/100); [`docs/lean4.md`](docs/lean4.md) |
| LEAN-4 | Split `h3_case_study.lean` and retire its maxHeartbeats override with no `set_option` left in the formal tree. | `gh issue view 102 --repo ActiveInferenceInstitute/fep_formal --json state -q .state` prints `CLOSED` | CUR-08 | P2 | [Issue #102](https://github.com/ActiveInferenceInstitute/fep_formal/issues/102); [`docs/lean4.md`](docs/lean4.md) |

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
