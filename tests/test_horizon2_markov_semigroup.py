"""H2.4 exact embedding and native semigroup contracts."""

from __future__ import annotations

import re
import tempfile
from pathlib import Path

import pytest

from fep_lean.formal.manifest import FORMAL_MODULES, FormalModuleRole
from fep_lean.formal.projection import formal_projection_drift
from fep_lean.lean_source import lean_code_without_comments
from tests._support.lake import lake_executable
from tests._support.lean_runner import run_lean_compile_probe

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LEAN_ROOT = PROJECT_ROOT / "lean"
FOUNDATION = PROJECT_ROOT / "src" / "fep_lean" / "formal" / "native_blanket.lean"
PROJECTION = LEAN_ROOT / "FepSketches" / "native_blanket.lean"
SEMIGROUP_FOUNDATION = (
    PROJECT_ROOT / "src" / "fep_lean" / "formal" / "markov_semigroup.lean"
)
SEMIGROUP_PROJECTION = LEAN_ROOT / "FepSketches" / "markov_semigroup.lean"

pytestmark = pytest.mark.serial_lean

EXACT_IMPORTS = (
    "FepSketches.markov_blanket",
    "Mathlib.MeasureTheory.Integral.Bochner.SumMeasure",
    "Mathlib.Probability.Independence.Conditional",
    "Mathlib.Probability.Kernel.Composition.Comp",
)
NEW_THEOREMS = (
    "embeddedKernel_identity",
    "embeddedKernel_comp",
)
SEMIGROUP_IMPORTS = (
    "FepSketches.continuous_time_markov",
    "FepSketches.native_blanket",
    "Mathlib.InformationTheory.KullbackLeibler.DataProcessing",
    "Mathlib.Probability.Kernel.Invariance",
)
SEMIGROUP_DEFINITIONS = (
    "embeddedFiniteKernelFamily",
    "liftFiniteMarkovSemigroup",
    "InvariantLaw",
    "ReversibleLaw",
    "embeddedActionKernelFamily",
    "liftActionIndexedSemigroup",
    "sampledKernel",
    "boolBlanketNativeActionIndexedSemigroup",
)
SEMIGROUP_THEOREMS = (
    "reversibleLaw_invariantLaw",
    "nativeKL_nonincrease",
    "nativeKL_to_invariant_nonincrease",
    "liftFiniteMarkovSemigroup_kernel",
    "liftActionIndexedSemigroup_kernel",
    "liftActionIndexedSemigroup_sampleTime",
    "liftActionIndexedSemigroup_sampledKernel",
    "boolBlanketNativeActionIndexedSemigroup_false_kernel",
    "boolBlanketNativeActionIndexedSemigroup_true_kernel",
    "boolBlanketNativeActionIndexedSemigroup_kernels_ne",
)


def test_h2_4a_extends_the_single_existing_embedding_owner() -> None:
    source = FOUNDATION.read_text(encoding="utf-8")
    owners = [module for module in FORMAL_MODULES if module.resource == FOUNDATION.name]

    assert len(owners) == 1
    owner = owners[0]
    assert owner.lean_module == "FepSketches.native_blanket"
    assert owner.role is FormalModuleRole.FOUNDATION
    assert owner.declaration_namespace == "FEP.NativeBlanket"
    assert tuple(re.findall(r"(?m)^import (\S+)$", source)) == EXACT_IMPORTS


def test_h2_4a_preserves_identity_and_chronological_composition_exactly() -> None:
    source = lean_code_without_comments(FOUNDATION.read_text(encoding="utf-8"))

    assert re.search(r"(?m)^theorem embeddedKernel_identity\b", source)
    assert re.search(r"(?m)^theorem embeddedKernel_comp\b", source)
    assert (
        "embeddedKernel (FiniteKernel.identity : FiniteKernel α α) = Kernel.id"
        in source
    )
    assert "embeddedKernel (FiniteKernel.comp later earlier)" in source
    assert "embeddedKernel later ∘ₖ embeddedKernel earlier" in source
    assert source.index("FiniteKernel.comp later earlier") < source.index(
        "embeddedKernel later ∘ₖ embeddedKernel earlier"
    )


