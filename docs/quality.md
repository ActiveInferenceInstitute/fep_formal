# Quality-gate decision record (updated 2026-10-15)

**Decision date:** 2026-08-19<br>
**Owner:** fep_lean repository maintainers<br>
**Decision:** Ruff lint and formatting are both blocking zero-debt gates.

## Current policy — 2026-10-15

Ruff lint and formatting remain blocking zero-debt gates. The
[root required-check inventory](../AGENTS.md#required-checks) owns their exact
commands: lint covers the repository with the reviewed exclusions in
[`pyproject.toml`](../pyproject.toml), while formatting covers `src`, `tests`,
`scripts` and `docs`. Mypy checks `src`, `scripts` and `docs` with the declared
3.14 target. The earlier narrower lint command below records its source epoch;
it is not the current command owner.

## Recorded policy — 2026-10-05 (superseded command scope)

CI now runs both `ruff check src tests scripts docs` and
`ruff format --check src tests scripts docs` without `--exit-zero` or a shell
fallback. Both checks must pass under the pinned development dependency before
acceptance is recorded for a source epoch.
Exceptions require a reviewed `pyproject.toml` rule policy or a narrowly scoped,
justified line-local suppression. The two `S102` suppressions currently in
[`tests/test_release_bundle.py`](../tests/test_release_bundle.py) execute only
allowlisted functions from held local workflow syntax. A separate suppression
in [tests/_support/custody_fixture_knobs.py](../tests/_support/custody_fixture_knobs.py)
loads the byte-checked historical validator for a synthetic, disposable test
epoch. These suppressions do not authorize broad ignores, an informational CI
wrapper or a lint fallback. Source review of an exception does not establish
runtime acceptance of the affected tests.

## Revision 4 — 2026-07-31 (superseded)

Ruff is pinned at `>=0.15.0`. Both `ruff check` (lint) and `ruff format --check`
(format) are clean — zero findings across `src/`, `tests/`, `scripts/`, `docs/`.
CI runs `ruff check` as a **blocking** gate and `ruff format --check` as
informational pending verification that the format pass is stable on CI runners.

### Updated staged plan

1. ✅ **Pin a reviewed Ruff version** in the `dev` extra.
   (Done: `pyproject.toml`. The former `.ruff_baseline.txt` artifact is
   deleted; it recorded a frozen ruff version and a 0-finding count that
   revision 5 made redundant.)
2. ✅ **Clear source and maintenance-script lint findings in small, reviewable batches.**
   (Done: ruff check is 0 findings.)
3. ✅ **Run `ruff format` on the 55 remaining files** to clear the format debt, then
   promote `ruff format --check` to a blocking gate. (Done: 55 files reformatted,
   format check clean locally.)
4. ✅ **Remove the CI format fallback and make the clean format check blocking.**
   (Completed in revision 5.)

### CI state

- `ruff check src tests scripts docs` — blocking (removed `--exit-zero`)
- `ruff format --check src tests scripts docs` — blocking

## Revision 3 — 2026-07-31 (superseded)

Revision 3 claimed Ruff was fully "clean" and promotion was "automatic", but this
was overstated: `ruff check` was indeed clean, but `ruff format --check` failed on
55 files, and CI still ran both steps with `--exit-zero`. Revision 4 corrects this
by treating lint and format as separate gates with distinct promotion criteria.

## Related contracts

- [Ideal-state assessment](../ISA.md)
- [Canonical backlog](../TODO.md)
- [Development checks](development.md)
