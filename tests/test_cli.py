"""Tests for the canonical fep-lean command-line entrypoint."""

from __future__ import annotations

import json
from pathlib import Path
from typing import ClassVar

from fep_lean import cli
from fep_lean._paths import project_root_errors
from fep_lean.verification._toolchain import pinned_lean_semver, read_toolchain_pin

PROJ = Path(__file__).resolve().parent.parent
_TOOLCHAIN_PIN = read_toolchain_pin(PROJ / "lean")
assert _TOOLCHAIN_PIN is not None
_PINNED_LEAN_VERSION = pinned_lean_semver(_TOOLCHAIN_PIN)
assert _PINNED_LEAN_VERSION is not None
_FIXTURE_LEAN_VERSION = f"Lean (version {_PINNED_LEAN_VERSION}, fixture, Release)"


class _Result:
    def __init__(self, complete: bool) -> None:
        self.complete = complete

    def as_dict(self) -> dict[str, bool]:
        return {"complete": self.complete}


def _make_checkout_root(root: Path) -> None:
    for relative, content in (
        ("config/topics.yaml", "topics: []\n"),
        ("config/settings.yaml", "{}\n"),
        ("lean/lean-toolchain", "leanprover/lean4:v4.29.0\n"),
        (
            "lean/lakefile.lean",
            'package FepSketches\nrequire mathlib from git "fixture" @ "v4.29.0"\n',
        ),
        (
            "lean/lake-manifest.json",
            '{"packages":[{"name":"mathlib","rev":"' + "a" * 40 + '"}]}\n',
        ),
        ("docs/manuscript/config.yaml", "{}\n"),
        ("src/fep_lean/__init__.py", "\n"),
        ("src/fep_lean/catalogue/registry.py", "BODIES = {}\n"),
    ):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def test_project_root_contract_identifies_checkout_assets(tmp_path: Path) -> None:
    assert project_root_errors(tmp_path)
    _make_checkout_root(tmp_path)
    assert project_root_errors(tmp_path) == ()


def test_main_rejects_substantive_command_outside_checkout(
    tmp_path: Path, capsys
) -> None:
    code = cli.main(["--project-root", str(tmp_path), "catalogue"])
    payload = json.loads(capsys.readouterr().out)
    assert code == 1
    assert payload["status"] == "error"
    assert "--project-root" in payload["failure_reason"]


def test_build_parser_registers_all_commands() -> None:
    parser = cli.build_parser()
    assert (
        parser.parse_args(["catalogue", "--area", "FEP", "--topic", "fep-001"]).command
        == "catalogue"
    )
    assert (
        parser.parse_args(["verify", "--area", "FEP", "--topic", "fep-001"]).command
        == "verify"
    )
    assert parser.parse_args(["run", "--workflow", "review"]).workflow == "review"
    assert parser.parse_args(["topic", "fep-001"]).topic_id == "fep-001"
    assert parser.parse_args(["atlas", "--check"]).check is True
    assert parser.parse_args(["dashboard", "--check"]).check is True
    assert parser.parse_args(["report"]).command == "report"


def test_print_result_handles_complete_and_incomplete_results() -> None:
    assert cli._print_result(_Result(True)) == 0
    assert cli._print_result(_Result(False)) == 1
    assert cli._print_result({"status": "error"}) == 1


