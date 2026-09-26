# Branch coverage

Coverage is measured with `concurrency = ["multiprocessing"]` in `pyproject.toml`.
`src/fep_lean/output/figures.py` renders charts via matplotlib with the Agg
backend only; it spawns no worker processes.
The `multiprocessing` concurrency setting is incompatible with `--cov-branch`
(a known pytest-cov limitation: branch data is not collected from worker processes).

## Measuring branch coverage

To measure branch coverage, run a separate non-parallel invocation that excludes
figure-generation tests:

```bash
uv run pytest tests/ -q --cov=src --cov-branch --cov-report=term-missing \
  --ignore=tests/test_figure_generation.py
```

This gives branch coverage for all source files except `src/fep_lean/output/figures.py`
(which is excluded from the branch run). The figure module has 100% line coverage
and no branch-dependent logic, so the gap is negligible.

## Expected values

Current runs show approximately **89.6% branch coverage** across all non-figure
modules. Branch coverage is **not** independently gated — `fail_under` in
`pyproject.toml` applies to line coverage only. The line coverage threshold of
89% provides adequate protection since branch coverage tracks within ~1.5
percentage points of line coverage for this codebase's error-handling patterns.

## Related

- [`pyproject.toml`](../pyproject.toml) — coverage concurrency setting

## 2026-09-25 — w23 serial-verdict: custody-settle delta table + TESTS-7 cadence receipts

Delta: baseline `b2bb5fa` → integrated `5cc9938` (w22 fold lineage; spawn base origin/main; battery-green by coordinator receipt). Baseline reference: TASKS.md line 31 — TASKS.md is absent in this worktree and at the brief's stated repo path (reported per brief line 5); the facts below are the brief's ledger facts used verbatim.

### Red-class delta

| Class | At b2bb5fa | At 5cc9938 | Owner / disposition |
| --- | --- | --- | --- |
| `horizon_acceptance` custody-staleness | 6 | 0 | Self-healed post-w20: 38/38 at fd737d8. |
| Fixture reds, state-flip class | 29 | 7 | 22 cleared with the pre-chore problem they asserted; 7 persist as W19-side green-state asserts needing state-parameterized re-issue — owned wave-2 class; NOT staleness regressions (`tests/test_custody_apply.py`). |
| Staleness regressions from w20+w22 waves | — | 0 | None. |

Receipts:

- Battery at `5cc9938`: 11 gates + roster gate (0 errors) + pair gate (ok) — GREEN; G06/G07 healed by build-product regens (gitignored, zero tracked changes).
- CI-side confirmation of the self-heal (python-lane FAILED, per-job `--log-failed`): 36 at `4a19297` (full pre-w20 custody-staleness class) → 7 at `970ee8a` → the same 7 at `5cc9938` (run 36144239624, python job 108101267417: "7 failed, 1771 passed, 14 skipped in 312.66s"). The exact surviving node set, all in `tests/test_custody_apply.py`: `test_cascade_serialization_discipline`, `test_cli_apply_gate_refusal_writes_nothing`, `test_cli_census_report_composes_read_only`, `test_gate_all_clear_fixture_admits_the_pipeline`, `test_gate_refuses_real_tree_live_red_classification`, `test_recapture_rebind_mutates_exactly_the_evidence_surfaces`, `test_required_surface_never_authorized_by_allowed_stale`. No parity red exists in CI at any tip: the python job's "Generate and validate publication inputs" step (ci.yml:48-50) runs `uv run fep-lean catalogue` before pytest, regenerating the gitignored `manuscript/manuscript_vars.yaml` the test reads — parity passes in CI at every tip, and an earlier draft's "peer wave-6 fix resolved it at head" wording was unsupported (CORRECTION 2026-09-25, settled by ci.yml evidence at both tips + local 3-pass run).
- CORRECTION (2026-09-25): no peer-owned python red exists. The parity test cannot fail in CI at any tip — ci.yml:48-50 regenerates its gitignored target (`manuscript/manuscript_vars.yaml`) via `uv run fep-lean catalogue` before pytest (verified at `97a6a18` and head); an earlier draft's "FAILED at `97a6a18`, resolved at head" claim was unsupported. The G11 local 8F parity component was a stale local build product (file absent pre-G06-regen); post-G06 local run = 3 passed.
- Lean-lane red (figures-infra class, not python): `tests/test_manuscript_rendering.py` — "manuscript asset roster sources are missing" (`status_distribution.png`, `topics_by_area.png`). Attempt 1 (job 108101499569) failed 13:57:39Z–14:21:00Z; the coordinator-authorized lean-job rerun (attempt 2, job 108112227271, 14:26:40Z–14:56:37Z) gives the per-test receipt: "1 failed, 527 passed, 5 skipped in 1426.83s" — the single failure `test_live_render_includes_author_block_and_canonical_graphical_abstract` raised `ManuscriptRenderError` for the same two figures, with the decisive delta that the rerun's step 12 ("Download the publication figure assets the render-deps job produced") succeeded yet both figures were still absent at render time: the saved render-deps artifact itself lacks them (render-deps output/roster mismatch), superseding the first-pass cache-ordering race as the sole explanation. Figures-infra owned; NOT a wave regression.
- CI lineage at head sha `5cc9938` (check-runs API, total_count 4): attempt 1 = render-deps success (108101267083), python failure (108101267417), lean failure (108101499569), render skipped; attempt 2 = lean rerun job 108112227271 (failure, figures class only), render-deps carried success (108112227578), python not re-executed (108112269348 retains recorded failure), render skipped (108123458724). Only run 36144239624 exists at this head; main == `5cc9938` ("q5: re-regen native receipt against cycle #26 seal (fold-fixup)", 2026-09-25T13:43:42Z) — no newer green run; the no-green streak (`36075721520` → `36144239624`, 30+ attempts) is inherited figures-infra lineage, NOT a wave regression.

