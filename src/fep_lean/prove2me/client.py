"""Prove2me HTTP client: authenticated REST access with typed errors.

Implements the t-0024 shared contract on top of the standard library only.
A :class:`Prove2meTransport` protocol lets tests inject in-memory fakes; the
default transport mirrors the ``fep_lean.llm.hermes`` hardening: a wall-clock
deadline enforced by a daemon worker thread, bounded reads (64 KiB chunks,
8 MiB cap), ``HTTPError`` mapped to
:class:`~fep_lean.prove2me.config.Prove2meAPIError` with the status code, and
network/timeout/OSError/non-JSON failures mapped to
:class:`~fep_lean.prove2me.config.Prove2meTransportError`.

Authentication exchanges the configured api key for an access token via an
unauthenticated ``POST /agent/refresh``; the token is cached and reused until
60 s before its ``expires_at``.  Any authenticated call that receives 401
triggers exactly one re-exchange and one retry; a second 401 raises
:class:`~fep_lean.prove2me.config.Prove2meAuthError` and never loops.

The api key appears only in the token-exchange request body.  Response
snippets and exception text are passed through a redactor that masks the api
key and the current access token before they reach any error message, and
request headers are never embedded in messages.
"""

from __future__ import annotations

import contextlib
import http.client
import json
import socket
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from collections.abc import Callable, Mapping, Sequence
from typing import Any, Protocol

from fep_lean.prove2me.config import (
    Prove2meAPIError,
    Prove2meAuthError,
    Prove2meConfig,
    Prove2meConfigError,
    Prove2meError,
    Prove2meTransportError,
)

__all__ = [
    "Prove2meClient",
    "Prove2meTransport",
    "TransportResult",
]

TransportResult = tuple[int, bytes]

_MAX_RESPONSE_CHUNK = 64 * 1024
_MAX_RESPONSE_BYTES = 8 * 1024 * 1024
_TOKEN_EXPIRY_SKEW_S = 60.0
_SNIPPET_CHARS = 300
_REDACTED = "***"


class Prove2meTransport(Protocol):
    """Blocking HTTP seam: one request in, ``(http_status, body)`` out."""

    def send(
        self,
        method: str,
        url: str,
        headers: Mapping[str, str],
        body: bytes | None,
        timeout_s: float,
    ) -> TransportResult:
        """Perform one HTTP request and return status and raw body bytes."""
        ...


class _UrllibTransport:
    """Default transport: stdlib urllib with hermes-style wall-clock guards.

    ``urllib``'s ``timeout`` argument bounds individual socket operations
    (connect, each read), not total wall time, so the blocking ``urlopen``
    plus bounded read run in a daemon worker thread that is abandoned — and
    whose open response socket is shut down — at the deadline.  Reads are
    capped at 8 MiB in 64 KiB chunks so a misbehaving endpoint cannot stream
    without end.
    """

    def send(
        self,
        method: str,
        url: str,
        headers: Mapping[str, str],
        body: bytes | None,
        timeout_s: float,
    ) -> TransportResult:
        req = urllib.request.Request(
            url, data=body, headers=dict(headers), method=method
        )
        result: dict[str, Any] = {}
        response_holder: list[Any] = []

        def _do_request() -> None:
            try:
                with urllib.request.urlopen(req, timeout=timeout_s) as resp:
                    response_holder.append(resp)
                    result["status"] = int(resp.status)
                    chunks: list[bytes] = []
                    total = 0
                    while True:
                        chunk = resp.read(_MAX_RESPONSE_CHUNK)
                        if not chunk:
                            break
                        total += len(chunk)
                        if total > _MAX_RESPONSE_BYTES:
                            result["exc"] = Prove2meTransportError(
                                f"response exceeds {_MAX_RESPONSE_BYTES} bytes; "
                                "rejecting oversized stream"
                            )
                            return
                        chunks.append(chunk)
                    result["raw"] = b"".join(chunks)
            except BaseException as inner_exc:  # re-raised on the calling thread
                result["exc"] = inner_exc

        worker = threading.Thread(target=_do_request, name="prove2me-http", daemon=True)
        worker.start()
        worker.join(timeout=timeout_s)
        if worker.is_alive():
            # Release the parked worker's socket buffer instead of letting it
            # accumulate until the endpoint closes the stream (see hermes.py).
            self._shutdown_response(response_holder[0] if response_holder else None)
            raise Prove2meTransportError(
                f"wall-clock timeout after {timeout_s}s; abandoning request"
            )
        if "exc" in result:
            raise self._classify(result["exc"])
        return int(result["status"]), result["raw"]

    @staticmethod
    def _shutdown_response(resp: Any) -> None:
        if resp is None:
            return
        with contextlib.suppress(OSError, ValueError, AttributeError):
            fp = getattr(resp, "fp", None)
            raw = getattr(fp, "raw", None) or fp
            sock_obj = getattr(raw, "_sock", None)
            if sock_obj is not None:
                sock_obj.shutdown(socket.SHUT_RDWR)
        with contextlib.suppress(OSError, ValueError):
            resp.close()

    @staticmethod
    def _classify(exc: BaseException) -> Prove2meError:
        """Map transport-layer failures onto the Prove2me error hierarchy."""
        if isinstance(exc, Prove2meError):
            return exc
        if isinstance(exc, urllib.error.HTTPError):
            try:
                body_text = exc.read().decode("utf-8", errors="replace")
            except OSError:
                body_text = ""
            return Prove2meAPIError(
                f"HTTP {exc.code}: {exc.reason} — {body_text[:_SNIPPET_CHARS]}",
                status_code=exc.code,
            )
        if isinstance(exc, urllib.error.URLError):
            return Prove2meTransportError(f"network error: {exc.reason}")
        if isinstance(exc, http.client.HTTPException):
            return Prove2meTransportError(
                f"HTTP transport error ({type(exc).__name__}): {exc}"
            )
        if isinstance(exc, (TimeoutError, OSError)):
            return Prove2meTransportError(
                f"connection error ({type(exc).__name__}): {exc}"
            )
        return Prove2meTransportError(
            f"unexpected transport failure ({type(exc).__name__}): {exc}"
        )


