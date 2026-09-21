# SCOPE-2026-09-20 — fep_lean improvement wave

Method: 7 read-only scout lanes (Ledger, CI, SRC, DOCS, TESTS, ARTIFACTS, LEAN) surveyed the live tree at HEAD `48b8d22` (merge of t-0001 H2.7 completion onto upstream post-batch re-seal `c31c524`). Coordinator triaged every item into wave assignments, landing-fold work, or deferrals.

## Binding constraints discovered by scoping

1. `SOURCE_OWNER_ROSTER` (provenance.py:25-28) binds every `src/fep_lean/**/*.py` byte — any src edit re-drifts the W2 bridge seal. Therefore ALL src edits go to ONE thread (W4) that finishes with the mechanical custody re-pin chore. No other thread may touch src.
2. The committed `output/native-verification.json` receipt is source-bound to the lean tree — ANY `lean/**/*.lean` byte change invalidates it and requires the full ~2.2h Lean battery. This wave touches ZERO .lean files; .lean items are deferred as their own verified change.
3. `tests/conftest.py` (PIN_FILE) + `pyproject.toml` (`pytest-timeout` config; H2.7-chain digest-bound) are owned by the coordinated ambient-hang fix thread / release surface — deferred.
4. `TODO.md` + `CHANGELOG.md` are the landing fold (coordinator-owned at landing).
5. Frozen custody dirs untouched by all threads: `specs/h3-case-study/**`, `specs/horizon-2-smooth-stochastic/**`, `specs/gnn-bridge-*/**`, `src/fep_lean/verification/horizon_acceptance.py`. Single sanctioned exception: W4's re-pin chore touches exactly `source-pin.json` + the two gnn-input documents.
6. GNN home checkout is fleet-synced (discards unpushed commits); the GNN-side pair bump happens once, at landing, by the coordinator.

## Wave assignments (disjoint file ownership)

