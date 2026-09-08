# Formalism authorship guide

This guide covers strengthening an existing reviewed topic and deciding when a
result belongs in the reusable formal kernel. Roster expansion is a separate
schema and scientific-review decision described in
[development.md](development.md).

## 1. Start from the scientific claim

Read the topic's row in `config/theorem_maturity.yaml` before touching Lean.
Review these independently:

- `invariant`: the precise narrowed claim intended for the primary theorem;
- `assumption_review`: assumptions that limit scientific reach;
- `non_vacuity`: why the premises admit meaningful witnesses;
- `acceptance_probe`: the native compiler check plus any topic-specific test;
- `disposition`: `formalized`, a proxy class, or an explicit gap.

Compilation does not justify promoting the disposition. A promotion requires
the primary theorem to state the reviewed invariant at the claimed level of
generality, with satisfiable assumptions.

## 2. Edit the maintained sources

Update the relevant rows in:

1. `config/catalogue_metadata.yaml` for title, area, import hint, or syntactic
   maturity;
2. `config/theorem_maturity.yaml` for semantic scope and primary theorem;
3. the matching family module under `src/fep_lean/catalogue/bodies/` for the
   canonical Lean body. `registry.py` validates the body and `latex.py` derives
   theorem signatures.

Each body must keep its topic namespace, use only pinned Mathlib declarations
or definitions supplied in the body, and contain no `sorry`. Prefer the
narrowest real Mathlib imports. Do not invent a local homonym when Mathlib
already provides the mathematical object.

For exploratory checking:

```bash
cd lean
lake env lean /absolute/path/to/scratch.lean
```

For the maintained row:

```bash
uv run fep-lean verify --topic fep-NNN --fail-on-warnings
```

If the new statement introduces a normalized carrier or law that multiple
topics should share, place it in the relevant canonical module under
`src/fep_lean/formal/`. If it genuinely consumes declarations from multiple
stable topic namespaces, place it in the appropriate manifested leaf under
`src/fep_lean/formal/compositions/` and add its novelty/relation evidence.
`composed.lean` is an import-only aggregate. Follow the ownership,
support-assumption, and dependency rules in
[formal-kernel methods](guides/formal-kernel-methods.md); do not manufacture a formal
relation from a shared import.

## 3. Regenerate; never mirror edits by hand

```bash
uv run python scripts/_maint_build_topics_catalogue.py
uv run python scripts/_maint_build_fep_all_lean.py
uv run python scripts/_maint_build_formal_modules.py
uv run python scripts/theorem_maturity_audit.py
uv run python scripts/build_formalism_coverage.py
uv run fep-lean atlas
uv run fep-lean dashboard
```

These commands update the checkout/package catalogue pair, whole-catalogue
Lean target, formal-module projection, semantic audit, coverage map, and the
two validation visualizations. Their `--check` modes must then be clean.

## 4. Review at four levels

1. **Syntactic:** the focused topic and aggregate compile with zero errors,
   warnings, and `sorry`.
2. **Semantic:** the exact primary theorem, assumptions, and witness story
   justify the maintained disposition.
3. **Relational:** every new `formal` relation, `formal_pairing`, or satisfied
   capability names a qualified declaration that resolves in the formalism
   audit. Use `formal` only for a real derivation or identification and
   `formal_pairing` for a checked conjunction; module imports remain separate
   implementation evidence.
4. **Publication:** manuscript theorem identifiers resolve, placeholders render
   fail-closed, bibliography keys resolve, and prose does not broaden the Lean
   statement.

Recommended focused gates:

```bash
uv run pytest \
  tests/test_semantics.py \
  tests/test_catalogue_registry_ssot.py \
  tests/test_formal_foundations.py \
  tests/test_formalism_coverage.py \
  tests/test_formalism_atlas.py \
  tests/test_formal_kernel_dashboard.py \
  tests/test_manuscript_references.py \
  -q --no-cov
uv run python docs/theorem_ref_audit.py
uv run fep-lean catalogue
uv run python scripts/render_manuscript.py --check
```

Then run the full development and native acceptance commands in
[development.md](development.md).

## 5. Evidence language

- “Compiles” means the pinned Lean compiler accepted the exact source.
- “Native claim-ready” additionally means a live-source-bound full-roster
  receipt with actual Lean output matching the pin, an exact resolved Mathlib
  revision, finite timings, zero errors, zero warnings, and zero `sorry`.
- “Formalism-audited” means every reviewed declaration resolved and its parsed
  axiom report contained no `sorryAx`; it does not judge scientific scope.
- “Full-run claim-ready” means the independent report validator accepted a
  complete credentialed Hermes/OpenGauss/Lean artifact bundle whose provider
  session, model, exact compiled source, compiler identity, dependency revision,
  topic files, and redundant manifests all reconcile with the live tree.
- “Numerically witnessed” means a deterministic finite example exhibits the
  expected shape; it is not a proof or an empirical validation result.
- “Formalized” is a semantic-disposition judgment, not a synonym for any of
  the three execution states above.
