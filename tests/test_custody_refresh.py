"""Tests for the composed custody-refresh command (lane B1, t-0043).

The command composes already-verified machinery (census, gate, apply,
validators, owner gate, native capture), so these tests pin the
composition contract: order, refusal messages, staging semantics, and
the native-capture preconditions. The gate and verify-set seams are
driven through the same evidence-fixture pattern as
``tests/test_custody_apply.py``: injected ``Census`` objects and canned
subprocess results — never the full battery, never a real native run.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

from fep_formal.catalogue.topics import FEPTopicCatalogue
from fep_formal.cli import build_parser, main
from fep_formal.custody import refresh as refresh_module
from fep_formal.custody.apply import SUCCESSOR_07
from fep_formal.custody.model import INTACT, LIVE_RED, STALE, Census, CensusRecord
from fep_formal.custody.refresh import (
    NATIVE_RECEIPT,
    RENDER_INPUTS,
    RefreshRefused,
    _bridge_warning,
    _load_journal,
    _render_barrier_paths,
    fixpoint_refresh,
    plan_refresh,
    refresh,
    resume_refresh,
)
from fep_formal.output.evidence import (
    build_native_lean_receipt,
    validate_native_lean_receipt,
    write_native_lean_receipt,
)
from fep_formal.output.provenance import SOURCE_OWNER_FILES, source_owner_paths
from fep_formal.verification._toolchain import pinned_lean_semver
from tests._support.custody_fixture_knobs import (
    JSON_WHITESPACE_DRIFT,
    drift_file,
    fixture_root,
    spec_path,
    stage_specs,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
VERIFY_SET_KEYS = frozenset(
    {
        "readiness",
        "h2_r0_custody",
        "terminal_acceptance",
        "diagnostics",
        "pytest_custody",
        "formalism_audit",
        "pin_audit",
    }
)


def test_native_receipt_path_is_the_sealed_relative_contract() -> None:
    """The capture argv contract is the checkout-relative receipt path.

    ``sandboxed_receipt`` patches ``refresh_module.NATIVE_RECEIPT`` to an
    absolute sandbox path per test; this pin keeps the sealed literal honest
    independently of any fixture.
    """
    assert NATIVE_RECEIPT == "output/native-verification.json"


def _stage_specs(tmp_path: Path) -> Path:
    return stage_specs(REPO_ROOT, tmp_path / "specs")


@pytest.fixture(autouse=True)
def _synthetic_custody_epoch(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """All positive receipt/commit records here are fabricated unit inputs."""
    root = fixture_root(tmp_path, monkeypatch)
    monkeypatch.setattr(sys.modules[__name__], "REPO_ROOT", root)
    committed = {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }
    monkeypatch.setattr(
        refresh_module, "_git_show", lambda project, relative: committed.get(relative)
    )


def _out_dir(tmp_path: Path) -> Path:
    return tmp_path / "output"


def _ok_run(*command: str, root: Path) -> dict[str, object]:
    return {"command": list(command), "exit_code": 0, "tail": ""}


def _all_clear_census(monkeypatch: pytest.MonkeyPatch) -> None:
    from fep_formal.custody.verify import GATE_EXPECTATIONS

    records = tuple(
        CensusRecord(path=path, status=INTACT, detail="fixture intact")
        for path in GATE_EXPECTATIONS.required_intact
    )
    monkeypatch.setattr(
        refresh_module, "census_from_tree", lambda specs, root: Census(records)
    )


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# ---------------------------------------------------------------------------
# Argument validation and refusals before any work.
# ---------------------------------------------------------------------------


def test_refresh_requires_a_non_empty_reason(tmp_path: Path) -> None:
    with pytest.raises(RefreshRefused, match="non-empty --reason"):
        refresh(REPO_ROOT / "specs", REPO_ROOT, _out_dir(tmp_path), reason="   ")


def test_refresh_refuses_missing_specs_dir(tmp_path: Path) -> None:
    with pytest.raises(RefreshRefused, match="specs dir not found"):
        refresh(tmp_path / "nope", REPO_ROOT, _out_dir(tmp_path), reason="r")


# ---------------------------------------------------------------------------
# Stop-gate: the census is computed first; a live-red refuses before apply.
# ---------------------------------------------------------------------------


def test_refresh_stop_gate_refuses_live_red_before_apply(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    out = _out_dir(tmp_path)
    record = CensusRecord(
        path="tests/test_horizon1_policy_action.py", status=LIVE_RED, detail="break"
    )
    monkeypatch.setattr(
        refresh_module, "census_from_tree", lambda specs, root: Census((record,))
    )
    with pytest.raises(RefreshRefused) as excinfo:
        refresh(REPO_ROOT / "specs", REPO_ROOT, out, reason="r")
    assert "live-red" in str(excinfo.value)
    assert "tests/test_horizon1_policy_action.py" in str(excinfo.value)
    assert not out.exists()


# ---------------------------------------------------------------------------
# Composition: all-clear fixture walks the phases and runs the verify set.
# ---------------------------------------------------------------------------


def test_refresh_all_clear_composes_every_phase(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[list[str]] = []

    def fake_run(*command: str, root: Path) -> dict[str, object]:
        calls.append(list(command))
        return _ok_run(*command, root=root)

    _all_clear_census(monkeypatch)
    monkeypatch.setattr(refresh_module, "_run", fake_run)
    monkeypatch.setattr(refresh_module, "_bridge_warning", lambda root: None)
    out = _out_dir(tmp_path)
    report = refresh(_stage_specs(tmp_path), REPO_ROOT, out, reason="composition")
    assert report.apply.phases == ()  # sealed tree: every phase is a no-op
    assert report.apply.files_written > 0  # the staged tree is flushed intact
    assert set(report.verify_set) == VERIFY_SET_KEYS
    assert report.verify_set["readiness"] == ()
    assert report.warnings == ()  # stubbed bridge: no cascade in this fixture
    assert report.native == {}  # no --native: no capture, no owner gate run
    assert len(calls) == 3  # pytest custody, formalism audit, pin audit
    for command in calls:
        assert command[0] == "uv"


def test_refresh_appends_the_bridge_cascade_warning(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    signature = (
        "bridge source binding is stale on: src/fep_formal/custody/cli.py "
        "(freshness STALE cascade expected); run the post-fold bridge pin "
        "cycle (coordinator-side; this command never pins)"
    )
    _all_clear_census(monkeypatch)

    def fake_run(*command: str, root: Path) -> dict[str, object]:
        return _ok_run(*command, root=root)

    monkeypatch.setattr(refresh_module, "_run", fake_run)
    monkeypatch.setattr(refresh_module, "_bridge_warning", lambda root: signature)
    report = refresh(_stage_specs(tmp_path), REPO_ROOT, _out_dir(tmp_path), reason="r")
    assert report.warnings == (signature,)


def test_refresh_verify_set_failure_blocks_the_report(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def failing_run(*command: str, root: Path) -> dict[str, object]:
        if "docs/pin_audit.py" in command:
            return {"command": list(command), "exit_code": 1, "tail": "FAIL: drift"}
        return _ok_run(*command, root=root)

    _all_clear_census(monkeypatch)
    monkeypatch.setattr(refresh_module, "_run", failing_run)
    with pytest.raises(RefreshRefused, match="pin_audit exit 1"):
        refresh(_stage_specs(tmp_path), REPO_ROOT, _out_dir(tmp_path), reason="r")


# ---------------------------------------------------------------------------
# Native capture preconditions: owner gate, clean tip, exact command.
# ---------------------------------------------------------------------------


def test_refresh_native_refused_on_owner_errors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[list[str]] = []

    def fake_run(*command: str, root: Path) -> dict[str, object]:
        calls.append(list(command))
        return _ok_run(*command, root=root)

    _all_clear_census(monkeypatch)
    monkeypatch.setattr(refresh_module, "_run", fake_run)
    monkeypatch.setattr(
        refresh_module,
        "report_owner_errors",
        lambda root: ("source owner is absent from manifest v21: x.py",),
    )
    with pytest.raises(RefreshRefused, match="pre-capture owner gate refused") as exc:
        refresh(
            _stage_specs(tmp_path),
            REPO_ROOT,
            _out_dir(tmp_path),
            reason="r",
            run_native=True,
        )
    assert "x.py" in str(exc.value)
    assert len(calls) == 3  # the verify set runs before the pre-capture gate
    assert not any(command[2:4] == ["fep-formal", "verify"] for command in calls)


def test_refresh_native_refused_on_dirty_tip(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[list[str]] = []

    def fake_run(*command: str, root: Path) -> dict[str, object]:
        calls.append(list(command))
        return _ok_run(*command, root=root)

    _all_clear_census(monkeypatch)
    monkeypatch.setattr(refresh_module, "_run", fake_run)
    monkeypatch.setattr(refresh_module, "report_owner_errors", lambda root: ())
    monkeypatch.setattr(refresh_module, "_git_dirty", lambda root: [" M src/x.py"])
    with pytest.raises(RefreshRefused, match="committed clean tip"):
        refresh(
            _stage_specs(tmp_path),
            REPO_ROOT,
            _out_dir(tmp_path),
            reason="r",
            run_native=True,
        )
    assert len(calls) == 3  # verify set precedes the gate; capture refused
    assert not any(command[2:4] == ["fep-formal", "verify"] for command in calls)


def test_refresh_native_runs_the_sealed_capture_command(
    synthetic_native_capture: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[list[str]] = []

    def fake_run(*command: str, root: Path) -> dict[str, object]:
        calls.append(list(command))
        return _ok_run(*command, root=root)

    _all_clear_census(monkeypatch)
    monkeypatch.setattr(refresh_module, "_run", fake_run)
    report = refresh(
        _stage_specs(tmp_path),
        REPO_ROOT,
        _out_dir(tmp_path),
        reason="r",
        run_native=True,
    )
    assert len(calls) == 3
    assert report.native["command"] == [
        "uv",
        "run",
        "fep-formal",
        "verify",
        "--fail-on-warnings",
        "--receipt",
        str(synthetic_native_capture),
    ]
    assert report.native["exit_code"] == 0
    assert report.native["receipt"] == str(synthetic_native_capture)
    assert report.native["validation"]["claim_ready"] is True
    assert report.native["validation"]["source_bound"] is True
    assert report.native["validation"]["errors"] == []


def test_refresh_native_command_failure_refused(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    calls: list[list[str]] = []

    def fake_run(*command: str, root: Path) -> dict[str, object]:
        calls.append(list(command))
        if command[2:4] == ("fep-formal", "verify"):
            return {"command": list(command), "exit_code": 1, "tail": "boom"}
        return _ok_run(*command, root=root)

    _all_clear_census(monkeypatch)
    monkeypatch.setattr(refresh_module, "_run", fake_run)
    monkeypatch.setattr(refresh_module, "report_owner_errors", lambda root: ())
    monkeypatch.setattr(refresh_module, "_git_dirty", lambda root: [])
    with pytest.raises(RefreshRefused, match="native capture failed") as exc:
        refresh(
            _stage_specs(tmp_path),
            REPO_ROOT,
            _out_dir(tmp_path),
            reason="r",
            run_native=True,
        )
    assert "exit 1" in str(exc.value)
    assert "boom" in str(exc.value)
    # The CLI surfaces the same refusal as a JSON error with exit 1.
    exit_code = main_with_root(
        tmp_path,
        [
            "--specs-dir",
            str(_stage_specs(tmp_path / "cli")),
            "--output-dir",
            str(tmp_path / "cli-out"),
            "--reason",
            "capture-fail",
            "--native",
        ],
    )
    assert exit_code == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "error"
    assert "native capture failed" in payload["failure_reason"]


def test_refresh_native_missing_receipt_refused(
    sandboxed_receipt: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _all_clear_census(monkeypatch)
    monkeypatch.setattr(refresh_module, "_run", _ok_run)
    monkeypatch.setattr(refresh_module, "report_owner_errors", lambda root: ())
    monkeypatch.setattr(refresh_module, "_git_dirty", lambda root: [])
    monkeypatch.setattr(refresh_module, "_git_head", lambda root: "fix-head")
    assert not sandboxed_receipt.exists()
    with pytest.raises(RefreshRefused, match="native receipt missing") as exc:
        refresh(
            _stage_specs(tmp_path),
            REPO_ROOT,
            _out_dir(tmp_path),
            reason="r",
            run_native=True,
        )
    assert str(sandboxed_receipt) in str(exc.value)


def test_refresh_native_stale_receipt_refused(
    sandboxed_receipt: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _all_clear_census(monkeypatch)
    monkeypatch.setattr(refresh_module, "_run", _ok_run)
    monkeypatch.setattr(refresh_module, "report_owner_errors", lambda root: ())
    monkeypatch.setattr(refresh_module, "_git_dirty", lambda root: [])
    monkeypatch.setattr(refresh_module, "_git_head", lambda root: "fix-head")
    sandboxed_receipt.parent.mkdir(parents=True, exist_ok=True)
    sandboxed_receipt.write_text("{}", encoding="utf-8")
    with pytest.raises(RefreshRefused, match="not claim-ready"):
        refresh(
            _stage_specs(tmp_path),
            REPO_ROOT,
            _out_dir(tmp_path),
            reason="r",
            run_native=True,
        )


def test_refresh_native_owner_drift_during_capture_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    owner_calls: list[int] = []

    def fake_owner_errors(root: Path) -> tuple[str, ...]:
        owner_calls.append(1)
        return () if len(owner_calls) == 1 else ("owner x drifted",)

    _all_clear_census(monkeypatch)
    monkeypatch.setattr(refresh_module, "_run", _ok_run)
    monkeypatch.setattr(refresh_module, "report_owner_errors", fake_owner_errors)
    monkeypatch.setattr(refresh_module, "_git_dirty", lambda root: [])
    monkeypatch.setattr(refresh_module, "_git_head", lambda root: "fix-head")
    with pytest.raises(RefreshRefused, match="owner drift during native capture"):
        refresh(
            _stage_specs(tmp_path),
            REPO_ROOT,
            _out_dir(tmp_path),
            reason="r",
            run_native=True,
        )


def test_refresh_native_head_moved_during_capture_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    head_calls: list[int] = []

    def fake_head(root: Path) -> str:
        head_calls.append(1)
        return "head-before" if len(head_calls) == 1 else "head-after"

    _all_clear_census(monkeypatch)
    monkeypatch.setattr(refresh_module, "_run", _ok_run)
    monkeypatch.setattr(refresh_module, "report_owner_errors", lambda root: ())
    monkeypatch.setattr(refresh_module, "_git_dirty", lambda root: [])
    monkeypatch.setattr(refresh_module, "_git_head", fake_head)
    with pytest.raises(RefreshRefused, match="HEAD moved during native capture"):
        refresh(
            _stage_specs(tmp_path),
            REPO_ROOT,
            _out_dir(tmp_path),
            reason="r",
            run_native=True,
        )


def test_refresh_native_tree_drift_during_capture_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    dirty_calls: list[int] = []

    def fake_dirty(root: Path) -> list[str]:
        dirty_calls.append(1)
        return [] if len(dirty_calls) == 1 else [" M src/x.py"]

    _all_clear_census(monkeypatch)
    monkeypatch.setattr(refresh_module, "_run", _ok_run)
    monkeypatch.setattr(refresh_module, "report_owner_errors", lambda root: ())
    monkeypatch.setattr(refresh_module, "_git_dirty", fake_dirty)
    monkeypatch.setattr(refresh_module, "_git_head", lambda root: "fix-head")
    with pytest.raises(RefreshRefused, match="tree drifted during native capture"):
        refresh(
            _stage_specs(tmp_path),
            REPO_ROOT,
            _out_dir(tmp_path),
            reason="r",
            run_native=True,
        )


# ---------------------------------------------------------------------------
# Bridge cascade warning: the fep_formal half of the known signature.
# ---------------------------------------------------------------------------


def test_bridge_warning_names_the_drifted_owner(tmp_path: Path) -> None:
    root = tmp_path
    pin_dir = root / "specs" / "gnn-bridge-w2-source-custody"
    pin_dir.mkdir(parents=True)
    owner = pin_dir / "owner.json"
    owner.write_text("{}\n", encoding="utf-8")
    pin = {
        "fep_lean": {
            "owners": {"specs/gnn-bridge-w2-source-custody/owner.json": "0" * 64}
        }
    }
    (pin_dir / "source-pin.json").write_text(json.dumps(pin), encoding="utf-8")
    warning = _bridge_warning(root)
    assert warning is not None
    assert "specs/gnn-bridge-w2-source-custody/owner.json" in warning

    fresh = {
        "fep_lean": {
            "owners": {
                "specs/gnn-bridge-w2-source-custody/owner.json": _sha(
                    owner.read_bytes()
                )
            }
        }
    }
    (pin_dir / "source-pin.json").write_text(json.dumps(fresh), encoding="utf-8")
    assert _bridge_warning(root) is None


def test_bridge_warning_is_silent_without_a_pin(tmp_path: Path) -> None:
    assert _bridge_warning(tmp_path) is None


# ---------------------------------------------------------------------------
# CLI surface: parser choices, required reason, and the staged live-red path.
# ---------------------------------------------------------------------------


def test_cli_refresh_surface_parses() -> None:
    args = build_parser().parse_args(
        ["custody", "refresh", "--reason", "smoke", "--native"]
    )
    assert args.operation == "refresh"
    assert args.reason == "smoke"
    assert args.native is True
    assert args.authorized is None


def test_cli_refresh_refuses_empty_reason_with_json_error(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    exit_code = main_with_root(tmp_path, [])
    assert exit_code == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "error"
    assert "--reason" in payload["failure_reason"]


def test_cli_refresh_gate_refusal_names_the_surface_and_writes_nothing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Injected live-red on a staged copy: non-zero exit, real tree untouched."""
    specs_dir = _stage_specs(tmp_path)
    receipt = specs_dir / "done/horizon-2-smooth-stochastic/readiness"
    (receipt / "terminal-acceptance.json").write_bytes(b"{ not json")
    live_receipt = (
        REPO_ROOT / "specs/done/horizon-2-smooth-stochastic/readiness/"
        "terminal-acceptance.json"
    )
    live_before = _sha(live_receipt.read_bytes())
    out = tmp_path / "staged-output"
    exit_code = main_with_root(
        tmp_path,
        [
            "--specs-dir",
            str(specs_dir),
            "--output-dir",
            str(out),
            "--reason",
            "gate-test",
        ],
    )
    assert exit_code == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "error"
    assert "terminal-acceptance.json" in payload["failure_reason"]
    assert not out.exists()
    assert _sha(live_receipt.read_bytes()) == live_before


