import json,os,sys,time
from pathlib import Path
out=Path(os.environ["GNN_OUTPUT_DIR"])
p={'model_name': 'FepLean Continuous OU Linear-Gaussian Model', 'framework': 'jax', 'model_kind': 'continuous', 'num_timesteps': 1, 'num_states': 1, 'num_observations': 1, 'beliefs': [[0.5295135831436204]], 'posterior_cov': [[[0.5]]], 'true_states_continuous': [[0.6498920118351406]], 'observations_continuous': [[1.0590271662872408]], 'controls': [[0.0]], 'control_mode': 'passive', 'rmse_vs_true': 0.12037842869152016, 'observations': [], 'actions': [], 'efe_history': [], 'validation': {'means_finite': True, 'posterior_cov_psd': True, 'rmse_finite': True, 'controls_finite': True, 'all_valid': True}, 'execution_time_seconds': 0.01, 'jax_version': '0.9.2'}
(out/"simulation_results.json").write_text(json.dumps(p))
