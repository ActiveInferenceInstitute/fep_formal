# Fixture contract

Pinned inputs for the suite. Treat every file here as evidence, not as
test-author convenience data.

## Rules

- Do not regenerate, reformat or reorder a fixture to make a test pass. Fix the
  consumer or record a reviewed replacement.
- Preserve exact bytes for `historical_*_Y.txt`: [`.gitattributes`](../../.gitattributes)
  disables text conversion for both files.
- A dated review fixture describes its named source epoch. Do not edit its
  values to describe a later checkout; add a new dated record instead.
- Add a fixture only together with the test that consumes it, and use the
  existing naming pattern (`<subject>_<kind>_<YYYYMMDD>.json` for dated
  reviews).
- A byte change can invalidate a digest, custody check or retained receipt.
  Review it as an evidence change, not as fixture cleanup.

Follow the [test contract](../AGENTS.md) and the
[root required checks](../../AGENTS.md#required-checks).
