"""Native declaration-resolution and axiom audit for reviewed formalisms."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path

from fep_lean.catalogue.generation import fep_all_projection_drift
from fep_lean.catalogue.registry import body_source_relative_paths
from fep_lean.catalogue.relations import EdgeKind, load_formalism_graph
from fep_lean.catalogue.semantics import load_theorem_maturity
from fep_lean.formal import (
    formal_aggregate_drift,
    formal_module_imports,
    formal_projection_drift,
    formal_resource_relative_paths,
    formal_theorem_modules,
)
from fep_lean.verification._subprocess import run_process_group
from fep_lean.verification._toolchain import (
    find_executable,
    lean_version_matches_pin,
    resolved_mathlib_revision,
    subprocess_env,
)

_WARNING_RE = re.compile(r"^.*warning:.*$", re.MULTILINE)
_ERROR_RE = re.compile(r"^.*error:.*$", re.MULTILINE)
_AXIOM_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_'.]*$")
_DEPENDS_MARKER = "' depends on axioms: ["
_NO_AXIOMS_MARKER = "' does not depend on any axioms"
_AXIOM_POLICY_VERSION = 1
_ALLOWED_AXIOMS = frozenset({"Classical.choice", "Quot.sound", "propext"})
_DIGEST_PATHS = (
    "config/catalogue_metadata.yaml",
    "config/theorem_maturity.yaml",
    "config/formalism_novelty.yaml",
    "config/formalism_relations.yaml",
    "src/fep_lean/catalogue/registry.py",
    *body_source_relative_paths(),
    "lean/lean-toolchain",
    "lean/lakefile.lean",
    "lean/lake-manifest.json",
)


@dataclass(frozen=True)
class FormalismEvidenceRecord:
    """Declaration-level provenance and native axiom evidence."""

    declaration: str
    source_roles: tuple[str, ...]
    source_ids: tuple[str, ...]
    formal_module: str
    resolved: bool
    axioms: tuple[str, ...]
    uses_sorry_ax: bool


@dataclass(frozen=True)
class FormalismAuditResult:
    """Fail-closed outcome of one native declaration/axiom probe."""

    schema_version: int
    kind: str
    complete: bool
    declaration_count: int
    evidence_count: int
    declarations_resolved: int
    warnings: tuple[str, ...]
    sorry_ax_detected: bool
    source_sha256: str
    lean_toolchain: str
    lean_version: str
    mathlib_revision: str
    axiom_policy_version: int
    returncode: int
    failure_reason: str
    evidence_declarations: tuple[str, ...]
    axiom_output: tuple[str, ...]
    axiom_parse_errors: tuple[str, ...]
    declaration_evidence: tuple[FormalismEvidenceRecord, ...]

    def as_dict(self) -> dict[str, object]:
        """Return a deterministic JSON-compatible payload."""
        payload = asdict(self)
        payload["warnings"] = list(self.warnings)
        payload["evidence_declarations"] = list(self.evidence_declarations)
        payload["axiom_output"] = list(self.axiom_output)
        payload["axiom_parse_errors"] = list(self.axiom_parse_errors)
        payload["declaration_evidence"] = [
            {
                "declaration": record.declaration,
                "source_roles": list(record.source_roles),
                "source_ids": list(record.source_ids),
                "formal_module": record.formal_module,
                "resolved": record.resolved,
                "axioms": list(record.axioms),
                "uses_sorry_ax": record.uses_sorry_ax,
            }
            for record in self.declaration_evidence
        ]
        return payload


def _primary_declarations(project_root: Path) -> tuple[str, ...]:
    audit = load_theorem_maturity(
        Path(project_root) / "config" / "theorem_maturity.yaml"
    )
    declarations = []
    for row in audit.records:
        digits = row.id.removeprefix("fep-")
        declarations.append(f"fep_fep{digits}.FEP{digits}.{row.primary_theorem}")
    return tuple(declarations)


def _evidence_declarations(project_root: Path) -> tuple[str, ...]:
    graph = load_formalism_graph(
        Path(project_root) / "config" / "formalism_relations.yaml"
    )
    declarations = {
        declaration for node in graph.capabilities for declaration in node.evidence
    }
    declarations.update(
        edge.witness
        for edge in graph.edges
        if edge.kind.is_theorem_witnessed and edge.witness is not None
    )
    declarations.update(formal_theorem_modules(project_root))
    return tuple(sorted(declarations))


def _declaration_sources(
    project_root: Path,
) -> tuple[tuple[str, ...], dict[str, tuple[tuple[str, str], ...]]]:
    """Return declaration closure and its authored semantic source pairs."""
    root = Path(project_root)
    maturity = load_theorem_maturity(root / "config" / "theorem_maturity.yaml")
    graph = load_formalism_graph(root / "config" / "formalism_relations.yaml")
    sources: dict[str, set[tuple[str, str]]] = {}
    primary: list[str] = []
    for row in maturity.records:
        digits = row.id.removeprefix("fep-")
        declaration = f"fep_fep{digits}.FEP{digits}.{row.primary_theorem}"
        primary.append(declaration)
        sources.setdefault(declaration, set()).add(("topic_primary", row.id))
    for node in graph.capabilities:
        for declaration in node.evidence:
            sources.setdefault(declaration, set()).add(("capability_evidence", node.id))
    for edge in graph.edges:
        if edge.kind.is_theorem_witnessed and edge.witness is not None:
            sources.setdefault(edge.witness, set()).add(
                (
                    "formal_relation"
                    if edge.kind is EdgeKind.FORMAL
                    else "formal_pairing",
                    f"{edge.source}->{edge.target}",
                )
            )
    for declaration, module in formal_theorem_modules(root).items():
        sources.setdefault(declaration, set()).add(("formal_module", module))
    evidence = _evidence_declarations(root)
    declarations = tuple(dict.fromkeys((*primary, *evidence)))
    return declarations, {
        declaration: tuple(sorted(sources[declaration])) for declaration in declarations
    }


def parse_axiom_output(
    output: str,
    *,
    expected: tuple[str, ...] | None = None,
) -> tuple[dict[str, tuple[str, ...]], tuple[str, ...]]:
    """Parse Lean ``#print axioms`` evidence without ambiguous overwrites.

    Lean may wrap long axiom lists and declaration names may end in primes.
    A small line-oriented parser handles both forms while reporting duplicate,
    unexpected, missing, unterminated, and malformed records fail closed.
    """
    parsed: dict[str, tuple[str, ...]] = {}
    errors: list[str] = []
    lines = output.splitlines()
    index = 0

    def add_record(declaration: str, axioms: tuple[str, ...]) -> None:
        if not declaration or declaration.strip() != declaration:
            errors.append(f"malformed declaration in axiom evidence: {declaration!r}")
            return
        if declaration in parsed:
            errors.append(f"duplicate axiom evidence for {declaration}")
            return
        parsed[declaration] = axioms

    while index < len(lines):
        line = lines[index].strip()
        depends_at = line.rfind(_DEPENDS_MARKER) if line.startswith("'") else -1
        no_axioms_at = line.rfind(_NO_AXIOMS_MARKER) if line.startswith("'") else -1
        if depends_at > 0:
            declaration = line[1:depends_at]
            payload = line[depends_at + len(_DEPENDS_MARKER) :]
            while "]" not in payload and index + 1 < len(lines):
                index += 1
                payload = f"{payload} {lines[index].strip()}"
            if "]" not in payload:
                errors.append(f"unterminated axiom list for {declaration}")
                index += 1
                continue
            axiom_blob, trailing = payload.split("]", 1)
            if trailing.strip():
                errors.append(f"trailing text in axiom evidence for {declaration}")
            raw_axioms = tuple(
                item.strip() for item in axiom_blob.split(",") if item.strip()
            )
            for axiom in raw_axioms:
                if not _AXIOM_NAME_RE.fullmatch(axiom):
                    errors.append(f"malformed axiom name for {declaration}: {axiom}")
            add_record(declaration, raw_axioms)
        elif no_axioms_at > 0:
            declaration = line[1:no_axioms_at]
            trailing = line[no_axioms_at + len(_NO_AXIOMS_MARKER) :]
            if trailing.strip():
                errors.append(f"trailing text in axiom evidence for {declaration}")
            add_record(declaration, ())
        elif line.startswith("'") and ("axiom" in line or "depend" in line):
            errors.append(f"malformed axiom evidence line: {line}")
        index += 1

    if expected is not None:
        expected_set = set(expected)
        for declaration in parsed:
            if declaration not in expected_set:
                errors.append(f"unexpected axiom evidence for {declaration}")
        for declaration in expected:
            if declaration not in parsed:
                errors.append(f"missing axiom evidence for {declaration}")
    return parsed, tuple(dict.fromkeys(errors))


# Compatibility alias: tests and external callers historically imported the
# private name; keep it importable until they migrate to ``parse_axiom_output``.
_parse_axiom_output = parse_axiom_output


def _axioms_by_declaration(output: str) -> dict[str, tuple[str, ...]]:
    """Compatibility projection of the strict parser's unambiguous records."""
    parsed, _ = parse_axiom_output(output)
    return parsed


