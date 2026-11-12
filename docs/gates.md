# Local gate arms

`bash scripts/gate.sh <arm>` is the repository's one local gate entry point.
Each arm executes the exact command hosted CI executes for that purpose; the
normative list remains the "Required checks" block in
[`AGENTS.md`](../AGENTS.md#required-checks), and
`tests/test_check_inventory.py` resolves the arms and fails if a command,
a CI arm or an arm-command drifts. A failing command does not stop the arm:
every command is attempted and the arm exits non-zero if any failed.

| Arm | What it runs | CI job that calls it |
| --- | --- | --- |
| `fast` (default) | CI's composition-inventory test plus the gate-inventory contract | none (local only) |
| `full` | CI's full non-serial pytest command with coverage, plus the measured package-floor gate | none (the `python` job still owns the two live Chrome probes and membership) |
| `lint` | `ruff check .` and the consolidated `ruff format --check` roots | `static` (via the `static` arm) |
| `types` | strict `mypy` over `src`, `scripts`, `docs` and the two CI helpers, plus the `fep_lean` adapter | `static` (via the `static` arm) |
| `catalogue` | catalogue materialization, generated projections, methods check, font/render receipts, theorem-reference and citation audits | `python` |
| `docs` | `catalogue` plus manuscript check, link, Markdown-hygiene and cross-reference checks | `documentation` |
| `gnn` | frozen-custody probe checks, GEO notation check, retained runner evidence, Gaussian composition replay | `gnn-conformance` |
| `static` | `uv lock --check`, `uv pip check`, composition inventory, catalogue, prose checks, lint, types, `git diff --check` | `static` |
| `all` | `fast`, `lint`, `types`, `docs`, `gnn` (not `full`) | none |

Setup is not an arm: run `uv sync --locked --extra dev` once first. The arms do
not install tools, fetch Mathlib or call a provider.

## Measured wall time

One warm run per arm on the estate host (macOS arm64, Python 3.14.10, uv
0.13.7), 2026-11-12, before and after routing CI through the arms. "Before" is
the same command sequence run directly, which is what the replaced CI steps
executed; it is not a hosted-runner measurement.

| Arm | Before | After |
| --- | --- | --- |
| `fast` | not separately measured (new selection) | 3.8 s |
| `lint` | 0.4 s | 0.1 s |
| `types` | 4 s | 0.9 s |
| `docs` | 74 s | 47 s |
| `gnn` | 4 s | 6 s |
| `static` | not separately measured (new sequence) | 32 s |
| `full` | 327 s (CI remainder command) | PENDING |

The `lint` and `types` "after" values are warm-cache runs; the "before"
values are the first cold runs of the same commands. The `docs` "before" run
was the replaced documentation-job command list executed directly; its
"after" run reuses the catalogue and generated projections warm. The `full`
"before" number is the baseline parallel remainder with coverage, which is the
same command the arm now runs.

Arm wall time is not a hosted-runner time. CI billing is locked for this
organization, so local runs are the only gate evidence; no hosted speedup is
claimed from these numbers.

### Lanes not measured here

The native Lean lane and the publication render are outside the arm table.
The exact native command

```bash
uv run fep-formal verify --fail-on-warnings --receipt output/native-verification.json
```

was stopped at 12 m 59 s after 159 of 168 topics under the 10-minute
measurement bound; it writes its receipt only after the full roster, so no
receipt was produced. `uv run python scripts/render_publication.py` was not run
because hydration refuses without that claim-ready receipt, and faking one is
not acceptable. The host did have the other render tools: pandoc 3.13,
`xelatex`, `rsvg-convert`, `@mermaid-js/mermaid-cli` 11.17.0, the two preamble
faces, and a `docxology/template` checkout at the workflow's pinned ref
`5b3c0f43940f0322fbc6205b3be4c2854f99329d`. The render lane remains a hosted
or long local run, not an arm.

## Documentation check

There is no MkDocs or `markdown-link-check` configuration in this repository.
The documentation gate is the repository's own pair:
`uv run python docs/check_links.py --strict --include-root` (relative links and
anchors, including the generated `.github/README.md` mirror) and
`uv run python docs/md_hygiene.py --strict --include-root`. Both are in the
`docs` and `static` arms.
