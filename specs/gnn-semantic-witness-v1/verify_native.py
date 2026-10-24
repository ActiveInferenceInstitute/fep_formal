"""Compile the scoped laws and false controls; retain one fresh native attempt."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from fep_lean.verification._toolchain import (
    lean_version_matches_pin,
    toolchain_identity,
)
from fep_lean.verification.lean_verifier import LeanVerifier


def compile_laws(output: Path) -> dict[str, object]:
    """Preserve exact positive/control code and every actual compiler result."""
    root = Path(__file__).resolve().parents[2]
    source_path = Path(__file__).with_name("semantic_laws.lean")
    source = source_path.read_text(encoding="utf-8")
    output.mkdir(parents=True, exist_ok=False)
    variants = {
        "positive": source,
        "zero-normalizer": "import Mathlib.Tactic\nexample : (0 : ℝ) / 0 = 1 := by norm_num\n",
        "omitted-observation-noise": "import Mathlib.Tactic\nexample : (1 - (1 : ℝ) / 2) ^ 2 = 1 / 2 := by norm_num\n",
    }
    verifier = LeanVerifier(lean_dir=root / "lean", project_root=root)
    results = {}
    passed = True
    pin = (root / "lean/lean-toolchain").read_text(encoding="utf-8").strip()
    for name, code in variants.items():
        (output / f"{name}.lean").write_text(code, encoding="utf-8")
        result = verifier.verify_sketch("semantic-" + name, code)
        accepted = (
            not result.skip_reason
            and lean_version_matches_pin(result.lean_version, pin)
            and not result.has_sorry
            and not result.warnings
            and (result.compiles if name == "positive" else not result.compiles)
        )
        if name != "positive":
            accepted = accepted and result.failure_kind == "tactic_failure"
        passed = passed and accepted
        results[name] = {
            **result.as_dict(),
            "stdout": result.stdout,
            "stderr": result.stderr,
            "accepted": accepted,
            "source_sha256": hashlib.sha256(code.encode()).hexdigest(),
        }
    receipt: dict[str, object] = {
        "schema": "fep-gnn-semantic-native-v1",
        "status": "passed" if passed else "failed",
        "source_path": source_path.relative_to(root).as_posix(),
        "source_sha256": hashlib.sha256(source.encode()).hexdigest(),
        "toolchain": toolchain_identity(root / "lean"),
        "results": results,
        "scope": "Finite-weight normalization and scalar arbitrary-H prior measurement algebra only; no GNN parser/runner, matrix Gaussian conditioning or universal translation proof.",
        "execution_source_verified": False,
        "universal_equivalence": False,
    }
    (output / "receipt.json").write_text(
        json.dumps(receipt, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    receipt = compile_laws(arguments.output.resolve())
    print(
        json.dumps(
            {
                "status": receipt["status"],
                "receipt": str(arguments.output / "receipt.json"),
            }
        )
    )
    return 0 if receipt["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
