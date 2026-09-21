"""Bridge v0.5 verify-document: roster glob, orchestration, and well-formedness."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from collections.abc import Iterator
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest

from fep_lean.bridge import cli, operations

REPO = Path(__file__).resolve().parents[1]
GNN_ROOT = REPO.parent / "GeneralizedNotationNotation"
LEAN_READY = bool(shutil.which("lake")) and (REPO / "lean" / "lakefile.lean").is_file()


def test_owner_roster_gnn_glob() -> None:
    """Every GNN owner path must live under the renamed src/gnn/ layout."""
    roster = operations.owner_roster(REPO, "gnn")
    assert roster, "roster must not be empty"
    assert "src/gnn/main.py" in roster
    assert operations.MIRROR in roster
    assert "docs/gnn/gnn_syntax.md" in roster
    assert "src/gnn/pipeline/step_registry.py" in roster
    fixed = {
        "pyproject.toml",
        "uv.lock",
        "src/gnn/main.py",
        operations.MIRROR,
        "docs/gnn/gnn_syntax.md",
        "src/gnn/pipeline/step_registry.py",
    }
    for path in set(roster) - fixed:
        assert path.startswith("src/gnn/"), f"stale owner path: {path}"


def test_roster_matches_renamed_tree() -> None:
    """Roster stays in lockstep with the tree (no stale or missing owners)."""
    roster = set(operations.owner_roster(REPO, "gnn"))
    on_disk = {
        p.relative_to(REPO).as_posix()
        for p in (REPO / "src" / "gnn").rglob("*.py")
        if "__pycache__" not in p.parts
    }
    on_disk |= {
        "pyproject.toml",
        "uv.lock",
        "src/gnn/main.py",
        operations.MIRROR,
        "docs/gnn/gnn_syntax.md",
        "src/gnn/pipeline/step_registry.py",
    }
    assert roster == on_disk


@pytest.mark.skipif(
    not (LEAN_READY and GNN_ROOT.is_dir()),
    reason="Lean toolchain or GNN checkout unavailable",
)
@pytest.mark.parametrize(
    "document, family",
    [
        (
            GNN_ROOT / "input/gnn_files/discrete/actinf_pomdp_agent.md",
            "finite",
        ),
        (
            GNN_ROOT / "input/gnn_files/continuous/continuous_navigation.md",
            "continuous",
        ),
    ],
)
def test_verify_document_well_formed(
    tmp_path: Path, document: Path, family: str
) -> None:
    receipt_path = tmp_path / "receipt.json"
    receipt = operations.verify_document(
        REPO,
        GNN_ROOT,
        document,
        model=family,
        receipt=receipt_path,
    )
    assert receipt["schema_version"] == 2
    assert receipt["status"] == "ok", receipt["warnings"]
    assert receipt["extracted_family"] == family
    assert receipt_path.is_file()
    assert json.loads(receipt_path.read_text())["status"] == "ok"


def test_verify_document_rejects_unknown_family(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="unknown model family"):
        operations.verify_document(
            REPO, GNN_ROOT, tmp_path / "missing.md", model="quantum"
        )


# ---------------------------------------------------------------------------
# Synthetic GNN checkout: the real dependency is a full sibling GNN
# repository, which CI's python lane and fresh worktrees do not have. The
# minimal stdlib stand-in keeps the verify-document orchestration and the
# Lean-probe construction testable without that checkout.
# ---------------------------------------------------------------------------

_STUB_EXTRACTOR = r'''"""Minimal stdlib stand-in for gnn.extract.pomdp_extractor.

Fixture only: parses the fixture document dialect (GNNSection, ModelName,
ModelAnnotation, StateSpaceBlock, Connections) well enough to drive the
bridge's verify-document orchestration without a GNN sibling checkout.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional


@dataclass
class POMDPStateSpace:
    model_name: str = ""
    gnn_section: Optional[str] = None
    model_annotation: Optional[str] = None
    model_kind: str = "discrete"
    state_variables: Optional[list] = None
    observation_variables: Optional[list] = None
    action_variables: Optional[list] = None
    connections: Optional[list] = None
    ontology_mapping: Optional[dict] = None
    initial_parameterization: Optional[dict] = None


