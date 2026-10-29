# Q7: fixed scalar OU artifact and coefficient-error certificate

This slice connects a canonical GNN JAX render of the P4b scalar OU document
to exact real one-step coefficients and bounds the error of its six embedded
binary64 parameters. The independently reviewed
[2026-10-05 source-pair capture](../comprehensive-science-improvement/evidence/public-q7-current-source-20261005-r1/summary.json)
passed all twelve stages and four closing checks on 2026-10-05. Its separate
native receipt binds the 291-input roster of that epoch and covers static coefficient
statements; generated-runner execution remains unverified.

The [proof report](REPORT.md) distinguishes this capture from the retained
2026-10-02 observations and the original [native JSON](native_receipt.json).
Historical receipts and failed attempts remain unchanged, with no promotion
of failed prefixes. Active GNN work is preserved. Package, hosted and H3
acceptance remain separately tracked in
[remaining acceptance](../comprehensive-science-improvement/NEXT.md).

The exact source model is `FEPComposed.SmoothReferenceKernel.selectedDynamics`
(rate 1, center 0, diffusion variance rate 2), its unit-duration `selectedFilter`,
and its centered unit-variance `selectedPrior`. The independent expected contract
requires `a = Real.exp (-1)`, `q = 1 - a^2`, identity observation, unit observation
variance, and passive control. This is not Q3 prior-gauge denotation: F and Q are
consumed here. P4b's declared `[1,1]` prior mean and emitted length-one vector are
explicitly frozen representations, not a claim of Q3 `ContinuousConforms`.

The artifact extractor reads literal assignments without importing or executing
the runner. Decimal source text is retained as an exact decimal rational, while
the parsed finite Python binary64 value is separately retained as an exact
dyadic rational. These values are not equated. No claim of correctly rounded
`Real.exp` evaluation is made: P4b currently uses powers of a rounded constant.

The Lean probe uses the pinned `Real.exp_one_near_20` bound to prove independently
that the actual dyadic F and Q are within `10^-15` of their exact OU formulas.
It then bounds one-step mean error by `epsilon * abs mean`, variance error by
`(2 * variance + 1) * epsilon`, and the stationary variance defect by
`3 * epsilon`. A nonstationary witness has mean 1 and variance 2, so replacing
prediction by the prior cannot pass the same narrow approximation bound. A
scalar Joseph-update identity connects the exact real arithmetic formulas.

The bounds concern real arithmetic over decoded coefficients. They do not bound
JAX arithmetic, solve operations, sampling, or accumulated trajectory error.
This slice proves no compiler/extractor correctness, generic LGSSM equivalence,
continuous path, SDE solution, control theorem, or physical applicability.

`refresh_render.py --fep-root ... --gnn-root ...` retains a canonical render under
this slice with before/after owner digests and exact input bytes. It invokes
`extract_pomdp_from_file(strict_validation=True)` followed by
`POMDPRenderProcessor._pomdp_to_gnn_spec` and public `render_gnn_spec(..., 'jax', ...)`.
An initial discovery run found that the generic dispatcher rejected this model
at a categorical A/B/C/D requirement; the parent repaired the dispatcher and
the final retained fixture is refreshed through that generic public route.
It never executes the emitted runner. `generate_probe.py --output-root PATH`
creates a fresh probe and manifest; `--check --output-root PATH` compares bytes
without writing. `--source-root PATH` selects the current source and parity input
profile; it defaults to this checkout. Generation refuses existing output paths.
The retained pre-cutover parity bindings were stale against the canonical
cutover source and were correctly refused. The October 28 hosted checkpoint
below explicitly refreshes the mutable working projections. Historical source-pair and native
receipts remain historical; no identity translation grants current acceptance. The parent
receipt engine owns source/toolchain/native custody and must check the manifest's
complete `receipt_contract` before accepting evidence. A generated manifest is
explicitly not native evidence.

