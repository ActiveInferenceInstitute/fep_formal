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
EXTRACTOR = "src/fep_formal/verification/gnn_continuous_artifact_proof.py"
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
    "src/fep_formal/verification/_jsonutil.py",
    "src/fep_formal/_paths.py",
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
    "src/fep_formal/verification/_jsonutil.py",
    "src/fep_formal/_paths.py",
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
        "src/fep_formal/verification/_jsonutil.py",
        "src/fep_formal/_paths.py",
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


def validate_scaffold_portability(
    root: Path,
    api: ModuleType,
    source: str,
    *,
    projection: dict[str, bytes] | None = None,
) -> None:
    """Reject stale parity bookkeeping; stored observations are not new runs."""
    encoded = (
        (root / CANONICAL_SCAFFOLD).read_bytes()
        if projection is None
        else projection["scaffold-canonical.json"]
    )
    evidence = api.read_json_object(
        (root / PORTABILITY_EVIDENCE).read_bytes()
        if projection is None
        else projection["scaffold-runtime-parity.json"]
    )
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
for name in ("fep_formal", "fep_formal.verification"):
    package = types.ModuleType(name)
    package.__path__ = []
    sys.modules[name] = package
for name, relative in (
    ("fep_formal._paths", "src/fep_formal/_paths.py"),
    ("fep_formal.verification._jsonutil", "src/fep_formal/verification/_jsonutil.py"),
    ("q7_portability_owner", "src/fep_formal/verification/gnn_continuous_artifact_proof.py"),
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
    from fep_formal.verification._subprocess import run_process_group

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
        # Portable recipe template, not the exact invocation of this capture.
        "probe_command": "uv run --locked python specs/gnn-bridge-q7-continuous-ou-proof/generate_probe.py --record-scaffold-portability --output-root NEW_DIRECTORY",
        "inputs": before,
        "input_stability_verified": True,
        "canonical_bytes": len(canonical),
        "canonical_sha256": hashlib.sha256(canonical).hexdigest(),
        "runtimes": observed,
    }


def _regular_path(path: Path) -> None:
    if any(parent.is_symlink() for parent in (path, *path.parents)):
        raise ValueError(f"Q7 publication refuses symlink paths: {path}")
    if not path.is_file() or path.stat().st_nlink != 1:
        raise ValueError(f"Q7 publication requires an unaliased regular file: {path}")


def _publication_files(directory: Path) -> dict[str, bytes]:
    if directory.is_symlink() or not directory.is_dir():
        raise ValueError("Q7 publication requires a regular generated directory")
    result = {}
    for path in directory.iterdir():
        _regular_path(path)
        result[path.name] = path.read_bytes()
    return result


def _install_publication(staged: Path, destination: Path, backup: Path) -> None:
    """Restore the complete preimage if installing the staged directory fails."""
    destination.rename(backup)
    try:
        staged.rename(destination)
    except OSError:
        backup.rename(destination)
        raise


