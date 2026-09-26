# H2.5c: exact four-coordinate Gaussian carrier

Status: **accepted. The exact carrier, native semigroup, scalar
specialization, packaging, axiom, and independent-review gates pass. The
separate native conditioning/precision blocker was subsequently repaired by
accepted H2.5d-R0 and maintained H2.5d**.

## Outcome

Instantiate H2.5b on the preregistered four-coordinate standardized carrier in
the order external, sensory, active, internal. Prove the exact matrix algebra,
native transition, semigroup, invariant law, and weak convergence before the
H2 terminal merge. H3 may inspect this export but may not construct or repair
it.

## Dependencies and owner

- H2.5b.
- Resource: `fin4_gaussian_semigroup.lean`.
- Module: `FepSketches.fin4_gaussian_semigroup`.
- Role: `FOUNDATION`.
- Namespace: `FEP.Fin4GaussianSemigroup`.

## Fixed carrier

Use a named four-element axis type and explicit equivalence to `Fin 4`. The
precision and covariance are fixed as

\[
K_\star=
\begin{pmatrix}
4&-1&-1&0\\
-1&4&0&-1\\
-1&0&4&-1\\
0&-1&-1&4
\end{pmatrix},
\qquad
\Sigma_\star=
\begin{pmatrix}
7/24&1/12&1/12&1/24\\
1/12&7/24&1/24&1/12\\
1/12&1/24&7/24&1/12\\
1/24&1/12&1/12&7/24
\end{pmatrix}.
\]

**Copyable LaTeX**
```latex
K_\star=
\begin{pmatrix}
4&-1&-1&0\\
-1&4&0&-1\\
-1&0&4&-1\\
0&-1&-1&4
\end{pmatrix},
\qquad
\Sigma_\star=
\begin{pmatrix}
7/24&1/12&1/12&1/24\\
1/12&7/24&1/24&1/12\\
1/12&1/24&7/24&1/12\\
1/24&1/12&1/12&7/24
\end{pmatrix}.
```

## Required declarations

- exact entries, symmetry, inverse identities, and positive definiteness;
- exact leading principal minors \(4,15,56,192\) or an equivalently strong
  formal positivity witness;
- exact eigenvalues \(2,4,4,6\), by any warning-free pinned route including a
  characteristic-polynomial/eigenspace proof;
- exact transition kernel and semigroup inherited from H2.5b;
- invariant Gaussian and weak convergence;
- external--internal precision entry zero and covariance entry \(1/24\ne0\);
- standardized-coordinate and axis-order declarations; and
- equality of the normalized all-ones-mode projection to H2.5a with rate `2`
  and diffusion variance rate `2`; and
- a complete export theorem containing only proved clauses.

The H1 product order bridge belongs to a future H3 composition, not this
foundation.

## Acceptance contract

| Field | Required evidence |
| --- | --- |
| Entry | H2.5b is accepted; the H2.0 exact matrix witness stays green; `fin4_scalar_specialization` is repaired against the live H2.5a owner. |
| Red | `tests/test_horizon2_fin4_gaussian_semigroup.py` fails on axis order, exact entries/inverse, positive definiteness, named eigenmodes, native transition, and scalar projection. |
| Green | Warning-free compile and standard-axiom audit prove the fixed carrier end-to-end; deterministic rational diagnostics exactly match theorem values. |
| Review | Independent algebra/carrier review checks axis permutation, matrix orientation, and that covariance is derived rather than separately stored. |
| Must stay green | H2.5a/b, exact H2.0 Fin4 probe, manifest/projection/import parity. |
| Feedback edge | Success supplies the required separate export to H2.7. H2.5d opens only after its independent conditioning/precision repair passes; accepted H2.5d-R0 now satisfies that entry gate. |
| Nearest excluded claim | A positional/equinumerous H1 blanket coercion or arbitrary Fin4 model. |

## Exit evidence

- `FEP.Fin4GaussianSemigroup` uses one named axis order and stores the fixed
  precision matrix only; covariance is definitionally its inverse. Exact
  inverse entries, positive definiteness, four independent nonzero eigenmodes
  with eigenvalues (2,4,4,6), and the external--internal precision/covariance
  contrast are theorem-derived.
- The H2.5b transition, Markov semigroup, invariant Gaussian, moments, and weak
  limit specialize to the four-axis carrier. The normalized all-ones
  projection is exactly H2.5a at rate `2` and diffusion variance rate `2`.
- The public surface is frozen at 18 definitions and 42 theorems. A Lean
  environment census rejects any extra public declaration syntax, a typed
  consumer checks the complete export proposition, and every named theorem is
  axiom-free or uses only the accepted standard axioms.
- Canonical source and workspace projection are byte-identical; manifest and
  aggregate ownership are exact. Direct compilation is warning-free, and
  fresh independent algebra/science review returned `APPROVE`.

This exit proves algebra, transition, invariance, convergence, and the scalar
specialization. It does not prove native Gaussian conditioning, infer
conditional independence from a zero precision entry, establish detailed
balance, or open H3.

## No-go

If exact matrix algebra is green but native kernel measurability or semigroup
is red, H2.5c is blocked. A symbolic/numerical matrix receipt is diagnostic,
not a formal carrier.
