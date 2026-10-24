# GNN bridge operations

This package owns source custody, deterministic emission, and numerical
comparison for the finite Boolean and scalar-OU GNN bridge examples.
The model interchange remains a GNN document; JSON receipts are evidence.

```text
explicit source pin → deterministic GNN document → renderer artifact
                                                → numerical comparison receipt
```

Use `uv run fep-lean bridge --help`. Every operation names `--gnn-root`.
`status`, `emit --check`, `verify-certificate`, and `certify` without
`--receipt` perform no writes. `pin`, `emit`, and `certify --receipt PATH`
are explicit mutations. `emit --refresh-digests` refuses content drift.

The source pin records commit references and the actual working-tree owner
hashes. It never claims that uncommitted bytes belong to the recorded commit.
Unrelated commits do not stale a document. Changed, added, or missing owners
do stale it. Pin changes do not reclassify old execution evidence.

A comparison receipt establishes agreement for an identified result artifact,
not that the current source produced it. `execution_source_verified` and
`native_claim_ready` remain false. Concrete renderer proofs have their own
artifact/proof receipt. Historical P3 comparisons remain historical.

The standard package test suite includes standalone fixture tests with no
sibling checkout. Live two-repository checks are explicit integration probes.

## Independent semantic audit

`audit-semantic` accepts a self-contained `gnn-semantic-witness-v2` receipt.
It independently reads the restricted authored E4 source and replays stationary
finite filtering with forward Bayes recursion, or passive linear-Gaussian
filtering with Kalman/Joseph updates. GNN uses complete path enumeration and
joint Gaussian conditioning respectively. Both sides check actual result
metadata, parameters, ordered inputs, axes, conditioning, float64 precision and
distribution validity; no probability or covariance is repaired to pass.

```bash
uv run fep-lean bridge audit-semantic --gnn-root /path/to/GNN \
  --results /path/to/semantic-witness.json --receipt /path/to/new-audit.json
```

Without `--receipt`, this operation is read-only. Output cannot alias the input
witness, including by symlink or hardlink. Source artifacts are limited to 1 MiB,
result/program artifacts to 16 MiB each, and the enclosing input receipt to
96 MiB. Missing, contradictory, malformed, oversized or nonfinite evidence
refuses explicitly. The audit replays every comparison and its fixed assumption
boundary; saved passing flags alone establish nothing.

`fep-semantic-witness-audit-v1` reports current source-owner hashes separately
from historical pair currency. It never re-pins sources or claims that supplied
result bytes came from a current execution. Qualified Lean declarations and
their exact source hashes retain their own assumptions. General matrix Gaussian
results are structural analogues of the scalar OU formal kernel, with unmatched
carrier and observation-time assumptions listed explicitly. The
[slice-local finite/scalar laws](../../../specs/gnn-semantic-witness-v1/README.md)
have a separate compiler/axiom receipt; neither numerical agreement nor those
bounded algebraic laws establish universal GNN translation equivalence.
