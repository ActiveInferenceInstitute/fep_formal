"""Tests for the canonical fep-lean command-line entrypoint."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import ClassVar

import pytest

from fep_lean import cli
from fep_lean._paths import project_root_errors
from fep_lean.verification import environment as environment_module
from fep_lean.verification import lean_verifier as verifier_module
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
        ("manuscript/config.yaml", "{}\n"),
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
    assert parser.parse_args(["setup"]).command == "setup"
    assert parser.parse_args(["preflight"]).command == "preflight"
    assert parser.parse_args(["status"]).command == "status"
    assert parser.parse_args(["status"]).gnn_root is None
    assert (
        str(parser.parse_args(["status", "--gnn-root", "/tmp/g"]).gnn_root) == "/tmp/g"
    )
    assert (
        parser.parse_args(["bridge", "status", "--gnn-root", "/tmp/g"]).operation
        == "status"
    )


def test_main_status_composes_on_checkout(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code = cli.main(["--project-root", str(PROJ), "status"])
    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    assert payload["status"] == "ok"
    assert [section["name"] for section in payload["sections"]] == [
        "catalogue_build_products",
        "render_receipt_freshness",
        "bridge_source_pin",
        "native_verification_receipt",
    ]


def test_print_result_handles_complete_and_incomplete_results() -> None:
    assert cli._print_result(_Result(True)) == 0
    assert cli._print_result(_Result(False)) == 1
    assert cli._print_result({"status": "error"}) == 1


@pytest.fixture
def setup_checkout(tmp_path: Path, monkeypatch) -> Path:
    """Real child processes with a local Git dependency and controlled Lake."""
    import os
    import subprocess
    import sys

    lean_dir = tmp_path / "lean"
    lean_dir.mkdir()
    for name in ("lean-toolchain", "lakefile.lean", "lake-manifest.json"):
        (lean_dir / name).write_bytes((PROJ / "lean" / name).read_bytes())
    (tmp_path / "uv.lock").write_text("fixture lock\n")
    mathlib = lean_dir / ".lake/packages/mathlib"
    mathlib.mkdir(parents=True)
    for args in (
        ["init", "-q"],
        [
            "-c",
            "user.name=Setup Test",
            "-c",
            "user.email=setup@example.invalid",
            "commit",
            "-q",
            "--allow-empty",
            "-m",
            "fixture",
        ],
    ):
        subprocess.run(["git", "-C", str(mathlib), *args], check=True)
    revision = subprocess.check_output(
        ["git", "-C", str(mathlib), "rev-parse", "HEAD"], text=True
    ).strip()
    manifest = json.loads((lean_dir / "lake-manifest.json").read_text())
    manifest["packages"][0]["rev"] = revision
    (lean_dir / "lake-manifest.json").write_text(json.dumps(manifest))
    lake = tmp_path / "lake"
    lake.write_text(
        f"#!{sys.executable}\n"
        "import json, os, subprocess, sys, time\n"
        "from pathlib import Path\n"
        "root = Path.cwd()\n"
        "args = sys.argv[1:]\n"
        "(root / 'cache-env.json').write_text(json.dumps({k: os.environ.get(k) for k in ('XDG_CACHE_HOME', 'MATHLIB_CACHE_DIR')}))\n"
        "with (root / 'calls.jsonl').open('a') as f: f.write(json.dumps(args) + '\\n')\n"
        "config = root / 'behavior.json'\n"
        "behavior = json.loads(config.read_text()) if config.exists() else {}\n"
        "if behavior.get('require_helper'): subprocess.run(['setup-toolchain-helper'], check=True)\n"
        "if args == behavior.get('drift_at'):\n"
        "    path = root / behavior.get('drift_file', 'lake-manifest.json')\n"
        "    path.write_text(path.read_text() + ' ')\n"
        "if args == behavior.get('fail_at'): sys.exit(7)\n"
        "if args == ['--wfail', 'exe', 'cache', 'get'] and behavior.get('cache_miss'):\n"
        "    print('Warning: some files were not found in the cache.', file=sys.stderr)\n"
        "if args == behavior.get('hang_at'):\n"
        "    child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])\n"
        "    (root / 'child.pid').write_text(str(child.pid))\n"
        "    time.sleep(60)\n"
        "if args == ['--version']:\n"
        f"    print('Lake version fixture (Lean version ' + behavior.get('version', '{_PINNED_LEAN_VERSION}') + ')')\n"
        "if args == ['--wfail', 'env', 'lean', '--version']:\n"
        f"    print('Lean (version ' + behavior.get('lean_version', '{_PINNED_LEAN_VERSION}') + ', fixture, Release)')\n"
    )
    lake.chmod(0o755)
    monkeypatch.setenv("FEP_LEAN_LAKE_EXE", str(lake))
    monkeypatch.setenv("ELAN_HOME", str(tmp_path / "elan"))
    monkeypatch.delenv("FEP_LEAN_DIR", raising=False)
    monkeypatch.delenv("FEP_LEAN_SETUP_TIMEOUT_SEC", raising=False)
    monkeypatch.delenv("FEP_LEAN_ELAN_EXE", raising=False)
    # Keep real git available; no user elan fallback is needed in these tests.
    monkeypatch.setenv("PATH", os.environ["PATH"])
    return tmp_path


def _setup_behavior(root: Path, **behavior) -> None:
    (root / "lean/behavior.json").write_text(json.dumps(behavior))


def _setup_calls(root: Path) -> list[list[str]]:
    path = root / "lean/calls.jsonl"
    return (
        [json.loads(line) for line in path.read_text().splitlines()]
        if path.exists()
        else []
    )


def test_setup_preserves_explicit_cache_isolation(
    setup_checkout: Path, monkeypatch
) -> None:
    locations = {
        name: str(setup_checkout / name.lower())
        for name in ("XDG_CACHE_HOME", "MATHLIB_CACHE_DIR")
    }
    for name, value in locations.items():
        monkeypatch.setenv(name, value)
    assert cli._setup(setup_checkout) == 0
    assert json.loads((setup_checkout / "lean/cache-env.json").read_text()) == locations


def test_setup_twice_preserves_locks(setup_checkout: Path) -> None:
    root = setup_checkout
    pins = [
        root / "lean" / name
        for name in ("lean-toolchain", "lakefile.lean", "lake-manifest.json")
    ] + [root / "uv.lock"]
    before = [path.read_bytes() for path in pins]
    for _ in range(2):
        assert cli._setup(root) == 0
        assert [path.read_bytes() for path in pins] == before
    assert (
        _setup_calls(root)
        == [
            ["--version"],
            ["--wfail", "env", "lean", "--version"],
            ["--wfail", "exe", "cache", "get"],
            ["--wfail", "build", "FepSketches"],
        ]
        * 2
    )


def test_setup_stops_on_zero_exit_cache_miss(setup_checkout: Path, capsys) -> None:
    _setup_behavior(setup_checkout, cache_miss=True)
    assert cli._setup(setup_checkout) == 1
    assert "no source build was started" in capsys.readouterr().out
    assert _setup_calls(setup_checkout)[-1] == ["--wfail", "exe", "cache", "get"]


@pytest.mark.parametrize(
    "failure",
    [
        ["--version"],
        ["--wfail", "env", "lean", "--version"],
        ["--wfail", "exe", "cache", "get"],
        ["--wfail", "build", "FepSketches"],
    ],
)
def test_setup_returns_acquisition_failure(setup_checkout: Path, failure) -> None:
    _setup_behavior(setup_checkout, fail_at=failure)
    assert cli._setup(setup_checkout) == 7
    assert _setup_calls(setup_checkout)[-1] == failure


@pytest.mark.parametrize(
    "pin", ["lean-toolchain", "lakefile.lean", "lake-manifest.json", "../uv.lock"]
)
def test_setup_rejects_missing_pin_before_lake(
    setup_checkout: Path, pin, capsys
) -> None:
    (setup_checkout / "lean" / pin).unlink()
    assert cli._setup(setup_checkout) == 1
    assert not _setup_calls(setup_checkout)
    assert "restore these files together" in capsys.readouterr().out


@pytest.mark.parametrize(
    "corruption", ["json", "tag", "toolchain", "revision", "packages", "empty"]
)
def test_setup_rejects_corrupt_or_mismatched_pin(
    setup_checkout: Path, corruption
) -> None:
    manifest_path = setup_checkout / "lean/lake-manifest.json"
    manifest = json.loads(manifest_path.read_text())
    if corruption == "json":
        manifest_path.write_text("{")
    elif corruption == "toolchain":
        (setup_checkout / "lean/lean-toolchain").write_text("leanprover/lean4:v0.0.1\n")
    else:
        if corruption == "tag":
            manifest["packages"][0]["inputRev"] = "v0.0.1"
        elif corruption == "revision":
            manifest["packages"][0]["rev"] = "floating"
        elif corruption == "packages":
            manifest["packages"] = [None]
        else:
            manifest["packages"] = []
        manifest_path.write_text(json.dumps(manifest))
    assert cli._setup(setup_checkout) == 1
    assert not _setup_calls(setup_checkout)


@pytest.mark.parametrize("key", ["version", "lean_version"])
def test_setup_rejects_wrong_actual_compiler(setup_checkout: Path, key) -> None:
    _setup_behavior(setup_checkout, **{key: "0.0.1"})
    assert cli._setup(setup_checkout) == 1
    assert ["--wfail", "exe", "cache", "get"] not in _setup_calls(setup_checkout)


def test_setup_rejects_wrong_materialized_mathlib(setup_checkout: Path) -> None:
    path = setup_checkout / "lean/lake-manifest.json"
    manifest = json.loads(path.read_text())
    manifest["packages"][0]["rev"] = "a" * 40
    path.write_text(json.dumps(manifest))
    assert cli._setup(setup_checkout) == 1
    assert ["--wfail", "exe", "cache", "get"] not in _setup_calls(setup_checkout)


@pytest.mark.parametrize("failure", [False, True])
@pytest.mark.parametrize("pin", ["lake-manifest.json", "../uv.lock"])
def test_setup_detects_subprocess_pin_drift(
    setup_checkout: Path, failure, pin, capsys
) -> None:
    step = ["--wfail", "exe", "cache", "get"]
    _setup_behavior(
        setup_checkout, drift_at=step, drift_file=pin, fail_at=step if failure else None
    )
    assert cli._setup(setup_checkout) == 1
    assert "setup pin drift" in capsys.readouterr().out
    assert _setup_calls(setup_checkout)[-1] == step


def test_setup_bootstraps_when_lake_is_unavailable(
    setup_checkout: Path, monkeypatch
) -> None:
    import sys

    root = setup_checkout
    elan = root / "elan-exe"
    elan.write_text(
        f"#!{sys.executable}\n"
        "import os, shutil, sys\n"
        "from pathlib import Path\n"
        f"assert sys.argv[1:] == ['toolchain', 'install', '{_TOOLCHAIN_PIN}']\n"
        "target = Path(os.environ['ELAN_HOME']) / 'toolchains' / sys.argv[3].replace('/', '--').replace(':', '---') / 'bin'\n"
        "target.mkdir(parents=True)\n"
        f"shutil.copy2({str(root / 'lake')!r}, target / 'lake')\n"
        "helper = target / 'setup-toolchain-helper'\n"
        "helper.write_text('#!/bin/sh\\nexit 0\\n')\n"
        "helper.chmod(0o755)\n"
    )
    elan.chmod(0o755)
    monkeypatch.setattr(environment_module, "find_executable", lambda *_args: None)
    monkeypatch.setenv("FEP_LEAN_ELAN_EXE", str(elan))
    _setup_behavior(root, require_helper=True)
    assert cli._setup(root) == 0
    assert _setup_calls(root)[-1] == ["--wfail", "build", "FepSketches"]


def test_setup_missing_elan(setup_checkout: Path, monkeypatch, capsys) -> None:
    monkeypatch.setattr(environment_module, "find_executable", lambda *_args: None)
    monkeypatch.setenv("PATH", "")
    assert cli._setup(setup_checkout) == 1
    assert "install elan or set FEP_LEAN_ELAN_EXE" in capsys.readouterr().out
    assert not _setup_calls(setup_checkout)


def test_setup_elan_acquisition_failure(setup_checkout: Path, monkeypatch) -> None:
    elan = setup_checkout / "bad-elan"
    elan.write_text("#!/bin/sh\nexit 7\n")
    elan.chmod(0o755)
    monkeypatch.setattr(environment_module, "find_executable", lambda *_args: None)
    monkeypatch.setenv("FEP_LEAN_ELAN_EXE", str(elan))
    assert cli._setup(setup_checkout) == 7
    assert not _setup_calls(setup_checkout)


@pytest.mark.parametrize("timeout", ["not-an-int", "0", "-1"])
def test_setup_rejects_invalid_timeout(monkeypatch, tmp_path: Path, timeout) -> None:
    monkeypatch.setenv("FEP_LEAN_SETUP_TIMEOUT_SEC", timeout)
    assert cli._setup(tmp_path) == 1


def test_setup_deadline_kills_real_descendant(
    setup_checkout: Path, monkeypatch
) -> None:
    import os
    import subprocess
    import time

    _setup_behavior(setup_checkout, hang_at=["--wfail", "exe", "cache", "get"])
    monkeypatch.setenv("FEP_LEAN_SETUP_TIMEOUT_SEC", "2")
    start = time.monotonic()
    assert cli._setup(setup_checkout) == 1
    assert time.monotonic() - start < 8
    pid = int((setup_checkout / "lean/child.pid").read_text())
    # A killed descendant may briefly be a zombie before init reaps it.
    for _ in range(30):
        state = subprocess.run(
            ["ps", "-o", "stat=", "-p", str(pid)],
            capture_output=True,
            text=True,
            check=False,
        ).stdout.strip()
        if not state or state.startswith("Z"):
            break
        time.sleep(0.05)
    else:
        os.kill(pid, 9)
        pytest.fail("setup deadline left its grandchild running")
    assert _setup_calls(setup_checkout)[-1] == ["--wfail", "exe", "cache", "get"]


def test_setup_total_deadline_does_not_reset(setup_checkout: Path, monkeypatch) -> None:
    ticks = iter([0.0, 1801.0])
    monkeypatch.setattr(environment_module.time, "monotonic", lambda: next(ticks))
    assert cli._setup(setup_checkout) == 1
    assert not _setup_calls(setup_checkout)


def test_setup_shell_delegates_to_locked_cli(tmp_path: Path) -> None:
    import os
    import subprocess

    uv = tmp_path / "uv"
    log = tmp_path / "args"
    uv.write_text('#!/bin/sh\nprintf "%s\\n" "$@" > "$SETUP_ARGS"\nexit 7\n')
    uv.chmod(0o755)
    result = subprocess.run(
        ["bash", str(PROJ / "scripts/_maint_bootstrap_lean_toolchain.sh")],
        env={**os.environ, "PATH": f"{tmp_path}:/usr/bin:/bin", "SETUP_ARGS": str(log)},
        cwd=tmp_path,
        check=False,
    )
    assert result.returncode == 7
    assert log.read_text().splitlines() == [
        "run",
        "--locked",
        "--project",
        str(PROJ),
        "fep-lean",
        "--project-root",
        str(PROJ),
        "setup",
    ]


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
    monkeypatch.setattr(verifier_module, "LeanVerifier", FakeVerifier)
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

    monkeypatch.setattr(cli.FEPTopicCatalogue, "from_yaml", CatalogueLoader.from_yaml)
    monkeypatch.setattr(verifier_module, "LeanVerifier", Verifier)
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

    monkeypatch.setattr(cli.FEPTopicCatalogue, "from_yaml", CatalogueLoader.from_yaml)
    monkeypatch.setattr(verifier_module, "LeanVerifier", Verifier)
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
    assert payload["status"] == "error"
    payload = payload["details"]["result"]
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


def test_emit_failure_is_byte_stable(capsys) -> None:
    """The versioned failure envelope has fixed order and nested context."""
    assert cli._emit_failure("boom") == 1
    assert capsys.readouterr().out == (
        '{"status": "error", "failure_reason": "boom", "details": {}}\n'
    )
    assert cli._emit_failure("boom", mode="lean-only", complete=False) == 1
    assert capsys.readouterr().out == (
        '{"status": "error", "failure_reason": "boom", '
        '"details": {"mode": "lean-only", "complete": false}}\n'
    )
    assert cli._emit_failure("boom", indent=2, complete=False, project_root="/x") == 1
    assert capsys.readouterr().out == (
        '{\n  "status": "error",\n  "failure_reason": "boom",\n'
        '  "details": {\n    "complete": false,\n    "project_root": "/x"\n  }\n}\n'
    )


def _failing_argv(tmp_path: Path, monkeypatch) -> list[list[str]]:
    class Topic:
        id = "fep-001"
        area = "FEP"
        lean_sketch = "theorem fixture : True := True.intro"

    class Catalogue:
        topics = (Topic(),)

    root = tmp_path / "checkout"
    root.mkdir()
    _make_checkout_root(root)
    monkeypatch.setattr(
        cli.FEPTopicCatalogue, "from_yaml", staticmethod(lambda _path: Catalogue())
    )
    pr = ["--project-root", str(root)]
    outside = ["--project-root", str(tmp_path)]
    return [
        [*outside, "catalogue"],
        [*pr, "verify", "--topic", "fep-999"],
        [*pr, "verify", "--area", "AI"],
        [*pr, "methods", "probe", "no-such-probe"],
        [*pr, "publication-capture", "--plan", "--template", str(tmp_path / "missing")],
    ]


@pytest.mark.parametrize("index", range(5))
def test_every_verb_failure_shares_one_error_schema(
    index: int, monkeypatch, tmp_path: Path, capsys
) -> None:
    argv = _failing_argv(tmp_path, monkeypatch)[index]
    assert cli.main(argv) == 1
    payload = json.loads(capsys.readouterr().out)
    assert list(payload) == ["status", "failure_reason", "details"]
    assert payload["status"] == "error"
    assert isinstance(payload["failure_reason"], str) and payload["failure_reason"]
    assert isinstance(payload["details"], dict)


def test_every_package_exception_is_a_fep_lean_error() -> None:
    import importlib
    import inspect
    import pkgutil

    import fep_lean
    from fep_lean import FepLeanError

    assert "FepLeanError" in fep_lean.__all__
    # These two modules are hash-pinned by the Q5/Q6/Q7 artifact-proof manifests
    # and retained native receipts; adopting the base needs a coordinated
    # evidence refresh, so they are tracked here rather than silently skipped.
    pinned = {
        "fep_lean.verification.gnn_artifact_proof",
        "fep_lean.verification.gnn_continuous_artifact_proof",
    }
    found = 0
    for info in pkgutil.walk_packages(fep_lean.__path__, "fep_lean."):
        module = importlib.import_module(info.name)
        for name, obj in vars(module).items():
            if (
                inspect.isclass(obj)
                and issubclass(obj, Exception)
                and obj.__module__ == info.name
                and info.name not in pinned
            ):
                found += 1
                assert issubclass(obj, FepLeanError), f"{info.name}.{name}"
    assert found >= 20


def test_setup_legacy_alias_is_canonical_acquisition_operation() -> None:
    assert cli._setup is environment_module.setup_workspace


def test_cli_explicit_root_precedes_nested_caller_without_environment_mutation(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    from fep_lean._paths import project_root, project_root_context

    env_root, caller_root, cli_root = (
        tmp_path / name for name in ("env", "caller", "cli")
    )
    monkeypatch.setenv("FEP_LEAN_PROJECT_ROOT", str(env_root))
    before = dict(os.environ)
    observed = []

    def snapshot(root, _gnn):
        observed.append((root, project_root()))
        assert dict(os.environ) == before
        return {"root": str(root)}

    monkeypatch.setattr(cli, "project_root_errors", lambda _root: ())
    monkeypatch.setattr(cli, "build_status_report", snapshot)
    monkeypatch.setattr(cli, "report_to_json", json.dumps)
    with project_root_context(caller_root):
        assert cli.main(["--project-root", str(cli_root), "status"]) == 0
        assert project_root() == caller_root
        assert cli.main(["status"]) == 0
    assert observed == [(cli_root, cli_root), (caller_root, caller_root)]
    assert project_root() == env_root
    assert dict(os.environ) == before
    assert len(capsys.readouterr().out.splitlines()) == 2


def test_cli_context_resets_after_handler_failure(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    from fep_lean._paths import project_root, project_root_context

    def reject(*_args):
        raise OSError("actual handler failed")

    monkeypatch.setattr(cli, "project_root_errors", lambda _root: ())
    monkeypatch.setattr(cli, "build_status_report", reject)
    before = dict(os.environ)
    with project_root_context(tmp_path / "caller"):
        assert cli.main(["--project-root", str(tmp_path / "cli"), "status"]) == 1
        assert (
            json.loads(capsys.readouterr().out)["failure_reason"]
            == "actual handler failed"
        )
        assert project_root() == tmp_path / "caller"
    assert dict(os.environ) == before


def test_concurrent_cli_roots_do_not_cross_or_mutate_environment(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    from fep_lean._paths import project_root

    barrier = Barrier(2)
    before = dict(os.environ)
    observed = []

    def snapshot(root, _gnn):
        barrier.wait(timeout=5)
        observed.append((root, project_root()))
        assert dict(os.environ) == before
        return {"root": str(root)}

    monkeypatch.setattr(cli, "project_root_errors", lambda _root: ())
    monkeypatch.setattr(cli, "build_status_report", snapshot)
    monkeypatch.setattr(cli, "report_to_json", json.dumps)
    roots = [tmp_path / "left", tmp_path / "right"]
    with ThreadPoolExecutor(max_workers=2) as pool:
        codes = list(
            pool.map(
                lambda root: cli.main(["--project-root", str(root), "status"]), roots
            )
        )
    assert codes == [0, 0]
    assert set(observed) == {(root, root) for root in roots}
    assert dict(os.environ) == before
    assert len(capsys.readouterr().out.splitlines()) == 2


_ERROR_TYPES = [
    ("fep_lean._paths", "FepLeanError"),
    ("fep_lean.llm.hermes", "HermesAPIError"),
    ("fep_lean.methods.model", "PositioningError"),
    ("fep_lean.methods.probes", "BoundaryProbeError"),
    ("fep_lean.prove2me.config", "Prove2meError"),
    ("fep_lean.prove2me.config", "Prove2meConfigError"),
    ("fep_lean.prove2me.config", "Prove2meAuthError"),
    ("fep_lean.prove2me.config", "Prove2meAPIError"),
    ("fep_lean.prove2me.config", "Prove2meTransportError"),
    ("fep_lean.prove2me.config", "Prove2meTimeoutError"),
    ("fep_lean.output.rendering", "ManuscriptRenderError"),
    ("fep_lean.output.publication_metadata", "PublicationMetadataError"),
    ("fep_lean.output.browser_capture", "BrowserCaptureError"),
    ("fep_lean.output.svg_raster", "SvgRasterError"),
    ("fep_lean.output.render_fonts", "FontProbeError"),
    ("fep_lean.output.release_bundle._core", "ReleaseBundleError"),
    ("fep_lean.verification.gnn_continuous_artifact_proof", "ContinuousArtifactError"),
    ("fep_lean.verification.gnn_artifact_proof", "ArtifactProofError"),
    ("fep_lean.custody.refresh", "RefreshRefused"),
    ("fep_lean.custody.apply", "ApplyRefused"),
    ("fep_lean.catalogue.registry", "RegistryValidationError"),
    ("fep_lean.catalogue.semantics", "SemanticValidationError"),
    ("fep_lean.catalogue.topics", "CatalogueValidationError"),
    ("fep_lean.catalogue.novelty", "NoveltyValidationError"),
]


@pytest.mark.parametrize(("module", "name"), _ERROR_TYPES)
def test_all_owned_errors_share_public_base(module, name):
    import importlib

    from fep_lean import FepLeanError
    from fep_lean._paths import FepLeanError as owned_base

    error = getattr(importlib.import_module(module), name)
    assert FepLeanError is owned_base
    assert issubclass(error, FepLeanError)


def test_proof_error_legacy_ancestry_and_setup_identity():
    from fep_lean.verification.gnn_artifact_proof import ArtifactProofError
    from fep_lean.verification.gnn_continuous_artifact_proof import (
        ContinuousArtifactError,
    )

    assert not issubclass(ArtifactProofError, ValueError)
    assert issubclass(ContinuousArtifactError, ValueError)
    assert cli._setup is environment_module.setup_workspace


@pytest.mark.parametrize(
    "verb",
    [
        "setup",
        "verify",
        "catalogue",
        "atlas",
        "dashboard",
        "run",
        "topic",
        "report",
        "preflight",
        "status",
        "publication-capture",
        "methods",
        "bridge",
        "custody",
    ],
)
def test_canonical_operational_failure_schema(verb, monkeypatch, capsys, tmp_path):
    from types import SimpleNamespace

    from fep_lean import methods
    from fep_lean.bridge import operations
    from fep_lean.output import release_bundle
    from fep_lean.verification import preflight as preflight_owner

    def refuse(*args, **kwargs):
        raise OSError("controlled owner refusal")

    def no_process(*args, **kwargs):
        raise AssertionError("failure fixture attempted a subprocess")

    monkeypatch.setattr("subprocess.Popen", no_process)
    failed = {"complete": False, "failure_reason": "controlled workflow refusal"}
    monkeypatch.setattr(
        cli,
        "run_pipeline",
        lambda **kw: SimpleNamespace(complete=False, as_dict=lambda: failed),
    )
    monkeypatch.setattr(
        cli,
        "run_single_topic",
        lambda *a, **kw: SimpleNamespace(complete=False, as_dict=lambda: failed),
    )
    monkeypatch.setattr(
        cli,
        "verify_catalogue",
        lambda *a, **kw: verifier_module.CatalogueVerification(failed, 7, 2),
    )
    monkeypatch.setattr(
        cli, "atlas_projection_drift", lambda root: [root / "atlas.svg"]
    )
    monkeypatch.setattr(
        cli, "formal_kernel_dashboard_drift", lambda root: [root / "dashboard.svg"]
    )
    monkeypatch.setattr(
        preflight_owner,
        "run_validation_checks",
        lambda *a, **kw: {"status": "error", "failed_count": 1, "checks": []},
    )
    monkeypatch.setattr(cli, "build_status_report", refuse)
    monkeypatch.setattr(methods, "build_mathematical_positioning", refuse)
    monkeypatch.setattr(release_bundle, "plan_publication_capture", refuse)
    monkeypatch.setattr(
        operations, "status", lambda *a: {"status": "error", "checks": {}}
    )
    monkeypatch.setenv("FEP_LEAN_SETUP_TIMEOUT_SEC", "invalid")
    arguments = {
        "setup": [],
        "verify": [],
        "catalogue": [],
        "atlas": ["--check"],
        "dashboard": ["--check"],
        "run": [],
        "topic": ["fep-001"],
        "report": [],
        "preflight": [],
        "status": [],
        "publication-capture": ["--template", str(tmp_path), "--plan"],
        "methods": ["inspect"],
        "bridge": ["status", "--gnn-root", str(tmp_path)],
        "custody": ["apply"],
    }
    assert cli.main(["--project-root", str(PROJ), verb, *arguments[verb]]) == 1
    output = capsys.readouterr()
    record = json.loads(output.out)
    assert set(record) == {"status", "failure_reason", "details"}
    assert record["status"] == "error"
    assert isinstance(record["failure_reason"], str) and record["failure_reason"]
    assert isinstance(record["details"], dict)
    assert not output.err


@pytest.mark.parametrize(
    "error", [KeyError("bug"), TypeError("bug"), RuntimeError("bug")]
)
def test_outer_cli_does_not_swallow_programming_errors(error, monkeypatch, capsys):
    def fail(*args):
        raise error

    monkeypatch.setattr(cli, "_dispatch_command", fail)
    with pytest.raises(type(error)):
        cli.main(["--project-root", str(PROJ), "status"])
    assert not capsys.readouterr().out


@pytest.mark.parametrize(
    "arguments",
    [
        ["status", "--unknown"],
        ["publication-capture", "--template", "unused", "--plan", "--resume"],
    ],
)
def test_error_schema_preserves_argparse_usage_exit_two(arguments, capsys):
    with pytest.raises(SystemExit) as error:
        cli.main(["--project-root", str(PROJ), *arguments])
    assert error.value.code == 2
    assert not capsys.readouterr().out


def test_projection_failure_callback_preserves_direct_owner_default(capsys):
    from fep_lean.catalogue.generation import check_or_write

    assert (
        check_or_write(
            PROJ, lambda root: [root / "missing.svg"], None, "fixture", check=True
        )
        == 1
    )
    assert capsys.readouterr().out == "STALE: missing.svg\n"


def test_direct_setup_default_retains_existing_failure_text(monkeypatch, capsys):
    monkeypatch.setenv("FEP_LEAN_SETUP_TIMEOUT_SEC", "invalid")
    assert environment_module.setup_workspace(PROJ) == 1
    assert (
        capsys.readouterr().out
        == "setup failed: FEP_LEAN_SETUP_TIMEOUT_SEC must be an integer\n"
    )


def test_native_result_success_bytes_and_failure_exit_are_separate(capsys):
    payload = {"complete": True, "topic": "fep-001", "unicode": "Δ"}
    result = verifier_module.CatalogueVerification(payload, 0, 2)
    before = result.to_json()
    assert result.emit_cli() == 0
    assert capsys.readouterr().out == before + "\n"
    failed = verifier_module.CatalogueVerification(
        {"complete": False, "failure_reason": "compile refusal"}, 7, 2
    )
    original = failed.to_json()
    assert failed.emit_cli() == 1
    record = json.loads(capsys.readouterr().out)
    assert record["details"]["exit_code"] == 7
    assert record["details"]["result"] == json.loads(original)
    assert failed.to_json() == original


def test_preflight_adapter_preserves_keyword_and_uses_full_mode(monkeypatch, capsys):
    from fep_lean.verification import preflight

    calls = []
    monkeypatch.setattr(preflight, "project_root", lambda: PROJ)
    monkeypatch.setattr(
        preflight,
        "run_validation_checks",
        lambda root, *, mode: (
            calls.append((root, mode)) or {"status": "error", "failed_count": 1}
        ),
    )
    before = dict(os.environ)
    assert preflight.run_preflight(require_gauss=False) == 1
    payload = json.loads(capsys.readouterr().out)
    assert (
        payload["status"] == "error"
        and payload["details"]["result"]["failed_count"] == 1
    )
    assert calls == [(PROJ, "full")]
    assert dict(os.environ) == before


def test_cli_context_resets_after_unhandled_programming_failure(tmp_path, monkeypatch):
    from fep_lean._paths import project_root, project_root_context

    def reject(*args):
        raise RuntimeError("programming fixture")

    monkeypatch.setattr(cli, "project_root_errors", lambda root: ())
    monkeypatch.setattr(cli, "build_status_report", reject)
    before = dict(os.environ)
    with project_root_context(tmp_path / "caller"):
        with pytest.raises(RuntimeError, match="programming fixture"):
            cli.main(["--project-root", str(tmp_path / "cli"), "status"])
        assert project_root() == tmp_path / "caller"
    assert dict(os.environ) == before


def test_setup_cli_late_failure_keeps_stdout_json(monkeypatch, capsys):
    import subprocess

    monkeypatch.setenv("FEP_LEAN_SETUP_TIMEOUT_SEC", "1800")
    monkeypatch.delenv("FEP_LEAN_DIR", raising=False)
    monkeypatch.setattr(
        environment_module, "find_executable", lambda *a: "/fixture/lake"
    )
    monkeypatch.setattr(
        environment_module,
        "run_process_group",
        lambda command, **kw: subprocess.CompletedProcess(
            command, 7, "compiler progress\n", "compiler diagnostic\n"
        ),
    )
    monkeypatch.setattr(
        subprocess,
        "Popen",
        lambda *a, **kw: pytest.fail("setup fixture spawned a process"),
    )
    assert cli.main(["--project-root", str(PROJ), "setup"]) == 1
    output = capsys.readouterr()
    payload = json.loads(output.out)
    assert set(payload) == {"status", "failure_reason", "details"}
    assert payload["status"] == "error" and payload["details"]["exit_code"] == 7
    assert payload["details"]["command"] == "setup"
    assert "compiler progress" in output.err and "compiler diagnostic" in output.err
    assert "[fep_lean setup]" in output.err


def test_setup_cli_success_keeps_final_line_and_routes_progress(monkeypatch, capsys):
    import subprocess

    manifest = json.loads((PROJ / "lean/lake-manifest.json").read_text())
    revision = next(
        row["rev"] for row in manifest["packages"] if row["name"] == "mathlib"
    )
    monkeypatch.setenv("FEP_LEAN_SETUP_TIMEOUT_SEC", "1800")
    monkeypatch.delenv("FEP_LEAN_DIR", raising=False)
    monkeypatch.setattr(
        environment_module, "find_executable", lambda *a: "/fixture/lake"
    )

    def run(command, **kwargs):
        if command[0] == "git":
            text = revision + "\n"
        elif command[-2:] == ["lean", "--version"]:
            text = _FIXTURE_LEAN_VERSION + "\n"
        elif command[-1] == "--version":
            text = f"Lake version fixture (Lean version {_PINNED_LEAN_VERSION})\n"
        else:
            text = "controlled progress\n"
        return subprocess.CompletedProcess(command, 0, text, "")

    monkeypatch.setattr(environment_module, "run_process_group", run)
    monkeypatch.setattr(
        subprocess,
        "Popen",
        lambda *a, **kw: pytest.fail("setup fixture spawned a process"),
    )
    assert cli.main(["--project-root", str(PROJ), "setup"]) == 0
    output = capsys.readouterr()
    assert (
        output.out
        == f"[fep_lean setup] OK | lean: {_FIXTURE_LEAN_VERSION} | mathlib: {revision}\n"
    )
    assert "controlled progress" in output.err
