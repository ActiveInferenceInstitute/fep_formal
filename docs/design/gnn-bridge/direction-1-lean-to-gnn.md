# Direction 1 — render and execute Lean-expressed generative models

Status: **research program; P1 and P2 accepted under
`specs/gnn-bridge-p1-finite-spike/`** (finite spike executed end-to-end;
projection regenerable with a freshness gate). P3, P4, and the certificate
content proposal below are prospective; every named module and command below
exists today. Parent program:
[GNN bridge README](README.md). Shared rules:
[bridge contract](bridge-contract.md).

## Goal

Given a Lean expression of a generative model in this catalog — a compiled,
`sorry`-free body naming explicit laws, kernels, and dynamics — produce a GNN
document that the GNN toolchain validates, renders, and executes, then carry
execution-derived quantities back as certificates checked against
Lean-witnessed properties.

The manuscript's own framing
(`manuscript/05d_comparative_analysis.md:37-39`) is the grounding: executable
tools "specify and run model instances" while Lean "states and proves
invariants", and end-to-end assurance needs both plus a proof that the
executable representation refines the formal one. The certificate stage of
this direction is that refinement claim, made checkable one model at a time.

## What the catalog supplies today

All names below are verified, compiled declarations in the pinned workspace
(`lean/FepSketches/`, projected byte-for-byte from `src/fep_formal/formal/` per
`src/fep_formal/formal/manifest.py`).

| Lean module | What it formalizes | Bridge relevance |
| --- | --- | --- |
| `active_inference.lean` | `GenerativeModel` (finite policy-conditioned POMDP: initial state, policy-indexed transition, likelihood, preferences, policy prior), `predictedState`/`predictedJoint`/`predictedOutcome`, `variationalFreeEnergy`, both EFE decompositions (`expectedFreeEnergy_eq_risk_add_ambiguity`, `epistemicValue_eq_entropy_sub_ambiguity`), `policyPosterior`, `ActionInterface`, `inferSelectActKernel` | the direct counterpart of the GNN discrete POMDP family |
| `finite_probability.lean` | `FiniteLaw`, `FiniteKernel`, `pointMass`, `uniform`, `product`, marginals | the carrier every emitted categorical matrix denotes |
| `finite_information.lean` | `entropy`, `finiteKL`, `crossEntropy`, `conditionalEntropy`, `mutualInformation` | certificate quantities (KL/VFE direction checks) |
| `temporal_inference.lean` | `FiniteHMM`, `forwardPrediction`, `forwardEvidence`, `forwardFilter_reconstruction`, `forward_backward_evidence_agree`, smoothing, `modelAverage` | the inference loop executed agents perform |
| `markov_blanket.lean` / `native_blanket.lean` | `Blanket`, `StaticModel`, blanket factorization, `staticJoint_condIndepFun` (native `CondIndepFun`) | structural validation of emitted blanket models |
| `controlled_markov.lean` | `ControlledKernel`, `actionBeliefUpdate`, `boltzmannPosterior`, `ReachableBeliefPOMDP`, `SophisticatedEFEModel` | policy and belief behavior of executed agents |
| `policy_tree.lean` | `PolicyTree`, `policyTreeValue`, `EFEPolicyTreeModel`, `policyTree_efe_eq_risk_add_ambiguity` | closed-loop planning behavior |
| `linear_gaussian_semigroup.lean` | `LinearGaussianParameters`, transition mean/covariance laws, `stationaryLaw_invariant`, OU specialization | the direct counterpart of the GNN continuous family (`F/H/Q/R`) |
| `scalar_gaussian_semigroup.lean` / `continuous_time_markov.lean` | scalar OU kernel, finite-rate semigroups, `nativeKL_contraction`, `ouKL_to_stationary_nonincrease` | KL-decrease certificate targets |

## Extraction contract (what a projectable definition must expose)

A Lean definition is projectable when the projection is mechanical:

1. **Index types.** Fintype carriers for hidden states, observations, and
   actions project to GNN dimension declarations.
2. **Named roles.** Law/kernel components whose roles match the GNN family
   grammar — prior (`D`), transition (`B`), likelihood (`A`), preferences
   (`C`), habit (`E`) for the discrete family; transition/readout/noise
   (`F/H/Q/R`) for the continuous family.
3. **Parameterization.** Explicit values or symbolic parameters; the
   projection records exact values and the rounding decision separately
   (contract section 9).
