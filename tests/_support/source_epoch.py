"""Exact current-to-historical test views; never production evidence or execution."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

TRANSITION_PATH = "tests/fixtures/source_epoch_20261026.json"
TRANSITION_SHA256 = "a0a9f208c9bb721361c328c76ee093974ea9922dd1dd035ba04559872e831049"
MANIFEST = "src/fep_lean/formal/manifest.py"


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _transition(root: Path) -> dict:
    raw = (root / TRANSITION_PATH).read_bytes()
    assert _sha(raw) == TRANSITION_SHA256, "static source transition identity changed"
    data = json.loads(raw)
    assert data["kind"] == "exact-source-epoch-static-test-adapter"
    assert (
        data["native_execution"]
        is data["scientific_acceptance"]
        is data["historical_evidence_renewed"]
        is False
    )
    return data


def authenticate_h3_partition(root: Path) -> None:
    """Reconstruct the exact pre-split monolith before any historical replay."""
    partition = _transition(root)["h3_partition"]
    facade = root / partition["facade_path"]
    assert (
        not facade.is_symlink()
        and _sha(facade.read_bytes()) == partition["facade_sha256"]
    ), "H3 facade changed"
    reconstructed = partition["original_prefix"].encode()
    for part in partition["parts"]:
        path = root / part["path"]
        assert not path.is_symlink(), "H3 leaf symlink"
        raw = path.read_bytes()
        assert _sha(raw) == part["sha256"], "H3 leaf identity changed"
        prefix, suffix = part["prefix"].encode(), part["suffix"].encode()
        assert raw.startswith(prefix) and raw.endswith(suffix)
        body = raw[len(prefix) : len(raw) - len(suffix)]
        assert _sha(body) == part["body_sha256"], "H3 proof fragment changed"
        reconstructed += body
    reconstructed += partition["original_suffix"].encode()
    assert _sha(reconstructed) == partition["original_sha256"], (
        "H3 monolith reconstruction changed"
    )


def predecessor_source(root: Path, relative: str, live: bytes) -> bytes:
    """Authenticate an exact approved postimage before returning static history."""
    transition = _transition(root)
    pair = transition["pairs"][relative]
    assert _sha(live) == pair["after_sha256"], (
        f"unrecognized current source epoch: {relative}"
    )
    if relative == MANIFEST:
        authenticate_h3_partition(root)
    before = pair["before_text"].encode()
    assert len(before) == pair["before_size"] and _sha(before) == pair["before_sha256"]
    return before


def recognized_postimage(root: Path, relative: str, live: bytes) -> bool:
    """Recognize only this named transition; callers retain all other refusals."""
    return _sha(live) == _transition(root)["pairs"][relative]["after_sha256"]


def historical_h3_owner_view(declarations: dict, root: Path) -> dict:
    """Return a copied historical comparison view; never mutate live results."""
    transition = _transition(root)
    authenticate_h3_partition(root)
    moves = transition["h3_theorem_relocations"]
    current_names = {
        name for name in declarations if name.startswith("FEPComposed.H3CaseStudy.")
    }
    assert current_names == set(moves), "H3 declaration membership changed"
    result = dict(declarations)
    for name, move in moves.items():
        assert declarations[name]["source_owner"] == move["after_owner"], (
            "H3 theorem owner changed"
        )
        assert (
            _sha(declarations[name]["statement"].encode()) == move["statement_sha256"]
        ), "H3 statement changed"
        result[name] = {**declarations[name], "source_owner": move["before_owner"]}
    return result
