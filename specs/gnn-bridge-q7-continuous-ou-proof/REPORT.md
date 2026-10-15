# Q7: scalar OU coefficient bounds

The independently reviewed
[current source-pair observation](../comprehensive-science-improvement/evidence/public-q7-current-source-20261005-r1/summary.json)
records a complete 2026-10-05 capture: all twelve stages and four closing checks
passed within the original limits. The official native receipt binds all 291
current inputs and twelve theorem reports with standard axioms only. Static
coefficient evidence leaves generated-runner execution unverified.

The retained 2026-10-02 observations below keep their recorded source epochs.
The dated [post-guidance observation](../comprehensive-science-improvement/evidence/public-q7-current-doc-20261002-r1/summary.json),
original 2026-09-04 report and [historical native JSON](native_receipt.json)
remain unchanged. Failed attempts supply no promoted prefixes or native result.
No Q5/Q6 observation is refreshed by a Q7 proof. Package and H3 acceptance
remain open in [remaining acceptance](../comprehensive-science-improvement/NEXT.md).

## Claim and scope

The decoded binary64 coefficients of the canonical scalar-OU JAX render have exact-real error bounds of 10^-15 against the selected OU formulas. The proof also bounds one-step prediction and stationary defects and proves a scalar Joseph identity.

These are real-arithmetic bounds over decoded coefficients. They do not bound JAX arithmetic, accumulated trajectory error, arbitrary LGSSMs, SDE solutions, or empirical behavior.

## Retained evidence

- The [public Q7 observation](../comprehensive-science-improvement/evidence/public-q7-closure-20261002-r1/summary.json) records accepted recapture r3 at actual receipt SHA-256 `8c7c8d89023eb9784405143c1750b4b7ddd4ff1453dbbd089e9d660633b912ad` and elapsed time 644.5096 seconds. Seven actual accepted substages from failed r2 are freshly revalidated; stages 8–12 actually run in r3. All 124 pure controls pass, zero skips.
- [Exact new native receipt copy](../comprehensive-science-improvement/evidence/q7-accepted-native-retention-20261002-r1/native-receipt.json) has SHA-256 `b0ecf640fffa06f019d67c74a2d02e22715120165a98d218d61f49f98366bc3b`, `native_claim_ready: true` and `runtime_execution_verified: false`. It binds Lean/the `v4.34.1` Mathlib release and the selected isolated GNN source pair.
- The same public observation records actual postcapture closure r2 at receipt SHA-256 `df7787a925bf1011a9bd09a8bcc5ae20240792ea0b4ca9bc435eb5204225ba59` and elapsed time 1,648.1618 seconds. Seven stages pass, including actual positive-axiom/wrong-F/wrong-Q native controls. The local outer observation records actual exit 0 and accepted transport at SHA-256 `3f69a197c00fd4960270db9bb8547bd1fd20b39172fa3efd7ff4b3e36ad15712`; the process is closed. This observer is a separate evidence plane from the native receipt.
- [Render provenance](render_provenance.json) is the mutable working projection bound by the complete 2026-10-05 source-pair capture. It does not rewrite the historical accepted render.
- [Generated proof manifest](generated/artifact_proof_manifest.json) is the mutable extraction/probe projection. It supplies no native or current capture acceptance by itself.
- At the recorded accepted epoch, the positive probe compiled without warnings or `sorryAx`; all 12 named theorem reports used only standard axioms. These are static coefficient statements; generated-runner execution remains unverified.
- Historical native JSON also binds its recorded contract, engine, Python/probe buffers, recursive imports, compiler binaries and transcripts at its earlier source epoch.
- Dated reported historical receipt SHA-256: `70f6e8b267c44189aa41e6b2adf3e777ad4ed51f60dfc8500e70c2110417c4a5`.
- Actual historical JSON SHA-256, read on 2026-10-02: `ba6df64c4515c2ac503d9a4f841b361766ed03039530f754f42108c0c593c8a2`. That file records historical compiler version `v4.33.1` and is not rewritten to match the earlier report or new receipt.

