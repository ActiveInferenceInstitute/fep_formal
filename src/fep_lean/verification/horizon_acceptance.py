"""Read-only, source-bound H2 exit and continuous H3.G0 evidence checks.

This module consumes actual captured evidence. It does not run Lean, generate
approvals, freeze an H3 protocol, or infer a proof from a numerical diagnostic.
"""

from __future__ import annotations

import ast
import hashlib
import json
import math
import re
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, cast

from fep_lean.catalogue.registry import BODY_MODULE_MANIFEST
from fep_lean.verification._jsonutil import load_strict_json
from fep_lean.verification.numerical_witnesses import (
    NON_PROOF_EVIDENCE,
    NumericalCheck,
    evaluate_numerical_witnesses,
)

BASE = "specs/horizon-2-smooth-stochastic/readiness/"
TERMINAL_RECEIPT = BASE + "terminal-acceptance.json"
R0_SUCCESSOR = BASE + "repairs/07-gaussian-vfe-natural-gradient-custody.json"
# Immutable full frozen-source collection; includes all parameterized case IDs.
CAPTURED_COLLECTION_SHA256 = (
    "22b5008f6c8a080bedff28385532d407cc4f2b31a47d440ca2d1705038b6b803"
)
PREDECESSORS = {
    BASE
    + "acceptance.json": "7e1366e029386c601a4c04c432bf213f9bb3ff64126c841640035efab4d6ec55",
    BASE
    + "repairs/05b-transition-covariance.json": "820166b70e8e8f35baa6e3493a197b91fee3eef54177d701b69c94716fc68752",
    BASE
    + "repairs/05d-gaussian-conditioning.json": "e9402bae458fdeda13e0d2ef06d33b7a875cad59cadb6e7f7a99741ee0e72625",
    BASE
    + "repairs/05d-gaussian-conditioning-lifecycle.json": "64e5abcfe7cbcaf5f5164378e65a230e8dd13904c3f1462aa4b73678338270d6",
    BASE
    + "repairs/06a-native-filter-posterior.json": "c6f58c41e4607f47bd8ff0203fa1ac78dcfb59f3d66bb4f20486517d28e2066f",
    BASE
    + "repairs/07-gaussian-vfe-natural-gradient.json": "d854a43bc412b67cf1c8485582ae2d27c52d0b279cb27cd1f69f0f184a18e629",
    R0_SUCCESSOR: "1cc86ea976f1a718e25451d4cfe0568f0b905c167f3225bc835f4e7e6454bfdf",
}
MANDATORY_TEST_FILES = tuple(
    "tests/test_" + name + ".py"
    for name in (
        "horizon2_readiness",
        "horizon2_gaussian_information_geometry",
        "horizon2_gaussian_coordinates",
        "horizon2_smooth_information_geometry",
        "horizon2_posterior_convergence",
        "horizon2_markov_semigroup",
        "horizon2_scalar_gaussian_semigroup",
        "horizon2_transition_covariance_readiness",
        "horizon2_linear_gaussian_semigroup",
        "horizon2_fin4_gaussian_semigroup",
        "horizon2_gaussian_conditioning_readiness",
        "horizon2_gaussian_precision_conditioning",
        "horizon2_native_filter_posterior_readiness",
        "horizon2_gaussian_filter",
        "horizon2_gaussian_control",
        "horizon2_gaussian_grid_path",
        "horizon2_gaussian_vfe_readiness",
        "horizon2_smooth_reference_kernel",
        "horizon1_decision_risk",
        "horizon1_policy_action",
        "horizon1_finite_reference_agent",
        "native_blanket_formalisms",
        "formal_foundations",
        "formal_composition",
        "formalism_coverage",
        "formalism_relations",
        "formalism_novelty",
        "formalism_audit",
    )
)
PIN_FILES = (
    "lean/lean-toolchain",
    "lean/lakefile.lean",
    "lean/lake-manifest.json",
    "tests/conftest.py",
    "tests/_support/lean_runner.py",
    "tests/_support/h2_r0_custody.py",
    "src/fep_lean/formal/manifest.py",
)
CURRENT_FILES = (
    "src/fep_lean/verification/horizon_acceptance.py",
    "src/fep_lean/verification/numerical_witnesses.py",
    "src/fep_lean/verification/_horizon_numerical_witnesses.py",
    "tests/test_horizon_acceptance.py",
    "tests/test_numerical_witnesses.py",
    "tests/test_horizon_numerical_witnesses.py",
    BASE + "terminal_acceptance.py",
    "specs/horizon-2-smooth-stochastic/slices/07-terminal-certificate.md",
    "src/fep_lean/catalogue/registry.py",
    "src/fep_lean/catalogue/latex.py",
    "src/fep_lean/catalogue/bodies/__init__.py",
    "src/fep_lean/formal/declarations.py",
    "src/fep_lean/lean_source.py",
    *(entry.source_relative_path for entry in BODY_MODULE_MANIFEST),
)
DIAGNOSTIC_IDS = ("h2-scalar-terminal", "h2-fin4-blanket")
HEAVY_NODE = "tests/test_horizon2_transition_covariance_readiness.py::test_h2_5b_r0_generic_contract_has_exact_fin4_consumer"
DOWNSTREAM = {
    "opened": ["H3.G0 read-only continuous eligibility"],
    "closed": ["H3.0--H3.7"],
}
G0_DECLARATIONS = {
    "fin4_gaussian_semigroup.lean": (
        "axisFin_order",
        "K_posDef",
        "K_mul_Sigma",
        "Sigma_mul_K",
        "Sigma_eq_entries",
        "Sigma_isSymm",
        "Sigma_posDef",
        "transition_apply",
        "transition_zero",
        "transition_add",
        "transition_mean",
        "transition_covariance",
        "transitionCovariance_posSemidef",
        "transitionCovariance_posDef",
        "stationaryLaw_eq_gaussian",
        "stationaryLaw_invariant",
        "transitionProbability_tendsto_invariant",
        "integral_transition_tendsto_invariant",
        "exactFin4Carrier",
        "scalarParameters_exact",
        "projectedTransition_eq_scalarOU",
    ),
    "gaussian_precision_conditioning.lean": (
        "stationaryPartition_eq_compProd",
        "endpointCondDistrib_ae_eq_product",
        "externalConditionalKernel_mean",
        "externalConditionalKernel_variance",
        "external_condIndep_internal_given_blanket",
        "stationary_external_internal_covariance",
        "precisionZero_covarianceNonzero_condIndep",
        "perturbedEndpoint_external_internal_covariance",
        "perturbedEndpoint_external_not_indep_internal",
    ),
    "compositions/smooth_reference_kernel.lean": (
        "smoothReferenceKernel_terminal",
        "fin4ReferenceKernel_terminal",
    ),
}


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _object(value: Any, fields: set[str], label: str) -> dict[str, Any]:
    _require(
        isinstance(value, dict) and set(value) == fields, f"{label}: invalid fields"
    )
    return cast(dict[str, Any], value)


