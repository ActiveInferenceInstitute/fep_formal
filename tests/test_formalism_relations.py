"""Maintained formalism relations remain typed, explicit, and non-cyclic."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

import pytest
import yaml

from fep_lean.catalogue import SemanticValidationError
from fep_lean.catalogue.relations import (
    CapabilityStatus,
    EdgeKind,
    FormalismGraph,
    load_formalism_graph,
)
from fep_lean.catalogue.schema import load_catalogue_metadata
from fep_lean.formal.declarations import (
    all_formal_theorem_declarations,
    composed_theorem_sources,
    formal_theorem_modules,
)
from fep_lean.formal.manifest import FORMAL_MODULES, FormalModuleRole

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SYNTHETIC_ROSTER = ("fep-001", "fep-002", "fep-003")

BASELINE_CAPABILITY_IDS = frozenset(
    {
        "cap-active-inference-generative-model",
        "cap-conditional-independence",
        "cap-conjugacy-laws",
        "cap-convex-information-functionals",
        "cap-cumulative-expected-free-energy",
        "cap-discrete-measurable-semigroup",
        "cap-empirical-bayes-model",
        "cap-entropy-optimization",
        "cap-evidence-lower-bound",
        "cap-expected-free-energy-decomposition",
        "cap-finite-information-theory",
        "cap-finite-kernel-algebra",
        "cap-finite-kl-chain-rules",
        "cap-finite-message-passing",
        "cap-finite-observable-consistency",
        "cap-gaussian-thermodynamic-model",
        "cap-hierarchical-factorization",
        "cap-markov-blanket-dynamics",
        "cap-measurable-variational-integrand",
        "cap-multidimensional-information-geometry",
        "cap-open-loop-policy-rollout",
        "cap-physical-erasure-model",
        "cap-policy-posterior-action",
        "cap-posterior-predictive-model",
        "cap-probability-normalization",
        "cap-quadratic-optimization-dynamics",
        "cap-statistical-manifold",
        "cap-stick-breaking-simplex",
        "cap-stochastic-dynamics",
        "cap-strong-law-consistency",
        "cap-sufficient-statistics",
        "cap-thermodynamic-constitutive-law",
        "cap-thermodynamic-potential",
    }
)

BASELINE_EDGE_SIGNATURES = frozenset(
    {
        ("fep-002", "fep-014", "formal", "FEPComposed.fep002_vfe_compProd_chain_rule"),
        (
            "fep-003",
            "fep-021",
            "formal",
            "FEPComposed.fep003_pragmaticCost_efe_balance",
        ),
        (
            "fep-004",
            "fep-038",
            "formal",
            "FEPComposed.fep004_bernoulliMetric_specialization",
        ),
        ("fep-005", "fep-009", "conceptual", None),
        ("fep-008", "fep-028", "conceptual", None),
        (
            "fep-011",
            "fep-026",
            "formal",
            "FEPComposed.fep026_priorComplexity_is_fep011_surprise",
        ),
        (
            "fep-012",
            "fep-028",
            "formal",
            "FEPComposed.fep012_softmax_entropyRegularizedCost_le",
        ),
        ("fep-013", "fep-002", "conceptual", None),
        (
            "fep-013",
            "fep-040",
            "formal",
            "FEPComposed.fep013_gaussianHelmholtz_derivative",
        ),
        ("fep-016", "fep-032", "conceptual", None),
        ("fep-017", "fep-045", "conceptual", None),
        ("fep-021", "fep-041", "formal", "FEPComposed.fep021_informationGain_balance"),
        (
            "fep-022",
            "fep-027",
            "formal",
            "FEPComposed.fep022_predictive_is_hierarchical_marginal",
        ),
        ("fep-024", "fep-014", "formal", "FEPComposed.fep024_regularizer_is_fep014_kl"),
        (
            "fep-025",
            "fep-049",
            "formal",
            "FEPComposed.fep025_current_dissipation_nonneg",
        ),
        (
            "fep-027",
            "fep-019",
            "formal",
            "FEPComposed.fep027_priorPredictive_is_fep019",
        ),
        ("fep-029", "fep-044", "conceptual", None),
        ("fep-030", "fep-031", "conceptual", None),
        (
            "fep-031",
            "fep-030",
            "formal",
            "FEPComposed.fep031_zeroBeta_binary_maxEntropy",
        ),
        (
            "fep-032",
            "fep-043",
            "formal",
            "FEPComposed.fep032_update_is_fep043_gradientStep",
        ),
        ("fep-034", "fep-047", "conceptual", None),
        (
            "fep-034",
            "fep-017",
            "formal",
            "FEPComposed.fep034_filter_is_fep017_posterior",
        ),
        (
            "fep-036",
            "fep-045",
            "formal",
            "FEPComposed.fep036_empiricalPosterior_closed",
        ),
        (
            "fep-037",
            "fep-020",
            "formal",
            "FEPComposed.fep037_autocorrelation_tracks_fep020",
        ),
        (
            "fep-038",
            "fep-018",
            "formal_pairing",
            "FEPComposed.fep038_fisherRao_separation",
        ),
        (
            "fep-039",
            "fep-005",
            "formal",
            "FEPComposed.fep039_partitionEnergy_conservation",
        ),
        (
            "fep-041",
            "fep-014",
            "formal",
            "FEPComposed.fep041_informationGain_is_fep014_kl",
        ),
        (
            "fep-042",
            "fep-036",
            "formal",
            "FEPComposed.fep036_empiricalPosterior_closed",
        ),
    }
)

EXPANSION_CAPABILITY_BY_FAMILY = {
    "causal-blankets-and-interventions": "cap-causal-intervention-invariants",
    "closed-loop-policy-trees-and-efe": "cap-closed-loop-policy-trees",
    "collective-and-multiagent-active-inference": "cap-collective-consensus-invariants",
    "control-and-planning-as-inference": "cap-controlled-markov-planning",
    "finite-exponential-family-dual-geometry": (
        "cap-finite-exponential-family-geometry"
    ),
    "finite-sample-risk-and-calibration": "cap-finite-sample-risk-calibration",
    "finite-to-native-blanket-transfer": "cap-native-blanket-transfer",
    "information-geometry-and-geometric-optimization": "cap-geometric-optimization",
    "learning-concentration-and-model-evidence": "cap-finite-learning-theory",
    "measure-bayesian-inversion": "cap-measure-bayesian-inversion",
    "path-space-stochastic-thermodynamics": "cap-finite-path-thermodynamics",
    "predictive-coding-and-generalized-coordinates": "cap-predictive-coding-dynamics",
    "temporal-and-hierarchical-inference": "cap-temporal-inference",
    "two-state-continuous-time-thermodynamics": ("cap-continuous-time-thermodynamics"),
    "variational-duality-and-information-bounds": "cap-finite-variational-duality",
    "standalone-efe-formalizations": "cap-standalone-efe-theorems",
}

EXPANSION_BOUNDARY_EVIDENCE = {
    "cap-causal-intervention-invariants": (
        "fep_fep085.FEP085.fep085_zeroEvidence_boundary"
    ),
    "cap-collective-consensus-invariants": (
        "FEP.CollectiveInference.boolConsensus_nonzero_strict_witness"
    ),
    "cap-controlled-markov-planning": (
        "FEP.ControlledMarkov.actionEvidence_zero_boundary"
    ),
    "cap-closed-loop-policy-trees": (
        "fep_fep134.FEP134.fep134_feedback_continuation_changes"
    ),
    "cap-continuous-time-thermodynamics": (
        "FEP.ContinuousTimeMarkov.TwoStateRates.benchmarkLyapunov_deriv_zero_neg"
    ),
    "cap-finite-exponential-family-geometry": (
        "FEP.ExponentialFamily.ScalarExponentialFamily.constantStatistic_variance_zero"
    ),
    "cap-finite-learning-theory": (
        "FEP.LearningTheory.bayesFactor_zero_denominator_boundary"
    ),
    "cap-finite-path-thermodynamics": (
        "FEP.PathThermodynamics.pathRatio_zero_reverse_boundary"
    ),
    "cap-finite-sample-risk-calibration": (
        "FEP.EmpiricalRisk.laplaceBias_nonzero_witness"
    ),
    "cap-finite-variational-duality": (
        "fep_fep064.FEP064.fep064_zeroMultiplier_boundary"
    ),
    "cap-geometric-optimization": (
        "FEP.GeometricOptimization.duplicatedScore_nullDirection_example"
    ),
    "cap-measure-bayesian-inversion": "FEP.MeasureBayes.finite_zero_evidence_boundary",
    "cap-native-blanket-transfer": "FEP.NativeBlanket.correlatedBlanket_nonvacuous",
    "cap-predictive-coding-dynamics": (
        "FEP.PredictiveCoding.generalizedFlow_top_boundary"
    ),
    "cap-standalone-efe-theorems": (
        "fep_fep158.FEP158.fep158_reduction_free_energy_monotone"
    ),
    "cap-temporal-inference": "FEP.TemporalInference.forwardEvidence_zero_boundary",
}


def test_shipped_graph_conserves_relation_and_capability_state() -> None:
    metadata = load_catalogue_metadata(
        PROJECT_ROOT / "config" / "catalogue_metadata.yaml"
    )
    graph = load_formalism_graph(
        PROJECT_ROOT / "config" / "formalism_relations.yaml",
        roster_ids=metadata.topic_ids,
    )

    capability_ids = frozenset(node.id for node in graph.capabilities)
    edge_signatures = frozenset(
        (edge.source, edge.target, edge.kind.value, edge.witness)
        for edge in graph.edges
    )
    assert capability_ids >= BASELINE_CAPABILITY_IDS
    assert edge_signatures >= BASELINE_EDGE_SIGNATURES
    assert frozenset(EXPANSION_CAPABILITY_BY_FAMILY.values()) <= capability_ids

    expansion_families = {
        family for family in metadata.families if not family.startswith("core-")
    }
    assert set(EXPANSION_CAPABILITY_BY_FAMILY) == expansion_families
    capability_by_id = {node.id: node for node in graph.capabilities}
    for capability_id in EXPANSION_CAPABILITY_BY_FAMILY.values():
        node = capability_by_id[capability_id]
        assert node.status is CapabilityStatus.SATISFIED
        assert len(node.evidence) >= 4
        assert EXPANSION_BOUNDARY_EVIDENCE[capability_id] in node.evidence
    expansion_topic_ids = {
        record.id for record in metadata.records if record.family in expansion_families
    }
    theorem_witnessed_sources = {
        edge.source for edge in graph.edges if edge.kind.is_theorem_witnessed
    }
    assert expansion_topic_ids <= theorem_witnessed_sources

    assert Counter(edge.kind for edge in graph.edges) == {
        EdgeKind.FORMAL: 20,
        EdgeKind.FORMAL_PAIRING: 109,
        EdgeKind.CONCEPTUAL: 8,
    }
    assert all(edge.witness for edge in graph.edges if edge.kind.is_theorem_witnessed)
    assert next(edge for edge in graph.edges if edge.source == "fep-038").kind is (
        EdgeKind.FORMAL_PAIRING
    )
    assert next(edge for edge in graph.edges if edge.source == "fep-060").kind is (
        EdgeKind.FORMAL
    )
    assert all(
        edge.kind is EdgeKind.FORMAL_PAIRING
        for edge in graph.edges
        if edge.source in expansion_topic_ids and edge.source != "fep-060"
    )
    assert all(edge.rationale.endswith(".") for edge in graph.edges)
    assert graph.capability_ids == capability_ids


def test_theorem_witnessed_edges_are_composition_leaves_using_both_endpoints() -> None:
    metadata = load_catalogue_metadata(
        PROJECT_ROOT / "config" / "catalogue_metadata.yaml"
    )
    graph = load_formalism_graph(
        PROJECT_ROOT / "config" / "formalism_relations.yaml",
        roster_ids=metadata.topic_ids,
    )
    theorem_modules = formal_theorem_modules(PROJECT_ROOT)
    composition_modules = {
        module.lean_module
        for module in FORMAL_MODULES
        if module.role is FormalModuleRole.COMPOSITION
    }
    sources = composed_theorem_sources(PROJECT_ROOT)

    for edge in graph.edges:
        if not edge.kind.is_theorem_witnessed:
            continue
        assert edge.witness is not None
        assert theorem_modules.get(edge.witness) in composition_modules
        source = sources[edge.witness]
        for topic_id in (edge.source, edge.target):
            digits = topic_id.removeprefix("fep-")
            assert f"fep_fep{digits}." in source


def test_capability_evidence_resolves_in_the_canonical_formal_closure() -> None:
    metadata = load_catalogue_metadata(
        PROJECT_ROOT / "config" / "catalogue_metadata.yaml"
    )
    graph = load_formalism_graph(
        PROJECT_ROOT / "config" / "formalism_relations.yaml",
        roster_ids=metadata.topic_ids,
    )
    known_declarations = all_formal_theorem_declarations(PROJECT_ROOT)
    required_declarations = {
        declaration for node in graph.capabilities for declaration in node.evidence
    }

    assert required_declarations <= known_declarations


def _write_graph(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "relations.yaml"
    path.write_text(body, encoding="utf-8")
    return path


def _load_synthetic_graph(path: Path) -> FormalismGraph:
    return load_formalism_graph(path, roster_ids=SYNTHETIC_ROSTER)


def test_formal_cycles_are_rejected(tmp_path: Path) -> None:
    path = _write_graph(
        tmp_path,
        """\
