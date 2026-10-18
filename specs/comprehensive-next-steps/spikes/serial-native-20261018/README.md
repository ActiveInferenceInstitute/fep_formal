# Exact-source serial native measurement

The retained baseline and a fresh isolated repeat cover the same 168 topics at
source commit `009b0676f0e2d1d50b2c73ed6c830e31c65fa199`. Catalogue, source,
configuration, roster, compiler and Mathlib identities match. Every per-topic
outcome and warning classification matches; both owner validators report
source-bound native readiness. Neither run records errors, warnings or `sorry` occurrences.
Tracked source bytes remained unchanged during the isolated repeat.

The sums of per-topic command intervals are 543.811 seconds and 723.187 seconds;
their medians are 3.082 and 4.166 seconds. These are not separately observed
loop wall times. The repeat's actual CLI lifetime is 729.47 seconds; orchestration
including lease waiting is 729.579 seconds. Darwin `time -l` observed a maximum
resident set size of 1534607360 bytes for the repeat command. No first-run
resource comparison or per-topic resource attribution is available. Machine
load and cache conditions are not controlled, so these measurements establish
no speedup. Per-topic intervals do not isolate imports or process startup.

[comparison.json](comparison.json) retains all 168 timing/outcome pairs and
artifact hashes. [baseline-native.json](baseline-native.json) and
[repeat-native.json](repeat-native.json) are the exact owner receipts;
[owner-validation.json](owner-validation.json) retains both independent owner
validator results. [repeat-native.log](repeat-native.log) contains the complete
actual command output and resource observations. [qualification.json](qualification.json)
records source preservation and the distinction between orchestration and CLI
timing. A failed initial package-module invocation ran no native verification;
its scratch log is retained separately. The successful command used the actual
`fep_lean.cli` entry module. Validation JSON was reparsed before acceptance.

Reproduce the serial repeat in a separate owned clone with the matching built
Mathlib cache and this compiler pin:

```sh
/usr/bin/time -l uv run fep-lean verify --fail-on-warnings \
  --receipt output/serial-native.json
```

Use the platform's timing tool when `time -l` is unavailable. Keep its raw units
explicit. This accepts Issue127/P11's narrow serial measurement; it changes no
verifier implementation and does not enable parallel execution. A future
parallel proposal still requires isolated workspaces, exact-roster outcome
comparison, resource bounds and actual child-cleanup controls. No fresh axiom
audit, full pipeline, production capture or scientific acceptance follows.