def _sections(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    current: str | None = None
    for line in text.splitlines():
        if line.startswith("## "):
            current = line[3:].strip()
            out[current] = ""
        elif current is not None:
            out[current] += line + "\n"
    return out


_VARIABLE_RE = re.compile(r"([A-Za-z_]\w*)\s*\[(\d+)\](?:\s+(\w+))?")
_CONNECTION_RE = re.compile(r"(\w+)\s*(->|-)\s*(\w+)")


def extract_pomdp_from_file(
    file_path: Any,
    strict_validation: bool = True,
    on_error: str = "lenient",
    insert_default_c: bool = True,
) -> Optional[POMDPStateSpace]:
    """Extract one document under the pinned render route's strict default."""
    text = Path(file_path).read_text(encoding="utf-8")
    parts = _sections(text)
    if "StateSpaceBlock" not in parts:
        return None
    section = parts.get("GNNSection", "").strip() or None
    variables: list[dict[str, Any]] = []
    for line in parts["StateSpaceBlock"].splitlines():
        match = _VARIABLE_RE.match(line.strip())
        if match:
            variables.append(
                {
                    "name": match.group(1),
                    "dimensions": [int(match.group(2))],
                    "type": (match.group(3) or "float").lower(),
                }
            )
    connections = []
    for line in parts.get("Connections", "").splitlines():
        match = _CONNECTION_RE.match(line.strip())
        if match:
            connections.append((match.group(1), match.group(2), match.group(3)))
    return POMDPStateSpace(
        model_name=parts.get("ModelName", "").strip() or "",
        gnn_section=section,
        model_annotation=parts.get("ModelAnnotation", "").strip() or None,
        model_kind=(
            "continuous"
            if section and "continuous" in section.lower()
            else "discrete"
        ),
        state_variables=[v for v in variables if v["name"].startswith("s_")],
        observation_variables=[v for v in variables if v["name"].startswith("o_")],
        action_variables=[v for v in variables if v["name"].startswith("a_")],
        connections=connections or None,
    )
'''

_STUB_SCHEMA = r'''"""Minimal stdlib stand-in for gnn.schema (fixture only)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class GNNVariable:
    name: str
    dimensions: list[Any] = field(default_factory=list)
    type: str = "float"


@dataclass
class GNNParseError:
    code: str
    message: str
    line: Optional[int] = None


_VARIABLE_RE = re.compile(r"([A-Za-z_]\w*)\s*\[([^\]]+)\]")


def parse_state_space(content: str, *, file_path: Optional[str] = None):
    """Parse the StateSpaceBlock section; returns (variables, errors)."""
    variables: list[GNNVariable] = []
    errors: list[GNNParseError] = []
    in_block = False
    for raw in content.splitlines():
        line = raw.strip()
        if line.startswith("## "):
            in_block = line[3:].strip() == "StateSpaceBlock"
            continue
        if not in_block or not line or line.startswith("#"):
            continue
        if "#" in line:
            line = line[: line.index("#")].strip()
        match = _VARIABLE_RE.match(line)
        if not match:
            continue
        dims = [
            int(part) if part.strip().isdigit() else part.strip()
            for part in match.group(2).split(",")
        ]
        variables.append(GNNVariable(name=match.group(1), dimensions=dims))
    return variables, errors
'''

_GNN_STUB_PACKAGE: dict[str, str] = {
    "src/gnn/__init__.py": "",
    "src/gnn/extract/__init__.py": "",
    "src/gnn/extract/pomdp_extractor.py": _STUB_EXTRACTOR,
    "src/gnn/schema/__init__.py": _STUB_SCHEMA,
}

FINITE_DOCUMENT = (
    "## GNNSection\n"
    "ActInfPOMDP\n"
    "\n"
    "## ModelName\n"
    "Symmetric Bool POMDP\n"
    "\n"
    "## ModelAnnotation\n"
    "Active Inference\n"
    "\n"
    "## StateSpaceBlock\n"
    "s_f [1] State\n"
    "o_f [1] Observation\n"
    "a_f [1] Action\n"
    "\n"
    "## Connections\n"
    "s_f -> o_f\n"
    "a_f - s_f\n"
)
CONTINUOUS_DOCUMENT = FINITE_DOCUMENT.replace("ActInfPOMDP", "ActInfPOMDPContinuous")
NOT_POMDP_DOCUMENT = "## ModelName\nNot A Pomdp\n"


def _drop_gnn_modules() -> dict[str, ModuleType]:
    """Drop cached ``gnn*`` modules so the stand-in imports fresh."""
    saved = {
        name: module
        for name, module in sys.modules.items()
        if name == "gnn" or name.startswith("gnn.")
    }
    for name in saved:
        del sys.modules[name]
    return saved


@pytest.fixture
def gnn_stub(tmp_path: Path) -> Iterator[Path]:
    """A checkout whose ``src/gnn`` is a minimal stdlib stand-in.

    Mirrors the ``pair`` fixture philosophy (no installed sibling required)
    for the extraction seam that ``verify_document`` binds at runtime.
    Import caches are restored afterwards so sibling-backed tests keep
    working.
    """
    gnn_root = tmp_path / "gnn"
    for relative, content in _GNN_STUB_PACKAGE.items():
        path = gnn_root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    saved = _drop_gnn_modules()
    try:
        yield gnn_root
    finally:
        _drop_gnn_modules()
        sys.modules.update(saved)


def _write_document(root: Path, name: str, text: str) -> Path:
    path = root / name
    path.write_text(text, encoding="utf-8")
    return path


def test_verify_document_missing_document_fails_before_verification(
    tmp_path: Path, gnn_stub: Path
) -> None:
    receipt_path = tmp_path / "receipt.json"
    with pytest.raises(FileNotFoundError, match="document not found"):
        operations.verify_document(
            tmp_path, gnn_stub, tmp_path / "absent.md", receipt=receipt_path
        )
    assert not receipt_path.exists()


def test_verify_document_rejects_document_without_pomdp_payload(
    tmp_path: Path, gnn_stub: Path
) -> None:
    document = _write_document(tmp_path, "not_pomdp.md", NOT_POMDP_DOCUMENT)
    receipt_path = tmp_path / "receipt.json"
    with pytest.raises(ValueError, match="does not extract as a POMDP"):
        operations.verify_document(tmp_path, gnn_stub, document, receipt=receipt_path)
    assert not receipt_path.exists()


def test_verify_document_skips_without_lean_workspace(
    tmp_path: Path, gnn_stub: Path
) -> None:
    """No lean workspace under the checkout root: skip, recorded as warning."""
    document = _write_document(tmp_path, "finite.md", FINITE_DOCUMENT)
    receipt_path = tmp_path / "receipt.json"
    receipt = operations.verify_document(
        tmp_path, gnn_stub, document, receipt=receipt_path
    )
    assert receipt["schema_version"] == 2
    assert receipt["status"] == "skipped"
    assert receipt["model_family"] == "finite"
    assert receipt["extracted_family"] == "finite"
    assert receipt["document"] == hashlib.sha256(document.read_bytes()).hexdigest()
    assert receipt["toolchain"]["lean"]
    assert receipt["warnings"], "verifier skip must be recorded as a warning"
    assert all("family mismatch" not in warning for warning in receipt["warnings"])
    assert json.loads(receipt_path.read_text(encoding="utf-8"))["status"] == "skipped"


def test_verify_document_reports_family_mismatch_as_warning(
    tmp_path: Path, gnn_stub: Path
) -> None:
    document = _write_document(tmp_path, "continuous.md", CONTINUOUS_DOCUMENT)
    receipt = operations.verify_document(tmp_path, gnn_stub, document, model="finite")
    assert receipt["model_family"] == "finite"
    assert receipt["extracted_family"] == "continuous"
    assert receipt["status"] == "skipped"
    mismatches = [w for w in receipt["warnings"] if "family mismatch" in w]
    assert len(mismatches) == 1
    assert "requested finite" in mismatches[0]


def test_verify_document_matching_family_has_no_mismatch_warning(
    tmp_path: Path, gnn_stub: Path
) -> None:
    document = _write_document(tmp_path, "continuous.md", CONTINUOUS_DOCUMENT)
    receipt = operations.verify_document(
        tmp_path, gnn_stub, document, model="continuous"
    )
    assert receipt["extracted_family"] == "continuous"
    assert all("family mismatch" not in warning for warning in receipt["warnings"])


def test_verify_document_fail_on_warnings_fails_closed(
    tmp_path: Path, gnn_stub: Path
) -> None:
    document = _write_document(tmp_path, "continuous.md", CONTINUOUS_DOCUMENT)
    receipt = operations.verify_document(
        tmp_path, gnn_stub, document, model="finite", fail_on_warnings=True
    )
    assert receipt["status"] == "failed"
    assert any("family mismatch" in warning for warning in receipt["warnings"])


def _declared_space(**overrides: object) -> SimpleNamespace:
    fields: dict[str, object] = {
        "model_name": "Symmetric Bool POMDP",
        "gnn_section": "ActInf POMDP!",
        "model_annotation": "Active Inference",
        "state_variables": [{"name": "s_f", "dimensions": [1], "type": "float"}],
        "observation_variables": [{"name": "o_f", "dimensions": [2], "type": "int"}],
        "action_variables": [{"name": "a_f", "dimensions": ["N"], "type": "bool"}],
        "connections": [("s_f", "->", "o_f"), ("a_f", "-", "s_f")],
        "initial_parameterization": {"b": 1, "a": 2.5},
        "ontology_mapping": {"s_f": "state"},
    }
    fields.update(overrides)
    return SimpleNamespace(**fields)


def test_probe_sections_projects_the_frozen_inventory() -> None:
    sections = operations._probe_sections(_declared_space(), [])
    joined = "\n".join(sections)
    assert '.gnnSection "ActInfPOMDP"' in joined
    assert '.modelName "Symmetric Bool POMDP"' in joined
    assert '.modelAnnotation "Active Inference"' in joined
    assert ".gnnVersionAndFlags .v1 []" in joined
    assert '.footer "Verified by fep-lean bridge verify-document' in joined
    state_block = next(s for s in sections if s.startswith(".stateSpaceBlock"))
    assert '"s_f", [.lit 1], .floatT' in state_block
    assert '"o_f", [.lit 2], .intT' in state_block
    assert '"a_f", [.ref "N"], .boolT' in state_block
    connections = next(s for s in sections if s.startswith(".connections"))
    assert ".directed" in connections
    assert ".undirected" in connections
    assert 'src := "s_f"' in connections
    assert 'dst := "o_f"' in connections
    parameterization = next(
        s for s in sections if s.startswith(".initialParameterization")
    )
    assert parameterization.index('⟨"a"') < parameterization.index('⟨"b"')
    assert any(s.startswith(".actInfOntologyAnnotation") for s in sections)


def test_probe_sections_omits_optional_sections_without_content() -> None:
    space = _declared_space(
        model_annotation=None,
        ontology_mapping=None,
        initial_parameterization=None,
        connections=None,
        gnn_section=None,
    )
    sections = operations._probe_sections(space, [])
    joined = "\n".join(sections)
    assert '.gnnSection "SymmetricBoolPOMDP"' in joined
    assert not any(s.startswith(".modelAnnotation") for s in sections)
    assert not any(s.startswith(".actInfOntologyAnnotation") for s in sections)
    assert ".initialParameterization []" in joined
    assert ".connections []" in joined
    state_block = next(s for s in sections if s.startswith(".stateSpaceBlock"))
    assert '"s_f"' in state_block


@pytest.mark.parametrize(
    "overrides, expected",
    [
        ({"gnn_section": None}, '"SymmetricBoolPOMDP"'),
        ({"gnn_section": None, "model_name": ""}, '"GNNModel"'),
        ({"gnn_section": "ActInf POMDP!"}, '"ActInfPOMDP"'),
    ],
)
def test_probe_sections_identifier_fallback(
    overrides: dict[str, object], expected: str
) -> None:
    space = _declared_space(**overrides)
    assert f".gnnSection {expected}" in "\n".join(operations._probe_sections(space, []))


def test_probe_sections_prefers_declared_variables() -> None:
    declared = [{"name": "d_1", "dimensions": [3], "type": "int"}]
    sections = operations._probe_sections(_declared_space(), declared)
    state_block = next(s for s in sections if s.startswith(".stateSpaceBlock"))
    assert '"d_1", [.lit 3]' in state_block
    assert '"s_f"' not in state_block


def test_lean_escape_renders_lean_string_literals() -> None:
    assert operations._lean_escape('a"b\\c\nd\te\rf') == 'a\\"b\\\\c\\nd\\te\\rf'


@pytest.mark.parametrize(
    "value, expected",
    [(True, "True"), (False, "False"), (3, "3"), (0.5, "0.5")],
)
def test_lean_number_renders_bools_before_ints(value: object, expected: str) -> None:
    assert operations._lean_number(value) == expected


def test_lean_payload_renders_scalars_rows_and_maps() -> None:
    assert operations._lean_payload("p", 0.5) == "{0.5}"
    assert operations._lean_payload("p", (1, 2)) == "{(1, 2)}"
    assert operations._lean_payload("p", {"a": 1, "b": 2}) == "{a: 1, b: 2}"
    rows = operations._lean_payload("p", [(1, 2), (3, 4)])
    assert rows.startswith("{\n  ")
    assert rows.endswith("\n}")
    assert "(1, 2)" in rows and "(3, 4)" in rows


def test_probe_lean_code_is_a_compile_once_decide_probe() -> None:
    space = _declared_space()
    declared = [
        {"name": "s_f", "dimensions": [1], "type": "float"},
        {"name": "o_f", "dimensions": [2], "type": "int"},
        {"name": "a_f", "dimensions": ["N"], "type": "bool"},
    ]
    code = operations._probe_lean_code(space, declared)
    assert code.startswith("import FepSketches.gnn_document\n")
    assert "open FEP.GnnDocument\n" in code
    assert "def bridgeProbeDoc : GnnDocument where" in code
    assert "example : documentWellFormed bridgeProbeDoc = true := by decide" in code
    for section in operations._probe_sections(space, declared):
        assert section in code


def _cli_namespace(gnn_root: Path, *extra: str) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    cli.add_arguments(parser)
    return parser.parse_args(["verify-document", "--gnn-root", str(gnn_root), *extra])


def test_cli_verify_document_requires_document(
    tmp_path: Path, gnn_stub: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert cli.run(tmp_path, _cli_namespace(gnn_stub)) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "error"
    assert "--document" in payload["error"]


def test_cli_verify_document_missing_file_errors_without_receipt(
    tmp_path: Path, gnn_stub: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    receipt_path = tmp_path / "receipt.json"
    document = tmp_path / "absent.md"
    assert (
        cli.run(
            tmp_path,
            _cli_namespace(
                gnn_stub, "--document", str(document), "--receipt", str(receipt_path)
            ),
        )
        == 1
    )
    assert json.loads(capsys.readouterr().out)["status"] == "error"
    assert not receipt_path.exists()


def test_cli_verify_document_skip_is_not_success(
    tmp_path: Path, gnn_stub: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A skipped verification is fail-closed: exit 1, never exit 0."""
    document = _write_document(tmp_path, "finite.md", FINITE_DOCUMENT)
    receipt_path = tmp_path / "receipt.json"
    assert (
        cli.run(
            tmp_path,
            _cli_namespace(
                gnn_stub, "--document", str(document), "--receipt", str(receipt_path)
            ),
        )
        == 1
    )
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "skipped"
    assert payload["receipt"]["status"] == "skipped"
    assert json.loads(receipt_path.read_text(encoding="utf-8"))["status"] == "skipped"


def test_cli_verify_document_fail_on_warnings_fails_closed(
    tmp_path: Path, gnn_stub: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    document = _write_document(tmp_path, "continuous.md", CONTINUOUS_DOCUMENT)
    assert (
        cli.run(
            tmp_path,
            _cli_namespace(
                gnn_stub,
                "--document",
                str(document),
                "--model",
                "finite",
                "--fail-on-warnings",
            ),
        )
        == 1
    )
    payload = json.loads(capsys.readouterr().out)
    assert payload["receipt"]["status"] == "failed"
    assert any("family mismatch" in w for w in payload["receipt"]["warnings"])
