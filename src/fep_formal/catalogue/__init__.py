"""Catalog data model, roster seal, and canonical Lean body registry.

The exact roster count is derived from the packaged schema-2 seal.

Public API
----------
    TopicEntry          — single theorem row (frozen dataclass)
    FEPTopicCatalogue   — in-memory catalog loaded from config/topics.yaml
"""

from typing import TYPE_CHECKING

from fep_formal.catalogue.novelty import (
    FormalismNoveltyLedger,
    FormalismNoveltyRecord,
    NoveltyValidationError,
    load_formalism_novelty,
)
from fep_formal.catalogue.registry import (
    BODY_MODULE_MANIFEST,
    BodyModule,
    RegistryValidationError,
    validate_body_family_ownership,
)
from fep_formal.catalogue.relations import (
    CapabilityNode,
    CapabilityStatus,
    EdgeKind,
    FormalismEdge,
    FormalismGraph,
    load_formalism_graph,
)
from fep_formal.catalogue.schema import (
    CatalogueMetadata,
    CatalogueMetadataManifest,
    RosterSeal,
    load_catalogue_metadata,
)
from fep_formal.catalogue.semantics import (
    SemanticDisposition,
    SemanticValidationError,
    TheoremMaturityAudit,
    TheoremMaturityRecord,
    load_theorem_maturity,
)
from fep_formal.catalogue.topics import (
    CatalogueValidationError,
    FEPTopicCatalogue,
    TopicEntry,
)

if TYPE_CHECKING:
    from fep_formal.catalogue.registry import BODIES, LATEX_EQUATIONS, THEOREM_LATEX


def __getattr__(name: str) -> object:
    """Resolve the lazily built registry maps on first access (PEP 562)."""
    if name in {"BODIES", "LATEX_EQUATIONS", "THEOREM_LATEX"}:
        from fep_formal.catalogue import registry

        value = getattr(registry, name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "BODIES",
    "BODY_MODULE_MANIFEST",
    "LATEX_EQUATIONS",
    "THEOREM_LATEX",
    "BodyModule",
    "CapabilityNode",
    "CapabilityStatus",
    "CatalogueMetadata",
    "CatalogueMetadataManifest",
    "CatalogueValidationError",
    "EdgeKind",
    "FEPTopicCatalogue",
    "FormalismEdge",
    "FormalismGraph",
    "FormalismNoveltyLedger",
    "FormalismNoveltyRecord",
    "NoveltyValidationError",
    "RegistryValidationError",
    "RosterSeal",
    "SemanticDisposition",
    "SemanticValidationError",
    "TheoremMaturityAudit",
    "TheoremMaturityRecord",
    "TopicEntry",
    "load_catalogue_metadata",
    "load_formalism_graph",
    "load_formalism_novelty",
    "load_theorem_maturity",
    "validate_body_family_ownership",
]
