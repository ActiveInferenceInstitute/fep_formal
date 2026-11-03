# Comprehensive science improvement

Dated scope, protocol and H2 recapture records from the 2026-09/10 improvement
cycle. This is a historical slice, not the current pickup point.

## Files

| File | Role |
| --- | --- |
| [SCOPE-2026-09-30.md](SCOPE-2026-09-30.md) | Retained preimplementation baseline of that day's scope review. |
| [SCOPE-2026-10-08.md](SCOPE-2026-10-08.md) | Scope review of that day; candidates were filed as Issues and tracked in [TODO.md](../../TODO.md). |
| [PROTOCOL.md](PROTOCOL.md) | The locked nine-criterion protocol for the cycle. |
| [EXECUTION.md](EXECUTION.md) | Dated execution log and checkpoints. |
| [NEXT.md](NEXT.md) | Remaining acceptance and continuation order at its recorded date. |
| [H2-CAPTURE-CONTRACT.md](H2-CAPTURE-CONTRACT.md) | Proposal for the current H2 mandatory-test recapture. |
| [capture_h2_evidence.py](capture_h2_evidence.py) | Capture harness for the H2 roster and its real outcomes. |
| [test_capture_h2_evidence.py](test_capture_h2_evidence.py) | Tests for the harness. |
| [evidence/](evidence/) | Retained captures and observations; frozen. |

## Status

The scope reviews, protocol and execution log are dated snapshots. They do not
describe current source acceptance. Current work lives in
[TODO.md](../../TODO.md) and the
[active next-step campaign](../comprehensive-next-steps/README.md).

An accepted capture record is preparation evidence only. It is not H2
acceptance, native evidence or scientific acceptance. The capture harness
never changes a receipt, frozen roster pin or diagnostics; the coordinator
must independently review and seal any successful capture.

## Rules

Follow the [spec contract](../AGENTS.md). Do not rewrite `evidence/` bytes or a
dated review to reflect a later checkout. Add a new dated record instead.
