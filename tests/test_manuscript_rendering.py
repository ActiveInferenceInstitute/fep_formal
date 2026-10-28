"""Publication rendering preserves sources and rejects unknown variables."""

from __future__ import annotations

import contextlib
import importlib.util
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path
from types import ModuleType

import pytest
import yaml

from fep_formal.catalogue import FEPTopicCatalogue
from fep_formal.methods import (
    build_mathematical_positioning,
    export_mathematical_positioning,
)
from fep_formal.output import manuscript as manuscript_module
from fep_formal.output.formal_kernel_dashboard import write_formal_kernel_dashboard
from fep_formal.output.formalism_atlas import write_formalism_atlas
from fep_formal.output.manuscript import (
    build_manuscript_vars,
    manuscript_projection_drift,
    write_manuscript_vars,
    write_unified_formalism_appendix_markdown,
)
from fep_formal.output.render_log import stale_render_defects
from fep_formal.output.rendering import (
    MANUSCRIPT_ASSETS,
    ManuscriptRenderError,
    manuscript_source_files,
    render_manuscript,
    substitute_placeholders,
    unreproducible_command_blocks,
    unresolved_placeholders,
)
from fep_formal.output.svg_raster import write_manuscript_figure_pngs
from fep_formal.pipeline import FEPPipeline

PROJ = Path(__file__).resolve().parent.parent
pytest_plugins = ["tests._support.catalogue_project"]


def _graphical_abstract_variables() -> dict[str, object]:
    return {
        "publication": {
            "graphical_abstract": {
                "source_path": "manuscript/assets/graphical-abstract.png",
                "render_path": "assets/graphical-abstract.png",
                "media_type": "image/png",
                "width_px": 1536,
                "height_px": 1024,
                "sha256": (
                    "969c7e959360545b3fff95963a9d88a8f7addb7f6d536a1b983da8032cbd9ccd"
                ),
                "alt_text": "Graphical abstract fixture",
            }
        }
    }


def _write_graphical_abstract_render_fixture(project_root: Path) -> Path:
    source = project_root / "manuscript"
    source.mkdir(parents=True)
    shutil.copy2(PROJ / "manuscript/config.yaml", source / "config.yaml")
    (source / "00_front_matter.md").write_text(
        "![Graphical abstract]({{publication.graphical_abstract.render_path}})\n",
        encoding="utf-8",
    )
    _stage_asset_roster(project_root)
    return source


def _stage_asset_roster(project_root: Path) -> None:
    """Stage every MANUSCRIPT_ASSETS source; copying is roster-driven."""
    for source_relative, _destination_relative in MANUSCRIPT_ASSETS.values():
        source_path = project_root / source_relative
        source_path.parent.mkdir(parents=True, exist_ok=True)
        source_path.write_bytes(b"<fixture/>\n")


def _copy_publication_metadata(project_root: Path) -> None:
    manuscript = project_root / "manuscript"
    shutil.copy2(PROJ / "CITATION.cff", project_root / "CITATION.cff")
    shutil.copy2(PROJ / "manuscript/config.yaml", manuscript / "config.yaml")
    shutil.copytree(PROJ / "manuscript/assets", manuscript / "assets")


