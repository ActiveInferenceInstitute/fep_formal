"""Capability failure cases using real temporary files and executables."""

from pathlib import Path

from fep_lean.catalogue.topics import FEPTopicCatalogue
from fep_lean.verification.environment import (
    _check_catalogue_import,
    _check_dirs,
    _check_lake,
    _check_lean_cli,
    _check_lean_workspace,
    _check_mathlib_built,
    _check_output_writable,
    _check_python_numpy_matplotlib,
    _check_references_bib,
    _check_toolchain_pin,
    _check_topics_yaml,
    _find_toolchain_lean,
)

PROJ = Path(__file__).resolve().parent.parent


def _write_toolchain_fixture(root: Path, version: str) -> None:
    lean = root / "lean"
    lean.mkdir()
    (lean / "lean-toolchain").write_text(
        f"leanprover/lean4:v{version}\n", encoding="utf-8"
    )
    (lean / "lakefile.lean").write_text(
        'require mathlib from git\n  "https://github.com/leanprover-community/mathlib4.git" '
        f'@ "v{version}"\n',
        encoding="utf-8",
    )


def test_toolchain_pin_check_follows_the_checkout_sources(tmp_path: Path) -> None:
    _write_toolchain_fixture(tmp_path, "9.8.7")

    ok, message = _check_toolchain_pin(tmp_path)

    assert ok
    assert "leanprover/lean4:v9.8.7" in message
    assert "Mathlib v9.8.7" in message


def test_cli_version_checks_follow_the_checkout_pin(
    monkeypatch, tmp_path: Path
) -> None:
    _write_toolchain_fixture(tmp_path, "9.8.7")
    lean_exe = tmp_path / "lean-fixture"
    lean_exe.write_text(
        "#!/bin/sh\nprintf '%s\\n' 'Lean (version 9.8.7, fixture, Release)'\n",
        encoding="utf-8",
    )
    lean_exe.chmod(0o755)
    lake_exe = tmp_path / "lake-fixture"
    lake_exe.write_text(
        "#!/bin/sh\nprintf '%s\\n' 'Lake version 5.0.0 (Lean version 9.8.7)'\n",
        encoding="utf-8",
    )
    lake_exe.chmod(0o755)
    monkeypatch.setenv("FEP_LEAN_LEAN_EXE", str(lean_exe))
    monkeypatch.setenv("FEP_LEAN_LAKE_EXE", str(lake_exe))

    assert _check_lean_cli(tmp_path)[0]
    assert _check_lake(tmp_path)[0]


def test_missing_lean_is_error(monkeypatch, tmp_path: Path) -> None:
    _write_toolchain_fixture(tmp_path, "9.8.7")
    monkeypatch.setenv("PATH", str(tmp_path))
    monkeypatch.setenv("ELAN_HOME", str(tmp_path / "elan"))
    ok, message = _check_lean_cli(tmp_path)
    assert not ok
    assert "unavailable" in message


def test_mathlib_check_is_read_only(tmp_path: Path) -> None:
    ok, message = _check_mathlib_built(tmp_path)
    assert not ok
    assert "missing" in message
    assert not (tmp_path / "lean" / ".lake").exists()


def test_missing_catalogue_is_error(tmp_path: Path) -> None:
    ok, message = _check_topics_yaml(tmp_path)
    assert not ok
    assert "cannot read" in message or "missing" in message


def test_malformed_catalogue_is_error(tmp_path: Path) -> None:
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "topics.yaml").write_text("invalid: [", encoding="utf-8")
    ok, message = _check_topics_yaml(tmp_path)
    assert not ok
    assert message


def test_layout_requires_all_directories(tmp_path: Path) -> None:
    ok, message = _check_dirs(tmp_path)
    assert not ok
    assert "missing" in message


def test_workspace_requires_tracked_aggregate(tmp_path: Path) -> None:
    (tmp_path / "lean").mkdir()
    (tmp_path / "lean" / "lakefile.lean").write_text("package fep", encoding="utf-8")
    ok, message = _check_lean_workspace(tmp_path)
    assert not ok
    assert "fep_all.lean" in message


def test_output_write_probe(tmp_path: Path) -> None:
    ok, message = _check_output_writable(tmp_path)
    assert ok
    assert "writable" in message


def test_scientific_stack_is_present() -> None:
    ok, message = _check_python_numpy_matplotlib()
    assert ok
    assert "Python" in message


def test_catalogue_import_uses_strict_loader() -> None:
    ok, message = _check_catalogue_import(PROJ)
    catalogue = FEPTopicCatalogue.from_yaml(PROJ / "config" / "topics.yaml")
    assert ok
    assert f"({len(catalogue.roster.topic_ids)} topics)" in message


def test_catalogue_import_missing_root(tmp_path: Path) -> None:
    ok, _ = _check_catalogue_import(tmp_path)
    assert not ok


def test_references_bib_is_required_and_nonempty(tmp_path: Path) -> None:
    ok, message = _check_references_bib(tmp_path)
    assert not ok
    assert "missing" in message

    manuscript = tmp_path / "docs" / "manuscript"
    manuscript.mkdir(parents=True)
    bibliography = manuscript / "references.bib"
    bibliography.write_text("\n", encoding="utf-8")
    ok, message = _check_references_bib(tmp_path)
    assert not ok
    assert "empty" in message


def test_references_bib_rejects_malformed_and_duplicate_entries(
    tmp_path: Path,
) -> None:
    manuscript = tmp_path / "docs" / "manuscript"
    manuscript.mkdir(parents=True)
    bibliography = manuscript / "references.bib"
    bibliography.write_text(
        "@article{broken,\n  title = {Unclosed title}\n",
        encoding="utf-8",
    )
    ok, message = _check_references_bib(tmp_path)
    assert not ok
    assert "unmatched opening brace" in message

    bibliography.write_text(
        "@article{same,\n  title = {First}\n}\n@book{same,\n  title = {Second}\n}\n",
        encoding="utf-8",
    )
    ok, message = _check_references_bib(tmp_path)
    assert not ok
    assert "duplicate bibliography keys: same" in message


def test_references_bib_accepts_project_bibliography() -> None:
    ok, message = _check_references_bib(PROJ)
    assert ok
    assert "unique entries" in message


def test_gauss_state_path_is_writable(monkeypatch, tmp_path: Path) -> None:
    from fep_lean.verification.environment import _check_gauss_config

    path = tmp_path / "gauss"
    monkeypatch.setenv("GAUSS_HOME", str(path))
    ok, _ = _check_gauss_config(tmp_path)
    assert ok


def test_find_toolchain_without_pin_returns_none(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("ELAN_HOME", str(tmp_path / "elan"))
    assert _find_toolchain_lean(tmp_path) is None
