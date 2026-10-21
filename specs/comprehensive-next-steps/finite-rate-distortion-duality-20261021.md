# F07 finite rate-distortion duality source candidate

This is the active source contract for [issue76](https://github.com/ActiveInferenceInstitute/fep_formal/issues/76), refining the existing F07 matrix in [work-packages.json](work-packages.json). Maintained qualification and acceptance remain pending. Follow the [research contract](../../docs/design/fep-research-program/research-contract.md).

| Field | Contract |
| --- | --- |
| Outcome | Every feasible finite nonnegative-distortion problem has an attained information minimum equal to the Lagrangian dual supremum. |
| Depends on | F03 and the existing finite-law compactness/continuity minimum. |
| Single owner | Existing `src/fep_lean/formal/variational_duality.lean`; regenerate its existing manifested workspace projection. |
| Stop/go spike | Actual fixed-source MI convexity with zero atoms, closed upper image, strict epsilon separation, and normalized infimum lower bounds. |
| Go condition | Strict Lean 4.35 compiles the exact finite-law conclusions with standard-only axiom reports and independent review. External core has passed; maintained gates remain pending. |
| No-go action | Block the closed-image -> epsilon-support -> all-feasible-dual-supremum clause if its actual proof fails; keep the separately proved strict-feasibility theorem scoped, without promoting endpoint attainment. |
| Theorem/API target | `rateDistortion_exists_minimizer_and_dual_supremum` uses finite `FiniteLaw` carriers, nonnegative real distortion and actual feasible-law existence. `rateDistortion_exists_slater_dual_optimizer` and `rateDistortion_primal_dual_extrema` additionally assume actual strict feasibility for a finite maximizing multiplier and complementary slackness. |
| Positive witness | Recover the maintained fair-Boolean natural-log curve as the dual supremum on the closed interval from 0 to 1/2; derive positive quarter-budget primal/dual attainment. |
| Boundary result | Actual zero-budget Boolean supremum log2; zero-distortion no-Slater equality with lambda0; negative-budget infeasibility; nonunique half-budget minimizers; zero atoms retained by fixed-source convexity. |
| Test surface | Formal manifest/projection and relation checks, canonical source signatures and installed-wheel parity, strict foundation/default build, actual serial/native catalogue lane, declaration/axiom audit, full Python/browser/coverage, deterministic publication and scoped PDF review. |
| Evidence plane | Formal/native/source/API/publication; no numerical or empirical promotion. |
| Human review | Independent Lean, domain and skeptical scientific review of the maintained exact source. This is a finite subpackage, not terminal horizon acceptance; terminal approvals remain separate. |
| Out of scope | Supplied optimizer/equality certificates, all-budget finite dual attainment, uniqueness, arbitrary-joint MI convexity, continuous alphabets, empirical claims. |

The source uses Lean `v4.35.0`, Mathlib `v4.35.0` at `56a005855ea17e0b0958f73ec801ae140b0a1679`. Pinned scalar entropy concavity, compactness, closed compact-plus-cone geometry and strict Hahn--Banach separation suffice; no upstream library no-go is asserted.

The primal set and dual-value set are explicitly nonempty. Mutual-information nonnegativity bounds the primal infimum; actual weak duality at a feasible minimizer bounds the dual supremum. Strict separation below the optimum gives arbitrarily close dual lower bounds even when Slater fails. Finite multiplier attainment uses the separate strict-feasibility theorem. No finite endpoint multiplier follows from equality of values.

External source probes and independent reviews are retained in the workspace evidence ledger. Their compilation does not substitute for the current maintained-source commands and receipts. Keep F07 and issue76 open until those gates and independent maintained reviews pass.