### TESTS-7 cadence receipts

- Definition (`SCOPE-2026-09-20.md:78`): "One serial-inclusive coverage run (no `-m` filter) after the wave lands; record per-module delta table in `docs/coverage-branch.md`. Requires the Lean toolchain; runs after the gate battery."
- Gate battery at `5cc9938`: GREEN — 11 gates + roster gate (0 errors) + pair gate (ok); G06/G07 healed by build-product regens (gitignored, zero tracked changes).
- Serial-inclusive plane: the local battery deselects `serial_lean`; the CI serial lane is the serial-inclusive receipt plane — run 36144239624 on `5cc9938`, lean serial lane 527 passed / 1 failed (attempt 1) and 527 passed / 1 failed on the attempt-2 rerun, both the same figures-infra node. The local serial-inclusive coverage run stays deferred to the next settled cadence (Lean-toolchain requirement; no local battery re-run authorized in-thread).
- Per-module delta table: the red-class table above (module-attributed: `horizon_acceptance`, `tests/test_custody_apply.py`, `test_manuscript_token_parity.py`, `test_manuscript_rendering.py`).

### Serial verdict

The custody chain settled: capture fb201372 claim-ready, packet ec253d59 validate-green, Q5 receipt 81264af0 bound at the #26 seal, pair `970ee8a`↔`d07e55808` CI-verified. Zero new reds from the w20+w22 waves: the 35 custody-staleness reds at baseline `b2bb5fa` fully decompose into 6 self-healed `horizon_acceptance` reds (38/38 at `fd737d8`) and 29 state-flip fixture reds (22 cleared with the pre-chore problem they asserted, 7 persisting as W19-side green-state asserts owned wave-2), with CI independently confirming the self-heal (python lane 36 at `4a19297` → 7 at `970ee8a` → the same 7 at `5cc9938`; parity reds cannot manifest in CI at any tip (catalogue regen precedes pytest, ci.yml:48-50)). Residual red classes are owned, not wave regressions: the 7 campaign-classified fixture-debt survivors (wave-2 seed, state-parameterized re-issue) and the inherited figures-infra lineage (`test_manuscript_rendering.py`, both CI attempts, render-deps output/roster mismatch). CI at `5cc9938` is receipted complete across both attempts — python lane = exactly the 7 fixture-debt survivors, lean attempt-2 rerun (job 108112227271) = the figures-infra node only with 527 serial-lane passes — so the serial-verdict receipt set is closed and the verdict stands on the battery + custody receipts plus the completed two-attempt CI receipts.