def _text(value: Any, label: str) -> str:
    _require(
        isinstance(value, str) and bool(value.strip()),
        f"{label}: empty/non-string value",
    )
    return cast(str, value)


def _file(root: Path, relative: str) -> Path:
    relative = _text(relative, "path")
    path = Path(relative)
    _require(not path.is_absolute() and ".." not in path.parts, "path escapes project")
    target = root / path
    _require(target.is_file(), f"missing evidence/source: {relative}")
    _require(target.resolve().is_relative_to(root.resolve()), "path escapes project")
    _require(
        not any(
            p.is_symlink()
            for p in (target, *target.parents)
            if p != root and root in p.parents
        ),
        "symlinked evidence/source",
    )
    return target


def _json(data: bytes) -> dict[str, Any]:
    try:
        result = load_strict_json(data)
    except RecursionError as exc:
        raise ValueError("JSON nesting exceeds the parser limit") from exc
    _require(isinstance(result, dict), "JSON root must be an object")
    return cast(dict[str, Any], result)


def source_snapshot(root: Path, paths: tuple[str, ...] | list[str]) -> dict[str, str]:
    """Hash exact input paths; refuse reads that race a mutation."""
    result = {}
    for relative in sorted(set(paths)):
        path = _file(root, relative)
        before = path.stat()
        result[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
        after = path.stat()
        _require(
            (before.st_mtime_ns, before.st_size, before.st_ino)
            == (after.st_mtime_ns, after.st_size, after.st_ino),
            "source changed during read",
        )
    return result


def native_source_paths(root: Path) -> tuple[str, ...]:
    """The native plane excludes Python validators/diagnostics added after capture."""
    canonical = root / "src/fep_lean/formal"
    resources = tuple(
        sorted(p.relative_to(canonical).as_posix() for p in canonical.rglob("*.lean"))
    )
    _require(bool(resources), "formal source roster empty")
    paths = list(PIN_FILES) + list(MANDATORY_TEST_FILES)
    for resource in resources:
        source = "src/fep_lean/formal/" + resource
        mirror = "lean/FepSketches/" + resource
        _require(
            _file(root, source).read_bytes() == _file(root, mirror).read_bytes(),
            "formal projection drift",
        )
        paths.extend((source, mirror))
    return tuple(sorted(paths))


def _artifact(root: Path, reference: Any) -> tuple[str, bytes]:
    ref = _object(reference, {"path", "sha256"}, "artifact")
    _require(
        isinstance(ref["sha256"], str)
        and re.fullmatch(r"[0-9a-f]{64}", ref["sha256"]) is not None,
        "invalid artifact digest",
    )
    data = _file(root, ref["path"]).read_bytes()
    _require(
        hashlib.sha256(data).hexdigest() == ref["sha256"], "artifact digest mismatch"
    )
    return ref["path"], data


def _number(value: str | None, *, integer: bool = False) -> float:
    _require(isinstance(value, str) and bool(value), "missing XML numeric field")
    assert isinstance(value, str)
    try:
        number = float(value)
    except (ValueError, OverflowError) as exc:
        raise ValueError("invalid XML number") from exc
    _require(math.isfinite(number) and number >= 0, "invalid XML number")
    _require(
        not integer or (value.isdecimal() and number.is_integer()), "invalid XML count"
    )
    return number


def validate_test_evidence(
    root: Path,
    collection: dict[str, Any],
    xml: bytes,
    supplemental_xml: bytes | None = None,
) -> tuple[str, ...]:
    """Compare the complete capture and JUnit, then enforce mandatory non-skips."""
    _object(collection, {"schema_version", "nodeids", "markers"}, "collection")
    _require(
        type(collection["schema_version"]) is int and collection["schema_version"] == 1,
        "collection schema",
    )
    nodes = collection["nodeids"]
    _require(
        isinstance(nodes, list)
        and bool(nodes)
        and all(isinstance(n, str) and "::" in n for n in nodes),
        "invalid collection nodeids",
    )
    _require(len(nodes) == len(set(nodes)), "duplicate collection node")
    markers = collection["markers"]
    _require(
        isinstance(markers, dict) and set(markers) == set(nodes),
        "collection markers incomplete",
    )
    _require(
        all(
            isinstance(m, list) and all(isinstance(s, str) for s in m)
            for m in markers.values()
        ),
        "invalid markers",
    )
    mandatory = tuple(n for n in nodes if n.split("::", 1)[0] in MANDATORY_TEST_FILES)
    for filename in MANDATORY_TEST_FILES:
        source = ast.parse(_file(root, filename).read_text())
        candidates = [
            *source.body,
            *(
                method
                for cls in source.body
                if isinstance(cls, ast.ClassDef) and cls.name.startswith("Test")
                for method in cls.body
            ),
        ]
        definitions = {
            n.name
            for n in candidates
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
            and n.name.startswith("test_")
        }
        collected = {
            n.split("::")[-1].split("[", 1)[0]
            for n in mandatory
            if n.startswith(filename + "::")
        }
        _require(
            bool(definitions) and definitions == collected,
            f"mandatory collection incomplete: {filename}",
        )
    _require(
        all(not {"skip", "xfail"}.intersection(markers[n]) for n in mandatory),
        "mandatory test marked skip/xfail",
    )
    cases = _junit_cases(xml)
    _require(set(cases) == set(nodes), "JUnit/collection node roster mismatch")
    skipped = {n for n in mandatory if cases[n].find("skipped") is not None}
    if supplemental_xml is not None:
        supplement = _junit_cases(supplemental_xml)
        _require(
            skipped == {HEAVY_NODE},
            "supplement must close only the captured heavy-probe skip",
        )
        _require(
            set(supplement) == {HEAVY_NODE}
            and supplement[HEAVY_NODE].find("skipped") is None,
            "supplement must pass the exact heavy probe",
        )
        skipped.remove(HEAVY_NODE)
    _require(not skipped, "mandatory JUnit test skipped/xfail")
    return mandatory


def _junit_cases(xml: bytes) -> dict[str, ET.Element]:
    _require(
        b"<!DOCTYPE" not in xml and b"<!ENTITY" not in xml,
        "DTD/entity XML is forbidden",
    )
    try:
        tree = ET.fromstring(xml)
    except (ET.ParseError, RecursionError) as exc:
        raise ValueError("invalid JUnit XML") from exc
    _require(tree.tag in {"testsuite", "testsuites"}, "invalid JUnit root")
    _require(
        not tree.findall(".//failure") and not tree.findall(".//error"),
        "JUnit contains failures/errors",
    )
    _require(
        all(
            element.tag
            in {
                "testsuites",
                "testsuite",
                "testcase",
                "skipped",
                "properties",
                "property",
                "system-out",
                "system-err",
            }
            for element in tree.iter()
        ),
        "unknown JUnit element or namespaced outcome",
    )
    cases: dict[str, ET.Element] = {}
    for case in tree.iter("testcase"):
        classname = _text(case.get("classname"), "JUnit classname")
        parts = classname.split(".")
        boundary = next(
            (i for i, part in enumerate(parts) if part.startswith("test_")), None
        )
        _require(boundary is not None, "unrecognized pytest classname")
        assert boundary is not None
        node = "/".join(parts[: boundary + 1]) + ".py::"
        node += "::".join(
            [*parts[boundary + 1 :], _text(case.get("name"), "JUnit name")]
        )
        _require(node not in cases, "duplicate JUnit node")
        _number(case.get("time"))
        _require(
            {child.tag for child in case}
            <= {"skipped", "properties", "system-out", "system-err"},
            "unknown testcase outcome",
        )
        cases[node] = case
    for suite in tree.iter("testsuite"):
        children = list(suite.iter("testcase"))
        _require(
            _number(suite.get("tests"), integer=True) == len(children),
            "JUnit test count mismatch",
        )
        _require(
            _number(suite.get("failures"), integer=True) == 0
            and _number(suite.get("errors"), integer=True) == 0,
            "JUnit nonzero failure counts",
        )
        _require(
            _number(suite.get("skipped"), integer=True)
            == sum(c.find("skipped") is not None for c in children),
            "JUnit skip count mismatch",
        )
        _number(suite.get("time"))
    _require(bool(cases), "empty JUnit report")
    if tree.tag == "testsuites":
        totals = {
            "tests": len(cases),
            "failures": 0,
            "errors": 0,
            "skipped": sum(c.find("skipped") is not None for c in cases.values()),
        }
        for name, expected in totals.items():
            if name in tree.attrib:
                _require(
                    _number(tree.get(name), integer=True) == expected,
                    "JUnit root count mismatch",
                )
        if "time" in tree.attrib:
            _number(tree.get("time"))
    return cases


def _predecessors(root: Path, binding: Any) -> None:
    _require(
        binding == PREDECESSORS, "predecessor chain differs from reviewed whitelist"
    )
    for path, digest in PREDECESSORS.items():
        _, data = _artifact(root, {"path": path, "sha256": digest})
        receipt = _json(data)  # Exact immutable digest pins the complete schema.
        for name, expected in receipt.get("source_sha256", {}).items():
            if path.endswith("/07-gaussian-vfe-natural-gradient.json") and name in {
                "src/fep_lean/formal/manifest.py",
                "tests/test_horizon2_gaussian_vfe_readiness.py",
            }:
                continue  # Only the fixed successor above may authorize this drift.
            _require(
                source_snapshot(root, [name])[name] == expected,
                "stale predecessor source",
            )
    successor = _json(_file(root, R0_SUCCESSOR).read_bytes())
    _require(
        successor["native_evidence"]["status"] == "verified",
        "R0 current native evidence pending",
    )
    _require(
        successor["native_evidence"]["historical_evidence_reused"] is False,
        "R0 historical execution reused",
    )
    for probe in successor["native_evidence"]["probes"]:
        _require(
            probe["source_sha256"] == successor["source_sha256"]
            and probe["pytest_exit_code"] == 0,
            "R0 probe source mismatch",
        )


def diagnostic_record(root: Path) -> dict[str, Any]:
    """Evaluate and source-bind the two H2 witnesses without invoking Lean."""
    inputs = sorted(set(CURRENT_FILES) | set(native_source_paths(root)))
    before = source_snapshot(root, inputs)
    evaluated = evaluate_numerical_witnesses(root)
    witnesses = {w.id: w for w in evaluated}
    _require(len(witnesses) == len(evaluated), "duplicate diagnostic ID")
    records = []
    for identifier in DIAGNOSTIC_IDS:
        _require(identifier in witnesses, "required H2 diagnostic missing")
        witness = witnesses[identifier]
        _require(
            witness.evidence_kind == NON_PROOF_EVIDENCE
            and getattr(witness, "scope", None) == "horizon2",
            "diagnostic is not horizon2 non-proof evidence",
        )
        _require(bool(witness.checks), "diagnostic checks empty")
        _require(witness.boundary_observed is True, "diagnostic boundary failed")
        for check in witness.checks:
            checked = NumericalCheck(**asdict(check))
            _require(checked.accepted, f"diagnostic check failed: {checked.id}")
        records.append(json.loads(json.dumps(asdict(witness), allow_nan=False)))
    after = source_snapshot(root, inputs)
    _require(before == after, "diagnostic source changed during evaluation")
    return {
        "schema_version": 1,
        "evidence_kind": NON_PROOF_EVIDENCE,
        "source_before": before,
        "source_after": after,
        "witnesses": records,
    }


@dataclass(frozen=True)
class HorizonAcceptance:
    """A validated bounded claim, without H3 implementation or publication promotion."""

    receipt_sha256: str
    mandatory_nodeids: tuple[str, ...]
    source_sha256: dict[str, str]
    reviewed_by: tuple[str, ...]
    opened: str = "H3.G0 read-only continuous eligibility"


def validate_terminal_acceptance(
    root: Path, receipt_path: str = TERMINAL_RECEIPT
) -> HorizonAcceptance:
    """Validate actual evidence and verify every consumed input stays byte/mtime stable."""
    root = root.resolve()
    consumed: set[str] = set()
    stats: dict[str, tuple[int, str]] = {}

    def track(paths: list[str] | tuple[str, ...]) -> None:
        for path in paths:
            file = _file(root, path)
            state = (
                file.stat().st_mtime_ns,
                hashlib.sha256(file.read_bytes()).hexdigest(),
            )
            _require(
                path not in stats or stats[path] == state,
                "input changed during validation",
            )
            stats[path] = state
            consumed.add(path)

    def artifact(reference: Any) -> tuple[str, bytes]:
        path, data = _artifact(root, reference)
        track([path])
        _require(stats[path][1] == reference["sha256"], "artifact changed during read")
        return path, data

    track([receipt_path])
    raw = _json(_file(root, receipt_path).read_bytes())
    _object(
        raw,
        {
            "schema_version",
            "gate",
            "decision",
            "native_evidence",
            "current_sources",
            "predecessors",
            "reviews",
            "diagnostics",
            "downstream",
        },
        "terminal acceptance",
    )
    _require(
        type(raw["schema_version"]) is int and raw["schema_version"] == 1,
        "acceptance schema",
    )
    _require(
        raw["gate"] == "H2.7" and raw["decision"] == "accepted",
        "terminal is not accepted",
    )
    _require(raw["downstream"] == DOWNSTREAM, "terminal downstream scope expanded")
    native_paths = native_source_paths(root)
    track(native_paths)
    track(CURRENT_FILES)
    native = source_snapshot(root, list(native_paths))
    current = source_snapshot(root, list(CURRENT_FILES))
    _require(
        raw["current_sources"] == current,
        "current validator/diagnostic source mismatch",
    )
    evidence = _object(
        raw["native_evidence"],
        {
            "collection",
            "junit",
            "source_before",
            "source_after",
            "pytest_exit_code",
            "heavy_probe_supplement",
        },
        "native evidence",
    )
    _require(
        type(evidence["pytest_exit_code"]) is int and evidence["pytest_exit_code"] == 0,
        "native pytest exit not successful",
    )
    _require(
        evidence["source_before"] == evidence["source_after"] == native,
        "native source capture stale or changed",
    )
    _, collection = artifact(evidence["collection"])
    _require(
        hashlib.sha256(collection).hexdigest() == CAPTURED_COLLECTION_SHA256,
        "collection differs from frozen captured roster",
    )
    _, xml = artifact(evidence["junit"])
    supplemental_xml = None
    if evidence["heavy_probe_supplement"] is not None:
        supplement = _object(
            evidence["heavy_probe_supplement"],
            {
                "junit",
                "source_before",
                "source_after",
                "pytest_exit_code",
                "environment",
            },
            "heavy probe supplement",
        )
        _require(
            type(supplement["pytest_exit_code"]) is int
            and supplement["pytest_exit_code"] == 0,
            "supplement did not pass",
        )
        _require(
            supplement["source_before"] == supplement["source_after"] == native,
            "supplement native source differs",
        )
        _require(
            supplement["environment"] == {"FEP_HEAVY_LEAN_PROBES": "1"},
            "supplement heavy-probe environment missing",
        )
        _, supplemental_xml = artifact(supplement["junit"])
    mandatory = validate_test_evidence(root, _json(collection), xml, supplemental_xml)
    track(list(PREDECESSORS))
    _predecessors(root, raw["predecessors"])
    for path in PREDECESSORS:
        track(list(_json(_file(root, path).read_bytes()).get("source_sha256", {})))
    _predecessors(root, raw["predecessors"])
    expected_review_sources = native | current
    reviews = raw["reviews"]
    _require(isinstance(reviews, list) and len(reviews) == 3, "three reviews required")
    roles: set[str] = set()
    people: list[str] = []
    review_paths: set[str] = set()
    for ref in reviews:
        path, data = artifact(ref)
        review_paths.add(path)
        review = _object(
            _json(data),
            {
                "schema_version",
                "role",
                "reviewer_id",
                "decision",
                "source_sha256",
                "findings",
            },
            "review",
        )
        _require(
            type(review["schema_version"]) is int and review["schema_version"] == 1,
            "review schema",
        )
        _require(review["decision"] == "approve", "review not approved")
        _require(
            review["source_sha256"] == expected_review_sources,
            "review target source mismatch",
        )
        _text(review["findings"], "review findings")
        roles.add(_text(review["role"], "review role"))
        people.append(_text(review["reviewer_id"], "reviewer identity"))
    _require(
        roles == {"lean", "domain", "skeptical"}
        and len(set(people)) == 3
        and len(review_paths) == 3,
        "reviews are not distinct independent roles",
    )
    _, data = artifact(raw["diagnostics"])
    _require(
        _json(data) == diagnostic_record(root),
        "diagnostic record differs from current evaluation",
    )
    for path in consumed:
        file = _file(root, path)
        _require(
            stats[path]
            == (file.stat().st_mtime_ns, hashlib.sha256(file.read_bytes()).hexdigest()),
            "input changed during validation",
        )
    return HorizonAcceptance(
        stats[receipt_path][1], mandatory, expected_review_sources, tuple(people)
    )


def validate_continuous_eligibility(root: Path, metadata_path: str) -> dict[str, Any]:
    """Evaluate G0 only; frozen protocols and finite-branch selection are out of scope."""
    root = root.resolve()
    acceptance = validate_terminal_acceptance(root)
    tracked = (*acceptance.source_sha256, TERMINAL_RECEIPT)
    initial_state = {
        name: (_file(root, name).stat().st_mtime_ns, _file(root, name).read_bytes())
        for name in tracked
    }
    _require(
        source_snapshot(root, list(acceptance.source_sha256))
        == acceptance.source_sha256,
        "G0 source changed after terminal validation",
    )
    metadata_file = _file(root.resolve(), metadata_path)
    before = (metadata_file.stat().st_mtime_ns, metadata_file.read_bytes())
    metadata = _object(
        _json(before[1]),
        {
            "schema_version",
            "branch",
            "outcomes_accessed",
            "pre_outcome_basis",
            "finite_branch_considered",
        },
        "G0 metadata",
    )
    _require(
        type(metadata["schema_version"]) is int and metadata["schema_version"] == 1,
        "G0 metadata schema",
    )
    _require(
        metadata["branch"] == "continuous" and metadata["outcomes_accessed"] is False,
        "G0 requires exactly one continuous pre-outcome branch",
    )
    _require(
        metadata["finite_branch_considered"] is False,
        "finite eligibility requires a separate H1 no-go/repair evidence review",
    )
    _text(metadata["pre_outcome_basis"], "pre-outcome selection basis")
    for resource, names in G0_DECLARATIONS.items():
        path = "src/fep_lean/formal/" + resource
        _require(
            source_snapshot(root, [path])[path] == acceptance.source_sha256[path],
            "G0 carrier source drift",
        )
        source = _file(root, path).read_text()
        for name in names:
            _require(
                re.search(r"(?m)^theorem " + re.escape(name) + r"\b", source)
                is not None,
                "G0 declaration missing: " + name,
            )
    _require(
        before == (metadata_file.stat().st_mtime_ns, metadata_file.read_bytes()),
        "G0 metadata changed during read",
    )
    _require(
        initial_state
        == {
            name: (_file(root, name).stat().st_mtime_ns, _file(root, name).read_bytes())
            for name in tracked
        },
        "G0 inputs changed during validation",
    )
    return {
        "schema_version": 1,
        "gate": "H3.G0",
        "branch": "continuous",
        "terminal_acceptance_sha256": acceptance.receipt_sha256,
        "metadata_sha256": hashlib.sha256(before[1]).hexdigest(),
        "declarations": {k: list(v) for k, v in G0_DECLARATIONS.items()},
        "source_sha256": acceptance.source_sha256,
        "opened": ["H3.0 protocol preparation"],
        "closed": ["H3.1--H3.7"],
        "protocol_frozen": False,
    }


def write_explicit_output(
    root: Path, target: Path, payload: dict[str, Any], *, inputs: tuple[Path, ...]
) -> None:
    """Exclusive-create an explicit output; never overwrite evidence or source."""
    destination = target.resolve()
    _require(destination not in {p.resolve() for p in inputs}, "output aliases input")
    _require(not target.is_symlink() and not target.exists(), "output already exists")
    lexical_target = target.absolute()
    # Locate the project through its actual ancestor identity: an external
    # alias (including macOS /tmp) must not hide symlinks below that root.
    project_ancestor = next(
        (
            parent
            for parent in reversed(lexical_target.parents)
            if parent.resolve() == root.resolve()
        ),
        None,
    )
    if project_ancestor is not None:
        _require(
            not any(
                parent.is_symlink()
                for parent in lexical_target.parents
                if parent != project_ancestor
                and parent.is_relative_to(project_ancestor)
            ),
            "output parent must not traverse a symlink within the project",
        )
    if destination.is_relative_to(root.resolve()):
        relative = destination.relative_to(root.resolve()).as_posix()
        _require(
            relative.startswith(("output/", "specs/h3-reference-study/output/")),
            "output must be in an evidence output directory",
        )
    serialized = json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n"
    with target.open("x", encoding="utf-8") as stream:
        stream.write(serialized)
