#!/usr/bin/env python3
"""Generate/check the Q7 static coefficient probe; never run Lean or a runner."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import shutil
import sys
import uuid
from pathlib import Path
from types import ModuleType

SLICE = Path(__file__).resolve().parent
ROOT = SLICE.parents[1]
PREFIX = "specs/gnn-bridge-q7-continuous-ou-proof"
EXTRACTOR = "src/fep_lean/verification/gnn_continuous_artifact_proof.py"
GENERATOR = f"{PREFIX}/generate_probe.py"
EXPECTED = f"{PREFIX}/expected.json"
FIXTURES = {"ou": f"{PREFIX}/fixtures/continuous_ou_jax.py"}
PROBES = {"ou": f"{PREFIX}/generated/probe.lean"}
MANIFEST = f"{PREFIX}/generated/artifact_proof_manifest.json"
TEMPLATE = f"{PREFIX}/probe.template.lean"
PROVENANCE = f"{PREFIX}/render_provenance.json"
INPUT = f"{PREFIX}/fixtures/FepLeanContinuousOU.md"
TARGETS = ("FepSketches.compositions.smooth_reference_kernel",)
SERIALIZATION_PROTOCOL = f"{PREFIX}/scaffold-serialization.md"
CANONICAL_SCAFFOLD = f"{PREFIX}/generated/scaffold-canonical.json"
PORTABILITY_EVIDENCE = f"{PREFIX}/generated/scaffold-runtime-parity.json"
PORTABILITY_INPUTS = (
    EXTRACTOR,
    GENERATOR,
    FIXTURES["ou"],
    SERIALIZATION_PROTOCOL,
    "src/fep_lean/verification/_jsonutil.py",
    "src/fep_lean/_paths.py",
)
PORTABILITY_CONTROLS = {
    "argument_order",
    "annotation",
    "bool_identity",
    "float_identity",
    "keyword_order",
    "type_comment",
    "unknown_node",
    "unknown_attribute",
    "unknown_field",
    "nonempty_type_params",
    "validator_contract",
}
EXTRA_FILES = (
    EXPECTED,
    TEMPLATE,
    INPUT,
    f"{PREFIX}/refresh_render.py",
    SERIALIZATION_PROTOCOL,
    CANONICAL_SCAFFOLD,
    PORTABILITY_EVIDENCE,
    "src/fep_lean/verification/_jsonutil.py",
    "src/fep_lean/_paths.py",
)


def _extractor(root: Path) -> ModuleType:
    path = root / EXTRACTOR
    verified = globals().get("_VERIFIED_ARTIFACT_DIGESTS")
    expected_digest = (
        verified[EXTRACTOR]
        if verified is not None
        else hashlib.sha256(path.read_bytes()).hexdigest()
    )
    source_bytes = path.read_bytes()
    if hashlib.sha256(source_bytes).hexdigest() != expected_digest:
        raise ValueError("Q7 extractor changed before its exact buffer was executed")
    module = ModuleType("_q7_checked_extractor_" + uuid.uuid4().hex)
    module.__file__ = str(path)
    # Preserve the parent's retained-buffer import authority for dependencies.
    module.__dict__["__builtins__"] = globals()["__builtins__"]
    sys.modules[module.__name__] = module
    try:
        exec(compile(source_bytes, str(path), "exec"), module.__dict__)  # noqa: S102 - execute exactly the digest-verified owned source buffer
    finally:
        sys.modules.pop(module.__name__, None)
    return module


def regenerate(root: Path = ROOT) -> tuple[dict[str, str], dict[str, object]]:
    """Pure artifact regeneration hook for the parent's source-verified loader.

    Parent custody must fingerprint and verify extractor/generator buffers before
    executing either module and recheck after regeneration. This hook emits no
    success verdict and performs no native or runner execution.
    """
    root = root.resolve()
    api = _extractor(root)
    expected_bytes = (root / EXPECTED).read_bytes()
    expected = api.read_json_object(expected_bytes)
    artifact_bytes = (root / FIXTURES["ou"]).read_bytes()
    validate_scaffold_portability(root, api, artifact_bytes.decode())
    artifact = api.extract_continuous_artifact(artifact_bytes.decode(), expected)
    input_bytes = (root / INPUT).read_bytes()
    api.validate_input_document(input_bytes.decode(), artifact)
    provenance = api.read_json_object((root / PROVENANCE).read_bytes())
    # Local integrity check only; parent must independently supply current owners.
    api.validate_render_provenance(
        provenance,
        input_bytes=input_bytes,
        artifact_bytes=artifact_bytes,
        owners=provenance.get("owners_before", {}),
    )
    probe = api.render_lean_probe(artifact, (root / TEMPLATE).read_text()).encode()
    files = [
        EXTRACTOR,
        GENERATOR,
        EXPECTED,
        TEMPLATE,
        PROVENANCE,
        INPUT,
        FIXTURES["ou"],
        f"{PREFIX}/refresh_render.py",
        SERIALIZATION_PROTOCOL,
        CANONICAL_SCAFFOLD,
        PORTABILITY_EVIDENCE,
        "src/fep_lean/verification/_jsonutil.py",
        "src/fep_lean/_paths.py",
    ]
    manifest = {
        "schema_version": 1,
        "evidence_plane": "static artifact certificate inputs",
        "native_evidence": "required separately; not supplied by generation",
        "artifact": artifact.to_dict(),
        "expected_contract_sha256": api.digest(expected_bytes),
        "inputs": {path: api.digest((root / path).read_bytes()) for path in files},
        "outputs": {PROBES["ou"]: api.digest(probe)},
        "receipt_contract": {
            "input_variant": "continuous",
            "canonical_variant": "ou",
            "fixtures": FIXTURES,
            "probes": PROBES,
            "targets": list(TARGETS),
            "theorems": {"ou": [f"{api.NAMESPACE}.{name}" for name in api.THEOREMS]},
            "render_route": api.RENDER_ROUTE,
            "extractor": EXTRACTOR,
            "extra_files": list(EXTRA_FILES),
            "allowed_axioms": ["propext", "Classical.choice", "Quot.sound"],
            "scope": "static binary64 coefficient approximation and real-arithmetic prediction bounds",
        },
    }
    return {
        "generated/probe.lean": probe.decode(),
        "generated/artifact_proof_manifest.json": api.canonical_json(manifest),
    }, manifest


def validate_scaffold_portability(root: Path, api: ModuleType, source: str) -> None:
    """Reject stale parity bookkeeping; stored observations are not new runs."""
    encoded = (root / CANONICAL_SCAFFOLD).read_bytes()
    evidence = api.read_json_object((root / PORTABILITY_EVIDENCE).read_bytes())
    expected_inputs = {
        name: hashlib.sha256((root / name).read_bytes()).hexdigest()
        for name in PORTABILITY_INPUTS
    }
    if (
        type(evidence.get("schema_version")) is not int
        or evidence.get("schema_version") != 1
        or evidence.get("kind") != "q7-canonical-scaffold-runtime-parity"
        or evidence.get("evidence_plane")
        != "static parser and candidate serialization observations"
        or evidence.get("runner_execution") is not False
        or evidence.get("native_evidence")
        != "not supplied; new native capture required separately"
        or evidence.get("validator_interpreters") != ["cpython 3.14"]
        or evidence.get("input_stability_verified") is not True
        or evidence.get("inputs") != expected_inputs
        or evidence.get("canonical_bytes") != len(encoded)
        or evidence.get("canonical_sha256") != api.digest(encoded)
        or encoded != api.canonical_scaffold_bytes(source)
    ):
        raise ValueError("Q7 canonical scaffold parity evidence is stale or malformed")
    runtimes = evidence.get("runtimes")
    if not isinstance(runtimes, list) or len(runtimes) != 5:
        raise ValueError("Q7 scaffold parity needs exactly five runtime observations")
    # Observations enumerate the reviewed candidate's present node classes.
    # The canonical serializer above still checks every node against the full
    # fail-closed schema; an allowed class need not occur in this candidate.
    present_nodes = {
        type(node).__name__ for node in ast.walk(ast.parse(source, type_comments=True))
    }
    for minor, record in zip(range(10, 15), runtimes, strict=True):
        expected_fields = {
            name: list(api._SCAFFOLD_AST_FIELDS[name]) for name in present_nodes
        }
        if minor < 12 and "FunctionDef" in expected_fields:
            expected_fields["FunctionDef"].remove("type_params")
        if (
            not isinstance(record, dict)
            or record.get("implementation") != "cpython"
            or not isinstance(record.get("version_info"), list)
            or len(record["version_info"]) != 3
            or any(
                type(value) is not int or value < 0 for value in record["version_info"]
            )
            or record["version_info"][:2] != [3, minor]
            or record.get("canonical_sha256") != api.digest(encoded)
            or record.get("observed_fields") != expected_fields
            or not isinstance(record.get("controls"), dict)
            or set(record["controls"]) != PORTABILITY_CONTROLS
            or any(value is not True for value in record["controls"].values())
        ):
            raise ValueError(
                "Q7 scaffold runtime observation is incomplete or rejecting"
            )


_PORTABILITY_PROGRAM = r"""
import ast, hashlib, json, platform, sys, types
from pathlib import Path
sys.dont_write_bytecode = True
root = Path(sys.argv[1])
for name in ("fep_lean", "fep_lean.verification"):
    package = types.ModuleType(name)
    package.__path__ = []
    sys.modules[name] = package
