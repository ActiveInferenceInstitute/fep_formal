"""Offline tests for fep_lean.prove2me.config (t-0024 slice A).

Every ``Prove2meConfig.load`` call injects ``env=`` and ``home=`` so no test
touches ``os.environ`` or the real home directory; nothing here performs
network I/O.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from fep_lean.prove2me.config import (
    CREDENTIALS_ENV_VAR,
    DEFAULT_BASE_URL,
    ENV_VAR,
    Prove2meAPIError,
    Prove2meAuthError,
    Prove2meConfig,
    Prove2meConfigError,
    Prove2meError,
    Prove2meTimeoutError,
    Prove2meTransportError,
    redact_secret,
)

FAKE_KEY = "p2m_TEST_FAKE_KEY"


def _write_credentials(path: Path, payload: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")
    return path


def _credentials_with_key(path: Path, key: str) -> Path:
    return _write_credentials(path, json.dumps({"api_key": key}))


def _make_all_sources(tmp_path: Path) -> dict[str, str]:
    """Point the credentials env var at an existing file (low-priority)."""
    env_credentials = _credentials_with_key(
        tmp_path / "from-env-var" / "credentials.json", "env-var-file-key"
    )
    return {CREDENTIALS_ENV_VAR: str(env_credentials)}


def _populate_home(tmp_path: Path) -> None:
    """Create both home credential files with distinct, low-priority keys."""
    _credentials_with_key(
        tmp_path / ".prove2me" / "credentials.json", "dot-prove2me-key"
    )
    _credentials_with_key(
        tmp_path / "prove2me_workspace" / "credentials.json", "workspace-key"
    )


# ── Resolution order ─────────────────────────────────────────────────────────


def test_load_explicit_key_wins_over_all_sources(tmp_path: Path) -> None:
    env = {ENV_VAR: "env-key", **_make_all_sources(tmp_path)}
    _populate_home(tmp_path)
    config = Prove2meConfig.load(api_key=FAKE_KEY, env=env, home=tmp_path)
    assert config.api_key == FAKE_KEY


def test_load_env_var_beats_all_credential_files(tmp_path: Path) -> None:
    env = {ENV_VAR: "env-key", **_make_all_sources(tmp_path)}
    _populate_home(tmp_path)
    config = Prove2meConfig.load(env=env, home=tmp_path)
    assert config.api_key == "env-key"


def test_load_credentials_env_file_beats_home_files(tmp_path: Path) -> None:
    env = _make_all_sources(tmp_path)
    _populate_home(tmp_path)
    config = Prove2meConfig.load(env=env, home=tmp_path)
    assert config.api_key == "env-var-file-key"


def test_load_home_dot_prove2me_beats_workspace_file(tmp_path: Path) -> None:
    _populate_home(tmp_path)
    config = Prove2meConfig.load(env={}, home=tmp_path)
    assert config.api_key == "dot-prove2me-key"


def test_load_workspace_file_used_when_nothing_else_present(tmp_path: Path) -> None:
    _credentials_with_key(
        tmp_path / "prove2me_workspace" / "credentials.json", "workspace-key"
    )
    config = Prove2meConfig.load(env={}, home=tmp_path)
    assert config.api_key == "workspace-key"


def test_load_env_var_used_when_no_files_exist(tmp_path: Path) -> None:
    config = Prove2meConfig.load(env={ENV_VAR: "env-key"}, home=tmp_path)
    assert config.api_key == "env-key"


def test_load_empty_explicit_key_falls_through_to_env(tmp_path: Path) -> None:
    """First *non-empty* wins: an empty explicit argument is not a candidate."""
    config = Prove2meConfig.load(api_key="", env={ENV_VAR: "env-key"}, home=tmp_path)
    assert config.api_key == "env-key"


def test_load_credentials_file_key_is_stripped(tmp_path: Path) -> None:
    _credentials_with_key(tmp_path / ".prove2me" / "credentials.json", "  spaced-key  ")
    config = Prove2meConfig.load(env={}, home=tmp_path)
    assert config.api_key == "spaced-key"


def test_load_uses_default_and_overridden_base_url(tmp_path: Path) -> None:
    assert Prove2meConfig.load(api_key="k", env={}, home=tmp_path).base_url == (
        DEFAULT_BASE_URL
    )
    config = Prove2meConfig.load(
        api_key="k", base_url="http://127.0.0.1:9/api/v1", env={}, home=tmp_path
    )
    assert config.base_url == "http://127.0.0.1:9/api/v1"


# ── Credentials-file error paths ─────────────────────────────────────────────


def test_load_malformed_json_raises_naming_path(tmp_path: Path) -> None:
    # Document snippet must not leak: embed the fake key in the broken JSON.
    broken = _write_credentials(
        tmp_path / "broken" / "credentials.json",
        f'{{"api_key": "{FAKE_KEY}" oops',
    )
    env = {CREDENTIALS_ENV_VAR: str(broken)}
    with pytest.raises(Prove2meConfigError) as excinfo:
        Prove2meConfig.load(env=env, home=tmp_path)
    message = str(excinfo.value)
    assert str(broken) in message
    assert FAKE_KEY not in message


def test_load_missing_api_key_entry_raises_naming_path(tmp_path: Path) -> None:
    missing_entry = _write_credentials(
        tmp_path / ".prove2me" / "credentials.json", json.dumps({"other": "value"})
    )
    with pytest.raises(Prove2meConfigError) as excinfo:
        Prove2meConfig.load(env={}, home=tmp_path)
    message = str(excinfo.value)
    assert str(missing_entry) in message
    assert "api_key" in message


def test_load_empty_api_key_entry_raises(tmp_path: Path) -> None:
    blank = _write_credentials(
        tmp_path / ".prove2me" / "credentials.json", json.dumps({"api_key": "   "})
    )
    with pytest.raises(Prove2meConfigError) as excinfo:
        Prove2meConfig.load(env={}, home=tmp_path)
    assert str(blank) in str(excinfo.value)


def test_load_non_object_credentials_raise(tmp_path: Path) -> None:
    array_file = _write_credentials(
        tmp_path / ".prove2me" / "credentials.json", json.dumps(["not", "an", "object"])
    )
    with pytest.raises(Prove2meConfigError) as excinfo:
        Prove2meConfig.load(env={}, home=tmp_path)
    message = str(excinfo.value)
    assert str(array_file) in message
    assert "JSON object" in message


def test_load_missing_everywhere_lists_searched_paths(tmp_path: Path) -> None:
    env = {CREDENTIALS_ENV_VAR: str(tmp_path / "explicit" / "credentials.json")}
    with pytest.raises(Prove2meConfigError) as excinfo:
        Prove2meConfig.load(env=env, home=tmp_path)
    message = str(excinfo.value)
    assert str(tmp_path / "explicit" / "credentials.json") in message
    assert str(tmp_path / ".prove2me" / "credentials.json") in message
    assert str(tmp_path / "prove2me_workspace" / "credentials.json") in message


def test_load_missing_everywhere_without_credentials_env_var(tmp_path: Path) -> None:
    with pytest.raises(Prove2meConfigError) as excinfo:
        Prove2meConfig.load(env={}, home=tmp_path)
    message = str(excinfo.value)
    assert str(tmp_path / ".prove2me" / "credentials.json") in message
    assert str(tmp_path / "prove2me_workspace" / "credentials.json") in message


def test_load_invalid_credentials_env_path_falls_through(tmp_path: Path) -> None:
    """A structurally invalid credentials-env path is 'not found', not fatal."""
    _credentials_with_key(tmp_path / ".prove2me" / "credentials.json", "dot-key")
    env = {
        CREDENTIALS_ENV_VAR: str(tmp_path / ".prove2me" / "credentials.json" / "sub")
    }
    config = Prove2meConfig.load(env=env, home=tmp_path)
    assert config.api_key == "dot-key"


# ── Redaction ────────────────────────────────────────────────────────────────


def test_redact_secret_masks_everything_but_length() -> None:
    assert redact_secret("") == "<unset>"
    assert redact_secret(FAKE_KEY) == f"p2m_***<len-{len(FAKE_KEY)}>"


def test_config_repr_and_str_redact_api_key() -> None:
    config = Prove2meConfig(api_key=FAKE_KEY)
    rendered = repr(config)
    assert FAKE_KEY not in rendered
    assert f"p2m_***<len-{len(FAKE_KEY)}>" in rendered
    assert DEFAULT_BASE_URL in rendered
    # A dataclass without __str__ renders via __repr__, so str() is redacted too.
    assert FAKE_KEY not in str(config)


def test_config_unset_key_renders_unset_marker() -> None:
    config = Prove2meConfig()
    assert "<unset>" in repr(config)
    assert FAKE_KEY not in repr(config)


def test_loaded_config_repr_is_redacted(tmp_path: Path) -> None:
    config = Prove2meConfig.load(env={ENV_VAR: FAKE_KEY}, home=tmp_path)
    assert FAKE_KEY not in repr(config)


def test_error_hierarchy_and_status_code() -> None:
    for error_type in (
        Prove2meConfigError,
        Prove2meAuthError,
        Prove2meAPIError,
        Prove2meTransportError,
        Prove2meTimeoutError,
    ):
        assert issubclass(error_type, Prove2meError)
    assert Prove2meError("boom").status_code is None
    api_error = Prove2meAPIError("bad response", status_code=418)
    assert api_error.status_code == 418
    assert str(api_error) == "bad response"


def test_config_error_messages_carry_no_key_material(tmp_path: Path) -> None:
    """Every config-error message stays key-free even with a hostile file."""
    hostile = _write_credentials(
        tmp_path / "explicit" / "credentials.json",
        f'{{"api_key": "{FAKE_KEY}"',
    )
    env = {CREDENTIALS_ENV_VAR: str(hostile)}
    with pytest.raises(Prove2meConfigError) as excinfo:
        Prove2meConfig.load(env=env, home=tmp_path)
    assert FAKE_KEY not in str(excinfo.value)
    assert FAKE_KEY not in repr(excinfo.value)