4. **Timescale.** One-step vs repeated/horizon semantics (`kernelPower`,
   `transition_add`) map to GNN `Time` and `ModelParameters`.
5. **Nothing else.** Any field requiring interpretation beyond the named
   declarations fails the projection (no-go registry).

## Pipeline stages

FEP_Formal side (evidence commands per `docs/cli-reference.md`):

```bash
uv run fep-formal verify --fail-on-warnings --receipt output/native-verification.json
uv run fep-formal dashboard --check   # explanatory witnesses for the selected families
```

GNN side (commands of record per the GNN documentation):

```bash
uv run gnn validate <emitted>.md --strict
uv run python src/main.py --target-dir <bridge-input-dir> --output-dir output \
  --only-steps "3,5,10,11,12" --verbose
uv run python src/11_render.py --target-dir <bridge-input-dir> --output-dir output \
  --frameworks "pymdp,jax" --strict-framework-success
uv run python src/12_execute.py --target-dir <bridge-input-dir> --output-dir output \
  --render-output-dir output/11_render_output --frameworks "pymdp,jax" --timeout 600
```

The home of emitted documents is a spec-slice decision (candidates: a
directory under the opened `specs/` slice, or a GNN-side bridge input
directory); P1 fixes it.

## Phases

| Phase | Outcome | Acceptance | No-go |
| --- | --- | --- | --- |
| P1 — single-model spike | one finite model (the H1 terminal-carrier family: a finite one-step posterior–decision–action model on a Boolean carrier) projected to a GNN document | `gnn validate --strict` passes; step 11 renders on at least one categorical backend; step 12 executes and writes its summaries | if any document field needs a judgment call, stop and narrow the extraction contract |
| P2 — deterministic emitter | projection module (prospective location: a sibling package beside `src/fep_formal/formal/`) plus emitter, regenerable with a freshness gate in the style of `fep-formal atlas --check` | byte-identical regeneration; provenance populated; drift gate green | if regeneration needs manual edits, the emitter scope is wrong |
| P3 — certificate protocol | execution-derived quantities compared with Lean-witnessed properties | compared quantities listed with their evidence planes; first disagreement filed as a finding | if comparisons require reclassifying a plane, refuse and record the boundary |
| P4 — continuous spike | the OU/linear-Gaussian family projected onto the GNN continuous family, rendered and executed on a Gaussian-capable backend | continuous exemplar round-trips; categorical backends report `unsupported` and are excluded from execution | if continuous parameters cannot be projected mechanically, the family stays out of scope |

## Certificate content (initial proposal)

On a shared model instance:

1. **Directional agreement.** Executed-agent free-energy trajectories move
   in the direction of the Lean-proved decrease families
   (`ouKL_to_stationary_nonincrease`, `nativeKL_contraction`,
   `certifiedSemigroup_detailedBalanced` consequences) — agreement of
   direction and order of magnitude, never equality of samples.
2. **Action-selection agreement.** The executed policy's chosen actions match
   the Lean-defined `boltzmannPosterior` / policy-tree optima on the same
   carrier and parameterization.
3. **Statistic-level only.** Lean witnesses and Python/JAX samplers share no
   RNG stream; the protocol compares distributions and summary statistics,
   never trace identity.

## Open problems

- **Exact vs floating values.** Lean bodies carry exact rationals/reals; GNN
  numeric fields are decimal strings. The rounding policy and its provenance
  digest need a fixed rule before P2.
- **Ontology vocabulary.** GNN step 10 validates bindings against its
  canonical vocabulary; any Lean-specific binding outside it (beyond the
  exemplar terms like `A=LikelihoodMatrix`, `π=PolicyVector`) needs an
  explicit GNN-side vocabulary extension, not a silent misspelling.
- **Time semantics.** GNN `Time` (static/dynamic, discrete/continuous,
  horizon) versus Lean time indexing (`kernelPower`, `transition_add`,
  semigroup parameter) needs an explicit mapping table before continuous
  emission.
- **Families without counterparts.** Multi-agent, hierarchical, and
  learning-rate/dirichlet-pseudo-count GNN families have no catalog
  counterpart today and stay out of scope (contract section 3).
- **Artifact custody.** Emitted documents, render summaries, and execution
  summaries must be bound to their generating commit digest so a later
  certificate run can re-derive its own inputs.