schema_version: 2
capabilities: []
edges:
  - source: fep-001
    target: fep-002
    kind: formal
    rationale: First direct dependency.
    witness: Example.first
  - source: fep-002
    target: fep-001
    kind: formal
    rationale: Cyclic direct dependency.
    witness: Example.second
""",
    )

    with pytest.raises(SemanticValidationError, match="formal relation cycle"):
        _load_synthetic_graph(path)


def test_formal_pairings_are_witnessed_but_not_directional_dependencies(
    tmp_path: Path,
) -> None:
    path = _write_graph(
        tmp_path,
        """\
schema_version: 2
capabilities: []
edges:
  - source: fep-001
    target: fep-002
    kind: formal_pairing
    rationale: Two checked laws share a review context without implication.
    witness: Example.first
  - source: fep-002
    target: fep-001
    kind: formal_pairing
    rationale: Reversing a pairing does not assert a dependency cycle.
    witness: Example.second
""",
    )

    graph = _load_synthetic_graph(path)

    assert all(edge.kind is EdgeKind.FORMAL_PAIRING for edge in graph.edges)
    assert all(edge.kind.is_theorem_witnessed for edge in graph.edges)


def test_blocked_edges_must_target_declared_capabilities(tmp_path: Path) -> None:
    path = _write_graph(
        tmp_path,
        """\