def test_h2_4a_reuses_the_embedding_and_existing_predictive_bridge() -> None:
    source = lean_code_without_comments(FOUNDATION.read_text(encoding="utf-8"))

    assert len(re.findall(r"(?m)^noncomputable def embeddedLaw\b", source)) == 1
    assert len(re.findall(r"(?m)^noncomputable def embeddedKernel\b", source)) == 1
    assert len(re.findall(r"(?m)^theorem embeddedPredictive_eq_comp\b", source)) == 1
    assert not re.search(r"(?m)^structure .*Embedding", source)
    assert not re.search(r"(?m)^class .*Embedding", source)
    assert not re.search(
        r"\b(?:sorry|admit|axiom|opaque)\b|unsafe\s+(?:def|theorem)|:\s*True\b",
        source,
    )


def test_h2_4a_projection_is_current() -> None:
    assert PROJECTION.read_bytes() == FOUNDATION.read_bytes()
    assert formal_projection_drift(PROJECT_ROOT) == ()


def test_h2_4a_native_owner_compiles_warning_free() -> None:
    with tempfile.TemporaryDirectory(prefix="fep-h2-4a-") as output_dir:
        output_path = Path(output_dir) / "native_blanket.olean"
        result = run_lean_compile_probe(
            FOUNDATION,
            cwd=LEAN_ROOT,
            import_root=PROJECT_ROOT / "src" / "fep_lean" / "formal",
            output_path=output_path,
            timeout_s=300,
            executable=lake_executable(
                missing="raise",
                context="H2.4a native acceptance",
            ),
        )
        assert output_path.is_file(), result.stdout + result.stderr

    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "warning:" not in output.lower()


def test_h2_4a_embedding_theorems_use_standard_axioms_and_fix_orientation(
    tmp_path: Path,
) -> None:
    probe = tmp_path / "EmbeddedKernelFunctoriality.lean"
    source = FOUNDATION.read_text(encoding="utf-8")
    prints = "\n".join(
        f"#print axioms FEP.NativeBlanket.{name}" for name in NEW_THEOREMS
    )
    orientation = """
open MeasureTheory ProbabilityTheory
open scoped ENNReal MeasureTheory ProbabilityTheory

private def earlierNot : FEP.FiniteKernel Bool Bool :=
  FEP.FiniteKernel.deterministic not

private def laterTrue : FEP.FiniteKernel Bool Bool :=
  FEP.FiniteKernel.deterministic (fun _ => true)

example :
    FEP.NativeBlanket.embeddedKernel
        (FEP.FiniteKernel.comp laterTrue earlierNot) =
      FEP.NativeBlanket.embeddedKernel laterTrue ∘ₖ
        FEP.NativeBlanket.embeddedKernel earlierNot :=
  FEP.NativeBlanket.embeddedKernel_comp laterTrue earlierNot

example :
    FEP.NativeBlanket.embeddedKernel
        (FEP.FiniteKernel.comp laterTrue earlierNot) false {true} = 1 := by
  rw [FEP.NativeBlanket.embeddedKernel_apply_singleton]
  simp [FEP.FiniteKernel.comp, earlierNot, laterTrue,
    FEP.FiniteKernel.deterministic]

example :
    FEP.NativeBlanket.embeddedKernel
        (FEP.FiniteKernel.comp earlierNot laterTrue) false {true} = 0 := by
  rw [FEP.NativeBlanket.embeddedKernel_apply_singleton]
  simp [FEP.FiniteKernel.comp, earlierNot, laterTrue,
    FEP.FiniteKernel.deterministic]
"""
    probe.write_text(f"{source}\n{prints}\n{orientation}\n", encoding="utf-8")
    result = run_lean_compile_probe(
        probe,
        cwd=LEAN_ROOT,
        import_root=PROJECT_ROOT / "src" / "fep_lean" / "formal",
        timeout_s=300,
        executable=lake_executable(
            missing="raise",
            context="H2.4a native acceptance",
        ),
    )

    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "sorryAx" not in output
    assert "warning:" not in output.lower()
    axiom_blocks = re.findall(r"depends on axioms: \[(.*?)\]", output, re.DOTALL)
    assert len(axiom_blocks) == len(NEW_THEOREMS), output
    for block in axiom_blocks:
        axioms = set(re.findall(r"'([^']+)'", block))
        assert axioms <= {"propext", "Classical.choice", "Quot.sound"}


