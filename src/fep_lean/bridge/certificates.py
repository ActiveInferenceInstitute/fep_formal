#!/usr/bin/env python3
"""Certificate protocol runner for the fep_lean <-> GNN bridge, phase P3.

Compares GNN-pipeline-executed quantities (pymdp 1.0.0 artifacts from the
P3 custody run) with Lean-witnessed claims for the P1 model instance

    FEP.ActiveInference.symmetricBoolModel trueBiasedPolicyPrior
      : GenerativeModel Bool Bool Bool   (active_inference.lean:743-749)

Certificates (see the slice README for the full protocol, evidence-plane
labels, and the tolerance justification):

  C1  policy-posterior agreement: executed `policy_posterior` vs the
      Lean-proved equality `policyPosterior = policyPrior`
      (active_inference.lean:816-826) with
      `trueBiasedPolicyPrior` = (1/4, 3/4) in (false, true) order
      (:731-734). Exact rationals; numerical-witness plane evaluation.
  C2  VFE agreement: executed `variational_free_energy` vs the proved
      closed form `VFE_initial = log 2` (variationalFreeEnergy
      :209-214; predictedOutcome = fairBoolLaw :762-773; posteriorState
      = initial belief :121-125,745; outcomeSurprisal :202-205),
      evaluated as math.log(2) in float64 (numerical-witness plane).
  C3  directional agreement: NOT RUN — recorded boundary (one-step
      instance; no Boolean-carrier decrease theorem on the Lean side).
  O1  informational divergence: executed `expected_free_energy` (pymdp
      `neg_efe`, linear-utility convention, pymdp/control.py:422-445)
      vs Lean `expectedFreeEnergy` = risk + ambiguity = log 2
      (:148-150, :789-812). Different conventions; filed with exact
      numbers, never averaged away.

Exit codes: 0 when every stated certificate (C1, C2) agrees within
tolerance; 1 on any disagreement or unstatable quantity. O1 never
changes the exit code.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any

TOLERANCE = 1e-6  # jax float32 backend; see README "Comparison policy"

# Lean-witnessed constants (exact; provenance in comments).

# lean/FepSketches/active_inference.lean:731-734 — trueBiasedPolicyPrior
# (mass policy := if policy then 3 / 4 else 1 / 4), Bool order
# (false, true); equality Q(π) = prior proved at :816-826.
LEAN_Q_FALSE = 0.25
LEAN_Q_TRUE = 0.75

# lean/FepSketches/active_inference.lean:209-214 with :202-205, :762-773,
# :121-125, :745 — VFE on the initial belief collapses to -log P(o) with
# P(o) = 1/2 (fair law), i.e. log 2 (nats). Evaluated in float64 as the
# numerical witness of the proved closed form.
LEAN_VFE_INITIAL = math.log(2)

# lean/FepSketches/active_inference.lean:148-150 with :789-812 — Lean
# expectedFreeEnergy = risk + ambiguity = 0 + entropy(fairBoolLaw) = log 2.
LEAN_EFE = math.log(2)

PLANE_EXECUTION = "reported numerical values; execution provenance unverified"
PLANE_LEAN_COMPILATION = "referenced Lean statement (native receipt checked separately)"
PLANE_NUMERICAL = "numerical witness"


def _finite_number(value: object) -> bool:
    try:
        return (
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and math.isfinite(value)
        )
    except OverflowError:
        return False


def _within(value: float, expected: float, tolerance: float) -> bool:
    return abs(value - expected) <= tolerance


def _cert_entry(
    cid: str,
    passed: bool,
    lean_value: str,
    executed_value: str,
    delta: str,
    lean_plane: str,
    executed_plane: str,
    detail: str,
) -> dict[str, Any]:
    return {
        "certificate": cid,
        "passed": passed,
        "lean_value": lean_value,
        "executed_value": executed_value,
        "delta": delta,
        "lean_evidence_plane": lean_plane,
        "executed_evidence_plane": executed_plane,
        "detail": detail,
    }


def _compare_c1(
    results: dict[str, Any], tolerance: float
) -> tuple[dict[str, Any], bool]:
    q_posterior = results.get("policy_posterior")
    q0 = q_posterior[0] if isinstance(q_posterior, list) and q_posterior else None
    if isinstance(q0, list) and len(q0) == 2 and all(_finite_number(v) for v in q0):
        executed_q_false = float(q0[0])
        executed_q_true = float(q0[1])
        d_false = abs(executed_q_false - LEAN_Q_FALSE)
        d_true = abs(executed_q_true - LEAN_Q_TRUE)
        c1_pass = _within(executed_q_false, LEAN_Q_FALSE, tolerance) and _within(
            executed_q_true, LEAN_Q_TRUE, tolerance
        )
        entry = _cert_entry(
            "C1",
            c1_pass,
            f"Q = ({LEAN_Q_FALSE}, {LEAN_Q_TRUE}) exact",
            f"policy_posterior[0] = ({executed_q_false!r}, {executed_q_true!r})",
            f"|dfalse| = {d_false:.3e}, |dtrue| = {d_true:.3e}",
            PLANE_LEAN_COMPILATION + " + " + PLANE_NUMERICAL,
            PLANE_EXECUTION,
            "Lean equality Q(pi)=prior (:816-826) vs pymdp infer_policies"
            " posterior; argmax executed = "
            + ("true" if executed_q_true > executed_q_false else "false"),
        )
        return entry, c1_pass
    entry = _cert_entry(
        "C1",
        False,
        str((LEAN_Q_FALSE, LEAN_Q_TRUE)),
        "unstatable",
        "n/a",
        PLANE_LEAN_COMPILATION + " + " + PLANE_NUMERICAL,
        PLANE_EXECUTION,
        "policy_posterior missing or not a 2-vector in executed results",
    )
    return entry, False


def _compare_c2(
    results: dict[str, Any], tolerance: float
) -> tuple[dict[str, Any], bool]:
    vfe = results.get("variational_free_energy")
    executed_vfe = (
        float(vfe[0])
        if isinstance(vfe, list) and vfe and _finite_number(vfe[0])
        else None
    )
    if executed_vfe is not None:
        d_vfe = abs(executed_vfe - LEAN_VFE_INITIAL)
        c2_pass = _within(executed_vfe, LEAN_VFE_INITIAL, tolerance)
        entry = _cert_entry(
            "C2",
            c2_pass,
            f"VFE_initial = log 2 = {LEAN_VFE_INITIAL!r}",
            f"variational_free_energy[0] = {executed_vfe!r}",
            f"|d| = {d_vfe:.3e}",
            PLANE_LEAN_COMPILATION + " + " + PLANE_NUMERICAL,
            PLANE_EXECUTION,
            "Lean VFE on initial belief (closed form, README C2) vs pymdp"
            " infer_states VFE",
        )
        return entry, c2_pass
    entry = _cert_entry(
        "C2",
        False,
        str(LEAN_VFE_INITIAL),
        "unstatable",
        "n/a",
        PLANE_LEAN_COMPILATION + " + " + PLANE_NUMERICAL,
        PLANE_EXECUTION,
        "variational_free_energy missing from executed results",
    )
    return entry, False


def _observe_o1(results: dict[str, Any]) -> list[dict[str, str]]:
    observations: list[dict[str, str]] = []
    efe = results.get("expected_free_energy")
    if (
        isinstance(efe, list)
        and efe
        and isinstance(efe[0], list)
        and efe[0]
        and _finite_number(efe[0][0])
    ):
        executed_efe = float(efe[0][0])
        observations.append(
            {
                "id": "O1",
                "lean_value": f"expectedFreeEnergy = log 2 = {LEAN_EFE!r}"
                " (active_inference.lean:148-150, :789-812)",
                "executed_value": f"expected_free_energy[0] ="
                f" {executed_efe!r}"
                " (pymdp neg_efe, linear utility, pymdp/control.py:422-445)",
                "delta": f"{abs(executed_efe - LEAN_EFE):.6f}",
                "note": "different C conventions across the bridge surface;"
                " filed, not smoothed over (README O1)",
            }
        )
    return observations


def compare(
    results: dict[str, Any], tolerance: float
) -> tuple[list[dict[str, Any]], list[dict[str, str]], bool]:
    """Run C1/C2 comparisons; return (certificates, observations, ok)."""
    if not _finite_number(tolerance) or tolerance < 0:
        raise ValueError("tolerance must be finite and nonnegative")
    c1_entry, c1_pass = _compare_c1(results, tolerance)
    c2_entry, c2_pass = _compare_c2(results, tolerance)
    observations = _observe_o1(results)
    ok = c1_pass and c2_pass
    return [c1_entry, c2_entry], observations, ok


def render_markdown(
    certificates: list[dict[str, Any]],
    observations: list[dict[str, str]],
    results_path: Path,
    ok: bool,
) -> str:
    lines = [
        "# P3 certificates — FepLeanSymmetricBool",
        "",
        f"Identified result artifact: `{results_path.name}`.",
        "",
        "Numerical comparison only; execution provenance unverified.",
        "`execution_source_verified: false`; `native_claim_ready: false`.",
        "A passing comparison does not establish a current pipeline execution or Lean proof.",
        "",
        "| Certificate | Result | Lean value | Executed value | Delta |",
        "| --- | --- | --- | --- | --- |",
    ]
    for c in certificates:
        lines.append(
            f"| {c['certificate']} | {'PASS' if c['passed'] else 'FAIL'}"
            f" | {c['lean_value']} | {c['executed_value']} | {c['delta']} |"
        )
    lines += [
        "",
        "C3 (directional agreement) is a recorded boundary, not run: the",
        "instance is one-step and no Lean-witnessed decrease family exists",
        "for the Boolean carrier (README C3).",
        "",
        "## Evidence planes",
        "",
    ]
    for c in certificates:
        lines.append(
            f"- {c['certificate']}: Lean side = {c['lean_evidence_plane']};"
            f" executed side = {c['executed_evidence_plane']}."
        )
    if observations:
        lines += ["", "## Observations (findings, exact numbers)", ""]
        for o in observations:
            lines += [
                (
                    f"- {o['id']}: executed {o['executed_value']}; Lean"
                    f" {o['lean_value']}; delta = {o['delta']}."
                    f" {o['note']}"
                ),
            ]
    lines += [
        "",
        f"Gate: {'PASS' if ok else 'FAIL'} (C1 and C2 within tolerance).",
        "",
    ]
    return "\n".join(lines)


def _semantic_json(text: str) -> Any:
    """Read evidence without last-key-wins or nonfinite JSON extensions."""

    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in pairs:
            if key in value:
                raise ValueError(f"duplicate JSON key: {key}")
            value[key] = item
        return value

    def nonfinite(value: str) -> Any:
        raise ValueError(f"nonfinite JSON value: {value}")

    return json.loads(text, object_pairs_hook=unique, parse_constant=nonfinite)


def _semantic_array(value: Any, name: str) -> Any:
    """Admit rectangular finite numerical arrays, never booleans or strings."""
    import numpy as np

    def numeric(item: Any) -> bool:
        if isinstance(item, list):
            return bool(item) and all(numeric(child) for child in item)
        return _finite_number(item)

    if not numeric(value):
        raise ValueError(f"{name}: finite nonboolean numeric values required")
    try:
        return np.asarray(value, dtype=np.float64)
    except (ValueError, OverflowError) as exc:
        raise ValueError(f"{name}: rectangular finite array required") from exc


def _semantic_source(source: str) -> dict[str, Any]:
    """Independently read the bounded E4 source grammar, without GNN imports."""
    import numpy as np

    if len(source.encode("utf-8")) > 1024 * 1024:
        raise ValueError("source byte budget exceeded")
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
            match = re.fullmatch(r"## ([A-Za-z]+)[ \t]*", line)
            if match is None or match.group(1) not in required:
                raise ValueError("unsupported or malformed level-two source heading")
    sections: dict[str, str] = {}
    parts = re.split(r"(?m)^## ([A-Za-z]+)\s*\n", text)
    for index in range(1, len(parts), 2):
        name = parts[index]
        if name in sections:
            raise ValueError(f"duplicate source section: {name}")
        sections[name] = parts[index + 1].strip()
    if set(sections) != {
        "ModelName",
        "GNNSection",
        "StateSpaceBlock",
        "InitialParameterization",
        "ModelParameters",
        "Equations",
        "NumericalWitness",
    }:
        raise ValueError("source outside restricted semantic witness grammar")
    declaration = _semantic_json(sections["NumericalWitness"])
    fields = {
        "schema",
        "model",
        "question",
        "dtype",
        "initial_time",
        "axes",
        "state_ids",
        "observation_ids",
    }
    if not isinstance(declaration, dict) or set(declaration) != fields:
        raise ValueError("unsupported semantic source declaration")
    if declaration["schema"] != "gnn-independent-numerical-witness-v1":
        raise ValueError("unsupported source witness schema")
    family = declaration["model"]
    if family not in {"finite", "gaussian"} or declaration["question"] != "filtering":
        raise ValueError("FEP replay admits finite or Gaussian filtering only")
    if (
        declaration["dtype"] != "float64"
        or declaration["initial_time"] != "first_observation_uses_prior"
    ):
        raise ValueError("incompatible precision or initial observation time")
    for name in ("state_ids", "observation_ids"):
        values = declaration[name]
        if (
            not isinstance(values, list)
            or not 1 <= len(values) <= 4
            or any(not isinstance(v, str) or not v for v in values)
            or len(set(values)) != len(values)
        ):
            raise ValueError("unique ordered state/observation identities required")
    n, m = len(declaration["state_ids"]), len(declaration["observation_ids"])
    parameters: dict[str, Any] = {}
    options: dict[str, Any] = {}
    for section, target, separator in (
        ("InitialParameterization", parameters, " = "),
        ("ModelParameters", options, ": "),
    ):
        for line in sections[section].splitlines():
            match = re.fullmatch(r"([A-Za-z_]+)" + re.escape(separator) + r"(.+)", line)
            if not match:
                raise ValueError("one JSON assignment per source line required")
            key, literal = match.groups()
            if key in target:
                raise ValueError(f"duplicate source parameter: {key}")
            target[key] = (
                literal if key == "b_tensor_order" else _semantic_json(literal)
            )
    expected_options = {"num_timesteps", "random_seed"} | (
        {"b_tensor_order"} if family == "finite" else set()
    )
    if (
        set(options) != expected_options
        or type(options["num_timesteps"]) is not int
        or not 1 <= options["num_timesteps"] <= 8
        or type(options["random_seed"]) is not int
        or options["random_seed"] < 0
    ):
        raise ValueError("source time/seed/option contract unsupported")
    if family == "finite":
        if (
            set(parameters) != {"A", "B", "C", "D"}
            or options["b_tensor_order"] != "next_state_previous_state_action"
        ):
            raise ValueError("finite model parameters or B orientation unsupported")
        a, b, c, d = (
            _semantic_array(parameters[key], key) for key in ("A", "B", "C", "D")
        )
        if (
            a.shape != (m, n)
            or b.ndim != 3
            or b.shape[:2] != (n, n)
            or not 1 <= b.shape[2] <= 4
            or c.shape != (m,)
            or d.shape != (n,)
            or np.any(c != 0)
            or n ** options["num_timesteps"] > 4096
        ):
            raise ValueError("finite model dimensions or passive preference contract")
        for name, array in (("A", a), ("B", b), ("D", d)):
            if np.any(array < 0) or not np.allclose(
                array.sum(axis=0), 1, rtol=0, atol=1e-14
            ):
                raise ValueError(
                    f"{name}: nonnegative normalized probabilities required"
                )
        variables = f"s[{n},1,type=int]\no[{m},1,type=int]\nu[{b.shape[2]},1,type=int]"
        equations = (
            "p(s_0)=D; p(o_t|s_t)=A[o_t,s_t]; p(s_(t+1)|s_t,a_t)=B[s_(t+1),s_t,a_t]"
        )
        axes = {
            "A": ["observation", "state"],
            "B": ["next_state", "previous_state", "action"],
        }
        section_name = "ActInfPOMDP"
    else:
        shapes = {
            "F": (n, n),
            "H": (m, n),
            "Q": (n, n),
            "R": (m, m),
            "prior_mean": (n,),
            "prior_cov": (n, n),
        }
        if set(parameters) != set(shapes):
            raise ValueError("only passive stationary Gaussian parameters admitted")
        for key, shape in shapes.items():
            values = _semantic_array(parameters[key], key)
            if values.shape != shape:
                raise ValueError(f"{key}: source dimensions disagree")
            if key in {"Q", "R", "prior_cov"}:
                if not np.allclose(values, values.T, rtol=0, atol=1e-14):
                    raise ValueError(f"{key}: symmetric covariance required")
                try:
                    np.linalg.cholesky(values)
                except np.linalg.LinAlgError as exc:
                    raise ValueError(
                        f"{key}: positive definite covariance required"
                    ) from exc
        variables = f"x[{n},1,type=float]\ny[{m},1,type=float]"
        equations = (
            "x_0~N(prior_mean,prior_cov); x_(t+1)=F*x_t+N(0,Q); y_t=H*x_t+N(0,R)"
        )
        axes = {"F": ["next_state", "previous_state"], "H": ["observation", "state"]}
        section_name = "ActInfContinuous"
    if (
        sections["StateSpaceBlock"] != variables
        or sections["Equations"] != equations
        or sections["GNNSection"] != section_name
        or declaration["axes"] != axes
    ):
        raise ValueError("source equations, axes or variable identities unsupported")
    return {
        **declaration,
        "source_sha256": hashlib.sha256(source.encode()).hexdigest(),
        "parameters": parameters,
        "model_parameters": options,
        "equations": equations,
    }


def _semantic_replay(
    contract: dict[str, Any], result: dict[str, Any]
) -> dict[str, Any]:
    """Use forward recursion, independently of GNN's path/joint references."""
    import numpy as np

    p = contract["parameters"]
    n, m = len(contract["state_ids"]), len(contract["observation_ids"])
    t = contract["model_parameters"]["num_timesteps"]
    if contract["model"] == "finite":
        observations, actions = (
            result.get("observations"),
            result.get("transition_actions"),
        )
        if (
            not isinstance(observations, list)
            or len(observations) != t
            or any(type(v) is not int or not 0 <= v < m for v in observations)
        ):
            raise ValueError("finite observations must name every admitted timestep")
        a, b, prior = (_semantic_array(p[key], key) for key in ("A", "B", "D"))
        if (
            not isinstance(actions, list)
            or len(actions) != t - 1
            or any(type(v) is not int or not 0 <= v < b.shape[2] for v in actions)
        ):
            raise ValueError("one valid ordered action per transition required")
        beliefs = []
        for index, observation in enumerate(observations):
            predicted = prior if index == 0 else b[:, :, actions[index - 1]] @ prior
            weighted = a[observation, :] * predicted
            evidence = float(weighted.sum())
            if not math.isfinite(evidence) or evidence <= 0:
                raise ValueError("zero or nonfinite observation evidence")
            prior = weighted / evidence
            beliefs.append(prior.tolist())
        return {"beliefs": beliefs}
    observations = _semantic_array(
        result.get("observations_continuous"), "observations"
    )
    if observations.shape != (t, m):
        raise ValueError("Gaussian observations must cover every admitted timestep")
    if result.get("control_mode") != "passive":
        raise ValueError("Gaussian replay admits passive filtering only")
    controls = _semantic_array(result.get("controls"), "controls")
    if controls.shape != (t, n) or np.any(controls != 0):
        raise ValueError("passive filtering requires explicit zero controls")
    f, h, q, r, mean, covariance = (
        _semantic_array(p[key], key)
        for key in ("F", "H", "Q", "R", "prior_mean", "prior_cov")
    )
    means, covariances = [], []
    with np.errstate(over="raise", invalid="raise", divide="raise"):
        for index, observation in enumerate(observations):
            if index:
                mean, covariance = f @ mean, f @ covariance @ f.T + q
            cross = covariance @ h.T
            innovation = h @ cross + r
            if not np.isfinite(innovation).all() or not np.isfinite(
                np.linalg.cond(innovation)
            ):
                raise ValueError(
                    "Gaussian innovation covariance is numerically singular or nonfinite"
                )
            np.linalg.cholesky(innovation)
            gain = np.linalg.solve(innovation, cross.T).T
            mean = mean + gain @ (observation - h @ mean)
            residual = np.eye(n) - gain @ h
            covariance = residual @ covariance @ residual.T + gain @ r @ gain.T
            if not np.isfinite(mean).all() or not np.isfinite(covariance).all():
                raise ValueError("Gaussian derived mean/covariance is nonfinite")
            means.append(mean.tolist())
            covariances.append(covariance.tolist())
    return {"beliefs": means, "posterior_cov": covariances}


