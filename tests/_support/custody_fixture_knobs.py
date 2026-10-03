"""Clearly synthetic, hermetic custody epochs; never historical reacceptance.

The live H2 seal is immutable and may legitimately precede roster expansion.
Positive unit tests therefore fabricate an internally consistent epoch under
tmp_path, including synthetic reviews and passing JUnit records. Only declared
validator/source/reference dependencies are copied. Unrelated research outputs
are never enumerated or copied. No compiler or scientific generator runs here.
Production validation remains unchanged; digest pins are patched only in the
test process and the disposable source copies.
"""

from __future__ import annotations

import ast
import hashlib
import json
import re
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

from fep_lean.custody import apply as apply_module
from fep_lean.output.provenance import CONFIG_OWNER_FILES, SOURCE_OWNER_FILES
from fep_lean.verification import horizon_acceptance as acceptance
from fep_lean.verification.horizon_acceptance import (
    CURRENT_FILES,
    MANDATORY_TEST_FILES,
    PIN_FILES,
    native_source_paths,
)
from tests._support import h2_r0_custody as current_r0

REPO_ROOT = Path(__file__).resolve().parents[2]

# Keep the real pre-H3 validator as recorded source, rather than weakening the
# current append-only custody rules to accept fabricated historical re-issues.
HISTORICAL_R0_COMMIT = "99e5cdf0690bebf219a49b598d9d80ff1da075d5"
HISTORICAL_R0_SOURCE = "tests/_support/h2_r0_custody.py"
HISTORICAL_R0_RESOURCE = "tests/_support/resources/h2_r0_custody_99e5cdf.py.txt"
HISTORICAL_R0_SHA256 = (
    "5c9452c8f9120ba0ae53adf19e35f1929701281a3891d2ef0cd1b1bd9523aabb"
)


def _historical_r0_bytes(source_root: Path) -> bytes:
    """Refuse any change to the frozen, explicitly test-only validator source."""
    resource = source_root / HISTORICAL_R0_RESOURCE
    assert resource.is_file() and not resource.is_symlink(), resource
    data = resource.read_bytes()
    assert hashlib.sha256(data).hexdigest() == HISTORICAL_R0_SHA256, (
        "frozen historical R0 validator changed"
    )
    return data


def _historical_r0_validator(source_root: Path) -> ModuleType:
    """Load the byte-checked historical implementation under an isolated name."""
    data = _historical_r0_bytes(source_root)
    filename = str(source_root / HISTORICAL_R0_RESOURCE)
    module = ModuleType("fep_lean_synthetic_pre_h3_r0_validator")
    module.__file__ = filename
    # Execute exactly the checked bytes, without a second filesystem read or
    # any loader cache that could substitute a different implementation.
    exec(compile(data, filename, "exec"), module.__dict__)  # noqa: S102 - pinned test resource
    return module


PY_DRIFT_MARKER = b"\n# custody fixture drift\n"

JSON_WHITESPACE_DRIFT = b"\n"

# The fep-lean CLI validates its project root against these checkout-bound
# markers (src/fep_lean/_paths.py); the fixture root carries copies so the
# custody CLI subcommands dispatch instead of refusing the checkout check.
_CHECKOUT_ONLY_FILES = (
    "config/topics.yaml",
    "config/settings.yaml",
    "manuscript/config.yaml",
    "src/fep_lean/__init__.py",
)


_SPEC_SEEDS = (
    apply_module.ACCEPTANCE,
    apply_module.MATRIX,
    apply_module.PIN_EVIDENCE,
    apply_module.PRIOR_07,
    apply_module.SUCCESSOR_07,
    apply_module.REPAIR_05D,
    apply_module.LIFECYCLE_05D,
    apply_module.REPAIR_05B,
    apply_module.REPAIR_06A,
    apply_module.TERMINAL_PACKET,
    apply_module.SPIKE_RECEIPT,
    apply_module.SPIKE_MODULE,
    apply_module.BASE + "validate.py",
    apply_module.BASE + "probes/11_unsupported_api_search.yaml",
)
_DIGEST_MAPS = frozenset(
    {
        "source_sha256",
        "source_before",
        "source_after",
        "current_sources",
        "predecessors",
        "digests",
    }
)
_SYNTHETIC_EVIDENCE = "specs/custody-unit-fixture/"


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json(root: Path, relative: str) -> dict[str, Any]:
    return json.loads((root / relative).read_text(encoding="utf-8"))


