# Relations endpoint adjudication — coverage gate (SRC 1)

Verdict: **NO TIGHTEN confirmed for the reviewed-primary-qualified endpoint rule**;
relations-ledger review entries recorded for every offender row on 2026-09-22.

## Context

The [historical 2026-09-09 scope](https://github.com/ActiveInferenceInstitute/fep_formal/blob/cd4a84cd91d884d6952b2b2f1b0289b2bdfd36ed/SCOPE-2026-09-09.md)
item SRC 1 proposed tightening the
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

## LEAN-6 review: pairings whose witnesses are named like derivations (2026-10-08)

Issue #104 asked whether any `formal_pairing` edge whose witness name says
"specializes", "refines", "extends", or "bounds" is in fact a derivation that
should be tagged `formal`. The test applied is strict: re-tag only if the
witness statement consumes one endpoint's theorem and produces the other
endpoint's statement (or an exact instance of it). A witness that conjoins two
independently proved endpoint laws is a pairing, however it is named. This
section is maintained by hand; no generator writes it.

| Edge | Witness | Statement shape | Decision |
| --- | --- | --- | --- |
| fep-089 → fep-006 | `FEPComposed.fep089_finite_jet_shift_specializes_fep006` | `shift (a+b) j = shift a (shift b j) ∧ iterateFlow (shift 1) (a+b) j = iterateFlow (shift 1) a (iterateFlow (shift 1) b j)` | Keep pairing. The second conjunct is fep-006's additivity at the one-degree shift, but nothing identifies `shift n` with the n-fold iterate of `shift 1`, so the native law is not used to obtain it. |
| fep-092 → fep-032 | `FEPComposed.fep092_quadratic_convergence_specializes_fep032` | `Tendsto (predictionError ∘ iteratePredictionUpdate) ∧ Tendsto (fep032_quadraticUpdate^[n] estimate) (nhds target)` | Keep pairing; tightened rationale proposed (released row is digest-sealed, so the YAML wording changes only with a reviewed seal delta). The old wording called the iterations "equivalent", which the witness does not prove. |
| fep-110 → fep-028 | `FEPComposed.fep110_product_of_experts_refines_fep028_normalization` | `∑ unitWeightProductOfExpertsPool = 1 ∧ ∑ fep028_softmax = 1` | Keep pairing. Two unrelated normalization laws; the rationale already disclaims identifying the weighting conventions. |
| fep-115 → fep-042 | `FEPComposed.fep115_frequency_union_bound_extends_fep042_counts` | `law.real (⋃ deviation events) ≤ card * failure ∧ fep042_bernoulliLikelihood = p^successes * (1-p)^failures` | Keep pairing; tightened rationale proposed (released row is digest-sealed, so the YAML wording changes only with a reviewed seal delta). The likelihood factorization does not consume the union bound. |
| fep-116 → fep-001 | `FEPComposed.fep116_pac_bayes_refines_fep001_variational_bound` | `E_posterior[pop] ≤ E_posterior[emp] + (KL + log(1/δ))/β ∧ surprisal ≤ fep001_variationalUpperBound ...` | Keep pairing; tightened rationale proposed (released row is digest-sealed, so the YAML wording changes only with a reviewed seal delta). The fep-001 conjunct is an independent instance, not a consequence of the finite PAC-Bayes bound. |
| fep-063 → fep-014 | `FEPComposed.fep063_channel_dpi_bounds_fep014` | `finiteKL (channel actual) (channel reference) ≤ finiteKL actual reference ∧ 0 ≤ klDiv nativeActual nativeReference` | Keep pairing; tightened rationale proposed (released row is digest-sealed, so the YAML wording changes only with a reviewed seal delta). The native measures are unrelated to the finite laws, so the second conjunct is not a bound on the first. |
| fep-054 → fep-017 | `FEPComposed.fep054_involution_of_fep017_posterior` | `(likelihood†prior)†(likelihood ∘ₘ prior) =ᵐ[prior] likelihood ∧ posterior ∘ₘ likelihood ∘ₘ prior = prior` | Keep pairing; tightened rationale proposed (released row is digest-sealed, so the YAML wording changes only with a reviewed seal delta). Each conjunct is its own topic's theorem; neither is derived from the other. |

Outcome: zero re-tags. The `formal` edge count is not raised by this review.
Every kept row now states in its `rationale` that it was reviewed on this date
and why it is not a derivation.

## LEAN-8 review: isolated topics (2026-10-08)

Issue #106 asked for the four topics with no or only conceptual relations.
Verified at the start of the review: fep-007, fep-046 and fep-050 had no edge
at all, and fep-029 had a single `conceptual` edge (to fep-044). No existing
composition or foundation theorem mentioned any of the four, so none could be
related by an existing qualified witness. Each now has a small new theorem in
an existing composition leaf, with an explicit scope statement in its
rationale.

| Topic | New edge | Witness (leaf) | What the theorem proves |
| --- | --- | --- | --- |
| fep-007 | fep-007 → fep-028 `formal` | `fep007_normalizedMessage_is_fep028_softmax` (`control_temporal`) | With unit incoming messages and factor `exp (-gamma * cost)`, the normalized message equals the support-aware softmax on the support embedded from `Fin 8` into `Fin 10`; fep-007's primary theorem then gives the softmax unit sum. |
| fep-029 | fep-029 → fep-104 `formal` (the conceptual fep-044 edge is kept) | `fep029_quadraticBregman_is_fep104_scalar_instance` (`thermo_geometry`) | The scalar quadratic Bregman divergence is the `d = 1` instance of the generic Bregman divergence, and fep-104's three-point identity gives the scalar three-point law. |
| fep-046 | fep-046 → fep-045 `formal` | `fep046_single_break_is_fep045_bernoulli` (`core`) | One break is the Bernoulli law of fep-045; fep-046's mass conservation derives the normalization of fep-045's posterior mass function. |
| fep-050 | fep-050 → fep-049 `formal` | `fep050_landauer_work_bound_from_fep049_entropy_production` (`thermo_geometry`) | With the explicit premise `totalEntropyChange = entropyProduction`, fep-049's nonnegativity discharges fep-050's second-law hypothesis and yields the Landauer work bound. |

Caveats recorded with the edges: the fep-050 → fep-049 premise is a modeling
assumption, not a consequence of either topic; the fep-007 → fep-028 identity
fixes the factor and incoming messages; the fep-046 → fep-045 identity covers
one break only. The relations schema has no "isolated by design" field, and none
was needed because every topic received a witnessed edge.
