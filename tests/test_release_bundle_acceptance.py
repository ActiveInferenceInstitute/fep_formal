"""Acceptance release/publication boundary contracts."""

from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Mapping
from pathlib import Path
from types import SimpleNamespace

import pytest

from fep_lean.output import release_bundle as bundle_module
from fep_lean.output.release_bundle import (
    build_numerical_witness_receipt,
)
from fep_lean.verification import _subprocess

PROJ = Path(__file__).resolve().parents[1]


def test_numerical_receipt_preserves_every_typed_check_and_evidence_boundary() -> None:
    project_root = Path(__file__).resolve().parents[1]

    payload = json.loads(build_numerical_witness_receipt(project_root))

    assert payload["kind"] == "numerical-witness-receipt"
    assert payload["complete"] is True
    assert payload["witness_count"] == 22
    assert payload["check_count"] == sum(
        len(witness["checks"]) for witness in payload["witnesses"]
    )
    assert all(witness["accepted"] is True for witness in payload["witnesses"])
    assert all(
        check["accepted"] is True
        for witness in payload["witnesses"]
        for check in witness["checks"]
    )
    assert all(
        witness["evidence_kind"] == payload["evidence_kind"]
        for witness in payload["witnesses"]
    )
    assert len(payload["source_sha256"]) == len(payload["config_sha256"]) == 64


@pytest.mark.parametrize("extra", [False, True])
def test_numerical_receipt_rejects_incomplete_or_extra_live_roster(
    monkeypatch: pytest.MonkeyPatch, extra: bool
) -> None:
    from fep_lean.output.release_bundle import _acceptance
    from fep_lean.verification.numerical_witnesses import evaluate_numerical_witnesses

    witnesses = evaluate_numerical_witnesses(PROJ, scope="catalogue")
    altered = (*witnesses, witnesses[0]) if extra else witnesses[:-1]
    monkeypatch.setattr(
        _acceptance, "evaluate_numerical_witnesses", lambda **_: altered
    )
    with pytest.raises(bundle_module.ReleaseBundleError, match="22-witness release"):
        build_numerical_witness_receipt(PROJ)


def test_python_receipts_bind_full_roster_and_coverage_floor(tmp_path: Path) -> None:
    output = tmp_path / "output"
    manuscript = tmp_path / "manuscript"
    output.mkdir()
    manuscript.mkdir()
    test_root = tmp_path / "tests"
    test_root.mkdir()
    source = tmp_path / "src/fep_lean"
    source.mkdir(parents=True)
    (source / "a.py").write_text(
        "\n".join(f"value_{index} = {index}" for index in range(1, 11)) + "\n",
        encoding="utf-8",
    )
    (test_root / "test_fixture.py").write_text(
        "def test_fixture():\n    assert True\n", encoding="utf-8"
    )
    (manuscript / "manuscript_vars.yaml").write_text(
        "tests:\n  collected: 3\n", encoding="utf-8"
    )

    def junit_xml(*, tests: int, skipped: int) -> str:
        cases = []
        for index in range(tests):
            outcome = '<skipped message="fixture"/>' if index < skipped else ""
            cases.append(
                f'<testcase classname="tests.test_fixture" name="test_{index}" '
                f'time="0">{outcome}</testcase>'
            )
        return (
            f'<testsuites><testsuite tests="{tests}" failures="0" errors="0" '
            f'skipped="{skipped}" time="0">{"".join(cases)}'
            "</testsuite></testsuites>\n"
        )

    def coverage_xml(*, covered: int) -> str:
        lines = "".join(
            f'<line number="{number}" hits="{int(number <= covered)}"/>'
            for number in range(1, 11)
        )
        return (
            f'<coverage line-rate="{covered / 10:.4f}" lines-valid="10" '
            f'lines-covered="{covered}"><packages><package><classes>'
            '<class filename="fep_lean/a.py"><lines>'
            f"{lines}</lines></class></classes></package></packages></coverage>\n"
        )

    (output / "pytest.xml").write_text(
        junit_xml(tests=3, skipped=1),
        encoding="utf-8",
    )
    coverage = output / "coverage.xml"
    coverage.write_text(coverage_xml(covered=9), encoding="utf-8")

    assert bundle_module._pytest_receipt_errors(tmp_path) == ()

    coverage.write_text(coverage_xml(covered=8), encoding="utf-8")
    assert "Python coverage line-rate 0.8000 is below 0.8900" in (
        bundle_module._pytest_receipt_errors(tmp_path)
    )

    coverage.write_text(coverage_xml(covered=9), encoding="utf-8")
    (output / "pytest.xml").write_text(
        junit_xml(tests=2, skipped=0),
        encoding="utf-8",
    )
    assert (
        "Python test receipt count differs from the canonical test roster: "
        "receipt=2, canonical=3" in bundle_module._pytest_receipt_errors(tmp_path)
    )

    (output / "pytest.xml").write_text(
        junit_xml(tests=3, skipped=3),
        encoding="utf-8",
    )
    assert "Python test receipt contains no executed tests" in (
        bundle_module._pytest_receipt_errors(tmp_path)
    )


