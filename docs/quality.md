# Quality-gate decision record (updated 2026-08-19)

**Decision date:** 2026-08-19<br>
**Owner:** fep_lean repository maintainers<br>
**Decision:** Ruff lint and formatting are both blocking zero-debt gates.

## Revision 5 — 2026-08-19 (current)

CI now runs both `ruff check src tests scripts docs` and
`ruff format --check src tests scripts docs` without `--exit-zero` or a shell
fallback. The repository is clean under the pinned development dependency.
Any future exception belongs in the reviewed `pyproject.toml` rule policy, not
in an informational CI wrapper.

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
