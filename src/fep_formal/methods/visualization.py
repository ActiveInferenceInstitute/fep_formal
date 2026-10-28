"""Deterministic offline visual analysis; neither proof nor empirical evidence.

The canonical visual model owns every displayed value and accessible table.
Family-domain coordinates and upstream affinities are editorial context. Authored
relations retain their original kinds and witnesses; no similarity creates an edge.
"""

from __future__ import annotations

import copy
import hashlib
import html
import io
import json
import math
import sys
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from decimal import (
    ROUND_HALF_EVEN,
    Context,
    Decimal,
    DivisionByZero,
    InvalidOperation,
    Overflow,
    localcontext,
)
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

TOLERANCE = 1e-12
_SERIES_LIMIT = 512
_SERIES_REMAINDER = Decimal("1e-75")
_DISPLAY_QUANTUM = Decimal("1e-24")
PRINT_WIDTH = 880
PRINT_HEIGHT = 760
PRINT_FONT_SIZE = 15
PRINT_RELATION_PANELS = {
    "authored-relations-formal.svg": "formal",
    "authored-relations-formal-pairing.svg": "formal_pairing",
    "authored-relations-conceptual.svg": "conceptual",
}
BOUNDARY = (
    "Offline authored mathematical context and deterministic exact-formula evaluations. "
    "No native compiler, upstream solution, learned embedding, Monte Carlo, empirical "
    "acceptance, or physical identification runs. Semantic dispositions and relation "
    "witnesses are copied without promotion. Family unions are not topic classifications."
)
UPSTREAM_COMMIT = "adc7f1241b42e322a6451854ab7e4b4c146bf78a"
AFFINITIES = (
    (
        "140",
        "measure-bayesian-inversion",
        "Gaussian inference",
        "Match priors, noise, memory and stopping rules.",
    ),
    (
        "221",
        "collective-and-multiagent-active-inference",
        "Diluted spin glasses",
        "Product laws do not imply a disorder thermodynamic limit.",
    ),
    (
        "222",
        "variational-duality-and-information-bounds",
        "Perceptron free energy",
        "Separate finiteness from limiting pressure and bounded-potential assumptions.",
    ),
    (
        "360",
        "core-information-geometry",
        "MTW transport geometry",
        "Fisher information does not imply MTW curvature.",
    ),
    (
        "374",
        "finite-to-native-blanket-transfer",
        "Brenier-map stability",
        "Match compact carriers, map norms and transport cost.",
    ),
)


def probability(value: float, *, interior: bool = False) -> float:
    if (
        not isinstance(value, (int, float))
        or isinstance(value, bool)
        or not math.isfinite(value)
    ):
        raise ValueError("probability must be finite")
    if not (0 < value < 1 if interior else 0 <= value <= 1):
        raise ValueError("probability outside its specified domain")
    return float(value)


def binary_kl(p: float, q: float) -> float | None:
    """Extended KL in nats; None represents positive mass outside reference support."""
    p, q = probability(p), probability(q)
    terms = []
    for mass, reference in ((p, q), (1 - p, 1 - q)):
        if mass == 0:
            continue
        if reference == 0:
            return None
        terms.append(mass * (math.log(mass) - math.log(reference)))
    return math.fsum(terms)


def fisher_energy(direction: Sequence[float], variance: float = 2.0) -> float:
    """Gaussian example, distinct from the source Bernoulli model: mean theta1+theta2, fixed variance: v^T I v=(v1+v2)^2/sigma²."""
    if len(direction) != 2 or not all(
        not isinstance(x, bool) and math.isfinite(x) for x in direction
    ):
        raise ValueError("direction needs two finite coordinates")
    if isinstance(variance, bool) or not math.isfinite(variance) or variance <= 0:
        raise ValueError("variance must be strictly positive and finite")
    try:
        total = math.fsum(direction)
        squared = total * total
        energy = squared / variance
        if (
            0 < squared < sys.float_info.min
            or not math.isfinite(energy)
            or (total != 0 and energy == 0)
        ):
            # Scale before squaring when an intermediate overflows/underflows;
            # (1e154 + 1e154)^2 / 1e308 is the representable energy 4.
            # Positive subnormal squares also lose precision before division.
            scaled = total / math.sqrt(variance)
            energy = scaled * scaled
    except OverflowError as exc:
        raise ValueError("Fisher energy exceeds the representable float range") from exc
    if not math.isfinite(energy) or (total != 0 and energy == 0):
        raise ValueError("Fisher energy is outside the representable float range")
    return energy


def _atan_series(value: Decimal) -> Decimal:
    """For |x|<=1/4, the alternating-series error is at most the next term."""
    if not value.is_finite() or abs(value) > Decimal("0.25"):
        raise ValueError("diagnostic atan series requires |x| <= 1/4")
    power = value
    result = Decimal(0)
    for index in range(_SERIES_LIMIT):
        term = power / (2 * index + 1)
        if abs(term) <= _SERIES_REMAINDER:
            return result
        result += term
        power *= -value * value
    raise ValueError("diagnostic atan remainder did not converge within its fixed cap")


def _decimal_atan(value: Decimal, pi: Decimal) -> Decimal:
    """Positive atan via reciprocal and half-angle reduction, then bounded series."""
    if not value.is_finite() or value < 0:
        raise ValueError("diagnostic atan requires a finite nonnegative argument")
    if value > 1:
        return pi / 2 - _decimal_atan(1 / value, pi)
    factor = 1
    while value > Decimal("0.25"):
        value /= 1 + (1 + value * value).sqrt()
        factor *= 2
    return factor * _atan_series(value)


def _decimal_sin(value: Decimal, pi: Decimal) -> Decimal:
    """Reduce to [-pi,pi]; after n>=1 omitted terms decrease in magnitude."""
    if not value.is_finite() or abs(value) > 4 * pi:
        raise ValueError("diagnostic sine requires a finite argument in [-4pi,4pi]")
    value %= 2 * pi
    if value > pi:
        value -= 2 * pi
    elif value < -pi:
        value += 2 * pi
    term = value
    result = Decimal(0)
    for index in range(_SERIES_LIMIT):
        # At index >=1 the next ratio is <=pi²/20<1. Consequently the
        # alternating Taylor tail is bounded by this first omitted term.
        if (index >= 1 or value == 0) and abs(term) <= _SERIES_REMAINDER:
            return result
        result += term
        term *= -value * value / ((2 * index + 2) * (2 * index + 3))
    raise ValueError("diagnostic sine remainder did not converge within its fixed cap")


def _display_number(value: Decimal) -> float:
    """Quantize derived display values; never round a generic probe input."""
    if not value.is_finite():
        raise ValueError("diagnostic display value must be finite")
    rounded = value.quantize(_DISPLAY_QUANTUM, rounding=ROUND_HALF_EVEN)
    return float(rounded) if rounded else 0.0


def _numerical_method() -> dict[str, Any]:
    """Disclose the finite-grid producer, separately from arithmetic acceptance."""
    return {
        "decimal_precision": 80,
        "elementary_functions": "Decimal ln/exp/sqrt; Machin pi = 16 atan(1/5) - 4 atan(1/239); reciprocal/half-angle atan and range-reduced sine alternating series",
        "series_cap": _SERIES_LIMIT,
        "series_first_omitted_term_limit": str(_SERIES_REMAINDER),
        "remainder_scope": "Alternating atan with |x|<=1/4 and sine on [-pi,pi] after decreasing terms: truncation error <= first omitted term. Atan reconstruction multiplies this bound by at most 4; Machin pi by at most 20. Decimal arithmetic is rounded at 80 digits; these are algorithmic bounds, not an interval-arithmetic certificate.",
        "grid_inputs": "Exact rational indices and coefficients: p=(i+1)/50, time=i/20, forecast=i/100; pi-dependent angle=2*pi*i/96 and log-space epsilon=exp((-6+i/8)*ln(10)) evaluated in Decimal",
        "display_decimal_places": 24,
        "rounding": "ROUND_HALF_EVEN",
        "serialization": "Finite derived grid values quantized to 24 decimal places then converted to IEEE float/JSON; signed zero canonicalized. Exact formulas and grid definitions remain authoritative.",
        "scope": "Finite explanatory publication grid only; generic binary_kl/fisher_energy retain their input and range contracts. Display quantization does not change the arithmetic tolerance or the exact-byte freshness comparator.",
    }


