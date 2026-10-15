# Cascadia river homing: a Lean 4 instance of a typed geospatial GNN artifact

Status: **slice-local native proof with a retained claim-ready receipt.** The
instance compiled warning-free at the historical `v4.34.1` Lean/Mathlib pin, all
46 theorems of the two files depend only on `propext`, `Classical.choice` and
`Quot.sound`, and four mutated instances are rejected. Nothing here touches
the sealed catalogue, its aggregate or the source-owner roster.

## Goal

GEO-INFER-ACT's Cascadia example models an adult salmon returning from the
Pacific up the lower Smith River (Del Norte County, California) to its natal
tributary, Rowdy Creek, as one-factor categorical active inference over 26 H3
resolution-8 cells traced from measured USGS NHDPlus HR flow lines. GEO-INFER
renders the model as GNN v1 Markdown, GNN's strict exporter produces the
`gnn-geo-infer/1` artifact, and GEO-INFER runs it through pymdp 1.0.4.

This slice states and proves, in Lean, facts about **that exported artifact**:
its tables are stochastic kernels, its transitions are local for the typed
river relations and hence for the recorded H3 adjacency, no plan reaches home
faster than the light cone allows, the bound is tight, the first Bayes update
is exact, the GNN source is a well-formed typed document, and the risk plus
ambiguity of fep_lean's carrier is exactly related to the score pymdp computes.

The canonical example documentation lives in the GEO_INFER checkout at
`GEO-INFER-ACT/docs/cascadia_river_homing.md` (prose path; each repository
validates its own links).

## Fixed decisions

1. **Bytes, not imports.** `fixtures/` holds verbatim copies of GEO-INFER's
   committed fixtures, copied by `refresh_fixtures.py` from an explicitly named
   checkout with a provenance record. No sibling checkout is opened by the
   generator, the verifier or the tests.
2. **Exact numbers.** JSON decimal literals are parsed as decimals, never
   through binary floats (every finite float is dyadic, so a dyadic check is
   only meaningful on the literal). Every A, B, D and E entry must be a
   power-of-two fraction with denominator at most 2^16; the Lean tables are
   the artifact's numbers times their denominators (B·4, A·64, D·4, E·8).
3. **Fail closed.** The artifact must name the source's SHA-256; the sidecar
   must name the same source, list the artifact's state order and repeat its
   exact tables; every column must sum to exactly one.
4. **Generated, then checked.** `generate_probe.py` computes the statement
   values (arrival bound, homing plan, evidence, posterior) from the fixtures;
   Lean checks them. A wrong value fails compilation.
5. **H3 enters as data.** The typed relations and the H3 adjacency table come
   from the sidecar, which GEO-INFER computed with `h3` 4.5. Lean checks the
   artifact's kernels against that table; it does not recompute H3 geometry.

## What is proved

General theory, `lean/CascadiaGeo/TypedGeospatial.lean`:

| Theorem | Statement |
| --- | --- |
| `rolloutKernel_support`, `plannedState_support` | An open-loop plan of `R`-local kernels connects only cells within `Reach R plan.length`; predicted mass outside the cone of the prior support is zero |
| `reach_potential` | An `R`-1-Lipschitz potential `φ` satisfies `φ c ≤ φ c' + n` along every `n`-step reach |
| `plannedState_eq_zero_of_potential` | If every start cell is farther than the plan is long, the plan predicts exactly zero mass at the target |
| `plannedState_pos_of_chain` | A chain of positive steps gives positive predicted mass |
| `risk_add_ambiguity_eq_logPartition_sub_pymdpNegEFE` | With preferences `softmax C`, risk plus ambiguity equals `log Σ exp C` minus pymdp 1.0.4's one-step score (expected utility plus state information gain), with no support hypothesis on states or outcomes |
| `riskAmbiguity_le_iff_pymdpNegEFE_le`, `controlPosterior_riskAmbiguity_eq_pymdp` | Policy rankings agree, and pymdp's policy posterior is the control posterior of risk plus ambiguity at every precision |