def _write_json(root: Path, relative: str, record: dict[str, Any]) -> str:
    data = apply_module.dump_json_bytes(record, relative=relative)
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return _sha(data)


def _consumed_paths(record: Any) -> set[str]:
    """Follow digest maps and actual terminal artifact refs, not historical prose."""
    paths: set[str] = set()
    if isinstance(record, dict):
        for key, value in record.items():
            if key in _DIGEST_MAPS and isinstance(value, dict):
                paths.update(value)
            paths.update(_consumed_paths(value))
        if record.get("gate") == "H2.7" and "native_evidence" in record:
            native = record["native_evidence"]
            refs = [
                native["collection"],
                native["junit"],
                record["diagnostics"],
                *record["reviews"],
            ]
            if native.get("heavy_probe_supplement") is not None:
                refs.append(native["heavy_probe_supplement"])
            paths.update(ref["path"] for ref in refs)
    elif isinstance(record, list):
        for value in record:
            paths.update(_consumed_paths(value))
    return paths


def declared_closure(source_root: Path) -> tuple[str, ...]:
    """Bounded transitive dependencies explicitly consumed by custody validators."""
    _historical_r0_bytes(source_root)
    pending = set(_SPEC_SEEDS) | set(acceptance.PREDECESSORS)
    pending |= set(PIN_FILES) | set(MANDATORY_TEST_FILES) | set(CURRENT_FILES)
    pending |= set(SOURCE_OWNER_FILES) | set(CONFIG_OWNER_FILES)
    pending |= set(native_source_paths(source_root)) | set(_CHECKOUT_ONLY_FILES)
    pending |= {
        "tests/_support/custody_fixture_knobs.py",
        "docs/development.md",
        HISTORICAL_R0_RESOURCE,
    }
    included: set[str] = set()
    while pending:
        relative = min(pending)
        pending.remove(relative)
        if relative in included:
            continue
        path = source_root / relative
        assert not Path(relative).is_absolute() and ".." not in Path(relative).parts
        assert path.is_file() and not path.is_symlink(), relative
        included.add(relative)
        if path.suffix == ".json":
            pending |= _consumed_paths(json.loads(path.read_text())) - included
    return tuple(sorted(included))


def stage_specs(source_root: Path, target: Path) -> Path:
    """Copy only the declared specs closure, including mutated fixture bytes."""
    target.mkdir(parents=True)
    for relative in declared_closure(source_root):
        if relative.startswith("specs/"):
            destination = target / relative[len("specs/") :]
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_root / relative, destination)
    return target


def _binding(root: Path, relative: str, name: str, value: Any) -> None:
    """Replace one literal in a disposable source; production pins stay intact."""
    path = root / relative
    source = path.read_text()
    matches = [
        node
        for node in ast.parse(source).body
        if isinstance(node, (ast.Assign, ast.AnnAssign))
        and any(
            isinstance(t, ast.Name) and t.id == name
            for t in (
                [node.target] if isinstance(node, ast.AnnAssign) else node.targets
            )
        )
    ]
    assert len(matches) == 1, (relative, name)
    old = ast.get_source_segment(source, matches[0].value)
    assert old is not None and source.count(old) == 1
    path.write_text(source.replace(old, json.dumps(value, indent=4), 1))


