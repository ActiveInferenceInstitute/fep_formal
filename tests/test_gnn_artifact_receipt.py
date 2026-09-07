"""Q5 retained-evidence tampering and synthetic native-process contracts.

All workspaces and transcripts here are synthetic. These tests never run Lean,
the GNN renderer, PyMDP, or a provider, and do not create native evidence.
"""

from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

from fep_lean.bridge import operations
from fep_lean.bridge.custody import fingerprint, write_json
from fep_lean.verification.gnn_artifact_receipt import ENGINE_PATH, ArtifactVerifier

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "specs/gnn-bridge-q5-artifact-proof/verify_native.py"


@pytest.fixture
def verifier() -> ArtifactVerifier:
    spec = importlib.util.spec_from_file_location("q5_native_receipt_tests", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.VERIFICATION


def _write(root: Path, name: str, text: str) -> None:
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


@pytest.fixture
def workspace(
    tmp_path: Path, verifier: ArtifactVerifier, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, Path]:
    root, gnn = tmp_path / "fep", tmp_path / "gnn"
    root.mkdir()
    gnn.mkdir()
    for checkout, key in ((root, "fep_lean"), (gnn, "gnn")):
        for name in operations.owner_roster(checkout, key):
            _write(checkout, name, "synthetic source\n")
    for name in (
        ENGINE_PATH,
        verifier.contract.adapter,
        verifier.contract.generator,
        verifier.contract.extractor,
        verifier.contract.renderer_tool,
    ):
        _write(root, name, (REPO / name).read_text(encoding="utf-8"))
    for name in verifier.contract.fixtures.values():
        _write(root, name, (REPO / name).read_text(encoding="utf-8"))
    for name in verifier.contract.targets:
        relative = name.removeprefix("FepSketches.").replace(".", "/")
        _write(root, f"src/fep_lean/formal/{relative}.lean", "-- synthetic owner\n")
        _write(root, f"lean/FepSketches/{relative}.lean", "-- synthetic owner\n")
        _write(
            root,
            f"lean/.lake/build/lib/lean/FepSketches/{relative}.olean",
            "synthetic cache",
        )
    _write(root, "lean/lean-toolchain", "leanprover/lean4:v4.33.1\n")
    _write(
        root,
        "lean/lake-manifest.json",
        json.dumps({"packages": [{"name": "mathlib", "rev": "a" * 40}]}),
    )
    _write(root, operations.DOCUMENTS["finite"], "synthetic current input\n")
    for name in ("lean", "lake"):
        _write(root, f"bin/{name}", "synthetic executable bytes")
    monkeypatch.setattr(
        verifier, "find_executable", lambda name, _: str(root / "bin" / name)
    )
    monkeypatch.setattr(verifier, "emit", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(verifier, "root", root)
    # Use the real generator in a synthetic root; only generated source text is written.
    module = ModuleType("q5_test_generator")
    module.__file__ = str(root / verifier.contract.generator)
    exec(  # noqa: S102 - trusted generator in an isolated synthetic workspace
        compile(
            (root / verifier.contract.generator).read_bytes(), module.__file__, "exec"
        ),
        module.__dict__,
    )
    texts, _ = module.regenerate()
    for name, text in texts.items():
        _write(root, f"{verifier.contract.slice}/{name}", text)
    pin = {"schema_version": 1}
    for checkout, key in ((root, "fep_lean"), (gnn, "gnn")):
        pin[key] = {
            "commit": "b" * 40,
            "owners": fingerprint(checkout, operations.owner_roster(checkout, key)),
        }
    write_json(root / operations.PIN, pin)
    owners = {key: pin[key]["owners"] for key in ("fep_lean", "gnn")}
    write_json(
        root / verifier.contract.provenance,
        {
            "schema_version": 1,
            "evidence_plane": "canonical GNN render (no runner execution)",
            "render_route": verifier.contract.render_route,
            "source_pin_sha256": verifier._digest((root / operations.PIN).read_bytes()),
            "input": {
                "path": operations.DOCUMENTS["finite"],
                "sha256": verifier._digest(
                    (root / operations.DOCUMENTS["finite"]).read_bytes()
                ),
            },
            "output": {
                "path": verifier.contract.fixtures["symmetric"],
                "sha256": verifier._digest(
                    (root / verifier.contract.fixtures["symmetric"]).read_bytes()
                ),
            },
            "owners_before": owners,
            "owners_after": owners,
            "command": [
                "uv",
                "run",
                "--offline",
                "--no-sync",
                "python",
                "-c",
                verifier._render_code(),
                str(root / operations.DOCUMENTS["finite"]),
                str(root / "q5_render_retained" / "rendered"),
            ],
            "returncode": 0,
            "stdout": "synthetic test only",
            "stderr": "",
        },
    )
    return root, gnn


def test_render_command_binds_checked_code_and_route(
    verifier: ArtifactVerifier, workspace: tuple[Path, Path]
) -> None:
    """The recorded argv is the reviewed literal code plus the exact route argv."""
    root, _gnn = workspace
    provenance = verifier.read_object(root / verifier.contract.provenance)
    assert provenance["command"] == [
        "uv",
        "run",
        "--offline",
        "--no-sync",
        "python",
        "-c",
        verifier._render_code(),
        str(root / operations.DOCUMENTS["finite"]),
        str(root / "q5_render_retained" / "rendered"),
    ]


@pytest.mark.parametrize(
    "slice_name",
    ["gnn-bridge-q6-activeinference-artifact", "gnn-bridge-q7-continuous-ou-proof"],
)
def test_backend_render_commands_accept_only_bound_frozen_inputs(
    slice_name: str,
) -> None:
    path = REPO / "specs" / slice_name / "verify_native.py"
    spec = importlib.util.spec_from_file_location("receipt_backend_contract_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    verifier = module.VERIFICATION
    contract = verifier.contract
    folder = REPO / ("q6-render-test" if contract.render_bindings else "q7-render-test")
    inputs = (
        [binding.input_path for binding in contract.render_bindings]
        if contract.render_bindings
        else [operations.DOCUMENTS[contract.input_variant]]
    )
    command = [
        "uv",
        "run",
        "--offline",
        "--no-sync",
        "python",
        "-c",
        verifier._render_code(),
        *(str(folder / Path(item).name) for item in inputs),
        str(folder / "rendered"),
    ]
    verifier._check_render_command(command)
    for index in range(7, len(command) - 1):
        changed = command.copy()
        changed[index] = str(folder / "unbound-input.json")
        with pytest.raises(ValueError, match="input"):
            verifier._check_render_command(changed)
    with pytest.raises(ValueError):
        verifier._check_render_command(command[:7])


def test_render_code_checks_the_exact_read_buffer(
    verifier: ArtifactVerifier,
    workspace: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, _ = workspace
    relative = verifier.contract.renderer_tool
    authority = fingerprint(root, [relative])
    original = Path.read_bytes

    def changed_read(path: Path) -> bytes:
        buffer = original(path)
        return buffer + b"\n# changed at read\n" if path == root / relative else buffer

    monkeypatch.setattr(Path, "read_bytes", changed_read)
    with pytest.raises(
        ValueError, match="renderer tool changed before render-code read"
    ):
        verifier._render_code(authority)


@pytest.mark.parametrize(
    "mutate",
    [
        "prefix",
        "code",
        "arity",
        "relative_input",
        "other_input",
        "temp_name",
        "true_command",
    ],
)
def test_rejects_forged_render_commands(
    mutate: str,
    verifier: ArtifactVerifier,
    workspace: tuple[Path, Path],
    receipt: dict[str, Any],
) -> None:
    """Self-attested commands cannot pass; argv binds to the checked code."""
    root, gnn = workspace
    provenance = verifier.read_object(root / verifier.contract.provenance)
    command = list(provenance["command"])
    if mutate == "prefix":
        command[0] = "true"
    elif mutate == "code":
        command[6] = command[6] + "\n# tampered\n"
    elif mutate == "arity":
        command.pop()
    elif mutate == "relative_input":
        command[7] = operations.DOCUMENTS["finite"]
    elif mutate == "other_input":
        command[7] = str(root / "input/other.md")
    elif mutate == "temp_name":
        command[8] = str(root / "unfrozen" / "rendered")
    else:
        command = ["true"]
    provenance["command"] = command
    write_json(root / verifier.contract.provenance, provenance)
    assert verifier.validate_receipt(gnn, receipt)


@pytest.mark.parametrize(
    "import_line",
    [
        "import fep_lean.verification.gnn_artifact_proof as checked_proof",
        "import fep_lean.verification.gnn_artifact_proof\nchecked_proof = fep_lean.verification.gnn_artifact_proof",
        "from fep_lean.verification import gnn_artifact_proof as checked_proof",
    ],
)
def test_direct_and_aliased_owned_imports_bind_checked_buffers(
    verifier: ArtifactVerifier, workspace: tuple[Path, Path], import_line: str
) -> None:
    """``import X.Y as m`` binds the digest-checked extractor, never cached state."""
    import sys

    root, gnn = workspace
    canonical = "fep_lean.verification.gnn_artifact_proof"
    poisoned = ModuleType(canonical)
    poisoned.POISON = True
    saved = sys.modules.get(canonical)
    sys.modules[canonical] = poisoned
    assert sys.modules.get(canonical) is poisoned
    try:
        generator = root / verifier.contract.generator
        source = generator.read_text(encoding="utf-8")
        mutated = source.replace(
            "from fep_lean.verification.gnn_artifact_proof import (",
            import_line + "\nfrom fep_lean.verification.gnn_artifact_proof import (",
            1,
        ).replace(
            "    texts: dict[str, str] = {}",
            '    assert not getattr(checked_proof, "POISON", False)\n'
            "    assert checked_proof.extract_pymdp_tables is extract_pymdp_tables\n"
            "    texts: dict[str, str] = {}",
            1,
        )
        assert mutated != source
        generator.write_text(mutated, encoding="utf-8")
        snapshot = verifier.source_snapshot(gnn)
        # The checked alias reproduces canonical behavior (the generator's own
        # assertions inside the buffer passed), and the canonical binding was
        # never replaced or executed.
        assert snapshot["artifacts"][verifier.contract.generator] == (
            verifier._digest(mutated.encode())
        )
        assert sys.modules.get(canonical) is poisoned
    finally:
        if saved is None:
            sys.modules.pop(canonical, None)
        else:
            sys.modules[canonical] = saved


def test_star_import_of_owned_module_stays_checked(
    verifier: ArtifactVerifier, workspace: tuple[Path, Path]
) -> None:
    """A star import of the owned extractor binds the checked buffer, not the cache."""
    import sys

    root, gnn = workspace
    canonical = "fep_lean.verification.gnn_artifact_proof"
    poisoned = ModuleType(canonical)
    poisoned.POISON = True
    saved = sys.modules.get(canonical)
    sys.modules[canonical] = poisoned
    try:
        generator = root / verifier.contract.generator
        source = generator.read_text(encoding="utf-8")
        anchor = "from fep_lean.verification.gnn_artifact_proof import ("
        head, sep, body = source.partition(anchor)
        assert sep
        _names, sep2, tail = body.partition(")\n")
        assert sep2
        mutated = (
            head
            + "from fep_lean.verification.gnn_artifact_proof import *\n"
            + "try:\n"
            + "    sha256_file  # star copy binds the checked buffer's public names\n"
            + "except NameError:\n"
            + "    raise AssertionError('star import did not bind the checked buffer')\n"
            + "\n"
            + tail
        )
        generator.write_text(mutated, encoding="utf-8")
        verifier.source_snapshot(gnn)
    finally:
        if saved is None:
            sys.modules.pop(canonical, None)
        else:
            sys.modules[canonical] = saved


def test_extractor_cache_poison_is_ignored(
    verifier: ArtifactVerifier, workspace: tuple[Path, Path]
) -> None:
    """A poisoned canonical sys.modules entry never feeds checked regeneration."""
    import sys

    _root, gnn = workspace
    canonical = "fep_lean.verification.gnn_artifact_proof"
    poisoned = ModuleType(canonical)
    poisoned.POISON = True
    saved = sys.modules.get(canonical)
    sys.modules[canonical] = poisoned
    try:
        snapshot = verifier.source_snapshot(gnn)
        assert snapshot["artifacts"]
    finally:
        if saved is None:
            sys.modules.pop(canonical, None)
        else:
            sys.modules[canonical] = saved


def test_generator_import_module_bypass_is_rejected(
    verifier: ArtifactVerifier, workspace: tuple[Path, Path]
) -> None:
    root, gnn = workspace
    generator = root / verifier.contract.generator
    source = generator.read_text(encoding="utf-8")
    generator.write_text(
        source.replace(
            "def regenerate()",
            "import importlib\n"
            "importlib.import_module('fep_lean.verification.gnn_artifact_proof')\n"
            "\n\ndef regenerate()",
            1,
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="importlib.import_module"):
        verifier.source_snapshot(gnn)


def test_extractor_relative_import_is_rejected(
    verifier: ArtifactVerifier, workspace: tuple[Path, Path]
) -> None:
    root, gnn = workspace
    extractor = root / verifier.contract.extractor
    relative = verifier.contract.extractor
    snapshot = verifier.source_snapshot(gnn)
    extractor.write_text(
        extractor.read_text() + "\nfrom . import nothing\n",
        encoding="utf-8",
    )
    buffer = (root / relative).read_bytes()
    with pytest.raises(ValueError, match="relative import"):
        verifier._regenerate(
            snapshot["artifacts"][verifier.contract.generator],
            {**snapshot["artifacts"], relative: verifier._digest(buffer)},
        )


def test_manual_importlib_util_loader_stays_allowed() -> None:
    """The gate blocks import_module, not the checked manual loader pattern."""
    from fep_lean.verification.gnn_artifact_receipt import _reject_unchecked_imports

    _reject_unchecked_imports(
        b"import importlib.util\n"
        b"spec = importlib.util.spec_from_file_location('m', 'p')\n",
        "owned extractor",
    )
    with pytest.raises(ValueError, match="importlib.import_module"):
        _reject_unchecked_imports(
            b"from importlib import import_module\nimport_module('x')\n",
            "generator",
        )
    with pytest.raises(ValueError, match="relative import"):
        _reject_unchecked_imports(b"from . import sibling\n", "generator")


def test_structured_rejection_for_called_process_error(
    verifier: ArtifactVerifier,
    workspace: tuple[Path, Path],
    receipt: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A broken checkout yields the machine-readable rejection, not a traceback."""

    def broken_sources(*_args: Any, **_kwargs: Any) -> list[str]:
        raise subprocess.CalledProcessError(128, "git rev-parse")

    monkeypatch.setattr(verifier, "check_sources", broken_sources)
    errors = verifier.validate_receipt(workspace[1], receipt)
    assert errors == ["Command 'git rev-parse' returned non-zero exit status 128."]


def test_structured_rejection_for_deeply_nested_receipt(
    verifier: ArtifactVerifier, workspace: tuple[Path, Path]
) -> None:
    _root, gnn = workspace
    deep: Any = {}
    node: dict[str, Any] = deep
    for _ in range(50_000):
        child: dict[str, Any] = {}
        node["k"] = child
        node = child
    errors = verifier.validate_receipt(gnn, {"source_before": {"artifacts": deep}})
    # Structured single-line rejection either way; 3.14's message names the
    # stack overflow in the receipt serializer rather than the JSON parser.
    assert errors and isinstance(errors[0], str) and errors[0]


def test_horizon_evidence_parsers_reject_deep_nesting() -> None:
    """F9: deeply nested hostile JSON/XML surface as structured rejections."""
    from fep_lean.verification import horizon_acceptance

    payload = ('{"k":' * 250_000) + "{}" + ("}" * 250_000)
    with pytest.raises(ValueError, match="nesting"):
        horizon_acceptance._json(payload.encode())
    with pytest.raises(ValueError):
        horizon_acceptance._junit_cases(b"<a>" * 250_000 + b"</a>" * 250_000)
    with pytest.raises(ValueError):
        horizon_acceptance._junit_cases(
            b"<suite>"
            + b"<a><b><c>" * 100_000
            + b"</c></b></a>" * 100_000
            + b"</suite>"
        )


def _output(verifier: ArtifactVerifier, variant: str) -> str:
    return (
        "\n".join(
            f"'{name}' depends on axioms: [propext, Classical.choice, Quot.sound]"
            for name in verifier.contract.theorems[variant]
        )
        + "\n"
    )


def _raw(stdout: str = "", command: list[str] | None = None) -> dict[str, Any]:
    return {
        "returncode": 0,
        "stdout": stdout,
        "stderr": "",
        "command": command or ["synthetic"],
    }


@pytest.fixture
def receipt(verifier: ArtifactVerifier, workspace: tuple[Path, Path]) -> dict[str, Any]:
    root, gnn = workspace
    lake, lean = str(root / "bin/lake"), str(root / "bin/lean")
    return verifier._receipt(
        verifier.source_snapshot(gnn),
        verifier.toolchain_snapshot(),
        verifier.compiled_imports(),
        _raw(
            "Lean (version 4.33.1, synthetic test)\n", [lake, "env", lean, "--version"]
        ),
        _raw(
            "Build completed successfully.", [lake, "build", *verifier.contract.targets]
        ),
        {
            key: _raw(
                _output(verifier, key),
                [
                    lake,
                    "env",
                    lean,
                    "-R",
                    str(root / "src/fep_lean/formal"),
                    str(root / f"probe_{key}.lean"),
                ],
            )
            for key in verifier.contract.probes
        },
    )


def test_retained_check_is_read_only(
    verifier: ArtifactVerifier,
    workspace: tuple[Path, Path],
    receipt: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, gnn = workspace
    target = root / "receipt.json"
    write_json(target, receipt)
    before = fingerprint(
        root, [p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()]
    )

    def forbidden(*_args: Any, **_kwargs: Any) -> None:
        pytest.fail("retained check invoked a subprocess or writer")

    monkeypatch.setattr(verifier, "run_process_group", forbidden)
    monkeypatch.setattr(verifier, "write_json", forbidden)
    assert verifier.main(["--gnn-root", str(gnn), "--receipt", str(target)]) == 0
    assert (
        verifier.main(["--check", "--gnn-root", str(gnn), "--receipt", str(target)])
        == 0
    )
    assert fingerprint(root, before) == before


@pytest.mark.parametrize(
    "field,value",
    [
        ("native_claim_ready", False),
        ("native_claim_ready", 1),
        ("runtime_execution_verified", True),
        ("schema_version", True),
        ("scope", "universal FEP"),
        ("probes", {}),
        ("source_after", {}),
        ("dependency_build", {}),
        ("compiler_version", {}),
        ("extra", "unapproved"),
    ],
)
def test_rejects_tampered_verdicts(
    verifier: ArtifactVerifier,
    workspace: tuple[Path, Path],
    receipt: dict[str, Any],
    field: str,
    value: Any,
) -> None:
    receipt[field] = value
    assert verifier.validate_receipt(workspace[1], receipt)


@pytest.mark.parametrize(
    "case",
    [
        "missing",
        "duplicate",
        "forbidden",
        "warning",
        "error",
        "sorry",
        "malformed",
        "nonzero",
        "hash",
        "axioms",
        "theorems",
        "source",
        "version",
        "build_warning",
    ],
)
def test_rejects_corrupt_native_evidence(
    verifier: ArtifactVerifier,
    workspace: tuple[Path, Path],
    receipt: dict[str, Any],
    case: str,
) -> None:
    probe = receipt["probes"]["symmetric"]
    if case == "missing":
        probe["stdout"] = ""
    elif case == "duplicate":
        probe["stdout"] += probe["stdout"]
    elif case == "forbidden":
        probe["stdout"] = probe["stdout"].replace("propext", "ExtraAxiom")
    elif case in {"warning", "error", "sorry"}:
        probe["stderr"] = case + ": synthetic rejected diagnostic"
    elif case == "malformed":
        probe["stdout"] = "'unclosed' depends on axioms: ["
    elif case == "nonzero":
        probe["returncode"] = 1
    elif case == "version":
        receipt["compiler_version"]["stdout"] = "Lean (version 4.32.0, synthetic)"
    elif case == "build_warning":
        receipt["dependency_build"]["stdout"] = "warning: dependency stale"
    else:
        key = {
            "hash": "stdout_sha256",
            "axioms": "axioms",
            "theorems": "theorems",
            "source": "audit_source_sha256",
        }[case]
        probe[key] = "corrupt"
    assert verifier.validate_receipt(workspace[1], receipt)


@pytest.mark.parametrize(
    "artifact",
    [
        "extractor",
        "generator",
        "verifier",
        "manifest",
        "symmetric",
        "asymmetric",
        "probe",
        "input",
        "pin",
        "provenance",
        "toolchain",
        "lake_manifest",
        "binary",
        "owner",
        "projection",
        "olean",
        "gnn_owner",
    ],
)
def test_rejects_changed_current_bytes(
    verifier: ArtifactVerifier,
    workspace: tuple[Path, Path],
    receipt: dict[str, Any],
    artifact: str,
) -> None:
    root, gnn = workspace
    paths = {
        "extractor": verifier.contract.extractor,
        "generator": verifier.contract.generator,
        "verifier": verifier.contract.adapter,
        "manifest": verifier.contract.manifest,
        "symmetric": verifier.contract.fixtures["symmetric"],
        "asymmetric": verifier.contract.fixtures["asymmetric"],
        "probe": verifier.contract.probes["symmetric"],
        "input": operations.DOCUMENTS["finite"],
        "pin": operations.PIN,
        "provenance": verifier.contract.provenance,
        "toolchain": "lean/lean-toolchain",
        "lake_manifest": "lean/lake-manifest.json",
        "binary": "bin/lean",
        "owner": "src/fep_lean/formal/gnn_denotation.lean",
        "projection": "lean/FepSketches/gnn_denotation.lean",
        "olean": "lean/.lake/build/lib/lean/FepSketches/gnn_denotation.olean",
    }
    path = (
        gnn / "src/gnn/main.py" if artifact == "gnn_owner" else root / paths[artifact]
    )
    path.write_bytes(path.read_bytes() + b"\n")
    assert verifier.validate_receipt(gnn, receipt)


@pytest.mark.parametrize(
    "field", ["render_route", "owners_after", "returncode", "input", "output"]
)
def test_rejects_forged_or_historical_render_provenance(
    verifier: ArtifactVerifier,
    workspace: tuple[Path, Path],
    receipt: dict[str, Any],
    field: str,
) -> None:
    root, gnn = workspace
    path = root / verifier.contract.provenance
    provenance = verifier.read_object(path)
    provenance[field] = "historical comparison is not current render evidence"
    write_json(path, provenance)
    assert verifier.validate_receipt(gnn, receipt)


def test_compile_uses_exact_probes_and_process_group_helper(
    verifier: ArtifactVerifier,
    workspace: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, gnn = workspace
    seen: list[list[str]] = []

    def run(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        seen.append(command)
        assert kwargs["cwd"] == root / "lean"
        assert kwargs["timeout"] > 0
        if command[-1] == "--version":
            output = "Lean (version 4.33.1, synthetic test)"
        elif command[1] == "build":
            assert command[2:] == list(verifier.contract.targets)
            output = "Build completed successfully."
        else:
            path = Path(command[-1])
            variant = "asymmetric" if "asymmetric" in path.name else "symmetric"
            assert path.read_text() == verifier.audit_source(variant)
            assert str(root / "src/fep_lean/formal") in command
            output = _output(verifier, variant)
        return subprocess.CompletedProcess(command, 0, output, "")

    monkeypatch.setattr(verifier, "run_process_group", run)
    monkeypatch.setattr(verifier, "subprocess_env", lambda _: {})
    result = verifier.compile_receipt(gnn, timeout=5)
    assert len(seen) == 4
    assert verifier.validate_receipt(gnn, result) == []
    assert not Path(seen[-1][-1]).exists()


def test_compile_rejects_mid_run_source_mutation(
    verifier: ArtifactVerifier,
    workspace: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, gnn = workspace

    def run(command: list[str], *_args: Any) -> dict[str, Any]:
        if command[-1] == "--version":
            return _raw("Lean (version 4.33.1, synthetic test)", command)
        if command[1] == "build":
            return _raw(command=command)
        variant = "asymmetric" if "asymmetric" in command[-1] else "symmetric"
        if variant == "asymmetric":
            path = root / verifier.contract.adapter
            path.write_bytes(path.read_bytes() + b"\n")
        return _raw(_output(verifier, variant), command)

    monkeypatch.setattr(verifier, "_run", run)
    with pytest.raises(ValueError, match="sources changed during compilation"):
        verifier.compile_receipt(gnn)


def test_compile_rejects_changed_probe_before_executing_it(
    verifier: ArtifactVerifier,
    workspace: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, gnn = workspace
    probe = root / verifier.contract.probes["symmetric"]
    original = probe.read_bytes()
    commands: list[list[str]] = []

    def run(command: list[str], *_args: Any) -> dict[str, Any]:
        commands.append(command)
        if command[-1] == "--version":
            return _raw("Lean (version 4.33.1, synthetic test)", command)
        if command[1] == "build":
            probe.write_bytes(original + b'\n#eval IO.println "unbound code"\n')
            return _raw(command=command)
        pytest.fail("changed probe reached the native process")

    monkeypatch.setattr(verifier, "_run", run)
    try:
        with pytest.raises(ValueError, match="probe source changed before compilation"):
            verifier.compile_receipt(gnn)
        assert len(commands) == 2
    finally:
        probe.write_bytes(original)


def test_json_duplicates_and_missing_receipts_reject(
    verifier: ArtifactVerifier,
    workspace: tuple[Path, Path],
    tmp_path: Path,
) -> None:
    path = tmp_path / "bad.json"
    path.write_text('{"schema_version":1,"schema_version":1}')
    with pytest.raises(ValueError, match="duplicate"):
        verifier.read_object(path)
    assert (
        verifier.main(
            ["--gnn-root", str(workspace[1]), "--receipt", str(tmp_path / "absent")]
        )
        == 1
    )


def test_numerical_receipt_cannot_be_promoted(
    verifier: ArtifactVerifier,
    workspace: tuple[Path, Path],
    receipt: dict[str, Any],
) -> None:
    historical = {
        "all_certificates_pass": True,
        "native_claim_ready": True,
        "source_before": copy.deepcopy(receipt["source_before"]),
    }
    assert verifier.validate_receipt(workspace[1], historical)


def test_changed_generator_is_rejected_before_loading(
    verifier: ArtifactVerifier,
    workspace: tuple[Path, Path],
    receipt: dict[str, Any],
) -> None:
    root, gnn = workspace
    path = root / verifier.contract.generator
    sentinel = root / "unexpected-generator-side-effect"
    path.write_text(path.read_text() + f"\nPath({str(sentinel)!r}).write_text('bad')\n")
    assert verifier.validate_receipt(gnn, receipt)
    assert not sentinel.exists()


def test_generator_swap_after_retained_fingerprint_never_executes(
    verifier: ArtifactVerifier,
    workspace: tuple[Path, Path],
    receipt: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, gnn = workspace
    path = root / verifier.contract.generator
    sentinel = root / "generator-race-side-effect"
    snapshot = verifier.source_snapshot

    def swap_then_snapshot(*args: Any, **kwargs: Any) -> dict[str, Any]:
        # The retained fingerprint has already passed. A fresh snapshot would
        # now see attacker bytes; it must still use the retained generator hash.
        path.write_text(
            path.read_text() + f"\nPath({str(sentinel)!r}).write_text('bad')\n"
        )
        return snapshot(*args, **kwargs)

    monkeypatch.setattr(verifier, "source_snapshot", swap_then_snapshot)
    errors = verifier.validate_receipt(gnn, receipt)
    assert errors and "generator source changed before execution" in errors[0]
    assert not sentinel.exists()


@pytest.mark.parametrize("regeneration", [1, 2])
def test_generator_swap_immediately_before_each_retained_exec_is_rejected(
    verifier: ArtifactVerifier,
    workspace: tuple[Path, Path],
    receipt: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
    regeneration: int,
) -> None:
    root, gnn = workspace
    path = root / verifier.contract.generator
    sentinel = root / "generator-exec-race-side-effect"
    regenerate = verifier._regenerate
    calls = 0

    def swap_then_regenerate(*args: Any, **kwargs: Any) -> dict[str, str]:
        nonlocal calls
        calls += 1
        if calls == regeneration:
            path.write_text(
                path.read_text() + f"\nPath({str(sentinel)!r}).write_text('bad')\n"
            )
        return regenerate(*args, **kwargs)

    monkeypatch.setattr(verifier, "_regenerate", swap_then_regenerate)
    errors = verifier.validate_receipt(gnn, receipt)
    assert errors and "generator source changed before execution" in errors[0]
    assert calls == regeneration
    assert not sentinel.exists()


def test_generator_exec_uses_the_hashed_buffer_without_rereading(
    verifier: ArtifactVerifier,
    workspace: tuple[Path, Path],
    receipt: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, gnn = workspace
    path = root / verifier.contract.generator
    original = path.read_bytes()
    sentinel = root / "generator-reread-side-effect"
    digest = verifier._digest
    swapped = False

    def swap_after_digest(value: bytes) -> str:
        nonlocal swapped
        result = digest(value)
        if value == original and not swapped:
            swapped = True
            path.write_bytes(
                original + f"\nPath({str(sentinel)!r}).write_text('bad')\n".encode()
            )
        return result

    monkeypatch.setattr(verifier, "_digest", swap_after_digest)
    assert verifier.validate_receipt(gnn, receipt)
    assert swapped
    assert not sentinel.exists()


def test_compile_final_snapshot_retains_original_generator_digest(
    verifier: ArtifactVerifier,
    workspace: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, gnn = workspace
    path = root / verifier.contract.generator
    sentinel = root / "compile-generator-race-side-effect"

    def run(command: list[str], *_args: Any) -> dict[str, Any]:
        if command[-1] == "--version":
            return _raw("Lean (version 4.33.1, synthetic test)", command)
        if command[1] == "build":
            return _raw(command=command)
        variant = "asymmetric" if "asymmetric" in command[-1] else "symmetric"
        if variant == "asymmetric":
            path.write_text(
                path.read_text() + f"\nPath({str(sentinel)!r}).write_text('bad')\n"
            )
        return _raw(_output(verifier, variant), command)

    monkeypatch.setattr(verifier, "_run", run)
    with pytest.raises(ValueError, match="generator source changed before execution"):
        verifier.compile_receipt(gnn)
    assert not sentinel.exists()


def test_compile_initial_snapshot_checks_buffer_before_any_native_launch(
    verifier: ArtifactVerifier,
    workspace: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, gnn = workspace
    path = root / verifier.contract.generator
    sentinel = root / "compile-initial-generator-race-side-effect"
    regenerate = verifier._regenerate

    def swap_then_regenerate(*args: Any, **kwargs: Any) -> dict[str, str]:
        path.write_text(
            path.read_text() + f"\nPath({str(sentinel)!r}).write_text('bad')\n"
        )
        return regenerate(*args, **kwargs)

    def forbidden(*_args: Any, **_kwargs: Any) -> None:
        pytest.fail("generator race launched native work")

    monkeypatch.setattr(verifier, "_regenerate", swap_then_regenerate)
    monkeypatch.setattr(verifier, "_run", forbidden)
    with pytest.raises(ValueError, match="generator source changed before execution"):
        verifier.compile_receipt(gnn)
    assert not sentinel.exists()


@pytest.mark.parametrize("target", ["source", "fixture", "cache", "binary", "gnn"])
def test_output_collisions_fail_before_native_launch(
    verifier: ArtifactVerifier,
    workspace: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
    target: str,
) -> None:
    root, gnn = workspace
    paths = {
        "source": root / verifier.contract.adapter,
        "fixture": root / verifier.contract.fixtures["symmetric"],
        "cache": root / "lean/.lake/build/lib/lean/FepSketches/gnn_denotation.olean",
        "binary": root / "bin/lean",
        "gnn": gnn / "src/gnn/main.py",
    }

    def forbidden(*_args: Any, **_kwargs: Any) -> None:
        pytest.fail("invalid output path launched native work")

    monkeypatch.setattr(verifier, "compile_receipt", forbidden)
    before = paths[target].read_bytes()
    assert (
        verifier.main(
            [
                "--compile",
                "--gnn-root",
                str(gnn),
                "--receipt",
                str(paths[target]),
            ]
        )
        == 1
    )
    assert paths[target].read_bytes() == before


def test_failed_native_compile_never_writes_success_receipt(
    verifier: ArtifactVerifier,
    workspace: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, gnn = workspace
    target = root / "new-receipt.json"
    monkeypatch.setattr(
        verifier,
        "_run",
        lambda *_args: {
            "returncode": 1,
            "stdout": "",
            "stderr": "synthetic compiler failure",
        },
    )
    assert (
        verifier.main(
            [
                "--compile",
                "--gnn-root",
                str(gnn),
                "--receipt",
                str(target),
            ]
        )
        == 1
    )
    assert not target.exists()


def test_missing_and_symlinked_owners_fail_closed(
    verifier: ArtifactVerifier,
    workspace: tuple[Path, Path],
    receipt: dict[str, Any],
) -> None:
    root, gnn = workspace
    path = root / verifier.contract.probes["symmetric"]
    original = path.read_bytes()
    path.unlink()
    assert verifier.validate_receipt(gnn, receipt)
    other = root / "aliased-probe.lean"
    other.write_bytes(original)
    path.symlink_to(other)
    assert verifier.validate_receipt(gnn, receipt)


@pytest.mark.parametrize("timeout", [0, -1, float("inf"), float("nan")])
def test_rejects_invalid_timeout(
    verifier: ArtifactVerifier, workspace: tuple[Path, Path], timeout: float
) -> None:
    with pytest.raises(ValueError, match="timeout"):
        verifier.compile_receipt(workspace[1], timeout=timeout)


def test_contract_defensively_copies_inputs(verifier: ArtifactVerifier) -> None:
    from dataclasses import replace

    fixtures = dict(verifier.contract.fixtures)
    changed = replace(verifier.contract, fixtures=fixtures)
    fixtures["symmetric"] = "different.py"
    assert changed.fixtures["symmetric"] == verifier.contract.fixtures["symmetric"]
    with pytest.raises(TypeError):
        changed.fixtures["symmetric"] = "different.py"  # type: ignore[index]
    projection = changed.record()
    projection["fixtures"]["symmetric"] = "different.py"
    assert changed.record() == verifier.contract.record()


@pytest.mark.parametrize(
    "field,value",
    [
        ("generator", "../escape.py"),
        ("extractor", "/absolute.py"),
        ("canonical_variant", "missing"),
        ("targets", ()),
        ("probes", {}),
        ("theorems", {"symmetric": (), "asymmetric": ()}),
    ],
)
def test_invalid_contract_rejects(
    verifier: ArtifactVerifier, field: str, value: Any
) -> None:
    from dataclasses import replace

    with pytest.raises(ValueError):
        replace(verifier.contract, **{field: value})


@pytest.mark.parametrize("section", ["compiler_version", "dependency_build", "probe"])
def test_wrong_native_command_rejects(
    verifier: ArtifactVerifier,
    workspace: tuple[Path, Path],
    receipt: dict[str, Any],
    section: str,
) -> None:
    target = receipt["probes"]["symmetric"] if section == "probe" else receipt[section]
    target["command"][0] = "/wrong/lake"
    assert verifier.validate_receipt(workspace[1], receipt)


def test_engine_source_change_rejects(
    verifier: ArtifactVerifier, workspace: tuple[Path, Path], receipt: dict[str, Any]
) -> None:
    source = workspace[0] / ENGINE_PATH
    source.write_text(source.read_text() + "\n# changed engine\n")
    assert verifier.validate_receipt(workspace[1], receipt)


@pytest.mark.parametrize("stage", ["snapshot", "regenerate"])
def test_extractor_swap_never_executes(
    verifier: ArtifactVerifier,
    workspace: tuple[Path, Path],
    receipt: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
    stage: str,
) -> None:
    root, gnn = workspace
    source = root / verifier.contract.extractor
    sentinel = root / "extractor-side-effect"
    name = "source_snapshot" if stage == "snapshot" else "_regenerate"
    original = getattr(verifier, name)

    def changed(*args: Any, **kwargs: Any) -> Any:
        source.write_text(
            source.read_text() + f"\nPath({str(sentinel)!r}).write_text('bad')\n"
        )
        return original(*args, **kwargs)

    monkeypatch.setattr(verifier, name, changed)
    assert verifier.validate_receipt(gnn, receipt)
    assert not sentinel.exists()


def test_extractor_uses_hashed_buffer(
    verifier: ArtifactVerifier,
    workspace: tuple[Path, Path],
    receipt: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, gnn = workspace
    source = root / verifier.contract.extractor
    original = source.read_bytes()
    sentinel = root / "extractor-buffer-side-effect"
    digest = verifier._digest
    swapped = False

    def changed(buffer: bytes) -> str:
        nonlocal swapped
        result = digest(buffer)
        if buffer == original and not swapped:
            swapped = True
            source.write_bytes(
                original + f"\nPath({str(sentinel)!r}).write_text('bad')\n".encode()
            )
        return result

    monkeypatch.setattr(verifier, "_digest", changed)
    assert verifier.validate_receipt(gnn, receipt)
    assert swapped and not sentinel.exists()


def test_retained_imports_do_not_reuse_or_replace_cached_extractor(
    verifier: ArtifactVerifier,
    workspace: tuple[Path, Path],
    receipt: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import sys

    from fep_lean.verification import gnn_artifact_proof

    cached = sys.modules[gnn_artifact_proof.__name__]

    def forbidden(*args: Any, **kwargs: Any) -> Any:
        pytest.fail("cached extractor used")

    monkeypatch.setattr(gnn_artifact_proof, "extract_pymdp_tables", forbidden)
    assert verifier.validate_receipt(workspace[1], receipt) == []
    assert sys.modules[gnn_artifact_proof.__name__] is cached
    assert not [name for name in sys.modules if name.startswith("_fep_checked_")]