def test_python_receipts_require_actual_testcase_and_coverage_line_records(
    tmp_path: Path,
) -> None:
    output = tmp_path / "output"
    manuscript = tmp_path / "manuscript"
    output.mkdir()
    manuscript.mkdir()
    (manuscript / "manuscript_vars.yaml").write_text(
        "tests:\n  collected: 1\n", encoding="utf-8"
    )
    (output / "pytest.xml").write_text(
        '<testsuites><testsuite tests="1" failures="0" errors="0" '
        'skipped="0" time="0"/></testsuites>\n',
        encoding="utf-8",
    )
    (output / "coverage.xml").write_text(
        '<coverage line-rate="0.9" lines-valid="10" lines-covered="9"/>\n',
        encoding="utf-8",
    )

    errors = bundle_module._pytest_receipt_errors(tmp_path)

    assert "Python test receipt testcase records disagree with suite counters" in errors
    assert "Python coverage receipt contains no executable line records" in errors


def test_python_receipts_aggregate_invalid_junit_and_coverage_records(
    tmp_path: Path,
) -> None:
    output = tmp_path / "output"
    manuscript = tmp_path / "manuscript"
    output.mkdir()
    manuscript.mkdir()
    (manuscript / "manuscript_vars.yaml").write_text(
        "tests:\n  collected: 0\n", encoding="utf-8"
    )
    (output / "pytest.xml").write_text(
        '<testsuite tests="1" failures="1" errors="1" skipped="1" time="0">'
        '<testcase time="not-a-number"><failure/><error/></testcase>'
        "</testsuite>\n",
        encoding="utf-8",
    )
    (output / "coverage.xml").write_text(
        '<notcoverage line-rate="nan" lines-valid="1" lines-covered="2">'
        '<class filename="../escape.py"><line number="bad" hits="bad"/></class>'
        "</notcoverage>\n",
        encoding="utf-8",
    )

    errors = bundle_module._pytest_receipt_errors(tmp_path)

    assert {
        "Python test receipt is not green: failures=1, errors=1",
        "Python test receipt testcase records disagree with suite counters",
        "Python test receipt contains an invalid testcase",
        "canonical collected-test count must be positive",
        "Python coverage receipt root must be coverage",
        "Python coverage line-rate must be finite in [0, 1]",
        "Python coverage line counters are invalid",
        "Python coverage receipt contains an invalid line record",
        "canonical Python source tree is missing or a symlink",
    } <= set(errors)


def test_python_receipts_bind_the_exact_collected_node_id_roster(
    tmp_path: Path,
) -> None:
    output = tmp_path / "output"
    manuscript = tmp_path / "manuscript"
    source = tmp_path / "src/fep_lean"
    output.mkdir()
    manuscript.mkdir()
    source.mkdir(parents=True)
    (source / "a.py").write_text("value = 1\n", encoding="utf-8")
    (manuscript / "manuscript_vars.yaml").write_text(
        "tests:\n  collected: 1\n", encoding="utf-8"
    )
    (output / "pytest.xml").write_text(
        '<testsuite tests="1" failures="0" errors="0" skipped="0" time="0">'
        '<testcase classname="tests.test_fixture" name="test_invented" time="0"/>'
        "</testsuite>\n",
        encoding="utf-8",
    )
    (output / "coverage.xml").write_text(
        '<coverage line-rate="1" lines-valid="1" lines-covered="1">'
        '<packages><package><classes><class filename="fep_lean/a.py">'
        '<lines><line number="1" hits="1"/></lines></class></classes>'
        "</package></packages></coverage>\n",
        encoding="utf-8",
    )

    errors = bundle_module._pytest_receipt_errors(
        tmp_path,
        expected_node_ids=("tests/test_fixture.py::test_fixture",),
    )

    assert (
        "Python test receipt testcase roster differs from collected node IDs" in errors
    )


