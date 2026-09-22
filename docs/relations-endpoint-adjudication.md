# Relations endpoint adjudication — coverage gate (SRC 1)

Verdict: **NO TIGHTEN confirmed for the reviewed-primary-qualified endpoint rule**;
relations-ledger review entries recorded for every offender row on 2026-09-22.

## Context

[SCOPE-2026-09-09](../SCOPE-2026-09-09.md) item SRC 1 proposed tightening the
theorem-witness endpoint check in
`src/fep_lean/catalogue/coverage.py:157-164`: instead of accepting any mention
of each endpoint's topic namespace, require a qualified reference to each
endpoint's reviewed primary theorem from
[config/theorem_maturity.yaml](../config/theorem_maturity.yaml). A prior dry-run
(recorded in the CHANGELOG verification-layer notes) found 89/125 edges failing
that strict rule, so the verdict was recorded as a relations-ledger review
rather than a code change. This record closes that review with per-site
evidence at commit `5b8650c`.

## Rule ladder, re-measured at 5b8650c

All 125 theorem-witnessed edges in
[config/formalism_relations.yaml](../config/formalism_relations.yaml) were
checked against each candidate rule over comment-stripped witness sources:

| Endpoint rule | Edges passing | Verdict |
| --- | --- | --- |
| Bare topic-namespace mention (gate as shipped) | 125/125 | current behavior |
| Review-namespace-qualified (`fep_fepNNN.FEPNNN.`) | 125/125 | viable, not adopted — see decision |
| Any reviewed theorem (primary ∪ supporting ∪ boundary) | 109/125 (16 fail, all `kind: formal`) | not adoptable without ledger re-authoring |
| Reviewed primary theorem only (the rule under adjudication) | 36/125 (**89 fail**) | **NO TIGHTEN confirmed** |

The strict rule therefore cannot be adopted without re-authoring 89 witness
rows; per the SCOPE decision rule the fix is a relations-ledger review, never a
code loosening. This lane reviewed the offender rows and recorded a review
entry on each; the gate code and every `witness` and `kind` are unchanged.

## Offender sites (measured, supersedes the stale 25-site count)

The offender sites group by topic as: fep-038×7, fep-009×4, fep-028×4,
fep-036×6, fep-049×3 — **24 call-sites** at `5b8650c`. (The earlier
f335724-era tally recorded 25 sites with fep-009×5, fep-028×5, fep-036×5; the
relation set shifted during the wave-D re-seal. The table below is measured at
this tip and is authoritative.)

Every site fails the strict rule only because the witness carries the relation
through the endpoint topic's reviewed *supporting* theorem (or, in one row,
through the topics' Fisher-metric definitions) rather than through the primary
theorem. Each row below now carries a dated `Reviewed 2026-09-22 against the
primary-qualified endpoint rule` entry in its `rationale` naming that evidence.

