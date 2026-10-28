# /// script
# requires-python = ">=3.14"
# dependencies = []
# ///
# How to run: uv run python specs/cascadia-experiments/proof_impact.py CONDITION
"""Compare exact Cascadia inputs and report the proof obligations a change reopens."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from fractions import Fraction
from pathlib import Path
from types import ModuleType
from typing import Final

REFERENCE: Final = Path(__file__).resolve().parents[1] / "cascadia-geo-act-proof"
REVIEWS: Final = {
    "A": (
        "likelihood stochasticity",
        "exact Bayes evidence and posterior",
        "score bridge instance",
    ),
    "B": (
        "transition stochasticity and locality",
        "light-cone lower bound",
        "tight homing plan",
    ),
    "C": ("log-preference softmax", "score and policy-posterior bridge instances"),
    "D": (
        "initial-prior stochasticity and support",
        "light-cone start set",
        "exact first update",
    ),
    "E": ("habit stochasticity", "policy-posterior bridge instance"),
    "carrier": (
        "state and observation carrier identities",
        "all indexed table witnesses",
    ),
    "geometry": (
        "recorded H3 adjacency",
        "river locality",
        "reachability and landmarks",
    ),
    "clock": ("physical-time interpretation; step-count proof alone is insufficient",),
}


@dataclass(frozen=True, slots=True)
class Component:
    name: str
    exact_value: str


@dataclass(frozen=True, slots=True)
class ModelInputs:
    components: tuple[Component, ...]
    file_sha256: tuple[tuple[str, str], ...]


@dataclass(frozen=True, slots=True)
class ProofImpact:
    """A review worksheet; this tool never issues a native proof receipt."""

    schema_version: str
    changed_components: tuple[str, ...]
    required_reviews: tuple[str, ...]
    reference_file_sha256: tuple[tuple[str, str], ...]
    candidate_file_sha256: tuple[tuple[str, str], ...]
    tooling_sha256: tuple[tuple[str, str], ...]
    reference_bytes_match: bool
    export_reproduction_required: bool = True
    native_claim_ready: bool = False


def generator_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "cascadia_impact_generator", REFERENCE / "generate_probe.py"
    )
    if spec is None or spec.loader is None:
        message = "reference fixture validator is unavailable"
        raise ImportError(message)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_inputs(folder: Path, generator: ModuleType) -> ModelInputs:
    """Use the exact fixture validator, then compare normalized rational values."""
    data = generator.load_fixtures(folder)
    domain = generator.load_json(folder / "smith_river_homing.domain.json")
    artifact = generator.load_json(folder / "smith_river_homing.geo-infer.json")
    for name in ("D", "E"):
        nums = data[f"{name.lower()}_num"]
        denominator = data[f"{name.lower()}_den"]
        if tuple(Fraction(v) for v in domain["exact"][name]) != tuple(
            Fraction(v, denominator) for v in nums
        ):
            message = f"sidecar {name} differs from artifact {name}"
            raise generator.FixtureError(message)
    if tuple(Fraction(v) for v in domain["C"]) != tuple(data["c"]):
        message = "sidecar C differs from artifact C"
        raise generator.FixtureError(message)
    values = {
        "A": str(
            tuple(Fraction(v, data["a_den"]) for row in data["a_num"] for v in row)
        ),
        "B": str(
            tuple(
                Fraction(v, data["b_den"])
                for plane in data["b_num"]
                for row in plane
                for v in row
            )
        ),
        "C": str(tuple(data["c"])),
        "D": str(tuple(Fraction(v, data["d_den"]) for v in data["d_num"])),
        "E": str(tuple(Fraction(v, data["e_den"]) for v in data["e_num"])),
        "carrier": json.dumps(
            [data["cells"], data["observation_labels"], domain["action_labels"]]
        ),
        "geometry": json.dumps(
            [data["relations"], data["adjacency"], data["landmarks"], data["roles"]],
            sort_keys=True,
        ),
        "clock": str(Fraction(artifact["time"]["step_seconds"])),
    }
    files = tuple(
        (name, hashlib.sha256((folder / name).read_bytes()).hexdigest())
        for name in (
            "smith_river_homing.gnn.md",
            "smith_river_homing.geo-infer.json",
            "smith_river_homing.domain.json",
        )
    )
    return ModelInputs(
        tuple(Component(name, value) for name, value in values.items()), files
    )


def assess(candidate: Path) -> ProofImpact:
    """Identify changed mathematical inputs without promoting reference evidence."""
    generator = generator_module()
    reference = load_inputs(REFERENCE / "fixtures", generator)
    variant = load_inputs(candidate, generator)
    changed = tuple(
        right.name
        for left, right in zip(reference.components, variant.components, strict=True)
        if left.exact_value != right.exact_value
    )
    reviews = tuple(
        dict.fromkeys(review for name in changed for review in REVIEWS[name])
    )
    tooling = tuple(
        (name, hashlib.sha256(path.read_bytes()).hexdigest())
        for name, path in (
            ("proof_impact.py", Path(__file__)),
            ("generate_probe.py", REFERENCE / "generate_probe.py"),
        )
    )
    return ProofImpact(
        "fep-formal/cascadia-proof-impact/1",
        changed,
        reviews,
        reference.file_sha256,
        variant.file_sha256,
        tooling,
        reference.file_sha256 == variant.file_sha256,
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("condition", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    content = (
        json.dumps(asdict(assess(args.condition)), indent=2, sort_keys=True) + "\n"
    )
    if args.output is not None:
        with args.output.open("x", encoding="utf-8") as stream:
            stream.write(content)
    print(content, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
