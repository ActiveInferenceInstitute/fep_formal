# Current finite-kernel category component

This fresh 2026-10-18 component run at source commit
`65215813fe92e94a960fb28cba113d0edb3c7580` retains the actual public consumer,
all ten raw axiom reports, their hashes and independent domain/custody review.
The consumer compiles without warnings, and every report names only `propext`,
`Classical.choice` and `Quot.sound`. The standard predictive-law functor preserves
normalization and composition; the Boolean witnesses establish identity,
propagation through a flip and involution. No causal or empirical claim follows.

From the repository's `lean/` directory, reproduce the retained consumer with:

```sh
lake --keep-toolchain env lean -DwarningAsError=true \
  ../specs/comprehensive-next-steps/spikes/category-native-20261018/FepFiniteKernelCategoryConsumer.lean
```

[qualification.json](qualification.json) binds the current authored/projected
leaf, test consumer owner and compiler/dependency files.
[axioms.log](axioms.log) retains the complete output.
[independent-review.json](independent-review.json) records review conclusions
and the remaining C05 predecessor. PR44's exact head and contributor attribution
remain in the earlier integration brief. Those earlier prospective records and
source epochs are preserved. This component does not close Issue58/R01, C05,
a horizon theorem, production capture or any scientific acceptance gate.
