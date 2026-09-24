"""Evidence-fixture census tests: isolated trees, never the live specs/ tree.

Every test builds a self-contained project fixture (the
``tests/test_horizon_acceptance.py`` evidence-fixture pattern: accepted
inputs copied byte-identical, the terminal receipt's native capture re-bound
to the fixture's own live digests, then deliberate mutations), runs the
read-only census over it, and checks the FEP-H27-RESEAL reference
classification. Validation constants are imported from
``fep_lean.verification.horizon_acceptance`` — never hardcoded.
"""

from __future__ import annotations

import hashlib
import inspect
import json
import os
import shutil
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from fep_lean import custody
from fep_lean.custody import (
    GATE_EXPECTATIONS,
    INTACT,
    LIVE_RED,
    STALE,
    STATUS_VOCABULARY,
    Census,
    CensusRecord,
    Expectations,
    census,
    verify,
)
from fep_lean.custody.census import _receipt_disk_path
from fep_lean.verification import horizon_acceptance as acceptance
from fep_lean.verification.horizon_acceptance import (
    MANDATORY_TEST_FILES,
    PREDECESSORS,
    R0_SUCCESSOR,
    TERMINAL_RECEIPT,
    native_source_paths,
    source_snapshot,
)

REFERENCE_ROOT = Path(
    os.environ.get("FEP_ACCEPTANCE_REFERENCE_ROOT", Path(__file__).resolve().parents[1])
)

# FEP-H27-RESEAL (TODO.md): the terminal receipt's native_evidence
# source_before/after snapshot predates the 2026-09-21 tests-wave changes
# (commit f55d558) to exactly these four captured files.
FOUR_STALE_FILES = (
    "tests/test_horizon1_decision_risk.py",
    "tests/test_horizon1_finite_reference_agent.py",
    "tests/test_horizon1_policy_action.py",
    "tests/test_native_blanket_formalisms.py",
)

MUTATION = b"\n# custody census fixture mutation\n"


def _evidence_tree(tmp_path: Path) -> tuple[Path, Path]:
    """The isolated project root (fixture-normalized on first creation)."""
    root = tmp_path / "project"
    specs_dir = root / "specs"
    if root.is_dir():
        # The autouse fixture already built and normalized this tree; never
        # re-copy raw reference bytes over its re-bound receipts.
        return root, specs_dir
    paths = set(native_source_paths(REFERENCE_ROOT)) | set(PREDECESSORS)
    paths.add(TERMINAL_RECEIPT)
    for name in PREDECESSORS:
        receipt = json.loads((REFERENCE_ROOT / name).read_bytes())
        paths.update(receipt.get("source_sha256", {}))
    for name in sorted(paths):
        destination = root / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REFERENCE_ROOT / name, destination)
    return root, specs_dir


def _rebind_capture(root: Path) -> dict[str, str]:
    """Re-bind the fixture receipt's capture to the fixture's live digests."""
    receipt_path = root / TERMINAL_RECEIPT
    receipt = json.loads(receipt_path.read_bytes())
    native = source_snapshot(root, list(native_source_paths(root)))
    receipt["native_evidence"]["source_before"] = native
    receipt["native_evidence"]["source_after"] = native
    receipt_path.write_bytes(
        (json.dumps(receipt, sort_keys=True, indent=2) + "\n").encode()
    )
    return native