The retained P4b `NUM_TIMESTEPS=1` observes the prior and never exercises F or Q:
`kalman_step(..., first=True)` skips prediction, and transitions run only for
`range(1, T)`. Separate numerical evidence must invoke `first=False` on a
nonstationary belief or use at least two samples. The GNN three-step nonstationary regression exercises that runtime route.
It remains execution evidence, distinct from the static coefficient proof.

## 2026-10-20 source-pair refresh

The [fresh native receipt](native_receipt_20261020_c06.json) binds GNN source
`c06d867efa914a52c76d584cacf2fff8ad5d01ea` and its recorded FEP source-owner set.
The owning render refresher renewed the emitted input, source-pin and owner
provenance, and the probe generator renewed the artifact manifest. The canonical
JAX runner, reviewed scaffold, Lean probe and all four historical
`native_receipt.json` files retain their earlier bytes.

A fresh compile and independent retained check passed on the recorded Lean
4.35.0 toolchain, including all twelve axiom reports with no compiler warnings
or admissions. Its scope is the static coefficient and real-arithmetic bounds
above; `runtime_execution_verified` remains false. It supplies no generated
runner, SDE or physical-model execution claim. Later source changes require
another fresh capture rather than editing this receipt's hashes.

The GNN paired workflow also checks current-Q7 source/provenance and generated
scaffold freshness on CPython 3.14. That read-only gate supplies no new native
proof evidence; the native receipt remains a distinct acceptance surface.

## 2026-10-20 Pillow 13 source epoch

The [new native receipt](native_receipt_20261020_e928.json) binds GNN
`e92883b22feb7a28f0b386e8aa2bc3d87236e459`, whose lock upgrades Pillow to 13.
The source pin and both emitted signatures were regenerated through the bridge
CLI, then the owning render refresher and probe generator renewed current
provenance. The actual JAX runner and Lean probe retain their earlier bytes.
The four original receipts and the earlier C06 receipt remain byte-identical
historical observations of their own source pairs.

A fresh native compile and retained check pass with all twelve standard-axiom
reports, no compiler warnings or admissions. The scope remains static binary64
coefficient approximation and real-arithmetic prediction bounds;
`runtime_execution_verified` is false. This capture does not renew generated
runner, SDE or physical execution evidence. Later source changes still require
fresh capture; the current-Q7 paired gate only checks read-only source freshness.

## Interpreter contract for the frozen scaffold

The [schema-1 serialization protocol](scaffold-serialization.md) retains all
reviewed AST fields, types and order, with only absent/empty
`FunctionDef.type_params` normalized. Ordinary comments and locations are
excluded; type comments are retained. Unknown grammar, fields and nonempty
type parameters fail closed. The schema-2 expected contract explicitly binds
this serialization and the independently reviewed new scaffold digest.

The [dated 2026-10-02 capture](../comprehensive-science-improvement/evidence/public-q7-final-source-20261002-r1/summary.json)
recorded 56,968 identical candidate bytes on real CPython 3.10.20, 3.11.15,
3.12.13, 3.13.16 and 3.14.4, with all 11 semantic/schema controls per runtime,
at SHA-256
`b34a350a0c66bd611c19cd87e2343592c6ee7d15ed2fd6e422b1f891597febec`.
The earlier 62,013-byte `f8dfe844…` observation is historical for the fixture
before its NumPyro-only branch was removed from the canonical JAX output.

The working [parity projection](generated/scaffold-runtime-parity.json) and
[canonical bytes](generated/scaffold-canonical.json) are mutable projections.
Their earlier bytes are bound by the 2026-10-05 source-pair capture. The current
2026-10-19 renderer adds quotes around the same model title in the module
docstring. Independent review confirms that all executable AST fields and six
parameter tables are identical. The exact new scaffold digest is
`0cf5e8b1afbfa7b82cd3c3cbaa5c22ba0931738030ed83195b944936a3a8b4ce`;
all five real CPython runtimes serialize the same 56,972 bytes. The complete
Lean probe and historical native receipts are unchanged. This parser refresh
supplies no new native or generated-runner execution evidence. A later source
change still requires fresh acceptance. Observe a current static parity projection
in a fresh directory with installed runtimes, without network access:

