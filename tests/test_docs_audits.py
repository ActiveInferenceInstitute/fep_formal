"""Docs-audit script gates: check_links, md_hygiene, xref_audit, theorem_ref_audit.

Each script is loaded from ``docs/`` via the importlib-spec pattern used by
``tests/test_pin_audit_latest.py``. ``check_links`` and ``md_hygiene`` scan
``DOCS_DIR`` (a module global derived from ``__file__``) and expose no root
flag, so each test redirects that single global to a tmp fixture tree.
``xref_audit`` takes ``--root`` and needs no redirection. ``theorem_ref_audit``
derives its root inline from ``__file__``, so redirecting it means patching
that one module attribute; its canonical-name surfaces are read from packaged
repo data, keeping the fixtures fully offline.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _load_docs_script(stem: str) -> ModuleType:
    """Load ``docs/<stem>.py`` as a fresh module (importlib-spec pattern)."""
    spec = importlib.util.spec_from_file_location(
        f"docs_{stem}", PROJECT_ROOT / "docs" / f"{stem}.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _run_script(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    stem: str,
    argv: list[str],
    *,
    redirect_root_from_docs_dir: bool = False,
    redirect_root_from_file: bool = False,
) -> tuple[int, str]:
    """Run a loaded docs script's ``main`` against a tmp fixture tree."""
    module = _load_docs_script(stem)
    if redirect_root_from_docs_dir:
        # The default scan root is the module-global DOCS_DIR; one global.
        monkeypatch.setattr(module, "DOCS_DIR", tmp_path)
    if redirect_root_from_file:
        # main() derives the repo root inline from __file__ (no separate
        # constant); repointing that single attribute redirects the scan.
        monkeypatch.setattr(module, "__file__", str(tmp_path / "docs" / f"{stem}.py"))
    monkeypatch.setattr(sys, "argv", [stem, *argv])
    code: int = module.main()
    return code, capsys.readouterr().out


def test_check_links_flags_broken_internal_link(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    (tmp_path / "index.md").write_text(
        "# Index\n\n[missing](nowhere.md)\n", encoding="utf-8"
    )
    code, out = _run_script(
        tmp_path,
        monkeypatch,
        capsys,
        "check_links",
        [],
        redirect_root_from_docs_dir=True,
    )

    assert code == 1
    assert "broken link" in out
    assert "nowhere.md" in out


def test_check_links_passes_clean_fixture_tree(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    (tmp_path / "index.md").write_text(
        "# Index\n\n[see](target.md)\n", encoding="utf-8"
    )
    (tmp_path / "target.md").write_text("# Target\n", encoding="utf-8")
    code, out = _run_script(
        tmp_path,
        monkeypatch,
        capsys,
        "check_links",
        [],
        redirect_root_from_docs_dir=True,
    )

    assert code == 0
    assert "no broken links" in out


def test_md_hygiene_flags_missing_trailing_newline(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    (tmp_path / "note.md").write_text("# Title\n\n- item", encoding="utf-8")
    code, out = _run_script(
        tmp_path,
        monkeypatch,
        capsys,
        "md_hygiene",
        [],
        redirect_root_from_docs_dir=True,
    )

    assert code == 1
    assert "does not end with a newline" in out


def test_md_hygiene_passes_clean_fixture_tree(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    (tmp_path / "note.md").write_text("# Title\n\n- item\n", encoding="utf-8")
    code, out = _run_script(
        tmp_path,
        monkeypatch,
        capsys,
        "md_hygiene",
        [],
        redirect_root_from_docs_dir=True,
    )

    assert code == 0
    assert "no hygiene issues" in out


def test_xref_audit_flags_unresolved_crossref(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = tmp_path / "manuscript"
    root.mkdir()
    (root / "chapter.md").write_text(
        "# Chapter\n\nSee [@sec:ghost].\n", encoding="utf-8"
    )
    code, out = _run_script(
        tmp_path, monkeypatch, capsys, "xref_audit", ["--root", str(root)]
    )

    assert code == 1
    assert "unresolved" in out
    assert "sec:ghost" in out


def test_xref_audit_passes_resolved_crossref(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = tmp_path / "manuscript"
    root.mkdir()
    (root / "chapter.md").write_text(
        "# Chapter\n\nSee [@sec:intro].\n\n## Intro {#sec:intro}\n",
        encoding="utf-8",
    )
    code, out = _run_script(
        tmp_path, monkeypatch, capsys, "xref_audit", ["--root", str(root)]
    )

    assert code == 0
    assert "all resolve" in out


def test_theorem_ref_audit_flags_unresolvable_manuscript_name(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    (manuscript / "chapter.md").write_text(
        "# Chapter\n\nTheorem fep999_absent_theorem states the claim.\n",
        encoding="utf-8",
    )
    code, out = _run_script(
        tmp_path,
        monkeypatch,
        capsys,
        "theorem_ref_audit",
        [],
        redirect_root_from_file=True,
    )

    assert code == 1
    assert "fep999_absent_theorem" in out
    assert "FAIL" in out


def test_theorem_ref_audit_passes_manuscript_without_references(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    (manuscript / "chapter.md").write_text(
        "# Chapter\n\nNo canonical declaration references here.\n",
        encoding="utf-8",
    )
    code, out = _run_script(
        tmp_path,
        monkeypatch,
        capsys,
        "theorem_ref_audit",
        [],
        redirect_root_from_file=True,
    )

    assert code == 0
    assert "references resolve" in out