def _canonical_axiom_output(
    declarations: tuple[str, ...], axiom_map: dict[str, tuple[str, ...]]
) -> tuple[str, ...]:
    """Normalize Lean's sometimes hard-wrapped axiom messages for receipts."""
    lines = []
    for declaration in declarations:
        if declaration not in axiom_map:
            continue
        axioms = axiom_map[declaration]
        if axioms:
            lines.append(f"'{declaration}' depends on axioms: [{', '.join(axioms)}]")
        else:
            lines.append(f"'{declaration}' does not depend on any axioms")
    return tuple(lines)


def _declaration_records(
    project_root: Path,
    *,
    probe_succeeded: bool,
    output: str,
    sorry_ax_detected: bool,
) -> tuple[FormalismEvidenceRecord, ...]:
    declarations, sources = _declaration_sources(project_root)
    axiom_map = _axioms_by_declaration(output)
    formal_modules = formal_theorem_modules(project_root)
    records = []
    for declaration in declarations:
        pairs = sources[declaration]
        axioms = axiom_map.get(declaration, ())
        uses_sorry = "sorryAx" in axioms or (
            sorry_ax_detected and declaration not in axiom_map
        )
        records.append(
            FormalismEvidenceRecord(
                declaration=declaration,
                source_roles=tuple(role for role, _ in pairs),
                source_ids=tuple(source_id for _, source_id in pairs),
                formal_module=formal_modules.get(declaration, "FepSketches.fep_all"),
                resolved=probe_succeeded and declaration in axiom_map,
                axioms=axioms,
                uses_sorry_ax=uses_sorry,
            )
        )
    return tuple(records)


