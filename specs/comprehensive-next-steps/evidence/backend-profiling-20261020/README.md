# Retained Python3.15 backend profiling observation

This immutable record describes an isolated installed-wheel experiment, before
the separate CLI ownership and NESS prose changes. It is engineering performance
evidence, not a mathematical, scientific or hosted-runtime acceptance record.

[observation.json](observation.json) is a portable summary of actual local raw
records. It preserves all six fresh-process samples, source/wheel/dependency
hashes, platform, scope, and raw-receipt hashes without local user directory
paths. The original byte receipts remain separately retained in the task
outputs. Sampling was denied process-memory access on this macOS setup; actual
Python3.15 tracing identified the work, and separate unprofiled measurements
supply the reported timing and peak process RSS. Instrumented timing is not used
as a speed comparison.

The baseline is Git commit
`d8fb341a2121e1add23ca3535a345c86a46ee51d`. Applying the exact
[candidate.patch](candidate.patch) to a separate archived copy changes only the
two identified Python owners. Build/install each wheel with the recorded exact
runtime dependency versions. Use the
[isolated profiling recipe](../../../../docs/development.md#profile-an-isolated-runtime)
and alternate three fresh Python3.15 processes per variant. Time the call to
load_packaged_formalism_query after import; consume its public as_dict output
before recording peak process RSS. Record subsequent warm calls separately.

The measured cold median was15.270s versus3.671s (4.16× locally), and median peak
process RSS was264.4MB versus151.6MB. The complete query JSON differed only in
the two owner digests. All100 selected methods/relation/coverage tests passed;
strict typing and formatting passed separately. A bounded immutable declaration
cache still reflected same-file edits, rejected introduced duplicates and
restored the original owner mapping when source bytes were restored.

A prior memory experiment broke the extractor's string-context contract and
was rejected. The retained candidate makes shared context opt-in only inside
the immutable builder; default extractor behavior is preserved. These small
local observations are not a universal speed guarantee. Full repository,
installed-wheel matrix, native/publication and issue acceptance remain separate.