def numerical_panels() -> list[dict[str, Any]]:
    """Evaluate finite display grids without platform libm or ambient Decimal state."""
    arithmetic = Context(
        prec=80,
        rounding=ROUND_HALF_EVEN,
        Emin=-999999,
        Emax=999999,
        capitals=1,
        clamp=0,
        traps=[InvalidOperation, DivisionByZero, Overflow],
    )
    with localcontext(arithmetic):
        one = Decimal(1)
        pi = 16 * _atan_series(one / 5) - 4 * _atan_series(one / 239)
        support = []
        for index in range(41):
            epsilon = ((-6 + Decimal(index) / 8) * Decimal(10).ln()).exp()
            support.append(
                {
                    "epsilon": _display_number(epsilon),
                    "total_variation": _display_number(epsilon),
                    "kl_delta_to_p": _display_number(-(1 - epsilon).ln()),
                    "kl_p_to_delta": None,
                }
            )
        fisher = []
        for index in range(49):
            p = Decimal(index + 1) / 50
            fisher.append(
                {
                    "p": _display_number(p),
                    "fisher": _display_number(1 / (p * (1 - p))),
                    "coordinate": _display_number(
                        2 * _decimal_atan((p / (1 - p)).sqrt(), pi)
                    ),
                }
            )
        directions = []
        for index in range(97):
            angle = Decimal(index) * 2 * pi / 96
            directions.append(
                {
                    "angle": _display_number(angle),
                    # For unit direction (cos a,sin a), fixed variance 2:
                    # (cos a+sin a)^2/2 = (1+sin(2a))/2.
                    "energy": _display_number((1 + _decimal_sin(2 * angle, pi)) / 2),
                }
            )
        hidden = []
        for index in range(61):
            time = Decimal(index) / 20
            hidden.append(
                {
                    "time": _display_number(time),
                    "observed_mean_both": _display_number((-time).exp()),
                    "hidden_mean_first": 0.0,
                    "hidden_mean_second": _display_number(3 * (-2 * time).exp()),
                    "full_law_kl": _display_number(Decimal("4.5") * (-4 * time).exp()),
                    "observed_law_kl": 0.0,
                }
            )
        risk = []
        for index in range(101):
            forecast = Decimal(index) / 100
            kl = sum(
                (
                    mass * (mass.ln() - reference.ln())
                    for mass, reference in (
                        (forecast, Decimal("0.2")),
                        (1 - forecast, Decimal("0.8")),
                    )
                    if mass
                ),
                Decimal(0),
            )
            risk.append(
                {
                    "forecast": _display_number(forecast),
                    "expected_brier": _display_number(
                        Decimal("0.21") + (forecast - Decimal("0.7")) ** 2
                    ),
                    "preference_kl": _display_number(kl),
                }
            )
    return [
        {
            "id": "support-convergence",
            "title": "Support controls the direction of KL convergence",
            "domain": "pε=(1−ε,ε), δ=(1,0); 0<ε≤0.1. Endpoint ε=0 has both KL values zero.",
            "formula": "TV(pε,δ)=ε; KL(δ||pε)=−log(1−ε); KL(pε||δ)=+∞ for every ε>0.",
            "scope": "Native extended-real KL; null means +∞, never a plotted finite replacement. TV convergence does not imply KL convergence in both directions.",
            "rows": support,
            "boundary": {"epsilon": 0.0, "both_kl": 0.0},
        },
        {
            "id": "fisher-geometry",
            "title": "Tangent information and a redundant coordinate",
            "domain": "Bernoulli 0<p<1; duplicated Gaussian mean θ1+θ2 with fixed variance σ²=2.",
            "formula": "I_B(p)=1/[p(1−p)]=(d(2 asin √p)/dp)²; I_G=½[[1,1],[1,1]].",
            "scope": "Categorical metric is regular on the simplex tangent. Duplicating a mean coordinate adds a null direction, not an identifiable dimension. Endpoints are excluded from Bernoulli Fisher.",
            "rows": fisher,
            "directions": directions,
            "eigenvalues": [0.0, 1.0],
            "null_direction": [1.0, -1.0],
            "null_energy": fisher_energy((1.0, -1.0)),
            "positive_energy": fisher_energy((1.0, 1.0)),
        },
        {
            "id": "hidden-projection",
            "title": "Equal observed laws retain unequal hidden laws",
            "domain": "Independent elementary two-coordinate Gaussian OU obstruction (not the native H3 model), rates (1,2), stationary covariance I, initial means (1,0) and (1,3); t≥0.",
            "formula": "μ1(t)=(e^(−t),0); μ2(t)=(e^(−t),3e^(−2t)); KL(full1||full2)=9e^(−4t)/2; KL(observed1||observed2)=0.",
            "scope": "Projection retains only coordinate 1. These displayed values concern one-time Gaussian laws; no sampled paths, process-existence receipt, or hidden-state identification is supplied.",
            "rows": hidden,
        },
        {
            "id": "risk-preference",
            "title": "Preference matching and predictive risk select different forecasts",
            "domain": "Y~Bernoulli(0.7), forecast q∈[0,1], preference law Bernoulli(0.2); Brier loss (q−Y)².",
            "formula": "E[(q−Y)²]=0.21+(q−0.7)²; preference objective KL(Bernoulli(q)||Bernoulli(0.2)).",
            "scope": "Bayes forecast q=0.7 minimizes Brier risk; q=0.2 minimizes preference KL. This specified comparison is not a general EFE formula or an empirical calibration result.",
            "rows": risk,
            "bayes_forecast": 0.7,
            "preferred_forecast": 0.2,
        },
    ]


def build_visual_model(source: Mapping[str, Any]) -> dict[str, Any]:
    families = copy.deepcopy(source["family_positions"])
    topics = copy.deepcopy(source["topics"])
    by_id = {row["id"]: row for row in topics}
    if len(by_id) != len(topics):
        raise ValueError("duplicate topic identity")
    by_family = {row["family"]: row for row in families}
    if len(by_family) != len(families) or any(
        row["family"] not in by_family for row in topics
    ):
        raise ValueError("family ownership mismatch")
    domains = copy.deepcopy(source["domains"])
    for family in families:
        if any(domain not in domains for domain in family["domains"]):
            raise ValueError("unknown domain")
        family["topic_count"] = sum(row["family"] == family["family"] for row in topics)
        family["semantic_counts"] = dict(
            sorted(
                Counter(
                    row["semantic_review"]["disposition"]
                    for row in topics
                    if row["family"] == family["family"]
                ).items()
            )
        )
    authored = copy.deepcopy(source["authored_relations"])
    capabilities = authored["capabilities"]
    by_capability = {row["id"]: row for row in capabilities}
    if len(by_capability) != len(capabilities):
        raise ValueError("duplicate capability identity")
    if any(
        row["status"] not in {"open", "partial", "satisfied"} for row in capabilities
    ):
        raise ValueError("unknown capability status")
    edges = authored["edges"]
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for edge in edges:
        if edge["kind"] not in {"formal", "formal_pairing", "conceptual", "blocked_by"}:
            raise ValueError("unknown relation kind")
        targets = by_capability if edge["kind"] == "blocked_by" else by_id
        if edge["source"] not in by_id or edge["target"] not in targets:
            raise ValueError("dangling relation endpoint")
        if edge["kind"] in {"formal", "formal_pairing"} and not edge.get("witness"):
            raise ValueError("theorem-backed relation lacks witness")
        if edge["kind"] == "blocked_by":
            continue
        key = (
            by_id[edge["source"]]["family"],
            by_id[edge["target"]]["family"],
            edge["kind"],
        )
        grouped[key].append(edge)
    affinities = [
        {
            "source": "upstream-" + identifier,
            "target": family,
            "title": title,
            "kind": "editorial_upstream_affinity",
            "boundary": boundary,
            "url": f"https://github.com/openai/math/blob/{UPSTREAM_COMMIT}/lean/docs/{identifier}.md",
        }
        for identifier, family, title, boundary in AFFINITIES
    ]
    if any(row["target"] not in by_family for row in affinities):
        raise ValueError("upstream affinity has unknown family")
    return {
        "schema_version": 1,
        "package_version": source.get(
            "package_version", "unversioned source projection"
        ),
        "evidence_boundary": BOUNDARY,
        "source_sha256": copy.deepcopy(source["source_sha256"]),
        "source_origin": copy.deepcopy(
            source.get("source_origin", "validated checkout source-text projection")
        ),
        "renderer_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "counts": copy.deepcopy(source["counts"]),
        "domain_order": list(domains),
        "domains": domains,
        "families": families,
        "topics": topics,
        "continuous_scope": copy.deepcopy(source["continuous_scope"]),
        "relations": edges,
        "authored_relations": authored,
        "capabilities": capabilities,
        "family_relation_summary": [
            {"source": a, "target": b, "kind": kind, "count": len(values)}
            for (a, b, kind), values in sorted(grouped.items())
        ],
        "upstream_affinities": affinities,
        "theorem_analysis": copy.deepcopy(source.get("theorem_analysis")),
        "cross_corpus_embedding": copy.deepcopy(source.get("cross_corpus_embedding")),
        "numerical_method": _numerical_method(),
        "numerical_panels": numerical_panels(),
        "arithmetic_tolerance": TOLERANCE,
        "tolerance_scope": "Absolute floating-point diagnostic tolerance, not a scientific/native acceptance threshold.",
    }