@pytest.fixture(autouse=True)
def _self_consistent_receipts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Make fixture receipts self-consistent regardless of the live tip.

    The reference tree may legitimately be mid-custody-chore (a drifted R0
    successor pin is exactly the debt this wave's tool addresses), so the
    fixtures pin their own consistent state: the successor receipt is
    rewritten from the fixture's live digests and the copied receipt's
    digest is bound into an in-process PREDECESSORS patch. Real receipt
    files are never touched.
    """
    root, _ = _evidence_tree(tmp_path)
    _rebind_capture(root)
    _rebind_successor(root)
    pins = {
        name: hashlib.sha256((root / name).read_bytes()).hexdigest()
        for name in PREDECESSORS
    }
    _edit_receipt(root, TERMINAL_RECEIPT, lambda r: r.update(predecessors=pins))
    monkeypatch.setattr(acceptance, "PREDECESSORS", pins)


def _rebind_successor(root: Path) -> None:
    """Rewrite the fixture successor receipt from the fixture's live digests."""
    successor_path = root / R0_SUCCESSOR
    successor = json.loads(successor_path.read_bytes())
    successor["source_sha256"] = source_snapshot(
        root, sorted(successor["source_sha256"])
    )
    for probe in successor["native_evidence"]["probes"]:
        probe["source_sha256"] = successor["source_sha256"]
    successor_path.write_bytes(
        (json.dumps(successor, sort_keys=True, indent=2) + "\n").encode()
    )


def _edit_receipt(
    root: Path, name: str, mutate: Callable[[dict[str, Any]], None]
) -> None:
    """Rewrite one fixture receipt through ``mutate`` (sorted, indent 2)."""
    receipt_path = root / name
    receipt = json.loads(receipt_path.read_bytes())
    mutate(receipt)
    receipt_path.write_bytes(
        (json.dumps(receipt, sort_keys=True, indent=2) + "\n").encode()
    )


def _mutate_file(root: Path, name: str) -> None:
    path = root / name
    path.write_bytes(path.read_bytes() + MUTATION)


def _capture_paths(root: Path) -> set[str]:
    receipt = json.loads((root / TERMINAL_RECEIPT).read_bytes())
    return set(receipt["native_evidence"]["source_before"])


def _record_of(tree: Census, path: str) -> CensusRecord:
    matches = [record for record in tree.records if record.path == path]
    assert len(matches) == 1, f"expected exactly one census record for {path}"
    return matches[0]


def _chain_paths() -> tuple[str, ...]:
    return (TERMINAL_RECEIPT, custody.VALIDATOR_PATH, *PREDECESSORS)


def test_reference_stale_files_are_captured_surfaces() -> None:
    """The FEP-H27-RESEAL four-file set is inside the captured native plane."""
    assert set(FOUR_STALE_FILES) <= set(MANDATORY_TEST_FILES)


def test_all_intact_census_verifies_clean(tmp_path: Path) -> None:
    """(a) A re-bound all-intact tree classifies intact and verifies ok."""
    root, specs_dir = _evidence_tree(tmp_path)
    _rebind_capture(root)
    tree = census(specs_dir, root)
    assert all(record.status == INTACT for record in tree.records)
    assert {record.path for record in tree.records} == (
        set(_chain_paths()) | _capture_paths(root)
    )
    assert tree.records[0].path == TERMINAL_RECEIPT
    assert not tree.is_gated()
    assert tree.live_red() == ()
    assert verify(tree, GATE_EXPECTATIONS) == (True, [])


def test_four_file_staleness_is_flagged_with_precise_paths(tmp_path: Path) -> None:
    """(b) The FEP-H27-RESEAL residual: stale files, intact chain, :592 red."""
    root, specs_dir = _evidence_tree(tmp_path)
    _rebind_capture(root)
    for name in FOUR_STALE_FILES:
        _mutate_file(root, name)
    tree = census(specs_dir, root)
    receipt_record = _record_of(tree, TERMINAL_RECEIPT)
    assert receipt_record.status == STALE
    assert "horizon_acceptance.py:592" in receipt_record.detail
    for name in FOUR_STALE_FILES:
        record = _record_of(tree, name)
        assert record.status == STALE
        assert "capture digest" in record.detail and "predates live" in record.detail
    for path in _chain_paths()[1:]:
        assert _record_of(tree, path).status == INTACT
    assert {STALE, INTACT, LIVE_RED} <= custody.STATUS_VOCABULARY
    assert tree.is_gated()
    assert tree.live_red() == ()
    ok, problems = verify(tree, GATE_EXPECTATIONS)
    assert ok is False
    assert {problem.split(": ", 1)[1].split(":", 1)[0] for problem in problems} == {
        TERMINAL_RECEIPT,
        *FOUR_STALE_FILES,
    }
    authorized = Expectations(
        required_intact=(custody.VALIDATOR_PATH, *PREDECESSORS),
        allowed_stale=frozenset({TERMINAL_RECEIPT, *FOUR_STALE_FILES}),
    )
    assert verify(tree, authorized) == (True, [])


def test_successor_receipt_digest_drift_fails_verify(tmp_path: Path) -> None:
    """(c) A drifted R0 successor receipt is live-red and fails the gate."""
    root, specs_dir = _evidence_tree(tmp_path)
    _rebind_capture(root)
    successor_path = root / R0_SUCCESSOR
    successor_path.write_bytes(successor_path.read_bytes() + b"\n")
    tree = census(specs_dir, root)
    successor_record = _record_of(tree, R0_SUCCESSOR)
    assert successor_record.status == LIVE_RED
    assert "receipt digest drift from PREDECESSORS pin" in successor_record.detail
    constant_record = _record_of(tree, custody.VALIDATOR_PATH)
    assert constant_record.status == LIVE_RED
    assert R0_SUCCESSOR in constant_record.detail
    for path in _chain_paths():
        if path not in (R0_SUCCESSOR, custody.VALIDATOR_PATH):
            assert _record_of(tree, path).status == INTACT
    ok, problems = verify(tree, GATE_EXPECTATIONS)
    assert ok is False
    assert any(R0_SUCCESSOR in problem for problem in problems)
    assert any(custody.VALIDATOR_PATH in problem for problem in problems)


@pytest.mark.parametrize(
    "mutate",
    [
        pytest.param(lambda r: r.update(schema_version="1"), id="schema"),
        pytest.param(lambda r: r.update(gate="H1"), id="gate"),
        pytest.param(lambda r: r.update(decision="rejected"), id="decision"),
        pytest.param(lambda r: r.update(predecessors={}), id="binding"),
        pytest.param(lambda r: r.pop("native_evidence"), id="native-evidence-missing"),
        pytest.param(
            lambda r: r["native_evidence"].update(source_before=5),
            id="source-before-malformed",
        ),
        pytest.param(
            lambda r: r["native_evidence"].update(source_after=5),
            id="source-after-malformed",
        ),
    ],
)
def test_broken_terminal_receipt_is_live_red_without_capture(
    tmp_path: Path, mutate: Callable[[dict[str, Any]], None]
) -> None:
    """Structurally broken terminal receipts classify live-red, fail closed."""
    root, specs_dir = _evidence_tree(tmp_path)
    _rebind_capture(root)
    _edit_receipt(root, TERMINAL_RECEIPT, mutate)
    tree = census(specs_dir, root)
    assert {item.path for item in tree.records} == set(_chain_paths())
    record = tree.records[0]
    assert record.path == TERMINAL_RECEIPT
    assert record.status == LIVE_RED
    ok, problems = verify(tree, GATE_EXPECTATIONS)
    assert ok is False
    assert len(problems) == 1


def test_inconsistent_capture_maps_are_live_red(tmp_path: Path) -> None:
    """source_before != source_after is the :592 inconsistent-capture red."""
    root, specs_dir = _evidence_tree(tmp_path)
    _rebind_capture(root)

    def _drift_one(receipt: dict[str, Any]) -> None:
        after = receipt["native_evidence"]["source_after"]
        key = min(after)
        after[key] = "0" * 64

    _edit_receipt(root, TERMINAL_RECEIPT, _drift_one)
    tree = census(specs_dir, root)
    assert {item.path for item in tree.records} == set(_chain_paths())
    assert tree.records[0].status == LIVE_RED
    assert "source_before != source_after" in tree.records[0].detail


def test_capture_roster_mismatch_is_live_red(tmp_path: Path) -> None:
    """A capture missing a native-plane file fails closed on the roster."""
    root, specs_dir = _evidence_tree(tmp_path)
    _rebind_capture(root)
    dropped = "tests/test_horizon1_policy_action.py"
    assert dropped in _capture_paths(root)

    def _drop_key(receipt: dict[str, Any]) -> None:
        for label in ("source_before", "source_after"):
            receipt["native_evidence"][label].pop(dropped)

    _edit_receipt(root, TERMINAL_RECEIPT, _drop_key)
    tree = census(specs_dir, root)
    assert {item.path for item in tree.records} == set(_chain_paths())
    assert tree.records[0].status == LIVE_RED
    assert "roster differs" in tree.records[0].detail


def test_missing_captured_file_fails_closed(tmp_path: Path) -> None:
    """A captured file missing from the live tree is live-red, not stale."""
    root, specs_dir = _evidence_tree(tmp_path)
    _rebind_capture(root)
    missing = "tests/test_horizon1_decision_risk.py"
    (root / missing).unlink()
    tree = census(specs_dir, root)
    record = _record_of(tree, missing)
    assert record.status == LIVE_RED
    assert "missing/unreadable" in record.detail
    receipt_record = _record_of(tree, TERMINAL_RECEIPT)
    assert receipt_record.status == LIVE_RED
    assert missing in receipt_record.detail
    intact = [
        item
        for item in tree.records
        if item.path in _capture_paths(root) and item.path != missing
    ]
    assert intact and all(item.status == INTACT for item in intact)


def test_mirror_drift_reports_the_native_plane_unavailable(tmp_path: Path) -> None:
    """A formal/mirror byte divergence fails closed before any comparison."""
    root, specs_dir = _evidence_tree(tmp_path)
    _rebind_capture(root)
    mirror = "lean/FepSketches/gaussian_information_geometry.lean"
    _mutate_file(root, mirror)
    tree = census(specs_dir, root)
    record = _record_of(tree, TERMINAL_RECEIPT)
    assert not any(item.path in _capture_paths(root) for item in tree.records)
    assert "native plane unavailable" in record.detail
    assert record.detail and tree.records[0].path == TERMINAL_RECEIPT


def test_detached_specs_dir_yields_identical_census(tmp_path: Path) -> None:
    """The receipt chain is injectable: a detached specs root censuses equal."""
    root, specs_dir = _evidence_tree(tmp_path)
    _rebind_capture(root)
    detached = tmp_path / "detached-specs"
    for name in (TERMINAL_RECEIPT, *PREDECESSORS):
        destination = detached / name[len("specs/") :]
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(root / name, destination)
    tree = census(specs_dir, root)
    detached_tree = census(detached, root)
    assert [(record.path, record.status) for record in detached_tree.records] == [
        (record.path, record.status) for record in tree.records
    ]


def test_receipt_key_outside_specs_is_rejected() -> None:
    """_receipt_disk_path fails closed on keys outside the specs/ prefix."""
    with pytest.raises(ValueError, match="receipt key outside specs/"):
        _receipt_disk_path(Path("/tmp/whatever-specs"), "elsewhere/receipt.json")


def test_missing_predecessor_receipt_is_live_red(tmp_path: Path) -> None:
    """A missing pinned predecessor receipt fails closed, chain-level red."""
    root, specs_dir = _evidence_tree(tmp_path)
    _rebind_capture(root)
    missing = next(
        path
        for path in PREDECESSORS
        if path.endswith("06a-native-filter-posterior.json")
    )
    (root / missing).unlink()
    tree = census(specs_dir, root)
    assert _record_of(tree, missing).status == LIVE_RED
    constant_record = _record_of(tree, custody.VALIDATOR_PATH)
    assert constant_record.status == LIVE_RED
    assert missing in constant_record.detail


def test_prior_receipt_digest_drift_is_live_red(tmp_path: Path) -> None:
    """A re-written predecessor receipt drifts its pin and the constant."""
    root, specs_dir = _evidence_tree(tmp_path)
    _rebind_capture(root)
    drifted = next(
        path for path in PREDECESSORS if path.endswith("05b-transition-covariance.json")
    )
    (root / drifted).write_bytes((root / drifted).read_bytes() + b"\n")
    tree = census(specs_dir, root)
    record = _record_of(tree, drifted)
    assert record.status == LIVE_RED
    assert "receipt digest drift from PREDECESSORS pin" in record.detail
    constant_record = _record_of(tree, custody.VALIDATOR_PATH)
    assert constant_record.status == LIVE_RED
    assert drifted in constant_record.detail


def test_unparseable_predecessor_receipt_is_live_red(tmp_path: Path) -> None:
    """An unparseable pinned receipt is live-red without a parse fallback."""
    root, specs_dir = _evidence_tree(tmp_path)
    _rebind_capture(root)
    broken = next(
        path for path in PREDECESSORS if path.endswith("05d-gaussian-conditioning.json")
    )
    (root / broken).write_bytes(b"{")
    tree = census(specs_dir, root)
    record = _record_of(tree, broken)
    assert record.status == LIVE_RED
    assert "predecessor receipt" in record.detail


def test_malformed_predecessor_source_map_is_live_red(tmp_path: Path) -> None:
    """A non-object source_sha256 map in a pinned receipt fails closed."""
    root, specs_dir = _evidence_tree(tmp_path)
    _rebind_capture(root)
    receipt_name = next(
        path for path in PREDECESSORS if path.endswith("05b-transition-covariance.json")
    )
    _edit_receipt(root, receipt_name, lambda r: r.update(source_sha256=5))
    tree = census(specs_dir, root)
    record = _record_of(tree, receipt_name)
    assert record.status == LIVE_RED
    assert "source_sha256 map malformed" in record.detail


def test_stale_predecessor_source_agrees_with_the_validator(
    tmp_path: Path,
) -> None:
    """Unexplained prior-source drift: census and validator both reject it."""
    root, specs_dir = _evidence_tree(tmp_path)
    _rebind_capture(root)
    drifted = "tests/test_horizon2_transition_covariance_readiness.py"
    _mutate_file(root, drifted)
    tree = census(specs_dir, root)
    record = _record_of(
        tree,
        next(
            path
            for path in PREDECESSORS
            if path.endswith("05b-transition-covariance.json")
        ),
    )
    assert record.status == LIVE_RED
    assert f"stale predecessor source: {drifted}" in record.detail
    with pytest.raises(ValueError, match="stale predecessor source"):
        acceptance._predecessors(root, acceptance.PREDECESSORS)


def test_authorized_prior_drift_matches_both_custody_sources(
    tmp_path: Path,
) -> None:
    """The restated permanent-drift pair matches its two reviewed origins."""
    root, _ = _evidence_tree(tmp_path)
    successor = json.loads((root / R0_SUCCESSOR).read_bytes())
    assert (
        tuple(successor["allowed_prior_source_changes"])
        == custody.AUTHORIZED_PRIOR_DRIFT
    )
    validator = inspect.getsource(acceptance._predecessors)
    for name in custody.AUTHORIZED_PRIOR_DRIFT:
        assert f'"{name}"' in validator


def test_manifest_drift_is_exempt_from_the_prior_and_flagged_on_the_successor(
    tmp_path: Path,
) -> None:
    """The authorized pair skips the prior 07 map, not the successor map."""
    root, specs_dir = _evidence_tree(tmp_path)
    _rebind_capture(root)
    _mutate_file(root, "src/fep_lean/formal/manifest.py")
    tree = census(specs_dir, root)
    prior_record = _record_of(
        tree,
        next(
            path
            for path in PREDECESSORS
            if path.endswith("07-gaussian-vfe-natural-gradient.json")
        ),
    )
    assert prior_record.status == INTACT
    successor_record = _record_of(tree, R0_SUCCESSOR)
    assert successor_record.status == LIVE_RED
    assert (
        "R0 successor custody digest drift: src/fep_lean/formal/manifest.py"
        in successor_record.detail
    )


@pytest.mark.parametrize(
    "mutate, expected",
    [
        pytest.param(
            lambda r: r["native_evidence"].update(status="pending"),
            "R0 current native evidence pending",
            id="status",
        ),
        pytest.param(
            lambda r: r["native_evidence"].update(historical_evidence_reused=True),
            "R0 historical execution reused",
            id="reuse",
        ),
        pytest.param(
            lambda r: r["native_evidence"].update(probes={}),
            "R0 successor probes malformed",
            id="probes-malformed",
        ),
        pytest.param(
            lambda r: r["native_evidence"].update(probes=[3]),
            "R0 probe 0 malformed",
            id="probe-malformed",
        ),
        pytest.param(
            lambda r: r["native_evidence"]["probes"][0].update(source_sha256={}),
            "R0 probe 0 source mismatch",
            id="probe-map",
        ),
        pytest.param(
            lambda r: r["native_evidence"]["probes"][0].update(pytest_exit_code=1),
            "R0 probe 0 source mismatch",
            id="probe-exit",
        ),
        pytest.param(
            lambda r: r.pop("source_sha256"),
            "R0 successor source_sha256 map missing/malformed",
            id="map-missing",
        ),
        pytest.param(
            lambda r: r["source_sha256"].update({"pyproject.toml": "0" * 64}),
            "R0 successor custody digest drift: pyproject.toml",
            id="map-drift",
        ),
        pytest.param(
            lambda r: r.pop("native_evidence"),
            "R0 successor native_evidence missing/malformed",
            id="native-evidence-missing",
        ),
    ],
)
def test_successor_custody_semantics_are_live_red(
    tmp_path: Path, mutate: Callable[[dict[str, Any]], None], expected: str
) -> None:
    """Every R0 successor custody violation classifies live-red precisely."""
    root, specs_dir = _evidence_tree(tmp_path)
    _rebind_capture(root)
    _edit_receipt(root, R0_SUCCESSOR, mutate)
    tree = census(specs_dir, root)
    record = _record_of(tree, R0_SUCCESSOR)
    assert record.status == LIVE_RED
    assert expected in record.detail


def test_verify_flags_missing_required_surfaces(tmp_path: Path) -> None:
    """A required surface absent from the census is a verify problem."""
    tree = Census(())
    ok, problems = verify(tree, GATE_EXPECTATIONS)
    assert ok is False
    assert sorted(problems) == sorted(
        f"missing from census: {path}" for path in GATE_EXPECTATIONS.required_intact
    )


def test_verify_required_beats_allowed_stale(tmp_path: Path) -> None:
    """allowed_stale never authorizes staleness on a required surface."""
    root, specs_dir = _evidence_tree(tmp_path)
    _rebind_capture(root)
    for name in FOUR_STALE_FILES:
        _mutate_file(root, name)
    tree = census(specs_dir, root)
    expectations = Expectations(
        required_intact=_chain_paths(),
        allowed_stale=frozenset({TERMINAL_RECEIPT, *FOUR_STALE_FILES}),
    )
    ok, problems = verify(tree, expectations)
    assert ok is False
    stale_problems = [
        problem for problem in problems if problem.startswith(f"{STALE}: ")
    ]
    assert [problem.split(": ")[1] for problem in stale_problems] == [TERMINAL_RECEIPT]


def test_verify_never_authorizes_live_red(tmp_path: Path) -> None:
    """live-red records fail even when their path is in allowed_stale."""
    root, specs_dir = _evidence_tree(tmp_path)
    _rebind_capture(root)
    successor_path = root / R0_SUCCESSOR
    successor_path.write_bytes(successor_path.read_bytes() + b"\n")
    tree = census(specs_dir, root)
    expectations = Expectations(
        required_intact=_chain_paths(),
        allowed_stale=frozenset({R0_SUCCESSOR}),
    )
    ok, problems = verify(tree, expectations)
    assert ok is False
    assert any(
        problem.startswith(f"{LIVE_RED}: {R0_SUCCESSOR}") for problem in problems
    )


def test_gate_expectations_require_the_whole_chain() -> None:
    """The strict gate demands the terminal receipt and every pinned chain."""
    assert set(GATE_EXPECTATIONS.required_intact) == set(_chain_paths())
    assert GATE_EXPECTATIONS.allowed_stale == frozenset()


def test_census_record_validation_is_fail_closed() -> None:
    """CensusRecord and Census reject malformed records and duplicates."""
    with pytest.raises(ValueError, match="path"):
        CensusRecord(path="", status=INTACT, detail="d")
    with pytest.raises(ValueError, match="status"):
        CensusRecord(path="p", status="unknown", detail="d")
    with pytest.raises(ValueError, match="detail"):
        CensusRecord(path="p", status=INTACT, detail="")
    with pytest.raises(ValueError, match="tuple of CensusRecord"):
        Census((CensusRecord("p", INTACT, "d"), "not-a-record"))  # type: ignore[arg-type]
    base = CensusRecord("p", INTACT, "d")
    with pytest.raises(ValueError, match="duplicate census surface"):
        Census((base, CensusRecord("p", STALE, "d")))
    tree = Census(
        (
            CensusRecord("a", INTACT, "ok"),
            CensusRecord("b", STALE, "old"),
            CensusRecord("c", LIVE_RED, "broken"),
        )
    )
    assert tree.status_of("b") == STALE
    assert tree.status_of("zz") is None
    assert [record.path for record in tree.live_red()] == ["c"]
    assert [record.path for record in tree.stale()] == ["b"]
    assert tree.is_gated() is True
    assert {INTACT, STALE, LIVE_RED} == STATUS_VOCABULARY


def test_unparseable_terminal_receipt_is_live_red(tmp_path: Path) -> None:
    """An unparseable terminal receipt fails closed before any comparison."""
    root, specs_dir = _evidence_tree(tmp_path)
    _rebind_capture(root)
    (root / TERMINAL_RECEIPT).write_bytes(b"{")
    tree = census(specs_dir, root)
    record = _record_of(tree, TERMINAL_RECEIPT)
    assert record.status == LIVE_RED
    assert "terminal receipt" in record.detail
    assert {item.path for item in tree.records} == set(_chain_paths())
    ok, problems = verify(tree, GATE_EXPECTATIONS)
    assert ok is False
    assert len(problems) == 1


def test_missing_successor_map_source_is_live_red(tmp_path: Path) -> None:
    """A successor-map file missing from the tree is live-red, not stale."""
    root, specs_dir = _evidence_tree(tmp_path)
    _rebind_capture(root)
    successor = json.loads((root / R0_SUCCESSOR).read_bytes())
    missing = next(
        name for name in sorted(successor["source_sha256"]) if name == "pyproject.toml"
    )
    (root / missing).unlink()
    tree = census(specs_dir, root)
    record = _record_of(tree, R0_SUCCESSOR)
    assert record.status == LIVE_RED
    assert f"R0 successor custody digest drift: {missing} missing/unreadable" in (
        record.detail
    )


def test_missing_predecessor_map_source_is_live_red(tmp_path: Path) -> None:
    """A predecessor-map file missing from the tree is live-red, not stale."""
    root, specs_dir = _evidence_tree(tmp_path)
    target = next(
        name
        for path in PREDECESSORS
        if not path.endswith("07-gaussian-vfe-natural-gradient-custody.json")
        for name in json.loads((root / path).read_bytes()).get("source_sha256", {})
        if name.startswith("tests/")
    )
    (root / target).unlink()
    tree = census(specs_dir, root)
    drifted = [
        item
        for item in tree.records
        if item.status == LIVE_RED
        and item.path in PREDECESSORS
        and not item.path.endswith("07-gaussian-vfe-natural-gradient-custody.json")
    ]
    assert len(drifted) == 1
    assert f"stale predecessor source: {target} missing/unreadable" in drifted[0].detail
