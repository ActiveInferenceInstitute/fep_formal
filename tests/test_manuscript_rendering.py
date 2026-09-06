"""Publication rendering preserves sources and rejects unknown variables."""

from __future__ import annotations

import importlib.util
import shutil
import subprocess
from pathlib import Path
from types import ModuleType

import pytest
import yaml

from fep_lean.catalogue import FEPTopicCatalogue
from fep_lean.output import manuscript as manuscript_module
from fep_lean.output.manuscript import (
    build_manuscript_vars,
    manuscript_projection_drift,
    write_manuscript_vars,
    write_unified_formalism_appendix_markdown,
)
from fep_lean.output.rendering import (
    ManuscriptRenderError,
    manuscript_source_files,
    render_manuscript,
    substitute_placeholders,
    unresolved_placeholders,
)

PROJ = Path(__file__).resolve().parent.parent


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
    return source


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

    assert module.main(["--check"]) == 0
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
    assert source_names[-1] == "08_appendix_a_overview.md"
    assert all(name[0].isdigit() for name in source_names)
    assert "preamble.md" not in source_names
    assert unresolved_placeholders(PROJ / "manuscript", variables) == ()


def test_live_render_includes_author_block_and_canonical_graphical_abstract(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("fep_lean.output.manuscript._count_test_cases", lambda _: 0)
    catalogue = FEPTopicCatalogue.from_yaml(PROJ / "config" / "topics.yaml")
    variables = build_manuscript_vars(catalogue, PROJ)

    rendered = render_manuscript(PROJ / "manuscript", tmp_path / "build", variables)

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
        PROJ / "src" / "fep_lean" / "formal",
        tmp_path / "src" / "fep_lean" / "formal",
    )
    (tmp_path / "manuscript").mkdir()
    _copy_publication_metadata(tmp_path)
    (tmp_path / "tests").mkdir()
    monkeypatch.setattr("fep_lean.output.manuscript._count_test_cases", lambda _root: 0)
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
        "[Interactive](assets/formalism-atlas.html)\n"
        "![Dashboard](assets/formal-kernel-dashboard.svg)\n"
        "[Dashboard data](assets/formal-kernel-dashboard.html)\n"
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


def test_rerender_replaces_the_owned_chapter_and_asset_roster(
    tmp_path: Path,
) -> None:
    source = tmp_path / "manuscript"
    destination = tmp_path / "build"
    docs = tmp_path / "docs"
    source.mkdir()
    docs.mkdir()
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

    assert tuple(path.name for path in destination.iterdir()) == ("01_keep.md",)
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
