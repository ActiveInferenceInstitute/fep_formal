#!/usr/bin/env python3
"""Retain a canonical scalar JAX render in this slice, never execute the runner."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path

from fep_lean.bridge.custody import contained_file, fingerprint, write_json, write_text
from fep_lean.bridge.operations import DOCUMENTS, PIN, check_sources, emit, owner_roster

SLICE = Path(__file__).resolve().parent
CODE = """
import sys
from pathlib import Path
from gnn.extract.pomdp_extractor import extract_pomdp_from_file
from gnn.render.pomdp_processor import POMDPRenderProcessor
from gnn.render.processor import render_gnn_spec
source, output = map(Path, sys.argv[1:])
model = extract_pomdp_from_file(source, strict_validation=True)
if model is None:
    raise RuntimeError('canonical extraction failed')
spec = POMDPRenderProcessor(output)._pomdp_to_gnn_spec(model)
ok, message, artifacts = render_gnn_spec(spec, 'jax', output)
if not ok:
    raise RuntimeError(message)
print(message)
"""
ROUTE = [
    "gnn.extract.pomdp_extractor.extract_pomdp_from_file(strict_validation=True)",
    "gnn.render.pomdp_processor.POMDPRenderProcessor._pomdp_to_gnn_spec",
    "gnn.render.processor.render_gnn_spec(jax)",
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fep-root", type=Path, required=True)
    parser.add_argument("--gnn-root", type=Path, required=True)
    args = parser.parse_args()
    fep, gnn = args.fep_root.resolve(), args.gnn_root.resolve()
    if fep != SLICE.parents[1]:
        raise ValueError("--fep-root must own this Q7 slice")
    source = contained_file(fep, DOCUMENTS["continuous"])
    input_bytes = source.read_bytes()
    pin_path = contained_file(fep, PIN)
    pin_bytes = pin_path.read_bytes()
    pin = json.loads(pin_bytes)
    errors = check_sources(fep, gnn, pin)
    if errors or not emit(fep, gnn, "continuous", check=True):
        raise ValueError(f"current source pin and continuous input required: {errors}")

    def owners() -> dict[str, dict[str, str]]:
        return {
            key: fingerprint(root, owner_roster(root, key))
            for key, root in (("fep_lean", fep), ("gnn", gnn))
        }

    before = owners()
    with tempfile.TemporaryDirectory(prefix="q7-render-") as temporary:
        temporary_path = Path(temporary)
        output = temporary_path / "rendered"
        frozen_input = temporary_path / source.name
        frozen_input.write_bytes(input_bytes)
        command = [
            "uv",
            "run",
            "--offline",
            "--no-sync",
            "python",
            "-c",
            CODE,
            str(frozen_input),
            str(output),
        ]
        env = dict(os.environ)
        env.pop("VIRTUAL_ENV", None)
        env.update(
            PYTHONPATH=str(gnn / "src"),
            PYTHONPYCACHEPREFIX=str(temporary_path / "bytecode"),
            PYTHONDONTWRITEBYTECODE="1",
        )
        result = subprocess.run(
            command,
            cwd=gnn,
            env=env,
            capture_output=True,
            text=True,
            check=False,
            timeout=120,
        )
        if result.returncode != 0:
            raise RuntimeError(f"canonical rendering failed: {result.stderr}")
        candidates = list(output.rglob("*.py"))
        if len(candidates) != 1:
            raise ValueError("expected exactly one canonical JAX Python artifact")
        artifact_bytes = candidates[0].read_bytes()
    after = owners()
    if (
        before != after
        or source.read_bytes() != input_bytes
        or pin_path.read_bytes() != pin_bytes
    ):
        raise ValueError("source custody changed during rendering")
    fixtures = SLICE / "fixtures"
    fixtures.mkdir(exist_ok=True)
    write_text(fixtures / "continuous_ou_jax.py", artifact_bytes.decode())
    write_text(fixtures / "FepLeanContinuousOU.md", input_bytes.decode())
    record = {
        "schema_version": 1,
        "evidence_plane": "canonical GNN render (no runner execution)",
        "render_route": ROUTE,
        "source_pin_sha256": hashlib.sha256(pin_bytes).hexdigest(),
        "input": {
            "path": DOCUMENTS["continuous"],
            "sha256": hashlib.sha256(input_bytes).hexdigest(),
        },
        "output": {
            "path": "specs/gnn-bridge-q7-continuous-ou-proof/fixtures/continuous_ou_jax.py",
            "sha256": hashlib.sha256(artifact_bytes).hexdigest(),
        },
        "owners_before": before,
        "owners_after": after,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "command": command,
    }
    write_json(SLICE / "render_provenance.json", record)
    print("Retained canonical scalar JAX artifact; no runner or native Lean execution.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
