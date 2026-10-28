"""Real-process compatibility checks for canonical and deprecated identities."""

from __future__ import annotations

import importlib
import json
import os
import runpy
import subprocess
import sys
import warnings
from pathlib import Path

import pytest


@pytest.mark.parametrize("legacy_first", [False, True])
def test_mixed_names_share_modules_classes_and_snapshot(legacy_first: bool) -> None:
    code = """
import importlib, sys, warnings
with warnings.catch_warnings(record=True) as notices:
    warnings.simplefilter('always', FutureWarning)
    first = importlib.import_module(ORDER[0])
    assert 'matplotlib' not in sys.modules
    second = importlib.import_module(ORDER[1])
    assert first is second
    assert first._SOURCE_RUNTIME_SHA256 is second._SOURCE_RUNTIME_SHA256
    assert any('deprecated' in str(n.message) for n in notices)
for suffix in ('_paths', 'catalogue.topics', 'methods.probes', 'output.evidence',
               'verification._subprocess', 'gauss.client'):
    canonical = importlib.import_module('fep_formal.' + suffix)
    legacy = importlib.import_module('fep_lean.' + suffix)
    assert canonical is legacy, suffix
    assert canonical.__spec__.name == 'fep_formal.' + suffix
    assert canonical.__package__.startswith('fep_formal')
    assert importlib.reload(legacy) is canonical
from fep_formal._paths import FepFormalError
from fep_lean._paths import FepLeanError
assert FepFormalError is FepLeanError
from fep_lean.catalogue import FEPTopicCatalogue as old
from fep_formal.catalogue import FEPTopicCatalogue as new
assert old is new
assert len(old.default().topics) == 168
try:
    importlib.import_module('fep_lean.no_such_module')
except ModuleNotFoundError:
    pass
else:
    raise AssertionError('missing alias falsely accepted')
"""
    names = ("fep_lean", "fep_formal") if legacy_first else ("fep_formal", "fep_lean")
    result = subprocess.run(
        [sys.executable, "-c", f"ORDER = {names!r}\n" + code],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("module", ["fep_lean", "fep_lean.cli"])
def test_deprecated_module_command_preserves_help_stdout(module: str) -> None:
    canonical = subprocess.run(
        [sys.executable, "-m", "fep_formal", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    legacy = subprocess.run(
        [sys.executable, "-m", module, "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert canonical.returncode == legacy.returncode == 0
    assert canonical.stdout == legacy.stdout
    assert "deprecated" in legacy.stderr
    assert "deprecated" not in canonical.stderr


def test_canonical_import_does_not_install_global_alias_finder() -> None:
    code = """
import sys
before = tuple(sys.meta_path)
import fep_formal
assert tuple(sys.meta_path) == before
assert 'fep_lean' not in sys.modules
assert 'matplotlib' not in sys.modules
"""
    subprocess.run([sys.executable, "-c", code], env=dict(os.environ), check=True)


@pytest.mark.parametrize("change", ["modify", "delete", "add"])
def test_bridge_binding_rejects_legacy_adapter_drift(
    tmp_path: Path, change: str
) -> None:
    from fep_formal.bridge.custody import fingerprint, validate_binding
    from fep_formal.bridge.operations import owner_roster

    shim = tmp_path / "src/fep_lean/__init__.py"
    stub = tmp_path / "src/fep_lean/catalogue/__init__.pyi"
    for path in (shim, stub):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# fixture\n")
    roster = owner_roster(tmp_path, "fep_lean")
    assert "src/fep_lean/__init__.py" in roster
    assert "src/fep_lean/catalogue/__init__.pyi" in roster
    assert "src/fep_lean/py.typed" in roster
    assert "compat/fep-lean/pyproject.toml" in roster
    for relative in roster:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_text("fixture\n")
    binding = fingerprint(tmp_path, roster)
    assert validate_binding(tmp_path, binding, roster) == []
    if change == "modify":
        shim.write_text("# changed executable shim\n")
    elif change == "delete":
        shim.unlink()
    else:
        (shim.parent / "new_owner.py").write_text("# added executable owner\n")
    assert validate_binding(tmp_path, binding, owner_roster(tmp_path, "fep_lean"))


def test_runtime_adapter_type_gate_cannot_be_shadowed_by_its_stub(
    tmp_path: Path,
) -> None:
    root = Path(__file__).resolve().parents[1]
    package = tmp_path / "fep_lean"
    package.mkdir()
    source = package / "__init__.py"
    source.write_bytes((root / "src/fep_lean/__init__.py").read_bytes())
    (package / "__init__.pyi").write_text(
        "# A valid stub must not hide implementation errors.\n"
    )
    config = tmp_path / "mypy.ini"
    config.write_text("[mypy]\nstrict = True\n")
    command = [
        sys.executable,
        "-m",
        "mypy",
        "--no-incremental",
        "--config-file",
        str(config),
        str(source),
    ]
    valid = subprocess.run(command, capture_output=True, text=True, check=False)
    assert valid.returncode == 0, valid.stdout + valid.stderr
    source.write_text(source.read_text() + '\n_gate_control: int = "wrong type"\n')
    invalid = subprocess.run(command, capture_output=True, text=True, check=False)
    assert invalid.returncode != 0
    assert "assignment" in invalid.stdout


def test_in_process_legacy_interfaces_keep_identity_resources_and_failure_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    import fep_formal
    from fep_formal.cli import legacy_main

    already_loaded = "fep_lean" in sys.modules
    with warnings.catch_warnings(record=True) as notices:
        warnings.simplefilter("always", FutureWarning)
        legacy = importlib.import_module("fep_lean")
    assert legacy is fep_formal
    if not already_loaded:
        assert any("deprecated" in str(item.message) for item in notices)
    for suffix in ("_paths", "catalogue", "methods.probes", "data"):
        old = importlib.import_module("fep_lean." + suffix)
        canonical = importlib.import_module("fep_formal." + suffix)
        assert old is canonical
        assert old.__spec__.name == "fep_formal." + suffix
    from importlib.resources import files

    assert (
        files("fep_lean.data").joinpath("topics.yaml").read_bytes()
        == files("fep_formal.data").joinpath("topics.yaml").read_bytes()
    )
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("fep_lean.definitely_absent_identity_module")
    missing = tmp_path / "absent-checkout"
    monkeypatch.setattr(
        sys, "argv", ["fep-lean", "--project-root", str(missing), "catalogue"]
    )
    with pytest.warns(FutureWarning, match="deprecated"):
        assert legacy_main() == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "error"
    assert not missing.exists()


def test_legacy_runpy_uses_canonical_code_and_loader_rejects_noncode_targets(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", FutureWarning)
        importlib.import_module("fep_lean")
    monkeypatch.setattr(sys, "argv", ["fep-lean", "--help"])
    with pytest.raises(SystemExit) as stopped:
        runpy.run_module("fep_lean", run_name="__main__")
    assert stopped.value.code == 0
    assert "fep-formal" in capsys.readouterr().out
    finder = next(
        entry
        for entry in sys.meta_path
        if type(entry).__module__ == "fep_lean"
        and type(entry).__name__ == "_AliasFinder"
    )
    spec = finder.find_spec("fep_lean.data")
    assert spec is not None and spec.loader is not None
    # Real built-in and missing-module inputs exercise rejection without
    # replacing import machinery or fabricating module specs.
    loader_type = type(spec.loader)
    for target in ("sys", "definitely_absent_identity_module"):
        with pytest.raises(ImportError, match="No executable canonical module"):
            loader_type(target).get_code("fep_lean.data")