```bash
uv run --locked python specs/gnn-bridge-q7-continuous-ou-proof/generate_probe.py \
  --record-scaffold-portability --output-root output/q7-current-parser-observations
```

The observation directory is separate from retained records. To generate a fresh
probe, explicitly prepare a separate source profile containing its own matching
parity projection, then pass that profile as `--source-root` and a new
`--output-root`. Unit tests use clearly labeled synthetic profiles solely to test
schema acceptance and rejection; they supply no observed runtime evidence.

Candidate serialization parity is static syntax evidence. Actual
`scaffold_digest`, extraction and receipt validation still accept exactly
**CPython 3.14** and refuse unsupported interpreters before parsing. The
installed-wheel matrix checks both candidate parity and that refusal. Q5/Q6
whole-file custody has its own evidence boundaries. Their native and delivery
observations remain historical after the W2 source re-pin; this Q7 capture does
not refresh them. The previous Q7 native receipt is retained as history;
updating hashes cannot replace a new native capture.

Acceptance requires focused extraction/custody-negative tests, current render
provenance, exact probe regeneration, native compilation with no warnings or
`sorryAx`, and axiom reports containing only the established standard axioms.
The implementation is integrated; changes require fresh source-bound evidence.

## Earlier isolated native evidence and reproduction

This historical checkpoint retains its exact earlier source pair. The
[fresh full capture](../comprehensive-science-improvement/evidence/public-q7-final-source-20261002-r1/summary.json)
supersedes it for the newly checked native inputs; the prose update preserves
the capture-time preimage and does not change native input bytes.

The [public Q7 observation](../comprehensive-science-improvement/evidence/public-q7-closure-20261002-r1/summary.json)
records earlier recapture r3 accepted across 12 stages in 644.5096 seconds: seven actual
accepted substages of failed r2 were freshly revalidated, and stages 8–12
actually ran in r3. All 124 pure
controls pass without skips. The isolated GNN pair owns its Git checkout and
private copied runtime at exact commit
`536d949829f6aed11dc540e5c5dec77578b25016`; all 703 owners are bound, with
191 FEP and 291 native owners guarded. The active GNN checkout/output remain
outside this isolated work.

The exact [new native receipt copy](../comprehensive-science-improvement/evidence/q7-accepted-native-retention-20261002-r1/native-receipt.json)
has SHA-256 `b0ecf640fffa06f019d67c74a2d02e22715120165a98d218d61f49f98366bc3b`.
It records `native_claim_ready: true`, `runtime_execution_verified: false`,
the warning-free positive probe and all 12 standard-axiom results.
The public observation also records postcapture closure r2 accepted across
seven actual stages in 1,648.1618 seconds, including the real positive
axiom census and both wrong-F/wrong-Q native controls. Its outer process exits
0 with accepted transport. The dated [post-guidance observation](../comprehensive-science-improvement/evidence/public-q7-current-doc-20261002-r1/summary.json)
records independent review and three passing read-only checks with stable source
custody; that acceptance closes the portability backlog probe.
Full operator-custody records remain local. The public summary is observational;
only the separately validated official native receipt supplies the native claim.

For a new coordinated capture, refresh the exact selected owners first. Use a
fresh candidate path and the same explicitly named GNN root for both commands;
never overwrite the historical `native_receipt.json`:

```bash
GNN_ROOT=/absolute/path/to/GeneralizedNotationNotation
uv run python specs/gnn-bridge-q7-continuous-ou-proof/verify_native.py \
  --compile --gnn-root "$GNN_ROOT" --receipt output/bridge/q7-native-candidate.json
uv run python specs/gnn-bridge-q7-continuous-ou-proof/verify_native.py \
  --check --gnn-root "$GNN_ROOT" --receipt output/bridge/q7-native-candidate.json
```

