"""Independent v3 replay controls; numerical fixtures are reported data only."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from copy import deepcopy
from pathlib import Path

import numpy as np
import pytest

SPEC = importlib.util.spec_from_file_location(
    "fep_product_audit", Path(__file__).with_name("audit_composition.py")
)
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)
ROOT = Path(__file__).resolve().parents[2]
BLOCKS = {
    "agent1": {
        "F": [[0.8]],
        "H": [[2.0], [-1.0]],
        "Q": [[0.07]],
        "R": [[0.3, 0.02], [0.02, 0.4]],
        "prior_mean": [0.4],
        "prior_cov": [[1.2]],
    },
    "agent2": {
        "F": [[0.7, 0.2], [-0.1, 0.9]],
        "H": [[1.3, -0.4]],
        "Q": [[0.12, 0.01], [0.01, 0.09]],
        "R": [[0.25]],
        "prior_mean": [-0.3, 0.8],
        "prior_cov": [[1.0, 0.2], [0.2, 0.7]],
    },
}
OBS = {
    "agent1": [[1.1, -0.2], [0.9, -0.6], [1.5, -0.1]],
    "agent2": [[0.2], [-0.1], [0.8]],
}


def source_bytes(blocks=None, *, count=3):
    blocks = BLOCKS if blocks is None else blocks
    labels = {
        key: {
            a: [f"{key}{i}" for i in range(len(blocks[a][matrix]))]
            for a in audit.AGENTS
        }
        for key, matrix in (("state_ids", "F"), ("observation_ids", "H"))
    }
    declaration = {
        "schema": audit.SOURCE_SCHEMA,
        "model": "gaussian_product",
        "question": "filtering",
        "dtype": "float64",
        "initial_time": "first_observation_uses_prior",
        "axes": audit.AXES,
        "agents": list(audit.AGENTS),
        **labels,
    }
    sections = {
        "ModelName": "FEP asymmetric product fixture",
        "GNNSection": "ActInfContinuousMultiAgent",
        "StateSpaceBlock": "\n".join(
            f"x_{a}[{len(blocks[a]['F'])},1,type=float]\ny_{a}[{len(blocks[a]['H'])},1,type=float]"
            for a in audit.AGENTS
        ),
        "InitialParameterization": "\n".join(
            f"{k}_{a} = {json.dumps(v)}"
            for a in audit.AGENTS
            for k, v in blocks[a].items()
        ),
        "ModelParameters": f"nr_agents: 2\nagent_coupling: independent\nnum_timesteps: {count}\nrandom_seed_agent1: 7\nrandom_seed_agent2: 19",
        "Equations": audit.product_equations(),
        "NumericalWitness": json.dumps(declaration),
    }
    return "\n\n".join(f"## {k}\n{v}" for k, v in sections.items()).encode()


def joint_prefix_oracle(parameters, observations):
    """Test-only whole-trajectory conditioning, not the replay's recursion."""
    p = {k: np.asarray(v, dtype=float) for k, v in parameters.items()}
    f, h, q, r, mu, prior = (p[k] for k in audit.PARAMETERS)
    t, n = len(observations), len(mu)
    # Explicit covariance Cov(x_i,x_j) from independent innovation sources.
    cov = np.empty((t * n, t * n))
    means = np.array([np.linalg.matrix_power(f, i) @ mu for i in range(t)])
    for i in range(t):
        for j in range(t):
            value = (
                np.linalg.matrix_power(f, i) @ prior @ np.linalg.matrix_power(f, j).T
            )
            for k in range(1, min(i, j) + 1):
                value += (
                    np.linalg.matrix_power(f, i - k)
                    @ q
                    @ np.linalg.matrix_power(f, j - k).T
                )
            cov[i * n : (i + 1) * n, j * n : (j + 1) * n] = value
    post_means, post_cov = [], []
    for i in range(t):
        obs_map = np.kron(np.eye(i + 1), h)
        state_obs = cov[i * n : (i + 1) * n, : (i + 1) * n] @ obs_map.T
        obs_cov = obs_map @ cov[: (i + 1) * n, : (i + 1) * n] @ obs_map.T + np.kron(
            np.eye(i + 1), r
        )
        gain = state_obs @ np.linalg.inv(obs_cov)
        post_means.append(
            (
                means[i]
                + gain
                @ (
                    np.asarray(observations[: i + 1]).reshape(-1)
                    - obs_map @ means[: i + 1].reshape(-1)
                )
            ).tolist()
        )
        post_cov.append(
            (
                cov[i * n : (i + 1) * n, i * n : (i + 1) * n] - gain @ state_obs.T
            ).tolist()
        )
    return {"beliefs": post_means, "posterior_cov": post_cov}