The recorded isolated GNN pair owns its Git checkout and copied runtime, with all 703
owners bound to `536d949829f6aed11dc540e5c5dec77578b25016` and a read-only
shared dependency base. FEP/native brackets cover 191/291 owners. Active GNN
work/output remain untouched by this isolated capture. Refreshed parity records
56,968 identical scaffold bytes on actual CPython 3.10.20, 3.11.15, 3.12.13,
3.13.15 and 3.14.4 at SHA-256
`b34a350a0c66bd611c19cd87e2343592c6ee7d15ed2fd6e422b1f891597febec`,
with all 11 controls per runtime. Strict evidence validation remains CPython 3.14.
Full operator-custody records remain local. The public summary is observational;
only the separately validated official native receipt supplies the native claim.

| Theorem | Native axiom result at the recorded accepted epoch |
| --- | --- |
| `FEPProbe.Q7ContinuousOU.artifact_F_bound` | standard axioms only |
| `FEPProbe.Q7ContinuousOU.artifact_Q_bound` | standard axioms only |
| `FEPProbe.Q7ContinuousOU.artifact_exact_parameters` | standard axioms only |
| `FEPProbe.Q7ContinuousOU.artifact_prediction_mean_bound` | standard axioms only |
| `FEPProbe.Q7ContinuousOU.artifact_prediction_variance_bound` | standard axioms only |
| `FEPProbe.Q7ContinuousOU.artifact_stationary_defect_bound` | standard axioms only |
| `FEPProbe.Q7ContinuousOU.exact_noise_formula` | standard axioms only |
| `FEPProbe.Q7ContinuousOU.exact_row_eq_selected` | standard axioms only |
| `FEPProbe.Q7ContinuousOU.nonstationary_prediction_changes_mean` | standard axioms only |
| `FEPProbe.Q7ContinuousOU.scalar_joseph_identity` | standard axioms only |
| `FEPProbe.Q7ContinuousOU.selected_decay` | standard axioms only |
| `FEPProbe.Q7ContinuousOU.selected_transitionVariance` | standard axioms only |

## Regression evidence

At the dated wave-2 epoch, Q6 passed both positive probes and the normalized previous/action-axis rejection.
Q7 passed its positive 12-theorem census and both wrong-coefficient rejections.
Its initial notation-scope and tactic-linter defects were repaired without
changing theorem statements, bounds, or warning policy. The independent read-only
review confirmed that scope and the repair. Q5's native regressions passed in
the frozen full baseline; its schema-2 receipt was then freshly compiled.

That historical integrated nonserial Python suite passed 1,460 tests with seven skips,
529 native deselections, and 89.83% coverage. See the
[coordinated wave-2 report](../gnn-bridge-w2-source-custody/WAVE2-REPORT.md) for
exact test scopes, source-freeze evidence, and the separate H2 acceptance record.

## Reproduction

Follow [the slice README](README.md) to refresh canonical rendering and regenerate
probes after source changes. Native compilation is explicit and serialized:

```bash
GNN_ROOT=/absolute/path/to/GeneralizedNotationNotation
uv run python specs/gnn-bridge-q7-continuous-ou-proof/verify_native.py --compile --gnn-root "$GNN_ROOT" --receipt output/bridge/q7-native-candidate.json
uv run python specs/gnn-bridge-q7-continuous-ou-proof/verify_native.py --check --gnn-root "$GNN_ROOT" --receipt output/bridge/q7-native-candidate.json
```

Use a fresh candidate path per capture and check that same candidate against
the same named GNN root; never overwrite the historical native JSON.
Default and `--check` validation are read-only. A source, contract, artifact,
import, or toolchain change invalidates the corresponding receipt. Content
custody assumes trusted local Python and toolchain binaries; it is not a sandbox
or independent host/compiler authentication. Publication and provider-backed
execution retain their separate acceptance requirements.
