# Horizon 3 case study: H3.G0 record, frozen typed chain, and H3.6S feasibility spike

Status: **H3.G0 selection recorded (branch: continuous); frozen typed chain
recorded; H3.6S synthetic-recovery feasibility spike executed (decision:
pass). No acceptance or exit-gate verdict is issued here — independent claim
review is the next phase, and the open items in the last section are exactly
what that review must adjudicate.** Base: `research/h3-case-study` @
`b992032` (isolated worktree), rebased onto origin/main `32258cf` on
2026-09-11 with a final-tree spike refresh (see "Final-tree spike refresh"
below). Last updated: 2026-09-11.

This spec executes the opening of the preregistered
[Horizon 3 protocol](../../docs/design/fep-research-program/horizon-3-scientific-case-study.md)
(`FEP-H3-SCIENCE`). It mutates no carrier, no Lean source, and no receipt.
All work is python-side read-only inspection plus one slice-local executable
under this directory. Lean compilation, H3.0 preregistration freezing, and any
H3.6E real-data branch remain closed.

## H3.G0 — read-only carrier acceptance and branch selection

### Selection

**Exactly one branch is recorded: `continuous`** — the exact H2.5
symmetric-precision `Fin 4` linear-Gaussian/OU carrier
(`FEP.Fin4GaussianSemigroup`), pulled back through `Axis ≃ Fin 4` in the
scientific order `external ↦ 0, sensory ↦ 1, active ↦ 2, internal ↦ 3`.

The finite H1 branch is **not selected**; it retains its negative-control role
with all covariance, diffusion, and continuous-time claims mechanically
excluded had it been chosen.

Selection inputs (`specs/h3-case-study/pre-outcome-metadata.json`):
`outcomes_accessed: false`; no external dataset, license, or protected outcome
was read; the basis is the accepted H2 source-bound carrier evidence and the
protocol's preregistered continuous draft.

### Continuous-branch evidence (read-only inspection, live digests)

Each criterion of the draft preregistration
(horizon-3-scientific-case-study.md:571-612) resolves at the live bytes of
`b992032` for the carrier sources:

1. **Exact Fin 4 carrier** — `src/fep_lean/formal/fin4_gaussian_semigroup.lean`
   (sha256 `d8d15d0abdfe6eb5…`, byte-identical to its
   `lean/FepSketches/` projection):
   `axisFin_order` (:54, external↦0/sensory↦1/active↦2/internal↦3), exact `K`
   (:85-117) with `K_posDef` (:118), covariance derived as the inverse with
   `K_mul_Sigma` (:247), `Sigma_mul_K` (:252), exact rational entries in
   `Sigma_eq_entries` (:257-274), `Sigma_isSymm` (:302), `Sigma_posDef`
   (:308). No arbitrary Hurwitz matrix and no stored covariance.
2. **Transition and semigroup** — `transition_apply` (:374),
   `transition_zero` (:397), `transition_add` (:403), `transition_mean`
   (:440), `transition_covariance` (:452),
   `transitionCovariance_posSemidef` (:354), `transitionCovariance_posDef`
   (:364).
3. **Stationarity and convergence** — `stationaryLaw_eq_gaussian` (:427),
   `stationaryLaw_invariant` (:432),
   `transitionProbability_tendsto_invariant` (:478),
   `integral_transition_tendsto_invariant` (:486); terminal export
   `exactFin4Carrier` (:863).
