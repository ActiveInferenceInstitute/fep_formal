#!/usr/bin/env python3
"""Native Lean verification receipts for the Cascadia river-homing slice.

``--compile`` (writes a receipt; requires the built pinned Mathlib cache):

1. compiles ``lean/CascadiaGeo/TypedGeospatial.lean`` to an isolated olean
   under ``output/cascadia-geo-act-proof/build`` with ``lake env lean -R -o``;
2. compiles ``generated/SmithRiverHoming.lean`` against it with one
   ``#print axioms`` request per theorem of both files;
3. compiles four mutated copies of the instance, each of which must fail:
   transposed B axes, one H3 adjacency edge removed, an arrival bound one step
   too strong, and a wrong exact posterior.

The receipt is claim-ready only when both positive compiles exit 0 with no
``error``, ``warning`` or ``sorry`` output, every theorem reports a subset of
``propext``, ``Classical.choice`` and ``Quot.sound``, and every mutation fails.

``--check`` (default) launches no Lean process: it re-hashes every bound input,
reparses the retained transcripts and recomputes the verdict.

    uv run python specs/cascadia-geo-act-proof/verify_native.py --compile \\
        --receipt output/cascadia-geo-act-proof/native-receipt.json
    uv run python specs/cascadia-geo-act-proof/verify_native.py --check \\
        --receipt specs/cascadia-geo-act-proof/native_receipt.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import signal
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SLICE = Path(__file__).resolve().parent
REPO_ROOT = SLICE.parents[1]
LEAN_DIR = REPO_ROOT / "lean"
THEORY_ROOT = SLICE / "lean"
THEORY = THEORY_ROOT / "CascadiaGeo" / "TypedGeospatial.lean"
INSTANCE = SLICE / "generated" / "SmithRiverHoming.lean"
BUILD = REPO_ROOT / "output" / "cascadia-geo-act-proof" / "build"
STANDARD_AXIOMS = {"propext", "Classical.choice", "Quot.sound"}
BOUND = [
    THEORY,
    INSTANCE,
    SLICE / "generated" / "manifest.json",
    SLICE / "generate_probe.py",
    Path(__file__).resolve(),
    SLICE / "fixtures" / "smith_river_homing.gnn.md",
    SLICE / "fixtures" / "smith_river_homing.geo-infer.json",
    SLICE / "fixtures" / "smith_river_homing.domain.json",
    LEAN_DIR / "lean-toolchain",
    LEAN_DIR / "lake-manifest.json",
]
MUTATIONS = {
    "transposed_b_axes": (
        "def bNum (a : Act) (c c' : Cell) : ℕ := ((bTable.getD a.val []).getD c.val []).getD c'.val 0",
        "def bNum (a : Act) (c c' : Cell) : ℕ := ((bTable.getD a.val []).getD c'.val []).getD c.val 0",
    ),
    "h3_edge_removed": (
        "def h3Adjacent (c c' : Cell) : Bool :=\n  (h3NeighborTable.getD c.val []).contains c'.val",
        "def h3Adjacent (c c' : Cell) : Bool :=\n  (h3NeighborTable.getD c.val []).contains c'.val &&\n    !(c.val == 0 && c'.val == 1) && !(c.val == 1 && c'.val == 0)",
    ),
    "arrival_bound_too_strong": (
        "theorem homing_lower_bound (plan : List Act) (hshort : plan.length < {bound}) :",
        "theorem homing_lower_bound (plan : List Act) (hshort : plan.length < {stronger}) :",
    ),
    "wrong_exact_posterior": (
        "      {posterior} := by\n  show (dNum sea",
        "      {wrong} := by\n  show (dNum sea",
    ),
}


def sha256_bytes(data: bytes) -> str:
    """Return the lowercase SHA-256 of bytes."""
    return hashlib.sha256(data).hexdigest()


def relative(path: Path) -> str:
    """Repository-relative POSIX path."""
    return path.resolve().relative_to(REPO_ROOT).as_posix()


def scrub(value: Any) -> Any:
    """Replace machine-specific roots in transcripts with stable tokens."""
    if isinstance(value, list):
        return [scrub(item) for item in value]
    text = value.replace(str(REPO_ROOT), "<repo>")
    return re.sub(r"\S*cascadia-lean-[A-Za-z0-9_]+", "<tmp>", text)


def bound_digests() -> dict[str, str]:
    """SHA-256 of every input the verdict depends on."""
    return {relative(path): sha256_bytes(path.read_bytes()) for path in BOUND}


def run_group(
    command: list[str], *, env: dict[str, str] | None = None, timeout: int = 3600
) -> dict[str, Any]:
    """Run in a new process group; kill the whole group on timeout."""
    started = time.monotonic()
    process = subprocess.Popen(
        command,
        cwd=LEAN_DIR,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        stdout, stderr = process.communicate()
        return {
            "command": command,
            "exit_code": None,
            "timed_out": True,
            "stdout": stdout,
            "stderr": stderr,
            "seconds": round(time.monotonic() - started, 2),
        }
    return {
        "command": command,
        "exit_code": process.returncode,
        "timed_out": False,
        "stdout": stdout,
        "stderr": stderr,
        "seconds": round(time.monotonic() - started, 2),
    }


def theorem_names(path: Path, namespace: str) -> list[str]:
    """Fully qualified names of top-level theorems declared in a file."""
    return [
        f"{namespace}.{name}"
        for name in re.findall(
            r"^theorem (\S+)", path.read_text(encoding="utf-8"), re.MULTILINE
        )
    ]


def parse_axioms(output: str) -> dict[str, list[str]]:
    """Parse ``#print axioms`` reports into theorem -> axioms."""
    reports: dict[str, list[str]] = {}
    for match in re.finditer(r"'([^']+)' depends on axioms: \[([^\]]*)\]", output):
        reports[match.group(1)] = sorted(
            part.strip() for part in match.group(2).split(",") if part.strip()
        )
    for match in re.finditer(r"'([^']+)' does not depend on any axioms", output):
        reports[match.group(1)] = []
    return reports


