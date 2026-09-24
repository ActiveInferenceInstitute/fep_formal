"""Offline tests for the orphan formal-module compile gate.

The script is loaded from ``docs/`` via the importlib-spec pattern used by
``tests/test_docs_audits.py`` and ``tests/test_citation_audit.py``. All
fixtures are synthetic trees, so the suite never invokes lake.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _load_script() -> ModuleType:
    """Load ``docs/check_orphan_compiles.py`` as a fresh module."""
    spec = importlib.util.spec_from_file_location(
        "check_orphan_compiles",
        PROJECT_ROOT / "docs" / "check_orphan_compiles.py",
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write_module(root: Path, resource: str, imports: tuple[str, ...] = ()) -> Path:
    """Write one canonical formal module with the given import lines."""
    path = root / "src" / "fep_lean" / "formal" / resource
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(f"import {name}\n" for name in imports), encoding="utf-8")
    return path


def _write_fep_all(root: Path, imports: tuple[str, ...]) -> None:
    """Write the generated aggregate with the given import lines."""
    path = root / "lean" / "FepSketches" / "fep_all.lean"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(f"import {name}\n" for name in imports), encoding="utf-8")


def _incident_fixture(root: Path) -> None:
    """The b5e6a9d/b85cfe0 shape: topic -> foundation chain plus orphans.

    ``posterior_convergence`` imports ``finite_posterior_learning`` (itself
    an orphan) which imports the manifested ``finite_probability``; nothing
    reachable from ``fep_all`` imports either of them, so both are orphans.
    """
    _write_fep_all(root, ("FepSketches.measure_bayes",))
    _write_module(
        root,
        "measure_bayes.lean",
        ("Mathlib.MeasureTheory.Measure.Probability", "FepSketches.finite_probability"),
    )
    _write_module(root, "finite_probability.lean", ("Mathlib.Tactic",))
    _write_module(
        root,
        "finite_posterior_learning.lean",
        ("FepSketches.finite_probability",),
    )
    _write_module(
        root,
        "posterior_convergence.lean",
        (
            "FepSketches.finite_posterior_learning",
            "Mathlib.Probability.Distributions.Gaussian.Fernique",
        ),
    )
    _write_module(root, "unrelated.lean")


def test_incident_shape_enumerates_posterior_convergence(tmp_path: Path) -> None:
    script = _load_script()
    _incident_fixture(tmp_path)

    assert script.orphan_modules(tmp_path) == (
        "finite_posterior_learning",
        "posterior_convergence",
        "unrelated",
    )


def test_closure_follows_multi_hop_foundation_chain(tmp_path: Path) -> None:
    script = _load_script()
    _write_fep_all(tmp_path, ("FepSketches.topic",))
    _write_module(tmp_path, "topic.lean", ("FepSketches.foundation",))
    _write_module(tmp_path, "foundation.lean", ("Mathlib.Tactic",))
    _write_module(tmp_path, "orphan.lean")

    assert script.orphan_modules(tmp_path) == ("orphan",)


def test_dotted_composition_import_traverses_subdirectory(tmp_path: Path) -> None:
    script = _load_script()
    _write_fep_all(tmp_path, ("FepSketches.aggregate",))
    _write_module(tmp_path, "aggregate.lean", ("FepSketches.compositions.core",))
    _write_module(tmp_path, "compositions/core.lean", ("FepSketches.fep_all",))
    _write_module(tmp_path, "composed.lean")

    # The compositions/fep_all cycle terminates (fep_all has no canonical
    # mirror, so it is a leaf), compositions/ is not enumerated, and the
    # top-level aggregate root plus composed.lean are classified correctly.
    assert script.orphan_modules(tmp_path) == ("composed",)


def test_main_dry_run_enumerates_without_compiling(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    script = _load_script()
    _incident_fixture(tmp_path)

    code = script.main(["--root", str(tmp_path), "--dry-run"])
    out = capsys.readouterr().out

    assert code == 0
    assert "orphaned formal modules outside fep_all's import closure: 3" in out
    assert "FepSketches.posterior_convergence" in out
    assert "FepSketches.finite_posterior_learning" in out


def test_main_compiles_every_orphan_from_lean_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    script = _load_script()
    _incident_fixture(tmp_path)
    recorded: list[tuple[Path, Path]] = []

    def fake_run(lean_dir: Path, source: Path) -> subprocess.CompletedProcess[str]:
        recorded.append((lean_dir, source))
        return subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")

    monkeypatch.setattr(script, "_lake_env_lean", fake_run)

    code = script.main(["--root", str(tmp_path)])
    out = capsys.readouterr().out

    orphans = script.orphan_modules(tmp_path)
    expected = tuple(
        (tmp_path / "lean", tmp_path / "src" / "fep_lean" / "formal" / f"{m}.lean")
        for m in orphans
    )
    assert code == 0
    assert tuple(recorded) == expected
    assert "compiled warning-free" in out


def test_lake_invocation_uses_env_lean_from_lean_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    script = _load_script()
    calls: list[tuple[tuple[object, ...], dict[str, object]]] = []

    def fake_subprocess_run(
        *args: object, **kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        calls.append((args, kwargs))
        return subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")

    monkeypatch.setattr(script.subprocess, "run", fake_subprocess_run)

    result = script._lake_env_lean(tmp_path / "lean", tmp_path / "x.lean")

    assert result.returncode == 0
    argv, kwargs = calls[0]
    assert argv[0] == ["lake", "env", "lean", str(tmp_path / "x.lean")]
    assert kwargs["cwd"] == tmp_path / "lean"


def test_main_fails_closed_on_compile_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    script = _load_script()
    _incident_fixture(tmp_path)

    def fake_run(lean_dir: Path, source: Path) -> subprocess.CompletedProcess[str]:
        failing = "posterior_convergence" in str(source)
        return subprocess.CompletedProcess(
            args=[],
            returncode=1 if failing else 0,
            stdout="error: unknown identifier 'ProbabilityMeasure'\n"
            if failing
            else "",
            stderr="",
        )

    monkeypatch.setattr(script, "_lake_env_lean", fake_run)

    code = script.main(["--root", str(tmp_path)])
    out = capsys.readouterr().out

    assert code == 1
    assert "FAIL FepSketches.posterior_convergence" in out
    assert "1 of 3 orphaned formal module(s) failed to compile" in out
    assert "unknown identifier 'ProbabilityMeasure'" in out


def test_main_fails_closed_on_warning(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    script = _load_script()
    _incident_fixture(tmp_path)

    def fake_run(lean_dir: Path, source: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=[], returncode=0, stdout="warning: unused variable\n", stderr=""
        )

    monkeypatch.setattr(script, "_lake_env_lean", fake_run)

    code = script.main(["--root", str(tmp_path)])
    out = capsys.readouterr().out

    assert code == 1
    assert "3 of 3 orphaned formal module(s) failed to compile" in out


def test_main_fails_closed_without_fep_all(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    script = _load_script()
    (tmp_path / "src" / "fep_lean" / "formal").mkdir(parents=True)

    code = script.main(["--root", str(tmp_path)])
    captured = capsys.readouterr()

    assert code == 1
    assert "fep_all aggregate not found" in captured.err
