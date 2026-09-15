# Development guide

## Setup

```bash
uv sync --locked --extra dev
uv run python -c "from fep_lean.catalogue import FEPTopicCatalogue; print(len(FEPTopicCatalogue.default().topics))"
```

The distribution uses a single `fep_lean` namespace under `src/fep_lean/`.
Do not add `PYTHONPATH` shims or import obsolete top-level modules such as
`catalogue` or `pipeline`; the isolated-wheel test enforces this boundary.

## Canonical authoring graph

- `config/catalogue_metadata.yaml`: stable topic metadata and Mathlib hints.
- `config/theorem_maturity.yaml`: semantic review and primary theorem.
- `config/formalism_novelty.yaml`: expansion-row nearest topics, carrier delta,
  invariant, and required composition bridge.
- `config/formalism_relations.yaml`: explicit derivational formal,
  non-implicational formal-pairing, conceptual, and blocker relations plus
  retained capability status/evidence.
- `src/fep_lean/catalogue/bodies/*.py`: family-owned canonical Lean bodies;
  `registry.py` validates their sole ordered union and `latex.py` derives
  theorem signatures.
- `src/fep_lean/formal/`: reusable finite and measure-theoretic foundations plus
  exact cross-topic proofs; `manifest.py` owns foundation, leaf-composition,
  and aggregate roles.
- `config/topics.yaml`, packaged `src/fep_lean/data/topics.yaml`, aggregate
  Lean, maturity audit, and coverage files: generated projections.

Every body keeps its `namespace FEPNNN ... end FEPNNN` wrapper and may declare
the narrow Mathlib imports it needs. Generated aggregate wrappers add a second
topic namespace to prevent helper collisions.

## Change loop

```bash
uv run python scripts/_maint_build_topics_catalogue.py
uv run python scripts/_maint_build_fep_all_lean.py
uv run python scripts/_maint_build_formal_modules.py
uv run python scripts/theorem_maturity_audit.py
uv run python scripts/build_formalism_coverage.py
uv run fep-lean atlas
uv run fep-lean dashboard

uv run python scripts/_maint_build_topics_catalogue.py --check
uv run python scripts/_maint_build_fep_all_lean.py --check
uv run python scripts/_maint_build_formal_modules.py --check
uv run python scripts/theorem_maturity_audit.py --check
uv run python scripts/build_formalism_coverage.py --check
uv run python scripts/_maint_build_lean_landscape.py --check
uv run fep-lean atlas --check
uv run fep-lean dashboard --check
uv run python specs/geo-infer-notation-bridge/check_geo_notation_bridge.py --check
uv run python docs/theorem_ref_audit.py
uv run python docs/citation_audit.py
uv run fep-lean catalogue
uv run python scripts/render_manuscript.py --check

uv run ruff check src tests scripts docs
uv run ruff format --check src tests scripts docs
uv run mypy src
uv run pytest tests/ -q --cov=src --cov-fail-under=89 -m "not serial_lean"
uv run python docs/check_links.py --strict --include-root
uv run python docs/md_hygiene.py --strict
uv run python docs/pin_audit.py --check-latest
uv run python docs/xref_audit.py
```

Run native Lean acceptance separately because it is the expensive semantic
compiler boundary:

```bash
uv run fep-lean verify \
  --fail-on-warnings \
  --receipt output/native-verification.json
cd lean && lake build FepSketches
cd .. && uv run python scripts/audit_formalisms.py \
  --receipt output/formalism-audit.json
```

The native receipt establishes exact-source compilation for the stable topic
roster; the formalism audit separately covers the maintained formal modules
and reviewed declarations. A credentialed full run remains a distinct gate:

```bash
uv run fep-lean preflight
uv run fep-lean run --topic fep-001
uv run fep-lean run
```

Never inject credentials into source, tests, or generated evidence.

## Package boundaries

| Area | Path | Contract |
| --- | --- | --- |
| Catalogue | `src/fep_lean/catalogue/` | typed authoring, loading, audits, coverage |
| Formal kernel | `src/fep_lean/formal/` | reusable finite carriers, cross-topic proofs, and exact Lake projection |
| Verification | `src/fep_lean/verification/` | read-only capability probes, Lean subprocesses, declaration/axiom audit |
| Hermes | `src/fep_lean/llm/` | provider request, retry, and response validation |
| Sessions | `src/fep_lean/gauss/` | SQLite ownership and per-topic runner |
| Pipeline | `src/fep_lean/pipeline/` | strict `catalogue`/`full` orchestration |
| Output | `src/fep_lean/output/` | receipts, reports, figures, rendering, atlas, and numerical witness dashboard |

Use type hints on public APIs, immutable dataclasses for source records,
structured results at subprocess/network boundaries, and temporary paths in
tests. Preserve catalogue, native, and full-run evidence as separate types and
claims.

For theorem ownership, support conventions, the validation ladder, and the
limits of numerical witnesses, see
[formal-kernel methods](formal-kernel-methods.md).

## Roster expansion

The current schema deliberately seals a reviewed, family-partitioned roster.
Adding another topic is a policy/schema change, not a YAML append. It requires
updating the roster seal and family metadata, semantic record, canonical body,
novelty record and composition bridge, generated projections, registry and
coverage tests, and manuscript review together. A new ID is not accepted until
that scientific review and its native acceptance plan are explicit.

## Source-owner roster expansion

The report and native receipts bind a versioned owner roster
(`SOURCE_OWNER_ROSTER` in `src/fep_lean/output/provenance.py`), not a
recursive checkout snapshot. Adding a file under `src/fep_lean/**/*.py` or
`scripts/*.py` fails receipt validation fail-closed until the file is
reviewed into the roster and `OWNER_MANIFEST_VERSION` is bumped. The bump
orphans every retained receipt that pins the previous version, so roster
growth is a coordinated evidence refresh (the completed refresh is recorded
in [CHANGELOG.md](CHANGELOG.md); a further roster change re-opens the
requirement), not a per-PR append. Per-PR alternatives: fold the new code
into an existing
rostered owner (the status verb lives in `cli.py`), or keep tooling
slice-local under `specs/`, which is not rostered.

See [authorship-guide.md](authorship-guide.md), [testing.md](testing.md), and
[troubleshooting.md](troubleshooting.md).

## Interpreter contract

`requires-python = ">=3.10"` declares the packaging floor, but the current
dev/evidence reality is narrower and pinned: `.python-version` pins CPython
3.14 for development and CI, mypy models 3.12 (`[tool.mypy] python_version`),
and the runtime test suite runs under 3.14 only. The declared 3.10/3.11 floor
is evidentially unsupported until `FEP-SCAFFOLD-PORTABILITY` resolves:
`scaffold_digest` freezes `ast.dump` output, which differs across CPython
minor versions, so a scaffold accepted under one interpreter cannot be
re-validated under another. Treat 3.14 as the only accepted runtime for
verification runs until that TODO lands a version-stable serialization or an
explicit multi-interpreter acceptance record.
