"""Offline tests for the Prove2me client: fakes plus loopback HTTP server.

Layer 1 uses an in-memory :class:`Prove2meTransport` fake for token
exchange/caching, the single 401 re-exchange retry, endpoint paths, methods
and bodies (including a multipart boundary parse for ``/verify``), and
secret redaction.  Layer 2 follows ``tests/test_hermes_error_paths.py``:
``pytest_httpserver`` serves the real urllib transport on
``http://127.0.0.1:<port>/`` — refresh + whoami happy path and HTTPError
mapping to :class:`Prove2meAPIError` with ``status_code``.  A final test
covers the poll-timeout path via an injected sleep.  No network beyond
loopback; the default ``https://prove2.me`` base URL is never contacted.
"""

from __future__ import annotations

import json
import time
from collections.abc import Mapping
from typing import Any

import pytest
from pytest_httpserver import HTTPServer

from fep_lean.prove2me.client import (
    Prove2meClient,
    Prove2meTransport,
    TransportResult,
)
from fep_lean.prove2me.config import (
    Prove2meAPIError,
    Prove2meAuthError,
    Prove2meConfig,
    Prove2meTimeoutError,
    Prove2meTransportError,
)
from fep_lean.prove2me.missions import wait_for_verdict

FAKE_KEY = "p2m_TEST_FAKE_KEY"
FAKE_TOKEN = "tok-fake-1"


class FakeTransport:
    """In-memory transport scripted per-method/status responses."""

    def __init__(self) -> None:
        self.requests: list[dict[str, Any]] = []
        self.script: dict[tuple[str, str], list[TransportResult]] = {}
        self.status: dict[tuple[str, str], int] = {}
        self.body: dict[tuple[str, str], bytes] = {}

    def script_response(self, method: str, path: str, status: int, body: bytes) -> None:
        self.status[(method, path)] = status
        self.body[(method, path)] = body

    def send(
        self,
        method: str,
        url: str,
        headers: Mapping[str, str],
        body: bytes | None,
        timeout_s: float,
    ) -> TransportResult:
        self.requests.append(
            {"method": method, "url": url, "headers": dict(headers), "body": body}
        )
        key = (method, _path_of(url))
        if key in self.body:
            return self.status[key], self.body[key]
        return 404, b'{"error": "unscripted path"}'


def _path_of(url: str) -> str:
    """Return the request path relative to the fake base URL."""
    return url.partition("?")[0].rsplit("/api/v1/", 1)[-1]


def make_client(
    transport: Prove2meTransport,
    *,
    now: Any = None,
    sleep: Any = None,
    timeout_s: float = 30.0,
) -> Prove2meClient:
    config = Prove2meConfig(base_url="http://127.0.0.1:1/api/v1", api_key=FAKE_KEY)
    kwargs: dict[str, Any] = {}
    if now is not None:
        kwargs["now"] = now
    if sleep is not None:
        kwargs["sleep"] = sleep
    return Prove2meClient(config, transport=transport, timeout_s=timeout_s, **kwargs)


def refresh_body(token: str = FAKE_TOKEN, expires_at: float | None = None) -> bytes:
    if expires_at is None:
        expires_at = time.time() + 3600
    return json.dumps(
        {"access_token": token, "expires_at": expires_at, "version": "v9"}
    ).encode("utf-8")


# ── token exchange and 401 semantics ─────────────────────────────────────────


def test_refresh_called_once_across_two_calls() -> None:
    """Token is exchanged once and reused while well before expiry."""
    transport = FakeTransport()
    transport.script_response(
        "POST", "agent/refresh", 200, refresh_body(expires_at=time.time() + 10_000)
    )
    transport.script_response("GET", "me", 200, b'{"agent": "a1"}')
    client = make_client(transport)

    assert client.whoami()["agent"] == "a1"
    assert client.whoami()["agent"] == "a1"

    refreshes = [r for r in transport.requests if r["url"].endswith("/agent/refresh")]
    assert len(refreshes) == 1
    assert json.loads(refreshes[0]["body"]) == {"api_key": FAKE_KEY}
    assert client.platform_version == "v9"