def test_junit_identity_preserves_scope_delimiters_inside_parameter_ids() -> None:
    node_id = (
        "tests/test_topic.py::TestCatalogue::test_body"
        "[fep-073-theorem x : xs = y :: ys]"
    )

    assert bundle_module._junit_identity_from_node_id(node_id) == (
        "tests.test_topic.TestCatalogue",
        "test_body[fep-073-theorem x : xs = y :: ys]",
    )


def test_python_receipts_reject_noncanonical_coverage_source_records(
    tmp_path: Path,
) -> None:
    output = tmp_path / "output"
    manuscript = tmp_path / "manuscript"
    source = tmp_path / "src/fep_lean"
    output.mkdir()
    manuscript.mkdir()
    source.mkdir(parents=True)
    (source / "real.py").write_text("value = 1\n", encoding="utf-8")
    (manuscript / "manuscript_vars.yaml").write_text(
        "tests:\n  collected: 1\n", encoding="utf-8"
    )
    (output / "pytest.xml").write_text(
        '<testsuite tests="1" failures="0" errors="0" skipped="0" time="0">'
        '<testcase classname="tests.test_fixture" name="test_fixture" time="0"/>'
        "</testsuite>\n",
        encoding="utf-8",
    )
    (output / "coverage.xml").write_text(
        '<coverage line-rate="1" lines-valid="1" lines-covered="1">'
        '<packages><package><classes><class filename="fep_lean/invented.py">'
        '<lines><line number="1" hits="1"/></lines></class></classes>'
        "</package></packages></coverage>\n",
        encoding="utf-8",
    )

    errors = bundle_module._pytest_receipt_errors(tmp_path)

    assert (
        "Python coverage source roster differs from canonical Python sources" in errors
    )


def test_python_coverage_floor_uses_exact_line_counters_not_rounded_rate(
    tmp_path: Path,
) -> None:
    output = tmp_path / "output"
    manuscript = tmp_path / "manuscript"
    output.mkdir()
    manuscript.mkdir()
    (manuscript / "manuscript_vars.yaml").write_text(
        "tests:\n  collected: 1\n", encoding="utf-8"
    )
    (output / "pytest.xml").write_text(
        '<testsuite tests="1" failures="0" errors="0" skipped="0" time="0">'
        '<testcase classname="tests.test_fixture" name="test_fixture" time="0"/>'
        "</testsuite>\n",
        encoding="utf-8",
    )
    lines_valid = 10_001
    lines_covered = 8_900
    lines = "".join(
        f'<line number="{number}" hits="{int(number <= lines_covered)}"/>'
        for number in range(1, lines_valid + 1)
    )
    (output / "coverage.xml").write_text(
        '<coverage line-rate="0.8900" lines-valid="10001" '
        'lines-covered="8900"><packages><package><classes>'
        '<class filename="fep_lean/a.py"><lines>'
        f"{lines}</lines></class></classes></package></packages></coverage>\n",
        encoding="utf-8",
    )

    errors = bundle_module._pytest_receipt_errors(tmp_path)

    assert "Python coverage counter-derived line-rate is below 0.8900" in errors


