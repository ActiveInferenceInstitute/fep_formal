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
        successor["prior"] == {"path": PRIOR_PATH, "sha256": PRIOR_SHA256},
        "successor must bind the fixed immutable prior",
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
    prior_manifest = manifest.replace(additions, "", 1)
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