def test_h2_4b_has_one_exact_foundation_owner() -> None:
    assert SEMIGROUP_FOUNDATION.is_file()
    source = SEMIGROUP_FOUNDATION.read_text(encoding="utf-8")
    owners = [
        module
        for module in FORMAL_MODULES
        if module.resource == SEMIGROUP_FOUNDATION.name
    ]

    assert len(owners) == 1
    owner = owners[0]
    assert owner.lean_module == "FepSketches.markov_semigroup"
    assert owner.role is FormalModuleRole.FOUNDATION
    assert owner.declaration_namespace == "FEP.MarkovSemigroup"
    assert tuple(re.findall(r"(?m)^import (\S+)$", source)) == SEMIGROUP_IMPORTS
    assert "namespace FEP.MarkovSemigroup\n" in source
    assert source.rstrip().endswith("end FEP.MarkovSemigroup")


def test_h2_4b_interface_stores_only_semigroup_laws() -> None:
    source = lean_code_without_comments(
        SEMIGROUP_FOUNDATION.read_text(encoding="utf-8")
    )

    native_match = re.search(
        r"structure NativeKernelSemigroup.*?where\n(?P<body>.*?)(?=\n(?:namespace|/--))",
        source,
        re.DOTALL,
    )
    assert native_match is not None
    assert tuple(re.findall(r"(?m)^  (\w+)\s*:", native_match["body"])) == (
        "kernel_zero",
        "kernel_add",
    )
    assert "kernel (left + right) = kernel right ∘ₖ kernel left" in source
    assert (
        tuple(re.findall(r"(?m)^(?:noncomputable )?def (\w+)\b", source))
        == SEMIGROUP_DEFINITIONS
    )
    assert tuple(re.findall(r"(?m)^theorem (\w+)\b", source)) == (SEMIGROUP_THEOREMS)
    assert not re.search(
        r"\b(?:generator|SDE|Ito|FokkerPlanck|parallelActionTransition)\b", source
    )
    assert not re.search(
        r"\b(?:sorry|admit|axiom|opaque)\b|unsafe\s+(?:def|theorem)|:\s*True\b",
        source,
    )


def test_h2_4b_lift_preserves_exact_action_time_and_carrier() -> None:
    source = lean_code_without_comments(
        SEMIGROUP_FOUNDATION.read_text(encoding="utf-8")
    )

    assert "FEP.ContinuousTimeMarkov.FiniteMarkovSemigroup" in source
    assert "FEP.ContinuousTimeMarkov.ActionIndexedSemigroup" in source
    assert "FEP.NativeBlanket.embeddedKernel" in source
    assert "time.1" in source
    assert "time.2" in source
    assert "indexed.sampleTime action" in source
    assert "indexed.sampleTime_nonneg action" in source
    assert "FEP.ContinuousTimeMarkov.BoolBlanketState" in source
    assert "boolBlanketActionIndexedSemigroup" in source
    assert "boolBlanketRefreshKernel" in source
    assert "Kernel.id" in source
    assert "kernel (earlier + increment) ∘ₘ actual" in source
    assert "kernel earlier ∘ₘ actual" in source
    assert "semigroup.kernel_add earlier increment" in source
    assert "InformationTheory.klDiv_comp_right_le" in source
    assert "threeCycleGenerator" not in source
    assert "threeCycleStationaryLaw" not in source


def test_h2_4b_projection_is_current() -> None:
    assert SEMIGROUP_PROJECTION.read_bytes() == SEMIGROUP_FOUNDATION.read_bytes()
    assert formal_projection_drift(PROJECT_ROOT) == ()


def test_h2_4b_foundation_compiles_warning_free() -> None:
    with tempfile.TemporaryDirectory(prefix="fep-h2-4b-") as output_dir:
        output_path = Path(output_dir) / "markov_semigroup.olean"
        result = run_lean_compile_probe(
            SEMIGROUP_FOUNDATION,
            cwd=LEAN_ROOT,
            import_root=PROJECT_ROOT / "src" / "fep_lean" / "formal",
            output_path=output_path,
            timeout_s=300,
            executable=lake_executable(
                missing="raise",
                context="H2.4a native acceptance",
            ),
        )
        assert output_path.is_file(), result.stdout + result.stderr

    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "warning:" not in output.lower()