4. **Scalar specialization, exactly and not by shape** —
   `scalarParameters_exact` (:680, rate 2 and diffusion variance rate 2 both
   `rfl`), `projectedTransition_eq_scalarOU` (:838), against the accepted
   scalar owner (`src/fep_lean/formal/scalar_gaussian_semigroup.lean`,
   source-bound in the terminal receipt's native map).
5. **Conditioning/precision seam** —
   `src/fep_lean/formal/gaussian_precision_conditioning.lean`
   (sha256 `be51dc0c06c28ee…`): `stationaryPartition_eq_compProd` (:769),
   `endpointCondDistrib_ae_eq_product` (:800),
   `externalConditionalKernel_mean` (:209),
   `externalConditionalKernel_variance` (:215, exactly 1/4),
   `external_condIndep_internal_given_blanket` (:869),
   `stationary_external_internal_covariance` (:902, exactly 1/24),
   `precisionZero_covarianceNonzero_condIndep` (:915),
   `perturbedEndpoint_external_internal_covariance` (:959, exactly −1/15),
   `perturbedEndpoint_external_not_indep_internal` (:985).
6. **H2.7 exit acceptance** —
   `specs/done/horizon-2-smooth-stochastic/readiness/terminal-acceptance.json`
   (sha256 `ad097e791e3f474d…`): `gate: H2.7`, `decision: accepted`, exactly
   three independent source-bound reviews (`lean`, `domain`, `skeptical`,
   all `approve`), the frozen 1771-node collection pin
   (`CAPTURED_COLLECTION_SHA256` matches the retained artifact), and 6 of 7
   predecessor records fully binding. Both terminal exports resolve:
   `smoothReferenceKernel_terminal`
   (`compositions/smooth_reference_kernel.lean:636`) and
   `fin4ReferenceKernel_terminal` (:768). The live recompute of the two H2
   diagnostics (`diagnostic_record`) evaluates green at the live bytes: every
   `NumericalCheck` accepted, boundaries observed, exact predicates
   (marginal endpoint covariance 1/24, conditional covariance 0, conditional
   variance 1/4, perturbed −1/15).

All 32 `G0_DECLARATIONS` names
(`src/fep_lean/verification/horizon_acceptance.py:113-152`) are present as
`theorem` declarations in the live carrier sources, and the three carrier
files are byte-bound to the terminal receipt's native source map.

### Finite-branch check (not selected)

The repaired H1.8 terminal carrier exists:
`FEPComposed.FiniteReferenceAgent.finiteReferenceAgent_terminal`
(`src/fep_lean/formal/compositions/finite_reference_agent.lean:360`); the H1
record is accepted and complete with independent reviews
(`specs/done/horizon-1-finite-synthesis/README.md:3,136-147`) and retains the
public first-merge no-go (`README.md:95-96`). It is not selected: the
continuous branch is the preregistered primary whose carrier evidence
resolves, and finite consideration under the existing contract
(`specs/h3-reference-study/README.md:29-31`) requires a separate H1
no-go/repair evidence review that has not been performed. Selecting it would
also mechanically exclude every covariance, diffusion, and continuous-time
claim — strictly weaker than the resolvable continuous evidence.

### The precise residual (reviewer item — not adjudicated here)

`validate_terminal_acceptance` does **not** revalidate end-to-end on the live
tree. Byte-exact binding holds for every Lean carrier source, carrier test,
spike, and 146 of 147 native-map files. The residual, fully enumerated:

- **`current_sources` (5 files)** — `src/fep_lean/verification/
  horizon_acceptance.py` (the W2 G0 machinery itself was added after the
  seal), `src/fep_lean/catalogue/registry.py`,
  `src/fep_lean/catalogue/latex.py`, `src/fep_lean/formal/declarations.py`,
  `src/fep_lean/lean_source.py`: changed by the reviewed scope-wave2
  hardening commits (`5fc0246` SC-6, `eb1cf42` SC-8, `5bf490c` SC-35)
  **after** the receipt was sealed at `f335724`.
- **`tests/conftest.py`** (native map) — changed at `740b595` (scope-wave2
  acceptance marker filter + xdist guard).
- **Diagnostics** — the retained diagnostics artifact is intact (hash
  matches), but its content no longer equals the live recompute, a direct
  consequence of the hardened validator inputs above.
- **One predecessor record** —
  `readiness/repairs/07-gaussian-vfe-natural-gradient.json` no longer binds
  its own captured maps for `src/fep_lean/formal/manifest.py` (last changed
  at `0b5d01e`, 2026-09-04, ~9h **before** the `f335724` seal) and
  `tests/test_horizon2_gaussian_vfe_readiness.py` (last changed at the seal
  commit `f335724` itself; `git log f335724..32258cf` over both paths is
  empty) — a captured-map staleness relative to record capture, not a
  post-seal drift wave. The other six predecessor records bind.

By the terminal contract's own rule ("changes to the bound sources invalidate
acceptance until new evidence is reviewed and sealed",
`terminal-acceptance-contract.md:6-7`), the H2.7 exit acceptance is
**structurally accepted but not revalidatable by source digest** at
`b992032`. Consequently the W2 eligibility validator
(`specs/h3-reference-study/eligibility.py`) fails on the live tree with
exactly `{"status": "error", "error": "current validator/diagnostic source
mismatch"}` (captured during this study, read-only). Re-sealing that receipt
is a `--write` lane on H2 evidence owned by the H2.7 re-seal backlog row
(`FEP-H27-RESEAL` in [TODO.md](../../TODO.md)), not by this study; the
broader Python-acceptance plane was re-bound by the coordinated refresh
completed deterministically on 2026-09-12 (recorded in
[CHANGELOG.md](../../CHANGELOG.md)). No Lean carrier source
drifted: the residual is confined to post-seal python-side harness files.

