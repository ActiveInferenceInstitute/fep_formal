"""Enforce generated-YAML parity with the canonical body registry.

The family modules are merged by ``fep_formal.catalogue.registry``; ``topics.yaml``
is a generated projection. This test catches accidental YAML-only drift without
a full Lean run.
"""

from __future__ import annotations

from pathlib import Path

from fep_formal.catalogue.topics import FEPTopicCatalogue

PROJ = Path(__file__).resolve().parent.parent
TOPICS = PROJ / "config" / "topics.yaml"


def _load_bodies():
    from fep_formal.catalogue.registry import BODIES

    return BODIES


def _load_latex_equations():
    from fep_formal.catalogue.registry import LATEX_EQUATIONS

    return LATEX_EQUATIONS


def test_yaml_lean_body_matches_registry_exactly() -> None:
    bodies = _load_bodies()
    cat = FEPTopicCatalogue.from_yaml(TOPICS)
    assert tuple(topic.id for topic in cat.topics) == tuple(bodies)

    mismatches: list[str] = []
    for t in cat.topics:
        expected = bodies.get(t.id)
        if expected is None:
            mismatches.append(f"{t.id}: missing key in body registry")
            continue
        if t.lean_sketch != expected:
            mismatches.append(f"{t.id}: topics.yaml body differs from registry")

    assert not mismatches, "body registry vs topics.yaml drift:\n" + "\n".join(
        mismatches
    )


def test_yaml_latex_equations_matches_qualified_registry() -> None:
    expected = _load_latex_equations()
    cat = FEPTopicCatalogue.from_yaml(TOPICS)
    for t in cat.topics:
        want = expected.get(t.id)
        assert want is not None, f"{t.id}: missing in LATEX_EQUATIONS"
        assert t.latex_equations == want, (
            f"{t.id}: topics.yaml latex_equations != LATEX_EQUATIONS"
        )
