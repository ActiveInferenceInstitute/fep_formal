"""Fast source-only composition rosters; no Lean executable or build is needed."""

from __future__ import annotations

import re

import pytest

from fep_lean.lean_source import lean_code_without_comments
from tests import test_geometry_continuous_time_formalisms as geometry
from tests import test_risk_policy_tree_formalisms as risk_policy
from tests._support.lean_module_contract import (
    assert_exposed_module_header,
    topic_namespace_owner_modules,
)


@pytest.mark.parametrize(
    ("resource", "foundation", "bridges"),
    (
        (
            "exponential_family.lean",
            "FepSketches.exponential_family",
            geometry.COMPOSITION_BRIDGES["exponential_family.lean"],
        ),
        (
            "continuous_time.lean",
            "FepSketches.continuous_time_markov",
            geometry.COMPOSITION_BRIDGES["continuous_time.lean"],
        ),
    ),
)
def test_slice04_composition_leaves_pin_exact_bridges_and_endpoint_proofs(
    resource: str,
    foundation: str,
    bridges: tuple[tuple[str, str, str], ...],
) -> None:
    source = (geometry.COMPOSITIONS_ROOT / resource).read_text(encoding="utf-8")
    owners = topic_namespace_owner_modules(
        geometry.PROJECT_ROOT / "lean/FepSketches/fep_all.lean"
    )
    code = lean_code_without_comments(source)
    namespaces = set(re.findall(r"\bfep_fep\d+\b", code))
    families = tuple(sorted({owners[namespace] for namespace in namespaces}))
    assert families
    assert "FepSketches.fep_all" not in code
    assert_exposed_module_header(source, (*families, foundation))
    assert "namespace FEPComposed\n" in source
    assert source.rstrip().endswith("end FEPComposed")
    assert len(bridges) == 7
    assert tuple(re.findall(r"(?m)^theorem\s+([A-Za-z0-9_]+)", source)) == (
        *(bridge[0] for bridge in bridges),
        {
            "exponential_family.lean": (
                "fep146_positive_fisher_supplies_fep148_mean_injectivity"
            ),
            "continuous_time.lean": (
                "fep154_nonstationary_relaxation_supplies_fep155_strict_decay"
            ),
        }[resource],
    )

    for name, new_ref, endpoint_ref in bridges:
        start = source.index(f"theorem {name}")
        next_theorem = source.find("\ntheorem ", start + len(name))
        end = (
            next_theorem
            if next_theorem >= 0
            else source.index("\nend FEPComposed", start)
        )
        declaration = source[start:end]
        statement, proof = declaration.split(":= by", maxsplit=1)
        assert "∧" in statement, name
        assert new_ref in proof, name
        assert endpoint_ref in proof, name

    assert not geometry.FORBIDDEN_DECLARATIONS.search(source)
    assert not geometry.FORBIDDEN_PROOFS.search(source)


@pytest.mark.parametrize("resource", tuple(risk_policy.COMPOSITION_BRIDGES))
def test_composition_leaves_pin_exact_bridge_names_and_imports(resource: str) -> None:
    source = (risk_policy.COMPOSITIONS_ROOT / resource).read_text(encoding="utf-8")
    foundation = resource.removesuffix("s.lean")
    if resource == "risk_calibration.lean":
        foundation = "empirical_risk"

    owners = topic_namespace_owner_modules(
        risk_policy.PROJECT_ROOT / "lean/FepSketches/fep_all.lean"
    )
    code = lean_code_without_comments(source)
    namespaces = set(re.findall(r"\bfep_fep\d+\b", code))
    families = tuple(sorted({owners[namespace] for namespace in namespaces}))
    assert families
    assert "FepSketches.fep_all" not in code
    assert_exposed_module_header(source, (*families, f"FepSketches.{foundation}"))
    assert tuple(re.findall(r"(?m)^theorem ([A-Za-z0-9_']+)", source)) == (
        *risk_policy.COMPOSITION_BRIDGES[resource],
        {
            "risk_calibration.lean": (
                "fep125_brier_identity_transfers_fep124_risk_bound"
            ),
            "policy_trees.lean": (
                "fep130_attaining_tree_dominates_fep131_embedded_plans"
            ),
        }[resource],
    )
    assert risk_policy.FORBIDDEN_FORMAL_TOKENS.search(source) is None
