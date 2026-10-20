# Historical generated-runner execution evidence

This BRIDGE-D1 slice retains two actual generated-runner invocations for the
[FEP source](https://github.com/ActiveInferenceInstitute/fep_formal/commit/cc2cd1699350530e2bfdec195e8dc9f28a6d4fcb)
and [GNN source](https://github.com/ActiveInferenceInstitute/Generalized_Notation_Notation/commit/9a94853e9fceb568dea3b91d11336c4ede6dcf7b).
The evidence binds that historical pair; it does not claim a current-source run.

Both invocations use the unmodified generated runner, seed 42 and T=1. They
exercise the initial Gaussian observation and posterior update. They do not
exercise OU prediction or dynamics. The independent checker recomputes the
posterior mean, covariance, control and RMSE with relative and absolute tolerances of 1e-12.
The retained records distinguish the two actual numerical runs from 22 synthetic
capture-adapter controls. Synthetic controls test physical refusal paths and are
not additional scientific observations.

## Offline validation

From this directory, run:

```sh
python -B validate_retained.py
python -B test_validate_retained.py
```

The default validator checks the reviewed manifest, all 369 retained files,
actual streams, protocol bindings, numerical outputs and separately reviewed
synthetic controls. It does not execute the runner, Lean, subprocesses or network
requests. The evidence includes the historical runtime inventory, not the runtime
binaries themselves.

To additionally check all 197 FEP and 771 GNN historical source owners against
locally available Git objects:

```sh
python -B validate_retained.py --fep-git /path/to/fep_formal --gnn-git /path/to/Generalized_Notation_Notation
```

Both arguments are required together. Git replacement objects and lazy fetching
are disabled. Missing historical objects cause refusal; obtain the needed objects
separately before invoking this read-only check. The validator does not require
checking out historical source into an active project.

## Reproduction boundary

The frozen capture adapter, protocol and logs preserve their original absolute
paths. They are historical evidence, not a portable command for overwriting those
paths. Reproduction must use new isolated directories and a new protocol while
retaining these records unchanged.

Create detached source exports at the two commits linked above. Use CPython
3.11.17 on Darwin arm64 with the retained requirements: jax 0.9.2, jaxlib 0.9.2,
numpy 2.4.4, scipy 1.17.1, ml_dtypes 0.5.4 and opt_einsum 3.4.0. The retained
protocol and capture source specify the exact generated input, CPU/x64/thread
environment, output schema, two invocations and 180-second deadline per invocation.
Retain a fresh inventory of the new runtime and bind the new absolute paths and
source owners before execution. The coordinator used CPython 3.14.8 and the
source-bound historical supervisor; preserve that distinction from the runner
interpreter. A successor capture must independently satisfy those same custody,
stream, numerical and refusal checks before it can be described as reproduced.

This slice does not promote historical Q5/Q6 fixtures, replace current Q7 native
acceptance, establish multistep dynamics, or supply browser or human-review
campaign evidence.
