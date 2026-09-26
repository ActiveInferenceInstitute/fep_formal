# H2.6b: filter-consuming finite control

Status: **accepted. Native compilation, standard-axiom, strict/tie witness,
packaging, and independent-review gates pass under the narrowed one-step
quadratic-risk contract**.

## Outcome

Add a finite action set and one-step posterior-conditioned quadratic decision
witness whose state belief is the exact H2.6a posterior and whose action
transition is the exact H2.5a/H2.4b native kernel. The objective consumes the
selected transition; this is not transition-aware tree planning or general
stochastic control.

## Dependencies and owner

- Accepted H2.4b, H2.5a, and H2.6a. H1.2/H1.4 remain must-stay-green
  interpretation and decision-boundary regressions, not direct owners of the
  continuous-state control result.
- Resource: `compositions/gaussian_control.lean`.
- Module: `FepSketches.compositions.gaussian_control`.
- Role: `COMPOSITION`.
- Namespace: `FEPComposed.GaussianControl`.
- Exact direct imports: `FepSketches.compositions.gaussian_filter`,
  `FepSketches.controlled_markov`,
  `FepSketches.gaussian_information_geometry`,
  `FepSketches.markov_semigroup`,
  `FepSketches.scalar_gaussian_semigroup`,
  `Mathlib.Probability.Distributions.Gaussian.Real`, and
  `Mathlib.Probability.Kernel.Posterior`.
- `controlled_markov` is the sole finite-minimizer owner through
  `finiteArgmin`; no policy-tree or active-inference import is justified.

## Required declarations

- finite action-indexed native transition using one H2.4b owner and one common
  positive comparison duration;
- belief input definitionally or theorem-equal to the H2.6a posterior;
- finite real-valued posterior-predictive terminal squared-error objective,
  plus a separately typed nonnegative action penalty;
- attained selected action and comparison with every alternative; and
- evidence-almost-everywhere agreement with selection from Mathlib's native
  posterior; and
- a literal Boolean strict-action witness plus an equal-risk tie boundary.

Squared terminal loss is unbounded as a statewise function. Its expectation is
finite under the selected Gaussian law, and the finite action image is bounded;
the source and tests must preserve this distinction.

## Acceptance contract

| Field | Required evidence |
| --- | --- |
| Entry | H2.4b/H2.5a/H2.6a are accepted; the exact Gaussian posterior and native action-kernel seams are current. |
| Red | `tests/test_horizon2_gaussian_control.py` rejects a second filter/belief/transition, an objective that ignores the selected transition, global `bayesRisk`/`IsBayesEstimator` substitution, and pointwise native-posterior equality. |
| Green | Warning-free compile proves the Gaussian closed-form risk from the actual composed law, finite attainment against every alternative, evidence-a.e. native-posterior selector agreement, a strict transition-derived Boolean witness, and a tie counterexample to generic uniqueness. |
| Review | Separate control/domain review checks the one-step horizon, transition dependence, Gaussian integrability, selector scope, and absence of EFE/reward relabeling. |
| Must stay green | H2.6a filter, H2.4b semigroup, H2.5a kernel, H1.2/H1.4 decision boundaries. |
| Feedback edge | Success supplies the transition-consuming one-step finite-control clause to H2.7; failure does not weaken filtering. |
| Nearest excluded claim | Mathlib global Bayes-estimator optimality, multi-step planning, infinite-horizon/HJB, or EFE-optimal stochastic control. |

## Exit evidence

- `FEPComposed.GaussianControl` derives the actual squared-loss integral under
  the selected OU transition composed with the H2.6a belief. Gaussian
  integrability is proved before the closed variance-plus-squared-bias formula;
  the action penalty remains separately typed and nonnegative.
- The finite selector reuses `FEP.ControlledMarkov.finiteArgmin`. Agreement
  with selection from Mathlib's posterior holds evidence almost everywhere,
  after intersecting the actionwise full-measure sets over the finite action
  type.
- A Boolean witness has exact posterior (N(0,1/4)), strictly selects the
  transition with risk (1/4) over the alternative
  (1/2-(1/4)\exp(-2)), and derives transition inequality from that strict
  risk separation. A separate equal-dynamics witness records the tie boundary.
- The public surface is frozen at one raw model structure, 17 definitions, and
  19 theorems. Canonical source, manifest, workspace projection, and aggregate
  ownership agree; direct compilation is warning-free; all named axiom probes
  are nonvacuous and standard only; and fresh independent control/science
  review returned `APPROVE`.

This is one-step posterior-predictive decision risk. It is not a global Mathlib
Bayes-estimator theorem, transition-aware tree planning, an EFE/reward
equivalence, multi-step stochastic control, or an infinite-horizon/HJB result.

## No-go

If control uses a second filter, transition, or belief carrier, it is blocked.
If the exact composed-law expected-square identity fails, do not store its
closed form as a certificate. If native-posterior equality does not lift
through the finite selector, retain the closed-form control result but keep its
native-control and H2.7 clauses closed. A generic Mathlib `bayesRisk` or
`IsBayesEstimator` result requires a separate measurable-selector gate. Do not
claim two-step policy-tree planning, EFE-optimal control, reward--EFE
equivalence, infinite horizon, Hamilton--Jacobi--Bellman, or physical work.
