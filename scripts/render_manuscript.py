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
    hand_maintained_module_cells,
    miscounted_area_labels,
    unattributed_row_declarations,
    unresolved_manuscript_references,
    unverified_non_catalogue_identifiers,
)
from fep_lean.formal.declarations import composed_theorem_declarations
from fep_lean.output.manuscript import (
    build_manuscript_vars,
    manuscript_projection_drift,
)
from fep_lean.output.publication_metadata import (
    PublicationMetadataError,
    pdf_metadata_drift,
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


# What the manuscript must typeset when the checkout is not the stamped tag.
# Each group is one disclosure; any token in a group satisfies it.
_SOURCE_DISCLOSURE_TOKENS: tuple[tuple[str, ...], ...] = (
    ("source.stamp", "source.short_commit", "source.commit"),
    ("source.published_note",),
)


def undisclosed_source_stamp(source_dir: Path) -> tuple[str, ...]:
    """Return the source disclosures the manuscript fails to typeset.

    The title page carries an authored ``paper.version``/``paper.date``. When
    the checkout has moved past that tag -- which it has for every commit
    between releases -- those two fields name a release that does not contain
    the numbers the render computed, and the audited PDF stamped v1.1.0 over a
    tree 15,033 Lean lines newer with nothing on the page to say so.

    Requiring the tag to match on every commit would make the mismatch a
    permanent failure rather than a disclosure. What must never happen is the
    mismatch going unsaid, so that is what is checked: the document must print
    the commit its numbers came from, and whether that commit is public.
    """

    typeset = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted(Path(source_dir).glob("*.md"))
    )
    return tuple(
        f"none of {{{', '.join(group)}}} is typeset"
        for group in _SOURCE_DISCLOSURE_TOKENS
        if not any(f"{{{{{token}}}}}" in typeset for token in group)
    )


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
    if stamp_status != 0:
        # A mismatch is allowed between releases; an undisclosed one is not.
        undisclosed = undisclosed_source_stamp(source_dir)
        if undisclosed:
            print("ERROR: the release-stamp mismatch is not disclosed to readers")
            for item in undisclosed:
                print(f"  {item}")
            return 1
        print("  disclosed: the manuscript typesets the source stamp it renders")
    unresolved = unresolved_placeholders(source_dir, variables)
    if unresolved:
        print("ERROR: unresolved manuscript placeholders")
        for item in unresolved:
            print(f"  {item}")
        return 1
    # The reference audits look past one reviewed set of names -- Mathlib
    # citations, this repository's own maintained Lean declarations, and
    # catalogue record fields. Each group is checked against the source it
    # claims, because a group comment is exactly what let a catalogue theorem
    # sit in the Mathlib group under a stripped prefix and read as prior art.
    pinned = project_root / "lean" / ".lake" / "packages" / "mathlib"
    mathlib_root: Path | None = pinned if (pinned / "Mathlib").is_dir() else None
    if mathlib_root is None:
        print(
            "  unchecked: the pinned Mathlib checkout is absent, so the audit's "
            "Mathlib citations are taken on trust; run `lake exe cache get` in lean/"
        )
    miscategorised = unverified_non_catalogue_identifiers(mathlib_root)
    if miscategorised:
        print("ERROR: allowlisted identifiers their claimed source does not contain")
        for item in miscategorised:
            print(f"  {item}")
        return 1
    stale_references = unresolved_manuscript_reference_report(source_dir)
    if stale_references:
        print("ERROR: stale theorem identifiers in the manuscript")
        for item in stale_references:
            print(f"  {item}")
        return 1
    # The framework tables' module column is computed from each row's own Lean
    # imports. Before it was generated, a hand-typed cell named a module the
    # row never imported on forty-two of seventy-one rows; nothing but this
    # check stops one being typed back in, because a literal module name
    # resolves as prose everywhere else.
    hand_typed = hand_maintained_module_cells(source_dir)
    if hand_typed:
        print("ERROR: hand-typed module cells in the manuscript")
        for item in hand_typed:
            print(f"  {item}")
        return 1
    # A row count labelled "theorems" is the same failure one level up: the
    # token resolves, so every placeholder gate passes, while the sentence
    # states a proof total the catalogue does not have. Two such sentences
    # shipped in a rendered PDF three lines below a heading that already said
    # "Rows"; only the heading had been fixed.
    miscounted = miscounted_area_labels(source_dir)
    if miscounted:
        print("ERROR: area row counts labelled as proved declarations")
        for item in miscounted:
            print(f"  {item}")
        return 1
    # ``manuscript/preamble.md`` is copied verbatim by the renderer and never
    # placeholder-substituted, so the PDF ``/Info`` subject and keyword strings
    # it carries are the one metadata copy the placeholder gate cannot check.
    try:
        metadata_drift = pdf_metadata_drift(project_root)
    except PublicationMetadataError as exc:
        print(f"ERROR: cannot validate PDF metadata: {exc}")
        return 1
    if metadata_drift:
        print("ERROR: PDF metadata in manuscript/preamble.md has drifted")
        for item in metadata_drift:
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
