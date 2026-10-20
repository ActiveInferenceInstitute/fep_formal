"""Boundary checks for the offline historical evidence validator."""

import hashlib
import importlib.util
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "retained_validator", HERE / "validate_retained.py"
)
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)
EVIDENCE = HERE / "evidence/observations-20261020"


def inventory(root):
    return {
        p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in root.rglob("*")
        if p.is_file()
    }


class RetainedEvidenceTests(unittest.TestCase):
    def test_default_validation_is_process_free_and_preserves_bytes(self):
        from unittest.mock import patch

        before = inventory(HERE)
        with patch.object(
            subprocess, "run", side_effect=AssertionError("unexpected process")
        ):
            result = validator.validate(EVIDENCE)
        self.assertEqual(result["actual_historical_invocations"], 2)
        self.assertEqual(result["synthetic_adapter_controls"], 22)
        self.assertFalse(result["runner_executed_by_validator"])
        self.assertEqual(before, inventory(HERE))
        self.assertFalse(list(HERE.rglob("__pycache__")))

    def test_physical_evidence_corruptions_are_rejected(self):
        for case in ("missing", "changed", "extra", "symlink", "coherent_manifest"):
            with self.subTest(case=case), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp) / "evidence"
                shutil.copytree(EVIDENCE, root)
                target = root / "actual/validate_output.py"
                if case == "missing":
                    target.unlink()
                elif case == "changed":
                    target.write_bytes(target.read_bytes() + b"\n# mutation\n")
                elif case == "extra":
                    (root / "unexpected").write_text("extra")
                elif case == "symlink":
                    target.unlink()
                    target.symlink_to(EVIDENCE / "actual/validate_output.py")
                else:
                    target.write_bytes(target.read_bytes() + b"\n# mutation\n")
                    manifest = json.loads((root / "manifest.json").read_text())
                    manifest["files_sha256"]["actual/validate_output.py"] = (
                        validator.sha(target)
                    )
                    (root / "manifest.json").write_text(json.dumps(manifest))
                with self.assertRaises(ValueError):
                    validator.validate(root)

    def test_both_git_arguments_required(self):
        with self.assertRaisesRegex(ValueError, "supply both"):
            validator.validate(EVIDENCE, fep_git=Path("."))

    def test_git_process_explicitly_disables_fetch_replacements_and_writes(self):
        from unittest.mock import patch

        calls = []

        def guarded_run(command, **kwargs):
            self.assertIn("--no-optional-locks", command)
            self.assertIn("--no-replace-objects", command)
            self.assertEqual(kwargs["env"]["GIT_NO_LAZY_FETCH"], "1")
            self.assertEqual(kwargs["env"]["GIT_NO_REPLACE_OBJECTS"], "1")
            self.assertEqual(kwargs["env"]["GIT_OPTIONAL_LOCKS"], "0")
            self.assertEqual(kwargs["timeout"], 30)
            calls.append(command)
            return subprocess.CompletedProcess(command, 0, stdout=b"missing\n")

        with patch.object(subprocess, "run", side_effect=guarded_run):
            with self.assertRaisesRegex(ValueError, "missing historical source blob"):
                validator.validate(EVIDENCE, fep_git=Path("fep"), gnn_git=Path("gnn"))
        self.assertEqual(len(calls), 1)

    def test_missing_git_objects_refuse_without_repository_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "empty.git"
            subprocess.run(
                ["git", "init", "--bare", str(repo)], check=True, capture_output=True
            )
            subprocess.run(
                ["git", "-C", str(repo), "config", "remote.origin.promisor", "true"],
                check=True,
            )
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(repo),
                    "config",
                    "remote.origin.url",
                    "http://127.0.0.1:1/unreachable",
                ],
                check=True,
            )
            before = inventory(repo)
            with self.assertRaises(ValueError):
                validator.validate(EVIDENCE, fep_git=repo, gnn_git=repo)
            self.assertEqual(before, inventory(repo))


if __name__ == "__main__":
    unittest.main()
