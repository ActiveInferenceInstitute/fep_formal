# GNN bridge P1 finite spike

Status: **complete; P1 and P2 accepted 2026-09-03 (see Acceptance and
`REPORT.md`)**. This slice implements Phase P1 (single finite model:
Lean expression -> GNN document -> validate -> render -> execute) and
Phase P2 (deterministic regenerable projection with a freshness gate)
of the [GNN bridge program](../../docs/design/gnn-bridge/README.md)
under the [bridge contract](../../docs/design/gnn-bridge/bridge-contract.md).
The GNN-side touchpoint record is
`GeneralizedNotationNotation/doc/other/fep_lean/fep_lean_gnn.md`.

## Extraction record (P1 task 1)

**Instance.** `FEP.ActiveInference.symmetricBoolModel trueBiasedPolicyPrior
: GenerativeModel Bool Bool Bool` — the symmetric two-policy, two-state,
two-observation finite generative model on Boolean carriers, with the
policy prior fixed to the `true`-biased witness. This is the concrete
`active_inference.lean` `GenerativeModel` instance; the H1 terminal
certificate carrier in
`lean/FepSketches/compositions/finite_reference_agent.lean` references
this same family (`symmetricBoolModel selectedPrior`,
`finite_reference_agent.lean:91-121`) but its own terminal objects
(`FiniteReferenceCoherence`) are proved uninhabited there, so the
applied-instance witness model is the projectable choice.

All values below are exact Lean source literals; every row names its
definition site. Commit digests at extraction time:
fep_lean `315e32994b59fd80e327b5b654c9f7852fad9933`,
GeneralizedNotationNotation `12a565b2f18db7f18c3a799568ad057834ba0358`.

| Bridge field | Lean source | file:line | Exact value |
| --- | --- | --- | --- |
| Carrier types Policy/State/Outcome = `Bool` | `symmetricBoolModel` signature | `lean/FepSketches/active_inference.lean:743-744` | 2 policies, 2 states, 2 observations |
| `D` initialState | `fairBoolLaw` (def) via `initialState := fairBoolLaw` | def `lean/FepSketches/active_inference.lean:719-722` (`mass _ := 1 / 2`, line 720); use line 745 | (1/2, 1/2) |
| `B` transition | `fairBoolKernel`, policy-indexed `transition _ := fairBoolKernel` | def `lean/FepSketches/active_inference.lean:725-728` (`mass _ _ := 1 / 2`, line 726); use line 746 | all 8 entries 1/2; both policy slices identical |
| `A` likelihood | `fairBoolKernel` via `likelihood := fairBoolKernel` | def `lean/FepSketches/active_inference.lean:725-728`; use line 747 | all 4 entries 1/2 |
| `C` preferences | `fairBoolLaw` via `preferences := fairBoolLaw` | def `lean/FepSketches/active_inference.lean:719-722`; use line 748 | (1/2, 1/2) |
| `E` policyPrior | `trueBiasedPolicyPrior` applied to `symmetricBoolModel (prior : FiniteLaw Bool)` | def `lean/FepSketches/active_inference.lean:731-734` (`mass policy := if policy then 3 / 4 else 1 / 4`, line 732); parameter site lines 743, 749 | E(false)=1/4, E(true)=3/4 |
| One-step timescale | `predictedState` applies `transition policy` once to `initialState` | `lean/FepSketches/active_inference.lean:30-32` | horizon 1 |

The `GenerativeModel` carrier itself is
`lean/FepSketches/active_inference.lean:21-27`. Both
`expectedFreeEnergy_eq_risk_add_ambiguity`
(`lean/FepSketches/active_inference.lean:300`) and
`symmetricBoolModel_expectedFreeEnergy`
(`lean/FepSketches/active_inference.lean:807-812`) are compiled
declarations over this instance.