def _synthetic_prior_manifest(manifest: str, r0: ModuleType) -> str:
    """Construct the test-only prior required by the real transition validator."""
    groups = (
        (r0.ADDED_MODULES, "FOUNDATION"),
        (r0.WAVE3_FOUNDATION_ADDED_MODULES, "FOUNDATION"),
        (r0.WAVE3_COMPOSITION_ADDED_MODULES, "COMPOSITION"),
        (r0.WAVE4_FOUNDATION_ADDED_MODULES, "FOUNDATION"),
        (r0.WAVE4_COMPOSITION_ADDED_MODULES, "COMPOSITION"),
        (r0.WAVE4B_FOUNDATION_ADDED_MODULES, "FOUNDATION"),
    )
    for modules, role in groups:
        block = "".join(
            "    FormalModule(\n"
            f'        resource="{resource}",\n'
            f'        lean_module="{module}",\n'
            f"        role=FormalModuleRole.{role},\n"
            f'        declaration_namespace="{namespace}",\n'
            "    ),\n"
            for resource, module, namespace in modules
        )
        assert manifest.count(block) == 1
        manifest = manifest.replace(block, "", 1)
    assert manifest.count(r0._W4_DERIVED_RESOURCES_BLOCK) == 1
    manifest = manifest.replace(r0._W4_DERIVED_RESOURCES_BLOCK, "", 1)
    assert manifest.count(r0._W4_CONSOLIDATION_ANCHOR) == 1
    return manifest.replace(
        r0._W4_CONSOLIDATION_ANCHOR, r0._W4_RESTORED_LITERAL_BLOCK, 1
    )


