"""Deterministic catalogue figures.

The functions intentionally accept a catalogue and an output directory only.
They do not depend on report state or network services, which makes catalogue
mode reproducible and safe to run in a clean checkout.
"""

from __future__ import annotations

import os
import tempfile
from collections.abc import Mapping
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure

from fep_lean.catalogue.topics import FEPTopicCatalogue


def _save(fig: Figure, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    # Render to a temporary file and atomically replace the canonical path so
    # a crash mid-encode cannot leave a torn PNG for downstream consumers.
    fd, raw_path = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    os.close(fd)
    try:
        fig.savefig(raw_path, dpi=150, format="png", metadata={"Software": "fep_lean"})
        os.replace(raw_path, path)
    finally:
        if os.path.exists(raw_path):
            os.unlink(raw_path)
    plt.close(fig)
    return path


def _write_bar_chart(
    values: Mapping[str, int],
    title: str,
    out: Path,
    *,
    show_pct: bool = False,
    subtitle: str | None = None,
) -> Path:
    labels = list(values)
    nums = [int(values[k]) for k in labels]
    fig, ax = plt.subplots(figsize=(7, 4.2))
    bars = ax.bar(labels, nums, color="#315f8c")
    ax.set_title(title)
    if subtitle:
        ax.set_xlabel(subtitle)
    ax.set_ylabel("Topics")
    ax.grid(axis="y", alpha=0.25)
    total = sum(nums) or 1
    for bar, n in zip(bars, nums, strict=False):
        label = f"{n} ({100 * n / total:.0f}%)" if show_pct else str(n)
        ax.text(bar.get_x() + bar.get_width() / 2, n, label, ha="center", va="bottom")
    return _save(fig, out)


def _write_maturity_heatmap(
    area_maturity: Mapping[str, Mapping[str, int]], out: Path
) -> Path:
    areas = list(area_maturity)
    statuses = ["real", "partial", "aspirational"]
    data = np.array(
        [[int(area_maturity[a].get(s, 0)) for s in statuses] for a in areas]
    )
    fig, ax = plt.subplots(figsize=(7, max(3.5, len(areas) * 0.55)))
    image = ax.imshow(
        data, cmap="Greens" if np.all(data[:, 1:] == 0) else "Blues", aspect="auto"
    )
    ax.set_xticks(range(len(statuses)), statuses)
    ax.set_yticks(range(len(areas)), areas)
    ax.set_title("Catalogue maturity by area")
    for i in range(len(areas)):
        for j in range(len(statuses)):
            ax.text(j, i, str(data[i, j]), ha="center", va="center")
    fig.colorbar(image, ax=ax, label="Topics")
    return _save(fig, out)


def _write_status_distribution(values: Mapping[str, int], out: Path) -> Path:
    labels = [k for k, v in values.items() if int(v) > 0]
    nums = [int(values[k]) for k in labels]
    fig, ax = plt.subplots(figsize=(5.2, 4.4))
    if nums:
        palette = ["#2f855a", "#d69e2e", "#c53030", "#3182ce"]
        # A fourth status used to silently cycle to the first color; a new
        # status must extend the palette, not alias an existing slice.
        assert len(nums) <= len(palette), (
            f"{len(labels)} statuses exceed the {len(palette)}-color palette"
        )
        ax.pie(
            nums,
            labels=labels,
            autopct="%1.0f%%",
            startangle=90,
            colors=palette[: len(nums)],
        )
    ax.set_title("Formalization status distribution")
    return _save(fig, out)


def _write_pipeline_dag(out: Path) -> Path:
    fig, ax = plt.subplots(figsize=(9, 2.4))
    names = ["Catalogue", "Validation", "Hermes + Lean", "Artifacts", "Report"]
    xs = range(len(names))
    ax.plot(list(xs), [0] * len(names), "o-", color="#315f8c", linewidth=2)
    for x, name in zip(xs, names, strict=False):
        ax.text(x, 0.08, name, ha="center", va="bottom")
    ax.set_xlim(-0.4, len(names) - 0.6)
    ax.set_ylim(-0.25, 0.35)
    ax.axis("off")
    ax.set_title("Strict execution pipeline")
    return _save(fig, out)


def _write_sequence_diagram(out: Path) -> Path:
    fig, ax = plt.subplots(figsize=(8, 4.5))
    actors = ["CLI", "Pipeline", "Hermes", "Lean", "SQLite"]
    for i, actor in enumerate(actors):
        ax.plot([i, i], [0, 4], linestyle="--", color="#9aa5b1", linewidth=0.8)
        ax.text(i, 4.1, actor, ha="center", va="bottom", weight="bold")
    arrows = [(0, 1, 3.3), (1, 2, 2.7), (2, 3, 2.1), (3, 4, 1.5), (1, 4, 0.9)]
    for start, end, y in arrows:
        ax.annotate(
            "",
            xy=(end, y),
            xytext=(start, y),
            arrowprops={"arrowstyle": "->", "color": "#315f8c"},
        )
    ax.set_xlim(-0.5, len(actors) - 0.5)
    ax.set_ylim(0.4, 4.6)
    ax.axis("off")
    ax.set_title("Execution sequence")
    return _save(fig, out)


def write_all_catalogue_figures(
    catalogue: FEPTopicCatalogue,
    project_root: Path,
    *,
    output_root: Path | None = None,
) -> list[Path]:
    """Write the nine canonical catalogue figures and return their paths."""
    out = (
        Path(output_root) if output_root is not None else Path(project_root) / "output"
    ) / "figures"
    summary = catalogue.summary()
    paths = [
        _write_bar_chart(
            summary["areas"],
            "Topics by area",
            out / "topics_by_area.png",
            show_pct=True,
        ),
        _write_bar_chart(
            summary["maturity"],
            "Topics by formalization status",
            out / "topics_by_status.png",
            show_pct=True,
        ),
        _write_maturity_heatmap(summary["area_maturity"], out / "area_maturity.png"),
        _write_status_distribution(
            summary["maturity"], out / "status_distribution.png"
        ),
        _write_pipeline_dag(out / "pipeline_dag.png"),
        _write_sequence_diagram(out / "execution_sequence.png"),
        _write_bar_chart(
            {t.id: t.lean_chars for t in catalogue.topics[:10]},
            "Lean sketch size (first ten)",
            out / "lean_size_sample.png",
        ),
        _write_bar_chart(
            {
                a: sum(t.lean_chars for t in catalogue.topics if t.area == a)
                for a in summary["areas"]
            },
            "Lean source size by area",
            out / "lean_size_by_area.png",
        ),
        _write_bar_chart(
            {
                a: sum(len(t.latex_equations) for t in catalogue.topics if t.area == a)
                for a in summary["areas"]
            },
            "Formal signatures by area",
            out / "signatures_by_area.png",
        ),
    ]
    return paths
