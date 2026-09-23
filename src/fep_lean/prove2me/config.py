"""Prove2me configuration and error types for the fep_lean integration.

Implements the shared t-0024 contract: a small error hierarchy, a fully
redacting configuration object, and a five-step credential-resolution chain
(explicit argument > ``PROVE2ME_API_KEY`` environment variable > credentials
file named by ``PROVE2ME_CREDENTIALS`` > ``~/.prove2me/credentials.json`` >
``~/prove2me_workspace/credentials.json``).  Stdlib only.
"""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

DEFAULT_BASE_URL = "https://prove2.me/api/v1"
ENV_VAR = "PROVE2ME_API_KEY"
CREDENTIALS_ENV_VAR = "PROVE2ME_CREDENTIALS"  # value = path to a credentials.json file
CREDENTIALS_FILENAME = "credentials.json"


class Prove2meError(Exception):
    """Base class for every Prove2me integration error.

    The message must never contain secret material: raise sites must redact
    API keys and access tokens out of any text embedded in ``message``.
    """

    status_code: int | None

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class Prove2meConfigError(Prove2meError):
    """Missing key, unreadable/malformed credentials file, or bad settings."""


class Prove2meAuthError(Prove2meError):
    """401 persists after one re-exchange, or the token exchange failed."""


class Prove2meAPIError(Prove2meError):
    """Non-2xx response from a normal API call (``status_code`` is set)."""


class Prove2meTransportError(Prove2meError):
    """Network failure or non-JSON body (``status_code`` is ``None``)."""


class Prove2meTimeoutError(Prove2meError):
    """Poll deadline exceeded while waiting for a terminal submission status."""


def redact_secret(value: str) -> str:
    """Full mask, zero secret material: '' -> '<unset>', else 'p2m_***<len-N>'."""
    if not value:
        return "<unset>"
    return f"p2m_***<len-{len(value)}>"


@dataclass
class Prove2meConfig:
    """Connection settings for the Prove2me client.

    Build with :meth:`load` to run the credential-resolution chain, or
    construct directly (e.g. in tests).  ``api_key`` is never exposed
    through ``repr`` — it is always rendered via :func:`redact_secret`.
    """

    base_url: str = DEFAULT_BASE_URL
    api_key: str = ""

    def __repr__(self) -> str:
        return (
            f"Prove2meConfig(base_url={self.base_url!r}, "
            f"api_key={redact_secret(self.api_key)!r})"
        )

    @classmethod
    def load(
        cls,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        env: Mapping[str, str] | None = None,
        home: Path | None = None,
    ) -> Prove2meConfig:
        """Resolve configuration via the five-step key-resolution chain.

        Resolution order (first non-empty candidate wins):

        1. the explicit ``api_key`` argument;
        2. the ``PROVE2ME_API_KEY`` environment variable;
        3. the credentials file whose path is stored in the
           ``PROVE2ME_CREDENTIALS`` environment variable;
        4. ``<home>/.prove2me/credentials.json``;
        5. ``<home>/prove2me_workspace/credentials.json``.

        A credentials file is a JSON object whose ``api_key`` entry holds the
        key (stripped, non-empty).  A credentials file that exists but is
        unreadable, contains malformed JSON, or lacks a usable ``api_key``
        entry raises :class:`Prove2meConfigError` naming that path.  When
        nothing resolves, :class:`Prove2meConfigError` is raised listing the
        searched locations (paths only — never file contents).  ``env``
        defaults to ``os.environ``; ``home`` defaults to ``Path.home()``.
        """
        env_map: Mapping[str, str] = os.environ if env is None else env
        home_dir = Path.home() if home is None else home

        resolved_key = _first_non_empty(api_key, env_map.get(ENV_VAR))
        if resolved_key is not None:
            return cls(
                base_url=base_url if base_url else DEFAULT_BASE_URL,
                api_key=resolved_key,
            )

        searched: list[Path] = []
        credentials_env_path = env_map.get(CREDENTIALS_ENV_VAR, "").strip()
        candidates: list[Path] = []
        if credentials_env_path:
            candidates.append(Path(credentials_env_path))
        candidates.append(home_dir / ".prove2me" / CREDENTIALS_FILENAME)
        candidates.append(home_dir / "prove2me_workspace" / CREDENTIALS_FILENAME)

        for candidate in candidates:
            searched.append(candidate)
            resolved_key = _key_from_credentials_file(candidate)
            if resolved_key is not None:
                break

        if resolved_key is None:
            locations = "; ".join(str(path) for path in searched)
            raise Prove2meConfigError(
                "No Prove2me API key resolved; checked the "
                f"{ENV_VAR} environment variable and the following credential "
                f"locations: {locations}"
            )

        return cls(
            base_url=base_url if base_url else DEFAULT_BASE_URL,
            api_key=resolved_key,
        )


def _first_non_empty(*candidates: str | None) -> str | None:
    """Return the first candidate that is a non-empty (stripped) string."""
    for candidate in candidates:
        if candidate is not None and candidate.strip():
            return candidate.strip()
    return None


def _key_from_credentials_file(path: Path) -> str | None:
    """Read the credential entry from a credentials JSON file.

    Returns ``None`` when no file exists at *path* (``ENOENT``/``ENOTDIR`` —
    the candidate is simply absent and the caller moves on).  Raises
    :class:`Prove2meConfigError` when an existing file is unreadable,
    malformed JSON, not a JSON object, or lacks a usable ``api_key`` entry.
    Error messages name the path but never quote file contents.
    """
    try:
        raw = path.read_text(encoding="utf-8")
    except (FileNotFoundError, NotADirectoryError):
        return None
    except UnicodeDecodeError as exc:
        raise Prove2meConfigError(
            f"Prove2me credentials file {path} is not valid UTF-8"
        ) from exc
    except OSError as exc:
        raise Prove2meConfigError(
            f"Could not read Prove2me credentials file {path}: {exc.strerror}"
        ) from exc
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        # Use exc.msg only: it is a generic parser message, never a document
        # snippet, so no credential material can leak into the error text.
        raise Prove2meConfigError(
            f"Prove2me credentials file {path} contains malformed JSON: {exc.msg}"
        ) from exc
    if not isinstance(payload, dict):
        raise Prove2meConfigError(
            f"Prove2me credentials file {path} must contain a JSON object"
        )
    entry = payload.get("api_key")
    if not isinstance(entry, str) or not entry.strip():
        raise Prove2meConfigError(
            f"Prove2me credentials file {path} has no usable api_key entry"
        )
    return entry.strip()