def test_h2_4b_bridge_and_dissipation_use_standard_axioms(tmp_path: Path) -> None:
    source = SEMIGROUP_FOUNDATION.read_text(encoding="utf-8")
    prints = "\n".join(
        f"#print axioms FEP.MarkovSemigroup.{name}" for name in SEMIGROUP_THEOREMS
    )
    contracts = r"""
open MeasureTheory ProbabilityTheory
open scoped ENNReal MeasureTheory NNReal ProbabilityTheory

example (action : Bool) :
    FEP.MarkovSemigroup.sampledKernel
        FEP.MarkovSemigroup.boolBlanketNativeActionIndexedSemigroup action =
      FEP.NativeBlanket.embeddedKernel
        (FEP.ContinuousTimeMarkov.boolBlanketActionIndexedSemigroup.sampledKernel
          action) :=
  FEP.MarkovSemigroup.liftActionIndexedSemigroup_sampledKernel
    FEP.ContinuousTimeMarkov.boolBlanketActionIndexedSemigroup action

example :
    FEP.MarkovSemigroup.sampledKernel
        FEP.MarkovSemigroup.boolBlanketNativeActionIndexedSemigroup false =
      Kernel.id :=
  FEP.MarkovSemigroup.boolBlanketNativeActionIndexedSemigroup_false_kernel

example :
    FEP.MarkovSemigroup.sampledKernel
        FEP.MarkovSemigroup.boolBlanketNativeActionIndexedSemigroup true =
      FEP.NativeBlanket.embeddedKernel
        FEP.ContinuousTimeMarkov.boolBlanketRefreshKernel :=
  FEP.MarkovSemigroup.boolBlanketNativeActionIndexedSemigroup_true_kernel

example :
    FEP.MarkovSemigroup.sampledKernel
        FEP.MarkovSemigroup.boolBlanketNativeActionIndexedSemigroup false ≠
      FEP.MarkovSemigroup.sampledKernel
        FEP.MarkovSemigroup.boolBlanketNativeActionIndexedSemigroup true :=
  FEP.MarkovSemigroup.boolBlanketNativeActionIndexedSemigroup_kernels_ne

example (earlier increment : ℝ≥0)
    (actual reference : FEP.FiniteLaw
      FEP.ContinuousTimeMarkov.BoolBlanketState) :
    InformationTheory.klDiv
        (FEP.MarkovSemigroup.embeddedActionKernelFamily
          FEP.ContinuousTimeMarkov.boolBlanketActionIndexedSemigroup true
          (earlier + increment) ∘ₘ FEP.NativeBlanket.embeddedLaw actual)
        (FEP.MarkovSemigroup.embeddedActionKernelFamily
          FEP.ContinuousTimeMarkov.boolBlanketActionIndexedSemigroup true
          (earlier + increment) ∘ₘ FEP.NativeBlanket.embeddedLaw reference) ≤
      InformationTheory.klDiv
        (FEP.MarkovSemigroup.embeddedActionKernelFamily
          FEP.ContinuousTimeMarkov.boolBlanketActionIndexedSemigroup true
          earlier ∘ₘ FEP.NativeBlanket.embeddedLaw actual)
        (FEP.MarkovSemigroup.embeddedActionKernelFamily
          FEP.ContinuousTimeMarkov.boolBlanketActionIndexedSemigroup true
          earlier ∘ₘ FEP.NativeBlanket.embeddedLaw reference) :=
  FEP.MarkovSemigroup.nativeKL_nonincrease
    (FEP.MarkovSemigroup.boolBlanketNativeActionIndexedSemigroup.semigroup true)
    earlier increment (FEP.NativeBlanket.embeddedLaw actual)
    (FEP.NativeBlanket.embeddedLaw reference)
"""
    probe = tmp_path / "NativeMarkovSemigroup.lean"
    probe.write_text(f"{source}\n{prints}\n{contracts}\n", encoding="utf-8")
    result = run_lean_compile_probe(
        probe,
        cwd=LEAN_ROOT,
        import_root=PROJECT_ROOT / "src" / "fep_lean" / "formal",
        timeout_s=300,
        executable=lake_executable(
            missing="raise",
            context="H2.4a native acceptance",
        ),
    )

    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "sorryAx" not in output
    assert "warning:" not in output.lower()
    axiom_blocks = re.findall(r"depends on axioms: \[(.*?)\]", output, re.DOTALL)
    assert len(axiom_blocks) == len(SEMIGROUP_THEOREMS), output
    for block in axiom_blocks:
        axioms = set(re.findall(r"'([^']+)'", block))
        assert axioms <= {"propext", "Classical.choice", "Quot.sound"}
