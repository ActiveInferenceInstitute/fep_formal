"""Canonical declaration inventory and manuscript reference audit."""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from dataclasses import fields
from pathlib import Path

from fep_lean.lean_source import lean_code_without_comments

from .coverage import topic_import_modules
from .registry import BODIES
from .topics import TopicEntry

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
# one of its declarations. The set is split by provenance, and every group is
# checked against its own source by :func:`unverified_non_catalogue_identifiers`
# rather than asserted in a comment. A comment is what let
# ``min_agrees_on_value`` sit in this set for two releases labelled "Mathlib
# declarations cited as prior art": no such Mathlib name exists, and the
# manuscript was printing this catalogue's own ``fep008_min_agrees_on_value``
# stripped of its prefix, between two real Mathlib names, so it read as prior
# art. A new unresolved name fails the audit rather than joining a group
# silently, and a name that joins a group it cannot be verified against fails
# the audit too.

#: Names the pinned Mathlib checkout introduces -- as a declaration header, or
#: as the quoted token of a tactic or syntax construct (``norm_num``). Verified
#: against ``lean/.lake/packages/mathlib``.
MATHLIB_CITED_NAMES = frozenset(
    {
        "CondIndep",
        "CondIndepFun",
        "ENNReal",
        "SigmaFinite",
        "klDiv_compProd_eq_add",
        "le_antisymm",
        "measure_union_le",
        "norm_num",
        "sq_nonneg",
    }
)
#: Names declared by this repository's own maintained Lean modules -- neither
#: Mathlib nor a catalogue topic body. Verified against ``src/fep_lean/formal``.
LOCAL_FORMAL_CITED_NAMES = frozenset({"FullSupport"})
#: Per-topic catalogue record fields, named where the prose explains what a
#: generated column reports. Verified against
#: :class:`fep_lean.catalogue.topics.TopicEntry`.
CATALOGUE_RECORD_FIELDS = frozenset(
    {
        "acceptance_probe",
        "assumption_review",
        "latex_equations",
        "lean_sketch",
        "mathlib_status",
        "non_vacuity",
        "primary_theorem",
        "semantic_disposition",
    }
)
NON_CATALOGUE_IDENTIFIERS = (
    MATHLIB_CITED_NAMES | LOCAL_FORMAL_CITED_NAMES | CATALOGUE_RECORD_FIELDS
)
# Lean introduces a name two ways, and prose cites both. A declaration header
# carries its name directly; a ``syntax``/``elab``/``macro`` construct carries
# an internal ``(name := ...)`` and a user-facing quoted token, which is how
# ``norm_num`` exists without a declaration header of that name. The window is
# generous because Mathlib routinely breaks the construct across lines.
_LEAN_DECLARATION_RE = re.compile(
    r"^[ \t]*(?:@\[[^\]]*\][ \t]*)?"
    r"(?:(?:protected|private|scoped|local|noncomputable|nonrec|partial|unsafe)[ \t]+)*"
    r"(?:theorem|lemma|def|abbrev|structure|inductive|class|instance|opaque|axiom)"
    r"[ \t]+([A-Za-z_][A-Za-z0-9_']*)",
    re.MULTILINE,
)
_LEAN_SYNTAX_RE = re.compile(
    r"^[ \t]*(?:@\[[^\]]*\][ \t]*)?(?:(?:scoped|local)[ \t]+)*(?:syntax|elab|macro)\b",
    re.MULTILINE,
)
_LEAN_SYNTAX_NAME_RE = re.compile(r"\(\s*name\s*:=\s*([A-Za-z_][A-Za-z0-9_'.]*)\s*\)")
_LEAN_SYNTAX_TOKEN_RE = re.compile(r"\"\s*([A-Za-z_][A-Za-z0-9_']*)\s*\"")
_SYNTAX_WINDOW = 200
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


def lean_names_introduced(lean_root: Path) -> frozenset[str]:
    """Return every name a Lean source tree introduces.

    Two forms count, because both are cited in prose. A declaration header
    (``theorem``/``def``/``class``/...) introduces its name directly. A
    ``syntax``/``elab``/``macro`` construct introduces an internal name via
    ``(name := ...)`` and a user-facing token via its quoted literal. Mathlib's
    ``norm_num`` reaches a reader through both of the second kind and neither
    of the first: ``syntax (name := norm_num) "norm_num " term,+ : attr``
    names the attribute, and ``elab (name := normNum) "norm_num" ... : tactic``
    names the tactic, while no ``theorem``/``def`` header carries the name at
    all. A header-only scan would report the pinned library does not have it.
    """

    root = Path(lean_root)
    if not root.is_dir():
        raise FileNotFoundError(f"no Lean sources under {root}")
    names: set[str] = set()
    for path in sorted(root.rglob("*.lean")):
        text = path.read_text(encoding="utf-8", errors="replace")
        names.update(_LEAN_DECLARATION_RE.findall(text))
        for match in _LEAN_SYNTAX_RE.finditer(text):
            window = text[match.end() : match.end() + _SYNTAX_WINDOW]
            names.update(_LEAN_SYNTAX_NAME_RE.findall(window))
            names.update(_LEAN_SYNTAX_TOKEN_RE.findall(window))
    return frozenset(names)


def unverified_non_catalogue_identifiers(
    mathlib_root: Path | None = None,
    *,
    formal_root: Path | None = None,
) -> tuple[str, ...]:
    """Return allowlisted identifiers their claimed source does not contain.

    :data:`NON_CATALOGUE_IDENTIFIERS` is the one place this audit is told to
    look past a name. Each group names where its members come from; this checks
    the claim. ``mathlib_root`` may be ``None`` when the pinned checkout is
    absent (``lean/.lake`` is a build artifact), in which case the Mathlib group
    is reported as unchecked rather than silently passed.
    """

    failures: list[str] = []
    if mathlib_root is None:
        failures.extend(
            f"MATHLIB_CITED_NAMES: {name}: unchecked, the pinned Mathlib "
            "checkout is absent; run `lake exe cache get` in lean/"
            for name in sorted(MATHLIB_CITED_NAMES)
        )
    else:
        mathlib_names = lean_names_introduced(Path(mathlib_root) / "Mathlib")
        failures.extend(
            f"MATHLIB_CITED_NAMES: {name}: the pinned Mathlib checkout "
            "introduces no such name"
            for name in sorted(MATHLIB_CITED_NAMES - mathlib_names)
        )
    root = (
        Path(formal_root)
        if formal_root is not None
        else Path(__file__).resolve().parents[1] / "formal"
    )
    local_names = lean_names_introduced(root)
    failures.extend(
        f"LOCAL_FORMAL_CITED_NAMES: {name}: no declaration under {root.name}/"
        for name in sorted(LOCAL_FORMAL_CITED_NAMES - local_names)
    )
    record_fields = frozenset(field.name for field in fields(TopicEntry)) | frozenset(
        name for name, value in vars(TopicEntry).items() if isinstance(value, property)
    )
    failures.extend(
        f"CATALOGUE_RECORD_FIELDS: {name}: TopicEntry has no such field"
        for name in sorted(CATALOGUE_RECORD_FIELDS - record_fields)
    )
    return tuple(failures)
