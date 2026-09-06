"""Manuscript theorem identifiers and module columns resolve to real Lean."""

from __future__ import annotations

from pathlib import Path

import pytest

from fep_lean.catalogue.coverage import (
    render_topic_import_modules,
    topic_import_modules,
)
from fep_lean.catalogue.references import (
    hand_maintained_module_cells,
    mathlib_module_index,
    unknown_topic_import_modules,
    unresolved_manuscript_references,
)
from fep_lean.formal.declarations import composed_theorem_declarations

PROJ = Path(__file__).resolve().parent.parent
MATHLIB = PROJ / "lean" / ".lake" / "packages" / "mathlib"
# ``lean/.lake`` is a build artifact, absent from a fresh checkout until
# ``lake exe cache get`` runs. Tests that index the pinned library say so
# rather than failing where the library was never fetched.
requires_mathlib = pytest.mark.skipif(
    not (MATHLIB / "Mathlib").is_dir(),
    reason="pinned Mathlib checkout absent; run `lake exe cache get` in lean/",
)


def test_all_fep_declaration_references_resolve() -> None:
    composed = {
        declaration.rsplit(".", 1)[-1]
        for declaration in composed_theorem_declarations()
    }
    assert (
        unresolved_manuscript_references(
            PROJ / "manuscript", additional_declarations=composed
        )
        == ()
    )


@requires_mathlib
def test_mathlib_module_index_sees_files_and_directories() -> None:
    index = mathlib_module_index(MATHLIB)
    # A single module, and a directory a hint is allowed to point at.
    assert "Mathlib.Data.Matrix.Mul" in index
    assert "Mathlib.Data.Finset" in index
    assert "Mathlib.Analysis.Calculus.Deriv.Monotone" not in index


@requires_mathlib
def test_every_imported_module_exists_in_the_pinned_mathlib() -> None:
    assert unknown_topic_import_modules(MATHLIB) == ()


@requires_mathlib
def test_import_audit_catches_a_module_a_rename_removed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A body importing a renamed-away module must fail, not print a dead path."""
    from fep_lean.catalogue import references

    monkeypatch.setattr(
        references,
        "topic_import_modules",
        lambda topic_id: (
            ("Mathlib.LinearAlgebra.Matrix.Multiplication",)
            if topic_id == "fep-047"
            else ()
        ),
    )
    defects = unknown_topic_import_modules(MATHLIB)
    assert defects == ("fep-047: Mathlib.LinearAlgebra.Matrix.Multiplication",)


def test_no_framework_table_cell_names_a_hand_typed_module() -> None:
    assert hand_maintained_module_cells(PROJ / "manuscript") == ()


def test_hand_typed_module_cell_is_rejected(tmp_path: Path) -> None:
    """The exact drift that shipped: a literal where the token belongs."""
    source = PROJ / "manuscript" / "04b_framework_active_inference.md"
    body = source.read_text(encoding="utf-8")
    token = "{{topics.fep-023.imported_modules}}"
    assert token in body
    stale = tmp_path / source.name
    stale.write_text(
        body.replace(token, "`MeasureTheory.Measure.Typeclasses.Probability`", 1),
        encoding="utf-8",
    )
    defects = hand_maintained_module_cells(tmp_path)
    assert len(defects) == 1
    assert "module column is hand-typed" in defects[0]
    assert "{{topics.fep-023.imported_modules}}" in defects[0]


def test_every_tabulated_row_prints_the_modules_its_body_imports() -> None:
    """The incidence relation, not a hint: fep-023's cell is its own import."""
    assert topic_import_modules("fep-023") == (
        "Mathlib.MeasureTheory.Measure.MeasureSpace",
    )
    assert (
        render_topic_import_modules(topic_import_modules("fep-023"))
        == "`MeasureTheory.Measure.MeasureSpace`"
    )
    assert render_topic_import_modules(()) == "---"
    assert (
        render_topic_import_modules(("FepSketches.native_blanket",))
        == "`FepSketches.native_blanket`"
    )


def test_mathlib_module_index_refuses_a_checkout_without_the_library(
    tmp_path: Path,
) -> None:
    try:
        mathlib_module_index(tmp_path)
    except FileNotFoundError as error:
        assert "lake exe cache get" in str(error)
    else:  # pragma: no cover - the audit must never pass on an absent library
        raise AssertionError("an absent Mathlib library must not index as empty")
