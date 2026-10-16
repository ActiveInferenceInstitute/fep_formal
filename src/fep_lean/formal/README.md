# FEP_Formal maintained Lean kernel

This directory owns canonical reusable Lean resources. The typed
[`manifest.py`](manifest.py) selects their exact paths, Lean module names,
roles and declaration namespaces. The generated
[`lean/FepSketches/`](../../../lean/FepSketches/) tree is a projection of those
owners, not a second authoring location.

## Proof ownership

Foundations own reusable finite and measure-theoretic carriers and laws.
Composition leaves own cross-topic theorems using stable catalogue namespaces;
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
