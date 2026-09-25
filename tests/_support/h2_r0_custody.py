"""Validate the one explicitly reviewed successor of the immutable H2.7-R0 gate.

Custody validation is distinct from fresh native evidence. A pending successor
preserves the accepted proof's scope; it does not attest to a new compiler run.
"""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
from typing import Any

PRIOR_PATH = (
    "specs/horizon-2-smooth-stochastic/readiness/repairs/"
    "07-gaussian-vfe-natural-gradient.json"
)
SUCCESSOR_PATH = (
    "specs/horizon-2-smooth-stochastic/readiness/repairs/"
    "07-gaussian-vfe-natural-gradient-custody.json"
)
PRIOR_SHA256 = "b5637ff30690748ccf1db992e6fb7c34a267a3ed1a7b74daacb1bc9cac844d01"
MANIFEST_PATH = "src/fep_lean/formal/manifest.py"
READINESS_TEST_PATH = "tests/test_horizon2_gaussian_vfe_readiness.py"
VALIDATOR_PATH = "tests/_support/h2_r0_custody.py"
ALLOWED_PRIOR_CHANGES = (MANIFEST_PATH, READINESS_TEST_PATH)
ADDED_MODULES = (
    ("gnn_document.lean", "FepSketches.gnn_document", "FEP.GnnDocument"),
    ("gnn_denotation.lean", "FepSketches.gnn_denotation", "FEP.GnnDenotation"),
    (
        "gnn_denotation_continuous.lean",
        "FepSketches.gnn_denotation_continuous",
        "FEP.GnnContinuous",
    ),
    (
        "gnn_render_statements.lean",
        "FepSketches.gnn_render_statements",
        "FEP.GnnRenderStatements",
    ),
)
NATIVE_PROBES = (
    "test_h2_7_r0_compiles_warning_free",
    "test_h2_7_r0_exact_types_environment_and_axioms",
    "test_h2_7_r0_typed_consumer_rejects_reversed_kl",
)
# W4 code consolidation (commit 849691ba41033d6f64d5ed16032438405f4036f0)
# replaced the R0-era literal released-shared-namespace frozenset with a
# derived comprehension moved below the FORMAL_MODULES roster; semantics are
# preserved (same resources, same derivation inputs). Custody reconstruction
# removes the exact derived bytes and restores the exact R0-era literal bytes
# at their recorded anchor, so the sealed R0 digest still binds the
# historical owners while the approved transformation is explicit.
W4_CONSOLIDATION_COMMIT = "849691ba41033d6f64d5ed16032438405f4036f0"
_W4_DERIVED_RESOURCES_BLOCK = (
    "_RELEASED_SHARED_DECLARATION_NAMESPACE_RESOURCES = frozenset(\n"
    "    module.resource\n"
    "    for module in FORMAL_MODULES\n"
    "    if module.role is FormalModuleRole.COMPOSITION\n"
    "    and module.declaration_namespace"
    " == _RELEASED_SHARED_DECLARATION_NAMESPACE\n"
    ")\n\n"
)
_W4_CONSOLIDATION_ANCHOR = "\n\n@dataclass(frozen=True)\nclass FormalModule:"
_W4_RESTORED_LITERAL_BLOCK = (
    "\n\n_RELEASED_SHARED_DECLARATION_NAMESPACE_RESOURCES = frozenset(\n"
    "    {\n"
    '        "compositions/core.lean",\n'
    '        "compositions/measure_variational.lean",\n'
    '        "compositions/control_temporal.lean",\n'
    '        "compositions/causal_predictive.lean",\n'
    '        "compositions/thermo_geometry.lean",\n'
    '        "compositions/collective_learning.lean",\n'
    '        "compositions/risk_calibration.lean",\n'
    '        "compositions/policy_trees.lean",\n'
    '        "compositions/native_blanket_transfer.lean",\n'
    '        "compositions/exponential_family.lean",\n'
    '        "compositions/continuous_time.lean",\n'
    "    }\n"
    ")\n"
    "\n\n@dataclass(frozen=True)\nclass FormalModule:"
)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    def unique_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            _require(key not in result, f"duplicate JSON key: {key}")
            result[key] = value
        return result

    result = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_keys)
    _require(isinstance(result, dict), "custody document must be an object")
    return result


