#!/usr/bin/env python3
"""Q7 native coefficient-bound evidence; default checks are read-only."""

import sys
from pathlib import Path

sys.dont_write_bytecode = True

from fep_lean.verification.gnn_artifact_receipt import (
    ArtifactContract,
    ArtifactVerifier,
)

SLICE = "specs/gnn-bridge-q7-continuous-ou-proof"
CONTRACT = ArtifactContract(
    slice=SLICE,
    input_variant="continuous",
    canonical_variant="ou",
    fixtures={"ou": f"{SLICE}/fixtures/continuous_ou_jax.py"},
    probes={"ou": f"{SLICE}/generated/probe.lean"},
    theorems={
        "ou": tuple(
            "FEPProbe.Q7ContinuousOU." + name
            for name in (
                "selected_decay",
                "selected_transitionVariance",
                "exact_row_eq_selected",
                "artifact_exact_parameters",
                "exact_noise_formula",
                "artifact_F_bound",
                "artifact_Q_bound",
                "artifact_prediction_mean_bound",
                "artifact_prediction_variance_bound",
                "artifact_stationary_defect_bound",
                "nonstationary_prediction_changes_mean",
                "scalar_joseph_identity",
            )
        )
    },
    targets=("FepSketches.compositions.smooth_reference_kernel",),
    scope="static binary64 coefficient approximation and real-arithmetic prediction bounds",
    render_route=(
        "gnn.extract.pomdp_extractor.extract_pomdp_from_file(strict_validation=True)",
        "gnn.render.pomdp_processor.POMDPRenderProcessor._pomdp_to_gnn_spec",
        "gnn.render.processor.render_gnn_spec(jax)",
    ),
    extractor="src/fep_lean/verification/gnn_continuous_artifact_proof.py",
    adapter=f"{SLICE}/verify_native.py",
    extra_files=(
        f"{SLICE}/expected.json",
        f"{SLICE}/probe.template.lean",
        f"{SLICE}/fixtures/FepLeanContinuousOU.md",
    ),
)
VERIFICATION = ArtifactVerifier(Path(__file__).resolve().parents[2], CONTRACT)

if __name__ == "__main__":
    raise SystemExit(VERIFICATION.main())