## Frozen typed chain (consumed by this study)

All rows are source-bound at `research/h3-case-study @ b992032`. Statuses
follow the protocol's claim-matrix vocabulary.

| # | Typed claim | Status | Source (file:line) |
| --- | --- | --- | --- |
| C1 | `K` symmetric positive-definite; `Sigma = K⁻¹` with 16 exact entries; `Sigma` symmetric/PD | proved | fin4_gaussian_semigroup.lean:118/247/252/257-274/302/308 |
| C2 | Exact transition kernel with Chapman–Kolmogorov (`transition_add`), zero-slice identity, mean/covariance laws, PSD/PD finite-time covariance | proved | fin4_gaussian_semigroup.lean:374/397/403/440/452/354/364 |
| C3 | Stationary Gaussian law exists, is invariant, and attracts every transition weakly; terminal export `exactFin4Carrier` | proved | fin4_gaussian_semigroup.lean:427/432/478/486/863 |
| C4 | Scalar OU specialization exact: all-ones eigenmode rate 2, diffusion variance rate 2 | proved | fin4_gaussian_semigroup.lean:680-683/838-841 |
| C5 | Blanket-partition factorization of the stationary law (native conditioning) | proved | gaussian_precision_conditioning.lean:769/800 |
| C6 | External ⊥ internal given (sensory, active); conditional variance 1/4; marginal covariance 1/24 ≠ 0 with precision entry 0 | proved | gaussian_precision_conditioning.lean:869/215/902/915; fin4_gaussian_semigroup.lean:313/317 |
| C7 | Precision-zero ⇒ CI is non-generic (perturbed witness: covariance −1/15, non-independence) | proved | gaussian_precision_conditioning.lean:959-961/985-988 |
| C8 | One-step finite control: Gaussian closed-form risk, finite attainment, native-posterior selector agreement | proved | compositions/gaussian_control.lean:228/291/303 |
| C9 | Scalar OU KL-to-stationary non-increase (path-law information layer) | proved | retained H2.6c/H2.5a owners (source-bound in terminal receipt) |
| C10 | VFE/natural-gradient terminal (scalar and Fin4 exports) | proved (H2.7 exit) | compositions/smooth_reference_kernel.lean:636/768; terminal receipt |
| A1 | Synthetic generator = the formal model (linear, Gaussian, symmetric-positive precision, dimensionless standardized state, stationarity) | assumed (by construction, synthetic-only) | this spec; protocol boundary list :667-683 |
| A2 | Positive affine raw-unit bridge `(x_raw − b)/s`, `s > 0` | assumed; exercised only as a rejection boundary (no raw data in this opening) | protocol :231-249 |
| R1 | Data satisfy linear-Gaussian/OU dynamics on the selected axes | not applicable yet (no real data; H3.0 closed) | protocol :658 |