def _load_render_script() -> ModuleType:
    script = PROJ / "scripts" / "render_manuscript.py"
    spec = importlib.util.spec_from_file_location("fep_lean_render_manuscript", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# Runs the real render-check script against the real tree: its Mathlib-citation
# verification needs the pinned lean/.lake/packages/mathlib checkout, so it is
# a workspace test like the other serial_lean files, not a CI-python test.
@pytest.mark.serial_lean
def test_render_manuscript_check_disables_test_count_cache(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_render_script()
    catalogue = object()
    cache_modes: list[bool] = []
    monkeypatch.setattr(
        module.FEPTopicCatalogue,
        "from_yaml",
        staticmethod(lambda _path: catalogue),
    )

    def build_variables(
        _catalogue: object,
        _root: Path,
        *,
        cache_test_count: bool = True,
    ) -> dict[str, object]:
        cache_modes.append(cache_test_count)
        return {}

    monkeypatch.setattr(module, "build_manuscript_vars", build_variables)
    monkeypatch.setattr(module, "manuscript_projection_drift", lambda *a, **k: ())
    monkeypatch.setattr(module, "unresolved_placeholders", lambda *a, **k: ())

    assert module.main(["--check", "--allow-unavailable-evidence"]) == 0
    assert cache_modes == [False]


def test_render_manuscript_fails_closed_without_mutating_source(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    destination = tmp_path / "build"
    source.mkdir()
    chapter = source / "01_chapter.md"
    original = "Verified: {{verify.claim_ready}}; missing: {{unknown.value}}\n"
    chapter.write_text(original, encoding="utf-8")

    with pytest.raises(ManuscriptRenderError, match="unknown.value"):
        render_manuscript(source, destination, {"verify": {"claim_ready": True}})

    assert chapter.read_text(encoding="utf-8") == original
    assert not destination.exists()


def test_render_manuscript_rejects_multiline_unknown_before_any_output(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    destination = tmp_path / "build"
    source.mkdir()
    (source / "01_good.md").write_text("Known: {{known}}\n", encoding="utf-8")
    (source / "02_bad.md").write_text("Unknown: {{unknown\nvalue}}\n", encoding="utf-8")

    with pytest.raises(ManuscriptRenderError, match="unknown value"):
        render_manuscript(source, destination, {"known": "resolved"})

    assert not destination.exists()


@pytest.mark.parametrize("malformed", ("{{unknown", "{{unknown}"))
def test_render_manuscript_rejects_malformed_delimiter_before_any_output(
    tmp_path: Path, malformed: str
) -> None:
    source = tmp_path / "source"
    destination = tmp_path / "build"
    source.mkdir()
    (source / "01_good.md").write_text("Known: {{known}}\n", encoding="utf-8")
    (source / "02_bad.md").write_text(f"Malformed: {malformed}\n", encoding="utf-8")

    with pytest.raises(ManuscriptRenderError, match="delimiter"):
        render_manuscript(source, destination, {"known": "resolved"})

    assert not destination.exists()


def test_all_authored_manuscript_placeholders_are_in_typed_projection() -> None:
    catalogue = FEPTopicCatalogue.from_yaml(PROJ / "config" / "topics.yaml")
    variables = build_manuscript_vars(catalogue, PROJ)
    source_names = tuple(
        path.name for path in manuscript_source_files(PROJ / "manuscript")
    )

    assert source_names[0] == "00_front_matter.md"
    assert source_names[-1] == "08b_mathematical_positioning_supplement.md"
    assert "08_appendix_a_overview.md" in source_names
    assert all(name[0].isdigit() for name in source_names)
    assert "preamble.md" not in source_names
    assert unresolved_placeholders(PROJ / "manuscript", variables) == ()


@pytest.mark.serial_lean
def test_live_render_includes_author_block_and_canonical_graphical_abstract(
    tmp_path: Path, catalogue_project: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Produce the real assets in a private checkout; a clean source tree has no
    # pre-existing output/figures, and shared report state is not a fixture.
    monkeypatch.setenv("GAUSS_HOME", str(tmp_path / "gauss"))
    result = FEPPipeline(
        catalogue_project, output_root=catalogue_project / "output"
    ).run(mode="catalogue")
    assert result.complete
    assert result.verified_topics == 0
    write_formalism_atlas(catalogue_project)
    write_formal_kernel_dashboard(catalogue_project)
    export_mathematical_positioning(
        build_mathematical_positioning(catalogue_project),
        catalogue_project / "docs/mathematical-positioning",
    )
    write_manuscript_figure_pngs(catalogue_project)
    catalogue = FEPTopicCatalogue.from_yaml(
        catalogue_project / "config" / "topics.yaml"
    )
    variables = build_manuscript_vars(catalogue, catalogue_project)

    rendered = render_manuscript(
        catalogue_project / "manuscript", tmp_path / "build", variables
    )

    assert rendered[0].name == "00_front_matter.md"
    front_matter = rendered[0].read_text(encoding="utf-8")
    assert "Daniel Ari Friedman" in front_matter
    assert "Active Inference Institute" in front_matter
    assert "https://orcid.org/0000-0001-6232-9096" in front_matter
    assert "daniel@activeinference.institute" in front_matter
    assert "assets/graphical-abstract.png" in front_matter
    assert (tmp_path / "build/assets/graphical-abstract.png").read_bytes() == (
        PROJ / "manuscript/assets/graphical-abstract.png"
    ).read_bytes()


def test_render_manuscript_fails_closed_when_graphical_abstract_is_missing(
    tmp_path: Path,
) -> None:
    source = _write_graphical_abstract_render_fixture(tmp_path)
    destination = tmp_path / "build"

    with pytest.raises(
        ManuscriptRenderError, match="graphical abstract asset is missing"
    ):
        render_manuscript(source, destination, _graphical_abstract_variables())

    assert not destination.exists()


def test_render_manuscript_fails_closed_when_graphical_abstract_is_tampered(
    tmp_path: Path,
) -> None:
    source = _write_graphical_abstract_render_fixture(tmp_path)
    asset = source / "assets/graphical-abstract.png"
    asset.parent.mkdir()
    data = bytearray((PROJ / "manuscript/assets/graphical-abstract.png").read_bytes())
    data[-1] ^= 1
    asset.write_bytes(data)
    destination = tmp_path / "build"

    with pytest.raises(ManuscriptRenderError, match="sha256 does not match"):
        render_manuscript(source, destination, _graphical_abstract_variables())

    assert not destination.exists()


def test_render_manuscript_rejects_graphical_abstract_that_escapes_root(
    tmp_path: Path,
) -> None:
    source = _write_graphical_abstract_render_fixture(tmp_path)
    config_path = source / "config.yaml"
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    outside = tmp_path.parent / f"{tmp_path.name}-outside.png"
    config["publication"]["graphical_abstract"]["path"] = f"../{outside.name}"
    config_path.write_text(
        yaml.safe_dump(config, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )
    outside.write_bytes(
        (PROJ / "manuscript/assets/graphical-abstract.png").read_bytes()
    )
    destination = tmp_path / "build"

    with pytest.raises(ManuscriptRenderError, match="unsafe graphical abstract asset"):
        render_manuscript(source, destination, _graphical_abstract_variables())

    assert not destination.exists()


def test_manuscript_projection_drift_detects_stale_stable_data(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import shutil

    import yaml

    shutil.copytree(PROJ / "config", tmp_path / "config")
    shutil.copytree(
        PROJ / "lean", tmp_path / "lean", ignore=shutil.ignore_patterns(".lake")
    )
    shutil.copytree(
        PROJ / "src" / "fep_formal" / "formal",
        tmp_path / "src" / "fep_formal" / "formal",
    )
    (tmp_path / "manuscript").mkdir()
    _copy_publication_metadata(tmp_path)
    (tmp_path / "tests").mkdir()
    monkeypatch.setattr(
        "fep_formal.output.manuscript._count_test_cases", lambda _root: 0
    )
    catalogue = FEPTopicCatalogue.from_yaml(tmp_path / "config" / "topics.yaml")
    vars_path = write_manuscript_vars(tmp_path, catalogue)
    appendix_path = write_unified_formalism_appendix_markdown(tmp_path, catalogue)

    assert manuscript_projection_drift(tmp_path, catalogue) == ()
    expected_variables = build_manuscript_vars(catalogue, tmp_path)
    assert (
        manuscript_projection_drift(
            tmp_path,
            catalogue,
            expected_variables=expected_variables,
        )
        == ()
    )

    variables = yaml.safe_load(vars_path.read_text(encoding="utf-8"))
    variables["topics"]["fep-036"]["primary_theorem"] = "stale_theorem"
    vars_path.write_text(
        yaml.safe_dump(variables, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    appendix_path.write_text(
        appendix_path.read_text(encoding="utf-8") + "\nSTALE\n",
        encoding="utf-8",
    )

    assert manuscript_projection_drift(tmp_path, catalogue) == (
        vars_path,
        appendix_path,
    )


def test_render_manuscript_copies_and_rewrites_visual_assets(
    tmp_path: Path,
) -> None:
    source = tmp_path / "manuscript"
    destination = tmp_path / "build"
    docs = tmp_path / "docs"
    source.mkdir()
    docs.mkdir()
    _stage_asset_roster(tmp_path)
    (source / "01_chapter.md").write_text(
        "![Atlas](../docs/formalism-atlas.svg)\n"
        "[Interactive](../docs/formalism-atlas.html)\n"
        "![Dashboard](../docs/formal-kernel-dashboard.svg)\n"
        "[Dashboard data](../docs/formal-kernel-dashboard.html)\n",
        encoding="utf-8",
    )
    (docs / "formalism-atlas.svg").write_text("<svg/>\n", encoding="utf-8")
    (docs / "formalism-atlas.html").write_text("<html/>\n", encoding="utf-8")
    (docs / "formal-kernel-dashboard.svg").write_text(
        '<svg id="dashboard"/>\n', encoding="utf-8"
    )
    (docs / "formal-kernel-dashboard.html").write_text(
        '<html id="dashboard"/>\n', encoding="utf-8"
    )

    rendered = render_manuscript(source, destination, {})

    assert len(rendered) == 1
    assert rendered[0].read_text(encoding="utf-8") == (
        "![Atlas](assets/formalism-atlas.svg)\n"
        "[Interactive](../build/assets/formalism-atlas.html)\n"
        "![Dashboard](assets/formal-kernel-dashboard.svg)\n"
        "[Dashboard data](../build/assets/formal-kernel-dashboard.html)\n"
    )
    assert (destination / "assets" / "formalism-atlas.svg").read_text(
        encoding="utf-8"
    ) == "<svg/>\n"
    assert (destination / "assets" / "formalism-atlas.html").read_text(
        encoding="utf-8"
    ) == "<html/>\n"
    assert (destination / "assets" / "formal-kernel-dashboard.svg").read_text(
        encoding="utf-8"
    ) == '<svg id="dashboard"/>\n'
    assert (destination / "assets" / "formal-kernel-dashboard.html").read_text(
        encoding="utf-8"
    ) == '<html id="dashboard"/>\n'
    for reading_directory in (destination, tmp_path / "pdf", tmp_path / "web"):
        for filename in ("formalism-atlas.html", "formal-kernel-dashboard.html"):
            assert (reading_directory / "../build/assets" / filename).resolve() == (
                destination / "assets" / filename
            ).resolve()


@pytest.mark.parametrize("reading_format", ["manuscript", "pdf", "web"])
def test_mathematical_explorer_exports_a_closed_local_asset_tree(
    tmp_path: Path,
    reading_format: str,
) -> None:
    source = tmp_path / "manuscript"
    source.mkdir()
    _stage_asset_roster(tmp_path)
    (source / "01_chapter.md").write_text(
        "[Explorer](../docs/mathematical-positioning/mathematical-map.html)\n"
        "![Geometry](../output/figures/mathematical-fisher-geometry.png)\n",
        encoding="utf-8",
    )
    explorer = tmp_path / "docs/mathematical-positioning/mathematical-map.html"
    explorer.write_text(
        '<html><img src="panels/fisher-geometry.svg">'
        '<a href="panels/authored-relations-formal.svg">Formal print layer</a>'
        '<a href="panels/authored-relations-formal-pairing.svg">Pairing print layer</a>'
        '<a href="panels/authored-relations-conceptual.svg">Conceptual print layer</a>'
        '<a href="visual-model.json">Data</a></html>\n',
        encoding="utf-8",
    )
    destination = tmp_path / "output/manuscript"
    render_manuscript(source, destination, {})

    assert (destination / "01_chapter.md").read_text(encoding="utf-8") == (
        "[Explorer](../manuscript/assets/mathematical-map.html)\n"
        "![Geometry](assets/mathematical-fisher-geometry.png)\n"
    )
    assert (destination / "assets/mathematical-map.html").read_bytes() == (
        explorer.read_bytes()
    )
    assert (destination / "assets/panels/fisher-geometry.svg").is_file()
    assert (destination / "assets/visual-model.json").is_file()
    assert (destination / "assets/mathematical-fisher-geometry.png").is_file()
    for panel in (
        "authored-relations-formal",
        "authored-relations-formal-pairing",
        "authored-relations-conceptual",
    ):
        assert (destination / f"assets/panels/{panel}.svg").is_file()
        assert (destination / f"assets/mathematical-{panel}.png").is_file()
    reading_directory = tmp_path / "output" / reading_format
    generated_link = (
        ((destination / "01_chapter.md").read_text(encoding="utf-8").splitlines()[0])
        .removeprefix("[Explorer](")
        .removesuffix(")")
    )
    assert (reading_directory / generated_link).resolve() == (
        destination / "assets/mathematical-map.html"
    ).resolve()


def test_rendered_companion_links_pass_the_source_freshness_guard(
    tmp_path: Path,
) -> None:
    """The writer and guard agree on exact production companion targets."""
    source = tmp_path / "manuscript"
    source.mkdir()
    _stage_asset_roster(tmp_path)
    chapter = (
        "Inspect the interactive mathematical explorer at "
        "[map](../docs/mathematical-positioning/mathematical-map.html).\n"
        "Download the full retained mathematical model from "
        "[data](../docs/mathematical-positioning/visual-model.json).\n"
        "![Geometry](../output/figures/mathematical-fisher-geometry.png)\n"
    )
    (source / "01_chapter.md").write_text(chapter, encoding="utf-8")
    destination = tmp_path / "output/manuscript"
    render_manuscript(source, destination, {})
    rendered = (destination / "01_chapter.md").read_text(encoding="utf-8")
    assert rendered == (
        "Inspect the interactive mathematical explorer at "
        "[map](../manuscript/assets/mathematical-map.html).\n"
        "Download the full retained mathematical model from "
        "[data](../manuscript/assets/visual-model.json).\n"
        "![Geometry](assets/mathematical-fisher-geometry.png)\n"
    )
    pdf = tmp_path / "output/pdf"
    pdf.mkdir()
    (pdf / "_combined_manuscript.md").write_text(rendered, encoding="utf-8")

    assert stale_render_defects(source, pdf, variables={}) == ()


def test_multiline_placeholder_companion_agrees_with_actual_writer_and_guard(
    tmp_path: Path,
) -> None:
    source = tmp_path / "manuscript"
    source.mkdir()
    _stage_asset_roster(tmp_path)
    prefix = "Read the mathematical explorer with its complete retained source model: "
    (source / "01_chapter.md").write_text(
        f"{prefix}[map](../docs/mathematical-positioning/{{{{asset\n}}}}).\n",
        encoding="utf-8",
    )
    variables = {"asset": "mathematical-map.html"}
    destination = tmp_path / "output/manuscript"
    render_manuscript(source, destination, variables)
    rendered = (destination / "01_chapter.md").read_text(encoding="utf-8")
    assert rendered == f"{prefix}[map](../manuscript/assets/mathematical-map.html).\n"
    pdf = tmp_path / "output/pdf"
    pdf.mkdir()
    (pdf / "_combined_manuscript.md").write_text(rendered, encoding="utf-8")

    assert stale_render_defects(source, pdf, variables=variables) == ()


@pytest.mark.parametrize("alias", ["parent", "dot"])
def test_custom_destination_alias_agrees_with_actual_writer_and_guard(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, alias: str
) -> None:
    source = tmp_path / "authored/manuscript"
    source.mkdir(parents=True)
    _stage_asset_roster(source.parent)
    prefix = (
        "Inspect the mathematical explorer with its complete retained source model: "
    )
    (source / "01_chapter.md").write_text(
        f"{prefix}[map](../docs/mathematical-positioning/mathematical-map.html).\n",
        encoding="utf-8",
    )
    nested = tmp_path / "output/custom-build"
    nested.mkdir(parents=True)
    if alias == "parent":
        render_target = nested / ".."
    else:
        monkeypatch.chdir(nested)
        render_target = Path(".")
    destination = render_target.resolve()
    render_manuscript(source, render_target, {})
    if alias == "dot":
        # The atomic tree replacement replaced the original working directory.
        monkeypatch.chdir(destination)
    rendered = (destination / "01_chapter.md").read_text(encoding="utf-8")
    assert (
        rendered
        == f"{prefix}[map](../{destination.name}/assets/mathematical-map.html).\n"
    )
    pdf = destination.parent / "pdf"
    pdf.mkdir()
    (pdf / "_combined_manuscript.md").write_text(rendered, encoding="utf-8")

    assert (
        stale_render_defects(
            source, pdf, variables={}, rendered_manuscript_dir=render_target
        )
        == ()
    )


@pytest.mark.parametrize(
    "missing",
    [
        "docs/mathematical-positioning/visual-model.json",
        "docs/mathematical-positioning/panels/fisher-geometry.svg",
        "output/figures/mathematical-fisher-geometry.png",
    ],
)
def test_missing_mathematical_asset_preserves_the_previous_build(
    tmp_path: Path, missing: str
) -> None:
    source = tmp_path / "manuscript"
    source.mkdir()
    _stage_asset_roster(tmp_path)
    (source / "01_chapter.md").write_text("New chapter\n", encoding="utf-8")
    destination = tmp_path / "build"
    destination.mkdir()
    old_chapter = destination / "01_chapter.md"
    old_chapter.write_text("Accepted previous chapter\n", encoding="utf-8")
    (tmp_path / missing).unlink()

    with pytest.raises(ManuscriptRenderError, match="asset roster sources are missing"):
        render_manuscript(source, destination, {})

    assert old_chapter.read_text(encoding="utf-8") == "Accepted previous chapter\n"
    assert set(destination.iterdir()) == {old_chapter}


def test_render_projects_canonical_cover_author_and_rejects_stale_variables(
    tmp_path: Path,
) -> None:
    from fep_formal.output.publication_metadata import load_publication_author

    source = tmp_path / "manuscript"
    source.mkdir()
    _copy_publication_metadata(tmp_path)
    _stage_asset_roster(tmp_path)
    (source / "01_chapter.md").write_text("Authored chapter\n")
    authored = (source / "config.yaml").read_bytes()
    author = load_publication_author(tmp_path).manuscript_variables()
    destination = tmp_path / "build"
    render_manuscript(source, destination, {"publication": {"author": author}})
    rendered = (destination / "config.yaml").read_bytes()
    assert yaml.safe_load(rendered)["authors"] == [
        {**author, "orcid": "0000-0001-6232-9096"}
    ]
    assert author["orcid"] == "https://orcid.org/0000-0001-6232-9096"
    assert b"# Project-resolved config" in rendered
    assert (source / "config.yaml").read_bytes() == authored
    with pytest.raises(ManuscriptRenderError, match="do not match CITATION.cff"):
        render_manuscript(
            source,
            destination,
            {"publication": {"author": {**author, "name": "Stale Author"}}},
        )
    assert (destination / "config.yaml").read_bytes() == rendered


def test_render_preserves_raw_metadata_and_removes_obsolete_copies(
    tmp_path: Path,
) -> None:
    source = tmp_path / "manuscript"
    destination = tmp_path / "build"
    source.mkdir()
    _stage_asset_roster(tmp_path)
    (source / "01_chapter.md").write_text("Chapter {{value}}\n", encoding="utf-8")
    metadata = {
        "config.yaml": b"title: '{{value}}'\r\n",
        "preamble.md": b"```latex\r\n% {{value}}\r\n```\r\n",
        "references.bib": b"@article{literal, title = {{{value}}}}\r\n",
    }
    for name, data in metadata.items():
        (source / name).write_bytes(data)
    (source / "extra.bib").write_bytes(b"outside the exact metadata roster\n")

    assert render_manuscript(source, destination, {"value": "resolved"}) == (
        destination / "01_chapter.md",
    )
    assert (destination / "01_chapter.md").read_text() == "Chapter resolved\n"
    for name, data in metadata.items():
        assert (destination / name).read_bytes() == data
    assert not (destination / "extra.bib").exists()

    (source / "references.bib").unlink()
    render_manuscript(source, destination, {"value": "resolved"})
    assert not (destination / "references.bib").exists()
    assert (destination / "preamble.md").read_bytes() == metadata["preamble.md"]


@pytest.mark.parametrize("kind", ["symlink", "broken_symlink", "directory"])
def test_render_rejects_nonregular_metadata_before_replacing_outputs(
    tmp_path: Path, kind: str
) -> None:
    source = tmp_path / "manuscript"
    destination = tmp_path / "build"
    source.mkdir()
    destination.mkdir()
    _stage_asset_roster(tmp_path)
    (source / "01_chapter.md").write_text("Current chapter\n", encoding="utf-8")
    previous = destination / "previous.md"
    previous.write_bytes(b"previous accepted output\n")
    metadata = source / "config.yaml"
    if kind == "directory":
        metadata.mkdir()
    else:
        target = tmp_path / "target.yaml"
        if kind == "symlink":
            target.write_bytes(b"title: external\n")
        metadata.symlink_to(target)

    with pytest.raises(ManuscriptRenderError, match="metadata is not a regular file"):
        render_manuscript(source, destination, {})
    assert tuple(destination.iterdir()) == (previous,)
    assert previous.read_bytes() == b"previous accepted output\n"


def test_rerender_replaces_the_owned_chapter_and_asset_roster(
    tmp_path: Path,
) -> None:
    source = tmp_path / "manuscript"
    destination = tmp_path / "build"
    docs = tmp_path / "docs"
    source.mkdir()
    docs.mkdir()
    _stage_asset_roster(tmp_path)
    (source / "01_keep.md").write_text(
        "![Atlas](../docs/formalism-atlas.svg)\n", encoding="utf-8"
    )
    old = source / "02_old.md"
    old.write_text("Old chapter\n", encoding="utf-8")
    (docs / "formalism-atlas.svg").write_text("<svg/>\n", encoding="utf-8")

    render_manuscript(source, destination, {})
    assert (destination / "02_old.md").is_file()
    assert (destination / "assets" / "formalism-atlas.svg").is_file()

    old.unlink()
    (source / "01_keep.md").write_text("Current chapter\n", encoding="utf-8")
    render_manuscript(source, destination, {})
    assert tuple(sorted(path.name for path in destination.iterdir())) == (
        "01_keep.md",
        "assets",
    )
    assert (destination / "assets" / "formalism-atlas.svg").is_file()
    assert (destination / "01_keep.md").read_text(encoding="utf-8") == (
        "Current chapter\n"
    )


def test_render_manuscript_fails_closed_for_missing_visual_asset(
    tmp_path: Path,
) -> None:
    source = tmp_path / "manuscript"
    destination = tmp_path / "build"
    source.mkdir()
    (source / "01_chapter.md").write_text(
        "![Atlas](../docs/formalism-atlas.svg)\n", encoding="utf-8"
    )

    with pytest.raises(ManuscriptRenderError, match="formalism-atlas.svg"):
        render_manuscript(source, destination, {})

    assert not destination.exists()


def test_a_release_stamp_mismatch_must_be_disclosed(tmp_path: Path) -> None:
    """FEPLEAN-ACC-02: v1.1.0 on the title page over a tree 15,033 lines newer.

    Between releases the checkout is always ahead of the stamped tag, so the
    mismatch itself cannot be the failure. Saying nothing about it can be.
    """
    module = _load_render_script()
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    (manuscript / "00_front_matter.md").write_text(
        "Rendered from an unnamed tree.\n", encoding="utf-8"
    )

    undisclosed = module.undisclosed_source_stamp(manuscript)

    assert len(undisclosed) == 2
    assert any("source.commit" in item for item in undisclosed)
    assert any("source.published_note" in item for item in undisclosed)


def test_a_disclosed_mismatch_passes(tmp_path: Path) -> None:
    module = _load_render_script()
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    (manuscript / "00_front_matter.md").write_text(
        "That checkout is `{{source.short_commit}}`. {{source.published_note}}\n",
        encoding="utf-8",
    )

    assert module.undisclosed_source_stamp(manuscript) == ()


def test_the_shipped_manuscript_discloses_its_source(tmp_path: Path) -> None:
    module = _load_render_script()

    assert module.undisclosed_source_stamp(PROJ / "manuscript") == ()


def _git(repository: Path, *arguments: str) -> None:
    subprocess.run(
        ["git", "-C", str(repository), *arguments],
        check=True,
        capture_output=True,
        text=True,
    )


def _repository_with_a_commit(tmp_path: Path) -> Path:
    repository = tmp_path / "repo"
    repository.mkdir()
    _git(repository, "init", "--initial-branch=main")
    _git(repository, "config", "user.email", "test@example.invalid")
    _git(repository, "config", "user.name", "Test")
    (repository / "README.md").write_text("x\n", encoding="utf-8")
    _git(repository, "add", "README.md")
    _git(repository, "commit", "-m", "initial")
    return repository


def test_an_unpushed_commit_links_through_the_default_branch(tmp_path: Path) -> None:
    """FEPLEAN-C9's second form: five sha permalinks that 404.

    A commit-pinned link is the right provenance, but only once the commit is
    on the remote. Until then it resolves nowhere, so the document says so and
    links through the branch instead.
    """
    repository = _repository_with_a_commit(tmp_path)

    stamp = manuscript_module._source_stamp_vars(repository)

    assert stamp["published"] == "false"
    assert stamp["published_ref"] == "main"
    assert "not yet on the public repository" in stamp["published_note"]


def test_a_pushed_commit_links_to_the_exact_tree(tmp_path: Path) -> None:
    """The same render self-heals into permalinks once the branch is pushed."""
    upstream = tmp_path / "upstream.git"
    subprocess.run(
        ["git", "init", "--bare", "--initial-branch=main", str(upstream)],
        check=True,
        capture_output=True,
        text=True,
    )
    repository = _repository_with_a_commit(tmp_path)
    _git(repository, "remote", "add", "origin", str(upstream))
    _git(repository, "push", "-u", "origin", "main")

    stamp = manuscript_module._source_stamp_vars(repository)

    assert stamp["published"] == "true"
    assert stamp["published_ref"] == stamp["commit"]
    assert "is on the public repository" in stamp["published_note"]


def test_local_candidate_links_disclose_uncommitted_source(tmp_path: Path) -> None:
    repository = _repository_with_a_commit(tmp_path)
    (repository / "README.md").write_text("local candidate\n", encoding="utf-8")
    stamp = manuscript_module._source_stamp_vars(repository)
    assert stamp["dirty"] == "true"
    assert "includes uncommitted local changes" in stamp["published_note"]
    assert "do not reproduce the local candidate" in stamp["published_note"]
    assert "`main` fallback reference" in stamp["published_note"]
    assert "exact tree described here" not in stamp["published_note"]


def test_substitution_stays_fail_closed_for_the_renderer() -> None:
    """An unknown key must never reach a page as a literal ``{{token}}``."""
    with pytest.raises(KeyError):
        substitute_placeholders("Holds {{total_topics}} bodies.", {})
    assert (
        substitute_placeholders("Holds {{total_topics}} bodies.", {}, strict=False)
        == "Holds {{total_topics}} bodies."
    )
    assert (
        substitute_placeholders("Holds {{total_topics}} bodies.", {"total_topics": 155})
        == "Holds 155 bodies."
    )


def _shell_block(*commands: str) -> str:
    """Return one fenced shell block, assembled so this file holds no fence."""
    fence = "`" * 3
    body = "".join(f"{command}\n" for command in commands)
    return f"{fence}bash\n{body}{fence}\n"


def test_no_published_command_block_runs_the_check_without_a_generator() -> None:
    assert unreproducible_command_blocks(PROJ) == ()


def test_published_block_without_a_generator_is_rejected(tmp_path: Path) -> None:
    """The exact Reproducibility Statement that shipped, both breaks and all.

    It opened `uv sync --locked` and ended on the check, so it failed twice
    over: nothing built the projection, and the sync had already removed the
    pytest the check collects. Each break is reported separately because
    fixing one leaves the block still broken.
    """
    (tmp_path / "06_conclusion.md").write_text(
        "Reproduce with:\n\n"
        + _shell_block(
            "uv sync --locked",
            "uv run python scripts/render_manuscript.py --check",
        ),
        encoding="utf-8",
    )
    defects = unreproducible_command_blocks(tmp_path)
    assert len(defects) == 2
    assert all(defect.startswith("06_conclusion.md:") for defect in defects)
    assert "runs with no generator ahead of it" in defects[0]
    assert "leaves no pytest to collect" in defects[1]


def test_published_block_with_a_starved_sync_is_rejected(tmp_path: Path) -> None:
    """A generator alone is not enough: `uv sync --locked` prunes `dev`."""
    (tmp_path / "06_conclusion.md").write_text(
        _shell_block(
            "uv sync --locked",
            "uv run fep-formal catalogue",
            "uv run python scripts/render_manuscript.py --check",
        ),
        encoding="utf-8",
    )
    defects = unreproducible_command_blocks(tmp_path)
    assert len(defects) == 1
    assert "leaves no pytest to collect" in defects[0]


def test_published_block_with_the_generator_is_accepted(tmp_path: Path) -> None:
    (tmp_path / "06_conclusion.md").write_text(
        "Reproduce with:\n\n"
        + _shell_block(
            "uv sync --locked --extra dev",
            "uv run fep-formal catalogue",
            "uv run python scripts/render_manuscript.py --check",
        ),
        encoding="utf-8",
    )
    assert unreproducible_command_blocks(tmp_path) == ()


def test_generating_render_mode_does_not_count_as_the_generator(
    tmp_path: Path,
) -> None:
    """It rebuilds the test cache but never writes ``manuscript_vars.yaml``."""
    (tmp_path / "README.md").write_text(
        _shell_block(
            "uv run python scripts/render_manuscript.py --check",
            "uv run python scripts/render_manuscript.py",
        ),
        encoding="utf-8",
    )
    defects = unreproducible_command_blocks(tmp_path)
    assert len(defects) == 1
    assert "runs with no generator ahead of it" in defects[0]


def test_crossref_missing_dependency_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from fep_formal.output import rendering

    monkeypatch.setattr(rendering.shutil, "which", lambda _name: None)
    assert rendering.crossref_toolchain_defects()


def test_real_pandoc_crossref_preserves_labels_citations_and_code(
    tmp_path: Path,
) -> None:
    import shutil

    from fep_formal.output import rendering
    from fep_formal.output.render_log import reference_render_defects

    if not shutil.which("pandoc") or not shutil.which("pandoc-crossref"):
        pytest.skip(
            "requires pandoc and pandoc-crossref; publication preflight fails without them"
        )
    assert rendering.crossref_toolchain_defects() == ()
    base = [
        "pandoc",
        "--from=markdown+tex_math_dollars+raw_tex+header_attributes",
        "--to=latex",
        "--number-sections",
        "--natbib",
    ]
    source = tmp_path / "probe.md"
    source.write_text(rendering._CROSSREF_PROBE, encoding="utf-8")
    # The former hosted path: a successful conversion with no filter is broken.
    for use_filter in (False, True):
        result = rendering.run_process_group(
            base
            + (["--filter", "pandoc-crossref"] if use_filter else [])
            + [str(source)],
            cwd=tmp_path,
            timeout=30,
            check=True,
        )
        (tmp_path / "_combined_manuscript.tex").write_text(
            result.stdout, encoding="utf-8"
        )
        defects = reference_render_defects(tmp_path)
        assert bool(defects) is not use_filter
        assert r"\citep{fep-bibliography-probe}" in result.stdout


@pytest.mark.parametrize("failure", ["noop", "incompatible", "timeout", "oserror"])
def test_crossref_probe_rejects_broken_installed_toolchain(
    monkeypatch: pytest.MonkeyPatch,
    failure: str,
) -> None:
    import subprocess

    from fep_formal.output import rendering

    monkeypatch.setattr(rendering.shutil, "which", lambda name: "/tools/" + name)

    inputs = []

    def broken(command, **kwargs):
        inputs.append(Path(command[-1]))
        assert inputs[-1].read_text(encoding="utf-8") == rendering._CROSSREF_PROBE
        assert Path(kwargs["cwd"]) == inputs[-1].parent
        assert kwargs["timeout"] == 30
        if failure == "oserror":
            raise OSError("tool disappeared")
        if failure == "timeout":
            raise subprocess.TimeoutExpired(command, kwargs["timeout"])
        return subprocess.CompletedProcess(
            command,
            0 if failure == "noop" else 1,
            stdout=rendering._CROSSREF_PROBE,
            stderr="" if failure == "noop" else "incompatible Pandoc API",
        )

    monkeypatch.setattr(rendering, "run_process_group", broken)
    assert rendering.crossref_toolchain_defects()
    assert inputs and not inputs[0].parent.exists()


@pytest.mark.skipif(os.name != "posix", reason="descendant cleanup requires POSIX")
@pytest.mark.timeout(10, method="signal")
@pytest.mark.parametrize("cancel", [False, True], ids=["timeout", "cancellation"])
def test_crossref_probe_cleans_up_live_filter_and_held_pipes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, cancel: bool
) -> None:
    from fep_formal.output import rendering

    # Real Pandoc stand-in launches a filter which inherits BOTH capture pipes.
    # Readiness records ensure we test a live descendant, not just a slow launch.
    records = [tmp_path / "pandoc.pid", tmp_path / "filter.pid"]
    source_record = tmp_path / "source.txt"
    broker_record = tmp_path / "broker.txt"
    descendant = (
        "import os,sys,time; from pathlib import Path; "
        "print('filter stdout',flush=True); "
        "print('filter stderr',file=sys.stderr,flush=True); "
        f"Path({str(records[1])!r}).write_text(str(os.getpid())); "
        "time.sleep(20)"
    )
    tool = tmp_path / "pandoc"
    tool.write_text(
        f"#!{sys.executable}\n"
        "import os,signal,subprocess,sys,time\nfrom pathlib import Path\n"
        f"Path({str(records[0])!r}).write_text(str(os.getpid()))\n"
        f"Path({str(source_record)!r}).write_text(sys.argv[-1])\n"
        f"Path({str(broker_record)!r}).write_text(os.environ['FEP_LEAN_PROCESS_OWNER_SOCKET'])\n"
        f"assert Path(sys.argv[-1]).read_text() == {rendering._CROSSREF_PROBE!r}\n"
        f"subprocess.Popen([sys.executable,'-S','-c',{descendant!r}])\n"
        "deadline=time.monotonic()+3\n"
        f"while not Path({str(records[1])!r}).exists() and time.monotonic()<deadline: time.sleep(.01)\n"
        f"assert Path({str(records[1])!r}).exists()\n"
        + (f"os.kill({os.getpid()},signal.SIGUSR1)\n" if cancel else "")
        + "time.sleep(20)\n",
        encoding="utf-8",
    )
    tool.chmod(0o700)
    monkeypatch.setattr(rendering.shutil, "which", lambda _name: str(tool))
    run = rendering.run_process_group

    def bounded_run(command, **kwargs):
        assert kwargs["timeout"] == 30
        return run(command, **{**kwargs, "timeout": 2})

    monkeypatch.setattr(rendering, "run_process_group", bounded_run)

    def interrupt(_signum, _frame):
        raise KeyboardInterrupt("probe cancelled")

    previous = signal.signal(signal.SIGUSR1, interrupt)
    started = time.monotonic()
    try:
        if cancel:
            with pytest.raises(KeyboardInterrupt, match="probe cancelled"):
                rendering.crossref_toolchain_defects()
        else:
            defects = rendering.crossref_toolchain_defects()
            assert len(defects) == 1 and "timed out" in defects[0]
        assert time.monotonic() - started < 5
        assert source_record.exists()
        assert not Path(source_record.read_text()).parent.exists()
        assert not Path(broker_record.read_text()).parent.exists()
        for record in records:
            assert record.exists(), "child did not reach readiness"
            pid = int(record.read_text())
            deadline = time.monotonic() + 1
            while True:
                state = subprocess.run(
                    ["/bin/ps", "-o", "stat=", "-p", str(pid)],
                    capture_output=True,
                    text=True,
                    timeout=1,
                    check=False,
                ).stdout.strip()
                if not state or state.startswith("Z"):
                    break
                assert time.monotonic() < deadline, f"live process survived: {pid}"
                time.sleep(0.01)
    finally:
        signal.signal(signal.SIGUSR1, previous)
        # Even a regressed implementation must not leave the test's sleepers.
        for record in records:
            if record.exists():
                with contextlib.suppress(ProcessLookupError):
                    os.kill(int(record.read_text()), signal.SIGKILL)