def _synthetic_epoch(root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Fabricate mutually bound unit inputs without asserting any real outcome."""
    r0 = _historical_r0_validator(root)
    (root / apply_module.H2_R0_CUSTODY).write_bytes(_historical_r0_bytes(root))
    manifest_path = root / r0.MANIFEST_PATH
    manifest_path.write_text(
        current_r0._strip_h3_owner_additions(manifest_path.read_text())
    )
    prior_manifest = _synthetic_prior_manifest(manifest_path.read_text(), r0)
    for relative in (
        apply_module.ACCEPTANCE,
        apply_module.REPAIR_05B,
        apply_module.REPAIR_05D,
        apply_module.REPAIR_06A,
        apply_module.PRIOR_07,
    ):
        record = _json(root, relative)
        record["source_sha256"] = {
            p: _sha((root / p).read_bytes()) for p in record["source_sha256"]
        }
        if relative == apply_module.ACCEPTANCE:
            record["output"] = (
                "SYNTHETIC-UNIT-FIXTURE: fabricated all-pass input; no compiler executed.\n"
            )
            record["output_sha256"] = _sha(record["output"].encode())
        else:
            record["compiler"] = "SYNTHETIC-UNIT-FIXTURE-NO-COMPILER"
            record["evidence"] = "Fabricated unit input, not actual native evidence."
            record["review"] = (
                "SYNTHETIC-UNIT-FIXTURE: not an actual scientific review."
            )
        if relative == apply_module.PRIOR_07:
            record["source_sha256"][r0.MANIFEST_PATH] = _sha(prior_manifest.encode())
            # The real successor contract requires exactly these two differences.
            record["source_sha256"][r0.READINESS_TEST_PATH] = _sha(
                b"synthetic earlier VFE test"
            )
        digest = _write_json(root, relative, record)
        if relative == apply_module.ACCEPTANCE:
            matrix_path = root / apply_module.MATRIX
            updated, count = re.subn(
                r"(?m)^(  receipt_sha256: )[0-9a-f]{64}$",
                rf"\g<1>{digest}",
                matrix_path.read_text(),
            )
            assert count == 1
            matrix_path.write_text(updated)
    lifecycle = _json(root, apply_module.LIFECYCLE_05D)
    lifecycle["corrected_artifact"]["repair_sha256"] = _sha(
        (root / apply_module.REPAIR_05D).read_bytes()
    )
    _write_json(root, apply_module.LIFECYCLE_05D, lifecycle)
    for name, relative in (
        ("R0_REPAIR_SHA256", apply_module.REPAIR_05D),
        ("R0_LIFECYCLE_SHA256", apply_module.LIFECYCLE_05D),
    ):
        _binding(
            root,
            apply_module.PRECISION_TEST,
            name,
            _sha((root / relative).read_bytes()),
        )
    prior_sha = _sha((root / apply_module.PRIOR_07).read_bytes())
    _binding(root, apply_module.H2_R0_CUSTODY, "PRIOR_SHA256", prior_sha)
    successor = _json(root, apply_module.SUCCESSOR_07)
    successor["prior"]["sha256"] = prior_sha
    successor["manifest_transition"]["prior_sha256"] = _sha(prior_manifest.encode())
    successor["manifest_transition"]["current_sha256"] = _sha(
        manifest_path.read_bytes()
    )
    successor["manifest_transition"]["unchanged_owners"] = r0._manifest_owners(
        prior_manifest
    )
    successor["source_sha256"] = {
        p: _sha((root / p).read_bytes()) for p in successor["source_sha256"]
    }
    for probe in successor["native_evidence"]["probes"]:
        probe["source_sha256"] = successor["source_sha256"]
    _write_json(root, apply_module.SUCCESSOR_07, successor)
    predecessors = {p: _sha((root / p).read_bytes()) for p in acceptance.PREDECESSORS}
    module_path = root / apply_module.HORIZON_ACCEPTANCE_MODULE
    module_source = module_path.read_text()
    for path, old_digest in acceptance.PREDECESSORS.items():
        assert module_source.count(old_digest) == 1
        module_source = module_source.replace(old_digest, predecessors[path], 1)
    module_path.write_text(module_source)
    monkeypatch.setattr(acceptance, "PREDECESSORS", predecessors)
    packet = _json(root, apply_module.TERMINAL_PACKET)
    nodes = []
    for filename in MANDATORY_TEST_FILES:
        for node in ast.parse((root / filename).read_text()).body:
            if isinstance(
                node, (ast.FunctionDef, ast.AsyncFunctionDef)
            ) and node.name.startswith("test_"):
                nodes.append(filename + "::" + node.name)
            elif isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
                nodes.extend(
                    filename + "::" + node.name + "::" + method.name
                    for method in node.body
                    if isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and method.name.startswith("test_")
                )
    collection = {
        "schema_version": 1,
        "nodeids": nodes,
        "markers": {
            node: ["skipif"] if node == acceptance.HEAVY_NODE else [] for node in nodes
        },
    }
    collection_ref = {"path": _SYNTHETIC_EVIDENCE + "collection.json"}
    collection_ref["sha256"] = _write_json(root, collection_ref["path"], collection)
    monkeypatch.setattr(
        acceptance, "CAPTURED_COLLECTION_SHA256", collection_ref["sha256"]
    )
    _binding(
        root,
        apply_module.HORIZON_ACCEPTANCE_MODULE,
        "CAPTURED_COLLECTION_SHA256",
        collection_ref["sha256"],
    )
    suite = ET.Element(
        "testsuite",
        name="SYNTHETIC-UNIT-FIXTURE-NO-COMPILER",
        tests=str(len(collection["nodeids"])),
        failures="0",
        errors="0",
        skipped="0",
        time="0",
    )
    for node in collection["nodeids"]:
        parts = node.split("::")
        classname = parts[0].removesuffix(".py").replace("/", ".")
        if len(parts) > 2:
            classname += "." + ".".join(parts[1:-1])
        ET.SubElement(suite, "testcase", classname=classname, name=parts[-1], time="0")
    junit_path = _SYNTHETIC_EVIDENCE + "tests.xml"
    (root / junit_path).write_bytes(ET.tostring(suite))
    native = acceptance.source_snapshot(root, list(native_source_paths(root)))
    current = acceptance.source_snapshot(root, list(CURRENT_FILES))
    reviews = []
    for role in ("lean", "domain", "skeptical"):
        path = _SYNTHETIC_EVIDENCE + f"review-{role}.json"
        digest = _write_json(
            root,
            path,
            {
                "schema_version": 1,
                "role": role,
                "reviewer_id": f"SYNTHETIC-UNIT-FIXTURE-{role}",
                "decision": "approve",
                "source_sha256": native | current,
                "findings": "Fabricated custody unit input only; no actual review, compiler pass or horizon acceptance.",
            },
        )
        reviews.append({"path": path, "sha256": digest})
    diagnostic_path = _SYNTHETIC_EVIDENCE + "diagnostics.json"
    diagnostic_sha = _write_json(
        root, diagnostic_path, acceptance.diagnostic_record(root)
    )
    packet.update(
        current_sources=current,
        predecessors=predecessors,
        reviews=reviews,
        diagnostics={"path": diagnostic_path, "sha256": diagnostic_sha},
    )
    packet["native_evidence"] = {
        "collection": collection_ref,
        "junit": {"path": junit_path, "sha256": _sha((root / junit_path).read_bytes())},
        "source_before": native,
        "source_after": native,
        "pytest_exit_code": 0,
        "heavy_probe_supplement": None,
    }
    _write_json(root, apply_module.TERMINAL_PACKET, packet)
    spike = {
        "schema_version": 1,
        "digests": {
            p: _sha((root / p).read_bytes())
            for p in _json(root, apply_module.SPIKE_RECEIPT)["digests"]
        },
        "claim_boundary": "SYNTHETIC CUSTODY UNIT FIXTURE; no scientific outcome",
    }
    _write_json(root, apply_module.SPIKE_RECEIPT, spike)
    spike_path = root / apply_module.SPIKE_MODULE
    spike_source = spike_path.read_text()
    pinned = next(
        node.value
        for node in ast.parse(spike_source).body
        if isinstance(node, ast.AnnAssign)
        and isinstance(node.target, ast.Name)
        and node.target.id == "PINNED_SOURCES"
    )
    for path, old_digest in ast.literal_eval(pinned).items():
        assert spike_source.count(old_digest) == 1
        spike_source = spike_source.replace(old_digest, spike["digests"][path], 1)
    spike_path.write_text(spike_source)
    _write_json(
        root,
        "output/custody-unit-fixture.json",
        {
            "kind": "SYNTHETIC-UNIT-FIXTURE",
            "real_native_or_scientific_acceptance": False,
            "compiler": "SYNTHETIC-UNIT-FIXTURE-NO-COMPILER",
            "epoch": {
                "kind": "synthetic-pre-H3-custody",
                "validator_commit": HISTORICAL_R0_COMMIT,
                "validator_source": HISTORICAL_R0_SOURCE,
                "validator_resource": HISTORICAL_R0_RESOURCE,
                "validator_sha256": HISTORICAL_R0_SHA256,
                "current_h3_owners_admitted": False,
            },
            "boundary": "Rebound disposable source/receipt epoch. Reviews and JUnit outcomes fabricated solely to test fail-closed custody contracts.",
        },
    )


def fixture_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch | None = None) -> Path:
    """Build once, then preserve subsequent explicit drift injections verbatim."""
    root = tmp_path / "project"
    if root.exists():
        return root
    assert monkeypatch is not None, "new synthetic epochs require test-scoped pins"
    for relative in declared_closure(REPO_ROOT):
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO_ROOT / relative, destination)
    _synthetic_epoch(root, monkeypatch)
    return root


def spec_path(root: Path, relative: str) -> Path:
    """Map a ``specs/...`` repo-relative path onto the fixture's staged copy."""
    assert relative.startswith("specs/")
    return root / "specs" / relative[len("specs/") :]


def drift_file(path: Path, marker: bytes = PY_DRIFT_MARKER) -> None:
    """Append ``marker`` to one fixture file; tmp copies only, never live."""
    path.write_bytes(path.read_bytes() + marker)
