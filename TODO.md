# FEP_Formal — canonical open backlog

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

## Release gate

Releases follow the short [release procedure](docs/release.md): one version
and date across version-bearing files, a dated changelog section, and a
successful hosted `ci.yml` run on the exact `main` commit, all checked by
`docs/release_check.py`. The untagged `1.4.0` candidate shipped in
`v1.5.0` (2026-10-06). Nothing below blocks a release.

## Evidence and research lanes

These keep their own acceptance probes and are reported in release notes, not
claimed. Hosted Chrome startup (CUR-01) passed its eight required cases on the
[accepted exact-source PR run](https://github.com/ActiveInferenceInstitute/fep_formal/actions/runs/37682721329).
The owner retired the historical private successor source-freeze and full
production-capture requirements (CUR-03/#52 and CUR-05/#53) as not planned.
Their original acceptance criteria were not met. Exact current software test
membership, source guards and release checks remain required. H3 primary seeds remain unopened; Q7
generated-runner execution remains unverified. The
[locked protocol](specs/comprehensive-science-improvement/PROTOCOL.md) retains
all nine original criteria; the [execution sequence](specs/comprehensive-science-improvement/NEXT.md)
orders this work.

| Work | Size | Predecessors | Closure probe |
| --- | --- | --- | --- |
| [CUR-08](https://github.com/ActiveInferenceInstitute/fep_formal/issues/55) — Refresh H3 native export and three independent proof-role reviews | Medium | [CUR-05](https://github.com/ActiveInferenceInstitute/fep_formal/issues/53), [CUR-06](https://github.com/ActiveInferenceInstitute/fep_formal/issues/49), [CUR-07](https://github.com/ActiveInferenceInstitute/fep_formal/issues/54) | Current 293-source export, 24 roles/33 supplements/12 witnesses and three independent proof-role reviews accepted. |
| [CUR-09](https://github.com/ActiveInferenceInstitute/fep_formal/issues/56) — Execute frozen H3 primary once and replay all 42 arrays | Major | [CUR-08](https://github.com/ActiveInferenceInstitute/fep_formal/issues/55) | Exactly one frozen primary invocation; all 42 arrays/control results retained and replayed, including governed scientific rejection. |
| [CUR-10](https://github.com/ActiveInferenceInstitute/fep_formal/issues/57) — Close outcome claims, study archive parity and clean installed reproduction | Major | [CUR-09](https://github.com/ActiveInferenceInstitute/fep_formal/issues/56) | Three outcome reviews, identical independently valid study archives and clean installed 42-array reproduction complete. |
| [CUR-14](https://github.com/ActiveInferenceInstitute/fep_formal/issues/59) — Audit all nine original criteria and final evidence boundaries | Medium | [CUR-05](https://github.com/ActiveInferenceInstitute/fep_formal/issues/53), [CUR-06](https://github.com/ActiveInferenceInstitute/fep_formal/issues/49), [CUR-07](https://github.com/ActiveInferenceInstitute/fep_formal/issues/54), [CUR-10](https://github.com/ActiveInferenceInstitute/fep_formal/issues/57) | Independent mapping closes all nine criteria and exact FORM-1–FORM-3 semantic/native/axiom boundaries at final source. |

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

## Separately governed lanes

These remain open and activate only on their stated conditions.
A governed empirical no-go satisfies the frozen current program. Accepted Q7
static proofs do not imply the future runner lane ran. PRs remain substantive
until a verified integration or disposition.

| Work | Size | Predecessors and activation | Closure probe |
| --- | --- | --- | --- |
| [CUR-12](https://github.com/ActiveInferenceInstitute/fep_formal/issues/50) — Refresh optional strict Hermes/OpenGauss evidence for all 168 topics | Medium | Secure current credential/model route and concrete spend boundary | Complete source-bound strict full-mode report for all 168 topics independently claim-ready; secure preflight and enforcement of the separately authorized spend ceiling remain required. |

## Upcoming minor, medium and major scopes

The [maintained research scopes](docs/design/fep-research-program/next-improvements.md)
retain the eleven existing detailed proposals; the additional bounded issues
cover configuration, accessibility, catalog review and general finite duality.
Use the [work-package contract](docs/design/fep-research-program/research-contract.md)
before activating an implementation. Demonstrate a concrete gap first for
configuration and visualization work. New owners require a coordinated source
roster refresh; new topics are not implicitly reserved by this plan.

| Work | Size | Predecessors | Closure probe |
| --- | --- | --- | --- |
| [FORM-D2](https://github.com/ActiveInferenceInstitute/fep_formal/issues/70) — fixed-truth consistency for the continuous static-latent model | Medium | [CUR-10](https://github.com/ActiveInferenceInstitute/fep_formal/issues/57) | Explicit infinite fixed-truth law, prefix/native equality and actual convergence proof; new protocol preserves current H3 seeds. |
| [CORE-J1](https://github.com/ActiveInferenceInstitute/fep_formal/issues/66) — equivalent Windows capture custody and process supervision | Major | [CUR-05](https://github.com/ActiveInferenceInstitute/fep_formal/issues/53), [CUR-06](https://github.com/ActiveInferenceInstitute/fep_formal/issues/49), [CUR-07](https://github.com/ActiveInferenceInstitute/fep_formal/issues/54) | Equivalent Windows no-follow handle custody and descendant containment; actual seven-stage acceptance and identical valid archives. |
| [CORE-J2](https://github.com/ActiveInferenceInstitute/fep_formal/issues/67) — measured incremental capture and bounded resource lifecycle | Major | [CUR-05](https://github.com/ActiveInferenceInstitute/fep_formal/issues/53), [CORE-D1](https://github.com/ActiveInferenceInstitute/fep_formal/issues/64) | Measured full/resumed/edited capture equivalence, exact dependency invalidation and closed-owned resource receipts without weaker budgets. |
| [FORM-J1](https://github.com/ActiveInferenceInstitute/fep_formal/issues/71) — observation-dependent finite-horizon control on one carrier | Major | [CUR-10](https://github.com/ActiveInferenceInstitute/fep_formal/issues/57) | Finite-horizon measurable updates/selectors, Bellman/native cost equality, attainment/moment bounds and exact two-step recovery. |
| [FORM-J2](https://github.com/ActiveInferenceInstitute/fep_formal/issues/72) — generator-to-path lifting with an explicit library stop gate | Major | [CUR-10](https://github.com/ActiveInferenceInstitute/fep_formal/issues/57) | Pinned generator/path API stop gate, semigroup compatibility and actual path construction, or bounded upstream proposal/no-go. |

## Scoped improvements (2026-10-08)

Filed from [SCOPE-2026-10-08.md](specs/comprehensive-science-improvement/SCOPE-2026-10-08.md). Formalism rows are
strengthening briefs following the completed [FORM-D3](https://github.com/ActiveInferenceInstitute/fep_formal/issues/75); none promotes a
disposition without independent semantic review. Rows marked by their
Issue as roster-bound wait for a coordinated provenance-roster refresh.

### Formalism strengthening

| Work | Size | Predecessors | Closure probe |
| --- | --- | --- | --- |
| [FORM-S5](https://github.com/ActiveInferenceInstitute/fep_formal/issues/88) — Route the fep-050 body through the hypothesis-free Landauer bound | Minor | [FORM-D3](https://github.com/ActiveInferenceInstitute/fep_formal/issues/75) | The fep-050 body no longer carries `hsecondLaw`; it consumes `FEP.PathThermodynamics.erasure_generalized_landauer` as a reviewed body change. |
| [FORM-S14](https://github.com/ActiveInferenceInstitute/fep_formal/issues/97) — Measure-level Gaussian Markov blanket from precision sparsity | Major | Mathlib Gaussian conditional kernel ([gap memo](docs/lean4.md#gaussian-conditioning-gap-memo)), [FORM-D3](https://github.com/ActiveInferenceInstitute/fep_formal/issues/75) | The algebraic dimension-generic statement, Fin4 instance and countermodel are on `main`; `K_ei = 0` implies `e ⟂ i ∣ (s, a)` as a `condIndepFun` statement for every positive-definite block precision. |

### Lean formal layer and relations

| Work | Size | Predecessors | Closure probe |
| --- | --- | --- | --- |
| [LEAN-2](https://github.com/ActiveInferenceInstitute/fep_formal/issues/100) — One Gaussian Markov semigroup interface | Medium | Independent | Duplicate names drop to one; unchanged `#print axioms`; H3 declaration names preserved. |
| [LEAN-4](https://github.com/ActiveInferenceInstitute/fep_formal/issues/102) — Split h3_case_study.lean and retire its maxHeartbeats override | Medium | [CUR-08](https://github.com/ActiveInferenceInstitute/fep_formal/issues/55) | No `set_option` in the formal tree; declaration names unchanged; native export refreshed. |

### Package infrastructure

| Work | Size | Predecessors | Closure probe |
| --- | --- | --- | --- |

### Documentation and manuscript

| Work | Size | Predecessors | Closure probe |
| --- | --- | --- | --- |

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

An item leaves TODO and its Issue closes only after its own exact-current-source
acceptance is retained and recorded in changelog/release notes or accepted
history. Missing, historical, partial or indirect evidence keeps it open.
Scientific null/rejection/no-go outcomes remain evidence under their protocol;
they do not authorize retries, changed gates or unsupported success claims.
Source-only approval, installation, local runtime, hosted acceptance and live
publication are separate states. Never close a broad requirement on a subset.