schema_version: 2
capabilities: []
edges:
  - source: fep-001
    target: cap-unknown
    kind: blocked_by
    rationale: Missing capability.
""",
    )

    with pytest.raises(
        SemanticValidationError, match="blocked_by target must be a known capability"
    ):
        _load_synthetic_graph(path)


def test_conceptual_edges_cannot_target_capabilities(tmp_path: Path) -> None:
    path = _write_graph(
        tmp_path,
        """\
schema_version: 2
capabilities:
  - id: cap-example
    title: Example capability
    description: A deliberately incomplete formal surface.
    status: open
edges:
  - source: fep-001
    target: cap-example
    kind: conceptual
    rationale: Wrong target class.
""",
    )

    with pytest.raises(
        SemanticValidationError, match="conceptual target must be a known topic"
    ):
        _load_synthetic_graph(path)


def test_relation_order_is_canonical(tmp_path: Path) -> None:
    path = _write_graph(
        tmp_path,
        """\
schema_version: 2
capabilities: []
edges:
  - source: fep-002
    target: fep-003
    kind: conceptual
    rationale: Later source first.
  - source: fep-001
    target: fep-002
    kind: conceptual
    rationale: Earlier source second.
""",
    )

    with pytest.raises(SemanticValidationError, match="must be sorted"):
        _load_synthetic_graph(path)


@pytest.mark.parametrize(
    ("data", "message"),
    [
        ({"schema_version": 3, "capabilities": [], "edges": []}, "schema_version"),
        (
            {
                "schema_version": 2,
                "capabilities": [],
                "edges": [],
                "surprise": True,
            },
            "unknown fields",
        ),
        (
            {"schema_version": 2, "capabilities": {}, "edges": []},
            "must be lists",
        ),
        (
            {"schema_version": 2, "capabilities": ["bad"], "edges": []},
            "capability row 1 must be an object",
        ),
        (
            {
                "schema_version": 2,
                "capabilities": [
                    {
                        "id": "BAD",
                        "title": "Bad",
                        "description": "Bad.",
                        "status": "open",
                    }
                ],
                "edges": [],
            },
            "invalid capability ID",
        ),
        (
            {
                "schema_version": 2,
                "capabilities": [
                    {
                        "id": "cap-b",
                        "title": "B",
                        "description": "B.",
                        "status": "open",
                    },
                    {
                        "id": "cap-a",
                        "title": "A",
                        "description": "A.",
                        "status": "open",
                    },
                ],
                "edges": [],
            },
            "must be ID-sorted",
        ),
        (
            {"schema_version": 2, "capabilities": [], "edges": ["bad"]},
            "edge row 1 must be an object",
        ),
        (
            {
                "schema_version": 2,
                "capabilities": [],
                "edges": [
                    {
                        "source": "fep-999",
                        "target": "fep-001",
                        "kind": "conceptual",
                        "rationale": "Unknown source.",
                    }
                ],
            },
            "unknown source",
        ),
        (
            {
                "schema_version": 2,
                "capabilities": [],
                "edges": [
                    {
                        "source": "fep-001",
                        "target": "fep-001",
                        "kind": "conceptual",
                        "rationale": "Self edge.",
                    }
                ],
            },
            "self-edge",
        ),
        (
            {
                "schema_version": 2,
                "capabilities": [],
                "edges": [
                    {
                        "source": "fep-001",
                        "target": "fep-002",
                        "kind": "invented",
                        "rationale": "Unknown kind.",
                    }
                ],
            },
            "unsupported edge kind",
        ),
        (
            {
                "schema_version": 2,
                "capabilities": [],
                "edges": [
                    {
                        "source": "fep-001",
                        "target": "fep-002",
                        "kind": "conceptual",
                        "rationale": "Duplicate edge.",
                    },
                    {
                        "source": "fep-001",
                        "target": "fep-002",
                        "kind": "conceptual",
                        "rationale": "Duplicate edge again.",
                    },
                ],
            },
            "duplicate conceptual edge",
        ),
        (
            {
                "schema_version": 2,
                "capabilities": [
                    {
                        "id": "cap-unused",
                        "title": "Unused",
                        "description": "Not referenced.",
                        "status": "open",
                    }
                ],
                "edges": [],
            },
            "unreferenced unresolved capability",
        ),
    ],
)
def test_invalid_relation_graphs_fail_closed(
    tmp_path: Path, data: object, message: str
) -> None:
    path = tmp_path / "invalid.yaml"
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")

    with pytest.raises(SemanticValidationError, match=message):
        _load_synthetic_graph(path)


def test_unreadable_and_malformed_graphs_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(SemanticValidationError, match="cannot read formalism graph"):
        _load_synthetic_graph(tmp_path / "missing.yaml")

    malformed = tmp_path / "malformed.yaml"
    malformed.write_text("edges: [", encoding="utf-8")
    with pytest.raises(SemanticValidationError, match="cannot read formalism graph"):
        _load_synthetic_graph(malformed)


def test_formal_edges_require_a_qualified_witness(tmp_path: Path) -> None:
    missing = _write_graph(
        tmp_path,
        """\
