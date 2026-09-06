"""Manuscript theorem identifiers resolve to canonical Lean declarations."""

from __future__ import annotations

from pathlib import Path

from fep_lean.catalogue.references import (
    mathlib_module_index,
    unknown_mathlib_navigation_hints,
    unresolved_manuscript_references,
)
from fep_lean.formal.declarations import composed_theorem_declarations

PROJ = Path(__file__).resolve().parent.parent
MATHLIB = PROJ / "lean" / ".lake" / "packages" / "mathlib"


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


def test_mathlib_module_index_sees_files_and_directories() -> None:
    index = mathlib_module_index(MATHLIB)
    # A single module, and a directory a hint is allowed to point at.
    assert "Mathlib.Data.Matrix.Mul" in index
    assert "Mathlib.Data.Finset" in index
    assert "Mathlib.Analysis.Calculus.Deriv.Monotone" not in index


def test_every_navigation_hint_names_something_in_the_pinned_mathlib() -> None:
    assert unknown_mathlib_navigation_hints(PROJ / "manuscript", MATHLIB) == ()


def test_navigation_hint_audit_catches_a_renamed_module(tmp_path: Path) -> None:
    """The audit must fail on the exact hints that shipped in the audited PDF."""
    source = PROJ / "manuscript" / "04d_framework_thermodynamics.md"
    stale = tmp_path / source.name
    body = source.read_text(encoding="utf-8")
    assert "`Data.Matrix.Mul`" in body
    stale.write_text(
        body.replace("`Data.Matrix.Mul`", "`LinearAlgebra.Matrix.Multiplication`"),
        encoding="utf-8",
    )
    defects = unknown_mathlib_navigation_hints(tmp_path, MATHLIB)
    assert len(defects) == 1
    assert defects[0].endswith("Mathlib.LinearAlgebra.Matrix.Multiplication")


def test_mathlib_module_index_refuses_a_checkout_without_the_library(
    tmp_path: Path,
) -> None:
    try:
        mathlib_module_index(tmp_path)
    except FileNotFoundError as error:
        assert "lake exe cache get" in str(error)
    else:  # pragma: no cover - the audit must never pass on an absent library
        raise AssertionError("an absent Mathlib library must not index as empty")
