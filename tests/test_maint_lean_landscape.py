"""Tests for ``scripts/_maint_build_lean_landscape.py``.

The landscape page is generated from the formal manifest and the real
``import FepSketches.*`` statements in the workspace sources. These tests
exercise the actual generator against the real repository so drift between
the manifest, the Lean sources, and ``docs/lean-landscape.md`` fails fast.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

from fep_formal.formal.manifest import FORMAL_MODULES, FormalModuleRole
from tests._support.lean_module_contract import topic_namespace_owner_modules

PROJ = Path(__file__).resolve().parent.parent
SCRIPT = PROJ / "scripts" / "_maint_build_lean_landscape.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("maint_lean_landscape", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_workspace_imports_preserve_plain_and_public_dependency_order(
    tmp_path: Path,
) -> None:
    source = tmp_path / "imports.lean"
    source.write_text(
        "module\n"
        "import FepSketches.finite_probability\n"
        "public import FepSketches.helmholtz_ao_ness\n"
        "  public\timport\tFepSketches.compositions.core\n"
        "import Mathlib.Tactic\n"
        "public import FepSketches\n"
        "import FepSketchesRelated.other\n",
        encoding="utf-8",
    )
    module = _load_module()
    assert module._workspace_imports(source) == [
        "finite_probability",
        "helmholtz_ao_ness",
        "compositions.core",
    ]


def test_workspace_imports_ignore_nested_comments_and_string_literals(
    tmp_path: Path,
) -> None:
    source = tmp_path / "comments.lean"
    source.write_text(
        "-- import FepSketches.line_comment\n"
        "/- public import FepSketches.block_comment\n"
        "/- nested comment -/\n"
        "public import FepSketches.nested_block_comment\n"
        "-/\n"
        'def importText := "first line\n'
        "public import FepSketches.string_literal\n"
        'escaped quote: \\" still a string\n'
        'import FepSketches.escaped_string_literal\n"\n'
        "/- leading comment -/ public import FepSketches.finite_probability\n"
        "import FepSketches.finite_information -- trailing comment\n",
        encoding="utf-8",
    )
    module = _load_module()
    assert module._workspace_imports(source) == [
        "finite_probability",
        "finite_information",
    ]


def test_layers_are_respected_by_real_imports() -> None:
    module = _load_module()
    layer, deps = module._layers(PROJ)
    topic_owners = topic_namespace_owner_modules(PROJ / "lean/FepSketches/fep_all.lean")
    topic_modules = {
        value.removeprefix("FepSketches.") for value in topic_owners.values()
    }
    assert set(layer) == {
        m.lean_module.removeprefix("FepSketches.") for m in FORMAL_MODULES
    }
    assert "helmholtz_ao_ness" in deps["law_weighted_split"]
    assert layer["helmholtz_ao_ness"] < layer["law_weighted_split"]
    assert any(deps.values())
    assert max(layer.values()) > 0
    for name, dep_names in deps.items():
        assert name in layer
        if name.startswith("compositions."):
            assert "fep_all" not in dep_names
        for dep in dep_names:
            if dep not in layer:
                # Only actual generated topic owners may sit outside the formal manifest.
                assert dep in topic_modules, (name, dep)
                continue
            assert layer[dep] < layer[name], (name, dep)


@pytest.mark.parametrize(
    ("information_import", "probability_import", "cycle"),
    (
        (
            "import FepSketches.finite_probability\n",
            "public import FepSketches.finite_information\n",
            "finite_information -> finite_probability -> finite_information",
        ),
        (
            "",
            "public import FepSketches.finite_probability\n",
            "finite_probability -> finite_probability",
        ),
    ),
)
def test_layers_reject_import_cycles_instead_of_publishing_false_layers(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    information_import: str,
    probability_import: str,
    cycle: str,
) -> None:
    module = _load_module()
    selected = tuple(
        owner
        for owner in FORMAL_MODULES
        if owner.resource in {"finite_probability.lean", "finite_information.lean"}
    )
    assert len(selected) == 2
    monkeypatch.setattr(module, "FORMAL_MODULES", selected)
    workspace = tmp_path / "lean" / "FepSketches"
    workspace.mkdir(parents=True)
    (workspace / "finite_information.lean").write_text(
        information_import, encoding="utf-8"
    )
    (workspace / "finite_probability.lean").write_text(
        probability_import, encoding="utf-8"
    )

    with pytest.raises(ValueError, match="cyclic formal Lean imports") as error:
        module._layers(tmp_path)
    assert str(error.value) == f"cyclic formal Lean imports: {cycle}"


def test_every_manifest_module_appears_in_rendered_page() -> None:
    module = _load_module()
    rendered = module.render_landscape(PROJ)
    for m in FORMAL_MODULES:
        name = m.lean_module.removeprefix("FepSketches.")
        assert f"`{name}`" in rendered
    assert "Total maintained formal modules:" in rendered
    foundation_rows = rendered.count("| foundation |")
    composition_rows = rendered.count("| composition |")
    assert foundation_rows > 0 and composition_rows > 0


def test_generated_page_is_current() -> None:
    page = PROJ / "docs" / "lean-landscape.md"
    assert page.exists(), "docs/lean-landscape.md must be tracked and current"
    module = _load_module()
    assert page.read_text(encoding="utf-8") == module.render_landscape(PROJ)


def test_check_gate_subprocess_exit_codes() -> None:
    ok = subprocess.run(
        [sys.executable, str(SCRIPT), "--check"],
        cwd=PROJ,
        capture_output=True,
        text=True,
        check=False,
    )
    assert ok.returncode == 0, ok.stdout + ok.stderr


def test_aggregate_and_topic_rows_are_annotated() -> None:
    module = _load_module()
    rendered = module.render_landscape(PROJ)
    assert "| aggregate |" in rendered
    assert FormalModuleRole.AGGREGATE.value in rendered
