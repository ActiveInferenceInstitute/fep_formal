# Cascadia river homing: a Lean 4 instance of a typed geospatial GNN artifact

Status: **slice-local native proof with a retained claim-ready receipt.** The
instance compiles warning-free at the pin (Lean v4.34.1, Mathlib v4.34.1), all
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