def _manifest_owners(source: str) -> list[dict[str, str | None]]:
    """Read literal module tuples without executing the Python manifest."""
    declarations = [
        node
        for node in ast.parse(source).body
        if isinstance(node, ast.AnnAssign)
        and isinstance(node.target, ast.Name)
        and node.target.id == "FORMAL_MODULES"
    ]
    _require(len(declarations) == 1, "manifest must have one FORMAL_MODULES roster")
    roster = declarations[0].value
    _require(isinstance(roster, ast.Tuple), "manifest roster must be a literal tuple")
    assert isinstance(roster, ast.Tuple)
    owners = []
    for entry in roster.elts:
        _require(
            isinstance(entry, ast.Call)
            and isinstance(entry.func, ast.Name)
            and entry.func.id == "FormalModule"
            and not entry.args,
            "manifest owner must be a literal FormalModule",
        )
        assert isinstance(entry, ast.Call)
        owner = {}
        for keyword in entry.keywords:
            _require(keyword.arg is not None, "manifest owner cannot expand keywords")
            assert keyword.arg is not None
            _require(keyword.arg not in owner, "duplicate manifest owner field")
            if keyword.arg == "role":
                role = keyword.value
                _require(
                    isinstance(role, ast.Attribute)
                    and isinstance(role.value, ast.Name)
                    and role.value.id == "FormalModuleRole",
                    "manifest role must name FormalModuleRole",
                )
                assert isinstance(role, ast.Attribute)
                owner[keyword.arg] = role.attr.lower()
            else:
                owner[keyword.arg] = ast.literal_eval(keyword.value)
        _require(
            set(owner) == {"resource", "lean_module", "role", "declaration_namespace"},
            "manifest owner fields changed",
        )
        owners.append(owner)
    for key in ("resource", "lean_module"):
        _require(
            len({owner[key] for owner in owners}) == len(owners),
            f"duplicate manifest {key}",
        )
    return owners


W4_CODE_CONSOLIDATION = {
    "commit": W4_CONSOLIDATION_COMMIT,
    "approved": "2026-09-24",
    "description": (
        "code consolidation replaced the R0-era literal"
        " released-shared-declaration-namespace frozenset with a derived"
        " comprehension below the FORMAL_MODULES roster; semantics preserved"
    ),
    "restored_declaration": "_RELEASED_SHARED_DECLARATION_NAMESPACE_RESOURCES",
    "restored_literal_block_sha256": _sha256(_W4_RESTORED_LITERAL_BLOCK.encode()),
    "derived_resources_block_sha256": _sha256(_W4_DERIVED_RESOURCES_BLOCK.encode()),
}