def semantic_formal_references(root: Path, family: str) -> list[dict[str, Any]]:
    """Resolve actual current theorem owners without manufacturing native proof."""
    from fep_lean.formal.declarations import formal_theorem_modules
    from fep_lean.formal.manifest import FORMAL_MODULES

    modules = formal_theorem_modules(root)
    resources = {item.lean_module: item.resource for item in FORMAL_MODULES}
    declarations: tuple[str, ...]
    if family == "finite":
        declarations = (
            "FEP.MeasureBayes.finite_posterior_reconstruction",
            "FEP.MeasureBayes.finite_posterior_normalized",
            "FEP.TemporalInference.forwardFilter_reconstruction",
            "FEP.TemporalInference.forwardFilter_sum_one",
            "FEP.TemporalInference.forwardEvidence_zero_boundary",
        )
        assumptions = [
            "Finite normalized nonnegative prior and emission/transition kernels.",
            "Strictly positive evidence at every selected observation.",
            "First observation uses the authored prior; action t acts between states t and t+1.",
        ]
        unmatched = [
            "No theorem here proves the GNN parser, translation, floating-point implementation or whole trace equivalent."
        ]
        alignment = "theorem_instance"
    elif family == "gaussian":
        declarations = (
            "FEPComposed.GaussianFilter.predictionBelief_law_eq_ouTransition",
            "FEPComposed.GaussianFilter.gaussianPDF_factorization",
            "FEPComposed.GaussianFilter.posteriorVariance_pos",
        )
        assumptions = [
            "Source prior/Q/R are symmetric positive definite; model and observations are finite dimensional.",
            "Numerical replay uses passive, first-observation-prior, float64 Gaussian filtering.",
        ]
        unmatched = [
            "Referenced Lean carrier is scalar OU dynamics with identity observation, not arbitrary matrix F/H/Q.",
            "Lean update predicts before observing; the GNN first observation consumes its prior directly.",
            "Native posterior equality is almost everywhere under the evidence law; this matrix-valued trace is not a proved instantiation.",
        ]
        alignment = "structural_analogue"
    else:
        raise ValueError("unsupported formal semantic family")
    references = []
    for declaration in declarations:
        module = modules[declaration]
        relative = "src/fep_lean/formal/" + resources[module]
        data = (root / relative).read_bytes()
        references.append(
            {
                "declaration": declaration,
                "lean_module": module,
                "source_path": relative,
                "source_sha256": hashlib.sha256(data).hexdigest(),
                "alignment": alignment,
                "assumptions": assumptions,
                "unmatched_assumptions": unmatched,
            }
        )
    return references