## 2026-10-21 GNN 4.2 source epoch

The [fresh native receipt](native_receipt_20261021_gnn420.json) binds GNN
`0b0028aaa2cc3c40bddf47ac934a1f7e6b8644fe`, including package 4.2.0 and its
current compatible dependency lock. Bridge pin/emissions, canonical render and
probe provenance were regenerated with their owning tools. A fresh native
compile and retained check pass all twelve standard-axiom reports without
warnings or admissions. The canonical runner, probe and every historical receipt
retain their prior bytes. Scope remains static binary64 coefficient and
real-arithmetic bounds; generated-runner execution remains unverified.

## 2026-10-21 repaired GNN 4.2 entrypoint epoch

The [new capture](native_receipt_20261021_gnn420_startup.json) binds GNN
`fb67431ee073fa27c0ce0c9e9336c7ff50e5737b` after its direct/supervised Python
entrypoint repair and fresh manuscript render. The earlier 4.2 capture above
retains its original source identity. Bridge signatures, Q7 render provenance
and probe metadata were regenerated again through their owners; a new native
compile and independent retained check pass all twelve axiom reports without
warnings/admissions. The runner, Lean probe and historical receipts are unchanged.
Scope remains static coefficients and real-arithmetic bounds, without emitted
runner execution or a general Python import-safety theorem.

## 2026-10-21 final typed GNN 4.2 source epoch

The [final source-pair capture](native_receipt_20261021_gnn420_typed.json) binds
GNN `097328f40299de1469df1e4a5c027d535e3c7132`. Its direct-script guard reads the
actual optional runtime package state while satisfying static type checks.
The scientific runner, counts, manuscript inputs and Lean probe are unchanged;
strict manuscript/token/hydration checks still pass. Owner hashes nevertheless
changed, so bridge emissions, Q7 render provenance and the native capture were
freshly regenerated again. All twelve standard-axiom reports pass without
warnings/admissions. Earlier receipts retain their own identities. This remains
static coefficient/real-arithmetic evidence and supplies no generated-runner
execution or general import-safety proof.

## 2026-10-23 GNN 5.0 metadata and source epoch

The [new source-pair observation](review_20261023_gnn500.json) records the
FEP_Formal 2.0 authored source and GNN
`15b4bbe2cab77753981673f69bcbde0d2bc99203`. Canonical bridge pinning, both
emissions, render provenance, generated scaffold and probe freshness were
renewed through their owners. Historical receipts retain their original bytes.

The GNN runner adds fourteen result metadata fields and a `hashlib` import.
Independent AST review found the six parameter tables and all existing
filtering, Joseph-update, control, sampling and timing expressions unchanged.
The new fields report schema, parameters, axes, conditioning, precision,
interpreter/library versions and the script digest. Reading that digest can
refuse an unreadable script and contributes to execution overhead; this review
makes no speed claim. The old scaffold correctly refused the new runner before
reviewed admission. The new canonical scaffold digest is
`0a7efe879324b4234283615fe2caf92c473060a2c6c8228e32c1a3c6b41fdf25`.
No serializer rule, numerical tolerance or scientific assumption was relaxed.

All five real Python parser/serializer observations agree; the validator still
requires CPython 3.14. There were 413 passing extraction/custody controls and
three passing native positive/wrong-F/wrong-Q controls. A new typed native
receipt passed compilation and independent retained validation on Lean 4.35.0
with the pinned Mathlib revision. Its exact hash is retained in the public
observation; the typed receipt stays in the operator evidence set. The public
observation does not replace that validator. The Lean probe is byte-identical.

This evidence remains static binary64 coefficient and real-arithmetic bounds.
`runtime_execution_verified` is false. Separate GNN numerical filtering tests
do not turn this certificate into generated-runner, SDE, multidimensional
filtering or universal translation equivalence evidence.

