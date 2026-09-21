"""Bridge v0.5 verify-document: offline contract coverage + roster globs.

The verify_document family (operations.py, contract v0.5 Direction 2 S7) is
covered offline against a synthetic ``gnn`` package and synthetic documents
under tmp_path — the ``pair``-fixture pattern proven in
test_gnn_bridge_operations.py — so the contract pins hold in fresh worktrees
without the GeneralizedNotationNotation sibling checkout. The sibling-gated
end-to-end test (real extractor, real Lean compile) is retained as extra
integration coverage for environments that have the checkout and toolchain.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest

from fep_lean.bridge import operations
from fep_lean.verification.lean_verifier import VerifyResult

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


# ---------------------------------------------------------------------------
# Offline verify_document contract (synthetic gnn package + documents)
# ---------------------------------------------------------------------------

_GNN_SCHEMA_SOURCE = '''\
"""Fixture stand-in for ``gnn.schema`` implementing the pinned interface."""

from __future__ import annotations

from typing import Any


def fixture_fields(text: str) -> dict[str, str]:
    """Parse the fixture document grammar: one ``key: value`` line per key."""
    fields: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip()
    return fields


def parse_state_space(text: str) -> tuple[list[dict[str, Any]], list[str]]:
    """Parse the ``variables`` inventory: ``name:dims:type`` entries."""
    declared: list[dict[str, Any]] = []
    errors: list[str] = []
    for entry in fixture_fields(text).get("variables", "").split():
        parts = entry.split(":")
        if len(parts) != 3:
            errors.append(f"malformed variable entry: {entry}")
            continue
        name, dims, kind = parts
        declared.append(
            {
                "name": name,
                "dimensions": [int(d) for d in dims.split("x")],
                "type": kind,
            }
        )
    return declared, errors
'''

_GNN_EXTRACTOR_SOURCE = '''\
"""Fixture stand-in for ``gnn.extract.pomdp_extractor`` (pinned render route)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from gnn.schema import fixture_fields


class FixtureSpace:
    """Attribute surface verify_document consumes from the extracted payload."""

    def __init__(self, **fields: Any) -> None:
        self.__dict__.update(fields)


def _split_entries(raw: str) -> list[str]:
    return [entry.strip() for entry in raw.split(";") if entry.strip()]


def extract_pomdp_from_file(path: Path, strict_validation: bool = False) -> Any:
    """Extract the fixture payload; ``None`` on strict-validation failure."""
    fields = fixture_fields(Path(path).read_text(encoding="utf-8"))
    required = ("model_kind", "states", "variables", "connections")
    if strict_validation and any(key not in fields for key in required):
        return None
    connections: list[tuple[str, str, str]] = []
    for edge in _split_entries(fields.get("connections", "")):
        parts = edge.split()
        if len(parts) == 3:
            connections.append((parts[0], parts[1], parts[2]))
    parameterization: dict[str, Any] = {}
    for entry in _split_entries(fields.get("initial_parameterization", "")):
        name, sep, payload = entry.partition("=")
        if sep:
            parameterization[name.strip()] = json.loads(payload)
    ontology: dict[str, str] = {}
    for entry in _split_entries(fields.get("ontology_mapping", "")):
        name, sep, term = entry.partition("=")
        if sep:
            ontology[name.strip()] = term.strip()
    return FixtureSpace(
        gnn_section=fields.get("gnn_section", ""),
        model_name=fields.get("model_name", ""),
        model_annotation=fields.get("model_annotation", ""),
        model_kind=fields.get("model_kind", "discrete"),
        state_variables=fields.get("states", "").split(),
        observation_variables=fields.get("observations", "").split(),
        action_variables=fields.get("actions", "").split(),
        connections=connections,
        initial_parameterization=parameterization,
        ontology_mapping=ontology,
    )
