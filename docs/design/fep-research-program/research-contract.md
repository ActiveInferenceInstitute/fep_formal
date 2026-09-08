# Research and evidence contract

This file owns the rules shared by all three horizons. Individual horizon files
own their mathematical work packages; they must link here instead of restating
these rules.

## One owner per fact

| Fact | Canonical owner | Enforcer or projection |
| --- | --- | --- |
| Current ordered topic roster and family metadata | [`config/catalogue_metadata.yaml`](../../../config/catalogue_metadata.yaml) | Catalogue schema and registry tests |
| Current primary theorem, assumptions, non-vacuity, and disposition | [`config/theorem_maturity.yaml`](../../../config/theorem_maturity.yaml) | Theorem-maturity audit |
| Current novelty and cross-topic relation/capability state | [`config/formalism_novelty.yaml`](../../../config/formalism_novelty.yaml) and [`config/formalism_relations.yaml`](../../../config/formalism_relations.yaml) | Coverage and relation validators |
| Current reusable formal module roster | [`formal/manifest.py`](../../../src/fep_lean/formal/manifest.py) | Formal projection and declaration audits |
| Prospective H1--H3 goals | This directory | Documentation checks and active/future specs |
| Active implementation status | A bounded directory under `specs/`; accepted history moves to `specs/done/` | Its tests and acceptance record |
| Lean/Mathlib pin and supported-version policy | [`lean/lean-toolchain`](../../../lean/lean-toolchain), [`lean/lake-manifest.json`](../../../lean/lake-manifest.json), and [`docs/lean4.md`](../../guides/lean4.md) | Pin audit, including `--check-latest` |
| Empirical protocol after preregistration | The frozen H3 protocol artifact selected by H3.0 | Dataset, analysis, and report validators |

No horizon may create another topic roster, theorem-maturity table, relation
graph, or numerical-witness registry. A planned capability remains in these
design documents until work starts. At activation it either extends the
existing relation/capability schema or stays in the active spec; a new YAML
claim registry is a no-go unless a schema spike proves the existing owners
cannot express the required state.

## Work-package contract

Every H1--H3 work package must have all of these fields before implementation:

| Field | Required content |
| --- | --- |
| Outcome | One proposition or artifact that becomes true |
| Depends on | Work-package identifiers, not prose such as "the earlier work" |
| Single owner | Existing module/config, or one explicitly justified new module |
| Stop/go spike | The smallest compiling or data-feasibility probe |
| Go condition | Observable success that opens implementation |
| No-go action | Delete, defer, upstream, or narrow; never "try harder" |
| Theorem/API target | Exact carrier, codomain, assumptions, and intended declaration shape |
| Positive witness | A nontrivial inhabited example |
| Boundary result | Countermodel, singular case, or failed premise |
| Test surface | Named tests and projection checks |
| Evidence plane | Formal, native, numerical, empirical, browser, provider, or publication |
| Human review | The scientific or architectural decision a person must sign |
| Out of scope | The nearest stronger claim that must remain impossible |

The active spec must instantiate these fields as a machine-checkable or
reviewable package matrix before source implementation. In particular, a
no-go action names the exact terminal-theorem clause and dependency-map edge it
removes, blocks, or weakens. “Continue with the remaining work” is not a no-go
action. A terminal merge may open only when every solid incoming package is
green or a human-approved revision has changed both the theorem and the DAG.

For every new Lean resource, “single owner” expands to six concrete facts:

1. packaged resource path;
2. `FormalModuleRole`;
3. workspace Lean module path;
4. declaration namespace;
5. exact imports and aggregate behavior; and
6. the manifest-roster and namespace tests that fail if any fact drifts.

H1.0 added and validated the fourth fact. Every current foundation and
composition has an explicit declaration namespace, the aggregate is
declaration-free, and new leaves fail closed on duplicate, missing, or
source-mismatched outer owners.

## Evidence planes

Evidence never promotes itself across rows in this table.

| Plane | Establishes | Does not establish |
| --- | --- | --- |
| Semantic review | The theorem statement matches its narrowed claim | That Lean accepted the current bytes |
| Native Lean | The pinned compiler accepted exact source with the recorded warnings and axioms | Scientific relevance or empirical truth |
| Declaration/axiom audit | Required declarations resolve and exclude `sorryAx` or unapproved project axioms | The intended interpretation of those declarations |
| Numerical witness | A deterministic example has the stated finite behavior | A proof, convergence guarantee, or empirical validation |
| Browser/publication | The accepted source projection is legible and source-bound | Mathematical or scientific correctness |
| Provider/full mode | The optional external pipeline completed with validated provenance | Proof quality or model benchmark superiority |
| Synthetic experiment | Implementation recovery, calibration, or negative controls on generated data | Generalization to observed systems |
| Empirical study | The preregistered analysis result on the named data | Universal validity, causality without identification, or biological mechanism |

## Countermodel contract

A countermodel theorem is accepted only when it proves:

1. every premise of the rejected implication on one explicit carrier;
2. the negation or strict failure of the proposed conclusion;
3. non-degeneracy of the witness; and
4. the smallest added hypothesis under which a positive theorem is recovered,
   when such a theorem is claimed.

Comments saying an implication can fail are not countermodels. A structure
field containing the desired conclusion is not a derivation.

## Toolchain and upstream policy

Before opening H1, H2, or H3:

1. run the local pin audit and its networked latest-stable check;
2. record the exact Lean tag, Mathlib tag, and resolved Mathlib revision in the
   active spec;
3. compile minimal probes for every unfamiliar Mathlib declaration;
4. search the pinned source before declaring an API absent; and
5. separate project proof work from a reusable upstream Mathlib prerequisite.

Release candidates, nightlies, floating branches, and mismatched stable tags
do not satisfy this policy. A new stable pair triggers a migration slice and
fresh evidence; it does not silently alter an active proof branch.

## Compatibility policy

Released topic identifiers, public Python imports, receipt schemas, and Lean
qualified names remain stable by default. A horizon may refactor internal
ownership only after a call-site inventory and migration spec. Compatibility
aliases are not automatic: an alias that recreates a flat or duplicate owner
is rejected. Future IDs are never preallocated.

## Scientific firewalls

The program must keep these distinctions mechanically visible:

- finite totalized real KL versus native extended KL;
- rowwise blanket factorization versus stationary-law conditional independence;
- observational conditional independence versus causal identification;
- normative active-inference design versus spontaneous inference in physical
  dynamics;
- variational, expected, Helmholtz, and thermodynamic free energies;
- path-law KL versus measured heat or entropy production;
- finite-horizon policy-tree optimality versus infinite-horizon control;
- posterior convergence versus parameter identifiability;
- synthetic recovery versus empirical calibration;
- model fit versus neural, biological, or causal mechanism;
- theorem compilation versus a universal Free Energy Principle.

Any proposed theorem or manuscript sentence that erases one of these
distinctions fails review even if it compiles.

## Human review quorum

Every terminal horizon theorem requires three independent approvals:

1. a Lean reviewer checks the carrier, proof dependencies, warnings, and axioms;
2. a domain reviewer checks the source equation, assumptions, and interpretation;
3. a skeptical reviewer checks countermodels, stronger readings, and negative
   evidence.

H3 empirical promotion additionally requires a statistical reviewer and a
data/domain owner. The same person may not supply all approvals.