def _encode_multipart(
    fields: Mapping[str, str],
    file_field: str,
    filename: str,
    file_content: str,
    file_content_type: str,
) -> tuple[bytes, str]:
    """Encode ``fields`` plus one file part as multipart/form-data (stdlib)."""
    boundary = uuid.uuid4().hex
    lines: list[bytes] = []
    for name, value in fields.items():
        lines.extend(
            [
                f"--{boundary}".encode("ascii"),
                f'Content-Disposition: form-data; name="{name}"'.encode("ascii"),
                b"",
                value.encode("utf-8"),
            ]
        )
    lines.extend(
        [
            f"--{boundary}".encode("ascii"),
            (
                "Content-Disposition: form-data; "
                f'name="{file_field}"; filename="{filename}"'
            ).encode("ascii"),
            f"Content-Type: {file_content_type}".encode("ascii"),
            b"",
            file_content.encode("utf-8"),
        ]
    )
    lines.append(f"--{boundary}--".encode("ascii"))
    body = b"\r\n".join(lines) + b"\r\n"
    return body, f"multipart/form-data; boundary={boundary}"


class Prove2meClient:
    """Authenticated client for the Prove2me REST API.

    Construct with a :class:`~fep_lean.prove2me.config.Prove2meConfig`; pass
    ``transport`` to replace the default urllib transport (tests inject
    in-memory fakes).  ``now`` and ``sleep`` are injectable clocks used for
    token-expiry bookkeeping and polling, respectively.
    """

    def __init__(
        self,
        config: Prove2meConfig,
        *,
        transport: Prove2meTransport | None = None,
        timeout_s: float = 30.0,
        now: Callable[[], float] = time.time,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._config = config
        self._transport: Prove2meTransport = (
            transport if transport is not None else _UrllibTransport()
        )
        self._timeout_s = timeout_s
        self.now = now
        self.sleep = sleep
        self.platform_version: str | None = None
        self._token: str | None = None
        self._token_expires_at: float | None = None

    # ── public endpoints ─────────────────────────────────────────────────────

    def refresh_token(self) -> None:
        """Force a token re-exchange, discarding any cached token."""
        self._exchange()

    def whoami(self) -> dict[str, Any]:
        """Return the authenticated agent profile. GET /me"""
        return self._request("GET", "/me")

    def search_fields(self, q: str) -> dict[str, Any]:
        """Search formalization fields. GET /fields?q="""
        return self._request("GET", "/fields", params={"q": q})

    def create_field(self, name: str) -> dict[str, Any]:
        """Create a formalization field. POST /fields body {"name": name}"""
        return self._request("POST", "/fields", json_body={"name": name})

    def list_missions(self, limit: int = 20, offset: int = 0) -> dict[str, Any]:
        """List missions. GET /missions?limit&offset"""
        return self._request(
            "GET", "/missions", params={"limit": limit, "offset": offset}
        )

    def search_theorems(
        self,
        *,
        q: str | None = None,
        status: str | None = None,
        sort: str | None = None,
        tags: Sequence[str] | None = None,
    ) -> dict[str, Any]:
        """Search theorems. GET /theorems?q&status&sort&tags.

        ``tags`` is a single comma-joined query parameter (the platform
        matches theorems carrying ALL of the listed tags).
        """
        return self._request(
            "GET",
            "/theorems",
            params={
                "q": q,
                "status": status,
                "sort": sort,
                "tags": ",".join(tags) if tags else None,
            },
        )

    def get_theorem(self, theorem_id: str) -> dict[str, Any]:
        """Fetch one theorem. GET /theorems/:id"""
        return self._request(
            "GET", f"/theorems/{urllib.parse.quote(theorem_id, safe='')}"
        )

    def submit_proof(
        self,
        theorem_id: str,
        solution_lean: str,
        *,
        proof_type: str = "prove",
        explanation: str | None = None,
    ) -> dict[str, Any]:
        """Submit a Lean proof for verification. POST /verify (multipart)."""
        fields = {"theorem_id": theorem_id, "proof_type": proof_type}
        if explanation is not None:
            fields["explanation"] = explanation
        body, content_type = _encode_multipart(
            fields, "file", "solution.lean", solution_lean, "text/plain"
        )
        return self._request("POST", "/verify", data=body, content_type=content_type)

    def get_submission(self, submission_id: str) -> dict[str, Any]:
        """Fetch a submission's verification state. GET /verify?submission_id="""
        return self._request("GET", "/verify", params={"submission_id": submission_id})

    def create_proposal(
        self,
        name: str,
        *,
        description: str | None = None,
        mission_type: str = "OpenProblem",
        field_ids: Sequence[str] | None = None,
        env: str | None = None,
        visibility: str | None = None,
    ) -> dict[str, Any]:
        """Create a mission proposal. POST /mission-proposals (None fields omitted)."""
        payload: dict[str, Any] = {"name": name, "mission_type": mission_type}
        if description is not None:
            payload["description"] = description
        if field_ids is not None:
            payload["field_ids"] = list(field_ids)
        if env is not None:
            payload["env"] = env
        if visibility is not None:
            payload["visibility"] = visibility
        return self._request("POST", "/mission-proposals", json_body=payload)

    def add_proposal_item(
        self, proposal_id: str, kind: str, payload: Mapping[str, Any]
    ) -> dict[str, Any]:
        """Append one item to a proposal. POST /mission-proposals/:id/items.

        The payload mapping is sent as-is with ``"kind"`` added.
        """
        body: dict[str, Any] = dict(payload)
        body["kind"] = kind
        return self._request(
            "POST",
            f"/mission-proposals/{urllib.parse.quote(proposal_id, safe='')}/items",
            json_body=body,
        )

    def get_proposal(self, proposal_id: str) -> dict[str, Any]:
        """Fetch one mission proposal. GET /mission-proposals/:id"""
        return self._request(
            "GET", f"/mission-proposals/{urllib.parse.quote(proposal_id, safe='')}"
        )

    def list_proposal_milestones(self, proposal_id: str) -> dict[str, Any]:
        """List a proposal's milestones. GET /mission-proposals/:id/milestones"""
        return self._request(
            "GET",
            f"/mission-proposals/{urllib.parse.quote(proposal_id, safe='')}/milestones",
        )

    def update_proposal(
        self, proposal_id: str, fields: Mapping[str, Any]
    ) -> dict[str, Any]:
        """Patch a mission proposal. PATCH /mission-proposals/:id"""
        return self._request(
            "PATCH",
            f"/mission-proposals/{urllib.parse.quote(proposal_id, safe='')}",
            json_body=dict(fields),
        )

    # ── request plumbing ─────────────────────────────────────────────────────

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json_body: Mapping[str, Any] | None = None,
        data: bytes | None = None,
        content_type: str | None = None,
    ) -> dict[str, Any]:
        """Build URL and body, send authenticated, and parse the JSON object."""
        url = self._build_url(path, params)
        headers: dict[str, str] = {}
        body: bytes | None = None
        if json_body is not None:
            body = json.dumps(json_body).encode("utf-8")
            headers["Content-Type"] = "application/json"
        elif data is not None:
            body = data
            if content_type is not None:
                headers["Content-Type"] = content_type
        status, raw = self._send(method, url, headers, body)
        return self._parse_json(method, path, status, raw)

    def _send(
        self,
        method: str,
        url: str,
        headers: dict[str, str],
        body: bytes | None,
    ) -> TransportResult:
        """Send an authenticated request with the single 401 re-exchange retry."""
        if self._token_usable() and self._token is not None:
            token = self._token
        else:
            token = self._exchange()
        headers["Authorization"] = f"Bearer {token}"
        status, raw = self._call_transport(method, url, headers, body)
        if status != 401:
            return status, raw
        # Exactly one re-exchange and one retry; a second 401 is terminal.
        token = self._exchange()
        headers["Authorization"] = f"Bearer {token}"
        status, raw = self._call_transport(method, url, headers, body)
        if status == 401:
            raise Prove2meAuthError(
                "API key expired: request rejected with HTTP 401 even after a "
                "fresh token exchange",
                status_code=401,
            )
        return status, raw

    def _exchange(self) -> str:
        """Exchange the api key for a fresh access token (POST /agent/refresh)."""
        api_key = self._config.api_key
        if not api_key:
            raise Prove2meConfigError(
                "no Prove2me api key configured; cannot exchange for a token"
            )
        body = json.dumps({"api_key": api_key}).encode("utf-8")
        url = self._build_url("/agent/refresh")
        status, raw = self._call_transport(
            "POST", url, {"Content-Type": "application/json"}, body
        )
        if status == 401:
            raise Prove2meAuthError(
                "API key expired: token exchange rejected with HTTP 401",
                status_code=401,
            )
        parsed = self._parse_json("POST", "/agent/refresh", status, raw)
        token = parsed.get("access_token")
        expires_at = parsed.get("expires_at")
        if not isinstance(token, str) or not token:
            raise Prove2meTransportError(
                "token exchange response is missing a usable access_token"
            )
        if not isinstance(expires_at, (int, float)) or isinstance(expires_at, bool):
            raise Prove2meTransportError(
                "token exchange response is missing a usable expires_at"
            )
        self._token = token
        self._token_expires_at = float(expires_at)
        version = parsed.get("version")
        self.platform_version = version if isinstance(version, str) else None
        return token

    def _token_usable(self) -> bool:
        """True while the cached token outlives the 60 s expiry skew margin."""
        if self._token is None or self._token_expires_at is None:
            return False
        return self.now() < self._token_expires_at - _TOKEN_EXPIRY_SKEW_S

    def _call_transport(
        self,
        method: str,
        url: str,
        headers: dict[str, str],
        body: bytes | None,
    ) -> TransportResult:
        """Run one transport call, typing and sanitizing any failure.

        Typed errors pass through unchanged in kind — the default transport
        raises :class:`Prove2meAPIError` for HTTP errors — but their message
        is re-redacted because the transport embeds response snippets
        verbatim.  Foreign exceptions become
        :class:`Prove2meTransportError` so callers only ever see
        ``Prove2meError`` subclasses.
        """
        try:
            return self._transport.send(method, url, headers, body, self._timeout_s)
        except Prove2meError as exc:
            raise type(exc)(
                self._redact(str(exc)), status_code=exc.status_code
            ) from exc
        except Exception as exc:
            raise Prove2meTransportError(
                f"{method} request failed ({type(exc).__name__}): "
                f"{self._redact(str(exc))}"
            ) from exc

    def _parse_json(
        self, method: str, path: str, status: int, raw: bytes
    ) -> dict[str, Any]:
        """Validate status, parse the body, and require a JSON object."""
        if not 200 <= status < 300:
            raise Prove2meAPIError(
                f"{method} {path} failed with HTTP {status}: {self._snippet(raw)}",
                status_code=status,
            )
        try:
            parsed = json.loads(raw)
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise Prove2meTransportError(
                f"{method} {path} returned a non-JSON body: {exc}"
            ) from exc
        if not isinstance(parsed, dict):
            raise Prove2meTransportError(
                f"{method} {path} returned JSON that is not an object"
            )
        return parsed

    def _build_url(self, path: str, params: Mapping[str, Any] | None = None) -> str:
        """Join base_url and path, appending non-empty query parameters."""
        url = self._config.base_url.rstrip("/") + "/" + path.lstrip("/")
        if not params:
            return url
        filtered: list[tuple[str, Any]] = []
        for key, value in params.items():
            if value is None or value == "":
                continue
            if isinstance(value, Sequence) and not value:
                continue
            filtered.append((key, value))
        if filtered:
            url += "?" + urllib.parse.urlencode(filtered, doseq=True)
        return url

    def _snippet(self, raw: bytes) -> str:
        """Redact then truncate a response body for error messages."""
        return self._redact(raw.decode("utf-8", errors="replace"))[:_SNIPPET_CHARS]

    def _redact(self, text: str) -> str:
        """Mask the api key and the current access token inside ``text``."""
        for secret in (self._config.api_key, self._token):
            if secret and secret in text:
                text = text.replace(secret, _REDACTED)
        return text
