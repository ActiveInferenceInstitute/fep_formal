#!/usr/bin/env python3
"""Explicitly retain a current canonical PyMDP render and its source provenance."""

from __future__ import annotations

import argparse
import os
import subprocess
import tempfile
from pathlib import Path

from verify_native import VERIFICATION as verification

from fep_lean.bridge.custody import fingerprint, write_json, write_text
from fep_lean.bridge.operations import DOCUMENTS, PIN, check_sources, emit, owner_roster

RENDER_CODE = """
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
ok, message, artifacts = render_gnn_spec(spec, 'pymdp', output)
if not ok:
    raise RuntimeError(message)
print(message)
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gnn-root", type=Path, required=True)
    args = parser.parse_args()
    root, gnn = verification.root, args.gnn_root.resolve()
    pin_path = root / PIN
    pin = verification.read_object(pin_path)
    errors = check_sources(root, gnn, pin)
    if errors or not emit(root, gnn, "finite", check=True):
        raise ValueError(f"current source pin and finite input required: {errors}")
    source = root / DOCUMENTS["finite"]
    input_digest = verification._digest(source.read_bytes())

    def owners() -> dict[str, dict[str, str]]:
        return {
            key: fingerprint(checkout, owner_roster(checkout, key))
            for key, checkout in (("fep_lean", root), ("gnn", gnn))
        }

    before = owners()
    with tempfile.TemporaryDirectory(prefix="q5_render_") as temporary:
        output = Path(temporary) / "rendered"
        command = [
            "uv",
            "run",
            "--offline",
            "--no-sync",
            "python",
            "-c",
            RENDER_CODE,
            str(source),
            str(output),
        ]
        env = dict(os.environ)
        env["PYTHONPATH"] = str(gnn / "src")
        # A fresh cache namespace prevents timestamp-valid old bytecode reads.
        env["PYTHONPYCACHEPREFIX"] = str(Path(temporary) / "bytecode")
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        result = subprocess.run(
            command,
            cwd=gnn,
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
            check=True,
        )
        artifacts = list(output.rglob("*.py"))
        if len(artifacts) != 1:
            raise ValueError(
                "canonical render must produce exactly one Python artifact"
            )
        rendered = artifacts[0].read_text(encoding="utf-8")
    after = owners()
    if before != after or verification.read_object(pin_path) != pin:
        raise ValueError("source custody changed during render")
    if verification._digest(source.read_bytes()) != input_digest:
        raise ValueError("finite input changed during render")
    fixture = verification.contract.fixtures["symmetric"]
    write_text(root / fixture, rendered)
    write_json(
        root / verification.contract.provenance,
        {
            "schema_version": 1,
            "evidence_plane": "canonical GNN render (no runner execution)",
            "render_route": list(verification.contract.render_route),
            "source_pin_sha256": verification._digest(pin_path.read_bytes()),
            "input": {"path": DOCUMENTS["finite"], "sha256": input_digest},
            "output": {
                "path": fixture,
                "sha256": verification._digest(rendered.encode()),
            },
            "owners_before": before,
            "owners_after": after,
            "command": command,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        },
    )
    print(
        "Retained current canonical render; regenerate probes before native verification."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
