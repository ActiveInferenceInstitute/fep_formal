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
| CUSTODY-GNN-1 | Re-freeze the FEP↔GNN source pair after GNN `448bee6d`, re-emit both documents and dispatch the qualification workflow. | `gh issue view 244 --repo ActiveInferenceInstitute/fep_formal --json state -q .state` prints `CLOSED` | Next GNN `v[0-9]*` tag or explicit source-pair qualification dispatch, after GNN content settles | P2 | [Issue #244](https://github.com/ActiveInferenceInstitute/fep_formal/issues/244); [`docs/design/gnn-bridge/README.md`](docs/design/gnn-bridge/README.md); [`.github/workflows/source-pair-qualification.yml`](.github/workflows/source-pair-qualification.yml) |
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

## Original requirement coverage and closure

| Original criterion | Required open gates |
| --- | --- |
| 1 — truthful static status | CUR-06, CUR-14 |
| 2 — actual package support | CUR-06, CUR-07 |
| 3 — docs and accepted render | CUR-07 |
| 4 — strict capture/archive parity | CUR-03, CUR-05 |
| 5 — information identity/coarsening | CUR-07, CUR-14 |
| 6 — relative-support/native information | CUR-07, CUR-14 |
| 7 — genuine finite rate-distortion | CUR-07, CUR-14 |
| 8 — frozen H3 full chain | CUR-08, CUR-09, CUR-10 |
| 9 — all checks/source/remote evidence | CUR-07, CUR-14 |

An item leaves this backlog and its Issue closes only after its own
exact-current-source acceptance is retained and recorded in changelog/release
notes or accepted history. Missing, historical, partial or indirect evidence
keeps it open. Scientific null/rejection/no-go outcomes remain evidence under
their protocol; they do not authorize retries, changed gates or unsupported
success claims. Source-only approval, installation, local runtime, hosted
acceptance and live publication are separate states. Never close a broad
requirement on a subset.