Generated instance, `generated/SmithRiverHoming.lean`:

| Theorem | Statement |
| --- | --- |
| `bNum_col_sum`, `aNum_col_sum`, `dNum_sum`, `eNum_sum` | The artifact's tables are exactly stochastic |
| `bNum_local`, `transition_local` | Positive transition mass stays put or makes one river move |
| `riverStep_h3Adjacent`, `h3Adjacent_symm`, `h3Adjacent_irrefl` | Every river move joins cells adjacent in the recorded H3 table |
| `homing_lower_bound` | No plan of fewer than 13 steps predicts positive mass at home, whatever its actions |
| `homing_bound_tight` | The 13-step plan (nine upstream, one turn, three upstream) reaches home with positive mass |
| `first_evidence`, `first_posterior_sea` | After a marine, faint-odor first observation the evidence is 57/128 and the exact posterior on the sea cell is 18/19 |
| `efe_bridge`, `policy_posterior_bridge` | The pymdp bridge at every current belief |
| `cascadiaDoc_wellFormed`, `cascadiaDoc_dims` | The GNN source transcribes to a well-formed Q1 `GnnDocument` whose declared dimensions are the carrier cardinalities |
| `cascadiaDoc_not_discreteConforms` | The source binds `C` to log-preferences, so the normalized-`C` Q2 denotation does not apply; `softmax C` is the bridge |

The full-support decomposition `expectedFreeEnergy_eq_risk_add_ambiguity`
does not apply here: a spatial belief gives exactly zero mass to most cells,
which is the light cone. The bridge theorem needs only that `softmax C` is
positive.

## Evidence boundary

Compilation establishes these exact Lean statements about the exported finite
model and nothing more. It does not verify any GEO-INFER or GNN code path,
pymdp's float32 arithmetic, H3 geometry beyond the recorded adjacency table,
or anything about salmon. GEO-INFER's own tests separately observe that
pymdp's float32 scores match the bridge identity within 10⁻⁵ and that its
float posterior equals 18/19; those are numerical observations, not proof.
The catalogue's semantic dispositions are unchanged.

## Artifacts

| Artifact | Role |
| --- | --- |
| [fixtures/](fixtures/) | Verbatim GEO-INFER source, artifact, sidecar and GNN export record, with `provenance.json` |
| [lean/CascadiaGeo/TypedGeospatial.lean](lean/CascadiaGeo/TypedGeospatial.lean) | Hand-written general theory |
| [generated/SmithRiverHoming.lean](generated/SmithRiverHoming.lean) | Generated instance; do not edit |
| [generated/manifest.json](generated/manifest.json) | Digests binding fixtures, generator, theory and instance, plus the derived facts |
| [native_receipt.json](native_receipt.json) | Retained native transcripts, axiom reports and mutation results |

## Operations

```bash
# Copy fixtures from a named GEO-INFER checkout (records its revision)
uv run python specs/cascadia-geo-act-proof/refresh_fixtures.py --geo-infer-root /path/to/GEO_INFER

# Regenerate, or check freshness without writing
uv run python specs/cascadia-geo-act-proof/generate_probe.py
uv run python specs/cascadia-geo-act-proof/generate_probe.py --check

# Native compile with axiom probes and mutations (needs the built Mathlib cache)
uv run python specs/cascadia-geo-act-proof/verify_native.py --compile \
  --receipt output/cascadia-geo-act-proof/native-receipt.json

# Read-only receipt validation: re-hash bound inputs, reparse transcripts
uv run python specs/cascadia-geo-act-proof/verify_native.py --check \
  --receipt specs/cascadia-geo-act-proof/native_receipt.json
```

`--compile` builds the theory into an isolated olean under
`output/cascadia-geo-act-proof/build` with `lake env lean -R … -o …`, then
compiles the instance with that directory on `LEAN_PATH`, so the Lake
workspace and its sealed aggregate are untouched. The four mutations are
transposed B axes, one H3 adjacency edge removed, an arrival bound one step
too strong, and a wrong exact posterior; each must fail.

