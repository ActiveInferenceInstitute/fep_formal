# Mathematical obligations for a Cascadia model matrix

A configured matrix reuses the [agent/process semantics](model-mismatch.md)
for an ordered set of cases. Its shared seed grid and horizon support controlled
descriptive comparisons; they do not supply new model-instance Lean proofs.
GEO-INFER-ACT owns the executable matrix and closed records. GNN owns each
notation-to-artifact reproduction. This slice reviews exact inputs and states
which mathematical hypotheses need a new checked witness.

For case $(Q,P)$, the process samples $o_t$ from $A_P(\cdot,s_t)$ and moves under
$B_P(\cdot,s_t,a_t)$. The agent uses $A_Q$ for the observation update and $B_Q$ for
belief prediction; $C_Q,D_Q,E_Q$ supply its preferences, initial belief and
habit. Process C/D/E do not initialize or govern that agent. The configured
true-state start is distinct from agent D.

| Change | Obligation for the named case |
| --- | --- |
| Agent A | Positive evidence for reachable process cues; posterior instance |
| Process A | Sampled cue law and support; score interpretation |
| Agent B | Belief prediction and policy evaluation assumptions |
| Process B | Realized transition locality, reachability and arrival bounds |
| Agent C/D/E | Preference, initial-support and policy/habit instances |
| Carrier or index meaning | Common ordered state/cue/action interpretation |
| Physical clock | Time interpretation of step-indexed statements |
| Seed grid or horizon | New execution and censoring records |

The denominator $\sum_j A_Q[o_t,j]q_t^-(j)$ must be positive for the update.
A cue reachable under P can violate that hypothesis under Q. The real runner
raises on impossible evidence; the matrix preserves the failed case and
finished predecessors without issuing a complete manifest. Conditioning with
an invented floor would change the model and its obligations.

The generic [diagnostic bounds](DiagnosticBounds.lean) apply to a finite
nonnegative posterior summing exactly to one: the full-carrier Brier score
against a point state lies in $[0,2]$. Equal dimensions or finite recorded
values do not discharge those hypotheses in Lean. The checked generic theorem
also does not prove that floating-point diagnostic code refines its real-number
definition. A process transition theorem concerns $B_P$; it cannot be reused
as a theorem about belief prediction under $B_Q$ solely because their shapes
match. Reference arrival witnesses remain bound to their exact carrier/tables.

Run [proof_impact.py](proof_impact.py) on each original condition directory,
retaining the notation, artifact and domain sidecar. The worksheet reports
exact changes relative to the reference and always records
`native_claim_ready: false`. Comparing two worksheets helps identify the two
roles' changes, but it is not a formal composition proof for the case. Current
GNN export qualification and ACT replay are separate evidence steps.

The consumer guide is `GEO-INFER-ACT/docs/cascadia_model_matrix.md` in GEO_INFER.
LectureCreate's `examples/cascadia_geo_act/matrix_companion.py` calls each
owning checkout's CLI in its explicitly selected environment and retains the
worksheets, exporter qualifications and comparisons. No new native receipt,
population effect, calibration claim or ecological claim follows from that
orchestration. The [validation record](publication-validation.md) documents
the preceding native and execution boundaries.
