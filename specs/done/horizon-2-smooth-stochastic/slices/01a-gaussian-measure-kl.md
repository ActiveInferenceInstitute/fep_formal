# H2.1a: scalar Gaussian measure and native KL

Status: **accepted; H2.1b subsequently accepted**.

## Outcome

Own one nondegenerate fixed-variance scalar Gaussian probability family in
`formal/gaussian_information_geometry.lean`. Prove its measure/density
identity, normalization, support and absolute-continuity boundary, and the
correctly oriented native-KL formula. This slice introduces no coordinate
geometry beyond the minimum parameters needed to state the law.

## Dependencies and owner

- Solid dependency: H2.0 rows `scalar_gaussian_density_ac` and
  `scalar_gaussian_native_kl`.
- Resource: `gaussian_information_geometry.lean`.
- Module: `FepSketches.gaussian_information_geometry`.
- Role: `FOUNDATION`.
- Namespace: `FEP.GaussianInformationGeometry`.
- Exact direct imports at the H2.1a exit:
  `Mathlib.InformationTheory.KullbackLeibler.Basic` and
  `Mathlib.Probability.Distributions.Gaussian.Real`. H2.1b later added the
  direct calculus owner `Mathlib.Analysis.Calculus.Deriv.Mul` to this shared
  resource.

The structure may store only a fixed strictly positive variance and the raw
location parameter. Normalization, support, density, absolute continuity, and
KL values are theorems, not fields.

## Required declarations

- the canonical law and density at a named mean and positive variance;
- equality to `gaussianReal` and normalization on `Set.univ`;
- the density/Radon--Nikodym equality used by native KL;
- mutual absolute continuity for equal positive variance;
- the oriented native KL between two locations;
- zero-shift equality and nonzero-shift strict positivity; and
- a regression showing the singular/zero-variance boundary is not silently
  included.

The theorem orientation must be explicit in argument names and formula. Native
KL remains in `ℝ≥0∞`; any real-valued closed form is connected by a proved
`ENNReal.ofReal` equality under its exact finiteness premises.

## TDD and evidence

Red first: missing manifest tuple, exact imports/namespace, public declaration
roster, support premise, and orientation guard. Green requires warning-free
direct compilation, explicit axiom probes, a zero- and nonzero-shift example,
projection byte equality, and focused foundation/geometry tests.

## Accepted result

The manifested foundation owns `FixedVarianceGaussian`, its native density and
law, and eleven public theorems. The general equal-positive-variance result is

\[
D_{\mathrm{KL}}\!\left(\mathcal N(\mu_s,v)\,\middle\|\,\mathcal N(\mu_r,v)\right)
= \operatorname{ofReal}\!\left(\frac{(\mu_s-\mu_r)^2}{2v}\right),
\qquad v>0.
\]

**Copyable LaTeX**
```latex
D_{\mathrm{KL}}\!\left(\mathcal N(\mu_s,v)\,\middle\|\,\mathcal N(\mu_r,v)\right)
= \operatorname{ofReal}\!\left(\frac{(\mu_s-\mu_r)^2}{2v}\right),
\qquad v>0.
```

The proof derives the Radon--Nikodym ratio, affine log-likelihood ratio,
integrability, and source-law expectation directly. Zero shift is zero,
distinct means give strict positivity, and zero variance is excluded by the
carrier. The result makes no singular, multivariate, coordinate, or process
claim.

Acceptance evidence: the six slice tests pass; the direct source compile is
warning-free; all eleven public theorems use only `propext`,
`Classical.choice`, and `Quot.sound`; the 39-test focused integration and
62-test manifest-consumer matrices pass; release/subpackage consumers pass
128 tests; formal projection, coverage, atlas, dashboard, and H2.0 readiness
checks are current. Independent scientific review accepted the KL orientation,
support, codomain, and boundary.

## Acceptance contract

| Field | Required evidence |
| --- | --- |
| Entry | H2.0 `scalar_gaussian_density_ac` and `scalar_gaussian_native_kl` are `go`; the readiness validator stays green. |
| Red | `tests/test_horizon2_gaussian_information_geometry.py` first fails on the absent owner, exact imports, namespace, support premise, and KL orientation. |
| Green | Direct source compilation is warning-free; public axioms are standard only; manifest, projection, import, and declaration rosters are exact. |
| Scientific review | A reviewer checks source/reference order, `ENNReal` codomain, positive-variance/support premises, zero shift, and strict nonzero shift. |
| Must stay green | H1 finite/native KL boundary tests, formal manifest/projection drift, and `tests/test_horizon2_readiness.py`. |
| Feedback edge | Success opens H2.1b and H2.3a; failure closes every outgoing solid edge named below. |
| Nearest excluded claim | Singular or multivariate Gaussian KL. |

## No-go

If the density or native-KL bridge cannot be proved without assuming the
conclusion, retain the successfully proved Gaussian measure lemmas only and
block H2.1b, H2.2, H2.3, H2.5, and H2.7. Do not substitute the finite H1
`finiteKL`, an unverified density, or a certificate field.

## Excluded claims

No singular covariance, arbitrary Gaussian family, multivariate KL, entropy
rate, empirical fit, or stochastic-process result belongs here.
