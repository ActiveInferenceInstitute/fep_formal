"""Validated, deterministic registry for family-owned Lean topic bodies."""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType, ModuleType

from fep_lean.lean_source import LEAN_THEOREM_RE, lean_code_without_comments

from .bodies import (
    causal_blankets_interventions,
    closed_loop_policy_trees,
    collective_inference,
    continuous_time_thermodynamics,
    controlled_markov,
    core_active_inference,
    core_bayesian_mechanics,
    core_free_energy,
    core_information_geometry,
    core_thermodynamics,
    exponential_family_geometry,
    finite_sample_risk_calibration,
    geometric_optimization,
    learning_theory,
    measure_bayesian_inversion,
    native_blanket_independence,
    path_thermodynamics,
    predictive_coding_generalized,
    standalone_efe_formalizations,
    temporal_inference,
    variational_duality,
)
from .latex import build_theorem_latex, build_topic_latex_equations

_TOPIC_ID_RE = re.compile(r"^fep-(\d{3})$")
_NAMESPACE_RE = re.compile(r"^\s*namespace\s+([A-Za-z][A-Za-z0-9_]*)\s*$", re.MULTILINE)
_END_RE = re.compile(r"^\s*end\s+([A-Za-z][A-Za-z0-9_]*)\s*$", re.MULTILINE)
_DECLARATION_RE = re.compile(
    r"^\s*(?:noncomputable\s+)?(?:theorem|lemma|def|abbrev|structure|inductive)\s+"
    r"([A-Za-z][A-Za-z0-9_]*)",
    re.MULTILINE,
)
_THEOREM_RE = LEAN_THEOREM_RE


class RegistryValidationError(ValueError):
    """Raised when a body module cannot participate in the canonical registry."""


@dataclass(frozen=True)
class BodyModule:
    """One explicit family/module entry in the body-source manifest."""

    family: str
    module: ModuleType

    @property
    def import_name(self) -> str:
        """Return the stable Python import name for this source owner."""
        return self.module.__name__

    @property
    def source_relative_path(self) -> str:
        """Return the checkout-relative path derived from the import name."""
        return "src/" + self.import_name.replace(".", "/") + ".py"

    @property
    def bodies(self) -> Mapping[str, str]:
        """Return the module's sole canonical body mapping."""
        value = getattr(self.module, "BODIES", None)
        if not isinstance(value, dict):
            raise RegistryValidationError(
                f"{self.import_name} must export BODIES as a dict[str, str]"
            )
        return value


BODY_MODULE_MANIFEST: tuple[BodyModule, ...] = (
    BodyModule("core-free-energy", core_free_energy),
    BodyModule("core-active-inference", core_active_inference),
    BodyModule("core-bayesian-mechanics", core_bayesian_mechanics),
    BodyModule("core-information-geometry", core_information_geometry),
    BodyModule("core-thermodynamics", core_thermodynamics),
    BodyModule("measure-bayesian-inversion", measure_bayesian_inversion),
    BodyModule(
        "variational-duality-and-information-bounds",
        variational_duality,
    ),
    BodyModule("control-and-planning-as-inference", controlled_markov),
    BodyModule("temporal-and-hierarchical-inference", temporal_inference),
    BodyModule(
        "causal-blankets-and-interventions",
        causal_blankets_interventions,
    ),
    BodyModule(
        "predictive-coding-and-generalized-coordinates",
        predictive_coding_generalized,
    ),
    BodyModule("path-space-stochastic-thermodynamics", path_thermodynamics),
    BodyModule(
        "information-geometry-and-geometric-optimization",
        geometric_optimization,
    ),
    BodyModule(
        "collective-and-multiagent-active-inference",
        collective_inference,
    ),
    BodyModule(
        "learning-concentration-and-model-evidence",
        learning_theory,
    ),
    BodyModule(
        "finite-sample-risk-and-calibration",
        finite_sample_risk_calibration,
    ),
    BodyModule(
        "closed-loop-policy-trees-and-efe",
        closed_loop_policy_trees,
    ),
    BodyModule(
        "finite-to-native-blanket-transfer",
        native_blanket_independence,
    ),
    BodyModule(
        "finite-exponential-family-dual-geometry",
        exponential_family_geometry,
    ),
    BodyModule(
        "two-state-continuous-time-thermodynamics",
        continuous_time_thermodynamics,
    ),
    BodyModule(
        "standalone-efe-formalizations",
        standalone_efe_formalizations,
    ),
)


