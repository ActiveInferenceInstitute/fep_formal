"""Finite-law to native conditional-independence boundary tests."""

from __future__ import annotations

import re
import runpy
import subprocess
from pathlib import Path

import pytest

from fep_lean.verification import formalism_audit
from fep_lean.lean_source import lean_code_without_comments
from tests._support.lake import lake_executable
from tests._support.lean_runner import run_lean_compile_probe

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LEAN_ROOT = PROJECT_ROOT / "lean"
FORMAL_ROOT = PROJECT_ROOT / "src" / "fep_lean" / "formal"
BODIES_ROOT = PROJECT_ROOT / "src" / "fep_lean" / "catalogue" / "bodies"
FOUNDATION = FORMAL_ROOT / "native_blanket.lean"
COMPOSITION = FORMAL_ROOT / "compositions" / "native_blanket_transfer.lean"
BODY_MODULE = BODIES_ROOT / "native_blanket_independence.py"
AXIOM_PROBE = (
    PROJECT_ROOT
    / "specs"
    / "done"
    / "formalism-catalogue-155"
    / "spikes"
    / "native_blanket.lean"
)

pytestmark = pytest.mark.serial_lean

FORBIDDEN_FORMAL_TOKENS = (
    "sorry",
    "admit",
    "axiom ",
    "opaque ",
    ": True",
    "unsafe def",
    "unsafe theorem",
)

AXIOM_DECLARATIONS = (
    "FEP.NativeBlanket.staticJoint_condIndepFun",
    "FEP.NativeBlanket.correlatedBlanket_nonvacuous",
    "fep_fep139.FEP139.fep139_staticJoint_condIndepFun",
    "fep_fep139.FEP139.fep139_correlatedBlanket_nonvacuous",
    "FEPComposed.fep135_embeddedLaw_extends_fep017",
    "FEPComposed.fep136_embeddedExpectation_extends_fep015",
    "FEPComposed.fep137_embeddedPredictive_extends_fep019",
    "FEPComposed.fep138_rectangleFactorization_extends_fep079",
    "FEPComposed.fep139_nativeCondIndep_connects_fep009_fep079",
    "FEPComposed.fep140_measurableCoarsening_extends_fep009",
    "FEPComposed.fep141_blanketTransition_extends_fep080",
)
ALLOWED_AXIOMS = frozenset({"Classical.choice", "Quot.sound", "propext"})


def _compile(source: Path) -> subprocess.CompletedProcess[str]:
    return run_lean_compile_probe(
        source,
        cwd=LEAN_ROOT,
        timeout_s=300,
        executable=lake_executable(),
    )


def _bodies() -> dict[str, str]:
    namespace = runpy.run_path(BODY_MODULE)
    return namespace["BODIES"]




def _declaration(source: str, name: str) -> str:
    uncommented = lean_code_without_comments(source)
    match = re.search(
        rf"(?:theorem|lemma|def|noncomputable def)\s+{re.escape(name)}\b"
        rf"(?P<body>.*?)(?=\n(?:theorem|lemma|def|noncomputable def|end)\b|\Z)",
        uncommented,
        flags=re.DOTALL,
    )
    assert match is not None, f"missing declaration {name}"
    return match.group(0)


def test_native_blanket_foundation_pins_the_measure_transfer_surface() -> None:
    source = FOUNDATION.read_text(encoding="utf-8")

    expected = (
        "embeddedLaw",
        "embeddedLaw_apply_singleton",
        "embeddedLaw_apply_univ",
        "embeddedLaw_injective",
        "embeddedLaw_integral_eq_sum",
        "embeddedKernel",
        "embeddedPredictive_eq_comp",
        "blanketCoordinate",
        "internalCoordinate",
        "externalCoordinate",
        "staticJoint_rectangle_factorization",
        "staticJoint_condIndepFun",
        "condIndepFun_measurableImages",
        "prediction_preserves_nativeBlanket",
        "correlatedBlanketModel",
        "correlatedBlanket_nonvacuous",
    )
    for name in expected:
        assert re.search(rf"\b{name}\b", source), name

    lowered = source.lower()
    for token in FORBIDDEN_FORMAL_TOKENS:
        assert token.lower() not in lowered


def test_native_stop_go_declaration_is_mathlib_cond_independence() -> None:
    source = FOUNDATION.read_text(encoding="utf-8")
    declaration = _declaration(source, "staticJoint_condIndepFun")

    assert "CondIndepFun" in declaration
    assert "blanketCoordinate" in declaration
    assert "internalCoordinate" in declaration
    assert "externalCoordinate" in declaration
    assert "embeddedLaw (staticJoint model)" in declaration
    assert "mutualInformation" not in declaration
    assert "conditionalMutualInformation" not in declaration


def test_rectangle_factorization_is_declaration_evidence_not_comment_only() -> None:
    source = FOUNDATION.read_text(encoding="utf-8")
    declaration = _declaration(source, "staticJoint_rectangle_factorization")

    assert "embeddedLaw (staticJoint model)" in declaration
    assert "blanketCoordinate" in declaration
    assert "internalCoordinate" in declaration
    assert "externalCoordinate" in declaration
    assert "model.blanketLaw" in declaration
    assert "model.internalGiven" in declaration
    assert "model.externalGiven" in declaration


