# Mahakala Adversarial Review: fep_lean

**Date:** 2026-07-31 | **Target:** `ActiveInferenceInstitute/fep_lean` @ `147c19b`
**Reviewers:** Mahakala dharmapala (Wave 1: Adversarial Critical Review, Wave 3: Deception + Process, Wave 4: 6 Persona Proxies) + direct test suite audit
**Duration:** ~2h total across multi-wave dispatch

> **Historical snapshot, superseded for current-state claims.** This review is
> retained as dated evidence. The 2026-08-19 hardening removed the misleading
> workflow pseudo-gate, made mypy and Ruff formatting blocking in CI, defined
> sketch versus semantic-disposition terminology, migrated code into the
> `fep_lean` namespace, and added typed native receipts plus semantic and
> coverage projections. File paths, counts, verdict conditions, and open items
> below describe commit `147c19b`, not the current tree.

---

## 1. BLUF

**Verdict: GO (with 3 pre-conditions).** fep_lean is a genuinely well-hardened research catalog with unusually honest evidence boundaries. The fail-closed design, deterministic SSOT triangle, zero-mock test suite, and zero-`sorry` Lean aggregate are verified-real. No evidence of deception, metric-gaming, or concealed failures. The gaps are in *framing and process hardening*, not in *integrity or correctness*. Three pre-conditions before publication claim: (1) resolve the documented-but-unimplemented `FEP_LEAN_GAUSS_WORKFLOWS` gate, (2) add CI enforcement for `mypy`, (3) pick and define "sketch" vs "proxy" terminology.

**Confidence: HIGH** — every finding is bound to file:line evidence, the test suite was independently re-run (339/339 passing), and all six persona proxies converged on the same thematic gaps.

---

## 2. Go/No-Go Recommendation

| Dimension | Score | Evidence |
|-----------|-------|----------|
| Evidence integrity | ✓ GO | Independent receipt validation, fail-closed pipeline, no mocks |
| Deception risk | ✓ GO | Zero concealed failures, no metric gaming, honest CHANGELOG |
| Reproducibility | ✓ GO | Deterministic generator, CI-enforced SSOT parity, pinned toolchain |
| Test quality | ✓ GO | 339 passing, 90.25% cov, 0 mocks, parallel-safe |
| Process hardening | ⚠ CONDITIONAL | CI missing `mypy`; Ruff non-gating; `FEP_LEAN_GAUSS_WORKFLOWS` unimplemented |
| FEP-mathematical rigor | ⚠ CONDITIONAL | ISA criteria omit non-vacuity gate; sketch/proxy terminology ambiguous |
| Release boundary | ✓ NOTED | Honest that ISA-06 is open; needs explicit README statement |

**Conditional GO** — the local infrastructure claim is blockingly solid. Publish for local verification now; publication requires the three pre-conditions above + a named release-boundary statement.

---

## 3. Findings Table

### By Severity (Top 10)

| # | Finding | Severity | Confidence | Source | File:Line |
|---|---------|----------|------------|--------|-----------|
| 1 | `FEP_LEAN_GAUSS_WORKFLOWS` gate documented but not implemented | MEDIUM | HIGH | Wave 3 D&D-1 | `src/gauss/runner.py:202-203, 352-353` |
| 2 | `mypy` not enforced in CI (type regression would pass merge) | MEDIUM | HIGH | Wave 3 PH-2 | `.github/workflows/ci.yml` |
| 3 | `FEP_LEAN_MAX_TOPICS` subset runs report `complete: true` | MEDIUM | HIGH | Wave 3 PH-4 | `src/pipeline/core.py:183, 199` |
| 4 | "sketch" vs "proxy" terminology used interchangeably (changes claim strength) | MEDIUM | HIGH | Wave 4 (Allie, both Julians, DAF) | `scripts/catalogue_sketches.py` vs `config/theorem_maturity.yaml` |
| 5 | ISA criteria lack a non-vacuity gate — FEP statements untested for triviality | MEDIUM | HIGH | Wave 4 (DAF) | `ISA.md` ISA-01–09 |
| 6 | Ruff non-gating (214 findings) with unbounded staged-debt plan | MEDIUM | MODERATE | Wave 3 PH-1, Wave 4 (DAF, Neville) | `docs/quality.md` |
| 7 | Stale corrupt Mathlib cache directory on disk | MEDIUM | HIGH | Wave 3 TM-1 | `lean/.lake/packages/mathlib.corrupt-20260730/` |
| 8 | Hermes cache key excludes area/Mathlib version | MEDIUM | HIGH | Wave 3 TM-4 | `src/gauss/runner.py:376-383` |
| 9 | "Why 50" unearned — catalogue size asserted without provenance | LOW | HIGH | Wave 4 (Allie, both Julians, Neville) | `README.md:1` |
| 10 | Release boundary implicit — needs one README sentence | LOW | HIGH | Wave 4 (Adam, both Julians, Neville) | `README.md`, `ISA.md` §Release boundary |

