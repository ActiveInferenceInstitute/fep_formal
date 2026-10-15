# Support-aware variational methods and finite-path reductions

Status: locally accepted. Baseline: `50a4a9578e661ff61fbd729c5d546b30ecf209d5`
(verified Lean/Mathlib migration). Lean/Mathlib: `v4.35.0`; Mathlib revision
`56a005855ea17e0b0958f73ec801ae140b0a1679`.

## Outcome and scope

Strengthen existing finite variational/control and path-space foundations,
then expose robust reusable numerical methods for the same constructions.
The shared carrier remains `FEP.FiniteLaw` / `FEP.FiniteKernel`. All 168 topic
IDs, primary theorem statements and semantic dispositions stay stable.
This is a foundation expansion, not a new terminal H1/H2/H3 acceptance or a
scientific/empirical promotion. The existing Gibbs and path normalizations
are reused; no second probability carrier or editable claim registry is added.

## Work packages and dependency graph

| Package | Depends on | Existing owner | Outcome and exact target |
| --- | --- | --- | --- |
| G1 | migration baseline | `formal/controlled_markov.lean` | Boltzmann posterior zero/positive support equivalence and its logarithm on positive prior atoms, derived from existing normalization. |
| G2 | G1 | `formal/efe_policy_selection.lean` | For candidate supported by prior and every real precision, `γ * E_Q[cost] + KL(Q,prior) = KL(Q,controlPosterior) - log Z`; divided identities for nonzero precision, unique minimum for positive precision, unique maximum for negative precision. |
| P1 | migration baseline | `formal/path_thermodynamics.lean` | Actual coordinate and stage marginals of the existing normalized Markov path law; reduce full-path entropy-production sums to endpoint and stage laws; prove stationary biased-cycle `n * log(2)/4`. |
| P2 | P1 | `formal/path_thermodynamics.lean`, `formal/compositions/thermo_geometry.lean` | With full support and detailed balance, path production with reverse initial law equal to the evolved forward endpoint equals initial-minus-final KL to the stationary law; the one-step case consumes the existing fep-099 inequality. |
| N1 | migration baseline; mathematical contracts G1/G2 | `methods/probes.py`, `methods/__init__.py`, `cli.py` | Public `finite_expectation`, `log_partition`, `exponential_tilt`, `gibbs_duality_diagnostics`; installed-wheel and JSON CLI access with explicit support, normalization, representability and underflow diagnostics. |
| I1 | G2, P2, N1 | existing tests, generators, docs and CI workflow | Exact source/namespace closure, package projections, current evidence, documented APIs; repair the inherited setup-uv pin mismatch without changing scientific epochs. |

G1/G2 and P1/P2 have disjoint source ownership. Numerical work is independent.
Native compiler jobs share one lease and are serialized. Review is independent
of the implementation author. The integrating agent owns shared generation,
closure-count tests, receipts, documentation and commits.

## Stop/go probes and failure cases

| Package | Smallest go probe | Positive witness | Boundary result | No-go action |
| --- | --- | --- | --- | --- |
| G1/G2 | Compile the support equivalence and candidate-weighted logarithm gap using existing relative-support KL expansion. | Three-state prior `[1/2,1/2,0]`, potential `[0,log 3,7]`, posterior `[1/4,3/4,0]`; supported strict nonoptimizer gap. | Unsupported Boolean candidate beats the alleged minimum under totalized KL; zero precision fails the divided minimizer claim; negative precision reverses optimization. | If exact gap fails, remove G2 sign/optimizer claims and N1 theorem-alignment language; retain only proved support facts and a precise gap report. No conclusion is installed as a certificate field. |
| P1/P2 | Compile coordinate-marginal induction from `markovPathMass_snoc` and normalization before stronger identities. | Full-support three-state biased cycle at arbitrary horizon, with strict production for positive horizon. | Reversible identity requires reverse initialization at the evolved endpoint, not an arbitrary terminal or stationary law; real totalized logs do not represent infinite production at zero reverse support. | If marginal reduction cannot be established, P2 and its fep-099 derivational bridge stay explicitly blocked; do not rename the already-existing full-path split as new work. |
| N1 | Independent high-precision oracle on sparse and ordinary examples; extremes and subnormal probes. | Sparse Gibbs example, shift and permutation invariance, stable large-offset nonuniform tilt. | Distinguish true support mismatch from numerical tilt underflow; reject malformed/nonfinite inputs and unrepresentable finite outputs. | Remove any report field whose support/precision meaning cannot be established; preserve legacy KL conventions and expose the limitation rather than manufacture infinity or a proof flag. |

## Numerical API contract

The four helpers live in the existing numerical owner and remain offline.
Input laws are nonempty and normalized within the existing `1e-12` tolerance;
potentials are finite. The scalar methods use the supplied masses. Diagnostics
explicitly normalize accepted input laws and report original mass sums and
residuals. Existing totalized and extended KL functions keep their conventions.