def test_native_blanket_family_owns_seven_ordered_standalone_bodies() -> None:
    bodies = _bodies()

    assert tuple(bodies) == tuple(f"fep-{number:03d}" for number in range(135, 142))
    for number, body in zip(range(135, 142), bodies.values(), strict=True):
        assert body.startswith("import FepSketches.native_blanket\n")
        assert f"namespace FEP{number:03d}\n" in body
        assert f"end FEP{number:03d}\n" in body
        assert f"theorem fep{number:03d}_" in body
        lowered = body.lower()
        for token in FORBIDDEN_FORMAL_TOKENS:
            assert token.lower() not in lowered


def test_fep139_body_exposes_native_predicate_and_coordinates() -> None:
    declaration = _declaration(_bodies()["fep-139"], "fep139_staticJoint_condIndepFun")

    assert "CondIndepFun" in declaration
    assert "FEP.NativeBlanket.blanketCoordinate" in declaration
    assert "FEP.NativeBlanket.internalCoordinate" in declaration
    assert "FEP.NativeBlanket.externalCoordinate" in declaration
    assert "mutualInformation" not in declaration
    assert "conditionalMutualInformation" not in declaration

    witness = _declaration(_bodies()["fep-139"], "fep139_correlatedBlanket_nonvacuous")
    assert "CondIndepFun" in witness
    assert "correlatedBlanketModel" in witness
    assert witness.count("= 1 / 2") == 2
    assert "≠ 1 / 2" in witness
    assert "correlatedBlanket_nonvacuous" in witness


def test_fep140_body_uses_mathlib_measurable_composition_law() -> None:
    declaration = _declaration(
        _bodies()["fep-140"], "fep140_condIndepFun_measurableImages"
    )

    assert "CondIndepFun" in declaration
    assert ".comp" in declaration
    assert "Measurable" in declaration


def test_correlated_blanket_example_is_nonvacuous_declaration_evidence() -> None:
    source = FOUNDATION.read_text(encoding="utf-8")
    declaration = _declaration(source, "correlatedBlanket_nonvacuous")

    assert "correlatedBlanketModel" in declaration
    assert "CondIndepFun" in declaration
    assert "≠" in declaration
    assert "True" not in declaration


def test_native_blanket_composition_pins_exact_endpoint_pairings() -> None:
    source = COMPOSITION.read_text(encoding="utf-8")
    expected = {
        "fep135_embeddedLaw_extends_fep017": ("fep_fep135.FEP135", "fep_fep017.FEP017"),
        "fep136_embeddedExpectation_extends_fep015": (
            "fep_fep136.FEP136",
            "fep_fep015.FEP015",
        ),
        "fep137_embeddedPredictive_extends_fep019": (
            "fep_fep137.FEP137",
            "fep_fep019.FEP019",
        ),
        "fep138_rectangleFactorization_extends_fep079": (
            "fep_fep138.FEP138",
            "fep_fep079.FEP079",
        ),
        "fep139_nativeCondIndep_connects_fep009_fep079": (
            "fep_fep139.FEP139",
            "fep_fep009.FEP009",
        ),
        "fep140_measurableCoarsening_extends_fep009": (
            "fep_fep140.FEP140",
            "fep_fep009.FEP009",
        ),
        "fep141_blanketTransition_extends_fep080": (
            "fep_fep141.FEP141",
            "fep_fep080.FEP080",
        ),
    }

    assert tuple(
        re.findall(r"^theorem\s+(fep\w+)", source, flags=re.MULTILINE)
    ) == tuple(expected)
    for name, endpoints in expected.items():
        declaration = _declaration(source, name)
        statement, proof = declaration.split(":= by", maxsplit=1)
        assert "∧" in statement, name
        assert endpoints[0] in proof, name
        assert endpoints[1] in proof, name

    stop_go = _declaration(source, "fep139_nativeCondIndep_connects_fep009_fep079")
    assert "CondIndepFun" in stop_go.split(":= by", maxsplit=1)[0]

    lowered = source.lower()
    for token in FORBIDDEN_FORMAL_TOKENS:
        assert token.lower() not in lowered


def test_native_blanket_probe_pins_condindep_and_composition_axioms() -> None:
    source = AXIOM_PROBE.read_text(encoding="utf-8")

    assert source.startswith(
        "import FepSketches.compositions.native_blanket_transfer\n"
    )
    assert (
        tuple(re.findall(r"(?m)^#print axioms ([A-Za-z0-9_.']+)$", source))
        == AXIOM_DECLARATIONS
    )
    assert not re.search(r"\b(?:sorry|admit|axiom|opaque)\b|:\s*True\b", source)


def test_native_blanket_foundation_compiles_warning_free() -> None:
    result = _compile(FOUNDATION)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "warning:" not in (result.stdout + result.stderr).lower()


def test_native_blanket_family_closure_compiles_warning_free(tmp_path: Path) -> None:
    import_line = "import FepSketches.native_blanket\n"
    combined = tmp_path / "native_blanket_independence.lean"
    combined.write_text(
        FOUNDATION.read_text(encoding="utf-8")
        + "\n"
        + "\n".join(body.removeprefix(import_line) for body in _bodies().values()),
        encoding="utf-8",
    )

    result = _compile(combined)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "warning:" not in (result.stdout + result.stderr).lower()


def test_native_blanket_axiom_probe_uses_only_trusted_axioms() -> None:
    result = _compile(AXIOM_PROBE)
    output = result.stdout + result.stderr

    assert result.returncode == 0, output
    assert "warning:" not in output.lower()
    parsed, errors = formalism_audit._parse_axiom_output(
        output,
        expected=AXIOM_DECLARATIONS,
    )
    assert errors == ()
    assert tuple(parsed) == AXIOM_DECLARATIONS
    for declaration, axioms in parsed.items():
        assert set(axioms) <= ALLOWED_AXIOMS, (declaration, axioms)
