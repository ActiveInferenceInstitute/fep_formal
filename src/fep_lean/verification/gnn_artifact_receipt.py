"""Contract-driven native static-artifact evidence. Retained checks are read-only."""

from __future__ import annotations

import argparse
import ast
import builtins
import hashlib
import json
import math
import re
import subprocess
import sys
import tempfile
import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from types import MappingProxyType, ModuleType
from typing import Any

from fep_lean.bridge.custody import contained_file, fingerprint, write_json
from fep_lean.bridge.operations import DOCUMENTS, PIN, check_sources, emit
from fep_lean.verification._jsonutil import load_strict_json
from fep_lean.verification._subprocess import run_process_group
from fep_lean.verification._toolchain import (
    find_executable,
    lean_version_matches_pin,
    read_toolchain_pin,
    resolved_mathlib_revision,
    subprocess_env,
)
from fep_lean.verification.formalism_audit import _parse_axiom_output

ENGINE_PATH = "src/fep_lean/verification/gnn_artifact_receipt.py"
ALLOWED_AXIOMS = frozenset({"propext", "Classical.choice", "Quot.sound"})
_DIAGNOSTIC = re.compile(r"\b(?:warning|error|sorryAx|sorry)\b", re.IGNORECASE)
_IMPORT = re.compile(r"^import (FepSketches\.[A-Za-z0-9_.]+)\s*$", re.MULTILINE)


def _checked_chain(name: str, load: Callable[[str], ModuleType]) -> ModuleType:
    """Ancestor proxies so ``import a.b.c``/``import a.b.c as m`` stay checked.

    ``import a.b.c`` and ``import a.b.c as m`` compile to ``IMPORT_NAME`` with
    a falsy ``fromlist`` followed by ``IMPORT_FROM`` attribute walks on the
    returned object. Wrapping the checked leaf in private parent proxies keeps
    that walk inside the checked set; neither the wrappers nor the leaf are
    registered in ``sys.modules`` under canonical names.
    """
    parts = name.split(".")
    proxy = load(name)
    for depth in range(len(parts) - 1, 0, -1):
        wrapper = ModuleType("_fep_checked_" + uuid.uuid4().hex)
        wrapper.__dict__[parts[depth]] = proxy
        proxy = wrapper
    return proxy


def _reject_unchecked_imports(source: bytes, label: str) -> None:
    """Reject the two import vectors that bypass ``checked_import``.

    Trusted local generator execution is not a general sandbox: the gate only
    blocks ``importlib.import_module`` and relative imports, leaving the
    deliberately checked manual ``importlib.util`` loaders intact.
    """
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.level:
            raise ValueError(
                f"{label} uses a relative import; it bypasses checked imports"
            )
        if (
            isinstance(node, ast.ImportFrom)
            and node.module == "importlib"
            and any(alias.name == "import_module" for alias in node.names)
        ):
            raise ValueError(
                f"{label} imports importlib.import_module; it bypasses checked imports"
            )
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, (ast.Name, ast.Attribute))
            and getattr(node.func, "attr", getattr(node.func, "id", ""))
            == "import_module"
        ):
            raise ValueError(
                f"{label} calls importlib.import_module; it bypasses checked imports"
            )


def _relative(value: str) -> str:
    path = PurePosixPath(value)
    if not value or path.is_absolute() or ".." in path.parts or str(path) != value:
        raise ValueError(f"noncanonical relative artifact path: {value!r}")
    return value


@dataclass(frozen=True, slots=True)
class RenderBinding:
    """One explicitly rendered variant in the multi-render provenance schema."""

    variant: str
    input_path: str
    input_kind: str
    route: tuple[str, ...]

    def __post_init__(self) -> None:
        _relative(self.input_path)
        object.__setattr__(self, "route", tuple(self.route))
        if not self.variant or not self.input_kind or not self.route:
            raise ValueError("render binding must name variant, kind, and route")


