"""The bridge's read-only checks fail closed on drift and invalid evidence."""

from __future__ import annotations

import hashlib
import json
import subprocess
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from fep_formal.bridge import operations
from fep_formal.bridge.certificates import compare
from fep_formal.bridge.custody import (
    CONTENT_DRIFT,
    FRESH,
    STALE_CUSTODY,
    classify_document,
    fingerprint,
    refresh_signature,
    validate_binding,
    write_json,
)


def _semantic_fixture(family: str) -> dict[str, Any]:
    """Small authored rational examples with independent closed-form answers."""
    from fep_formal.bridge.certificates import _semantic_quantity

    finite = family == "finite"
    parameters = (
        {
            "A": [[0.8, 0.2], [0.2, 0.8]],
            "B": [[[0.9], [0.3]], [[0.1], [0.7]]],
            "C": [0, 0],
            "D": [0.6, 0.4],
        }
        if finite
        else {
            "F": [[0.7]],
            "H": [[1.0]],
            "Q": [[0.2]],
            "R": [[0.5]],
            "prior_mean": [0.0],
            "prior_cov": [[1.0]],
        }
    )
    axes = (
        {"A": ["observation", "state"], "B": ["next_state", "previous_state", "action"]}
        if finite
        else {"F": ["next_state", "previous_state"], "H": ["observation", "state"]}
    )
    declaration = {
        "schema": "gnn-independent-numerical-witness-v1",
        "model": family,
        "question": "filtering",
        "dtype": "float64",
        "initial_time": "first_observation_uses_prior",
        "axes": axes,
        "state_ids": ["left", "right"] if finite else ["x"],
        "observation_ids": ["red", "blue"] if finite else ["y"],
    }
    options: dict[str, Any] = {"num_timesteps": 2, "random_seed": 19}
    if finite:
        options["b_tensor_order"] = "next_state_previous_state_action"
    variables = (
        "s[2,1,type=int]\no[2,1,type=int]\nu[1,1,type=int]"
        if finite
        else "x[1,1,type=float]\ny[1,1,type=float]"
    )
    equations = (
        "p(s_0)=D; p(o_t|s_t)=A[o_t,s_t]; p(s_(t+1)|s_t,a_t)=B[s_(t+1),s_t,a_t]"
        if finite
        else "x_0~N(prior_mean,prior_cov); x_(t+1)=F*x_t+N(0,Q); y_t=H*x_t+N(0,R)"
    )
    source = (
        "\n\n".join(
            (
                "# FEP semantic source fixture",
                "## ModelName\nIndependent rational example",
                "## GNNSection\n" + ("ActInfPOMDP" if finite else "ActInfContinuous"),
                "## StateSpaceBlock\n" + variables,
                "## InitialParameterization\n"
                + "\n".join(
                    f"{key} = {json.dumps(value)}" for key, value in parameters.items()
                ),
                "## ModelParameters\n"
                + "\n".join(f"{key}: {value}" for key, value in options.items()),
                "## Equations\n" + equations,
                "## NumericalWitness\n" + json.dumps(declaration),
            )
        )
        + "\n"
    )
    contract = {
        **declaration,
        "parameters": parameters,
        "model_parameters": options,
        "equations": equations,
        "source_sha256": hashlib.sha256(source.encode()).hexdigest(),
    }
    quantities = (
        {"beliefs": [[3 / 11, 8 / 11], [204 / 263, 59 / 263]]}
        if finite
        else {
            "beliefs": [[2 / 3], [31 / 518]],
            "posterior_cov": [[[1 / 3]], [[109 / 518]]],
        }
    )
    observations = [1, 0] if finite else [[1.0], [-0.5]]
    actions = [0] if finite else []
    identity = {
        "dtype": "float64",
        "initial_time": declaration["initial_time"],
        "axes": axes,
        "conditioning_horizon": [1, 2],
        "num_timesteps": 2,
        "num_states": 2 if finite else 1,
        "num_observations": 2 if finite else 1,
        "random_seed": 19,
        "inference_contract": "bnlearn_fixed_action_filter_v1"
        if finite
        else "gnn_lgssm_filter_v1",
        "inference_mode": "exact_categorical_filtering"
        if finite
        else "gaussian_filtering",
        "control_mode": "fixed_transition_actions" if finite else "passive",
    }
    result = {
        **identity,
        **quantities,
        "framework": "bnlearn" if finite else "jax",
        "parameters": {key: value for key, value in parameters.items() if key != "C"},
    }
    if finite:
        result.update(
            observations=observations,
            transition_actions=actions,
            action_semantics="transition_into_next_state",
        )
    else:
        result.update(observations_continuous=observations, controls=[[0.0], [0.0]])
    comparisons = {
        f"identity:{key}": {
            "status": "passed",
            "reason": "",
            "expected": value,
            "actual": value,
        }
        for key, value in identity.items()
    }
    comparisons["identity:framework"] = {
        "status": "passed",
        "reason": "",
        "expected": ["bnlearn"]
        if finite
        else ["jax", "numpyro", "pytorch", "ngclearn"],
        "actual": result["framework"],
    }
    comparisons["validity:beliefs"] = {"status": "passed", "reason": ""}
    if not finite:
        comparisons["validity:posterior_cov"] = {"status": "passed", "reason": ""}
    for key, value in parameters.items():
        if key != "C":
            comparisons[f"parameter:{key}"] = _semantic_quantity(
                value, value, exact=True
            )
    for key, value in quantities.items():
        comparisons[key] = _semantic_quantity(value, value)
    if finite:
        comparisons["identity:action_semantics"] = {
            "status": "passed",
            "reason": "",
            "expected": "transition_into_next_state",
            "actual": "transition_into_next_state",
        }
    else:
        comparisons["controls"] = _semantic_quantity(
            result["controls"], result["controls"], exact=True
        )

    def artifact(text: str) -> dict[str, str]:
        return {"utf8": text, "sha256": hashlib.sha256(text.encode()).hexdigest()}

    return {
        "schema": "gnn-semantic-witness-v2",
        "status": "passed",
        "source_contract": contract,
        "reference": {
            "algorithm": "finite_complete_path_enumeration"
            if finite
            else "joint_gaussian_prefix_conditioning",
            "quantities": quantities,
            "observations": observations,
            "transition_actions": actions,
            "conditioning_horizon": [1, 2],
        },
        "candidate": {
            **identity,
            "observations": observations,
            "transition_actions": actions,
            "quantities": quantities,
        },
        "comparisons": comparisons,
        "assumptions": {
            **{
                key: declaration[key]
                for key in (
                    "question",
                    "initial_time",
                    "state_ids",
                    "observation_ids",
                    "axes",
                )
            },
            "conditioning_horizon": [1, 2],
            "label_mapping": "Ordered source labels name numeric axes; native label provenance is not authenticated.",
            "scope": "One stationary factor, fixed exogenous actions or passive LGSSM; float64; at most eight times/four dimensions; no planning, coupled/hybrid semantics or universal equivalence.",
        },
        "artifacts": {
            "source": artifact(source),
            "result": artifact(json.dumps(result)),
            "program": None,
        },
        "formal_evidence": {"status": "unavailable", "universal_equivalence": False},
        "execution_evidence": {
            "status": "artifact_only",
            "execution_source_verified": False,
            "reported_framework": "bnlearn" if finite else "jax",
            "reported_versions": {},
        },
    }