Excluded from the H3 foundation per protocol (:84-88, :197-199):
`FepSketches.gaussian_information_geometry`, `FepSketches.posterior_convergence`,
`FepSketches.controlled_markov`, and the finite `FepSketches.markov_blanket`
owner enter only, if ever, through the H3 composition leaf's explicit
imports — never through an unnamed coercion.

Frozen tolerances for the executable (preregistered before the first
recovery run, hard-coded in the spike): rate relative error ≤ 5%;
reconstructed-`K` max-entry error ≤ 0.2; diffusion rate |r̂−2| ≤ 0.25;
recognition coefficients ±0.02; residual variances ±0.03; intercepts ±0.02;
float semigroup/stationarity/projection ≤ 1e-12; misspecification excess
≥ 0.005. Seeds `20260911`; 200,000 i.i.d. stationary pairs per setting;
sampling intervals Δ = 0.25 (setting A) and 0.5 (setting B).

## H3.6S — synthetic recovery feasibility spike

Single executable: `specs/h3-case-study/h3_reference_study_spike.py`
(slice-local per the per-PR tooling rule; promotion into
`src/fep_lean/verification/h3_reference_study.py` with
`tests/test_h3_reference_study.py` remains the orchestrator-owned H3.6S
step). It consumes exported typed parameters mirrored exactly from the Lean
declarations (with file:line citations in the source) and theorem-owned
equations — no model registry. Retained receipt:
`specs/h3-case-study/spike-receipt.json` (byte-reproducible; rerun is
byte-identical).

### Exact fixture round-trip (all exact, rational arithmetic)

- `Sigma = K⁻¹` equals the 16 named entries of `Sigma_eq_entries`; `K·Σ = I`.
- `K·v = λ·v` exactly for the four eigenmodes (rates 2, 4, 4, 6).
- Seam: `K[external, internal] = 0`; `Σ[external, internal] = 1/24`;
  endpoint-conditional covariance 0 and conditional variance exactly 1/4;
  perturbed endpoint covariance exactly −1/15.
- Stationary reconstruction from the rates:
  `Σ = Σ_m (1/λ_m)·v_m v_mᵀ/‖v_m‖²` with squared norms (4, 2, 2, 4) —
  exact.
- Float theorem mirrors: semigroup composition error 3.5e-18, stationary
  covariance error 5.6e-17, all-ones scalar projection error 0.0 (tolerance
  1e-12; mirrors `transition_add`, `stationaryLaw_invariant`,
  `projectedTransition_eq_scalarOU`).

### Two identifiable synthetic settings (frozen tolerances)

| Quantity | Setting A (Δ=0.25, sensory+active observed) | Setting B (Δ=0.5, sensory observed) | Frozen tolerance |
| --- | --- | --- | --- |
| Eigenmode rates vs (2, 4, 4, 6) | max rel. err 1.17% | max rel. err 4.25% | ≤ 5% |
| Reconstructed `K̂` max-entry error vs `K` | 0.0415 | 0.1829 | ≤ 0.2 |
| Diffusion rate vs 2 | [1.9971, 2.0271, 2.0008, 2.0084] | [2.0975, 2.0332, 2.0169, 1.9826] | ±0.25 |
| Recognition coefficients | [0.25336, 0.24854] vs (1/4, 1/4) | [0.28521] vs 2/7 ≈ 0.285714 | ±0.02 |
| Conditional intercept | 0.00057 | 0.00040 | ±0.02 |
| Residual variance vs theorem value | 0.25015 vs 1/4 | 0.26877 vs 15/56 | ±0.03 |

