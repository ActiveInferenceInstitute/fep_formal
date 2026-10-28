"""Failure controls for preparation tooling; these do not attest H2 approval."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).with_name("capture_h2_evidence.py")
spec = importlib.util.spec_from_file_location("science_h2_capture", SCRIPT)
assert spec is not None and spec.loader is not None
capture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(capture)


@pytest.mark.parametrize("phase", ["before", "after", "timeout", "changed_collection"])
def test_capture_retains_rejecting_record(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, phase: str
) -> None:
    output = tmp_path / "capture"
    monkeypatch.setattr(sys, "argv", [str(SCRIPT), "--output", str(output)])
    monkeypatch.setenv("PYTEST_ADDOPTS", "-k omitted_parameter")
    monkeypatch.setenv("PYTEST_PLUGINS", "untrusted_selection_plugin")
    monkeypatch.setenv("FEP_FORMAL_LIVE_TESTS", "1")
    monkeypatch.setenv("FEP_LEAN_LIVE_TESTS", "1")
    monkeypatch.setattr(capture, "native_source_paths", lambda _: ("fixture",))
    reads = 0

    def snapshot(*_: object) -> dict[str, str]:
        nonlocal reads
        reads += 1
        if phase == "before" or (phase == "after" and reads > 1):
            raise ValueError("synthetic source snapshot failure")
        return {"fixture": "0" * 64}

    monkeypatch.setattr(capture, "source_snapshot", snapshot)

    def run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        env = kwargs["env"]
        assert isinstance(env, dict)
        assert "PYTEST_ADDOPTS" not in env and "PYTEST_PLUGINS" not in env
        assert env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] == "1"
        assert env["FEP_FORMAL_LIVE_TESTS"] == "0"
        assert "FEP_LEAN_LIVE_TESTS" not in env
        if phase == "timeout":
            raise subprocess.TimeoutExpired(
                command, 0.1, output=b"retained stdout", stderr=b"retained stderr"
            )
        is_collection = "--collect" in command
        capture.write_new(
            output / ("collection.json" if is_collection else "run-collection.json"),
            {
                "nodeids": ["test[param-a]", "test[param-b]"]
                if is_collection
                else ["test[param-a]"]
            },
        )
        (output / "junit.xml").write_text("synthetic unit fixture")
        return subprocess.CompletedProcess(command, 0, "synthetic output", "")

    monkeypatch.setattr(capture, "run_process_group", run)
    assert capture.main() == 1
    record = json.loads((output / "capture.json").read_bytes())
    assert record["accepted"] is False
    assert "capture_error" in record
    if phase == "timeout":
        assert (output / "collection-stdout.log").read_bytes() == b"retained stdout"
        assert (output / "collection-stderr.log").read_bytes() == b"retained stderr"
    if phase == "changed_collection":
        assert record["collection_unchanged"] is False


@pytest.mark.parametrize("selection", [["-k", "selected"], ["-m", "selected"]])
def test_capture_rejects_explicit_selection(
    tmp_path: Path, selection: list[str]
) -> None:
    config = pytest.Config.fromdictargs({}, selection)
    with pytest.raises(pytest.UsageError, match="forbids"):
        capture.CollectionCapture(tmp_path / "unused").pytest_configure(config)