### Publishing current working projections

After preserving the old projections and recording five fresh real interpreter
observations into a new output directory, explicitly adopt that directory:

```bash
uv run python specs/gnn-bridge-q7-continuous-ou-proof/generate_probe.py \
  --publish-scaffold-from output/q7-current-parser-observations
uv run python specs/gnn-bridge-q7-continuous-ou-proof/generate_probe.py \
  --output-root output/q7-current-generated
uv run python specs/gnn-bridge-q7-continuous-ou-proof/generate_probe.py \
  --publish-generated-from output/q7-current-generated
```

Publication rejects incomplete, extra, aliased, symlinked, tampered or stale
inputs before replacing the working projections. Scaffold adoption checks the
current owner hashes, canonical bytes and all five runtime records; it validates
stored observations and does not establish that new runtimes were executed.
Probe adoption requires exact regeneration against current source and parity.
Generation still requires a fresh output directory, and `--check` remains
read-only and refuses stale projections. Neither operation updates historical
receipts or supplies native evidence.

The publisher stages all four working files and retains the previous directory
as `.generated-before-<unique-id>` beside `generated`. Two directory renames
expose complete projections or a briefly absent directory, so concurrent readers
fail closed instead of consuming a mixed pair. An installation error restores
the old directory; a process interruption between renames requires restoring the
retained backup before retrying. Run publication under the repository lease.

The parity record's `probe_command` is a portable producer recipe, not a captured
exact invocation. New records include `--output-root NEW_DIRECTORY`; substitute
a fresh directory when executing the recipe. Publication accepts earlier
nonempty string recipes under the same schema, while rejecting missing, empty
or non-string recipes. Recipe text alone never establishes runtime execution.


### Hosted canonical-identity checkpoint (2026-10-28)

[Source-pair qualification run 40765894086](https://github.com/ActiveInferenceInstitute/fep_formal/actions/runs/40765894086)
captured the canonical working projections for FEP source
`36669da54690ddfdc3ee29f5135f79e44f9d0f03` and GNN source
`714cea22eeb68991c364cef11a23b57f1a618932`. The
[transport context](source_qualification_ci40765894086.json) retains the
separate workflow revision, attempt and exact exported-file hashes.
The [native receipt](native_receipt_ci40765894086_fep36669da_gnn714cea22.json)
was compiled and independently checked on that Linux producer. Current source
binding also matches the imported projections locally.

These are five real parser observations and twelve static coefficient/prediction
bounds, without generated-runner execution, full-mode or release acceptance.
Native receipts retain their actual compiler environment and command paths;
a local native claim requires the applicable local capture and check.
Earlier receipts remain unchanged historical evidence.


### Website shutdown source checkpoint (2026-10-28)

[Source-pair qualification run40786981014](https://github.com/ActiveInferenceInstitute/fep_formal/actions/runs/40786981014)
captured FEP source `daae1d2928fe295c0eea6629f0857d4cb5cdc6d1` with
GNN source `e7cad532b5a0dea156fa39c9e918cd80f0ef99bb`, after the loopback
website server retained its bound HTTP server across immediate shutdown.
The [transport context](source_qualification_ci40786981014.json) records the exact source and workflow
revisions, attempt and exported-file hashes. The only changed GNN Python
owner is `src/gnn/website/serve.py`; the source roster and FEP owner bytes
match the previous checkpoint. The rendered runner, canonical scaffold and
Lean probe retain their previous bytes.

The [new native receipt](native_receipt_ci40786981014_fepdaae1d2_gnne7cad532.json) compiled and independently checked all
twelve static Q7 statements on its recorded Linux Lean4.35.0 producer, with
zero compiler warnings and the same three standard axioms. Five real parser
observations renew the working serialization projection. Local read-only
source checks must independently match these imported projections; this does
not claim local native execution, generated-runner execution, full mode or
release acceptance. Earlier source and native receipts remain unchanged.
