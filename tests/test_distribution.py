"""Installed-distribution contracts for the public package boundary."""

from __future__ import annotations

import os
import shutil
import site
import subprocess
import sys
import venv
import zipfile
from importlib.metadata import distribution
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_distribution_exports_one_root_package_and_console_script() -> None:
    """Wheel metadata must match the documented import and CLI surfaces."""
    dist = distribution("fep_lean")

    top_level = (dist.read_text("top_level.txt") or "").split()
    assert top_level == ["fep_lean"]

    scripts = {
        entry.name: entry.value
        for entry in dist.entry_points
        if entry.group == "console_scripts"
    }
    assert scripts == {"fep-lean": "fep_lean.cli:main"}


def test_built_wheel_imports_in_isolated_namespace(tmp_path: Path) -> None:
    """Exercise the built bytes outside the checkout's import path."""
    uv = shutil.which("uv")
    assert uv is not None, "the project test contract requires uv"
    dist_dir = tmp_path / "dist"
    subprocess.run(
        [uv, "build", "--wheel", "--out-dir", str(dist_dir)],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    wheel = next(dist_dir.glob("fep_lean-*.whl"))
    with zipfile.ZipFile(wheel) as archive:
        metadata_name = next(
            name for name in archive.namelist() if name.endswith(".dist-info/METADATA")
        )
        wheel_metadata = archive.read(metadata_name).decode("utf-8")
    assert "License-Expression: CC-BY-4.0\n" in wheel_metadata
    assert "License-File: LICENSE\n" in wheel_metadata
    assert "Author-email: Daniel Ari Friedman <daniel@activeinference.institute>\n" in (
        wheel_metadata
    )
    assert "Description-Content-Type: text/markdown\n" in wheel_metadata
    assert (
        "Project-URL: Repository, https://github.com/ActiveInferenceInstitute/fep_formal\n"
        in wheel_metadata
    )
    assert (
        "Project-URL: Changelog, https://github.com/ActiveInferenceInstitute/fep_formal/blob/main/CHANGELOG.md\n"
        in wheel_metadata
    )
    assert (
        "Project-URL: Concept DOI, https://doi.org/10.5281/zenodo.19699233\n"
        in wheel_metadata
    )

    environment = tmp_path / "venv"
    # Preserve the managed interpreter's library resolution on POSIX (notably
    # uv's macOS Python builds whose dylib lives beside the original binary).
    venv.EnvBuilder(
        with_pip=False, system_site_packages=True, symlinks=os.name != "nt"
    ).create(environment)
    python = environment / "bin" / "python"
    subprocess.run(
        [
            uv,
            "pip",
            "install",
            "--python",
            str(python),
            "--offline",
            "--no-deps",
            str(wheel),
        ],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )
    # Reuse only the already-locked test environment's third-party dependencies.
    # The child environment still owns the installed fep_lean bytes, whose path is
    # asserted below, while the smoke remains deterministic and registry-free.
    child_site = (
        environment
        / "lib"
        / f"python{sys.version_info.major}.{sys.version_info.minor}"
        / "site-packages"
    )
    dependency_site = next(Path(path) for path in site.getsitepackages())
    (child_site / "_fep_lean_test_dependencies.pth").write_text(
        f"{dependency_site}\n", encoding="utf-8"
    )
    clean_env = dict(os.environ)
    clean_env.pop("PYTHONPATH", None)
    probe = subprocess.run(
        [
            str(python),
            "-c",
            (
                "import importlib.resources, importlib.util, pathlib, fep_lean; "
                "from fep_lean.bridge.custody import classify_document; "
                "from fep_lean.bridge.certificates import compare; "
                "assert callable(classify_document) and callable(compare); "
                "from fep_lean.catalogue import BODIES, FEPTopicCatalogue; "
                f"assert pathlib.Path(fep_lean.__file__).is_relative_to(pathlib.Path({str(environment)!r})); "
                "assert len(FEPTopicCatalogue.default().topics) == len(BODIES); "
                "assert callable(fep_lean.build_formal_kernel_dashboard); "
                "formal = importlib.resources.files('fep_lean.formal').joinpath('composed.lean'); "
                "core = importlib.resources.files('fep_lean.formal').joinpath('compositions/core.lean'); "
                "assert 'import FepSketches.compositions.core' in formal.read_text(encoding='utf-8'); "
                "assert 'fep002_vfe_compProd_chain_rule' in core.read_text(encoding='utf-8'); "
                "assert importlib.util.find_spec('catalogue') is None"
            ),
        ],
        cwd=tmp_path,
        env=clean_env,
        check=False,
        capture_output=True,
        text=True,
    )
    assert probe.returncode == 0, probe.stderr or probe.stdout
    cli = subprocess.run(
        [str(environment / "bin" / "fep-lean"), "--help"],
        cwd=tmp_path,
        env=clean_env,
        check=False,
        capture_output=True,
        text=True,
    )
    assert cli.returncode == 0, cli.stderr or cli.stdout
    assert "Strict FEP Lean catalogue" in cli.stdout
    outside_checkout = subprocess.run(
        [str(environment / "bin" / "fep-lean"), "catalogue"],
        cwd=tmp_path,
        env=clean_env,
        check=False,
        capture_output=True,
        text=True,
    )
    assert outside_checkout.returncode == 1
    assert "--project-root" in outside_checkout.stdout
    live_check = subprocess.run(
        [
            str(environment / "bin" / "fep-lean"),
            "--project-root",
            str(PROJECT_ROOT),
            "atlas",
            "--check",
        ],
        cwd=tmp_path,
        env=clean_env,
        check=False,
        capture_output=True,
        text=True,
    )
    assert live_check.returncode == 0, live_check.stderr or live_check.stdout
    assert "projections are current" in live_check.stdout
    dashboard_check = subprocess.run(
        [
            str(environment / "bin" / "fep-lean"),
            "--project-root",
            str(PROJECT_ROOT),
            "dashboard",
            "--check",
        ],
        cwd=tmp_path,
        env=clean_env,
        check=False,
        capture_output=True,
        text=True,
    )
    assert dashboard_check.returncode == 0, (
        dashboard_check.stderr or dashboard_check.stdout
    )
    assert "dashboard projections are current" in dashboard_check.stdout