def test_python_acceptance_is_emitted_only_by_the_exact_stable_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = tmp_path / "output"
    manuscript = tmp_path / "manuscript"
    tests = tmp_path / "tests"
    output.mkdir()
    manuscript.mkdir()
    tests.mkdir()
    source = tmp_path / "src/fep_lean"
    source.mkdir(parents=True)
    (source / "a.py").write_text("value = 1\n", encoding="utf-8")
    test_source = tests / "test_fixture.py"
    test_source.write_text("def test_fixture():\n    assert True\n", encoding="utf-8")
    (manuscript / "manuscript_vars.yaml").write_text(
        "tests:\n  collected: 1\n", encoding="utf-8"
    )
    monkeypatch.setattr(bundle_module, "report_source_digest", lambda _root: "1" * 64)
    monkeypatch.setattr(bundle_module, "report_config_digest", lambda _root: "2" * 64)
    observed_runs: list[tuple[list[str], Mapping[str, str]]] = []
    tool_bin_links: list[str] = []

    def completed_run(command: list[str], **kwargs: object) -> SimpleNamespace:
        environment = kwargs["env"]
        assert isinstance(environment, dict)
        assert all(
            isinstance(key, str) and isinstance(value, str)
            for key, value in environment.items()
        )
        observed_runs.append((command, environment))
        if "--collect-only" in command:
            return SimpleNamespace(
                returncode=0,
                stdout=(
                    "tests/test_fixture.py::test_fixture\n1 test collected in 0.01s\n"
                ),
                stderr="",
            )
        run_root = Path(environment["COVERAGE_FILE"]).parent
        tool_bin_links.extend(
            link.name for link in (run_root / "acceptance-tool-bin").iterdir()
        )
        (output / "pytest.xml").write_text(
            '<testsuites><testsuite tests="1" failures="0" errors="0" '
            'skipped="0" time="0.1"><testcase classname="tests.test_fixture" '
            'name="test_fixture" time="0.1"/></testsuite></testsuites>\n',
            encoding="utf-8",
        )
        (output / "coverage.xml").write_text(
            '<coverage line-rate="1" lines-valid="1" lines-covered="1">'
            '<packages><package><classes><class filename="fep_lean/a.py">'
            '<lines><line number="1" hits="1"/></lines></class></classes>'
            "</package></packages></coverage>\n",
            encoding="utf-8",
        )
        return SimpleNamespace(returncode=0, stdout="passed", stderr="")

    monkeypatch.setattr(_subprocess, "run_process_group", completed_run)

    receipt_path = bundle_module.run_python_acceptance(tmp_path)
    receipt = json.loads(receipt_path.read_bytes())

    assert len(observed_runs) == 3
    assert "--collect-only" in observed_runs[0][0]
    assert "--collect-only" not in observed_runs[1][0]
    assert "--collect-only" in observed_runs[2][0]
    assert all(
        environment["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] == "1"
        for _command, environment in observed_runs
    )
    assert receipt["schema_version"] == 3
    assert receipt["collection"]["node_ids"] == ["tests/test_fixture.py::test_fixture"]
    assert len(receipt["executor"]["interpreter"]["executable_sha256"]) == 64
    assert "pytest-cov" in receipt["executor"]["plugin_distributions"]
    assert len(receipt["executor"]["external_executables"]["uv"]["sha256"]) == 64
    assert sorted(tool_bin_links) == ["fc-list", "git"]
    tool_bin = Path(observed_runs[1][1]["COVERAGE_FILE"]).parent / (
        "acceptance-tool-bin"
    )
    for _command, environment in observed_runs:
        if "--collect-only" in _command:
            continue
        assert environment["PATH"] == receipt["executor"]["environment"][
            "PATH"
        ].replace("<temporary>", str(tool_bin.parent))
        assert environment["PATH"].split(os.pathsep)[2] == str(tool_bin)
    assert set(receipt["executor"]["external_executables"]) == {
        "fc-list",
        "git",
        "uv",
    }
    assert receipt["coverage"]["source_records"] == [
        {
            "lines": [{"hits": 1, "number": 1}],
            "path": "src/fep_lean/a.py",
            "source_sha256": hashlib.sha256(b"value = 1\n").hexdigest(),
        }
    ]
    assert receipt["inputs"]["before"] == receipt["inputs"]["after"]
    assert receipt["inputs"]["stable"] is True
    assert receipt["tests"]["passed"] == 1
    assert receipt["coverage"]["line_rate"] == 1.0
    assert bundle_module.build_python_acceptance_receipt(tmp_path) == (
        receipt_path.read_bytes()
    )

    static_snapshot = {
        path: (path.read_bytes(), path.stat().st_mtime_ns)
        for path in tmp_path.rglob("*")
        if path.is_file()
    }

    def forbidden_collection(*_args: object, **_kwargs: object) -> None:
        pytest.fail("static Python validation started collection")

    with monkeypatch.context() as static_patch:
        static_patch.setattr(_subprocess, "run_process_group", forbidden_collection)
        static_patch.setattr(
            bundle_module, "_collect_python_node_ids", forbidden_collection
        )
        assert (
            bundle_module._python_acceptance_receipt_errors(
                tmp_path, check_runtime=False
            )
            == ()
        )
        receipt["collection"]["node_ids"] = [
            "tests/test_fixture.py::test_fixture",
            "tests/test_fixture.py::test_fixture",
        ]
        receipt_path.write_bytes(bundle_module._canonical_json(receipt))
        assert "Python acceptance receipt collected node IDs are invalid" in (
            bundle_module._python_acceptance_receipt_errors(
                tmp_path, check_runtime=False
            )
        )
        receipt["collection"]["node_ids"] = ["tests/test_fixture.py::test_invented"]
        receipt_path.write_bytes(bundle_module._canonical_json(receipt))
        assert (
            "Python test receipt testcase roster differs from collected node IDs"
            in bundle_module._python_acceptance_receipt_errors(
                tmp_path, check_runtime=False
            )
        )
    receipt["collection"]["node_ids"] = ["tests/test_fixture.py::test_fixture"]
    receipt_path.write_bytes(bundle_module._canonical_json(receipt))
    # The deliberately mutated receipt is restored; all other inputs and evidence
    # must retain the exact bytes and mtimes across both static checks.
    assert {
        path: state for path, state in static_snapshot.items() if path != receipt_path
    } == {
        path: (path.read_bytes(), path.stat().st_mtime_ns)
        for path in tmp_path.rglob("*")
        if path.is_file() and path != receipt_path
    }

    receipt["collection"]["node_ids"] = ["tests/test_fixture.py::test_invented"]
    receipt_path.write_bytes(bundle_module._canonical_json(receipt))
    with pytest.raises(
        bundle_module.ReleaseBundleError,
        match="Python acceptance receipt collected node IDs are stale",
    ):
        bundle_module.build_python_acceptance_receipt(tmp_path)
    receipt["collection"]["node_ids"] = ["tests/test_fixture.py::test_fixture"]
    receipt_path.write_bytes(bundle_module._canonical_json(receipt))

    test_source.write_text("def test_fixture():\n    assert False\n", encoding="utf-8")
    with pytest.raises(
        bundle_module.ReleaseBundleError,
        match="Python acceptance receipt input snapshot is stale",
    ):
        bundle_module.build_python_acceptance_receipt(tmp_path)


@pytest.mark.parametrize("mutation", ["test_tree", "test_count_owner", "executor"])
def test_python_acceptance_rolls_back_when_inputs_or_executor_change_during_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    output = tmp_path / "output"
    manuscript = tmp_path / "manuscript"
    tests = tmp_path / "tests"
    output.mkdir()
    manuscript.mkdir()
    tests.mkdir()
    source = tmp_path / "src/fep_lean"
    source.mkdir(parents=True)
    (source / "a.py").write_text("value = 1\n", encoding="utf-8")
    test_source = tests / "test_fixture.py"
    test_source.write_text("def test_fixture():\n    assert True\n", encoding="utf-8")
    test_count_owner = manuscript / "manuscript_vars.yaml"
    test_count_owner.write_text(
        f"tests:\n  collected: {2 if mutation == 'test_count_owner' else 1}\n",
        encoding="utf-8",
    )
    prior = {
        output / "pytest.xml": b"prior junit\n",
        output / "coverage.xml": b"prior coverage\n",
        output / "python-acceptance.json": b"prior acceptance\n",
    }
    for path, data in prior.items():
        path.write_bytes(data)
    monkeypatch.setattr(bundle_module, "report_source_digest", lambda _root: "1" * 64)
    monkeypatch.setattr(bundle_module, "report_config_digest", lambda _root: "2" * 64)
    if mutation == "executor":
        executor_calls = 0
        stable_executor = bundle_module._python_acceptance_runtime_identity()

        def changing_executor() -> dict[str, object]:
            nonlocal executor_calls
            executor_calls += 1
            return {
                **stable_executor,
                "fingerprint_sha256": ("1" * 64 if executor_calls == 1 else "2" * 64),
            }

        monkeypatch.setattr(
            bundle_module,
            "_python_acceptance_runtime_identity",
            changing_executor,
        )

    def changing_run(command: list[str], **_kwargs: object) -> SimpleNamespace:
        if "--collect-only" in command:
            return SimpleNamespace(
                returncode=0,
                stdout=(
                    "tests/test_fixture.py::test_fixture\n1 test collected in 0.01s\n"
                ),
                stderr="",
            )
        (output / "pytest.xml").write_text(
            '<testsuite tests="1" failures="0" errors="0" skipped="0" '
            'time="0"><testcase classname="tests.test_fixture" '
            'name="test_fixture" time="0"/></testsuite>\n',
            encoding="utf-8",
        )
        (output / "coverage.xml").write_text(
            '<coverage line-rate="1" lines-valid="1" lines-covered="1">'
            '<packages><package><classes><class filename="fep_lean/a.py">'
            '<lines><line number="1" hits="1"/></lines></class></classes>'
            "</package></packages></coverage>\n",
            encoding="utf-8",
        )
        if mutation == "test_tree":
            test_source.write_text(
                "def test_fixture():\n    assert False\n", encoding="utf-8"
            )
        elif mutation == "test_count_owner":
            test_count_owner.write_text("tests:\n  collected: 1\n", encoding="utf-8")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(_subprocess, "run_process_group", changing_run)

    with pytest.raises(
        bundle_module.ReleaseBundleError,
        match=(
            "executor changed during acceptance"
            if mutation == "executor"
            else "changed during acceptance"
        ),
    ):
        bundle_module.run_python_acceptance(tmp_path)

    assert {path: path.read_bytes() for path in prior} == prior


def test_python_acceptance_rolls_back_after_an_interrupted_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = tmp_path / "output"
    manuscript = tmp_path / "manuscript"
    tests = tmp_path / "tests"
    output.mkdir()
    manuscript.mkdir()
    tests.mkdir()
    (tests / "test_fixture.py").write_text(
        "def test_fixture():\n    assert True\n", encoding="utf-8"
    )
    (manuscript / "manuscript_vars.yaml").write_text(
        "tests:\n  collected: 1\n", encoding="utf-8"
    )
    prior = {
        output / "pytest.xml": b"prior junit\n",
        output / "coverage.xml": b"prior coverage\n",
        output / "python-acceptance.json": b"prior acceptance\n",
    }
    for path, data in prior.items():
        path.write_bytes(data)
    monkeypatch.setattr(bundle_module, "report_source_digest", lambda _root: "1" * 64)
    monkeypatch.setattr(bundle_module, "report_config_digest", lambda _root: "2" * 64)

    def interrupted_run(command: list[str], **_kwargs: object) -> SimpleNamespace:
        if "--collect-only" in command:
            return SimpleNamespace(
                returncode=0,
                stdout=(
                    "tests/test_fixture.py::test_fixture\n1 test collected in 0.01s\n"
                ),
                stderr="",
            )
        (output / "pytest.xml").write_bytes(b"partial junit\n")
        (output / "coverage.xml").write_bytes(b"partial coverage\n")
        raise KeyboardInterrupt

    monkeypatch.setattr(_subprocess, "run_process_group", interrupted_run)

    with pytest.raises(KeyboardInterrupt):
        bundle_module.run_python_acceptance(tmp_path)

    assert {path: path.read_bytes() for path in prior} == prior


def test_python_acceptance_failure_removes_partial_new_receipts_and_restores_prior(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = tmp_path / "output"
    manuscript = tmp_path / "manuscript"
    tests = tmp_path / "tests"
    output.mkdir()
    manuscript.mkdir()
    tests.mkdir()
    (tests / "test_fixture.py").write_text(
        "def test_fixture():\n    assert True\n", encoding="utf-8"
    )
    (manuscript / "manuscript_vars.yaml").write_text(
        "tests:\n  collected: 1\n", encoding="utf-8"
    )
    acceptance = output / bundle_module.PYTHON_ACCEPTANCE_RECEIPT.name
    acceptance.write_bytes(b"prior acceptance\n")
    junit = output / bundle_module.PYTEST_RECEIPT.name
    coverage = output / bundle_module.PYTHON_COVERAGE_RECEIPT.name
    monkeypatch.setattr(bundle_module, "report_source_digest", lambda _root: "1" * 64)
    monkeypatch.setattr(bundle_module, "report_config_digest", lambda _root: "2" * 64)
    monkeypatch.setattr(
        bundle_module,
        "_python_acceptance_runtime_identity",
        lambda: {"fingerprint_sha256": "3" * 64},
    )
    monkeypatch.setattr(
        bundle_module,
        "collection_runtime_identity",
        lambda: {"pytest_arguments": []},
    )
    monkeypatch.setattr(
        bundle_module,
        "_python_acceptance_environment",
        lambda _temporary_root: {},
    )

    def failed_run(command: list[str], **_kwargs: object) -> SimpleNamespace:
        if "--collect-only" in command:
            return SimpleNamespace(
                returncode=0,
                stdout="tests/test_fixture.py::test_fixture\n1 test collected in 0.01s\n",
                stderr="",
            )
        junit.write_bytes(b"partial junit\n")
        coverage.write_bytes(b"partial coverage\n")
        return SimpleNamespace(returncode=3, stdout="", stderr="suite failed")

    monkeypatch.setattr(_subprocess, "run_process_group", failed_run)

    with pytest.raises(
        bundle_module.ReleaseBundleError,
        match="canonical Python acceptance command failed: suite failed",
    ):
        bundle_module.run_python_acceptance(tmp_path)

    assert not junit.exists()
    assert not coverage.exists()
    assert acceptance.read_bytes() == b"prior acceptance\n"


def test_python_acceptance_validator_aggregates_stale_noncanonical_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = tmp_path / "output"
    output.mkdir()
    receipt = {
        "schema_version": 2,
        "kind": "invented-receipt",
        "complete": False,
        "returncode": 1,
        "command": ["invented-command"],
        "executor": {"fingerprint_sha256": "stale"},
        "collection": {
            "command": ["invented-collection"],
            "node_ids": ["tests/test_fixture.py::test_invented"],
        },
        "inputs": {
            "before": {"fingerprint_sha256": "before"},
            "after": {"fingerprint_sha256": "stale"},
            "stable": False,
        },
        "tests": {"collected": 0},
        "coverage": {"line_rate": 0.0},
    }
    (tmp_path / bundle_module.PYTHON_ACCEPTANCE_RECEIPT).write_text(
        json.dumps(receipt, indent=2), encoding="utf-8"
    )
    monkeypatch.setattr(
        bundle_module,
        "_collect_python_node_ids",
        lambda _root, _temporary_root: ("tests/test_fixture.py::test_fixture",),
    )
    monkeypatch.setattr(
        bundle_module,
        "collection_runtime_identity",
        lambda: {"pytest_arguments": ["--collect-only"]},
    )
    executor_calls = 0

    def changing_executor() -> dict[str, str]:
        nonlocal executor_calls
        executor_calls += 1
        return {"fingerprint_sha256": "current" if executor_calls == 1 else "changed"}

    input_calls = 0

    def changing_inputs(_root: Path) -> dict[str, str]:
        nonlocal input_calls
        input_calls += 1
        return {"fingerprint_sha256": "current" if input_calls == 1 else "changed"}

    monkeypatch.setattr(
        bundle_module, "_python_acceptance_runtime_identity", changing_executor
    )
    monkeypatch.setattr(bundle_module, "_python_input_snapshot", changing_inputs)
    monkeypatch.setattr(
        bundle_module,
        "_python_evidence_summary",
        lambda _root: {
            "tests": {"collected": 1},
            "coverage": {"line_rate": 1.0},
        },
    )
    monkeypatch.setattr(
        bundle_module,
        "_pytest_receipt_errors",
        lambda _root, **_kwargs: ("underlying Python evidence is invalid",),
    )

    errors = bundle_module._python_acceptance_receipt_errors(tmp_path)

    assert {
        "underlying Python evidence is invalid",
        "Python acceptance receipt is not canonical sorted JSON",
        "Python acceptance receipt schema_version must be 3",
        "Python acceptance receipt kind is invalid",
        "Python acceptance receipt is not complete and green",
        "Python acceptance receipt command is not canonical",
        "Python acceptance receipt executor identity is stale",
        "Python acceptance receipt collection command is not canonical",
        "Python acceptance receipt collected node IDs are stale",
        "Python acceptance receipt input snapshots are not stable",
        "Python acceptance receipt input snapshot is stale",
        "Python acceptance receipt JUnit summary or hash is stale",
        "Python acceptance receipt coverage summary or hash is stale",
        "Python acceptance inputs changed during validation",
        "Python acceptance executor changed during validation",
    } <= set(errors)