def _validate_body(topic_id: str, body: str) -> tuple[str, tuple[str, ...]]:
    match = _TOPIC_ID_RE.fullmatch(topic_id)
    if match is None:
        raise RegistryValidationError(
            f"malformed topic ID {topic_id!r}; expected fep-NNN"
        )
    if not body:
        raise RegistryValidationError(f"{topic_id}: canonical Lean body is empty")
    digits = match.group(1)
    expected_namespace = f"FEP{digits}"
    code = lean_code_without_comments(body)
    namespaces = _NAMESPACE_RE.findall(code)
    if namespaces != [expected_namespace]:
        raise RegistryValidationError(
            f"{topic_id}: namespaces must be exactly [{expected_namespace!r}], "
            f"found {namespaces!r}"
        )
    if _END_RE.findall(code) != [expected_namespace]:
        raise RegistryValidationError(
            f"{topic_id}: namespace {expected_namespace!r} must have one named end"
        )
    declarations = tuple(_DECLARATION_RE.findall(code))
    if not declarations:
        raise RegistryValidationError(f"{topic_id}: body declares no Lean symbols")
    duplicate_declarations = sorted(
        {name for name in declarations if declarations.count(name) > 1}
    )
    if duplicate_declarations:
        raise RegistryValidationError(
            f"{topic_id}: duplicate declarations in {expected_namespace}: "
            + ", ".join(duplicate_declarations)
        )
    theorem_names = tuple(_THEOREM_RE.findall(code))
    if not theorem_names:
        raise RegistryValidationError(f"{topic_id}: body declares no theorems")
    wrong_prefix = sorted(
        name for name in theorem_names if not name.startswith(f"fep{digits}_")
    )
    if wrong_prefix:
        raise RegistryValidationError(
            f"{topic_id}: theorem names must start with fep{digits}_: "
            + ", ".join(wrong_prefix)
        )
    return expected_namespace, declarations


def build_body_registry(
    modules: Iterable[BodyModule],
) -> Mapping[str, str]:
    """Validate explicit body modules and return an immutable ID-ordered mapping."""
    entries = tuple(modules)
    families = tuple(entry.family for entry in entries)
    if len(families) != len(set(families)):
        raise RegistryValidationError("body module families must be unique")
    import_names = tuple(entry.import_name for entry in entries)
    if len(import_names) != len(set(import_names)):
        raise RegistryValidationError("body module import names must be unique")

    merged: dict[str, str] = {}
    namespaces: dict[str, str] = {}
    qualified_declarations: dict[str, str] = {}
    for entry in entries:
        for topic_id, body in entry.bodies.items():
            if not isinstance(topic_id, str) or not isinstance(body, str):
                raise RegistryValidationError(
                    f"{entry.import_name}: BODIES must map strings to strings"
                )
            if topic_id in merged:
                raise RegistryValidationError(f"duplicate topic ID: {topic_id}")
            namespace, declarations = _validate_body(topic_id, body)
            if namespace in namespaces:
                raise RegistryValidationError(
                    f"duplicate topic namespace {namespace}: "
                    f"{namespaces[namespace]} and {topic_id}"
                )
            namespaces[namespace] = topic_id
            for declaration in declarations:
                qualified = f"{namespace}.{declaration}"
                if qualified in qualified_declarations:
                    raise RegistryValidationError(
                        f"duplicate qualified declaration {qualified}: "
                        f"{qualified_declarations[qualified]} and {topic_id}"
                    )
                qualified_declarations[qualified] = topic_id
            merged[topic_id] = body
    ordered = dict(sorted(merged.items()))
    return MappingProxyType(ordered)


def validate_body_roster(bodies: Mapping[str, str], topic_ids: Sequence[str]) -> None:
    """Reject any missing, extra, or reordered registry body against a roster seal."""
    expected = tuple(topic_ids)
    actual = tuple(bodies)
    if actual != expected:
        missing = tuple(topic_id for topic_id in expected if topic_id not in bodies)
        extra = tuple(topic_id for topic_id in actual if topic_id not in expected)
        raise RegistryValidationError(
            "body registry does not match the sealed roster: "
            f"missing={missing!r} extra={extra!r} order_matches={actual == expected}"
        )


def validate_body_family_ownership(
    topic_families: Mapping[str, str],
    *,
    manifest: Sequence[BodyModule] = BODY_MODULE_MANIFEST,
) -> None:
    """Require every topic body to live in its metadata-declared family module."""
    for entry in manifest:
        for topic_id in entry.bodies:
            expected = topic_families.get(topic_id)
            if expected != entry.family:
                raise RegistryValidationError(
                    f"{topic_id}: family owner mismatch; metadata={expected!r} "
                    f"body_module={entry.family!r}"
                )


def assert_roster(topic_ids: Sequence[str]) -> None:
    """Validate the canonical registry against an externally sealed roster."""
    validate_body_roster(BODIES, topic_ids)


def body_source_relative_paths(
    manifest: Sequence[BodyModule] = BODY_MODULE_MANIFEST,
) -> tuple[str, ...]:
    """Return canonical body source paths from the sole module manifest."""
    return tuple(entry.source_relative_path for entry in manifest)


BODIES: Mapping[str, str] = build_body_registry(BODY_MODULE_MANIFEST)
THEOREM_LATEX = MappingProxyType(build_theorem_latex(BODIES))
LATEX_EQUATIONS = MappingProxyType(
    {
        topic_id: tuple(rows)
        for topic_id, rows in build_topic_latex_equations(BODIES, THEOREM_LATEX).items()
    }
)

__all__ = [
    "BODIES",
    "BODY_MODULE_MANIFEST",
    "LATEX_EQUATIONS",
    "THEOREM_LATEX",
    "BodyModule",
    "RegistryValidationError",
    "assert_roster",
    "body_source_relative_paths",
    "build_body_registry",
    "validate_body_family_ownership",
    "validate_body_roster",
]
