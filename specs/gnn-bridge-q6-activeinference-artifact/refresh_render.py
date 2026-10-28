#!/usr/bin/env python3
"""Explicitly render both Q6 inputs and retain source-bound provenance."""

from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
import tempfile
from pathlib import Path

from verify_native import CONTRACT, VERIFICATION

from fep_formal.bridge.custody import (
    contained_file,
    fingerprint,
    write_json,
    write_text,
)
from fep_formal.bridge.operations import (
    DOCUMENTS,
    PIN,
    check_sources,
    emit,
    owner_roster,
)

CODE = """
import json, sys
from pathlib import Path
from gnn.pomdp_extractor import extract_pomdp_from_file
from render.pomdp_processor import POMDPRenderProcessor
from render.processor import render_gnn_spec
source, asymmetric, output = map(Path, sys.argv[1:])
model = extract_pomdp_from_file(source, strict_validation=True)
if model is None:
    raise RuntimeError('canonical extraction failed')
specs = {
    'symmetric': POMDPRenderProcessor(output)._pomdp_to_gnn_spec(model),
    'asymmetric': json.loads(asymmetric.read_text()),
}
for variant, spec in specs.items():
    ok, message, artifacts = render_gnn_spec(spec, 'activeinference_jl', output / variant)
    if not ok:
        raise RuntimeError(message)
    print(variant + ': ' + message)
    if variant == 'symmetric':
        (output / 'symmetric_renderer_input.json').write_text(json.dumps(spec, sort_keys=True, indent=2)+'\\n')
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gnn-root", type=Path, required=True)
    args = parser.parse_args()
    root, gnn = VERIFICATION.root, args.gnn_root.resolve()
    pin_path = contained_file(root, PIN)
    pin_bytes = pin_path.read_bytes()
    pin = VERIFICATION.read_object(pin_path)
    errors = check_sources(root, gnn, pin)
    if errors or not emit(root, gnn, "finite", check=True):
        raise ValueError(f"current source pin and finite input required: {errors}")
    sources = [binding.input_path for binding in CONTRACT.render_bindings]
    inputs = {name: contained_file(root, name).read_bytes() for name in sources}

    def owners() -> dict[str, dict[str, str]]:
        return {
            key: fingerprint(checkout, owner_roster(checkout, key))
            for key, checkout in (("fep_lean", root), ("gnn", gnn))
        }

    before = owners()
    with tempfile.TemporaryDirectory(prefix="q6-render-") as temporary:
        folder = Path(temporary)
        source = folder / Path(DOCUMENTS["finite"]).name
        control = folder / "asymmetric_renderer_input.json"
        source.write_bytes(inputs[DOCUMENTS["finite"]])
        control.write_bytes(
            inputs[f"{CONTRACT.slice}/fixtures/asymmetric_renderer_input.json"]
        )
        output = folder / "rendered"
        command = [
            "uv",
            "run",
            "--offline",
            "--no-sync",
            "python",
            "-c",
            CODE,
            str(source),
            str(control),
            str(output),
        ]
        env = dict(os.environ)
        env.pop("VIRTUAL_ENV", None)
        env.update(
            PYTHONPATH=str(gnn / "src"),
            PYTHONDONTWRITEBYTECODE="1",
            PYTHONPYCACHEPREFIX=str(folder / "bytecode"),
        )
        result = subprocess.run(
            command,
            cwd=gnn,
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
            check=True,
        )
        artifacts = {}
        for variant in CONTRACT.fixtures:
            paths = list((output / variant).glob("*.jl"))
            if len(paths) != 1:
                raise ValueError("expected one canonical Julia artifact per variant")
            artifacts[variant] = paths[0].read_bytes()
        symmetric_input = (output / "symmetric_renderer_input.json").read_text()
    after = owners()
    if before != after or pin_path.read_bytes() != pin_bytes:
        raise ValueError("source custody changed during rendering")
    if any(
        contained_file(root, name).read_bytes() != data for name, data in inputs.items()
    ):
        raise ValueError("render input changed during rendering")
    for variant, data in artifacts.items():
        write_text(root / CONTRACT.fixtures[variant], data.decode())
    write_text(
        root / CONTRACT.slice / "fixtures/symmetric_renderer_input.json",
        symmetric_input,
    )
    renders = {
        binding.variant: {
            "input": {
                "path": binding.input_path,
                "sha256": hashlib.sha256(inputs[binding.input_path]).hexdigest(),
                "kind": binding.input_kind,
            },
            "output": {
                "path": CONTRACT.fixtures[binding.variant],
                "sha256": hashlib.sha256(artifacts[binding.variant]).hexdigest(),
            },
            "render_route": list(binding.route),
        }
        for binding in CONTRACT.render_bindings
    }
    write_json(
        root / CONTRACT.provenance,
        {
            "schema_version": 1,
            "evidence_plane": "canonical GNN render (no runner execution)",
            "source_pin_sha256": hashlib.sha256(pin_bytes).hexdigest(),
            "renders": renders,
            "owners_before": before,
            "owners_after": after,
            "command": command,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        },
    )
    print(
        "Retained both canonical Julia renders; regenerate probes and compile explicitly."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