schema_version: 2
capabilities: []
edges:
  - source: fep-001
    target: fep-002
    kind: formal
    rationale: Direct dependency without evidence.
""",
    )
    with pytest.raises(SemanticValidationError, match="missing witness"):
        _load_synthetic_graph(missing)

    malformed = _write_graph(
        tmp_path,
        """\
schema_version: 2
capabilities: []
edges:
  - source: fep-001
    target: fep-002
    kind: formal
    rationale: Direct dependency with malformed evidence.
    witness: not-qualified
""",
    )
    with pytest.raises(SemanticValidationError, match="qualified declaration"):
        _load_synthetic_graph(malformed)

    pairing_without_witness = _write_graph(
        tmp_path,
        """\
schema_version: 2
capabilities: []
edges:
  - source: fep-001
    target: fep-002
    kind: formal_pairing
    rationale: Checked pairings require their declaration too.
""",
    )
    with pytest.raises(SemanticValidationError, match="missing witness"):
        _load_synthetic_graph(pairing_without_witness)


def test_nonformal_edges_reject_witness_fields(tmp_path: Path) -> None:
    path = _write_graph(
        tmp_path,
        """\
schema_version: 2
capabilities: []
edges:
  - source: fep-001
    target: fep-002
    kind: conceptual
    rationale: Conceptual adjacency is not compiled evidence.
    witness: Example.notAllowed
""",
    )
    with pytest.raises(SemanticValidationError, match="unknown witness"):
        _load_synthetic_graph(path)
