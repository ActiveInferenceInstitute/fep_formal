# Formal Lean resources

This package owns the manifested formal kernel. Foundation modules build
reusable finite and measure-theoretic carriers; `compositions/*.lean` contains
the cross-topic theorems that reference stable topic namespaces; and
`composed.lean` is their import-only aggregate. Every manifested
`lean/FepSketches/<resource>` counterpart is an exact generated
projection. Add a theorem only when it strengthens the module's typed contract,
compiles warning-free at the pinned toolchain, has explicit support or
regularity assumptions, and is named by corresponding novelty, capability, or
relation evidence when it closes a reviewed claim.

Do not copy topic bodies here, infer scientific relations from module imports,
add axioms or `sorry`, introduce a second probability carrier without a proved
bridge, or edit workspace projections by hand.

Preserve required public/meta imports and public declaration sections when
changing module headers. Review actual importing consumers and the manifest's
namespace/role contracts before changing a shared foundation or adding a leaf.
The [kernel guide](README.md) explains the ownership seam; the
[root required checks](../../../AGENTS.md#required-checks) own projection,
compilation and axiom-audit commands.
