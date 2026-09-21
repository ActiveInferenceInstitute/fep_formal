"""Manuscript theorem identifiers and module columns resolve to real Lean."""

from __future__ import annotations

from pathlib import Path

import pytest

from fep_lean.catalogue.coverage import (
    render_topic_import_modules,
    topic_import_modules,
)
from fep_lean.catalogue.references import (
    MATHLIB_CITED_NAMES,
    hand_maintained_module_cells,
    lean_names_introduced,
    mathlib_module_index,
    miscounted_area_labels,
    unattributed_row_declarations,
    unknown_topic_import_modules,
    unresolved_manuscript_references,
    unverified_non_catalogue_identifiers,
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


def test_no_area_row_count_is_labelled_a_declaration_count() -> None:
    assert miscounted_area_labels(PROJ / "manuscript") == ()


def test_area_row_count_labelled_theorems_is_rejected(tmp_path: Path) -> None:
    """The exact drift that shipped in the PDF: rows printed as theorems."""
    stale = tmp_path / "04c_framework_sophisticated_dynamics.md"
    stale.write_text(
        "**The {{areas.InfoGeometry.count}} Information Geometry theorems** "
        "establish the substrate:\n",
        encoding="utf-8",
    )
    defects = miscounted_area_labels(tmp_path)
    assert len(defects) == 1
    assert "counts catalogue rows but is labelled 'theorems'" in defects[0]
    assert "{{areas.InfoGeometry.count}}" in defects[0]


def test_area_row_count_labelled_rows_is_accepted(tmp_path: Path) -> None:
    """A row noun clears the audit, and so does a heading that names topics."""
    clean = tmp_path / "04c_framework_sophisticated_dynamics.md"
    clean.write_text(
        "**The {{areas.InfoGeometry.count}} Information Geometry rows** "
        "establish the substrate, proving many theorems.\n"
        "### Results ({{areas.BayesianMechanics.count}} topics)\n"
        "| Information Geometry | {{areas.InfoGeometry.count}} | rate |\n",
        encoding="utf-8",
    )
    assert miscounted_area_labels(tmp_path) == ()


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
        "Mathlib.MeasureTheory.Measure.Typeclasses.Probability",
    )
    assert (
        render_topic_import_modules(topic_import_modules("fep-023"))
        == "`MeasureTheory.Measure.Typeclasses.Probability`"
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


@requires_mathlib
def test_every_allowlisted_identifier_exists_in_its_claimed_source() -> None:
    """The reference audits' one blind spot is checked, not asserted in prose."""
    assert unverified_non_catalogue_identifiers(MATHLIB) == ()


@requires_mathlib
def test_lean_name_index_sees_declarations_and_tactic_tokens() -> None:
    names = lean_names_introduced(MATHLIB / "Mathlib")
    # A declaration header, and a tactic whose only name is a quoted token in
    # ``elab (name := normNum) "norm_num" ... : tactic``.
    assert "klDiv_compProd_eq_add" in names
    assert "norm_num" in names
    # The name that shipped as Mathlib prior art. It is this catalogue's own.
    assert "min_agrees_on_value" not in names


@requires_mathlib
def test_a_catalogue_row_cannot_pass_as_mathlib_prior_art(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The exact drift that shipped: fep-008's own theorem, prefix stripped."""
    from fep_lean.catalogue import references

    monkeypatch.setattr(
        references,
        "MATHLIB_CITED_NAMES",
        MATHLIB_CITED_NAMES | {"min_agrees_on_value"},
    )
    defects = unverified_non_catalogue_identifiers(MATHLIB)
    expected = (
        "MATHLIB_CITED_NAMES: min_agrees_on_value: "
        "the pinned Mathlib checkout introduces no such name"
    )
    assert defects == (expected,)


def test_an_absent_mathlib_is_reported_unchecked_not_passed() -> None:
    """No pinned library means no verification, and the audit must say so."""
    defects = unverified_non_catalogue_identifiers(None)
    assert len(defects) == len(MATHLIB_CITED_NAMES)
    assert all("unchecked" in defect for defect in defects)


def test_local_and_record_groups_are_checked_without_mathlib() -> None:
    """``FullSupport`` and the record fields resolve off the pinned library."""
    defects = unverified_non_catalogue_identifiers(None)
    assert not any(
        defect.startswith(("LOCAL_FORMAL_CITED_NAMES", "CATALOGUE_RECORD_FIELDS"))
        for defect in defects
    )


def test_fep008_prose_names_the_row_not_a_bare_lemma() -> None:
    """fep-008's proof paragraph must not print a catalogue name as Mathlib's."""
    prose = (PROJ / "manuscript" / "04b_framework_active_inference.md").read_text(
        encoding="utf-8"
    )
    assert "`fep008_min_agrees_on_value`" in prose
    assert "`min_agrees_on_value`" not in prose


def test_a_known_declaration_beside_its_row_passes(tmp_path: Path) -> None:
    """The strongest claim the prose makes: a real catalogue name, quoted."""
    (tmp_path / "01_rows.md").write_text(
        "# Rows\n\nRow fep-008 proves `fep008_min_is_lb`.\n",
        encoding="utf-8",
    )
    assert unattributed_row_declarations(tmp_path) == ()


def test_an_unattributed_row_declaration_is_rejected(tmp_path: Path) -> None:
    """The shipped drift: the row's own theorem with the prefix stripped."""
    (tmp_path / "01_rows.md").write_text(
        "# Rows\n\nRow fep-008 proves `min_is_lb` via `PhantomLemma`.\n",
        encoding="utf-8",
    )
    assert unattributed_row_declarations(tmp_path) == (
        "01_rows.md:3: min_is_lb",
        "01_rows.md:3: PhantomLemma",
    )


def test_reviewed_non_catalogue_identifiers_clear_the_row_audit(
    tmp_path: Path,
) -> None:
    """Mathlib, local-formal, and record-field names beside a row pass."""
    (tmp_path / "01_rows.md").write_text(
        "# Rows\n\n"
        "Row fep-001 leans on `sq_nonneg` and `FullSupport`; its record "
        "field is `lean_sketch`.\n",
        encoding="utf-8",
    )
    assert unattributed_row_declarations(tmp_path) == ()


def test_additional_declarations_extend_the_known_set(tmp_path: Path) -> None:
    """An out-of-band name passes only once it is declared additionally."""
    (tmp_path / "01_rows.md").write_text(
        "# Rows\n\nRow fep-042 composes `new_lemma_name`.\n",
        encoding="utf-8",
    )
    assert unattributed_row_declarations(tmp_path) == ("01_rows.md:3: new_lemma_name",)
    assert (
        unattributed_row_declarations(
            tmp_path, additional_declarations=("new_lemma_name",)
        )
        == ()
    )
