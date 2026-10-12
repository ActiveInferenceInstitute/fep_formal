"""Cascadia river-homing slice: fixtures, generator, GNN AST and native receipts."""

from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
from types import ModuleType

import pytest

from tests._support.lake import lake_executable

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SLICE = PROJECT_ROOT / "specs" / "cascadia-geo-act-proof"
FIXTURES = SLICE / "fixtures"
RETAINED_RECEIPT = SLICE / "native_receipt.json"


def _load(name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        f"cascadia_{name}", SLICE / f"{name}.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def generator() -> ModuleType:
    """The slice generator, loaded lazily so collection never needs ``specs/``."""
    return _load("generate_probe")


@pytest.fixture(scope="module")
def verifier() -> ModuleType:
    """The slice native verifier, loaded lazily."""
    return _load("verify_native")


def _copy_fixtures(tmp_path: Path) -> Path:
    target = tmp_path / "fixtures"
    shutil.copytree(FIXTURES, target)
    return target


def test_generator_check_gate_is_fresh() -> None:
    result = subprocess.run(
        [sys.executable, str(SLICE / "generate_probe.py"), "--check"],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
        timeout=120,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_fixture_provenance_digests_match_the_copied_bytes(
    generator: ModuleType,
) -> None:
    record = json.loads((FIXTURES / "provenance.json").read_text(encoding="utf-8"))
    for name, digest in record["files"].items():
        assert generator.sha256_bytes((FIXTURES / name).read_bytes()) == digest
    export = json.loads(
        (FIXTURES / "smith_river_homing.export.json").read_text(encoding="utf-8")
    )
    source = (FIXTURES / "smith_river_homing.gnn.md").read_bytes()
    assert export["source_sha256"] == generator.sha256_bytes(source)
    assert export["producer_module"] == "gnn.export.geo_infer"


def test_fixtures_load_with_exact_power_of_two_tables(generator: ModuleType) -> None:
    data = generator.load_fixtures()
    assert (data["n"], data["m"], data["u"]) == (26, 12, 4)
    assert (data["a_den"], data["b_den"], data["d_den"], data["e_den"]) == (64, 4, 4, 8)
    for action in range(data["u"]):
        for previous in range(data["n"]):
            assert sum(data["b_num"][action][previous]) == data["b_den"]
    assert [
        data["roles"].count(role)
        for role in ("sea", "main", "slough", "tributary", "natal")
    ] == [1, 16, 2, 3, 4]


def test_derived_facts_match_the_hand_computation(generator: ModuleType) -> None:
    data = generator.load_fixtures()
    facts = generator.derived_facts(data)
    assert facts["bound"] == 13
    assert [generator.ACTIONS[a] for a in facts["plan"]] == ["upstream"] * 9 + [
        "turn"
    ] + ["upstream"] * 3
    assert facts["path"][-1] == data["landmarks"]["home"]
    # D = (3/4 sea, 1/4 mouth); A(marine|faint) = 9/16 at sea and 3/32 at the mouth.
    assert facts["evidence"] == Fraction(3, 4) * Fraction(9, 16) + Fraction(
        1, 4
    ) * Fraction(3, 32)
    assert facts["evidence"] == Fraction(57, 128)
    assert facts["posterior_sea"] == Fraction(18, 19)


def test_artifact_bound_to_a_different_source_is_rejected(
    tmp_path: Path, generator: ModuleType
) -> None:
    fixtures = _copy_fixtures(tmp_path)
    source = fixtures / "smith_river_homing.gnn.md"
    source.write_text(source.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(generator.FixtureError, match="source digest"):
        generator.load_fixtures(fixtures)


def test_tampered_transition_entry_is_rejected(
    tmp_path: Path, generator: ModuleType
) -> None:
    fixtures = _copy_fixtures(tmp_path)
    path = fixtures / "smith_river_homing.geo-infer.json"
    artifact = json.loads(path.read_text(encoding="utf-8"))
    artifact["matrices"]["B"][2][1][2] = 0.25
    path.write_text(json.dumps(artifact), encoding="utf-8")
    with pytest.raises(generator.FixtureError, match="B"):
        generator.load_fixtures(fixtures)


def test_duplicate_keys_and_non_dyadic_values_are_rejected(
    tmp_path: Path, generator: ModuleType
) -> None:
    duplicate = tmp_path / "dup.json"
    duplicate.write_text('{"a": 1, "a": 2}', encoding="utf-8")
    with pytest.raises(generator.FixtureError, match="duplicate"):
        generator.load_json(duplicate)
    with pytest.raises(generator.FixtureError, match="power of two"):
        generator.exact_table(
            [Decimal("0.3333333333333333"), Decimal("0.6666666666666667")], "X"
        )
    with pytest.raises(generator.FixtureError, match="exceeds"):
        generator.exact_table(
            [Decimal(1) / Decimal(1 << 20), 1 - Decimal(1) / Decimal(1 << 20)], "X"
        )
    with pytest.raises(generator.FixtureError, match="exact JSON decimal"):
        generator.exact_table([0.5, 0.5], "X")


def test_gnn_source_parses_into_the_canonical_q1_sections(
    generator: ModuleType,
) -> None:
    sections = dict(
        generator.parse_gnn(
            (FIXTURES / "smith_river_homing.gnn.md").read_text(encoding="utf-8")
        )
    )
    assert list(sections) == list(generator.SECTION_ORDER)
    declarations = {name: dims for name, dims, _ in sections["StateSpaceBlock"]}
    assert declarations["A"] == [12, 26] and declarations["B"] == [26, 26, 4]
    assert declarations["G"] == ["π"]
    assert ("C", "LogPreferenceVector") in sections["ActInfOntologyAnnotation"]
    assert ("SpaceKind", "h3") in sections["Time"]
    payloads = dict(sections["InitialParameterization"])
    assert set(payloads) == {"A", "B", "C", "D", "E"}
    assert payloads["E"] == "{(0.125, 0.125, 0.5, 0.25)}"


def test_parser_rejects_out_of_order_sections(generator: ModuleType) -> None:
    text = (FIXTURES / "smith_river_homing.gnn.md").read_text(encoding="utf-8")
    swapped = text.replace("## Connections", "## TEMP").replace(
        "## StateSpaceBlock", "## Connections"
    )
    with pytest.raises(generator.FixtureError, match="section order"):
        generator.parse_gnn(swapped.replace("## TEMP", "## StateSpaceBlock"))


def test_every_mutation_applies_exactly_once(verifier: ModuleType) -> None:
    manifest = json.loads(
        (SLICE / "generated" / "manifest.json").read_text(encoding="utf-8")
    )
    instance = (SLICE / "generated" / "SmithRiverHoming.lean").read_text(
        encoding="utf-8"
    )
    mutated = verifier.mutation_texts(instance, manifest)
    assert set(mutated) == set(verifier.MUTATIONS)
    assert all(text != instance for text in mutated.values())


def test_retained_receipt_is_claim_ready_and_current() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(SLICE / "verify_native.py"),
            "--check",
            "--receipt",
            str(RETAINED_RECEIPT),
        ],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
        timeout=120,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    receipt = json.loads(RETAINED_RECEIPT.read_text(encoding="utf-8"))
    assert receipt["verdict"]["claim_ready"] is True
    assert receipt["verdict"]["theorems_reported"] == len(receipt["theorems"])


def test_receipt_check_detects_a_tampered_verdict(
    tmp_path: Path, verifier: ModuleType
) -> None:
    receipt = json.loads(RETAINED_RECEIPT.read_text(encoding="utf-8"))
    receipt["mutations"]["transposed_b_axes"]["exit_code"] = 0
    path = tmp_path / "receipt.json"
    path.write_text(json.dumps(receipt), encoding="utf-8")
    assert verifier.check_receipt(path) == 1


@pytest.mark.serial_lean
def test_native_compile_is_claim_ready_and_rejects_every_mutation(
    tmp_path: Path, verifier: ModuleType
) -> None:
    lake_executable(missing="raise", context="the Cascadia native receipt")
    receipt_path = tmp_path / "native-receipt.json"
    assert verifier.compile_receipt(receipt_path) == 0
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert receipt["verdict"]["claim_ready"] is True
    assert all(receipt["verdict"]["mutations_rejected"].values())
    assert "CascadiaGeo.SmithRiverHoming.homing_lower_bound" in receipt["theorems"]
