"""Filesystem-only tests for deterministic Lean toolchain resolution."""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path

import pytest

from fep_formal.verification import _toolchain as toolchain


def test_toolchain_pin_rejects_missing_and_non_utf8_files(tmp_path: Path) -> None:
    assert toolchain.read_toolchain_pin(tmp_path) is None

    (tmp_path / "lean-toolchain").write_bytes(b"\xff")
    assert toolchain.read_toolchain_pin(tmp_path) is None


def test_mathlib_tag_requires_exactly_one_canonical_dependency(tmp_path: Path) -> None:
    assert toolchain.read_mathlib_tag(tmp_path) is None

    first = (
        "require mathlib from git "
        '"https://github.com/leanprover-community/mathlib4.git" @ "v4.19.0"'
    )
    duplicate = (
        "require duplicate from git "
        '"https://github.com/leanprover-community/mathlib4.git" @ "v4.19.0"'
    )
    (tmp_path / "lakefile.lean").write_text(
        f"{first}\n{duplicate}",
        encoding="utf-8",
    )
    assert toolchain.read_mathlib_tag(tmp_path) is None


@pytest.mark.parametrize(
    "payload",
    (
        {"packages": {}},
        {
            "packages": [
                {"name": "mathlib", "rev": "a" * 40},
                {"name": "mathlib", "rev": "b" * 40},
            ]
        },
        {"packages": [{"name": "mathlib", "rev": 42}]},
        {"packages": [{"name": "mathlib", "rev": "not-a-revision"}]},
    ),
)
def test_mathlib_revision_rejects_ambiguous_or_malformed_manifests(
    tmp_path: Path,
    payload: object,
) -> None:
    (tmp_path / "lake-manifest.json").write_text(
        json.dumps(payload),
        encoding="utf-8",
    )

    assert toolchain.resolved_mathlib_revision(tmp_path) == ""


def test_writable_elan_home_honors_an_explicit_override(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selected = tmp_path / "isolated-elan"
    monkeypatch.setenv("ELAN_HOME", str(selected))

    assert toolchain.get_writable_elan_home() == str(selected)


def test_toolchain_name_is_absent_without_a_valid_pin(tmp_path: Path) -> None:
    assert toolchain.read_toolchain_name(tmp_path) is None


def test_toolchain_bin_returns_none_when_elan_home_is_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ELAN_HOME", str(tmp_path / "missing-elan"))

    assert toolchain.find_toolchain_bin() is None


def test_toolchain_bin_handles_an_unreadable_toolchains_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    elan_home = tmp_path / "elan"
    toolchains = elan_home / "toolchains"
    toolchains.mkdir(parents=True)
    monkeypatch.setenv("ELAN_HOME", str(elan_home))
    real_is_dir = Path.is_dir

    def unreadable(path: Path) -> bool:
        if path == toolchains:
            raise OSError("injected directory read failure")
        return real_is_dir(path)

    monkeypatch.setattr(Path, "is_dir", unreadable)

    assert toolchain.find_toolchain_bin() is None


def test_toolchain_bin_falls_closed_when_pinned_candidate_cannot_be_statted(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    elan_home = tmp_path / "elan"
    toolchains = elan_home / "toolchains"
    candidate = toolchains / "leanprover--lean4---v4.19.0" / "bin"
    candidate.mkdir(parents=True)
    lean_dir = tmp_path / "lean"
    lean_dir.mkdir()
    (lean_dir / "lean-toolchain").write_text(
        "leanprover/lean4:v4.19.0\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("ELAN_HOME", str(elan_home))
    real_is_dir = Path.is_dir

    def fail_candidate(path: Path) -> bool:
        if path == candidate:
            raise OSError("injected candidate stat failure")
        return real_is_dir(path)

    monkeypatch.setattr(Path, "is_dir", fail_candidate)

    assert toolchain.find_toolchain_bin(lean_dir) is None


def test_toolchain_bin_handles_directory_enumeration_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    elan_home = tmp_path / "elan"
    toolchains = elan_home / "toolchains"
    toolchains.mkdir(parents=True)
    monkeypatch.setenv("ELAN_HOME", str(elan_home))
    real_iterdir = Path.iterdir

    def fail_enumeration(path: Path) -> Iterator[Path]:
        if path == toolchains:
            raise OSError("injected enumeration failure")
        return real_iterdir(path)

    monkeypatch.setattr(Path, "iterdir", fail_enumeration)

    assert toolchain.find_toolchain_bin() is None


def test_explicit_toolchain_executable_must_be_a_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("FEP_FORMAL_LEAN_EXE", str(tmp_path / "missing-lean"))

    assert toolchain.find_executable("lean") is None


def test_executable_resolution_uses_path_before_the_elan_proxy(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path_lean = tmp_path / "path-lean"
    path_lean.write_bytes(b"binary")
    monkeypatch.delenv("FEP_FORMAL_LEAN_EXE", raising=False)
    monkeypatch.setattr(toolchain, "find_toolchain_bin", lambda _lean_dir=None: None)
    monkeypatch.setattr(toolchain.shutil, "which", lambda _name: str(path_lean))

    assert toolchain.find_executable("lean") == str(path_lean)


def test_executable_resolution_falls_back_to_an_existing_elan_proxy(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    elan_home = tmp_path / "elan"
    proxy = elan_home / "bin" / "lake"
    proxy.parent.mkdir(parents=True)
    proxy.write_bytes(b"binary")
    monkeypatch.setenv("ELAN_HOME", str(elan_home))
    monkeypatch.delenv("FEP_FORMAL_LAKE_EXE", raising=False)
    monkeypatch.setattr(toolchain, "find_toolchain_bin", lambda _lean_dir=None: None)
    monkeypatch.setattr(toolchain.shutil, "which", lambda _name: None)

    assert toolchain.find_executable("lake") == str(proxy)
