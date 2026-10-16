"""Tests for ``scripts/_maint_build_fep_all_lean.py``.

The body registry is the source of truth for tracked ``lean/FepSketches/fep_all.lean``.
These tests guard the same invariants that
:mod:`tests.test_fep_all_lean_ssot` enforces on the materialized file, so a
body-registry edit that breaks the SSOT contract fails fast in unit tests rather
than only at the project-wide ``test_fep_all_lean_*`` gate.
"""

from __future__ import annotations

import importlib
import importlib.util
import re
import sys
from pathlib import Path

import pytest
import yaml

from fep_lean.catalogue.generation import (
    hoisted_sketch_imports,
    render_fep_all_lean,
    topic_id_to_namespace,
)
from fep_lean.catalogue.registry import BODIES

PROJ = Path(__file__).resolve().parent.parent
SCRIPTS = PROJ / "scripts"
TOPICS_YAML = PROJ / "config" / "topics.yaml"

_NS_RE = re.compile(r"^namespace fep_fep(\d+)", re.MULTILINE)


@pytest.fixture(scope="module")
def generator_module():
    """Import the generator module by file path so tests stay decoupled from
    package layout (``scripts/`` is not a package)."""
    spec = importlib.util.spec_from_file_location(
        "_maint_build_fep_all_lean",
        SCRIPTS / "_maint_build_fep_all_lean.py",
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _yaml_topic_ids() -> set[str]:
    data = yaml.safe_load(TOPICS_YAML.read_text(encoding="utf-8"))
    return {t["id"] for t in data["topics"]}


def test_write_aggregate_emits_the_sealed_topic_namespaces(
    tmp_path: Path, generator_module
) -> None:
    fep_all_path, n = generator_module.write_aggregate(out_dir=tmp_path)
    expected_count = len(_yaml_topic_ids())
    assert n == expected_count
    assert fep_all_path.is_file()

    text = fep_all_path.read_text(encoding="utf-8")
    namespaces = {f"fep-{m.group(1)}" for m in _NS_RE.finditer(text)}
    assert len(namespaces) == expected_count, (
        f"expected {expected_count} fep_fepNNN namespaces, got {len(namespaces)}: "
        f"{sorted(namespaces)}"
    )


def test_write_aggregate_covers_every_yaml_topic(
    tmp_path: Path, generator_module
) -> None:
    fep_all_path, _ = generator_module.write_aggregate(out_dir=tmp_path)
    text = fep_all_path.read_text(encoding="utf-8")
    lean_ids = {f"fep-{m.group(1)}" for m in _NS_RE.finditer(text)}
    yaml_ids = _yaml_topic_ids()

    missing_from_lean = yaml_ids - lean_ids
    extra_in_lean = lean_ids - yaml_ids
    assert not missing_from_lean, (
        f"in topics.yaml but not in regenerated fep_all.lean: {sorted(missing_from_lean)}"
    )
    assert not extra_in_lean, (
        f"in regenerated fep_all.lean but not in topics.yaml: {sorted(extra_in_lean)}"
    )


def test_write_aggregate_no_non_comment_sorry(tmp_path: Path, generator_module) -> None:
    fep_all_path, _ = generator_module.write_aggregate(out_dir=tmp_path)
    text = fep_all_path.read_text(encoding="utf-8")
    offending: list[str] = []
    for i, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith("--"):
            continue
        if re.search(r"\bsorry\b", line):
            offending.append(f"line {i}: {line.rstrip()}")
    assert not offending, (
        "non-comment sorry leaked into generated fep_all.lean:\n" + "\n".join(offending)
    )


def test_write_aggregate_hoists_exact_distinct_import_union(
    tmp_path: Path, generator_module
) -> None:
    """The aggregate preserves the canonical narrow dependency surface."""
    fep_all_path, _ = generator_module.write_aggregate(out_dir=tmp_path)
    text = fep_all_path.read_text(encoding="utf-8")
    import_lines = [
        ln.removeprefix("public ")
        for ln in text.splitlines()
        if ln.startswith(("public import ", "public meta import "))
    ]
    assert import_lines == list(hoisted_sketch_imports(BODIES))
    assert len(import_lines) == len(set(import_lines))
    assert "import Mathlib" not in import_lines
    assert "import Mathlib.Tactic" not in import_lines
    assert "meta import Lean.Meta.Tactic.NormCast" in import_lines
    assert "meta import Lean.Elab.Tactic.Omega" in import_lines
    assert "import Mathlib.Probability.Kernel.Invariance" in import_lines
    assert "import Mathlib.Analysis.SpecialFunctions.BinaryEntropy" in import_lines


def test_regenerated_aggregate_is_the_only_library_target(
    tmp_path: Path, generator_module
) -> None:
    """The generator emits one canonical aggregate and no companion library."""
    path, _ = generator_module.write_aggregate(out_dir=tmp_path)
    assert path.name == "fep_all.lean"
    assert not (tmp_path / "Basic.lean").exists()


def test_topic_id_to_namespace_round_trips() -> None:
    assert topic_id_to_namespace("fep-001") == "fep_fep001"
    assert topic_id_to_namespace("fep-050") == "fep_fep050"
    with pytest.raises(ValueError):
        topic_id_to_namespace("not-a-topic")
    with pytest.raises(ValueError):
        topic_id_to_namespace("fep-xyz")


def test_build_aggregate_rejects_empty_body_registry() -> None:
    with pytest.raises(ValueError, match="body registry is empty"):
        render_fep_all_lean({})


def test_aggregate_is_current_detects_drift(tmp_path: Path, generator_module) -> None:
    path, _ = generator_module.write_aggregate(out_dir=tmp_path)
    assert generator_module.aggregate_is_current(path)
    path.write_text(path.read_text(encoding="utf-8") + "-- drift\n", encoding="utf-8")
    assert not generator_module.aggregate_is_current(path)
