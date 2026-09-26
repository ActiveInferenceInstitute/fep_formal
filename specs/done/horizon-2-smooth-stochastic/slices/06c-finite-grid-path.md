# H2.6c: finite-grid path laws

Status: **accepted**.

## Outcome

Use `Kernel.partialTraj` only on a typed nondecreasing time grid to construct a
forward path law from the exact H2.5a kernel. Map that law through an explicit
coordinate-reversal involution to obtain a reverse-aligned comparison law.
Prove normalization, support-aware native KL identities, and both
absolute-continuity and integrability failure boundaries. The mapped law is
not called a reverse OU process. Continuous-path laws remain absent.

## Dependencies and owner

- Accepted H2.4b/H2.5a and H2.0 `finite_grid_trajectory`.
- Resource: `compositions/gaussian_grid_path.lean`.
- Module: `FepSketches.compositions.gaussian_grid_path`.
- Role: `COMPOSITION`.
- Namespace: `FEPComposed.GaussianGridPath`.
- Direct imports: H2.5a; native KL, Bochner integral, Radon--Nikodym, and exact
  Ionescu--Tulcea partial-trajectory owners. H2.4b remains a scheduling and
  must-stay-green dependency, but is not a direct import unless its declaration
  is named. The finite `path_thermodynamics` owner is forbidden because its
  `FiniteLaw`/`Fintype Path` carrier cannot represent real-valued grid paths.

## Required declarations

- a `TimeGrid` carrier whose timestamp function is monotone, so `NNReal`
  subtraction cannot silently turn a descending timestamp into a zero-duration
  transition; repeated equal timestamps remain permitted and explicitly denote
  the identity transition;
- the exact H2.5a step kernel read from the last grid coordinate;
- finite-grid `partialTraj` composition and forward-law normalization;
- measurable coordinate reversal, its involution law, and normalization of
  the mapped reverse-aligned law;
- a bounded-continuous observable map identity;
- a Radon--Nikodym ratio theorem under an explicit common dominating measure;
- forward-to-reverse-aligned native KL equal to the expected real log ratio
  under explicit absolute-continuity and integrability premises;
- nonnegativity of that real expected log ratio; and
- exact `∞` results when absolute continuity or log-ratio integrability fails.

Native `klDiv` is already nonnegative by codomain, so `0 ≤ klDiv` is not an
acceptance theorem. Stationarity is not reversibility. Deterministic starts and
repeated grid times do not acquire full-product density by assertion.

## Acceptance contract

| Field | Required evidence |
| --- | --- |
| Entry | H2.4b/H2.5a are accepted and H2.0 `finite_grid_trajectory` remains green. |
| Red | `tests/test_horizon2_gaussian_grid_path.py` rejects raw or descending timestamp functions, unnormalized laws, reversed composition orientation, `FiniteLaw` carrier substitution, pointwise density claims, vacuous KL nonnegativity, and continuous-path/Girsanov names. |
| Green | Warning-free compile and standard-axiom audit prove exact finite-grid laws, coordinate-reversal identities, support-aware native KL/real-log-ratio results, and bounded-observable transfer. |
| Review | Path-probability review checks grid order, support, KL direction, and finite-versus-continuous scope. |
| Must stay green | H2.5a/H2.4b, H2.0 `partialTraj` probe, existing finite path-thermodynamics boundaries. |
| Feedback edge | Success supplies only the finite-grid path clause to H2.7; failure removes that clause. |
| Nearest excluded claim | Girsanov or continuous-path entropy production. |

## No-go

Failure removes H2.6c and its terminal clause. Never infer path reversibility
from invariant marginals, Girsanov, continuous-path entropy production,
time-reversal SDEs, or transfer of unbounded observables. A forward-only spike
may remain unmanifested but is not H2.6c acceptance.

## Exit evidence

- The maintained composition owns one monotone `TimeGrid`, two abbreviations,
  seven definitions, and eleven public theorems. Every path, reversal, and KL
  API consumes the same typed grid and exact H2.5a transition.
- The malformed descending-schedule tracer failed before the carrier repair;
  it is green after raw timestamp functions became unrepresentable. Repeated
  times remain explicit zero-duration identity steps.
- Direct native compilation is warning-free. All eleven public theorems use
  only `propext`, `Classical.choice`, and `Quot.sound`; no `sorryAx` occurs.
- Eight focused tests pass. The final all-H2/formal/thermodynamic matrix passes
  124 tests with 19 expected opt-in skips, and the default Lean build completes
  all 8,753 jobs.
- Formal workspace, coverage, atlas, and dashboard projections are current at
  44 maintained modules, 28 foundations, and 1,284 theorem declarations.
- Fresh unprimed scientific and code reviews both returned `APPROVE`. The
  accepted result remains a finite-grid coordinate-reversal comparison, not a
  reverse OU process, reversibility theorem, continuous path, Girsanov result,
  or physical entropy-production law.
