"""Canonical declaration inventory and manuscript reference audit."""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from pathlib import Path

from fep_lean.lean_source import lean_code_without_comments

from .coverage import topic_import_modules
from .registry import BODIES

_DECLARATION_RE = re.compile(
    r"^\s*(?:noncomputable\s+)?(?:theorem|lemma|def|abbrev|structure|inductive)\s+"
    r"([A-Za-z][A-Za-z0-9_]*)",
    re.MULTILINE,
)
_REFERENCE_RE = re.compile(r"\bfep\d{3}_[A-Za-z0-9_]+\b")
_FENCE_RE = re.compile(r"```.*?```", re.DOTALL)
# A ``lean``-tagged fence is typeset as a catalogue body, so a ``fepNNN_`` name
# inside it is a claim about a real declaration. Blanking every fence made this
# audit structurally unable to see that class: the primer printed
# ``fep001_union_bound`` as "catalogue row fep-001" for two releases while the
# gate reported "all references resolve". Only non-Lean fences are blanked now.
_LEAN_FENCE_RE = re.compile(r"^```lean[^\n]*\n.*?^```", re.DOTALL | re.MULTILINE)
_ANY_FENCE_RE = re.compile(r"^```[^\n]*\n.*?^```", re.DOTALL | re.MULTILINE)
# A line that names a ``fep-NNN`` row and quotes an identifier-shaped token is
# telling the reader that token is one of that row's declarations.
_ROW_RE = re.compile(r"\bfep-\d{3}\b")
_BACKTICK_RE = re.compile(r"`([^`]+)`")
# The framework chapters print each row's module column. It used to be
# hand-maintained "Mathlib navigation hint" prose, and forty-two of its
# seventy-one cells named a module the row never imports; the column is now
# the ``{{topics.fep-NNN.imported_modules}}`` token, computed from the body's
# own imports. This pattern matches a five-column ``fep-NNN`` row and captures
# that column so a hand-typed value can be rejected before it drifts again.
_MODULE_ROW_RE = re.compile(
    r"^\|\s*(?P<topic>fep-\d{3})\s*\|[^|]*\|[^|]*\|(?P<modules>[^|]*)\|[^|]*\|\s*$"
)
_IMPORTED_MODULES_TOKEN = "{{{{topics.{topic}.imported_modules}}}}"
# snake_case (must contain an underscore, so bare English words are ignored)
# or CamelCase type-shaped names.
_IDENTIFIER_RE = re.compile(
    r"[a-z][A-Za-z0-9]*(?:_[A-Za-z0-9]+)+|[A-Z][A-Za-z0-9]*[a-z][A-Za-z0-9]*"
)
# Identifiers that legitimately appear beside a ``fep-NNN`` row without being
# one of its declarations: Mathlib lemma names the prose cites as prior art,
# and catalogue metadata field names. Every entry is a reviewed exception; a
# new unresolved name fails the audit rather than joining this set silently.
NON_CATALOGUE_IDENTIFIERS = frozenset(
    {
        # Mathlib declarations cited as prior art or as a proof step.
        "klDiv_compProd_eq_add",
        "le_antisymm",
        "measure_union_le",
        "min_agrees_on_value",
        "norm_num",
        "sq_nonneg",
        # Mathlib and maintained-module type names cited as context, verified
        # present under lean/.lake/packages/mathlib or src/fep_lean/formal.
        "CondIndep",
        "CondIndepFun",
        "ENNReal",
        "FullSupport",
        "SigmaFinite",
        # Catalogue metadata field names from config/catalogue_metadata.yaml.
        "mathlib_status",
        "semantic_disposition",
        "assumption_review",
        "non_vacuity",
        "acceptance_probe",
        "primary_theorem",
        "lean_sketch",
        "latex_equations",
    }
)
_EXCLUDED_MANUSCRIPT_FILES = frozenset(
    {
        "AGENTS.md",
        "README.md",
        "09z_unified_formalism_catalogue.md",
        "09z_appendix_b_lean_catalogue.md",
        "09zc_appendix_c_lean_equations.md",
    }
)


def declaration_names(bodies: Mapping[str, str] = BODIES) -> frozenset[str]:
    """Return every named declaration in the canonical topic bodies."""
    return frozenset(
        name
        for body in bodies.values()
        for name in _DECLARATION_RE.findall(lean_code_without_comments(body))
    )


def _blank_non_lean_fences(text: str) -> str:
    """Blank every fence except ``lean`` ones, preserving line numbering."""

    def _blank(match: re.Match[str]) -> str:
        block = match.group(0)
        if _LEAN_FENCE_RE.fullmatch(block):
            return block
        return "\n" * block.count("\n")

    return _ANY_FENCE_RE.sub(_blank, text)


def manuscript_reference_files(manuscript_dir: Path) -> tuple[Path, ...]:
    """Return the authored Markdown files this audit inspects."""
    return tuple(
        path
        for path in sorted(Path(manuscript_dir).glob("*.md"))
        if path.name not in _EXCLUDED_MANUSCRIPT_FILES
    )