Weighted expectations must retain subnormal products and severe cancellation.
Gibbs weights are centered on positive reference support before adding reference
log masses, with a second log-sum-exp center. Diagnostics use centered,
high-precision quantities, never KL against an underflow-truncated returned
optimizer. True support mismatch is an extended-domain boundary represented
with JSON-safe infinity strings. Zero-reference and floating underflow indices
are separate. Every report declares numerical, non-proof evidence.

## Acceptance

- New source tests pin exact signatures, sign/support premises, qualified owner
  names, the explicit new declaration roster and workspace byte parity.
- Native downstream probes compile positive examples and rejected stronger
  readings with zero warnings and only the existing allowed axioms.
- Existing full-support names and primary topic contracts continue to compile.
- Numerical tests use independent oracles, shift/permutation properties,
  `±1e308` offsets, opposite extremes, `5e-324` inputs, zero support, invalid
  shapes, malformed numbers and representability boundaries.
- Real isolated-wheel imports and CLI/API results agree. Public exports are
  exact; generated resources and mathematical-methods artifacts are current.
- Ruff, mypy, applicable source/semantic/projection/doc audits and Python tests
  pass. Fresh native build, declaration audit and 168-topic receipt bind to the
  final source. Publication acceptance is refreshed by a real render.
- Frozen scientific JSON and primary seeds remain untouched. Independent code
  and mathematical-scope review is recorded; no human scientific approval is
  invented. Hosted CI/publication claims require their own exact remote evidence.

## Decisions

- Reuse existing Boltzmann normalization; extend its support theorem surface.
- Keep new mathematical facts in existing foundation/composition owners, with
  no manifest or production Python source-owner growth.
- Keep the sealed catalogue stable. New generic facts are not new topics.
- Treat all-real precision separately from positive/negative divided objectives.
- Preserve the distinction between finite totalized KL and extended KL.
- Use exact accumulation for products of supplied binary floats where useful;
  use explicit high-precision centered arithmetic for logarithms and exponentials.
- Use a private 700-digit context for arbitrary-input Gibbs calculations.
  Independent review exposed lost near-one mass tails at 80 digits; five
  regressions now compare positive results with an independent 1,100-digit
  oracle. MDS and fixed publication grids retain their existing 80-digit context.
- Pin uv `0.13.0` in the standalone project as well as all ten workflow steps.
  The historical custody validator correctly refuses that metadata change.
  Its test separately exercises this refusal and the old source-drift guard
  using a disposable copy; historical records and validation are unchanged.
- Do not activate licensed-data, provider-spend or frozen primary-seed lanes.

## Current handoff

Baseline migration is committed and its old evidence is archived under ignored
`output/extension-baseline/`. G1/G2 add 19 public theorems; P1/P2 add 13.
Independent mathematical reviews found all 122 released theorem signatures
preserved across the four edited modules, correct support/sign/endpoint scope,
and no remaining formal findings. Numerical and shared-workflow review caught
the precision issue above; an independent recheck accepted its correction.
These are agent code/mathematical reviews, not human scientific approvals.

The integrated native build passed 9,120 jobs. The declaration audit resolved
1,875/1,875 theorems with no warnings or `sorryAx`; the methods statement census
is 2,225. New numerical contracts pass 46 tests, Gibbs contracts pass nine
including their native probe, and path contracts pass five including theirs.
All eight targeted native contracts pass, including the additional
detailed-balance zero-production consumer. The fresh 168-topic receipt is
independently valid, source-bound and native-claim-ready. The real publication
render passed at 385 pages with all nine acceptance counters zero; its receipt
and three focused publication tests pass.

The full nonserial Python selection recorded 2,914 passes, ten skips and five
integration-check failures at 91.53% coverage (89% floor). The failures were
historical rejection ordering, documentation-index membership, two declaration
inventories and a release-test mutation that matched `required-version` instead
of the project version. After correction all five affected modules pass 61
tests. A separate 59-test focused recheck passes, as do 167 spec contracts.
The real isolated-wheel test exercised all four new APIs and the CLI. These
are a full selection followed by focused corrections, not a second clean
full-suite session. The 301 production/config owner bytes remain identical to
the frozen native source throughout those corrections.

[The acceptance snapshot](acceptance-evidence.json) records exact source/config
digests, counts, review scope and digest-bound `local_gitignored_path` evidence.
It keeps native, Python, render and hosted qualification separate. FORM-S6's
mathematical closure was independently reviewed and its completed row removed
from the open backlog. Other scientific/capture/runner lanes retain their own
acceptance gates. Publication targets `ActiveInferenceInstitute/fep_formal`
`main`; the publishing handoff reports its independently checked remote commit.
A local snapshot does not assert hosted CI, a tagged release or an archive.