def _semantic_equal(left: Any, right: Any) -> bool:
    """Preserve JSON type/axis identity, including integer-versus-boolean roles."""
    return json.dumps(left, sort_keys=True, allow_nan=False) == json.dumps(
        right, sort_keys=True, allow_nan=False
    )


def _semantic_quantity(
    reference: Any, actual: Any, *, exact: bool = False
) -> dict[str, Any]:
    """Independent relation-aware diagnostic under the fixed float64 policy."""
    import numpy as np

    expected = _semantic_array(reference, "reference")
    candidate = _semantic_array(actual, "candidate")
    if expected.shape != candidate.shape:
        raise ValueError("semantic quantity shape mismatch")
    atol, rtol = (0.0, 0.0) if exact else (1e-12, 1e-10)
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        difference = np.abs(candidate - expected)
        relative = difference / np.maximum(np.abs(expected), np.finfo(np.float64).tiny)
    maximum, relative_maximum = float(difference.max()), float(relative.max())
    if not math.isfinite(maximum) or not math.isfinite(relative_maximum):
        raise ValueError("numerical diagnostic exceeds finite range")
    passed = bool(np.all(difference <= atol + rtol * np.abs(expected)))
    return {
        "status": "passed" if passed else "failed",
        "reason": "" if passed else "outside declared tolerance",
        "max_abs_error": maximum,
        "max_rel_error": relative_maximum,
        "atol": atol,
        "rtol": rtol,
        "shape": list(expected.shape),
    }


