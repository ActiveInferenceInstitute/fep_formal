"""Explicit bridge emission and read-only source/artifact verification."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from types import ModuleType
from typing import Any

from fep_lean.bridge.certificates import TOLERANCE, compare, render_markdown
from fep_lean.bridge.custody import (
    FRESH,
    binding_digest,
    contained_file,
    fingerprint,
    refresh_signature,
    valid_commit,
    validate_binding,
    write_json,
    write_text,
)

PIN = "specs/gnn-bridge-w2-source-custody/source-pin.json"
EMITTERS = {
    "finite": "specs/gnn-bridge-p1-finite-spike/projection.py",
    "continuous": "specs/gnn-bridge-p4b-continuous-emission/projection_continuous.py",
}
DOCUMENTS = {
    "finite": "specs/gnn-bridge-p1-finite-spike/gnn-input/FepLeanSymmetricBool.md",
    "continuous": "specs/gnn-bridge-p4b-continuous-emission/gnn-input/FepLeanContinuousOU.md",
}
CONTRACT = "docs/design/gnn-bridge/bridge-contract.md"
MIRROR = "docs/other/fep_lean/bridge-contract.md"
SYNTAX_PIN = "specs/gnn-bridge-w1-bridge-operations/syntax-pin.json"
SYNTAX_FILES = ("docs/gnn/gnn_syntax.md", "src/gnn/pipeline/step_registry.py")


def owner_roster(root: Path, repository: str) -> list[str]:
    """Discover relevant owners; validation also rejects additions/deletions."""
    patterns: tuple[str, ...]
    if repository == "fep_lean":
        fixed = [
            "pyproject.toml",
            "uv.lock",
            "lean/lean-toolchain",
            "lean/lakefile.lean",
            "lean/lake-manifest.json",
            CONTRACT,
            *EMITTERS.values(),
        ]
        patterns = ("src/fep_lean/**/*.py", "src/fep_lean/formal/**/*.lean")
    elif repository == "gnn":
        fixed = [
            "pyproject.toml",
            "uv.lock",
            "src/gnn/main.py",
            MIRROR,
            *SYNTAX_FILES,
        ]
        patterns = ("src/gnn/**/*.py",)
    else:
        raise ValueError("unknown repository")
    return sorted(
        set(fixed)
        | {
            p.relative_to(root).as_posix()
            for pattern in patterns
            for p in root.glob(pattern)
        }
    )


def _head(root: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
        timeout=15,
    )
    return result.stdout.strip()


def read_object(path: Path) -> dict[str, Any]:
    result = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(result, dict):
        raise TypeError(f"JSON root must be an object: {path.name}")
    return result


def pin_sources(root: Path, gnn: Path) -> dict[str, Any]:
    """Explicitly seal current owner bytes. Does not bless any existing receipt."""
    pin: dict[str, Any] = {"schema_version": 1}
    for key, checkout in (("fep_lean", root), ("gnn", gnn)):
        pin[key] = {
            "commit": _head(checkout),
            "owners": fingerprint(checkout, owner_roster(checkout, key)),
        }
    write_json(root / PIN, pin)
    return pin


def check_sources(root: Path, gnn: Path, pin: dict[str, Any]) -> list[str]:
    errors = []
    if pin.get("schema_version") != 1:
        errors.append("unsupported source pin schema")
    for key, checkout in (("fep_lean", root), ("gnn", gnn)):
        entry = pin.get(key)
        if (
            not isinstance(entry, dict)
            or not valid_commit(entry.get("commit"))
            or not isinstance(entry.get("owners"), dict)
        ):
            errors.append(f"malformed {key} source binding")
            continue
        errors.extend(
            f"{key}: {error}"
            for error in validate_binding(
                checkout, entry["owners"], owner_roster(checkout, key)
            )
        )
    return errors


def _emitter(root: Path, model: str, expected_digest: str) -> ModuleType:
    path = contained_file(root, EMITTERS[model])
    source = path.read_bytes()
    if hashlib.sha256(source).hexdigest() != expected_digest:
        raise ValueError("emitter source changed after custody validation")
    # Execute exactly the verified source, never timestamp-valid cached bytecode.
    module = ModuleType(f"bridge_{model}_emitter")
    module.__file__ = str(path)
    exec(compile(source, str(path), "exec"), module.__dict__)  # noqa: S102 -- pinned local emitter source
    return module


def projected_document(root: Path, model: str, pin: dict[str, Any]) -> str:
    if model not in EMITTERS:
        raise ValueError("unknown bridge model")
    module = _emitter(root, model, pin["fep_lean"]["owners"][EMITTERS[model]])
    document = str(
        module.build_document(pin["fep_lean"]["commit"], pin["gnn"]["commit"])
    )
    return document + (
        f"source_owners_sha256: {binding_digest(pin['fep_lean']['owners'])}\n"
        f"pipeline_owners_sha256: {binding_digest(pin['gnn']['owners'])}\n"
    )


def emit(
    root: Path, gnn: Path, model: str, *, check: bool = False, refresh: bool = False
) -> bool:
    pin = read_object(root / PIN)
    errors = check_sources(root, gnn, pin)
    if errors:
        raise ValueError("source pin is stale: " + "; ".join(errors))
    document = projected_document(root, model, pin)
    path = root / DOCUMENTS[model]
    if check:
        return path.is_file() and path.read_text(encoding="utf-8") == document
    if refresh:
        refresh_signature(path, document)
    else:
        write_text(path, document)
    return True


def _contract_body(text: str) -> str:
    return "\n".join(
        line
        for line in text.splitlines()
        if not line.startswith(("| Canonical copy |", "| Mirror copy |"))
    )


def status(root: Path, gnn: Path) -> dict[str, Any]:
    """Inspect both models and all owners. Never invoke an emitting subprocess."""
    checks: dict[str, dict[str, Any]] = {}
    try:
        pin = read_object(root / PIN)
        errors = check_sources(root, gnn, pin)
        checks["source_binding"] = {"passed": not errors, "errors": errors}
        for model in DOCUMENTS:
            fresh = emit(root, gnn, model, check=True) if not errors else False
            checks[f"{model}_freshness"] = {
                "passed": fresh,
                "status": FRESH if fresh else "STALE",
            }
    except (ValueError, OSError, KeyError, TypeError) as exc:
        checks["source_binding"] = {"passed": False, "errors": [str(exc)]}
    try:
        syntax_pin = read_object(root / SYNTAX_PIN)
        actual = fingerprint(gnn, SYNTAX_FILES)
        checks["syntax_surface"] = {
            "passed": all(actual[name] == syntax_pin.get(name) for name in SYNTAX_FILES)
        }
        checks["contract_mirror"] = {
            "passed": _contract_body((root / CONTRACT).read_text())
            == _contract_body((gnn / MIRROR).read_text())
        }
        from fep_lean.formal.manifest import FORMAL_MODULES

        drift = [
            m.resource
            for m in FORMAL_MODULES
            if (root / "src/fep_lean/formal" / m.resource).read_bytes()
            != (root / "lean/FepSketches" / m.resource).read_bytes()
        ]
        checks["formal_projection"] = {"passed": not drift, "drift": drift}
    except (ValueError, OSError, KeyError, TypeError) as exc:
        checks["contracts"] = {"passed": False, "errors": [str(exc)]}
    passed = all(check["passed"] for check in checks.values())
    return {
        "schema_version": 1,
        "status": "ok" if passed else "error",
        "checks": checks,
        "evidence_plane": "bridge source and artifact custody",
        "native_claim_ready": False,
    }


def certificate_receipt(
    root: Path, gnn: Path, results: Path, *, tolerance: float = TOLERANCE
) -> dict[str, Any]:
    """Evaluate one explicit result artifact; records agreement, never a proof."""
    pin = read_object(root / PIN)
    errors = check_sources(root, gnn, pin)
    if errors:
        raise ValueError("stale source pin: " + "; ".join(errors))
    if not emit(root, gnn, "finite", check=True):
        raise ValueError("finite document is stale")
    relative = results.resolve().relative_to(root.resolve()).as_posix()
    artifacts = fingerprint(root, [relative, DOCUMENTS["finite"]])
    payload = read_object(results)
    certificates, observations, ok = compare(payload, tolerance)
    if fingerprint(root, artifacts) != artifacts or check_sources(root, gnn, pin):
        raise ValueError("sources or artifacts changed during comparison")
    return {
        "schema_version": 1,
        "source_pin": pin,
        "artifacts": artifacts,
        "results_path": relative,
        "tolerance": tolerance,
        "policy_match": tolerance == TOLERANCE,
        "all_certificates_pass": ok,
        "certificates": certificates,
        "observations": observations,
        "evidence_plane": "numerical comparison of an identified artifact",
        "native_claim_ready": False,
        "execution_source_verified": False,
    }


def validate_certificate(root: Path, gnn: Path, receipt: dict[str, Any]) -> list[str]:
    """Recompute the whole comparison and binding; never trust a passed flag."""
    try:
        pin = read_object(root / PIN)
        if receipt.get("source_pin") != pin:
            return ["certificate source pin mismatch"]
        results = root / receipt["results_path"]
        expected = certificate_receipt(
            root, gnn, results, tolerance=receipt["tolerance"]
        )
        if (
            expected != receipt
            or not expected["all_certificates_pass"]
            or not expected["policy_match"]
        ):
            return ["certificate content, numeric result, or tolerance policy mismatch"]
        return []
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return [str(exc)]


def emit_certificate(path: Path, receipt: dict[str, Any]) -> None:
    write_json(path, receipt)
    write_text(
        path.with_suffix(".md"),
        render_markdown(
            receipt["certificates"],
            receipt["observations"],
            Path(receipt["results_path"]),
            receipt["all_certificates_pass"],
        ),
    )


# ---------------------------------------------------------------------------
# Direction 2 S7 (contract v0.5): verify-document
# ---------------------------------------------------------------------------

_VERIFY_RECEIPT_SCHEMA = 2


def _lean_escape(text: str) -> str:
    """Escape ``text`` for a Lean string literal."""
    return (
        text.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("\t", "\\t")
    )


def _lean_number(value: Any) -> str:
    """Format one numeric payload entry deterministically."""
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, int):
        return str(value)
    return repr(float(value))


def _lean_payload(name: str, value: Any) -> str:
    """Render one parameterization entry as a verbatim brace payload."""

    def render(v: Any) -> str:
        if isinstance(v, dict):
            inner = ", ".join(f"{k}: {_lean_number(x)}" for k, x in v.items())
            return "{" + inner + "}"
        if isinstance(v, (list, tuple)):
            if v and isinstance(v[0], (list, tuple, dict)):
                return "{\n  " + ", ".join(render(row) for row in v) + "\n}"
            return "{" + "(" + ", ".join(_lean_number(x) for x in v) + ")" + "}"
        return "{" + _lean_number(v) + "}"

    return render(value)


_VALUE_TYPE_LEAN = {"float": ".floatT", "int": ".intT", "bool": ".boolT"}


def _probe_sections(space: Any, declared: list[dict[str, Any]]) -> list[str]:
    """Project one extracted POMDP state space onto ``GnnSection`` values.

    Mirrors the frozen 13-kind inventory in canonical rank order; optional
    sections are emitted only when the extracted payload carries content.
    """
    import re as _re

    def conn_edge(src: str, op: str, dst: str) -> str:
        kind = ".undirected" if op == "-" else ".directed"
        return (
            '{ src := "'
            + _lean_escape(src)
            + '", kind := '
            + kind
            + ', dst := "'
            + _lean_escape(dst)
            + '", label := none }'
        )

    def decl(var: Any) -> str:
        def attr(obj: Any, key: str, default: Any) -> Any:
            if isinstance(obj, dict):
                return obj.get(key, default)
            return getattr(obj, key, default)

        def dim(d: Any) -> str:
            text = str(d)
            if isinstance(d, int) or text.isdigit():
                return f".lit {int(d)}"
            return f'.ref "{_lean_escape(text)}"'

        dims = ", ".join(dim(d) for d in (attr(var, "dimensions", None) or [1]))
        value_type = _VALUE_TYPE_LEAN.get(
            str(attr(var, "type", attr(var, "data_type", "float"))), ".floatT"
        )
        return (
            '⟨"'
            + _lean_escape(str(attr(var, "name", "")))
            + '", ['
            + dims
            + "], "
            + value_type
            + ", none⟩"
        )

    sections: list[str] = []
    identifier = _re.sub(
        r"[^A-Za-z0-9_π']", "", space.gnn_section or space.model_name or "GNNModel"
    )
    sections.append(f'.gnnSection "{_lean_escape(identifier)}"')
    sections.append(".gnnVersionAndFlags .v1 []")
    sections.append(f'.modelName "{_lean_escape(space.model_name or identifier)}"')
    if space.model_annotation:
        sections.append(f'.modelAnnotation "{_lean_escape(space.model_annotation)}"')

    # Full StateSpaceBlock inventory: the POMDP extractor classifies only
    # state/observation/action variables, while well-formedness requires
    # every declared variable (incl. A-E matrices and F/G readouts).
    variables = declared or [
        *(space.state_variables or []),
        *(space.observation_variables or []),
        *(space.action_variables or []),
    ]
    decls = ", ".join(decl(v) for v in variables)
    sections.append(f".stateSpaceBlock [{decls}]")

    edges = ", ".join(conn_edge(s, op, d) for s, op, d in (space.connections or []))
    sections.append(f".connections [{edges}]")

    param_entries = ", ".join(
        '⟨"'
        + _lean_escape(str(var))
        + '", "'
        + _lean_escape(_lean_payload(var, payload))
        + '"⟩'
        for var, payload in sorted((space.initial_parameterization or {}).items())
    )
    sections.append(f".initialParameterization [{param_entries}]")

    bindings = ", ".join(
        '⟨"' + _lean_escape(str(var)) + '", "' + _lean_escape(str(term)) + '"⟩'
        for var, term in sorted((space.ontology_mapping or {}).items())
    )
    if bindings:
        sections.append(f".actInfOntologyAnnotation [{bindings}]")

    sections.append(
        '.footer "Verified by fep-lean bridge verify-document (contract v0.5)"'
    )
    return sections


def _probe_lean_code(space: Any, declared: list[dict[str, Any]]) -> str:
    """Build the compile-once probe that guards well-formedness."""
    sections = ",\n    ".join(_probe_sections(space, declared))
    return (
        "import FepSketches.gnn_document\n\n"
        "open FEP.GnnDocument\n\n"
        "-- bridge verify-document probe: constructed from the extracted\n"
        "-- typed payload of one emitted document (contract v0.5, S7).\n"
        "def bridgeProbeDoc : GnnDocument where\n"
        "  sections :=\n"
        "    [ " + sections + "\n"
        "    ]\n\n"
        "example : documentWellFormed bridgeProbeDoc = true := by decide\n"
    )


def verify_document(
    root: Path,
    gnn: Path,
    document: Path,
    model: str = "finite",
    receipt: Path | None = None,
    fail_on_warnings: bool = False,
) -> dict[str, Any]:
    """Verify one emitted GNN document against the ``FEP.GnnDocument`` AST.

    Direction 2 S7 (contract v0.5): extract the typed payload via the pinned
    render route, construct a ``GnnDocument`` value in a compile-once Lean
    probe, and decide ``documentWellFormed``. Proves syntax and mechanical
    well-formedness only — never ``DiscreteConforms``/``ContinuousConforms``
    (documented no-go, contract §13).
    """
    from fep_lean.verification.lean_verifier import LeanVerifier

    warnings: list[str] = []
    if model not in EMITTERS:
        raise ValueError(f"unknown model family: {model}")
    document = document.resolve()
    if not document.is_file():
        raise FileNotFoundError(f"document not found: {document}")

    document_sha = hashlib.sha256(document.read_bytes()).hexdigest()

    # Render-route extraction (pinned: gnn.extract.pomdp_extractor, strict).
    gnn_src = gnn.resolve() / "src"
    import sys as _sys

    inserted = str(gnn_src) not in _sys.path
    if inserted:
        _sys.path.insert(0, str(gnn_src))
    try:
        # Runtime-bridged imports: the GNN checkout is bound via sys.path
        # above (see RENDER_ROUTE pinning); gnn is not a fep_lean dependency.
        from gnn.extract.pomdp_extractor import (  # type: ignore[import-not-found]
            extract_pomdp_from_file,
        )
        from gnn.schema import parse_state_space  # type: ignore[import-not-found]

        space = extract_pomdp_from_file(document, strict_validation=True)
    finally:
        if inserted:
            _sys.path.remove(str(gnn_src))
    if space is None:
        raise ValueError(f"document does not extract as a POMDP: {document}")

    extracted_family = (
        "continuous"
        if getattr(space, "model_kind", "discrete") == "continuous"
        else "finite"
    )
    if extracted_family != model:
        warnings.append(
            f"model family mismatch: requested {model}, document extracts as {extracted_family}"
        )

    verifier = LeanVerifier(
        lean_dir=root.resolve() / "lean", project_root=root.resolve()
    )
    declared, _decl_errors = parse_state_space(document.read_text(encoding="utf-8"))
    result = verifier.verify_sketch(
        "bridge-verify-document", _probe_lean_code(space, declared)
    )
    if result.skip_reason:
        status = "skipped"
        warnings.append(result.skip_reason)
    elif result.compiles and not result.has_sorry:
        status = "ok"
    else:
        status = "failed"
    if fail_on_warnings and warnings:
        status = "failed"

    payload: dict[str, Any] = {
        "schema_version": _VERIFY_RECEIPT_SCHEMA,
        "document": document_sha,
        "model_family": model,
        "extracted_family": extracted_family,
        "toolchain": {"lean": result.lean_version},
        "status": status,
        "warnings": warnings,
    }
    if receipt is not None:
        write_json(receipt, payload)
    return payload
