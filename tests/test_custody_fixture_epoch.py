"""A frozen synthetic epoch must never reaccept current publication evidence."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

from fep_lean.custody import apply as apply_module
from fep_lean.verification import horizon_acceptance as acceptance
from tests._support import custody_fixture_knobs as fixtures
from tests._support import h2_r0_custody as current_r0
from tests._support.lean435_migration import (
    bridge_dev_lock_predecessor,
    function_ratchet_metadata_predecessor,
    historical_manifest_bytes,
    historical_metadata_bytes,
)
from tests._support.release_lineage import custody_root

REPO_ROOT = Path(__file__).resolve().parents[1]


def _production_snapshot() -> dict[str, bytes]:
    paths = set(acceptance.CURRENT_FILES) | set(
        acceptance.native_source_paths(REPO_ROOT)
    )
    paths |= {
        "pyproject.toml",
        "uv.lock",
        apply_module.PRIOR_07,
        apply_module.SUCCESSOR_07,
        current_r0.H3_ADDENDUM_PATH,
        current_r0.VALIDATOR_PATH,
        acceptance.TERMINAL_RECEIPT,
    }
    return {relative: (REPO_ROOT / relative).read_bytes() for relative in paths}


def test_frozen_validator_has_recorded_commit_and_byte_digest() -> None:
    data = fixtures._historical_r0_bytes(REPO_ROOT)
    assert fixtures.HISTORICAL_R0_COMMIT == ("99e5cdf0690bebf219a49b598d9d80ff1da075d5")
    assert fixtures.HISTORICAL_R0_SOURCE == current_r0.VALIDATOR_PATH
    assert hashlib.sha256(data).hexdigest() == fixtures.HISTORICAL_R0_SHA256
    assert data != (REPO_ROOT / current_r0.VALIDATOR_PATH).read_bytes()


def test_frozen_validator_tampering_is_rejected_before_load_or_stage(
    tmp_path: Path,
) -> None:
    resource = tmp_path / fixtures.HISTORICAL_R0_RESOURCE
    resource.parent.mkdir(parents=True)
    resource.write_bytes(fixtures._historical_r0_bytes(REPO_ROOT) + b"\n# tamper\n")
    for check in (
        fixtures._historical_r0_validator,
        fixtures.declared_closure,
    ):
        with pytest.raises(AssertionError, match="frozen historical R0 validator"):
            check(tmp_path)


def test_loader_executes_checked_bytes_after_resource_mutation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    checked = fixtures._historical_r0_bytes(REPO_ROOT)
    resource = tmp_path / fixtures.HISTORICAL_R0_RESOURCE
    resource.parent.mkdir(parents=True)
    resource.write_bytes(checked)
    original = fixtures._historical_r0_bytes

    def mutate_after_check(root: Path) -> bytes:
        data = original(root)
        resource.write_text("raise RuntimeError('unchecked substituted source')\n")
        return data

    monkeypatch.setattr(fixtures, "_historical_r0_bytes", mutate_after_check)
    loaded = fixtures._historical_r0_validator(tmp_path)
    assert loaded.PRIOR_PATH == current_r0.PRIOR_PATH
    assert loaded.__name__ == "fep_lean_synthetic_pre_h3_r0_validator"
    assert not any(resource.parent.rglob("*.pyc"))


def test_synthetic_epoch_uses_real_isolated_historical_validator(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    before = _production_snapshot()
    live_module = sys.modules["tests._support.h2_r0_custody"]
    root = fixtures.fixture_root(tmp_path, monkeypatch)
    historical = fixtures._historical_r0_validator(root)
    assert historical is not current_r0
    assert sys.modules["tests._support.h2_r0_custody"] is live_module
    # Run the actual historical validator over the rebound disposable source.
    historical.PRIOR_SHA256 = hashlib.sha256(
        (root / apply_module.PRIOR_07).read_bytes()
    ).hexdigest()
    result = historical.validate_h2_r0_custody(root)
    assert result["gate"] == "H2.7-R0-custody"
    provenance = json.loads((root / "output/custody-unit-fixture.json").read_text())
    assert provenance["real_native_or_scientific_acceptance"] is False
    assert provenance["compiler"] == "SYNTHETIC-UNIT-FIXTURE-NO-COMPILER"
    assert provenance["epoch"] == {
        "kind": "synthetic-pre-H3-custody",
        "validator_commit": fixtures.HISTORICAL_R0_COMMIT,
        "validator_source": fixtures.HISTORICAL_R0_SOURCE,
        "validator_resource": fixtures.HISTORICAL_R0_RESOURCE,
        "validator_sha256": fixtures.HISTORICAL_R0_SHA256,
        "current_h3_owners_admitted": False,
    }
    assert not (root / current_r0.H3_ADDENDUM_PATH).exists()
    # Current canonical source copies remain available to shared diagnostics;
    # the fabricated custody epoch does not admit their H3 manifest owners.
    assert all((root / path).exists() for path in current_r0.H3_OWNER_SOURCE_PATHS)
    owners = current_r0._manifest_owners((root / current_r0.MANIFEST_PATH).read_text())
    current_owners = current_r0._manifest_owners(
        (REPO_ROOT / current_r0.MANIFEST_PATH).read_text()
    )
    assert len(owners) == 69 and len(current_owners) == 72
    category_resource = "compositions/finite_kernel_category.lean"
    assert category_resource in {owner["resource"] for owner in current_owners}
    assert category_resource not in {owner["resource"] for owner in owners}
    assert before == _production_snapshot()
    # The current validator refuses synthetic rewrites of the immutable past.
    with pytest.raises(ValueError, match="immutable R0 prior changed"):
        current_r0.validate_h2_r0_custody(root)


def test_current_post_h3_terminal_is_still_refused_without_mutation(
    tmp_path: Path,
) -> None:
    before = _production_snapshot()
    recorded_root = custody_root(REPO_ROOT, tmp_path)
    # The current category owner is outside the frozen manifest transition.
    with pytest.raises(
        ValueError,
        match=r"^H3 owner subtraction does not recover the historical custody manifest$",
    ):
        current_r0.validate_h2_r0_custody(recorded_root)
    # Restore only the disposable manifest from its authenticated companion
    # to reach the independent metadata and migrated-source guards below.
    manifest = recorded_root / current_r0.MANIFEST_PATH
    manifest.write_bytes(historical_manifest_bytes(REPO_ROOT, manifest.read_bytes()))
    addendum = json.loads((REPO_ROOT / current_r0.H3_ADDENDUM_PATH).read_bytes())
    recorded_manifest_digest = addendum["source_sha256"][current_r0.MANIFEST_PATH]
    assert hashlib.sha256(manifest.read_bytes()).hexdigest() == recorded_manifest_digest
    # The uv pin and reviewed tooling scope are real metadata changes beyond
    # the approved release-token reversal; the historical validator refuses.
    with pytest.raises(
        ValueError,
        match="release metadata has unlisted changes beyond the root version: pyproject.toml",
    ):
        current_r0.validate_h2_r0_custody(recorded_root)
    # Authenticate the exact reviewed live profile and historical companion
    # before restoring only the disposable metadata to its recorded 1.4 epoch.
    # The migrated formal sources must still fail the next historical guard.
    metadata = recorded_root / "pyproject.toml"
    metadata.write_bytes(historical_metadata_bytes(REPO_ROOT, metadata.read_bytes()))
    recorded_digest = addendum["source_sha256"]["pyproject.toml"]
    assert hashlib.sha256(metadata.read_bytes()).hexdigest() == recorded_digest
    # The new locked dev parser is also real source drift; authenticate and
    # reverse only that exact delta in this disposable historical control.
    with pytest.raises(
        ValueError,
        match="release metadata has unlisted changes beyond the root version: uv.lock",
    ):
        current_r0.validate_h2_r0_custody(recorded_root)
    lock = recorded_root / "uv.lock"
    lock.write_bytes(bridge_dev_lock_predecessor(lock.read_bytes()))
    with pytest.raises(ValueError, match="stale historical custody source digest"):
        current_r0.validate_h2_r0_custody(recorded_root)
    with pytest.raises(
        ValueError, match="current validator/diagnostic source mismatch"
    ):
        acceptance.validate_terminal_acceptance(REPO_ROOT)
    assert before == _production_snapshot()


@pytest.mark.parametrize("tamper", ("none", "append", "ceiling", "exception", "rule"))
def test_function_ratchet_metadata_reversal_authenticates_complete_profile(
    tamper: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    from fep_lean import __version__
    from tests._support import lean435_migration as migration

    before = _production_snapshot()
    live = (REPO_ROOT / "pyproject.toml").read_bytes()
    predecessor = function_ratchet_metadata_predecessor(live)
    recorded = current_r0.RELEASE_METADATA_REPLACEMENTS["pyproject.toml"][1].encode()
    current = recorded.replace(b'"1.4.0"', f'"{__version__}"'.encode())
    assert predecessor.count(current) == 1
    normalized = predecessor.replace(
        current, recorded.replace(b'"1.4.0"', b'"1.6.0"'), 1
    )
    assert hashlib.sha256(normalized).hexdigest() == (
        "734fc9d2bf373242030d38f16bd64439c752ce3f59f5319f83ddec8c5c696705"
    )
    if tamper == "none":
        assert function_ratchet_metadata_predecessor(predecessor) == predecessor
        assert historical_metadata_bytes(REPO_ROOT, live) == historical_metadata_bytes(
            REPO_ROOT, predecessor
        )
    else:
        changed = {
            "append": live + b"\n# unreviewed metadata\n",
            "ceiling": live.replace(b"max-statements = 100", b"max-statements = 101"),
            "exception": live + b'"tests/extra.py" = ["PLR0915"]\n',
            "rule": live.replace(
                b'    "PLR0915", # statement complexity;',
                b'    "PLR0914", # statement complexity;',
            ),
        }[tamper]
        assert changed != live
        assert function_ratchet_metadata_predecessor(changed) == changed

        def forbidden_parse(*args: object, **kwargs: object) -> None:
            pytest.fail("unknown metadata must fail before companion parsing")

        monkeypatch.setattr(migration.json, "loads", forbidden_parse)
        with pytest.raises(AssertionError, match="unreviewed normalized metadata"):
            historical_metadata_bytes(REPO_ROOT, changed)
    assert before == _production_snapshot()
