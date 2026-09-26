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
import shutil
from pathlib import Path

import pytest

from fep_lean.cli import build_parser, main
from fep_lean.custody import refresh as refresh_module
from fep_lean.custody.model import INTACT, LIVE_RED, Census, CensusRecord
from fep_lean.custody.refresh import (
    NATIVE_RECEIPT,
    RefreshRefused,
    _bridge_warning,
    refresh,
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


def _stage_specs(tmp_path: Path) -> Path:
    target = tmp_path / "specs"
    shutil.copytree(REPO_ROOT / "specs", target, symlinks=False)
    return target


def _out_dir(tmp_path: Path) -> Path:
    return tmp_path / "output"


def _ok_run(*command: str, root: Path) -> dict[str, object]:
    return {"command": list(command), "exit_code": 0, "tail": ""}


def _all_clear_census(monkeypatch: pytest.MonkeyPatch) -> None:
    from fep_lean.custody.verify import GATE_EXPECTATIONS

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
        "bridge source binding is stale on: src/fep_lean/custody/cli.py "
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
    assert not any(command[2:4] == ["fep-lean", "verify"] for command in calls)


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
    assert not any(command[2:4] == ["fep-lean", "verify"] for command in calls)


def test_refresh_native_runs_the_sealed_capture_command(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[list[str]] = []

    def fake_run(*command: str, root: Path) -> dict[str, object]:
        calls.append(list(command))
        return _ok_run(*command, root=root)

    _all_clear_census(monkeypatch)
    monkeypatch.setattr(refresh_module, "_run", fake_run)
    monkeypatch.setattr(refresh_module, "report_owner_errors", lambda root: ())
    monkeypatch.setattr(refresh_module, "_git_dirty", lambda root: [])
    report = refresh(
        _stage_specs(tmp_path),
        REPO_ROOT,
        _out_dir(tmp_path),
        reason="r",
        run_native=True,
    )
    assert calls[-1] == [
        "uv",
        "run",
        "fep-lean",
        "verify",
        "--fail-on-warnings",
        "--receipt",
        NATIVE_RECEIPT,
    ]
    assert report.native["exit_code"] == 0


# ---------------------------------------------------------------------------
# Bridge cascade warning: the fep_lean half of the known signature.
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
    assert "--reason" in payload["error"]


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
    assert "terminal-acceptance.json" in payload["error"]
    assert not out.exists()
    assert _sha(live_receipt.read_bytes()) == live_before


# ---------------------------------------------------------------------------
# Helpers.
# ---------------------------------------------------------------------------


def main_with_root(tmp_path: Path, extra: list[str]) -> int:
    """Run the CLI with the project root pinned to this checkout."""
    return main(["--project-root", str(REPO_ROOT), "custody", "refresh", *extra])
