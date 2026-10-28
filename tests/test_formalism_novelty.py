"""Novelty claims are complete, ordered, and tied to compiled bridges."""

from __future__ import annotations

import shutil
from collections.abc import Callable
from pathlib import Path

import pytest
import yaml

from fep_formal.catalogue.generation import build_topics_data
from fep_formal.catalogue.novelty import (
    NoveltyValidationError,
    load_formalism_novelty,
)
from fep_formal.catalogue.schema import load_catalogue_metadata
from fep_formal.formal.declarations import composed_theorem_sources
from fep_formal.formal.manifest import FormalModuleRole, formal_resource_paths

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _write_ledger(path: Path, topics: list[dict[str, object]]) -> None:
    path.write_text(
        yaml.safe_dump(
            {
                "schema_version": 1,
                "baseline_last_id": "fep-050",
                "topics": topics,
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )


def _row(topic_id: str = "fep-051") -> dict[str, object]:
    return {
        "id": topic_id,
        "nearest_topics": ["fep-017"],
        "new_invariant": "Reconstruction is equivalent to absolute continuity.",
        "carrier_delta": "Moves from finite atoms to native finite measures.",
        "required_bridge": "FEPComposed.fep051_rn_reconstruction_refines_fep017",
    }


def test_live_expansion_ledger_is_complete_and_uses_declared_bridges() -> None:
    metadata = load_catalogue_metadata(
        PROJECT_ROOT / "config" / "catalogue_metadata.yaml"
    )
    sources = composed_theorem_sources(PROJECT_ROOT)
    ledger = load_formalism_novelty(
        PROJECT_ROOT / "config" / "formalism_novelty.yaml",
        metadata.topic_ids,
        composed_sources=sources,
    )

    assert ledger.baseline_last_id == "fep-050"
    assert tuple(record.id for record in ledger.records) == metadata.topic_ids[50:]
    assert len({record.required_bridge for record in ledger.records}) == len(
        ledger.records
    )
    for record in ledger.records:
        source = sources[record.required_bridge]
        assert f"fep_fep{record.id.removeprefix('fep-')}." in source
        assert any(
            f"fep_fep{nearest.removeprefix('fep-')}." in source
            for nearest in record.nearest_topics
        )


def test_expansion_row_requires_a_resolved_composed_bridge(tmp_path: Path) -> None:
    path = tmp_path / "novelty.yaml"
    row = _row()
    _write_ledger(path, [row])
    roster = tuple(f"fep-{index:03d}" for index in range(1, 52))

    ledger = load_formalism_novelty(
        path,
        roster,
        composed_sources={
            str(row["required_bridge"]): (
                "fep_fep051.FEP051.fep051_claim fep_fep017.FEP017.fep017_claim"
            )
        },
    )

    assert ledger.by_topic_id["fep-051"].nearest_topics == ("fep-017",)

    with pytest.raises(NoveltyValidationError, match="does not resolve"):
        load_formalism_novelty(
            path,
            roster,
            composed_sources={},
        )


def test_novelty_bridge_must_use_the_new_topic_and_a_declared_nearest_topic(
    tmp_path: Path,
) -> None:
    path = tmp_path / "novelty.yaml"
    row = _row()
    _write_ledger(path, [row])

    with pytest.raises(NoveltyValidationError, match="nearest-topic endpoint"):
        load_formalism_novelty(
            path,
            tuple(f"fep-{index:03d}" for index in range(1, 52)),
            composed_sources={
                str(row["required_bridge"]): "fep_fep051.FEP051.fep051_claim"
            },
        )


def test_novelty_bridge_does_not_count_comment_only_endpoint_mentions(
    tmp_path: Path,
) -> None:
    path = tmp_path / "novelty.yaml"
    row = _row()
    _write_ledger(path, [row])

    with pytest.raises(NoveltyValidationError, match="nearest-topic endpoint"):
        load_formalism_novelty(
            path,
            tuple(f"fep-{index:03d}" for index in range(1, 52)),
            composed_sources={
                str(row["required_bridge"]): (
                    "fep_fep051.FEP051.fep051_claim\n-- fep_fep017.FEP017.fep017_claim"
                )
            },
        )


def test_novelty_rows_cannot_reuse_one_bridge_declaration(tmp_path: Path) -> None:
    path = tmp_path / "novelty.yaml"
    first = _row("fep-051")
    second = _row("fep-052")
    second["required_bridge"] = first["required_bridge"]
    _write_ledger(path, [first, second])
    shared = str(first["required_bridge"])

    with pytest.raises(NoveltyValidationError, match="unique required_bridge"):
        load_formalism_novelty(
            path,
            tuple(f"fep-{index:03d}" for index in range(1, 53)),
            composed_sources={
                shared: (
                    "fep_fep051.FEP051.fep051_claim "
                    "fep_fep052.FEP052.fep052_claim "
                    "fep_fep017.FEP017.fep017_claim"
                )
            },
        )


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda row: row.update(nearest_topics=[]), "nearest_topics"),
        (lambda row: row.update(nearest_topics=["fep-051"]), "must precede"),
        (lambda row: row.update(new_invariant=""), "new_invariant"),
        (lambda row: row.update(carrier_delta=""), "carrier_delta"),
        (lambda row: row.update(required_bridge="fep051_bridge"), "required_bridge"),
    ],
)
def test_novelty_rows_reject_empty_or_self_certifying_claims(
    tmp_path: Path,
    mutate: Callable[[dict[str, object]], None],
    message: str,
) -> None:
    path = tmp_path / "novelty.yaml"
    row = _row()
    mutate(row)
    _write_ledger(path, [row])

    with pytest.raises(NoveltyValidationError, match=message):
        load_formalism_novelty(
            path,
            tuple(f"fep-{index:03d}" for index in range(1, 52)),
            composed_sources={str(row["required_bridge"]): ""},
        )


def test_novelty_roster_is_exact_ordered_expansion_tail(tmp_path: Path) -> None:
    path = tmp_path / "novelty.yaml"
    _write_ledger(path, [_row("fep-052"), _row("fep-051")])

    with pytest.raises(NoveltyValidationError, match="expansion tail"):
        load_formalism_novelty(
            path,
            tuple(f"fep-{index:03d}" for index in range(1, 53)),
            composed_sources={},
        )


def test_catalogue_generation_rejects_novelty_ledger_drift(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    for name in ("catalogue_metadata.yaml", "theorem_maturity.yaml"):
        shutil.copy2(PROJECT_ROOT / "config" / name, config_dir / name)
    formal_dir = tmp_path / "src" / "fep_formal" / "formal"
    formal_dir.mkdir(parents=True)
    source_formal_dir = PROJECT_ROOT / "src" / "fep_formal" / "formal"
    for source in formal_resource_paths(
        FormalModuleRole.COMPOSITION,
        project_root=PROJECT_ROOT,
    ):
        destination = formal_dir / source.relative_to(source_formal_dir)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    _write_ledger(config_dir / "formalism_novelty.yaml", [_row()])

    with pytest.raises(NoveltyValidationError, match="expansion tail"):
        build_topics_data(tmp_path)