All setting gates pass. The recognition map is the exact Gaussian
conditional-mean structure of the H2.5d seam: on the exact carrier,
regressing external on (sensory, active) must recover coefficients (1/4, 1/4)
with residual variance 1/4, and external on sensory alone must recover 2/7
with residual 15/56 — both derived from the named Σ entries and recovered
from synthetic data inside the frozen tolerances.

### Mandatory rejection boundaries (all fire)

- **R1 reordered parameters**: the all-ones mode paired with rate 6 fails the
  exact eigenmode relation (`K·ones = 2·ones`); an external↔sensory axis
  transposition breaks the named covariance and the `K[external, internal]=0`
  seam — both rejected.
- **R2 missing units**: raw-unit input without calibration, or with zero or
  negative scale, rejected; the exact forward/inverse affine round trip holds
  for positive scales.
- **R3 stale digests**: the executable pins the sha256 of the three carrier
  sources, the filter/control composition owners, and the H2.7 terminal
  receipt; a tampered-source probe is rejected (`stale source digest: …`),
  while the live tree passes all six pins.

### Negative control (misspecification is detectable)

Recognizing internal from external while assuming covariance zero because the
precision entry is zero — exactly the protocol's rejected covariance-zero
substitute for the precision-zero seam — costs exactly 1/168 of MSE in law
(optimal residual 2/7 with coefficient 1/7 vs zero-covariance MSE 7/24,
since the marginal covariance is exactly 1/24). Observed: excess MSE 0.006028
(frozen detection threshold 0.005), fitted coefficient 0.143895 vs 1/7. The
control is detected; the seam's nonzero marginal covariance is real signal.

### Decision recorded by the executable

`decision: "pass"` — fixture, settings, rejections, and negative-control
gates all pass. This is a **feasibility** receipt under the non-proof
numerical-witness discipline. It is not an H3.6S acceptance verdict, not a
full H3.6S implementation, not observed-data calibration, and not an
empirical claim.

## What was created on this branch

- `specs/h3-case-study/pre-outcome-metadata.json` — G0 pre-outcome record
  (eligibility-contract schema).
- `specs/h3-case-study/h3_reference_study_spike.py` — the frozen
  feasibility spike (single executable; digests pinned; deterministic).
- `specs/h3-case-study/spike-receipt.json` — the machine-readable run
  receipt (byte-identical across reruns).
- This README.

Nothing outside `specs/h3-case-study/` was modified. Scoped checks run for
this slice only: `ruff check`/`ruff format --check` and `mypy` on the spike
file (clean), the deterministic rerun, the live-tree digest proof, and the
tampered-digest rejection proof.

## Open items for independent claim review (hard-stop boundary)
No acceptance or exit-gate verdict is issued here. The reviewer must check:

1. **H2.7 receipt residual** — adjudicate whether the continuous-branch G0
   selection stands on the carrier-bound evidence (every Lean carrier source
   binds exactly; diagnostics recompute green) while the python-side source
   drift — exactly five `current_sources` files (latex.py, registry.py,
   declarations.py, lean_source.py, horizon_acceptance.py) plus
   tests/conftest.py in one R0 map, with the two stale-captured-map files in
   the 07 predecessor record being record staleness rather than post-seal
   drift — is re-sealed under the durable owner row `FEP-H27-RESEAL`
   (main-tree TODO.md; acceptance probe: `validate_terminal_acceptance`
   passes at the live tree with the receipt claim-ready), or whether the
   H2.7 re-seal must precede G0 acceptance. The no-go alternative (switching
   to the finite branch) is not evidence-improving: the H1.8 exit has no
   current digest-bound exit receipt, and finite consideration requires a
   separate review that does not exist.
2. **W2 G0 machinery** — confirm the captured validator failure
   (`current validator/diagnostic source mismatch`) is the same residual as
   the Python-acceptance plane remainder that the coordinated refresh
   completed deterministically on 2026-09-12 re-bound (recorded in
   [CHANGELOG.md](../../CHANGELOG.md)), and that no
   carrier repair is implied.
