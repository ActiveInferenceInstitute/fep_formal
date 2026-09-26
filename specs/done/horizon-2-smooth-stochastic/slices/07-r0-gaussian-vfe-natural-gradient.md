# H2.7-R0: continuous Gaussian VFE and natural-gradient gate

Status: **accepted; the source-bound `go` decision opens H2.7 implementation
only, while H3 remains closed**.

## Outcome

Establish the continuous-density variational-free-energy seam that the
accepted H2 owners do not yet provide. The gate must use the actual H2.6a
evidence density and posterior family, H2.1a's native recognition-to-posterior
KL orientation, and H2.1b's mean-coordinate Fisher metric. It must derive a
local natural-gradient descent direction rather than relabel coordinate
duality as a natural-gradient theorem.

This is a source-bound spike, not a maintained owner:

- Spike: `spikes/07_gaussian_vfe_natural_gradient.lean`.
- Test: `tests/test_horizon2_gaussian_vfe_readiness.py`.
- Decision: `readiness/repairs/07-gaussian-vfe-natural-gradient.json`.
- Namespace: `FEPProbe.H2_7GaussianVFE`.

The historical H2.0 readiness receipt is immutable. The accepted
[`go` decision](../readiness/repairs/07-gaussian-vfe-natural-gradient.json)
is an append-only source-bound record that opens H2.7 implementation only.

## Exact scientific carrier

For one `ScalarGaussianFilterModel`, one nondegenerate
`ScalarGaussianBelief`, and datum \(y\), let \(q_y\) be the maintained closed
Gaussian posterior and let \(p(y)\) be the actual evidence law's Lebesgue
density. Restrict recognition laws to the same fixed posterior variance and a
free mean \(m\). Define

\[
\mathcal F_y(m)
=D_{\mathrm{KL}}\!\left(q_m\,\|\,q_y\right)
-\log p(y).
\]

The source must state that the surprisal is relative to Lebesgue density. It is
not a singleton-event probability, a finite-law mass identity, physical
energy, expected free energy, or a claim about arbitrary recognition
families.

Writing \(m_y\) and \(V_y>0\) for the derived posterior mean and variance,
the gate must prove

\[
\mathcal F_y(m)
=\frac{(m-m_y)^2}{2V_y}-\log p(y),
\qquad
\partial_m\mathcal F_y(m)=\frac{m-m_y}{V_y}.
\]

The mean-coordinate Fisher metric is \(I_m=V_y^{-1}\), so its inverse applied
to the differential is the displacement \(m-m_y\). Along the derived local
flow \(m(t)=m-t(m-m_y)\), the time-zero derivative must be

\[
\left.\frac{d}{dt}\mathcal F_y(m(t))\right|_{t=0}
=-\frac{(m-m_y)^2}{V_y}<0
\quad\text{when }m\ne m_y.
\]

## Required proof surface

The exact roster is frozen before the first native compile. At minimum it must
prove:

1. `evidenceLaw` is `volume.withDensity evidenceDensity`;
2. evidence density is positive and finite at the selected datum;
3. VFE equals the oriented native KL plus density surprisal;
4. the VFE gap is the recognition-to-posterior KL and vanishes exactly at the
   posterior mean;
5. the mean derivative, Fisher inverse, and natural-gradient displacement are
   derived from accepted H2.1 declarations; and
6. the negative natural-gradient flow has a strictly negative local VFE
   derivative away from the posterior mean.

Definitions may store only the named density-relative surprisal, VFE,
natural-gradient tangent, and its local flow. Positivity, optimality,
derivatives, and strictness are theorems.

## Red-to-green contract

The red test rejects an absent spike, reversed KL, a point-mass evidence
substitute, a finite H1 `GenerativeModel`, a stored derivative or strictness
certificate, a recognition-coordinate descent claim disconnected from the
posterior, or an unqualified Fisher-equals-covariance statement.

Green requires warning-free compilation at the pinned Lean/Mathlib revision,
an exact syntax-independent public-environment census, typed consumers for
every public theorem, a nonvacuous per-theorem standard-axiom audit, source and
test hashes, and independent Lean, probability/information-geometry, and
skeptical claim-scope approvals.

## Stop/go

- **Go:** H2.7 may reproduce the reviewed bridge on its selected scalar model
  and connect it to the accepted posterior, semigroup, filter, control, and
  path declarations.
- **No-go:** preserve the compiled predecessor surface, remove the unsupported
  VFE/natural-gradient clause from any positive terminal claim through an
  explicit reviewed no-go, and keep continuous H3 eligibility closed. Never
  replace this gate with H1 finite VFE or with H2.2a coordinate duality alone.