The receipt binds the theory, instance, manifest, generator, verifier,
fixtures, `lean-toolchain` and `lake-manifest.json`. Any change to them makes
`--check` report a stale receipt until a fresh `--compile` replaces it.

Tests: [tests/test_cascadia_geo_act_proof.py](../../tests/test_cascadia_geo_act_proof.py).
The `serial_lean` test recompiles natively in the hosted Lean job; the other
tests check fixtures, generation, the GNN AST parser and the retained receipt.

## From one explanation to an assumption study

The active [experiment change-review slice](../cascadia-experiments/README.md)
compares candidate exact tables and carriers against these fixtures and emits
a machine-readable proof-impact worksheet. It leaves this reference receipt
intact and never promotes a variant to native claim readiness.

The sibling GEO_INFER example now includes
`GEO-INFER-ACT/examples/cascadia/cascadia_study.py`: a declared process-seed
grid under the reference model, a uniform E, and an uninformative odor A.
Each condition has its own GNN-emitted artifact and retains every trajectory,
including right-censored arrivals. Its qualification checks replay, numerical
support and the float32 EFE identity. Those observations complement this
slice's exact statements and do not extend its native receipt.

The proof consequence of a change must be reviewed by carrier:

| Change | Review required before a new native claim |
| --- | --- |
| Process seed or observation horizon only | Same finite tables; retain a new execution receipt, with no claim that Lean proves the sampled trajectory |
| E (habit prior) | New eNum data/denominator and policy-posterior instance; preserve stochasticity witnesses |
| A (odor/habitat likelihood) | New aNum data/denominator, Bayes evidence/posterior witnesses and score bridge instance |
| C | New log-preference vector and bridge instance; C remains unnormalized and enters through softmax |
| B, state order or network selection | New carrier, adjacency/relation data, locality, reachability bound and tight-plan witness |
| Step seconds | New clock metadata; a step-count theorem does not automatically establish a physical-time bound |

For a variant, retain a **new named slice** with the condition's source,
ordered identifiers, domain, artifact and export record. Adapt the generated
instance and its theorem roster to those inputs, compile it against the
pinned toolchain, inspect axiom reports and include mutations that break its
own normalization, locality, bound or posterior assertions. The current
generator and refresh commands target the reference slice; they are not a
generic variant-proof CLI. Do not overwrite these fixtures to make a study
condition appear to inherit the 46-statement reference receipt.

The type of a statement matters: an exact lower bound is universal over
admissible action plans in the finite model; a seeded trajectory is one
execution; a finite seed-grid arrival fraction is a descriptive summary.
None establishes an ecological homing rate. The canonical experiment and
censoring definitions live in GEO_INFER's
`GEO-INFER-ACT/docs/cascadia_river_homing.md`; the GNN custody guide lives in
`docs/other/geo_infer/cascadia_river_homing.md` of that repository.

## Catalogue compile checkpoint, 2026-10-12

The separate [retained catalogue receipt](catalogue_native_receipt_20261012.json)
records native compilation of all 168 canonical topic bodies against Lean
4.34.1 and the pinned Mathlib revision. Independent receipt validation reports
`native_claim_ready: true` and `source_bound: true`, with zero warnings and
zero `sorry` occurrences. It is a dated checkpoint, not a perpetual guarantee
of freshness after source changes. Revalidate it against the named checkout:

```bash
uv run python -c 'from pathlib import Path; import json; from fep_lean.output.evidence import validate_native_lean_receipt; r = validate_native_lean_receipt(Path("specs/cascadia-geo-act-proof/catalogue_native_receipt_20261012.json"), project_root=Path.cwd()); print(json.dumps(r, indent=2)); raise SystemExit(not r["native_claim_ready"])'
```

This receipt has a different scope from the 46-statement Cascadia instance
receipt. Neither is full Hermes/OpenGauss execution evidence, and neither
promotes the catalogue's maintained semantic dispositions or proves the
study's variant artifacts.