### W1 — DocsLedger
Owns: `docs/**`, `manuscript/README.md`, `README.md`, root `AGENTS.md`, `SPEC.md`, `CITATION.cff`, `HANDOFF.md`, `specs/README.md` (new), `specs/done/formalism-catalogue-120/assets/acceptance.json`, `specs/done/active-inference-formal-depth/README.md`.
Items: DOCS 1-5 (lean4.md pin narrative; getting-started serial_lean filter; gate-list canonicalization with docs/testing.md as canonical — includes adding the figure-gate pair to README/AGENTS per CI item 7's doc half; design handoff H2.7 status refresh; manuscript 04j inventory), LEDGER 5/6/7 (SPEC.md:8 Mathlib 4.33.1→4.34.0; CITATION.cff:12 abstract toolchain; HANDOFF.md:6 release line v1.2.0), ARTIFACTS 1-2 (historical acceptance receipts → local_gitignored_path convention + vanished run-dir annotation; specs/README.md convention doc).

### W2 — CI
Owns: `.github/**` only.
Items: CI 1 (serial_lean gate in lean job), 2 (bridge `--check` gates in python job; frozen-dir failures = report only), 3 (Mathlib cache-fetch tolerance → fail closed or surfaced fallback; owner decision documented), 4 (render-deps job split), 5 (`if: always()` on native-formal-evidence upload), 6 (xdist `-n auto --dist loadgroup`), 8 (lean-latest.yml `uv run python`), 9 (measure `mypy scripts docs`; extend only if clean).
Skipped: CI 7 doc edits (W1 owns those files).

### W3 — Tests
Owns: `tests/**` EXCEPT `tests/conftest.py`; also `pyproject.toml` is off-limits (deferred).
Items: TESTS 1-13: dotenv class-attr mutation → monkeypatch fixture; verify_document ported to offline pair fixture; unattributed_row_declarations coverage; dead `_LIVE_TESTS_ENABLED` flag delete; padding test delete; test_edge_cases.py fold + delete; private SQLite schema pins → public surface; error-string wording pins → behavior assertions; check_mathlib_built consolidation; THEOREM_LATEX snapshots → one named golden table; macOS Chrome skip gates → resolve_browser_executable(); env writes → monkeypatch; shared lake fixture in tests/_support/. Plus: unprefixed pytest command fix in tests/AGENTS.md:29 + tests/README.md:4; plus the numerical-witnesses writer contract test (paired with W4's item 13).
Evidence-only (no edits this wave): ambient HTTP seam map + GAUSS_HOME hydration seam (coordinated hang thread input).

### W4 — SrcCustody
Owns: `src/fep_lean/**` except `verification/horizon_acceptance.py`; `scripts/build_release_bundle.py`; `lean/build.sh`; `lean/AGENTS.md`; local-only deletions (`output/verify-document-*.json`, leaked `lean/FepSketches/_verify_fep-097_ixo4v6z3.lean`).
Items: SRC 1 (coverage.py endpoint check — dry-run gate before tightening), 2 (reporter.py decompose, error strings byte-identical), 3 (toolchain identity consolidation, silent except-pass removed), 4 (child env allowlist, SC-33a), 5 (settings.yaml silent discards → warnings at both sites), 6 (SC-20 presentation threading), 7 (manifest.py derive from FORMAL_MODULES + generator --check), 8 (deprecated alias retirement), 9 (parse_axiom_output promotion), 10 (chunked sha256_file + call sites), 11 (hermes env masking warnings), 12 (cli.py micro-pass), 13 (numerical-witnesses standalone writer + build_release_bundle.py flag), LEAN 2 (build.sh/AGENTS.md stale v4.33.1 pins), LEAN 4 (verifier temp sweep + leak deletion), ARTIFACTS 4 (orphan receipt deletion).
Final mandatory chore: custody re-pin (bridge pin ×2 → emit --refresh-digests ×2 → emit --check ×2 → bridge status 6/6 → 40+55 targeted suites) + re-seal commit.

## Deferred (with reasons)

- LEAN 1 (narrow `import Mathlib` umbrella in 3 foundation modules) — .lean bytes → full Lean battery; schedule as its own verified change.
- LEAN 3 (FepSketches.lean docstring vs lakefile globs) — same.
- SRC 13 (release_bundle.py ~3800-line monolith split, SC-11) — major/architectural; needs coordinated roster refresh.
- ARTIFACTS 5 (toolchain-generation split in output receipts) — owned by FEP-RELEASE-NEXT (release evidence refresh).
- SRC 14 / custody.py `os`-import test coupling — cross-lane contract; document, don't change.
- Ambient hang fix: conftest.py + pytest-timeout thread-method + HTTP seam (TestsScout item 14 evidence map) — dedicated coordinated thread.
- pyproject.toml / uv.lock edits — H2.7-chain digest-bound release surface.

## Landing fold (coordinator, after wave merges + post-wave battery)

- LEDGER 1: delete CHANGELOG.md lines 975-1746 (verbatim duplicate of 200-974) BEFORE writing new entries; re-run md_hygiene + check_links.
- LEDGER 2: append post-release custody program entry (pin cycles #11/#12, GNN v3.4.0 + 083ddaf re-seals, t-0001 merge 48b8d22, manuscript commits).
- LEDGER 3-4: TODO.md FEP-RELEASE-NEXT preamble rewrite (v4.34.0 receipt + H2.7 re-seal done) + stale Unreleased pointer fix.
- SCOPE doc placement; TODO/CHANGELOG re-verify via doc gates.
- GNN pair pin bump to final fep_lean tip + fetch-guard pushes (fep_lean first, GNN second).

## Verification

Post-wave Python battery thread on the integrated tip (t-0003's G01-G25 table as baseline; Lean job skipped — zero .lean bytes; committed-receipt re-validation instead). Push sequence: in-flight custody fix (`48b8d22` after t-0004 green) → wave landing → GNN pair bump.