def mutation_texts(instance: str, manifest: dict[str, Any]) -> dict[str, str]:
    """Apply each mutation exactly once to the generated instance."""
    facts = manifest["facts"]
    bound = facts["home_lower_bound_steps"]
    numerator, denominator = facts["first_posterior_sea"].split("/")
    values = {
        "bound": str(bound),
        "stronger": str(bound + 1),
        "posterior": f"{numerator} / {denominator}",
        "wrong": f"{int(numerator) + 1} / {int(denominator) + 1}",
    }
    texts = {}
    for name, (old, new) in MUTATIONS.items():
        old, new = old.format(**values), new.format(**values)
        if instance.count(old) != 1:
            raise RuntimeError(
                f"mutation {name} does not match the instance exactly once"
            )
        texts[name] = instance.replace(old, new)
    return texts


def clean(result: dict[str, Any]) -> bool:
    """Exit 0 and no error, warning or sorry in the transcript."""
    text = (result["stdout"] or "") + (result["stderr"] or "")
    return result["exit_code"] == 0 and not re.search(
        r"\berror\b|\bwarning\b|\bsorry\b", text
    )


def verdict(receipt: dict[str, Any]) -> dict[str, Any]:
    """Recompute the verdict from retained transcripts."""
    theory, instance = receipt["theory_compile"], receipt["instance_compile"]
    reports = parse_axioms(instance["stdout"] + instance["stderr"])
    expected = receipt["theorems"]
    missing = sorted(set(expected) - set(reports))
    nonstandard = {
        name: axioms
        for name, axioms in reports.items()
        if not set(axioms) <= STANDARD_AXIOMS
    }
    rejected = {
        name: result["exit_code"] not in (0, None)
        and "error" in (result["stdout"] + result["stderr"])
        for name, result in receipt["mutations"].items()
    }
    return {
        "theory_clean": clean(theory),
        "instance_clean": clean(instance),
        "theorems_reported": len(reports),
        "missing_axiom_reports": missing,
        "nonstandard_axioms": nonstandard,
        "mutations_rejected": rejected,
        "claim_ready": clean(theory)
        and clean(instance)
        and not missing
        and not nonstandard
        and set(rejected) == set(MUTATIONS)
        and all(rejected.values()),
    }


