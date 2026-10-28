"""Copy canonical methods inputs into generated installable YAML resources."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __name__ == "__main__":
    sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[2]
RESOURCES = {
    "catalogue_metadata.yaml": "config/catalogue_metadata.yaml",
    "theorem_maturity.yaml": "config/theorem_maturity.yaml",
    "formalism_relations.yaml": "config/formalism_relations.yaml",
    "positioning.yaml": "specs/openai-math-methods/positioning.yaml",
}


def validate_upstream_passports(root: Path) -> None:
    """Bind authored result identities to the reviewed lock without a corpus checkout."""
    from fep_formal.methods.model import PositioningError, load_yaml

    policy = load_yaml(root / RESOURCES["positioning.yaml"])
    table = policy.get("cross_corpus")
    if table is None:
        return
    lock_path = root / "specs/openai-math-methods/upstream.lock.json"
    lock_bytes = lock_path.read_bytes()

    def unique_mapping(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise PositioningError("duplicate upstream lock key")
            result[key] = value
        return result

    lock = json.loads(lock_bytes, object_pairs_hook=unique_mapping)
    pin = table["upstream_pin"]
    if any(
        pin[key] != lock[other]
        for key, other in (
            ("repository_url", "repository"),
            ("commit", "commit"),
            ("license", "license"),
        )
    ):
        raise PositioningError("cross-corpus upstream pin disagrees with reviewed lock")
    records = {row["path"]: row for row in lock["reviewed_files"]}
    if len(records) != len(lock["reviewed_files"]):
        raise PositioningError("duplicate upstream lock source path")
    for row in table["upstream_results"]:
        reference = records.get(row["source_path"])
        if (
            reference is None
            or reference["sha256"] != row["source_sha256"]
            or reference["url"] != row["source_url"]
        ):
            raise PositioningError(
                "cross-corpus result source disagrees with reviewed lock: " + row["id"]
            )
    if lock_path.read_bytes() != lock_bytes:
        raise PositioningError("upstream lock changed during passport validation")


def resource_projection_drift(root: Path) -> tuple[Path, ...]:
    """Compare exact authored bytes; never repair a drifted generated copy."""
    return tuple(
        root / "src/fep_formal/data" / name
        for name, owner in RESOURCES.items()
        if not (root / "src/fep_formal/data" / name).is_file()
        or (root / "src/fep_formal/data" / name).read_bytes()
        != (root / owner).read_bytes()
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    validate_upstream_passports(ROOT)
    if args.check:
        drift = resource_projection_drift(ROOT)
        if drift:
            print(
                "methods package resource drift: "
                + ", ".join(str(path.relative_to(ROOT)) for path in drift)
            )
            return 1
        print("methods package resources are current")
        return 0
    for name, owner in RESOURCES.items():
        (ROOT / "src/fep_formal/data" / name).write_bytes((ROOT / owner).read_bytes())
    print("wrote methods package resources from canonical owners")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
