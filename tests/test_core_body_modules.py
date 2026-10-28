"""Module-scoped roster tests for the five core_* canonical body modules.

The other fifteen body modules own per-family roster/compile tests; these five
were previously covered only by the aggregate regex validation that happens
as a side effect of importing ``registry``. A broken ``BODIES`` dict in a
core module must fail its own test, not merely the aggregate.
"""

from __future__ import annotations

import importlib

import pytest

from fep_formal.catalogue.registry import BODIES

CORE_BODY_MODULES = (
    "core_free_energy",
    "core_active_inference",
    "core_bayesian_mechanics",
    "core_information_geometry",
    "core_thermodynamics",
)

EXPECTED_CORE_ROSTERS: dict[str, tuple[str, ...]] = {
    "core_free_energy": (
        "fep-001",
        "fep-002",
        "fep-006",
        "fep-011",
        "fep-012",
        "fep-015",
        "fep-016",
        "fep-026",
        "fep-032",
        "fep-035",
        "fep-039",
        "fep-043",
        "fep-048",
    ),
    "core_active_inference": (
        "fep-003",
        "fep-007",
        "fep-008",
        "fep-021",
        "fep-023",
        "fep-028",
        "fep-033",
        "fep-034",
        "fep-041",
        "fep-047",
    ),
    "core_bayesian_mechanics": (
        "fep-005",
        "fep-009",
        "fep-010",
        "fep-017",
        "fep-019",
        "fep-020",
        "fep-022",
        "fep-027",
        "fep-036",
        "fep-040",
        "fep-042",
        "fep-045",
        "fep-046",
    ),
    "core_information_geometry": (
        "fep-004",
        "fep-014",
        "fep-018",
        "fep-024",
        "fep-029",
        "fep-038",
        "fep-044",
    ),
    "core_thermodynamics": (
        "fep-013",
        "fep-025",
        "fep-030",
        "fep-031",
        "fep-037",
        "fep-049",
        "fep-050",
    ),
}


@pytest.mark.parametrize("module_name", sorted(EXPECTED_CORE_ROSTERS))
def test_core_module_exports_its_exact_roster(module_name: str) -> None:
    module = importlib.import_module(f"fep_formal.catalogue.bodies.{module_name}")
    assert tuple(module.BODIES) == EXPECTED_CORE_ROSTERS[module_name]


@pytest.mark.parametrize("module_name", sorted(EXPECTED_CORE_ROSTERS))
def test_core_module_bodies_are_registered_in_the_aggregate(
    module_name: str,
) -> None:
    module = importlib.import_module(f"fep_formal.catalogue.bodies.{module_name}")
    for topic_id, body in module.BODIES.items():
        assert BODIES[topic_id] == body
