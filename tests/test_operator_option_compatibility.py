"""Preserve documented template fallback and bridge option applicability."""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

from fep_formal.bridge import cli as bridge_cli


@pytest.mark.parametrize(
    "explicit_valid,environment_valid",
    [(True, True), (True, False), (False, True), (False, False)],
)
def test_render_template_uses_first_valid_candidate(
    tmp_path, monkeypatch, explicit_valid, environment_valid
):
    root = Path(__file__).resolve().parent.parent
    scripts = root / "scripts"
    monkeypatch.syspath_prepend(str(scripts))
    spec = importlib.util.spec_from_file_location(
        "render_precedence_control", scripts / "render_publication.py"
    )
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, spec.name, module)
    spec.loader.exec_module(module)
    explicit, environment = tmp_path / "explicit", tmp_path / "environment"
    for path, valid in [(explicit, explicit_valid), (environment, environment_valid)]:
        if valid:
            stage = path / module.RENDER_STAGE
            stage.parent.mkdir(parents=True)
            stage.write_text("# test template sentinel\n")
    monkeypatch.setenv(module.TEMPLATE_ENVIRONMENT_VARIABLE, str(environment))
    monkeypatch.setattr(
        subprocess, "Popen", lambda *a, **k: pytest.fail("resolver started a process")
    )
    if explicit_valid or environment_valid:
        assert (
            module.resolve_template(explicit)
            == (explicit if explicit_valid else environment).resolve()
        )
    else:
        with pytest.raises(FileNotFoundError, match="no rendering template"):
            module.resolve_template(explicit)


def test_bridge_status_ignores_inapplicable_compatibility_flags(
    tmp_path, monkeypatch, capsys
):
    parser = argparse.ArgumentParser()
    bridge_cli.add_arguments(parser)
    paths = {
        name: tmp_path / (name + "-must-remain-absent")
        for name in ["document", "results", "receipt"]
    }
    args = parser.parse_args(
        [
            "status",
            "--gnn-root",
            str(tmp_path / "gnn"),
            "--model",
            "continuous",
            "--fail-on-warnings",
            *[arg for name, path in paths.items() for arg in ["--" + name, str(path)]],
        ]
    )
    calls = []
    monkeypatch.setattr(
        bridge_cli.operations,
        "status",
        lambda root, gnn: calls.append((root, gnn)) or {"status": "ok"},
    )

    def forbidden(*args, **kwargs):
        pytest.fail("inapplicable flag invoked a writer, reader or child process")

    for name in [
        "read_object",
        "pin_sources",
        "emit",
        "certificate_receipt",
        "emit_certificate",
        "validate_certificate",
        "verify_document",
    ]:
        monkeypatch.setattr(bridge_cli.operations, name, forbidden)
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    before = list(tmp_path.rglob("*"))
    assert bridge_cli.run(tmp_path, args) == 0
    assert calls == [(tmp_path, (tmp_path / "gnn").resolve())]
    assert json.loads(capsys.readouterr().out) == {"status": "ok"}
    assert list(tmp_path.rglob("*")) == before
    assert not any(path.exists() for path in paths.values())


def test_accept_only_delegates_without_template_lock_or_hydration(monkeypatch):
    root = Path(__file__).resolve().parent.parent
    monkeypatch.syspath_prepend(str(root / "scripts"))
    spec = importlib.util.spec_from_file_location(
        "render_accept_only_control", root / "scripts/render_publication.py"
    )
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, spec.name, module)
    spec.loader.exec_module(module)
    calls = []
    monkeypatch.setattr(module, "accept_render", lambda args: calls.append(args) or 0)

    def forbidden(*args, **kwargs):
        pytest.fail("accept-only invoked template, lock, hydration or rendering")

    for name in [
        "resolve_template",
        "acquire_lock",
        "render_sources",
        "render_publication",
    ]:
        monkeypatch.setattr(module, name, forbidden)
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    assert (
        module.main(
            [
                "--accept-only",
                "--template",
                "/missing-ignored-template",
                "--lock-timeout",
                "0",
                "--skip-font-probe",
                "--require-release-stamp",
            ]
        )
        == 0
    )
    assert calls == [
        [
            "--pdf-dir",
            str(root / "output/pdf"),
            "--manuscript-dir",
            str(root / "manuscript"),
            "--receipt",
            str(root / module.RECEIPT_PATH),
        ]
    ]
