"""Seam types for the H2.7 custody census: status vocabulary and records.

The census classifies every custody surface against the live tree with three
statuses. ``intact`` means the recorded custody value equals the live value.
``stale`` means recorded evidence predates a live change: the receipt-side
staleness a custody chore legitimately re-binds or re-captures. ``live-red``
means a structural or semantic break — a missing or unparseable receipt, a
drifted ``PREDECESSORS`` pin, or custody semantics the validator itself
rejects — which no re-bind of the recorded values may paper over.

The FEP-H27-RESEAL row (TODO.md) is the reference case: the native capture
stale on exactly the 2026-09-21 tests-wave files while the terminal receipt,
the ``PREDECESSORS`` constant, and the 07-gaussian-vfe-natural-gradient R0
successor custody stay intact.
"""

from __future__ import annotations

from dataclasses import dataclass

INTACT = "intact"
STALE = "stale"
LIVE_RED = "live-red"
STATUS_VOCABULARY = frozenset({INTACT, STALE, LIVE_RED})


@dataclass(frozen=True)
class CensusRecord:
    """One custody surface's classification: precise path, status, detail."""

    path: str
    status: str
    detail: str

    def __post_init__(self) -> None:
        if not isinstance(self.path, str) or not self.path:
            raise ValueError("census record path must be a non-empty string")
        if self.status not in STATUS_VOCABULARY:
            raise ValueError(
                f"census record status {self.status!r} outside "
                f"{sorted(STATUS_VOCABULARY)}"
            )
        if not isinstance(self.detail, str) or not self.detail:
            raise ValueError("census record detail must be a non-empty string")


@dataclass(frozen=True)
class Census:
    """An ordered, duplicate-free census over the H2.7 custody surface.

    Census-green is necessary, not sufficient, for
    ``validate_terminal_acceptance``: the census enumerates the custody chain
    and the native capture, not the packet's frozen evidence artifacts.
    """

    records: tuple[CensusRecord, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.records, tuple) or not all(
            isinstance(record, CensusRecord) for record in self.records
        ):
            raise ValueError("census records must be a tuple of CensusRecord")
        seen: set[str] = set()
        for record in self.records:
            if record.path in seen:
                raise ValueError(f"duplicate census surface: {record.path}")
            seen.add(record.path)

    def status_of(self, path: str) -> str | None:
        """The recorded status for one surface, or ``None`` if not censused."""
        for record in self.records:
            if record.path == path:
                return record.status
        return None

    def stale(self) -> tuple[CensusRecord, ...]:
        """Evidence predating live changes: the chore's re-bind territory."""
        return tuple(record for record in self.records if record.status == STALE)

    def live_red(self) -> tuple[CensusRecord, ...]:
        """Structural breaks: unexplained drift the validator would reject."""
        return tuple(record for record in self.records if record.status == LIVE_RED)

    def is_gated(self) -> bool:
        """True iff any surface is non-intact, so the H2.7 gate cannot pass."""
        return any(record.status != INTACT for record in self.records)