def _semantic_native_admission(
    contract: dict[str, Any], result: dict[str, Any]
) -> None:
    """Refuse explicit contradictory native claims even if saved rows omit them."""
    finite = contract["model"] == "finite"
    optional_identity = {
        "source_sha256": contract["source_sha256"],
        "state_ids": contract["state_ids"],
        "observation_ids": contract["observation_ids"],
        "model_kind": "discrete" if finite else "continuous",
        "schema_version": "bnlearn_fixed_action_filter_v1"
        if finite
        else "gnn_lgssm_filter_v1",
    }
    for key, expected in optional_identity.items():
        if key in result and not _semantic_equal(result[key], expected):
            raise ValueError(f"contradictory native {key}")
    source_identity = result.get("source_identity")
    if "source_identity" in result and not isinstance(source_identity, dict):
        raise TypeError("native source_identity must be a mapping")
    if (
        isinstance(source_identity, dict)
        and "source_sha256" in source_identity
        and source_identity["source_sha256"] != contract["source_sha256"]
    ):
        raise ValueError("contradictory native source_identity.source_sha256")
    frameworks = {"bnlearn"} if finite else {"jax", "numpyro", "pytorch", "ngclearn"}
    if result.get("framework") not in frameworks:
        raise ValueError("unsupported native framework declaration")
    if "success" in result and result["success"] is not True:
        raise ValueError("native result explicitly reports non-success")
    if "status" in result and (
        not isinstance(result["status"], str)
        or result["status"].lower()
        not in {
            "success",
            "completed",
        }
    ):
        raise ValueError("native result status is not successful")
    validation = result.get("validation")
    if "validation" in result and not isinstance(validation, dict):
        raise TypeError("native validation must be a mapping")
    if (
        isinstance(validation, dict)
        and "all_valid" in validation
        and validation["all_valid"] is not True
    ):
        raise ValueError("native validation explicitly failed")
    pending = [(len("validation"), validation, 0)]
    queued = 1
    while pending:
        path_chars, value, depth = pending.pop()
        if isinstance(value, dict):
            children = ((1 + len(key), child) for key, child in value.items())
        elif isinstance(value, list):
            children = (
                (2 + len(str(index)), child) for index, child in enumerate(value)
            )
        else:
            if value is False:
                raise ValueError("native result declares a nested validation failure")
            continue
        for suffix_chars, child in children:
            queued += 1
            if queued > 4096 or depth + 1 > 32 or path_chars + suffix_chars > 2048:
                raise ValueError("native validation exceeds node, depth or path budget")
            pending.append((path_chars + suffix_chars, child, depth + 1))