**No Lean compilation was performed or required** (task constraint).
The extraction plane is source reading of declarations that the pinned
workspace maintains as projected, compiled artifacts
(`src/fep_lean/formal/manifest.py` projection; Direction 1 "What the
catalogue supplies today"). Native `fep-lean verify` remains the S1
gate for later certificate phases, not P1.

## Rounding policy (contract section 9)

Fixed for this slice: **exact Lean `ℚ` literals are emitted as their
shortest exact terminating decimal string; no value is ever rounded. A
Lean value whose decimal expansion does not terminate makes the field
unprojectable in P1/P2 and is a no-go, not a rounding.** All extracted
values above (1/2, 1/4, 3/4) terminate exactly, so every emitted
numeric string is the exact value. Consequence recorded under ontology
below: `C` is emitted as the probability law itself, never as
`Real.log`-transformed values (`log(1/2)` does not terminate).

## Ontology bindings (contract section 9 vocabulary rule)

Emitted bindings, all present in
`GeneralizedNotationNotation/src/ontology/act_inf_ontology_terms.json`
(64 terms, checked 2026-09-03): `A=LikelihoodMatrix`,
`B=TransitionMatrix`, `C=Preferences`, `D=PriorOverHiddenStates`,
`E=Habit`, `F=VariationalFreeEnergy`, `G=ExpectedFreeEnergy`,
`s=HiddenState`, `s_prime=NextHiddenState`, `o=Observation`,
`π=PolicyVector`, `t=Time`.

Deviation from the discrete exemplar, deliberate: the exemplar binds
`C=LogPreferenceVector` because its C values are log-probabilities. The
Lean `preferences : FiniteLaw Outcome` is a probability law; binding
`C=Preferences` (canonical term, ACTO_000010) matches the Lean
semantics exactly and avoids a non-deterministic log transform. No
vocabulary extension request is needed; no binding outside the
canonical set is emitted.

Variables absent from the Lean carrier are not emitted: `GenerativeModel`
has no `Action` type (that is `ActionInterface`'s role,
`lean/FepSketches/active_inference.lean`; separate structure, not part
of the projected instance), so no `u` variable or `u`-edges are emitted.
`F`/`G` are the compiled EFE/VFE readouts
(`lean/FepSketches/active_inference.lean:148-150, 209-214`).

## Document inventory

Emitted by `projection.py` into `gnn-input/FepLeanSymmetricBool.md`:

- `GNNSection` `FepLeanSymmetricBool` — `FepLean` prefix, no spaces,
  no `continuous` keyword (mechanical discrete-kind detection).
- `GNNVersionAndFlags` `GNN v1` — pins the
  `GeneralizedNotationNotation/doc/gnn/gnn_syntax.md` v1.1 surface, same
  pin string as the discrete exemplar.
- `ModelName`, `ModelAnnotation` (extraction table with file:line).
- `StateSpaceBlock`: `A[2,2]`, `B[2,2,2]` (next, previous, policy),
  `C[2]`, `D[2]`, `E[2]`, `s[2,1]`, `s_prime[2,1]`, `o[2,1]`,
  `π[2]`, `F[π]`, `G[π]`, `t[1]`.
- `Connections`: `D>s`, `s-B`, `B>s_prime`, `s_prime-A`, `A-o`,
  `E>π`, `π-B`, `C>G`, `G>π` (plain v1.0 edges; finding below).
- `InitialParameterization` with exact decimals and per-matrix file:line
  provenance comments.
- `Equations` restating the Lean-defined quantities.
- `Time` `Dynamic`/`Discrete`/`ModelTimeHorizon=1`.
- `ActInfOntologyAnnotation` as above.
- `ModelParameters`: `num_hidden_states: 2`, `num_obs: 2`,
  `num_actions: 2`, `num_timesteps: 1`.
- `Footer`; `Signature` = mandatory provenance block: both repository
  commit digests, Lean module + definitions, generator identity,
  rounding policy, targeted syntax version.

## Acceptance checklist

P1 (all required):

- [x] A1 — instance identified with file:line for every value (above).
- [x] A2 — spec slice opened before implementation (this file).
- [x] A3 — `projection.py` inside this slice emits the document;
      re-runnable, byte-deterministic.
- [x] A4 — `uv run gnn validate gnn-input/FepLeanSymmetricBool.md
      --strict` exits 0 (run from the GNN repo root).
- [x] A5 — `uv run python src/main.py --target-dir
      specs/.../gnn-bridge-p1-finite-spike/gnn-input --output-dir
      specs/.../gnn-bridge-p1-finite-spike/gnn_output --only-steps
      "3,5,11,12" --verbose` completes; render summary reports at least
      one categorical backend rendered (`unsupported` distinct from
      `failed` if any backend declines); execution summary written.
      Observed: all four steps ran to completion; steps 3/5/11 exit 0
      (run 2 has zero step-3 warnings); step 12's overall exit 1 is
      caused solely by the rxinfer backend returning rc=1 after writing
      its artifacts (finding F1 in `REPORT.md`); pymdp executed rc=0,
      render summary reports 9/9 backends rendered, execution summary
      written (6 success / 1 failed / 2 skipped).
- [x] A6 — ontology annotations verified against
      `src/ontology/act_inf_ontology_terms.json` (all 12 bindings
      canonical; supplementary step-10 run recorded).
- [x] A7 — `REPORT.md` written with statuses, commands + exit codes,
      key summary numbers, blockers.

P2 (required for the freshness gate):

- [x] P2.1 — re-running `projection.py` reproduces the on-disk document
      byte-identically (`cmp` clean).
- [x] P2.2 — `projection.py --check` exits 0 on a fresh tree and
      non-zero on drift (artifact bytes or provenance digests), in the
      style of `fep-lean atlas --check`.
- [x] P2.3 — `uv run ruff check` and `uv run mypy` pass on
      `projection.py` from the fep_lean root.

## No-go registry (slice-local findings)

- No extraction no-go triggered: every emitted field names a compiled
  Lean declaration and an exact literal (table above).
- `C=LogPreferenceVector` not emitted: the log transform is
  non-terminating and is a representation decision, not derivable data;
  canonical `C=Preferences` used instead (see rounding policy).
- No `Action`/`u` surface: absent from `GenerativeModel`; emitting one
  would be a judgment call (contract section 9 trigger).
- Concurrent-agent caveat: `--check` compares recorded provenance
  digests against live `git rev-parse HEAD` of both repositories. A new
  commit in either repository legitimately flips the gate to
  `stale` (artifact custody, bridge contract section 9); that is
  drift reporting, not script failure.
- GNN-side parser inconsistency (recorded, not repaired here): the
  v1.1 syntax (doc/gnn/gnn_syntax.md section 3) allows `A>B:label`
  connection annotations and requires parsers to accept them, but the
  pipeline markdown parser (src/gnn/parsers/markdown_parser.py
  `_parse_connection_definition`, lines 314-357) never strips the
  `:annotation` suffix, so step 3 warns "Connection references unknown
  target variables" for every annotated edge while `gnn validate
  --strict` (separate code path) accepts the same document. The emitted
  document therefore uses plain edges; annotations live in
  ModelAnnotation/Equations. Filed for the GNN side; no GNN source was
  edited from this slice.

## Evidence planes

- This slice's extraction: Lean source reading (semantic review plane,
  file:line anchored). Establishes: the projected values are the
  literals of the named definitions. Never establishes: that the Lean
  theorems hold (they are already proved in the pinned workspace, which
  is a different plane), nor model correctness.
- GNN pipeline run (steps 3/5/11/12 + supplementary 10): establishes
  the document parses, type-checks, renders, and executes. Never
  establishes mathematical correctness of the model or any Lean claim
  (bridge contract section 7 firewall).
- No execution statistic is compared with any Lean-witnessed property in
  P1/P2; that is P3's certificate protocol and is out of scope here.

## Artifact custody

`gnn-input/FepLeanSymmetricBool.md` records both commit digests,
generator identity (`specs/gnn-bridge-p1-finite-spike/projection.py`),
the Lean module/definitions, the rounding policy, and the targeted
syntax version in its `Signature` section. `gnn_output/` is dedicated
to this slice; the shared GNN `output/` tree is owned by another agent
and is never written by this slice.
