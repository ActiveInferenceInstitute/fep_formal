"""Real installed-wheel migration and ownership contracts."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_identity_distribution_transition(tmp_path: Path) -> None:
    uv = shutil.which("uv")
    assert uv is not None
    env = {
        key: value
        for key, value in os.environ.items()
        if key
        not in {
            "PYTHONPATH",
            "PYTHONHOME",
            "VIRTUAL_ENV",
            "UV_PYTHON",
            "UV_PROJECT_ENVIRONMENT",
        }
        and not key.startswith(("FEP_FORMAL_", "FEP_LEAN_", "MYPY"))
    }
    counter = 0

    def run(
        *args: str, cwd: Path = tmp_path, ok: bool = True
    ) -> subprocess.CompletedProcess[str]:
        nonlocal counter
        result = subprocess.run(
            args,
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            timeout=300,
            check=False,
        )
        counter += 1
        (tmp_path / f"command-{counter:02d}.txt").write_text(
            repr(args)
            + "\nexit="
            + str(result.returncode)
            + "\nstdout:\n"
            + result.stdout
            + "\nstderr:\n"
            + result.stderr,
            encoding="utf-8",
        )
        if ok:
            assert result.returncode == 0, result.stdout + result.stderr
        return result

    def build(source: Path, name: str) -> Path:
        destination = tmp_path / name
        run(uv, "build", "--out-dir", str(destination), cwd=source)
        wheels = list(destination.glob("*.whl"))
        assert len(wheels) == 1
        return wheels[0]

    canonical = build(ROOT, "canonical")
    legacy = build(ROOT / "compat/fep-lean", "legacy")
    with zipfile.ZipFile(legacy) as archive:
        names = archive.namelist()
        assert all(".dist-info/" in name for name in names)
        metadata = archive.read(
            next(n for n in names if n.endswith("/METADATA"))
        ).decode()
        assert "Requires-Dist: fep-formal==" in metadata
        assert 'extra == "dev"' in metadata
        assert not any(n.endswith("/entry_points.txt") for n in names)
    with zipfile.ZipFile(canonical) as archive:
        names = archive.namelist()
        assert "fep_lean/__init__.py" in names
        assert "fep_lean/__init__.pyi" in names
        assert "fep_lean/py.typed" in names
        entry = archive.read(
            next(n for n in names if n.endswith("/entry_points.txt"))
        ).decode()
        assert "fep-formal = fep_formal.cli:main" in entry
        assert "fep-lean = fep_formal.cli:legacy_main" in entry

    environment = tmp_path / "venv"
    run(
        uv,
        "venv",
        "--python",
        os.environ.get("FEP_DISTRIBUTION_PYTHON", sys.executable),
        str(environment),
    )
    scripts = environment / ("Scripts" if os.name == "nt" else "bin")
    python = scripts / ("python.exe" if os.name == "nt" else "python")
    run(uv, "pip", "install", "--python", str(python), str(canonical), str(legacy))
    probe = """
import importlib, importlib.metadata as md, importlib.resources as resources
import fep_formal, fep_lean
assert fep_formal is fep_lean
for suffix in ('_paths', 'catalogue', 'catalogue.schema', 'output.evidence'):
    assert importlib.import_module('fep_formal.' + suffix) is importlib.import_module('fep_lean.' + suffix)
