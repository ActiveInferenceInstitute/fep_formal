#!/usr/bin/env python3
"""Q5 native evidence adapter. Default/--check is read-only; --compile is explicit."""

from __future__ import annotations

import sys
from pathlib import Path

sys.dont_write_bytecode = True

from fep_formal.verification.gnn_artifact_receipt import (
    ArtifactContract,
    ArtifactVerifier,
)

SLICE = "specs/gnn-bridge-q5-artifact-proof"
CONTRACT = ArtifactContract(
    slice=SLICE,
    input_variant="finite",
    fixtures={
        v: f"{SLICE}/fixtures/pymdp_{v}_runner.py" for v in ("symmetric", "asymmetric")
    },
    probes={
        v: f"{SLICE}/generated/probe_{v}.lean" for v in ("symmetric", "asymmetric")
    },
    theorems={
        "symmetric": tuple(
            f"FEPProbe.Q5ArtifactProof.{name}"
            for name in (
                "symArtifactTables_faithful",
                "symArtifact_statement5Pymdp",
                "symArtifact_carrierMasses",
                "symArtifact_aMass_eq_original",
            )
        ),
        "asymmetric": tuple(
            f"FEPProbe.Q5ArtifactProofAsym.{name}"
            for name in (
                "asymArtifactTables_faithful",
                "asymExpected_ne_symBoolPayload",
            )
        ),
    },
    targets=("FepSketches.gnn_denotation", "FepSketches.gnn_render_statements"),
    scope="Q5 concrete static Boolean tables; no runner execution or C/EFE equivalence",
    render_route=(
        "extract_pomdp_from_file(strict_validation=True)",
        "POMDPRenderProcessor._pomdp_to_gnn_spec",
        "render_gnn_spec",
    ),
    extractor="src/fep_formal/verification/gnn_artifact_proof.py",
    adapter=f"{SLICE}/verify_native.py",
)
VERIFICATION = ArtifactVerifier(Path(__file__).resolve().parents[2], CONTRACT)


def main(argv: list[str] | None = None) -> int:
    return VERIFICATION.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