def artifact(raw):
    return {"sha256": hashlib.sha256(raw).hexdigest(), "utf8": raw.decode()}


def reported_witness(
    blocks=None, observations=None, *, program=b"reported only", count=3
):
    blocks, observations = (
        deepcopy(BLOCKS if blocks is None else blocks),
        deepcopy(OBS if observations is None else observations),
    )
    raw_source = source_bytes(blocks, count=count)
    contract = audit.read_product_source(raw_source.decode())
    children, components = {}, {}
    joint_mean = np.zeros((count, len(contract["state_ids"])))
    joint_cov = np.zeros(
        (count, len(contract["state_ids"]), len(contract["state_ids"]))
    )
    start = 0
    for a in audit.AGENTS:
        component = contract["components"][a]
        values = joint_prefix_oracle(blocks[a], observations[a])
        child = {
            **audit.seam._semantic_identities(component),
            "model_kind": "continuous",
            "schema_version": "gnn_lgssm_filter_v1",
            "framework": "jax",
            "parameters": blocks[a],
            "observations_continuous": observations[a],
            "controls": np.zeros((count, len(component["state_ids"]))).tolist(),
            "validation": {"all_valid": True, "means_finite": True},
            **values,
        }
        if program is not None:
            child["generated_script_sha256"] = hashlib.sha256(program).hexdigest()
        children[a] = child
        components[a] = {
            "observations": observations[a],
            "quantities": values,
            "state_ids": component["state_ids"],
            "observation_ids": component["observation_ids"],
        }
        end = start + len(component["state_ids"])
        joint_mean[:, start:end], joint_cov[:, start:end, start:end] = (
            values["beliefs"],
            values["posterior_cov"],
        )
        start = end
    result = {
        "schema_version": "gnn_multi_agent_continuous_v1",
        "model_kind": "multi_agent_continuous",
        "framework": "jax",
        "agents": list(audit.AGENTS),
        "agent_coupling": "independent",
        "num_timesteps": count,
        "agent_results": children,
        "validation": {"all_valid": True},
    }
    for key in ("beliefs", "posterior_cov", "controls", "observations_continuous"):
        result[key + "_by_agent"] = {
            a: deepcopy(children[a][key]) for a in audit.AGENTS
        }
    reference = {
        "algorithm": "joint_block_diagonal_gaussian_prefix_conditioning",
        "conditioning_horizon": list(range(1, count + 1)),
        "observations": np.concatenate(
            [observations[a] for a in audit.AGENTS], axis=1
        ).tolist(),
        "quantities": {
            "beliefs": joint_mean.tolist(),
            "posterior_cov": joint_cov.tolist(),
        },
        "components": components,
        "cross_agent_covariance": audit.CROSS,
    }
    artifacts = {
        "source": artifact(raw_source),
        "result": artifact(json.dumps(result).encode()),
        "program": artifact(program) if program is not None else None,
    }
    return {
        "schema": "gnn-semantic-witness-v3",
        "status": "passed",
        "source_contract": contract,
        "reference": reference,
        "candidate": {"agents": list(audit.AGENTS), "components": deepcopy(children)},
        "comparisons": audit.comparison_rows(
            contract, result, reference, artifacts["program"]
        ),
        "assumptions": {
            "question": "filtering",
            "agent_coupling": "independent",
            "control_mode": "passive",
            "initial_time": "first_observation_uses_prior",
            "conditioning_horizon": list(range(1, count + 1)),
            "state_ids": contract["state_ids"],
            "observation_ids": contract["observation_ids"],
            "axes": audit.AXES,
            "label_mapping": "Source labels name ordered numeric axes; native label provenance is not authenticated.",
            "scope": audit.SCOPE,
        },
        "artifacts": artifacts,
        "formal_evidence": {"status": "unavailable", "universal_equivalence": False},
        "execution_evidence": {
            "status": "artifact_only",
            "execution_source_verified": False,
            "reported_framework": "jax",
        },
    }


