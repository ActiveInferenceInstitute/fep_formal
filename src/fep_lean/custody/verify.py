"""Gate verdicts: a custody census compared against declared expectations.

``verify`` is a strict comparator, not a validator: it never reads the tree
or re-derives any custody value. Expectations carry the required-intact
surfaces and the authorized-stale set (a chore's forced-change set); a
``live-red`` record is never authorized, because a structural break is not
re-bind territory.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from fep_lean.custody.census import VALIDATOR_PATH
from fep_lean.custody.model import (
    INTACT,
    STALE,
    Census,
)
from fep_lean.verification import horizon_acceptance as acceptance
from fep_lean.verification.horizon_acceptance import TERMINAL_RECEIPT


@dataclass(frozen=True)
class Expectations:
    """The declared custody state a census must satisfy.

    ``required_intact`` surfaces must appear in the census and be intact;
    ``allowed_stale`` surfaces may come back ``stale`` (the authorized
    capture-refresh residual). Any ``live-red`` record fails regardless.
    """

    required_intact: tuple[str, ...] = ()
    allowed_stale: frozenset[str] = field(default_factory=frozenset)


def gate_expectations() -> Expectations:
    """Strict gate: the terminal receipt, validator constant, and every
    pinned predecessor must be intact. Read from the imported module object
    so a chore's PREDECESSORS patch is honored without a re-import.
    """
    return Expectations(
        required_intact=(TERMINAL_RECEIPT, VALIDATOR_PATH, *acceptance.PREDECESSORS)
    )


GATE_EXPECTATIONS = gate_expectations()


def verify(census: Census, expectations: Expectations) -> tuple[bool, list[str]]:
    """Return ``(ok, problems)`` for the census against the expectations.

    Every non-intact record is a problem unless it is stale on a surface the
    expectations authorize; every required surface absent from the census is
    a problem; a required surface that came back non-intact is already
    reported through its record and never authorized by ``allowed_stale``.
    """
    problems: list[str] = []
    for record in census.records:
        if record.status == INTACT:
            continue
        if (
            record.status == STALE
            and record.path in expectations.allowed_stale
            and record.path not in expectations.required_intact
        ):
            continue
        problems.append(f"{record.status}: {record.path}: {record.detail}")
    for path in expectations.required_intact:
        if census.status_of(path) is None:
            problems.append(f"missing from census: {path}")
    return (not problems, problems)
