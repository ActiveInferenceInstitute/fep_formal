"""Docs-audit script gates: check_links, md_hygiene, xref_audit, theorem_ref_audit.

Each script is loaded from ``docs/`` via the importlib-spec pattern used by
``tests/test_pin_audit_latest.py``. ``check_links`` and ``md_hygiene`` scan
``DOCS_DIR`` (a module global derived from ``__file__``); ``--include-root``
widens the scan to ``DOCS_DIR.parent``. Each test redirects that single global
to a tmp fixture tree.
``xref_audit`` takes ``--root`` and needs no redirection. ``theorem_ref_audit``
derives its root inline from ``__file__``, so redirecting it means patching
that one module attribute; its canonical-name surfaces are read from packaged
repo data. Count-reference fixtures copy the maintained coverage projection and
root documents, keeping the fixtures fully offline.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _load_docs_script(stem: str) -> ModuleType:
    """Load ``docs/<stem>.py`` as a fresh module (importlib-spec pattern)."""
    spec = importlib.util.spec_from_file_location(
        f"docs_{stem}", PROJECT_ROOT / "docs" / f"{stem}.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _run_script(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    stem: str,
    argv: list[str],
    *,
    redirect_root_from_docs_dir: bool = False,
    redirect_root_from_file: bool = False,
) -> tuple[int, str]:
    """Run a loaded docs script's ``main`` against a tmp fixture tree."""
    module = _load_docs_script(stem)
    if redirect_root_from_docs_dir:
        # The default scan root is the module-global DOCS_DIR; one global.
        monkeypatch.setattr(module, "DOCS_DIR", tmp_path)
    if redirect_root_from_file:
        # main() derives the repo root inline from __file__ (no separate
        # constant); repointing that single attribute redirects the scan.
        monkeypatch.setattr(module, "__file__", str(tmp_path / "docs" / f"{stem}.py"))
    monkeypatch.setattr(sys, "argv", [stem, *argv])
    code: int = module.main()
    return code, capsys.readouterr().out


