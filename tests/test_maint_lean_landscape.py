"""Tests for ``scripts/_maint_build_lean_landscape.py``.

The landscape page is generated from the formal manifest and the real
``import FepSketches.*`` statements in the workspace sources. These tests
exercise the actual generator against the real repository so drift between
the manifest, the Lean sources, and ``docs/generated/lean-landscape.md`` fails fast.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

from fep_lean.formal.manifest import FORMAL_MODULES, FormalModuleRole

PROJ = Path(__file__).resolve().parent.parent
SCRIPT = PROJ / "scripts" / "_maint_build_lean_landscape.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("maint_lean_landscape", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_layers_are_respected_by_real_imports() -> None:
    module = _load_module()
    layer, deps = module._layers(PROJ)
    assert set(layer) == {
        m.lean_module.removeprefix("FepSketches.") for m in FORMAL_MODULES
    }
    for name, dep_names in deps.items():
        assert name in layer
        for dep in dep_names:
            if dep not in layer:
                # Generated aggregates (fep_all) are not manifested modules.
                assert dep == "fep_all", (name, dep)
                continue
            assert layer[dep] < layer[name], (name, dep)


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
    assert page.exists(), "docs/generated/lean-landscape.md must be tracked and current"
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
