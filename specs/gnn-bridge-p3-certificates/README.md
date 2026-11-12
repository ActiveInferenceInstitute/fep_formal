# GNN bridge P3 certificate protocol

Status: **complete; P3 verified** — protocol defined, custody run executed,
C1/C2 pass within tolerance, C3 boundary and O1 divergence filed, and the
whole protocol independently re-verified 2026-09-04 (REPORT.md,
"Verification (2026-09-04)"). This
slice implements Phase P3 of the
[GNN bridge program](../../docs/design/gnn-bridge/README.md) under the
[bridge contract](../../docs/design/gnn-bridge/bridge-contract.md)
([Direction 1](../../docs/design/gnn-bridge/direction-1-lean-to-gnn.md),
P3 row) on the accepted P1 instance
`FEP.ActiveInference.symmetricBoolModel trueBiasedPolicyPrior`
(`lean/FepSketches/active_inference.lean:743-749`), whose GNN artifact is
`specs/gnn-bridge-p1-finite-spike/gnn-input/FepLeanSymmetricBool.md`
(accepted in `specs/gnn-bridge-p1-finite-spike/REPORT.md`). Spec-first:
this file is the acceptance record and precedes all code in the slice.

## Certificates (what is mechanically statable for THIS instance)

Every compared quantity names both sides' evidence planes (contract
section 7). Comparison is statistic-level only: distributions and
summary statistics, never trace identity; Lean witnesses and pymdp/JAX
share no RNG stream.

### C1 — action-selection agreement (task candidate (a))

- **Lean-witnessed claim (native Lean compilation plane, pinned
  workspace; numerical-witness evaluation of exact rationals).**
  `symmetricBoolModel_policyPosterior_eq_prior`
  (`lean/FepSketches/active_inference.lean:816-826`) proves
  `policyPosterior γ (symmetricBoolModel prior) _ policy = prior policy`
  for every precision γ — the Boltzmann policy posterior equals the
  policy prior because every policy has equal EFE
  (`symmetricBoolModel_expectedFreeEnergy`, :807-812). With
  `prior := trueBiasedPolicyPrior` (:731-734; false→1/4, true→3/4):
  `Q(π) = (1/4, 3/4)` in (false, true) order; `argmax Q = true`.
- **Executed quantity (GNN pipeline execution plane).** pymdp 1.0.0
  `infer_policies` posterior `q_pi = softmax(γ·neg_efe + ln E)`
  (`GeneralizedNotationNotation` venv `pymdp/control.py:288,841`), with
  equal per-policy scores ⇒ `q_pi = E` normalized. Serialized per step
  as `policy_posterior` in `simulation_results.json`.
- **Comparison.** Element-wise |Δ| and argmax equality.
- **Note.** The executed `actions` entry is a single sample from `q_pi`
  (`pymdp_simulation.py:443-445`) — trace-level, used only as a
  consistency observation (argmax agreement), never as the certificate.

### C2 — F[1] variational-free-energy readout (task candidate (b))

- **Lean-witnessed claim (native Lean compilation plane; numerical
  witness = float64 evaluation of the proved closed form).**
  `variationalFreeEnergy` (:209-214) = `finiteKL(recognition ||
  posteriorState) + outcomeSurprisal` (:202-205). For the executed
  instance: `predictedOutcome = fairBoolLaw` (:762-773) ⇒
  `P(o) = 1/2` for both o ⇒ surprisal = `log 2`;
  `posteriorState` (:121-125, exact Bayes :190-198) = `(1/2·1/2)/(1/2) = 1/2`
  per state = fair law = the initial belief itself (initialState :=
  fairBoolLaw, :745) ⇒ `finiteKL = 0`. Closed form:
  **`VFE_initial = log 2 ≈ 0.6931471805599453` (nats), independent of
  the executed policy and observation.**
- **Executed quantity (GNN pipeline execution plane).** pymdp
  `infer_states(..., return_info=True)` VFE, serialized as
  `variational_free_energy` (`src/execute/pymdp/pymdp_simulation.py:450,468`).
- **Comparison.** |executed − log 2| at the stated tolerance.

### C3 — directional agreement (task candidate (c)) — BOUNDARY, not run

Two independent obstacles, either alone sufficing: (i) the P1 instance
is one-step (`num_timesteps: 1`; executed `simulation_results.json`
confirms), so no ≥2-step trajectory is executed; (ii) the Lean-witnessed
decrease families (`ouKL_to_stationary_nonincrease`,
`nativeKL_contraction`) live in the smooth/semigroup family, not on the
Boolean POMDP carrier — no Lean-witnessed decrease property exists for
this instance to compare direction against. Recorded as a boundary
finding per contract section 9; not forced.

### O1 — observed divergence (not a certificate): EFE readout