def test_asymmetric_replay_matches_joint_conditioning_without_execution_claim():
    witness = reported_witness()
    result = audit.audit_composition(witness, ROOT)
    assert result["status"] == "passed", result["errors"]
    assert len(result["independent_replay"]["comparisons"]) == 10
    assert result["formal_evidence"]["native_claim_ready"] is False
    assert result["execution_evidence"]["execution_source_verified"] is False
    assert np.any(
        np.asarray(
            witness["reference"]["components"]["agent2"]["quantities"]["posterior_cov"]
        )[:, 0, 1]
        != 0
    )


@pytest.mark.parametrize("program", [None, b"reported only"])
def test_optional_program_is_custody_only(program):
    assert (
        audit.audit_composition(reported_witness(program=program), ROOT)["status"]
        == "passed"
    )


def test_permutation_and_future_observations_preserve_filtering_boundaries():
    first = reported_witness()
    changed_obs = deepcopy(OBS)
    changed_obs["agent2"][-1][0] += 20
    second = reported_witness(observations=changed_obs)
    a, b = (audit.audit_composition(x, ROOT) for x in (first, second))
    assert a["status"] == b["status"] == "passed"
    np.testing.assert_array_equal(
        a["independent_replay"]["components"]["agent1"]["beliefs"],
        b["independent_replay"]["components"]["agent1"]["beliefs"],
    )
    np.testing.assert_array_equal(
        a["independent_replay"]["components"]["agent2"]["beliefs"][:-1],
        b["independent_replay"]["components"]["agent2"]["beliefs"][:-1],
    )
    swapped = reported_witness(
        {"agent1": BLOCKS["agent2"], "agent2": BLOCKS["agent1"]},
        {"agent1": OBS["agent2"], "agent2": OBS["agent1"]},
    )
    c = audit.audit_composition(swapped, ROOT)
    assert c["status"] == "passed"
    np.testing.assert_allclose(
        a["independent_replay"]["components"]["agent1"]["beliefs"],
        c["independent_replay"]["components"]["agent2"]["beliefs"],
    )


@pytest.mark.parametrize(
    "old,new",
    [
        ("agent_coupling: independent", "agent_coupling: coupled"),
        ("num_timesteps: 3", "num_timesteps: 9"),
        ("random_seed_agent1: 7", "random_seed_agent1: true"),
        ('"dtype": "float64"', '"dtype": "float32"'),
        ('"question": "filtering"', '"question": "smoothing"'),
        ("F_agent1 = [[0.8]]", "F_agent1 = [[true]]"),
        ("Q_agent1 = [[0.07]]", "Q_agent1 = [[-0.07]]"),
        ("F_agent1 = ", "F_agent1 = [[0.8]]\nF_agent1 = "),
        ("Q_agent1 = [[0.07]]\n", ""),
        ("F_agent1 = ", "Q_shared = [[1.0]]\nF_agent1 = "),
        ("F_agent1 = ", "goal_mean_agent1 = [0.0]\nF_agent1 = "),
        ("F_agent1*x_agent1_t", "F_agent1*x_agent2_t"),
        ("## Equations", "## Coupling\nshared = 1\n\n## Equations"),
    ],
)
def test_unsupported_source_refuses_before_replay(old, new):
    source = source_bytes().decode()
    assert old in source
    with pytest.raises(ValueError):
        audit.read_product_source(source.replace(old, new))