def compile_receipt(receipt_path: Path) -> int:
    """Run the native compiles and write a receipt."""
    BUILD.mkdir(parents=True, exist_ok=True)
    olean_dir = BUILD / "CascadiaGeo"
    olean_dir.mkdir(exist_ok=True)
    base = run_group(["lake", "env", "printenv", "LEAN_PATH"], timeout=300)
    environment = dict(
        os.environ, LEAN_PATH=base["stdout"].strip() + os.pathsep + str(BUILD)
    )
    version = run_group(["lake", "env", "lean", "--version"], timeout=300)
    theory = run_group(
        [
            "lake",
            "env",
            "lean",
            "-R",
            str(THEORY_ROOT),
            "-o",
            str(olean_dir / "TypedGeospatial.olean"),
            str(THEORY),
        ]
    )
    names = theorem_names(THEORY, "CascadiaGeo") + theorem_names(
        INSTANCE, "CascadiaGeo.SmithRiverHoming"
    )
    instance_text = INSTANCE.read_text(encoding="utf-8")
    manifest = json.loads(
        (SLICE / "generated" / "manifest.json").read_text(encoding="utf-8")
    )
    with tempfile.TemporaryDirectory(prefix="cascadia-lean-") as temp:
        probe = Path(temp) / "SmithRiverHomingProbe.lean"
        probe.write_text(
            instance_text + "".join(f"\n#print axioms {name}" for name in names) + "\n",
            encoding="utf-8",
        )
        instance = run_group(["lake", "env", "lean", str(probe)], env=environment)
        mutations = {}
        for name, text in mutation_texts(instance_text, manifest).items():
            path = Path(temp) / f"{name}.lean"
            path.write_text(text, encoding="utf-8")
            result = run_group(["lake", "env", "lean", str(path)], env=environment)
            result["first_error"] = next(
                (
                    line
                    for line in (result["stdout"] + result["stderr"]).splitlines()
                    if "error" in line
                ),
                None,
            )
            mutations[name] = result
    receipt: dict[str, Any] = {
        "schema_version": "fep-lean/cascadia-native-receipt/1",
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "platform": platform.platform(),
        "lean_version": version["stdout"].strip(),
        "bound_inputs": bound_digests(),
        "theorems": names,
        "theory_compile": theory,
        "instance_compile": instance,
        "mutations": mutations,
    }
    for record in (theory, instance, *mutations.values()):
        for key in ("command", "stdout", "stderr", "first_error"):
            if key in record and record[key] is not None:
                record[key] = scrub(record[key])
    receipt["verdict"] = verdict(receipt)
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(
        json.dumps(receipt, indent=1, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(receipt["verdict"], indent=1, sort_keys=True))
    return 0 if receipt["verdict"]["claim_ready"] else 1


def check_receipt(receipt_path: Path) -> int:
    """Validate a retained receipt against the current bound inputs."""
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    problems = []
    if receipt.get("schema_version") != "fep-lean/cascadia-native-receipt/1":
        problems.append("unexpected receipt schema")
    current = bound_digests()
    for name, digest in receipt.get("bound_inputs", {}).items():
        if current.get(name) != digest:
            problems.append(f"{name}: bound digest differs from the current file")
    if set(receipt.get("bound_inputs", {})) != set(current):
        problems.append("bound input set differs from the current roster")
    recomputed = verdict(receipt)
    if recomputed != receipt.get("verdict"):
        problems.append("retained verdict differs from the recomputed verdict")
    if not recomputed["claim_ready"]:
        problems.append("receipt is not claim-ready")
    for problem in problems:
        print(f"STALE: {problem}", file=sys.stderr)
    if not problems:
        print(
            f"OK: claim-ready receipt for {len(receipt['theorems'])} theorems; "
            f"{len(receipt['mutations'])} mutations rejected"
        )
    return 1 if problems else 0


def main() -> int:
    """Dispatch ``--compile`` or ``--check``."""
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--compile", action="store_true")
    mode.add_argument("--check", action="store_true")
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    if args.compile:
        return compile_receipt(args.receipt)
    return check_receipt(args.receipt)


if __name__ == "__main__":
    raise SystemExit(main())