def svg_bytes(fig: Any, title: str, description: str) -> bytes:
    import matplotlib
    from matplotlib.text import Text

    font = Path(matplotlib.get_data_path()) / "fonts" / "ttf" / "DejaVuSans.ttf"
    if (
        hashlib.sha256(font.read_bytes()).hexdigest()
        != "3fdf69cabf06049ea70a00b5919340e2ce1e6d02b0cc3c4b44fb6801bd1e0d22"
    ):
        raise ValueError("plot font differs from the reviewed bundled DejaVu Sans")
    for axes in fig.axes:
        axes.get_xticklabels()
        axes.get_yticklabels()
    for text in fig.findobj(Text):
        properties = text.get_fontproperties().copy()
        properties.set_file(str(font))
        text.set_fontproperties(properties)
    output = io.BytesIO()
    fig.savefig(
        output,
        format="svg",
        metadata={"Date": None, "Creator": "FEP Formal offline visual methods"},
    )
    node = ET.fromstring(output.getvalue())
    namespace = "http://www.w3.org/2000/svg"
    for child in list(node):
        if child.tag.endswith("metadata"):
            node.remove(child)
    node.set("role", "img")
    node.set("aria-labelledby", "panel-title panel-desc")
    title_node = ET.Element("{" + namespace + "}title", {"id": "panel-title"})
    title_node.text = title
    desc = ET.Element("{" + namespace + "}desc", {"id": "panel-desc"})
    desc.text = description
    node.insert(0, desc)
    node.insert(0, title_node)
    return bytes(ET.tostring(node, encoding="utf-8", xml_declaration=True)) + b"\n"