3. **Spike promotion** — the feasibility spike is slice-local under
   `specs/h3-case-study/`; promoting it into
   `src/fep_lean/verification/h3_reference_study.py` with
   `tests/test_h3_reference_study.py` is an owner-manifest (v17) change
   requiring coordinated custody (`AGENTS.md` source-owner roster), not a
   per-PR append.
4. **H3.0 is not frozen** — no real-data preregistration exists; the dashed
   H3.6S→H3.6E unlock remains closed; any H3.0 freeze must reuse this G0
   record's hash and re-adjudicate item 1 first.
5. **Frozen-tolerance calibration** — tolerances were sized analytically
   before the first run and were never exercised beforehand; the reviewer
   should confirm they are appropriately strict for the full H3.6S protocol
   (observed margins: setting A comfortable; setting B K̂ error 0.1829
   against the frozen 0.2 limit is the tightest margin, driven by the
   Δ=0.5 fast-mode eigenvalue conditioning).
6. **Negative-control margin** — the frozen detection threshold 0.005 sits
   below the exact excess 1/168 ≈ 0.005952 with ~17% headroom; the reviewer
   should confirm threshold and control design before the full H3.6S freeze.
7. **Digest re-pinning** — the spike pins six source digests at `b992032`;
   any rebase, re-pin, or receipt re-seal invalidates them and requires a
   new frozen run (the executable rejects stale digests by construction).

## Final-tree spike refresh (2026-09-11)

The branch was rebased onto origin/main `32258cf` (the wave-2 evidence
refresh: custody re-seals, gnn-input projection re-emission, and the
renderer roster-contract fix) with no conflicts — every file on this branch
is new under `specs/h3-case-study/`. The spike was then re-run per the
procedure above (`uv`-only, from the rebased worktree root) against the
final tree:

- **Decision reproduced**: `decision: "pass"`, all four gate classes
  (fixture, settings, rejections, negative-control) pass with the same
  exactness classes and byte-identical numerics as the `b992032` run.
- **Receipt refresh**: old receipt sha256
  `6913b5b50c65d2b7e09e1fa7f69c96fa505b070914aff513f286822b9ef158a4` →
  new receipt sha256
  `6913b5b50c65d2b7e09e1fa7f69c96fa505b070914aff513f286822b9ef158a4`
  (unchanged): the rerun's payload is byte-identical to the retained
  `spike-receipt.json`, so the refresh is a verification, not a rewrite.
- **Drift classes observed between `b992032` and `32258cf`** (18 files):
  CI workflow, CHANGELOG/TODO records, gnn-input projection markdown,
  artifact-proof manifests, gnn-bridge custody pins
  (`specs/gnn-bridge-w2-source-custody/source-pin.json`,
  `specs/gnn-bridge-q7-continuous-ou-proof/syntax-pin.json`), the
  renderer/release-bundle modules (`src/fep_lean/output/{manuscript,
  release_bundle,rendering}.py`), and their tests. **None of these
  intersect the spike's six-pin set**: all five pinned Lean carrier/
  composition sources and the H2.7 terminal receipt are byte-identical at
  `32258cf`, so no pin or receipt value required updating.
- **Residual re-verified**: the W2 eligibility validator still fails on the
  live tree with exactly `{"status": "error", "error": "current
  validator/diagnostic source mismatch"}` (re-run read-only at `32258cf`)
  — the "precise residual" section above is unchanged by the rebase, as
  none of its six named files drifted.

The HARD STOP stands: this refresh is a feasibility-spike receipt refresh
only (in-contract for a spike, unlike the repo's custody manifests, which
were not touched). It issues no acceptance or exit-gate verdict and makes
no study-completion claim; independent claim review remains the next phase.

## Boundary

This record performs no proof, repairs no carrier, hybridizes no branch, and
issues no acceptance/exit-gate verdict and no study-completion claim. The
continuous-branch selection is recorded; its acceptance remains the
independent reviewer's judgment on the enumerated residual. Every claim above
is source-bound to `b992032` bytes; a moved base invalidates the record.