@pytest.mark.parametrize("family", ["finite", "gaussian"])
def test_source_semantic_replay_resolves_theorems_without_promoting_evidence(
    family: str,
) -> None:
    from fep_formal.bridge.certificates import audit_semantic_witness

    audit = audit_semantic_witness(
        _semantic_fixture(family), Path(__file__).resolve().parents[1]
    )
    assert audit["status"] == "passed", audit["errors"]
    assert audit["formal_references"]
    assert audit["independent_replay"]["algorithm"] == (
        "finite_forward_filter" if family == "finite" else "gaussian_kalman_joseph"
    )
    assert all(
        row["status"] == "passed"
        for row in audit["independent_replay"]["comparisons"].values()
    )
    assert audit["formal_evidence"]["native_claim_ready"] is False
    assert audit["execution_evidence"]["execution_source_verified"] is False
    assert {item["alignment"] for item in audit["formal_references"]} == (
        {"theorem_instance"} if family == "finite" else {"structural_analogue"}
    )
    assert all(item["unmatched_assumptions"] for item in audit["formal_references"])


@pytest.mark.parametrize(
    "mutation",
    [
        "digest",
        "source",
        "candidate",
        "reference",
        "comparison",
        "proof",
        "execution",
        "status",
        "deleted_framework",
        "invented_framework",
        "fabricated",
        "malformed_row",
        "scope",
        "label_mapping",
        "assumptions_list",
    ],
)
def test_source_semantic_replay_refuses_plausible_tampering(mutation: str) -> None:
    from fep_formal.bridge.certificates import audit_semantic_witness

    witness = deepcopy(_semantic_fixture("gaussian"))
    if mutation == "digest":
        witness["artifacts"]["result"]["sha256"] = "0" * 64
    elif mutation == "source":
        witness["source_contract"]["parameters"]["H"] = [[2.0]]
    elif mutation == "candidate":
        witness["candidate"]["dtype"] = "float32"
    elif mutation == "reference":
        witness["reference"]["quantities"]["posterior_cov"][0][0][0] += 0.1
    elif mutation == "comparison":
        witness["comparisons"]["beliefs"]["max_abs_error"] = 0.1
    elif mutation == "proof":
        witness["formal_evidence"]["universal_equivalence"] = True
    elif mutation == "execution":
        witness["execution_evidence"]["execution_source_verified"] = True
    elif mutation == "deleted_framework":
        del witness["comparisons"]["identity:framework"]
    elif mutation == "invented_framework":
        witness["comparisons"]["identity:framework"]["actual"] = "invented"
    elif mutation == "fabricated":
        witness["comparisons"]["fabricated"] = {
            "status": "passed",
            "reason": "invented law",
        }
    elif mutation == "malformed_row":
        witness["comparisons"]["fabricated"] = []
    elif mutation in {"scope", "label_mapping"}:
        witness["assumptions"][mutation] = "universal equivalence proved"
    elif mutation == "assumptions_list":
        witness["assumptions"] = []
    else:
        witness["status"] = "failed"
    audit = audit_semantic_witness(witness, Path(__file__).resolve().parents[1])
    assert audit["status"] != "passed"
    assert audit["errors"]


@pytest.mark.parametrize(
    "field,value",
    [
        ("dtype", "float32"),
        ("random_seed", True),
        ("initial_time", "predict_before_first_observation"),
        ("controls", [[1], [0]]),
        ("conditioning_horizon", [2, 2]),
    ],
)
def test_source_semantic_replay_checks_native_owned_assumptions(
    field: str, value: Any
) -> None:
    from fep_formal.bridge.certificates import audit_semantic_witness

    witness = _semantic_fixture("gaussian")
    payload = json.loads(witness["artifacts"]["result"]["utf8"])
    payload[field] = value
    text = json.dumps(payload)
    witness["artifacts"]["result"] = {
        "utf8": text,
        "sha256": hashlib.sha256(text.encode()).hexdigest(),
    }
    audit = audit_semantic_witness(witness, Path(__file__).resolve().parents[1])
    assert audit["status"] == "refused"
    assert audit["errors"]


@pytest.mark.parametrize(
    "field,value",
    [
        ("source_sha256", "0" * 64),
        ("source_identity", {"source_sha256": "0" * 64}),
        ("state_ids", ["different"]),
        ("observation_ids", ["different"]),
        ("model_kind", "discrete"),
        ("framework", "unregistered"),
        ("schema_version", "synthetic_backend_smoke_v1"),
        ("success", False),
        ("status", "incomplete"),
        ("validation", {"nested": [{"valid": False}]}),
        ("validation", []),
        ("source_identity", []),
    ],
)
def test_semantic_audit_refuses_explicit_raw_contradictions_even_without_saved_rows(
    field: str, value: Any
) -> None:
    from fep_formal.bridge.certificates import audit_semantic_witness

    witness = _semantic_fixture("gaussian")
    payload = json.loads(witness["artifacts"]["result"]["utf8"])
    payload[field] = value
    text = json.dumps(payload)
    witness["artifacts"]["result"] = {
        "utf8": text,
        "sha256": hashlib.sha256(text.encode()).hexdigest(),
    }
    audit = audit_semantic_witness(witness, Path(__file__).resolve().parents[1])
    assert audit["status"] == "refused"
    assert audit["errors"]


@pytest.mark.parametrize("budget", ["nodes", "depth", "path"])
def test_semantic_audit_refuses_native_validation_beyond_gnn_budget(
    budget: str,
) -> None:
    from fep_formal.bridge.certificates import audit_semantic_witness

    witness = _semantic_fixture("finite")
    payload = json.loads(witness["artifacts"]["result"]["utf8"])
    validation: dict[str, Any] = {"values": [True] * 4096}
    if budget == "depth":
        validation = {}
        for _ in range(33):
            validation = {"nested": validation}
    elif budget == "path":
        validation = {"v" * 2048: True}
    payload["validation"] = validation
    text = json.dumps(payload)
    witness["artifacts"]["result"] = {
        "utf8": text,
        "sha256": hashlib.sha256(text.encode()).hexdigest(),
    }
    audit = audit_semantic_witness(witness, Path(__file__).resolve().parents[1])
    assert audit["status"] == "refused"
    assert audit["errors"] == ["native validation exceeds node, depth or path budget"]


