"""Bridge failures preserve artifacts and cannot promote numerical evidence."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

import pytest

from fep_formal.bridge import custody, operations
from fep_formal.bridge.certificates import compare, render_markdown
from fep_formal.bridge.cli import add_arguments, run
from tests import test_gnn_bridge_operations as bridge_fixtures
from tests.test_gnn_bridge_operations import (
    document,
    result_file,
    snapshot,
)

pair = bridge_fixtures.pair


def _arguments(gnn: Path, *arguments: str) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    add_arguments(parser)
    return parser.parse_args([*arguments, "--gnn-root", str(gnn)])


def test_efe_observation_is_reported_without_becoming_a_certificate() -> None:
    certificates, observations, passed = compare(
        {
            "policy_posterior": [[0.25, 0.75]],
            "variational_free_energy": [0.6931471805599453],
            "expected_free_energy": [[-0.42]],
        },
        1e-6,
    )
    assert passed
    assert [entry["certificate"] for entry in certificates] == ["C1", "C2"]
    assert len(observations) == 1
    assert observations[0]["id"] == "O1"
    assert "-0.42" in observations[0]["executed_value"]
    assert "different C conventions" in observations[0]["note"]
    markdown = render_markdown(certificates, observations, Path("results.json"), passed)
    assert "## Observations (findings, exact numbers)" in markdown
    assert "O1: executed" in markdown
    assert "-0.42" in markdown
    assert "native_claim_ready: false" in markdown


def test_unknown_signature_metadata_is_content_not_refreshable_custody() -> None:
    original = document() + "reviewer: original\n"
    assert custody.classify_document(original, original) == custody.FRESH
    assert (
        custody.classify_document(original, original.replace("original", "changed"))
        == custody.CONTENT_DRIFT
    )
    missing_commit = document().replace("pipeline_commit: gnn\n", "")
    assert (
        custody.classify_document(missing_commit, document()) == custody.CONTENT_DRIFT
    )


def test_atomic_emission_refuses_symlink_without_changing_target(
    tmp_path: Path,
) -> None:
    target = tmp_path / "target.md"
    target.write_text("original")
    link = tmp_path / "receipt.md"
    link.symlink_to(target)
    with pytest.raises(ValueError, match="symlink"):
        custody.write_text(link, "replacement")
    assert link.is_symlink()
    assert target.read_text() == "original"


def test_failed_atomic_replacement_preserves_prior_and_removes_temporary_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "receipt.md"
    target.write_text("accepted content")
    before = snapshot(tmp_path)

    def refuse_replace(source: str, destination: Path) -> None:
        assert Path(source).read_text() == "replacement"
        assert destination == target
        raise OSError("simulated atomic replacement failure")

    monkeypatch.setattr(custody.os, "replace", refuse_replace)
    with pytest.raises(OSError, match="replacement failure"):
        custody.write_text(target, "replacement")
    assert snapshot(tmp_path) == before


def test_unknown_repository_and_model_are_explicit_errors(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="unknown repository"):
        operations.owner_roster(tmp_path, "unregistered")
    with pytest.raises(ValueError, match="unknown bridge model"):
        operations.projected_document(tmp_path, "unregistered", {})


def test_explicit_cli_pin_records_each_real_checkout_head(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root, gnn = tmp_path / "fep", tmp_path / "gnn"
    for checkout, repository in ((root, "fep_lean"), (gnn, "gnn")):
        checkout.mkdir()
        for name in operations.owner_roster(checkout, repository):
            path = checkout / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"{repository} owner\n")
        subprocess.run(["git", "init", "-q", str(checkout)], check=True)
        subprocess.run(
            [
                "git",
                "-c",
                "user.name=Bridge Test",
                "-c",
                "user.email=bridge@example.test",
                "-c",
                "core.hooksPath=/dev/null",
                "commit",
                "--allow-empty",
                "--no-gpg-sign",
                "-qm",
                repository,
            ],
            cwd=checkout,
            check=True,
        )
    assert run(root, _arguments(gnn, "pin")) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["status"] == "ok"
    assert "existing receipts are not promoted" in output["note"]
    pin = json.loads((root / operations.PIN).read_text())
    for checkout, repository in ((root, "fep_lean"), (gnn, "gnn")):
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=checkout,
            check=True,
            text=True,
            capture_output=True,
        ).stdout.strip()
        assert pin[repository]["commit"] == head
        assert pin[repository]["owners"] == custody.fingerprint(
            checkout, operations.owner_roster(checkout, repository)
        )
    assert operations.check_sources(root, gnn, pin) == []


@pytest.mark.parametrize("malformed", [None, {"commit": "bad", "owners": {}}, []])
def test_malformed_source_entries_fail_closed(
    pair: tuple[Path, Path], malformed: object
) -> None:
    root, gnn = pair
    pin = json.loads((root / operations.PIN).read_text())
    pin["schema_version"] = 2
    pin["fep_lean"] = malformed
    pin["gnn"]["owners"] = []
    assert operations.check_sources(root, gnn, pin) == [
        "unsupported source pin schema",
        "malformed fep_lean source binding",
        "malformed gnn source binding",
    ]


@pytest.mark.parametrize("fault", ["missing", "array", "invalid_json"])
def test_status_reports_unreadable_pin_and_contracts_without_writing(
    pair: tuple[Path, Path], fault: str
) -> None:
    root, gnn = pair
    path = root / operations.PIN
    if fault == "missing":
        path.unlink()
    else:
        path.write_text("[]" if fault == "array" else "{invalid")
    (gnn / operations.MIRROR).unlink()
    before = snapshot(root), snapshot(gnn)
    result = operations.status(root, gnn)
    assert result["status"] == "error"
    assert result["native_claim_ready"] is False
    assert result["checks"]["source_binding"]["passed"] is False
    assert result["checks"]["source_binding"]["errors"]
    assert result["checks"]["contracts"]["passed"] is False
    assert result["checks"]["contracts"]["errors"]
    if fault == "array":
        assert (
            "JSON root must be an object"
            in result["checks"]["source_binding"]["errors"][0]
        )
    assert (snapshot(root), snapshot(gnn)) == before


def test_projected_document_rejects_changed_emitter_before_executing_it(
    pair: tuple[Path, Path],
) -> None:
    root, _ = pair
    pin = json.loads((root / operations.PIN).read_text())
    marker = root / "must-not-exist"
    (root / operations.EMITTERS["finite"]).write_text(
        f"from pathlib import Path\nPath({str(marker)!r}).write_text('executed')\n"
    )
    with pytest.raises(ValueError, match="emitter source changed"):
        operations.projected_document(root, "finite", pin)
    assert not marker.exists()


def test_emit_cli_checks_stale_document_then_refreshes_only_its_signature(
    pair: tuple[Path, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    root, gnn = pair
    path = root / operations.DOCUMENTS["finite"]
    expected = path.read_text()
    path.write_text(
        expected.replace("source_commit: " + "a" * 40, "source_commit: old")
    )
    before = snapshot(root)
    assert run(root, _arguments(gnn, "emit", "--check")) == 1
    assert json.loads(capsys.readouterr().out) == {
        "status": "error",
        "failure_reason": "bridge operation refused",
        "details": {
            "result": {"status": "error", "model": "finite", "read_only": True}
        },
    }
    assert snapshot(root) == before
    assert run(root, _arguments(gnn, "emit", "--refresh-digests")) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "ok"
    assert path.read_text() == expected


def test_certification_cli_rejects_stale_document_without_emitting_receipts(
    pair: tuple[Path, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    root, gnn = pair
    results = result_file(root)
    (root / operations.DOCUMENTS["finite"]).write_text("stale body")
    target = root / "rejected-receipt.json"
    before = snapshot(root)
    assert (
        run(
            root,
            _arguments(
                gnn, "certify", "--results", str(results), "--receipt", str(target)
            ),
        )
        == 1
    )
    assert (
        json.loads(capsys.readouterr().out)["failure_reason"]
        == "finite document is stale"
    )
    assert snapshot(root) == before
    assert not target.exists()
    assert not target.with_suffix(".md").exists()


def test_verification_cli_requires_an_explicit_receipt(
    pair: tuple[Path, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    root, gnn = pair
    before = snapshot(root)
    assert run(root, _arguments(gnn, "verify-certificate")) == 1
    assert (
        json.loads(capsys.readouterr().out)["failure_reason"]
        == "verify-certificate requires --receipt"
    )
    assert snapshot(root) == before
