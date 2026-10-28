"""gauss — OpenGauss integration layer.

Provides the OpenGauss CLI connector, the SQLite session client, and the
orchestrator that binds the LLM and verification layers.

Public API
----------
    check_gauss_cli       — probes isolated local CLI availability
    OpenGaussClient       — SQLite database client for topics/turns/logs
    SessionRecord         — data structure for an open session
    GaussRunner           — orchestrator running topics through LLM then Lean
    TopicRunResult        — outcome of a formalization run
"""

from fep_formal.gauss.cli import check_gauss_cli
from fep_formal.gauss.client import OpenGaussClient, SessionRecord
from fep_formal.gauss.runner import GaussRunner, TopicRunResult

__all__ = [
    "GaussRunner",
    "OpenGaussClient",
    "SessionRecord",
    "TopicRunResult",
    "check_gauss_cli",
]
