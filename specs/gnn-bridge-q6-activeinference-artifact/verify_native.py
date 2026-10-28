#!/usr/bin/env python3
"""Q6 native embedded-input evidence; default checks are read-only."""

import sys
from pathlib import Path

sys.dont_write_bytecode = True

from fep_formal.bridge.operations import DOCUMENTS
from fep_formal.verification.gnn_artifact_receipt import (
    ArtifactContract,
    ArtifactVerifier,
    RenderBinding,
)

SLICE = "specs/gnn-bridge-q6-activeinference-artifact"
ROUTE = (
    "extract_pomdp_from_file(strict_validation=True)",
    "POMDPRenderProcessor._pomdp_to_gnn_spec",
    "render_gnn_spec(activeinference_jl)",
)
CONTRACT = ArtifactContract(
    slice=SLICE,
    input_variant="finite",
    fixtures={
        v: f"{SLICE}/fixtures/activeinference_{v}_runner.jl"
        for v in ("symmetric", "asymmetric")
    },
    probes={
        v: f"{SLICE}/generated/probe_{v}.lean" for v in ("symmetric", "asymmetric")
    },
    theorems={
        "symmetric": tuple(
            "FEPProbe.Q6JuliaEmbeddedInput." + name
            for name in (
                "symEmbeddedInput_eq_Q2",
                "symEmbeddedInput_Q4_conditional",
                "symEmbeddedInput_Q2_carrierMasses",
            )
        ),
        "asymmetric": tuple(
            "FEPProbe.Q6JuliaEmbeddedInputAsym." + name
            for name in (
                "asymEmbeddedInput_eq_expected",
                "asymExpected_differs_from_Q2",
            )
        ),
    },
    targets=("FepSketches.gnn_denotation", "FepSketches.gnn_render_statements"),
    scope="Q6 raw embedded Boolean input tables; no consumed-C, Julia runtime, package-agent or EFE equivalence",
    render_route=ROUTE,
    extractor="src/fep_formal/verification/gnn_julia_artifact_proof.py",
    adapter=f"{SLICE}/verify_native.py",
    extra_files=(
        f"{SLICE}/skeleton/canonical_bool_runner.jl.in",
        f"{SLICE}/fixtures/symmetric_renderer_input.json",
        f"{SLICE}/fixtures/asymmetric_renderer_input.json",
        "src/fep_formal/verification/gnn_artifact_proof.py",
    ),
    render_bindings=(
        RenderBinding(
            "symmetric", DOCUMENTS["finite"], "official_finite_GNN_input", ROUTE
        ),
        RenderBinding(
            "asymmetric",
            f"{SLICE}/fixtures/asymmetric_renderer_input.json",
            "independently_authored_canonical_control",
            ("render_gnn_spec(activeinference_jl)",),
        ),
    ),
)
VERIFICATION = ArtifactVerifier(Path(__file__).resolve().parents[2], CONTRACT)

if __name__ == "__main__":
    raise SystemExit(VERIFICATION.main())