def test_semantic_cli_binds_live_sources_without_refreshing_historical_pin(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    import argparse

    from fep_formal.bridge.cli import add_arguments, run

    root = Path(__file__).resolve().parents[1]
    gnn = tmp_path / "gnn"
    gnn.mkdir()
    for relative in operations.owner_roster(gnn, "gnn"):
        owner = gnn / relative
        owner.parent.mkdir(parents=True, exist_ok=True)
        owner.write_text("independent test owner\n")
    subprocess.run(["git", "init", "--quiet"], cwd=gnn, check=True)
    subprocess.run(["git", "add", "."], cwd=gnn, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Semantic Test",
            "-c",
            "user.email=semantic@example.invalid",
            "commit",
            "--quiet",
            "-m",
            "test source",
        ],
        cwd=gnn,
        check=True,
    )
    witness = tmp_path / "witness.json"
    witness.write_text(json.dumps(_semantic_fixture("finite")))
    receipt = tmp_path / "audit.json"
    before_pin = (root / operations.PIN).read_bytes()
    parser = argparse.ArgumentParser()
    add_arguments(parser)
    args = parser.parse_args(
        [
            "audit-semantic",
            "--gnn-root",
            str(gnn),
            "--results",
            str(witness),
            "--receipt",
            str(receipt),
        ]
    )
    assert run(root, args) == 0
    audit = json.loads(receipt.read_text())
    assert audit["status"] == "passed"
    assert audit["live_sources"]["gnn"]["dirty_paths"] == []
    assert len(audit["live_sources"]["gnn"]["owners_sha256"]) == 64
    assert audit["pair_evidence"]["status"] == "unavailable"
    assert audit["pair_evidence"]["current_pair_synchronized"] is False
    assert (root / operations.PIN).read_bytes() == before_pin
    assert json.loads(capsys.readouterr().out)["status"] == "ok"


@pytest.mark.parametrize(
    "heading",
    ["## CouplingV2", "## Unexpected-Section", "##ModelName", "  ## ModelName"],
)
def test_semantic_source_refuses_unknown_or_malformed_headings(heading: str) -> None:
    from fep_formal.bridge.certificates import _semantic_source

    source = _semantic_fixture("finite")["artifacts"]["source"]["utf8"]
    with pytest.raises(ValueError, match="heading"):
        _semantic_source(heading + "\nignored-looking semantics\n" + source)
    with pytest.raises(ValueError, match="heading"):
        _semantic_source(
            source.replace(
                "Independent rational example",
                "Independent rational example\n" + heading,
            )
        )


def test_semantic_source_rejects_byte_budget_without_normalizing() -> None:
    from fep_formal.bridge.certificates import _semantic_source

    source = _semantic_fixture("finite")["artifacts"]["source"]["utf8"]
    with pytest.raises(ValueError, match="byte budget"):
        _semantic_source("é" * (1024 * 1024) + source)


@pytest.mark.parametrize(
    "family,quantity,value",
    [
        ("finite", "beliefs", [[1 + 1e-13, -1e-13], [0.5, 0.5]]),
        ("finite", "beliefs", [[1 + 1e-13, 0], [0.5, 0.5]]),
        ("finite", "beliefs", [[0.2, 0.2], [0.5, 0.5]]),
        ("gaussian", "posterior_cov", [[[-1e-13]], [[0.1]]]),
        ("gaussian", "posterior_cov", [[[0]], [[0.1]]]),
        ("gaussian", "posterior_cov", [[[True]], [[0.1]]]),
    ],
)
def test_semantic_candidate_invariants_precede_numerical_tolerance(
    family: str, quantity: str, value: Any
) -> None:
    from fep_formal.bridge.certificates import _semantic_candidate_validity

    witness = _semantic_fixture(family)
    payload = json.loads(witness["artifacts"]["result"]["utf8"])
    payload[quantity] = value
    with pytest.raises(ValueError):
        _semantic_candidate_validity(witness["source_contract"], payload)


def test_semantic_audit_reports_derived_overflow_and_solver_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import numpy as np

    from fep_formal.bridge.certificates import audit_semantic_witness

    witness = _semantic_fixture("gaussian")
    source = witness["artifacts"]["source"]["utf8"].replace(
        "H = [[1.0]]", "H = [[1e+308]]"
    )
    digest = hashlib.sha256(source.encode()).hexdigest()
    witness["artifacts"]["source"] = {"utf8": source, "sha256": digest}
    witness["source_contract"]["source_sha256"] = digest
    witness["source_contract"]["parameters"]["H"] = [[1e308]]
    audit = audit_semantic_witness(witness, Path(__file__).resolve().parents[1])
    assert audit["status"] == "refused"
    assert audit["errors"]

    def singular(*args: Any, **kwargs: Any) -> Any:
        raise np.linalg.LinAlgError("bounded solver failure")

    monkeypatch.setattr(np.linalg, "solve", singular)
    audit = audit_semantic_witness(
        _semantic_fixture("gaussian"), Path(__file__).resolve().parents[1]
    )
    assert audit["status"] == "refused"
    assert "bounded solver failure" in audit["errors"]


@pytest.mark.parametrize("alias_kind", ["same", "symlink", "hardlink"])
def test_semantic_cli_cannot_overwrite_input_artifact(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], alias_kind: str
) -> None:
    import argparse

    from fep_formal.bridge.cli import add_arguments, run

    witness = tmp_path / "input.json"
    witness.write_text(json.dumps(_semantic_fixture("finite")))
    alias = witness if alias_kind == "same" else tmp_path / "alias.json"
    if alias_kind == "symlink":
        alias.symlink_to(witness)
    elif alias_kind == "hardlink":
        alias.hardlink_to(witness)
    before = witness.read_bytes()
    parser = argparse.ArgumentParser()
    add_arguments(parser)
    args = parser.parse_args(
        [
            "audit-semantic",
            "--gnn-root",
            str(tmp_path),
            "--results",
            str(witness),
            "--receipt",
            str(alias),
        ]
    )
    assert run(tmp_path, args) == 1
    assert witness.read_bytes() == before
    assert "overwrite or alias" in capsys.readouterr().out


