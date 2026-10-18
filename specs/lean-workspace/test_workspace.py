"""Real filesystem/Git controls for Lean workspace acceptance."""

import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "workspace", Path(__file__).with_name("workspace.py")
)
workspace = importlib.util.module_from_spec(spec)
spec.loader.exec_module(workspace)


class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.project = self.root / "lean"
        self.project.mkdir()
        (self.project / "lakefile.toml").write_text(
            'name = "Example"\n[[lean_lib]]\nname = "Example"\n'
        )
        (self.project / "lean-toolchain").write_text(workspace.TOOLCHAIN + "\n")
        (self.project / "Example.lean").write_text(
            "theorem identity (n : Nat) : n = n := rfl\n"
        )
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        subprocess.run(["git", "add", "."], cwd=self.root, check=True)
        subprocess.run(
            [
                "git",
                "-c",
                "user.name=Workspace Test",
                "-c",
                "user.email=workspace@example.invalid",
                "commit",
                "-qm",
                "fixture",
            ],
            cwd=self.root,
            check=True,
        )
        self.repo = {
            "nameWithOwner": "example/project",
            "path": str(self.root),
            "mode": "account",
        }

    def lock(self):
        return workspace.project_lock(self.repo, Path("lean/lakefile.toml"))

    def test_aligned_core_needs_no_mathlib(self):
        self.assertEqual(workspace.check_project(self.lock())["state"], "aligned")

    def test_pinned_reference_reports_drift_without_building(self):
        self.repo["mode"] = "mirror-pinned"
        lock = self.lock()
        (self.project / "lean-toolchain").write_text("leanprover/lean4:v4.33.0\n")
        checked = workspace.check_project(lock)
        self.assertEqual(checked["state"], "reference-only")
        self.assertEqual(checked["alignment"], "not-aligned")
        self.assertIn("toolchain is not exact 4.35.0", checked["problems"])
        built = workspace.build_project(lock, self.root / "logs", "/missing/elan", 5)
        self.assertEqual(built["state"], "reference-only")
        self.assertFalse((self.root / "logs").exists())

    def test_added_tracked_source_fails(self):
        lock = self.lock()
        (self.project / "Additional.lean").write_text(
            "theorem extra : True := trivial\n"
        )
        subprocess.run(["git", "add", "."], cwd=self.root, check=True)
        self.assertEqual(workspace.check_project(lock)["state"], "not-aligned")

    def test_commented_requirement_does_not_add_mathlib(self):
        config = self.project / "lakefile.toml"
        config.write_text(config.read_text() + "# Never require mathlib in the core.\n")
        self.assertEqual(workspace.check_project(self.lock())["state"], "aligned")

    def test_floating_mathlib_declaration_fails_even_with_matching_lock(self):
        config = self.project / "lakefile.toml"
        config.write_text(config.read_text() + '\n[[require]]\nname = "mathlib"\n')
        (self.project / "lake-manifest.json").write_text(
            json.dumps(
                {"packages": [{"name": "mathlib", "rev": workspace.MATHLIB_REV}]}
            )
        )
        self.assertEqual(workspace.check_project(self.lock())["state"], "not-aligned")

    def test_wrong_compiler_fails(self):
        lock = self.lock()
        (self.project / "lean-toolchain").write_text("leanprover/lean4:v4.34.0\n")
        self.assertEqual(workspace.check_project(lock)["state"], "not-aligned")

    def test_uncommitted_proof_change_fails(self):
        lock = self.lock()
        (self.project / "Example.lean").write_text(
            "theorem falseClaim : False := by sorry\n"
        )
        self.assertIn(
            "Lean source changed: lean/Example.lean",
            workspace.check_project(lock)["problems"],
        )

    def test_untracked_lean_source_fails(self):
        lock = self.lock()
        (self.project / "Untracked.lean").write_text(
            "theorem exampleProof : True := by trivial\n"
        )
        self.assertEqual(workspace.check_project(lock)["state"], "not-aligned")

    def test_missing_proof_fails(self):
        lock = self.lock()
        (self.project / "Example.lean").unlink()
        self.assertEqual(workspace.check_project(lock)["state"], "not-aligned")

    def test_missing_mathlib_lock_fails(self):
        p = self.project / "lakefile.toml"
        p.write_text(
            p.read_text()
            + '\n[[require]]\nname = "mathlib"\ngit = "https://github.com/leanprover-community/mathlib4"\nrev = "v4.35.0"\n'
        )
        self.assertEqual(workspace.check_project(self.lock())["state"], "not-aligned")

    def test_wrong_resolved_mathlib_fails(self):
        p = self.project / "lakefile.toml"
        p.write_text(
            p.read_text() + '\n[[require]]\nname = "mathlib"\nrev = "v4.35.0"\n'
        )
        (self.project / "lake-manifest.json").write_text(
            json.dumps({"packages": [{"name": "mathlib", "rev": "0" * 40}]})
        )
        self.assertEqual(workspace.check_project(self.lock())["state"], "not-aligned")

    def test_matching_mathlib_passes_then_manifest_drift_fails(self):
        p = self.project / "lakefile.toml"
        p.write_text(
            p.read_text() + '\n[[require]]\nname = "mathlib"\nrev = "v4.35.0"\n'
        )
        manifest = self.project / "lake-manifest.json"
        manifest.write_text(
            json.dumps(
                {"packages": [{"name": "mathlib", "rev": workspace.MATHLIB_REV}]}
            )
        )
        lock = self.lock()
        self.assertEqual(workspace.check_project(lock)["state"], "aligned")
        manifest.write_text("{}")
        self.assertEqual(workspace.check_project(lock)["state"], "not-aligned")

    def test_workspace_omits_reference_mirrors_and_preserves_independent_roots(self):
        one = self.lock()
        two = {**one, "mode": "mirror-pinned", "id": "upstream/reference:lean"}
        dest = self.root / "editor"
        workspace.create_workspace({"repositories": [{"projects": [one, two]}]}, dest)
        result = json.loads((dest / "Lean.code-workspace").read_text())
        self.assertEqual(
            result["folders"], [{"name": one["id"], "path": one["directory"]}]
        )
        self.assertFalse((self.project / "lakefile.lean").exists())


if __name__ == "__main__":
    unittest.main()