def render_panels(model: Mapping[str, Any]) -> dict[str, bytes]:
    """Standard plotting library, frozen style, and no timestamps or random layout."""
    import matplotlib
    from matplotlib.figure import Figure

    artifacts = {}
    with matplotlib.rc_context(
        {
            "svg.hashsalt": "fep-formal-math-v1",
            "svg.fonttype": "none",
            "font.family": "DejaVu Sans",
            "font.size": 17,
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    ):
        artifacts["family-domains.svg"] = family_domains_svg(model)
        artifacts["semantic-layers.svg"] = semantic_layers_svg(model)
        for panel in model["numerical_panels"]:
            fig = Figure(figsize=(10, 5), layout="constrained")
            rows = panel["rows"]
            if panel["id"] == "support-convergence":
                ax = fig.subplots()
                ax.loglog(
                    [r["epsilon"] for r in rows],
                    [r["total_variation"] for r in rows],
                    label="total variation ε",
                    linewidth=3,
                )
                ax.loglog(
                    [r["epsilon"] for r in rows],
                    [r["kl_delta_to_p"] for r in rows],
                    "--",
                    label="KL(δ || pε), nats",
                )
                ax.set_xlabel("ε (positive support outside δ)")
                ax.set_ylabel("Finite value")
                ax.text(
                    0.03,
                    0.85,
                    "KL(pε || δ) = +∞ for all plotted ε",
                    transform=ax.transAxes,
                )
            elif panel["id"] == "fisher-geometry":
                ax, other = fig.subplots(1, 2)
                ax.plot(
                    [r["p"] for r in rows],
                    [r["fisher"] for r in rows],
                    label="Bernoulli tangent coefficient",
                )
                ax.set_xlabel("p ∈ (0,1)")
                ax.set_ylabel("I(p)")
                other.plot(
                    [r["angle"] for r in panel["directions"]],
                    [r["energy"] for r in panel["directions"]],
                    color="#c28220",
                )
                other.set_xlabel("Unit-direction angle, radians")
                other.set_ylabel("Duplicated Gaussian Fisher energy")
                other.set_title("Eigenvalues 0 and 1 · variance 2", fontsize=17)
            elif panel["id"] == "hidden-projection":
                ax = fig.subplots()
                ax.plot(
                    [r["time"] for r in rows],
                    [r["full_law_kl"] for r in rows],
                    label="full Gaussian KL",
                )
                ax.plot(
                    [r["time"] for r in rows],
                    [r["observed_law_kl"] for r in rows],
                    "--",
                    label="projected Gaussian KL = 0",
                )
                ax.set_xlabel("t ≥ 0 (specified OU rates 1 and 2)")
                ax.set_ylabel("KL, nats")
            else:
                ax = fig.subplots()
                ax.plot(
                    [r["forecast"] for r in rows],
                    [r["expected_brier"] for r in rows],
                    label="expected Brier risk, truth 0.7",
                )
                ax.plot(
                    [r["forecast"] for r in rows],
                    [r["preference_kl"] for r in rows],
                    label="preference KL, preference 0.2",
                )
                ax.axvline(0.7, color="#245a80", linestyle=":")
                ax.axvline(0.2, color="#c28220", linestyle=":")
                ax.set_xlabel("Forecast q")
                ax.set_ylabel("Specified dimensionless objective")
            ax.legend(fontsize=12)
            fig.suptitle(panel["title"], fontsize=17)
            artifacts[panel["id"] + ".svg"] = svg_bytes(
                fig,
                panel["title"],
                panel["domain"] + " " + panel["formula"] + " " + panel["scope"],
            )
    artifacts["authored-relations.svg"] = relation_svg(model)
    artifacts.update(
        {
            name: relation_print_svg(model, kind)
            for name, kind in PRINT_RELATION_PANELS.items()
        }
    )
    if model.get("theorem_analysis"):
        artifacts["theorem-contracts.svg"] = theorem_contracts_svg(model)
    if model.get("cross_corpus_embedding"):
        artifacts["cross-corpus-embedding.svg"] = cross_corpus_svg(model)
        artifacts["cross-corpus-features.svg"] = cross_features_svg(model)
    return artifacts


def _print_root(title: str, description: str) -> ET.Element:
    """At the reviewed 451.9pt × 364.5pt caps, 15 units render at ≥7.19pt."""
    root = ET.Element(
        "svg",
        {
            "xmlns": "http://www.w3.org/2000/svg",
            "viewBox": f"0 0 {PRINT_WIDTH} {PRINT_HEIGHT}",
            "role": "img",
            "aria-labelledby": "print-title print-desc",
        },
    )
    ET.SubElement(root, "title", {"id": "print-title"}).text = title
    ET.SubElement(root, "desc", {"id": "print-desc"}).text = description
    ET.SubElement(
        root,
        "rect",
        {"width": str(PRINT_WIDTH), "height": str(PRINT_HEIGHT), "fill": "white"},
    )
    return root


def _print_text(
    root: ET.Element,
    x: float,
    y: float,
    text: str,
    *,
    size: int = PRINT_FONT_SIZE,
    anchor: str = "start",
    rotation: int = 0,
    color: str = "#152d3a",
) -> ET.Element:
    attributes = {
        "x": str(x),
        "y": str(y),
        "font-family": "DejaVu Sans",
        "font-size": str(size),
        "text-anchor": anchor,
        "fill": color,
    }
    if rotation:
        attributes["transform"] = f"rotate({rotation} {x} {y})"
    node = ET.SubElement(root, "text", attributes)
    node.text = text
    return node


def _family_key(
    root: ET.Element, families: Sequence[Mapping[str, Any]], y: int
) -> None:
    _print_text(
        root,
        20,
        y,
        "Family key · full topic contracts remain in the accessible HTML tables",
    )
    lines = (len(families) + 1) // 2
    for index, family in enumerate(families):
        column, line = divmod(index, lines)
        node = _print_text(
            root,
            20 + column * 430,
            y + 25 + line * 17,
            f"F{index + 1:02d} · {family['family']}",
        )
        node.set("data-family-key", family["family"])


def _print_bytes(root: ET.Element) -> bytes:
    return bytes(ET.tostring(root, encoding="utf-8", xml_declaration=True)) + b"\n"


def cross_corpus_svg(model: Mapping[str, Any]) -> bytes:
    """Two MDS axes preserve signed coordinates; no layout forces or jitter."""
    data = model["cross_corpus_embedding"]
    projection = data["projection"]
    root = _print_root(
        "Common mathematical coordinates: classical MDS",
        data["assignment_boundary"] + " " + projection["interpretation"],
    )
    _print_text(root, 20, 28, "Common mathematical coordinates: classical MDS", size=20)
    _print_text(
        root, 20, 53, "FEP family unions and individually named OpenAI result units"
    )
    x0, y0, width, height = 95, 90, 710, 470
    points = projection["coordinates"]
    extent = max((abs(value) for point in points for value in point), default=0.0)
    # A zero-rank carrier retains zero coordinates; unit extent is a plotting
    # viewport only and is explicitly labeled. No synthetic point is introduced.
    viewport = extent * 1.15 if extent else 1.0
    horizontal_viewport = viewport * width / height

    def location(point: Sequence[float]) -> tuple[float, float]:
        return x0 + width * (point[0] / horizontal_viewport + 1) / 2, y0 + height * (
            1 - point[1] / viewport
        ) / 2

    ET.SubElement(
        root,
        "rect",
        {
            "x": str(x0),
            "y": str(y0),
            "width": str(width),
            "height": str(height),
            "fill": "#f6f8fa",
            "stroke": "#9fb2be",
        },
    )
    for endpoint in (-1, 0, 1):
        x, y = location((endpoint * horizontal_viewport, endpoint * viewport))
        _print_text(
            root,
            x,
            y0 + height + 22,
            f"{endpoint * horizontal_viewport:.2f}",
            anchor="middle",
        )
        _print_text(root, x0 - 10, y + 5, f"{endpoint * viewport:.2f}", anchor="end")
    center_x, center_y = location((0, 0))
    _print_text(root, 25, y0 + height / 2, "MDS axis 2", anchor="middle", rotation=-90)
    ET.SubElement(
        root,
        "path",
        {
            "d": f"M{x0},{center_y}h{width} M{center_x},{y0}v{height}",
            "stroke": "#b7c5cc",
            "fill": "none",
        },
    )
    groups: dict[tuple[int, ...], list[int]] = {}
    for index, vector in enumerate(data["vectors"]):
        groups.setdefault(tuple(vector), []).append(index)
    point_locations = [location(points[indices[0]]) for indices in groups.values()]
    labels: list[tuple[float, float]] = []
    for group_index, indices in enumerate(groups.values(), 1):
        first = indices[0]
        x, y = location(points[first])
        kinds = {data["rows"][index]["kind"] for index in indices}
        color = (
            "#245a80"
            if kinds == {"fep_family_context"}
            else "#b67818"
            if kinds == {"upstream_result"}
            else "#77539c"
        )
        node = ET.SubElement(
            root,
            "circle",
            {
                "cx": str(x),
                "cy": str(y),
                "r": "6",
                "fill": color,
                "data-row-ids": "|".join(data["row_order"][index] for index in indices),
            },
        )
        ET.SubElement(node, "title").text = "; ".join(
            data["row_order"][index] for index in indices
        )
        # Label placement is a deterministic display operation, independent of
        # data coordinates. Labels never displace points or imply a new edge.
        label_x, label_y = x + 9, y - 9
        for dx, dy in (
            (dx, dy) for dy in (-9, 20, -27, 38, -45, 56) for dx in (9, -38, 38, -67)
        ):
            proposed = (
                min(max(x + dx, x0 + 5), x0 + width - 45),
                min(max(y + dy, y0 + 20), y0 + height - 8),
            )
            if all(
                abs(proposed[0] - old[0]) > 38 or abs(proposed[1] - old[1]) > 16
                for old in labels
            ) and not any(
                proposed[0] - 8 <= point_x <= proposed[0] + 39
                and proposed[1] - 20 <= point_y <= proposed[1] + 10
                for point_x, point_y in point_locations
            ):
                label_x, label_y = proposed
                break
        else:
            raise ValueError(
                "MDS label placement cannot preserve readable keys without moving data"
            )
        labels.append((label_x, label_y))
        if abs(label_x - x) > 20 or abs(label_y - y) > 24:
            endpoint_x = label_x if label_x > x else label_x + 30
            ET.SubElement(
                root,
                "line",
                {
                    "x1": str(x),
                    "y1": str(y),
                    "x2": str(endpoint_x),
                    "y2": str(label_y - 6),
                    "stroke": "#81939d",
                    "stroke-width": "0.7",
                    "stroke-dasharray": "3,3",
                    "data-label-guide": f"G{group_index:02d}",
                },
            )
        _print_text(root, label_x, label_y, f"G{group_index:02d}")
    _print_text(
        root,
        x0 + width / 2,
        608,
        "MDS axis 1 · sign and orientation are display conventions",
        anchor="middle",
    )
    _print_text(
        root,
        20,
        640,
        f"Positive rank {projection['positive_rank']} · 2D normalized stress {projection['normalized_stress']:.4f}",
    )
    _print_text(
        root,
        20,
        664,
        f"Displayed positive inertia {projection['explained_positive_inertia']:.1%} · repeated eigenspaces {len(projection['eigenambiguity'])}",
    )
    _print_text(
        root,
        20,
        690,
        "Blue: FEP context · amber: OpenAI result · purple: identical mixed features",
    )
    _print_text(
        root,
        20,
        714,
        "G keys group identical vectors; full keys, features, spectra and source hashes: HTML",
    )
    _print_text(
        root,
        20,
        738,
        "Dashed key guides are annotations; no theorem edge or point jitter is introduced.",
    )
    return _print_bytes(root)


def cross_features_svg(model: Mapping[str, Any]) -> bytes:
    """Show every assigned coordinate and source row, with accessible exact keys."""
    data = model["cross_corpus_embedding"]
    root = _print_root(
        "Explicit cross-corpus feature incidence",
        data["assignment_boundary"] + " " + data["coordinate_weight"],
    )
    _print_text(root, 20, 27, "Explicit cross-corpus feature incidence", size=20)
    _print_text(
        root,
        20,
        51,
        "Assigned = filled; absent = unassigned. Every coordinate has unit weight.",
    )
    count = len(data["coordinates"])
    row_count = len(data["rows"])
    if count > 40 or row_count > 40:
        raise ValueError(
            "publication feature matrix exceeds reviewed 40-row/coordinate capacity"
        )
    x0, y0, cell_x, cell_y = 140, 115, 17, 14
    for index, coordinate in enumerate(data["coordinates"]):
        node = _print_text(
            root,
            x0 + index * cell_x + 8,
            y0 - 13,
            f"C{index + 1:02d}",
            anchor="start",
            rotation=-90,
        )
        node.set("data-coordinate", coordinate["id"])
        ET.SubElement(node, "title").text = (
            coordinate["id"] + ": " + coordinate["definition"]
        )
    fep_index = upstream_index = 0
    for row_index, (row, vector) in enumerate(
        zip(data["rows"], data["vectors"], strict=True)
    ):
        if row["kind"] == "fep_family_context":
            fep_index += 1
            label = f"F{fep_index:02d}"
        else:
            upstream_index += 1
            label = f"U{upstream_index:02d}"
        _print_text(
            root, x0 - 12, y0 + row_index * cell_y + 12, label, anchor="end"
        ).set("data-row-id", row["id"])
        for index, value in enumerate(vector):
            ET.SubElement(
                root,
                "rect",
                {
                    "x": str(x0 + index * cell_x),
                    "y": str(y0 + row_index * cell_y),
                    "width": "15",
                    "height": "12",
                    "fill": "#245a80"
                    if value and row["kind"] == "fep_family_context"
                    else "#b67818"
                    if value
                    else "#e6edf1",
                    "data-row": row["id"],
                    "data-coordinate": data["coordinates"][index]["id"],
                    "data-value": str(value),
                },
            )
    _print_text(
        root,
        20,
        700,
        "F: family context unions · U: individually reviewed source result units",
    )
    _print_text(
        root,
        20,
        722,
        "C: common domain / carrier / premise-or-regime coordinates; complete keys in HTML",
    )
    _print_text(
        root,
        20,
        746,
        "Binary mismatches define squared Euclidean distance; no hidden learned weights.",
    )
    return _print_bytes(root)


def theorem_contracts_svg(model: Mapping[str, Any]) -> bytes:
    """Contrast exact row syntax with human review and inherited family context."""
    analysis = model["theorem_analysis"]
    root = _print_root(
        "Lean statement passports and semantic ownership", analysis["analysis_boundary"]
    )
    _print_text(
        root, 20, 27, "Lean statement passports and semantic ownership", size=20
    )
    _print_text(
        root,
        20,
        52,
        "Exact signatures + maintained row review + separately inherited family context",
    )
    by_id = {row["id"]: row for row in model["topics"]}
    for index, topic_id in enumerate(
        ("fep-005", "fep-038", "fep-043", "fep-104", "fep-137", "fep-168")
    ):
        topic = by_id[topic_id]
        record = analysis["declarations"][topic["primary_theorem_qualified"]]
        y = 87 + index * 96
        _print_text(
            root,
            20,
            y,
            topic_id + " · " + record["qualified_name"].rsplit(".", 1)[-1],
            size=17,
        )
        _print_text(
            root,
            20,
            y + 23,
            f"Typed binder groups: {len(record['binders'])} · context groups: {len(record['context_binders'])} · review: {topic['semantic_review']['disposition']}",
        )
        roles = Counter(
            row["role"]
            for row in record["declaration_mentions"]
            if "qualified_name" in row
        )
        _print_text(
            root,
            20,
            y + 46,
            f"Resolved source mentions · statement: {roles['statement_reference']} · proof: {roles['proof_reference']}",
        )
        _print_text(
            root,
            20,
            y + 68,
            f"Reviewed supporting refs: {len(topic['reviewed_theorems_qualified']['supporting_theorems'])} · boundary refs: {len(topic['reviewed_theorems_qualified']['boundary_theorems'])}",
        )
    _print_text(
        root,
        20,
        690,
        "Binder counts are syntax, not elaborated premise counts or scientific guarantees.",
    )
    _print_text(
        root,
        20,
        714,
        "Exact statements, binder types, conclusions and maintained assumptions: HTML + API",
    )
    _print_text(
        root,
        20,
        738,
        "Lexical mentions are not kernel dependency certificates. No certified translation runs.",
    )
    return _print_bytes(root)


def family_domains_svg(model: Mapping[str, Any]) -> bytes:
    """Editorial incidence with a legible family key; no per-topic promotion."""
    labels = {
        "causal-inference": "Causal",
        "differential-geometry": "Diff. geom.",
        "dynamical-systems": "Dynamics",
        "graph-theory": "Graphs",
        "information-theory": "Information",
        "measure-theory": "Measure",
        "optimization": "Optim.",
        "thermodynamics": "Thermo.",
    }
    root = _print_root(
        "Authored family-domain incidence",
        "Binary editorial family union, not per-topic proof classification. Compact domain labels name the exact domain in their titles. Full family names and accessible topic contracts remain available.",
    )
    _print_text(root, 20, 26, "Authored family-domain incidence", size=20)
    _print_text(
        root, 20, 51, "Editorial family union; not a per-topic proof classification."
    )
    x0, y0, column_width, row_height = 195, 139, 42, 17
    for j, domain in enumerate(model["domain_order"]):
        label = _print_text(
            root,
            x0 + j * column_width + 21,
            y0 - 9,
            labels.get(domain, domain.capitalize()),
            rotation=-55,
        )
        ET.SubElement(label, "title").text = domain
    for i, family in enumerate(model["families"]):
        _print_text(
            root, x0 - 12, y0 + i * row_height + 13, f"F{i + 1:02d}", anchor="end"
        )
        for j, domain in enumerate(model["domain_order"]):
            present = domain in family["domains"]
            cell = ET.SubElement(
                root,
                "rect",
                {
                    "x": str(x0 + j * column_width),
                    "y": str(y0 + i * row_height),
                    "width": str(column_width),
                    "height": str(row_height),
                    "fill": "#154575" if present else "#edf2f5",
                    "stroke": "white",
                    "data-family": family["family"],
                    "data-domain": domain,
                    "data-present": str(int(present)),
                },
            )
            ET.SubElement(
                cell, "title"
            ).text = f"{family['family']} / {domain}: {int(present)}"
    _family_key(root, model["families"], 537)
    return _print_bytes(root)


def semantic_layers_svg(model: Mapping[str, Any]) -> bytes:
    """Copied semantic counts with the same family codes and full readable key."""
    root = _print_root(
        "Maintained semantic dispositions",
        "Exact counts copied from reviewed semantic records, separated by family. These labels do not validate a current native receipt or empirical acceptance.",
    )
    _print_text(root, 20, 26, "Maintained semantic dispositions", size=20)
    _print_text(root, 20, 51, "Copied semantic review; no native receipt validation.")
    families = model["families"]
    maximum = 2 * math.ceil(max(row["topic_count"] for row in families) / 2)
    x0, y0, width, row_height = 195, 70, 600, 16
    colors = {
        "formalized": "#245a80",
        "conditional_proxy": "#b57917",
        "structural_proxy": "#8260a6",
    }
    for i, family in enumerate(families):
        _print_text(
            root, x0 - 12, y0 + i * row_height + 12, f"F{i + 1:02d}", anchor="end"
        )
        left = 0
        for disposition, color in colors.items():
            count = family["semantic_counts"].get(disposition, 0)
            if count:
                ET.SubElement(
                    root,
                    "rect",
                    {
                        "x": str(x0 + width * left / maximum),
                        "y": str(y0 + i * row_height + 1),
                        "width": str(width * count / maximum),
                        "height": "14",
                        "fill": color,
                        "data-family": family["family"],
                        "data-disposition": disposition,
                        "data-count": str(count),
                    },
                )
                _print_text(
                    root,
                    x0 + width * (left + count / 2) / maximum,
                    y0 + i * row_height + 12,
                    str(count),
                    anchor="middle",
                    color="white",
                )
            left += count
    bottom = y0 + len(families) * row_height
    ET.SubElement(
        root,
        "path",
        {"d": f"M{x0} {y0}V{bottom}H{x0 + width}", "fill": "none", "stroke": "#152d3a"},
    )
    for count in range(0, maximum + 1, 2):
        _print_text(
            root, x0 + width * count / maximum, bottom + 25, str(count), anchor="middle"
        )
    _print_text(
        root, x0 + width / 2, bottom + 52, "Canonical topic records", anchor="middle"
    )
    for i, (disposition, color) in enumerate(colors.items()):
        ET.SubElement(
            root,
            "rect",
            {
                "x": str(80 + i * 260),
                "y": "498",
                "width": "18",
                "height": "14",
                "fill": color,
            },
        )
        _print_text(root, 104 + i * 260, 510, disposition)
    _family_key(root, families, 540)
    return _print_bytes(root)


def relation_print_svg(model: Mapping[str, Any], kind: str) -> bytes:
    """One relation kind per publication panel; every cell retains its exact count."""
    titles = {
        "formal": ("Formal derivations", "#246489"),
        "formal_pairing": ("Formal theorem pairings", "#a15a18"),
        "conceptual": ("Conceptual associations", "#7866a1"),
    }
    if kind not in titles:
        raise ValueError(
            "publication relation kind must be formal, formal_pairing or conceptual"
        )
    title, color = titles[kind]
    root = _print_root(
        title,
        f"Directed family adjacency matrix for {kind} topic edges. Rows are sources; columns are targets. Counts preserve original authored edges, not family-level theorems. Exact endpoints and qualified witnesses remain in the accessible HTML table. Editorial upstream affinities are excluded.",
    )
    root.set("data-relation-kind", kind)
    _print_text(root, 20, 26, title, size=20, color=color)
    _print_text(
        root,
        20,
        51,
        "Source rows → target columns · numbers count original topic edges",
    )
    families = model["families"]
    lookup = {
        (row["source"], row["target"]): row["count"]
        for row in model["family_relation_summary"]
        if row["kind"] == kind
    }
    maximum = max(lookup.values(), default=1)
    x0, y0, cell = 242, 97, 18
    for i, family in enumerate(families):
        code = f"F{i + 1:02d}"
        _print_text(root, x0 - 12, y0 + i * cell + 13, code, anchor="end")
        _print_text(root, x0 + i * cell + 9, y0 - 7, code, rotation=-70)
        for j, target in enumerate(families):
            count = lookup.get((family["family"], target["family"]), 0)
            opacity = (
                0.15 + 0.85 * math.log1p(count) / math.log1p(maximum) if count else 0
            )
            rectangle = ET.SubElement(
                root,
                "rect",
                {
                    "x": str(x0 + j * cell),
                    "y": str(y0 + i * cell),
                    "width": str(cell),
                    "height": str(cell),
                    "fill": color if count else "#edf2f5",
                    "stroke": "white",
                    "fill-opacity": f"{opacity:.4f}" if count else "1",
                    "data-source": family["family"],
                    "data-target": target["family"],
                    "data-count": str(count),
                    "data-kind": kind,
                },
            )
            ET.SubElement(
                rectangle, "title"
            ).text = f"{family['family']} → {target['family']}: {count} {kind} topic relations"
            if count:
                _print_text(
                    root,
                    x0 + j * cell + 9,
                    y0 + i * cell + 13,
                    str(count),
                    anchor="middle",
                    color="white" if opacity > 0.55 else "#152d3a",
                )
    _family_key(root, families, 516)
    _print_text(
        root,
        20,
        742,
        "Family aggregation adds no theorem; editorial upstream affinities are separate.",
    )
    return _print_bytes(root)


def relation_svg(model: Mapping[str, Any]) -> bytes:
    """Readable adjacency-matrix graph encoding; no geometric or proof inference."""
    families = model["families"]
    indices = {row["family"]: i for i, row in enumerate(families)}
    size = len(families)
    cell = 16
    colors = {"formal": "#246489", "formal_pairing": "#a15a18", "conceptual": "#7866a1"}
    chunks = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1240 1000" role="img" aria-labelledby="graph-title graph-desc"><title id="graph-title">Typed authored relation adjacency matrices</title><desc id="graph-desc">Three directed adjacency matrices aggregate exact topic edges by family. Rows are sources, columns are targets. Numbers count original edges, not family theorems. Formal, theorem pairing and conceptual kinds remain separate. Editorial upstream affinities are listed in a fourth separate band. Exact topic endpoints and witnesses are available in the HTML table.</desc><rect width="1240" height="1000" fill="white"/><text x="35" y="35" font-family="sans-serif" font-size="21">Authored relation graph · source rows → target columns</text><text x="35" y="61" font-family="sans-serif" font-size="13">Cell counts aggregate canonical topic edges, not family-level proofs or inferred implications.</text>'
    ]
    for panel_index, (kind, color) in enumerate(colors.items()):
        x0, y0 = 50 + panel_index * 400, 125
        chunks.append(
            f'<text x="{x0}" y="97" font-family="sans-serif" font-size="18" fill="{color}">{kind}</text>'
        )
        lookup = {
            (edge["source"], edge["target"]): edge["count"]
            for edge in model["family_relation_summary"]
            if edge["kind"] == kind
        }
        maximum = max(lookup.values(), default=1)
        for row in families:
            i = indices[row["family"]]
            code = f"F{i + 1:02d}"
            chunks.append(
                f'<text x="{x0 - 5}" y="{y0 + i * cell + 12}" text-anchor="end" font-family="sans-serif" font-size="9">{code}</text><text x="{x0 + i * cell + 8}" y="{y0 - 6}" text-anchor="middle" font-family="sans-serif" font-size="9" transform="rotate(-70 {x0 + i * cell + 8} {y0 - 6})">{code}</text>'
            )
            for target in families:
                j = indices[target["family"]]
                count = lookup.get((row["family"], target["family"]), 0)
                opacity = (
                    0.15 + 0.85 * math.log1p(count) / math.log1p(maximum)
                    if count
                    else 0
                )
                title = html.escape(
                    f"{row['family']} → {target['family']}: {count} {kind} topic relations"
                )
                chunks.append(
                    f'<rect x="{x0 + j * cell}" y="{y0 + i * cell}" width="{cell}" height="{cell}" fill="#edf2f5" stroke="white"><title>{title}</title></rect>'
                )
                if count:
                    chunks.append(
                        f'<rect x="{x0 + j * cell}" y="{y0 + i * cell}" width="{cell}" height="{cell}" fill="{color}" fill-opacity="{opacity:.4f}"><title>{title}</title></rect><text x="{x0 + j * cell + 8}" y="{y0 + i * cell + 12}" text-anchor="middle" font-family="sans-serif" font-size="9" fill="{"white" if opacity > 0.55 else "#152d3a"}">{count}</text>'
                    )
    legend_y = 125 + size * cell + 40
    chunks.append(
        f'<text x="35" y="{legend_y}" font-family="sans-serif" font-size="17">Family key (the exact topic graph remains in the accessible HTML table)</text>'
    )
    for i, row in enumerate(families):
        col, line = i // 11, i % 11
        chunks.append(
            f'<text x="{35 + col * 605}" y="{legend_y + 27 + line * 22}" font-family="sans-serif" font-size="12">F{i + 1:02d} · {html.escape(row["family"])}</text>'
        )
    band_y = legend_y + 310
    chunks.append(
        f'<text x="35" y="{band_y}" font-family="sans-serif" font-size="17">Editorial upstream affinities · no formal edge or native acceptance</text>'
    )
    for i, row in enumerate(model["upstream_affinities"]):
        code = f"F{indices[row['target']] + 1:02d}"
        chunks.append(
            f'<text x="35" y="{band_y + 28 + i * 27}" font-family="sans-serif" font-size="12">{html.escape(row["source"])} ···→ {code}: {html.escape(row["boundary"])}</text>'
        )
    chunks.append("</svg>")
    return "".join(chunks).encode() + b"\n"


