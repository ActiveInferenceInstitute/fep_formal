"""Thin helpers for mission proposals and proof verification on Prove2me.

These functions compose :class:`~fep_lean.prove2me.client.Prove2meClient`
calls into the small workflows used when authoring mission proposals and
checking verification verdicts.  Payloads omit ``None`` fields, mirroring the
client's own parameter handling.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from fep_lean.prove2me.client import Prove2meClient
from fep_lean.prove2me.config import Prove2meTimeoutError

__all__ = [
    "add_theorem_item",
    "draft_proposal",
    "submit_solution",
    "wait_for_verdict",
]


def draft_proposal(
    client: Prove2meClient,
    *,
    name: str,
    description: str | None = None,
    mission_type: str = "OpenProblem",
    field_ids: Sequence[str] | None = None,
    env: str | None = None,
    visibility: str | None = None,
) -> dict[str, Any]:
    """Create a mission proposal from the captain payload.

    Builds the proposal payload (``name``, ``description``, ``mission_type``,
    ``field_ids``, ``env``, ``visibility`` -- omitting ``None`` fields) and
    delegates to :meth:`Prove2meClient.create_proposal`.
    """
    payload: dict[str, Any] = {"name": name, "mission_type": mission_type}
    if description is not None:
        payload["description"] = description
    if field_ids is not None:
        payload["field_ids"] = field_ids
    if env is not None:
        payload["env"] = env
    if visibility is not None:
        payload["visibility"] = visibility
    return client.create_proposal(**payload)


def add_theorem_item(
    client: Prove2meClient,
    proposal_id: str,
    *,
    theorem_name: str,
    formal_statement: str,
    theorem_title: str | None = None,
    natural_language_statement: str | None = None,
    preamble: str = "",
    source: str = "",
    tags: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Attach a theorem entry (the contribute.md body) to a proposal.

    Builds the theorem payload -- required ``theorem_name`` and
    ``formal_statement``, empty-string ``preamble``/``source`` defaults, and
    the optional fields only when not ``None`` -- and delegates to
    :meth:`Prove2meClient.add_proposal_item` with kind ``"theorem"``.
    """
    payload: dict[str, Any] = {
        "theorem_name": theorem_name,
        "formal_statement": formal_statement,
        "preamble": preamble,
        "source": source,
    }
    if theorem_title is not None:
        payload["theorem_title"] = theorem_title
    if natural_language_statement is not None:
        payload["natural_language_statement"] = natural_language_statement
    if tags is not None:
        payload["tags"] = tags
    return client.add_proposal_item(proposal_id, "theorem", payload)


def submit_solution(
    client: Prove2meClient,
    theorem_id: str,
    solution_lean: str,
    *,
    proof_type: str = "prove",
    explanation: str | None = None,
) -> dict[str, Any]:
    """Submit a Lean solution for verification via the client's ``/verify`` call."""
    return client.submit_proof(
        theorem_id,
        solution_lean,
        proof_type=proof_type,
        explanation=explanation,
    )


def wait_for_verdict(
    client: Prove2meClient,
    submission_id: str,
    *,
    timeout_s: float = 600.0,
    poll_s: float = 5.0,
) -> dict[str, Any]:
    """Poll a submission until a terminal verdict or the deadline.

    Calls :meth:`Prove2meClient.get_submission` in a loop: a ``"PENDING"``
    status sleeps ``poll_s`` seconds (via ``client.sleep``) and retries; any
    other status (``ACCEPTED``, ``SKETCH_ACCEPTED``, ``CE``, ``WA``,
    ``SORRY``, ``FAILED``, ``ERROR``) is terminal and the submission document
    is returned.  When the wall-clock deadline (``client.now()`` start plus
    ``timeout_s``) elapses while still pending, raises
    :class:`~fep_lean.prove2me.config.Prove2meTimeoutError` naming the
    submission id and the last observed status.
    """
    deadline = client.now() + timeout_s
    while True:
        submission = client.get_submission(submission_id)
        status = submission.get("status")
        if status != "PENDING":
            return submission
        if client.now() >= deadline:
            raise Prove2meTimeoutError(
                f"submission {submission_id} still pending "
                f"(last status {status!r}) after {timeout_s} s"
            )
        client.sleep(poll_s)
