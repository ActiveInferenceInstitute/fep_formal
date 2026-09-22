## Unreleased

### Comprehensive improvement wave (2026-09-20/21) — SCOPE-2026-09-20

A 7-lane read-only scoping swarm (Ledger, CI, SRC, DOCS, TESTS, ARTIFACTS,
LEAN) over `1c3c627` produced `SCOPE-2026-09-20.md` (37 items). Execution ran
as ten parallel project threads (t-0009..t-0018), after the parallel t-0005/6/7
waves (docs+ledger hygiene, CI hardening, tests suite quality — landed
earlier the same day) were restored onto the synced tip when a reset-to-origin
dropped their merges (re-merged as `8e67751`, `ba1c582`, `2037b40`). Landed
item groups:

- **CI** (t-0009, rebased onto the restored `de62368` hardening): a
  `lean/.lake/build` cache keyed on toolchain + lakefile + manifest +
  `fep_all.lean`, and `pull_request` paths-ignore so doc-only PRs skip the
  lean/render chain.
- **Render receipt classification** (t-0010): `receipt_defects`/`_moved_sources`
  now classify generated appendices — a moved `09z` remediates with
  `fep-lean catalogue`, authored moves keep the render remediation; a missing
  generated source fails closed via a receipt defect (the digest function
  stays byte-stable, so committed custody receipts remain valid); the false
  boundary docstring corrected; `check_render_log.py` prints a degraded-mode
  WARN when `manuscript_vars.yaml` is absent; the contents-overflow scan
  covers an absent combined log when a sibling log exists; nine regressions
  in `tests/test_render_log.py`; the status-verb fixture stages the generated
  appendix; the `scripts/AGENTS.md` receipt-boundary claim corrected.
- **Render publication** (t-0011): `--require-release-stamp` pass-through
  (default off); render-lock holder-pid file, dead-holder stale-lock warning,
  and a guarded release that never masks the render exit code; tests.
- **fsutil consolidation** (t-0012): the deprecated `_sha256`/`_atomic_text`/
  `_atomic_bytes` shims removed across `browser_capture`/`evidence`/
  `release_bundle`/`rendering`/`reporter` (callsites point at `fsutil`);
  `reporter`'s inline digest → `sha256_bytes`; `release_bundle`'s
  coverage-line parse fails closed on malformed records; the divergent
  `gnn_artifact_proof.sha256_file` renamed `sha256_file_strict` (the Q5
  probe, the star-copy pin, the contract-edge attribute, and the
  regenerated `artifact_proof_manifest.json` aligned — 206 tests green on
  the proof trio).
- **Manuscript projections** (t-0013): `manuscript.py` atomic writes folded
  into `fsutil`; hand-typed structural counts tokenized — areas via the
  existing `{{total_areas}}`, expansion-family counts via new
  `manuscript_vars` projections (`expansion_families`, `expansion_family_topics`,
  second-wave boundary at `fep-121`); nine chapters updated; token-parity
  tests added.
- **check_or_write** (t-0014): one shared `--check`/write shell in
  `catalogue/generation`; six script callers plus the `cli` `_atlas`/
  `_dashboard` twins thinned; STALE wording unified (stdout); `cli`'s broad
  except narrowed.
- **Lean test adoption** (t-0015): raw `subprocess.run` lean compiles adopted
  onto the process-group-safe probes (`tests/_support/lean_runner.py` +
  the two-stance `tests/_support/lake.py`); 21 `_without_lean_comments`
  copies deduped onto `fep_lean.lean_source.lean_code_without_comments`;
  the bridge verify-document well-formedness test marked `serial_lean`; the
  conftest two-stance missing-tool policy documented.
- **Docs/config truth** (t-0016): `pin_audit` regex hardened for
  backtick-quoted Mathlib tags; the `coverage-branch.md`/`pyproject.toml`
  ProcessPoolExecutor claim corrected; the quickref bridge line gains the
  required `--gnn-root`; dead settings keys removed (`gauss.source`,
  `gauss.log_level`, `gauss.verify_lean`, `output.report_dir`) with
  README/configuration rows corrected (`gauss.default_model` kept —
  `pin_audit` cross-checks it against `hermes.model`).
- **Lean/specs** (t-0017): `lean/build.sh` runs lake from its own directory
  (root invocations previously failed); lean README/AGENTS version and
  `ELAN_HOME` refs refreshed; three bridge spec READMEs moved from "active"
  to accepted wording; the 2026-09-05 review spec moved under `specs/done/`
  (the getting-started link updated); the geo-bridge and h3-reference
  READMEs corrected.
- **Test behavior** (t-0018): the renderer-layering test made behavioral
  (monkeypatched probes replace source-text assertions); the font-coverage
  CI-conditional skip replaced with a stub-aware expectation.

Ledger truth pass (LED-1/LED-2/LED-3): `FEP-RELEASE-NEXT` re-anchored —
v1.2.0 shipped and the native receipt already records the v4.34.0 pin
(owner_manifest_version 18, 155 topics, 0 sorry); `FEP-H27-RESEAL`
re-recorded live — `validate_terminal_acceptance` is red at the current
tree on the native source capture (exactly the four tests-wave files:
horizon1 decision_risk / finite_reference_agent / policy_action,
native_blanket; receipt digest `d324e3d0` intact), so the native-evidence
re-capture rides the H3.0-gated adjudication, whose record's open item 1 is
flagged as predating the rebind chain.

Known gate consequence: the nine tokenized chapters make the committed
render-acceptance receipt stale until the next CI render (chapter bytes
changed by design; the receipt's classification names the render
remediation for authored moves).

## 1.2.0 — 2026-09-17 — connected Horizon research program

### Post-release custody program and Wave 2026-09-20 landing fold (2026-09-16/21)

Commits (in order): `fde5dca1` pin cycle #11 sealing the wave-3 trees (GNN
doctor module joined the sealed roster; emit refresh + both models check
green) and `4f08f013` pin cycle #12 after the GNN doctor format commit;
manuscript commits `a0a507e`/`2d7d64b`/`17d626b`/`6b9dfab` (display-equation
numbering, extarticle 9pt typesetting, the pfr2023lean author field, and the
v4.34.0 evidence-tree acceptance-receipt refresh); release `7886e3f4`
(v1.2.0); post-release custody re-seals `e48371b0` at GNN `v3.4.0`
/ `90f40bfd2` and `1c3c627a` re-recording the Horizon-2/H3 acceptance chain
for the release bump; merge `48b8d22` completes the H2.7 terminal-packet
diagnostics re-pin (`0c22c76`: `1c3c627` regenerated `diagnostics.json`
wholesale but left its artifact ref at the pre-regeneration digest
`ad7d8b0c`; re-pinned to the live `e6ce5d7f` with a lockstep H3 spike
re-pin; immutable history preserved); `c31c5243` re-seals the source roster
at GNN `083ddaf948c9` after the post-batch GNN wave landing (#117-#125).
The Wave 2026-09-20 improvement wave ran seven read-only scout lanes and
four implementation threads (docs, CI, tests, src/custody) plus this
landing fold; method, constraints, assignments, and deferrals are recorded
in [SCOPE-2026-09-20.md](SCOPE-2026-09-20.md).

### Lean/Mathlib v4.34.0 toolchain program and pin cycle #7 (2026-09-15)

Commits (in order): `ff5c712` bridge re-pin to GNN
`e983de5e5c997d413a24c8af212d0d4a2ecf61a6` sealing the post-`fa931c8`
owner content; `88ffd01` toolchain bump of Lean/Mathlib to v4.34.0 (the
newest-stable gate demanded it: `lean/lean-toolchain` v4.33.1 → v4.34.0,
lakefile + lake-manifest re-resolved at mathlib `5ed29652`) with the
155-topic FepSketches workspace migrated to the 4.34 Mathlib API, canonical
surfaces migrated and projections regenerated byte-identical,
`lake build FepSketches` at zero warnings, `fep-lean verify` at 155/155
verified with `native_claim_ready=true`, and the coordinated evidence-custody
refresh bound to the new pin; `98c6324` formalism-coverage projections
regenerated after the 4.34 migration (the CI catalogue-check step);
`1534610` ruff-format of the fixture constants in
`tests/test_reporter.py`/`tests/test_native_evidence.py` — all three merged
as PR #19 (`63aac26`); `430b725` pin cycle #7 re-seal to GNN
`e983de5e5c997d413a24c8af212d0d4a2ecf61a6` (the #19 merge's owner-content
changes invalidated the pre-bump seal; emit refresh-digests plus both-models
`emit --check` green with `--fail-on-warnings`); `24f570a` bump-proof
fixture normalization — the formalism-audit fixture now derives the Lean
version from the pinned toolchain, the same form the reporter and
native-evidence fixtures already used.

Post-entry bridge re-pins recorded here for the same program: `2b51c3d` pin
cycle #8 (GNN wave changed the sealed owner roster — framework_common.py
fold, context deletion, intelligent_analysis repoint); `1e4d634` pin cycle #9
(GNN wave-2 landed bnlearn executor + B-orientation diagnostics on the
sealed rosters; syntax-pin rebound for gnn_syntax.md); `26955f3` pin cycle
#10 (ruff-format reflowed two sealed owner files: bnlearn_runner.py,
orientation.py). Each re-pin ran emit refresh + both-models
`emit --check` green with `--fail-on-warnings`.