for name, relative in (
    ("fep_lean._paths", "src/fep_lean/_paths.py"),
    ("fep_lean.verification._jsonutil", "src/fep_lean/verification/_jsonutil.py"),
    ("q7_portability_owner", "src/fep_lean/verification/gnn_continuous_artifact_proof.py"),
):
    path = root / relative
    data = path.read_bytes()
    module = types.ModuleType(name)
    module.__file__ = str(path)
    sys.modules[name] = module
    exec(compile(data, str(path), "exec"), module.__dict__)
    assert path.read_bytes() == data, "owned source changed during loading"
api = sys.modules["q7_portability_owner"]
source = (root / "specs/gnn-bridge-q7-continuous-ou-proof/fixtures/continuous_ou_jax.py").read_text()
encoded = api.canonical_scaffold_bytes(source)
controls = {}
for label, old, new in (
    ("argument_order", "def solve(a, b):", "def solve(b, a):"),
    ("annotation", "def arr(x):", "def arr(x: int) -> float:"),
    ("bool_identity", "jax_enable_x64', True", "jax_enable_x64', 1"),
    ("float_identity", "DT = 1.0", "DT = 1"),
    ("keyword_order", "parents=True, exist_ok=True", "exist_ok=True, parents=True"),
    ("type_comment", "RANDOM_SEED = 42", "RANDOM_SEED = 42  # type: int"),
):
    assert old in source
    controls[label] = api.canonical_scaffold_bytes(source.replace(old, new)) != encoded
