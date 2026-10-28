"""Comprehensive tests for fep_formal.llm.hermes — zero direct, real network/os testing."""

from __future__ import annotations

import http.server
import json
import os
import socket
import threading
import time
from pathlib import Path
from types import SimpleNamespace

import pytest
from pytest_httpserver import HTTPServer

from fep_formal.llm import hermes
from fep_formal.llm.hermes import (
    HermesAPIError,
    HermesConfig,
    HermesExplainer,
    HermesResult,
    _extract_explanation,
    _extract_lean_block,
    _hermes_network_max_retries,
)

PROJ = Path(__file__).resolve().parent.parent


# ── Local HTTP server helpers (no external deps, no direct execution) ───────────────────


class _FixedStatusHandler(http.server.BaseHTTPRequestHandler):
    """Local HTTP handler that replies with a configured status code for any POST.

    Sends a complete HTTP response including ``Content-Length`` so that
    ``urllib`` can fully read the error body before the connection closes.
    Without ``Content-Length``, urllib may see a ``ConnectionResetError``
    while trying to read the body via ``HTTPError.read()``.
    """

    _status: int = 404
    _body: bytes = b"test error response"

    def do_POST(self) -> None:
        body = self._body
        self.send_response(self._status)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
        self.wfile.flush()

    def log_message(self, *args: object) -> None:  # suppress server output
        pass


def _make_handler(status: int) -> type:
    """Return a handler subclass pre-configured to return *status*."""
    return type(f"_Handler{status}", (_FixedStatusHandler,), {"_status": status})


class _SlowResponseHandler(http.server.BaseHTTPRequestHandler):
    """Reply 200 with ``Content-Length`` set, but trickle bytes slowly.

    Each ``write`` is paced under the per-op socket timeout, so urllib's own
    ``timeout`` argument never fires; only a hard wall-clock deadline can
    bound this. Used to verify that ``_make_request`` aborts via its
    worker-thread ``join(timeout=...)`` and surfaces a transient
    ``HermesAPIError`` instead of hanging.
    """

    _delay_per_byte: float = 0.5  # 500 ms between bytes
    _total_bytes: int = 64
    _status: int = 200

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", 0) or 0)
        if length:
            self.rfile.read(length)
        self.send_response(self._status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(self._total_bytes))
        self.end_headers()
        for _ in range(self._total_bytes):
            try:
                self.wfile.write(b"x")
                self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                return  # client gave up — expected when the deadline fires
            import time as _t

            _t.sleep(self._delay_per_byte)

    def log_message(self, *args: object) -> None:
        pass


class _TruncatedContentHandler(http.server.BaseHTTPRequestHandler):
    """Reply 200 with ``Content-Length`` larger than the bytes actually sent.

    ``urllib`` keeps reading until *length* bytes are received; the server closes
    early so the client raises ``http.client.IncompleteRead`` — the same class
    of failure as chunked/streaming drops from upstream APIs.
    """

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", 0) or 0)
        if length:
            self.rfile.read(length)
        payload = b'{"partial":'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", "4096")
        self.end_headers()
        self.wfile.write(payload)
        self.wfile.flush()

    def log_message(self, *args: object) -> None:  # suppress server output
        pass


def _start_local_server(status: int) -> tuple[http.server.HTTPServer, int]:
    """Bind an ephemeral-port HTTPServer in a daemon thread; return (server, port)."""
    srv = http.server.HTTPServer(("127.0.0.1", 0), _make_handler(status))
    port: int = srv.server_address[1]
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    return srv, port


def _start_truncated_body_server() -> tuple[http.server.HTTPServer, int]:
    """HTTPServer that returns a truncated 200 JSON body (IncompleteRead on client)."""
    srv = http.server.HTTPServer(("127.0.0.1", 0), _TruncatedContentHandler)
    port: int = srv.server_address[1]
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    return srv, port


def _start_slow_response_server(
    status: int = 200,
) -> tuple[http.server.ThreadingHTTPServer, int]:
    """HTTPServer that drips bytes slowly so only a wall-clock deadline can bound it.

    Uses ``ThreadingHTTPServer`` with ``daemon_threads=True`` so the in-flight
    slow handler does not block ``server.shutdown()`` in the test teardown.
    """
    handler = type("_SlowHandler", (_SlowResponseHandler,), {"_status": status})
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    srv.daemon_threads = True
    port: int = srv.server_address[1]
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    return srv, port