### Docs pinning sweep and bridge re-pins #13/#14 (2026-09-14/15)

Commits (in order): `d8ca59b` canonical bridge re-pin runbook
(`docs/design/gnn-bridge/README.md` — status → pin both → emit
`--refresh-digests` → emit `--check` → PR/merge → GNN pair-pin bump LAST,
with the owner-file warning and mirror rule), the quickref bridge row, the
AGENTS.md status/topic/report verbs, the 3.14-only validator note, and
`uv sync --locked` quickstart alignment with CI; `942f836` docs pinning —
`uv sync --locked` in quickref/getting-started/development (matching CI,
README, and ISA-03) plus the two CI-enforced render acceptance gates
(`build_render_fonts.py --check`, `check_render_log.py --verify-receipt`)
added to the testing.md release-gate list; `1e398ee` (merged `8d8ef28`,
PR #13) bridge re-pin after the GNN quality/render sweep (mypy
`strict_equality` + `warn_unreachable` at 0, structural render specs, the
logging single-entry contract, SC-22 re-render + re-record), sealed at GNN
`b0865d32`; `33bc7da` (merged `dec6dce`, PR #14) bridge re-pin at the GNN
final content state (ruff-format of the two issue-#111 render files +
figures/SC-22 re-render), sealed at GNN `c2332212`. Both re-pins pass
`bridge emit --check` finite + continuous with `--fail-on-warnings`. The
GNN-side counterpart pin bump is `a4e73837a` (fep_lean source pin raised to
the PR #14 merge head).

### scope-wave2: FEP-CI-RENDER lane and evidence-currency close-out (2026-09-12)

Commits (in order): `8ffbe2a` hermetic acceptance carries exactly git + fc-list
and the real user font inventory; `2951557` Q7 scaffold records the CPython 3.14
interpreter contract with a pinned-digest test; `f942ec9`/`dc29ecf`-chained
custody re-pins bind the Q5/Q6 manifests and the bridge source pin to the
current extractor bytes; `bb35bad` collection evidence carries the canonical
marker filter and svg_raster coverage; `237fe02` bridge custody re-pin at
`bb35bad`; `ffccdc0` collection-cache schema pins reconciled to 5 (the
`bb35bad` cache-format bump intentionally invalidated old caches; the two
hermetic tests pin the schema so a bump forces a conscious test update);
`d818efb` the renderer carries the full manuscript asset roster; `f8cd645`
bridge custody re-pin at `d818efb`.

- Renderer contract (owner-visible decision): `render_manuscript` now copies
  every `MANUSCRIPT_ASSETS` destination unconditionally (roster-driven),
  failing closed when any roster source is absent. Rationale: the release
  assembler requires the full roster, chapters hyperlink the interactive
  companions through published-ref URLs by design (`d1c0530` replaced the
  404ing relative links), and the appendix promises the offline HTML
  "without requiring a network connection" — so a reference-only filter
  silently dropped the SVG/HTML companions from the release bundle. The
  referenced-only filter was the stale side of the contract.
- Hermetic acceptance (granted final run on the converged tree): 0 failed /
  0 errors; junit roster equals `manuscript_vars.tests.collected` at 1617
  (1604 passed + 13 skipped); line coverage 0.891 against the 0.89 floor;
  receipts retained under `output/` (pytest.xml, coverage.xml,
  python-acceptance.json).
- Deterministic release bundle: two `SOURCE_DATE_EPOCH=0` builds are
  byte-identical, sha256 `ceb08c1811a7aa832245cba8cb7bd56adaaa6bdff8e8e8e8ecaeab7abfb8bb38`
  (308 members), and `--check` validates the same bundle claim-ready against
  the live roster.
  (run 6 against the 32258cf tree; superseded by the later reconciliations —
  the final restoration chain's bundle is `f6ecc47136f895f01e502edd1b05e1c4c0859be8158b0e71d2759e9621ee61c2`,
  also byte-identical ×2 and `--check` claim-ready, recorded in the
  restoration-record section below)
- Evidence currency: native verification receipt regenerated on the final
  tree — 155/155 topics compile warning- and sorry-free; the formal two-arg
  `validate_native_lean_receipt(receipt, project_root=...)` reports `valid`,
  `source_bound`, and `native_claim_ready`. Bridge custody re-pinned
  (`specs/gnn-bridge-w2-source-custody/source-pin.json` at `d818efb`; both
  Q5 and Q6 freshness gates green). Formalism-audit receipt refreshed
  (complete, zero errors, no sorry-axiom). Publication plane current
  (catalogue, render-fonts, and the strict-default `render_manuscript
  --check` all green) and the browser interaction receipt re-captured with
  zero receipt errors against the live Chrome replay.
- Evidence boundary: the report receipt validates in catalogue mode
  (`valid`, `source_bound`; `claim_ready` is full-mode-only by definition —
  a catalogue-mode report must never be read as provider evidence); native
  compilation is claim-ready at 155/155 for the exact recorded digests; the
  Hermes/OpenGauss provider plane remains historical (FEP-FULL-155 owns the
  next full-mode run under its own credential and spend boundary).
- Process lesson, recorded for the ledger: acceptance runs bind their input
  snapshot, so the dependency chain is native → manuscript vars → render →
  acceptance → bundle. An acceptance run launched concurrently with the
  native re-seal completed before the native receipt landed and correctly
  failed the bundle's input-snapshot gate; the binding run is the one
  executed after the evidence plane converges. Manuscript vars were never
  reverted to satisfy a gate — the claim-ready state is the published state.
- Merge record (2026-09-12): `origin/main` (`0da46d7`) merged over merge-base
  `4bb32ec`; its delta touches the custody/spec plane only (two `gnn-input/`
  topic documents, the w1 `syntax-pin.json`, and the w2 `source-pin.json`
  re-seal) with zero `src/`/`scripts/` files, so the rostered source digest is
  unchanged and the native receipt needed no re-run. The `source-pin.json`
  conflict resolved to the wave side (`f8cd645` re-seal binds the current
  roster bytes; origin's re-seal pinned pre-wave bytes), re-verified by the
  Q5/Q6/geo freshness gates and bridge status after the merge. The owner's
  newer pending re-seal branch `origin/repin6` is intentionally not merged
  and remains on its own PR flow.
- Merge record (2026-09-12, second reconciliation): `origin/main` (`03f7cd4`,
  the owner's merged `repin6` re-seal) merged over the prior merge head. Its
  delta again touches only the custody/spec plane (the two `gnn-input/`
  projections, the w2 `source-pin.json`) with zero rostered source bytes, so
  the native receipt needed no re-run. The `source-pin.json` conflict again
  resolved to the wave re-seal: repin6 re-sealed against the origin lineage
  whose owner bytes pre-date the wave commits and is stale for this tree. The
  two `gnn-input/` documents are projections of the pinned sources, so the
  owner's hand-edited copies were superseded by re-emitting both models from
  the wave sources (`fep-lean bridge emit`, finite + continuous); bridge
  status reports every check fresh and the Q5/Q6/geo gates stay green.
- CI restoration record (2026-09-12): CI ruff round 2 formatted
  `rendering.py` (`b399d45`, byte-level formatting only — the d818efb
  contract is unchanged) and the render lane was restored to verify
  identifiers against the pinned template checkout; CI rounds 3–5 are
  workflow-only. The rostered byte shift invalidated the standing custody
  and evidence bindings, so the chain was re-run and re-bound at the
  formatted bytes: native verification recompiled 155/155 warning- and
  sorry-free (two-arg gate triple-True), bridge custody re-sealed, the
  publication plane re-rendered, and the hermetic acceptance plus the
  deterministic release bundle were re-validated under the new receipts.

- CI render lane accepted (2026-09-12): the `render` job passed end-to-end on
  GitHub CI twice (runs 34680452819 and 34681926826 — lean, python, and render
  all green; the render leg writes and validates fresh `docs/render-acceptance.json`
  plus `docs/render-fonts.json` in the same run over the pinned template ref),
  closing the FEP-CI-RENDER backlog row per its own probe.

### Wave-2 coordinated refactor and partial evidence refresh (2026-09-10)

Code (all receipt-digest-shifting by design; one coordinated refresh):

- Catalogue spine: `FEPTopicCatalogue` gained the sole validating
  construction path (roster/order/vocabulary asserted in `__init__`,
  `topics` frozen to a tuple); `from_yaml` delegates document/roster/family
  metadata validation to `schema.load_catalogue_metadata` (new
  `GENERATED_TOPIC_FIELDS` row-field set) and keeps only the
  generated-projection checks; one canonical Lean theorem-header regex
  (`LEAN_THEOREM_RE`) replaces five divergent copies.
- Verification layer: bridge custody `read_object` rejects duplicate JSON
  keys and non-finite constants; one strict-JSON loader
  (`verification/_jsonutil.load_strict_json`) replaces five hand-rolled
  parsers; `LeanVerifier` threads `lean_dir` into every subprocess
  environment and now delegates tool resolution to the shared
  `_toolchain` layer; Hermes preflight no longer mutates shared config
  budgets (per-call probe budgets instead); the theorem-witness endpoint
  dry-run found 89/125 edges failing a reviewed-primary-qualified rule —
  recorded as a relations-ledger review, not a code loosening.
- Output plane: shared `output/fsutil` primitives (atomic writes, digests);
  manuscript's pytest-collection evidence functions promoted to public
  names; a shared SVG presentation kernel serves atlas and dashboard; a
  versioned `RELEASE_SEAL` (plus individual constants) is the single
  definition site for the 155-topic release shape; the theorem-maturity
  projection is importable (`catalogue/theorem_maturity_projection.py`),
  removing the receipt validator's `runpy` execution of a script;
  release-bundle prerequisite passes one built presentation through both
  drift helpers; `render_manuscript` fails closed by default when the
  native receipt is not claim-ready (`--allow-unavailable-evidence` opts
  out); `summary.json` is written once (no hash-less crash window); the
  CDP WebSocket handshake closes the socket when `sendall` fails.
- Hygiene: `02_run_single_topic.py` requires an explicit topic id; the
  interpreter contract (packaging floor vs accepted 3.14 runtime) is
  documented in `src/fep_lean/README.md` and `docs/development.md`;
  per-user ELAN tempdir; `settings.yaml` `api_key` rejected; `.aii` test
  task runs under uv; the bare `index.md` gitignore is scoped to the root;
  Hermes API responses are bounded (8 MiB cap) and the wall-clock deadline
  now force-shuts the abandoned socket; `verify_batch` runs as a plain
  sequential loop; references.bib duplicate detection uses `Counter`;
  dead environment aliases removed; the status-pie palette asserts its
  arity.

Evidence refresh state (final chain, 2026-09-11 against 3ee3007): bridge custody re-pinned; native verification receipt valid/source-bound/claim-ready (155/155, formal two-arg call); formalism audit zero errors; publication plane current including the strict-default render check; browser acceptance clean; `fep-lean status` reads all four sections current with the top-level `native_claim_ready` flag derived from the section state (VI-7 fix). At this stamp the Python-acceptance plane was the remaining blocker (the hermetic environment could not run the tool-dependent lanes; see then-open TODO `FEP-EVIDENCE-CURRENT`) — superseded 2026-09-12: the owner authorized the hermetic-policy change (git + fc-list allowlist), and the close-out section above records the granted final acceptance run. Owner roster bumped
15 → 17 for the new rostered modules.

### Evidence-currency status verb and GEO-INFER notation slice (2026-09-08)

- Added the read-only `fep-lean status` verb: it composes existing
  fail-closed checks (catalogue projection drift, render-receipt defects,
  bridge source-pin binding, native-receipt validation) into one
  evidence-currency report whose every section carries its capability
  boundary; exit 0 means the report composed, never that evidence is
  current. The implementation lives in the rostered `cli.py` owner: report
  and native receipts bind a versioned source-owner roster, so a new
  `src/fep_lean/**` module would fail source-binding until a coordinated
  `OWNER_MANIFEST_VERSION` refresh.
- Added the `specs/geo-infer-notation-bridge/` slice: charter, the
  `data/notation-map.yaml` correspondence artifact (reviewed rows between
  fep_lean theorem proxies and the GEO-INFER-ACT implemented surface), and a
  slice-local deterministic checker; registered in the AGENTS required-check
  list and `docs/development.md`, which now also document the source-owner
  roster rule.
- Corrected five stale `scripts/check_geo_notation_bridge.py` references to
  the slice path after the checker moved under `specs/` (AGENTS required
  checks, development guide, slice README and checker docstring,
  notation-map header), and completed `docs/cli-reference.md`: the `status`
  verb, its exit-status boundary, `verify --receipt/--fail-on-warnings`, and
  the `emit --check/--refresh-digests` flags.

### Publication render remediation

- Made the published reproduction recipes reproduce. The conclusion's
  Reproducibility Statement, the `AGENTS.md` required-check list, `README.md`,
  `scripts/README.md`, `docs/SPEC.md`, `docs/testing.md`,
  `docs/development.md`, `docs/authorship-guide.md` and one block in
  `docs/cold-start-and-cleanup.md` ran
  `scripts/render_manuscript.py --check` with no generator ahead of it.
  `manuscript/manuscript_vars.yaml` and the generated appendix are
  `.gitignore`d build products, so on a fresh checkout the check exits 1 with
  "test collection cache is missing" before validating anything. Each block
  now runs `uv run fep-lean catalogue` first, and
  `unreproducible_command_blocks` fails the render path on any published shell
  block that reintroduces the gap -- it found five sites beyond the two that
  were reported. The generating form of `render_manuscript.py` does not
  qualify: with the projection absent it exits 1 the same way `--check` does.
- Restored the test extras the Reproducibility Statement's own first line
  removed. It opened `uv sync --locked`, which prunes the `dev` group, and the
  check it ends with counts the collected suite: running the published
  sequence verbatim gave "required pytest collection distribution is missing:
  pytest" and exit 1 from both `fep-lean catalogue` and
  `render_manuscript.py --check`. The statement and 3.6.6's checklist now say
  `uv sync --locked --extra dev`, and the same audit rejects a block whose
  sync starves the check that follows it.

- Replaced the primer's hand-typed "about 1-2 seconds" per verification with
  the receipt's own distribution. Nothing supported the range: the same PDF
  prints 14.952 s per result in the compilation chapter, and the cited receipt
  records a per-topic minimum of 2.381 s, a median of 8.982 s and a maximum of
  183.318 s, with 0 of 155 topics at or under 2 s. `verify.min_topic_s`,
  `verify.median_topic_s` and `verify.max_topic_s` now project that spread
  beside the existing mean, so the sentence is regenerated rather than typed.
- Published a verification command that runs. The primer printed `lake env
  lean lean/FepSketches/FepCheck_fep001.lean`, which exits 1 from every
  directory because no file of that name is ever created: `LeanVerifier` uses
  `tempfile.mkstemp(prefix=f"_verify_{topic_id}_")` and unlinks the result.
  The chapter now names the real argv, run with `lean/` as the working
  directory, and publishes `uv run fep-lean verify --topic fep-001` as the
  reproducible entry point. The same paragraph claimed `_wrap_lean_code`
  prepends imports, adds area-specific opens and wraps the body in a
  namespace; all 155 catalogue bodies already begin with `import` and declare
  their own `namespace FEP<NNN>`, so the wrapper returns every one of them
  unchanged. It also credited native mode with writing `VerifyResult` to
  SQLite; the session store belongs to full OpenGauss mode.

- Stopped printing catalogue row counts as theorem counts. Two sentences in
  the sophisticated-dynamics synthesis read "The {{areas.InfoGeometry.count}}
  Information Geometry theorems" and "The {{areas.BayesianMechanics.count}}
  Bayesian Mechanics theorems"; those tokens carry row counts, three lines
  below a heading that already said "Rows" and a sentence that already said
  "rows", so the rendered PDF contradicted itself on one page and understated
  its own proof totals, which `docs/formalism-coverage.json` sums per area
  from each row's `theorem_count`. Both sentences now say "rows", and
  `miscounted_area_labels` fails the render path on any `{{areas.*.count}}`
  token whose following noun names theorems, lemmas, declarations, proofs, or
  definitions, so the class cannot return through a third sentence.

- Typeset Lean's Unicode operator suffixes: the code face is JuliaMono, not
  FreeMono, which covers none of U+2098 U+2096 U+1D50 U+209A U+1D62 U+1D9C and
  had XeTeX drop all 162 occurrences silently -- printing the complement lemma
  `μ sᶜ = 1 - μ s` as the false `μ s = 1 - μ s`.
- Made the LaTeX pass fail closed. `scripts/check_render_log.py` rejects a
  render whose log records any `! ` error or `Missing character`, a mermaid
  diagram that shipped as verbatim source, a combined build older than its own
  manuscript sources, an uncaptioned table, or a contents number that overflows
  its number box. The shared template's own success test looks for four fatal
  markers and passes all of these.
- Gave every line break a cue. `\seqinsert` now emits a discretionary carrying
  a grey continuation arrow, so a table cell can no longer print
  `FEP.FiniteKernel.comp_assoc` as `FEP.Fini` / `teKernel.comp_assoc`; fvextra
  gains `breaknonspaceingroup`, without which `breaklines` was inert for every
  Lean listing because pandoc wraps each token in a macro.
- Widened the contents number columns. `article`'s default
  `\@dottedtocline` widths are too narrow for numbering that reaches
  `15.100.1`, so 224 contents lines printed as `15.100fep-100`.
- Captioned all 36 tables and the pipeline diagram. The combined build had 36
  `longtable`s and six captions, all six on figures, so no table carried a
  number any prose could cite; the one Mermaid diagram shipped as
  "Figure 3: Mermaid diagram", the template's placeholder.
- Carried `manuscript/config.yaml`'s subtitle and fifteen keywords into the PDF
  `/Info` dictionary, and made `scripts/render_manuscript.py` fail closed when
  the preamble copy drifts from the config (`pdf_metadata_drift`).
- Replaced the hand-maintained "Mathlib navigation hint" column with each
  row's own imports. Forty-two of its 71 cells named a module the row never
  imports -- `fep-023` advertised
  `MeasureTheory.Measure.Typeclasses.Probability` against a body that imports
  `Mathlib.MeasureTheory.Measure.MeasureSpace` -- because nothing recomputed a
  cell when a body moved an import. Every cell is now
  `{{topics.fep-NNN.imported_modules}}`, produced from the same regex and
  source as the coverage report's incidence table;
  `hand_maintained_module_cells` fails the render path on a literal typed back
  in, and `unknown_topic_import_modules` checks the relation itself against the
  pinned Mathlib.
- Stopped a catalogue theorem reading as Mathlib prior art, and made the
  allowlist that hid it self-checking. `manuscript/04b_framework_active_inference.md`
  said fep-008's proof used "`min_agrees_on_value` plus `le_antisymm`", between
  two real Mathlib names; `grep -rl min_agrees_on_value
  lean/.lake/packages/mathlib/Mathlib` matches nothing, because the name is
  this catalogue's own `fep008_min_agrees_on_value`
  (`src/fep_lean/catalogue/bodies/core_active_inference.py`) printed without its
  prefix. It evaded the reference audit only by sitting in
  `NON_CATALOGUE_IDENTIFIERS` under the comment "Mathlib declarations cited as
  prior art", which made that set's own header claim -- "Every entry is a
  reviewed exception" -- false. The prose now attributes each step to its
  owner, the entry is gone, and the set is split into three provenance groups
  that `unverified_non_catalogue_identifiers` checks against their sources: a
  Mathlib citation against the names the pinned checkout introduces (a
  declaration header, or a quoted token -- no `theorem`/`def` header carries
  `norm_num`; the tactic's name reaches the reader as the literal in
  `elab (name := normNum) "norm_num" ... : tactic`), a local citation
  against `src/fep_lean/formal`, and a record field against `TopicEntry`.
  `scripts/render_manuscript.py` fails on an unverifiable entry and prints an
  explicit "unchecked" line when the pinned library is absent rather than
  passing the group in silence.

- Gave the acceptance somewhere to bite. `scripts/check_render_log.py` was a
  real, tested check that nothing ran: `grep -rn check_render_log
  --include="*.yml" .github/` matched nothing, so every defect it catches could
  reach `main` unopposed. CI cannot re-run it, because CI does not render this
  manuscript: that needs a checkout of the shared template, XeLaTeX, pandoc,
  `rsvg-convert`, the mermaid CLI and the two faces the preamble selects. So a
  clean acceptance now writes `docs/render-acceptance.json` and CI runs
  `--verify-receipt` against it. The
  receipt is bound to a digest over every typeset manuscript source plus
  `manuscript/preamble.md`, so a chapter or a font selection changed without a
  fresh render fails CI; it is not bound to the values a `{{token}}` resolves
  to, which `manuscript_projection_drift` and `stale_render_defects` own on the
  render path. A rejected render writes no receipt and withdraws the standing
  one: sources can drift out of a render without changing, so the digest alone
  would let a superseded receipt keep vouching. The digests are recorded per
  file, so a stale receipt names what moved instead of printing two hashes.
- Made the publication entry point fail closed. `scripts/render_publication.py`
  runs the shared template's render stage and this repository's acceptance and
  exits on the conjunction, so a render the template calls successful over a
  dirty log is rejected here. The template compiles with
  `-interaction=nonstopmode` and tests four fatal markers; it is a separate
  repository, and `_pdf_latex_pipeline._check_fatal_error` still fails open
  upstream (as does `_pdf_mermaid.py`'s `render_disabled_reason` branch, which
  warns where the missing-`mmdc` branch raises).
- Recorded and probed the font requirement the render depends on. The R1 fix
  was a font installed on one machine and nothing in the checkout said which
  glyphs the document needs, so a render elsewhere would regress identically
  and silently. `docs/render-fonts.json` is derived from the sources and
  `--check`ed in CI; `scripts/build_render_fonts.py --probe` asks the host's
  fontconfig whether the selected faces cover the set, and
  `render_publication.py` runs it as a preflight.
- Judged render staleness by content instead of modification time, over every
  authored source rather than the ones a clock singles out. The first guard
  failed the delivered artifact because regenerating two files to
  byte-identical content moved their mtimes, and it could not have caught the
  opposite case at all: the template renders from `output/manuscript` when that
  directory exists and its hydration hook does not fire for this project, so a
  render made after two chapters were fixed reproduced their drift exactly
  while being newer than every source. The verdict is now whether each source's
  own lines, substituted the way the renderer substitutes them, are lines of
  the combined document -- and `render_publication.py` renders the authored
  sources itself before handing off to the template. Lines carrying a
  `{{source.*}}` stamp are exempt: they name the commit and date of one render,
  so no committed projection can agree with them, and a line whose markup the
  renderer consumes (the italic caption under a diagram fence becomes that
  figure's `\caption`) counts as rendered when its text is in the document.
- Linked into the repository through a ref that resolves. Five source links
  were pinned to a commit that existed only locally, so all five 404ed in the
  published PDF; they now resolve through the commit once it is on the remote
  and through the default branch until then, and the front matter prints which
  (`{{source.published_note}}`).
- Made an undisclosed release-stamp mismatch fatal. Between releases the
  checkout is always ahead of the stamped tag, so the mismatch cannot be the
  failure -- saying nothing about it can be, and the audited PDF stamped v1.1.0
  over a tree 15,033 Lean lines newer with nothing on the page to say so.
- Restored the green `ruff check` / `ruff format --check` gate that the render
  and audit fixes had broken (6 findings, 8 unformatted files).

- Hardened every production Lean/Lake probe against orphaned-grandchild
  timeouts: new `src/fep_lean/verification/_subprocess.py` runs each external
  probe in its own process group with a watchdog `SIGKILL` of the whole group
  on deadline (mirroring the test-suite's `run_lean_probe`), wired into the
  verifier compile probe, the declaration/axiom audit probes, and the `setup`
  bootstrap/lake commands. A wedged `lean`/`elan` grandchild can no longer
  hold the pipes and the `.olean` lock region past the advertised deadline.
- Made the theorem LaTeX projection fail closed: an unextractable statement
  raises instead of silently emitting a `\mathsf{?}` placeholder into the
  generated appendix.
- Extended generated-catalogue parity: `from_yaml` now also asserts
  `latex_equations` against `registry.LATEX_EQUATIONS`, matching the existing
  `lean_sketch` contract, wherever the catalogue is loaded (including wheels).
- Extended the coverage join to fail closed when a `theorem_maturity.yaml`
  primary/supporting/boundary reference is not a resolvable formal
  declaration (qualified namespace form).
- Preserved line numbers when the manuscript reference audit strips fenced
  blocks, so reported locations match the real file.
- Unified OpenGauss state-directory resolution (`resolve_gauss_home`:
  `GAUSS_HOME` → `config/settings.yaml` `gauss.home` → `~/.gauss`) across the
  SQLite client, `GaussRunner.create_default`, preflight validation, and the
  Hermes dotenv loader's home, so validation always checks the directory the
  run writes.
- Guarded CITATION.cff publication metadata: `docs/citation_audit.py` now
  fails when the CFF `version` drifts from the pyproject package version
  (same drift class as the toolchain pin audit).
- Output layer: atlas/dashboard/figure writers now render through atomic
  temp-file + `os.replace` semantics like every other projection writer; the
  dashboard y-axis label derives from the actual plotted floor instead of a
  hardcoded `0`; `latest_claim_ready_full_report` orders candidate reports by
  the deterministic run-id directory name instead of filesystem mtime; the
  reporter run-id helper drops the inline `__import__` and uses a tz-aware
  timestamp; and the stale `_write_sorry_distribution` figure helper is
  renamed to `_write_status_distribution`.
- Catalogue loaders fail closed: `FEPTopicCatalogue.summary()` raises on an
  unknown `mathlib_status` instead of silently counting it as `partial`, and
  the roster seal rejects `first_id` below `fep-001` (the canonical interval
  definition shared with novelty loading).
- Tests: the `serial_lean` marker now pins Lean-probe tests to a single xdist
  group via `pytest_collection_modifyitems`; live OpenRouter tests are
  strictly opt-in (`FEP_LEAN_LIVE_TESTS=1` required, never inferred from key
  presence); the Hermes deadline-abort ceiling allows scheduler slack; the
  future-mtime manuscript test stamps both times from one clock; and new
  `tests/test_core_body_modules.py` pins the five core_* body modules'
  exact rosters.
- Docs: scoped `formal/README.md`'s audit-inclusion claim to public theorems
  (private helpers are covered transitively), refreshed the stale
  `.ruff_baseline.txt` narrative, and removed six dead no-op LaTeX rewrite
  rules whose inputs were consumed by earlier loops.
- CI: added the `docs/lean-landscape.md` drift gate
  (`scripts/_maint_build_lean_landscape.py --check`) to the projection-check
  step and a least-privilege `permissions: contents: read` block.
- Tests: replaced the nip.io DNS dependency in the OpenRouter fallback test
  with a loopback httpserver plus an explicit `_build_model_chain` patch.

- Accepted H1.0--H1.8 of the dependency-gated Horizon research program, with
  optional H1.5 accepted separately. The archived
  [Horizon 1 record](specs/done/horizon-1-finite-synthesis/README.md) preserves
  the first H1.8 carrier-merge no-go and the repaired terminal theorem: one
  finite, synthetic, one-step posterior--decision--action certificate on a
  shared 16-state Boolean carrier, with a genuine sensory--active blanket and
  same-kernel strict real/native KL decrease.
- Kept the Horizon 1 exit claim narrow. It is not transition-aware planning,
  EFE-optimal control, physical thermodynamics, causal identification,
  empirical validation, or a universal FEP theorem.
- Advanced Horizon 2 through accepted H2.0--H2.3b, H2.4a/b,
  H2.5a/b/c/d (including H2.5b-R0 and H2.5d-R0), H2.6a/b/c, and H2.6a-R0:
  fixed-variance scalar Gaussian KL and coordinate geometry, local smooth
  duality, native kernel/action semigroups with the exact H1 lift, a scalar OU
  transition semigroup, a same-joint native posterior martingale with its
  limiting-observation conditional-expectation endpoint, selected-model
  identification, joint-law and fixed-truth posterior consistency, weak
  convergence to the sampled-parameter Dirac law, bounded-continuous transfer,
  bounded zero-one risk convergence, and monotone
  finite-grid path laws with support-aware
  forward-to-coordinate-reversed KL boundaries. Dynamic `Fin 4` transition
  covariance is derived generically by the accepted H2.5b-R0 spectral repair;
  the maintained H2.5b owner now constructs the native finite-axis Markov
  semigroup, invariant Gaussian, moments, full-time weak limit, and exact
  `Fin 1` H2.5a specialization while preserving the historical H2.0 no-go.
  The accepted H2.6a-R0 repair proves the selected scalar Gaussian
  density factorization, joint-law and evidence-marginal identities, and
  evidence-a.e. equality to Mathlib's native posterior; the maintained H2.6a
  owner adds exact posterior parameters, normalization, and chronological
  finite observation recursion. H2.5c now instantiates the preregistered
  external--sensory--active--internal carrier, derives its covariance, exact
  transition laws, invariant Gaussian, weak limit, and scalar specialization.
  The accepted H2.5d-R0 repair orthogonalizes the centered stationary law.
  Maintained H2.5d reconstructs the arbitrary-center blanket/endpoints
  `compProd`, identifies native pair and scalar conditionals blanket-marginal
  almost everywhere, proves endpoint `CondIndepFun` while retaining actual
  marginal covariance `1 / 24`, and derives a fixed bivariate precision
  perturbation with actual covariance `-1 / 15` and native non-independence.
  It claims no generic precision equivalence, transition-row conditioning,
  causal blanket, reversibility, H2.7 theorem, or H3 result.
  H2.6b now derives one-step posterior-predictive quadratic risk from the actual
  selected transition, proves finite attainment and evidence-a.e. native
  selector agreement, and supplies strict and tie witnesses without claiming
  policy-tree, reward--EFE, global Bayes-estimator, or infinite-horizon control.
  The H2.3b same-law countermodel keeps the native posterior equal to the prior
  only almost everywhere under the predictive law, and no entropy, logarithmic,
  unbounded-observable, rate, arbitrary-prior, continuous-parameter, or tail-field
  claim was introduced.
  No SDE, Fokker--Planck, Girsanov, continuous-path, reverse-OU, or physical
  entropy-production claim was introduced.
- Resliced and accepted the H2 terminal proof gate. H2.7-R0 proves actual
  Lebesgue-density evidence surprisal, recognition-to-exact-posterior native
  KL, the mean-coordinate Fisher-metric-dual natural-gradient tangent, and
  strict local descent. Its append-only source-bound decision opens H2.7 only;
  H3 remains closed pending the connected terminal merge and review.
- Added a deterministic manuscript author block and graphical abstract under a
  strict metadata, digest, dimension, and rendering contract. These changes,
  together with the accepted post-release H1/H2 source wave, deliberately
  invalidate the v1.1.0 evidence receipts for the live checkout until
  `FEP-EVIDENCE-CURRENT` is completed.
- No post-v1.1.0 theorem, manuscript, or generated artifact is part of the
  immutable v1.1.0 release. A later release must choose its own version and DOI
  only after the connected theorem and source-bound evidence gates settle.
- Refreshed the deterministic offline evidence surface after the post-v1.1.0
  source wave (`fep-evidence` lane): catalogue stage exit 0, formalism coverage
  regenerated (52 maintained formal modules, 33 foundation modules, 1480 total
  theorem declarations, 226 composed theorem declarations, including the new
  `FepSketches.ness_flow` and `FepSketches.compositions.smooth_reference_kernel`
  owners), atlas and formal-kernel dashboard projections regenerated and
  byte-current, theorem-maturity projection current, manuscript render check
  passing with every authored placeholder resolved. Native Lean compile sweep
  and Hermes/OpenGauss receipts remain deferred to the coordinator.

### CI integrity and maintenance accuracy (2026-09-07)

- Fixed the red `main` CI. The projection-check step ran
  `scripts/build_render_fonts.py --check` before `uv run fep-lean catalogue`
  had materialized the gitignored generated appendix
  (`manuscript/09z_unified_formalism_catalogue.md`), so every fresh checkout
  derived a smaller glyph set than the committed `docs/render-fonts.json` and
  the workflow reported a false STALE. The check now runs after the catalogue
  step, and requirement derivation fails closed on its own: without the
  generated appendix, `render_font_projection` and `font_coverage_defects`
  raise `FontProbeError` naming the remedy instead of silently deriving an
  understated requirement that every later check would accept.
- Closed `FEP-H2-SMOOTH` per the backlog closure rule: H2.7 and its R0 proof
  gate are accepted with terminal evidence in the Horizon 2 spec (328
  mandatory cases, the enabled Fin4 supplement, three source-bound reviews).
  Remaining H3 work stays under `FEP-H3-SCIENCE`. The backlog gains three
  cold-startable major rows: `FEP-CI-RENDER`, `FEP-LEAN-UPGRADE`, and
  `FEP-RELEASE-NEXT`; `FEP-EVIDENCE-CURRENT` now names the settled owner
  roster (bridge contract v0.6, GNN 3.3.0 route rename re-pin).
- CI hygiene: `concurrency` groups with PR cancellation, `timeout-minutes` on
  every job, a coverage-report artifact, a pinned `elan-init` commit plus an
  elan-toolchain cache, and a deduplicated failure issue from the weekly
  pin-audit schedule, whose result previously went to nobody. Actions moved
  to current majors: checkout@v7, upload-artifact@v7, setup-uv@v10.0.1 (no
  rolling v10 major tag exists), cache@v6, github-script@v9.
- Moved `scripts/render_manuscript.py --check` to the lean CI job, after the
  Mathlib cache fetch: its Mathlib-citation allowlist verification fails
  closed when `lean/.lake/packages/mathlib` is absent, which made the check
  unpassable in the Python job on every fresh checkout (masked behind the
  font-check STALE, which died first). The job also runs
  `uv run fep-lean catalogue` first, because the generated manuscript inputs
  do not survive across jobs.
- Made the Python CI suite finish at all: the post-v1.1.0 wave had never
  reached a green CI run, so three latent host dependencies surfaced once
  the earlier steps stopped dying. `.python-version` pins CPython 3.14 —
  the Q7 runner-scaffold digest freezes `ast.dump` output, which is
  interpreter-sensitive, and the reviewed digest was pinned under 3.14 (a
  3.12 interpreter computes a different digest and fails all 22 scaffold
  tests). The two manuscript-rendering tests that drive the real render
  path against the real tree (pinned Mathlib checkout, generated figure
  rasters) are `serial_lean` workspace tests now, and the host-font
  coverage probe skips CI runners, whose fontconfig resolves a glyphless
  JuliaMono stub; the render-host preflight
  (`scripts/build_render_fonts.py --probe`) remains the font acceptance.
- Documentation accuracy: `--gnn-root` documented as required for every
  `bridge` verb; the README/AGENTS/SPEC check lists now match what CI runs
  (`docs/pin_audit.py --check-latest`, `uv lock --check`, the
  `build_render_fonts.py --check` gate, and the `-m "not serial_lean"` pytest
  filter); HANDOFF's H2.7 status paragraph and its bridge-contract version
  (v0.4 → v0.6) refreshed against the tree. Dependency bumps were attempted
  and reverted: the Horizon predecessor receipts bind `uv.lock` bytes, so a
  lock refresh without the coordinated evidence re-pin fails the acceptance
  chain fail-closed (see `FEP-EVIDENCE-CURRENT`).
- Follow-up parity sweep after an adversarial doc review: the README, AGENTS,
  SPEC, HANDOFF, testing, development, and cold-start check lists now name the
  exact CI invocations for the atlas and formal-kernel dashboard projections
  (the generator `--check` scripts, not the CLI freshness forms), and carry the
  render-acceptance receipt verification, the lock check, the
  `--check-latest` pin audit, and the `-m "not serial_lean"` pytest filter
  wherever the corresponding recipe appears. The `FEP-SCAFFOLD-PORTABILITY`
  backlog row now scopes only the Q7 scaffold digest (Q5's runner custody is
  whole-file sha256 and already interpreter-independent).

## 1.1.0 — 2026-08-23

### 155-topic formalism expansion and release acceptance

- Extended the maintained schema-2 roster beyond `fep-120` through `fep-155`,
  yielding 155 stable topics in 20 families across the five established areas.
  The five new families cover finite-sample Laplace/Brier risk, closed-loop
  policy trees and treewise EFE, finite-to-native blanket transfer, finite
  exponential-family dual geometry, and exact two-state continuous-time
  thermodynamics.
- Added one reusable foundation and one seven-theorem composition leaf for each
  family. The new rows name explicit assumptions and non-vacuity boundaries:
  nonzero Laplace bias, a strict Boolean feedback advantage, a correlated
  nondegenerate blanket model satisfying native `CondIndepFun`, positive and
  zero Fisher-information witnesses, and a strictly decreasing nonstationary
  Lyapunov example.
- Expanded the typed numerical dashboard from ten to fifteen family witnesses.
  Each witness now owns multiple typed checks with independent tolerances;
  acceptance is their conjunction plus a named boundary observation.
- Added the authored 155-topic manuscript chapter with theorem names,
  assumptions, composition bridges, evidence-plane boundaries, and primary
  sources for Brier risk, sophisticated inference, information geometry, and
  the pinned Lean/Mathlib releases.
- The release-snapshot schema-4 formalism audit independently validates all 823 required
  formal-resource declarations, including 699 evidence declarations, under
  Lean 4.33.1 and the locked Mathlib revision with zero warnings, no `sorryAx`,
  and no untrusted axiom. The release-snapshot native receipt validates the exact 155
  topic roster with zero failures, warnings, or `sorry`; the schema-3 Python
  receipt binds the complete canonical collected-node roster, records zero
  failures or errors, and enforces the maintained 89% line-coverage floor;
  and the schema-4 browser receipt replays six accepted
  screenshots against all 20 families and 15 typed numerical witnesses. The
  retained 50-topic provider report remains historical and was not promoted to
  full-mode evidence for that release snapshot. Later source waves must
  regenerate every receipt before making a current-source claim.

### Prior 120-topic expansion and family-owned formal sources

- Advanced the schema-2 roster seal from `fep-050` through `fep-120`, yielding
  120 reviewed topics in 15 families across the five established areas. The
  expansion adds measure-theoretic Bayesian inversion, variational duality and
  information bounds, controlled and temporal inference, causal interventions,
  generalized predictive coding, path thermodynamics, geometric optimization,
  collective inference, and learning/model-evidence families.
- Replaced the monolithic body owner with family modules under
  `src/fep_lean/catalogue/bodies/`. One explicit registry validates namespace,
  declaration, ordering, uniqueness, and roster parity; theorem signatures are
  projected separately from the canonical bodies.
- Added a maintained novelty ledger for every expansion row. Each record names
  earlier nearest topics, its invariant and carrier delta, and a required
  `FEPComposed` bridge. Cross-topic witnesses now live in manifested leaf
  composition modules, with `composed.lean` reduced to an import-only aggregate.
- Added explicit finite path-law, fluctuation, Jarzynski, reversible-dissipation,
  categorical Fisher, Cramér--Rao, natural-gradient, mirror-descent,
  Bregman-projection, replicator, collective-agent, consensus, concentration,
  PAC-Bayes, posterior-concentration, regret, and Bayes-factor surfaces with
  named support and non-vacuity boundaries.
- The generated coverage, maturity audit, atlas, dashboard, and manuscript
  projections own all live counts. The 50-topic native, declaration, and full
  reports below are retained as historical evidence for their exact source
  snapshot and do not bind the expanded roster.

### Prior 120-topic acceptance evidence (historical source snapshot)

- Migrated the exact reproducibility pins to the newest stable pair, Lean
  4.33.1 and Mathlib `v4.33.1`, with resolved Mathlib revision
  `0df444a360eaa60ab8c11dca51a86af692955474`. Added a fail-closed networked
  latest-compatible-pair audit to pull-request CI and a scheduled weekly check;
  newer Lean-only patches remain visibly pending until a matching Mathlib tag
  exists, and release candidates or nightlies never replace the stable compiler.
- Updated the canonical calculus bodies for Lean 4.33's stricter elaboration,
  replaced deprecated square-root imports, migrated fep-036 from the retired
  PMF binomial API to Mathlib's measure-valued binomial distribution, and made
  every affected topic compile independently rather than borrowing aggregate
  imports. The complete `FepSketches` closure builds warning-free in 8,732 jobs.
- The source-bound native schema-4 receipt independently validates 120/120
  topics with zero warnings, zero `sorry`, and a 334.632-second duration under
  Lean 4.33.1 and the resolved pinned Mathlib revision.
- The schema-4 declaration audit independently resolves 647/647 audited
  declarations, including 558 structured evidence declarations, with zero
  warnings, no `sorryAx`, and trusted axiom policy version 1.
- The complete Python suite passes with 744 tests passed, 22 skipped, and
  90.62% coverage. Strict MyPy, Ruff, formatting, lock/install compatibility,
  projection freshness, manuscript rendering, links, pins, cross-references,
  theorem references, and 73-entry citation coverage were green for that
  snapshot.
- Six retained standalone, desktop, and mobile atlas/dashboard captures passed
  fresh unprimed visual review. The browser receipt verifies all five areas,
  15 families, 120 topics, 98 scientific relations, 43 satisfied capabilities,
  ten numerical witnesses, search/filter/keyboard behavior, zero external
  assets, and no body overflow.
- No new provider run was made for the expanded source. The retained 50-topic
  full report and two earlier one-topic smokes remain historical evidence only.

### Prior 50-topic semantic milestone (historical source snapshot)

- Deepened all 50 catalogue rows to directly formalized, deliberately bounded
  topic scopes. The final fep-036 promotion adds Mathlib's finite binomial PMF,
  an outcome-indexed Laplace prior, exact shrinkage, consistency transfer from
  convergent empirical frequencies, and posterior closure while explicitly
  excluding an unproved LLN, finite-sample risk, or marginal-likelihood claim.
- Added exact theorem families for native posterior inversion, normalized
  filtering and hierarchy; Bernoulli Fisher information, natural gradient,
  Fisher--Rao distance, and Hellinger divergence; measurable semigroups,
  quadratic convergence, finite stationary currents, Gaussian entropy and
  Helmholtz calculus, finite stick conservation, and matrix message passing.
- Expanded the canonical composed module to 22 declaration-witnessed seams
  spanning inference, information geometry, policy choice, dynamics,
  thermodynamics, and partition-energy conservation. The generated capability
  ledger now resolves all 33 retained nodes without erasing broader scientific
  limitations that remain outside those bounded capabilities.
- Expanded the joined formal surface to 412 theorems, 175 definitions, 10
  abbreviations, and 8 structures: 257 topic theorems plus 155 theorems in six
  foundation modules and the composed module. The authored graph now contains
  20 theorem-witnessed formal relations and 8 conceptual relations, with all
  33 retained capabilities satisfied at their deliberately bounded scopes.

### Prior publication and validation surfaces

- Added a semantic-closure manuscript chapter that embeds the generated SVG
  atlas, links its offline interactive counterpart, and presents the six
  executable theorem strands plus the seven-layer validation contract.
- Made manuscript rendering copy and rewrite declared atlas assets into the
  build tree and fail closed before writing when a referenced visual is
  missing. Zero-valued relation and capability buckets are now retained in the
  manuscript variable schema so placeholders cannot disappear at closure.
- Reconciled the manuscript and background documentation with the live native
  posterior, Bernoulli geometry, finite NESS, response, entropy-production,
  Gaussian, and Landauer theorems while preserving the continuous,
  multidimensional, empirical, and microscopic boundaries.
- Removed copied fallback-table counts from the atlas renderer. The accessible
  node and relation summaries now derive from the live graph, and regression
  tests pin their parity.
- Applied an independent desktop/mobile visual critique: the evidence inspector
  now precedes a bounded pan viewport, canonical totals remain visible outside
  the scroll plane, graph typography renders at a readable scale, panning is
  explicitly signposted, and every thin edge has a wide transparent pointer
  target. Exact 1440x900 and 390x844 acceptance captures are retained with the
  closed rationale.

### Prior independent failure-seam hardening

- Repaired `review` as an ordered two-turn workflow: the first provider turn
  must emit refinable Lean, the exact compiled result is supplied to a
  contradiction-free prose-only review prompt, both turns are persisted and
  separately cached, and review failure now fails the requested workflow.
- Propagated native Lean warning lists through `TopicRunResult`, pipeline
  completion/statistics, summary/run/verification manifests, Markdown reports,
  and independent receipt reconciliation. A warning-bearing full row can no
  longer be counted as verified.
- Made declaration evidence fail closed when Lean exits zero but omits one or
  more `#print axioms` results. The multiline parser now handles Lean's hard
  wrapping, normalizes the complete canonical declaration closure, and the
  validator independently checks return code, counts, resolution, axiom parity,
  warnings, `sorryAx`, toolchain, digest, and failure state.
- Made the installed console boundary explicit: imports/resources and help are
  wheel-native, while substantive commands require and validate a source
  checkout. The isolated-wheel smoke now proves both the fail-closed no-root
  path and a real explicit-root `atlas --check` command.
- Bound the repository report-receipt adapter to a live source root by default
  and exposed `--project-root` for explicit independent validation.

### Historical 50-topic evidence state

The following receipts and counts describe the earlier source snapshot that
they hash. They are not current acceptance evidence for the 155-topic cut.

- The historical coverage and theorem-maturity projections for that source
  snapshot recorded all 50 bounded semantic dispositions as
  `formalized`, 48 distinct Mathlib imports, 104 topic-import edges, 28 authored
  relations, and 33/33 satisfied retained capabilities.
- The source-bound native schema-3 receipt independently validates 50/50 topics
  with zero warnings, zero `sorry`, and a 100.446-second duration. The
  schema-4 formalism receipt independently resolves 262/262 declarations,
  including 243 evidence declarations, with zero warnings, no `sorryAx`, and
  trusted axiom policy version 1. The aggregate Lake target completes 8,257
  jobs cleanly.
- The owner-manifest-2 full report
  `output/reports/run_20260820_183143_709998` independently validates as
  schema 3, source-bound, complete, and claim-ready. Gemini 3.7 Flash completed
  all 50 selected topics: 50 Hermes successes, 50 preserved semantic
  declaration contracts, and 50 direct provider Lean compiles, with zero
  warnings, zero `sorry`, and zero network retries.
- The full run used 133,519 tokens and completed in 496.386 seconds, including
  418.745 seconds of Gauss sessions and 75.37 seconds of manuscript artifacts.
  Independent receipt validation checked all 56 hashed artifacts without an
  error.
- Two bounded one-topic OpenRouter/Hermes full-mode smokes completed against
  earlier source snapshots: `fep-001` with Kimi K2.6 and `fep-002` with Gemini
  3.7 Flash. Each selected topic passed its then-current provider, Gauss, and
  Lean path. The present validator rejects both report directories because
  they predate the current report-receipt schema and their source/configuration
  digests no longer match the live tree. They are not claim-ready evidence for
  the final source or the complete 50-topic catalogue.
- `FEP-FULL-002` and `FEP-PROV-003` were complete for that snapshot. The
  historical run stored no provider secret and granted no authority for a
  later release.

## Development snapshot — 2026-08-19

### Package and canonical ownership

- Replaced collision-prone loose top-level modules with one installable
  `fep_lean` namespace, package-relative imports, packaged catalogue data, and
  an isolated wheel/import/console-script contract.
- Split maintained catalogue metadata, semantic review, canonical Lean bodies,
  and generated projections into typed single-owner seams. Regeneration now
  preserves the checkout and wheel catalogue bytes deterministically.
- Added a strictly validated authored formalism graph with explicit
  `conceptual`, `formal`, and `blocked_by` edge kinds. Formal edges require
  qualified Lean witnesses, and capability nodes retain open/partial/satisfied
  resolution history with declaration evidence. Its generated coverage report
  records 50 topics, 227 topic theorems, 18 definitions, 15 abbreviations, 37
  distinct Mathlib imports, 98 topic-import edges, 31 authored relations, 3
  composed theorems, and 14 capability nodes.

### Formal kernel and semantic depth

- Replaced scalar KL stand-ins in fep-002 and fep-014 with pinned Mathlib
  `InformationTheory.klDiv` facts, including native nonnegativity,
  self/zero characterization, VFE bounds, and the composition-product chain
  rule. The absent-at-pin data-processing theorem remains an explicit gap.
- Replaced fep-048's implication-shaped premise with Mathlib's native
  `ContractingWith` fixed-point API, a satisfiable real-line halving witness,
  unique-zero theorem, and convergence of every halving iterate.
- Added direct quadratic Bregman identity/nonnegativity/zero characterization
  to fep-029 and normalized finite Boltzmann–Gibbs weights to fep-031.
- Added native conditional-independence symmetry/non-vacuity (fep-009),
  reversible-Markov-kernel invariance (fep-010), binary entropy
  maximum/equality (fep-030), and strict two-point Jensen for logarithm
  (fep-035).
- Added the canonical packaged `FEPComposed` module. Its witnessed theorems
  compose fep-002 with fep-014's KL chain rule and fep-031's two-state
  zero-inverse-temperature Gibbs law with fep-030's binary entropy maximum.
- Removed all project-owned Lean warnings without suppression and made warning
  rejection part of the native verifier and CI contract.
- Reclassified only the exact narrowed results supported by source. The current
  semantic census is 9 `formalized`, 13 `conditional_proxy`, 6
  `structural_proxy`, 5 `proxy`, and 17 explicit `scope_gap` rows.

### Evidence, manuscript, and audit integrity

- Added atomic, source-digest-bound native Lean receipts and kept their
  `native_claim_ready` predicate distinct from catalogue completion and
  claim-ready full Hermes/OpenGauss reports.
- Replaced in-place manuscript substitution with fail-closed source-to-build
  rendering. Missing, stale, partial, or tampered evidence renders explicit
  unavailability rather than zero-valued success prose.
- Added deterministic formalism coverage, theorem-reference, citation, and
  placeholder audits to CI. All 59 bibliography entries are both indexed and
  cited, and every canonical `fepNNN_*` manuscript reference resolves.
- Added a deterministic, offline formalism atlas rendered from the same
  coverage join: a publication-safe SVG plus searchable, filterable,
  keyboard-accessible HTML with complete node/edge tables. The evidence-first
  view defaults to theorem-witnessed edges, exposes non-color status labels and
  line-style semantics, wraps topic titles, labels proved compositions, and
  expands its inspector only on demand.
- Added a native formalism audit that resolves every primary and graph-evidence
  declaration, records `#print axioms` results, and fails on stale projection,
  compiler errors, warnings, timeouts, or `sorryAx`.
- Reconciled the manuscript and background documentation with the exact Lean
  statements, semantic dispositions, evidence classes, and primary sources;
  removed completed-Hermes, universal-FEP, KL-availability, thermodynamic,
  NESS, information-geometric, and dependency overclaims.

### Local acceptance

- Full Python/coverage gate: 409 collected, 406 passed, 3 intentionally
  skipped, 90.77% coverage against the 89% floor.
- Mypy passed for 39 source files; Ruff and format checks passed for all 157
  checked files; lock and installed-dependency checks passed.
- Wheel and source distributions built successfully with the packaged
  catalogue and canonical composed Lean source.
- Aggregate Lean build completed 8,251 jobs with no project warning.
- The independently validated native receipt records 50/50 clean topics, zero
  warnings, zero `sorry`, Lean/Mathlib v4.29.0, and 106.732 seconds.
- The declaration audit resolves 56/56 primary/composed declarations and all
  12 evidence declarations, with no warnings or `sorryAx`.
- All generator, link, Markdown, pin, cross-reference, theorem, citation, and
  manuscript-placeholder gates passed. Catalogue mode remained honest at zero
  verified topics.

### Still externally gated

- Full preflight passes every local capability and fails only because neither
  `OPENROUTER_API_KEY` nor `ANTHROPIC_API_KEY` is configured. The live
  Hermes/OpenGauss smoke, complete run, and final full-report receipt remain
  open; no credential, provider call, commit, push, or publication occurred.

## Development snapshot — 2026-07-31

### Verified in the local audit

- Repaired bounded Lean setup so it resolves the declared Lean 4.29.0
  toolchain directly, acquires Mathlib v4.29.0, and fails rather than masking
  installer or build errors.
- Built `FepSketches` successfully and passed the native 50-topic compile
  sweep with no compile errors or `sorry` results.
- Repaired the documented `scripts/03_lean_verify_only.py` path by adding the
  first-class `fep-lean verify` command, which performs the same 50-topic
  native sweep without Hermes or OpenGauss.
- Hardened full-mode fail-closed behavior, Hermes preflight budget restoration,
  SQLite session cleanup, selected-topic report denominators, nested artifact
  hashes, and custom manuscript output-root isolation.
- Added the strict `mypy` development gate and reconciled the test census at
  342 collected tests across 30 modules.
- Reconciled repository documentation and operator metadata with the 1.0.0
  checkout.
- Added `HANDOFF.md` with the next-reviewer protocol, evidence receipt, and
  remaining extension scope.
- Added a maintained semantic review for all 50 theorem proxies in
  `config/theorem_maturity.yaml`, with generated Markdown, theorem-name parity
  validation, explicit non-vacuity and assumption reviews, and native Lean
  acceptance probes. The audit records scope gaps honestly and changes no
  `mathlib_status` claim.
- Added the read-only `validate_report_receipt` API and
  `scripts/verify_report_receipt.py`. It recomputes every listed artifact hash,
  rejects report-directory escapes, and reconciles summary, run, and
  verification manifests. A real complete full-mode receipt is still required
  before FEP-PROV-003 can close.
- Re-ran `uv run fep-lean verify`: `complete: true`, 50/50 clean native Lean
  results, no `sorry` results. The catalogue CLI receipt also passed the new
  independent checker with `mode: catalogue` and `verified_topics: 0`.
- The complete Python gate passed with `339 passed, 3 skipped`, 90.24% line
  coverage, and 342 collected tests; strict receipt failure paths, including
  malformed boolean flags, are covered without lowering the 89% threshold.
- Recorded the Ruff policy decision in `docs/quality.md`: the current 216
  findings (down from the prior 222-finding baseline) are explicitly
  non-gating until Ruff is pinned, debt is reduced in staged batches, and the
  exact check and format commands run in CI.

### Still externally gated

- A permitted `OPENROUTER_API_KEY` or `ANTHROPIC_API_KEY` is still required to
  exercise the live Hermes/OpenGauss/Lean full-mode smoke and complete-catalogue
  runs. No credential is stored in this repository.

## Development snapshot — 2026-07-31 (revision 2)

### Improvements from Mahakala adversarial review

- **AGENTS.md**: Added Terminology section defining "sketch" (Lean code body)
  vs "proxy" (theorem statement). Documented `complete: true` semantics for
  `FEP_LEAN_MAX_TOPICS` subset runs. Added `preflight` JSON stability note.
- **README.md**: Added "why 50" provenance sentence, `verify` mode in Contract,
  inline "strict" definition (`Missing capability → complete: false, no report
  directory`), explicit releaseable-local statement, and Notation section with
  Lean↔FEP convention bridge.
- **ISA.md**: Added ISA-10 — non-vacuity/assumption-strength gate on every
  theorem proxy in `config/theorem_maturity.yaml`.
- **docs/quality.md**: Ruff pinned to `>=0.15.0` in dev dependencies, baseline
  captured at `.ruff_baseline.txt`, CI runs `ruff check` and `ruff format
  --check` in informational mode. Staged debt plan has deadlines.
- **CI**: Added `mypy src`, `ruff check`, and `ruff format --check` steps.
- **src/fep_lean/gauss/runner.py**: Removed misleading `FEP_LEAN_GAUSS_WORKFLOWS=1`
  docstring claims (gate was documented but never implemented in code).
- **lean/.lake/packages/**: Removed stale corrupt Mathlib cache directory
  `mathlib.corrupt-20260730`.
- Added `docs/test-suite-review.md` (31 files, 342 tests, 0 mocks, 0
  `except:pass`, parallel-safe, 90.25% cov, no blocking issues).
- Added `docs/mahakala-review.md` (multi-wave adversarial review with 6 persona
  proxies, 15 findings, GO with 3 pre-conditions, 9/10 overall score).

### Ruff cleanup (216 → 0)

- Applied 125 auto-fixed + 18 unsafe-fixed findings across 49 files
- Manually fixed 25 E741 ambiguous-variable-name violations (l→line)
- Fixed 3 B023 loop-variable-in-closure (captured via default arg)
- Fixed 7 E402 import-ordering violations (moved imports to top)
- Fixed 6 PYI036 `__exit__` type annotations, 1 PLW1510 `check=False`,
  1 TRY004 `TypeError` vs `ValueError`
- Suppressed RUF001/RUF003 (intentional math Unicode), BLE001 (fail-closed
  design), EXE001 (scripts imported not execed) via pyproject.toml
- `.ruff_baseline.txt`: baseline reduced to 0
- `docs/quality.md`: revision 3 — Ruff is clean, staged debt plan complete

### Gate verification

All gates re-run and passing after improvements:
- 339 passed, 3 skipped, 90.49% coverage (was 90.25%)
- mypy: 23 source files, no issues
- **ruff: 0 findings** (was 216 — 100% reduction)
- Lean verify: 50/50 clean, `complete: true`
- All 6 doc audits pass (links, md_hygiene, pin_audit, xref, catalogue, receipt)
Owner roster bumped
15 → 17 for the new rostered modules.