def test_semantic_audit_refuses_oversized_sparse_input_before_source_checks(
    tmp_path: Path,
) -> None:
    witness = tmp_path / "oversized.json"
    with witness.open("wb") as stream:
        stream.truncate(96 * 1024 * 1024 + 1)
    with pytest.raises(ValueError, match="receipt byte budget"):
        operations.semantic_witness_audit(tmp_path, tmp_path, witness)


@pytest.mark.parametrize(
    "content,error",
    [
        pytest.param(
            '{"schema":"first","schema":"second"}',
            "duplicate JSON key",
            id="duplicate",
        ),
        pytest.param('{"value":NaN}', "nonfinite JSON value", id="nan"),
        pytest.param('{"value":Infinity}', "nonfinite JSON value", id="infinity"),
        pytest.param("[" * 5000 + "0" + "]" * 5000, "JSON object", id="deep-nonobject"),
    ],
)
def test_semantic_cli_rejects_malformed_captured_json_without_traceback(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    content: str,
    error: str,
) -> None:
    import argparse

    from fep_formal.bridge.cli import add_arguments, run

    witness = tmp_path / "input.json"
    witness.write_text(content)
    parser = argparse.ArgumentParser()
    add_arguments(parser)
    args = parser.parse_args(
        [
            "audit-semantic",
            "--gnn-root",
            str(tmp_path),
            "--results",
            str(witness),
        ]
    )
    assert run(tmp_path, args) == 1
    assert error in capsys.readouterr().out
    assert witness.read_text() == content


def _bind_semantic_artifact(witness: dict[str, Any], name: str, text: str) -> None:
    """Retain actual edited bytes and their digest in a test receipt."""
    witness["artifacts"][name] = {
        "utf8": text,
        "sha256": hashlib.sha256(text.encode()).hexdigest(),
    }


@pytest.mark.parametrize(
    "old,new,error",
    [
        ("## ModelName", "### ModelName", "outside restricted"),
        ('"schema": "gnn-independent-numerical-witness-v1", ', "", "declaration"),
        (
            "gnn-independent-numerical-witness-v1",
            "unknown-schema",
            "source witness schema",
        ),
        ('"model": "finite"', '"model": "hybrid"', "filtering only"),
        ('"dtype": "float64"', '"dtype": "float32"', "precision"),
        (
            '"state_ids": ["left", "right"]',
            '"state_ids": ["left", "left"]',
            "identities",
        ),
        ("A = ", "A: ", "JSON assignment"),
        ("num_timesteps: 2", "num_timesteps: true", "time/seed/option"),
        ("num_timesteps: 2", "num_timesteps: 9", "time/seed/option"),
        ("random_seed: 19", "random_seed: -1", "time/seed/option"),
        (
            "next_state_previous_state_action",
            "previous_state_next_state_action",
            "B orientation",
        ),
        ("A = [[0.8, 0.2], [0.2, 0.8]]", "A = [[0.8, 0.2]]", "dimensions"),
        ("C = [0, 0]", "C = [1, 0]", "passive preference"),
        ("D = [0.6, 0.4]", "D = [0.6, 0.5]", "normalized probabilities"),
        ("s[2,1,type=int]", "s[2,1,type=float]", "source equations"),
    ],
)
def test_semantic_source_refuses_unreviewed_grammar_and_parameters(
    old: str, new: str, error: str
) -> None:
    from fep_formal.bridge.certificates import _semantic_source

    source = _semantic_fixture("finite")["artifacts"]["source"]["utf8"]
    assert source.count(old) == 1
    with pytest.raises(ValueError, match=error):
        _semantic_source(source.replace(old, new, 1))


@pytest.mark.parametrize("section", ["ModelName", "InitialParameterization"])
def test_semantic_source_refuses_duplicate_sections_or_parameters(section: str) -> None:
    from fep_formal.bridge.certificates import _semantic_source

    source = _semantic_fixture("finite")["artifacts"]["source"]["utf8"]
    if section == "ModelName":
        source += "\n## ModelName\nRepeated identity\n"
        error = "duplicate source section"
    else:
        source = source.replace("D = [0.6, 0.4]", "D = [0.6, 0.4]\nD = [0.6, 0.4]")
        error = "duplicate source parameter"
    with pytest.raises(ValueError, match=error):
        _semantic_source(source)


@pytest.mark.parametrize(
    "case,error",
    [
        ("missing", "stationary Gaussian parameters"),
        ("dimension", "source dimensions"),
        ("symmetric", "symmetric covariance"),
        ("positive", "positive definite covariance"),
    ],
)
def test_semantic_source_refuses_invalid_gaussian_covariance_contract(
    case: str, error: str
) -> None:
    from fep_formal.bridge.certificates import _semantic_source

    source = _semantic_fixture("gaussian")["artifacts"]["source"]["utf8"]
    if case == "missing":
        source = source.replace("Q = [[0.2]]\n", "")
    elif case == "dimension":
        source = source.replace("F = [[0.7]]", "F = [[0.7, 0.0]]")
    elif case == "positive":
        source = source.replace("Q = [[0.2]]", "Q = [[0.0]]")
    else:
        replacements = {
            '"state_ids": ["x"]': '"state_ids": ["x", "z"]',
            "x[1,1,type=float]": "x[2,1,type=float]",
            "F = [[0.7]]": "F = [[0.7, 0.0], [0.0, 0.7]]",
            "H = [[1.0]]": "H = [[1.0, 0.0]]",
            "Q = [[0.2]]": "Q = [[0.2, 0.1], [0.0, 0.2]]",
            "prior_mean = [0.0]": "prior_mean = [0.0, 0.0]",
            "prior_cov = [[1.0]]": "prior_cov = [[1.0, 0.0], [0.0, 1.0]]",
        }
        for old, new in replacements.items():
            assert source.count(old) == 1
            source = source.replace(old, new, 1)
    with pytest.raises(ValueError, match=error):
        _semantic_source(source)


@pytest.mark.parametrize(
    "family,field,value,error",
    [
        ("finite", "observations", [True, 0], "finite observations"),
        ("finite", "transition_actions", [], "ordered action"),
        ("gaussian", "observations_continuous", [[1.0]], "every admitted timestep"),
        ("gaussian", "control_mode", "closed_loop", "passive filtering"),
    ],
)
def test_semantic_replay_refuses_incomplete_or_mistyped_conditioning(
    family: str, field: str, value: Any, error: str
) -> None:
    from fep_formal.bridge.certificates import _semantic_replay

    witness = _semantic_fixture(family)
    result = json.loads(witness["artifacts"]["result"]["utf8"])
    result[field] = value
    with pytest.raises(ValueError, match=error):
        _semantic_replay(witness["source_contract"], result)


