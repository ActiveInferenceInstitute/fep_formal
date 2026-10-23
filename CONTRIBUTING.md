# Contributing to FEP_Formal

The agent and contributor contract is [AGENTS.md](AGENTS.md); this page is the
short human entry point and links to it rather than copying it.

Use American English in maintained human-facing text. Preserve exact public
identifiers, proper names, citations, and frozen evidence in their original form.

## Environment

Use the validator Python selected by [`.python-version`](.python-version)
(currently 3.14) and the exact uv version declared in
[`pyproject.toml`](pyproject.toml). The packaging floor is a compatibility
boundary, not an alternative validator environment.

```bash
uv sync --locked --extra dev
```

Run this **before any `uv run`**. A bare `uv run` on an unsynced environment
does not install the `dev` extra and can silently run a stale `ruff` that
reports errors the pinned one does not (or the reverse).

## Check tiers

[AGENTS.md "Required checks"](AGENTS.md#required-checks) is the single source of
the command list; run the tier that matches your change.

| Tier | When | What to run |
| --- | --- | --- |
| Docs-only | Markdown edits | The canonical strict link, root-inclusive Markdown hygiene, pin/latest-stable and cross-reference checks; materialize manuscript inputs before checking their references. |
| Static | Python, config or generator edits | The docs-only tier plus affected projection checks, repository-wide Ruff lint, formatting and mypy over `src`, `scripts` and `docs`, using the exact commands in the canonical list. |
| Full | Before requesting merge of code, Lean or manuscript changes | Everything in "Required checks", including the `pytest` coverage run; hosted `ci.yml` repeats it and a green run on the exact commit is the release gate ([release procedure](docs/release.md)) |

## Rules that bite

- **Provenance roster.** A new file under `src/fep_lean/**/*.py` or
  `scripts/*.py` fails report and native receipts fail-closed until it is
  reviewed into `SOURCE_OWNER_ROSTER` in
  [`src/fep_lean/output/provenance.py`](src/fep_lean/output/provenance.py). Roster
  growth is a coordinated evidence refresh, not a per-PR append. Fold new code
  into an existing owner, or keep tooling slice-local under `specs/`. Editing
  existing files is fine.
- **Generated files.** Never hand-edit a generated file (`config/topics.yaml`,
  `src/fep_lean/data/topics.yaml`, `lean/FepSketches/fep_all.lean`, the atlas,
  coverage, landscape and maturity-audit documents, formal Lake projections).
  Change the source or the generator listed under "Source of truth" in
  [AGENTS.md](AGENTS.md) and regenerate; the matching `--check` must pass.
- **Evidence boundaries.** Boundary sentences in README, AGENTS and HANDOFF are
  deliberate claim hygiene. Relocate them verbatim; do not paraphrase or weaken.
- **Open work** lives in [TODO.md](TODO.md); finished work goes in
  [CHANGELOG.md](CHANGELOG.md).

## Pull requests

Branch from `main` on a short-lived topic branch and open a pull request;
`main` history uses merge commits (`Merge pull request #N from ...`), and the
repository deletes the head branch after merge.
Commit subjects are short and imperative, usually with a conventional-style
prefix (`docs:`, `tooling:`, `bridge:`, `tests:`, `ci:`, `fix(ci):`); reference
the issue number where one exists, for example
`docs: first-run path at the top of the README (#138)`. Describe which check
tier you ran.