def rejected(label, callback):
    try:
        callback()
    except api.ContinuousArtifactError as error:
        controls[label] = error.reason == "scaffold_schema"
    else:
        controls[label] = False
rejected("unknown_node", lambda: api.canonical_scaffold_bytes(source + "\nclass New: pass\n"))
node = ast.Name(id="x", ctx=ast.Load())
node.future_semantic = "unreviewed"
rejected("unknown_attribute", lambda: api._canonical_scaffold_value(node))
fields = ast.Name._fields
ast.Name._fields = (*fields, "future_semantic")
try:
    rejected("unknown_field", lambda: api._canonical_scaffold_value(ast.Name(id="x", ctx=ast.Load())))
finally:
    ast.Name._fields = fields
function = next(node for node in ast.parse(source).body if isinstance(node, ast.FunctionDef))
function.type_params = [ast.Name(id="T", ctx=ast.Load())]
rejected("nonempty_type_params", lambda: api._canonical_scaffold_value(function))
if sys.version_info[:2] == (3, 14):
    controls["validator_contract"] = api.scaffold_digest(source) == hashlib.sha256(encoded).hexdigest()
else:
    try:
        api.scaffold_digest("invalid syntax !!!")
    except api.ContinuousArtifactError as error:
        controls["validator_contract"] = error.reason == "interpreter"
    else:
        controls["validator_contract"] = False
