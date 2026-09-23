"""prove2me — client for the Prove2me Lean-formalization platform.

Prove2me (https://prove2.me) hosts formalized theorem statements and accepts
Lean 4 proof submissions for automated verification.  This package provides a
stdlib-only (``urllib``) HTTP client with API-key authentication (token
exchange cached until shortly before expiry, one re-exchange and retry on 401),
theorem/field/mission queries, mission-proposal authoring, multipart proof
submission, and verdict polling.  The API key is resolved by
``Prove2meConfig.load`` from an explicit argument, the environment, or
credentials files, and is redacted from representations and error messages;
see ``docs/prove2me.md``.

Public API
----------
    Prove2meConfig      — configuration + API-key resolution
    Prove2meClient      — authenticated API client
    Prove2meTransport   — transport protocol (injection seam for tests)
    TransportResult     — transport return type ``(http_status, body)``
    draft_proposal      — create a mission proposal
    add_theorem_item    — attach a theorem entry to a proposal
    submit_solution     — submit a Lean proof for verification
    wait_for_verdict    — poll a submission until a terminal verdict
    Prove2me*Error      — error hierarchy rooted at ``Prove2meError``
    redact_secret       — full secret masking helper
"""

from fep_lean.prove2me.client import (
    Prove2meClient,
    Prove2meTransport,
    TransportResult,
)
from fep_lean.prove2me.config import (
    Prove2meAPIError,
    Prove2meAuthError,
    Prove2meConfig,
    Prove2meConfigError,
    Prove2meError,
    Prove2meTimeoutError,
    Prove2meTransportError,
    redact_secret,
)
from fep_lean.prove2me.missions import (
    add_theorem_item,
    draft_proposal,
    submit_solution,
    wait_for_verdict,
)

__all__ = [
    "Prove2meAPIError",
    "Prove2meAuthError",
    "Prove2meClient",
    "Prove2meConfig",
    "Prove2meConfigError",
    "Prove2meError",
    "Prove2meTimeoutError",
    "Prove2meTransport",
    "Prove2meTransportError",
    "TransportResult",
    "add_theorem_item",
    "draft_proposal",
    "redact_secret",
    "submit_solution",
    "wait_for_verdict",
]