def build_formalism_probe(
    project_root: Path,
) -> tuple[str, tuple[str, ...], tuple[str, ...]]:
    """Build Lean source resolving all primaries and printing evidence axioms."""
    primary = _primary_declarations(project_root)
    evidence = _evidence_declarations(project_root)
    declarations = tuple(dict.fromkeys((*primary, *evidence)))
    lines = [
        *(f"import {module}" for module in formal_module_imports()),
        "",
    ]
    lines.extend(f"#check {declaration}" for declaration in declarations)
    lines.append("")
    lines.extend(f"#print axioms {declaration}" for declaration in declarations)
    return "\n".join(lines).rstrip() + "\n", primary, evidence


def _source_digest(project_root: Path) -> str:
    root = Path(project_root)
    digest = hashlib.sha256()
    relative_paths = tuple(Path(relative) for relative in _DIGEST_PATHS) + tuple(
        formal_resource_relative_paths()
    )
    for relative in relative_paths:
        path = root / relative
        relative_text = relative.as_posix()
        digest.update(relative_text.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes() if path.is_file() else b"")
        digest.update(b"\0")
    return digest.hexdigest()


def _toolchain(project_root: Path) -> str:
    path = Path(project_root) / "lean" / "lean-toolchain"
    return path.read_text(encoding="utf-8").strip() if path.is_file() else ""


def _mathlib_revision(project_root: Path) -> str:
    """Return the exact Mathlib Git revision resolved by Lake."""
    return resolved_mathlib_revision(Path(project_root) / "lean")