assert all(controls.values()), controls
print(json.dumps({
    "implementation": sys.implementation.name,
    "version": sys.version,
    "version_info": list(sys.version_info[:3]),
    "platform": sys.platform,
    "machine": platform.machine(),
    "canonical_bytes": encoded.decode("ascii"),
    "canonical_sha256": hashlib.sha256(encoded).hexdigest(),
    "controls": controls,
    "observed_fields": {type(node).__name__: list(node._fields) for node in ast.walk(ast.parse(source, type_comments=True))},
}, sort_keys=True))
"""


def scaffold_portability_evidence(root: Path = ROOT) -> tuple[bytes, dict[str, object]]:
    """Observe real parser/serializer parity; no runner or native execution."""
    from fep_lean.verification._subprocess import run_process_group

    root = root.resolve()
    uv = shutil.which("uv")
    if uv is None:
        raise ValueError("scaffold parity requires uv and all five installed runtimes")
    before = {
        name: hashlib.sha256((root / name).read_bytes()).hexdigest()
        for name in PORTABILITY_INPUTS
    }
    observed: list[dict[str, object]] = []
    canonical: bytes | None = None
    environment = {
        key: value
        for key, value in os.environ.items()
        if key not in {"PYTHONPATH", "PYTHONHOME", "VIRTUAL_ENV"}
    }
    for minor in range(10, 15):
        command = [
            uv,
            "run",
            "--offline",
            "--no-project",
            "--python",
            f"3.{minor}",
            "python",
            "-I",
            "-c",
            _PORTABILITY_PROGRAM,
            str(root),
        ]
        completed = run_process_group(command, cwd=root, env=environment, timeout=30)
        if completed.returncode:
            raise ValueError(
                f"CPython 3.{minor} parity probe failed: {completed.stderr}"
            )
        record = json.loads(completed.stdout)
        encoded = record.pop("canonical_bytes").encode("ascii")
        if record["implementation"] != "cpython" or record["version_info"][:2] != [
            3,
            minor,
        ]:
            raise ValueError("parity probe ran an unexpected interpreter")
        if hashlib.sha256(encoded).hexdigest() != record["canonical_sha256"]:
            raise ValueError("parity probe bytes and digest disagree")
        if canonical is None:
            canonical = encoded
        elif encoded != canonical:
            raise ValueError("canonical scaffold bytes differ across actual runtimes")
        observed.append(record)
    after = {
        name: hashlib.sha256((root / name).read_bytes()).hexdigest()
        for name in PORTABILITY_INPUTS
    }
    if before != after or canonical is None:
        raise ValueError("parity inputs changed during observations")
    return canonical, {
        "schema_version": 1,
        "kind": "q7-canonical-scaffold-runtime-parity",
        "evidence_plane": "static parser and candidate serialization observations",
        "runner_execution": False,
        "native_evidence": "not supplied; new native capture required separately",
        "validator_interpreters": ["cpython 3.14"],
        "probe_command": "uv run --locked python specs/gnn-bridge-q7-continuous-ou-proof/generate_probe.py --record-scaffold-portability",
        "inputs": before,
        "input_stability_verified": True,
        "canonical_bytes": len(canonical),
        "canonical_sha256": hashlib.sha256(canonical).hexdigest(),
        "runtimes": observed,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--record-scaffold-portability", action="store_true")
    args = parser.parse_args()
    if args.record_scaffold_portability:
        canonical, evidence = scaffold_portability_evidence()
        (ROOT / CANONICAL_SCAFFOLD).write_bytes(canonical)
        (ROOT / PORTABILITY_EVIDENCE).write_text(
            json.dumps(evidence, sort_keys=True, indent=2) + "\n"
        )
        print(
            f"Five real CPython runtimes returned identical candidate bytes: {evidence['canonical_sha256']}; no runner/native execution."
        )
        return 0
    outputs, _manifest = regenerate()
    if args.check:
        changed = [
            path
            for path, data in outputs.items()
            if not (SLICE / path).is_file() or (SLICE / path).read_text() != data
        ]
        if changed:
            raise ValueError(f"Q7 generated artifacts differ: {changed}")
        print(
            "Q7 generated artifacts current; native evidence must be checked separately."
        )
    else:
        for path, data in outputs.items():
            (SLICE / path).parent.mkdir(parents=True, exist_ok=True)
            (SLICE / path).write_text(data)
        print("Generated Q7 probe and manifest; no native compilation performed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
