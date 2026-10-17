"""Exercise the public, slice-owned multi-repository workspace controls."""

import importlib.util
from pathlib import Path

_SOURCE = Path(__file__).resolve().parents[1] / "specs/lean-workspace/test_workspace.py"
_SPEC = importlib.util.spec_from_file_location("lean_workspace_controls", _SOURCE)
assert _SPEC is not None and _SPEC.loader is not None
_CONTROLS = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_CONTROLS)


class TestLeanWorkspace(_CONTROLS.WorkspaceTests):
    """Run the same real filesystem/Git controls in the normal suite."""