| # | Edge | Kind | Witness | Primary not cited | Reviewed supporting theorem(s) carrying the relation |
| --- | --- | --- | --- | --- | --- |
| 1 | fep-004 → fep-038 | formal | `FEPComposed.fep004_bernoulliMetric_specialization` | both sides | definitions only: `fep_fep004.FEP004.fep004_fisherMetric`, `fep_fep038.FEP038.fep038_fisherMetric` |
| 2 | fep-038 → fep-018 | formal_pairing | `FEPComposed.fep038_fisherRao_separation` | fep-038 | `fep_fep038.FEP038.fep038_fisherMetric_pos` |
| 3 | fep-101 → fep-038 | formal_pairing | `FEPComposed.fep101_fisher_pullback_extends_fep038` | fep-038 | `fep_fep038.FEP038.fep038_fisherMetric_pullback` |
| 4 | fep-102 → fep-038 | formal_pairing | `FEPComposed.fep102_cramer_rao_uses_fep038_score_geometry` | fep-038 | `fep_fep038.FEP038.fep038_expectedScore_zero` |
| 5 | fep-103 → fep-038 | formal_pairing | `FEPComposed.fep103_natural_gradient_extends_fep038` | fep-038 | `fep_fep038.FEP038.fep038_naturalGradient_duality` |
| 6 | fep-106 → fep-038 | formal_pairing | `FEPComposed.fep106_replicator_links_fep028_fep038` | fep-038 | `fep_fep038.FEP038.fep038_naturalGradient_duality` |
| 7 | fep-145 → fep-038 | formal_pairing | `FEPComposed.fep145_centeredScore_extends_fep038` | fep-038 | `fep_fep038.FEP038.fep038_expectedScore_zero` |
| 8 | fep-079 → fep-009 | formal_pairing | `FEPComposed.fep079_blanket_cmi_refines_fep009` | fep-009 | `fep_fep009.FEP009.fep009_joint_product_nonneg` |
| 9 | fep-081 → fep-009 | formal_pairing | `FEPComposed.fep081_coupled_blanket_composes_fep009` | fep-009 | `fep_fep009.FEP009.fep009_joint_product_nonneg` |
| 10 | fep-083 → fep-009 | formal_pairing | `FEPComposed.fep083_intervention_invariance_refines_fep009` | fep-009 | `fep_fep009.FEP009.fep009_likelihood_mono` |
| 11 | fep-085 → fep-009 | formal_pairing | `FEPComposed.fep085_local_markov_refines_fep009` | fep-009 | `fep_fep009.FEP009.fep009_condIndep_bot_right` |
| 12 | fep-012 → fep-028 | formal | `FEPComposed.fep012_softmax_entropyRegularizedCost_le` | fep-028 | `fep_fep028.FEP028.fep028_softmax_nonneg`, `fep_fep028.FEP028.fep028_softmax_le_one` |
| 13 | fep-070 → fep-028 | formal_pairing | `FEPComposed.fep070_controlPosterior_refines_fep028_softmax` | fep-028 | `fep_fep028.FEP028.fep028_softmax_probs_sum_one` |
| 14 | fep-076 → fep-028 | formal_pairing | `FEPComposed.fep076_variational_update_refines_fep028_softmax` | fep-028 | `fep_fep028.FEP028.fep028_softmax_probs_sum_one` |
| 15 | fep-110 → fep-028 | formal_pairing | `FEPComposed.fep110_product_of_experts_refines_fep028_normalization` | fep-028 | `fep_fep028.FEP028.fep028_softmax_probs_sum_one` |
| 16 | fep-036 → fep-045 | formal | `FEPComposed.fep036_empiricalPosterior_closed` | fep-036 | `fep_fep036.FEP036.fep036_smoothedRate_pos`, `fep_fep036.FEP036.fep036_smoothedRate_lt_one` |
| 17 | fep-042 → fep-036 | formal | `FEPComposed.fep036_empiricalPosterior_closed` | fep-036 | same as row 16 (shared witness) |
| 18 | fep-114 → fep-036 | formal_pairing | `FEPComposed.fep114_subgaussian_tail_refines_fep036_empirical_rate` | fep-036 | `fep_fep036.FEP036.fep036_smoothedRate_pos` |
| 19 | fep-121 → fep-036 | formal_pairing | `FEPComposed.fep121_laplaceError_extends_fep036` | fep-036 | `fep_fep036.FEP036.fep036_smoothedRate_eq_shrunkEmpirical` |
| 20 | fep-122 → fep-036 | formal_pairing | `FEPComposed.fep122_laplaceBias_extends_fep036` | fep-036 | `fep_fep036.FEP036.fep036_smoothedRate_mem_Ioo` |
| 21 | fep-123 → fep-036 | formal_pairing | `FEPComposed.fep123_laplaceAbsoluteError_extends_fep036` | fep-036 | `fep_fep036.FEP036.fep036_smoothedRate_eq_shrunkEmpirical` |
| 22 | fep-025 → fep-049 | formal | `FEPComposed.fep025_current_dissipation_nonneg` | fep-049 | `fep_fep049.FEP049.fep049_entropyProduction_nonneg` |
| 23 | fep-094 → fep-049 | formal_pairing | `FEPComposed.fep094_path_kl_refines_fep049_entropy_production` | fep-049 | `fep_fep049.FEP049.fep049_entropyProduction_nonneg` |
| 24 | fep-096 → fep-049 | formal_pairing | `FEPComposed.fep096_integral_fluctuation_refines_fep049` | fep-049 | `fep_fep049.FEP049.fep049_flux_force_identity` |

Three of the sixteen edges that also fail the weaker any-reviewed-theorem rule
fall inside these groups (row 1 on both sides; rows 17 and 22 on their
non-listed sides). Those
witnesses relate the topics through the topics' *definitions* — the composed
theorems construct and connect the endpoint objects directly (Fisher metric,
smoothed empirical rate, entropy production) without invoking any reviewed
theorem, which is theorem-structure evidence, not a spurious namespace mention.

## Decision

1. **No code change.** The strict reviewed-primary rule stays unimplemented;
   the shipped gate is untouched, and no projection-affecting loosening was
   made.
2. **Ledger review entries recorded.** Each of the 24 offender rows in
   [config/formalism_relations.yaml](../config/formalism_relations.yaml) now
   carries a dated review entry naming the reviewed supporting theorem (or
   definitions) that actually carries the relation, and stating that the row
   stands unchanged.
3. **Projections regenerated.** `docs/formalism-coverage.json`,
   `docs/formalism-coverage.md`, and `docs/formalism-atlas.*` were regenerated
   from the amended ledger and pass their `--check` gates.
4. **Follow-up for a future wave.** Satisfying the strict rule would require
   re-composing 89 witnesses to cite each endpoint's primary theorem — a
   Lean-authoring relations effort, deliberately not simulated here. The
   review-namespace-qualified tightening (125/125 green) remains available as
   a strictly stronger, non-breaking gate if that wave lands.