assert fep_formal.FepFormalError is fep_lean.FepLeanError
assert resources.files('fep_formal.data').joinpath('topics.yaml').read_bytes() == resources.files('fep_lean.data').joinpath('topics.yaml').read_bytes()
canonical = md.distribution('fep-formal')
assert all('.dist-info/' in str(f) for f in md.distribution('fep-lean').files)
assert any(str(f) == 'fep_lean/__init__.py' for f in canonical.files)
print('installed identities, resources, and ownership passed')
"""
    identity = run(str(python), "-I", "-c", probe)
    assert "FutureWarning" in identity.stderr
    formal = run(str(scripts / "fep-formal"), "--help")
    old = run(str(scripts / "fep-lean"), "--help")
    assert formal.stdout == old.stdout
    assert "deprecated" not in formal.stderr.lower()
    assert "deprecated" in old.stderr.lower()
    typing_source = tmp_path / "consumer.py"
    typing_source.write_text(
        "from fep_formal import FepFormalError\n"
        "from fep_lean import FepLeanError\n"
        "from fep_lean.catalogue import TopicEntry\n"
        "canonical: type[FepFormalError] = FepLeanError\n",
        encoding="utf-8",
    )
    typing_config = tmp_path / "mypy.ini"
    typing_config.write_text("[mypy]\n", encoding="utf-8")
    run(
        sys.executable,
        "-m",
        "mypy",
        "--config-file",
        str(typing_config),
        "--python-executable",
        str(python),
        "--follow-imports=silent",
        str(typing_source),
    )
    typing_source.write_text(
        "from fep_lean import FepLeanError\nvalue: int = FepLeanError('bad')\n",
        encoding="utf-8",
    )
    invalid = run(
        sys.executable,
        "-m",
        "mypy",
        "--config-file",
        str(typing_config),
        "--python-executable",
        str(python),
        "--follow-imports=silent",
        str(typing_source),
        ok=False,
    )
    assert invalid.returncode != 0
    assert "assignment" in invalid.stdout
    run(uv, "pip", "check", "--python", str(python))
    run(uv, "pip", "uninstall", "--python", str(python), "fep-lean")
    run(
        str(python),
        "-I",
        "-c",
        "import fep_formal, fep_lean; assert fep_formal is fep_lean",
    )
    run(str(scripts / "fep-formal"), "--help")
    run(str(scripts / "fep-lean"), "--help")
    run(uv, "pip", "install", "--python", str(python), "--no-deps", str(legacy))
    run(uv, "pip", "uninstall", "--python", str(python), "fep-formal")
    broken = run(uv, "pip", "check", "--python", str(python), ok=False)
    assert broken.returncode != 0
    assert "fep-formal" in (broken.stdout + broken.stderr)
    run(
        str(python),
        "-I",
        "-c",
        "import importlib.util; assert importlib.util.find_spec('fep_formal') is None; assert importlib.util.find_spec('fep_lean') is None",
    )
    assert not (scripts / "fep-formal").exists()
    assert not (scripts / "fep-lean").exists()

    # Upgrade from the actual retained pre-cutover source, never a fake wheel.
    baseline = tmp_path / "baseline"
    baseline.mkdir()
    archive = tmp_path / "baseline.tar"
    run(
        "git",
        "archive",
        "--format=tar",
        "--output",
        str(archive),
        "7dcc30bc54d00988f3daa420d72f76e38be134b0",
        cwd=ROOT,
    )
    run("tar", "-xf", str(archive), "-C", str(baseline))
    previous = build(baseline, "previous")
    run(uv, "pip", "uninstall", "--python", str(python), "fep-lean")
    run(uv, "pip", "install", "--python", str(python), "--no-deps", str(previous))
    run(
        str(python),
        "-I",
        "-c",
        "import fep_lean; assert '/venv/' in fep_lean.__file__.replace('\\\\', '/')",
    )
    # Remove the old RECORD owners before installing their replacements.
    run(uv, "pip", "uninstall", "--python", str(python), "fep-lean")
    run(uv, "pip", "install", "--python", str(python), str(canonical), str(legacy))
    run(str(python), "-I", "-c", probe)
    run(uv, "pip", "check", "--python", str(python))
    run(str(scripts / "fep-formal"), "--help")
    run(str(scripts / "fep-lean"), "--help")


def test_legacy_stub_generator_rejects_drift(tmp_path: Path) -> None:
    source = tmp_path / "src/fep_formal"
    source.mkdir(parents=True)
    (source / "__init__.py").write_text("__all__ = ['Public']\n", encoding="utf-8")
    command = [
        sys.executable,
        str(ROOT / "specs/identity-cutover/generate_legacy_stubs.py"),
        "--root",
        str(tmp_path),
    ]
    subprocess.run(command, check=True, capture_output=True, text=True)
    subprocess.run([*command, "--check"], check=True, capture_output=True, text=True)
    stub = tmp_path / "src/fep_lean/__init__.pyi"
    assert "Public as Public" in stub.read_text(encoding="utf-8")
    stub.write_text("# drift\n", encoding="utf-8")
    result = subprocess.run(
        [*command, "--check"], check=False, capture_output=True, text=True
    )
    assert result.returncode == 1
    assert "Legacy stub drift:" in result.stdout
    (tmp_path / "src/fep_lean/unexpected.pyi").write_text("# extra\n", encoding="utf-8")
    result = subprocess.run(command, check=False, capture_output=True, text=True)
    assert result.returncode != 0
    assert "Unexpected legacy stubs:" in result.stderr


def test_legacy_stub_generator_rejects_missing_source(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "specs/identity-cutover/generate_legacy_stubs.py"),
            "--root",
            str(tmp_path),
            "--check",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "Missing canonical package:" in result.stderr
