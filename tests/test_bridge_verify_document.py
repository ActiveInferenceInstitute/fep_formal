"""Bridge v0.5 verify-document: roster glob + end-to-end well-formedness."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from fep_lean.bridge import operations

REPO = Path(__file__).resolve().parents[1]
GNN_ROOT = REPO.parent / "GeneralizedNotationNotation"
LEAN_READY = bool(shutil.which("lake")) and (REPO / "lean" / "lakefile.lean").is_file()


def test_owner_roster_gnn_glob() -> None:
    """Every GNN owner path must live under the renamed src/gnn/ layout."""
    roster = operations.owner_roster(REPO, "gnn")
    assert roster, "roster must not be empty"
    assert "src/gnn/main.py" in roster
    assert operations.MIRROR in roster
    assert "doc/gnn/gnn_syntax.md" in roster
    assert "src/gnn/pipeline/step_registry.py" in roster
    fixed = {"pyproject.toml", "uv.lock", "src/gnn/main.py", operations.MIRROR,
             "doc/gnn/gnn_syntax.md", "src/gnn/pipeline/step_registry.py"}
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
        "doc/gnn/gnn_syntax.md",
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
    import json

    assert json.loads(receipt_path.read_text())["status"] == "ok"


def test_verify_document_rejects_unknown_family(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="unknown model family"):
        operations.verify_document(
            REPO, GNN_ROOT, tmp_path / "missing.md", model="quantum"
        )