The executed serialization `expected_free_energy` (pymdp `neg_efe`,
`pymdp/agent.py:860` "`G = neg_efe = -EFE`") reads **0.5 per policy**,
while Lean `expectedFreeEnergy` (:148-150; :789-812) = risk + ambiguity
= `log 2 ≈ 0.693147…`. Source-verified root cause: pymdp 1.0.0
`compute_expected_utility` (`pymdp/control.py:422-445`) uses **linear**
utility `Σ_o q(o)·C(o)` with C as a payoff vector (0.5·0.5 + 0.5·0.5 =
0.5; info-gain term 0 on uniform A), while the GNN discrete exemplar's
own comment calls C "log-probabilities" and binds
`C=LogPreferenceVector`, and Lean defines C as a probability law with
`risk = finiteKL` (:128-131). Three C-conventions coexist across the
bridge surface; the divergence is filed with exact numbers and source
references, not smoothed over, and is the GNN-side vocabulary/mapping
question P3 exists to surface. O1 is informational — it neither passes
nor fails C1/C2 (different quantities under different conventions).

## Comparison policy (contract section 9)

- Lean exact rationals are compared as exact decimal values; the only
  transcendental Lean value (`log 2`) is evaluated as `math.log(2)` in
  float64 — a numerical witness of a proved closed form, not a rounded
  Lean value.
- Tolerance **|Δ| ≤ 1e-6**: the executed backend is jax float32
  (`model_parameters.backend = "jax"`); float32 epsilon ≈ 1.19e-7 at
  these magnitudes, observed deviations ≤ 6.0e-8 (C1) and 1.9e-9 (C2).
- First disagreement is filed as a finding with exact numbers;
  disagreements are never absorbed into tolerances.

## Execution custody

The protocol runs the GNN pipeline fresh on the accepted P1 document
(read-only input, `specs/gnn-bridge-p1-finite-spike/gnn-input/`) with
output dedicated to this slice (`gnn_output/`), so every consumed
execution artifact is bound to this slice's run. The shared GNN
`output/` is never written.

## Acceptance checklist

P3 (all required; boxes flip only after the named command exits 0):

- [x] P3.1 — spec slice opened before any code (this file).
- [x] P3.2 — pipeline run under P3 custody completes; steps 3/5/11 exit
      0; execution summaries written (rxinfer-class backend failures are
      recorded verbatim, distinct from `unsupported`, per P1 REPORT).
- [x] P3.3 — `certify.py` (ruff + mypy strict clean from fep_lean root)
      runs the C1/C2 comparisons and emits `certificates.json` +
      `CERTIFICATES.md` with per-quantity evidence-plane labels.
- [x] P3.4 — C1 and C2 agree within tolerance (exit 0); any disagreement
      filed with exact numbers as a finding.
- [x] P3.5 — C3 boundary recorded (not run).
- [x] P3.6 — O1 divergence recorded with exact numbers and source refs.
- [x] P3.7 — `REPORT.md` written; honest phase boundary stated.

## No-go registry (slice-local)

- C3 is a boundary, not a failure: no ≥2-step execution exists and no
  Lean-witnessed decrease family applies to the Boolean carrier. No
  multi-step document is emitted here (that would be a different Lean
  statement — `rolloutKernel`/`cumulativeExpectedFreeEnergy` semantics —
  and is out of P3 scope).
- No evidence plane is reclassified: pymdp-internal computations that
  the executed runner serializes stay on the GNN-execution plane; the
  float64 evaluation of Lean closed forms stays on the numerical-witness
  plane; Lean theorems stay on the pinned-workspace compilation plane
  (delegated as in P1 — no local Lean compilation per constraints).
- If `simulation_results.json` were to stop exposing `policy_posterior`
  or `variational_free_energy`, the corresponding certificate is
  recorded as unstatable rather than recomputed off-plane.

## Evidence planes summary

| Quantity | Lean side | Executed side |
| --- | --- | --- |
| Q(π) | compilation (theorem :816-826) + numerical witness (exact rationals) | GNN pipeline execution (`policy_posterior`) |
| VFE | compilation (equalities :209-214, :762-773, :121-125) + numerical witness (`math.log(2)`) | GNN pipeline execution (`variational_free_energy`) |
| EFE (O1) | compilation (:148-150, :789-812) — different convention, compared informatively | GNN pipeline execution (`expected_free_energy` = pymdp `neg_efe`) |

## Historical provenance of the retained outputs

`gnn_output/` is a record of the 2026-09-03 certificate run, not a
reproduction against the current pin.

- The retained `FepLeanSymmetricBool_json.json` and `_parsed.json` signatures
  stamp `source_commit: 315e32994b59fd80e327b5b654c9f7852fad9933` (the FEP
  source this slice used) and
  `pipeline_commit: 12a565b2f18db7f18c3a799568ad057834ba0358`
  (`git describe` in the GNN repository: `v3.2.0-3-g12a565b2f`).
- The retained pipeline log shows the run executing the pre-rename step scripts
  `3_gnn.py`, `5_type_checker.py`, `11_render.py` and `12_execute.py` on
  2026-09-03; `src/3_gnn.py` no longer exists on current GNN `main`.
- The stamped `target_syntax` names `doc/gnn/gnn_syntax.md`; the file is now
  `docs/gnn/gnn_syntax.md`.
- Current custody is
  [`../gnn-bridge-w2-source-custody/source-pin.json`](../gnn-bridge-w2-source-custody/source-pin.json)
  (`gnn` = `v5.1.0` at `75c834bd8519dc7b5adc4d24f16bf393cfd1ecdf`; projections
  still from `2778e65c` until the pair-wide re-pin). The numbers in
  `certificates.json` were produced by the 2026-09-03 execution and are not a
  claim about the current pin.
