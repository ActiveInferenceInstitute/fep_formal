#!/usr/bin/env python3
"""Generate Q6 raw-input probes, or check their exact bytes without writing.

This command does not run Julia, Lean, a renderer, or a package installer.
An extracted table summary is not the independent Lean proof oracle.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from fep_formal.verification import gnn_artifact_proof as shared_tables
from fep_formal.verification.gnn_julia_artifact_proof import (
    SKELETON_PATH,
    SLICE,
    VARIANTS,
    backend_contract,
    extract_julia_embedded_tables,
    render_julia_input_probe,
    table_manifest,
)

ROOT = Path(__file__).resolve().parents[2]


def regenerate() -> tuple[dict[str, str], dict[str, object]]:
    """Build deterministic texts in memory from the retained fixture bytes."""
    skeleton_bytes = (ROOT / SKELETON_PATH).read_bytes()
    skeleton = skeleton_bytes.decode("utf-8")
    sources: dict[str, str] = {}
    summaries: dict[str, object] = {}
    outputs: dict[str, str] = {}
    for variant in VARIANTS:
        path = f"{SLICE}/fixtures/activeinference_{variant}_runner.jl"
        raw = (ROOT / path).read_bytes()
        tables = extract_julia_embedded_tables(
            raw.decode("utf-8"), skeleton_text=skeleton
        )
        sources[path] = hashlib.sha256(raw).hexdigest()
        summaries[variant] = table_manifest(tables)
        outputs[f"generated/probe_{variant}.lean"] = render_julia_input_probe(
            tables, variant=variant
        )
    for path in (
        SKELETON_PATH,
        f"{SLICE}/generate_probe.py",
        "src/fep_formal/verification/gnn_julia_artifact_proof.py",
    ):
        sources[path] = hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
    sources["src/fep_formal/verification/gnn_artifact_proof.py"] = hashlib.sha256(
        Path(shared_tables.__file__).read_bytes()
    ).hexdigest()
    manifest: dict[str, object] = {
        "schema_version": 1,
        "backend_contract": backend_contract(),
        "source_sha256": sources,
        "generated_sha256": {
            name: hashlib.sha256(text.encode()).hexdigest()
            for name, text in outputs.items()
        },
        "extracted_input_summary": summaries,
        "native_verification": "not_established_by_generation",
        "renderer_custody": "requires_separate_current_receipt",
    }
    outputs["generated/artifact_proof_manifest.json"] = (
        json.dumps(manifest, sort_keys=True, indent=2, allow_nan=False) + "\n"
    )
    return outputs, manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check", action="store_true", help="read-only freshness check"
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        help="fresh output slice; retained outputs are never overwritten",
    )
    args = parser.parse_args(argv)
    if not args.check and args.output_root is None:
        parser.error("current-source generation requires a fresh --output-root")
    target_root = args.output_root.resolve() if args.output_root else ROOT / SLICE
    if not args.check:
        target_root.mkdir(parents=True, exist_ok=False)
    texts, _manifest = regenerate()
    mismatches: list[str] = []
    for relative, text in texts.items():
        target = target_root / relative
        encoded = text.encode("utf-8")
        if args.check:
            if not target.is_file() or target.read_bytes() != encoded:
                mismatches.append(relative)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(encoded)
    if mismatches:
        print("Q6 stale artifacts: " + ", ".join(mismatches))
        return 1
    print("Q6 embedded-input artifacts current; native/runtime evidence not claimed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