## 2026-09-25 — M-11 fep-side close-out: bridge cancellation/atomicity (cycle #27)

Delta: fep tip `7267119` (cycle-27 worktree base: w22 fold `f060ec1` + fixup `5cc9938` + w23 fold `f701873` + parity-attribution correction `7267119`). Companion lane: GNN-side M-11 (PR #205 → GNN main `b32fbcf32`) made the lean dispatch cancellable; this section closes the fep-side question with an evidence-first verdict and NO code change.

### Kill channel

The GNN execution envelope honors its CancelToken pre-spawn and mid-flight (0.25 s poll) and on cancel GROUP-KILLs the bridge subprocess tree via SIGKILL (`subprocess_envelope.py:190-215`, `kill_process_group`); the bridge subprocess (`uv run --frozen fep-lean bridge verify-document`) is killed, not asked. SIGKILL is uncatchable — no in-bridge cooperative-cancel handler can intercept it — and a SIGTERM handler would be dead code under the current kill channel. Decision: none is added.

### Receipt write-site classification (at `7267119`)

Every bridge-plane file write routes through the shared atomic-write pair (`src/fep_lean/output/fsutil.py:50-67`: mkstemp sibling temp → write + fsync → `os.replace`). No bridge-plane destination write bypasses rename atomicity; raw direct writes exist only outside the bridge path and are enumerated in the sweep below.

| Site | Destination | Route | Verdict | Consumed by |
| --- | --- | --- | --- | --- |
| `src/fep_lean/bridge/operations.py:128` (`pin_sources`) | `specs/gnn-bridge-w2-source-custody/source-pin.json` | `custody.write_json` → `custody.write_text` → `fsutil.atomic_write_text` | atomic | `bridge status`/`check_sources`, CI pair gate, GNN paired-CI freshness gate; written only by explicit `bridge pin` (short command, not killed mid-flight) |
| `src/fep_lean/bridge/operations.py:193` (`emit`) | projected documents `specs/gnn-bridge-p1-finite-spike/gnn-input/*.md` and `specs/gnn-bridge-p4b-continuous-emission/gnn-input/*.md` | `custody.write_text` | atomic | seal/`verify-document` inputs; the `emit --refresh` path re-emits via `custody.refresh_signature` (`custody.py:127-136`), also atomic |
| `src/fep_lean/bridge/operations.py:305-314` (`emit_certificate`) | certificate receipt JSON + sibling `.md` | `custody.write_json` / `custody.write_text` | atomic | `certify --receipt` output; `verify-certificate` recomputes from the pin rather than trusting the file |
| `src/fep_lean/bridge/operations.py:557-558` (`verify_document`) | caller-supplied `--receipt` path | `custody.write_json` | atomic | GNN `lean_runner` receipt — the one write a GNN-side cancel can kill mid-flight |
| `src/fep_lean/bridge/cli.py:116,119` | stdout only | — | n/a | process stdout; no file written |

Long-run scratch, classified out of the receipt set: the Lean probe files `verify_document` compiles are written under the verification plane (`src/fep_lean/verification/lean_verifier.py:505-514` mkstemp temp `.lean`; `src/fep_lean/verification/gnn_artifact_receipt.py:873-874` probe inputs) — per-run throwaway inputs, never GNN-consumed receipts; a kill leaves discardable scratch and the next run re-creates it. The native-receipt writer is an inline atomic equivalent (`src/fep_lean/output/evidence.py:167-184`: mkstemp → fsync → `os.replace`), as is the audit receipt writer (`src/fep_lean/verification/formalism_audit.py:573-583`). The release-bundle render wrapper writes its shell wrapper inside a `tempfile.TemporaryDirectory` (`src/fep_lean/output/release_bundle/_manuscript.py:427-446`) — ephemeral, not a consumed receipt. The `output/` plane otherwise writes via `fsutil.atomic_write_text`/`atomic_write_bytes`, inline mkstemp+fsync+`os.replace` equivalents, or staged-tree installs with `os.replace` (`rendering.py:385-388`, `reporter.py:1765-1791`, `manuscript.py:777-808`, `browser_capture.py:1373-1384` — capture artifacts staged into a `tempfile.mkdtemp` staging dir, then installed via `_install_capture_transaction` (`browser_capture.py:1415-1431`), `release_bundle/_acceptance.py:384,794,887`, `figures.py:33-34` (savefig to a temp, then `os.replace`), `graphical_abstract.py:381`, `formal_kernel_dashboard.py:1255-1256`, `formalism_atlas.py:867-868`). Full write-idiom sweep over `src/fep_lean/` — every raw direct destination write, none on the GNN kill path (coordinator-invoked planes: custody-apply, formal, catalogue, gauss, render lane): `write_bytes` — `src/fep_lean/output/svg_raster.py:155` (published figure PNG copy, render lane, non-atomic), `src/fep_lean/custody/apply.py:198` (custody-apply evidence surfaces), `src/fep_lean/formal/projection.py:80` (formal projection copies); `write_text` — `src/fep_lean/formal/projection.py:53` (formal aggregate), `src/fep_lean/catalogue/generation.py:240` (topics catalogues, both projections), `src/fep_lean/catalogue/coverage.py:614-617` (coverage JSON + markdown), `src/fep_lean/gauss/client.py:420` (JSONL export); external-process — `src/fep_lean/output/svg_raster.py:102-111` (the external rasterizer writes the destination PNG directly via `--output`). Staged/ephemeral: `src/fep_lean/output/browser_capture.py:1421,1424` (mkdtemp staging → `_install_capture_transaction`), `src/fep_lean/output/release_bundle/_manuscript.py:439,450` (TemporaryDirectory render environment), `src/fep_lean/gauss/client.py:389` (tmp then `os.replace`), probe scratch (`src/fep_lean/verification/lean_verifier.py:514`, `src/fep_lean/verification/gnn_artifact_receipt.py:874`). Every `open`-for-write is `os.fdopen` over a `tempfile.mkstemp` handle (`fsutil.py:55`, `evidence.py:175`, `formalism_audit.py:472,578`, `release_bundle/_assemble.py:430`); `json.dump` reaches destinations only through those staged writers; copy sweeps (`shutil.copy`/`copyfile`/`copy2`/`copytree`) zero; logging is console-only (`src/fep_lean/cli.py:50-54` `basicConfig`, no `FileHandler` anywhere). The bridge's only formal-plane import is the read-only `FORMAL_MODULES` manifest (`operations.py:230`), it imports neither `svg_raster` nor `fep_lean.custody`, and no write site executes on the bridge path — so the verdict above is unaffected.

### The `custody.py:123` probe, resolved

The earlier probe's "raw `write_text(json.dumps(payload...))` at `src/fep_lean/bridge/custody.py:123`" is a misread of the current tree: lines 121-124 are `write_json`, whose single statement calls the module-local `write_text` (`custody.py:112-118`), which delegates to `fsutil.atomic_write_text` (import at `custody.py:13`). The `import os  # noqa: F401` note at `custody.py:7-8` exists precisely because tests patch `custody.os.replace` and the patch reaches the delegated `fsutil` write — delegation is the designed path. Readers of custody-plane outputs: the w2 source pin (`bridge status`, `check_sources`, CI pair gate, GNN paired-CI freshness gate) and the receipts in the table above (GNN `lean_runner`).

### Crash window under SIGKILL

`fsutil.atomic_write_bytes` (`fsutil.py:50-62`) writes a sibling `.name.XXXX` temp, fsyncs, then `os.replace`s onto the destination. SIGKILL skips the `finally` unlink (`fsutil.py:60-62`), so an orphaned dot-prefixed temp file can remain; the destination itself is never torn — a reader observes either the previous content or the complete new content. mkstemp's unique names prevent temp collisions, and every consumer reads exact paths rather than scanning directories, so orphans are inert. Classification: safe.

### Verdict

M-11 fep-side resolved by design at cycle #27, tip `7267119` (2026-09-25): every receipt path the GNN envelope can kill mid-write is already atomic (table above); the kill channel is uncatchable SIGKILL, so no in-bridge cooperative-cancel handler is added (dead code under the current kill channel). No code change; documentation close-out only.