@dataclass(frozen=True, slots=True)
class ArtifactContract:
    """Fixed backend identity; mutable caller mappings are defensively copied."""

    slice: str
    input_variant: str
    fixtures: Mapping[str, str]
    probes: Mapping[str, str]
    theorems: Mapping[str, tuple[str, ...]]
    targets: tuple[str, ...]
    scope: str
    render_route: tuple[str, ...]
    extractor: str
    adapter: str
    generator: str = ""
    renderer_tool: str = ""
    manifest: str = ""
    provenance: str = ""
    extra_files: tuple[str, ...] = ()
    canonical_variant: str = "symmetric"
    render_bindings: tuple[RenderBinding, ...] = ()

    def __post_init__(self) -> None:
        for key, name in (
            ("generator", "generate_probe.py"),
            ("renderer_tool", "refresh_render.py"),
            ("manifest", "generated/artifact_proof_manifest.json"),
            ("provenance", "render_provenance.json"),
        ):
            if not getattr(self, key):
                object.__setattr__(self, key, f"{self.slice}/{name}")
        for key in ("fixtures", "probes"):
            object.__setattr__(self, key, MappingProxyType(dict(getattr(self, key))))
        object.__setattr__(
            self,
            "theorems",
            MappingProxyType({k: tuple(v) for k, v in self.theorems.items()}),
        )
        for key in ("targets", "render_route", "extra_files", "render_bindings"):
            object.__setattr__(self, key, tuple(getattr(self, key)))
        variants = set(self.fixtures)
        if (
            not variants
            or variants != set(self.probes)
            or variants != set(self.theorems)
        ):
            raise ValueError(
                "fixture/probe/theorem variants must be equal and nonempty"
            )
        if (
            self.canonical_variant not in variants
            or self.input_variant not in DOCUMENTS
        ):
            raise ValueError("unknown canonical/input variant")
        if not self.scope or not self.targets or not self.render_route:
            raise ValueError("scope, native targets, and render route must be explicit")
        if any(not re.fullmatch(r"[a-z][a-z0-9_]*", v) for v in variants):
            raise ValueError("invalid artifact variant")
        names = [name for roster in self.theorems.values() for name in roster]
        if any(not roster for roster in self.theorems.values()) or len(
            set(names)
        ) != len(names):
            raise ValueError("native theorem roster must be nonempty and unique")
        if any(
            not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.]*", n)
            for n in (*self.targets, *names)
        ):
            raise ValueError("invalid native declaration/target name")
        paths = [
            self.slice,
            self.extractor,
            self.adapter,
            self.generator,
            self.renderer_tool,
            self.manifest,
            self.provenance,
            *self.fixtures.values(),
            *self.probes.values(),
            *self.extra_files,
        ]
        for value in paths:
            _relative(value)
        outputs = [self.manifest, *self.probes.values()]
        if len(set(outputs)) != len(outputs) or any(
            not p.startswith(self.slice + "/") for p in outputs
        ):
            raise ValueError("generated outputs must be unique and inside the slice")
        if set(outputs) & {
            self.extractor,
            self.adapter,
            self.generator,
            self.renderer_tool,
            *self.fixtures.values(),
            *self.extra_files,
        }:
            raise ValueError("generated outputs collide with source inputs")
        bindings = [b.variant for b in self.render_bindings]
        if bindings and (set(bindings) != variants or len(bindings) != len(variants)):
            raise ValueError("render bindings must cover every variant exactly once")

    def record(self) -> dict[str, Any]:
        """JSON-compatible immutable-contract projection, fresh on every call."""
        return {
            "slice": self.slice,
            "input_variant": self.input_variant,
            "fixtures": dict(self.fixtures),
            "probes": dict(self.probes),
            "theorems": {k: list(v) for k, v in self.theorems.items()},
            "targets": list(self.targets),
            "scope": self.scope,
            "render_route": list(self.render_route),
            "extractor": self.extractor,
            "adapter": self.adapter,
            "generator": self.generator,
            "renderer_tool": self.renderer_tool,
            "manifest": self.manifest,
            "provenance": self.provenance,
            "extra_files": list(self.extra_files),
            "canonical_variant": self.canonical_variant,
            "render_bindings": [
                {
                    "variant": b.variant,
                    "input_path": b.input_path,
                    "input_kind": b.input_kind,
                    "route": list(b.route),
                }
                for b in self.render_bindings
            ],
        }


