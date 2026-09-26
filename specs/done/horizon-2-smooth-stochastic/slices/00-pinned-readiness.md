# H2.0: pinned-library readiness barrier

Status: **accepted with explicit boundaries**.

## Outcome

Every row in [`../readiness/matrix.yaml`](../readiness/matrix.yaml) now carries
evidence from a minimal warning-free Lean example or a bounded negative
source/identifier search at the exact supported pin. H2.0 owns no maintained
formal module, theorem namespace, manifest row, projection, catalogue topic, or
publication claim.

## Dependencies

- accepted [Horizon 1](../../done/horizon-1-finite-synthesis/README.md);
- Lean `v4.33.1`;
- Mathlib tag `v4.33.1` at revision
  `0df444a360eaa60ab8c11dca51a86af692955474`; and
- the source-bound toolchain, manifest, and pin audits already maintained by
  the repository.

## Probe contract

Each positive probe must contain at least one `example` exercising the intended
construction. `#check` may document an API but cannot by itself make a row
`go`. Compile probes one at a time from `lean/`, fail on warnings, and retain no
generated `.olean` in the spec directory.

The probe suite is:

1. `01_api_surface.lean`: warning-free low-risk smoke over the exact pin;
2. `01_calculus.lean`: finite sums, exponential/logarithmic derivatives, and
   finite-coordinate Fréchet derivatives;
3. `02_local_geometry.lean`: required coordinate duality plus separately
   optional Riemannian/covariant packaging;
4. `03_weak_convergence.lean`: bounded-continuous and characteristic-function
   forms of weak convergence;
5. `04_posterior_martingale.lean`: posterior kernel, conditional expectation,
   martingale limit, and optional native Bayes-estimator vocabulary;
6. `05_scalar_gaussian.lean`: scalar density/AC, moments, parameter
   measurability, affine convolution, and native KL;
7. `06_native_semigroup_bridge.lean`: native composition/invariance/DPI and
   exact finite `embeddedKernel` functoriality;
8. `07_fin4_matrix_gaussian.lean`: finite-dimensional matrix algebra, exact
   `Fin 4` witness, a partial scalar-specialization ingredient, a deliberately
   insufficient generic covariance-PSD example, and a genuine state-dependent
   multivariate Gaussian kernel;
9. `08_gaussian_conditioning.lean`: native conditional-law/factorization and
   exact scalar filter-posterior feasibility;
10. `09_finite_grid.lean`: `Kernel.partialTraj` fixed-grid construction and
    support boundaries;
11. `10_brownian_fdl.lean`: optional finite-dimensional/pre-Brownian
    regression; and
12. `11_unsupported_api_search.yaml`: source-bound negative searches for six
    excluded API families.

If one source file supports several matrix rows, record the same probe digest
on each row while keeping the scientific obligations distinct.

## Matrix evidence

The final matrix record for every row must add:

- exact command and working directory;
- exit code;
- warning count and digest;
- probe SHA-256, plus every project-owned source digest used by the probe;
- declarations actually used, after removing aspirational entries;
- observed status: `go`, `optional_no_go`, or `blocking_no_go`;
- the smallest missing obligation; and
- the exact row-to-slice readiness closures disabled by a no-go. These are
  gating metadata, not a duplicate of the canonical scheduling DAG.

The matrix currently owns 42 atomic rows rather than one row per probe, so a
green measure constructor cannot certify density/KL, kernel measurability,
conditioning, or convergence. The matrix as a whole records a deterministic
digest over its canonical rows.
The focused test must reject missing, duplicate, reordered, unknown, or stale
rows and any `go` row without a compiled `example`.

## Bounded negative searches

Search the locked Mathlib tree for stochastic integration, Itô formula,
general SDE existence/uniqueness, Fokker--Planck solutions, Girsanov,
continuous-path density ratios, specialized Gaussian conditioning, and a
general Markov-semigroup interface. Record exact patterns, roots, revision,
and result counts. A zero result means only “not found in this bounded search.”
It does not establish mathematical impossibility.

Do not commit an intentionally failing Lean file. A failed exploratory probe
is summarized in the matrix, then either repaired to a truthful positive probe
or removed when its row becomes a no-go.

## Red-to-green sequence

1. Add a failing readiness-contract test for the absent matrix evidence.
2. Compile the pin/API-surface probe and close only its rows.
3. Close each remaining row through a separate red-to-green cycle.
4. Run the final schema, digest, tamper, absence, and opt-in serialized-compile
   tests.
5. Perform refactor-clean, code review, and choice audit before opening H2.1.

## Exit evidence

- Decision distribution: 25 `go`, 13 `optional_no_go`, three
  `blocking_no_go`, and one `upstream_required`.
- Canonical acceptance: 34 passed, zero warnings, with exact source hashes in
  [`../readiness/acceptance.json`](../readiness/acceptance.json).
- Static validation: `uv run python
  specs/horizon-2-smooth-stochastic/readiness/validate.py --check`.
- The validator rejects pending/reordered/tampered rows, missing probes, stale
  receipt or source digests, and a maintained H2 formal resource during the
  H2.0 capture phase. The receipt permanently records that empty capture roster;
  the completed validator permits later accepted slices to add resources.
- Blocking rows: `transition_covariance_psd`,
  `gaussian_conditioning_precision`, and `native_filter_posterior`.
- Upstream-required row: `fin4_scalar_specialization`.

## Exit gate

H2.0 is green only when:

- every required row is `go` or the affected solid edge and terminal clause
  have been explicitly removed through review;
- optional no-go rows name their excluded claims;
- the pin and every probe/source digest are current;
- all positive probes compile warning-free in serialized order;
- the captured receipt proves that no maintained H2 formal resource or manifest
  entry existed at the H2.0 boundary; and
- README, HANDOFF, choices, design DAG, and the matrix agree.

This gate is satisfied. Only slices whose exact incoming rows are green may
open; H2.1a is next. The named blocking and upstream-required edges remain
closed, and H3 remains closed.
