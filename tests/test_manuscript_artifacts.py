"""manuscript_vars structure from catalogue. All real methods, no direct execution."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

import fep_lean.output.manuscript as manuscript_module
from fep_lean.catalogue.coverage import build_formalism_coverage
from fep_lean.catalogue.relations import EdgeKind
from fep_lean.catalogue.topics import FEPTopicCatalogue
from fep_lean.output.graphical_abstract import render_graphical_abstract
from fep_lean.output.manuscript import (
    _SMALL_NUMBER_WORDS,
    UNIFIED_FORMALISM_CATALOGUE_FILENAME,
    _count_test_cases,
    _get_latest_verification_manifest,
    _hermes_block_from_summary,
    _read_toolchain_vars,
    _test_collection_fingerprint,
    _test_collection_input_paths,
    _verify_block_from_manifest,
    build_lean_catalogue_markdown,
    build_manuscript_vars,
    build_typeset_equations_markdown,
    build_unified_formalism_appendix_markdown,
    write_manuscript_vars,
    write_unified_formalism_appendix_markdown,
)
from fep_lean.output.publication_metadata import (
    PublicationMetadataError,
    load_publication_author,
    pdf_metadata_drift,
    pdf_metadata_fields,
)

PROJ = Path(__file__).resolve().parent.parent


def _copy_publication_metadata(project_root: Path) -> None:
    manuscript = project_root / "manuscript"
    manuscript.mkdir(parents=True, exist_ok=True)
    shutil.copy2(PROJ / "CITATION.cff", project_root / "CITATION.cff")
    shutil.copy2(PROJ / "manuscript/config.yaml", manuscript / "config.yaml")
    shutil.copytree(PROJ / "manuscript/assets", manuscript / "assets")


def test_authored_figure_anchors_are_attached_to_figures() -> None:
    for path in sorted((PROJ / "manuscript").glob("*.md")):
        for line_number, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            if "{#fig:" in line:
                assert line.lstrip().startswith("!["), f"{path}:{line_number}"


def test_appendix_orientation_tables_avoid_narrow_identifier_columns() -> None:
    appendix = (PROJ / "manuscript/08_appendix_a_overview.md").read_text(
        encoding="utf-8"
    )

    assert "| Area (topics) | Native compile (verifier) | Mathlib domains |" in appendix
    assert "| Topic | Appendix B (Lean) | Appendix C (display math) |" in appendix
    assert "| Role |" not in appendix
    assert appendix.count("```bash") == 2
    assert "`uv run fep-lean catalogue`" not in appendix


def test_pdf_preamble_wraps_highlighted_lean_without_clipping() -> None:
    preamble = (PROJ / "manuscript/preamble.md").read_text(encoding="utf-8")

    assert r"\usepackage{fvextra}" in preamble
    assert r"\RecustomVerbatimEnvironment{Highlighting}{Verbatim}" in preamble
    assert "breaklines=true" in preamble
    assert "breakanywhere=true" in preamble


def test_build_manuscript_vars_shape(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("fep_lean.output.manuscript._count_test_cases", lambda _: 0)
    c = FEPTopicCatalogue.from_yaml(PROJ / "config" / "topics.yaml")
    v = build_manuscript_vars(c, PROJ)
    summary = c.summary()
    coverage = build_formalism_coverage(PROJ)
    expected_relation_counts = {
        kind.value: int(coverage["relation_counts"].get(kind.value, 0))
        for kind in EdgeKind
    }
    expected_capability_counts = {
        status: int(coverage["capability_status_counts"].get(status, 0))
        for status in ("satisfied", "partial", "open")
    }
    combined_info_bayes = summary["areas"].get("InfoGeometry", 0) + summary[
        "areas"
    ].get("BayesianMechanics", 0)

    assert v["total_topics"] == len(c.roster.topic_ids)
    assert v["total_areas"] == len(summary["areas"])
    assert v["areas"] == {
        area: {"count": count} for area, count in summary["areas"].items()
    }
    assert v["semantic_dispositions"] == summary["semantic_dispositions"]
    assert v["formalism"]["metrics"] == coverage["metrics"]
    assert v["formalism"]["relation_counts"] == expected_relation_counts
    assert v["formalism"]["capability_status_counts"] == expected_capability_counts
    assert v["combined_info_bayes_count"] == combined_info_bayes
    assert v["combined_info_bayes_count_caps"] == _SMALL_NUMBER_WORDS.get(
        combined_info_bayes, str(combined_info_bayes)
    )
    assert "compile_rate" in v
    assert v["topic_ids"] == list(c.roster.topic_ids)
    t035 = next(t for t in c.topics if t.id == "fep-035")
    row035 = v["topics"]["fep-035"]
    assert row035["area"] == "FEP"
    assert row035["maturity"] == "real"
    assert row035["maturity_icon"] == "✅"
    assert row035["mathlib_status"] == "real"
    assert int(row035["lean_chars"]) == t035.lean_chars
    assert row035["nl_statement"] == t035.nl
    assert row035["lean_sketch"] == t035.lean_sketch
    assert "maturity_icon" in v["topics"]["fep-035"]
    assert "lean_chars" in v["topics"]["fep-035"]
    assert "verify" in v
    assert (
        v["lean_toolchain"]
        == (PROJ / "lean" / "lean-toolchain")
        .read_text(encoding="utf-8")
        .strip()
        .splitlines()[0]
    )
    assert v["lean_version"] == v["lean_toolchain"].rsplit(":v", 1)[-1]
    assert v["mathlib_tag"] == f"v{v['lean_version']}"


def test_build_manuscript_vars_projects_the_canonical_citation_author(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("fep_lean.output.manuscript._count_test_cases", lambda _: 0)
    catalogue = FEPTopicCatalogue.from_yaml(PROJ / "config" / "topics.yaml")
    citation = yaml.safe_load((PROJ / "CITATION.cff").read_text(encoding="utf-8"))
    author = citation["authors"][0]

    variables = build_manuscript_vars(catalogue, PROJ)
    manuscript_config = yaml.safe_load(
        (PROJ / "manuscript/config.yaml").read_text(encoding="utf-8")
    )

    assert variables["publication"]["author"] == {
        "name": f"{author['given-names']} {author['family-names']}",
        "affiliation": author["affiliation"],
        "email": author["email"],
        "orcid": author["orcid"],
    }
    assert "authors" not in manuscript_config


def test_publication_author_rejects_a_duplicated_preferred_citation_owner(
    tmp_path: Path,
) -> None:
    _copy_publication_metadata(tmp_path)
    citation_path = tmp_path / "CITATION.cff"
    citation = yaml.safe_load(citation_path.read_text(encoding="utf-8"))
    citation["preferred-citation"]["authors"] = [dict(citation["authors"][0])]
    citation_path.write_text(
        yaml.safe_dump(citation, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )

    with pytest.raises(PublicationMetadataError, match="reuse the canonical authors"):
        load_publication_author(tmp_path)


def test_build_manuscript_vars_validates_the_canonical_graphical_abstract(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("fep_lean.output.manuscript._count_test_cases", lambda _: 0)
    catalogue = FEPTopicCatalogue.from_yaml(PROJ / "config" / "topics.yaml")

    variables = build_manuscript_vars(catalogue, PROJ)

    assert variables["publication"]["graphical_abstract"] == {
        "source_path": "manuscript/assets/graphical-abstract.png",
        "render_path": "assets/graphical-abstract.png",
        "media_type": "image/png",
        "width_px": 1536,
        "height_px": 1024,
        "sha256": "91a1898d10a0d8416661183e8cac9d6348489f6039b362b7a573d30a657b3503",
        "alt_text": (
            "Graphical abstract: the fep_lean verification pipeline. Maintained "
            "GNN-typed authoring inputs join by stable topic ID into a 155-topic, "
            "20-family catalogue with reviewed semantic dispositions; a pinned "
            "Lean 4 and Mathlib compile of FepSketches with zero warnings and "
            "zero sorry binds a source-digest-bound, claim-ready native evidence "
            "receipt; a dashed optional full mode adds Hermes and OpenGauss "
            "evidence behind its own independently validated receipt; a "
            "fail-closed manuscript projection consumes both. A green build "
            "proves a sketch compiles and never promotes a reviewed semantic "
            "disposition."
        ),
    }


def test_render_graphical_abstract_writes_canonical_deterministic_png(
    tmp_path: Path,
) -> None:
    """The builder writes the exact canonical form the config pin validates."""

    import hashlib
    import struct

    first = render_graphical_abstract(tmp_path)
    data = first.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    width, height = struct.unpack(">II", data[16:24])
    assert (width, height) == (1536, 1024)
    # 8-bit depth, RGB color type, no interlace.
    assert data[24:29] == bytes((8, 2, 0, 0, 0))

    second = render_graphical_abstract(tmp_path)
    assert second.read_bytes() == data
    assert (
        hashlib.sha256(data).hexdigest()
        == "91a1898d10a0d8416661183e8cac9d6348489f6039b362b7a573d30a657b3503"
    )


def test_build_manuscript_vars_can_disable_test_count_cache(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cache_modes: list[bool] = []

    def count_without_cache(_root: Path, *, write_cache: bool = True) -> int:
        cache_modes.append(write_cache)
        return 17

    monkeypatch.setattr(
        "fep_lean.output.manuscript._count_test_cases", count_without_cache
    )
    catalogue = FEPTopicCatalogue.from_yaml(PROJ / "config" / "topics.yaml")

    values = build_manuscript_vars(catalogue, PROJ, cache_test_count=False)

    assert values["tests"]["collected"] == 17
    assert cache_modes == [False]


def test_read_toolchain_vars_matches_disk(tmp_path: Path) -> None:
    lean = tmp_path / "lean"
    lean.mkdir(parents=True)
    (lean / "lean-toolchain").write_text("leanprover/lean4:v4.29.0\n", encoding="utf-8")
    (lean / "lakefile.lean").write_text(
        'require mathlib from git\n  "https://github.com/leanprover-community/mathlib4.git" @ "v4.29.0"\n',
        encoding="utf-8",
    )
    t = _read_toolchain_vars(tmp_path)
    assert t["lean_toolchain"] == "leanprover/lean4:v4.29.0"
    assert t["lean_version"] == "4.29.0"
    assert t["mathlib_tag"] == "v4.29.0"


def test_read_toolchain_vars_fallback_lake_manifest(tmp_path: Path) -> None:
    lean = tmp_path / "lean"
    lean.mkdir(parents=True)
    (lean / "lean-toolchain").write_text("leanprover/lean4:v4.29.0\n", encoding="utf-8")
    (lean / "lakefile.lean").write_text("package foo\n", encoding="utf-8")
    (lean / "lake-manifest.json").write_text(
        '{"packages": [{"name": "mathlib", "inputRev": "v4.29.0"}]}',
        encoding="utf-8",
    )
    t = _read_toolchain_vars(tmp_path)
    assert t["mathlib_tag"] == "v4.29.0"


def test_build_lean_catalogue_markdown_matches_topics() -> None:
    c = FEPTopicCatalogue.from_yaml(PROJ / "config" / "topics.yaml")
    md = build_lean_catalogue_markdown(c)
    assert md.count("\n```lean\n") == len(c.topics)
    assert "**Version**:" not in md
    assert "**Status**: Generated" not in md
    assert "**Source**: `src/fep_lean/output/manuscript.py`" not in md
    for t in c.topics:
        assert t.id in md
        assert t.lean_sketch.strip() in md
    last_heading = f"## {c.topics[-1].id} — {c.topics[-1].title}"
    assert f"\\newpage\n\n{last_heading}" in md


def test_write_unified_formalism_appendix_markdown_roundtrip(tmp_path: Path) -> None:
    import shutil

    shutil.copytree(PROJ / "config", tmp_path / "config")
    shutil.copytree(
        PROJ / "src" / "fep_lean" / "formal",
        tmp_path / "src" / "fep_lean" / "formal",
    )
    (tmp_path / "manuscript").mkdir(parents=True, exist_ok=True)
    c = FEPTopicCatalogue.from_yaml(tmp_path / "config" / "topics.yaml")
    out = write_unified_formalism_appendix_markdown(tmp_path, c)
    assert out.is_file()
    assert out.name == UNIFIED_FORMALISM_CATALOGUE_FILENAME
    out2 = write_unified_formalism_appendix_markdown(tmp_path, c)
    assert out2.resolve() == out.resolve()
    text = out.read_text(encoding="utf-8")
    assert text.count("```lean") == len(c.topics)
    assert f"## {c.topics[0].id} —" in text
    assert f"## {c.topics[-1].id} —" in text
    assert "### Lean sketch" in text
    assert "### Typeset statement signatures" in text
    assert "**Version**:" not in text
    assert "**Status**: Generated" not in text
    assert "**Source**: `src/fep_lean/output/manuscript.py`" not in text
    assert text.startswith("<!-- AUTO-GENERATED by src/fep_lean/output/manuscript.py")


def test_build_typeset_equations_markdown_structure() -> None:
    c = FEPTopicCatalogue.from_yaml(PROJ / "config" / "topics.yaml")
    md = build_typeset_equations_markdown(c, PROJ)
    assert "# Appendix C:" in md
    assert md.startswith("\\newpage\n\n# Appendix C:")
    assert "sec:appendix_c_latex_equations" in md
    for t in c.topics:
        assert f"## {t.id} —" in md
        assert f"sec:eqs-{t.id}" in md
        n_eq = len(re.findall(rf"\{{#eq:{re.escape(t.id)}-\d+\}}", md))
        n_th = len(re.findall(r"^\s*theorem\s+", t.lean_sketch, re.MULTILINE))
        assert n_eq > 0
        assert n_eq == n_th
    last_heading = f"## {c.topics[-1].id} — {c.topics[-1].title}"
    assert f"\\newpage\n\n{last_heading}" in md


def test_build_unified_formalism_appendix_markdown_structure() -> None:
    c = FEPTopicCatalogue.from_yaml(PROJ / "config" / "topics.yaml")
    md = build_unified_formalism_appendix_markdown(c, PROJ)
    assert "sec:appendix_b_full_topic_lean_catalogue" in md
    assert md.count("### Lean sketch") == len(c.topics)
    assert md.count("### Typeset statement signatures") == len(c.topics)
    equation_count = sum(len(topic.latex_equations) for topic in c.topics)
    labels = re.findall(r"\{#(eq:fep-\d{3}-\d+)\}", md)
    assert len(labels) == equation_count
    assert len(set(labels)) == equation_count
    assert "\\label{eq:" not in md
    assert (
        "# Appendix B: Full Lean Catalogue {#sec:appendix_b_full_topic_lean_catalogue}"
        in md
    )
    assert "# Appendix C: Typeset Equations {#sec:appendix_c_latex_equations}" in md
    for t in c.topics:
        assert f"## {t.id} — {t.title} {{#sec:catalogue-{t.id}}}" in md
        assert f"## {t.id} — {t.title} {{#sec:eqs-{t.id}}}" in md


def test_fep_001_latex_equations_from_yaml_matches_data_module() -> None:
    from fep_lean.catalogue.registry import LATEX_EQUATIONS, THEOREM_LATEX

    c = FEPTopicCatalogue.from_yaml(PROJ / "config" / "topics.yaml")
    t1 = next(t for t in c.topics if t.id == "fep-001")
    assert t1.latex_equations == tuple(LATEX_EQUATIONS["fep-001"])
    assert (
        t1.latex_equations[0]
        == THEOREM_LATEX[("fep-001", "fep001_variationalUpperBound_ge")]
    )


def test_theorem_latex_is_probability_measure_not_double_wrapped() -> None:
    from fep_lean.catalogue.registry import THEOREM_LATEX

    s = THEOREM_LATEX[("fep-002", "fep002_prob_measure_univ")]
    assert r"\mathsf{IsProbability\mathsf{Measure}" not in s
    assert r"\mathsf{IsProbabili\mathsf{Measure}" not in s
    assert r"\mathsf{IsProbabilityMeasure}" in s
    s2 = THEOREM_LATEX[("fep-002", "fep002_prob_compl")]
    assert r"\mathsf{IsProbability\mathsf{Measure}" not in s2
    assert r"\mathsf{IsProbabilityMeasure}" in s2


def test_verify_block_from_manifest_missing() -> None:
    b = _verify_block_from_manifest(None)
    assert b["manifest_present"] is False


def test_verify_block_from_manifest_invalid_json(tmp_path: Path) -> None:
    p = tmp_path / "verification_manifest.json"
    p.write_text("{not json", encoding="utf-8")
    b = _verify_block_from_manifest(p)
    assert b["manifest_present"] is True
    assert b["verify_lean_ran"] is False


def test_verify_block_from_manifest_topics_fallback(tmp_path: Path) -> None:
    p = tmp_path / "verification_manifest.json"
    p.write_text('{"results": [{"x": 1}, {"x": 2}]}', encoding="utf-8")
    b = _verify_block_from_manifest(p)
    assert b["topics_with_result"] == 2


def test_latest_verification_manifest_uses_validated_selector(
    tmp_path: Path, monkeypatch
) -> None:
    base = tmp_path / "output" / "reports"
    old = base / "run_old"
    new = base / "run_new"
    old.mkdir(parents=True)
    new.mkdir(parents=True)
    (old / "verification_manifest.json").write_text("{}", encoding="utf-8")
    (new / "verification_manifest.json").write_text("{}", encoding="utf-8")
    # The wrapper consumes only the report selected by the independent receipt
    # validator.  The fixture payloads themselves are intentionally minimal.
    (old / "summary.json").write_text(json.dumps({"complete": True}), encoding="utf-8")
    (new / "summary.json").write_text(json.dumps({"complete": True}), encoding="utf-8")
    monkeypatch.setattr(
        "fep_lean.output.manuscript.latest_claim_ready_full_report",
        lambda *_args, **_kwargs: new,
    )
    picked = _get_latest_verification_manifest(tmp_path)
    assert picked is not None
    assert "run_new" in str(picked)


def test_latest_verification_manifest_rejects_unvalidated_runs(tmp_path: Path) -> None:
    """A crashed/partial run (no complete summary) must never be served as the
    current verification block."""
    base = tmp_path / "output" / "reports"
    incomplete = base / "run_partial"
    complete_run = base / "run_complete"
    incomplete.mkdir(parents=True)
    complete_run.mkdir(parents=True)
    # The incomplete run is NEWER, but lacks a complete summary.
    (incomplete / "verification_manifest.json").write_text(
        json.dumps({"compiles_true": 9}), encoding="utf-8"
    )
    (incomplete / "summary.json").write_text(
        json.dumps({"complete": False}), encoding="utf-8"
    )
    (complete_run / "verification_manifest.json").write_text(
        json.dumps({"compiles_true": 3}), encoding="utf-8"
    )
    (complete_run / "summary.json").write_text(
        json.dumps({"complete": True}), encoding="utf-8"
    )
    import os
    import time

    # One clock read for both stamps: separate time.time() calls could
    # straddle an NTP step or coarse-FS-timestamp boundary and flip ordering.
    now = time.time()
    os.utime(incomplete / "summary.json", (now + 1, now + 1))
    assert _get_latest_verification_manifest(tmp_path) is None


def test_latest_verification_manifest_rejects_complete_catalogue_report(
    tmp_path: Path,
) -> None:
    run_dir = tmp_path / "output" / "reports" / "run_catalogue"
    run_dir.mkdir(parents=True)
    (run_dir / "summary.json").write_text(
        json.dumps({"mode": "catalogue", "complete": True}), encoding="utf-8"
    )
    (run_dir / "verification_manifest.json").write_text(
        json.dumps(
            {
                "verify_lean_ran": False,
                "topics_with_result": 0,
                "compiles_true": 0,
                "compiles_false": 0,
                "results": [],
            }
        ),
        encoding="utf-8",
    )

    assert _get_latest_verification_manifest(tmp_path) is None


def test_manuscript_vars_honor_explicit_output_root(tmp_path: Path) -> None:
    custom = tmp_path / "custom-output" / "reports" / "run_custom"
    custom.mkdir(parents=True)
    (custom / "summary.json").write_text(
        json.dumps({"complete": True}), encoding="utf-8"
    )
    (custom / "verification_manifest.json").write_text(
        json.dumps(
            {
                "verify_lean_ran": True,
                "topics_with_result": 1,
                "compiles_true": 1,
                "compiles_false": 0,
                "results": [{"topic_id": "fep-001", "compiles": True}],
            }
        ),
        encoding="utf-8",
    )
    c = FEPTopicCatalogue.from_yaml(PROJ / "config" / "topics.yaml")
    values = build_manuscript_vars(c, PROJ, output_root=tmp_path / "custom-output")
    assert values["verify"]["topics_with_result"] == 0
    assert values["verify"]["claim_ready"] is False


def test_verify_block_from_manifest_json(tmp_path: Path) -> None:
    p = tmp_path / "verification_manifest.json"
    p.write_text(
        json.dumps(
            {
                "verify_lean_ran": True,
                "topics_with_result": 3,
                "compiles_true": 1,
                "compiles_false": 2,
            }
        ),
        encoding="utf-8",
    )
    b = _verify_block_from_manifest(p)
    assert b["manifest_present"] is True
    assert b["verify_lean_ran"] is True
    assert b["topics_with_result"] == 3


def test_verify_block_reports_the_topic_duration_spread(tmp_path: Path) -> None:
    """A mean alone let "about 1-2 seconds" stand against a 14.95 s mean."""
    p = tmp_path / "verification_manifest.json"
    p.write_text(
        json.dumps(
            {
                "verify_lean_ran": True,
                "results": [
                    {"topic_id": "fep-001", "compiles": True, "duration_s": 2.5},
                    {"topic_id": "fep-002", "compiles": True, "duration_s": 9.0},
                    {"topic_id": "fep-003", "compiles": True, "duration_s": 183.5},
                ],
            }
        ),
        encoding="utf-8",
    )
    b = _verify_block_from_manifest(p)
    assert b["min_topic_s"] == 2.5
    assert b["median_topic_s"] == 9.0
    assert b["max_topic_s"] == 183.5
    # The mean sits between the median and the maximum and resembles neither,
    # which is exactly why the spread is published beside it.
    assert b["mean_topic_s"] == 65.0


def test_verify_block_spread_is_zero_without_results() -> None:
    b = _verify_block_from_manifest(None)
    assert b["min_topic_s"] == 0.0
    assert b["median_topic_s"] == 0.0
    assert b["max_topic_s"] == 0.0


def test_hermes_block_missing_summary_returns_zeros() -> None:
    block = _hermes_block_from_summary(None)
    assert block["summary_present"] is False
    assert block["processed"] == 0
    assert block["success_count"] == 0
    assert block["tokens_total"] == 0
    assert block["primary_model"] == ""
    assert block["models_used"] == ""


def test_hermes_block_aggregates_from_summary(tmp_path: Path) -> None:
    summary_path = tmp_path / "summary.json"
    summary_path.write_text(
        json.dumps(
            {
                "run_id": "20260420_111111",
                "topics": [
                    {
                        "topic_id": "fep-001",
                        "hermes_success": True,
                        "lean_compiles": True,
                        "hermes_lean_compiles": True,
                        "cache_hit": True,
                        "tokens_used": 1000,
                        "hermes_model": "z-ai/glm-5.1",
                    },
                    {
                        "topic_id": "fep-002",
                        "hermes_success": True,
                        "lean_compiles": True,
                        "hermes_lean_compiles": False,
                        "cache_hit": False,
                        "tokens_used": 2000,
                        "hermes_model": "z-ai/glm-5.1",
                    },
                    {
                        "topic_id": "fep-003",
                        "hermes_success": False,
                        "lean_compiles": False,
                        "cache_hit": False,
                        "tokens_used": 0,
                        "hermes_model": "",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    block = _hermes_block_from_summary(summary_path)
    assert block["summary_present"] is True
    assert block["run_id"] == "run_20260420_111111"
    assert block["processed"] == 3
    assert block["success_count"] == 2
    assert block["cache_hits"] == 1
    assert block["tokens_total"] == 3000
    assert block["tokens_mean"] == 1500
    assert block["hermes_lean_compiles_count"] == 1
    assert block["primary_model"] == "z-ai/glm-5.1"
    assert "z-ai/glm-5.1" in block["models_used"]
    # All three topics used the same model, so the OpenRouter chain never
    # had to advance past the primary; ``model_fallback_count`` reports 0.
    assert block["model_fallback_count"] == 0
    # No per-topic ``network_retries`` or ``chain_advance_reason`` fields in
    # this fixture ⇒ aggregates default to zero / empty.
    assert block["network_retry_count"] == 0
    assert block["chain_advance_reasons"] == {}
    assert block["chain_advance_reasons_summary"] == "none"


def test_hermes_block_counts_model_chain_advances(tmp_path: Path) -> None:
    """When a topic advances beyond the configured primary,
    ``model_fallback_count`` reports the recorded advance.

    Also asserts that per-topic ``network_retries`` sum into
    ``network_retry_count`` and ``chain_advance_reason`` strings are tallied
    into ``chain_advance_reasons``.
    """
    summary_path = tmp_path / "summary.json"
    summary_path.write_text(
        json.dumps(
            {
                "run_id": "20260420_222222",
                "topics": [
                    {
                        "hermes_model": "moonshotai/kimi-k2.6",
                        "hermes_success": True,
                        "network_retries": 1,
                    },
                    {
                        "hermes_model": "moonshotai/kimi-k2.6",
                        "hermes_success": True,
                        "network_retries": 0,
                    },
                    {
                        "hermes_model": "moonshotai/kimi-k2-thinking",
                        "hermes_success": True,
                        "network_retries": 2,
                        "chain_advance_reason": "empty_content",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    block = _hermes_block_from_summary(summary_path)
    assert block["primary_model"] == "moonshotai/kimi-k2.6"
    assert block["model_fallback_count"] == 1
    assert block["network_retry_count"] == 3
    assert block["chain_advance_reasons"] == {"empty_content": 1}
    assert block["chain_advance_reasons_summary"] == "1× empty_content"


def test_hermes_block_does_not_mislabel_a_frequently_used_fallback(
    tmp_path: Path,
) -> None:
    summary_path = tmp_path / "summary.json"
    summary_path.write_text(
        json.dumps(
            {
                "run_id": "20260420_222223",
                "topics": [
                    {
                        "hermes_model": "primary/model",
                        "hermes_success": True,
                        "chain_advance_reason": "",
                    },
                    {
                        "hermes_model": "fallback/model",
                        "hermes_success": True,
                        "chain_advance_reason": "empty_content",
                    },
                    {
                        "hermes_model": "fallback/model",
                        "hermes_success": True,
                        "chain_advance_reason": "empty_content",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    block = _hermes_block_from_summary(summary_path)

    assert block["primary_model"] == "primary/model"
    assert block["model_fallback_count"] == 2


def test_hermes_block_leaves_primary_unavailable_when_every_row_advanced(
    tmp_path: Path,
) -> None:
    summary_path = tmp_path / "summary.json"
    summary_path.write_text(
        json.dumps(
            {
                "run_id": "20260420_222224",
                "topics": [
                    {
                        "hermes_model": "fallback/a",
                        "hermes_success": True,
                        "chain_advance_reason": "empty_content",
                    },
                    {
                        "hermes_model": "fallback/b",
                        "hermes_success": True,
                        "chain_advance_reason": "wall_clock_timeout",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    block = _hermes_block_from_summary(summary_path)

    assert block["primary_model"] == ""
    assert block["model_fallback_count"] == 2


def test_hermes_block_aggregates_chain_reasons(tmp_path: Path) -> None:
    """Distinct chain-advance reasons aggregate into a sorted summary string."""
    summary_path = tmp_path / "summary.json"
    summary_path.write_text(
        json.dumps(
            {
                "run_id": "20260420_222333",
                "topics": [
                    {
                        "hermes_model": "openai/gpt-oss-120b:free",
                        "hermes_success": True,
                        "chain_advance_reason": "wall_clock_timeout",
                    },
                    {
                        "hermes_model": "openai/gpt-oss-120b:free",
                        "hermes_success": True,
                        "chain_advance_reason": "wall_clock_timeout",
                    },
                    {
                        "hermes_model": "deepseek/deepseek-chat-v3.1:free",
                        "hermes_success": True,
                        "chain_advance_reason": "transport_error",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    block = _hermes_block_from_summary(summary_path)
    assert block["chain_advance_reasons"] == {
        "wall_clock_timeout": 2,
        "transport_error": 1,
    }
    # Summary is sorted by descending count, so wall_clock_timeout comes first.
    assert block["chain_advance_reasons_summary"] == (
        "2× wall_clock_timeout, 1× transport_error"
    )


def test_build_manuscript_vars_exposes_hermes_block(
    tmp_path: Path, monkeypatch
) -> None:
    """``build_manuscript_vars`` must expose a top-level ``hermes`` block when a
    sibling ``summary.json`` is present alongside the verification manifest."""
    shutil.copytree(PROJ / "config", tmp_path / "config")
    shutil.copytree(
        PROJ / "src" / "fep_lean" / "formal",
        tmp_path / "src" / "fep_lean" / "formal",
    )
    _copy_publication_metadata(tmp_path)
    # _read_toolchain_vars only reads ``lean-toolchain``, ``lakefile.lean``,
    # ``lake-manifest.json``; skip the multi-GB ``.lake`` build cache and the
    # transient FepSketches verification scratch dir.
    shutil.copytree(
        PROJ / "lean",
        tmp_path / "lean",
        ignore=shutil.ignore_patterns(".lake", "FepSketches"),
    )
    run_dir = tmp_path / "output" / "reports" / "run_test_hermes_block"
    run_dir.mkdir(parents=True)
    (run_dir / "verification_manifest.json").write_text(
        json.dumps(
            {
                "verify_lean_ran": True,
                "topics_with_result": 2,
                "compiles_true": 2,
                "compiles_false": 0,
                "results": [
                    {"topic_id": "fep-001", "compiles": True, "lean_has_sorry": False},
                    {"topic_id": "fep-002", "compiles": True, "lean_has_sorry": False},
                ],
            }
        ),
        encoding="utf-8",
    )
    (run_dir / "summary.json").write_text(
        json.dumps(
            {
                "run_id": "test_hermes_block",
                "complete": True,
                "topics": [
                    {
                        "topic_id": "fep-001",
                        "hermes_success": True,
                        "lean_compiles": True,
                        "hermes_lean_compiles": True,
                        "cache_hit": False,
                        "tokens_used": 500,
                        "hermes_model": "z-ai/glm-5.1",
                    },
                    {
                        "topic_id": "fep-002",
                        "hermes_success": True,
                        "lean_compiles": True,
                        "hermes_lean_compiles": True,
                        "cache_hit": True,
                        "tokens_used": 1500,
                        "hermes_model": "z-ai/glm-5.1",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "fep_lean.output.manuscript.latest_claim_ready_full_report",
        lambda *_args, **_kwargs: run_dir,
    )
    monkeypatch.setattr("fep_lean.output.manuscript._count_test_cases", lambda _: 1)
    c = FEPTopicCatalogue.from_yaml(tmp_path / "config" / "topics.yaml")
    v = build_manuscript_vars(c, tmp_path)
    assert "hermes" in v
    assert v["hermes"]["summary_present"] is True
    assert v["hermes"]["processed"] == 2
    assert v["hermes"]["success_count"] == 2
    assert v["hermes"]["cache_hits"] == 1
    assert v["hermes"]["tokens_mean"] == 1000
    assert v["hermes"]["primary_model"] == "z-ai/glm-5.1"
    assert v["hermes"]["hermes_lean_compiles_count"] == 2
    assert "tests" in v
    assert v["tests"]["collected"] == 1


def test_write_manuscript_vars_roundtrip(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    shutil.copytree(PROJ / "config", tmp_path / "config")
    _copy_publication_metadata(tmp_path)
    for d in ("scripts", "tests", "src", "output"):
        (tmp_path / d).mkdir()
    (tmp_path / "src" / "__init__.py").write_text('"""x"""\n', encoding="utf-8")
    shutil.copytree(
        PROJ / "src" / "fep_lean" / "formal",
        tmp_path / "src" / "fep_lean" / "formal",
    )
    shutil.copytree(
        PROJ / "lean",
        tmp_path / "lean",
        ignore=shutil.ignore_patterns(".lake", "FepSketches"),
    )
    monkeypatch.setattr("fep_lean.output.manuscript._count_test_cases", lambda _: 1)

    c = FEPTopicCatalogue.from_yaml(tmp_path / "config" / "topics.yaml")
    out = write_manuscript_vars(tmp_path, c)
    assert out.is_file()
    data = yaml.safe_load(out.read_text(encoding="utf-8"))
    assert data["total_topics"] == len(c.topics)
    assert (tmp_path / "manuscript" / UNIFIED_FORMALISM_CATALOGUE_FILENAME).is_file()
    expected_toolchain = _read_toolchain_vars(tmp_path)
    assert data["lean_version"] == expected_toolchain["lean_version"]
    assert data["mathlib_tag"] == expected_toolchain["mathlib_tag"]
    assert data["lean_toolchain"] == expected_toolchain["lean_toolchain"]


def test_write_manuscript_vars_rolls_back_projection_pair_on_replace_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    vars_path = manuscript / "manuscript_vars.yaml"
    appendix_path = manuscript / UNIFIED_FORMALISM_CATALOGUE_FILENAME
    vars_before = b"old: variables\n"
    appendix_before = b"old appendix\n"
    vars_path.write_bytes(vars_before)
    appendix_path.write_bytes(appendix_before)
    catalogue = FEPTopicCatalogue.from_yaml(PROJ / "config" / "topics.yaml")
    monkeypatch.setattr(
        manuscript_module,
        "build_manuscript_vars",
        lambda *args, **kwargs: {"new": True},
    )
    real_replace = os.replace
    installs = 0

    def fail_second_install(source: object, destination: object) -> None:
        nonlocal installs
        if Path(destination) in {vars_path, appendix_path}:
            installs += 1
            if installs == 2:
                real_replace(source, destination)
                raise OSError("injected pair install failure")
        real_replace(source, destination)

    monkeypatch.setattr(manuscript_module.os, "replace", fail_second_install)

    with pytest.raises(OSError, match="injected pair install failure"):
        write_manuscript_vars(tmp_path, catalogue)

    assert vars_path.read_bytes() == vars_before
    assert appendix_path.read_bytes() == appendix_before
    assert not tuple(manuscript.glob(".*.tmp"))


def test_write_manuscript_vars_rolls_back_absent_pair_on_keyboard_interrupt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "manuscript").mkdir()
    vars_path = tmp_path / "manuscript" / "manuscript_vars.yaml"
    appendix_path = tmp_path / "manuscript" / UNIFIED_FORMALISM_CATALOGUE_FILENAME
    catalogue = FEPTopicCatalogue.from_yaml(PROJ / "config" / "topics.yaml")
    monkeypatch.setattr(
        manuscript_module,
        "build_manuscript_vars",
        lambda *args, **kwargs: {"new": True},
    )
    real_replace = os.replace
    installs = 0

    def interrupt_second_install(source: object, destination: object) -> None:
        nonlocal installs
        if Path(destination) in {vars_path, appendix_path}:
            installs += 1
            if installs == 2:
                real_replace(source, destination)
                raise KeyboardInterrupt
        real_replace(source, destination)

    monkeypatch.setattr(manuscript_module.os, "replace", interrupt_second_install)

    with pytest.raises(KeyboardInterrupt):
        write_manuscript_vars(tmp_path, catalogue)

    assert not vars_path.exists()
    assert not appendix_path.exists()
    assert not tuple((tmp_path / "manuscript").glob(".*.tmp"))


def test_manuscript_projection_writers_reject_symlinked_destination_ancestor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "project"
    root.mkdir()
    outside = tmp_path / "outside-manuscript"
    outside.mkdir()
    (root / "manuscript").symlink_to(outside, target_is_directory=True)
    catalogue = FEPTopicCatalogue.from_yaml(PROJ / "config" / "topics.yaml")
    monkeypatch.setattr(
        manuscript_module,
        "build_manuscript_vars",
        lambda *args, **kwargs: {"new": True},
    )

    with pytest.raises(ValueError, match="symlink path component"):
        write_manuscript_vars(root, catalogue)
    with pytest.raises(ValueError, match="symlink path component"):
        write_unified_formalism_appendix_markdown(root, catalogue)

    assert not tuple(outside.iterdir())


def test_count_test_cases_is_content_addressed_over_production_parameters(
    tmp_path: Path,
) -> None:
    """A production-only parameter change must invalidate collection cache."""
    (tmp_path / "tests").mkdir()
    parameter_source = (
        tmp_path
        / "src"
        / "fep_lean"
        / "catalogue"
        / "bodies"
        / "causal_blankets_interventions.py"
    )
    parameter_source.parent.mkdir(parents=True)
    parameter_source.write_text("alpha\nbeta\n", encoding="utf-8")
    test_file = tmp_path / "tests" / "test_sample.py"
    test_file.write_text(
        "from pathlib import Path\n"
        "import pytest\n"
        "PARAMETERS = (Path(__file__).parents[1] / "
        "'src/fep_lean/catalogue/bodies/causal_blankets_interventions.py').read_text().splitlines()\n"
        "@pytest.mark.parametrize('value', PARAMETERS)\n"
        "def test_value(value): assert value\n",
        encoding="utf-8",
    )

    assert _count_test_cases(tmp_path) == 2
    cache_path = tmp_path / "output" / ".cache" / "tests_collected.json"
    first_cache = json.loads(cache_path.read_text(encoding="utf-8"))
    assert first_cache["schema_version"] == 5

    parameter_source.write_text("alpha\nbeta\ngamma\n", encoding="utf-8")

    assert _count_test_cases(tmp_path) == 3
    second_cache = json.loads(cache_path.read_text(encoding="utf-8"))
    assert second_cache["input_sha256"] != first_cache["input_sha256"]
    assert not tuple(tmp_path.rglob("__pycache__"))
    assert not (tmp_path / ".pytest_cache").exists()


def test_test_collection_fingerprint_recursively_binds_python_test_helpers(
    tmp_path: Path,
) -> None:
    nested = tmp_path / "tests" / "unit"
    nested.mkdir(parents=True)
    helper = nested / "helpers.py"
    conftest = nested / "conftest.py"
    helper.write_text("VALUE = 1\n", encoding="utf-8")
    conftest.write_text("pytest_plugins = ()\n", encoding="utf-8")

    paths = _test_collection_input_paths(tmp_path)
    first = _test_collection_fingerprint(tmp_path)
    helper.write_text("VALUE = 2\n", encoding="utf-8")
    second = _test_collection_fingerprint(tmp_path)

    assert helper in paths
    assert conftest in paths
    assert second != first


def test_collection_runtime_identity_canonicalizes_interpreter_aliases(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    interpreter = tmp_path / "python-real"
    interpreter.write_bytes(b"interpreter fixture\n")
    first_alias = tmp_path / "python"
    second_alias = tmp_path / "python3"
    first_alias.symlink_to(interpreter)
    second_alias.symlink_to(interpreter)

    monkeypatch.setattr(sys, "executable", str(first_alias))
    first = manuscript_module._collection_runtime_identity()
    monkeypatch.setattr(sys, "executable", str(second_alias))
    second = manuscript_module._collection_runtime_identity()

    assert first == second
    assert first["interpreter"]["executable"] == interpreter.as_posix()


@pytest.mark.parametrize("surface", ("tests", "src", "config"))
def test_test_collection_inputs_reject_symlinked_surface_ancestors(
    tmp_path: Path, surface: str
) -> None:
    root = tmp_path / "project"
    root.mkdir()
    outside = tmp_path / f"outside-{surface}"
    outside.mkdir()
    (root / surface).symlink_to(outside, target_is_directory=True)

    with pytest.raises(ValueError, match="symlink path component"):
        _test_collection_input_paths(root)


def test_test_collection_inputs_reject_owner_path_escape(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "project"
    root.mkdir()
    outside = tmp_path / "outside.py"
    outside.write_text("VALUE = 1\n", encoding="utf-8")
    monkeypatch.setattr(
        manuscript_module, "source_owner_paths", lambda _root: (outside,)
    )
    monkeypatch.setattr(manuscript_module, "config_owner_paths", lambda _root: ())

    with pytest.raises(ValueError, match="path escapes project root"):
        _test_collection_input_paths(root)


def test_test_collection_inputs_reject_symlink_in_project_root_ancestry(
    tmp_path: Path,
) -> None:
    actual_parent = tmp_path / "actual"
    root = actual_parent / "project"
    root.mkdir(parents=True)
    linked_parent = tmp_path / "linked"
    linked_parent.symlink_to(actual_parent, target_is_directory=True)
    linked_root = linked_parent / "project"

    with pytest.raises(ValueError, match="project root ancestor is a symlink"):
        _test_collection_input_paths(linked_root)


@pytest.mark.parametrize("linked_component", ("output", "cache", "cache_file"))
def test_count_test_cases_rejects_symlinked_cache_ancestors(
    tmp_path: Path, linked_component: str
) -> None:
    root = tmp_path / "project"
    root.mkdir()
    (root / "tests").mkdir()
    outside = tmp_path / "outside-cache"
    outside.mkdir()
    if linked_component == "output":
        (root / "output").symlink_to(outside, target_is_directory=True)
    elif linked_component == "cache":
        (root / "output").mkdir()
        (root / "output" / ".cache").symlink_to(outside, target_is_directory=True)
    else:
        cache_dir = root / "output" / ".cache"
        cache_dir.mkdir(parents=True)
        outside_file = outside / "tests_collected.json"
        outside_file.write_text("{}\n", encoding="utf-8")
        (cache_dir / "tests_collected.json").symlink_to(outside_file)

    with pytest.raises(ValueError, match="symlink path component"):
        _count_test_cases(root, write_cache=False)


def test_count_test_cases_rejects_non_directory_cache_ancestor(tmp_path: Path) -> None:
    root = tmp_path / "project"
    root.mkdir()
    (root / "tests").mkdir()
    (root / "output").mkdir()
    (root / "output" / ".cache").write_text("not a directory\n", encoding="utf-8")

    with pytest.raises(ValueError, match="non-directory path component"):
        _count_test_cases(root, write_cache=False)


def test_count_test_cases_rejects_partial_count_from_failed_collection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_sample.py").write_text("def test_sample(): pass\n", encoding="utf-8")
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args=args[0],
            returncode=2,
            stdout="1 test collected\n",
            stderr="import error",
        ),
    )

    with pytest.raises(ValueError, match="pytest collection failed with exit code 2"):
        _count_test_cases(tmp_path)

    assert not (tmp_path / "output" / ".cache" / "tests_collected.json").exists()


def test_count_test_cases_rejects_collection_timeout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_sample.py").write_text("def test_sample(): pass\n", encoding="utf-8")

    def raise_timeout(*args: object, **kwargs: object) -> None:
        raise subprocess.TimeoutExpired(cmd="pytest --collect-only", timeout=120)

    monkeypatch.setattr(subprocess, "run", raise_timeout)

    with pytest.raises(
        ValueError, match="pytest collection timed out after 120 seconds"
    ):
        _count_test_cases(tmp_path)


@pytest.mark.parametrize(
    "collection_output", ("collection complete\n", "0 tests collected\n")
)
def test_count_test_cases_rejects_missing_positive_count(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    collection_output: str,
) -> None:
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_sample.py").write_text("def test_sample(): pass\n", encoding="utf-8")
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args=args[0], returncode=0, stdout=collection_output, stderr=""
        ),
    )

    with pytest.raises(ValueError, match="exactly one anchored positive summary"):
        _count_test_cases(tmp_path)


def test_count_test_cases_uses_final_pytest_summary_count(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_sample.py").write_text("def test_sample(): pass\n", encoding="utf-8")
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args=args[0],
            returncode=0,
            stdout=(
                "tests/test_sample.py::test_label[0 tests collected\\n]\n"
                "tests/test_sample.py::test_second\n"
                "tests/test_sample.py::test_third\n"
                "===== 3 tests collected in 0.01s =====\n"
            ),
            stderr="",
        ),
    )

    assert _count_test_cases(tmp_path) == 3


@pytest.mark.parametrize(
    ("stdout", "stderr", "message"),
    (
        (
            "===== 2 tests collected in 0.01s =====\n"
            + "===== 3 tests collected in 0.02s =====\n",
            "",
            "exactly one anchored positive summary; found 2",
        ),
        (
            "===== 2 tests collected in 0.01s =====\n",
            "delayed warning\n",
            "wrote unexpected stderr",
        ),
        (
            "===== 2 tests collected in 0.01s =====\ntrailing stdout\n",
            "",
            "summary was not the final stdout line",
        ),
    ),
)
def test_count_test_cases_rejects_ambiguous_summary_or_trailing_stderr(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    stdout: str,
    stderr: str,
    message: str,
) -> None:
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_sample.py").write_text("def test_sample(): pass\n", encoding="utf-8")
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args=args[0], returncode=0, stdout=stdout, stderr=stderr
        ),
    )

    with pytest.raises(ValueError, match=message):
        _count_test_cases(tmp_path)


def test_count_test_cases_preserves_prior_cache_when_atomic_replace_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_sample.py").write_text("def test_sample(): pass\n", encoding="utf-8")
    cache = tmp_path / "output" / ".cache" / "tests_collected.json"
    cache.parent.mkdir(parents=True)
    prior_bytes = b'{"schema_version":1,"collected":41}\n'
    cache.write_bytes(prior_bytes)
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args=args[0],
            returncode=0,
            stdout=(
                "tests/test_sample.py::test_sample\n"
                "===== 1 test collected in 0.01s =====\n"
            ),
            stderr="",
        ),
    )

    def reject_replace(source: object, destination: object) -> None:
        raise OSError("injected replace failure")

    monkeypatch.setattr(os, "replace", reject_replace)

    with pytest.raises(OSError, match="injected replace failure"):
        _count_test_cases(tmp_path)

    assert cache.read_bytes() == prior_bytes


def test_count_test_cases_check_fails_without_cache_or_subprocess_side_effects(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_sample.py").write_text("def test_sample(): pass\n", encoding="utf-8")
    before = tuple(sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*")))

    def reject_subprocess(*args: object, **kwargs: object) -> None:
        raise AssertionError("check mode must not launch pytest")

    monkeypatch.setattr(subprocess, "run", reject_subprocess)

    with pytest.raises(ValueError, match="test collection cache is missing"):
        _count_test_cases(tmp_path, write_cache=False)

    after = tuple(sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*")))
    assert after == before
    assert not tuple(tmp_path.rglob("__pycache__"))
    assert not (tmp_path / "output" / ".cache" / "tests_collected.json").exists()


def test_count_test_cases_does_not_replace_stale_cache_when_writes_are_disabled(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_sample.py").write_text("def test_sample(): pass\n", encoding="utf-8")
    cache = tmp_path / "output" / ".cache" / "tests_collected.json"
    cache.parent.mkdir(parents=True)
    prior_bytes = b'{"schema_version":1,"collected":41}\n'
    cache.write_bytes(prior_bytes)

    def reject_subprocess(*args: object, **kwargs: object) -> None:
        raise AssertionError("check mode must not launch pytest")

    monkeypatch.setattr(subprocess, "run", reject_subprocess)

    with pytest.raises(ValueError, match="test collection cache is stale or invalid"):
        _count_test_cases(tmp_path, write_cache=False)

    assert cache.read_bytes() == prior_bytes
    assert not tuple(tmp_path.rglob("__pycache__"))


def test_test_count_generation_is_hermetic_and_check_reuses_cache_read_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tests = tmp_path / "tests" / "unit"
    tests.mkdir(parents=True)
    (tests / "test_sample.py").write_text("def test_sample(): pass\n", encoding="utf-8")
    captured: dict[str, object] = {}

    def collect(
        command: list[str], **kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        captured["command"] = command
        captured.update(kwargs)
        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout=(
                "tests/unit/test_sample.py::test_sample\n"
                "===== 1 test collected in 0.01s =====\n"
            ),
            stderr="",
        )

    monkeypatch.setattr(subprocess, "run", collect)

    assert _count_test_cases(tmp_path) == 1

    command = captured["command"]
    assert isinstance(command, list)
    assert command[:4] == [sys.executable, "-m", "pytest", "tests"]
    assert command[command.index("-p") + 1] == "pytest_timeout"
    cache_option = command[command.index("-o") + 1]
    assert cache_option.startswith("cache_dir=")
    assert not Path(cache_option.removeprefix("cache_dir=")).exists()
    environment = captured["env"]
    assert isinstance(environment, dict)
    assert environment["PYTHONDONTWRITEBYTECODE"] == "1"
    assert environment["PYTEST_ADDOPTS"] == ""
    assert environment["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] == "1"
    assert environment["PYTHONHASHSEED"] == "0"
    assert environment["FEP_LEAN_LIVE_TESTS"] == "0"
    cache = tmp_path / "output" / ".cache" / "tests_collected.json"
    payload = json.loads(cache.read_text(encoding="utf-8"))
    assert payload["schema_version"] == 5
    assert payload["node_ids"] == ["tests/unit/test_sample.py::test_sample"]
    assert payload["collection_identity"]["plugin_distributions"]["pytest"]
    before = tuple(sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*")))
    cache_bytes = cache.read_bytes()

    def reject_subprocess(*args: object, **kwargs: object) -> None:
        raise AssertionError("check mode must reuse the validated cache")

    monkeypatch.setattr(subprocess, "run", reject_subprocess)

    assert _count_test_cases(tmp_path, write_cache=False) == 1
    assert cache.read_bytes() == cache_bytes
    assert (
        tuple(sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*")))
        == before
    )
    assert not tuple(tmp_path.rglob("__pycache__"))


def test_test_count_cache_is_bound_to_runtime_and_plugin_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_sample.py").write_text("def test_sample(): pass\n", encoding="utf-8")
    identity = manuscript_module._collection_runtime_identity()
    monkeypatch.setattr(
        manuscript_module, "_collection_runtime_identity", lambda: identity
    )
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda command, **kwargs: subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout=(
                "tests/test_sample.py::test_sample\n"
                "===== 1 test collected in 0.01s =====\n"
            ),
            stderr="",
        ),
    )
    assert _count_test_cases(tmp_path) == 1
    changed_identity = json.loads(json.dumps(identity))
    changed_identity["plugin_distributions"]["pytest"] = "changed-version"
    monkeypatch.setattr(
        manuscript_module,
        "_collection_runtime_identity",
        lambda: changed_identity,
    )

    with pytest.raises(ValueError, match="test collection cache is stale or invalid"):
        _count_test_cases(tmp_path, write_cache=False)


def test_test_count_cache_rejects_a_tampered_collected_total(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_sample.py").write_text("def test_sample(): pass\n", encoding="utf-8")
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda command, **kwargs: subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout=(
                "tests/test_sample.py::test_sample\n"
                "===== 1 test collected in 0.01s =====\n"
            ),
            stderr="",
        ),
    )
    assert _count_test_cases(tmp_path) == 1
    cache = tmp_path / "output" / ".cache" / "tests_collected.json"
    payload = json.loads(cache.read_text(encoding="utf-8"))
    payload["collected"] = 999
    cache.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="test collection cache is stale or invalid"):
        _count_test_cases(tmp_path, write_cache=False)


def test_test_count_generation_rejects_inputs_changed_during_collection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tests = tmp_path / "tests"
    tests.mkdir()
    test_file = tests / "test_sample.py"
    test_file.write_text("def test_sample(): pass\n", encoding="utf-8")

    def collect_after_mutation(
        command: list[str], **kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        test_file.write_text(
            "def test_sample(): pass\ndef test_added(): pass\n", encoding="utf-8"
        )
        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout=(
                "tests/test_sample.py::test_sample\n"
                "===== 1 test collected in 0.01s =====\n"
            ),
            stderr="",
        )

    monkeypatch.setattr(subprocess, "run", collect_after_mutation)

    with pytest.raises(
        ValueError, match="test collection inputs or runtime changed during collection"
    ):
        _count_test_cases(tmp_path)
    assert not (tmp_path / "output" / ".cache" / "tests_collected.json").exists()


def test_live_preamble_carries_every_declared_pdf_metadata_string() -> None:
    """The published preamble must already agree with ``config.yaml``."""
    assert pdf_metadata_drift(PROJ) == ()
    fields = pdf_metadata_fields(PROJ)
    preamble = (PROJ / "manuscript/preamble.md").read_text(encoding="utf-8")
    assert f"pdfsubject={{{fields['pdfsubject']}}}" in preamble
    assert f"pdfkeywords={{{fields['pdfkeywords']}}}" in preamble


def test_pdf_metadata_drift_reports_a_changed_keyword_list(tmp_path: Path) -> None:
    """A keyword added to config alone must fail before the PDF is built."""
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir(parents=True)
    config_path = manuscript / "config.yaml"
    shutil.copy2(PROJ / "manuscript/config.yaml", config_path)
    shutil.copy2(PROJ / "manuscript/preamble.md", manuscript / "preamble.md")
    assert pdf_metadata_drift(tmp_path) == ()

    config_path.write_text(
        config_path.read_text(encoding="utf-8").replace(
            '  - "mathlib4"\n', '  - "mathlib4"\n  - "unannounced keyword"\n'
        ),
        encoding="utf-8",
    )
    drift = pdf_metadata_drift(tmp_path)
    assert len(drift) == 1
    assert "pdfkeywords does not match" in drift[0]
    assert "unannounced keyword" in drift[0]


def test_pdf_metadata_drift_reports_a_missing_hypersetup_field(tmp_path: Path) -> None:
    """Deleting the preamble copy must fail rather than silently drop metadata."""
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir(parents=True)
    shutil.copy2(PROJ / "manuscript/config.yaml", manuscript / "config.yaml")
    fields = pdf_metadata_fields(PROJ)
    preamble = (PROJ / "manuscript/preamble.md").read_text(encoding="utf-8")
    (manuscript / "preamble.md").write_text(
        preamble.replace(f"  pdfsubject={{{fields['pdfsubject']}}},\n", ""),
        encoding="utf-8",
    )
    drift = pdf_metadata_drift(tmp_path)
    assert len(drift) == 1
    assert "declares no \\hypersetup pdfsubject" in drift[0]


def test_pdf_metadata_fields_reject_a_latex_unsafe_keyword(tmp_path: Path) -> None:
    """A brace or the separator inside a keyword would corrupt ``\\hypersetup``."""
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir(parents=True)
    (manuscript / "config.yaml").write_text(
        (PROJ / "manuscript/config.yaml")
        .read_text(encoding="utf-8")
        .replace('  - "mathlib4"\n', '  - "mathlib4; smuggled"\n'),
        encoding="utf-8",
    )
    with pytest.raises(PublicationMetadataError, match="not LaTeX-safe"):
        pdf_metadata_fields(tmp_path)