def test_semantic_finite_replay_refuses_zero_evidence() -> None:
    from fep_formal.bridge.certificates import _semantic_replay

    witness = _semantic_fixture("finite")
    contract = witness["source_contract"]
    contract["parameters"]["A"] = [[0.0, 0.0], [1.0, 1.0]]
    result = json.loads(witness["artifacts"]["result"]["utf8"])
    result["observations"] = [0, 0]
    with pytest.raises(ValueError, match="zero or nonfinite observation evidence"):
        _semantic_replay(contract, result)


@pytest.mark.parametrize(
    "reference,candidate,error",
    [
        ([[1.0], [2.0, 3.0]], [[1.0]], "rectangular finite array"),
        ([[1.0]], [[1.0, 2.0]], "shape mismatch"),
        ([-1e308], [1e308], "finite range"),
        ([5e-324], [1e308], "finite range"),
    ],
)
def test_semantic_diagnostics_refuse_ragged_shape_and_float_range(
    reference: Any, candidate: Any, error: str
) -> None:
    from fep_formal.bridge.certificates import _semantic_quantity

    with pytest.raises(ValueError, match=error):
        _semantic_quantity(reference, candidate)


def test_semantic_identity_does_not_equate_boolean_with_integer() -> None:
    from fep_formal.bridge.certificates import _semantic_identity_row

    with pytest.raises(ValueError, match="scientific identity"):
        _semantic_identity_row(True, 1)


def test_semantic_covariance_requires_positive_definiteness_beyond_positive_diagonal() -> (
    None
):
    from fep_formal.bridge.certificates import _semantic_candidate_validity

    contract = _semantic_fixture("gaussian")["source_contract"]
    contract["state_ids"] = ["x", "z"]
    valid = {
        "beliefs": [[0.0, 0.0], [0.0, 0.0]],
        "posterior_cov": [[[1.0, 0.0], [0.0, 1.0]]] * 2,
    }
    assert (
        _semantic_candidate_validity(contract, valid)["validity:posterior_cov"][
            "status"
        ]
        == "passed"
    )
    valid["posterior_cov"] = [[[1.0, 2.0], [2.0, 1.0]]] * 2
    with pytest.raises(ValueError, match="must be positive definite"):
        _semantic_candidate_validity(contract, valid)
    valid["beliefs"] = [[0.0]]
    with pytest.raises(ValueError, match="candidate shape mismatch"):
        _semantic_candidate_validity(contract, valid)


@pytest.mark.parametrize(
    "case,error",
    [
        ("schema", "unsupported GNN semantic witness"),
        ("artifacts", "artifact roster"),
        ("artifact_shape", "invalid embedded artifact"),
        ("result_type", "JSON object"),
        ("reference_roster", "reference inputs"),
        ("parameters", "parameter arrays unavailable"),
        ("parameter_drift", "does not pass numerical and semantic admission"),
        ("validation_false", "validation explicitly failed"),
    ],
)
def test_semantic_audit_refuses_structural_and_native_parameter_defects(
    case: str, error: str
) -> None:
    from fep_formal.bridge.certificates import audit_semantic_witness

    witness = _semantic_fixture("gaussian")
    if case == "schema":
        witness["schema"] = "gnn-semantic-witness-v1"
    elif case == "artifacts":
        witness["artifacts"] = []
    elif case == "artifact_shape":
        witness["artifacts"]["result"] = {"utf8": None, "sha256": "0" * 64}
    elif case == "result_type":
        _bind_semantic_artifact(witness, "result", "[]")
    elif case == "reference_roster":
        del witness["reference"]["conditioning_horizon"]
    else:
        result = json.loads(witness["artifacts"]["result"]["utf8"])
        if case == "parameters":
            result["parameters"] = None
        elif case == "parameter_drift":
            result["parameters"]["F"] = [[0.7 + 1e-13]]
        else:
            result["validation"] = {"all_valid": False}
        _bind_semantic_artifact(witness, "result", json.dumps(result))
    audit = audit_semantic_witness(witness, Path(__file__).resolve().parents[1])
    assert audit["status"] == "refused"
    assert any(error in message for message in audit["errors"])


def test_semantic_audit_independently_rejects_a_mutually_fabricated_trace() -> None:
    from fep_formal.bridge.certificates import audit_semantic_witness

    witness = _semantic_fixture("finite")
    forged = [[0.5, 0.5], [0.5, 0.5]]
    result = json.loads(witness["artifacts"]["result"]["utf8"])
    result["beliefs"] = forged
    witness["candidate"]["quantities"]["beliefs"] = forged
    witness["reference"]["quantities"]["beliefs"] = forged
    _bind_semantic_artifact(witness, "result", json.dumps(result))
    audit = audit_semantic_witness(witness, Path(__file__).resolve().parents[1])
    assert audit["status"] == "failed"
    assert audit["errors"] == [
        "independent reference:beliefs disagreement",
        "independent candidate:beliefs disagreement",
    ]
    assert audit["formal_evidence"]["native_claim_ready"] is False


def test_semantic_audit_accepts_bound_optional_declarations_without_execution_claim() -> (
    None
):
    from fep_formal.bridge.certificates import audit_semantic_witness

    witness = _semantic_fixture("gaussian")
    result = json.loads(witness["artifacts"]["result"]["utf8"])
    digest = witness["source_contract"]["source_sha256"]
    result.update(
        source_identity={"source_sha256": digest},
        status="completed",
        validation={"all_valid": True},
    )
    rows = {
        "identity:source_identity.source_sha256": (digest, digest),
        "identity:status": (["success", "completed"], "completed"),
        "identity:validation.all_valid": (True, True),
    }
    program = "print('retained generated bytes')\n"
    _bind_semantic_artifact(witness, "program", program)
    program_digest = witness["artifacts"]["program"]["sha256"]
    result["generated_script_sha256"] = program_digest
    rows["identity:generated_script_sha256"] = (program_digest, program_digest)
    for key, (expected, actual) in rows.items():
        witness["comparisons"][key] = {
            "status": "passed",
            "reason": "",
            "expected": expected,
            "actual": actual,
        }
    _bind_semantic_artifact(witness, "result", json.dumps(result))
    audit = audit_semantic_witness(witness, Path(__file__).resolve().parents[1])
    assert audit["status"] == "passed", audit["errors"]
    assert audit["execution_evidence"]["execution_source_verified"] is False
    assert audit["formal_evidence"]["native_claim_ready"] is False


