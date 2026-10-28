"""Canonical packaged Lean resources and deterministic workspace projection."""

from fep_formal.formal.declarations import (
    all_formal_theorem_declarations,
    composed_theorem_declarations,
    formal_theorem_modules,
    topic_theorem_declarations,
)
from fep_formal.formal.manifest import (
    FORMAL_MODULES,
    FormalModule,
    FormalModuleRole,
    formal_module_imports,
    formal_resource_manifest_drift,
    formal_resource_paths,
    formal_resource_relative_paths,
)
from fep_formal.formal.projection import (
    formal_aggregate_drift,
    formal_projection_drift,
    formal_projection_pairs,
    render_formal_aggregate,
    write_formal_aggregate,
    write_formal_projections,
)

__all__ = [
    "FORMAL_MODULES",
    "FormalModule",
    "FormalModuleRole",
    "all_formal_theorem_declarations",
    "composed_theorem_declarations",
    "formal_aggregate_drift",
    "formal_module_imports",
    "formal_projection_drift",
    "formal_projection_pairs",
    "formal_resource_manifest_drift",
    "formal_resource_paths",
    "formal_resource_relative_paths",
    "formal_theorem_modules",
    "render_formal_aggregate",
    "topic_theorem_declarations",
    "write_formal_aggregate",
    "write_formal_projections",
]
