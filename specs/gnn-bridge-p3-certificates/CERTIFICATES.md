# P3 certificates — FepLeanSymmetricBool

Identified result artifact: `simulation_results.json`.

Numerical comparison only; execution provenance unverified.
`execution_source_verified: false`; `native_claim_ready: false`.
A passing comparison does not establish a current pipeline execution or Lean proof.

| Certificate | Result | Lean value | Executed value | Delta |
| --- | --- | --- | --- | --- |
| C1 | PASS | Q = (0.25, 0.75) exact | policy_posterior[0] = (0.25, 0.7500000596046448) | |dfalse| = 0.000e+00, |dtrue| = 5.960e-08 |
| C2 | PASS | VFE_initial = log 2 = 0.6931471805599453 | variational_free_energy[0] = 0.6931471824645996 | |d| = 1.905e-09 |

C3 (directional agreement) is a recorded boundary, not run: the
instance is one-step and no Lean-witnessed decrease family exists
for the Boolean carrier (README C3).

## Evidence planes

- C1: Lean side = referenced Lean statement (native receipt checked separately) + numerical witness; executed side = reported numerical values; execution provenance unverified.
- C2: Lean side = referenced Lean statement (native receipt checked separately) + numerical witness; executed side = reported numerical values; execution provenance unverified.

## Observations (findings, exact numbers)

- O1: executed expected_free_energy[0] = 0.5 (pymdp neg_efe, linear utility, pymdp/control.py:422-445); Lean expectedFreeEnergy = log 2 = 0.6931471805599453 (active_inference.lean:148-150, :789-812); delta = 0.193147. different C conventions across the bridge surface; filed, not smoothed over (README O1)

Gate: PASS (C1 and C2 within tolerance).
