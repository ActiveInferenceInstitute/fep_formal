# Cascadia experiments: mathematical change review

This active slice adds an exact-input review worksheet beside the retained
[reference proof](../cascadia-geo-act-proof/README.md). It helps an experiment
author identify which witnesses must be revisited after changing a model.
The worksheet does not generate Lean, compile a variant, or issue a native
proof receipt. The separate diagnostic theorem check below has its own scope.

## Ownership and execution

- GEO-INFER-ACT owns the river model, configured seed grid, simulation, static
  run qualification, and interactive explorer.
- GNN owns notation extraction and artifact production. Its worked-example
  `docs/other/geo_infer/qualify_export.py` reproduces an export in that checkout's
  environment; a worksheet cannot replace that check.
- This slice owns exact comparison against the reference carrier and the
  resulting list of proof obligations.
- LectureCreate's `examples/cascadia_geo_act/study_companion.py` invokes these
  tools in separate environments and retains their outputs for teaching.

Cross-checkout paths above are prose references. No foreign package is imported.

## Generate a worksheet

Use the mounted GitVault checkout and `TMPDIR` / `UV_CACHE_DIR` task directories
on that volume outside the repository, with `UV_LINK_MODE=copy`. Installed-wheel
and catalogue isolation tests require temporary projects outside the source
checkout. These are environment bindings, not model assumptions or proof inputs.

From this checkout, pass one retained condition directory containing the GNN
source, artifact, and domain sidecar:

```bash
uv run python specs/cascadia-experiments/proof_impact.py \
  ../GEO_INFER/GEO-INFER-ACT/examples/outputs/STUDY/uniform_habit \
  --output output/uniform_habit-proof-impact.json
```

The output path must have an existing parent and must not exist. Omitting
`--output` prints JSON without writing. Input digests and tool digests accompany
the worksheet. `native_claim_ready` is always false, even when the reference
bytes match. Revalidate the reference receipt separately before citing it.

The exact fixture loader rejects stale source hashes, inconsistent A/B tables,
non-dyadic probabilities, and failed stochasticity. This tool also compares
the D/E sidecar fractions and C values with the artifact. Rational values are
compared after denominator normalization, so merely choosing an equivalent
fraction representation does not invent a mathematical change. This is a
comparison of a supported finite Cascadia carrier, not a general artifact
schema validator or an independent GNN exporter.

## Interpreting changes

[Separate agent/process obligations](model-mismatch.md) distinguish realized
process transitions from agent belief predictions and identify which graph,
score and policy hypotheses reopen under model mismatch.

[Matrix proof obligations](matrix-proof-obligations.md) apply that distinction
to configured case selections, shared seeds and horizons, including positive
agent evidence for process-generated cues and retained impossible-cue failures.

| Component | Mathematical review reopened |
| --- | --- |
| A | Likelihood stochasticity, exact evidence/posterior, score instance |
| B | Transition stochasticity/locality, lower bound, tight plan |
| C | Log-preference softmax and score/posterior instances |
| D | Initial support, initial-prior stochasticity, first update |
| E | Habit stochasticity and policy-posterior instance |
| Carrier | State/observation/action identities and indexed tables |
| Geometry | Recorded adjacency, river relations, roles and landmarks |
| Clock | Physical-time interpretation; a step theorem alone is insufficient |

The generic score theorem remains a reusable theorem under its hypotheses.
A new table or carrier requires a new checked instance and its own source
custody. A changed process seed or observation horizon alone does not change
these tables; it still requires an execution record. A successful simulation,
export reproduction, or worksheet does not establish ecological validity.

## Recorded-state score bounds

[DiagnosticBounds.lean](DiagnosticBounds.lean) defines the full-carrier Brier
score $\sum_i(p_i-\mathbf{1}_{i=s})^2$ and proves nonnegativity, the exact
identity $\sum_i p_i^2-2p_s+1$, and the upper bound two for a finite
nonnegative vector with sum exactly one. A binary wrong-point-mass theorem
attains two, so replacing the upper bound with one is a false claim.

[verify_diagnostic_bounds.py](verify_diagnostic_bounds.py) uses the maintained
Lean/Mathlib pins, compiles six statements with an exact axiom roster, and
requires two mutated statements to fail: a universal upper bound one and an
incorrect binary score. Every attempt is a new output directory; compiler
transcripts, source copies and failed attempts remain preserved.

[cascadia_diagnostic_evidence.py](cascadia_diagnostic_evidence.py) owns the
receipt types, strict decoding, input fingerprints and evidence admission;
the entry point owns compilation and output orchestration. Both owner bytes
are bound, together with the package's strict-JSON and process supervision
helpers. A previous receipt becomes historical when these owners change.

```bash
uv run python specs/cascadia-experiments/verify_diagnostic_bounds.py \
  --compile output/cascadia-diagnostic-bounds-new
uv run python specs/cascadia-experiments/verify_diagnostic_bounds.py \
  --check output/cascadia-diagnostic-bounds-new
```

The read-only recheck binds input/output digests, transcripts, source copies,
compiler pin and actual Mathlib revision. `diagnostic_theorems_verified`
refers to these generic real-number statements only. `native_claim_ready`
remains false for the simulation. The floating-point diagnostic implementation
and tolerance are not proved to refine this definition, and no theorem here
establishes calibrated beliefs, homing success, or ecological validity.

## Checks

The [matrix validation record](matrix-validation.md) records the October 14
configured matrix, strict receipt controls, actual replay and companion checks.

The [cross-repository validation record](publication-validation.md) records
the main-publication source identities, checks, retained failures and
mathematical scope for the October 13 improvements.

```bash
uv run pytest specs/cascadia-experiments/test_proof_impact.py -q --no-cov
uv run pytest specs/cascadia-experiments/test_diagnostic_bounds.py -q --no-cov
uv run ruff check specs/cascadia-experiments
uv run ruff format --check specs/cascadia-experiments
uv run python specs/cascadia-geo-act-proof/generate_probe.py --check
uv run python specs/cascadia-geo-act-proof/verify_native.py --check \
  --receipt specs/cascadia-geo-act-proof/native_receipt.json
```

Tests change an exact habit, clock, probability literal, and source digest;
they also construct an inconsistent E sidecar. The unchanged reference
case confirms that identity never promotes the worksheet to proof.