def escape(value: Any) -> str:
    return html.escape(str(value), quote=True)


def table(rows: Sequence[Mapping[str, Any]], caption: str) -> str:
    if not rows:
        return "<p>No rows.</p>"
    keys = sorted(rows[0])
    chunks = [
        '<div class="table-scroll"><table><caption>'
        + escape(caption)
        + "</caption><thead><tr>"
    ]
    chunks.extend(
        '<th scope="col">' + escape(key.replace("_", " ")) + "</th>" for key in keys
    )
    chunks.append("</tr></thead><tbody>")
    for row in rows:
        chunks.append("<tr>")
        chunks.extend(
            "<td>" + ("+∞" if row[key] is None else escape(row[key])) + "</td>"
            for key in keys
        )
        chunks.append("</tr>")
    chunks.append("</tbody></table></div>")
    return "".join(chunks)


def render_html(model: Mapping[str, Any]) -> bytes:
    topic_count = len(model["topics"])
    origin = json.dumps(model["source_origin"], ensure_ascii=False, sort_keys=True)
    chunks = [
        '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src \'none\'; img-src \'self\' data:; style-src \'unsafe-inline\'; script-src \'unsafe-inline\'; connect-src \'none\'; base-uri \'none\'"><title>FEP Formal · Mathematical map</title><style>body{margin:0;background:#edf2f5;color:#153345;font:16px/1.55 system-ui,sans-serif}main{max-width:1240px;margin:auto;padding:24px}h1{font-size:clamp(2rem,5vw,3.3rem);line-height:1.1}h2{margin-top:2.8rem}nav,.controls{display:flex;gap:12px;flex-wrap:wrap}a{color:#135b7b}a:focus-visible,summary:focus-visible,input:focus-visible,select:focus-visible{outline:3px solid #d69521;outline-offset:3px}section,.card{background:white;border:1px solid #cad8de;border-radius:12px;padding:20px;margin:20px 0}label{display:flex;flex-direction:column;gap:5px}input,select{font:inherit;padding:9px;max-width:100%;border:1px solid #829ca9;border-radius:5px}details{border-top:1px solid #cfdae0;padding:12px 0}summary{cursor:pointer;font-weight:650}code{overflow-wrap:anywhere}p,dd,td{overflow-wrap:anywhere}dt{font-weight:650;margin-top:10px}dd{margin-left:0}img{width:100%;height:auto}.table-scroll{overflow:auto;max-width:100%}table{border-collapse:collapse;width:100%;font-size:.86rem}th,td{padding:8px;border-bottom:1px solid #dae3e8;text-align:left;vertical-align:top}caption{text-align:left;font-weight:650;padding:12px 0}th{background:#f0f5f7}[hidden]{display:none!important}.boundary{border-left:5px solid #c28220;padding-left:15px}.small{font-size:.9rem;color:#395664}@media(max-width:600px){main{padding:12px}section{padding:12px}.controls label{width:100%}}@media print{.controls{display:none}details{break-inside:avoid}details>*{display:block!important}body{background:white}}</style></head><body><main><header><p>FEP Formal / offline research methods</p><h1>Where the mathematics lives</h1><p>A map of carriers, conditional statements, and their boundaries.</p><p class="boundary">'
        + escape(model["evidence_boundary"])
        + '</p><p class="small">Source origin: '
        + escape(origin)
        + '</p><p class="small">Package version: '
        + escape(model["package_version"])
        + '</p><nav aria-label="Sections"><a href="#families">Family coordinates</a><a href="#contracts">Topic contracts</a><a href="#relations">Authored relations</a><a href="#capabilities">Capabilities</a><a href="#boundaries">Numerical boundaries</a></nav></header>'
    ]
    chunks.append(
        '<section id="families"><h2>Family context, carriers, and evidence layers</h2><p>Domain incidence is a family union. Semantic labels are maintained review records; they do not validate a current native receipt.</p><img src="panels/family-domains.svg" alt="Editorial family-domain incidence matrix; exact values in the table below"><img src="panels/semantic-layers.svg" alt="Stacked family topic counts by maintained semantic disposition"><details><summary>Accessible family coordinates and carrier table</summary>'
    )
    chunks.append(
        table(
            [
                {
                    "family": row["family"],
                    "topics": row["topic_count"],
                    "domains": ", ".join(row["domains"]),
                    "carriers": "; ".join(row["carriers"]),
                    "modes": "; ".join(row["scale"]),
                    "dispositions": json.dumps(row["semantic_counts"], sort_keys=True),
                    "topology": row["topology"],
                    "embedding": row["embedding"],
                    "statistics": row["statistics"],
                    "boundary": row["limits"],
                }
                for row in model["families"]
            ],
            "All authored family axes; inherited family context only",
        )
    )
    chunks.append(
        "</details><details><summary>Selected continuous/native source scopes</summary>"
        + table(
            model["continuous_scope"],
            "Maintained module scopes, not live native acceptance",
        )
        + "</details></section>"
    )
    if model.get("cross_corpus_embedding"):
        chunks.append(_cross_corpus_html(model["cross_corpus_embedding"]))
    if model.get("theorem_analysis"):
        chunks.append(
            '<section id="statement-analysis"><h2>Source-grounded theorem analysis</h2><p class="boundary">'
            + escape(model["theorem_analysis"]["analysis_boundary"])
            + '</p><img src="panels/theorem-contracts.svg" alt="Six exact row passports separate signature syntax, maintained row review, and inherited family context"><p>Each contract below exposes its exact primary signature. Supporting and boundary declarations remain individually qualified; their exact analyses are retained in visual-model.json and the theorem API.</p></section>'
        )
    chunks.append(
        f'<section id="contracts"><h2>Explore all {topic_count} topic contracts</h2><p>Search covers the full invariant, assumptions, boundary, and qualified witness. No fields are summarized away.</p><div class="controls"><label>Search<input id="query" aria-label="Search topic contracts" type="search" placeholder="ID, theorem, invariant, assumption…"></label>'
    )
    for key, label, options in [
        ("family", "Family", [r["family"] for r in model["families"]]),
        ("domain", "Family domain", model["domain_order"]),
        (
            "disposition",
            "Disposition",
            sorted({r["semantic_review"]["disposition"] for r in model["topics"]}),
        ),
    ]:
        chunks.append(
            f'<label>{label}<select id="{key}" aria-label="{label}"><option value="">All</option>'
            + "".join(
                f'<option value="{escape(v)}">{escape(v)}</option>' for v in options
            )
            + "</select></label>"
        )
    chunks.append(
        f'</div><p id="topic-status" role="status" aria-live="polite">{topic_count} topic contracts shown</p><div id="topic-list">'
    )
    for topic in model["topics"]:
        review = topic["semantic_review"]
        chunks.append(
            f'<details class="topic" id="{escape(topic["id"])}" data-family="{escape(topic["family"])}" data-disposition="{escape(review["disposition"])}" data-domains="{escape("|".join(topic["mathematical_context"]["domains"]))}"><summary>{escape(topic["id"])} · {escape(topic["title"])} · {escape(review["disposition"])}</summary><dl>'
        )
        values = {
            "Family context (editorial)": topic["family"],
            "Primary qualified witness": topic["primary_theorem_qualified"],
            "Invariant": review["invariant"],
            "Assumption review": review["assumption_review"],
            "Non-vacuity": review["non_vacuity"],
            "Acceptance probe (requirement; not executed here)": review[
                "acceptance_probe"
            ],
            "Supporting qualified declarations": "; ".join(
                topic["reviewed_theorems_qualified"]["supporting_theorems"]
            )
            or "Absent",
            "Boundary qualified declarations": "; ".join(
                topic["reviewed_theorems_qualified"]["boundary_theorems"]
            )
            or "Absent",
            "Canonical body SHA-256": topic["canonical_body_sha256"],
        }
        for label, value in values.items():
            chunks.append(
                "<dt>" + escape(label) + "</dt><dd>" + escape(value) + "</dd>"
            )
        if model.get("theorem_analysis"):
            record = model["theorem_analysis"]["declarations"][
                topic["primary_theorem_qualified"]
            ]
            chunks.append(
                "<dt>Exact Lean statement (proof omitted)</dt><dd><pre><code>"
                + escape(record["statement"])
                + "</code></pre></dd><dt>Exact conclusion</dt><dd><pre><code>"
                + escape(record["conclusion"])
                + "</code></pre></dd><dt>Source statement SHA-256</dt><dd><code>"
                + escape(record["statement_sha256"])
                + "</code></dd><dt>Active namespace variable context (not an elaborated signature)</dt><dd>"
                + table(
                    [
                        {"source": value}
                        for value in record["namespace_variable_context"]
                    ],
                    "Retained active variable commands",
                )
                + "</dd><dt>Explicit, implicit and instance binder syntax</dt><dd>"
                + table(
                    record["binders"],
                    "Exact primary binder groups; types are not elaborated here",
                )
                + "</dd><dt>Source declaration mentions</dt><dd>"
                + table(
                    [
                        {
                            "identifier": row["identifier"],
                            "role": row["role"],
                            "resolution": row["resolution"],
                            "qualified_name": row.get("qualified_name", "unresolved"),
                            "candidates": row.get("candidates", []),
                        }
                        for row in record["declaration_mentions"]
                    ],
                    record["dependency_boundary"],
                )
                + "</dd>"
            )
        chunks.append(
            f"<dt>Owned canonical source identity</dt><dd>{escape(topic['body_source'])}</dd></dl></details>"
        )
    chunks.append(
        "</div><noscript><p>JavaScript is disabled. All contracts and tables remain available; use browser text search.</p></noscript></section>"
    )
    chunks.append(
        '<section id="relations"><h2>Authored relations retain their meanings</h2><p>Formal edges carry a derivational witness; formal_pairing records a witnessed theorem pairing. Conceptual links and upstream affinities remain separate. The adjacency-matrix graph uses source rows and target columns, aggregates topic edges, and does not assert a family theorem.</p><img src="panels/authored-relations.svg" alt="Three directed family adjacency matrices: formal, theorem-pairing and conceptual; separate editorial upstream affinities"><label>Filter relation kind<select id="relation-kind" aria-label="Filter relation kind"><option value="">All authored kinds</option><option>formal</option><option>formal_pairing</option><option>conceptual</option><option>blocked_by</option></select></label><p id="relation-status" role="status"></p><div class="table-scroll"><table id="relation-table"><caption>Exact authored topic edges and witnesses</caption><thead><tr><th scope="col">Source</th><th scope="col">Target</th><th scope="col">Kind</th><th scope="col">Witness and rationale</th></tr></thead><tbody>'
    )
    for edge in model["relations"]:
        chunks.append(
            f'<tr data-kind="{escape(edge["kind"])}"><td><a href="#{escape(edge["source"])}">{escape(edge["source"])}</a></td><td><a href="#{escape(edge["target"])}">{escape(edge["target"])}</a></td><td>{escape(edge["kind"])}</td><td><code>{escape(edge.get("witness", "Absent: blocker or conceptual association"))}</code><br>{escape(edge["rationale"])}</td></tr>'
        )
    chunks.append(
        "</tbody></table></div><p>Separate publication panels retain the same cell counts: "
        '<a href="panels/authored-relations-formal.svg">formal derivations</a> · '
        '<a href="panels/authored-relations-formal-pairing.svg">formal theorem pairings</a> · '
        '<a href="panels/authored-relations-conceptual.svg">conceptual associations</a>. '
        "The combined matrix above remains the overview for this offline explorer.</p>"
        "<details><summary>Editorial upstream affinities and mismatch obligations</summary>"
        + table(
            model["upstream_affinities"],
            "Pinned research affinities, never proof edges",
        )
        + "</details></section>"
    )
    chunks.append(
        '<section id="capabilities"><h2>Authored capability contracts and evidence</h2><p>All maintained capability nodes retain their original review status, description and qualified evidence. A satisfied source review does not validate a current native receipt. A blocked_by edge targets a capability and remains separate from topic-to-topic theorem relations.</p><div class="controls"><label>Search capabilities<input id="capability-query" aria-label="Search capabilities" type="search" placeholder="Capability, description or evidence…"></label><label>Capability status<select id="capability-status-filter" aria-label="Capability status"><option value="">All statuses</option><option>open</option><option>partial</option><option>satisfied</option></select></label></div><p id="capability-status" role="status" aria-live="polite"></p><div class="table-scroll"><table id="capability-table"><caption>Exact authored capability nodes and qualified evidence</caption><thead><tr><th scope="col">Capability</th><th scope="col">Status</th><th scope="col">Description</th><th scope="col">Qualified evidence</th></tr></thead><tbody>'
    )
    for capability in model["capabilities"]:
        chunks.append(
            f'<tr id="{escape(capability["id"])}" data-status="{escape(capability["status"])}"><td><code>{escape(capability["id"])}</code><br>{escape(capability["title"])}</td><td>{escape(capability["status"])}</td><td>{escape(capability["description"])}</td><td>'
            + "<br>".join(
                "<code>" + escape(ref) + "</code>"
                for ref in capability.get("evidence", [])
            )
            + "</td></tr>"
        )
    chunks.append("</tbody></table></div></section>")
    chunks.append(
        '<section id="boundaries"><h2>Exact formulas expose interpretation boundaries</h2><p>Deterministic numerical evaluation; no random samples or empirical observations. Absolute arithmetic tolerance: '
        + escape(model["arithmetic_tolerance"])
        + ". This is not a scientific or native acceptance threshold.</p>"
        + table(
            [model["numerical_method"]],
            "Reproducible diagnostic arithmetic and display serialization",
        )
    )
    for panel in model["numerical_panels"]:
        chunks.append(
            f'<article><h3>{escape(panel["title"])}</h3><p>{escape(panel["domain"])}</p><p><code>{escape(panel["formula"])}</code></p><p class="boundary">{escape(panel["scope"])}</p><img src="panels/{escape(panel["id"])}.svg" alt="{escape(panel["title"])}; exact formula data below"><details><summary>Accessible exact-formula data</summary>'
            + table(panel["rows"], panel["title"] + " — same data as the figure")
            + (
                table(
                    panel["directions"], "Duplicated Gaussian unit-direction energies"
                )
                if "directions" in panel
                else ""
            )
            + "</details></article>"
        )
    chunks.append(
        '</section><footer><p>Reproduce with <code>fep-formal methods export --output-root DIRECTORY</code>; <code>fep-formal methods check --output-root DIRECTORY</code> compares exact artifact bytes without repairing them. Checkout inspection uses <code>fep-formal --project-root CHECKOUT methods export --output-root DIRECTORY</code>. Visual positions and editorial tags carry no theorem implication.</p><p><a href="visual-model.json">Download canonical visual model</a> · Source and evidence scope are included above</p></footer></main><script>"use strict";const topics=[...document.querySelectorAll(".topic")];const q=document.getElementById("query"),f=document.getElementById("family"),d=document.getElementById("domain"),s=document.getElementById("disposition");function filter(){const text=q.value.toLocaleLowerCase();let count=0;for(const row of topics){const show=(!f.value||row.dataset.family===f.value)&&(!d.value||row.dataset.domains.split("|").includes(d.value))&&(!s.value||row.dataset.disposition===s.value)&&row.textContent.toLocaleLowerCase().includes(text);row.hidden=!show;count+=Number(show);}document.getElementById("topic-status").textContent=count+" of "+topics.length+" topic contracts shown";}for(const control of [q,f,d,s])control.addEventListener("input",filter);function focusHash(){let id;try{id=decodeURIComponent(location.hash.slice(1));}catch{return;}const row=topics.find(r=>r.id===id);if(row){q.value="";f.value="";d.value="";s.value="";filter();row.open=true;row.scrollIntoView({block:"start"});}}window.addEventListener("hashchange",focusHash);focusHash();const selector=document.getElementById("relation-kind");const edges=[...document.querySelectorAll("#relation-table tbody tr")];function edgeFilter(){let count=0;for(const row of edges){row.hidden=!!selector.value&&row.dataset.kind!==selector.value;count+=Number(!row.hidden);}document.getElementById("relation-status").textContent=count+" authored relations shown";}selector.addEventListener("change",edgeFilter);edgeFilter();const capabilityQuery=document.getElementById("capability-query"),capabilityStatus=document.getElementById("capability-status-filter");const capabilities=[...document.querySelectorAll("#capability-table tbody tr")];function capabilityFilter(){let count=0;for(const row of capabilities){row.hidden=!!capabilityStatus.value&&row.dataset.status!==capabilityStatus.value||!row.textContent.toLocaleLowerCase().includes(capabilityQuery.value.toLocaleLowerCase());count+=Number(!row.hidden);}document.getElementById("capability-status").textContent=count+" of "+capabilities.length+" authored capabilities shown";}capabilityQuery.addEventListener("input",capabilityFilter);capabilityStatus.addEventListener("change",capabilityFilter);capabilityFilter();</script></body></html>\n'
    )
    result = "".join(chunks)
    result = result.replace(
        "<style>", "<style>pre{white-space:pre-wrap;overflow-wrap:anywhere}", 1
    )
    if model.get("theorem_analysis"):
        result = result.replace(
            '<a href="#relations">',
            '<a href="#statement-analysis">Statement analysis</a><a href="#relations">',
            1,
        )
    if model.get("cross_corpus_embedding"):
        result = result.replace(
            '<a href="#relations">',
            '<a href="#cross-corpus">Common corpus coordinates</a><a href="#relations">',
            1,
        )
        result = result.replace(
            "</script>",
            'const cq=document.getElementById("cross-query"),ck=document.getElementById("cross-kind"),cf=document.getElementById("cross-feature");const cr=[...document.querySelectorAll("#cross-row-table tbody tr")];function crossFilter(){let shown=0;for(const row of cr){row.hidden=!!ck.value&&row.dataset.kind!==ck.value||!!cf.value&&!row.dataset.features.split("|").includes(cf.value)||!row.textContent.toLocaleLowerCase().includes(cq.value.toLocaleLowerCase());shown+=Number(!row.hidden);}document.getElementById("cross-status").textContent=shown+" of "+cr.length+" source records shown";}for(const c of [cq,ck,cf])c.addEventListener("input",crossFilter);crossFilter();</script>',
        )
    return result.encode()