def test_check_links_flags_broken_internal_link(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    (tmp_path / "index.md").write_text(
        "# Index\n\n[missing](nowhere.md)\n", encoding="utf-8"
    )
    code, out = _run_script(
        tmp_path,
        monkeypatch,
        capsys,
        "check_links",
        [],
        redirect_root_from_docs_dir=True,
    )

    assert code == 1
    assert "broken link" in out
    assert "nowhere.md" in out


def test_check_links_passes_clean_fixture_tree(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    (tmp_path / "index.md").write_text(
        "# Index\n\n[see](target.md)\n", encoding="utf-8"
    )
    (tmp_path / "target.md").write_text("# Target\n", encoding="utf-8")
    code, out = _run_script(
        tmp_path,
        monkeypatch,
        capsys,
        "check_links",
        [],
        redirect_root_from_docs_dir=True,
    )

    assert code == 0
    assert "no broken links" in out


def test_md_hygiene_flags_missing_trailing_newline(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    (tmp_path / "note.md").write_text("# Title\n\n- item", encoding="utf-8")
    code, out = _run_script(
        tmp_path,
        monkeypatch,
        capsys,
        "md_hygiene",
        [],
        redirect_root_from_docs_dir=True,
    )

    assert code == 1
    assert "does not end with a newline" in out


def test_md_hygiene_passes_clean_fixture_tree(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    (tmp_path / "note.md").write_text("# Title\n\n- item\n", encoding="utf-8")
    code, out = _run_script(
        tmp_path,
        monkeypatch,
        capsys,
        "md_hygiene",
        [],
        redirect_root_from_docs_dir=True,
    )

    assert code == 0
    assert "no hygiene issues" in out


def test_xref_audit_flags_unresolved_crossref(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = tmp_path / "manuscript"
    root.mkdir()
    (root / "chapter.md").write_text(
        "# Chapter\n\nSee [@sec:ghost].\n", encoding="utf-8"
    )
    code, out = _run_script(
        tmp_path, monkeypatch, capsys, "xref_audit", ["--root", str(root)]
    )

    assert code == 1
    assert "unresolved" in out
    assert "sec:ghost" in out
    assert "fep-lean catalogue" in out


def test_xref_audit_omits_the_catalogue_hint_when_generated_inputs_exist(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = tmp_path / "manuscript"
    root.mkdir()
    (root / "chapter.md").write_text(
        "# Chapter\n\nSee [@sec:ghost].\n", encoding="utf-8"
    )
    for name in (
        "09z_unified_formalism_catalogue.md",
        "09z_appendix_b_lean_catalogue.md",
        "09zc_appendix_c_lean_equations.md",
    ):
        (root / name).write_text("# Generated\n", encoding="utf-8")
    code, out = _run_script(
        tmp_path, monkeypatch, capsys, "xref_audit", ["--root", str(root)]
    )

    assert code == 1
    assert "sec:ghost" in out
    assert "fep-lean catalogue" not in out


def test_xref_audit_passes_resolved_crossref(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = tmp_path / "manuscript"
    root.mkdir()
    (root / "chapter.md").write_text(
        "# Chapter\n\nSee [@sec:intro].\n\n## Intro {#sec:intro}\n",
        encoding="utf-8",
    )
    code, out = _run_script(
        tmp_path, monkeypatch, capsys, "xref_audit", ["--root", str(root)]
    )

    assert code == 0
    assert "all resolve" in out


def _write_count_references(root: Path) -> dict[str, int]:
    """Use the maintained join, rather than a second expected-count inventory."""
    coverage = json.loads(
        (PROJECT_ROOT / "docs" / "formalism-coverage.json").read_text(encoding="utf-8")
    )
    projection = {
        "metrics": {"topics": coverage["metrics"]["topics"]},
        "topics": [
            {"family": row["family"], "area": row["area"]} for row in coverage["topics"]
        ],
        "area_counts": coverage["area_counts"],
    }
    docs = root / "docs"
    docs.mkdir(exist_ok=True)
    (docs / "formalism-coverage.json").write_text(
        json.dumps(projection), encoding="utf-8"
    )
    for name in ("README.md", "AGENTS.md", "SPEC.md", "HANDOFF.md"):
        (root / name).write_text(
            (PROJECT_ROOT / name).read_text(encoding="utf-8"), encoding="utf-8"
        )
    return {
        "topics": coverage["metrics"]["topics"],
        "families": len({row["family"] for row in coverage["topics"]}),
        "areas": len(coverage["area_counts"]),
    }


def test_theorem_ref_audit_flags_unresolvable_manuscript_name(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _write_count_references(tmp_path)
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    (manuscript / "chapter.md").write_text(
        "# Chapter\n\nTheorem fep999_absent_theorem states the claim.\n",
        encoding="utf-8",
    )
    code, out = _run_script(
        tmp_path,
        monkeypatch,
        capsys,
        "theorem_ref_audit",
        [],
        redirect_root_from_file=True,
    )

    assert code == 1
    assert "fep999_absent_theorem" in out
    assert "FAIL" in out


def test_theorem_ref_audit_passes_manuscript_without_references(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _write_count_references(tmp_path)
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    (manuscript / "chapter.md").write_text(
        "# Chapter\n\nNo canonical declaration references here.\n",
        encoding="utf-8",
    )
    code, out = _run_script(
        tmp_path,
        monkeypatch,
        capsys,
        "theorem_ref_audit",
        [],
        redirect_root_from_file=True,
    )

    assert code == 0
    assert "references resolve" in out


@pytest.mark.parametrize("claim", ("intro", "current-boundary", "families", "areas"))
def test_current_readme_count_mutation_fails_the_actual_audit_gate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    claim: str,
) -> None:
    counts = _write_count_references(tmp_path)
    (tmp_path / "manuscript").mkdir()
    original = (tmp_path / "README.md").read_text(encoding="utf-8")
    replacements = {
        "intro": (
            f"catalog of {counts['topics']} ",
            f"catalog of {counts['topics'] + 1} ",
        ),
        "current-boundary": (
            f"spans {counts['topics']} topics",
            f"spans {counts['topics'] + 1} topics",
        ),
        "families": (
            f"{counts['families']} reviewed families",
            f"{counts['families'] + 1} reviewed families",
        ),
        # The actual area claim wraps across lines and spells out its count.
        "areas": ("families in five\nareas", "families in six\nareas"),
    }
    before, after = replacements[claim]
    assert before in original
    (tmp_path / "README.md").write_text(
        original.replace(before, after, 1), encoding="utf-8"
    )

    code, out = _run_script(
        tmp_path,
        monkeypatch,
        capsys,
        "theorem_ref_audit",
        [],
        redirect_root_from_file=True,
    )

    assert code == 1
    assert "README.md:" in out
    assert "current catalog" in out
    assert "disagrees with docs/formalism-coverage.json" in out


@pytest.mark.parametrize(
    ("name", "section", "unit"),
    (
        ("AGENTS.md", "Purpose", "topics"),
        ("SPEC.md", "Scope", "topics"),
        ("HANDOFF.md", "Current formal breadth and depth", "families"),
    ),
)
def test_current_count_audit_covers_the_other_root_contracts(
    tmp_path: Path, name: str, section: str, unit: str
) -> None:
    counts = _write_count_references(tmp_path)
    (tmp_path / name).write_text(
        f"# Contract\n\n## {section}\n\nThe catalog has {counts[unit] + 1} {unit}.\n",
        encoding="utf-8",
    )
    module = _load_docs_script("theorem_ref_audit")

    failures = module.root_count_reference_failures(tmp_path)

    assert len(failures) == 1
    assert failures[0].startswith(f"{name}:5:")
    assert f"current catalog {unit} count" in failures[0]

    # The spelling change must not remove either count-recognition boundary.
    for spelling in ("catalog", "catalogue"):
        (tmp_path / name).write_text(
            f"# Contract\n\n## {section}\n\nA {spelling} of {counts['topics'] + 1} entries.\n",
            encoding="utf-8",
        )
        spelling_failures = module.root_count_reference_failures(tmp_path)
        assert len(spelling_failures) == 1
        assert "current catalog topics count" in spelling_failures[0]


def test_count_audit_preserves_histories_subsets_and_non_prose(tmp_path: Path) -> None:
    counts = _write_count_references(tmp_path)
    (tmp_path / "README.md").write_text(
        f"# Catalog\n\nA catalog of {counts['topics']} topics.\n"
        "Its five second-expansion families form a subset.\n"
        "[Example](/999-topic.md)\n"
        "<!-- An abandoned draft said 999 topics. -->\n\n"
        "```text\n## Formal depth\n999 topics in 999 families and 999 areas\n```\n"
        "~~~~text\n999 topics in 999 families and 999 areas\n~~~~\n\n"
        "## Release\n\nThe dated v0.1 release contained 50 topics in 7 families.\n"
        "That release passed 2,404 tests; this total belongs to its source epoch.\n\n"
        "## Formal depth\n\n"
        f"The maintained catalog spans {counts['topics']} topics in\n"
        f"{counts['families']} reviewed families across {counts['areas']} areas.\n",
        encoding="utf-8",
    )
    (tmp_path / "HANDOFF.md").write_text(
        "# Handoff\n\n## Historical external stage\n\n"
        "The earlier snapshot had 50 topics in 7 families across 3 areas.\n",
        encoding="utf-8",
    )
    module = _load_docs_script("theorem_ref_audit")

    assert module.root_count_reference_failures(tmp_path) == ()


@pytest.mark.parametrize(
    "defect",
    (
        "missing",
        "invalid-json",
        "topic-total",
        "area-total",
        "top-level-type",
        "metrics-type",
        "row-type",
    ),
)
def test_count_audit_rejects_missing_or_inconsistent_coverage(
    tmp_path: Path, defect: str
) -> None:
    _write_count_references(tmp_path)
    reference = tmp_path / "docs" / "formalism-coverage.json"
    if defect == "missing":
        reference.unlink()
    elif defect == "invalid-json":
        reference.write_text("{", encoding="utf-8")
    else:
        coverage = json.loads(reference.read_text(encoding="utf-8"))
        if defect == "top-level-type":
            coverage = []
        elif defect == "metrics-type":
            coverage["metrics"] = []
        elif defect == "row-type":
            coverage["topics"][0] = []
        elif defect == "topic-total":
            coverage["metrics"]["topics"] += 1
        else:
            first_area = next(iter(coverage["area_counts"]))
            coverage["area_counts"][first_area] += 1
        reference.write_text(json.dumps(coverage), encoding="utf-8")
    module = _load_docs_script("theorem_ref_audit")

    failures = module.root_count_reference_failures(tmp_path)

    assert len(failures) == 1
    assert failures[0].startswith(
        "docs/formalism-coverage.json: cannot validate catalog count references:"
    )


@pytest.mark.parametrize(
    ("figure", "kind", "phrase"),
    (
        ("math_formal_relations", "formal", "The {count} edges"),
        ("math_formal_pairings", "formal_pairing", "locates {count} checked pairings"),
        (
            "math_conceptual_relations",
            "conceptual",
            "orientation of {count} maintained associations",
        ),
    ),
)
def test_relation_captions_follow_the_canonical_counts_and_a_changed_count(
    figure: str, kind: str, phrase: str
) -> None:
    from fep_lean.output.rendering import substitute_placeholders

    coverage = json.loads(
        (PROJECT_ROOT / "docs" / "formalism-coverage.json").read_text(encoding="utf-8")
    )
    source = (
        PROJECT_ROOT / "manuscript" / "08b_mathematical_positioning_supplement.md"
    ).read_text(encoding="utf-8")
    caption = next(line for line in source.splitlines() if f"#fig:{figure} " in line)
    count = coverage["relation_counts"][kind]
    for expected in (count, count + 1):
        rendered = substitute_placeholders(
            caption, {"formalism": {"relation_counts": {kind: expected}}}
        )
        assert phrase.format(count=expected) in rendered


def test_second_expansion_heading_does_not_grow_with_the_full_catalogue() -> None:
    from fep_lean.output.rendering import substitute_placeholders

    source = (PROJECT_ROOT / "manuscript" / "04i_formalism_catalogue_155.md").read_text(
        encoding="utf-8"
    )
    heading = source.splitlines()[0]
    # Distinct synthetic counts expose an accidental use of the live total
    # instead of the endpoint owned by this particular expansion.
    variables = {
        "topics_before_second_expansion": 80,
        "topics_before_third_expansion": 100,
        "total_topics": 120,
    }
    rendered = substitute_placeholders(heading, variables)

    assert "Second Expansion, from 80 to 100 Topics:" in rendered
    assert "{#sec:formalism_catalogue_155}" in rendered
    variables["total_topics"] = 140
    assert substitute_placeholders(heading, variables) == rendered


def test_second_expansion_current_toolchain_comes_from_workspace_variables() -> None:
    from fep_lean.output.rendering import substitute_placeholders

    source = (PROJECT_ROOT / "manuscript" / "04i_formalism_catalogue_155.md").read_text(
        encoding="utf-8"
    )
    toolchain_paragraph = next(
        paragraph
        for paragraph in source.split("\n\n")
        if paragraph.startswith("The authoring workspace pins")
    )
    rendered = substitute_placeholders(
        toolchain_paragraph,
        {
            "lean_toolchain": "leanprover/lean4:v9.8.7",
            "mathlib_tag": "v9.8.7",
            "total_topics": 120,
        },
    )

    assert "**`leanprover/lean4:v9.8.7`** and Mathlib\n**`v9.8.7`**" in rendered
    assert "Earlier Lean and Mathlib releases provide historical" in rendered


def _make_repo(tmp_path: Path) -> Path:
    """Build a minimal repo-shaped tree; returns its ``docs/`` directory."""
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "index.md").write_text("# Index\n", encoding="utf-8")
    source = "# Project\n"
    (tmp_path / "README.md").write_text(source, encoding="utf-8")
    github = tmp_path / ".github"
    github.mkdir()
    module = _load_docs_script("check_links")
    (github / "README.md").write_text(
        module.render_github_readme(source), encoding="utf-8"
    )
    return docs


def _run_wide(
    docs: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    stem: str,
    argv: list[str],
) -> tuple[int, str]:
    module = _load_docs_script(stem)
    monkeypatch.setattr(module, "DOCS_DIR", docs)
    monkeypatch.setattr(sys, "argv", [stem, "--include-root", *argv])
    code: int = module.main()
    return code, capsys.readouterr().out


@pytest.mark.parametrize(
    "rel",
    [
        "HANDOFF.md",
        "src/fep_lean/custody/README.md",
        "src/fep_lean/custody/AGENTS.md",
        "tests/AGENTS.md",
        "config/README.md",
        "scripts/AGENTS.md",
        "lean/README.md",
        "manuscript/AGENTS.md",
        "specs/some-spec/README.md",
        ".github/AGENTS.md",
        ".github/pull_request_template.md",
        ".github/workflows/guide.md",
    ],
)
def test_check_links_include_root_catches_broken_link_everywhere(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    rel: str,
) -> None:
    docs = _make_repo(tmp_path)
    target = tmp_path / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("# T\n\n[gone](missing-file.md)\n", encoding="utf-8")

    code, out = _run_wide(docs, monkeypatch, capsys, "check_links", [])

    assert code == 1
    assert "missing-file.md" in out
    assert rel in out


@pytest.mark.parametrize(
    "rel",
    [
        "specs/done/old-run/NOTES.md",
        "specs/live/evidence/journal/README.md",
        "specs/live/gnn_output/PIPELINE_REPORT.md",
        "specs/live/gnn-input/Model.md",
        "specs/live/fixtures/Model.md",
        "src/fep_lean/custody/NOTES.md",  # only AGENTS.md / README.md in src
        "lean/.lake/packages/dep/README.md",
        ".github/evidence/old-run/README.md",
        ".github/node_modules/vendor/README.md",
        ".github/.cache/README.md",
    ],
)
def test_include_root_excludes_historical_and_vendored_trees(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    rel: str,
) -> None:
    docs = _make_repo(tmp_path)
    target = tmp_path / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("# T\n\n[gone](missing-file.md)  \n", encoding="utf-8")

    for stem in ("check_links", "md_hygiene"):
        code, out = _run_wide(docs, monkeypatch, capsys, stem, ["--strict"])
        assert code == 0, out


def test_check_links_without_include_root_ignores_non_docs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    docs = _make_repo(tmp_path)
    (tmp_path / "HANDOFF.md").write_text("# H\n\n[x](nope.md)\n", encoding="utf-8")
    module = _load_docs_script("check_links")
    monkeypatch.setattr(module, "DOCS_DIR", docs)
    monkeypatch.setattr(sys, "argv", ["check_links"])
    assert module.main() == 0
    capsys.readouterr()


@pytest.mark.parametrize("state", ["missing", "stale"])
def test_github_readme_freshness_is_read_only_and_requires_exact_projection(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    state: str,
) -> None:
    docs = _make_repo(tmp_path)
    mirror = tmp_path / ".github" / "README.md"
    if state == "missing":
        mirror.unlink()
    else:
        mirror.write_text("# Project\n", encoding="utf-8")
    before = mirror.read_bytes() if mirror.exists() else None
    source = (tmp_path / "README.md").read_bytes()

    code, out = _run_wide(docs, monkeypatch, capsys, "check_links", ["--strict"])

    assert code == 1
    assert ".github/README.md is missing or stale" in out
    assert "--write-github-readme" in out
    assert (mirror.read_bytes() if mirror.exists() else None) == before
    assert (tmp_path / "README.md").read_bytes() == source


def test_github_readme_rebases_local_destinations_and_preserves_code_and_urls(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    docs = _make_repo(tmp_path)
    (docs / "guide.md").write_text("# Guide\n\n## Section\n", encoding="utf-8")
    (docs / "guide space.md").write_text("# Guide\n\n## Section\n", encoding="utf-8")
    (docs / "figure(1).svg").write_text("<svg/>\n", encoding="utf-8")
    (tmp_path / "LICENSE").write_text("License\n", encoding="utf-8")
    source = (
        "# Project\n\n## Details\n\n"
        '[guide](docs/guide.md#section "Guide")\n'
        "![figure](docs/figure(1).svg)\n"
        "[spaced](<docs/guide%20space.md#section>)\n"
        "[raw space](<docs/guide space.md#section>)\n"
        "[relative](./docs/guide.md#section)\n"
        "[query](docs/guide.md?plain=1#section)\n"
        "[canonical](README.md#details) [here](#details)\n"
        "[![License](https://example.org/badge.svg)](LICENSE)\n"
        "[![Local](docs/figure(1).svg)](docs/guide.md#section)\n"
        "[reference][guide-ref]\n"
        '[guide-ref]: docs/guide.md#section "Reference [literal](unchanged.md)"\n'
        "[web](https://example.org/a) [scheme](custom+v1:document)\n"
        "[mail](mailto:maintainer@example.org) [network](//example.org/a)\n"
        "[data](data:image/png;base64,AAAA)\n"
        "`[inline](unchanged.md)` and ``[two `ticks`](unchanged.md)``\n"
        "```markdown\n[example](unchanged.md)\n```\n"
        "~~~markdown\n![example](unchanged.svg)\n~~~\n"
    )
    root_readme = tmp_path / "README.md"
    root_readme.write_text(source, encoding="utf-8")
    mirror = tmp_path / ".github" / "README.md"

    code, out = _run_script(
        docs,
        monkeypatch,
        capsys,
        "check_links",
        ["--strict", "--write-github-readme"],
        redirect_root_from_docs_dir=True,
    )

    assert code == 0, out
    projected = mirror.read_text(encoding="utf-8")
    assert projected.startswith(
        "<!-- Generated from ../README.md by ../docs/check_links.py;"
    )
    for original, expected in (
        (
            '[guide](docs/guide.md#section "Guide")',
            '[guide](../docs/guide.md#section "Guide")',
        ),
        ("![figure](docs/figure(1).svg)", "![figure](../docs/figure(1).svg)"),
        (
            "[spaced](<docs/guide%20space.md#section>)",
            "[spaced](<../docs/guide%20space.md#section>)",
        ),
        (
            "[raw space](<docs/guide space.md#section>)",
            "[raw space](<../docs/guide space.md#section>)",
        ),
        (
            "[relative](./docs/guide.md#section)",
            "[relative](.././docs/guide.md#section)",
        ),
        (
            "[query](docs/guide.md?plain=1#section)",
            "[query](../docs/guide.md?plain=1#section)",
        ),
        ("[canonical](README.md#details)", "[canonical](../README.md#details)"),
        (
            "[![License](https://example.org/badge.svg)](LICENSE)",
            "[![License](https://example.org/badge.svg)](../LICENSE)",
        ),
        (
            "[![Local](docs/figure(1).svg)](docs/guide.md#section)",
            "[![Local](../docs/figure(1).svg)](../docs/guide.md#section)",
        ),
        (
            '[guide-ref]: docs/guide.md#section "Reference [literal](unchanged.md)"',
            '[guide-ref]: ../docs/guide.md#section "Reference [literal](unchanged.md)"',
        ),
    ):
        assert original in source
        assert expected in projected
    for literal in (
        "[here](#details)",
        "[web](https://example.org/a)",
        "[scheme](custom+v1:document)",
        "[mail](mailto:maintainer@example.org)",
        "[network](//example.org/a)",
        "[data](data:image/png;base64,AAAA)",
        "`[inline](unchanged.md)`",
        "``[two `ticks`](unchanged.md)``",
        "```markdown\n[example](unchanged.md)\n```",
        "~~~markdown\n![example](unchanged.svg)\n~~~",
    ):
        assert literal in projected
    assert root_readme.read_text(encoding="utf-8") == source
    first = mirror.read_bytes()
    code, out = _run_wide(
        docs, monkeypatch, capsys, "check_links", ["--strict", "--write-github-readme"]
    )
    assert code == 0, out
    assert mirror.read_bytes() == first
    code, out = _run_wide(docs, monkeypatch, capsys, "check_links", ["--strict"])
    assert code == 0, out


def test_readme_projection_keeps_absolute_paths_and_reference_fragments() -> None:
    module = _load_docs_script("check_links")
    source = (
        "# Project\n\n"
        "[web-root](/absolute/path.md) [query](?plain=1#project)\n"
        "[up](../sibling.md#heading)\n"
        "[fragment]: #project\n"
        "[scheme]: file:///absolute/path.md\n"
        "[^note]: An explanatory paragraph.\n"
    )
    projected = module.render_github_readme(source)
    assert "[web-root](/absolute/path.md) [query](?plain=1#project)" in projected
    assert "[up](../../sibling.md#heading)" in projected
    assert "[fragment]: #project" in projected
    assert "[scheme]: file:///absolute/path.md" in projected
    assert "[^note]: An explanatory paragraph." in projected


@pytest.mark.parametrize(
    "prose", ["`unmatched [actual](missing.md)", r"\`[actual](missing.md)"]
)
def test_unclosed_or_escaped_code_delimiters_do_not_hide_actual_links(
    tmp_path: Path, prose: str
) -> None:
    module = _load_docs_script("check_links")
    page = tmp_path / "page.md"
    page.write_text("# Page\n\n" + prose + "\n", encoding="utf-8")
    issues = module.check_file(page, strict=True, anchor_cache={})
    assert len(issues) == 1
    assert "missing.md" in issues[0]


def test_fenced_heading_does_not_supply_a_real_anchor(tmp_path: Path) -> None:
    module = _load_docs_script("check_links")
    page = tmp_path / "page.md"
    page.write_text(
        "# Page\n\n[absent](#example)\n\n~~~~markdown\n# Example\n~~~\n~~~~\n",
        encoding="utf-8",
    )
    issues = module.check_file(page, strict=True, anchor_cache={})
    assert len(issues) == 1
    assert "in-page anchor '#example'" in issues[0]


@pytest.mark.parametrize(
    "literal",
    [
        "    [example](unchanged.md)\n",
        "\t[example](unchanged.md)\n",
        "> ```markdown\n> [example](unchanged.md)\n> ```\n",
        "- ```markdown\n  [example](unchanged.md)\n  ```\n",
        "1. ~~~markdown\n   [example](unchanged.md)\n   ~~~\n",
        "- Container:\n\n  ```markdown\n  [example](unchanged.md)\n  ```\n",
        "> - ```markdown\n>   [example](unchanged.md)\n>   ```\n",
        "- > ```markdown\n  > [example](unchanged.md)\n  > ```\n",
        "- Outer:\n  - ```markdown\n    [example](unchanged.md)\n    ```\n",
        "- Container:\n\n      [example](unchanged.md)\n",
        "- ```markdown\n  [example](unchanged.md)\n\n  [example](unchanged.md)\n  ```\n",
        "> - ```markdown\n>   [example](unchanged.md)\n>\n>   [example](unchanged.md)\n>   ```\n",
    ],
)
def test_indented_and_contained_code_is_preserved_without_hiding_following_links(
    tmp_path: Path, literal: str
) -> None:
    module = _load_docs_script("check_links")
    page = tmp_path / "README.md"
    (tmp_path / "target.md").write_text("# Target\n", encoding="utf-8")
    source = "# Page\n\n" + literal + "\n[real](target.md)\n"
    page.write_text(source, encoding="utf-8")

    projected = module.render_github_readme(source)

    assert literal in projected
    assert "[example](../unchanged.md)" not in projected
    assert "[real](../target.md)" in projected
    assert module.check_file(page, strict=True, anchor_cache={}) == []


@pytest.mark.parametrize(
    "paragraph",
    [
        "- List item [real](missing.md)\n",
        "- List item\n    [real](missing.md)\n",
        "- List item\n\n    [real](missing.md)\n",
        "Paragraph\n    [real](missing.md)\n",
        "Paragraph\n\t[real](missing.md)\n",
        "> Paragraph\n>     [real](missing.md)\n",
        "- > Paragraph\n  >     [real](missing.md)\n",
        "1234. Paragraph\n    [real](missing.md)\n",
    ],
)
def test_real_list_and_indented_continuation_prose_remains_auditable(
    tmp_path: Path, paragraph: str
) -> None:
    module = _load_docs_script("check_links")
    page = tmp_path / "README.md"
    source = "# Page\n\n" + paragraph
    page.write_text(source, encoding="utf-8")

    assert "[real](../missing.md)" in module.render_github_readme(source)
    issues = module.check_file(page, strict=True, anchor_cache={})
    assert len(issues) == 1
    assert "missing.md" in issues[0]


@pytest.mark.parametrize(
    "literal",
    [
        "> ```markdown\n> [example](unchanged.md)\n",
        "- ```markdown\n  [example](unchanged.md)\n",
    ],
)
def test_unclosed_contained_fence_ends_with_its_container(
    tmp_path: Path, literal: str
) -> None:
    module = _load_docs_script("check_links")
    page = tmp_path / "README.md"
    source = "# Page\n\n" + literal + "\n[real](missing.md)\n"
    page.write_text(source, encoding="utf-8")

    projected = module.render_github_readme(source)

    assert literal in projected
    assert "[real](../missing.md)" in projected
    issues = module.check_file(page, strict=True, anchor_cache={})
    assert len(issues) == 1
    assert "missing.md" in issues[0]


@pytest.mark.parametrize(
    ("literal", "following"),
    [
        ("> ```markdown\n> [example](unchanged.md)\n", "\n> [real](missing.md)\n"),
        (
            "- > ```markdown\n  > [example](unchanged.md)\n",
            "\n  > [real](missing.md)\n",
        ),
        (
            "> - ```markdown\n>   [example](unchanged.md)\n",
            "\n> - [real](missing.md)\n",
        ),
        (
            "> > ```markdown\n> > [example](unchanged.md)\n",
            ">\n> > [real](missing.md)\n",
        ),
    ],
)
def test_blank_without_quote_prefix_ends_its_fence(
    tmp_path: Path, literal: str, following: str
) -> None:
    module = _load_docs_script("check_links")
    page = tmp_path / "README.md"
    source = "# Page\n\n" + literal + following
    page.write_text(source, encoding="utf-8")

    projected = module.render_github_readme(source)

    assert literal in projected
    assert "[real](../missing.md)" in projected
    issues = module.check_file(page, strict=True, anchor_cache={})
    assert len(issues) == 1
    assert "missing.md" in issues[0]


def test_github_projection_refuses_symlink_targets_without_writing(
    tmp_path: Path,
) -> None:
    _make_repo(tmp_path)
    module = _load_docs_script("check_links")
    outside = tmp_path / "preserved.md"
    outside.write_text("Preserve these bytes.\n", encoding="utf-8")
    mirror = tmp_path / ".github" / "README.md"
    mirror.unlink()
    mirror.symlink_to(outside)
    assert module.github_readme_issues(tmp_path, write=True)
    assert mirror.is_symlink()
    assert outside.read_text(encoding="utf-8") == "Preserve these bytes.\n"


def test_include_root_discovery_matches_for_all_maintained_github_markdown(
    tmp_path: Path,
) -> None:
    docs = _make_repo(tmp_path)
    maintained = {
        ".github/README.md",
        ".github/AGENTS.md",
        ".github/workflows/notes.md",
    }
    for rel in maintained - {".github/README.md"}:
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# Notes\n", encoding="utf-8")
    discovered = []
    for stem in ("check_links", "md_hygiene"):
        module = _load_docs_script(stem)
        discovered.append(
            {
                path.relative_to(tmp_path).as_posix()
                for path in module.discover_files(docs, include_root=True)
            }
        )
        assert module.discover_files(docs, include_root=False) == [docs / "index.md"]
    assert discovered[0] == discovered[1]
    assert maintained <= discovered[0]


def test_md_hygiene_include_root_flags_trailing_whitespace_in_src_readme(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    docs = _make_repo(tmp_path)
    readme = tmp_path / "src" / "fep_lean" / "custody" / "README.md"
    readme.parent.mkdir(parents=True)
    readme.write_text("# Custody\n\ntrailing   \n", encoding="utf-8")

    code, out = _run_wide(docs, monkeypatch, capsys, "md_hygiene", ["--strict"])

    assert code == 1
    assert "src/fep_lean/custody/README.md:3: trailing whitespace" in out


def test_md_hygiene_numeric_brackets_are_not_orphans(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    docs = _make_repo(tmp_path)
    (docs / "math.md").write_text(
        "# M\n\nindex [0] and interval [1, 1/10] and vector [0.25, 0.5].\n",
        encoding="utf-8",
    )
    code, out = _run_wide(docs, monkeypatch, capsys, "md_hygiene", ["--strict"])
    assert code == 0, out


def test_every_docs_markdown_page_is_linked_from_docs_readme() -> None:
    """Each ``docs/*.md`` page (bar README/AGENTS) must be reachable from the index."""
    docs = PROJECT_ROOT / "docs"
    index = (docs / "README.md").read_text(encoding="utf-8")
    missing = sorted(
        page.name
        for page in docs.glob("*.md")
        if page.name not in {"README.md", "AGENTS.md"}
        and f"({page.name})" not in index
        and f"({page.name}#" not in index
    )
    assert not missing, f"docs/README.md does not link: {missing}"