def publish(root: Path, incoming: Path, *, scaffold: bool) -> Path:
    """Publish checked working projections, retaining a recoverable preimage.

    Two directory renames expose either complete bytes or a missing directory
    (fail-closed readers), never a mixed pair. An installation error restores
    the original directory. A process interruption leaves the named backup.
    This operation validates stored observations; it does not repeat runtimes.
    """
    destination = root / PREFIX / "generated"
    if (
        incoming.resolve() == (root / PREFIX).resolve()
        or incoming.resolve().is_relative_to(destination.resolve())
        or destination.resolve().is_relative_to(incoming.resolve())
    ):
        raise ValueError("Q7 publication source aliases destination")
    if set(incoming.iterdir()) != {incoming / "generated"}:
        raise ValueError("Q7 publication source must contain only generated outputs")
    candidate = _publication_files(incoming / "generated")
    names = (
        {"scaffold-canonical.json", "scaffold-runtime-parity.json"}
        if scaffold
        else {"probe.lean", "artifact_proof_manifest.json"}
    )
    if set(candidate) != names:
        raise ValueError("Q7 publication output set is incomplete or unknown")
    owned = {*PORTABILITY_INPUTS, *EXTRA_FILES, PROVENANCE}
    # Scaffold publication must work when the existing parity is stale.
    if scaffold:
        owned -= {CANONICAL_SCAFFOLD, PORTABILITY_EVIDENCE}
    for name in owned:
        _regular_path(root / name)
    before = {name: (root / name).read_bytes() for name in owned}
    if scaffold:
        validate_scaffold_portability(
            root,
            _extractor(root),
            (root / FIXTURES["ou"]).read_text(),
            projection=candidate,
        )
        evidence = _extractor(root).read_json_object(
            candidate["scaffold-runtime-parity.json"]
        )
        if set(evidence) != {
            "schema_version",
            "kind",
            "evidence_plane",
            "runner_execution",
            "native_evidence",
            "validator_interpreters",
            "probe_command",
            "inputs",
            "input_stability_verified",
            "canonical_bytes",
            "canonical_sha256",
            "runtimes",
        }:
            raise ValueError("Q7 publication parity contains unknown or missing fields")
        if (
            not isinstance(evidence["probe_command"], str)
            or not evidence["probe_command"].strip()
        ):
            raise ValueError("Q7 publication probe_command must be a nonempty recipe")
        for record in evidence.get("runtimes", []):
            if not isinstance(record, dict) or set(record) != {
                "implementation",
                "version",
                "version_info",
                "platform",
                "machine",
                "canonical_sha256",
                "controls",
                "observed_fields",
            }:
                raise ValueError(
                    "Q7 publication runtime contains unknown or missing fields"
                )
            if any(
                not isinstance(record[name], str) or not record[name]
                for name in ("version", "platform", "machine")
            ):
                raise ValueError("Q7 publication runtime metadata is malformed")
    else:
        outputs, _ = regenerate(root)
        if candidate != {
            Path(name).name: data.encode() for name, data in outputs.items()
        }:
            raise ValueError(
                "Q7 publication generated artifacts differ from current source"
            )
    previous = _publication_files(destination)
    if set(previous) != {
        "scaffold-canonical.json",
        "scaffold-runtime-parity.json",
        "probe.lean",
        "artifact_proof_manifest.json",
    }:
        raise ValueError("Q7 destination contains incomplete or unknown outputs")
    token = uuid.uuid4().hex
    staged = destination.with_name(f".generated-publish-{token}")
    backup = destination.with_name(f".generated-before-{token}")
    staged.mkdir()
    try:
        for name, data in (previous | candidate).items():
            with (staged / name).open("xb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
        if (
            before != {name: (root / name).read_bytes() for name in owned}
            or candidate != _publication_files(incoming / "generated")
            or previous != _publication_files(destination)
        ):
            raise ValueError("Q7 publication inputs changed before installation")
        for name in owned:
            _regular_path(root / name)
        _install_publication(staged, destination, backup)
    finally:
        if staged.exists():
            shutil.rmtree(staged)
    return backup


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--record-scaffold-portability", action="store_true")
    mode.add_argument("--publish-scaffold-from", type=Path)
    mode.add_argument("--publish-generated-from", type=Path)
    parser.add_argument(
        "--source-root",
        type=Path,
        default=ROOT,
        help="current source and parity input profile",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        help="fresh output slice; retained outputs are never overwritten",
    )
    args = parser.parse_args(argv)
    source_root = args.source_root.resolve()
    incoming = args.publish_scaffold_from or args.publish_generated_from
    if incoming is not None:
        if args.output_root is not None:
            parser.error("publication does not accept --output-root")
        _regular_path(args.source_root / EXTRACTOR)
        backup = publish(
            source_root,
            incoming.absolute(),
            scaffold=args.publish_scaffold_from is not None,
        )
        print(
            f"Published checked Q7 working projections; preimage: {backup}; no runtime/native execution."
        )
        return 0
    target = args.output_root.resolve() if args.output_root else source_root / PREFIX
    if not args.check:
        if args.output_root is None:
            parser.error("current-source generation requires a fresh --output-root")
        if target.exists():
            parser.error("--output-root already exists; choose a fresh directory")
    if args.record_scaffold_portability:
        canonical, evidence = scaffold_portability_evidence(source_root)
        target.mkdir(parents=True, exist_ok=False)
        (target / "generated").mkdir()
        (target / "generated/scaffold-canonical.json").write_bytes(canonical)
        (target / "generated/scaffold-runtime-parity.json").write_text(
            json.dumps(evidence, sort_keys=True, indent=2) + "\n"
        )
        print(
            f"Five real CPython runtimes returned identical candidate bytes: {evidence['canonical_sha256']}; no runner/native execution."
        )
        return 0
    outputs, _manifest = regenerate(source_root)
    if args.check:
        changed = [
            path
            for path, data in outputs.items()
            if not (target / path).is_file() or (target / path).read_text() != data
        ]
        if changed:
            raise ValueError(f"Q7 generated artifacts differ: {changed}")
        print(
            "Q7 generated artifacts current; native evidence must be checked separately."
        )
    else:
        target.mkdir(parents=True, exist_ok=False)
        for path, data in outputs.items():
            (target / path).parent.mkdir(parents=True, exist_ok=True)
            (target / path).write_text(data)
        print("Generated Q7 probe and manifest; no native compilation performed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
