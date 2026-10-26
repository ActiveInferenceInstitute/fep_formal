"""Independently audit the bounded GNN v3 Gaussian product witness, offline."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

import numpy as np

from fep_lean.bridge import certificates as seam

AGENTS = ("agent1", "agent2")
SOURCE_SCHEMA = "gnn-independent-gaussian-composition-v1"
AXES = {"F": ["next_state", "previous_state"], "H": ["observation", "state"]}
PARAMETERS = ("F", "H", "Q", "R", "prior_mean", "prior_cov")
SCOPE = (
    "Exactly two independent passive stationary Gaussian agents; float64; at most "
    "eight times and four total state/observation axes; no coupling, shared noise, "
    "control, smoothing or universal equivalence."
)
CROSS = "zero_by_declared_product_model; not a measured native quantity"


def _require(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError(reason)


def product_equations() -> str:
    """State the admitted authored independence, without inferring it from shape."""
    equations = [
        "p(x_agent1,x_agent2,y_agent1,y_agent2)=p(x_agent1,y_agent1)*p(x_agent2,y_agent2)"
    ]
    for agent in AGENTS:
        equations += [
            f"x_{agent}_0~N(prior_mean_{agent},prior_cov_{agent})",
            f"x_{agent}_(t+1)=F_{agent}*x_{agent}_t+N(0,Q_{agent})",
            f"y_{agent}_t=H_{agent}*x_{agent}_t+N(0,R_{agent})",
        ]
    return "; ".join(equations)


def read_product_source(source: str) -> dict[str, Any]:
    """Read raw authored blocks, then apply FEP's existing single-agent admission.

    The component text is constructed from these independently parsed source
    assignments, never from the GNN receipt's extracted parameters. No GNN
    parser, renderer, witness implementation or backend is imported.
    """
    _require(len(source.encode()) <= 1024 * 1024, "source byte budget exceeded")
    required = {
        "ModelName",
        "GNNSection",
        "StateSpaceBlock",
        "InitialParameterization",
        "ModelParameters",
        "Equations",
        "NumericalWitness",
    }
    text = source.replace("\r\n", "\n")
    for line in text.splitlines():
        if re.match(r"^[ \t]*##(?!#)", line):
            heading = re.fullmatch(r"## ([A-Za-z]+)[ \t]*", line)
            _require(
                heading is not None and heading[1] in required,
                "unsupported or malformed product source heading",
            )
    parts = re.split(r"(?m)^## ([A-Za-z]+)\s*\n", text)
    sections: dict[str, str] = {}
    for index in range(1, len(parts), 2):
        name = parts[index]
        _require(name not in sections, "duplicate product source section")
        sections[name] = parts[index + 1].strip()
    _require(set(sections) == required, "incomplete product source envelope")
    declaration = seam._semantic_json(sections["NumericalWitness"])
    fields = {
        "schema",
        "model",
        "question",
        "dtype",
        "initial_time",
        "axes",
        "agents",
        "state_ids",
        "observation_ids",
    }
    _require(
        isinstance(declaration, dict) and set(declaration) == fields,
        "unsupported product declaration fields",
    )
    expected = {
        "schema": SOURCE_SCHEMA,
        "model": "gaussian_product",
        "question": "filtering",
        "dtype": "float64",
        "initial_time": "first_observation_uses_prior",
        "axes": AXES,
        "agents": list(AGENTS),
    }
    for key, value in expected.items():
        _require(
            seam._semantic_equal(declaration[key], value),
            f"unsupported product declaration: {key}",
        )
    labels = {}
    for name in ("state_ids", "observation_ids"):
        mapping = declaration[name]
        _require(
            isinstance(mapping, dict) and set(mapping) == set(AGENTS),
            f"exact product agent labels required: {name}",
        )
        for values in mapping.values():
            _require(
                isinstance(values, list)
                and 1 <= len(values) <= 3
                and all(isinstance(v, str) and 1 <= len(v) <= 256 for v in values)
                and len(set(values)) == len(values),
                "invalid ordered agent labels",
            )
        _require(sum(map(len, mapping.values())) <= 4, "product axis budget exceeded")
        labels[name] = mapping
    parsed = {}
    for section, separator in (
        ("InitialParameterization", " = "),
        ("ModelParameters", ": "),
    ):
        values = {}
        for line in sections[section].splitlines():
            if not line.strip():
                continue
            match = re.fullmatch(
                r"([A-Za-z_][A-Za-z_0-9]*)" + separator + r"(.+)", line
            )
            _require(match is not None, "one exact JSON assignment per line required")
            key, literal = match.groups()
            _require(key not in values, f"duplicate product parameter: {key}")
            values[key] = (
                literal if key == "agent_coupling" else seam._semantic_json(literal)
            )
        parsed[section] = values
    options, parameters = parsed["ModelParameters"], parsed["InitialParameterization"]
    _require(
        set(options)
        == {
            "nr_agents",
            "agent_coupling",
            "num_timesteps",
            "random_seed_agent1",
            "random_seed_agent2",
        },
        "unsupported product model options",
    )
    _require(
        type(options["nr_agents"]) is int
        and options["nr_agents"] == 2
        and options["agent_coupling"] == "independent",
        "explicit independent pair required",
    )
    _require(
        type(options["num_timesteps"]) is int and 1 <= options["num_timesteps"] <= 8,
        "product horizon budget exceeded",
    )
    _require(
        set(parameters) == {f"{key}_{agent}" for agent in AGENTS for key in PARAMETERS},
        "complete passive parameter blocks required; shared/control/extra blocks forbidden",
    )
    _require(
        sections["GNNSection"] == "ActInfContinuousMultiAgent"
        and sections["Equations"] == product_equations(),
        "unsupported product equations",
    )
    variables, components = [], {}
    digest = hashlib.sha256(source.encode()).hexdigest()
    for agent in AGENTS:
        seed = options[f"random_seed_{agent}"]
        _require(type(seed) is int and 0 <= seed <= 2**32 - 1, "invalid agent seed")
        states, observed = labels["state_ids"][agent], labels["observation_ids"][agent]
        variables += [
            f"x_{agent}[{len(states)},1,type=float]",
            f"y_{agent}[{len(observed)},1,type=float]",
        ]
        child_declaration = {
            "schema": "gnn-independent-numerical-witness-v1",
            "model": "gaussian",
            "question": "filtering",
            "dtype": "float64",
            "axes": AXES,
            "initial_time": "first_observation_uses_prior",
            "state_ids": states,
            "observation_ids": observed,
        }
        child_sections = {
            "ModelName": agent,
            "GNNSection": "ActInfContinuous",
            "StateSpaceBlock": f"x[{len(states)},1,type=float]\ny[{len(observed)},1,type=float]",
            "InitialParameterization": "\n".join(
                f"{key} = {json.dumps(parameters[f'{key}_{agent}'])}"
                for key in PARAMETERS
            ),
            "ModelParameters": f"num_timesteps: {options['num_timesteps']}\nrandom_seed: {seed}",
            "Equations": "x_0~N(prior_mean,prior_cov); x_(t+1)=F*x_t+N(0,Q); y_t=H*x_t+N(0,R)",
            "NumericalWitness": json.dumps(child_declaration),
        }
        child = seam._semantic_source(
            "\n\n".join(f"## {key}\n{value}" for key, value in child_sections.items())
        )
        child.pop("equations")
        child.update(schema=SOURCE_SCHEMA, source_sha256=digest)
        components[agent] = child
    _require(
        sections["StateSpaceBlock"] == "\n".join(variables),
        "agent axis declarations disagree",
    )
    return {
        **declaration,
        **{
            name: [
                f"{agent}:{label}" for agent in AGENTS for label in labels[name][agent]
            ]
            for name in ("state_ids", "observation_ids")
        },
        "source_sha256": digest,
        "components": components,
        "parameters": parameters,
        "model_parameters": options,
        "equations": sections["Equations"],
    }


def _artifacts(witness: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], Any]:
    fields = {
        "schema",
        "status",
        "source_contract",
        "reference",
        "candidate",
        "comparisons",
        "assumptions",
        "artifacts",
        "formal_evidence",
        "execution_evidence",
    }
    _require(
        isinstance(witness, dict)
        and set(witness) == fields
        and witness["schema"] == "gnn-semantic-witness-v3",
        "exact v3 witness fields required",
    )
    artifacts = witness["artifacts"]
    _require(
        isinstance(artifacts, dict)
        and set(artifacts) == {"source", "result", "program"},
        "exact source/result/program artifact roster required",
    )
    for name, artifact in artifacts.items():
        if name == "program" and artifact is None:
            continue
        _require(
            isinstance(artifact, dict)
            and set(artifact) == {"sha256", "utf8"}
            and isinstance(artifact["utf8"], str),
            f"invalid {name} artifact",
        )
        raw = artifact["utf8"].encode()
        _require(
            len(raw) <= (1024 * 1024 if name == "source" else 16 * 1024 * 1024)
            and hashlib.sha256(raw).hexdigest() == artifact["sha256"],
            f"{name} hash or byte budget mismatch",
        )
    contract = read_product_source(artifacts["source"]["utf8"])
    _require(
        seam._semantic_equal(contract, witness["source_contract"]),
        "source contract disagrees with independent extraction",
    )
    result = seam._semantic_json(artifacts["result"]["utf8"])
    _require(isinstance(result, dict), "native result object required")
    return contract, result, artifacts["program"]


def comparison_rows(
    contract: dict[str, Any],
    result: dict[str, Any],
    reference: dict[str, Any],
    program: Any,
) -> dict[str, Any]:
    """Reconstruct v3 diagnostics from source and raw reported quantities only."""
    count = contract["model_parameters"]["num_timesteps"]
    outer = {
        "schema_version": "gnn_multi_agent_continuous_v1",
        "model_kind": "multi_agent_continuous",
        "framework": "jax",
        "agents": list(AGENTS),
        "agent_coupling": "independent",
        "num_timesteps": count,
    }
    rows = {
        f"identity:{key}": seam._semantic_identity_row(value, result.get(key))
        for key, value in outer.items()
    }
    common = {
        key: result[key]
        for key in (
            "validation",
            "status",
            "success",
            "source_sha256",
            "source_identity",
        )
        if key in result
    }
    common["framework"] = result.get("framework")
    seam._semantic_native_admission(contract["components"]["agent1"], common)
    rows.update(seam._semantic_declared_rows(contract["components"]["agent1"], common))
    rows["identity:framework"] = seam._semantic_identity_row(
        "jax", result.get("framework")
    )
    optional = {
        "dtype": "float64",
        "inference_mode": "independent_gaussian_filtering",
        "inference_contract": "gnn_independent_gaussian_filter_v1",
        "control_mode": "passive",
        "state_ids": contract["state_ids"],
        "observation_ids": contract["observation_ids"],
    }
    for key, expected in optional.items():
        if key in result:
            rows[f"identity:{key}"] = seam._semantic_identity_row(expected, result[key])
    rows["identity:validation.all_valid"] = seam._semantic_identity_row(
        True, result.get("validation", {}).get("all_valid")
    )
    records = result.get("agent_results")
    _require(
        isinstance(records, dict) and set(records) == set(AGENTS),
        "exact two native child records required",
    )
    rows["identity:agent_results"] = {"status": "passed", "reason": ""}
    for key in ("beliefs", "posterior_cov", "controls", "observations_continuous"):
        mapping = result.get(key + "_by_agent")
        _require(
            isinstance(mapping, dict) and set(mapping) == set(AGENTS),
            "exact native projection agents required",
        )
        rows[f"identity:{key}_projection_agents"] = seam._semantic_identity_row(
            list(AGENTS), sorted(mapping)
        )
    for agent in AGENTS:
        child, component = records[agent], contract["components"][agent]
        _require(isinstance(child, dict), "complete native child object required")
        seam._semantic_native_admission(component, child)
        checks = seam._semantic_expected_comparisons(
            component, child, reference["components"][agent], program
        )
        for key, expected in {
            "framework": "jax",
            "schema_version": "gnn_lgssm_filter_v1",
            "model_kind": "continuous",
        }.items():
            checks[f"identity:{key}"] = seam._semantic_identity_row(
                expected, child.get(key)
            )
        parameters = child.get("parameters")
        _require(isinstance(parameters, dict), "native parameters required")
        checks["identity:parameter_keys"] = seam._semantic_identity_row(
            sorted(component["parameters"]), sorted(parameters)
        )
        checks["identity:validation.all_valid"] = seam._semantic_identity_row(
            True, child.get("validation", {}).get("all_valid")
        )
        checks["observations"] = seam._semantic_quantity(
            reference["components"][agent]["observations"],
            child.get("observations_continuous"),
            exact=True,
        )
        for key in ("beliefs", "posterior_cov", "controls", "observations_continuous"):
            checks[f"projection:{key}"] = seam._semantic_quantity(
                child.get(key), result[key + "_by_agent"][agent], exact=True
            )
        rows.update({f"{agent}:{key}": row for key, row in checks.items()})
    _require(
        all(row["status"] == "passed" for row in rows.values()),
        "raw composition admission failed",
    )
    return rows


def audit_composition(witness: dict[str, Any], root: Path) -> dict[str, Any]:
    """Compare GNN's joint-prefix conditioning with separate FEP recursion."""
    audit: dict[str, Any] = {
        "schema": "fep-gaussian-product-witness-audit-v1",
        "status": "refused",
        "independent_replay": {
            "algorithm": "separate_agent_kalman_joseph",
            "components": {},
            "comparisons": {},
        },
        "formal_evidence": {
            "status": "referenced_not_compiled",
            "alignment": "finite_weight_algebra_only",
            "native_claim_ready": False,
            "universal_equivalence": False,
        },
        "execution_evidence": {
            "status": "artifact_only",
            "execution_source_verified": False,
        },
        "cross_agent_covariance": CROSS,
        "errors": [],
    }
    try:
        contract, result, program = _artifacts(witness)
        reference = witness["reference"]
        _require(
            isinstance(reference, dict)
            and set(reference)
            == {
                "algorithm",
                "conditioning_horizon",
                "observations",
                "quantities",
                "components",
                "cross_agent_covariance",
            },
            "exact joint reference fields required",
        )
        count = contract["model_parameters"]["num_timesteps"]
        _require(
            reference["algorithm"]
            == "joint_block_diagonal_gaussian_prefix_conditioning"
            and seam._semantic_equal(
                reference["conditioning_horizon"], list(range(1, count + 1))
            )
            and reference["cross_agent_covariance"] == CROSS,
            "reference algorithm/time/independence boundary mismatch",
        )
        observations = result.get("observations_continuous_by_agent")
        _require(
            isinstance(observations, dict) and set(observations) == set(AGENTS),
            "complete observation inventory required",
        )
        joint_observations = np.concatenate(
            [seam._semantic_array(observations[a], a) for a in AGENTS], axis=1
        ).tolist()
        _require(
            seam._semantic_equal(reference["observations"], joint_observations),
            "reference observations disagree with raw result",
        )
        quantities = reference["quantities"]
        _require(
            isinstance(quantities, dict)
            and set(quantities) == {"beliefs", "posterior_cov"},
            "exact joint quantity inventory required",
        )
        n = len(contract["state_ids"])
        means, covariance = (
            seam._semantic_array(quantities[key], key)
            for key in ("beliefs", "posterior_cov")
        )
        _require(
            means.shape == (count, n) and covariance.shape == (count, n, n),
            "joint reference dimensions disagree",
        )
        components = reference["components"]
        _require(
            isinstance(components, dict) and set(components) == set(AGENTS),
            "exact reference components required",
        )
        start = 0
        assembled_means, assembled_covariance = (
            np.zeros_like(means),
            np.zeros_like(covariance),
        )
        replay = audit["independent_replay"]
        for agent in AGENTS:
            component = contract["components"][agent]
            end = start + len(component["state_ids"])
            expected_component = {
                "observations": observations[agent],
                "state_ids": component["state_ids"],
                "observation_ids": component["observation_ids"],
                "quantities": {
                    "beliefs": means[:, start:end].tolist(),
                    "posterior_cov": covariance[:, start:end, start:end].tolist(),
                },
            }
            _require(
                seam._semantic_equal(expected_component, components[agent]),
                "reference component projection mismatch",
            )
            raw_child = result.get("agent_results", {}).get(agent)
            _require(isinstance(raw_child, dict), "native child record unavailable")
            values = seam._semantic_replay(component, raw_child)
            replay["components"][agent] = values
            assembled_means[:, start:end] = values["beliefs"]
            assembled_covariance[:, start:end, start:end] = values["posterior_cov"]
            for key, expected in values.items():
                for target, actual in (
                    ("reference", components[agent]["quantities"][key]),
                    ("candidate", raw_child.get(key)),
                ):
                    row = seam._semantic_quantity(expected, actual)
                    replay["comparisons"][f"{agent}:{target}:{key}"] = row
                    _require(
                        row["status"] == "passed",
                        f"independent {agent}:{target}:{key} disagreement",
                    )
            start = end
        for key, expected in (
            ("beliefs", assembled_means.tolist()),
            ("posterior_cov", assembled_covariance.tolist()),
        ):
            row = seam._semantic_quantity(expected, quantities[key])
            replay["comparisons"][f"joint_reference:{key}"] = row
            _require(row["status"] == "passed", f"independent joint {key} disagreement")
        # Off-diagonal zero belongs to the declared reference; no native joint quantity is supplied.
        split = len(contract["components"]["agent1"]["state_ids"])
        _require(
            np.all(covariance[:, :split, split:] == 0)
            and np.all(covariance[:, split:, :split] == 0),
            "declared product reference has nonzero cross-agent covariance",
        )
        _require(
            seam._semantic_equal(
                witness["candidate"],
                {"agents": list(AGENTS), "components": result["agent_results"]},
            ),
            "candidate inventory differs from raw children",
        )
        expected_rows = comparison_rows(contract, result, reference, program)
        _require(
            seam._semantic_equal(expected_rows, witness["comparisons"]),
            "comparison roster/content differs from raw replay",
        )
        assumptions = {
            "question": "filtering",
            "agent_coupling": "independent",
            "control_mode": "passive",
            "initial_time": "first_observation_uses_prior",
            "conditioning_horizon": list(range(1, count + 1)),
            "state_ids": contract["state_ids"],
            "observation_ids": contract["observation_ids"],
            "axes": AXES,
            "label_mapping": "Source labels name ordered numeric axes; native label provenance is not authenticated.",
            "scope": SCOPE,
        }
        _require(
            seam._semantic_equal(witness["assumptions"], assumptions),
            "composition assumption boundary mismatch",
        )
        _require(
            seam._semantic_equal(
                witness["formal_evidence"],
                {"status": "unavailable", "universal_equivalence": False},
            )
            and seam._semantic_equal(
                witness["execution_evidence"],
                {
                    "status": "artifact_only",
                    "execution_source_verified": False,
                    "reported_framework": result["framework"],
                },
            ),
            "proof/execution evidence was promoted",
        )
        _require(witness["status"] == "passed", "GNN numerical admission did not pass")
        law = root / "specs/gnn-semantic-witness-v1/composition_laws.lean"
        audit["formal_evidence"].update(
            source_path=law.relative_to(root).as_posix(),
            source_sha256=hashlib.sha256(law.read_bytes()).hexdigest(),
            scope="Finite nonnegative weight products with explicit positive marginal masses; not a Gaussian measure/kernel or matrix-conditioning proof.",
        )
        audit.update(status="passed", source_sha256=contract["source_sha256"])
    except (
        ValueError,
        TypeError,
        KeyError,
        AttributeError,
        OSError,
        OverflowError,
        FloatingPointError,
        np.linalg.LinAlgError,
        RecursionError,
    ) as exc:
        audit["errors"].append(str(exc))
    return audit


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--witness", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    if args.receipt.exists():
        parser.error("receipt exists; choose a fresh path")
    raw = args.witness.read_bytes()
    if len(raw) > 64 * 1024 * 1024:
        parser.error("witness byte budget exceeded")
    witness = seam._semantic_json(raw.decode())
    root = Path(__file__).resolve().parents[2]
    audit = audit_composition(witness, root)
    audit["input"] = {
        "path": str(args.witness.resolve()),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }
    audit["input_bookends_equal"] = args.witness.read_bytes() == raw
    if not audit["input_bookends_equal"]:
        audit["status"] = "refused"
        audit["errors"].append("input changed during replay")
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(audit, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"status": audit["status"], "receipt": str(args.receipt)}))
    return 0 if audit["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