def _semantic_identities(contract: dict[str, Any]) -> dict[str, Any]:
    """Declared native semantics required by this exact filtering contract."""
    finite = contract["model"] == "finite"
    t = contract["model_parameters"]["num_timesteps"]
    return {
        "dtype": "float64",
        "initial_time": contract["initial_time"],
        "axes": contract["axes"],
        "conditioning_horizon": list(range(1, t + 1)),
        "num_timesteps": t,
        "num_states": len(contract["state_ids"]),
        "num_observations": len(contract["observation_ids"]),
        "random_seed": contract["model_parameters"]["random_seed"],
        "inference_contract": "bnlearn_fixed_action_filter_v1"
        if finite
        else "gnn_lgssm_filter_v1",
        "inference_mode": "exact_categorical_filtering"
        if finite
        else "gaussian_filtering",
        "control_mode": "fixed_transition_actions" if finite else "passive",
    }


def _semantic_assumptions(contract: dict[str, Any]) -> dict[str, Any]:
    """The whole versioned assumption boundary, including its non-proof prose."""
    return {
        **{
            key: contract[key]
            for key in (
                "question",
                "initial_time",
                "state_ids",
                "observation_ids",
                "axes",
            )
        },
        "conditioning_horizon": list(
            range(1, contract["model_parameters"]["num_timesteps"] + 1)
        ),
        "label_mapping": "Ordered source labels name numeric axes; native label provenance is not authenticated.",
        "scope": "One stationary factor, fixed exogenous actions or passive LGSSM; float64; at most eight times/four dimensions; no planning, coupled/hybrid semantics or universal equivalence.",
    }


