# H2.3b: identifiability, consistency, and bounded risk

Status: **accepted**. Exit reviewed 2026-08-24.

## Outcome

Separate the statistical identification step from martingale convergence.
For the selected distinct-mean Gaussian model, derive posterior consistency,
weak convergence of the parameter posterior, and a bounded-continuous decision
consequence. Include an executable nonidentifiable boundary.

## Dependencies and owner

- H2.3a, H2.1a, and H2.0 rows `weak_bounded_continuous` and
  `weak_characteristic_function`.
- Same resource/module/role/namespace as H2.3a.

## Required declarations

- injectivity/separation of the two selected Gaussian observation laws;
- the limiting-observation measurability or likelihood-ratio identification
  lemma actually needed to identify the martingale limit;
- almost-everywhere posterior convergence to the true hypothesis under a
  positive prior and distinct means;
- weak convergence of the associated parameter `ProbabilityMeasure` to a
  Dirac law;
- convergence of bounded continuous posterior expectations;
- a bounded zero-one or explicitly bounded Bayes-risk consequence; and
- a same-law/nonidentifiable countermodel whose posterior remains the prior.

Martingale convergence, identification, weak convergence, and risk transfer
remain four separately named theorems.

## Acceptance contract

| Field | Required evidence |
| --- | --- |
| Entry | H2.3a/H2.1a are accepted and both named weak-convergence readiness rows remain green. |
| Red | The H2.3 test fails on missing identification, consistency, bounded-observable transfer, and same-law countermodel declarations. |
| Green | Warning-free compile and standard-axiom audit keep the four inference steps separate and instantiate the selected Gaussian laws. |
| Review | Statistical review checks prior support, truth measure, identification, topology, and boundedness. |
| Must stay green | H2.3a martingale tests, H2.1 Gaussian extensionality, H2.0 weak-convergence probes. |
| Feedback edge | Success contributes the statistical edge to H2.7; failure preserves only H2.3a. |
| Nearest excluded claim | Transfer of entropy, log loss, or any unbounded observable. |

## No-go

If identification fails, retain H2.3a's martingale limit but block the H2.3b
and H2.7 consistency clauses. Weak convergence never transfers entropy,
logarithms, or other unbounded observables without new domination or uniform-
integrability proofs.

## Exit evidence

- `FEP.PosteriorConvergence` keeps the accepted H2.3a prefix intact and adds
  five definitions, two named Markov-kernel instances, and twelve public
  theorems for identification, consistency, weak convergence, bounded risk,
  and the same-law boundary.
- Branchwise variance-one Gaussian strong laws identify the limiting
  observation conditional expectation through an explicit statistic measurable
  under the supremum of the finite observation filtrations. This is not a
  Kolmogorov tail-field theorem.
- Consistency holds under the selected joint law and separately under each
  fixed-truth trajectory law. Weak convergence is stated for native
  `ProbabilityMeasure`; only bounded continuous expectations and the bounded
  zero-one risk are transferred.
- The nonidentifiable model uses a native input-independent likelihood and
  proves posterior-equals-prior only almost everywhere under the predictive
  law.
- Direct Lean compilation is warning-free; the focused suite passes 25 tests;
  all 26 theorem axiom reports are standard-only and non-vacuous. Exact
  environment and typed-signature mutation tests reject hidden public
  declarations, extra theorem premises, and forbidden axioms. Fresh independent
  science review returned `APPROVE`.
- Integrated acceptance: 49 maintained modules, 1,412 theorem declarations,
  184 all-H2/formal tests, 8,758 Lake jobs, and 60 presentation-projection
  tests.
