#!/usr/bin/env python3
"""Validate or render manuscript variables without mutating authored sources.

Every run prints the source stamp -- the commit the numbers were computed from
and whether the checkout was clean -- because a title page carrying an authored
``paper.version`` cannot say that on its own. Pass ``--require-release-stamp``
before tagging or archiving to make a checkout that has moved past the stamped
tag a hard failure.

Usage:
    uv run python scripts/render_manuscript.py --check
    uv run python scripts/render_manuscript.py
    uv run python scripts/render_manuscript.py --output-dir output/manuscript
    uv run python scripts/render_manuscript.py --check --require-release-stamp
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

# A direct check/render invocation must not update checkout-local bytecode.
if __name__ == "__main__":
    sys.dont_write_bytecode = True

import yaml

from fep_lean.catalogue import FEPTopicCatalogue
from fep_lean.catalogue.references import (
    unattributed_row_declarations,
    unresolved_manuscript_references,
)
from fep_lean.formal.declarations import composed_theorem_declarations
from fep_lean.output.manuscript import (
    build_manuscript_vars,
    manuscript_projection_drift,
)
from fep_lean.output.rendering import (
    ManuscriptRenderError,
    render_manuscript,
    unresolved_placeholders,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="fail-closed source-to-build manuscript rendering"
    )
    parser.add_argument(
        "--check",
        "--dry-run",
        dest="check",
        action="store_true",
        help="validate that every placeholder resolves without writing output",
    )
    parser.add_argument(
        "--require-release-stamp",
        action="store_true",
        help="fail when the checkout is not exactly the tag named by "
        "manuscript/config.yaml paper.version (run before tagging or archiving)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="render destination (default: output/manuscript)",
    )
    return parser


def report_source_stamp(project_root: Path, variables: dict[str, Any]) -> int:
    """Print the render's source provenance; return 1 on a version/tag mismatch.

    ``manuscript/config.yaml`` stamps an authored ``paper.version`` on the title
    page. When the checkout has moved past that tag, every live-token count in
    the paper describes a tree the stamped release does not contain, and a
    reader who fetches the tag cannot reproduce one of them.
    """

    source = variables.get("source")
    if not isinstance(source, dict):
        print("WARNING: no source stamp available for this render")
        return 0
    print(f"Source stamp: {source.get('stamp', 'unknown')}")
    print(f"  git describe: {source.get('describe', 'unknown')}")
    config_path = project_root / "manuscript" / "config.yaml"
    declared = ""
    if config_path.is_file():
        config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        paper = config.get("paper")
        if isinstance(paper, dict):
            declared = str(paper.get("version", ""))
    exact_tag = str(source.get("exact_tag", "none"))
    normalized_tag = exact_tag.removeprefix("v")
    if declared and normalized_tag == declared and source.get("dirty") == "false":
        print(f"  release stamp: checkout is exactly v{declared}")
        return 0
    print(
        f"  release stamp MISMATCH: config.yaml paper.version is "
        f"{declared or '(unset)'} but the checkout is "
        f"{source.get('describe', 'unknown')}"
    )
    print(
        "  the title page will name a release that does not contain the "
        "numbers this render computes; typeset {{source.stamp}} alongside it"
    )
    return 1


def unresolved_manuscript_reference_report(source_dir: Path) -> tuple[str, ...]:
    """Return every manuscript identifier that names no canonical declaration.

    The abstract claims that "stale theorem identifiers block publication". Until
    this call existed, nothing on the render path checked one: the audit lived in
    ``docs/theorem_ref_audit.py``, which no gate invoked. Both forms are checked --
    the ``fepNNN_`` prefix form inside prose and ``lean`` fences, and the
    un-prefixed identifiers a line attributes to a ``fep-NNN`` row.
    """

    composed = {
        declaration.rsplit(".", 1)[-1]
        for declaration in composed_theorem_declarations()
    }
    # A name that is both ``fepNNN_``-shaped and quoted beside its row matches
    # both audits; report each location once, in file order.
    found = [
        *unresolved_manuscript_references(source_dir, additional_declarations=composed),
        *unattributed_row_declarations(source_dir, additional_declarations=composed),
    ]
    return tuple(dict.fromkeys(found))


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    project_root = Path(__file__).resolve().parents[1]
    source_dir = project_root / "manuscript"
    try:
        catalogue = FEPTopicCatalogue.from_yaml(project_root / "config" / "topics.yaml")
        variables = build_manuscript_vars(
            catalogue,
            project_root,
            cache_test_count=not args.check,
        )
        drift = manuscript_projection_drift(
            project_root,
            catalogue,
            expected_variables=variables,
        )
    except (OSError, ValueError) as exc:
        print(f"ERROR: cannot validate manuscript projections: {exc}")
        return 1
    if drift:
        print("ERROR: stale manuscript projections")
        for path in drift:
            try:
                display_path = path.relative_to(project_root)
            except ValueError:
                display_path = path
            print(f"  {display_path}")
        return 1
    stamp_status = report_source_stamp(project_root, variables)
    if args.require_release_stamp and stamp_status != 0:
        return stamp_status
    unresolved = unresolved_placeholders(source_dir, variables)
    if unresolved:
        print("ERROR: unresolved manuscript placeholders")
        for item in unresolved:
            print(f"  {item}")
        return 1
    stale_references = unresolved_manuscript_reference_report(source_dir)
    if stale_references:
        print("ERROR: stale theorem identifiers in the manuscript")
        for item in stale_references:
            print(f"  {item}")
        return 1
    if args.check:
        print(
            "OK: manuscript projections are current and every authored "
            "placeholder resolves"
        )
        return 0
    destination = (
        args.output_dir
        if args.output_dir is not None
        else project_root / "output" / "manuscript"
    )
    try:
        rendered = render_manuscript(source_dir, destination, variables)
    except ManuscriptRenderError as exc:
        print(f"ERROR: {exc}")
        return 1
    print(f"Rendered {len(rendered)} manuscript files to {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