def test_setup_requires_lake(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.delenv("FEP_LEAN_LAKE_EXE", raising=False)
    monkeypatch.setenv("PATH", "")
    monkeypatch.setenv("ELAN_HOME", str(tmp_path / "elan"))
    assert cli._setup(tmp_path) == 1


def test_setup_runs_cache_and_build(monkeypatch, tmp_path: Path) -> None:
    (tmp_path / "lean").mkdir()
    lake = tmp_path / "lake"
    lake.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    lake.chmod(0o755)
    monkeypatch.setenv("FEP_LEAN_LAKE_EXE", str(lake))
    assert cli._setup(tmp_path) == 0


def test_setup_returns_lake_failure(monkeypatch, tmp_path: Path) -> None:
    (tmp_path / "lean").mkdir()
    lake = tmp_path / "lake"
    lake.write_text("#!/bin/sh\nexit 7\n", encoding="utf-8")
    lake.chmod(0o755)
    monkeypatch.setenv("FEP_LEAN_LAKE_EXE", str(lake))
    assert cli._setup(tmp_path) == 7


def test_setup_bootstraps_when_lake_is_not_on_path(monkeypatch, tmp_path: Path) -> None:
    (tmp_path / "scripts").mkdir()
    bootstrap = tmp_path / "scripts" / "_maint_bootstrap_lean_toolchain.sh"
    bootstrap.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    bootstrap.chmod(0o755)
    monkeypatch.delenv("FEP_LEAN_LAKE_EXE", raising=False)
    monkeypatch.setattr(cli, "find_executable", lambda *_args: None)
    calls: list[list[str]] = []

    def fake_run(command, **kwargs):
        calls.append(command)
        return type("Completed", (), {"returncode": 0})()

    monkeypatch.setattr(cli, "run_process_group", fake_run)
    assert cli._setup(tmp_path) == 0
    assert calls == [["bash", str(bootstrap)]]


def test_setup_rejects_invalid_timeout(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("FEP_LEAN_SETUP_TIMEOUT_SEC", "not-an-int")
    assert cli._setup(tmp_path) == 1


def test_verify_command_is_lean_only(monkeypatch, tmp_path: Path, capsys) -> None:
    _make_checkout_root(tmp_path)

    class Topic:
        def __init__(self) -> None:
            self.id = "fep-001"
            self.area = "FEP"
            self.lean_sketch = "theorem fixture : True := True.intro"

    class Catalogue:
        def __init__(self) -> None:
            self.topics = [Topic()]

    class VerifyResult:
        compiles = True
        has_sorry = False

        def as_dict(self) -> dict[str, object]:
            return {"topic_id": "fep-001", "compiles": True, "has_sorry": False}

    class FakeVerifier:
        def __init__(self, **kwargs) -> None:
            self.kwargs = kwargs

        def check_mathlib_built(self) -> tuple[bool, str]:
            return True, "fixture Mathlib cache"

        def verify_batch(self, items: list[tuple[str, str]]) -> list[VerifyResult]:
            assert items == [("fep-001", "theorem fixture : True := True.intro")]
            return [VerifyResult()]

    monkeypatch.setattr(
        cli.FEPTopicCatalogue, "from_yaml", staticmethod(lambda _path: Catalogue())
    )
    monkeypatch.setattr(cli, "LeanVerifier", FakeVerifier)
    assert (
        cli.main(["--project-root", str(tmp_path), "verify", "--topic", "fep-001"]) == 0
    )
    payload = json.loads(capsys.readouterr().out)
    assert payload["mode"] == "lean-only"
    assert payload["complete"] is True
    assert payload["verified_topics"] == 1
    assert payload["results"][0]["lean_file"] is None


def test_verify_can_write_native_receipt(monkeypatch, tmp_path: Path, capsys) -> None:
    class Topic:
        id = "fep-001"
        area = "FEP"
        lean_sketch = "theorem fixture : True := True.intro"

    class Catalogue:
        topics: ClassVar[list[Topic]] = [Topic()]

    class CatalogueLoader:
        from_yaml = staticmethod(lambda _path: Catalogue())

    class Result:
        compiles = True
        has_sorry = False
        lean_version = _FIXTURE_LEAN_VERSION

        def as_dict(self) -> dict[str, object]:
            return {
                "topic_id": "fep-001",
                "compiles": True,
                "has_sorry": False,
                "warnings": [],
                "errors": [],
                "lean_version": self.lean_version,
            }

    class Verifier:
        def __init__(self, **_kwargs) -> None:
            pass

        def check_mathlib_built(self) -> tuple[bool, str]:
            return True, "fixture"

        def verify_batch(self, _items: list[tuple[str, str]]) -> list[Result]:
            return [Result()]

    monkeypatch.setattr(cli, "FEPTopicCatalogue", CatalogueLoader)
    monkeypatch.setattr(cli, "LeanVerifier", Verifier)
    receipt = tmp_path / "receipts" / "native.json"

    code = cli.main(
        [
            "--project-root",
            str(PROJ),
            "verify",
            "--topic",
            "fep-001",
            "--receipt",
            str(receipt),
        ]
    )

    assert code == 0
    assert json.loads(receipt.read_text(encoding="utf-8"))["kind"] == "native-lean"
    assert json.loads(capsys.readouterr().out)["receipt"] == str(receipt)


def test_verify_warning_counts_align_with_strict_native_receipt(
    monkeypatch, tmp_path: Path, capsys
) -> None:
    class Topic:
        id = "fep-001"
        area = "FEP"
        lean_sketch = "theorem fixture : True := True.intro"

    class Catalogue:
        topics: ClassVar[list[Topic]] = [Topic()]

    class CatalogueLoader:
        from_yaml = staticmethod(lambda _path: Catalogue())

    class Result:
        compiles = True
        has_sorry = False
        warnings: ClassVar[list[str]] = ["declaration uses a warning-producing option"]
        lean_version = _FIXTURE_LEAN_VERSION

        def as_dict(self) -> dict[str, object]:
            return {
                "topic_id": "fep-001",
                "compiles": True,
                "has_sorry": False,
                "warnings": self.warnings,
                "errors": [],
                "lean_version": self.lean_version,
            }

    class Verifier:
        def __init__(self, **_kwargs) -> None:
            pass

        def check_mathlib_built(self) -> tuple[bool, str]:
            return True, "fixture"

        def verify_batch(self, _items: list[tuple[str, str]]) -> list[Result]:
            return [Result()]

    monkeypatch.setattr(cli, "FEPTopicCatalogue", CatalogueLoader)
    monkeypatch.setattr(cli, "LeanVerifier", Verifier)
    receipt = tmp_path / "receipts" / "native.json"

    code = cli.main(
        [
            "--project-root",
            str(PROJ),
            "verify",
            "--topic",
            "fep-001",
            "--fail-on-warnings",
            "--receipt",
            str(receipt),
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    receipt_payload = json.loads(receipt.read_text(encoding="utf-8"))
    assert code == 1
    assert payload["complete"] is False
    assert payload["compiled_without_sorry_topics"] == 1
    assert payload["verified_topics"] == 0
    assert receipt_payload["verified_topics"] == 0
    assert receipt_payload["complete"] is False


def test_main_dispatches_pipeline_commands(monkeypatch) -> None:
    calls: list[tuple[str, dict[str, object]]] = []

    def fake_pipeline(**kwargs):
        calls.append(("pipeline", kwargs))
        return _Result(True)

    def fake_topic(topic_id: str, **kwargs):
        calls.append((topic_id, kwargs))
        return _Result(True)

    monkeypatch.setattr(cli, "run_pipeline", fake_pipeline)
    monkeypatch.setattr(cli, "run_single_topic", fake_topic)

    assert cli.main(["catalogue", "--area", "FEP", "--topic", "fep-001"]) == 0
    assert cli.main(["run", "--workflow", "review"]) == 0
    assert cli.main(["topic", "fep-001", "--workflow", "prove"]) == 0
    assert cli.main(["report"]) == 0

    assert calls[0] == (
        "pipeline",
        {"mode": "catalogue", "area_filter": "FEP", "topic_filter": ["fep-001"]},
    )
    assert calls[1][1]["workflow"] == "review"
    assert calls[2] == ("fep-001", {"mode": "full", "workflow": "prove"})
    assert calls[3] == ("pipeline", {"mode": "catalogue"})


def test_atlas_command_writes_and_checks_projection(
    monkeypatch, tmp_path: Path
) -> None:
    _make_checkout_root(tmp_path)
    svg = tmp_path / "docs" / "formalism-atlas.svg"
    html = tmp_path / "docs" / "formalism-atlas.html"
    monkeypatch.setattr(cli, "write_formalism_atlas", lambda _root: (svg, html))
    monkeypatch.setattr(cli, "atlas_projection_drift", lambda _root: ())

    assert cli.main(["--project-root", str(tmp_path), "atlas"]) == 0
    assert cli.main(["--project-root", str(tmp_path), "atlas", "--check"]) == 0


def test_atlas_check_reports_stale_projection(monkeypatch, tmp_path: Path) -> None:
    _make_checkout_root(tmp_path)
    stale = tmp_path / "docs" / "formalism-atlas.svg"
    monkeypatch.setattr(cli, "atlas_projection_drift", lambda _root: (stale,))

    assert cli.main(["--project-root", str(tmp_path), "atlas", "--check"]) == 1


def test_dashboard_command_writes_and_checks_projection(
    monkeypatch, tmp_path: Path
) -> None:
    _make_checkout_root(tmp_path)
    svg = tmp_path / "docs" / "formal-kernel-dashboard.svg"
    html = tmp_path / "docs" / "formal-kernel-dashboard.html"
    monkeypatch.setattr(cli, "write_formal_kernel_dashboard", lambda _root: (svg, html))
    monkeypatch.setattr(cli, "formal_kernel_dashboard_drift", lambda _root: ())

    assert cli.main(["--project-root", str(tmp_path), "dashboard"]) == 0
    assert cli.main(["--project-root", str(tmp_path), "dashboard", "--check"]) == 0


def test_dashboard_check_reports_stale_projection(monkeypatch, tmp_path: Path) -> None:
    _make_checkout_root(tmp_path)
    stale = tmp_path / "docs" / "formal-kernel-dashboard.svg"
    monkeypatch.setattr(cli, "formal_kernel_dashboard_drift", lambda _root: (stale,))

    assert cli.main(["--project-root", str(tmp_path), "dashboard", "--check"]) == 1


def test_main_preflight_returns_error_for_incomplete_root(
    monkeypatch, tmp_path: Path
) -> None:
    assert cli.main(["--project-root", str(tmp_path), "--verbose", "preflight"]) == 1


def test_verify_rejects_unknown_topics(monkeypatch, tmp_path: Path, capsys) -> None:
    """Verify --topic with IDs not in the catalogue returns error."""

    class Topic:
        def __init__(self) -> None:
            self.id = "fep-001"
            self.area = "FEP"
            self.lean_sketch = "theorem fixture : True := True.intro"

    class Catalogue:
        def __init__(self) -> None:
            self.topics = [Topic()]

    _make_checkout_root(tmp_path)
    monkeypatch.setattr(
        cli.FEPTopicCatalogue, "from_yaml", staticmethod(lambda _path: Catalogue())
    )
    result = cli.main(["--project-root", str(tmp_path), "verify", "--topic", "fep-999"])
    assert result == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "error"
    assert "unknown topic id" in payload["failure_reason"]


def test_verify_returns_error_when_no_topics_match(
    monkeypatch, tmp_path: Path, capsys
) -> None:
    """Verify with an area filter that matches nothing returns error."""

    class Topic:
        def __init__(self) -> None:
            self.id = "fep-001"
            self.area = "FEP"
            self.lean_sketch = "theorem fixture : True := True.intro"

    class Catalogue:
        def __init__(self) -> None:
            self.topics = [Topic()]

    _make_checkout_root(tmp_path)
    monkeypatch.setattr(
        cli.FEPTopicCatalogue, "from_yaml", staticmethod(lambda _path: Catalogue())
    )
    result = cli.main(["--project-root", str(tmp_path), "verify", "--area", "AI"])
    assert result == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "error"
    assert "no catalogue topics matched" in payload["failure_reason"]


def test_print_result_returns_1_for_incomplete_object_without_as_dict() -> None:
    """_print_result returns 1 for objects lacking as_dict and complete=False fallback."""

    class Incomplete:
        pass

    assert cli._print_result(Incomplete()) == 1


def test_main_returns_2_for_unsupported_command(monkeypatch, tmp_path: Path) -> None:
    """An unrecognised subcommand returns exit code 2 via argparse error."""
    monkeypatch.setenv("FEP_LEAN_SETUP_TIMEOUT_SEC", "1800")
    try:
        cli.main(["--project-root", str(tmp_path), "nonexistent"])
        assert False, "expected SystemExit"
    except SystemExit as exc:
        assert exc.code == 2