def unresolved_manuscript_references(
    manuscript_dir: Path, *, additional_declarations: Iterable[str] = ()
) -> tuple[str, ...]:
    """Return locations whose ``fepNNN_*`` name is not in a canonical surface.

    ``lean``-tagged fences are inspected. A fence that prints a theorem under a
    catalogue-row heading is the strongest claim the manuscript makes about a
    declaration, so it is exactly where a stale name must be caught.
    """
    known = declaration_names() | frozenset(additional_declarations)
    failures: list[str] = []
    for path in manuscript_reference_files(manuscript_dir):
        text = _blank_non_lean_fences(path.read_text(encoding="utf-8"))
        for line_number, line in enumerate(text.splitlines(), 1):
            for reference in _REFERENCE_RE.findall(line):
                if reference not in known:
                    failures.append(f"{path.name}:{line_number}: {reference}")
    return tuple(failures)


def unattributed_row_declarations(
    manuscript_dir: Path, *, additional_declarations: Iterable[str] = ()
) -> tuple[str, ...]:
    """Return identifier-shaped names claimed beside a ``fep-NNN`` row that do not exist.

    ``_REFERENCE_RE`` only matches the ``fepNNN_`` prefix form, so a navigation
    aid naming ``descent_contracts``, ``grad_sq_nonneg`` or ``ConjugateFamily``
    for a row passed every gate while matching nothing in the repository. This
    audit covers the un-prefixed form; :data:`NON_CATALOGUE_IDENTIFIERS` is the
    reviewed exception set for Mathlib names and metadata fields.
    """
    known = declaration_names() | frozenset(additional_declarations)
    failures: list[str] = []
    for path in manuscript_reference_files(manuscript_dir):
        text = _blank_non_lean_fences(path.read_text(encoding="utf-8"))
        for line_number, line in enumerate(text.splitlines(), 1):
            if not _ROW_RE.search(line):
                continue
            for token in _BACKTICK_RE.findall(line):
                if not _IDENTIFIER_RE.fullmatch(token):
                    continue
                if token in known or token in NON_CATALOGUE_IDENTIFIERS:
                    continue
                failures.append(f"{path.name}:{line_number}: {token}")
    return tuple(failures)


def mathlib_module_index(mathlib_root: Path) -> frozenset[str]:
    """Return every module and module directory in a Mathlib checkout.

    A directory counts because a navigation hint is allowed to point at a
    subtree (``Data.Finset``) rather than a single file.
    """
    root = Path(mathlib_root)
    library = root / "Mathlib"
    if not library.is_dir():
        raise FileNotFoundError(
            f"no Mathlib library under {root}; run `lake exe cache get` in lean/"
        )
    names: set[str] = {"Mathlib"}
    for path in library.rglob("*"):
        if path.is_dir():
            names.add(".".join(("Mathlib", *path.relative_to(library).parts)))
        elif path.suffix == ".lean":
            relative = path.relative_to(library).with_suffix("")
            names.add(".".join(("Mathlib", *relative.parts)))
    return frozenset(names)


def hand_maintained_module_cells(manuscript_dir: Path) -> tuple[str, ...]:
    """Return framework-table rows whose module column is hand-typed.

    The column names the Mathlib modules a row's Lean body imports. When it was
    authored by hand, forty-two of its seventy-one cells named a module the
    row never imported -- ``fep-023`` advertised
    ``MeasureTheory.Measure.Typeclasses.Probability`` while its body imports
    ``Mathlib.MeasureTheory.Measure.MeasureSpace`` -- because nothing recomputed
    a cell when a body narrowed or moved an import. Every cell is now the
    row's own ``imported_modules`` token, and this audit is what stops a
    literal from being typed back in.
    """

    failures: list[str] = []
    for path in manuscript_reference_files(manuscript_dir):
        for line_number, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), 1
        ):
            match = _MODULE_ROW_RE.match(line.strip())
            if match is None:
                continue
            expected = _IMPORTED_MODULES_TOKEN.format(topic=match.group("topic"))
            if match.group("modules").strip() == expected:
                continue
            failures.append(
                f"{path.name}:{line_number}: module column is hand-typed "
                f"({match.group('modules').strip()!r}); use {expected}"
            )
    return tuple(failures)


def unknown_topic_import_modules(mathlib_root: Path) -> tuple[str, ...]:
    """Return imported Mathlib modules that name nothing in the pinned library.

    The generated column is only as good as the incidence relation behind it:
    a body that imports a module a Mathlib rename removed would print a dead
    path for every reader. This checks the relation itself, over all catalogue
    topics rather than only the rows a framework chapter tabulates.
    """

    index = mathlib_module_index(mathlib_root)
    failures: list[str] = []
    for topic_id in BODIES:
        for module in topic_import_modules(topic_id):
            if not module.startswith("Mathlib"):
                continue
            if module not in index:
                failures.append(f"{topic_id}: {module}")
    return tuple(failures)
