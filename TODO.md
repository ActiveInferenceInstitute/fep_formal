# FEP_Formal — canonical open backlog

Rescoped on 2026-10-06. Only open work belongs here; completed delivery and
dated acceptance belong in [CHANGELOG.md](CHANGELOG.md) and retained history.
Each linked GitHub Issue contains its owner, detailed scope, dependencies,
positive acceptance, failure controls and claim boundary. Size means
implementation scope, not a version or schedule promise.

The [2026-10-16 publication handoff](WORK_STATUS.md) records pushed work and
remaining acceptance. [PR182](https://github.com/ActiveInferenceInstitute/fep_formal/pull/182) has passed
all 15 hosted jobs and is integrated. The
[complete issue review](specs/comprehensive-next-steps/open-issue-review-20261016.md)
records implemented fixes, exact-source evidence and remaining acceptance;
backlog rows remain open until their scope is accepted.

The earlier software/proof-component checkpoint is
[PR201](https://github.com/ActiveInferenceInstitute/fep_formal/pull/201), main
`de9643f5249ad207219af51f6446327197a01247`, qualified by the
[full exact-main workflow](https://github.com/ActiveInferenceInstitute/fep_formal/actions/runs/39449116181).
The 30 first-column Issue rows account for accepted PKG-6 (#119), CORE-D2
(#65), BRIDGE-D1 (#61), CORE-M3 (#73), CORE-D3 (#74) and LEAN-12 (#110),
delivered through PR203, PR205, PR206 and PR207. Independent API/schema and semantic review are now retained for CORE-D2;
its conceptual Bernoulli relation keeps the explicit conjugate-carrier boundary.
PKG-13 remains in delivery history. FORM-D1, FORM-S3, LEAN-6, CORE-D1, PKG-7, LEAN-9, FORM-S2 and the
maintainer-closed CUR-15 remain in delivery history. This board reconciliation
supplies no new production browser or primary scientific evidence.
The subsequent [PR202](https://github.com/ActiveInferenceInstitute/fep_formal/pull/202)
advances source-pair custody only; it adds no theorem or algorithm claim.

The earlier accepted software checkpoint is
[PR206](https://github.com/ActiveInferenceInstitute/fep_formal/pull/206), main
`40856a1985065a2ca7e92950e3a29f5effa5c28a`, qualified by the
[full exact-main workflow](https://github.com/ActiveInferenceInstitute/fep_formal/actions/runs/39504371245)
and independently checked uploaded artifacts and scoped PDF review. The runner
receipt establishes the historical named pair's actual initial-Gaussian update;
current-source runner execution and OU dynamics remain separate claims. These
four closeouts supply no production browser or primary scientific acceptance.
Fresh full capture and its evidence boundaries remain in CUR-05/CUR-07.

The current accepted software checkpoint is
[PR207](https://github.com/ActiveInferenceInstitute/fep_formal/pull/207), main
`ad4569db717a7d1998141ea5d0dbd68a7f6b5b64`, qualified by the
[full exact-main workflow](https://github.com/ActiveInferenceInstitute/fep_formal/actions/runs/39532685900)
and independently authenticated uploaded artifacts and scoped direct PDF review.
Its accessible offline views and finite KL/Mathlib-only draft complete the two
additional software closeouts. All six retain their recorded scope boundaries;
full Hermes/capture, primary scientific acceptance and upstream submission are
separate requirements.

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
Fresh full capture and the closed production DOM rejection (CUR-15) retain
their own acceptance gates. H3 primary seeds remain unopened; Q7
generated-runner execution remains unverified. The
[locked protocol](specs/comprehensive-science-improvement/PROTOCOL.md) retains
all nine original criteria; the [execution sequence](specs/comprehensive-science-improvement/NEXT.md)
orders this work.

| Work | Size | Predecessors | Closure probe |
| --- | --- | --- | --- |
| [CUR-03](https://github.com/ActiveInferenceInstitute/fep_formal/issues/52) — Seal complete approved tests membership in the successor source freeze | Minor | [CUR-01](https://github.com/ActiveInferenceInstitute/fep_formal/issues/46), [CUR-02](https://github.com/ActiveInferenceInstitute/fep_formal/issues/47), [CUR-04](https://github.com/ActiveInferenceInstitute/fep_formal/issues/48), [CUR-15](https://github.com/ActiveInferenceInstitute/fep_formal/issues/51) | Exact approved full tests membership enforced before imports/planning/dispatch and at closure; nonauthor source review passes. |
| [CUR-05](https://github.com/ActiveInferenceInstitute/fep_formal/issues/53) — Accept a fresh full seven-stage capture and identical package archives | Medium | [CUR-01](https://github.com/ActiveInferenceInstitute/fep_formal/issues/46), [CUR-02](https://github.com/ActiveInferenceInstitute/fep_formal/issues/47), [CUR-03](https://github.com/ActiveInferenceInstitute/fep_formal/issues/52), [CUR-04](https://github.com/ActiveInferenceInstitute/fep_formal/issues/48), [CUR-15](https://github.com/ActiveInferenceInstitute/fep_formal/issues/51) | All seven actual stages and closing guards pass; two identical package archives independently claim-ready. |
| [CUR-07](https://github.com/ActiveInferenceInstitute/fep_formal/issues/54) — Pass every declared check and exact-SHA hosted artifact gate | Medium | [CUR-01](https://github.com/ActiveInferenceInstitute/fep_formal/issues/46), [CUR-02](https://github.com/ActiveInferenceInstitute/fep_formal/issues/47), [CUR-04](https://github.com/ActiveInferenceInstitute/fep_formal/issues/48), [CUR-05](https://github.com/ActiveInferenceInstitute/fep_formal/issues/53), [CUR-06](https://github.com/ActiveInferenceInstitute/fep_formal/issues/49) | Every applicable declared check and all same-SHA hosted jobs/artifacts validate; local and hosted evidence remain separate. |
| [CUR-08](https://github.com/ActiveInferenceInstitute/fep_formal/issues/55) — Refresh H3 native export and three independent proof-role reviews | Medium | [CUR-05](https://github.com/ActiveInferenceInstitute/fep_formal/issues/53), [CUR-06](https://github.com/ActiveInferenceInstitute/fep_formal/issues/49), [CUR-07](https://github.com/ActiveInferenceInstitute/fep_formal/issues/54) | Current 293-source export, 24 roles/33 supplements/12 witnesses and three independent proof-role reviews accepted. |
| [CUR-09](https://github.com/ActiveInferenceInstitute/fep_formal/issues/56) — Execute frozen H3 primary once and replay all 42 arrays | Major | [CUR-08](https://github.com/ActiveInferenceInstitute/fep_formal/issues/55) | Exactly one frozen primary invocation; all 42 arrays/control results retained and replayed, including governed scientific rejection. |
| [CUR-10](https://github.com/ActiveInferenceInstitute/fep_formal/issues/57) — Close outcome claims, study archive parity and clean installed reproduction | Major | [CUR-09](https://github.com/ActiveInferenceInstitute/fep_formal/issues/56) | Three outcome reviews, identical independently valid study archives and clean installed 42-array reproduction complete. |
| [CUR-14](https://github.com/ActiveInferenceInstitute/fep_formal/issues/59) — Audit all nine original criteria and final evidence boundaries | Medium | [CUR-05](https://github.com/ActiveInferenceInstitute/fep_formal/issues/53), [CUR-06](https://github.com/ActiveInferenceInstitute/fep_formal/issues/49), [CUR-07](https://github.com/ActiveInferenceInstitute/fep_formal/issues/54), [CUR-10](https://github.com/ActiveInferenceInstitute/fep_formal/issues/57) | Independent mapping closes all nine criteria and exact FORM-1–FORM-3 semantic/native/axiom boundaries at final source. |

## Separately governed lanes

These remain open and activate only on their stated conditions.
A governed empirical no-go satisfies the frozen current program. Accepted Q7
static proofs do not imply the future runner lane ran. PRs remain substantive
until a verified integration or disposition; they are not removed as legacy.

| Work | Size | Predecessors and activation | Closure probe |
| --- | --- | --- | --- |
| [CUR-12](https://github.com/ActiveInferenceInstitute/fep_formal/issues/50) — Refresh optional strict Hermes/OpenGauss evidence for all 168 topics | Medium | Secure current credential/model route and concrete spend boundary | Complete source-bound strict full-mode report for all 168 topics independently claim-ready; secure preflight and enforcement of the separately authorized spend ceiling remain required. |
| [CUR-13](https://github.com/ActiveInferenceInstitute/fep_formal/issues/58) — Review substantive PR44 against current formal and ownership contracts | Medium | [CUR-07](https://github.com/ActiveInferenceInstitute/fep_formal/issues/54) | Fresh current-base PR44 formal/ownership brief, warning-free native/axiom/projection evidence and independent domain review before integration. |
| [EMP-J1](https://github.com/ActiveInferenceInstitute/fep_formal/issues/77) — Gate future empirical work on licensed data and new immutable protocol | Major | [CUR-10](https://github.com/ActiveInferenceInstitute/fep_formal/issues/57) and named licensed data/new protocol | Verifiable license/provenance/split and independently reviewed real measurements, or retained governed no-go. |

## Upcoming minor, medium and major scopes

The [maintained research scopes](docs/design/fep-research-program/next-improvements.md)
retain the eleven existing detailed proposals; the additional bounded issues
cover configuration, accessibility, catalogue review and general finite duality.
Use the [work-package contract](docs/design/fep-research-program/research-contract.md)
before activating an implementation. Demonstrate a concrete gap first for
configuration and visualization work. New owners require a coordinated source
roster refresh; new topics are not implicitly reserved by this plan.

| Work | Size | Predecessors | Closure probe |
| --- | --- | --- | --- |
| [Issue #211](https://github.com/ActiveInferenceInstitute/fep_formal/issues/211) — Correct complete theorem statement and proof spans | Minor | Current canonical owners and installed query contract | Reviewed complete source slices, unchanged public inventory, adversarial grammar controls, deterministic projections, installed-wheel parity and actual publication evidence. |
| [CORE-M2](https://github.com/ActiveInferenceInstitute/fep_formal/issues/63) — maintain current guidance through dependency review | Minor | [CUR-04](https://github.com/ActiveInferenceInstitute/fep_formal/issues/48) | Current active reading paths, complete retirement caller inventory, strict links/hygiene/xrefs and preserved historical evidence. |
| [FORM-M1](https://github.com/ActiveInferenceInstitute/fep_formal/issues/68) — align primary theorem proxies with the proved information seams | Minor | [CUR-07](https://github.com/ActiveInferenceInstitute/fep_formal/issues/54) | Exact primary types/assumptions/non-vacuity reviewed; stable IDs/signatures and all native/axiom/boundary projections accepted. |
| [FORM-D2](https://github.com/ActiveInferenceInstitute/fep_formal/issues/70) — fixed-truth consistency for the continuous static-latent model | Medium | [CUR-10](https://github.com/ActiveInferenceInstitute/fep_formal/issues/57) | Explicit infinite fixed-truth law, prefix/native equality and actual convergence proof; new protocol preserves current H3 seeds. |
| [FORM-D3](https://github.com/ActiveInferenceInstitute/fep_formal/issues/75) — Review all 168 theorem proxies and rank substantive strengthening | Medium | [CUR-07](https://github.com/ActiveInferenceInstitute/fep_formal/issues/54), [FORM-M1](https://github.com/ActiveInferenceInstitute/fep_formal/issues/68) | All 168 proxies receive statement-based semantic review and ranked substantive proof briefs; no automatic disposition promotion. |
| [CORE-J1](https://github.com/ActiveInferenceInstitute/fep_formal/issues/66) — equivalent Windows capture custody and process supervision | Major | [CUR-05](https://github.com/ActiveInferenceInstitute/fep_formal/issues/53), [CUR-06](https://github.com/ActiveInferenceInstitute/fep_formal/issues/49), [CUR-07](https://github.com/ActiveInferenceInstitute/fep_formal/issues/54) | Equivalent Windows no-follow handle custody and descendant containment; actual seven-stage acceptance and identical valid archives. |
| [CORE-J2](https://github.com/ActiveInferenceInstitute/fep_formal/issues/67) — measured incremental capture and bounded resource lifecycle | Major | [CUR-05](https://github.com/ActiveInferenceInstitute/fep_formal/issues/53), [CORE-D1](https://github.com/ActiveInferenceInstitute/fep_formal/issues/64) | Measured full/resumed/edited capture equivalence, exact dependency invalidation and closed-owned resource receipts without weaker budgets. |
| [FORM-J1](https://github.com/ActiveInferenceInstitute/fep_formal/issues/71) — observation-dependent finite-horizon control on one carrier | Major | [CUR-10](https://github.com/ActiveInferenceInstitute/fep_formal/issues/57) | Finite-horizon measurable updates/selectors, Bellman/native cost equality, attainment/moment bounds and exact two-step recovery. |
| [FORM-J2](https://github.com/ActiveInferenceInstitute/fep_formal/issues/72) — generator-to-path lifting with an explicit library stop gate | Major | [CUR-10](https://github.com/ActiveInferenceInstitute/fep_formal/issues/57) | Pinned generator/path API stop gate, semigroup compatibility and actual path construction, or bounded upstream proposal/no-go. |
| [FORM-J3](https://github.com/ActiveInferenceInstitute/fep_formal/issues/76) — Probe general finite rate-distortion strong duality before staged proof | Major | [FORM-D1](https://github.com/ActiveInferenceInstitute/fep_formal/issues/69) | Pinned convexity/support/separation/endpoint seam passes before derived general finite duality, or explicit library no-go. |

## Scoped improvements (2026-10-08)

Filed from [SCOPE-2026-10-08.md](specs/comprehensive-science-improvement/SCOPE-2026-10-08.md). Formalism rows are
strengthening briefs that feed [FORM-D3](https://github.com/ActiveInferenceInstitute/fep_formal/issues/75); none promotes a
disposition without independent semantic review. Rows marked by their
Issue as roster-bound wait for a coordinated provenance-roster refresh.

### Formalism strengthening

| Work | Size | Predecessors | Closure probe |
| --- | --- | --- | --- |
| [FORM-S5](https://github.com/ActiveInferenceInstitute/fep_formal/issues/88) — Route the fep-050 body through the hypothesis-free Landauer bound | Minor | [FORM-D3](https://github.com/ActiveInferenceInstitute/fep_formal/issues/75) | The fep-050 body no longer carries `hsecondLaw`; it consumes `FEP.PathThermodynamics.erasure_generalized_landauer` as a reviewed body change. |
| [FORM-S10](https://github.com/ActiveInferenceInstitute/fep_formal/issues/93) — Review the fep-034↔047 relation against the delivered tree sum-product theory | Minor | [FORM-D3](https://github.com/ActiveInferenceInstitute/fep_formal/issues/75) | The `fep-034 ↔ fep-047` edge carries a dated review note; any tag change is a reviewed seal delta. |
| [FORM-S11](https://github.com/ActiveInferenceInstitute/fep_formal/issues/94) — Review the fep-071 invariant as a Bayesian update | Minor | [FORM-D3](https://github.com/ActiveInferenceInstitute/fep_formal/issues/75) | The Bayes-sound planners, fep-134 re-derivation and observation-ignoring countermodel are on `main`; an independent semantic review moves the 071 invariant from 'authored update' to 'Bayesian update'. |
| [FORM-S12](https://github.com/ActiveInferenceInstitute/fep_formal/issues/95) — Dirichlet–categorical learning, stage 2 (digamma, Dirichlet measure, variational update) | Medium | [FORM-D3](https://github.com/ActiveInferenceInstitute/fep_formal/issues/75) | Stage 1 is on `main`. A library probe like FORM-J2/J3 either starts stage 2 or records a no-go. |
| [FORM-S14](https://github.com/ActiveInferenceInstitute/fep_formal/issues/97) — Measure-level Gaussian Markov blanket from precision sparsity | Major | Mathlib Gaussian conditional kernel ([gap memo](docs/lean4.md#gaussian-conditioning-gap-memo)), [FORM-D3](https://github.com/ActiveInferenceInstitute/fep_formal/issues/75) | The algebraic dimension-generic statement, Fin4 instance and countermodel are on `main`; `K_ei = 0` implies `e ⟂ i ∣ (s, a)` as a `condIndepFun` statement for every positive-definite block precision. |
| [FORM-S15](https://github.com/ActiveInferenceInstitute/fep_formal/issues/98) — Recover the fep-163 weighted-divergence carrier from the Fokker–Planck current | Minor | [FORM-D3](https://github.com/ActiveInferenceInstitute/fep_formal/issues/75) | A qualified theorem derives the fep-163 expansion (or a stated discretisation of it) from `FEP.NessFlow.probCurrent` and `divergence`, with any pairing recorded as a reviewed relation. |

### Lean formal layer and relations

| Work | Size | Predecessors | Closure probe |
| --- | --- | --- | --- |
| [LEAN-2](https://github.com/ActiveInferenceInstitute/fep_formal/issues/100) — One Gaussian Markov semigroup interface | Medium | Independent | Duplicate names drop to one; unchanged `#print axioms`; H3 declaration names preserved. |
| [LEAN-4](https://github.com/ActiveInferenceInstitute/fep_formal/issues/102) — Split h3_case_study.lean and retire its maxHeartbeats override | Medium | [CUR-08](https://github.com/ActiveInferenceInstitute/fep_formal/issues/55) | No `set_option` in the formal tree; declaration names unchanged; native export refreshed. |
| [LEAN-5](https://github.com/ActiveInferenceInstitute/fep_formal/issues/103) — A reviewed derivational edge in every family | Medium | [FORM-D3](https://github.com/ActiveInferenceInstitute/fep_formal/issues/75) | At most six families without a `formal` edge; endpoint-qualification notes per the adjudication doc; relation tests pass. |
| [LEAN-7](https://github.com/ActiveInferenceInstitute/fep_formal/issues/105) — Obligation records for conceptual relations | Minor | Independent | A schema test requires `blocked_by` on every conceptual edge; at least one converted to a pairing (034↔047 via FORM-S10 or 016↔032). |

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