def _free_port() -> int:
    """Return an ephemeral port number that has nothing listening on it.

    Binds a socket to port 0 (kernel assigns a free port), records the port,
    then closes the socket — leaving the port closed/refused but known.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class TestLoadGaussDotenv:
    """Test HermesConfig._load_gauss_dotenv."""

    @pytest.fixture(autouse=True)
    def _dotenv_keys(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Expand allowed dotenv keys for test coverage of arbitrary variables."""
        monkeypatch.setattr(
            HermesConfig,
            "_ALLOWED_DOTENV_KEYS",
            frozenset(
                {
                    "FOO_KEY",
                    "BAZ",
                    "EXISTING_VAR",
                    "VALID",
                    "Q1",
                    "Q2",
                    "X",
                }
                | HermesConfig._ALLOWED_DOTENV_KEYS
            ),
        )

    def test_loads_keys_from_dotenv(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        dotenv = tmp_path / ".env"
        dotenv.write_text("FOO_KEY=bar123\nBAZ=qux\n", encoding="utf-8")
        monkeypatch.setenv("GAUSS_HOME", str(tmp_path))
        monkeypatch.delenv("FOO_KEY", raising=False)
        monkeypatch.delenv("BAZ", raising=False)

        HermesConfig._load_gauss_dotenv()
        assert os.environ["FOO_KEY"] == "bar123"
        assert os.environ["BAZ"] == "qux"

    def test_does_not_overwrite_existing_env(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        dotenv = tmp_path / ".env"
        dotenv.write_text("EXISTING_VAR=from_file\n", encoding="utf-8")
        monkeypatch.setenv("GAUSS_HOME", str(tmp_path))
        monkeypatch.setenv("EXISTING_VAR", "original")

        HermesConfig._load_gauss_dotenv()
        assert os.environ["EXISTING_VAR"] == "original"

    def test_handles_missing_dotenv(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("GAUSS_HOME", str(tmp_path))
        HermesConfig._load_gauss_dotenv()  # should not raise

    def test_handles_comments_and_blank_lines(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        dotenv = tmp_path / ".env"
        dotenv.write_text("# comment\n\nVALID=yes\n  \n", encoding="utf-8")
        monkeypatch.setenv("GAUSS_HOME", str(tmp_path))
        monkeypatch.delenv("VALID", raising=False)

        HermesConfig._load_gauss_dotenv()
        assert os.environ["VALID"] == "yes"

    def test_strips_quotes_from_values(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        dotenv = tmp_path / ".env"
        dotenv.write_text("Q1='single'\nQ2=\"double\"\n", encoding="utf-8")
        monkeypatch.setenv("GAUSS_HOME", str(tmp_path))
        monkeypatch.delenv("Q1", raising=False)
        monkeypatch.delenv("Q2", raising=False)

        HermesConfig._load_gauss_dotenv()
        assert os.environ["Q1"] == "single"
        assert os.environ["Q2"] == "double"

    def test_handles_read_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("GAUSS_HOME", str(tmp_path))
        dotenv = tmp_path / ".env"
        dotenv.write_text("X=Y\n", encoding="utf-8")

        # Genuine read error via filesystem permissions
        dotenv.chmod(0o000)
        HermesConfig._load_gauss_dotenv()  # should not raise
        dotenv.chmod(0o644)

    @pytest.mark.parametrize("process_key", [None, "sk-synthetic-process", ""])
    def test_readonly_configuration_matches_hydration_without_environment_mutation(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        process_key: str | None,
    ) -> None:
        for name in (
            "OPENROUTER_API_KEY",
            "ANTHROPIC_API_KEY",
            "OPENAI_API_KEY",
            "OPENAI_BASE_URL",
            "GAUSS_DEFAULT_MODEL",
            "HERMES_MODEL",
            "HERMES_API_BASE",
            "HERMES_FALLBACK_MODELS",
        ):
            # Register absent keys too: default hydration writes them directly,
            # and teardown must restore the caller's original environment.
            monkeypatch.setenv(name, "")
            monkeypatch.delenv(name)
        monkeypatch.setenv("GAUSS_HOME", str(tmp_path))
        if process_key is not None:
            monkeypatch.setenv("OPENAI_API_KEY", process_key)
        dotenv = tmp_path / ".env"
        dotenv.write_text(
            "OPENAI_API_KEY=sk-synthetic-dotenv\n"
            "OPENAI_API_KEY=sk-synthetic-later-duplicate\n"
            "OPENAI_BASE_URL=https://api.example.test/v1\n"
            "GAUSS_DEFAULT_MODEL=synthetic/model\n"
            "UNALLOWLISTED=ignored\n"
        )
        before = dict(os.environ)
        before_bytes = dotenv.read_bytes()
        before_mtime = dotenv.stat().st_mtime_ns
        readonly = HermesConfig.from_settings(tmp_path, hydrate_environment=False)
        assert dict(os.environ) == before
        assert readonly.api_key == (
            "sk-synthetic-dotenv" if process_key is None else process_key
        )
        assert readonly.base_url == "https://api.example.test/v1"
        assert readonly.model == "synthetic/model"
        hydrated = HermesConfig.from_settings(tmp_path)
        assert hydrated.api_key == readonly.api_key
        assert hydrated.runtime_policy() == readonly.runtime_policy()
        assert "UNALLOWLISTED" not in os.environ
        assert dotenv.read_bytes() == before_bytes
        assert dotenv.stat().st_mtime_ns == before_mtime


class TestFallbackEnvironmentPolicy:
    @pytest.mark.parametrize(
        "raw",
        [
            "",
            "[",
            "null",
            '"model/name"',
            '{"models": ["model/name"]}',
            "[]",
            "[1]",
            "[true]",
            "[null]",
            "[NaN]",
            '["valid/model", []]',
            '[""]',
            '[" "]',
            '[" model/name"]',
            '["model/name "]',
            json.dumps(["model/" + "x" * 256]),
            json.dumps(["model/name"] * 33),
            " " * 8193,
            "[" * 2000 + "]" * 2000,
        ],
    )
    def test_invalid_override_fails_closed_without_echoing_input(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, raw: str
    ) -> None:
        monkeypatch.setenv("GAUSS_HOME", str(tmp_path))
        monkeypatch.setenv("HERMES_FALLBACK_MODELS", raw)
        with pytest.raises(ValueError, match="HERMES_FALLBACK_MODELS") as rejected:
            HermesConfig.from_settings(tmp_path)
        assert str(rejected.value).startswith(
            "HERMES_FALLBACK_MODELS must be a nonempty JSON list"
        )
        if raw and raw.strip():
            assert raw not in str(rejected.value)

    @pytest.mark.parametrize(
        "fallbacks,expected",
        [
            (["stealth/space-bunny-alpha"], ["stealth/space-bunny-alpha"]),
            (
                ["stealth/space-bunny-alpha", "openai/gpt-6.1-sol:batch"],
                ["stealth/space-bunny-alpha", "openai/gpt-6.1-sol:batch"],
            ),
            (
                ["approved/second", "approved/first", "approved/second"],
                ["stealth/space-bunny-alpha", "approved/second", "approved/first"],
            ),
        ],
    )
    def test_explicit_override_freezes_chain_without_settings_mutation(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        fallbacks: list[str],
        expected: list[str],
    ) -> None:
        monkeypatch.setenv("GAUSS_HOME", str(tmp_path))
        monkeypatch.setenv("HERMES_MODEL", "stealth/space-bunny-alpha")
        monkeypatch.setenv("HERMES_API_BASE", "https://openrouter.ai/api/v1")
        monkeypatch.setenv("HERMES_FALLBACK_MODELS", json.dumps(fallbacks))
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        settings = config_dir / "settings.yaml"
        settings.write_text(
            "hermes:\n  model: ambient/primary\n  fallback_models: [ambient/escape]\n",
            encoding="utf-8",
        )
        before = (settings.read_bytes(), settings.stat().st_mtime_ns)
        cfg = HermesConfig.from_settings(tmp_path)
        assert cfg.fallback_models == fallbacks
        assert HermesExplainer(cfg)._build_model_chain() == expected
        assert "ambient/escape" not in expected
        assert (settings.read_bytes(), settings.stat().st_mtime_ns) == before

    def test_absent_override_preserves_yaml_and_builtin_defaults(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("GAUSS_HOME", str(tmp_path))
        monkeypatch.delenv("HERMES_FALLBACK_MODELS", raising=False)
        monkeypatch.setenv("HERMES_MODEL", "primary/model")
        monkeypatch.setenv("HERMES_API_BASE", "https://openrouter.ai/api/v1")
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        settings = config_dir / "settings.yaml"
        settings.write_text(
            "hermes:\n  fallback_models: [yaml/first, yaml/second]\n",
            encoding="utf-8",
        )
        cfg = HermesConfig.from_settings(tmp_path)
        assert HermesExplainer(cfg)._build_model_chain() == [
            "primary/model",
            "yaml/first",
            "yaml/second",
        ]
        settings.unlink()
        cfg = HermesConfig.from_settings(tmp_path)
        assert HermesExplainer(cfg)._build_model_chain() == [
            "primary/model",
            *hermes._FREE_MODEL_CHAIN,
        ]

    def test_primary_only_rate_limit_never_escapes_to_ambient_models(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        httpserver: HTTPServer,
    ) -> None:
        monkeypatch.setenv("GAUSS_HOME", str(tmp_path))
        monkeypatch.setenv("HERMES_MODEL", "approved/primary")
        # The path selects the existing OpenRouter policy, while the host and
        # every actual request remain on loopback with a synthetic credential.
        endpoint = "/openrouter.ai/api/v1"
        monkeypatch.setenv("HERMES_API_BASE", httpserver.url_for(endpoint))
        monkeypatch.setenv("HERMES_FALLBACK_MODELS", '["approved/primary"]')
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-synthetic-fixture")
        monkeypatch.setenv("HERMES_429_MAX_RETRIES", "0")
        monkeypatch.setenv("HERMES_NETWORK_MAX_RETRIES", "0")
        httpserver.expect_request(
            endpoint + "/chat/completions", method="POST"
        ).respond_with_json({"error": {"message": "fixture rate limit"}}, status=429)
        cfg = HermesConfig.from_settings(tmp_path)
        explainer = HermesExplainer(cfg)
        assert explainer._build_model_chain() == ["approved/primary"]
        result = explainer.explain_topic(
            SimpleNamespace(
                id="fixture", lean_sketch="theorem fixture : True := by trivial"
            )
        )
        assert not result.success and result.error
        assert result.model_used == "approved/primary"
        assert [request.get_json()["model"] for request, _ in httpserver.log] == [
            "approved/primary"
        ]

    def test_runtime_policy_serialization_excludes_credentials_and_headers(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        key = "sk-or-synthetic-runtime-policy-secret"
        monkeypatch.setenv("GAUSS_HOME", str(tmp_path))
        monkeypatch.setenv("HERMES_MODEL", "approved/primary")
        monkeypatch.setenv("HERMES_API_BASE", "https://openrouter.ai/api/v1")
        monkeypatch.setenv("HERMES_FALLBACK_MODELS", '["approved/primary"]')
        monkeypatch.setenv("OPENROUTER_API_KEY", key)
        cfg = HermesConfig.from_settings(tmp_path)
        cfg.http_referer = "https://example.invalid/private-header"
        cfg.x_title = "synthetic-private-header"
        policy = cfg.runtime_policy()
        assert set(policy) == {
            "schema_version",
            "model",
            "base_url",
            "fallback_models",
            "max_tokens",
            "timeout_s",
            "reasoning_max_tokens",
            "reasoning_timeout_s",
            "enabled",
            "cache_ttl_hours",
        }
        serialized = json.dumps(policy, sort_keys=True)
        assert key not in serialized and key not in repr(cfg)
        assert "private-header" not in serialized
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-another-synthetic-secret")
        changed_key = HermesConfig.from_settings(tmp_path)
        assert changed_key.runtime_policy() == policy
        policy["fallback_models"].append("mutated/serialization")
        assert cfg.fallback_models == ["approved/primary"]
        assert not (tmp_path / "config" / "settings.yaml").exists()

    @pytest.mark.parametrize(
        "url",
        [
            "https://user:synthetic-url-secret@example.invalid/api/v1",
            "https://synthetic-url-secret@example.invalid/api/v1",
            "https://example.invalid/api/v1?key=synthetic-url-secret",
            "https://example.invalid/api/v1#synthetic-url-secret",
            "https://example.invalid:synthetic-url-secret/api/v1",
            "file:///synthetic-url-secret",
            "relative/synthetic-url-secret",
        ],
    )
    def test_runtime_policy_rejects_credential_bearing_endpoint_urls(
        self, url: str
    ) -> None:
        cfg = HermesConfig(base_url=url)
        with pytest.raises(
            ValueError, match="without userinfo, query or fragment"
        ) as e:
            cfg.runtime_policy()
        assert "synthetic-url-secret" not in str(e.value)
        assert e.value.__suppress_context__


class TestKeyAffinityValidation:
    """Test that API key ↔ endpoint mismatches are caught."""

    def test_anthropic_key_to_openrouter_disables(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-temporary-key")
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.setenv("GAUSS_HOME", "/tmp/__no_gauss__")

        cfg = HermesConfig.from_settings(settings_path=Path("/nonexistent"))
        assert cfg.enabled is False
        assert cfg.api_key == "sk-ant-temporary-key"

    def test_openrouter_key_to_anthropic_disables(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-v1-temporary-or-key")
        monkeypatch.setenv("HERMES_API_BASE", "https://api.anthropic.com/v1")
        monkeypatch.setenv("GAUSS_HOME", "/tmp/__no_gauss__")

        cfg = HermesConfig.from_settings(settings_path=Path("/nonexistent"))
        assert cfg.enabled is False

    def test_correct_key_stays_enabled_without_logging_key_material(
        self,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        key = "sk-or-v1-correct-key"
        monkeypatch.setenv("OPENROUTER_API_KEY", key)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.setenv("GAUSS_HOME", "/tmp/__no_gauss__")
        caplog.set_level("INFO", logger="fep_formal.llm.hermes")

        cfg = HermesConfig.from_settings(settings_path=Path("/nonexistent"))
        assert cfg.enabled is True
        assert cfg.api_key == key
        assert "OPENROUTER_API_KEY" in caplog.text
        assert key not in caplog.text
        assert key[:12] not in caplog.text


class TestCallAPI:
    """Test HermesExplainer._call_api using genuine local OS/network operations.

    Tests use real sockets on loopback — no external network, no direct execution,
    no FEP_FORMAL_LIVE_TESTS gate.  They exercise ``urllib`` exception branches
    inside ``_call_api``:

    * ``urllib.error.HTTPError`` (non-2xx response) → ``HermesAPIError(status_code=N, transient=False)``
    * ``urllib.error.URLError`` (connection refused) → ``HermesAPIError(..., transient=True)``
    * Truncated ``Content-Length`` / ``IncompleteRead`` → ``HermesAPIError(..., transient=True)``

    Implementation details
    ----------------------
    * ``test_call_api_http_error`` spins up a daemon ``HTTPServer`` on an
      ephemeral loopback port that returns a hard-coded 404 for any POST.
      The server thread is cleaned up via ``server.shutdown()`` in the
      ``finally`` block so it does not linger across tests.

    * ``test_call_api_url_error`` allocates an ephemeral port via a socket
      bound to port 0, reads the OS-assigned port number, then closes the
      socket *without* starting a listener.  Any connection attempt
      immediately receives ECONNREFUSED, which ``urllib`` wraps in
      ``urllib.error.URLError`` — exactly the path we want to exercise.
      The timeout is set to 1 s so the test is fast even if the OS queues
      the refused connection.
    """

    def test_call_api_http_error(self) -> None:
        """_call_api raises HermesAPIError(status_code=404) on a 404 response.

        Uses a local daemon HTTPServer (no external network).
        """
        server, port = _start_local_server(404)
        try:
            cfg = HermesConfig(
                enabled=True,
                api_key="sk-or-test",
                base_url=f"http://127.0.0.1:{port}",
            )
            h = HermesExplainer(cfg)
            with pytest.raises(HermesAPIError) as exc_info:
                h._call_api([{"role": "user", "content": "hi"}], "temporary-model")
            assert exc_info.value.status_code == 404
            assert exc_info.value.transient is False
            assert "HTTP 404: Not Found — test error response" in str(exc_info.value)
        finally:
            # shutdown() only stops the serve_forever loop; without
            # server_close() the listening socket leaks — one FD per server
            # per test, which across a full-order run can exhaust the FD
            # table and hang later socket binds (ambient-hang seam (a)).
            server.shutdown()
            server.server_close()

    def test_call_api_url_error(self) -> None:
        """_call_api raises HermesAPIError("Network error: …") on connection refused.

        Binds a socket to get a free port number, closes it (leaving nothing
        listening), then points HermesExplainer at that port — guaranteeing
        ECONNREFUSED without touching external DNS or the network.
        """
        refused_port = _free_port()
        cfg = HermesConfig(
            enabled=True,
            api_key="sk-or-test",
            base_url=f"http://127.0.0.1:{refused_port}",
            timeout_s=1,
        )
        h = HermesExplainer(cfg)
        with pytest.raises(HermesAPIError) as exc_info:
            h._call_api([{"role": "user", "content": "hi"}], "temporary-model")
        assert "Network error" in str(exc_info.value)
        assert exc_info.value.transient is True

    def test_call_api_truncated_body_raises_transient_hermes_api_error(self) -> None:
        """_call_api maps IncompleteRead-style failures to transient HermesAPIError."""
        server, port = _start_truncated_body_server()
        try:
            cfg = HermesConfig(
                enabled=True,
                api_key="sk-or-test",
                base_url=f"http://127.0.0.1:{port}",
                timeout_s=5,
            )
            h = HermesExplainer(cfg)
            with pytest.raises(HermesAPIError) as exc_info:
                h._call_api([{"role": "user", "content": "hi"}], "temporary-model")
            assert exc_info.value.status_code is None
            assert exc_info.value.transient is True
            assert (
                "HTTP transport error" in str(exc_info.value)
                or "Connection error" in str(exc_info.value)
                or "not valid JSON" in str(exc_info.value)
            )
        finally:
            server.shutdown()
            server.server_close()

    @pytest.mark.parametrize("status", [200, 403, 503])
    def test_call_api_wall_clock_deadline_aborts_slow_stream(self, status: int) -> None:
        """_make_request enforces a hard wall-clock deadline on slow responses.

        urllib's per-op ``timeout`` argument does not bound total wall time
        when a server trickles bytes within the timeout window. We observed
        a 150 s ``timeout_s`` taking 10+ minutes in production. The
        worker-thread + ``join(timeout=...)`` guard in ``_make_request``
        must abort the request and raise a transient ``HermesAPIError``
        within ``timeout_s`` seconds.
        """
        server, port = _start_slow_response_server(status)
        deadline_s = 1  # ~32 s of trickle would otherwise be needed (64B * 0.5s)
        try:
            cfg = HermesConfig(
                enabled=True,
                api_key="sk-or-test",
                base_url=f"http://127.0.0.1:{port}",
                timeout_s=deadline_s,
            )
            h = HermesExplainer(cfg)
            import time as _t

            t0 = _t.monotonic()
            with pytest.raises(HermesAPIError) as exc_info:
                h._call_api([{"role": "user", "content": "hi"}], "temporary-model")
            elapsed = _t.monotonic() - t0
            # The same hard deadline covers the HTTPError body and its close.
            assert elapsed < deadline_s + 2, (
                f"deadline not enforced: elapsed={elapsed:.2f}s "
                f"(expected < {deadline_s + 2}s)"
            )
            assert exc_info.value.transient is (status == 200)
            assert exc_info.value.status_code == (None if status == 200 else status)
            assert "Wall-clock timeout" in str(exc_info.value)
        finally:
            server.shutdown()
            server.server_close()

    @pytest.mark.parametrize("status", [200, 403])
    def test_call_api_caps_success_and_http_error_bodies(
        self, monkeypatch: pytest.MonkeyPatch, status: int
    ) -> None:
        # Real loopback streams exercise the shared bounded reader with a small
        # limit, keeping this failure probe independent of large allocations.
        monkeypatch.setattr(hermes, "_MAX_RESPONSE_BYTES", 128)
        monkeypatch.setattr(hermes, "_MAX_RESPONSE_CHUNK", 64)
        handler = type(
            "_OversizedHandler",
            (_FixedStatusHandler,),
            {"_status": status, "_body": b"x" * 1024},
        )
        server = http.server.HTTPServer(("127.0.0.1", 0), handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            explainer = HermesExplainer(
                HermesConfig(
                    enabled=True,
                    api_key="fixture",
                    base_url=f"http://127.0.0.1:{server.server_address[1]}",
                    timeout_s=2,
                )
            )
            with pytest.raises(HermesAPIError, match="exceeds 128 bytes") as error:
                explainer._call_api([{"role": "user", "content": "hi"}], "fixture")
            assert error.value.transient is (status == 200)
            assert error.value.status_code == (None if status == 200 else status)
        finally:
            server.shutdown()
            server.server_close()

    def test_http_error_message_replaces_invalid_utf8_and_caps_excerpt(self) -> None:
        handler = type(
            "_ErrorTextHandler",
            (_FixedStatusHandler,),
            {"_status": 401, "_body": b"\xffdenied " + b"x" * 400},
        )
        server = http.server.HTTPServer(("127.0.0.1", 0), handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            explainer = HermesExplainer(
                HermesConfig(
                    api_key="fixture",
                    base_url=f"http://127.0.0.1:{server.server_address[1]}",
                )
            )
            with pytest.raises(HermesAPIError) as error:
                explainer._call_api([{"role": "user", "content": "hi"}], "fixture")
            assert error.value.status_code == 401
            assert error.value.transient is False
            assert str(error.value).endswith(("�denied " + "x" * 400)[:300])
        finally:
            server.shutdown()
            server.server_close()

    @pytest.mark.parametrize("status", [403, 429])
    @pytest.mark.parametrize("body_failure", ["oversized", "slow", "malformed"])
    def test_failed_http_diagnostics_preserve_auth_and_rate_limit_retry_policy(
        self,
        monkeypatch: pytest.MonkeyPatch,
        status: int,
        body_failure: str,
    ) -> None:
        monkeypatch.setattr(hermes, "_MAX_RESPONSE_BYTES", 128)
        monkeypatch.setattr(hermes, "_MAX_RESPONSE_CHUNK", 64)
        monkeypatch.setenv("HERMES_NETWORK_MAX_RETRIES", "3")
        monkeypatch.setenv("HERMES_429_MAX_RETRIES", "1")
        delays: list[float] = []
        # Keep the server's real pacing; replace only Hermes' backoff clock.
        monkeypatch.setattr(
            hermes,
            "time",
            SimpleNamespace(monotonic=time.monotonic, sleep=delays.append),
        )
        requests: list[int] = []
        base = _SlowResponseHandler if body_failure == "slow" else _FixedStatusHandler

        class PolicyHandler(base):
            _status = status
            _body = b"x" * 1024
            _delay_per_byte = 0.1

            def do_POST(self) -> None:
                requests.append(status)
                if body_failure != "malformed":
                    super().do_POST()
                    return
                length = int(self.headers.get("Content-Length", 0) or 0)
                self.rfile.read(length)
                self.send_response(status)
                self.send_header("Transfer-Encoding", "chunked")
                self.end_headers()
                self.wfile.write(b"not-a-chunk-size\r\n")
                self.wfile.flush()

        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), PolicyHandler)
        server.daemon_threads = True
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            cfg = HermesConfig(
                api_key="fixture",
                base_url=f"http://127.0.0.1:{server.server_address[1]}",
                timeout_s=1,
            )
            explainer = HermesExplainer(cfg)
            started = time.monotonic()
            raw, fatal, error, retries, reason = explainer._try_fetch_raw(
                [{"role": "user", "content": "hi"}], "fixture", "fep-001"
            )
            assert time.monotonic() - started < 4
            assert raw is None
            assert error.startswith(f"HTTP {status}:")
            assert "diagnostic body unavailable" in error
            assert requests == [status] * (2 if status == 429 else 1)
            assert delays == ([2.0] if status == 429 else [])
            assert retries == (1 if status == 429 else 0)
            assert fatal is (status == 403)
            assert cfg.enabled is (status == 429)
            assert reason == "non_retriable_http"
        finally:
            server.shutdown()
            server.server_close()


class TestHermesNetworkMaxRetriesEnv:
    """``HERMES_NETWORK_MAX_RETRIES`` parsing."""

    def test_default_when_unset(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("HERMES_NETWORK_MAX_RETRIES", raising=False)
        assert _hermes_network_max_retries() == 2

    def test_numeric_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("HERMES_NETWORK_MAX_RETRIES", "5")
        assert _hermes_network_max_retries() == 5


class TestTextExtraction:
    """Test _extract_lean_block and _extract_explanation."""

    def test_extract_lean_block_standard(self) -> None:
        content = "Some text\n```lean\ntheorem foo : True := trivial\n```\nMore text"
        assert "theorem foo" in _extract_lean_block(content)

    def test_extract_lean_block_fallback(self) -> None:
        content = "Some text\n```\ntheorem bar : True := trivial\n```\nMore text"
        assert "theorem bar" in _extract_lean_block(content)

    def test_extract_lean_block_none(self) -> None:
        assert _extract_lean_block("no code here") == ""

    def test_extract_explanation(self) -> None:
        content = "First paragraph.\n\n```lean\ncode\n```\n\nSecond paragraph."
        result = _extract_explanation(content)
        assert "First paragraph." in result
        assert "code" not in result

    def test_extract_explanation_headers_skipped(self) -> None:
        content = "# Header\n\nReal content.\n\n```lean\nx\n```"
        result = _extract_explanation(content)
        assert "Header" not in result
        assert "Real content" in result


class TestHermesConfigMisc:
    """Test HermesConfig helper methods."""

    def test_is_reasoning_model(self) -> None:
        cfg = HermesConfig(model="nvidia/nemotron-3-super-120b-a12b:free")
        assert cfg.is_reasoning_model() is True
        cfg2 = HermesConfig(model="some-other-model")
        assert cfg2.is_reasoning_model() is False

    def test_effective_max_tokens(self) -> None:
        cfg = HermesConfig(
            model="nvidia/nemotron-3-super-120b-a12b:free",
            max_tokens=100,
            reasoning_max_tokens=9999,
        )
        assert cfg.effective_max_tokens() == 9999
        cfg2 = HermesConfig(model="other", max_tokens=100, reasoning_max_tokens=9999)
        assert cfg2.effective_max_tokens() == 100

    def test_effective_timeout(self) -> None:
        cfg = HermesConfig(
            model="nvidia/nemotron-3-super-120b-a12b:free",
            timeout_s=30,
            reasoning_timeout_s=600,
        )
        assert cfg.effective_timeout() == 600

    def test_hermes_result_as_dict(self) -> None:
        r = HermesResult(
            success=True, model_used="m", topic_id="t", reasoning="x" * 3000
        )
        d = r.as_dict()
        assert d["success"] is True
        assert len(d["reasoning"]) <= 2000

    def test_build_model_chain_openrouter(self) -> None:
        cfg = HermesConfig(
            model="primary-model", base_url="https://openrouter.ai/api/v1"
        )
        h = HermesExplainer(cfg)
        chain = h._build_model_chain()
        assert chain[0] == "primary-model"
        assert len(chain) > 1

    def test_build_model_chain_non_openrouter(self) -> None:
        cfg = HermesConfig(model="primary-only", base_url="https://custom.api.com/v1")
        h = HermesExplainer(cfg)
        chain = h._build_model_chain()
        assert chain == ["primary-only"]


class TestFromSettingsEdgeCases:
    """Cover HermesConfig.from_settings branches: malformed YAML, API key priority, is_live."""

    def test_malformed_settings_yaml(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A settings file that exists but fails to parse fails closed."""
        bad_yaml = tmp_path / "settings.yaml"
        bad_yaml.write_text("hermes: { bad: [ yaml }", encoding="utf-8")
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.setenv("GAUSS_HOME", "/tmp/__no_gauss__")
        with pytest.raises(ValueError, match="unreadable Hermes settings file"):
            HermesConfig.from_settings(settings_path=bad_yaml)

    def test_api_key_anthropic_fallback(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Cover lines 205-207: ANTHROPIC_API_KEY used when OPENROUTER absent."""
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test123")
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.setenv("HERMES_API_BASE", "https://api.anthropic.com/v1")
        monkeypatch.setenv("GAUSS_HOME", "/tmp/__no_gauss__")
        cfg = HermesConfig.from_settings(settings_path=Path("/nonexistent"))
        assert cfg.api_key == "sk-ant-test123"

    def test_api_key_openai_fallback(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Cover lines 208-210: OPENAI_API_KEY used when others absent."""
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.setenv("OPENAI_API_KEY", "sk-openai-test456")
        monkeypatch.setenv("GAUSS_HOME", "/tmp/__no_gauss__")
        cfg = HermesConfig.from_settings(settings_path=Path("/nonexistent"))
        assert cfg.api_key == "sk-openai-test456"

    def test_api_key_from_settings_yaml_is_rejected(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """SC-33(c): runtime settings never carry provider credentials.

        A committed settings.yaml api_key is rejected (logged, key left
        empty) instead of silently honored — the file is an owner byte that
        can drift into a published checkout.
        """
        import logging

        yaml_file = tmp_path / "settings.yaml"
        yaml_file.write_text("hermes:\n  api_key: sk-yaml-key789\n", encoding="utf-8")
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.setenv("GAUSS_HOME", "/tmp/__no_gauss__")
        with caplog.at_level(logging.ERROR, logger="fep_formal.llm.hermes"):
            cfg = HermesConfig.from_settings(settings_path=yaml_file)
        assert cfg.api_key == ""
        assert any("rejected" in record.message for record in caplog.records)

    def test_no_api_key_anywhere(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Cover line 215-216: empty api_key when none set."""
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.setenv("GAUSS_HOME", "/tmp/__no_gauss__")
        cfg = HermesConfig.from_settings(settings_path=Path("/nonexistent"))
        assert cfg.api_key == ""
        assert cfg.enabled is True  # enabled but no key


class TestIsLiveProperty:
    """Cover line 308: HermesExplainer.is_live property."""

    def test_is_live_enabled_with_key(self) -> None:
        cfg = HermesConfig(enabled=True, api_key="sk-test")
        assert HermesExplainer(cfg).is_live is True

    def test_is_live_enabled_no_key(self) -> None:
        cfg = HermesConfig(enabled=True, api_key="")
        assert HermesExplainer(cfg).is_live is False

    def test_is_live_disabled_with_key(self) -> None:
        cfg = HermesConfig(enabled=False, api_key="sk-test")
        assert HermesExplainer(cfg).is_live is False

    def test_is_live_disabled_no_key(self) -> None:
        cfg = HermesConfig(enabled=False, api_key="")
        assert HermesExplainer(cfg).is_live is False


class TestParseResponse:
    """Cover lines 464-498: HermesExplainer._parse_response edge cases."""

    def _make_explainer(self) -> HermesExplainer:
        return HermesExplainer(HermesConfig(enabled=False))

    def test_empty_choices(self) -> None:
        h = self._make_explainer()
        r = h._parse_response({"choices": []}, "model-x", 1.0, "fep-001")
        assert r.success is False
        assert "empty choices" in r.error

    def test_missing_choices_key(self) -> None:
        h = self._make_explainer()
        r = h._parse_response({}, "model-x", 1.0, "fep-001")
        assert r.success is False

    def test_valid_response_with_lean_block(self) -> None:
        h = self._make_explainer()
        raw = {
            "choices": [
                {
                    "message": {
                        "content": "Explanation.\n\n```lean\ntheorem x : True := trivial\n```"
                    }
                }
            ],
            "usage": {"completion_tokens": 100, "prompt_tokens": 50},
        }
        r = h._parse_response(raw, "model-y", 2.5, "fep-002")
        assert r.success is True
        assert r.model_used == "model-y"
        assert "theorem x" in r.refined_lean_sketch
        assert r.tokens_used == 150
        assert r.duration_s == 2.5
        assert r.topic_id == "fep-002"

    def test_think_tags_extracted_as_reasoning(self) -> None:
        h = self._make_explainer()
        raw = {
            "choices": [
                {
                    "message": {
                        "content": "Before<think>Deep reasoning here</think>After text"
                    }
                }
            ],
            "usage": {"completion_tokens": 50, "prompt_tokens": 20},
        }
        r = h._parse_response(raw, "model-z", 1.0, "fep-003")
        assert r.reasoning == "Deep reasoning here"
        assert "<think>" not in r.explanation
        assert r.tokens_used == 70

    def test_reasoning_field_direct(self) -> None:
        h = self._make_explainer()
        raw = {
            "choices": [
                {"message": {"content": "content", "reasoning": "direct reasoning"}}
            ],
            "usage": {},
        }
        r = h._parse_response(raw, "model-r", 0.5, "fep-004")
        assert r.reasoning == "direct reasoning"
        assert r.tokens_used == 0

    def test_empty_content_returns_failure(self) -> None:
        h = self._make_explainer()
        raw = {
            "choices": [{"message": {"content": ""}}],
            "usage": {"completion_tokens": 10, "prompt_tokens": 5},
        }
        r = h._parse_response(raw, "model-e", 0.1, "fep-005")
        assert r.success is False  # bool("") is False