def _semantic_identity_row(expected: Any, actual: Any) -> dict[str, Any]:
    if not _semantic_equal(expected, actual):
        raise ValueError("native scientific identity mismatch or unavailable")
    return {"status": "passed", "reason": "", "expected": expected, "actual": actual}


def _semantic_declared_rows(
    contract: dict[str, Any], result: dict[str, Any]
) -> dict[str, Any]:
    """Reconstruct every optional raw declaration and required framework row."""
    finite = contract["model"] == "finite"
    optional = {
        "source_sha256": contract["source_sha256"],
        "state_ids": contract["state_ids"],
        "observation_ids": contract["observation_ids"],
        "model_kind": "discrete" if finite else "continuous",
        "schema_version": "bnlearn_fixed_action_filter_v1"
        if finite
        else "gnn_lgssm_filter_v1",
        "success": True,
    }
    rows = {
        f"identity:{key}": _semantic_identity_row(value, result[key])
        for key, value in optional.items()
        if key in result
    }
    source_identity = result.get("source_identity")
    if isinstance(source_identity, dict) and "source_sha256" in source_identity:
        rows["identity:source_identity.source_sha256"] = _semantic_identity_row(
            contract["source_sha256"], source_identity["source_sha256"]
        )
    rows["identity:framework"] = {
        "status": "passed",
        "reason": "",
        "expected": ["bnlearn"]
        if finite
        else ["jax", "numpyro", "pytorch", "ngclearn"],
        "actual": result["framework"],
    }
    if "status" in result:
        rows["identity:status"] = {
            "status": "passed",
            "reason": "",
            "expected": ["success", "completed"],
            "actual": result["status"],
        }
    validation = result.get("validation")
    if isinstance(validation, dict) and "all_valid" in validation:
        rows["identity:validation.all_valid"] = _semantic_identity_row(
            True, validation["all_valid"]
        )
    return rows