def _probe_lean_version(
    lake: str,
    lean_dir: Path,
    *,
    timeout: int = 20,
) -> tuple[str, str]:
    """Record the exact compiler identity used by ``lake env lean``."""
    try:
        completed = run_process_group(
            [lake, "env", "lean", "--version"],
            cwd=lean_dir,
            env=subprocess_env(lean_dir),
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return "", f"cannot identify resolved Lean compiler: {exc}"
    output = ((completed.stdout or "") + (completed.stderr or "")).strip()
    first_line = output.splitlines()[0] if output else ""
    if completed.returncode != 0 or not first_line:
        return "", "resolved Lean compiler did not report a version"
    return first_line, ""


def _failed_result(
    project_root: Path,
    declarations: tuple[str, ...],
    evidence: tuple[str, ...],
    reason: str,
    *,
    lean_version: str = "",
) -> FormalismAuditResult:
    return FormalismAuditResult(
        schema_version=4,
        kind="formalism-declaration-audit",
        complete=False,
        declaration_count=len(declarations),
        evidence_count=len(evidence),
        declarations_resolved=0,
        warnings=(),
        sorry_ax_detected=False,
        source_sha256=_source_digest(project_root),
        lean_toolchain=_toolchain(project_root),
        lean_version=lean_version,
        mathlib_revision=_mathlib_revision(project_root),
        axiom_policy_version=_AXIOM_POLICY_VERSION,
        returncode=127,
        failure_reason=reason,
        evidence_declarations=evidence,
        axiom_output=(),
        axiom_parse_errors=(),
        declaration_evidence=_declaration_records(
            project_root,
            probe_succeeded=False,
            output="",
            sorry_ax_detected=False,
        ),
    )


def run_formalism_audit(
    project_root: Path, *, timeout: int = 300
) -> FormalismAuditResult:
    """Run the pinned Lean declaration probe and reject warnings or `sorryAx`."""
    root = Path(project_root)
    probe, primary, evidence = build_formalism_probe(root)
    declarations = tuple(dict.fromkeys((*primary, *evidence)))
    aggregate_drift = fep_all_projection_drift(root)
    if aggregate_drift:
        return _failed_result(
            root,
            declarations,
            evidence,
            "whole-catalogue Lean projection is stale",
        )
    if formal_aggregate_drift(root):
        return _failed_result(
            root,
            declarations,
            evidence,
            "formal composition aggregate is stale",
        )
    drift = formal_projection_drift(root)
    if drift:
        return _failed_result(
            root, declarations, evidence, "formal Lean workspace projection is stale"
        )
    lean_dir = root / "lean"
    lake = find_executable("lake", lean_dir)
    if lake is None:
        return _failed_result(
            root, declarations, evidence, "pinned lake executable is unavailable"
        )
    mathlib_revision = _mathlib_revision(root)
    if not mathlib_revision:
        return _failed_result(
            root,
            declarations,
            evidence,
            "resolved Mathlib revision is unavailable from lake-manifest.json",
        )
    lean_version, version_error = _probe_lean_version(lake, lean_dir)
    if version_error:
        return _failed_result(
            root,
            declarations,
            evidence,
            version_error,
            lean_version=lean_version,
        )
    if not lean_version_matches_pin(lean_version, _toolchain(root)):
        return _failed_result(
            root,
            declarations,
            evidence,
            "resolved Lean compiler version does not match the pinned toolchain",
            lean_version=lean_version,
        )

    sketches = lean_dir / "FepSketches"
    sketches.mkdir(parents=True, exist_ok=True)
    fd, raw_path = tempfile.mkstemp(
        prefix="formalism_audit_", suffix=".lean", dir=sketches
    )
    probe_path = Path(raw_path)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(probe)
        try:
            completed = run_process_group(
                [lake, "env", "lean", str(probe_path.relative_to(lean_dir))],
                cwd=lean_dir,
                env=subprocess_env(lean_dir),
                timeout=timeout,
                check=False,
            )
            output = (completed.stdout or "") + (completed.stderr or "")
            returncode = completed.returncode
            failure_reason = ""
        except (OSError, subprocess.TimeoutExpired) as exc:
            output = str(exc)
            returncode = 124 if isinstance(exc, subprocess.TimeoutExpired) else 126
            failure_reason = str(exc)
    finally:
        probe_path.unlink(missing_ok=True)

    warnings = tuple(_WARNING_RE.findall(output))
    errors = tuple(_ERROR_RE.findall(output))
    if returncode != 0 and not failure_reason:
        failure_reason = (
            f"Lean declaration probe failed: {errors[0]}"
            if errors
            else "Lean declaration probe failed without a reported Lean error"
        )
    sorry_ax = "sorryAx" in output
    axiom_map, axiom_parse_errors = parse_axiom_output(
        output,
        expected=declarations,
    )
    axiom_output = _canonical_axiom_output(declarations, axiom_map)
    unapproved_axioms = tuple(
        sorted(
            {
                axiom
                for axioms in axiom_map.values()
                for axiom in axioms
                if axiom not in _ALLOWED_AXIOMS
            }
        )
    )
    declaration_evidence = _declaration_records(
        root,
        probe_succeeded=returncode == 0,
        output=output,
        sorry_ax_detected=sorry_ax,
    )
    declarations_resolved = sum(record.resolved for record in declaration_evidence)
    complete = (
        returncode == 0
        and not warnings
        and not sorry_ax
        and not axiom_parse_errors
        and not unapproved_axioms
        and all(record.resolved for record in declaration_evidence)
    )
    if warnings and not failure_reason:
        failure_reason = "Lean declaration probe emitted warnings"
    if sorry_ax and not failure_reason:
        failure_reason = "Lean declaration evidence depends on sorryAx"
    if axiom_parse_errors and not failure_reason:
        failure_reason = "; ".join(axiom_parse_errors)
    if unapproved_axioms and not failure_reason:
        failure_reason = (
            "Lean declaration evidence uses unapproved axioms: "
            + ", ".join(unapproved_axioms)
        )
    if declarations_resolved != len(declarations) and not failure_reason:
        missing_count = len(declarations) - declarations_resolved
        failure_reason = (
            f"Lean axiom probe omitted evidence for {missing_count} declaration(s)"
        )
    return FormalismAuditResult(
        schema_version=4,
        kind="formalism-declaration-audit",
        complete=complete,
        declaration_count=len(declarations),
        evidence_count=len(evidence),
        declarations_resolved=declarations_resolved,
        warnings=warnings,
        sorry_ax_detected=sorry_ax,
        source_sha256=_source_digest(root),
        lean_toolchain=_toolchain(root),
        lean_version=lean_version,
        mathlib_revision=mathlib_revision,
        axiom_policy_version=_AXIOM_POLICY_VERSION,
        returncode=returncode,
        failure_reason=failure_reason,
        evidence_declarations=evidence,
        axiom_output=axiom_output,
        axiom_parse_errors=axiom_parse_errors,
        declaration_evidence=declaration_evidence,
    )


def write_formalism_audit_receipt(path: Path, result: FormalismAuditResult) -> Path:
    """Atomically write the declaration-audit receipt."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, raw_path = tempfile.mkstemp(
        prefix=f".{destination.name}.", dir=destination.parent
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(result.as_dict(), handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(raw_path, destination)
    except Exception:
        Path(raw_path).unlink(missing_ok=True)
        raise
    return destination


def validate_formalism_audit_receipt(path: Path, project_root: Path) -> tuple[str, ...]:
    """Validate a stored audit receipt against live canonical owners."""
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return (f"cannot read formalism audit receipt: {exc}",)
    if not isinstance(payload, dict):
        return ("formalism audit receipt must be a JSON object",)

    root = Path(project_root)
    try:
        aggregate_drift = fep_all_projection_drift(root)
        composition_aggregate_drift = formal_aggregate_drift(root)
        resource_drift = formal_projection_drift(root)
        live_source_digest = _source_digest(root)
        live_toolchain = _toolchain(root)
        live_mathlib_revision = _mathlib_revision(root)
        declarations, source_map = _declaration_sources(root)
        formal_modules = formal_theorem_modules(root)
        evidence = _evidence_declarations(root)
    except (OSError, TypeError, ValueError, UnicodeError) as exc:
        return (f"live formalism owners cannot be loaded: {exc}",)

    errors: list[str] = []
    if aggregate_drift:
        errors.append("live whole-catalogue Lean projection is stale")
    if composition_aggregate_drift:
        errors.append("live formal composition aggregate is stale")
    if resource_drift:
        errors.append("live formal Lean workspace projection is stale")
    if payload.get("schema_version") != 4:
        errors.append("receipt schema_version must be 4")
    if payload.get("kind") != "formalism-declaration-audit":
        errors.append("receipt kind is not formalism-declaration-audit")
    if payload.get("source_sha256") != live_source_digest:
        errors.append("receipt source_sha256 does not match canonical owners")
    if payload.get("lean_toolchain") != live_toolchain:
        errors.append("receipt lean_toolchain does not match the live pin")
    lean_version = payload.get("lean_version")
    if not isinstance(lean_version, str) or not lean_version_matches_pin(
        lean_version, live_toolchain
    ):
        errors.append("receipt lean_version does not match the live pin")
    if payload.get("mathlib_revision") != live_mathlib_revision:
        errors.append("receipt mathlib_revision does not match lake-manifest.json")
    if payload.get("axiom_policy_version") != _AXIOM_POLICY_VERSION:
        errors.append("receipt axiom policy version is unsupported")

    raw_records = payload.get("declaration_evidence")
    if not isinstance(raw_records, list):
        errors.append("receipt declaration_evidence must be a list")
        raw_records = []
    record_declarations = [
        record.get("declaration") if isinstance(record, dict) else None
        for record in raw_records
    ]
    if record_declarations != list(declarations):
        errors.append("receipt declaration evidence does not match canonical closure")

    resolved_count = 0
    uses_sorry_ax = False
    for record in raw_records:
        if not isinstance(record, dict):
            errors.append("receipt declaration evidence contains a non-object")
            continue
        declaration = record.get("declaration")
        if declaration not in source_map:
            continue
        expected_pairs = source_map[declaration]
        if record.get("source_roles") != [role for role, _ in expected_pairs]:
            errors.append(f"receipt source roles drifted for {declaration}")
        if record.get("source_ids") != [source_id for _, source_id in expected_pairs]:
            errors.append(f"receipt source IDs drifted for {declaration}")
        expected_module = formal_modules.get(declaration, "FepSketches.fep_all")
        if record.get("formal_module") != expected_module:
            errors.append(f"receipt formal module drifted for {declaration}")
        if not isinstance(record.get("resolved"), bool):
            errors.append(f"receipt resolved flag is invalid for {declaration}")
        elif record["resolved"]:
            resolved_count += 1
        axioms = record.get("axioms")
        if not isinstance(axioms, list) or not all(
            isinstance(item, str) and item for item in axioms
        ):
            errors.append(f"receipt axioms are invalid for {declaration}")
        elif any(item not in _ALLOWED_AXIOMS for item in axioms):
            errors.append(f"receipt axioms violate policy for {declaration}")
        if not isinstance(record.get("uses_sorry_ax"), bool):
            errors.append(f"receipt sorryAx flag is invalid for {declaration}")
        elif record["uses_sorry_ax"]:
            uses_sorry_ax = True

    if payload.get("declaration_count") != len(declarations):
        errors.append("receipt declaration_count does not match canonical closure")
    if payload.get("evidence_count") != len(evidence):
        errors.append("receipt evidence_count does not match canonical evidence")
    if payload.get("evidence_declarations") != list(evidence):
        errors.append("receipt evidence declarations do not match canonical evidence")
    if type(payload.get("returncode")) is not int or payload.get("returncode") != 0:
        errors.append("receipt returncode must be 0")
    warnings = payload.get("warnings")
    if warnings != []:
        errors.append("receipt warnings must be empty")
    if payload.get("declarations_resolved") != resolved_count:
        errors.append("receipt declarations_resolved does not match resolved evidence")
    if payload.get("declarations_resolved") != len(declarations):
        errors.append("receipt declarations_resolved must equal declaration_count")
    if resolved_count != len(declarations):
        errors.append("receipt contains unresolved declaration evidence")
    if uses_sorry_ax:
        errors.append("receipt declaration evidence reports sorryAx")
    raw_axiom_output = payload.get("axiom_output")
    if not isinstance(raw_axiom_output, list) or not all(
        isinstance(line, str) for line in raw_axiom_output
    ):
        errors.append("receipt axiom_output must be a list of strings")
        raw_axiom_output = []
    parsed_axioms, reparsed_errors = parse_axiom_output(
        "\n".join(raw_axiom_output),
        expected=declarations,
    )
    if payload.get("axiom_parse_errors") != []:
        errors.append("receipt axiom_parse_errors must be empty")
    if reparsed_errors:
        errors.append("receipt axiom output is ambiguous or malformed")
    if any(
        axiom not in _ALLOWED_AXIOMS
        for axioms in parsed_axioms.values()
        for axiom in axioms
    ):
        errors.append("receipt axiom output violates the trusted policy")
    if set(parsed_axioms) != set(declarations) or len(raw_axiom_output) != len(
        declarations
    ):
        errors.append("receipt axiom output does not cover the declaration closure")
    for record in raw_records:
        if not isinstance(record, dict):
            continue
        declaration = record.get("declaration")
        if declaration in parsed_axioms and record.get("axioms") != list(
            parsed_axioms[declaration]
        ):
            errors.append(f"receipt axiom evidence drifted for {declaration}")
    if payload.get("complete") is not True:
        errors.append("receipt is incomplete")
    if payload.get("failure_reason") != "":
        errors.append("receipt failure_reason must be empty")
    if payload.get("sorry_ax_detected") is not False:
        errors.append("receipt reports sorryAx")
    return tuple(dict.fromkeys(errors))