@pytest.mark.parametrize(
    "change",
    [
        "source_hash",
        "raw_result",
        "reference",
        "boolean_horizon",
        "cross",
        "candidate",
        "verdict",
        "rows",
        "proof",
        "execution",
        "assumptions",
        "v2",
        "extra_field",
    ],
)
def test_saved_witness_tampering_is_not_accepted(change):
    witness = reported_witness()
    if change == "source_hash":
        witness["artifacts"]["source"]["sha256"] = "0" * 64
    elif change == "raw_result":
        witness["artifacts"]["result"]["utf8"] += " "
    elif change == "boolean_horizon":
        witness["reference"]["conditioning_horizon"][0] = True
    elif change == "reference":
        witness["reference"]["quantities"]["beliefs"][0][0] += 0.2
    elif change == "cross":
        witness["reference"]["quantities"]["posterior_cov"][0][0][1] = 0.1
    elif change == "candidate":
        witness["candidate"]["components"]["agent1"]["beliefs"][0][0] += 0.2
    elif change == "verdict":
        witness["status"] = "failed"
    elif change == "rows":
        witness["comparisons"].pop(next(iter(witness["comparisons"])))
    elif change == "proof":
        witness["formal_evidence"]["status"] = "compiled"
    elif change == "execution":
        witness["execution_evidence"]["execution_source_verified"] = True
    elif change == "assumptions":
        witness["assumptions"]["control_mode"] = "active"
    elif change == "v2":
        witness["schema"] = "gnn-semantic-witness-v2"
    else:
        witness["extra"] = 1
    assert audit.audit_composition(witness, ROOT)["status"] == "refused"


@pytest.mark.parametrize(
    "change",
    [
        "seed",
        "precision",
        "framework",
        "source",
        "nested_failure",
        "parameter",
        "missing",
        "extra_agent",
        "projection",
        "observation",
        "covariance",
        "program",
    ],
)
def test_rehashed_native_mutations_cannot_borrow_agreeing_numbers(change):
    witness = reported_witness()
    result = json.loads(witness["artifacts"]["result"]["utf8"])
    child = result["agent_results"]["agent2"]
    if change == "seed":
        child["random_seed"] = True
    elif change == "precision":
        child["dtype"] = "float32"
    elif change == "framework":
        child["framework"] = "pytorch"
    elif change == "source":
        child["source_sha256"] = "0" * 64
    elif change == "nested_failure":
        child["validation"]["hidden"] = {"passed": False}
    elif change == "parameter":
        child["parameters"]["F"][0][1] += 0.2
    elif change == "missing":
        del child["conditioning_horizon"]
    elif change == "extra_agent":
        result["agent_results"]["agent3"] = deepcopy(child)
    elif change == "projection":
        result["beliefs_by_agent"]["agent2"][0][0] += 0.2
    elif change == "observation":
        child["observations_continuous"][0][0] += 0.2
    elif change == "covariance":
        child["posterior_cov"][0][0][1] += 0.1
    else:
        child["generated_script_sha256"] = "0" * 64
    witness["artifacts"]["result"] = artifact(json.dumps(result).encode())
    assert audit.audit_composition(witness, ROOT)["status"] == "refused"


def test_cli_preserves_input_and_refuses_receipt_overwrite(tmp_path, monkeypatch):
    witness, receipt = tmp_path / "input.json", tmp_path / "audit.json"
    witness.write_text(json.dumps(reported_witness()))
    before = witness.read_bytes()
    monkeypatch.setattr(
        "sys.argv", ["audit", "--witness", str(witness), "--receipt", str(receipt)]
    )
    assert audit.main() == 0
    assert witness.read_bytes() == before
    assert json.loads(receipt.read_bytes())["input_bookends_equal"] is True
    with pytest.raises(SystemExit):
        audit.main()


@pytest.mark.parametrize("text", ['{"duplicate":1,"duplicate":2}', '{"bad":NaN}'])
def test_duplicate_and_nonfinite_json_are_refused(text):
    with pytest.raises(ValueError):
        audit.seam._semantic_json(text)