def test_401_triggers_single_reexchange_then_success() -> None:
    """First 401 re-exchanges once and retries; second attempt succeeds."""
    transport = FakeTransport()
    transport.script_response(
        "POST", "agent/refresh", 200, refresh_body(expires_at=time.time() + 10_000)
    )
    transport.script_response("GET", "me", 200, b'{"agent": "a1"}')
    client = make_client(transport)
    original_send = transport.send
    me_calls = {"n": 0}

    def flaky_send(
        method: str,
        url: str,
        headers: Mapping[str, str],
        body: bytes | None,
        timeout_s: float,
    ) -> TransportResult:
        result = original_send(method, url, headers, body, timeout_s)
        if _path_of(url) == "me":
            me_calls["n"] += 1
            if me_calls["n"] == 1:
                return 401, b'{"error": "expired"}'
        return result

    transport.send = flaky_send  # type: ignore[method-assign]
    assert client.whoami()["agent"] == "a1"
    assert me_calls["n"] == 2
    refreshes = [r for r in transport.requests if r["url"].endswith("/agent/refresh")]
    assert len(refreshes) == 2


def test_401_twice_raises_auth_error() -> None:
    """A 401 that survives the re-exchange retry raises Prove2meAuthError."""
    transport = FakeTransport()
    transport.script_response(
        "POST", "agent/refresh", 200, refresh_body(expires_at=time.time() + 10_000)
    )
    transport.script_response("GET", "me", 401, b'{"error": "revoked"}')
    client = make_client(transport)

    with pytest.raises(Prove2meAuthError) as excinfo:
        client.whoami()
    assert excinfo.value.status_code == 401
    assert "API key expired" in str(excinfo.value)
    me_calls = [r for r in transport.requests if r["url"].endswith("/me")]
    assert len(me_calls) == 2


def test_refresh_endpoint_failure_raises_auth_error() -> None:
    """A failed token exchange surfaces as Prove2meAuthError."""
    transport = FakeTransport()
    transport.script_response("POST", "agent/refresh", 401, b'{"error": "bad key"}')
    client = make_client(transport)

    with pytest.raises(Prove2meAuthError) as excinfo:
        client.refresh_token()
    assert "API key expired" in str(excinfo.value)


# ── endpoint paths, methods, payloads ─────────────────────────────────────────


@pytest.fixture()
def scripted_client() -> tuple[Prove2meClient, FakeTransport]:
    transport = FakeTransport()
    transport.script_response(
        "POST", "agent/refresh", 200, refresh_body(expires_at=time.time() + 10_000)
    )
    client = make_client(transport)
    return client, transport


def test_get_endpoints_paths_and_params(
    scripted_client: tuple[Prove2meClient, FakeTransport],
) -> None:
    """GET endpoints hit the contract paths with urlencoded params."""
    client, transport = scripted_client
    transport.script_response("GET", "fields", 200, b'{"results": []}')
    transport.script_response("GET", "missions", 200, b'{"items": []}')
    transport.script_response("GET", "theorems", 200, b'{"items": []}')
    transport.script_response("GET", "theorems/T-1", 200, b'{"id": "T-1"}')
    transport.script_response("GET", "verify", 200, b'{"status": "PENDING"}')
    transport.script_response("GET", "mission-proposals/P-9", 200, b'{"id": "P-9"}')

    client.search_fields("category theory")
    client.list_missions(limit=5, offset=10)
    client.search_theorems(q="nat", status="OPEN", sort="new", tags=["a", "b"])
    client.get_theorem("T-1")
    client.get_submission("S-7")
    client.get_proposal("P-9")

    gets = [r for r in transport.requests if r["method"] == "GET"]
    urls = [r["url"] for r in gets]
    assert urls[0] == "http://127.0.0.1:1/api/v1/fields?q=category+theory"
    assert "limit=5" in urls[1] and "offset=10" in urls[1]
    assert "q=nat" in urls[2] and "status=OPEN" in urls[2]
    assert "sort=new" in urls[2] and "tags=a%2Cb" in urls[2]
    assert urls[3].endswith("/theorems/T-1")
    assert "submission_id=S-7" in urls[4]
    assert urls[5].endswith("/mission-proposals/P-9")


