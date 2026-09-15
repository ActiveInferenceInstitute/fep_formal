# Q7: fixed scalar OU artifact and coefficient-error certificate

This slice connects a current canonical GNN JAX render of the P4b scalar OU
document to exact real one-step coefficients and bounds the error of its six
embedded binary64 parameters. The exact generated probe has a validated [native receipt](native_receipt.json);
its complete axiom census and both coefficient-negative regressions passed.
See [the delivery report](REPORT.md).

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
It never executes the emitted runner. `generate_probe.py` creates the probe and
manifest; `generate_probe.py --check` compares bytes without writing. The parent
receipt engine owns source/toolchain/native custody and must check the manifest's
complete `receipt_contract` before accepting evidence. A generated manifest is
explicitly not native evidence.

The retained P4b `NUM_TIMESTEPS=1` observes the prior and never exercises F or Q:
`kalman_step(..., first=True)` skips prediction, and transitions run only for
`range(1, T)`. Separate numerical evidence must invoke `first=False` on a
nonstationary belief or use at least two samples. The GNN three-step nonstationary regression exercises that runtime route.
It remains execution evidence, distinct from the static coefficient proof.

## Interpreter contract for the frozen scaffold

`scaffold_digest` freezes `ast.dump(...)` output, whose formatting is CPython
minor-version-sensitive: the accepted `expected.json` digest
(`runner_ast_sha256`) was reviewed and pinned under CPython 3.14 and does not
reproduce under other minor versions (the 3.12 dump differs). The accepted
interpreter set for validating this scaffold is therefore exactly **CPython
3.14**, the version `.python-version` pins for development and CI; no other
CPython is accepted to re-validate the frozen digest until
`FEP-SCAFFOLD-PORTABILITY` lands a version-stable canonical serialization,
which requires a new reviewed scaffold and a coordinated custody re-pin rather
than a unilateral `expected.json` regeneration. Since 2026-09-15 the
contract is enforced in-module: `scaffold_digest` refuses to run before
parsing under any interpreter outside the accepted set, raising
`ContinuousArtifactError` with an `interpreter` reason that names both the
accepted set and the running interpreter; the pinned digest is unchanged by
the guard (no receipt re-seal). The focused test
`tests/test_gnn_continuous_artifact_proof.py::test_frozen_scaffold_digest_reproduces_the_pinned_interpreter_contract`
asserts the whole contract: the checkout pins 3.14, the validating
interpreter IS 3.14, a non-accepted interpreter is refused with the clear
error, an explicitly accepted interpreter proceeds, and `scaffold_digest` of
the retained runner reproduces the pinned `runner_ast_sha256` under it. Q5/Q6
runner custody is whole-file sha256 and already interpreter-independent; this
contract governs only the Q7 AST scaffold digest.

Acceptance requires focused extraction/custody-negative tests, current render
provenance, exact probe regeneration, native compilation with no warnings or
`sorryAx`, and axiom reports containing only the established standard axioms.
The implementation is integrated; changes require fresh source-bound evidence.
