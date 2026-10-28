"""Call-time compatibility checks using real environment and CLI boundaries."""

import json
import os
import subprocess
import sys
import warnings
from pathlib import Path

import pytest

from fep_formal import cli
from fep_formal._paths import (
    explicit_project_root,
    project_child_environment,
    project_root_context,
    resolve_environment,
    resolve_output_root,
)
from fep_formal.gauss.cli import _require_gauss_from_env
from fep_formal.gauss.runner import _prefetch_enabled
from fep_formal.pipeline.core import _max_topics_from_env
from fep_formal.verification.lean_verifier import _get_retry_killed, _get_timeout

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def isolated_public_environment(monkeypatch):
    for name in tuple(os.environ):
        if name.startswith(("FEP_FORMAL_", "FEP_LEAN_")):
            monkeypatch.delenv(name)


@pytest.mark.parametrize("canonical", [None, "", "canonical-secret"])
def test_precedence_and_name_only_warnings(monkeypatch, canonical):
    monkeypatch.setenv("FEP_LEAN_TEST_VALUE", "legacy-secret")
    if canonical is not None:
        monkeypatch.setenv("FEP_FORMAL_TEST_VALUE", canonical)
    before = dict(os.environ)
    with pytest.warns(FutureWarning) as caught:
        actual = resolve_environment("FEP_FORMAL_TEST_VALUE", "default")
    assert actual == ("legacy-secret" if canonical is None else canonical)
    assert dict(os.environ) == before
    for item in caught:
        message = str(item.message)
        assert "FEP_LEAN_TEST_VALUE" in message
        assert "FEP_FORMAL_TEST_VALUE" in message
        assert "legacy-secret" not in message
        assert "canonical-secret" not in message


def test_default_equal_alias_and_late_edits(monkeypatch):
    assert resolve_environment("FEP_FORMAL_TEST_VALUE") is None
    assert resolve_environment("FEP_FORMAL_TEST_VALUE", "default") == "default"
    monkeypatch.setenv("FEP_FORMAL_TEST_VALUE", "first")
    monkeypatch.setenv("FEP_LEAN_TEST_VALUE", "first")
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        assert resolve_environment("FEP_FORMAL_TEST_VALUE") == "first"
    assert not caught
    monkeypatch.setenv("FEP_FORMAL_TEST_VALUE", "second")
    with pytest.warns(FutureWarning):
        assert resolve_environment("FEP_FORMAL_TEST_VALUE") == "second"
    with pytest.raises(ValueError, match="canonical"):
        resolve_environment("UNRELATED")


def test_paths_and_child_context(monkeypatch, tmp_path):
    monkeypatch.setenv("FEP_LEAN_PROJECT_ROOT", str(tmp_path / "legacy"))
    with pytest.warns(FutureWarning):
        assert explicit_project_root() == (tmp_path / "legacy").resolve()
    monkeypatch.setenv("FEP_FORMAL_PROJECT_ROOT", "")
    with pytest.warns(FutureWarning):
        assert explicit_project_root() is None
    monkeypatch.setenv("FEP_LEAN_OUTPUT_ROOT", str(tmp_path / "old-output"))
    monkeypatch.setenv("FEP_FORMAL_OUTPUT_ROOT", "")
    with pytest.warns(FutureWarning):
        assert resolve_output_root(tmp_path) == tmp_path / "output"
    base = {"FEP_LEAN_PROJECT_ROOT": "legacy", "FEP_FORMAL_PROJECT_ROOT": ""}
    before = dict(base)
    assert project_child_environment(base) == base
    with project_root_context(tmp_path):
        assert explicit_project_root() == tmp_path.resolve()
        child = project_child_environment(base)
        assert child["FEP_FORMAL_PROJECT_ROOT"] == str(tmp_path.resolve())
    assert base == before


@pytest.mark.parametrize(
    ("suffix", "reader", "value", "expected"),
    [
        ("MAX_TOPICS", _max_topics_from_env, "3", 3),
        ("VERIFY_TIMEOUT", _get_timeout, "17", 17),
        ("VERIFY_RETRY_KILLED", _get_retry_killed, "1", 1),
        ("REQUIRE_GAUSS", _require_gauss_from_env, "yes", True),
        ("PREFETCH", _prefetch_enabled, "true", True),
    ],
)
def test_runtime_readers_legacy_and_canonical(
    monkeypatch, suffix, reader, value, expected
):
    monkeypatch.setenv("FEP_LEAN_" + suffix, value)
    with pytest.warns(FutureWarning):
        assert reader() == expected
    monkeypatch.setenv("FEP_FORMAL_" + suffix, value)
    assert reader() == expected


@pytest.mark.parametrize("prefix", ["FEP_FORMAL_", "FEP_LEAN_"])
def test_cli_setup_timeout_rejects_invalid_before_acquisition(
    monkeypatch, capsys, prefix
):
    monkeypatch.setenv(prefix + "SETUP_TIMEOUT_SEC", "0")
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        assert cli.main(["--project-root", str(ROOT), "setup"]) == 1
    result = json.loads(capsys.readouterr().out)
    assert "FEP_FORMAL_SETUP_TIMEOUT_SEC must be positive" in result["failure_reason"]
    assert any(issubclass(item.category, FutureWarning) for item in caught) == (
        prefix == "FEP_LEAN_"
    )


@pytest.mark.parametrize("prefix", ["FEP_FORMAL_", "FEP_LEAN_"])
def test_cli_max_topics_rejects_invalid_before_outputs(
    monkeypatch, capsys, tmp_path, prefix
):
    monkeypatch.setenv(prefix + "MAX_TOPICS", "-1")
    monkeypatch.setenv("FEP_FORMAL_OUTPUT_ROOT", str(tmp_path / "output"))
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        assert cli.main(["--project-root", str(ROOT), "catalogue"]) == 1
    result = json.loads(capsys.readouterr().out)
    assert "FEP_FORMAL_MAX_TOPICS must be a positive integer" in str(result)
    assert not (tmp_path / "output").exists()
    assert any(issubclass(item.category, FutureWarning) for item in caught) == (
        prefix == "FEP_LEAN_"
    )


@pytest.mark.parametrize("prefix", ["FEP_FORMAL_", "FEP_LEAN_"])
def test_timeout_does_not_capture_a_deleted_import_time_override(prefix):
    code = """
import os
os.environ[PREFIX + 'VERIFY_TIMEOUT'] = '17'
from fep_formal.verification.lean_verifier import _get_timeout
assert _get_timeout() == 17
del os.environ[PREFIX + 'VERIFY_TIMEOUT']
assert _get_timeout() == 1800
os.environ[PREFIX + 'VERIFY_TIMEOUT'] = '23'
assert _get_timeout() == 23
"""
    result = subprocess.run(
        [sys.executable, "-c", f"PREFIX = {prefix!r}\n" + code],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
