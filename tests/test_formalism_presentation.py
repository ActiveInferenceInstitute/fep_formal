"""The presentation join conserves the two canonical evidence sources."""

from __future__ import annotations

import shutil
from collections import Counter
from collections.abc import MutableMapping
from dataclasses import FrozenInstanceError
from pathlib import Path
from typing import cast

import pytest

from fep_lean.catalogue.coverage import build_formalism_coverage
from fep_lean.output import formal_kernel_dashboard, formalism_atlas
from fep_lean.output.formal_kernel_dashboard import (
    formal_kernel_dashboard_drift,
    write_formal_kernel_dashboard,
)
from fep_lean.output.formalism_atlas import (
    atlas_projection_drift,
    write_formalism_atlas,
)
from fep_lean.output.formalism_presentation import (
    FormalismPresentation,
    build_formalism_presentation,
    humanize_formalism_identifier,
)
from fep_lean.verification.numerical_witnesses import (
    NON_PROOF_EVIDENCE,
    evaluate_numerical_witnesses,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_scientific_acronyms_survive_human_readable_labels() -> None:
    assert (
        humanize_formalism_identifier("closed-loop-policy-trees-and-efe")
        == "Closed Loop Policy Trees And EFE"
    )
    assert humanize_formalism_identifier("finite-kl-cmi") == "Finite KL CMI"


def test_presentation_join_conserves_canonical_sources_and_is_immutable() -> None:
    coverage = build_formalism_coverage(PROJECT_ROOT)
    evaluated = evaluate_numerical_witnesses(scope="catalogue")
    presentation = build_formalism_presentation(PROJECT_ROOT)

    assert tuple(topic.id for topic in presentation.topics) == tuple(
        row["id"] for row in coverage["topics"]
    )
    assert tuple(
        (relation.source, relation.kind, relation.target, relation.witness)
        for relation in presentation.relations
    ) == tuple(
        (row["source"], row["kind"], row["target"], row["witness"])
        for row in coverage["relations"]
    )
    assert presentation.witnesses == evaluated
    assert presentation.metrics == coverage["metrics"]
    assert len(presentation.topics) == 155
    assert len(presentation.areas) == 5
    assert len(presentation.families) == 20
    assert len(presentation.witnesses) == 15
    assert presentation.unmatched_witness_families == ()
    assert all(
        witness.evidence_kind == NON_PROOF_EVIDENCE
        for witness in presentation.witnesses
    )
    assert all(witness.accepted for witness in presentation.witnesses)

    review_date_field = "review_date"
    with pytest.raises(FrozenInstanceError):
        setattr(presentation, review_date_field, "mutable")
    mutable_metrics = cast(MutableMapping[str, int], presentation.metrics)
    with pytest.raises(TypeError):
        mutable_metrics["topics"] = 0


def test_renderers_depend_only_on_the_shared_presentation_join(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The atlas and dashboard must model everything through the shared join.

    The join seam inside each renderer module returns a snapshot built before
    the patch, while the canonical sources one layer below are wired to
    explode. A renderer that reaches ``build_formalism_coverage`` or
    ``evaluate_numerical_witnesses`` directly fails here, and a renderer that
    stops fetching the join fails the seam record before its drift gate can
    bless anything.
    """
    presentation = build_formalism_presentation(PROJECT_ROOT)
    join_calls: list[Path] = []

    def _poison_canonical_source(*_args: object, **_kwargs: object) -> object:
        raise AssertionError(
            "renderer reached a canonical source instead of the shared join"
        )

    def _join_stub(project_root: Path) -> FormalismPresentation:
        join_calls.append(Path(project_root))
        return presentation

    monkeypatch.setattr(formalism_atlas, "build_formalism_presentation", _join_stub)
    monkeypatch.setattr(
        formal_kernel_dashboard, "build_formalism_presentation", _join_stub
    )
    monkeypatch.setattr(
        "fep_lean.catalogue.coverage.build_formalism_coverage",
        _poison_canonical_source,
    )
    monkeypatch.setattr(
        "fep_lean.verification.numerical_witnesses.evaluate_numerical_witnesses",
        _poison_canonical_source,
    )

    atlas_root = tmp_path / "atlas"
    write_formalism_atlas(PROJECT_ROOT, output_root=atlas_root)
    assert join_calls == [PROJECT_ROOT]
    assert atlas_projection_drift(PROJECT_ROOT, output_root=atlas_root) == ()

    join_calls.clear()
    dashboard_root = tmp_path / "dashboard"
    write_formal_kernel_dashboard(PROJECT_ROOT, output_root=dashboard_root)
    assert join_calls == [PROJECT_ROOT]
    assert (
        formal_kernel_dashboard_drift(PROJECT_ROOT, output_root=dashboard_root)
        == ()
    )


def test_family_summaries_conserve_witness_formal_alignment() -> None:
    presentation = build_formalism_presentation(PROJECT_ROOT)
    witnesses_by_family = {
        family.id: tuple(
            witness for witness in presentation.witnesses if witness.family == family.id
        )
        for family in presentation.families
    }

    for family in presentation.families:
        expected = Counter(
            witness.formal_alignment for witness in witnesses_by_family[family.id]
        )
        assert dict(family.formal_alignment_counts) == dict(sorted(expected.items()))

    learning_family = next(
        family
        for family in presentation.families
        if family.id == "learning-concentration-and-model-evidence"
    )
    assert dict(learning_family.formal_alignment_counts) == {"structural_analogue": 1}


def test_presentation_resolves_witnesses_against_the_supplied_checkout(
    tmp_path: Path,
) -> None:
    config = tmp_path / "config"
    config.mkdir()
    for name in (
        "catalogue_metadata.yaml",
        "theorem_maturity.yaml",
        "formalism_relations.yaml",
    ):
        shutil.copy2(PROJECT_ROOT / "config" / name, config / name)
    shutil.copytree(
        PROJECT_ROOT / "src" / "fep_lean" / "formal",
        tmp_path / "src" / "fep_lean" / "formal",
    )
    predictive = tmp_path / "src" / "fep_lean" / "formal" / "predictive_coding.lean"
    source = predictive.read_text(encoding="utf-8")
    source = source.replace(
        "theorem predictionError_update", "theorem predictionError_update_removed", 1
    )
    predictive.write_text(source, encoding="utf-8")

    with pytest.raises(
        ValueError,
        match=(
            "finite-jet-error-descent -> FEP.PredictiveCoding.predictionError_update"
        ),
    ):
        build_formalism_presentation(tmp_path)