def test_list_proposal_milestones_hits_milestones_path(
    scripted_client: tuple[Prove2meClient, FakeTransport],
) -> None:
    """Milestone listing GETs /mission-proposals/:id/milestones with quoted id."""
    client, transport = scripted_client
    transport.script_response(
        "GET", "mission-proposals/P-9/milestones", 200, b'{"items": []}'
    )

    client.list_proposal_milestones("P-9")

    (request,) = [r for r in transport.requests if r["method"] == "GET"]
    assert request["url"].endswith("/mission-proposals/P-9/milestones")


def test_json_post_patch_bodies(
    scripted_client: tuple[Prove2meClient, FakeTransport],
) -> None:
    """POST/PATCH endpoints send contract JSON bodies with auth header."""
    client, transport = scripted_client
    transport.script_response("POST", "fields", 200, b'{"id": "F-1"}')
    transport.script_response("POST", "mission-proposals", 200, b'{"id": "P-1"}')
    transport.script_response(
        "POST", "mission-proposals/P-1/items", 200, b'{"ok": true}'
    )
    transport.script_response("PATCH", "mission-proposals/P-1", 200, b'{"id": "P-1"}')

    client.create_field("geometry")
    client.create_proposal("P", description="d", field_ids=["f1"])
    client.add_proposal_item("P-1", "theorem", {"theorem_name": "t"})
    client.update_proposal("P-1", {"name": "renamed"})

    posts = [
        r
        for r in transport.requests
        if r["method"] in ("POST", "PATCH") and not r["url"].endswith("/agent/refresh")
    ]
    assert json.loads(posts[0]["body"]) == {"name": "geometry"}
    assert json.loads(posts[1]["body"]) == {
        "name": "P",
        "mission_type": "OpenProblem",
        "description": "d",
        "field_ids": ["f1"],
    }
    assert json.loads(posts[2]["body"]) == {"theorem_name": "t", "kind": "theorem"}
    assert json.loads(posts[3]["body"]) == {"name": "renamed"}
    assert posts[0]["headers"]["Content-Type"] == "application/json"
    assert posts[0]["headers"]["Authorization"] == f"Bearer {FAKE_TOKEN}"
    assert posts[1]["headers"]["Content-Type"] == "application/json"


def test_submit_proof_multipart_boundary_parse(
    scripted_client: tuple[Prove2meClient, FakeTransport],
) -> None:
    """/verify sends multipart/form-data with fields and the Lean file part."""
    client, transport = scripted_client
    transport.script_response("POST", "verify", 200, b'{"status": "PENDING"}')

    client.submit_proof(
        "T-1",
        "theorem t : True := trivial",
        proof_type="sketch",
        explanation="obvious",
    )

    (post,) = [
        r
        for r in transport.requests
        if r["method"] == "POST" and r["url"].endswith("/verify")
    ]
    content_type = post["headers"]["Content-Type"]
    assert content_type.startswith("multipart/form-data; boundary=")
    boundary = content_type.split("boundary=", 1)[1]
    body = post["body"]
    assert body is not None
    text = body.decode("utf-8")
    assert text.count(f"--{boundary}") >= 4
    assert 'name="theorem_id"' in text and "T-1" in text
    assert 'name="proof_type"' in text and "sketch" in text
    assert 'name="explanation"' in text and "obvious" in text
    assert 'filename="solution.lean"' in text
    assert "Content-Type: text/plain" in text
    assert "theorem t : True := trivial" in text
    assert text.rstrip().endswith(f"--{boundary}--")


# ── redaction ────────────────────────────────────────────────────────────────


