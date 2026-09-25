#!/usr/bin/env python3
"""
pymdp 1.0.0 runner for FepLean Symmetric Boolean Generative Model

This file was generated from a GNN specification by
``render/pymdp/pymdp_renderer.py``. It delegates the actual rollout
to the GNN pipeline's tested execution module
(``execute.pymdp.run_pymdp_simulation``), which in turn calls
real pymdp 1.0.0 (JAX-first) under the hood.

Model:        FepLean Symmetric Boolean Generative Model
Description:  

State Space:
  - Hidden States: 2
  - Observations:  2
  - Actions:       2

Initial matrices present in GNN spec:
  - A (likelihood):   Present
  - B (transitions):  Present
  - C (preferences):  Present
  - D (state prior):  Present
  - E (policy prior): Present
"""
from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Script directory name 'pymdp' would shadow the installed library — drop it
# ---------------------------------------------------------------------------
if sys.path and sys.path[0] and sys.path[0].endswith("pymdp"):
    sys.path.pop(0)

# ---------------------------------------------------------------------------
# Repository root resolution (prefer GNN_PROJECT_ROOT; else walk upwards)
# ---------------------------------------------------------------------------
_gnn_root = os.environ.get("GNN_PROJECT_ROOT")
if _gnn_root:
    _repo = Path(_gnn_root).resolve()
    sys.path.insert(0, str(_repo / "src"))
else:
    _cur = Path(__file__).resolve().parent
    _found = None
    for _ in range(24):
        if (_cur / "pyproject.toml").is_file() and (_cur / "src").is_dir():
            _found = _cur
            break
        if _cur.parent == _cur:
            break
        _cur = _cur.parent
    if _found is None:
        print(
            "ERROR: Cannot locate GNN repository root. Run via the pipeline "
            "execute step, or set GNN_PROJECT_ROOT to the checkout root.",
            file=sys.stderr,
        )
        sys.exit(1)
    sys.path.insert(0, str(_found / "src"))

# ---------------------------------------------------------------------------
# pymdp 1.0.0 presence check (hard requirement)
# ---------------------------------------------------------------------------
try:
    import pymdp  # noqa: F401
    from pymdp.agent import Agent  # noqa: F401
    if not hasattr(Agent, "update_empirical_prior"):
        raise ImportError("unsupported pymdp (<1.0.0) detected")
    print("PyMDP 1.0.0+ detected (JAX-first Agent).")
except ImportError as e:
    print(
        "ERROR: pymdp 1.0.0 required. Install with: "
        "uv pip install 'inferactively-pymdp>=1.0.0' (original error: "
        + str(e) + ")",
        file=sys.stderr,
    )
    sys.exit(1)