def _cross_corpus_html(data: Mapping[str, Any]) -> str:
    """Expose every coordinate, source passport, distance and spectrum without a server."""
    projection = data["projection"]
    groups: dict[tuple[int, ...], list[int]] = {}
    for index, vector in enumerate(data["vectors"]):
        groups.setdefault(tuple(vector), []).append(index)
    group_keys = {
        index: f"G{group_index:02d}"
        for group_index, indices in enumerate(groups.values(), 1)
        for index in indices
    }
    rows = []
    for index, (record, vector, point) in enumerate(
        zip(data["rows"], data["vectors"], projection["coordinates"], strict=True)
    ):
        rows.append(
            {
                "key": (
                    f"F{index + 1:02d}"
                    if record["kind"] == "fep_family_context"
                    else f"U{index - sum(row['kind'] == 'fep_family_context' for row in data['rows']) + 1:02d}"
                ),
                "plot_group": group_keys[index],
                "id": record["id"],
                "kind": record["kind"],
                "title": record["title"],
                "features": "; ".join(record["features"]),
                "vector": json.dumps(vector),
                "axis_1": point[0],
                "axis_2": point[1],
                "evidence_status": record["evidence_status"],
                "scope": record["scope"],
                "rationale": record["rationale"],
            }
        )
    chunks = [
        '<section id="cross-corpus"><h2>FEP / OpenAI common mathematical coordinates</h2><p class="boundary">'
        + escape(data["assignment_boundary"])
        + "</p><p>"
        + escape(data["coordinate_weight"])
        + "</p><p>"
        + escape(data["relation_boundary"])
        + '</p><img src="panels/cross-corpus-embedding.svg" alt="Classical MDS on authored common binary features; exact signed coordinates, row keys and eigenspectrum below"><img src="panels/cross-corpus-features.svg" alt="Every assigned binary feature for FEP family unions and individually reviewed OpenAI results"><div class="controls"><label>Search source records<input id="cross-query" aria-label="Search cross-corpus records" type="search"></label><label>Record kind<select id="cross-kind" aria-label="Cross-corpus record kind"><option value="">All</option><option value="fep_family_context">FEP family context</option><option value="upstream_result">OpenAI result unit</option></select></label><label>Assigned coordinate<select id="cross-feature" aria-label="Assigned mathematical coordinate"><option value="">All</option>'
        + "".join(
            '<option value="'
            + escape(row["id"])
            + '">'
            + escape(row["id"])
            + "</option>"
            for row in data["coordinates"]
        )
        + '</select></label></div><p id="cross-status" role="status" aria-live="polite"></p><div class="table-scroll"><table id="cross-row-table"><caption>All common-coordinate records, keys and signed axes; authored proximity is not theorem equivalence</caption><thead><tr>'
        + "".join('<th scope="col">' + escape(key) + "</th>" for key in rows[0])
        + "</tr></thead><tbody>"
    ]
    for row, record in zip(rows, data["rows"], strict=True):
        chunks.append(
            '<tr data-kind="'
            + escape(row["kind"])
            + '" data-features="'
            + escape("|".join(record["features"]))
            + '">'
            + "".join("<td>" + escape(value) + "</td>" for value in row.values())
            + "</tr>"
        )
    chunks.append(
        "</tbody></table></div>"
        + table(
            [
                {"key": f"C{index + 1:02d}", **row}
                for index, row in enumerate(data["coordinates"])
            ],
            "Complete common-coordinate definitions",
        )
    )
    chunks.append(
        "<details><summary>Exact pinned OpenAI source passports and hypotheses</summary>"
        + table(
            [
                {"field": key, "value": value}
                for key, value in data["upstream_pin"].items()
            ],
            "Retained upstream pin and review status",
        )
    )
    for row in data["rows"]:
        if row["kind"] != "upstream_result":
            continue
        chunks.append(
            "<article><h3>"
            + escape(row["id"])
            + " · "
            + escape(row["title"])
            + '</h3><p><a href="'
            + escape(row["source_url"])
            + '">Pinned source statement</a></p>'
            + table(
                [
                    {
                        key: row[key]
                        for key in (
                            "source_path",
                            "source_sha256",
                            "status",
                            "statement",
                            "carriers",
                            "hypotheses",
                            "scope",
                            "rationale",
                        )
                    }
                ],
                "Individual result scope and source identity",
            )
            + "</article>"
        )
    chunks.append(
        "</details><details><summary>MDS mathematics, spectrum, stress and complete distance matrix</summary>"
        + table(
            [
                {"field": key, "value": value}
                for key, value in projection.items()
                if key not in {"coordinates", "distances"}
            ],
            "Projection definitions and diagnostics",
        )
        + table(
            [
                {
                    "id": record["id"],
                    **{
                        other["id"]: value
                        for other, value in zip(data["rows"], distances, strict=True)
                    },
                }
                for record, distances in zip(
                    data["rows"], projection["distances"], strict=True
                )
            ],
            "Full pairwise feature Euclidean distances",
        )
        + table(
            [
                {"input": key, "sha256": value}
                for key, value in data["input_sha256"].items()
            ],
            "Authored table input hashes; informational source identity",
        )
        + "</details></section>"
    )
    return "".join(chunks)


def projection_bytes(model: Mapping[str, Any]) -> dict[Path, bytes]:
    result = {
        Path("visual-model.json"): (
            json.dumps(
                model, indent=2, ensure_ascii=False, sort_keys=True, allow_nan=False
            )
            + "\n"
        ).encode(),
        Path("mathematical-map.html"): render_html(model),
    }
    result.update(
        {Path("panels") / name: data for name, data in render_panels(model).items()}
    )
    return result
