#!/usr/bin/env python3
"""Read-only historical P3 numerical comparison; use --output to emit explicitly.

For source-bound receipts use `fep-formal bridge certify --gnn-root PATH
--results PATH`. Numerical agreement is not execution provenance or Lean proof.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from fep_formal.bridge.certificates import compare, render_markdown
from fep_formal.bridge.custody import write_json, write_text

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_RESULTS = SCRIPT_DIR / "gnn_output/12_execute_output/FepLeanSymmetricBool/pymdp/simulation_data/simulation_results.json"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--tolerance", type=float, default=1e-6)
    parser.add_argument("--output", type=Path, help="explicit JSON output; adjacent Markdown also emitted")
    args = parser.parse_args(argv)
    try:
        results = json.loads(args.results.read_text())
        if not isinstance(results, dict):
            # Preserve the historical certifier's invalid-document exception.
            raise ValueError("results must be an object")  # noqa: TRY004
        certificates, observations, ok = compare(results, args.tolerance)
        receipt = {"all_certificates_pass": ok, "certificates": certificates, "observations": observations, "tolerance": args.tolerance, "results_path": str(args.results), "source_bound": False, "native_claim_ready": False}
        if args.output is not None:
            write_json(args.output, receipt)
            write_text(args.output.with_suffix(".md"), render_markdown(certificates, observations, args.results, ok))
        print(json.dumps(receipt, indent=2, allow_nan=False))
        return 0 if ok else 1
    except (OSError, ValueError, TypeError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
