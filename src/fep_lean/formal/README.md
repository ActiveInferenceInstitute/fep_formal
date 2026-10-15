# Maintained formal Lean kernel

This package resource is the maintained home for the reusable foundation
modules and the leaf modules that genuinely compose catalogue rows. The exact
roster and roles live in `manifest.py`; `composed.lean` is the import-only
aggregate over the composition leaves. Run
`uv run python scripts/_maint_build_formal_modules.py` after an edit, and use
`--check` in CI or review.

Topic-local Lean remains in the family modules under
`fep_lean.catalogue.bodies`. Foundation imports are explicit implementation
dependencies; `config/formalism_novelty.yaml` and
`config/formalism_relations.yaml` separately name every required bridge,
authored scientific relation, and capability witness.

The current foundation surface includes:

- normalized finite kernels, zero-safe entropy, support-aware finite KL,
  conditional KL, chain rules, and finite Bayesian inversion;
- posterior VFE, variational duality, one-step and cumulative EFE, controlled
  kernels, temporal smoothing, and finite Markov dissipation;
- static, dynamic, and intervention-aware blanket factorization together with
  predictive-coding and generalized-coordinate updates;
- normalized forward/reverse path laws, entropy production, fluctuation and
  Jarzynski identities, local detailed balance, and reversible KL decay;
- Fisher lowering and pullback, categorical tangent geometry, scalar
  Cramer--Rao, chart-equivariant natural gradients, mirror descent, Bregman
  projection, and replicator equivalence;
- product-agent and collective objectives, consensus dynamics, finite
  concentration, PAC-Bayes, posterior odds/concentration, mixture regret, and
  Bayes-factor updates;
- exact Laplace error decomposition, finite-law squared/Brier-risk transfer,
  and concentration-event containment;
- finite observation-contingent policy trees, Bellman minimization, open-loop
  embedding and dominance, treewise EFE decomposition, and a strict Boolean
  feedback witness;
- weighted-Dirac finite-law/kernel embeddings, expectation and prediction
  transfer, native `CondIndepFun`, measurable coarsening, and rowwise blanket
  transition closure;
- finite scalar exponential-family normalization, log-partition derivatives,
  centered scores, Fisher/variance equality, KL/Bregman duality, and an
  interval-local mean-coordinate injection; and
- an exact positive-rate Boolean continuous-time semigroup with forward and
  backward master equations, stationarity, detailed balance, relaxation, and
  quadratic Lyapunov decay.

The [support-aware variational extension](../../../docs/support-aware-variational-methods.md)
strengthens the existing Gibbs construction with exact support preservation,
relative-support gaps and signed-precision optimization. General-horizon path
proofs now establish actual coordinate/stage marginals, reduce production to
endpoint/stage laws, prove stationary linear growth, and identify reversible
endpoint KL loss with a qualified one-step fep-099 bridge.

The exact resource list is the typed manifest, rather than this synopsis. The
remaining support, positivity, independence, and invertibility premises in the
declarations are part of the results, not removable prose.

Every maintained public theorem is included in the declaration/axiom audit,
and every formal relation or capability witness must resolve from canonical
declarations. Private helper lemmas are covered transitively through the
public probed theorems that depend on them and are folded into the coverage
report's declaration totals.
Validate projection, compilation, and evidence axioms with:

```bash
uv run python scripts/_maint_build_formal_modules.py --check
cd lean && lake build FepSketches
cd .. && uv run python scripts/audit_formalisms.py \
  --receipt output/formalism-audit.json
```