def test_semantic_formal_references_refuse_unknown_family() -> None:
    from fep_formal.bridge.certificates import semantic_formal_references

    with pytest.raises(ValueError, match="unsupported formal semantic family"):
        semantic_formal_references(Path(__file__).resolve().parents[1], "hybrid")


@pytest.fixture
def semantic_pair(pair: tuple[Path, Path]) -> tuple[Path, Path]:
    """Real formal source bytes in independent disposable source roots."""
    from fep_formal.formal.manifest import FORMAL_MODULES

    root, gnn = pair
    original = Path(__file__).resolve().parents[1]
    for module in FORMAL_MODULES:
        relative = Path("src/fep_formal/formal") / module.resource
        (root / relative).write_bytes((original / relative).read_bytes())
    operations.pin_sources(root, gnn)
    for checkout in (root, gnn):
        subprocess.run(["git", "init", "--quiet"], cwd=checkout, check=True)
    return root, gnn


def test_semantic_operation_preserves_numerical_audit_when_pair_pin_is_missing(
    semantic_pair: tuple[Path, Path], tmp_path: Path
) -> None:
    root, gnn = semantic_pair
    (root / operations.PIN).unlink()
    witness = tmp_path / "witness.json"
    witness.write_text(json.dumps(_semantic_fixture("finite")))
    before = snapshot(root), snapshot(gnn)
    audit = operations.semantic_witness_audit(root, gnn, witness)
    assert audit["status"] == "passed", audit["errors"]
    assert audit["pair_evidence"]["status"] == "unavailable"
    assert audit["pair_evidence"]["errors"]
    assert audit["pair_evidence"]["current_pair_synchronized"] is False
    assert (snapshot(root), snapshot(gnn)) == before