def _semantic_candidate_validity(
    contract: dict[str, Any], result: dict[str, Any]
) -> dict[str, Any]:
    """Admit actual probabilities and positive Gaussian covariance before errors."""
    import numpy as np

    t, n = contract["model_parameters"]["num_timesteps"], len(contract["state_ids"])
    rows = {}
    for name, shape in (("beliefs", (t, n)), ("posterior_cov", (t, n, n))):
        if contract["model"] == "finite" and name == "posterior_cov":
            continue
        values = _semantic_array(result.get(name), name)
        if values.shape != shape:
            raise ValueError(f"{name}: candidate shape mismatch")
        if (
            name == "beliefs"
            and contract["model"] == "finite"
            and (
                np.any(values < 0)
                or np.any(values > 1)
                or not np.allclose(values.sum(axis=1), 1, atol=1e-12, rtol=0)
            )
        ):
            raise ValueError(
                "candidate categorical masses must be nonnegative probabilities with unit row mass"
            )
        if name == "posterior_cov":
            for covariance in values:
                scale = max(1.0, float(np.max(np.abs(covariance))))
                if not np.allclose(
                    covariance,
                    covariance.T,
                    rtol=0,
                    atol=64 * np.finfo(np.float64).eps * scale,
                ) or np.any(np.diag(covariance) <= 0):
                    raise ValueError(
                        "candidate covariance symmetry or positive variance failed"
                    )
                try:
                    np.linalg.cholesky(covariance)
                except np.linalg.LinAlgError as exc:
                    raise ValueError(
                        "candidate covariance must be positive definite"
                    ) from exc
        rows[f"validity:{name}"] = {"status": "passed", "reason": ""}
    return rows


def _semantic_expected_comparisons(
    contract: dict[str, Any],
    result: dict[str, Any],
    reference: dict[str, Any],
    program: Any,
) -> dict[str, Any]:
    """Rebuild the exact comparison roster and every diagnostic from raw bytes."""
    import numpy as np

    finite = contract["model"] == "finite"
    rows = {
        f"identity:{key}": _semantic_identity_row(value, result.get(key))
        for key, value in _semantic_identities(contract).items()
    }
    rows.update(_semantic_declared_rows(contract, result))
    rows.update(_semantic_candidate_validity(contract, result))
    if finite:
        rows["identity:action_semantics"] = _semantic_identity_row(
            "transition_into_next_state", result.get("action_semantics")
        )
    else:
        rows["controls"] = _semantic_quantity(
            np.zeros(
                (
                    contract["model_parameters"]["num_timesteps"],
                    len(contract["state_ids"]),
                )
            ).tolist(),
            result.get("controls"),
            exact=True,
        )
    parameters = result.get("parameters")
    if not isinstance(parameters, dict):
        raise TypeError("native parameter arrays unavailable")
    for key, value in contract["parameters"].items():
        if not (finite and key == "C"):
            rows[f"parameter:{key}"] = _semantic_quantity(
                value, parameters.get(key), exact=True
            )
    if program is not None:
        rows["identity:generated_script_sha256"] = _semantic_identity_row(
            program["sha256"], result.get("generated_script_sha256")
        )
    for key, value in reference["quantities"].items():
        rows[key] = _semantic_quantity(value, result.get(key))
    if any(row["status"] != "passed" for row in rows.values()):
        raise ValueError("raw result does not pass numerical and semantic admission")
    return rows


def _semantic_embedded_artifacts(
    witness: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], Any]:
    """Validate source/result/program bindings before allocating replay arrays."""
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
    if (
        not isinstance(witness, dict)
        or set(witness) != fields
        or witness.get("schema") != "gnn-semantic-witness-v2"
    ):
        raise ValueError("unsupported GNN semantic witness schema or fields")
    artifacts = witness["artifacts"]
    if not isinstance(artifacts, dict) or set(artifacts) != {
        "source",
        "result",
        "program",
    }:
        raise ValueError("unsupported artifact roster")
    for name in ("source", "result", "program"):
        artifact = artifacts[name]
        if name == "program" and artifact is None:
            continue
        if (
            not isinstance(artifact, dict)
            or set(artifact) != {"sha256", "utf8"}
            or not isinstance(artifact["utf8"], str)
        ):
            raise ValueError(f"{name}: invalid embedded artifact")
        raw = artifact["utf8"].encode("utf-8")
        limit = 1024 * 1024 if name == "source" else 16 * 1024 * 1024
        if len(raw) > limit or hashlib.sha256(raw).hexdigest() != artifact["sha256"]:
            raise ValueError(f"{name}: artifact digest or byte budget mismatch")
    contract = _semantic_source(artifacts["source"]["utf8"])
    if not _semantic_equal(contract, witness["source_contract"]):
        raise ValueError("source contract differs from independent source reading")
    result = _semantic_json(artifacts["result"]["utf8"])
    if not isinstance(result, dict):
        raise TypeError("native result must be a JSON object")
    return contract, result, artifacts["program"]


