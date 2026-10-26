"""Retain one serial native check of finite product laws and false controls."""

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


def compile_composition(
    output: Path, lean_dir: Path | None = None
) -> dict[str, object]:
    """Check existing ready pins/cache only; never acquire dependencies."""
    root = Path(__file__).resolve().parents[2]
    workspace = (root / "lean") if lean_dir is None else lean_dir.resolve()
    files = ("lean-toolchain", "lakefile.lean", "lake-manifest.json")
    pins = {name: (root / "lean" / name).read_bytes() for name in files}
    if any((workspace / name).read_bytes() != raw for name, raw in pins.items()):
        raise ValueError(
            "explicit native workspace differs from project toolchain/Mathlib pins"
        )
    source_path = Path(__file__).with_name("composition_laws.lean")
    source = source_path.read_text()
    variants = {
        "positive": source,
        "zero-product-normalizer": "import Mathlib.Tactic\nexample : (0 : ℝ) / (0 * 2) = 1 := by norm_num\n",
        "omitted-product-assumption": "import Mathlib.Tactic\nexample : (1 : ℝ) / 2 = (1 / 2) * (1 / 2) := by norm_num\n",
    }
    output.mkdir(parents=True, exist_ok=False)
    verifier = LeanVerifier(lean_dir=workspace, project_root=root)
    results, passed = {}, True
    for name, code in variants.items():
        (output / f"{name}.lean").write_text(code)
        result = verifier.verify_sketch("composition-" + name, code)
        accepted = (
            not result.skip_reason
            and lean_version_matches_pin(
                result.lean_version, pins["lean-toolchain"].decode().strip()
            )
            and not result.has_sorry
            and "sorryAx" not in result.stdout
            and not result.warnings
            and (result.compiles if name == "positive" else not result.compiles)
        )
        if name != "positive":
            accepted = accepted and result.failure_kind == "tactic_failure"
        results[name] = {
            **result.as_dict(),
            "stdout": result.stdout,
            "stderr": result.stderr,
            "accepted": accepted,
            "source_sha256": hashlib.sha256(code.encode()).hexdigest(),
        }
        passed = passed and accepted
    unchanged = source_path.read_text() == source and all(
        (root / "lean" / name).read_bytes() == raw == (workspace / name).read_bytes()
        for name, raw in pins.items()
    )
    receipt = {
        "schema": "fep-gnn-finite-product-native-v1",
        "status": "passed" if passed and unchanged else "failed",
        "source_path": source_path.relative_to(root).as_posix(),
        "source_sha256": hashlib.sha256(source.encode()).hexdigest(),
        "native_workspace": str(workspace),
        "toolchain": toolchain_identity(workspace),
        "pin_sha256": {
            name: hashlib.sha256(raw).hexdigest() for name, raw in pins.items()
        },
        "source_and_pin_bookends_equal": unchanged,
        "results": results,
        "scope": "Finite post-evidence product-weight normalization/nonnegativity with explicit masses and a correlated counterexample; no Gaussian measure/kernel, matrix-conditioning, parser/runner or general composition proof.",
        "execution_source_verified": False,
        "universal_equivalence": False,
    }
    (output / "receipt.json").write_text(
        json.dumps(receipt, indent=2, allow_nan=False) + "\n"
    )
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--lean-dir",
        type=Path,
        help="Existing ready workspace with byte-identical project pins",
    )
    args = parser.parse_args()
    receipt = compile_composition(args.output.resolve(), args.lean_dir)
    print(
        json.dumps(
            {"status": receipt["status"], "receipt": str(args.output / "receipt.json")}
        )
    )
    return 0 if receipt["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