def test_error_messages_redact_key_and_token(
    scripted_client: tuple[Prove2meClient, FakeTransport],
) -> None:
    """API failures embed body snippets with secrets masked out."""
    client, transport = scripted_client
    leak_body = (
        '{"error": "key ' + FAKE_KEY + " token " + FAKE_TOKEN + ' leaked?"}'
    ).encode("utf-8")
    transport.script_response("GET", "me", 503, leak_body)

    with pytest.raises(Prove2meAPIError) as excinfo:
        client.whoami()
    message = str(excinfo.value)
    assert FAKE_KEY not in message
    assert FAKE_TOKEN not in message
    assert excinfo.value.status_code == 503


def test_transport_exception_text_redacts_token(
    scripted_client: tuple[Prove2meClient, FakeTransport],
) -> None:
    """Foreign transport exceptions get the same redaction treatment."""
    client, _ = scripted_client
    client.refresh_token()  # cache FAKE_TOKEN so redaction is exercised

    class ExplodingTransport:
        def send(
            self,
            method: str,
            url: str,
            headers: Mapping[str, str],
            body: bytes | None,
            timeout_s: float,
        ) -> TransportResult:
            raise RuntimeError(f"socket died with token {FAKE_TOKEN} attached")

    client._transport = ExplodingTransport()
    with pytest.raises(Prove2meTransportError) as excinfo:
        client.whoami()
    message = str(excinfo.value)
    assert FAKE_TOKEN not in message
    assert FAKE_KEY not in message


# ── real urllib transport over loopback ──────────────────────────────────────


def _loopback_config(httpserver: HTTPServer) -> Prove2meConfig:
    return Prove2meConfig(
        base_url=httpserver.url_for("/api/v1").rstrip("/"), api_key=FAKE_KEY
    )


def test_loopback_refresh_and_whoami(httpserver: HTTPServer) -> None:
    """Real urllib transport: token exchange then authenticated GET /me."""
    httpserver.expect_request("/api/v1/agent/refresh", method="POST").respond_with_json(
        {"access_token": FAKE_TOKEN, "expires_at": time.time() + 3600, "version": "v3"}
    )
    httpserver.expect_request("/api/v1/me", method="GET").respond_with_json(
        {"agent": "loop"}
    )
    client = Prove2meClient(_loopback_config(httpserver))

    assert client.whoami() == {"agent": "loop"}
    assert client.platform_version == "v3"
    refresh = httpserver.log[0][0]
    assert json.loads(refresh.data) == {"api_key": FAKE_KEY}


def test_loopback_http_error_maps_to_api_error(httpserver: HTTPServer) -> None:
    """Real urllib transport: HTTPError becomes Prove2meAPIError(status_code)."""
    httpserver.expect_request("/api/v1/agent/refresh", method="POST").respond_with_json(
        {"access_token": FAKE_TOKEN, "expires_at": time.time() + 3600, "version": "v3"}
    )
    httpserver.expect_request("/api/v1/me", method="GET").respond_with_data(
        '{"error": "nope"}', status=418, content_type="application/json"
    )
    client = Prove2meClient(_loopback_config(httpserver))

    with pytest.raises(Prove2meAPIError) as excinfo:
        client.whoami()
    assert excinfo.value.status_code == 418


# ── poll timeout ─────────────────────────────────────────────────────────────


def test_wait_for_verdict_timeout_via_injected_sleep() -> None:
    """PENDING submissions past the deadline raise Prove2meTimeoutError."""
    transport = FakeTransport()
    clock = {"t": 0.0}
    sleeps: list[float] = []
    transport.script_response(
        "POST", "agent/refresh", 200, refresh_body(expires_at=clock["t"] + 10_000)
    )
    transport.script_response("GET", "verify", 200, b'{"status": "PENDING"}')

    def fake_sleep(seconds: float) -> None:
        sleeps.append(seconds)
        clock["t"] += seconds

    client = make_client(transport, now=lambda: clock["t"], sleep=fake_sleep)

    with pytest.raises(Prove2meTimeoutError) as excinfo:
        wait_for_verdict(client, "S-7", timeout_s=1.0, poll_s=2.0)
    assert "S-7" in str(excinfo.value)
    assert sleeps  # the poll loop slept between attempts
