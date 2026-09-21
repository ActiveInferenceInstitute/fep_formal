"""The bridge's read-only checks fail closed on drift and invalid evidence."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from fep_lean.bridge import operations
from fep_lean.bridge.certificates import compare
from fep_lean.bridge.custody import (
    CONTENT_DRIFT,
    FRESH,
    STALE_CUSTODY,
    classify_document,
    fingerprint,
    refresh_signature,
    validate_binding,
    write_json,
)


def document(commit: str = "old", body: str = "A\nB\n") -> str:
    return body + "## Signature\nsource_commit: " + commit + "\npipeline_commit: gnn\n"


def test_only_signature_custody_changes_are_refreshable(tmp_path: Path) -> None:
    path = tmp_path / "model.md"
    path.write_text(document())
    assert classify_document(document(), document()) == FRESH
    assert classify_document(document(), document("new")) == STALE_CUSTODY
    refresh_signature(path, document("new"))
    assert path.read_text() == document("new")


@pytest.mark.parametrize(
    "body", ["B\nA\n", "A\nA\nB\n", "A\n", "A\nB\nsource_commit: new\n"]
)
def test_refresh_refuses_content_changes_without_writing(
    tmp_path: Path, body: str
) -> None:
    path = tmp_path / "model.md"
    path.write_text(document(body=body))
    before = (path.read_bytes(), path.stat().st_mtime_ns)
    assert classify_document(path.read_text(), document("new")) == CONTENT_DRIFT
    with pytest.raises(ValueError, match="content"):
        refresh_signature(path, document("new"))
    assert (path.read_bytes(), path.stat().st_mtime_ns) == before


@pytest.mark.parametrize(
    "bad",
    [
        "",
        "## Signature\nsource_commit: one\nsource_commit: two\n",
        "## Signature\n## Signature\n",
    ],
)
def test_ambiguous_provenance_is_content_drift(bad: str) -> None:
    assert classify_document(bad, document()) == CONTENT_DRIFT


def test_binding_checks_missing_changed_and_extra_owners(tmp_path: Path) -> None:
    (tmp_path / "owner.py").write_text("original")
    binding = fingerprint(tmp_path, ["owner.py"])
    assert validate_binding(tmp_path, binding, ["owner.py"]) == []
    (tmp_path / "owner.py").write_text("changed")
    assert validate_binding(tmp_path, binding, ["owner.py"])
    (tmp_path / "owner.py").unlink()
    assert validate_binding(tmp_path, binding, ["owner.py"])
    assert validate_binding(tmp_path, {}, ["owner.py"])


@pytest.mark.parametrize("path", ["../outside", "/absolute", "a/../../outside"])
def test_binding_rejects_escape(tmp_path: Path, path: str) -> None:
    with pytest.raises(ValueError):
        fingerprint(tmp_path, [path])


def test_binding_rejects_symlinked_owners(tmp_path: Path) -> None:
    target = tmp_path / "real.py"
    target.write_text("content")
    (tmp_path / "link.py").symlink_to(target)
    with pytest.raises(ValueError):
        fingerprint(tmp_path, ["link.py"])


def test_explicit_json_emission_is_deterministic(tmp_path: Path) -> None:
    path = tmp_path / "receipt.json"
    write_json(path, {"b": 2, "a": 1})
    before = (path.read_bytes(), path.stat().st_mtime_ns)
    write_json(path, {"a": 1, "b": 2})
    assert (path.read_bytes(), path.stat().st_mtime_ns) == before
    assert json.loads(path.read_bytes()) == {"a": 1, "b": 2}


@pytest.mark.parametrize("tolerance", [float("inf"), float("nan"), -1.0, True])
def test_invalid_tolerances_never_pass(tolerance: float) -> None:
    with pytest.raises(ValueError, match="tolerance"):
        compare(
            {"policy_posterior": [[999, -998]], "variational_free_energy": [999]},
            tolerance,
        )


@pytest.mark.parametrize(
    "value", [float("inf"), float("nan"), True, "0.25", None, 10**400]
)
def test_invalid_numeric_payload_never_passes(value: object) -> None:
    _, _, ok = compare(
        {
            "policy_posterior": [[value, 0.75]],
            "variational_free_energy": [0.6931471805599453],
        },
        1e-6,
    )
    assert not ok


def test_numerical_agreement_does_not_claim_proof() -> None:
    certificates, _, ok = compare(
        {
            "policy_posterior": [[0.25, 0.75]],
            "variational_free_energy": [0.6931471805599453],
        },
        1e-6,
    )
    assert ok
    assert all("numerical witness" in c["lean_evidence_plane"] for c in certificates)


@pytest.fixture
def pair(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path]:
    """Two independent tiny source checkouts, with no installed sibling required."""
    root, gnn = tmp_path / "fep", tmp_path / "gnn"
    monkeypatch.setattr(operations, "_head", lambda _: "a" * 40)
    from fep_lean.formal.manifest import FORMAL_MODULES

    for module in FORMAL_MODULES:
        for prefix in ("src/fep_lean/formal", "lean/FepSketches"):
            path = root / prefix / module.resource
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("-- fixture formal owner\n")
    for checkout, key in ((root, "fep_lean"), (gnn, "gnn")):
        for name in operations.owner_roster(checkout, key):
            path = checkout / name
            path.parent.mkdir(parents=True, exist_ok=True)
            if not path.exists():
                path.write_text("fixture owner\n")
    for relative in operations.EMITTERS.values():
        (root / relative).write_text(
            "def build_document(source, pipeline):\n"
            '    return "A\\nB\\n## Signature\\nsource_commit: " + source + "\\npipeline_commit: " + pipeline + "\\n"\n'
        )
    (root / operations.CONTRACT).write_text("same contract\n")
    (gnn / operations.MIRROR).write_text("same contract\n")
    write_json(root / operations.SYNTAX_PIN, fingerprint(gnn, operations.SYNTAX_FILES))
    operations.pin_sources(root, gnn)
    for model in operations.DOCUMENTS:
        operations.emit(root, gnn, model)
    return root, gnn


def snapshot(root: Path) -> dict[str, tuple[bytes, int]]:
    return {
        str(p.relative_to(root)): (p.read_bytes(), p.stat().st_mtime_ns)
        for p in root.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts
    }


def test_status_and_checks_do_not_write(pair: tuple[Path, Path]) -> None:
    root, gnn = pair
    before = snapshot(root), snapshot(gnn)
    assert operations.status(root, gnn)["status"] == "ok"
    assert all(operations.emit(root, gnn, m, check=True) for m in operations.DOCUMENTS)
    assert (snapshot(root), snapshot(gnn)) == before


def test_unrelated_head_movement_does_not_change_custody(
    pair: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    root, gnn = pair
    monkeypatch.setattr(operations, "_head", lambda _: "b" * 40)
    assert operations.status(root, gnn)["status"] == "ok"


def test_status_flags_unpinned_syntax_surface(pair: tuple[Path, Path]) -> None:
    """Drift on either pinned syntax file must fail the W1 surface check."""
    root, gnn = pair
    (gnn / operations.SYNTAX_FILES[0]).write_text("drifted syntax\n")
    before = snapshot(gnn)
    report = operations.status(root, gnn)
    assert report["checks"]["syntax_surface"] == {"passed": False}
    assert report["status"] == "error"
    assert snapshot(gnn) == before


def test_status_fails_closed_on_missing_syntax_pin(pair: tuple[Path, Path]) -> None:
    root, gnn = pair
    (root / operations.SYNTAX_PIN).unlink()
    report = operations.status(root, gnn)
    assert report["checks"]["contracts"]["passed"] is False
    assert report["checks"]["contracts"]["errors"]
    assert report["status"] == "error"


def test_status_fails_closed_on_missing_source_pin(pair: tuple[Path, Path]) -> None:
    root, gnn = pair
    (root / operations.PIN).unlink()
    report = operations.status(root, gnn)
    assert report["checks"]["source_binding"]["passed"] is False
    assert report["checks"]["source_binding"]["errors"]
    assert report["status"] == "error"


def test_status_flags_stale_emitted_document(pair: tuple[Path, Path]) -> None:
    """A mutated emitted document is stale, and status must not re-emit."""
    root, gnn = pair
    document = root / operations.DOCUMENTS["finite"]
    document.write_text(document.read_text(encoding="utf-8") + "drift\n")
    before = snapshot(root)
    report = operations.status(root, gnn)
    assert report["checks"]["finite_freshness"] == {
        "passed": False,
        "status": "STALE",
    }
    assert report["status"] == "error"
    assert snapshot(root) == before


@pytest.mark.parametrize("change", ["add", "delete", "change"])
def test_relevant_roster_changes_are_rejected(
    pair: tuple[Path, Path], change: str
) -> None:
    root, gnn = pair
    if change == "add":
        path = gnn / "src/gnn/render/new.py"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("new owner")
    elif change == "delete":
        (gnn / "src/gnn/main.py").unlink()
    else:
        (gnn / "src/gnn/main.py").write_text("changed")
    assert operations.status(root, gnn)["status"] == "error"
    with pytest.raises(ValueError, match="stale"):
        operations.emit(root, gnn, "finite")


def result_file(root: Path) -> Path:
    path = root / "output/run/results.json"
    write_json(
        path,
        {
            "policy_posterior": [[0.25, 0.75]],
            "variational_free_energy": [0.6931471805599453],
        },
    )
    return path


def test_receipt_validation_is_read_only_and_recomputes_evidence(
    pair: tuple[Path, Path],
) -> None:
    root, gnn = pair
    path = result_file(root)
    before = snapshot(root)
    receipt = operations.certificate_receipt(root, gnn, path)
    assert not receipt["native_claim_ready"]
    assert not receipt["execution_source_verified"]
    assert operations.validate_certificate(root, gnn, receipt) == []
    assert snapshot(root) == before
    receipt["certificates"][0]["delta"] = "invented"
    assert operations.validate_certificate(root, gnn, receipt)


@pytest.mark.parametrize(
    "mutation", ["artifact", "owner", "source_pin", "tolerance", "path"]
)
def test_receipt_tampering_is_rejected(pair: tuple[Path, Path], mutation: str) -> None:
    root, gnn = pair
    path = result_file(root)
    receipt = operations.certificate_receipt(root, gnn, path)
    if mutation == "artifact":
        path.write_text('{"policy_posterior": [[0.5, 0.5]]}')
    elif mutation == "owner":
        (gnn / "src/gnn/main.py").write_text("modified")
    elif mutation == "source_pin":
        receipt["source_pin"]["gnn"]["owners"] = {}
    elif mutation == "tolerance":
        receipt["tolerance"] = float("inf")
    else:
        receipt["results_path"] = "../escape.json"
    assert operations.validate_certificate(root, gnn, receipt)


def test_comparison_rejects_mid_check_source_change(
    pair: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    root, gnn = pair
    original = operations.compare

    def changed(*args: object) -> object:
        (gnn / "src/gnn/main.py").write_text("changed during check")
        return original(*args)

    monkeypatch.setattr(operations, "compare", changed)
    with pytest.raises(ValueError, match="changed during"):
        operations.certificate_receipt(root, gnn, result_file(root))


def test_legacy_certifier_default_does_not_emit(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    import runpy

    root = Path(__file__).resolve().parents[1]
    script = root / "specs/gnn-bridge-p3-certificates/certify.py"
    entry = runpy.run_path(str(script))
    results = result_file(tmp_path)
    before = snapshot(script.parent)
    assert entry["main"](["--results", str(results)]) == 0
    assert snapshot(script.parent) == before
    assert json.loads(capsys.readouterr().out)["source_bound"] is False


def test_bridge_cli_round_trip_and_missing_results(
    pair: tuple[Path, Path], tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    import argparse

    from fep_lean.bridge.cli import add_arguments, run

    root, gnn = pair
    parser = argparse.ArgumentParser()
    add_arguments(parser)
    assert run(root, parser.parse_args(["status", "--gnn-root", str(gnn)])) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "ok"
    assert run(root, parser.parse_args(["certify", "--gnn-root", str(gnn)])) == 1
    capsys.readouterr()
    receipt = tmp_path / "receipt.json"
    results = result_file(root)
    assert (
        run(
            root,
            parser.parse_args(
                [
                    "certify",
                    "--gnn-root",
                    str(gnn),
                    "--results",
                    str(results),
                    "--receipt",
                    str(receipt),
                ]
            ),
        )
        == 0
    )
    capsys.readouterr()
    assert (
        run(
            root,
            parser.parse_args(
                [
                    "verify-certificate",
                    "--gnn-root",
                    str(gnn),
                    "--receipt",
                    str(receipt),
                ]
            ),
        )
        == 0
    )
    capsys.readouterr()
    assert receipt.with_suffix(".md").is_file()


def test_emitter_ignores_unbound_bytecode(pair: tuple[Path, Path]) -> None:
    import importlib.util
    import marshal
    import struct

    root, _ = pair
    emitter = root / operations.EMITTERS["finite"]
    pin = operations.read_object(root / operations.PIN)
    expected = operations.projected_document(root, "finite", pin)
    cache = Path(importlib.util.cache_from_source(str(emitter)))
    cache.parent.mkdir(parents=True, exist_ok=True)
    malicious = compile(
        "def build_document(*args): return 'poisoned'", str(emitter), "exec"
    )
    stat = emitter.stat()
    cache.write_bytes(
        importlib.util.MAGIC_NUMBER
        + struct.pack("<III", 0, int(stat.st_mtime), stat.st_size)
        + marshal.dumps(malicious)
    )
    assert operations.projected_document(root, "finite", pin) == expected


@pytest.mark.parametrize(
    "operation",
    ["certify", "pin", "status", "verify-certificate", "verify-document"],
)
@pytest.mark.parametrize("flag", ["--check", "--refresh-digests"])
def test_emission_flags_reject_other_operations_without_writing(
    pair: tuple[Path, Path], operation: str, flag: str
) -> None:
    import argparse

    from fep_lean.bridge.cli import add_arguments, run

    root, gnn = pair
    parser = argparse.ArgumentParser()
    add_arguments(parser)
    results = result_file(root)
    before = snapshot(root)
    args = parser.parse_args(
        [
            operation,
            flag,
            "--gnn-root",
            str(gnn),
            "--results",
            str(results),
            "--receipt",
            str(root / "receipt.json"),
        ]
    )
    assert run(root, args) == 1
    assert snapshot(root) == before


def test_markdown_receipt_preserves_numerical_only_scope(
    pair: tuple[Path, Path],
) -> None:
    root, gnn = pair
    receipt = operations.certificate_receipt(root, gnn, result_file(root))
    target = root / "certificate.json"
    operations.emit_certificate(target, receipt)
    markdown = target.with_suffix(".md").read_text()
    assert "execution_source_verified: false" in markdown
    assert "native_claim_ready: false" in markdown
    assert "execution provenance unverified" in markdown


@pytest.mark.parametrize(
    "payload",
    [
        '{"schema_version": 1, "fep_lean": {"commit": "a", "commit": "b"}}',
        '{"owners": {"a": "x"}, "owners": {}}',
    ],
    ids=["duplicate-nested-key", "duplicate-top-level-key"],
)
def test_read_object_rejects_duplicate_keys(tmp_path: Path, payload: str) -> None:
    target = tmp_path / "pin.json"
    target.write_text(payload, encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate JSON key"):
        operations.read_object(target)


@pytest.mark.parametrize(
    "payload",
    ['{"x": NaN}', '{"x": Infinity}', '{"x": -Infinity}'],
)
def test_read_object_rejects_nonfinite_constants(tmp_path: Path, payload: str) -> None:
    target = tmp_path / "pin.json"
    target.write_text(payload, encoding="utf-8")
    with pytest.raises(ValueError, match="non-finite JSON constant"):
        operations.read_object(target)


def test_read_object_accepts_wellformed_pin(tmp_path: Path) -> None:
    target = tmp_path / "pin.json"
    target.write_text('{"schema_version": 1, "owners": {"a": "b"}}', encoding="utf-8")
    assert operations.read_object(target) == {
        "schema_version": 1,
        "owners": {"a": "b"},
    }