def _semantic_reference(
    contract: dict[str, Any],
    result: dict[str, Any],
    reference: Any,
    quantities: dict[str, Any],
) -> None:
    """Preserve exactly the observation, action-time and conditioning identities."""
    finite = contract["model"] == "finite"
    expected = {
        "algorithm": "finite_complete_path_enumeration"
        if finite
        else "joint_gaussian_prefix_conditioning",
        "observations": result["observations" if finite else "observations_continuous"],
        "transition_actions": result["transition_actions"] if finite else [],
        "conditioning_horizon": list(
            range(1, contract["model_parameters"]["num_timesteps"] + 1)
        ),
    }
    if (
        not isinstance(reference, dict)
        or set(reference) != {*expected, "quantities"}
        or any(
            not _semantic_equal(value, reference.get(key))
            for key, value in expected.items()
        )
        or not isinstance(reference["quantities"], dict)
        or set(reference["quantities"]) != set(quantities)
    ):
        raise ValueError("reference inputs, conditioning or quantity roster mismatch")


def audit_semantic_witness(witness: dict[str, Any], root: Path) -> dict[str, Any]:
    """Replay the entire admitted v2 record and resolve separately qualified laws.

    This checker imports neither GNN code nor its test references. Its recursive
    Bayes/Kalman updates independently compare GNN's path/joint references and
    raw native quantities. Byte bindings do not authenticate artifact production.
    """
    from copy import deepcopy

    from numpy.linalg import LinAlgError

    errors: list[str] = []
    replay: dict[str, Any] = {
        "algorithm": None,
        "status": "refused",
        "quantities": {},
        "comparisons": {},
        "errors": errors,
    }
    audit: dict[str, Any] = {
        "schema": "fep-semantic-witness-audit-v1",
        "status": "refused",
        "gnn_witness": deepcopy(witness),
        "independent_replay": replay,
        "formal_references": [],
        "formal_evidence": {
            "status": "referenced_not_compiled",
            "universal_equivalence": False,
            "native_claim_ready": False,
        },
        "execution_evidence": {
            "status": "artifact_only",
            "execution_source_verified": False,
        },
        "errors": errors,
    }
    try:
        contract, result, program = _semantic_embedded_artifacts(witness)
        _semantic_native_admission(contract, result)
        quantities = _semantic_replay(contract, result)
        replay["algorithm"] = (
            "finite_forward_filter"
            if contract["model"] == "finite"
            else "gaussian_kalman_joseph"
        )
        replay["quantities"] = quantities
        reference = witness["reference"]
        _semantic_reference(contract, result, reference, quantities)
        candidate = {key: result.get(key) for key in _semantic_identities(contract)}
        candidate.update(
            observations=reference["observations"],
            transition_actions=reference["transition_actions"],
            quantities={key: result.get(key) for key in quantities},
        )
        if not _semantic_equal(candidate, witness["candidate"]):
            raise ValueError("stored candidate differs from raw native artifact")
        comparisons = witness["comparisons"]
        expected_rows = _semantic_expected_comparisons(
            contract, result, reference, program
        )
        if (
            not isinstance(comparisons, dict)
            or any(not isinstance(row, dict) for row in comparisons.values())
            or not _semantic_equal(expected_rows, comparisons)
        ):
            raise ValueError(
                "comparison roster or content differs from independent raw-artifact replay"
            )
        if not _semantic_equal(_semantic_assumptions(contract), witness["assumptions"]):
            raise ValueError("source assumptions or evidence boundary mismatch")
        for key, expected in quantities.items():
            for target, value in (
                ("reference", reference["quantities"][key]),
                ("candidate", result.get(key)),
            ):
                row = _semantic_quantity(expected, value)
                replay["comparisons"][f"{target}:{key}"] = row
                if row["status"] != "passed":
                    errors.append(f"independent {target}:{key} disagreement")
        expected_execution = {
            "status": "artifact_only",
            "execution_source_verified": False,
            "reported_framework": result.get("framework"),
            "reported_versions": {
                key: result[key]
                for key in (
                    "python_version",
                    "numpy_version",
                    "jax_version",
                    "bnlearn_version",
                    "torch_version",
                )
                if key in result
            },
        }
        if not _semantic_equal(
            witness["formal_evidence"],
            {"status": "unavailable", "universal_equivalence": False},
        ) or not _semantic_equal(witness["execution_evidence"], expected_execution):
            raise ValueError("GNN proof or execution evidence boundary was promoted")
        if witness["status"] != "passed":
            raise ValueError(
                "GNN artifact does not report admitted numerical agreement"
            )
        audit["formal_references"] = semantic_formal_references(root, contract["model"])
        replay["status"] = "failed" if errors else "passed"
        audit["status"] = replay["status"]
    except (
        ValueError,
        TypeError,
        KeyError,
        OSError,
        OverflowError,
        FloatingPointError,
        LinAlgError,
        RecursionError,
    ) as exc:
        errors.append(str(exc))
    return audit