### Also Noted (LOW/PASS)

| # | Finding | Severity | Source |
|---|---------|----------|--------|
| 11 | Test suite is exceptional: 0 mocks, 0 `except:pass`, 342 tests, parallel-safe | ✓ PASS | Direct audit |
| 12 | FI-CI enforcement of deterministic aggregate (`git diff --exit-code`) | ✓ PASS | Wave 3 PH-5 |
| 13 | Independent report receipt validator (6 failure modes tested) | ✓ PASS | Direct audit |
| 14 | Zero `sorry`/`admit`/`sorryAxm` in 1708-line Lean aggregate | ✓ PASS | Wave 4 (all personas) |
| 15 | CI missing parallel-mode test (non-determinism uncaught) | LOW | Wave 3 PH-3 |
| 16 | Lean output truncated at 8000 chars (logged, not concealed) | LOW | Wave 3 D&D-4 |
| 17 | Coverage threshold thin (1.25pt buffer) | LOW | Wave 3 PH-6 |
| 18 | SQLite no `integrity_check` on connection | LOW | Wave 3 TM-3 |
| 19 | API key prefix-only validation (not cryptographic) | LOW | Wave 3 TM-2 |

---

## 4. Top 3 Fixes (highest impact per effort)

### Fix 1: Implement or remove `FEP_LEAN_GAUSS_WORKFLOWS` gate (30 min)
**Action:** Either add `os.environ.get("FEP_LEAN_GAUSS_WORKFLOWS")` checks to `GaussRunner.run_topic()` at `runner.py:202-203` to gate the `prove`/`draft`/`review` workflow preambles, or remove the claim from the docstrings. Currently the docs promise a safety gate that doesn't exist.
**Severity:** MEDIUM | **Effort:** LOW (one `if` block or doc edit)
**Evidence:** `src/gauss/runner.py:202-203` docstring, verified zero code references to the env var.

### Fix 2: Add `mypy src` to CI (15 min)
**Action:** Add `uv run mypy src` to `.github/workflows/ci.yml`. Currently passes locally (23 files, no issues) but a type regression could be merged undetected.
**Severity:** MEDIUM | **Effort:** VERY LOW (one CI line)
**Evidence:** `.github/workflows/ci.yml` has no `mypy` step despite `AGENTS.md` listing it as a required check.

### Fix 3: Resolve "sketch" vs "proxy" terminology (30 min)
**Action:** Pick one term, define it in `AGENTS.md` or `README.md`, and audit the entire codebase + docs for the other. If "proxy" (as the theorem-maturity audit suggests), state plainly in README that "compiles clean" means "the stand-in statement type-checks," not "the real FEP theorem is proven."
**Severity:** MEDIUM | **Effort:** LOW (sed + doc edit)
**Evidence:** `scripts/catalogue_sketches.py` uses "sketch" (partial proof); `config/theorem_maturity.yaml` and proxy-review language uses "proxy" (stand-in). The central "compiles clean" claim means different things under each.

---

## 5. Competing Hypotheses

