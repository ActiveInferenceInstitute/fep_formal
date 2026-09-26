# Design programs

This directory owns prospective architecture and research programs. It is not a
second topic catalogue, capability graph, theorem-maturity ledger, or evidence
store. A design becomes current implementation work only when a bounded slice
is opened under `specs/` and linked back to its design goal. Once that slice
ships, its acceptance record moves under `specs/done/`; the design document
continues to describe the longer research dependency.

## Active programs

| Program | Purpose | Status |
| --- | --- | --- |
| [FEP research horizons](fep-research-program/README.md) | Move from the released finite catalogue to a falsifiable, carrier-spanning, end-to-end scientific theorem chain | Active: [Horizon 1 accepted](../../specs/done/horizon-1-finite-synthesis/README.md); [H2.7 accepted](../../specs/done/horizon-2-smooth-stochastic/readiness/terminal-acceptance.json); only read-only H3.G0 eligibility open |
| [GNN bridge](gnn-bridge/README.md) | Cross-repo articulation with the GNN pipeline: render and execute Lean-expressed generative models (Direction 1) and formalize GNN steps and methods in Lean (Direction 2) | Q1–Q4/P1–P4b implementation records retained; [W2 source custody](../../specs/gnn-bridge-w2-source-custody/REPORT.md) and [Q5 concrete artifact proof](../../specs/gnn-bridge-q5-artifact-proof/REPORT.md), [Q6 embedded Julia inputs](../../specs/gnn-bridge-q6-activeinference-artifact/REPORT.md), and [Q7 OU coefficient bounds](../../specs/gnn-bridge-q7-continuous-ou-proof/REPORT.md) verified |

## Lifecycle

```text
research question
  -> design goal in docs/design/
  -> stop/go spike
  -> bounded implementation spec in specs/
  -> canonical source and tests
  -> evidence at the relevant parser/compiler/browser boundary
  -> completed record in specs/done/
```

Design documents may name target declarations, modules, and acceptance probes,
but those names remain prospective until the corresponding active slice proves
and accepts them. They must not reserve future `fep-NNN` identifiers or add
planned objects to generated coverage. Current implementation status belongs
to the linked spec while active and to its archived acceptance record after
exit; catalogue and formalism ownership remain with the files listed in the
[topic reference](../topics-reference.md) and
[formalism authorship guide](../authorship-guide.md).

## Design rules

- Optimize for a dependency-complete theorem chain, not topic count.
- Give every fact one canonical owner and every check a separate enforcer.
- State a no-go action for every feasibility spike.
- Treat counterexamples and singular boundaries as first-class results.
- Keep compilation, semantic review, numerical illustration, browser
  acceptance, provider execution, and empirical evidence distinct.
- Preserve released identifiers and APIs. Add migration machinery only when a
  concrete accepted slice changes a released surface.
- Re-audit the newest matching stable Lean/Mathlib pair before opening a new
  horizon; do not substitute a release candidate or nightly.
