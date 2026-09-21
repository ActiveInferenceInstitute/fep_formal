# fep_lean review — 2026-09-05

Status: closed; findings landed on main (state self-pinned to `f335724`)
Closed: 2026-09-05

Deep review + improve + document cycle over the wave-2 delivery state.
Method: scoped Python gates (pytest, ruff, mypy, manuscript/docs gate
scripts) run by the parent, plus a four-lens read-only review pool
(code quality, docs accuracy, test/gate health, spec/receipt consistency).
Improvements were limited to safe, high-value fixes: no Lean/Lake/native
builds, no dependency changes, no API changes, no commits or pushes.

## Baseline

- Repo: `projects/outside_of_hum/fep_lean`, HEAD
  `f3357245015e4d0e19b09dc8cf7c33d7385a28a1` ("feat: seal GNN artifact
  proofs and H2 terminal acceptance", 2026-09-04 21:14:01 -0700). The
  wave-2 specs/receipt artifacts are committed in this seal commit; the
  wave-2 code/manuscript changes were uncommitted on top of it (18 dirty
  files at review start, per the wave-2 handoff).
- Working tree at review end: 27 dirty tracked files = the original 18
  (preserved, untouched except where listed below) + 8 files edited by
  this review + 1 concurrent edit by another agent (see F10).
- Prior verified state: WAVE2-REPORT.md claims an integrated FEP Python
  scope of 1,460 passed / 7 skipped / 529 deselected at 89.83% coverage.

## Findings

Severity reflects gate/correctness impact on the current tree.

### F1 (HIGH, fixed) — CI python job would fail on serial_lean tests

`.github/workflows/ci.yml` pytest step had no `-m "not serial_lean"`
deselect, but the python job installs no elan/lake. At least six
`serial_lean` tests call `lake` unguarded
(`tests/test_gnn_continuous_native_proof.py:19`,
`tests/test_gnn_julia_artifact_proof.py:271,300`,
`tests/test_gnn_artifact_proof.py:622` → `tests/_support/lean_runner.py:36`
`Popen(["lake", ...])`), so the first real CI run would error, not skip.
Native evidence is separately owned by the `lean` job (elan + warning-free
`lake build FepSketches` + `fep-lean verify`). Fix: added
`-m "not serial_lean"` to the CI pytest step, matching the validated
integrated scope. Note: the `on:` trigger block itself is part of the
uncommitted wave-2 state, so CI has not yet exercised any of this.

### F2 (HIGH, fixed) — wave-2 crossref migration broke the citation gate

The uncommitted wave-2 state migrated the manuscript from LaTeX
`\label{eq:…}` / `\ref{…}` to pandoc-crossref `{#eq:…}` / `[@eq:…]`
(git grep: 0 crossref-style refs at HEAD `b9d315c` vs 139 in the worktree).
`docs/citation_audit.py` `cited_keys()` collected every `@key` inside
bracket citations, so `[@sec:…]` / `[@eq:…]` / `[@tbl:…]` crossref
references were counted as bibliography citations → "undefined citation
keys" (89 keys) → `test_citation_audit.py` failed and the CI
`citation_audit` step (ci.yml line 38) would fail. Fix: added
`_CROSSREF_PREFIXES = frozenset({"sec", "eq", "fig", "tbl", "lst"})`
(mirroring `docs/xref_audit.py`) and filtered those prefixes in
`cited_keys()`.

### F3 (HIGH, fixed) — artifact tests pinned the legacy equation-anchor form

`build_typeset_equations_markdown` now emits `$$ … $$ {#eq:topic-N}`
(pandoc-crossref numbering; `\label` inside `$$` is invisible to the
filter), and `build_unified_formalism_appendix_markdown` composes the
builders directly (no disk fallback). Two tests still asserted the old
`\label{eq:…}` form and could never pass against the new builder:
`tests/test_manuscript_artifacts.py:298` (`n_eq` counted `\label{…}`,
got 0) and `:313` (`labels` vs `equation_count`, got 0 == 487). Fix:
updated both regexes to the `{#eq:…}` contract and strengthened the
negative assertion to `"\\label{eq:" not in md` (the whole point of the
wave-2 change, per the comment at `src/fep_lean/output/manuscript.py:1007`).

### F4 (HIGH, fixed) — xref audit could never resolve generated-appendix refs

`docs/xref_audit.py` collects findings over `manuscript_source_files()`,
which excludes the generated `manuscript/09z_unified_formalism_catalogue.md`
— the only definition home for `sec:catalogue-*`, `sec:eqs-*`,
`sec:appendix_b_full_topic_lean_catalogue`, and `sec:appendix_c_latex_equations`.
Chapters reference those anchors 33 times, so the audit failed
structurally ("FAIL: 34 finding(s) … unresolved=33") on any checkout,
including CI (which generates the appendix before the xref step). Fix:
`audit()` now takes `definition_files`; `main()` passes the full
`manuscript/*.md` glob for anchor definitions while keeping findings
restricted to renderable sources. Result: 339 → 1138 anchors defined,
all 87 crossref references resolve.

### F5 (MED, fixed) — hand-numbered "Table 1" fails the strict xref gate

`manuscript/02b_background.md:135` ("Table 1 reports the present
catalogue's scope") tripped `_RE_HAND_NUMBER`; `xref_audit` exits 1 on
any finding, so CI's xref step would stay red even with appendices
generated. Fix: rephrased to "The table below reports…" (no test pins
the old wording; verified by grep over `tests/` and `docs/`).

### F6 (MED, fixed) — unused `noqa` broke ruff on the gate script itself

`docs/xref_audit.py:66` carried `# noqa: E402`; E402 is not enabled in
the pinned rule set, so RUF100 flagged it and
`ruff check src tests scripts docs` failed on the wave-2 tree. Fix:
removed the directive.

### F7 (MED, fixed) — docs accuracy gaps

- `docs/cli-reference.md` omitted the entire `fep-lean bridge`
  subcommand (exists at `src/fep_lean/cli.py` with operations
  `status|pin|emit|certify|verify-certificate`, required `--gnn-root`;
  AGENTS.md documents it). Added the table row and a read-only vs
  mutating sentence.
- `docs/testing.md` listed `_maint_build_lean_landscape.py --check`
  twice; removed the first occurrence so the block matches CI order.
- `README.md` H2.7 sentence omitted the 180-source-hash binding that
  `terminal-acceptance.json` and WAVE2-REPORT.md both carry; added
  "180 bound source hashes".
- `HANDOFF.md` had no pointer to the wave-2 evidence layer; added one
  sentence linking `specs/gnn-bridge-w2-source-custody/WAVE2-REPORT.md`.

### F8 (MED, fixed) — stale "retained" claims for wiped evidence dirs

README and HANDOFF described `output/reports/run_20260820_*` as
retained/historical evidence, but those directories no longer exist
(verified: `output/reports/` holds only `run_20260905_1553*` runs plus
stage snapshots including `stage-01-clean-output-directories.json`,
i.e. a deliberate custody cleanup). Reworded both to past tense with an
explicit "no longer present under the current `output/reports/` tree".

### F9 (HIGH, recorded — not fixed) — WAVE2-REPORT.md custody section is stale

WAVE2-REPORT.md states "Repository HEADs remain … FEP b9d315cb…; neither
repository was committed, pushed, or published by this work." Actual
state: HEAD is `f3357245` (2026-09-04 21:14 -0700), a commit whose diff
is exactly the wave-2 specs/receipt artifact set; the wave-2 code and
manuscript changes remain uncommitted on top of it. The report was
therefore written before the seal commit and its no-commit/HEAD claim no
longer describes the repository. Disposition: intentionally NOT edited —
WAVE2-REPORT.md is a delivered evidence artifact inside the seal commit,
and this review must not mutate sealed custody records; correction
belongs to the sealing agent/maintainer. Suggested wording: "HEAD at
report writing b9d315c; wave-2 specs artifacts subsequently sealed in
f3357245; code and manuscript changes remain uncommitted."

### F10 (record) — concurrent agent activity observed during the review

`manuscript/04g_finite_active_inference_kernel.md` changed mid-review
(dashboard figure reference `../docs/formal-kernel-dashboard.svg` →
`../output/figures/formal-kernel-dashboard.png`; the PNG exists,
generated ~15:53 today), and fresh `output/reports/run_20260905_*` runs
appeared. Preserved untouched; all gates re-verified green with the edit
in place.

### F11 (record) — wave-2 report vs tree drift

WAVE2-REPORT.md's verification table reports green FEP quality (strict
mypy 82 files, Ruff/format surfaces pass) and the 1,460-passed final
scope, yet the delivered uncommitted tree failed 4 pytest tests and 3
gate scripts (xref, citation, ruff) before this review's fixes. The
four test failures are mechanically implied by the wave-2
`manuscript.py` emission change and could not have passed against the
current sources. Most likely explanation: the report's runs predate the
final manuscript-emission/manuscript edits, or were taken before the
pandoc-crossref migration landed in the worktree. Recorded as a custody
discrepancy for the wave-2 owner; this review's fixes reconcile the
tree with the reported scope (final numbers below).

### Lens advisories (recorded, intentionally not applied)

From the code-quality lens (no high findings; the changed rendering code
was otherwise verified sound — transactional writes, fail-closed
placeholder/asset gates, and drift semantics all check out):

- `rendering.py:117-142` `_atomic_text`/`_atomic_bytes` duplicate
  `manuscript.py` staging helpers; consolidate later.
- `manuscript.py:159-176` vs `:206-224`: clean/failed topic-id
  classification duplicated with different `has_sorry` fallbacks;
  extract a shared helper.
- `manuscript.py:800-801` force-sets `verify["claim_ready"] = True` on
  manifest presence regardless of manifest contents — confirm intent.
- `manuscript.py:~330` `model_fallback_count` sums all
  `chain_advance_reasons`, not only fallback reasons (naming/API-shape).

From the test/gate-health lens:

- `pyproject.toml` `timeout = 900` silently halves the documented
  1800 s `FEP_LEAN_PROBE_TIMEOUT` for serial_lean probes.
- `xdist_group("lean")` is inert without `--dist loadgroup`; documented
  in `tests/AGENTS.md` (fix applied), the conftest marker itself kept.
- `filterwarnings` blanket-ignores three warning classes suite-wide.
- `tests/test_browser_capture.py` skips on macOS (`google-chrome` vs
  `"Google Chrome"` binary name).
- `docs/xref_audit.py` fence tracking is naive for nested/`~~~` fences.

Skip inventory: all 7 integrated-scope skips are annotated and
justified; no xfail anywhere; no brittle implementation-pinning tests
found in the wave-2 surface.

### Spec/receipt consistency (independently verified, all confirmed)

The fourth lens verified the wave-2 receipt claims against artifacts:
Q5 = 6 / Q6 = 5 / Q7 = 12 native theorem reports (23 total), every
axiom entry exactly `[propext, Classical.choice, Quot.sound]`, no
`sorryAx`; all three receipts `schema_version: 2` with
`runtime_execution_verified: false` (scope honesty intact); receipt
SHA-256 claims match the retained verification ledger; bridge contract
v0.4 identical in both checkouts; H2.7 `terminal-acceptance.json` =
328 mandatory cases, 180 source hashes (33 current + 147 native),
exactly 3 approving reviews (lean/domain/skeptical), downstream opens
only H3.G0 read-only eligibility; baseline 1,727 passed / 44 skipped;
all relative links across the five wave-2 REPORTs resolve.

## Fixes applied (8 files + 2 already-dirty files touched)

| File | Change |
| --- | --- |
| `.github/workflows/ci.yml` | pytest step: added `-m "not serial_lean"` |
| `docs/citation_audit.py` | crossref-prefix filter in `cited_keys()` |
| `docs/xref_audit.py` | removed unused `noqa`; `definition_files` widening |
| `tests/test_manuscript_artifacts.py` | two regexes to `{#eq:…}` contract; `\label` absence assertion |
| `tests/conftest.py` | removed dead `group_started` bookkeeping |
| `tests/AGENTS.md` | documented `--dist loadgroup` parallel command |
| `manuscript/02b_background.md` | "Table 1" → "The table below" |
| `docs/cli-reference.md` | added `fep-lean bridge` row + custody sentence |
| `docs/testing.md` | removed duplicate gate line |
| `README.md` | H2.7 "180 bound source hashes"; retention claims corrected |
| `HANDOFF.md` | retention claims corrected; wave-2 evidence pointer |

Environment (gitignored, CI-equivalent state, no tracked bytes):
regenerated 9 catalogue figures into `output/figures/`, refreshed
`manuscript/manuscript_vars.yaml` (the designed test-collection-cache
refresh after editing tests), left the existing generated
`manuscript/09z_unified_formalism_catalogue.md` untouched.

## Verification evidence

Before fixes (start of review):

- `uv run pytest tests/ -q --no-cov -m "not serial_lean"` →
  4 failed / 1,456 passed / 7 skipped / 529 deselected
  (`test_citation_audit` bijectivity, 2 × `test_manuscript_artifacts`
  structure, `test_manuscript_rendering` live render).
- `uv run ruff check src tests scripts docs` → 1 error (RUF100).
- `uv run python docs/xref_audit.py` → FAIL, 34 findings
  (hand-number=1, unresolved=33), 339 anchors.
- `uv run python docs/citation_audit.py` → fails via pytest;
  "undefined citation keys: …" (89 crossref keys).
- `uv run mypy src` → Success: no issues found in 82 source files
  (clean before and after).

After fixes:

- Full suite (post-fix tree):
  `uv run pytest tests/ -q --no-cov -m "not serial_lean"` →
  **1,460 passed, 7 skipped, 529 deselected** — exact match to the
  WAVE2-REPORT.md integrated scope; a confirmation re-run on the exact
  final tree reproduced the same totals.
- `uv run pytest tests/test_citation_audit.py
  tests/test_manuscript_artifacts.py tests/test_manuscript_rendering.py
  -q --no-cov` → 78 passed.
- `uv run ruff check src tests scripts docs` → All checks passed;
  `ruff format --check` → 289 files already formatted.
- `uv run python docs/xref_audit.py` → OK: 28 rendered files, 1,138
  anchors defined, 87 crossref references — all resolve.
- `uv run python docs/citation_audit.py` → OK: 79 bibliography entries
  defined, indexed, and cited.
- `uv run python scripts/render_manuscript.py --check` → OK
  (projections current, placeholders resolve).
- `uv run python docs/check_links.py --strict --include-root` → OK, 47
  files; `uv run python docs/md_hygiene.py --strict` → OK, 43 files
  (both re-run after all doc edits, including the concurrent 04g edit).

## Recommended follow-ups

1. Custody: correct WAVE2-REPORT.md's "Boundaries and custody" section
   to name the seal commit `f3357245` (see F9), or append a dated
   errata note beside it.
2. Reconcile the wave-2 verification-table provenance (F11): state
   which tree state the green quality/pytest rows were measured on.
3. Decide whether tests should require generated catalogue artifacts
   (`fep-lean catalogue`) or degrade gracefully on clean checkouts;
   today CI ordering covers it, local AGENTS.md "required checks" do
   not spell out the prerequisite.
4. Add `MANUSCRIPT_ASSETS`/generation coverage for
   `output/figures/formal-kernel-dashboard.png` if the 04g svg→png
   migration is kept (currently the renderer's asset map only pins
   `status_distribution.png`).
5. Test-config hygiene (advisory list above): probe-timeout ceiling
   documentation, warning-filter narrowing, macOS Chrome skip paths.
6. Consider a shared `_CROSSREF_PREFIXES` constant (or import) between
   `docs/xref_audit.py` and `docs/citation_audit.py` so the two gates
   cannot drift again.

## Boundaries

No commits, pushes, Lean/Lake invocations, dependency changes, or API
changes. All 18 pre-existing dirty files preserved; `src/fep_lean/
output/{manuscript,rendering}.py` untouched. Edited files are listed
above; the 04g concurrent edit was left to its owner.