def validate_h2_r0_custody(project_root: Path) -> dict[str, Any]:
    """Validate fixed prior/successor bytes and permitted drift, returning status."""
    prior_bytes = (project_root / PRIOR_PATH).read_bytes()
    _require(_sha256(prior_bytes) == PRIOR_SHA256, "immutable R0 prior changed")
    prior = _read_json(project_root / PRIOR_PATH)
    successor = _read_json(project_root / SUCCESSOR_PATH)
    _require(
        set(successor)
        == {
            "schema_version",
            "gate",
            "decision",
            "decision_scope",
            "prior",
            "allowed_prior_source_changes",
            "manifest_transition",
            "source_sha256",
            "downstream",
            "native_evidence",
        },
        "successor fields changed",
    )
    _require(successor["schema_version"] == 1, "unsupported successor schema")
    _require(successor["gate"] == "H2.7-R0-custody", "wrong custody gate")
    _require(
        successor["decision"] == "preserve_accepted_R0", "custody decision changed"
    )
    _require(
        successor["decision_scope"] == "open_H2.7_implementation_only",
        "custody scope expanded",
    )
    _require(
        successor["allowed_prior_source_changes"] == list(ALLOWED_PRIOR_CHANGES),
        "unreviewed source-change allowance",
    )
    _require(
        successor["downstream"] == prior["downstream"], "downstream scope expanded"
    )

    manifest_bytes = (project_root / MANIFEST_PATH).read_bytes()
    manifest = manifest_bytes.decode("utf-8")
    owners = _manifest_owners(manifest)
    added = [
        {
            "resource": resource,
            "lean_module": module,
            "role": "foundation",
            "declaration_namespace": namespace,
        }
        for resource, module, namespace in ADDED_MODULES
    ]
    blocks = [
        "    FormalModule(\n"
        f'        resource="{resource}",\n'
        f'        lean_module="{module}",\n'
        "        role=FormalModuleRole.FOUNDATION,\n"
        f'        declaration_namespace="{namespace}",\n'
        "    ),\n"
        for resource, module, namespace in ADDED_MODULES
    ]
    _require(
        all(manifest.count(block) == 1 for block in blocks),
        "approved added owners missing, duplicated, or changed",
    )
    additions = "".join(blocks)
    _require(manifest.count(additions) == 1, "approved additions must retain order")
    stripped_manifest = manifest.replace(additions, "", 1)
    _require(
        stripped_manifest.count(_W4_DERIVED_RESOURCES_BLOCK) == 1,
        "approved W4 code consolidation record missing, duplicated, or changed",
    )
    without_w4 = stripped_manifest.replace(_W4_DERIVED_RESOURCES_BLOCK, "", 1)
    _require(
        without_w4.count(_W4_CONSOLIDATION_ANCHOR) == 1,
        "W4 code consolidation anchor missing, duplicated, or changed",
    )
    prior_manifest = without_w4.replace(
        _W4_CONSOLIDATION_ANCHOR, _W4_RESTORED_LITERAL_BLOCK, 1
    )
    prior_manifest_sha = prior["source_sha256"][MANIFEST_PATH]
    _require(
        _sha256(prior_manifest.encode()) == prior_manifest_sha,
        "manifest has unlisted changes to historical owners or code",
    )
    retained = _manifest_owners(prior_manifest)
    _require(
        [owner for owner in owners if owner not in added] == retained,
        "historical owner roles or order changed",
    )
    _require(
        successor["manifest_transition"]
        == {
            "prior_sha256": prior_manifest_sha,
            "current_sha256": _sha256(manifest_bytes),
            "added_modules": added,
            "unchanged_owners": retained,
            "code_consolidation": W4_CODE_CONSOLIDATION,
        },
        "manifest transition receipt does not match exact owners",
    )

    source_paths = set(prior["source_sha256"]) | {VALIDATOR_PATH}
    current = {
        path: _sha256((project_root / path).read_bytes()) for path in source_paths
    }
    _require(successor["source_sha256"] == current, "stale successor source digest")
    changed = {
        path
        for path, digest in prior["source_sha256"].items()
        if current[path] != digest
    }
    _require(changed == set(ALLOWED_PRIOR_CHANGES), "unapproved prior source drift")
    evidence = successor["native_evidence"]
    _require(
        isinstance(evidence, dict)
        and set(evidence) == {"status", "historical_evidence_reused", "probes"}
        and evidence["historical_evidence_reused"] is False,
        "native evidence must not reuse historical execution",
    )
    if evidence["status"] == "pending":
        _require(
            evidence["probes"] == [], "pending native evidence cannot claim probes"
        )
    else:
        _require(evidence["status"] == "verified", "unknown native evidence status")
        probes = evidence["probes"]
        _require(isinstance(probes, list) and len(probes) == 3, "native probes missing")
        for name, probe in zip(NATIVE_PROBES, probes, strict=True):
            _require(
                probe
                == {
                    "nodeid": f"{READINESS_TEST_PATH}::{name}",
                    "pytest_exit_code": 0,
                    "source_sha256": current,
                },
                "native probe does not bind current source and exact passing test",
            )
    return successor