'''

FINITE_DOCUMENT = """\
# fixture gnn document: finite POMDP
gnn_section: DemoPomdp
model_name: DemoPomdp
model_annotation: offline fixture model
model_kind: finite
variables: s1:2:float s2:2x2:float o1:3:int a1:1:bool
states: s1 s2
observations: o1
actions: a1
connections: s1 - s2; s1 -> o1; a1 -> s1
initial_parameterization: s1={"mu": 0.25}; s2=[[0.25, 0.75], [0.5, 0.5]]; a1=3
ontology_mapping: s1=state
"""

CONTINUOUS_DOCUMENT = """\
# fixture gnn document: continuous SDE model
gnn_section: ContinuousNav
model_name: ContinuousNav
model_annotation: continuous fixture model
model_kind: continuous
variables: x:1:float v:1:float u:1:float
states: x
observations: v
actions: u
connections: x -> v; u -> x
initial_parameterization: x=[0.1, 0.2]
ontology_mapping: x=state
"""


@pytest.fixture
def offline_pair(tmp_path: Path) -> Iterator[tuple[Path, Path]]:
    """Synthetic fep_lean root + gnn checkout; no sibling repo is required.

    Follows the proven ``pair`` pattern from test_gnn_bridge_operations.py:
    tiny tmp_path checkouts instead of the real sibling. The fixture ``gnn``
    package implements the pinned extraction interface verify_document binds
    via sys.path at ``<gnn>/src``. ``root/lean`` carries no lakefile, so the
    real LeanVerifier skips deterministically when it is not stubbed.
    """
    root = tmp_path / "fep"
    gnn = tmp_path / "gnn"
    (root / "lean").mkdir(parents=True)
    src = gnn / "src"
    for relative, body in (
        ("gnn/schema.py", _GNN_SCHEMA_SOURCE),
        ("gnn/extract/pomdp_extractor.py", _GNN_EXTRACTOR_SOURCE),
    ):
        path = src / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
    for package in ("gnn", "gnn/extract"):
        (src / package / "__init__.py").write_text("", encoding="utf-8")
    # verify_document imports the checkout modules and leaves them in
    # sys.modules; bind every test to its own checkout and restore the
    # pre-fixture import state afterwards (sibling-gated tests import the
    # real package and must never see these stand-ins).
    saved = {
        name: sys.modules[name]
        for name in list(sys.modules)
        if name == "gnn" or name.startswith("gnn.")
    }
    for name in saved:
        del sys.modules[name]
    yield root, gnn
    for name in [n for n in sys.modules if n == "gnn" or n.startswith("gnn.")]:
        del sys.modules[name]
    sys.modules.update(saved)


def write_document(tmp_path: Path, text: str) -> Path:
    """Write one synthetic GNN input document under tmp_path."""
    path = tmp_path / "documents" / "model.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def stub_verifier(
    monkeypatch: pytest.MonkeyPatch,
    *,
    compiles: bool = True,
    has_sorry: bool = False,
    skip_reason: str = "",
) -> None:
    """Replace LeanVerifier with a deterministic stand-in.

    verify_document imports LeanVerifier inside the call, so patching the
    module attribute is picked up on every invocation.
    """
    from fep_lean.verification import lean_verifier as lean_verifier_module

    class StubVerifier:
        def __init__(self, lean_dir: Path, project_root: Path | None = None) -> None:
            self.lean_dir = lean_dir
            self.project_root = project_root

        def verify_sketch(self, topic_id: str, lean_code: str) -> VerifyResult:
            return VerifyResult(
                topic_id=topic_id,
                compiles=compiles,
                has_sorry=has_sorry,
                lean_version="stub",
                skip_reason=skip_reason,
            )

    monkeypatch.setattr(lean_verifier_module, "LeanVerifier", StubVerifier)


def test_verify_document_offline_passes_finite(
    tmp_path: Path,
    offline_pair: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A finite document verifies clean and writes a schema-2 receipt."""
    root, gnn = offline_pair
    document = write_document(tmp_path, FINITE_DOCUMENT)
    receipt_path = tmp_path / "receipt.json"
    stub_verifier(monkeypatch)
    receipt = operations.verify_document(
        root, gnn, document, model="finite", receipt=receipt_path
    )
    assert set(receipt) == {
        "schema_version",
        "document",
        "model_family",
        "extracted_family",
        "toolchain",
        "status",
        "warnings",
    }
    assert receipt["schema_version"] == 2
    assert receipt["status"] == "ok", receipt["warnings"]
    assert receipt["warnings"] == []
    assert receipt["model_family"] == "finite"
    assert receipt["extracted_family"] == "finite"
    assert receipt["document"] == hashlib.sha256(document.read_bytes()).hexdigest()
    assert json.loads(receipt_path.read_text(encoding="utf-8")) == receipt


def test_verify_document_offline_passes_continuous_with_matching_model(
    tmp_path: Path,
    offline_pair: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Continuous documents verify only under the continuous model family."""
    root, gnn = offline_pair
    document = write_document(tmp_path, CONTINUOUS_DOCUMENT)
    stub_verifier(monkeypatch)
    receipt = operations.verify_document(root, gnn, document, model="continuous")
    assert receipt["status"] == "ok", receipt["warnings"]
    assert receipt["warnings"] == []
    assert receipt["model_family"] == "continuous"
    assert receipt["extracted_family"] == "continuous"


def test_verify_document_offline_family_mismatch_warns(
    tmp_path: Path,
    offline_pair: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Requesting the wrong family warns but still verifies (default policy)."""
    root, gnn = offline_pair
    document = write_document(tmp_path, CONTINUOUS_DOCUMENT)
    stub_verifier(monkeypatch)
    receipt = operations.verify_document(root, gnn, document)
    assert receipt["status"] == "ok"
    assert receipt["warnings"] == [
        "model family mismatch: requested finite, document extracts as continuous"
    ]
    assert receipt["extracted_family"] == "continuous"
    # verification stays side-effect free unless a receipt path is given
    assert not list(tmp_path.rglob("*.json"))


def test_verify_document_offline_fail_on_warnings_fails(
    tmp_path: Path,
    offline_pair: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """fail_on_warnings flips a warned verification to failed (fail closed)."""
    root, gnn = offline_pair
    document = write_document(tmp_path, CONTINUOUS_DOCUMENT)
    stub_verifier(monkeypatch)
    receipt = operations.verify_document(root, gnn, document, fail_on_warnings=True)
    assert receipt["status"] == "failed"
    assert receipt["warnings"], "the flipped status must be traceable"
    assert "model family mismatch" in receipt["warnings"][0]


@pytest.mark.parametrize(
    ("compiles", "has_sorry"),
    [(False, False), (True, True)],
    ids=["compile-error", "compiles-with-sorry"],
)
def test_verify_document_offline_verifier_failures(
    tmp_path: Path,
    offline_pair: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
    compiles: bool,
    has_sorry: bool,
) -> None:
    """A probe that does not compile cleanly fails the document."""
    root, gnn = offline_pair
    document = write_document(tmp_path, FINITE_DOCUMENT)
    stub_verifier(monkeypatch, compiles=compiles, has_sorry=has_sorry)
    receipt = operations.verify_document(root, gnn, document, model="finite")
    assert receipt["status"] == "failed"
    assert receipt["warnings"] == []


def test_verify_document_offline_skips_without_lean_workspace(
    tmp_path: Path,
    offline_pair: tuple[Path, Path],
) -> None:
    """Without a Lean workspace the document is skipped, never a silent pass."""
    root, gnn = offline_pair  # root/lean exists but has no lakefile.lean
    document = write_document(tmp_path, FINITE_DOCUMENT)
    receipt = operations.verify_document(root, gnn, document, model="finite")
    assert receipt["status"] == "skipped"
    assert receipt["warnings"], "the skip reason must be recorded"
    assert receipt["schema_version"] == 2
    assert receipt["extracted_family"] == "finite"


def test_verify_document_offline_rejects_unknown_family(
    tmp_path: Path,
    offline_pair: tuple[Path, Path],
) -> None:
    root, gnn = offline_pair
    with pytest.raises(ValueError, match="unknown model family"):
        operations.verify_document(root, gnn, tmp_path / "missing.md", model="quantum")


def test_verify_document_offline_missing_document_raises(
    tmp_path: Path,
    offline_pair: tuple[Path, Path],
) -> None:
    root, gnn = offline_pair
    with pytest.raises(FileNotFoundError, match="document not found"):
        operations.verify_document(
            root, gnn, tmp_path / "documents" / "absent.md", model="finite"
        )


def test_verify_document_offline_rejects_non_pomdp_document(
    tmp_path: Path,
    offline_pair: tuple[Path, Path],
) -> None:
    """A document the pinned extraction route cannot parse fails closed."""
    root, gnn = offline_pair
    document = write_document(tmp_path, "# not a gnn document\n")
    with pytest.raises(ValueError, match="does not extract as a POMDP"):
        operations.verify_document(root, gnn, document, model="finite")


# ---------------------------------------------------------------------------
# Sibling-gated end-to-end integration (retained: real extractor + real Lean)
# ---------------------------------------------------------------------------


@pytest.mark.serial_lean
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
