# Mathematical obligations for separate agent and process models

GEO-INFER-ACT's `run_closed_loop(..., process_artifact=...)` distinguishes
the process laws $A_P,B_P$ from the agent laws $A_Q,B_Q,C_Q,D_Q,E_Q$.
The GNN artifact remains a finite categorical model with explicit matrix axes,
ordered state IDs and physical clock. Matching those fields is necessary for
pairing, but schema 1 cannot verify the meanings of observation/action indices.

## Which quantities belong to which model

The process emits a cue according to $A_P(o_t\mid s_t)$. Agent evidence is
$Z_Q(o_t)=\sum_s A_Q(o_t\mid s)q_t^-(s)$, not the process likelihood at the
true state. If $Z_Q=0$, Bayesian conditioning is undefined and execution fails;
the runner does not smooth a structural zero.

After conditioning, pymdp evaluates policies against $A_Q,B_Q,C_Q$ and the
habit $E_Q$. Its one-step state information gain and expected utility are
numerical Active Inference quantities, distinct from the process's realized
next state. The agent propagates $B_Qq_t$ while the process samples $B_P$.
Inference replay verifies the agent against the retained cue record; fresh
paired replay also regenerates the process states and cues.

| Statement | Hypotheses to revisit |
| --- | --- |
| Posterior and evidence instance | Agent A/D, previous selected actions, realized cue support |
| EFE decomposition | Agent A/B/C and the same posterior used by policy inference |
| Policy posterior | Agent E, policy order and backend precision/convention |
| Actual trajectory locality and lower bound | Process B support on the typed graph and initial true state |
| Belief-support light cone | Agent B/D, conditioning support and index alignment |
| Full-carrier Brier bounds | Exact normalized nonnegative agent posterior and a true-state index in the same carrier |
| Physical elapsed time | Both artifact clocks and observation timestamps |

The [existing diagnostic theorems](README.md#recorded-state-score-bounds) are
generic statements about finite real probability vectors. They do not require
the posterior to be accurate, but their application requires the stated exact
hypotheses. Floating-point execution and its tolerance are not a proved
refinement. A mismatch changes the interpretation of numerical results without
turning a generic bound into a native certificate for that model pair.

## Numerical evaluation of log preferences

For finite C, compute log preferences directly as $C-\log\sum_o e^{C_o}$.
Exponentiating and then taking a logarithm can underflow a mathematically
positive preference to zero. GEO's risk and pragmatic-cost evaluator uses the
log representation; the regression compares extreme finite preferences against
the real supported pymdp backend. This is a numerical implementation check,
not a newly formalized floating-point theorem.

## Evidence to retain

Keep both GNN sources and producer reproduction receipts, both consumed
artifacts and their distinct identities, the seed/horizon design, physical-clock
records and failed attempts. A pair manifest's portable integrity check is
relative to that manifest. Its optional fresh replay compares the actual
process/agent execution and numerical diagnostics. Native receipts and source
custody must be checked separately for each claimed theorem instance.

The consumer's `GEO-INFER-ACT/docs/cascadia_model_mismatch.md` documents its
retained four-pair comparison and deterministic HTML generation/freshness
check. Display integrity, finite score parsing and exact-byte freshness are
separate from actual inference replay and from native theorem admission.
