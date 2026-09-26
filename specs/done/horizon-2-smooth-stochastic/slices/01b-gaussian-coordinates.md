# H2.1b: Gaussian coordinates, score, Fisher, and Bregman laws

Status: **accepted; H2.2a subsequently exited**.

## Outcome

Extend the H2.1 owner with the fixed-variance scalar Gaussian location family's
natural and mean coordinates. The coordinate labels are part of every public
theorem and prevent the false unqualified claim that mean-coordinate Fisher
information equals covariance.

## Dependencies and owner

- H2.1a and the H2.0 `coordinate_duality` route. The accepted implementation
  rewrites the actual Gaussian log-density ratio to a quadratic before
  differentiating, so the provisional `finite_sum_derivatives` and
  `real_exp_log_derivatives` rows are not implementation dependencies.
- Same resource, module, role, and namespace as H2.1a.
- No additional project-local geometry carrier.
- Exact live imports are `Mathlib.Analysis.Calculus.Deriv.Mul`,
  `Mathlib.InformationTheory.KullbackLeibler.Basic`, and
  `Mathlib.Probability.Distributions.Gaussian.Real`.

For fixed variance \(v>0\), use natural coordinate \(\eta=\mu/v\). The required
identities are

\[
A''(\eta)=I_{\eta}=v=\operatorname{Cov}(X),
\qquad I_{\mu}=v^{-1}.
\]

**Copyable LaTeX**
```latex
A''(\eta)=I_{\eta}=v=\operatorname{Cov}(X),
\qquad I_{\mu}=v^{-1}.
```

## Required declarations

- mutually inverse mean/natural coordinate maps on the positive-variance
  domain;
- natural log partition and its first/second derivatives;
- natural- and mean-coordinate scores, each centered under the same law;
- natural Fisher equals variance/covariance;
- mean Fisher equals reciprocal variance;
- the proved pullback relating the two metrics;
- oriented KL equals the natural-coordinate Bregman divergence; and
- injectivity of the selected mean map.

Global Legendre bijectivity, boundary essential smoothness, and manifold
completeness are not inferred from these scalar local/global-coordinate facts.

## TDD and evidence

Red first on the exact coordinate-qualified theorem roster and a forbidden
unqualified mean-coordinate covariance claim. Green requires warning-free
compile, derivative-domain visibility, exact axiom audit, and numerical
zero/nonzero diagnostics labeled non-proof.

## Accepted result

The existing owner now contains one pair of inverse coordinate maps,

\[
\eta=\mu/v,
\qquad \mu=v\eta,
\]

**Copyable LaTeX**
```latex
\eta=\mu/v,
\qquad \mu=v\eta,
```

and derives the coordinate-specific information identities

\[
A'(\eta)=\mu,
\qquad A''(\eta)=I_\eta=v=\operatorname{Cov}(X,X),
\qquad I_\mu=v^{-1}.
\]

**Copyable LaTeX**
```latex
A'(\eta)=\mu,
\qquad A''(\eta)=I_\eta=v=\operatorname{Cov}(X,X),
\qquad I_\mu=v^{-1}.
```

Both scores are derivatives of the actual same-variance Gaussian log-density
ratio and are centered under the corresponding law. Mean-coordinate Fisher is
proved as the two-Jacobian-factor pullback of natural-coordinate Fisher.
Literal covariance, the oriented natural Bregman identity, and injectivity of
both the natural-to-mean map and the fixed-variance law are theorem-visible.

Acceptance evidence: five slice tests and the combined eleven H2.1 tests pass;
the direct compile is warning-free; all twenty coordinate theorems use only
`propext`, `Classical.choice`, and `Quot.sound`; the module builds through
3,124 Lake jobs; 23 central formal-owner tests, 62 formalism consumers, and 128
release/subpackage consumers pass. Formal workspace, coverage, atlas,
dashboard, and H2.0 readiness checks are current. Independent review returned
GO after requiring literal covariance and an allowlisted coordinate-qualified
Fisher/covariance name.

## Acceptance contract

| Field | Required evidence |
| --- | --- |
| Entry | H2.1a is accepted and all three named calculus/coordinate readiness rows remain `go`. |
| Red | The H2.1 test rejects an absent or unqualified coordinate roster and any mean-coordinate “Fisher equals covariance” statement. |
| Green | Warning-free compilation derives both coordinate maps, scores, Fisher values, pullback, and oriented Bregman/KL equality with visible (v>0). |
| Review | Lean and domain reviewers separately check derivative domains and coordinate labels; refactor review rejects a second geometry carrier. |
| Must stay green | H2.1a support/KL tests, H2.0 calculus probes, manifest/projection/import parity. |
| Feedback edge | Success opens H2.2a and contributes to H2.7; failure leaves H2.1a intact. |
| Nearest excluded claim | Global Legendre/manifold completeness. |

## No-go

If the native measure result remains green but a calculus identity fails, keep
H2.1a and block H2.1b/H2.2/H2.7 geometry. Do not store a Fisher value, use
finite score algebra as the Gaussian proof, or rename one coordinate as the
other.
