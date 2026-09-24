"""H2.7 evidence-custody surfaces: census records, gate verification, and apply.

``model`` owns the census seam types (status vocabulary, records), ``census``
the read-only drift classification, and ``verify`` the all-clear gate; the
``apply``/``cli`` machinery belongs to the custody-CLI consumer.
"""

from __future__ import annotations

from fep_lean.custody.census import AUTHORIZED_PRIOR_DRIFT, VALIDATOR_PATH, census
from fep_lean.custody.model import (
    INTACT,
    LIVE_RED,
    STALE,
    STATUS_VOCABULARY,
    Census,
    CensusRecord,
)
from fep_lean.custody.verify import GATE_EXPECTATIONS, Expectations, verify

__all__ = [
    "AUTHORIZED_PRIOR_DRIFT",
    "GATE_EXPECTATIONS",
    "INTACT",
    "LIVE_RED",
    "STALE",
    "STATUS_VOCABULARY",
    "VALIDATOR_PATH",
    "Census",
    "CensusRecord",
    "Expectations",
    "census",
    "verify",
]
