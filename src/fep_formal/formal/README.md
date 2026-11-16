# FEP_Formal maintained Lean kernel

This directory owns canonical reusable Lean resources. The typed
[`manifest.py`](manifest.py) selects their exact paths, Lean module names,
roles and declaration namespaces. The generated
[`lean/FepSketches/`](../../../lean/FepSketches/) tree is a projection of those
owners, not a second authoring location.

## Proof ownership

Foundations own reusable finite and measure-theoretic carriers and laws.
Composition leaves own cross-topic theorems using stable catalog namespaces;
`composed.lean` is their import-only aggregate. Topic-local bodies remain in
[`catalogue/bodies/`](../catalogue/bodies/).

A Lean import records an implementation dependency. Authored scientific
relations and novelty bridges have their separate maintained YAML owners in
[`config/`](../../../config/README.md). A newly compiled module does not create
an edge or promote a semantic disposition.

The generated [coverage](../../../docs/formalism-coverage.md) and
[landscape](../../../docs/lean-landscape.md) describe the kernel's declared
surface. Exact statements and their support, positivity, independence,
regularity or invertibility premises remain in the qualified declarations.
The [support-aware variational guide](../../../docs/support-aware-variational-methods.md)
explains the reusable Gibbs/support extension and its claim boundaries.

## Endpoint tilts and supported path laws

`FEP.TemporalInference.terminalTiltKernel` reuses the finite smoothing law at
each transition row, with an explicit fallback on zero-normalizer rows.
`terminalTiltJoint_eq_smoothing` proves equality to joint endpoint smoothing
after tilting the initial law by its backward message. Null backward rows have
zero tilted source mass, so `terminalTiltJoint_fallback_invariant` applies to
arbitrary fallback laws.

The heterogeneous two-step construction retains the intermediate state in
`State × Middle × Terminal`. `terminalTiltTwoStepPath_eq_smoothing` factors
endpoint smoothing into the tilted initial law and two time-inhomogeneous
kernels. `terminalTiltTwoStepPath_fallback_invariant` proves equality of the
entire path law for arbitrary middle and terminal fallbacks, including reachable
null intermediate rows. Positive initial endpoint evidence is required;
`terminalTiltKernel_comp_of_pos` separately requires a positive backward source
row. The Boolean witnesses exhibit a positive surviving path and a reachable
null path with distinct fallback laws. These results cover two heterogeneous
steps; arbitrary finite-horizon recursion is not asserted.

## Event-weighted coarse-graining

`FEP.FiniteMarkovDynamics.weightedBlockMass` is the unnormalized weighted
predictive mass pushed into a target block.
`weightedBlockMass_forall_laws_iff_rowwise` characterizes exact reduction across
all preparations by rowwise equality, using point masses for necessity and
finite-sum linearity for sufficiency. Fibre-constant weights and lumpable
movement preserve total event evidence and positive-evidence conditional
readouts. `bool_conditional_equal_evidence_differs` exhibits hidden substates
with survival weights 4/5 and 2/5 and identical conditional coarse readouts;
conditional agreement alone does not certify event evidence.

## Changing a resource

Edit the canonical resource and its manifest owner where needed. Preserve
module-system imports and public declaration visibility, regenerate through
`_maint_build_formal_modules.py`, then inspect the exact workspace diff.
Changing shared foundations also requires their actual importing consumers,
including resources outside the topic aggregate, to be checked.

Projection freshness, aggregate/orphan compilation, exact-roster native
verification and declaration/axiom auditing answer different questions. The
[required-check inventory](../../../AGENTS.md#required-checks) owns their
commands. The audit selects the primary/evidence closure and maintained formal
theorems; private helpers remain proof dependencies of the declarations that
use them. Source-text coverage totals alone are not native audit evidence.

Follow the [local contract](AGENTS.md) and the
[source-owner evidence policy](../../../AGENTS.md#source-of-truth). Preserve
historical receipts at their original source epoch when a resource changes.