class ArtifactVerifier:
    """One immutable artifact contract and one explicitly selected checkout."""

    def __init__(self, root: Path, contract: ArtifactContract) -> None:
        self.root = root.resolve()
        self.contract = contract

    check_sources = staticmethod(check_sources)
    emit = staticmethod(emit)
    find_executable = staticmethod(find_executable)
    run_process_group = staticmethod(run_process_group)
    subprocess_env = staticmethod(subprocess_env)
    write_json = staticmethod(write_json)

    def _digest(self, value: bytes) -> str:
        return hashlib.sha256(value).hexdigest()

    def _canonical(self, value: Any) -> str:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)

    def _equal(self, actual: Any, expected: Any, label: str) -> None:
        if self._canonical(actual) != self._canonical(expected):
            raise ValueError(f"{label} mismatch")


    def read_object(self, path: Path) -> dict[str, Any]:
        """Reject duplicate keys and non-standard numeric values in receipts."""
        result = load_strict_json(path.read_text(encoding="utf-8"))
        if not isinstance(result, dict):
            raise TypeError("JSON root must be an object")
        self._canonical(result)
        return result

    def _render_code(self, authority: Mapping[str, str] | None = None) -> str:
        """The exact ``-c`` program literal the checked renderer tool executes.

        The render command never names the renderer tool on its command line;
        the tool defines the reviewed ``RENDER_CODE`` (Q5) or ``CODE`` (Q6/Q7)
        module-level string literal that is passed to ``python -c``. When
        artifact-digest authority is supplied, the exact buffer is
        digest-checked before parsing, so a temporary renderer-tool
        replacement cannot influence command checking and be restored.
        """
        renderer_bytes = contained_file(
            self.root, self.contract.renderer_tool
        ).read_bytes()
        if (
            authority is not None
            and self._digest(renderer_bytes) != authority[self.contract.renderer_tool]
        ):
            raise ValueError("renderer tool changed before render-code read")
        tree = ast.parse(renderer_bytes.decode(encoding="utf-8"))
        literals = [
            node.value.value
            for node in tree.body
            if isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id in ("RENDER_CODE", "CODE")
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        ]
        if len(literals) != 1 or not literals[0]:
            raise ValueError(
                "renderer tool must define exactly one nonempty RENDER_CODE or CODE literal"
            )
        return literals[0]

    def _check_render_command(
        self, command: list[str], authority: Mapping[str, str] | None = None
    ) -> None:
        """Bind the recorded render argv to the checked renderer code and route.

        Actual commands run ``[uv, run, --offline, --no-sync, python, -c,
        <checked code>, <absolute inputs...>, <absolute frozen output>]``,
        not the renderer tool itself. Inputs are the fixed official input
        document or correctly named frozen temporary copies; the output is
        the frozen temporary ``rendered`` directory of the render run.
        """
        prefix = [
            "uv",
            "run",
            "--offline",
            "--no-sync",
            "python",
            "-c",
            self._render_code(authority),
        ]
        if command[: len(prefix)] != prefix:
            raise ValueError(
                "render provenance command does not execute the checked render code"
            )
        *inputs, output = command[len(prefix) :]
        if not inputs or any(
            not path or not Path(path).is_absolute() for path in inputs
        ):
            raise ValueError("render inputs must be absolute paths")
        output_path = Path(output)
        if (
            not output
            or not output_path.is_absolute()
            or output_path.name != "rendered"
        ):
            raise ValueError(
                "render output must be the absolute frozen temporary render directory"
            )
        if not re.fullmatch(r"q\d[^/]*render[^/]*", output_path.parent.name):
            raise ValueError(
                "render output parent is not a frozen render temporary directory"
            )
        if self.contract.render_bindings:
            bindings = self.contract.render_bindings
            if len(inputs) != len(bindings):
                raise ValueError(
                    "render command input count does not match the render bindings"
                )
            for binding, recorded_input in zip(bindings, inputs, strict=True):
                official = str(self.root / binding.input_path)
                frozen = (
                    Path(recorded_input).name == PurePosixPath(binding.input_path).name
                    and Path(recorded_input).parent == output_path.parent
                )
                if recorded_input != official and not frozen:
                    raise ValueError(
                        "render input neither reads the official file nor a "
                        f"correctly named frozen copy for {binding.variant}"
                    )
        else:
            official = str(self.root / DOCUMENTS[self.contract.input_variant])
            frozen_input = str(output_path.parent / Path(official).name)
            if inputs not in ([official], [frozen_input]):
                raise ValueError("render command must read the fixed official input")

    def _check_render(self, pin: dict[str, Any], authority: Mapping[str, str]) -> None:
        recorded = self.read_object(contained_file(self.root, self.contract.provenance))
        command = recorded.get("command")
        if (
            not isinstance(command, list)
            or not command
            or any(not isinstance(a, str) or not a for a in command)
        ):
            raise ValueError("render provenance lacks the actual command")
        if not all(isinstance(recorded.get(k), str) for k in ("stdout", "stderr")):
            raise ValueError("render provenance lacks captured output")
        # stdout/stderr are preserved as captured transcripts, never regenerated;
        # the argv itself is bound to the checked renderer code below, using the
        # recorded artifact digests as authority when this runs in _regenerate.
        self._check_render_command(command, authority)
        owners = {key: pin[key]["owners"] for key in ("fep_lean", "gnn")}

        def file_record(path: str) -> dict[str, str]:
            return {"path": path, "sha256": fingerprint(self.root, [path])[path]}

        expected = {
            "schema_version": 1,
            "evidence_plane": "canonical GNN render (no runner execution)",
            "source_pin_sha256": self._digest(
                contained_file(self.root, PIN).read_bytes()
            ),
            "owners_before": owners,
            "owners_after": owners,
            "command": command,
            "returncode": 0,
            "stdout": recorded["stdout"],
            "stderr": recorded["stderr"],
        }
        if self.contract.render_bindings:
            expected["renders"] = {
                b.variant: {
                    "input": {**file_record(b.input_path), "kind": b.input_kind},
                    "output": file_record(self.contract.fixtures[b.variant]),
                    "render_route": list(b.route),
                }
                for b in self.contract.render_bindings
            }
        else:
            expected.update(
                {
                    "render_route": list(self.contract.render_route),
                    "input": file_record(DOCUMENTS[self.contract.input_variant]),
                    "output": file_record(
                        self.contract.fixtures[self.contract.canonical_variant]
                    ),
                }
            )
        self._equal(recorded, expected, "current canonical render provenance")

    def _regenerate(
        self,
        expected_generator_sha256: str,
        expected_artifact_digests: Mapping[str, str],
    ) -> dict[str, str]:
        # Hash and execute the same buffer. Never derive fresh authorization after a race.
        path = contained_file(self.root, self.contract.generator)
        source_bytes = path.read_bytes()
        if self._digest(source_bytes) != expected_generator_sha256:
            raise ValueError("generator source changed before execution")
        _reject_unchecked_imports(source_bytes, "generator")
        module = ModuleType("retained_artifact_generator")
        module.__file__ = str(path)
        module.__dict__["_VERIFIED_ARTIFACT_DIGESTS"] = MappingProxyType(
            dict(expected_artifact_digests)
        )
        # Imports of owned extractors use the same retained authority as the
        # generator. Private module aliases avoid replacing application modules
        # or selecting a backend through process-global state.
        owned = {
            relative.removeprefix("src/")
            .removesuffix(".py")
            .replace("/", "."): relative
            for relative in (self.contract.extractor, *self.contract.extra_files)
            if relative.startswith("src/") and relative.endswith(".py")
        }
        loaded: dict[str, ModuleType] = {}
        aliases: list[str] = []

        def load_owned(name: str) -> ModuleType:
            if name in loaded:
                return loaded[name]
            relative = owned[name]
            source_path = contained_file(self.root, relative)
            buffer = source_path.read_bytes()
            if self._digest(buffer) != expected_artifact_digests[relative]:
                raise ValueError("extractor source changed before execution")
            _reject_unchecked_imports(buffer, "owned extractor")
            alias = "_fep_checked_" + uuid.uuid4().hex
            result = ModuleType(alias)
            result.__file__ = str(source_path)
            result.__package__ = name.rpartition(".")[0]
            result.__dict__["__builtins__"] = {
                **vars(builtins),
                "__import__": checked_import,
            }
            loaded[name] = result
            aliases.append(alias)
            sys.modules[alias] = result  # dataclass resolves postponed annotations here
            exec(compile(buffer, str(source_path), "exec"), result.__dict__)  # noqa: S102 - execute the exact retained extractor buffer
            return result

        def checked_import(
            name: str,
            globals: Any = None,
            locals: Any = None,
            fromlist: Any = (),
            level: int = 0,
        ) -> Any:
            if level == 0 and name in owned:
                # Every owned-module import form binds the digest-checked
                # buffer. ``from X import name`` (named fromlist) and
                # ``from X import *`` (fromlist ("*",)) both need the leaf:
                # IMPORT_FROM reads the leaf attribute, IMPORT_STAR copies
                # the leaf's public names. Only the empty-fromlist plain
                # ``import a.b.c``/``import a.b.c as m`` needs the ancestor
                # chain so its attribute walk stays inside the checked set.
                # No path touches canonical sys.modules.
                if fromlist:
                    return load_owned(name)
                return _checked_chain(name, load_owned)
            selected = [item for item in fromlist or () if f"{name}.{item}" in owned]
            if level == 0 and selected:
                package = builtins.__import__(
                    name, globals, locals, ("__name__",), level
                )
                # No mutation of the real package object or canonical sys.modules.
                proxy = ModuleType(name)
                proxy.__dict__.update(vars(package))
                for item in selected:
                    setattr(proxy, item, load_owned(f"{name}.{item}"))
                return proxy
            return builtins.__import__(name, globals, locals, fromlist, level)

        module.__dict__["__builtins__"] = {
            **vars(builtins),
            "__import__": checked_import,
        }
        try:
            exec(compile(source_bytes, str(path), "exec"), module.__dict__)  # noqa: S102 - execute exact source-bound local generator
            texts, _payload = module.regenerate()
        finally:
            for alias in aliases:
                sys.modules.pop(alias, None)
        expected_names = {
            str(PurePosixPath(path).relative_to(self.contract.slice))
            for path in (*self.contract.probes.values(), self.contract.manifest)
        }
        if not isinstance(texts, dict) or set(texts) != expected_names:
            raise ValueError("generator artifact roster mismatch")
        for name, source in texts.items():
            if not isinstance(source, str):
                raise TypeError("generator produced non-text output")
            if (
                contained_file(self.root, f"{self.contract.slice}/{name}").read_bytes()
                != source.encode()
            ):
                raise ValueError(f"stale generated artifact: {name}")
        return texts

    def _import_files(self) -> list[str]:
        """Bind exact owner/projection pairs for the recursive local import closure."""
        pending = list(self.contract.targets)
        found: set[str] = set()
        while pending:
            module = pending.pop()
            if module in found:
                continue
            found.add(module)
            resource = module.removeprefix("FepSketches.").replace(".", "/") + ".lean"
            owner = contained_file(self.root, f"src/fep_lean/formal/{resource}")
            projection = contained_file(self.root, f"lean/FepSketches/{resource}")
            if owner.read_bytes() != projection.read_bytes():
                raise ValueError(f"stale formal projection: {resource}")
            pending.extend(_IMPORT.findall(owner.read_text(encoding="utf-8")))
        return sorted(found)

    def _artifact_files(self) -> set[str]:
        imports = self._import_files()
        return {
            PIN,
            ENGINE_PATH,
            self.contract.provenance,
            self.contract.adapter,
            self.contract.generator,
            self.contract.renderer_tool,
            self.contract.manifest,
            self.contract.extractor,
            DOCUMENTS[self.contract.input_variant],
            "lean/lean-toolchain",
            "lean/lakefile.lean",
            "lean/lake-manifest.json",
            *self.contract.fixtures.values(),
            *self.contract.probes.values(),
            *self.contract.extra_files,
            *(b.input_path for b in self.contract.render_bindings),
            *("lean/" + name.replace(".", "/") + ".lean" for name in imports),
            *(
                "src/fep_lean/formal/"
                + name.removeprefix("FepSketches.").replace(".", "/")
                + ".lean"
                for name in imports
            ),
        }

    def source_snapshot(
        self,
        gnn: Path,
        *,
        expected_generator_sha256: str | None = None,
        expected_artifact_digests: Mapping[str, str] | None = None,
    ) -> dict[str, Any]:
        pin = self.read_object(contained_file(self.root, PIN))
        errors = self.check_sources(self.root, gnn, pin)
        if errors:
            raise ValueError("source pin is stale: " + "; ".join(errors))
        before = fingerprint(self.root, self._artifact_files())
        authority = (
            before if expected_artifact_digests is None else expected_artifact_digests
        )
        if not self.emit(self.root, gnn, self.contract.input_variant, check=True):
            raise ValueError("current input is stale")
        self._check_render(pin, authority)
        self._regenerate(
            authority[self.contract.generator]
            if expected_generator_sha256 is None
            else expected_generator_sha256,
            authority,
        )
        self._equal(
            fingerprint(self.root, self._artifact_files()),
            before,
            "snapshot inputs changed",
        )
        return {"source_pin": pin, "artifacts": before}

    def toolchain_snapshot(self) -> dict[str, Any]:
        """Hash resolved binaries without executing them during retained checks."""
        lean_dir = self.root / "lean"
        pin = read_toolchain_pin(lean_dir)
        revision = resolved_mathlib_revision(lean_dir)
        if pin is None or not revision:
            raise ValueError("missing valid Lean pin or resolved Mathlib revision")
        binaries: dict[str, dict[str, str]] = {}
        for name in ("lean", "lake"):
            executable = self.find_executable(name, lean_dir)
            if executable is None:
                raise ValueError(f"{name} executable unavailable")
            path = Path(executable).resolve(strict=True)
            binaries[name] = {
                "path": str(path),
                "sha256": self._digest(path.read_bytes()),
            }
        return {"pin": pin, "mathlib_revision": revision, "binaries": binaries}

    def compiled_imports(self) -> dict[str, str]:
        return fingerprint(
            self.root,
            [
                "lean/.lake/build/lib/lean/" + name.replace(".", "/") + ".olean"
                for name in self._import_files()
            ],
        )

    def audit_source(self, variant: str, *, expected_sha256: str | None = None) -> str:
        buffer = contained_file(self.root, self.contract.probes[variant]).read_bytes()
        if expected_sha256 is not None and self._digest(buffer) != expected_sha256:
            raise ValueError("probe source changed before compilation")
        source = buffer.decode("utf-8")
        return (
            source
            + "\n"
            + "\n".join(
                f"#print axioms {name}" for name in self.contract.theorems[variant]
            )
            + "\n"
        )

    def _raw_result(self, record: Any) -> dict[str, Any]:
        if not isinstance(record, dict):
            raise TypeError("missing native process evidence")
        if type(record.get("returncode")) is not int or record["returncode"] != 0:
            raise ValueError("native process did not exit successfully")
        if not all(isinstance(record.get(key), str) for key in ("stdout", "stderr")):
            raise ValueError("missing native process transcript")
        command = record.get("command")
        if (
            not isinstance(command, list)
            or not command
            or any(not isinstance(a, str) or not a for a in command)
        ):
            raise ValueError("missing actual native argv")
        raw = {
            key: record[key] for key in ("returncode", "stdout", "stderr", "command")
        }
        if _DIAGNOSTIC.search(raw["stdout"] + "\n" + raw["stderr"]):
            raise ValueError("native transcript contains errors, warnings, or sorry")
        return raw

    def _check_native_command(
        self,
        raw: dict[str, Any],
        toolchain: dict[str, Any],
        kind: str,
        variant: str = "",
    ) -> None:
        lake = toolchain["binaries"]["lake"]["path"]
        lean = toolchain["binaries"]["lean"]["path"]
        command = raw["command"]
        if kind == "version":
            expected = [lake, "env", lean, "--version"]
        elif kind == "build":
            expected = [lake, "build", *self.contract.targets]
        else:
            if (
                len(command) != 6
                or not Path(command[-1]).is_absolute()
                or Path(command[-1]).name != f"probe_{variant}.lean"
            ):
                raise ValueError("native probe argv does not name exact audit variant")
            expected = [
                lake,
                "env",
                lean,
                "-R",
                str(self.root / "src/fep_lean/formal"),
                command[-1],
            ]
        self._equal(command, expected, "native argv")

    def _probe_record(self, variant: str, recorded: Any) -> dict[str, Any]:
        raw = self._raw_result(recorded)
        self._check_native_command(raw, self.toolchain_snapshot(), "probe", variant)
        parsed, errors = _parse_axiom_output(
            raw["stdout"] + "\n" + raw["stderr"],
            expected=self.contract.theorems[variant],
        )
        if errors or any(set(axioms) - ALLOWED_AXIOMS for axioms in parsed.values()):
            raise ValueError(
                "missing, malformed, duplicate, or forbidden axiom evidence"
            )
        return {
            **raw,
            "probe_sha256": self._digest(
                contained_file(self.root, self.contract.probes[variant]).read_bytes()
            ),
            "audit_source_sha256": self._digest(self.audit_source(variant).encode()),
            "theorems": list(self.contract.theorems[variant]),
            "axioms": {
                name: list(parsed[name]) for name in self.contract.theorems[variant]
            },
            "stdout_sha256": self._digest(raw["stdout"].encode()),
            "stderr_sha256": self._digest(raw["stderr"].encode()),
        }

    def _receipt(
        self,
        snapshot: dict[str, Any],
        toolchain: dict[str, Any],
        imports: dict[str, str],
        version: Any,
        build: Any,
        probes: Any,
    ) -> dict[str, Any]:
        version_raw = self._raw_result(version)
        self._check_native_command(version_raw, toolchain, "version")
        self._check_native_command(self._raw_result(build), toolchain, "build")
        if not lean_version_matches_pin(version_raw["stdout"], toolchain["pin"]):
            raise ValueError(
                "actual compiler version differs from the pinned toolchain"
            )
        if not isinstance(probes, dict) or set(probes) != set(self.contract.probes):
            raise ValueError("all configured native probe results are required")
        return {
            "schema_version": 2,
            "contract": self.contract.record(),
            "engine_sha256": snapshot["artifacts"][ENGINE_PATH],
            "scope": self.contract.scope,
            "evidence_plane": "native concrete static artifact proof",
            "native_claim_ready": True,
            "runtime_execution_verified": False,
            "source_before": snapshot,
            "source_after": snapshot,
            "toolchain": toolchain,
            "compiled_imports": imports,
            "compiler_version": version_raw,
            "dependency_build": {
                **self._raw_result(build),
                "targets": list(self.contract.targets),
            },
            "probes": {
                key: self._probe_record(key, probes[key])
                for key in self.contract.probes
            },
        }

    def validate_receipt(self, gnn: Path, recorded: Any) -> list[str]:
        """Reconstruct every verdict from retained native output and current bytes."""
        try:
            if not isinstance(recorded, dict):
                raise TypeError("native receipt must be an object")
            self._equal(
                fingerprint(self.root, self._artifact_files()),
                recorded["source_before"]["artifacts"],
                "retained input binding",
            )
            generator_sha256 = recorded["source_before"]["artifacts"][
                self.contract.generator
            ]
            snapshot = self.source_snapshot(
                gnn,
                expected_generator_sha256=generator_sha256,
                expected_artifact_digests=recorded["source_before"]["artifacts"],
            )
            toolchain = self.toolchain_snapshot()
            imports = self.compiled_imports()
            expected = self._receipt(
                snapshot,
                toolchain,
                imports,
                recorded.get("compiler_version"),
                recorded.get("dependency_build"),
                recorded.get("probes"),
            )
            self._equal(recorded, expected, "native receipt")
            self._equal(
                self.source_snapshot(
                    gnn,
                    expected_generator_sha256=generator_sha256,
                    expected_artifact_digests=recorded["source_before"]["artifacts"],
                ),
                snapshot,
                "sources changed during check",
            )
            self._equal(
                self.toolchain_snapshot(), toolchain, "toolchain changed during check"
            )
            self._equal(
                self.compiled_imports(), imports, "imports changed during check"
            )
            return []
        except (
            OSError,
            ValueError,
            TypeError,
            KeyError,
            UnicodeError,
            subprocess.CalledProcessError,
            RecursionError,
        ) as exc:
            return [str(exc)]

    def _run(self, command: list[str], timeout: float) -> dict[str, Any]:
        result = self.run_process_group(
            command,
            cwd=self.root / "lean",
            env=self.subprocess_env(self.root / "lean"),
            timeout=timeout,
        )
        return {
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "command": list(command),
        }

    def compile_receipt(self, gnn: Path, *, timeout: float = 1800) -> dict[str, Any]:
        """Build only local imports, then compile both exact probes with axiom census."""
        if not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("timeout must be finite and positive")
        snapshot = self.source_snapshot(gnn)
        toolchain = self.toolchain_snapshot()
        lake = toolchain["binaries"]["lake"]["path"]
        lean = toolchain["binaries"]["lean"]["path"]
        version = self._run([lake, "env", lean, "--version"], min(timeout, 30))
        self._raw_result(version)
        if not lean_version_matches_pin(version["stdout"], toolchain["pin"]):
            raise ValueError(
                "actual compiler version differs from the pinned toolchain"
            )
        build = self._run([lake, "build", *self.contract.targets], timeout)
        self._raw_result(build)
        imports = self.compiled_imports()
        probes: dict[str, Any] = {}
        with tempfile.TemporaryDirectory(prefix="fep_artifact_native_") as directory:
            for variant in self.contract.probes:
                source = self.audit_source(
                    variant,
                    expected_sha256=snapshot["artifacts"][
                        self.contract.probes[variant]
                    ],
                )
                path = Path(directory) / f"probe_{variant}.lean"
                path.write_text(source, encoding="utf-8")
                probes[variant] = self._run(
                    [
                        lake,
                        "env",
                        lean,
                        "-R",
                        str(self.root / "src/fep_lean/formal"),
                        str(path),
                    ],
                    timeout,
                )
                self._probe_record(variant, probes[variant])
        self._equal(
            self.source_snapshot(
                gnn,
                expected_generator_sha256=snapshot["artifacts"][
                    self.contract.generator
                ],
                expected_artifact_digests=snapshot["artifacts"],
            ),
            snapshot,
            "sources changed during compilation",
        )
        self._equal(
            self.toolchain_snapshot(), toolchain, "toolchain changed during compilation"
        )
        self._equal(
            self.compiled_imports(), imports, "imports changed during compilation"
        )
        return self._receipt(snapshot, toolchain, imports, version, build, probes)

    def _check_output(self, gnn: Path, path: Path) -> None:
        """Reject receipt output aliases into either source tree or compiled inputs."""
        target = path.resolve()
        protected = {(self.root / name).resolve() for name in self._artifact_files()}
        pin = self.read_object(contained_file(self.root, PIN))
        for checkout, key in ((self.root, "fep_lean"), (gnn, "gnn")):
            protected.update((checkout / name).resolve() for name in pin[key]["owners"])
        protected.update(
            (
                self.root
                / ("lean/.lake/build/lib/lean/" + name.replace(".", "/") + ".olean")
            ).resolve()
            for name in self._import_files()
        )
        protected.update(
            Path(entry["path"])
            for entry in self.toolchain_snapshot()["binaries"].values()
        )
        if any(parent.is_symlink() for parent in [path, *path.parents]):
            raise ValueError("receipt output must not traverse a symlink")
        if target in protected:
            raise ValueError("receipt output collides with a protected input")

    def main(self, argv: list[str] | None = None) -> int:
        parser = argparse.ArgumentParser(description=__doc__)
        mode = parser.add_mutually_exclusive_group()
        mode.add_argument(
            "--check", action="store_true", help="read-only retained check (default)"
        )
        mode.add_argument(
            "--compile", action="store_true", help="explicit native compilation"
        )
        parser.add_argument("--gnn-root", type=Path, required=True)
        parser.add_argument("--receipt", type=Path, required=True)
        parser.add_argument("--timeout", type=float, default=1800)
        args = parser.parse_args(argv)
        try:
            if args.compile:
                self._check_output(args.gnn_root.resolve(), args.receipt)
                receipt = self.compile_receipt(
                    args.gnn_root.resolve(), timeout=args.timeout
                )
                self._check_output(args.gnn_root.resolve(), args.receipt)
                self.write_json(args.receipt, receipt)
            else:
                errors = self.validate_receipt(
                    args.gnn_root.resolve(), self.read_object(args.receipt)
                )
                if errors:
                    raise ValueError("; ".join(errors))
        except (
            OSError,
            ValueError,
            TypeError,
            KeyError,
            UnicodeError,
            subprocess.TimeoutExpired,
            subprocess.CalledProcessError,
            RecursionError,
        ) as exc:
            print(f"Artifact evidence rejected: {exc}", file=sys.stderr)
            return 1
        print(
            "Native static-artifact evidence is current; runner execution is not claimed"
        )
        return 0