from gnn.execute.pymdp import execute_pymdp_simulation

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def main() -> int:
    """Run a pymdp 1.0.0 simulation for the GNN model embedded in this file."""
    # Matrices embedded verbatim from the GNN spec.
    A_data = [[0.5, 0.5], [0.5, 0.5]]
    B_data = [[[0.5, 0.5], [0.5, 0.5]], [[0.5, 0.5], [0.5, 0.5]]]
    C_data = [0.5, 0.5]
    D_data = [0.5, 0.5]
    E_data = [0.25, 0.75]

    # Full parsed spec, with matrices merged into initialparameterization.
    gnn_spec = {
    "name": "FepLean Symmetric Boolean Generative Model",
    "model_name": "FepLean Symmetric Boolean Generative Model",
    "description": "Bridge P1 spike: the fep_lean active_inference.lean\nGenerativeModel instance `symmetricBoolModel trueBiasedPolicyPrior`\n(two policies, two hidden states, two observations, one step)\nprojected deterministically to GNN v1 syntax.\nExtraction record (file:line in the fep_lean checkout at the\ncommit recorded under Signature):\n- D initialState = fairBoolLaw (1/2, 1/2)\n[def active_inference.lean:719-722; use :745]\n- B transition = fairBoolKernel, policy-indexed, all entries 1/2\n[def active_inference.lean:725-728; use :746]\n- A likelihood = fairBoolKernel, all entries 1/2\n[def active_inference.lean:725-728; use :747]\n- C preferences = fairBoolLaw (1/2, 1/2)\n[def active_inference.lean:719-722; use :748]\n- E policyPrior = trueBiasedPolicyPrior: E(False)=1/4, E(True)=3/4\n[def active_inference.lean:731-734; parameter :743,:749]\n- Timescale: one transition application [active_inference.lean:30-32]\n- The Lean GenerativeModel carries no Action type, so no `u`\nvariable or action edges are emitted.",
    "gnn_section": "FepLeanSymmetricBool",
    "model_parameters": {
        "num_hidden_states": 2,
        "num_obs": 2,
        "num_actions": 2,
        "num_timesteps": 1,
        "b_tensor_order": "next_state_previous_state_action",
        "num_state_factors": 2,
        "num_modalities": 1,
        "state_factors": [
            {
                "name": "s",
                "size": 2,
                "dimensions": [
                    2,
                    1
                ],
                "type": "float",
                "comment": "initialState distribution",
                "index": 0,
                "role": "factor"
            },
            {
                "name": "s_prime",
                "size": 2,
                "dimensions": [
                    2,
                    1
                ],
                "type": "float",
                "comment": "predictedState (one-step)",
                "index": 1,
                "role": "bookkeeping"
            }
        ],
        "observation_modalities": [
            {
                "name": "o",
                "size": 2,
                "dimensions": [
                    2,
                    1
                ],
                "type": "float",
                "comment": "predictedOutcome distribution",
                "index": 0,
                "role": "factor"
            }
        ],
        "control_factors": [
            {
                "name": "\u03c0",
                "size": 2,
                "dimensions": [
                    2
                ],
                "type": "float",
                "comment": "policy prior / posterior over policies",
                "index": 0,
                "role": "bookkeeping"
            }
        ],
        "passive_model": False,
        "simulation_params": {}
    },
    "initialparameterization": {
        "A": [
            [
                0.5,
                0.5
            ],
            [
                0.5,
                0.5
            ]
        ],
        "B": [
            [
                [
                    0.5,
                    0.5
                ],
                [
                    0.5,
                    0.5
                ]
            ],
            [
                [
                    0.5,
                    0.5
                ],
                [
                    0.5,
                    0.5
                ]
            ]
        ],
        "C": [
            0.5,
            0.5
        ],
        "D": [
            0.5,
            0.5
        ],
        "E": [
            0.25,
            0.75
        ]
    },
    "structured_pomdp": {
        "matrices": {
            "A": [
                [
                    0.5,
                    0.5
                ],
                [
                    0.5,
                    0.5
                ]
            ],
            "B": [
                [
                    [
                        0.5,
                        0.5
                    ],
                    [
                        0.5,
                        0.5
                    ]
                ],
                [
                    [
                        0.5,
                        0.5
                    ],
                    [
                        0.5,
                        0.5
                    ]
                ]
            ],
            "C": [
                0.5,
                0.5
            ],
            "D": [
                0.5,
                0.5
            ],
            "E": [
                0.25,
                0.75
            ]
        },
        "matrix_provenance": {
            "A": {
                "source": "InitialParameterization",
                "shape": [
                    2,
                    2
                ],
                "derived": False
            },
            "B": {
                "source": "InitialParameterization",
                "shape": [
                    2,
                    2,
                    2
                ],
                "derived": False,
                "declared_order": [
                    "next_state",
                    "previous_state",
                    "action"
                ],
                "declared_order_explicit": False,
                "claimed_slice_convention": None,
                "detected_order": None,
                "canonical_order": "next_state_previous_state_action",
                "contradiction": False,
                "reason": None,
                "source_order": "next_state_previous_state_action"
            },
            "C": {
                "source": "InitialParameterization",
                "shape": [
                    2
                ],
                "derived": False
            },
            "D": {
                "source": "InitialParameterization",
                "shape": [
                    2
                ],
                "derived": False
            },
            "E": {
                "source": "InitialParameterization",
                "shape": [
                    2
                ],
                "derived": False
            }
        },
        "state_factors": [
            {
                "name": "s",
                "size": 2,
                "dimensions": [
                    2,
                    1
                ],
                "type": "float",
                "comment": "initialState distribution",
                "index": 0,
                "role": "factor"
            },
            {
                "name": "s_prime",
                "size": 2,
                "dimensions": [
                    2,
                    1
                ],
                "type": "float",
                "comment": "predictedState (one-step)",
                "index": 1,
                "role": "bookkeeping"
            }
        ],
        "observation_modalities": [
            {
                "name": "o",
                "size": 2,
                "dimensions": [
                    2,
                    1
                ],
                "type": "float",
                "comment": "predictedOutcome distribution",
                "index": 0,
                "role": "factor"
            }
        ],
        "control_factors": [
            {
                "name": "\u03c0",
                "size": 2,
                "dimensions": [
                    2
                ],
                "type": "float",
                "comment": "policy prior / posterior over policies",
                "index": 0,
                "role": "bookkeeping"
            }
        ],
        "adapter_notes": [],
        "canonical_b_order": "next_state_previous_state_action"
    },
    "matrix_provenance": {
        "A": {
            "source": "InitialParameterization",
            "shape": [
                2,
                2
            ],
            "derived": False
        },
        "B": {
            "source": "InitialParameterization",
            "shape": [
                2,
                2,
                2
            ],
            "derived": False,
            "declared_order": [
                "next_state",
                "previous_state",
                "action"
            ],
            "declared_order_explicit": False,
            "claimed_slice_convention": None,
            "detected_order": None,
            "canonical_order": "next_state_previous_state_action",
            "contradiction": False,
            "reason": None,
            "source_order": "next_state_previous_state_action"
        },
        "C": {
            "source": "InitialParameterization",
            "shape": [
                2
            ],
            "derived": False
        },
        "D": {
            "source": "InitialParameterization",
            "shape": [
                2
            ],
            "derived": False
        },
        "E": {
            "source": "InitialParameterization",
            "shape": [
                2
            ],
            "derived": False
        }
    },
    "canonical_pomdp_schema": "canonical_pomdp_v1",
    "variables": [
        {
            "name": "s",
            "dimensions": [
                2,
                1
            ],
            "type": "float",
            "comment": "initialState distribution"
        },
        {
            "name": "s_prime",
            "dimensions": [
                2,
                1
            ],
            "type": "float",
            "comment": "predictedState (one-step)"
        },
        {
            "name": "t",
            "dimensions": [
                1
            ],
            "type": "float",
            "comment": "discrete time step (one-step model)"
        },
        {
            "name": "o",
            "dimensions": [
                2,
                1
            ],
            "type": "float",
            "comment": "predictedOutcome distribution"
        },
        {
            "name": "\u03c0",
            "dimensions": [
                2
            ],
            "type": "float",
            "comment": "policy prior / posterior over policies"
        }
    ],
    "connections": [
        {
            "source": "D",
            "relation": ">",
            "target": "s"
        },
        {
            "source": "s",
            "relation": "-",
            "target": "B"
        },
        {
            "source": "B",
            "relation": ">",
            "target": "s_prime"
        },
        {
            "source": "s_prime",
            "relation": "-",
            "target": "A"
        },
        {
            "source": "A",
            "relation": "-",
            "target": "o"
        },
        {
            "source": "E",
            "relation": ">",
            "target": "\u03c0"
        },
        {
            "source": "\u03c0",
            "relation": "-",
            "target": "B"
        },
        {
            "source": "C",
            "relation": ">",
            "target": "G"
        },
        {
            "source": "G",
            "relation": ">",
            "target": "\u03c0"
        }
    ],
    "ontology_mapping": {
        "A": "LikelihoodMatrix",
        "B": "TransitionMatrix",
        "C": "Preferences",
        "D": "PriorOverHiddenStates",
        "E": "Habit",
        "F": "VariationalFreeEnergy",
        "G": "ExpectedFreeEnergy",
        "s": "HiddenState",
        "s_prime": "NextHiddenState",
        "o": "Observation",
        "\u03c0": "PolicyVector",
        "t": "Time"
    },
    "initial_parameterization": {
        "A": [
            [
                0.5,
                0.5
            ],
            [
                0.5,
                0.5
            ]
        ],
        "B": [
            [
                [
                    0.5,
                    0.5
                ],
                [
                    0.5,
                    0.5
                ]
            ],
            [
                [
                    0.5,
                    0.5
                ],
                [
                    0.5,
                    0.5
                ]
            ]
        ],
        "C": [
            0.5,
            0.5
        ],
        "D": [
            0.5,
            0.5
        ],
        "E": [
            0.25,
            0.75
        ]
    }
}
    gnn_spec.setdefault("initialparameterization", {})
    if A_data is not None: gnn_spec["initialparameterization"]["A"] = A_data
    if B_data is not None: gnn_spec["initialparameterization"]["B"] = B_data
    if C_data is not None: gnn_spec["initialparameterization"]["C"] = C_data
    if D_data is not None: gnn_spec["initialparameterization"]["D"] = D_data
    if E_data is not None: gnn_spec["initialparameterization"]["E"] = E_data
    gnn_spec.setdefault("model_parameters", {})
    gnn_spec["model_parameters"].setdefault("num_timesteps", 1)

    output_dir = Path(os.environ.get("PYMDP_OUTPUT_DIR", "output/pymdp_simulations/FepLean Symmetric Boolean Generative Model"))
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Running pymdp 1.0.0 rollout for FepLean Symmetric Boolean Generative Model")
    logger.info("Output directory: %s", output_dir)

    try:
        success, results = execute_pymdp_simulation(
            gnn_spec=gnn_spec,
            output_dir=output_dir,
            correlation_id="render_generated_script",
        )
    except Exception as exc:  # noqa: BLE001
        import traceback
        logger.error("Unexpected error: %s", exc)
        traceback.print_exc()
        return 1

    if success:
        logger.info("Simulation completed successfully")
        logger.info("  framework:    %s", results.get("framework"))
        logger.info("  pymdp ver:    %s", results.get("pymdp_version"))
        logger.info("  backend:      %s", results.get("backend"))
        logger.info("  num_timesteps:%s", results.get("num_timesteps"))
        return 0

    logger.error("Simulation failed: %s", results.get("error", "Unknown error"))
    return 1


if __name__ == "__main__":
    sys.exit(main())