| Hypothesis | Evidence supporting | Evidence against | Confidence |
|-----------|-------------------|------------------|------------|
| **The repo is ready to ship** | All 10 gates pass, 0 mocks, 0 except:pass, fail-closed, zero sorry | CI missing mypy, terminology unresolved, FEP_LEAN_GAUSS_WORKFLOWS gate unimplemented | MODERATE |
| **The repo needs CI hardening before release** | mypy not in CI, Ruff non-gating, parallel mode untested in CI | These are process gaps, not integrity flaws; the core output (catalogue + Lean) is unaffected | HIGH |
| **The FEP-mathematical claims are hollow** | No ISA gate on non-vacuity; "sketch"/"proxy" fuzzy; theorem-maturity audit is maintained but not gating | Maturity audit exists (357 lines) with explicit disposition, non-vacuity, and assumption review for all 50 | LOW |

The evidence strongly favors hypothesis 2 — the infrastructure is solid, the FEP claims are honestly scoped, and the gaps are in CI process and documentation framing, not in integrity or correctness.

---

## 6. Per-Wave Appendix

### Wave 1: Adversarial Critical Review (partial — original subagent completed but truncated)
- Gates re-ran and confirmed: 339 passed, mypy clean, 90.25% cov
- Claim-evidence mapping: every README/AGENTS claim verified against source
- Key finding: fail-closed design is genuine — `src/pipeline/core.py:185` enforces

### Wave 3: Deception & Process Hardening (full, 15 findings)
- D&D-1: MEDIUM — documented `FEP_LEAN_GAUSS_WORKFLOWS` gate not in code
- PH-2: MEDIUM — `mypy` not in CI
- PH-4: MEDIUM — `FEP_LEAN_MAX_TOPICS` complete flag semantics
- TM-1: MEDIUM — stale corrupt Mathlib cache directory on disk
- TM-4: MEDIUM — Hermes cache key scope
- 10 LOW/NIL findings — all justified cleanup or documentation gaps

### Wave 4: Persona-Based Review (full, 6 personas, 366 lines)
**Convergent themes (all 6 agreed):**
- Evidence boundary is real and well-architected ✓
- "Why 50" needs provenance — one sentence would fix it
- Sketch/proxy terminology is fuzzy — resolves a meaning
- Release boundary needs one explicit README sentence

**Persona-specific insights:**
- **Adam:** Real-Filesystem SQLite partial-write failure not tested; preflight JSON schema undocumented
- **DAF:** ISA criteria lack non-vacuity gate; notation table missing for FEP community bridge
- **Allie:** Why 50 catalogue size unearned; sketch-vs-proxy ambiguity
- **Julian (Polite):** Rigorous but constructive — earn the 50, fix terminology, name release-blocker
- **Julian (Rude):** "A good repo wearing a slightly misleading outfit" — same gaps, unfiltered register
- **Neville:** Lead with evidence boundary as product, not catalogue size; add date to Ruff plan

### Test Suite Review (direct audit, 31 files, 342 tests)
- 0 mock/fake/stub usage anywhere
- 0 `except: pass` or `except: continue` patterns
- 90.25% coverage (≥89% threshold) with 1.25pt buffer
- 12-worker parallel: 339/339 in 44s (vs 111s sequential)
- 14 sad-path files covering every failure boundary
- All 3 skipped tests justified (Mathlib build, lake on PATH, API key)
- No blocking issues found

---

## 7. Calibrated Assessment

```
Evidence integrity:   ██████████ 10/10
FEP rigor:           ███████░░░  7/10  (missing non-vacuity gate)
Process hardening:   ███████░░░  7/10  (CI gaps, unimplemented gate)
Documentation:       ████████░░  8/10  (terminology, provenance, boundary)
Test quality:        ██████████ 10/10
Reproducibility:     ██████████ 10/10
Deception risk:      ██████████ 10/10  (no evidence of concealment)
Overall:             █████████░  9/10  (GO with 3 pre-conditions)
```

**Final word:** This is among the most honestly-scoped research repos I've reviewed. The fail-closed design, independent receipt validation, zero-mock test suite, and zero-`sorry` Lean aggregate are genuine — not green-washing, not metric-gaming, not overclaim. The three pre-conditions are all small-effort fixes (under 30 min each) that would close the gap between "very good local infrastructure" and "release-ready."
