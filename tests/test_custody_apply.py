"""Custody apply-phase tests on isolated tmp_path fixture roots.

Every pipeline run stages a ``shutil.copytree`` of the repo's ``specs/`` tree
into ``tmp_path`` and flushes into a fresh output directory. Every drift
injection lands on a ``tmp_path`` fixture root (see
``tests/_support/custody_fixture_knobs.fixture_root``: a ``specs/`` copy plus
byte-identical copies of every hashed non-specs surface), so no test ever
writes the live tree. Gates are driven through injected
``Census``/``Expectations`` objects per the evidence-fixture pattern, or the
real census over the fixture when the fixture itself is the subject; every
expected verdict derives from ``census``/``verify`` over the same tree, never
from live custody state.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
from pathlib import Path

import pytest

from fep_lean.custody.apply import (
    ACCEPTANCE,
    DIAGNOSTICS,
    H2_R0_CUSTODY,
    HORIZON_ACCEPTANCE_MODULE,
    LIFECYCLE_05D,
    MATRIX,
    PHASE_ORDER,
    PRECISION_TEST,
    PRIOR_07,
    SUCCESSOR_07,
    TERMINAL_PACKET,
    ApplyRefused,
    ApplyReport,
    _StagedView,
    apply_refresh,
    byte_replace,
    dump_json_bytes,
)
from fep_lean.custody.census import census as census_from_tree
from fep_lean.custody.model import LIVE_RED, STALE, Census, CensusRecord
from fep_lean.custody.verify import Expectations, gate_expectations
from fep_lean.custody.verify import verify as verify_gate
from fep_lean.verification.horizon_acceptance import TERMINAL_RECEIPT
from tests._support.custody_fixture_knobs import (
    JSON_WHITESPACE_DRIFT,
    drift_file,
    fixture_root,
    spec_path,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
BASE = "specs/done/horizon-2-smooth-stochastic/readiness/"
EVIDENCE = BASE + "evidence/20260904-wave2/"
PROBE_08 = BASE + "probes/08_gaussian_conditioning.lean"
REVIEW_FILES = tuple(
    EVIDENCE + name
    for name in ("review-lean.json", "review-domain.json", "review-skeptical.json")
)
LIVE_RED_FILES = (
    "tests/test_horizon1_decision_risk.py",
    "tests/test_horizon1_finite_reference_agent.py",
    "tests/test_horizon1_policy_action.py",
    "tests/test_native_blanket_formalisms.py",
)
# The re-bind residual the pipeline actually sees on this tree: the review and
# diagnostics source maps drift on exactly these three files, and the packet's
# 07-custody predecessor pin is stale against the live successor receipt.
AUTHORIZED_RECAPTURE = (
    "tests/_support/h2_r0_custody.py",
    "tests/test_horizon2_gaussian_control.py",
    "tests/test_horizon2_gaussian_vfe_readiness.py",
    SUCCESSOR_07,
)
CAPTURE_DETAIL = "capture digest 0123456789ab predates live fedcba987654"
TERMINAL_DETAIL = (
    "native source capture stale or changed (horizon_acceptance.py:592): "
    "4 captured file(s) differ from the live tree"
)
INSERTION_ORDER_FILES = frozenset(
    {"05d-gaussian-conditioning-lifecycle.json", "diagnostics.json"}
)


def _stage_specs(tmp_path: Path) -> Path:
    target = tmp_path / "specs"
    shutil.copytree(REPO_ROOT / "specs", target, symlinks=False)
    return target


def _out_dir(tmp_path: Path) -> Path:
    return tmp_path / "output"


def _out_path(out: Path, relative: str) -> Path:
    assert relative.startswith("specs/")
    return out / relative[len("specs/") :]


def _out_bytes(out: Path, relative: str) -> bytes:
    return _out_path(out, relative).read_bytes()


def _all_clear() -> tuple[Census, Expectations]:
    return Census(records=()), Expectations()


def _live_red_fixture() -> Census:
    """The verified FEP-H27-RESEAL classification: terminal + four stale files."""
    return Census(
        (
            CensusRecord(path=TERMINAL_PACKET, status=STALE, detail=TERMINAL_DETAIL),
            *(
                CensusRecord(path=path, status=STALE, detail=CAPTURE_DETAIL)
                for path in LIVE_RED_FILES
            ),
        )
    )


def _mutate_probe(specs_dir: Path) -> None:
    probe = specs_dir / PROBE_08[len("specs/") :]
    probe.write_bytes(probe.read_bytes() + b"\n-- cascade drift marker\n")


def _rewrite_json(path: Path, mutate: object) -> None:
    record = json.loads(path.read_text())
    mutate(record)
    path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")


def _assert_untouched(out: Path) -> None:
    assert not out.exists() or not any(out.iterdir())


def _tree_snapshot(root: Path) -> dict[str, str]:
    """Digest every file under ``root``; proves a CLI run wrote nothing."""
    return {
        path.relative_to(root).as_posix(): _sha(path.read_bytes())
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _apply(
    tmp_path: Path,
    *,
    authorized: tuple[str, ...],
    census: Census | None = None,
    expectations: Expectations | None = None,
    specs_dir: Path | None = None,
) -> ApplyReport:
    fixture_census, fixture_expectations = _all_clear()
    return apply_refresh(
        specs_dir if specs_dir is not None else _stage_specs(tmp_path),
        REPO_ROOT,
        _out_dir(tmp_path),
        expectations if expectations is not None else fixture_expectations,
        census=census if census is not None else fixture_census,
        authorized_changes=authorized,
    )


# ---------------------------------------------------------------------------
# Settled order + serialization helpers.
# ---------------------------------------------------------------------------


def test_phase_order_is_the_settled_14() -> None:
    assert PHASE_ORDER == (
        "pin_evidence_recollection",
        "acceptance_rebind",
        "matrix_receipt_sha256",
        "prior_07_reissue",
        "h2_r0_custody_prior_sha256",
        "successor_07_reissue",
        "record_reissues",
        "lifecycle_repair_sha256",
        "precision_test_constants",
        "predecessors_patch",
        "reviews_reissue",
        "diagnostics_regen",
        "terminal_packet_reissue",
        "h3_lockstep",
    )
    assert (
        PHASE_ORDER.index("matrix_receipt_sha256")
        == PHASE_ORDER.index("acceptance_rebind") + 1
    )
    assert PHASE_ORDER[-1] == "h3_lockstep"


def test_byte_replace_replaces_single_occurrence() -> None:
    assert byte_replace(b"a-X-b", b"X", b"Y") == b"a-Y-b"


def test_byte_replace_refuses_missing_anchor() -> None:
    with pytest.raises(ApplyRefused, match="anchor count 0"):
        byte_replace(b"abc", b"zzz", b"Y")


def test_byte_replace_refuses_ambiguous_anchor() -> None:
    with pytest.raises(ApplyRefused, match="anchor count 2"):
        byte_replace(b"x-x", b"x", b"Y")


def test_serialization_discipline_exceptions() -> None:
    payload = {"z_key": 1, "a_key": {"b": 2}}
    sorted_bytes = dump_json_bytes(payload, relative="acceptance.json")
    assert sorted_bytes.startswith(b'{\n  "a_key"')
    insertion_bytes = dump_json_bytes(payload, relative="diagnostics.json")
    assert insertion_bytes.startswith(b'{\n  "z_key"')
    assert (
        dump_json_bytes(payload, relative="05d-gaussian-conditioning-lifecycle.json")
        == insertion_bytes
    )


def test_staged_view_put_is_idempotent(tmp_path: Path) -> None:
    staged = tmp_path / "staged.bin"
    staged.write_bytes(b"same")
    view = _StagedView(tmp_path, tmp_path)
    assert view.put("staged.bin", b"same") is False
    assert view.put("staged.bin", b"changed") is True
    assert view.issued == {"staged.bin"}
    assert view.read("staged.bin") == b"changed"


# ---------------------------------------------------------------------------
# Gate: the live-red four-file classification is the gate case.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "drift",
    (
        pytest.param("sealed", id="sealed_fixture_census_green"),
        pytest.param("digest", id="successor_receipt_digest_drift"),
        pytest.param("unlink", id="missing_predecessor_receipt"),
    ),
)
def test_gate_refuses_real_tree_live_red_classification(
    tmp_path: Path, drift: str
) -> None:
    """The real census over the staged copy classifies the injected drift."""
    root = fixture_root(tmp_path)
    specs_dir = root / "specs"
    out = _out_dir(tmp_path)
    if drift == "digest":
        drift_file(spec_path(root, SUCCESSOR_07), JSON_WHITESPACE_DRIFT)
    elif drift == "unlink":
        spec_path(root, PRIOR_07).unlink()
    census_obj = census_from_tree(specs_dir, root)
    ok, problems = verify_gate(census_obj, gate_expectations())
    if drift == "sealed":
        assert ok, problems
        report = apply_refresh(specs_dir, root, out)
        assert report.phases == ()
        assert report.mutations == ()
        return
    assert not ok
    with pytest.raises(ApplyRefused) as excinfo:
        apply_refresh(specs_dir, root, out)
    assert str(excinfo.value) == "custody verify gate refused: " + "; ".join(problems)
    _assert_untouched(out)


def test_gate_refuses_live_red_fixture_and_writes_nothing(tmp_path: Path) -> None:
    specs_dir = _stage_specs(tmp_path)
    out = _out_dir(tmp_path)
    with pytest.raises(ApplyRefused) as excinfo:
        apply_refresh(specs_dir, REPO_ROOT, out, None, census=_live_red_fixture())
    for path in LIVE_RED_FILES:
        assert path in str(excinfo.value)
    _assert_untouched(out)


def test_gate_live_red_is_never_authorized(tmp_path: Path) -> None:
    specs_dir = _stage_specs(tmp_path)
    out = _out_dir(tmp_path)
    record = CensusRecord(
        path="tests/test_horizon1_policy_action.py", status=LIVE_RED, detail="break"
    )
    expectations = Expectations(allowed_stale=frozenset({record.path}))
    with pytest.raises(ApplyRefused):
        apply_refresh(specs_dir, REPO_ROOT, out, expectations, census=Census((record,)))
    _assert_untouched(out)


@pytest.mark.parametrize("state", ("sealed", "forced"))
def test_gate_all_clear_fixture_admits_the_pipeline(
    tmp_path: Path, state: str
) -> None:
    """A passing gate is not the blocker; the authorized pipeline completes."""
    root = fixture_root(tmp_path)
    specs_dir = root / "specs"
    out = _out_dir(tmp_path)
    census_obj = census_from_tree(specs_dir, root)
    ok, problems = verify_gate(census_obj, gate_expectations())
    assert ok, problems
    if state == "sealed":
        report = apply_refresh(specs_dir, root, out)
        assert report.phases == ()
        assert report.mutations == ()
        return
    # Forced-change residual: probe 08 drifts in the staged copy; the
    # pipeline re-binds exactly the surfaces the receipt chain covers.
    _mutate_probe(specs_dir)
    report = apply_refresh(
        specs_dir,
        root,
        out,
        Expectations(),
        census=Census(records=()),
        authorized_changes=(PROBE_08,),
    )
    assert report.phases[-1] == "h3_lockstep"
    assert report.files_written > 0
    assert DIAGNOSTICS not in report.mutations
    assert LIFECYCLE_05D in report.mutations
    for relative in (DIAGNOSTICS, *REVIEW_FILES):
        assert _out_bytes(out, relative) == spec_path(root, relative).read_bytes()
    assert _out_bytes(out, ACCEPTANCE) != spec_path(root, ACCEPTANCE).read_bytes()


# ---------------------------------------------------------------------------
# Fail-closed pipeline refusals.
# ---------------------------------------------------------------------------


def test_unexplained_drift_refuses_and_writes_nothing(tmp_path: Path) -> None:
    specs_dir = _stage_specs(tmp_path)
    _mutate_probe(specs_dir)
    out = _out_dir(tmp_path)
    census, expectations = _all_clear()
    with pytest.raises(ApplyRefused, match="unexplained source drift"):
        apply_refresh(
            specs_dir,
            REPO_ROOT,
            out,
            expectations,
            census=census,
            authorized_changes=(),  # probe-08 deliberately NOT authorized
        )
    _assert_untouched(out)


def test_byte_replace_abort_leaves_output_untouched(tmp_path: Path) -> None:
    specs_dir = _stage_specs(tmp_path)
    _mutate_probe(specs_dir)
    matrix = specs_dir / MATRIX[len("specs/") :]
    text = matrix.read_text()
    match = re.search(r"\n  receipt_sha256: ([0-9a-f]{64})\n", text)
    assert match is not None
    matrix.write_text(
        text.replace(match.group(0), match.group(0) + match.group(0), 1)
    )  # adjacent duplicate keeps the YAML valid for the phase-1 parse
    out = _out_dir(tmp_path)
    census, expectations = _all_clear()
    with pytest.raises(ApplyRefused, match="anchor count 2 != 1"):
        apply_refresh(
            specs_dir,
            REPO_ROOT,
            out,
            expectations,
            census=census,
            authorized_changes=(PROBE_08, *AUTHORIZED_RECAPTURE),
        )
    _assert_untouched(out)


def test_pin_evidence_toolchain_mismatch_refuses(tmp_path: Path) -> None:
    specs_dir = _stage_specs(tmp_path)
    pin_path = specs_dir / "done/horizon-2-smooth-stochastic/readiness/pin_evidence.json"
    _rewrite_json(
        pin_path, lambda record: record["stable_pair"].update({"tag": "v9.9.9"})
    )
    out = _out_dir(tmp_path)
    census, expectations = _all_clear()
    with pytest.raises(ApplyRefused, match="stable_pair tag"):
        apply_refresh(specs_dir, REPO_ROOT, out, expectations, census=census)
    _assert_untouched(out)


def test_pin_evidence_missing_repositories_refuses(tmp_path: Path) -> None:
    specs_dir = _stage_specs(tmp_path)
    pin_path = specs_dir / "done/horizon-2-smooth-stochastic/readiness/pin_evidence.json"
    _rewrite_json(pin_path, lambda record: record.pop("repositories"))
    out = _out_dir(tmp_path)
    census, expectations = _all_clear()
    with pytest.raises(ApplyRefused, match="repositories roster missing"):
        apply_refresh(specs_dir, REPO_ROOT, out, expectations, census=census)
    _assert_untouched(out)


def test_missing_staged_receipt_refuses(tmp_path: Path) -> None:
    specs_dir = _stage_specs(tmp_path)
    (
        specs_dir
        / "done/horizon-2-smooth-stochastic/readiness/repairs/06a-native-filter-posterior.json"
    ).unlink()
    out = _out_dir(tmp_path)
    census, expectations = _all_clear()
    with pytest.raises(ApplyRefused, match="missing staged/source file"):
        apply_refresh(specs_dir, REPO_ROOT, out, expectations, census=census)
    _assert_untouched(out)


def test_prior_exempt_roster_bogus_entry_refuses(tmp_path: Path) -> None:
    specs_dir = _stage_specs(tmp_path)
    path = specs_dir / SUCCESSOR_07[len("specs/") :]
    _rewrite_json(
        path,
        lambda record: record["allowed_prior_source_changes"].append("bogus/path.py"),
    )
    out = _out_dir(tmp_path)
    census, expectations = _all_clear()
    with pytest.raises(ApplyRefused, match="exempt entries not present"):
        apply_refresh(specs_dir, REPO_ROOT, out, expectations, census=census)
    _assert_untouched(out)


def test_successor_probe_map_inconsistency_refuses(tmp_path: Path) -> None:
    specs_dir = _stage_specs(tmp_path)
    path = specs_dir / SUCCESSOR_07[len("specs/") :]
    _rewrite_json(
        path,
        lambda record: record["native_evidence"]["probes"][0].update(
            {"source_sha256": {}}
        ),
    )
    out = _out_dir(tmp_path)
    census, expectations = _all_clear()
    with pytest.raises(ApplyRefused, match="probe map differs"):
        apply_refresh(specs_dir, REPO_ROOT, out, expectations, census=census)
    _assert_untouched(out)


def test_successor_manifest_transition_inconsistency_refuses(tmp_path: Path) -> None:
    specs_dir = _stage_specs(tmp_path)
    path = specs_dir / SUCCESSOR_07[len("specs/") :]
    _rewrite_json(
        path,
        lambda record: record["manifest_transition"].update(
            {"current_sha256": "deadbeef"}
        ),
    )
    out = _out_dir(tmp_path)
    census, expectations = _all_clear()
    with pytest.raises(ApplyRefused, match="manifest_transition inconsistent"):
        apply_refresh(specs_dir, REPO_ROOT, out, expectations, census=census)
    _assert_untouched(out)


def test_successor_prior_reference_drift_refuses(tmp_path: Path) -> None:
    specs_dir = _stage_specs(tmp_path)
    path = specs_dir / SUCCESSOR_07[len("specs/") :]
    _rewrite_json(path, lambda record: record["prior"].update({"sha256": "deadbeef"}))
    out = _out_dir(tmp_path)
    census, expectations = _all_clear()
    with pytest.raises(ApplyRefused, match="prior reference drift"):
        apply_refresh(specs_dir, REPO_ROOT, out, expectations, census=census)
    _assert_untouched(out)


def test_diagnostics_byte_drift_without_source_drift_refuses(tmp_path: Path) -> None:
    """Same source maps, different bytes (sorted serialization): refuse."""
    specs_dir = _stage_specs(tmp_path)
    from fep_lean.verification.horizon_acceptance import diagnostic_record

    recomputed = diagnostic_record(REPO_ROOT)
    path = specs_dir / DIAGNOSTICS[len("specs/") :]
    path.write_text(json.dumps(recomputed, indent=2, sort_keys=True) + "\n")
    out = _out_dir(tmp_path)
    census, expectations = _all_clear()
    with pytest.raises(ApplyRefused, match="byte drift without source drift"):
        apply_refresh(
            specs_dir,
            REPO_ROOT,
            out,
            expectations,
            census=census,
            authorized_changes=AUTHORIZED_RECAPTURE,
        )
    _assert_untouched(out)


def test_packet_current_sources_roster_drift_refuses(tmp_path: Path) -> None:
    specs_dir = _stage_specs(tmp_path)
    path = specs_dir / TERMINAL_PACKET[len("specs/") :]
    _rewrite_json(
        path,
        lambda record: record["current_sources"].update({"bogus/extra.py": "0" * 64}),
    )
    out = _out_dir(tmp_path)
    census, expectations = _all_clear()
    with pytest.raises(ApplyRefused, match="current_sources roster drift"):
        apply_refresh(
            specs_dir,
            REPO_ROOT,
            out,
            expectations,
            census=census,
            authorized_changes=AUTHORIZED_RECAPTURE,
        )
    _assert_untouched(out)


def test_frozen_evidence_drift_refuses(tmp_path: Path) -> None:
    specs_dir = _stage_specs(tmp_path)
    collection = specs_dir / (EVIDENCE + "collection.json")[len("specs/") :]
    collection.write_bytes(collection.read_bytes() + b" ")
    out = _out_dir(tmp_path)
    census, expectations = _all_clear()
    with pytest.raises(ApplyRefused, match="frozen evidence drifted"):
        apply_refresh(
            specs_dir,
            REPO_ROOT,
            out,
            expectations,
            census=census,
            authorized_changes=AUTHORIZED_RECAPTURE,
        )
    _assert_untouched(out)


def test_review_roster_drift_refuses(tmp_path: Path) -> None:
    specs_dir = _stage_specs(tmp_path)
    path = specs_dir / REVIEW_FILES[0][len("specs/") :]
    _rewrite_json(
        path,
        lambda record: record["source_sha256"].pop(min(record["source_sha256"])),
    )
    out = _out_dir(tmp_path)
    census, expectations = _all_clear()
    with pytest.raises(ApplyRefused, match="source roster drift"):
        apply_refresh(
            specs_dir,
            REPO_ROOT,
            out,
            expectations,
            census=census,
            authorized_changes=AUTHORIZED_RECAPTURE,
        )
    _assert_untouched(out)


def test_h3_roster_drift_refuses(tmp_path: Path) -> None:
    specs_dir = _stage_specs(tmp_path)
    path = specs_dir / "h3-case-study/spike-receipt.json"
    _rewrite_json(path, lambda record: record["digests"].pop(min(record["digests"])))
    out = _out_dir(tmp_path)
    census, expectations = _all_clear()
    with pytest.raises(ApplyRefused, match="PINNED_SOURCES roster drift"):
        apply_refresh(
            specs_dir,
            REPO_ROOT,
            out,
            expectations,
            census=census,
            authorized_changes=AUTHORIZED_RECAPTURE,
        )
    _assert_untouched(out)


# ---------------------------------------------------------------------------
# Recapture re-bind: reviews, diagnostics, packet, H3 lockstep.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("state", ("sealed", "recapture"))
def test_recapture_rebind_mutates_exactly_the_evidence_surfaces(
    tmp_path: Path, state: str
) -> None:
    """The recapture residual is synthesized on the fixture, never the live tree."""
    root = fixture_root(tmp_path)
    out = _out_dir(tmp_path)
    if state == "sealed":
        report = apply_refresh(root / "specs", root, out)
        assert report.phases == ()
        assert report.mutations == ()
        return
    # Synthesized pre-chore residual: the successor receipt's PREDECESSORS
    # pin predates its re-recorded bytes, and the reviews/diagnostics source
    # planes drift on two Python surfaces. Python only: a lone Lean mirror
    # edit trips the formal-projection drift check instead of a stale map.
    drift_file(spec_path(root, SUCCESSOR_07), JSON_WHITESPACE_DRIFT)
    drifted = (
        "tests/test_horizon_acceptance.py",
        "tests/test_numerical_witnesses.py",
    )
    for name in drifted:
        drift_file(root / name)
    report = apply_refresh(
        root / "specs",
        root,
        out,
        Expectations(),
        census=Census(records=()),
        authorized_changes=(*drifted, SUCCESSOR_07),
    )
    assert report.phases == (
        "predecessors_patch",
        "reviews_reissue",
        "diagnostics_regen",
        "terminal_packet_reissue",
        "h3_lockstep",
    )
    assert set(report.mutations) == {
        *REVIEW_FILES,
        DIAGNOSTICS,
        TERMINAL_PACKET,
        "specs/h3-case-study/spike-receipt.json",
        "specs/h3-case-study/h3_reference_study_spike.py",
    }
    assert len(report.directives) == 1
    directive = report.directives[0]
    assert directive.path == HORIZON_ACCEPTANCE_MODULE
    assert directive.phase == "predecessors_patch"
    live = (root / HORIZON_ACCEPTANCE_MODULE).read_bytes()
    assert live.count(directive.anchor) == 1
    assert _sha(_out_bytes(out, SUCCESSOR_07)).encode() in directive.replacement
    # diagnostics keeps insertion order; the packet keeps sorted keys.
    diagnostics = json.loads(_out_bytes(out, DIAGNOSTICS))
    assert (
        _out_bytes(out, DIAGNOSTICS)
        == (json.dumps(diagnostics, indent=2) + "\n").encode()
    )
    assert (
        _out_bytes(out, DIAGNOSTICS)
        != (json.dumps(diagnostics, indent=2, sort_keys=True) + "\n").encode()
    )


# ---------------------------------------------------------------------------
# Cascade: acceptance re-bind strictly precedes the matrix step.
# ---------------------------------------------------------------------------


def _run_cascade(tmp_path: Path) -> tuple[ApplyReport, Path]:
    specs_dir = _stage_specs(tmp_path)
    _mutate_probe(specs_dir)
    out = _out_dir(tmp_path)
    census, expectations = _all_clear()
    report = apply_refresh(
        specs_dir,
        REPO_ROOT,
        out,
        expectations,
        census=census,
        authorized_changes=(PROBE_08, *AUTHORIZED_RECAPTURE),
    )
    return report, out


def test_cascade_matrix_follows_acceptance_rebind(tmp_path: Path) -> None:
    report, out = _run_cascade(tmp_path)
    assert "acceptance_rebind" in report.phases
    assert "matrix_receipt_sha256" in report.phases
    assert report.phases.index("acceptance_rebind") < report.phases.index(
        "matrix_receipt_sha256"
    )
    assert report.phases[-1] == "h3_lockstep"
    matrix_text = _out_bytes(out, MATRIX).decode("utf-8")
    expected = _sha(_out_bytes(out, ACCEPTANCE))
    assert f"receipt_sha256: {expected}" in matrix_text
    assert matrix_text.count("receipt_sha256: ") == 1


@pytest.mark.parametrize("drift_class", ("probe_rewrite", "diagnostics_stale"))
def test_cascade_serialization_discipline(tmp_path: Path, drift_class: str) -> None:
    """Per-file serialization discipline over whatever the cascade mutates."""
    root = fixture_root(tmp_path)
    specs_dir = root / "specs"
    out = _out_dir(tmp_path)
    if drift_class == "probe_rewrite":
        _mutate_probe(specs_dir)
        authorized: tuple[str, ...] = (PROBE_08,)
    else:
        drifted = (
            "tests/test_horizon_acceptance.py",
            "tests/test_numerical_witnesses.py",
        )
        for name in drifted:
            drift_file(root / name)
        authorized = drifted
    report = apply_refresh(
        specs_dir,
        root,
        out,
        Expectations(),
        census=Census(records=()),
        authorized_changes=authorized,
    )
    mutated_json = [
        relative for relative in report.mutations if relative.endswith(".json")
    ]
    if drift_class == "probe_rewrite":
        assert LIFECYCLE_05D in mutated_json
        assert DIAGNOSTICS not in report.mutations
        assert (
            _out_bytes(out, DIAGNOSTICS) == spec_path(root, DIAGNOSTICS).read_bytes()
        )
    else:
        assert DIAGNOSTICS in mutated_json
    for relative in mutated_json:
        data = _out_bytes(out, relative)
        payload = json.loads(data)
        if relative.rsplit("/", 1)[-1] in INSERTION_ORDER_FILES:
            assert data == (json.dumps(payload, indent=2) + "\n").encode()
            assert (
                data != (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode()
            ), relative
        else:
            assert (
                data == (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode()
            ), relative


def test_cascade_emits_repo_side_directives(tmp_path: Path) -> None:
    report, out = _run_cascade(tmp_path)
    by_path: dict[str, list[str]] = {}
    for directive in report.directives:
        by_path.setdefault(directive.path, []).append(directive.phase)
    assert by_path == {
        H2_R0_CUSTODY: ["h2_r0_custody_prior_sha256"],
        PRECISION_TEST: ["precision_test_constants", "precision_test_constants"],
        HORIZON_ACCEPTANCE_MODULE: ["predecessors_patch"] * 7,
    }
    for directive in report.directives:
        live = (REPO_ROOT / directive.path).read_bytes()
        assert live.count(directive.anchor) == 1, directive.path
        assert directive.anchor != directive.replacement
    prior_directive = next(d for d in report.directives if d.path == H2_R0_CUSTODY)
    assert prior_directive.replacement.endswith(
        b'PRIOR_SHA256 = "' + _sha(_out_bytes(out, PRIOR_07)).encode() + b'"'
    )


def test_cascade_h3_lockstep_agrees_with_spike_receipt(tmp_path: Path) -> None:
    _report, out = _run_cascade(tmp_path)
    receipt = json.loads(_out_bytes(out, "specs/h3-case-study/spike-receipt.json"))
    spike_text = _out_bytes(
        out, "specs/h3-case-study/h3_reference_study_spike.py"
    ).decode()
    match = re.search(
        r"PINNED_SOURCES: dict\[str, str\] = \{(.*?)\n\}", spike_text, re.DOTALL
    )
    assert match is not None
    pinned = dict(re.findall(r'"([^"]+)": \(\s*"([0-9a-f]{64})"\s*\),', match.group(1)))
    assert pinned == receipt["digests"]
    assert receipt["digests"][TERMINAL_PACKET] == _sha(_out_bytes(out, TERMINAL_PACKET))


# ---------------------------------------------------------------------------
# Precondition guards and strict expectation behavior.
# ---------------------------------------------------------------------------


def test_missing_specs_dir_is_an_operator_error(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="specs dir not found"):
        apply_refresh(tmp_path / "nope", REPO_ROOT, tmp_path / "out")


def test_missing_repo_root_is_an_operator_error(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="repo root not found"):
        apply_refresh(_stage_specs(tmp_path), tmp_path / "nope", tmp_path / "out")


def test_output_dir_must_not_be_the_specs_tree(tmp_path: Path) -> None:
    specs_dir = _stage_specs(tmp_path)
    with pytest.raises(ValueError, match="staging copy"):
        apply_refresh(specs_dir, REPO_ROOT, specs_dir)


def test_dirty_output_dir_refuses(tmp_path: Path) -> None:
    specs_dir = _stage_specs(tmp_path)
    out = _out_dir(tmp_path)
    out.mkdir()
    (out / "stale.bin").write_bytes(b"leftover")
    with pytest.raises(ValueError, match="output dir not empty"):
        _apply(tmp_path, authorized=AUTHORIZED_RECAPTURE, specs_dir=specs_dir)


def test_required_surface_never_authorized_by_allowed_stale(tmp_path: Path) -> None:
    """A required surface reported stale refuses; it is never laundered."""
    root = fixture_root(tmp_path)
    out = _out_dir(tmp_path)
    terminal_record = CensusRecord(
        path=TERMINAL_PACKET, status=STALE, detail=TERMINAL_DETAIL
    )
    assert TERMINAL_PACKET == TERMINAL_RECEIPT
    laundered = Expectations(
        required_intact=(TERMINAL_PACKET,), allowed_stale=frozenset({TERMINAL_PACKET})
    )
    ok, problems = verify_gate(Census((terminal_record,)), laundered)
    assert not ok
    assert problems == [f"stale: {TERMINAL_PACKET}: {TERMINAL_DETAIL}"]
    undeclared = Expectations(allowed_stale=frozenset({TERMINAL_PACKET}))
    assert verify_gate(Census((terminal_record,)), undeclared) == (True, [])
    census_obj = Census((terminal_record,))
    ok, problems = verify_gate(census_obj, gate_expectations())
    assert not ok
    with pytest.raises(ApplyRefused) as excinfo:
        apply_refresh(root / "specs", root, out, census=census_obj)
    assert str(excinfo.value) == "custody verify gate refused: " + "; ".join(problems)
    _assert_untouched(out)


def test_path_escape_is_refused(tmp_path: Path) -> None:
    view = _StagedView(tmp_path, tmp_path)
    with pytest.raises(ApplyRefused, match="path escapes project"):
        view.read("../outside.bin")


def test_structural_tampers_refuse(tmp_path: Path) -> None:
    """Missing/malformed structural fields fail closed with precise reasons."""
    cases: tuple[tuple[str, str, object], ...] = (
        (
            "specs/done/horizon-2-smooth-stochastic/readiness/pin_evidence.json",
            "stable_pair.tag missing",
            lambda record: record.pop("stable_pair"),
        ),
        (
            "specs/done/horizon-2-smooth-stochastic/readiness/matrix.yaml",
            "unparseable YAML",
            None,  # handled below by truncation
        ),
        (
            SUCCESSOR_07,
            "allowed_prior_source_changes missing",
            lambda record: record.pop("allowed_prior_source_changes"),
        ),
        (
            SUCCESSOR_07,
            "native_evidence missing",
            lambda record: record.pop("native_evidence"),
        ),
        (
            SUCCESSOR_07,
            "manifest_transition missing",
            lambda record: record.pop("manifest_transition"),
        ),
        (
            SUCCESSOR_07,
            "prior reference missing",
            lambda record: record.pop("prior"),
        ),
        (
            LIFECYCLE_05D,
            "corrected_artifact.repair_sha256 missing",
            lambda record: record.pop("corrected_artifact"),
        ),
        (
            TERMINAL_PACKET,
            "reviews roster missing",
            lambda record: record.pop("reviews"),
        ),
        (
            TERMINAL_PACKET,
            "native_evidence missing",
            lambda record: record.pop("native_evidence"),
        ),
    )
    for relative, message, mutate in cases:
        specs_dir = _stage_specs(tmp_path)
        out = _out_dir(tmp_path)
        if mutate is None:
            matrix = specs_dir / MATRIX[len("specs/") :]
            matrix.write_text("= not yaml =")
        else:
            _rewrite_json(specs_dir / relative[len("specs/") :], mutate)
        with pytest.raises(ApplyRefused, match=message):
            _apply(
                tmp_path,
                authorized=AUTHORIZED_RECAPTURE,
                specs_dir=specs_dir,
            )
        _assert_untouched(out)
        shutil.rmtree(tmp_path / "specs", ignore_errors=True)


def test_successor_probe_roster_missing_refuses(tmp_path: Path) -> None:
    specs_dir = _stage_specs(tmp_path)
    path = specs_dir / SUCCESSOR_07[len("specs/") :]
    _rewrite_json(path, lambda record: record["native_evidence"].update({"probes": []}))
    out = _out_dir(tmp_path)
    census, expectations = _all_clear()
    with pytest.raises(ApplyRefused, match="native_evidence.probes missing"):
        apply_refresh(specs_dir, REPO_ROOT, out, expectations, census=census)
    _assert_untouched(out)


def test_pin_evidence_matrix_toolchain_mismatch_refuses(tmp_path: Path) -> None:
    specs_dir = _stage_specs(tmp_path)
    matrix = specs_dir / MATRIX[len("specs/") :]
    matrix.write_text(
        matrix.read_text().replace("mathlib_tag: v4.34.0", "mathlib_tag: v4.33.1", 1)
    )
    out = _out_dir(tmp_path)
    census, expectations = _all_clear()
    with pytest.raises(ApplyRefused, match="matrix toolchain mathlib_tag mismatch"):
        apply_refresh(specs_dir, REPO_ROOT, out, expectations, census=census)
    _assert_untouched(out)


# ---------------------------------------------------------------------------
# CLI surface: census report and the gate-refusal exit path.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("state", ("green", "residual"))
def test_cli_census_report_composes_read_only(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    state: str,
) -> None:
    """The report composes the census over the patched fixture root."""
    root = fixture_root(tmp_path)
    if state == "residual":
        drift_file(root / "tests/test_horizon2_gaussian_filter.py")
        drift_file(spec_path(root, SUCCESSOR_07), JSON_WHITESPACE_DRIFT)
    before = _tree_snapshot(root)
    monkeypatch.setenv("FEP_LEAN_PROJECT_ROOT", str(root))
    from fep_lean.cli import main as cli_main

    assert cli_main(["custody", "census"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "ok"
    derived = census_from_tree(root / "specs", root)
    assert payload["gated"] == derived.is_gated()
    assert payload["stale"] == [record.path for record in derived.stale()]
    assert payload["live_red"] == [record.path for record in derived.live_red()]
    assert [record["path"] for record in payload["records"]] == [
        record.path for record in derived.records
    ]
    if state == "green":
        assert payload["gated"] is False
        assert payload["stale"] == []
        assert payload["live_red"] == []
    else:
        assert payload["gated"] is True
        assert TERMINAL_PACKET in payload["stale"]
        assert SUCCESSOR_07 in payload["live_red"]
    assert _tree_snapshot(root) == before


def test_cli_apply_refuses_without_output_dir(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FEP_LEAN_PROJECT_ROOT", str(REPO_ROOT))
    from fep_lean.cli import main as cli_main

    assert cli_main(["custody", "apply"]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "error"
    assert "requires --output-dir" in payload["error"]


@pytest.mark.parametrize("state", ("sealed", "residual"))
def test_cli_apply_gate_refusal_writes_nothing(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    state: str,
) -> None:
    """Exit codes and zero-effect write discipline on the fixture root."""
    root = fixture_root(tmp_path)
    monkeypatch.setenv("FEP_LEAN_PROJECT_ROOT", str(root))
    out = _out_dir(tmp_path)
    from fep_lean.cli import main as cli_main

    if state == "sealed":
        assert cli_main(["custody", "apply", "--output-dir", str(out)]) == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload["status"] == "ok"
        assert payload["phases"] == []
        assert payload["mutations"] == []
        return
    drift_file(spec_path(root, SUCCESSOR_07), JSON_WHITESPACE_DRIFT)
    census_obj = census_from_tree(root / "specs", root)
    ok, problems = verify_gate(census_obj, gate_expectations())
    assert not ok
    assert cli_main(["custody", "apply", "--output-dir", str(out)]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "error"
    assert payload["error"] == "custody verify gate refused: " + "; ".join(problems)
    _assert_untouched(out)