def test_semantic_operation_refuses_artifact_changed_after_replay(
    semantic_pair: tuple[Path, Path], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, gnn = semantic_pair
    witness = tmp_path / "witness.json"
    witness.write_text(json.dumps(_semantic_fixture("finite")))
    original = operations.audit_semantic_witness

    def mutate_after_replay(document: dict[str, Any], checkout: Path) -> dict[str, Any]:
        audit = original(document, checkout)
        assert audit["status"] == "passed", audit["errors"]
        witness.write_text(witness.read_text() + "\n")
        return audit

    monkeypatch.setattr(operations, "audit_semantic_witness", mutate_after_replay)
    audit = operations.semantic_witness_audit(root, gnn, witness)
    assert audit["status"] == "refused"
    assert audit["errors"] == [
        "live owners, revisions or result artifact changed during semantic audit"
    ]


def test_semantic_receipt_read_bounds_growth_after_fstat(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import os

    witness = tmp_path / "growing.json"
    witness.write_bytes(b"{}")
    real_fstat = os.fstat

    def grow_after_stat(descriptor: int) -> Any:
        observed = real_fstat(descriptor)
        with witness.open("r+b") as stream:
            stream.truncate(96 * 1024 * 1024 + 1)
        return observed

    monkeypatch.setattr(operations.os, "fstat", grow_after_stat)
    with pytest.raises(ValueError, match="receipt byte budget exceeded"):
        operations._semantic_receipt_bytes(witness)


def test_semantic_cli_requires_an_explicit_input_without_writes(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    import argparse

    from fep_formal.bridge.cli import add_arguments, run

    parser = argparse.ArgumentParser()
    add_arguments(parser)
    args = parser.parse_args(["audit-semantic", "--gnn-root", str(tmp_path)])
    assert run(tmp_path, args) == 1
    assert "requires --results" in capsys.readouterr().out
    assert list(tmp_path.iterdir()) == []


def document(commit: str = "old", body: str = "A\nB\n") -> str:
    return body + "## Signature\nsource_commit: " + commit + "\npipeline_commit: gnn\n"


def test_only_signature_custody_changes_are_refreshable(tmp_path: Path) -> None:
    path = tmp_path / "model.md"
    path.write_text(document())
    assert classify_document(document(), document()) == FRESH
    assert classify_document(document(), document("new")) == STALE_CUSTODY
    refresh_signature(path, document("new"))
    assert path.read_text() == document("new")


@pytest.mark.parametrize(
    "body", ["B\nA\n", "A\nA\nB\n", "A\n", "A\nB\nsource_commit: new\n"]
)
def test_refresh_refuses_content_changes_without_writing(
    tmp_path: Path, body: str
) -> None:
    path = tmp_path / "model.md"
    path.write_text(document(body=body))
    before = (path.read_bytes(), path.stat().st_mtime_ns)
    assert classify_document(path.read_text(), document("new")) == CONTENT_DRIFT
    with pytest.raises(ValueError, match="content"):
        refresh_signature(path, document("new"))
    assert (path.read_bytes(), path.stat().st_mtime_ns) == before


@pytest.mark.parametrize(
    "bad",
    [
        "",
        "## Signature\nsource_commit: one\nsource_commit: two\n",
        "## Signature\n## Signature\n",
    ],
)
def test_ambiguous_provenance_is_content_drift(bad: str) -> None:
    assert classify_document(bad, document()) == CONTENT_DRIFT


def test_binding_checks_missing_changed_and_extra_owners(tmp_path: Path) -> None:
    (tmp_path / "owner.py").write_text("original")
    binding = fingerprint(tmp_path, ["owner.py"])
    assert validate_binding(tmp_path, binding, ["owner.py"]) == []
    (tmp_path / "owner.py").write_text("changed")
    assert validate_binding(tmp_path, binding, ["owner.py"])
    (tmp_path / "owner.py").unlink()
    assert validate_binding(tmp_path, binding, ["owner.py"])
    assert validate_binding(tmp_path, {}, ["owner.py"])


@pytest.mark.parametrize("path", ["../outside", "/absolute", "a/../../outside"])
def test_binding_rejects_escape(tmp_path: Path, path: str) -> None:
    with pytest.raises(ValueError):
        fingerprint(tmp_path, [path])


def test_binding_rejects_symlinked_owners(tmp_path: Path) -> None:
    target = tmp_path / "real.py"
    target.write_text("content")
    (tmp_path / "link.py").symlink_to(target)
    with pytest.raises(ValueError):
        fingerprint(tmp_path, ["link.py"])


def test_explicit_json_emission_is_deterministic(tmp_path: Path) -> None:
    path = tmp_path / "receipt.json"
    write_json(path, {"b": 2, "a": 1})
    before = (path.read_bytes(), path.stat().st_mtime_ns)
    write_json(path, {"a": 1, "b": 2})
    assert (path.read_bytes(), path.stat().st_mtime_ns) == before
    assert json.loads(path.read_bytes()) == {"a": 1, "b": 2}


@pytest.mark.parametrize("tolerance", [float("inf"), float("nan"), -1.0, True])
def test_invalid_tolerances_never_pass(tolerance: float) -> None:
    with pytest.raises(ValueError, match="tolerance"):
        compare(
            {"policy_posterior": [[999, -998]], "variational_free_energy": [999]},
            tolerance,
        )


@pytest.mark.parametrize(
    "value", [float("inf"), float("nan"), True, "0.25", None, 10**400]
)
def test_invalid_numeric_payload_never_passes(value: object) -> None:
    _, _, ok = compare(
        {
            "policy_posterior": [[value, 0.75]],
            "variational_free_energy": [0.6931471805599453],
        },
        1e-6,
    )
    assert not ok


def test_numerical_agreement_does_not_claim_proof() -> None:
    certificates, _, ok = compare(
        {
            "policy_posterior": [[0.25, 0.75]],
            "variational_free_energy": [0.6931471805599453],
        },
        1e-6,
    )
    assert ok
    assert all("numerical witness" in c["lean_evidence_plane"] for c in certificates)


@pytest.fixture
def pair(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path]:
    """Two independent tiny source checkouts, with no installed sibling required."""
    root, gnn = tmp_path / "fep", tmp_path / "gnn"
    monkeypatch.setattr(operations, "_head", lambda _: "a" * 40)
    from fep_formal.formal.manifest import FORMAL_MODULES

    for module in FORMAL_MODULES:
        for prefix in ("src/fep_formal/formal", "lean/FepSketches"):
            path = root / prefix / module.resource
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("-- fixture formal owner\n")
    for checkout, key in ((root, "fep_lean"), (gnn, "gnn")):
        for name in operations.owner_roster(checkout, key):
            path = checkout / name
            path.parent.mkdir(parents=True, exist_ok=True)
            if not path.exists():
                path.write_text("fixture owner\n")
    for relative in operations.EMITTERS.values():
        (root / relative).write_text(
            "def build_document(source, pipeline):\n"
            '    return "A\\nB\\n## Signature\\nsource_commit: " + source + "\\npipeline_commit: " + pipeline + "\\n"\n'
        )
    (root / operations.CONTRACT).write_text("same contract\n")
    (gnn / operations.MIRROR).write_text("same contract\n")
    write_json(root / operations.SYNTAX_PIN, fingerprint(gnn, operations.SYNTAX_FILES))
    operations.pin_sources(root, gnn)
    for model in operations.DOCUMENTS:
        operations.emit(root, gnn, model)
    return root, gnn


def snapshot(root: Path) -> dict[str, tuple[bytes, int]]:
    return {
        str(p.relative_to(root)): (p.read_bytes(), p.stat().st_mtime_ns)
        for p in root.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts
    }


def test_status_and_checks_do_not_write(pair: tuple[Path, Path]) -> None:
    root, gnn = pair
    before = snapshot(root), snapshot(gnn)
    assert operations.status(root, gnn)["status"] == "ok"
    assert all(operations.emit(root, gnn, m, check=True) for m in operations.DOCUMENTS)
    assert (snapshot(root), snapshot(gnn)) == before


def test_unrelated_head_movement_does_not_change_custody(
    pair: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    root, gnn = pair
    monkeypatch.setattr(operations, "_head", lambda _: "b" * 40)
    assert operations.status(root, gnn)["status"] == "ok"


def test_status_flags_unpinned_syntax_surface(pair: tuple[Path, Path]) -> None:
    """Drift on either pinned syntax file must fail the W1 surface check."""
    root, gnn = pair
    (gnn / operations.SYNTAX_FILES[0]).write_text("drifted syntax\n")
    before = snapshot(gnn)
    report = operations.status(root, gnn)
    assert report["checks"]["syntax_surface"] == {"passed": False}
    assert report["status"] == "error"
    assert snapshot(gnn) == before


def test_status_fails_closed_on_missing_syntax_pin(pair: tuple[Path, Path]) -> None:
    root, gnn = pair
    (root / operations.SYNTAX_PIN).unlink()
    report = operations.status(root, gnn)
    assert report["checks"]["contracts"]["passed"] is False
    assert report["checks"]["contracts"]["errors"]
    assert report["status"] == "error"


def test_status_fails_closed_on_missing_source_pin(pair: tuple[Path, Path]) -> None:
    root, gnn = pair
    (root / operations.PIN).unlink()
    report = operations.status(root, gnn)
    assert report["checks"]["source_binding"]["passed"] is False
    assert report["checks"]["source_binding"]["errors"]
    assert report["status"] == "error"


def test_status_flags_stale_emitted_document(pair: tuple[Path, Path]) -> None:
    """A mutated emitted document is stale, and status must not re-emit."""
    root, gnn = pair
    document = root / operations.DOCUMENTS["finite"]
    document.write_text(document.read_text(encoding="utf-8") + "drift\n")
    before = snapshot(root)
    report = operations.status(root, gnn)
    assert report["checks"]["finite_freshness"] == {
        "passed": False,
        "status": "STALE",
    }
    assert report["status"] == "error"
    assert snapshot(root) == before


@pytest.mark.parametrize("change", ["delete", "change"])
def test_relevant_roster_changes_are_rejected(
    pair: tuple[Path, Path], change: str
) -> None:
    root, gnn = pair
    if change == "delete":
        (gnn / "src/gnn/main.py").unlink()
    else:
        (gnn / "src/gnn/main.py").write_text("changed")
    assert operations.status(root, gnn)["status"] == "error"
    with pytest.raises(ValueError, match="stale"):
        operations.emit(root, gnn, "finite")


def test_gnn_implementation_tree_is_not_pinned(pair: tuple[Path, Path]) -> None:
    """GNN owns its implementation tree: src/gnn code is not a custody owner."""
    root, gnn = pair
    implementation = gnn / "src/gnn/render/new.py"
    implementation.parent.mkdir(parents=True, exist_ok=True)
    implementation.write_text("new implementation\n")
    assert operations.status(root, gnn)["status"] == "ok"
    implementation.write_text("changed implementation\n")
    assert operations.status(root, gnn)["status"] == "ok"


def result_file(root: Path) -> Path:
    path = root / "output/run/results.json"
    write_json(
        path,
        {
            "policy_posterior": [[0.25, 0.75]],
            "variational_free_energy": [0.6931471805599453],
        },
    )
    return path


def test_receipt_validation_is_read_only_and_recomputes_evidence(
    pair: tuple[Path, Path],
) -> None:
    root, gnn = pair
    path = result_file(root)
    before = snapshot(root)
    receipt = operations.certificate_receipt(root, gnn, path)
    assert not receipt["native_claim_ready"]
    assert not receipt["execution_source_verified"]
    assert operations.validate_certificate(root, gnn, receipt) == []
    assert snapshot(root) == before
    receipt["certificates"][0]["delta"] = "invented"
    assert operations.validate_certificate(root, gnn, receipt)


@pytest.mark.parametrize(
    "mutation", ["artifact", "owner", "source_pin", "tolerance", "path"]
)
def test_receipt_tampering_is_rejected(pair: tuple[Path, Path], mutation: str) -> None:
    root, gnn = pair
    path = result_file(root)
    receipt = operations.certificate_receipt(root, gnn, path)
    if mutation == "artifact":
        path.write_text('{"policy_posterior": [[0.5, 0.5]]}')
    elif mutation == "owner":
        (gnn / "src/gnn/main.py").write_text("modified")
    elif mutation == "source_pin":
        receipt["source_pin"]["gnn"]["owners"] = {}
    elif mutation == "tolerance":
        receipt["tolerance"] = float("inf")
    else:
        receipt["results_path"] = "../escape.json"
    assert operations.validate_certificate(root, gnn, receipt)


def test_comparison_rejects_mid_check_source_change(
    pair: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    root, gnn = pair
    original = operations.compare

    def changed(*args: object) -> object:
        (gnn / "src/gnn/main.py").write_text("changed during check")
        return original(*args)

    monkeypatch.setattr(operations, "compare", changed)
    with pytest.raises(ValueError, match="changed during"):
        operations.certificate_receipt(root, gnn, result_file(root))


def test_legacy_certifier_default_does_not_emit(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    import runpy

    root = Path(__file__).resolve().parents[1]
    script = root / "specs/gnn-bridge-p3-certificates/certify.py"
    entry = runpy.run_path(str(script))
    results = result_file(tmp_path)
    before = snapshot(script.parent)
    assert entry["main"](["--results", str(results)]) == 0
    assert snapshot(script.parent) == before
    assert json.loads(capsys.readouterr().out)["source_bound"] is False


def test_bridge_cli_round_trip_and_missing_results(
    pair: tuple[Path, Path], tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    import argparse

    from fep_formal.bridge.cli import add_arguments, run

    root, gnn = pair
    parser = argparse.ArgumentParser()
    add_arguments(parser)
    assert run(root, parser.parse_args(["status", "--gnn-root", str(gnn)])) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "ok"
    assert run(root, parser.parse_args(["certify", "--gnn-root", str(gnn)])) == 1
    capsys.readouterr()
    receipt = tmp_path / "receipt.json"
    results = result_file(root)
    assert (
        run(
            root,
            parser.parse_args(
                [
                    "certify",
                    "--gnn-root",
                    str(gnn),
                    "--results",
                    str(results),
                    "--receipt",
                    str(receipt),
                ]
            ),
        )
        == 0
    )
    capsys.readouterr()
    assert (
        run(
            root,
            parser.parse_args(
                [
                    "verify-certificate",
                    "--gnn-root",
                    str(gnn),
                    "--receipt",
                    str(receipt),
                ]
            ),
        )
        == 0
    )
    capsys.readouterr()
    assert receipt.with_suffix(".md").is_file()


def test_emitter_ignores_unbound_bytecode(pair: tuple[Path, Path]) -> None:
    import importlib.util
    import marshal
    import struct

    root, _ = pair
    emitter = root / operations.EMITTERS["finite"]
    pin = operations.read_object(root / operations.PIN)
    expected = operations.projected_document(root, "finite", pin)
    cache = Path(importlib.util.cache_from_source(str(emitter)))
    cache.parent.mkdir(parents=True, exist_ok=True)
    malicious = compile(
        "def build_document(*args): return 'poisoned'", str(emitter), "exec"
    )
    stat = emitter.stat()
    cache.write_bytes(
        importlib.util.MAGIC_NUMBER
        + struct.pack("<III", 0, int(stat.st_mtime), stat.st_size)
        + marshal.dumps(malicious)
    )
    assert operations.projected_document(root, "finite", pin) == expected


@pytest.mark.parametrize(
    "operation",
    ["certify", "pin", "status", "verify-certificate", "verify-document"],
)
@pytest.mark.parametrize("flag", ["--check", "--refresh-digests"])
def test_emission_flags_reject_other_operations_without_writing(
    pair: tuple[Path, Path], operation: str, flag: str
) -> None:
    import argparse

    from fep_formal.bridge.cli import add_arguments, run

    root, gnn = pair
    parser = argparse.ArgumentParser()
    add_arguments(parser)
    results = result_file(root)
    before = snapshot(root)
    args = parser.parse_args(
        [
            operation,
            flag,
            "--gnn-root",
            str(gnn),
            "--results",
            str(results),
            "--receipt",
            str(root / "receipt.json"),
        ]
    )
    assert run(root, args) == 1
    assert snapshot(root) == before


def test_markdown_receipt_preserves_numerical_only_scope(
    pair: tuple[Path, Path],
) -> None:
    root, gnn = pair
    receipt = operations.certificate_receipt(root, gnn, result_file(root))
    target = root / "certificate.json"
    operations.emit_certificate(target, receipt)
    markdown = target.with_suffix(".md").read_text()
    assert "execution_source_verified: false" in markdown
    assert "native_claim_ready: false" in markdown
    assert "execution provenance unverified" in markdown


@pytest.mark.parametrize(
    "payload",
    [
        '{"schema_version": 1, "fep_lean": {"commit": "a", "commit": "b"}}',
        '{"owners": {"a": "x"}, "owners": {}}',
    ],
    ids=["duplicate-nested-key", "duplicate-top-level-key"],
)
def test_read_object_rejects_duplicate_keys(tmp_path: Path, payload: str) -> None:
    target = tmp_path / "pin.json"
    target.write_text(payload, encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate JSON key"):
        operations.read_object(target)


@pytest.mark.parametrize(
    "payload",
    ['{"x": NaN}', '{"x": Infinity}', '{"x": -Infinity}'],
)
def test_read_object_rejects_nonfinite_constants(tmp_path: Path, payload: str) -> None:
    target = tmp_path / "pin.json"
    target.write_text(payload, encoding="utf-8")
    with pytest.raises(ValueError, match="non-finite JSON constant"):
        operations.read_object(target)


def test_read_object_accepts_wellformed_pin(tmp_path: Path) -> None:
    target = tmp_path / "pin.json"
    target.write_text('{"schema_version": 1, "owners": {"a": "b"}}', encoding="utf-8")
    assert operations.read_object(target) == {
        "schema_version": 1,
        "owners": {"a": "b"},
    }