def test_cli_refresh_payload_native_status(
    synthetic_native_capture: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The payload taxonomy separates no-capture from claim-ready capture."""
    _all_clear_census(monkeypatch)
    monkeypatch.setattr(refresh_module, "_run", _ok_run)
    specs_dir = _stage_specs(tmp_path)
    exit_code = main_with_root(
        tmp_path,
        [
            "--specs-dir",
            str(specs_dir),
            "--output-dir",
            str(_out_dir(tmp_path)),
            "--reason",
            "fixture",
            "--native",
        ],
    )
    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "ok"
    assert payload["native_status"] == "captured_claim_ready"
    assert payload["native"]["validation"]["claim_ready"] is True

    exit_code = main_with_root(
        tmp_path,
        [
            "--specs-dir",
            str(specs_dir),
            "--output-dir",
            str(tmp_path / "output-no-native"),
            "--reason",
            "fixture",
        ],
    )
    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["native_status"] == "not_requested"
    assert payload["native"] == {}


# ---------------------------------------------------------------------------
# Helpers.
# ---------------------------------------------------------------------------


def main_with_root(tmp_path: Path, extra: list[str]) -> int:
    """Run the CLI with the project root pinned to this checkout."""
    return main(["--project-root", str(REPO_ROOT), "custody", "refresh", *extra])


@pytest.fixture()
def sandboxed_receipt(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirect the native receipt to a per-test sandbox path.

    The machinery resolves the receipt as ``root / NATIVE_RECEIPT`` from the
    module global; patching it to an absolute sandbox path redirects every
    resolution site (capture argv, post-capture checks, report payload) into
    ``tmp_path``. Parallel xdist workers therefore never share checkout
    state, and a run killed between a fixture write and its restore can
    never leak a receipt into the real checkout.
    """
    receipt = tmp_path / "receipts" / "native-verification.json"
    monkeypatch.setattr(refresh_module, "NATIVE_RECEIPT", str(receipt))
    return receipt


def _claim_ready_payload(root: Path) -> dict[str, object]:
    """Build a validator-accepted synthetic payload bound to the fixture tree.

    Rows are synthetic (every topic compiles clean) but the digests, roster,
    and toolchain identity are recomputed from the disposable source tree.
    No compiler runs; this exercises validation and composition, not actual
    native acceptance.
    """
    pin = pinned_lean_semver((root / "lean" / "lean-toolchain").read_text().strip())
    assert pin is not None, "lean-toolchain pin must be a canonical semver"
    version = f"Lean (version {pin}, fixture-toolchain, commit 000000000000)"
    catalogue = FEPTopicCatalogue.from_yaml(root / "config" / "topics.yaml")
    live_topic_ids = [topic.id for topic in catalogue.topics]
    rows = [
        {
            "topic_id": topic_id,
            "compiles": True,
            "has_sorry": False,
            "sorry_occurrences": 0,
            "warnings": [],
            "errors": [],
            "duration_s": 0.5,
            "lean_version": version,
        }
        for topic_id in live_topic_ids
    ]
    return build_native_lean_receipt(root, live_topic_ids, rows)


def _native_fixture_git(root: Path, *arguments: str) -> str:
    result = subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "-c",
            "commit.gpgsign=false",
            "-c",
            f"core.hooksPath={root / '.git/hooks'}",
            *arguments,
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


@pytest.fixture()
def canonical_native_root(
    tmp_path: Path,
    sandboxed_receipt: Path,
) -> Path:
    """Keep historical projections separate from a sealed current-source tree."""
    write_native_lean_receipt(sandboxed_receipt, _claim_ready_payload(REPO_ROOT))
    rejected = validate_native_lean_receipt(sandboxed_receipt, project_root=REPO_ROOT)
    assert not rejected["native_claim_ready"]
    assert rejected["errors"] and all(
        "source owner is absent from manifest" in error for error in rejected["errors"]
    )
    sandboxed_receipt.unlink()
    native_root = tmp_path / "canonical-native-project"
    excluded = {}
    for source in sorted(REPO_ROOT.rglob("*")):
        if not source.is_file():
            continue
        assert not source.is_symlink()
        relative = source.relative_to(REPO_ROOT).as_posix()
        if (
            relative.startswith("src/fep_lean/")
            and source.suffix == ".py"
            and relative not in SOURCE_OWNER_FILES
        ):
            excluded[relative] = _sha(source.read_bytes())
            continue
        destination = native_root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    assert excluded
    (tmp_path / "historical-projection-ledger.json").write_text(
        json.dumps(excluded, indent=2)
    )
    for relative, digest in excluded.items():
        assert _sha((REPO_ROOT / relative).read_bytes()) == digest
        assert not (native_root / relative).exists()
    for source in source_owner_paths(REPO_ROOT):
        assert (
            source.read_bytes()
            == (native_root / source.relative_to(REPO_ROOT)).read_bytes()
        )
    assert refresh_module.report_owner_errors(native_root) == ()
    (native_root / ".gitignore").write_text("output/\n")
    _native_fixture_git(native_root, "init", "--quiet")
    _native_fixture_git(native_root, "config", "user.name", "Synthetic custody fixture")
    _native_fixture_git(native_root, "config", "user.email", "fixture@example.invalid")
    _native_fixture_git(native_root, "add", "--all")
    _native_fixture_git(
        native_root, "commit", "--quiet", "-m", "Synthetic native source fixture"
    )
    assert refresh_module._git_dirty(native_root) == []
    return native_root


@pytest.mark.parametrize(
    ("scenario", "message"),
    [
        ("clean", None),
        ("owner_before", "pre-capture owner gate refused"),
        ("dirty_before", "requires a committed clean tip"),
        ("command_failure", "native capture failed"),
        ("dirty_after", "tree drifted during native capture"),
        ("head_after", "HEAD moved during native capture"),
        ("owner_after", "owner drift during native capture"),
        ("missing_receipt", "native receipt missing"),
        ("invalid_receipt", "native receipt is not claim-ready"),
        ("source_after", "native receipt is not claim-ready"),
    ],
)
def test_capture_native_real_source_boundaries(
    canonical_native_root: Path,
    sandboxed_receipt: Path,
    monkeypatch: pytest.MonkeyPatch,
    scenario: str,
    message: str | None,
) -> None:
    """Real Git/files/owner/receipt checks; synthetic compile rows only."""
    root = canonical_native_root
    payload = _claim_ready_payload(root)
    calls = []
    if scenario == "owner_before":
        (root / "src/fep_lean/unrostered.py").write_text("unrostered = True\n")
    elif scenario == "dirty_before":
        (root / "dirty.txt").write_text("dirty\n")

    def capture(*command: str, root: Path) -> dict[str, object]:
        assert root == canonical_native_root
        calls.append(list(command))
        if scenario == "command_failure":
            return {
                "command": list(command),
                "exit_code": 7,
                "tail": "synthetic failure",
            }
        if scenario != "missing_receipt":
            if scenario == "invalid_receipt":
                sandboxed_receipt.parent.mkdir(parents=True, exist_ok=True)
                sandboxed_receipt.write_text("{}")
            else:
                write_native_lean_receipt(sandboxed_receipt, payload)
        if scenario == "dirty_after":
            (root / "dirty.txt").write_text("dirty\n")
        elif scenario == "head_after":
            _native_fixture_git(
                root, "commit", "--quiet", "--allow-empty", "-m", "Moved fixture HEAD"
            )
        elif scenario == "owner_after":
            (root / ".git/info/exclude").write_text("src/fep_lean/unrostered.py\n")
            (root / "src/fep_lean/unrostered.py").write_text("unrostered = True\n")
            assert refresh_module._git_dirty(root) == []
        elif scenario == "source_after":
            relative = "src/fep_formal/_paths.py"
            _native_fixture_git(root, "update-index", "--assume-unchanged", relative)
            source = root / relative
            source.write_bytes(source.read_bytes() + b"\n# hidden source drift\n")
            assert refresh_module._git_dirty(root) == []
        return {"command": list(command), "exit_code": 0, "tail": ""}

    monkeypatch.setattr(refresh_module, "_run", capture)
    if message is None:
        result = refresh_module._capture_native(root)
        assert result["validation"]["claim_ready"] is True
        assert result["validation"]["source_bound"] is True
        assert validate_native_lean_receipt(sandboxed_receipt, project_root=root)[
            "native_claim_ready"
        ]
    else:
        with pytest.raises(RefreshRefused, match=message):
            refresh_module._capture_native(root)
    expected = (
        []
        if scenario in ("owner_before", "dirty_before")
        else [
            [
                "uv",
                "run",
                "fep-formal",
                "verify",
                "--fail-on-warnings",
                "--receipt",
                str(sandboxed_receipt),
            ]
        ]
    )
    assert calls == expected


@pytest.fixture()
def synthetic_native_capture(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[Path]:
    """Composition-only seam; independent helper tests own real native checks."""
    receipt = tmp_path / "synthetic-composition-native.json"
    receipt.write_text(
        json.dumps({"kind": "SYNTHETIC-COMPOSITION-NOT-NATIVE-EVIDENCE"})
    )
    roots = []

    def capture(root: Path) -> dict[str, Any]:
        assert root == REPO_ROOT
        roots.append(root)
        return {
            "command": [
                "uv",
                "run",
                "fep-formal",
                "verify",
                "--fail-on-warnings",
                "--receipt",
                str(receipt),
            ],
            "exit_code": 0,
            "receipt": str(receipt),
            "fixture_kind": "SYNTHETIC-COMPOSITION-NOT-NATIVE-EVIDENCE",
            "validation": {
                "claim_ready": True,
                "source_bound": True,
                "live_catalogue_topics": len(
                    FEPTopicCatalogue.from_yaml(REPO_ROOT / "config/topics.yaml").topics
                ),
                "errors": [],
            },
        }

    monkeypatch.setattr(refresh_module, "_capture_native", capture)
    yield receipt
    assert roots == [REPO_ROOT]


# ---------------------------------------------------------------------------
# Plan mode (t-0057 phase 1): read-only, journal state planned.
# ---------------------------------------------------------------------------


def _mode_ready(monkeypatch: pytest.MonkeyPatch, head: str = "plan-head") -> None:
    """Stub the shared plan/fixpoint seams for a clean committed tip."""
    _all_clear_census(monkeypatch)
    monkeypatch.setattr(refresh_module, "_git_dirty", lambda root: [])
    monkeypatch.setattr(refresh_module, "_git_head", lambda root: head)
    monkeypatch.setattr(refresh_module, "report_owner_errors", lambda root: ())


def test_plan_mode_writes_planned_journal_without_subprocesses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _mode_ready(monkeypatch)

    def bomb(*command: str, root: Path) -> dict[str, object]:
        raise AssertionError(f"plan mode ran a subprocess: {command}")

    monkeypatch.setattr(refresh_module, "_run", bomb)
    # Default location: REPO_ROOT/output/custody-journal/<operation-id>/,
    # deterministic from (head stub, reason, mode); cleaned up below.
    landed = (
        REPO_ROOT
        / refresh_module.JOURNAL_DIR
        / refresh_module._operation_id("plan-head", "planning pass", "plan")
        / "journal.json"
    )
    journal = plan_refresh(_stage_specs(tmp_path), REPO_ROOT, (), "planning pass")
    try:
        assert journal["state"] == "planned"
        assert journal["mode"] == "plan"
        assert journal["schema_version"] == 1
        assert journal["pre_commit_head"] == "plan-head"
        assert journal["reason"] == "planning pass"
        assert journal["owner_snapshot"], "owner snapshot must list owner digests"
        assert journal["owner_snapshot"][0]["path"]
        assert all(len(entry["sha256"]) == 64 for entry in journal["owner_snapshot"])
        assert journal["owner_errors"] == []
        assert journal["census"]["stale"] == []
        assert journal["census"]["live_red"] == []
        assert journal["verify_gate"] == {"ok": True, "problems": []}
        assert journal["pin_check"].startswith("direct check:")
        assert journal["phases"] == []
        assert journal["next_action"].startswith("coordinator commit")
        assert Path(journal["journal_path"]) == landed
        assert landed.is_file()
        on_disk = json.loads(landed.read_text(encoding="utf-8"))
        assert on_disk == journal
        assert on_disk["updated_at"].endswith("+00:00")
    finally:
        shutil.rmtree(landed.parent, ignore_errors=True)


def test_plan_mode_refuses_an_unreviewed_authorized_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _mode_ready(monkeypatch)
    with pytest.raises(RefreshRefused, match="unreviewed roster growth") as exc:
        plan_refresh(
            _stage_specs(tmp_path),
            REPO_ROOT,
            ("tests/test_horizon1_policy_action.py",),
            "r",
        )
    assert "tests/test_horizon1_policy_action.py" in str(exc.value)


def test_plan_mode_refuses_a_live_red_census(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _mode_ready(monkeypatch)
    record = CensusRecord(
        path="tests/test_horizon1_policy_action.py", status=LIVE_RED, detail="break"
    )
    monkeypatch.setattr(
        refresh_module, "census_from_tree", lambda specs, root: Census((record,))
    )
    with pytest.raises(RefreshRefused, match="live-red") as exc:
        plan_refresh(_stage_specs(tmp_path), REPO_ROOT, (), "r")
    assert "tests/test_horizon1_policy_action.py" in str(exc.value)


def test_plan_mode_refuses_a_dirty_tip(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _mode_ready(monkeypatch)
    monkeypatch.setattr(refresh_module, "_git_dirty", lambda root: [" M src/x.py"])
    with pytest.raises(RefreshRefused, match="committed clean tip"):
        plan_refresh(_stage_specs(tmp_path), REPO_ROOT, (), "r")


def test_plan_mode_authorizes_declared_staleness(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Stale inside --authorized passes the mode gate; outside refuses."""
    _mode_ready(monkeypatch)
    from fep_formal.custody.verify import GATE_EXPECTATIONS

    capture = "src/fep_formal/verification/numerical_witnesses.py"
    stale = CensusRecord(path=capture, status=STALE, detail="capture predates")

    def census_stub(specs: Path, root: Path) -> Census:
        required = tuple(
            CensusRecord(path=path, status=INTACT, detail="fixture intact")
            for path in GATE_EXPECTATIONS.required_intact
        )
        return Census((*required, stale))

    monkeypatch.setattr(refresh_module, "census_from_tree", census_stub)
    specs_dir = _stage_specs(tmp_path)
    with pytest.raises(RefreshRefused, match="custody verify gate refused"):
        plan_refresh(specs_dir, REPO_ROOT, (), "r")
    journal = plan_refresh(specs_dir, REPO_ROOT, (capture,), "authorized residual")
    assert journal["census"]["stale"] == [capture]
    assert journal["census"]["authorized"] == [capture]
    assert journal["state"] == "planned"


def test_plan_mode_refuses_a_pin_toolchain_mismatch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _mode_ready(monkeypatch)
    specs_dir = _stage_specs(tmp_path)
    matrix = specs_dir / "done/horizon-2-smooth-stochastic/readiness/matrix.yaml"
    matrix.write_text(
        matrix.read_text(encoding="utf-8").replace("lean: v4.34.1", "lean: v4.33.1", 1)
    )
    with pytest.raises(RefreshRefused, match="pin/toolchain mismatch"):
        plan_refresh(specs_dir, REPO_ROOT, (), "r")


def test_plan_journal_dir_override_lands_the_journal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _mode_ready(monkeypatch)
    override = tmp_path / "journal-override"
    journal = plan_refresh(
        _stage_specs(tmp_path), REPO_ROOT, (), "r", journal_dir=override
    )
    landed = Path(journal["journal_path"])
    assert landed.parent.parent == override
    assert landed.name == "journal.json"
    assert landed.is_file()


def test_cli_plan_missing_reason_stops(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    exit_code = main_with_root(tmp_path, ["--plan"])
    assert exit_code == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "error"
    assert "--reason" in payload["failure_reason"]


def test_cli_plan_happy_path_journals_under_the_override(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _mode_ready(monkeypatch)

    def bomb(*command: str, root: Path) -> dict[str, object]:
        raise AssertionError(f"plan mode ran a subprocess: {command}")

    monkeypatch.setattr(refresh_module, "_run", bomb)
    override = tmp_path / "journals"
    exit_code = main_with_root(
        tmp_path,
        ["--plan", "--reason", "cli plan", "--journal-dir", str(override)],
    )
    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "ok"
    assert payload["mode"] == "plan"
    assert payload["state"] == "planned"
    assert Path(payload["journal_path"]).is_file()
    assert Path(payload["journal_path"]).parent.parent == override


def test_cli_refresh_modes_are_mutually_exclusive() -> None:
    with pytest.raises(SystemExit):
        build_parser().parse_args(
            ["custody", "refresh", "--plan", "--fixpoint", "--reason", "r"]
        )
    with pytest.raises(SystemExit):
        build_parser().parse_args(
            ["custody", "refresh", "--plan", "--resume", "j", "--reason", "r"]
        )
    args = build_parser().parse_args(
        ["custody", "refresh", "--resume", "some/journal", "--reason", "r"]
    )
    assert args.resume == Path("some/journal")
    assert args.max_rounds == 4
    assert args.journal_dir is None


def test_cli_resume_refuses_without_output_dir(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Resume mode is an evidence-composing mode: it requires --output-dir."""
    _mode_ready(monkeypatch)
    monkeypatch.setattr(
        refresh_module, "_git_head", lambda root: "not-the-journal-head"
    )
    exit_code = main_with_root(tmp_path, ["--resume", "some/journal", "--reason", "r"])
    assert exit_code == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "error"
    assert "--output-dir" in payload["failure_reason"]


# ---------------------------------------------------------------------------
# Fixpoint mode (t-0057 phase 2): bounded staged fixpoint with the chain.
# ---------------------------------------------------------------------------


def _fixpoint_drift_fixture(tmp_path: Path) -> tuple[Path, tuple[str, ...]]:
    """The historical two-pass shape: re-issues in round 1, settled by round 2."""
    root = fixture_root(tmp_path)
    drifted = ("tests/test_horizon_acceptance.py", "tests/test_numerical_witnesses.py")
    for name in drifted:
        drift_file(root / name)
    drift_file(spec_path(root, SUCCESSOR_07), JSON_WHITESPACE_DRIFT)
    return root, (*drifted, SUCCESSOR_07)


def test_fixpoint_converges_by_round_two_with_the_carry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, authorized = _fixpoint_drift_fixture(tmp_path)
    _mode_ready(monkeypatch)
    out = tmp_path / "output"
    journal = fixpoint_refresh(root / "specs", root, out, authorized, "fixpoint")
    assert journal["state"] == "awaiting-commit"
    assert journal["mode"] == "fixpoint"
    rounds = journal["phases"]
    assert len(rounds) == 2
    first, second = rounds
    assert first["mutations"], "round 1 must mutate the staged receipts"
    assert first["directives"], "round 1 must emit the predecessors directive"
    assert first["converged"] is False
    assert second["zero_mutations"] is True
    assert second["zero_directives"] is True
    assert second["byte_identical_reapplication"] is True
    assert second["converged"] is True
    # Cycle evidence: no state hash repeats before convergence.
    assert first["input_state_hash"] != second["input_state_hash"]
    assert second["input_state_hash"] == first["output_state_hash"]
    assert journal["evidence_note"].startswith("receipt re-issues")
    candidate = Path(journal["staged_candidate"])
    assert candidate.is_dir()
    assert Path(
        candidate / "done/horizon-2-smooth-stochastic/readiness/matrix.yaml"
    ).is_file()
    landed = Path(journal["journal_path"])
    assert json.loads(landed.read_text(encoding="utf-8"))["state"] == "awaiting-commit"


def test_fixpoint_sealed_tree_converges_at_round_one(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = fixture_root(tmp_path)
    _mode_ready(monkeypatch)
    journal = fixpoint_refresh(
        root / "specs", root, tmp_path / "output", reason="sealed"
    )
    assert journal["state"] == "awaiting-commit"
    assert len(journal["phases"]) == 1
    only = journal["phases"][0]
    assert only["round"] == 1
    assert only["converged"] is True
    assert only["byte_identical_reapplication"] is True
    assert only["mutations"] == []
    assert only["directives"] == []


def test_fixpoint_did_not_converge_within_the_bound(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, authorized = _fixpoint_drift_fixture(tmp_path)
    _mode_ready(monkeypatch)
    with pytest.raises(RefreshRefused, match="did not converge within 1 rounds"):
        fixpoint_refresh(
            root / "specs", root, tmp_path / "output", authorized, "bound", max_rounds=1
        )


def test_fixpoint_cycle_detection_refuses_a_repeated_state_hash(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, authorized = _fixpoint_drift_fixture(tmp_path)
    _mode_ready(monkeypatch)
    monkeypatch.setattr(
        refresh_module, "_state_hash", lambda specs, overlay: "constant-hash"
    )
    with pytest.raises(RefreshRefused, match="fixpoint cycle detected at round 2"):
        fixpoint_refresh(root / "specs", root, tmp_path / "output", authorized, "cycle")


def test_fixpoint_mode_gates_mirror_plan_mode(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = fixture_root(tmp_path)
    _mode_ready(monkeypatch)
    monkeypatch.setattr(refresh_module, "_git_dirty", lambda root: [" M src/x.py"])
    with pytest.raises(RefreshRefused, match="fixpoint requires a committed clean tip"):
        fixpoint_refresh(root / "specs", root, tmp_path / "output", reason="r")
    monkeypatch.setattr(refresh_module, "_git_dirty", lambda root: [])
    monkeypatch.setattr(refresh_module, "report_owner_errors", lambda root: ("boom",))
    with pytest.raises(RefreshRefused, match="fixpoint owner gate refused"):
        fixpoint_refresh(root / "specs", root, tmp_path / "output", reason="r")
    monkeypatch.setattr(refresh_module, "report_owner_errors", lambda root: ())
    record = CensusRecord(
        path="tests/test_horizon1_policy_action.py", status=LIVE_RED, detail="break"
    )
    monkeypatch.setattr(
        refresh_module, "census_from_tree", lambda specs, root: Census((record,))
    )
    with pytest.raises(RefreshRefused, match="custody verify gate refused"):
        fixpoint_refresh(root / "specs", root, tmp_path / "output", reason="r")


def test_cli_fixpoint_refuses_without_output_dir(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _mode_ready(monkeypatch)
    exit_code = main_with_root(tmp_path, ["--fixpoint", "--reason", "r"])
    assert exit_code == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "error"
    assert "--output-dir" in payload["failure_reason"]


def test_cli_fixpoint_gate_refusal_exits_one(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _mode_ready(monkeypatch)
    monkeypatch.setattr(refresh_module, "_git_dirty", lambda root: [" M src/x.py"])
    exit_code = main_with_root(
        tmp_path,
        ["--fixpoint", "--reason", "r", "--output-dir", str(tmp_path / "out")],
    )
    assert exit_code == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "error"
    assert "committed clean tip" in payload["failure_reason"]


def test_cli_fixpoint_happy_path_payload(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Specs-side drift drives a round-1 directive; the carry settles round 2.

    The CLI pins the project root to this checkout, so the drift lives in
    the staged specs tree: the drifted successor receipt's digest breaks its
    PREDECESSORS pin, round 1 emits the directive, and the carried
    projection settles round 2 to awaiting-commit.
    """
    _mode_ready(monkeypatch)
    specs_dir = _stage_specs(tmp_path)
    successor = specs_dir / SUCCESSOR_07[len("specs/") :]
    successor.write_bytes(successor.read_bytes() + JSON_WHITESPACE_DRIFT)
    out = tmp_path / "output"
    payload: dict[str, Any] = {}
    exit_code = main_with_root(
        tmp_path,
        [
            "--specs-dir",
            str(specs_dir),
            "--output-dir",
            str(out),
            "--reason",
            "cli fixpoint",
            "--fixpoint",
            "--authorized",
            SUCCESSOR_07,
        ],
    )
    try:
        assert exit_code == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload["status"] == "ok"
        assert payload["mode"] == "fixpoint"
        assert payload["state"] == "awaiting-commit"
        assert payload["rounds_completed"] == 2
        assert len(payload["phases"]) == 2
        assert payload["phases"][0]["directives"], "round 1 must emit the pin patch"
        assert payload["phases"][1]["converged"] is True
        assert Path(payload["journal_path"]).is_file()
        assert Path(payload["staged_candidate"]).is_dir()
    finally:
        shutil.rmtree(Path(payload["journal_path"]).parent, ignore_errors=True)


# ---------------------------------------------------------------------------
# Resume mode (t-0057 phase 3): commit barrier, render-acceptance gate,
# composed verify set, optional native capture, journal terminal state.
# ---------------------------------------------------------------------------


FIXTURE_PATH = "tests/_support/custody_fixture_knobs.py"


def _head_bytes(relative: str) -> bytes:
    """Read the explicit synthetic committed-byte seam, independent of drift."""
    data = refresh_module._git_show(REPO_ROOT, relative)
    assert data is not None, relative
    return data


def _resume_journal(
    tmp_path: Path,
    *,
    mode: str = "fixpoint",
    state: str = "awaiting-commit",
    pre_commit_head: str = "journal-head",
    changed_paths: dict[str, str] | None = None,
    render_barrier_paths: list[str] | None = None,
) -> Path:
    """Land a journal in a temp dir; returns the operation directory."""
    if changed_paths is None:
        data = (REPO_ROOT / FIXTURE_PATH).read_bytes()
        changed_paths = {FIXTURE_PATH: _sha(data)}
    journals = tmp_path / "journals"
    journals.mkdir(exist_ok=True)
    operation = journals / f"op-{len(list(journals.iterdir())) + 1}"
    operation.mkdir(parents=True)
    journal_path = operation / "journal.json"
    journal: dict[str, Any] = {
        "schema_version": 1,
        "mode": mode,
        "reason": "resume fixture",
        "authorized": [FIXTURE_PATH],
        "pre_commit_head": pre_commit_head,
        "changed_paths": changed_paths,
        "owner_snapshot": [],
        "owner_errors": [],
        "census": {"stale": [], "live_red": [], "authorized": [FIXTURE_PATH]},
        "verify_gate": {"ok": True, "problems": []},
        "pin_check": "fixture",
        "state": state,
        "updated_at": "2026-01-01T00:00:00+00:00",
    }
    if mode == "fixpoint":
        journal["phases"] = []
        journal["rounds_completed"] = 1
        journal["staged_candidate"] = str(tmp_path / "candidate")
        journal["evidence_note"] = "receipt re-issues are dependency re-binds"
    journal["render_barrier_paths"] = render_barrier_paths or []
    journal["journal_path"] = str(journal_path)
    journal_path.write_text(json.dumps(journal, indent=2) + "\n", encoding="utf-8")
    return operation


def _resume_ready(
    monkeypatch: pytest.MonkeyPatch,
    *,
    head: str = "committed-tip",
) -> list[list[str]]:
    """Stub the resume seams for a committed candidate tip; returns _run calls."""
    calls: list[list[str]] = []

    def spy_run(*command: str, root: Path) -> dict[str, object]:
        calls.append(list(command))
        return _ok_run(*command, root=root)

    _all_clear_census(monkeypatch)
    monkeypatch.setattr(refresh_module, "_run", spy_run)
    monkeypatch.setattr(refresh_module, "_bridge_warning", lambda root: None)
    monkeypatch.setattr(refresh_module, "_git_dirty", lambda root: [])
    monkeypatch.setattr(refresh_module, "_git_head", lambda root: head)
    monkeypatch.setattr(refresh_module, "report_owner_errors", lambda root: ())
    return calls


def test_resume_happy_path_completes_verify_set_without_capture(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Committed candidate + clean gates → verify set at the tip, state captured."""
    calls = _resume_ready(monkeypatch)
    operation = _resume_journal(tmp_path, pre_commit_head="journal-head")
    journal = resume_refresh(
        REPO_ROOT / "specs",
        REPO_ROOT,
        tmp_path / "output",
        operation,
        reason="resume fixture",
    )
    assert journal["state"] == "captured"
    assert set(journal["verify_set"]) == VERIFY_SET_KEYS
    assert journal["native"] == {"status": "capture_not_requested"}
    assert journal["resume_head"] == "committed-tip"
    assert journal["resume_attempts"] == 1
    # The three verify-set subprocesses ran through the composed refresh().
    assert len(calls) == 3
    assert all(command[0] == "uv" for command in calls)
    assert not any(command[2:4] == ["fep-formal", "verify"] for command in calls)
    landed = json.loads((operation / "journal.json").read_text(encoding="utf-8"))
    assert landed["state"] == "captured"
    assert landed["native"] == {"status": "capture_not_requested"}


def test_resume_refuses_a_missing_journal(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _resume_ready(monkeypatch)
    with pytest.raises(RefreshRefused, match="journal not found"):
        resume_refresh(
            REPO_ROOT / "specs",
            REPO_ROOT,
            tmp_path / "output",
            tmp_path / "nope",
            reason="r",
        )


def test_resume_parent_directory_with_one_operation_child_resolves(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = _resume_ready(monkeypatch)
    operation = _resume_journal(tmp_path, pre_commit_head="journal-head")
    journal = resume_refresh(
        REPO_ROOT / "specs",
        REPO_ROOT,
        tmp_path / "output",
        operation.parent,
        reason="resume fixture",
    )
    assert journal["state"] == "captured"
    assert len(calls) == 3


def test_resume_refuses_an_already_captured_journal(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _resume_ready(monkeypatch)
    operation = _resume_journal(tmp_path, state="captured")
    with pytest.raises(RefreshRefused, match="not resumable"):
        resume_refresh(
            REPO_ROOT / "specs",
            REPO_ROOT,
            tmp_path / "output",
            operation,
            reason="r",
        )


def test_resume_refuses_an_unknown_mode(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _resume_ready(monkeypatch)
    operation = _resume_journal(tmp_path, mode="apply")
    with pytest.raises(RefreshRefused, match="not resumable"):
        resume_refresh(
            REPO_ROOT / "specs",
            REPO_ROOT,
            tmp_path / "output",
            operation,
            reason="r",
        )


def test_resume_refuses_when_head_is_unchanged(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _resume_ready(monkeypatch, head="journal-head")
    operation = _resume_journal(tmp_path, pre_commit_head="journal-head")
    with pytest.raises(RefreshRefused, match="committed first"):
        resume_refresh(
            REPO_ROOT / "specs",
            REPO_ROOT,
            tmp_path / "output",
            operation,
            reason="r",
        )


def test_resume_refuses_a_dirty_tip(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _resume_ready(monkeypatch)
    monkeypatch.setattr(refresh_module, "_git_dirty", lambda root: [" M src/x.py"])
    operation = _resume_journal(tmp_path)
    with pytest.raises(RefreshRefused, match="committed clean tip"):
        resume_refresh(
            REPO_ROOT / "specs",
            REPO_ROOT,
            tmp_path / "output",
            operation,
            reason="r",
        )


def test_resume_refuses_on_committed_bytes_mismatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A journal digest differing from HEAD's bytes means amended/wrong commit."""
    _resume_ready(monkeypatch)
    operation = _resume_journal(tmp_path, changed_paths={FIXTURE_PATH: "f" * 64})
    with pytest.raises(RefreshRefused, match="do not match") as exc:
        resume_refresh(
            REPO_ROOT / "specs",
            REPO_ROOT,
            tmp_path / "output",
            operation,
            reason="r",
        )
    assert FIXTURE_PATH in str(exc.value)


def test_resume_refuses_an_untracked_changed_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _resume_ready(monkeypatch)
    operation = _resume_journal(tmp_path, changed_paths={"specs/nope.json": "0" * 64})
    with pytest.raises(RefreshRefused, match="not tracked at HEAD"):
        resume_refresh(
            REPO_ROOT / "specs",
            REPO_ROOT,
            tmp_path / "output",
            operation,
            reason="r",
        )


def test_resume_refuses_owner_errors(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _resume_ready(monkeypatch)
    monkeypatch.setattr(
        refresh_module,
        "report_owner_errors",
        lambda root: ("source owner is absent from manifest v23: x.py",),
    )
    operation = _resume_journal(tmp_path)
    with pytest.raises(RefreshRefused, match="resume owner gate refused"):
        resume_refresh(
            REPO_ROOT / "specs",
            REPO_ROOT,
            tmp_path / "output",
            operation,
            reason="r",
        )


def test_resume_refuses_a_live_red_census(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _resume_ready(monkeypatch)
    record = CensusRecord(
        path="tests/test_horizon1_policy_action.py", status=LIVE_RED, detail="break"
    )
    monkeypatch.setattr(
        refresh_module, "census_from_tree", lambda specs, root: Census((record,))
    )
    operation = _resume_journal(tmp_path)
    with pytest.raises(RefreshRefused, match="live-red"):
        resume_refresh(
            REPO_ROOT / "specs",
            REPO_ROOT,
            tmp_path / "output",
            operation,
            reason="r",
        )


def test_resume_refuses_when_the_walk_is_not_a_noop(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """One mutation in the verification round means the commit is not agreed."""
    from fep_formal.custody.apply import ApplyReport

    _resume_ready(monkeypatch)

    def spy_apply(*args: Any, **kwargs: Any) -> ApplyReport:
        return ApplyReport(
            phases=("stub-phase",),
            mutations=("specs/done/x/receipt.json",),
            directives=(),
            output_dir="stub",
            files_written=0,
        )

    monkeypatch.setattr(refresh_module, "apply_refresh", spy_apply)
    operation = _resume_journal(tmp_path)
    with pytest.raises(RefreshRefused, match="not the agreed candidate") as exc:
        resume_refresh(
            REPO_ROOT / "specs",
            REPO_ROOT,
            tmp_path / "output",
            operation,
            reason="r",
        )
    assert "receipt.json" in str(exc.value)


def test_resume_barrier_fires_before_any_capture(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The render barrier precedes the verify set and any native capture argv."""

    def bomb(*command: str, root: Path) -> dict[str, object]:
        raise AssertionError(f"resume ran a subprocess at the barrier: {command}")

    _resume_ready(monkeypatch)
    monkeypatch.setattr(refresh_module, "_run", bomb)
    docs = _head_bytes("docs/development.md")
    operation = _resume_journal(
        tmp_path, changed_paths={"docs/development.md": _sha(docs)}
    )
    with pytest.raises(RefreshRefused, match="render-acceptance barrier") as exc:
        resume_refresh(
            REPO_ROOT / "specs",
            REPO_ROOT,
            tmp_path / "output",
            operation,
            reason="r",
        )
    assert "docs/development.md" in str(exc.value)
    landed = json.loads((operation / "journal.json").read_text(encoding="utf-8"))
    assert landed["state"] == "awaiting-render-acceptance"
    assert landed["render_barrier_paths"] == ["docs/development.md"]
    assert landed["render_barriers"][-1]["paths"] == ["docs/development.md"]
    assert "render re-acceptance" in landed["next_action"]


def test_resume_barrier_acknowledged_on_reinvocation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Second resume with unchanged barrier paths: re-validate, then proceed."""
    calls = _resume_ready(monkeypatch)
    docs = _head_bytes("docs/development.md")
    changed = {"docs/development.md": _sha(docs)}
    operation = _resume_journal(tmp_path, changed_paths=changed)
    with pytest.raises(RefreshRefused, match="render-acceptance barrier"):
        resume_refresh(
            REPO_ROOT / "specs",
            REPO_ROOT,
            tmp_path / "output",
            operation,
            reason="r",
        )
    # Re-invocation must validate the actual acceptance rather than imply it.
    accepted = {"receipt_sha256": "a" * 64}
    monkeypatch.setattr(
        refresh_module, "_validate_render_acceptance", lambda root: accepted
    )
    journal = resume_refresh(
        REPO_ROOT / "specs",
        REPO_ROOT,
        tmp_path / "output",
        operation,
        reason="r",
    )
    assert journal["state"] == "captured"
    assert journal["render_barrier_paths"] == []
    assert journal["resume_attempts"] == 1  # the barrier stop never counted
    assert journal["render_acceptance"] == accepted
    assert len(calls) == 3  # verify set ran only on the acknowledged pass
    landed = json.loads((operation / "journal.json").read_text(encoding="utf-8"))
    assert landed["state"] == "captured"
    assert len(landed["render_barriers"]) == 1
    barrier = landed["render_barriers"][0]
    assert barrier["paths"] == ["docs/development.md"]
    assert barrier["triggered_at"].endswith("+00:00")


def test_resume_barrier_rearms_on_a_new_render_input(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A changed-path set with a NEW render input re-triggers the barrier."""
    _resume_ready(monkeypatch)
    docs = _head_bytes("docs/development.md")
    knobs = (REPO_ROOT / FIXTURE_PATH).read_bytes()
    changed = {
        "docs/development.md": _sha(docs),
        FIXTURE_PATH: _sha(knobs),
        "src/fep_formal/output/rendering.py": _sha(
            _head_bytes("src/fep_formal/output/rendering.py")
        ),
    }
    operation = _resume_journal(tmp_path, changed_paths=changed)
    with pytest.raises(RefreshRefused, match="render-acceptance barrier"):
        resume_refresh(
            REPO_ROOT / "specs",
            REPO_ROOT,
            tmp_path / "output",
            operation,
            reason="r",
        )
    first = json.loads((operation / "journal.json").read_text(encoding="utf-8"))
    assert first["state"] == "awaiting-render-acceptance"
    assert first["render_barrier_paths"] == [
        "docs/development.md",
        "src/fep_formal/output/rendering.py",
    ]
    # Validate an accepted render before the re-invocation proceeds.
    monkeypatch.setattr(
        refresh_module,
        "_validate_render_acceptance",
        lambda root: {"receipt_sha256": "a" * 64},
    )
    journal = resume_refresh(
        REPO_ROOT / "specs",
        REPO_ROOT,
        tmp_path / "output",
        operation,
        reason="r",
    )
    assert journal["state"] == "captured"
    # A NEW render input after acknowledgment re-arms the barrier: rebuild a
    # fresh resumable journal (state awaiting-commit) with the new path added.
    render_script = _head_bytes("scripts/render_manuscript.py")
    rearmed_operation = _resume_journal(
        tmp_path,
        changed_paths={
            **changed,
            "scripts/render_manuscript.py": _sha(render_script),
        },
    )
    landed_path = rearmed_operation / "journal.json"
    with pytest.raises(RefreshRefused, match="render-acceptance barrier"):
        resume_refresh(
            REPO_ROOT / "specs",
            REPO_ROOT,
            tmp_path / "output",
            rearmed_operation,
            reason="r",
        )
    rearmed = json.loads(landed_path.read_text(encoding="utf-8"))
    assert rearmed["state"] == "awaiting-render-acceptance"
    assert rearmed["render_barrier_paths"] == [
        "docs/development.md",
        "scripts/render_manuscript.py",
        "src/fep_formal/output/rendering.py",
    ]


def test_resume_reinvocation_cannot_acknowledge_a_rejected_render(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = _resume_ready(monkeypatch)
    changed = {"docs/development.md": _sha(_head_bytes("docs/development.md"))}
    operation = _resume_journal(tmp_path, changed_paths=changed)
    with pytest.raises(RefreshRefused, match="render-acceptance barrier"):
        resume_refresh(
            REPO_ROOT / "specs", REPO_ROOT, tmp_path / "output", operation, reason="r"
        )

    def rejected(root: Path) -> dict[str, str]:
        raise RefreshRefused("render-acceptance barrier: stale manuscript")

    monkeypatch.setattr(refresh_module, "_validate_render_acceptance", rejected)
    with pytest.raises(RefreshRefused, match="stale manuscript"):
        resume_refresh(
            REPO_ROOT / "specs", REPO_ROOT, tmp_path / "output", operation, reason="r"
        )
    landed = json.loads((operation / "journal.json").read_text())
    assert landed["state"] == "awaiting-render-acceptance"
    assert "render_acceptance" not in landed
    assert calls == []


def _render_candidate(root: Path) -> Path:
    from fep_formal.output.render_log import build_acceptance_receipt

    manuscript = root / "manuscript"
    manuscript.mkdir()
    (manuscript / "01_abstract.md").write_text("A named scientific model.\n")
    (manuscript / "09z_unified_formalism_catalogue.md").write_text("# Catalogue\n")
    (manuscript / "config.yaml").write_text("title: Render barrier fixture\n")
    (manuscript / "references.bib").write_text("% Render barrier reference input.\n")
    pdf = root / "output/pdf"
    pdf.mkdir(parents=True)
    (pdf / "_combined_manuscript.tex").write_text(
        "\\begin{document}\n\\begin{equation}\nx=y\n\\end{equation}\n\\end{document}\n"
    )
    counts = dict.fromkeys(
        (
            "tex_errors",
            "missing_characters",
            "mermaid_fallbacks",
            "stale_sources",
            "uncaptioned_tables",
            "contents_number_overflows",
            "unresolved_references",
            "publication_cover",
            "unnumbered_equations",
        ),
        0,
    )
    receipt = root / "docs/render-acceptance.json"
    receipt.parent.mkdir()
    receipt.write_text(
        json.dumps(build_acceptance_receipt(manuscript, pdf, counts=counts))
    )
    provenance = root / "output/manuscript/renderer-provenance.json"
    provenance.parent.mkdir(parents=True)
    provenance.write_text('{"fixture": true}\n')
    return receipt


@pytest.mark.parametrize(
    "defect",
    (
        "missing",
        "rejected",
        "stale",
        "malformed",
        "stale_config",
        "stale_references",
        "unnumbered_equations",
    ),
)
def test_render_barrier_rejects_invalid_receipts_before_reproduction(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, defect: str
) -> None:
    from fep_formal.output import release_bundle

    receipt = _render_candidate(tmp_path)
    if defect == "missing":
        receipt.unlink()
    elif defect == "rejected":
        payload = json.loads(receipt.read_text())
        payload["accepted"] = False
        receipt.write_text(json.dumps(payload))
    elif defect == "malformed":
        receipt.write_text("invalid JSON")
    elif defect == "stale_config":
        (tmp_path / "manuscript/config.yaml").write_text("title: Changed fixture\n")
    elif defect == "stale_references":
        (tmp_path / "manuscript/references.bib").write_text(
            "% Changed reference input.\n"
        )
    elif defect == "unnumbered_equations":
        payload = json.loads(receipt.read_text())
        payload["checks"]["unnumbered_equations"] = 1
        receipt.write_text(json.dumps(payload))
    else:
        (tmp_path / "manuscript/01_abstract.md").write_text("Changed model.\n")

    def forbidden(root: Path) -> tuple[str, ...]:
        raise AssertionError("invalid acceptance launched publication reproduction")

    monkeypatch.setattr(release_bundle, "publication_manuscript_errors", forbidden)
    with pytest.raises(RefreshRefused, match="render-acceptance barrier"):
        refresh_module._validate_render_acceptance(tmp_path)


@pytest.mark.parametrize(
    "defect", ("none", "hydration_drift", "output_drift", "source_race", "receipt_race")
)
def test_render_barrier_binds_acceptance_and_independent_reproduction(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, defect: str
) -> None:
    from fep_formal.output import release_bundle

    receipt = _render_candidate(tmp_path)
    before = receipt.read_bytes()
    calls: list[Path] = []
    hydration_calls: list[Path] = []

    def hydrate_check(root: Path) -> tuple[str, ...]:
        hydration_calls.append(root)
        if defect == "hydration_drift":
            return ("rendered manuscript is stale: output/manuscript/01_abstract.md",)
        return ()

    def reproduce(root: Path) -> tuple[str, ...]:
        calls.append(root)
        if defect == "output_drift":
            return (
                "publication manuscript member is stale: output/manuscript/fep.pdf",
            )
        if defect == "source_race":
            (root / "manuscript/01_abstract.md").write_text("Changed during check.\n")
        elif defect == "receipt_race":
            receipt.write_text(receipt.read_text() + "\n")
        return ()

    monkeypatch.setattr(release_bundle, "publication_manuscript_errors", reproduce)
    monkeypatch.setattr(release_bundle, "_rendered_manuscript_errors", hydrate_check)
    if defect == "none":
        accepted = refresh_module._validate_render_acceptance(tmp_path)
        assert accepted["receipt_sha256"] == _sha(before)
        assert len(accepted["renderer_provenance_sha256"]) == 64
    else:
        with pytest.raises(RefreshRefused, match="render-acceptance barrier"):
            refresh_module._validate_render_acceptance(tmp_path)
    assert hydration_calls == [tmp_path]
    assert calls == ([] if defect == "hydration_drift" else [tmp_path])


def test_resume_native_happy_path_captures_claim_ready(
    synthetic_native_capture: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """--native on resume: the composed capture runs and the journal records it."""
    calls = _resume_ready(monkeypatch)
    operation = _resume_journal(tmp_path)
    journal = resume_refresh(
        REPO_ROOT / "specs",
        REPO_ROOT,
        tmp_path / "output",
        operation,
        reason="resume fixture",
        run_native=True,
    )
    assert journal["state"] == "captured"
    assert journal["native"]["validation"]["claim_ready"] is True
    capture = [c for c in calls if c[2:4] == ["fep-formal", "verify"]]
    assert capture == []
    assert (
        journal["native"]["fixture_kind"] == "SYNTHETIC-COMPOSITION-NOT-NATIVE-EVIDENCE"
    )


def test_resume_journal_atomic_rewrite_preserves_landed_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The terminal rewrite keeps the operation id directory and no tmp litter."""
    calls = _resume_ready(monkeypatch)
    operation = _resume_journal(tmp_path)
    journal = resume_refresh(
        REPO_ROOT / "specs",
        REPO_ROOT,
        tmp_path / "output",
        operation,
        reason="resume fixture",
    )
    assert journal["journal_path"] == str(operation / "journal.json")
    assert (operation / "journal.json").is_file()
    assert list(operation.iterdir()) == [operation / "journal.json"]
    assert len(calls) == 3


def test_render_barrier_paths_matches_the_documented_surface() -> None:
    """Exact-match files and manuscript/docs prefix hits, per the docs table."""
    assert _render_barrier_paths(
        [
            "manuscript/sections/intro.tex",
            "src/fep_formal/output/rendering.py",
            "scripts/render_publication.py",
            "render.py",
            "scripts/render_manuscript.py",
            "docs/pin_audit.py",
            "src/fep_formal/custody/refresh.py",
        ]
    ) == [
        "manuscript/sections/intro.tex",
        "src/fep_formal/output/rendering.py",
        "scripts/render_publication.py",
        "render.py",
        "scripts/render_manuscript.py",
        "docs/pin_audit.py",
    ]
    assert RENDER_INPUTS == (
        "manuscript/",
        "src/fep_formal/output/rendering.py",
        "scripts/render_publication.py",
        "render.py",
        "scripts/render_manuscript.py",
        "docs/",
    )


def test_journal_loader_supports_operation_dir_and_parent(
    tmp_path: Path,
) -> None:
    operation = _resume_journal(tmp_path)
    journal = _load_journal(operation, REPO_ROOT)
    assert journal["mode"] == "fixpoint"
    parent = _load_journal(operation.parent, REPO_ROOT)
    assert parent == journal
    with pytest.raises(RefreshRefused, match="journal not found"):
        _load_journal(tmp_path, REPO_ROOT)


def test_fixpoint_journal_carries_changed_paths_for_resume(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The phase-2 producer now records the candidate digests resume digests."""
    root, authorized = _fixpoint_drift_fixture(tmp_path)
    _mode_ready(monkeypatch)
    journal = fixpoint_refresh(
        root / "specs", root, tmp_path / "output", authorized, "fixpoint"
    )
    changed = journal["changed_paths"]
    assert changed, "the candidate must record its changed paths"
    assert SUCCESSOR_07 in changed
    staged = Path(journal["staged_candidate"])
    staged_digest = _sha((staged / SUCCESSOR_07[len("specs/") :]).read_bytes())
    assert changed[SUCCESSOR_07] == staged_digest
    # The projected directive path enters the record with its digest too.
    directives = journal["phases"][0]["directives"]
    assert all(directive["path"] in changed for directive in directives)


def test_plan_journal_changed_paths_match_owner_snapshot(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _mode_ready(monkeypatch)
    journal = plan_refresh(_stage_specs(tmp_path), REPO_ROOT, (), "planning pass")
    landed = Path(journal["journal_path"])
    try:
        expected = {
            entry["path"]: entry["sha256"]
            for entry in journal["owner_snapshot"]
            if entry["sha256"] != "missing"
        }
        assert journal["changed_paths"] == expected
        on_disk = json.loads(landed.read_text(encoding="utf-8"))
        assert on_disk["changed_paths"] == expected
    finally:
        shutil.rmtree(landed.parent, ignore_errors=True)


def test_cli_resume_happy_path_payload(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    calls = _resume_ready(monkeypatch)
    operation = _resume_journal(tmp_path, pre_commit_head="journal-head")
    exit_code = main_with_root(
        tmp_path,
        [
            "--resume",
            str(operation),
            "--output-dir",
            str(tmp_path / "output"),
            "--reason",
            "resume fixture",
        ],
    )
    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "ok"
    assert payload["state"] == "captured"
    assert payload["native_status"] == "not_requested"
    assert payload["native"] == {"status": "capture_not_requested"}
    assert set(payload["verify_set"]) == VERIFY_SET_KEYS
    assert len(calls) == 3
    landed = json.loads((operation / "journal.json").read_text(encoding="utf-8"))
    assert landed["state"] == "captured"


def test_cli_resume_committed_bytes_mismatch_exits_one(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _resume_ready(monkeypatch)
    operation = _resume_journal(tmp_path, changed_paths={FIXTURE_PATH: "f" * 64})
    exit_code = main_with_root(
        tmp_path,
        [
            "--resume",
            str(operation),
            "--output-dir",
            str(tmp_path / "output"),
            "--reason",
            "r",
        ],
    )
    assert exit_code == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "error"
    assert "do not match" in payload["failure_reason"]


def test_cli_resume_render_barrier_exits_one_with_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _resume_ready(monkeypatch)
    docs = _head_bytes("docs/development.md")
    operation = _resume_journal(
        tmp_path, changed_paths={"docs/development.md": _sha(docs)}
    )
    exit_code = main_with_root(
        tmp_path,
        [
            "--resume",
            str(operation),
            "--output-dir",
            str(tmp_path / "output"),
            "--reason",
            "r",
        ],
    )
    assert exit_code == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "error"
    assert "render-acceptance barrier" in payload["failure_reason"]
    landed = json.loads((operation / "journal.json").read_text(encoding="utf-8"))
    assert landed["state"] == "awaiting-render-acceptance"


def test_cli_resume_missing_journal_exits_one(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _resume_ready(monkeypatch)
    exit_code = main_with_root(
        tmp_path,
        [
            "--resume",
            str(tmp_path / "nope"),
            "--output-dir",
            str(tmp_path / "output"),
            "--reason",
            "r",
        ],
    )
    assert exit_code == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "error"
    assert "journal not found" in payload["failure_reason"]


def test_cli_resume_requires_a_reason(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _resume_ready(monkeypatch)
    operation = _resume_journal(tmp_path)
    exit_code = main_with_root(
        tmp_path,
        ["--resume", str(operation), "--output-dir", str(tmp_path / "output")],
    )
    assert exit_code == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "error"
    assert "--reason" in payload["failure_reason"]


@pytest.mark.skipif(os.name != "posix", reason="process groups are POSIX")
def test_run_timeout_reaps_grandchild_and_reports_failure(tmp_path: Path) -> None:
    """A timed-out verify command fails closed and leaves no descendant alive."""
    import subprocess
    import sys
    import time

    marker = tmp_path / "grandchild.json"
    grand = (
        "import os,time,json;from pathlib import Path;"
        f"Path({str(marker)!r}).write_text(json.dumps(os.getpid()));"
        "time.sleep(30)"
    )
    program = (
        "import sys,subprocess,time\nfrom pathlib import Path\n"
        f"subprocess.Popen([sys.executable,'-S','-c',{grand!r}])\n"
        f"while not Path({str(marker)!r}).exists(): time.sleep(.005)\n"
        "time.sleep(30)\n"
    )
    started = time.monotonic()
    result = refresh_module._run(
        sys.executable, "-S", "-c", program, root=tmp_path, timeout=1.5
    )
    assert time.monotonic() - started < 10
    assert result["exit_code"] == refresh_module.TIMEOUT_EXIT_CODE
    assert "timed out" in result["tail"]
    assert marker.is_file()
    pid = json.loads(marker.read_text())
    deadline = time.monotonic() + 3
    state = "alive"
    while time.monotonic() < deadline:
        state = subprocess.run(
            ["/bin/ps", "-o", "stat=", "-p", str(pid)],
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        ).stdout.strip()
        if not state or state.startswith("Z"):
            break
        time.sleep(0.05)
    assert not state or state.startswith("Z"), f"grandchild survived: {pid}"
