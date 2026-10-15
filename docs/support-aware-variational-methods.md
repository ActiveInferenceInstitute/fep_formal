# Support-aware Gibbs laws and finite Markov paths

These extensions reuse the normalized `FEP.FiniteLaw` and `FEP.FiniteKernel`
carriers. Canonical proofs live in the existing controlled-Markov, EFE-policy,
path-thermodynamics and thermodynamic-composition modules. They add generic
foundation results while retaining the 168 topic IDs, primary statements and
semantic dispositions. The [work package](../specs/support-aware-variational-methods/README.md)
records scope, acceptance and review.

## Gibbs normalization and support

For prior `q`, precision `γ` and cost `c`, the existing construction is
`Q*(a) = q(a) exp(-γ c(a)) / Z`. Its normalizer is strictly positive for every
real precision because the prior is a normalized finite law. No full-support
assumption is needed for normalization.

The controlled-Markov module now proves three reusable facts:

| Qualified name in `FEP.ControlledMarkov` | Exact boundary |
| --- | --- |
| `boltzmannPosterior_eq_zero_iff` | A posterior atom is zero exactly when its prior atom is zero. |
| `boltzmannPosterior_pos_iff` | A posterior atom is positive exactly when its prior atom is positive. |
| `log_boltzmannPosterior` | The posterior log is the prior log minus energy minus log normalizer, on an atom with positive prior mass. |

The logarithm premise is atomwise. At a shared zero atom a candidate-weighted
term must vanish before a logarithm identity is applied.

## Relative support and signed precision

Let `Q` charge only atoms with positive prior mass. The EFE-policy module derives
the exact identity

```text
γ E_Q[c] + finiteKL(Q, q) = finiteKL(Q, Q*) - log Z.
```

`efeControl_scaled_objective_eq_kl_sub_logPartition` holds for every real `γ`,
including zero. For nonzero `γ`, division yields the gap for the existing
objective `Jγ(Q) = E_Q[c] + γ⁻¹ finiteKL(Q, q)`:

```text
Jγ(Q) - Jγ(Q*) = γ⁻¹ finiteKL(Q, Q*).
```

The exact names are
`efeControlObjective_sub_eq_kl_of_relativeSupport` and
`efeControlObjective_eq_optimizer_iff_of_relativeSupport`. Nonnegative KL and
its equality characterization imply a unique minimum at positive precision
and a unique maximum at negative precision, among supported candidates. The
module includes strict inequalities for every supported nonoptimizer. The
released full-support theorem signatures remain available and consume the
stronger supported results.

The sparse witness has prior `[1/2, 1/2, 0]` and potential
`[0, log 3, 7]` (cost is its negative at precision one). Its partition is
exactly `2`, and its posterior is `[1/4, 3/4, 0]`. A large potential on the
forbidden atom cannot create mass. The prior is a strict nonoptimizer, and a
separate supported point-mass witness exhibits the negative-precision maximum.

Two proved countermodels delimit these results. Dropping candidate support
allows an unsupported Boolean point mass to beat the posterior under the
repository's real-valued totalized KL. At zero precision the posterior remains
the prior, while Lean's totalized reciprocal removes the KL penalty from the
divided objective; a full-support Boolean prior need not minimize expected cost.
The all-real scaled identity does not make that zero-precision objective a
minimization theorem. Negative precision here is a mathematical sign case,
without a physical precision interpretation.

The [numerical API](mathematical-methods.md#reusable-finite-variational-methods)
uses potential `φ = -γ c`. Its supported normalized diagnostic agrees with the
ordinary logarithmic KL interpretation. Its explicit infinity boundary is
extended KL; it does not replace the totalized finite functional at zero
reference mass. Numerical evaluations provide no native proof evidence.

## Actual marginals of general-horizon paths

For a homogeneous kernel `K`, initial law `μ₀` and horizon `n`, the maintained
path law assigns mass `μ₀(x₀) ∏ K(x_t, x_{t+1})`. Write `μ_t` for prediction
by `kernelPower K t`. New proofs establish actual pushforward laws:

| Qualified name in `FEP.PathThermodynamics` | Result |
| --- | --- |
| `markovPathLaw_map_coordinate` | Coordinate `t : Fin (n+1)` has law `μ_t`. |
| `markovPathLaw_map_stage` | Adjacent pair `t : Fin n` has joint law `μ_t(i) K(i,j)`. |
| `markovPathLaw_sum_coordinate` | Expectations of coordinate functions reduce to `μ_t`. |
| `markovPathLaw_sum_stage` | Expectations of adjacent-pair functions reduce to the corresponding joint. |

These reductions need no positivity assumptions. They follow from normalized
path masses, snoc decomposition and induction, without introducing a second
path carrier or assuming the desired marginals.

With positive initial law, terminal reference `ρ`, forward kernel `K` and
reverse kernel `R`, the existing full-path log-ratio split now reduces to

```text
EP(K, μ₀; R, ρ; n)
  = crossEntropy(μ_n, ρ) - entropy(μ₀)
    + Σ(t<n) Σ(i,j) μ_t(i) K(i,j) log(K(i,j) / R(j,i)).
```

The theorem is `entropyProduction_markov_marginal_decomposition`. Positivity
is explicit because the real totalized logarithm does not encode infinite
production at a zero reverse atom. For a stationary full-support chain against
the same reverse kernel, `entropyProduction_markov_stationary_horizon` proves
that production is `n` times its one-step value. The existing three-state
biased cycle therefore has production exactly `n * log(2) / 4`: zero at horizon
zero and strictly positive at every positive horizon.

## Reversible endpoint KL drop

Suppose `K` has positive entries and satisfies detailed balance for a positive
stationary law `π`. With a positive actual initial law, initialize the reverse
chain at the actual evolved endpoint `μ_n`. The pathwise ratio telescopes,
and the mean identity becomes

```text
EP(K, μ₀; K, μ_n; n) = finiteKL(μ₀, π) - finiteKL(μ_n, π).
```

`entropyProduction_markov_reversible_KL_drop` proves this for every horizon.
The qualified composition witness
`FEPComposed.fep099_markov_path_KL_drop_reduction` specializes it
to one step and explicitly consumes the existing fep-099 dissipation theorem.
Its namespace is part of the source contract, rather than an inferred graph
edge. No new authored scientific relation is installed by the import alone.

Reverse initialization matters. A native counterexample uses horizon zero and
a reversible reset kernel: replacing the actual endpoint by the stationary
law can give positive path production although the initial-minus-final KL
drop is zero. Reversibility by itself does not justify that replacement.

These are finite, exact statements. They identify no physical heat, biological
state, empirical outcome or continuous-time limit. Validation keeps native
compilation, declaration axioms, numerical checks and publication rendering
as separate evidence stages.
