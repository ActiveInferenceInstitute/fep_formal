# OpenAI mathematics corpus: source review and integration decision

Initially reviewed on 2026-10-06 and extended on 2026-10-07 against
[`adc7f1241b42e322a6451854ab7e4b4c146bf78a`](https://github.com/openai/math/tree/adc7f1241b42e322a6451854ab7e4b4c146bf78a).
The local FEP source baseline was `195d4e9c340e588534603780a7afb1f470a9d501`.
The [reference lock](upstream.lock.json) records exact upstream paths, commit
URLs, byte counts, SHA-256 digests, and commit-tree Git blob identities.

## What the upstream provides

This is a research collection with a Lean Lake package inside it. The pinned
[README](https://github.com/openai/math/blob/adc7f1241b42e322a6451854ab7e4b4c146bf78a/README.md)
reports 722 manuscripts in 372 families; CONTENTS and the overview each have
372 family records. The collection explicitly contains results at different
verification stages. Model-generated reasoning summaries, informal papers,
formal scope descriptions, challenge specifications, and solution modules
are distinct artifacts.

The inspected
[formalization catalogue](https://github.com/openai/math/blob/adc7f1241b42e322a6451854ab7e4b4c146bf78a/lean/formalization.yaml)
has 162 cited source manuscripts, 185 selected main-result entries, and 30
related formalizations. Its scope says partial progress and its review status
is unchecked. These are counts of source metadata, not independently accepted
proofs. They are not comparable to FEP's topic count: a manuscript, family,
proxy, supporting lemma, and selected main result are different units.

The inspected toolchain and resolved Mathlib revision matched FEP's pins at
review time: `4.34.1` for Lean and Mathlib
`d13f23b723b8a846827a245b89c10fc7d3f11612`. The upstream resolved Lake
manifest nevertheless contains 42 packages, and its Lake configuration
contains dependency patching logic and hooks. Matching those two pins does
not establish compatibility of the full environments. The upstream Lean
README recommends compiling small portions. A recursive tree response was
truncated after 58,746 entries with more than 1 GB of reported blob bytes;
this is a lower bound, not a full size measurement.

The extended source review covers 82 pinned metadata, scope, challenge, manuscript,
and substantive TeX slices. Each downloaded slice was rehashed locally and
matched to its commit-tree Git blob identity. No upstream Lean solution was
built, no Comparator run was performed, and no manuscript proof was
independently adjudicated.

The follow-up independently rechecked all 82 retained files and the unchanged
public main commit. Twelve individually named result units now retain exact
statement-source paths and hashes in `positioning.yaml`, alongside their
carriers, assumptions, formalization-scope boundaries and transfer obstacles.
All are labelled `reviewed_source_statement_uncompiled`; the upstream global
review remains unchecked. The source table is generated into the installed
methods resource, and its maintenance check binds every passport to the lock.
The six additional units cover graph-switch mixing (131), exact oracle-query
complexity (139), multiple mixing (145), entropy-rate dimension (148), Markov
type and superreflexivity (327), and metric Markov cotype of real ℓ₁ (332).
The 332 paper dated October 5 and the six original families are compared in
Supplement A with explicit exclusions. Finite stationarity is not a mixing
rate; query complexity is not runtime; feature MDS is not Banach renormability;
and measure dimension one is not absolute continuity.

## Integration decision

Use a pinned reference corpus and an offline FEP analysis module. This slice
does not add a Git remote, submodule, Lake dependency, Python dependency, or
upstream build hook. It brings the upstream into the research context through
reviewed source identities and selected mathematical affinities.

[`upstream.py`](upstream.py) validates the lock offline. An optional
`--upstream-root` compares a separately acquired exact checkout's HEAD and
selected source bytes. The check executes only Git identity inspection; it
does not execute upstream code, obtain dependencies, attest unreviewed files,
or guarantee that a snapshot remains held after return. The default explicitly
reports that upstream bytes were not rechecked. Each reviewed file is limited
to 8 MiB and a comparison reads at most its expected size plus one byte.

The upstream Apache-2.0 license remains its own license. FEP's existing
licensing and attribution remain separate. This change retains metadata and
original analysis rather than vendoring upstream proof or manuscript bodies.
Any later source reuse must retain the applicable attribution and notices.

## Selected mathematical affinities

All links below are bound to the reviewed commit. They identify candidates
for comparison; they create no cross-repository formal relation.

| Upstream source | Local object to compare | First obligation |
| --- | --- | --- |
| [093: logarithmic Sobolev inequality](https://github.com/openai/math/blob/adc7f1241b42e322a6451854ab7e4b4c146bf78a/preprints/A-dimension-free-logarithmic-Sobolev-inequality-for-subgaussian-log-concave-measures-September-23-2026/README.md) | Gaussian/OU entropy relaxation | Identify actual entropy, gradient, log-concavity and uniform-constant hypotheses; the inspected family has no linked Lean scope record |
| [140: Gaussian inference](https://github.com/openai/math/blob/adc7f1241b42e322a6451854ab7e4b4c146bf78a/lean/docs/140.md) | Gaussian posterior, observation kernels, hidden-mode identifiability | Match noisy versus noiseless experiments, sphere versus Gaussian priors, finite memory, dimension, and stopping/output restrictions |
| [221: diluted spin glasses](https://github.com/openai/math/blob/adc7f1241b42e322a6451854ab7e4b4c146bf78a/lean/docs/221.md) | Gibbs/variational duality, collective inference | Distinguish finite product laws from random-disorder thermodynamic limits and hierarchical trial-law spaces |
| [222: perceptron free energy](https://github.com/openai/math/blob/adc7f1241b42e322a6451854ab7e4b4c146bf78a/lean/docs/222.md) | Log partition, variational values, control | Distinguish supporting finiteness for Ising from limiting-pressure claims for spherical models; retain bounded continuous potentials |
| [360: weak MTW transport](https://github.com/openai/math/blob/adc7f1241b42e322a6451854ab7e4b4c146bf78a/lean/docs/360.md) | Statistical geometry and sensitivity | Supply cost geometry, injectivity domain, densities and MTW assumptions; Fisher geometry alone supplies none of these |
| [374: Brenier stability](https://github.com/openai/math/blob/adc7f1241b42e322a6451854ab7e4b4c146bf78a/lean/docs/374.md) | Native law perturbation and observation projection | Match compact support, convexity, map norms, Wasserstein metric and constants; unrestricted Gaussian support fails the compact-carrier match |

## Methods carried into FEP Formal

The supplement and module adopt carrier-first statement exposition, explicit
primitive assumptions, theorem-level scope, a proof-family map, separate
well-definedness and asymptotic claims, and paired positive/obstruction
examples. The complete FEP join preserves semantic review fields and
qualified declarations. Mathematical domain tags are authored family context,
while relations retain the existing canonical edge kinds and witnesses.

The [supplement](../../manuscript/08b_mathematical_positioning_supplement.md)
works through simplex interiors and support faces, attained rate-distortion
optimization, finite/native KL boundaries, Fisher rank and null directions,
faithful probability embedding, Gaussian process projection, statistical
identification, and missing constitutive heat information. It explicitly
marks the general score-rank argument as a proposed derivation rather than a
new Lean theorem.

The upstream Comparator pattern is also useful: name exact challenge and
solution modules, theorem names, and permitted axioms. Sample inspected
configurations permit `propext`, `Quot.sound`, and `Classical.choice`, and set
`enable_nanoda` to false. Challenge specifications intentionally contain
`sorry`; the solution closure and trusted definitions require their own
checking. The
[official Comparator contract](https://github.com/leanprover/comparator)
requires additional semantic review for definition-hole solutions. None of
those upstream checking outcomes is claimed here.

## Review and remaining acceptance

Two independent native Codex reviewers inspected upstream facts and the
mathematical supplement. Their corrections were applied: rate-distortion
feasibility is a closed constrained subset, log-score rank needs support,
one-time marginals differ from joint paths, weighted-Dirac transfer is a
separate embedding, and family context is not a per-topic domain theorem.

An independent static review of the reference adapter identified inherited
Git repository selectors and unbounded reads of drifted files. Both were
repaired with a copied subprocess environment and bounded file reads. Tests
use real Git processes, inherited selectors pointing at a second checkout,
file mutation, symlinks, and an oversized sparse replacement. No parent Git
environment is modified. Fresh follow-up review independently passed all ten
adapter tests and rechecked all 42 retained upstream source identities. It
found no remaining defect within the stated bounded static scope. The
analysis artifacts themselves remain non-proof evidence.

Later native integration requires one exact named theorem slice, a reviewed
statement/definition adapter, isolated dependency/patch evaluation, clean
native and axiom acceptance, and a fresh semantic review. Publication and
governed H3 empirical/runner lanes retain their existing gates. This review
does not activate those lanes or change their evidence.

The observations below describe the initial source slice. The subsequent
[1.6.0 continuation validation](VALIDATION.md) records the portable package,
expanded supplement, visualizations and their current acceptance separately.

Local verification on Python 3.14.4 passed 40 slice tests: 30 methods tests and
10 reference-adapter tests. A fresh independent follow-up repeated all 30
methods tests and the exact projection check after repairing numerical
overflow and step-size wording. Reloading JSON regenerates identical JSON,
Markdown, and SVG bytes. The inspected SVG is readable and includes
accessible descriptions and every family/domain label.

The relevant manuscript regression run passed 122 checks, with its one
chapter-order expectation then updated for the new supplement and separately
re-passed. Canonical catalogue/formal/maturity/coverage projections, strict
documentation links/hygiene, theorem references, bibliography, cross-references,
font requirements, dependency compatibility, and focused Ruff checks passed.
Catalogue mode generated all topic artifacts with zero verified topics. The
intentionally dry manuscript render produced 31 files and passed its freshness
check. Strict publication rendering remained unavailable because the native
receipt was absent or not claim-ready; no PDF/publication or new native
acceptance is asserted.
