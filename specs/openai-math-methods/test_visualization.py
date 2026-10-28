"""Behavior, numerical domains and adversarial controls for offline visual methods."""

from __future__ import annotations

import copy
import hashlib
import json
import math
import re
import sys
from decimal import (
    ROUND_HALF_EVEN,
    ROUND_UP,
    Context,
    Decimal,
    Inexact,
    Underflow,
    localcontext,
)
from html.parser import HTMLParser
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

from fep_formal.methods import build_mathematical_positioning
from fep_formal.methods import visualization as visual

HERE = Path(__file__).resolve().parent


@pytest.fixture(scope="module")
def source():
    return build_mathematical_positioning(HERE.parents[1]).as_dict()


@pytest.fixture(scope="module")
def model(source):
    return visual.build_visual_model(source)


def test_full_contracts_and_authored_edges_preserved_without_promotion(source, model):
    assert len(model["topics"]) == 168
    assert model["topics"] == source["topics"]
    assert model["relations"] == source["authored_relations"]["edges"]
    assert model["authored_relations"] == source["authored_relations"]
    assert model["capabilities"] == source["authored_relations"]["capabilities"]
    assert len(model["capabilities"]) == model["counts"]["capabilities"] == 50
    assert sum(row["count"] for row in model["family_relation_summary"]) == len(
        model["relations"]
    )
    assert sum(row["topic_count"] for row in model["families"]) == len(model["topics"])
    assert all(
        row["kind"] == "editorial_upstream_affinity"
        for row in model["upstream_affinities"]
    )
    assert all("witness" not in row for row in model["upstream_affinities"])
    original = copy.deepcopy(source)
    visual.build_visual_model(source)
    assert source == original


def test_capability_blockers_remain_separate_from_topic_relation_matrices(source):
    data = copy.deepcopy(source)
    target = data["authored_relations"]["capabilities"][0]
    target["status"] = "partial"
    edge = {
        "source": data["topics"][0]["id"],
        "target": target["id"],
        "kind": "blocked_by",
        "rationale": "Explicit future capability obligation.",
    }
    data["authored_relations"]["edges"].append(edge)
    result = visual.build_visual_model(data)
    assert result["relations"][-1] == edge
    assert not any(
        row["kind"] == "blocked_by" for row in result["family_relation_summary"]
    )
    output = visual.render_html(result).decode()
    assert f'href="#{target["id"]}"' in output
    assert f'id="{target["id"]}" data-status="partial"' in output
    assert "Explicit future capability obligation." in output
    edge["target"] = "cap-unreviewed"
    with pytest.raises(ValueError, match="endpoint"):
        visual.build_visual_model(data)


def test_capability_html_preserves_all_evidence_and_control_names(model):
    output = visual.render_html(model).decode()
    tags = Tags()
    tags.feed(output)
    for capability in model["capabilities"]:
        assert visual.escape(capability["description"]) in output
        for witness in capability.get("evidence", []):
            assert visual.escape(witness) in output
    rows = [attrs for tag, attrs in tags.tags if tag == "tr" and "data-status" in attrs]
    assert len(rows) == 50
    controls = {
        attrs["id"]: attrs for tag, attrs in tags.tags if tag in {"input", "select"}
    }
    assert controls["domain"]["aria-label"] == "Family domain"
    assert controls["capability-query"]["aria-label"] == "Search capabilities"
    assert controls["capability-status-filter"]["aria-label"] == "Capability status"
    assert "fep-formal methods check --output-root DIRECTORY" in output


@pytest.mark.parametrize(
    "case",
    [
        "duplicate-topic",
        "unknown-family",
        "unknown-domain",
        "dangling-edge",
        "unknown-kind",
        "missing-witness",
    ],
)
def test_inconsistent_graphs_refused(source, case):
    data = copy.deepcopy(source)
    if case == "duplicate-topic":
        data["topics"].append(data["topics"][0])
    elif case == "unknown-family":
        data["topics"][0]["family"] = "unknown"
    elif case == "unknown-domain":
        data["family_positions"][0]["domains"].append("unknown")
    elif case == "dangling-edge":
        data["authored_relations"]["edges"][0]["target"] = "unknown"
    elif case == "unknown-kind":
        data["authored_relations"]["edges"][0]["kind"] = "inferred-proof"
    else:
        data["authored_relations"]["edges"][0].pop("witness")
    with pytest.raises(ValueError):
        visual.build_visual_model(data)


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), -0.1, 1.1, True])
def test_probability_domain_rejected(bad):
    with pytest.raises(ValueError):
        visual.binary_kl(bad, 0.5)


def test_support_orientation_and_extreme_probabilities_remain_extended():
    assert visual.binary_kl(1.0, 1.0) == 0
    assert visual.binary_kl(0.5, 1.0) is None
    assert visual.binary_kl(1.0, 0.999) == pytest.approx(
        -math.log(0.999), abs=visual.TOLERANCE
    )
    assert math.isfinite(visual.binary_kl(1.0, 1e-320))
    panels = {p["id"]: p for p in visual.numerical_panels()}
    for row in panels["support-convergence"]["rows"]:
        assert row["kl_p_to_delta"] is None
        assert row["total_variation"] == row["epsilon"]
        assert row["kl_delta_to_p"] == pytest.approx(
            -math.log1p(-row["epsilon"]), abs=visual.TOLERANCE
        )
    assert panels["support-convergence"]["boundary"]["both_kl"] == 0


def test_fisher_null_and_positive_tangents_and_invalid_variance():
    assert visual.fisher_energy((1.0, -1.0)) == 0
    assert visual.fisher_energy((1.0, 1.0)) == 2
    for variance in [0.0, -1.0, float("inf"), float("nan")]:
        with pytest.raises(ValueError):
            visual.fisher_energy((1.0, 1.0), variance)
    panel = visual.numerical_panels()[1]
    for row in panel["rows"]:
        p = row["p"]
        assert row["fisher"] == pytest.approx(
            (1 / math.sqrt(p * (1 - p))) ** 2, abs=visual.TOLERANCE
        )
    assert panel["directions"][36]["energy"] == pytest.approx(0, abs=visual.TOLERANCE)


def test_fisher_energy_refuses_unrepresentable_values_and_boolean_parameters():
    for direction, variance in (
        ((1e308, 1e308), 2.0),
        ((1.0, 1.0), 5e-324),
        ((1e-300, 0.0), 1e300),
        ((True, 0.0), 2.0),
        ((0.0, False), 2.0),
        ((1.0, 1.0), True),
        ((1.0, 1.0), False),
    ):
        with pytest.raises(ValueError):
            visual.fisher_energy(direction, variance)
    assert visual.fisher_energy((1e154, 1e154), 1e308) == pytest.approx(4.0)
    assert visual.fisher_energy((1e308, -1e308), 5e-324) == 0.0
    assert visual.fisher_energy((3.0, -1.0), 4.0) == 1.0


@pytest.mark.parametrize(
    "direction,variance",
    [((1.6e-162, 0.0), 5e-324), ((1e-160, 0.0), 1e-320)],
)
def test_fisher_energy_preserves_representable_subnormal_intermediate_results(
    direction, variance
):
    total = math.fsum(direction)
    assert 0 < total * total < sys.float_info.min
    with localcontext() as context:
        context.prec = 1000
        exact_total = sum(Decimal.from_float(value) for value in direction)
        expected = float(exact_total * exact_total / Decimal.from_float(variance))
    actual = visual.fisher_energy(direction, variance)
    # Compare exact binary input values, allowing only final arithmetic rounding.
    assert abs(actual - expected) <= 2 * math.ulp(expected)
    assert abs(total * total / variance - expected) > 2 * math.ulp(expected)


def test_fisher_energy_keeps_normal_float_api_values_unchanged():
    for index in range(97):
        angle = index * 2 * math.pi / 96
        direction = math.cos(angle), math.sin(angle)
        assert (
            visual.fisher_energy(direction) == (direction[0] + direction[1]) ** 2 / 2.0
        )


def test_decimal_diagnostic_grid_matches_independent_exact_identities():
    panels = visual.numerical_panels()
    with localcontext(Context(prec=110, rounding=ROUND_HALF_EVEN)):
        quantum = Decimal("1e-24")

        def published(value):
            return float(value.quantize(quantum, rounding=ROUND_HALF_EVEN))

        support, fisher, hidden, risk = panels
        assert support["rows"][-1]["epsilon"] == 0.1
        assert support["rows"][-1]["kl_delta_to_p"] == published(
            -(Decimal(9) / 10).ln()
        )
        # Independent arcsin series (not the producer's range-reduced atan).
        p = Decimal("0.12")
        term = p.sqrt()
        arcsin = term
        for index in range(500):
            term *= (2 * index + 1) ** 2 * p / (2 * (index + 1) * (2 * index + 3))
            arcsin += term
            if abs(term) < Decimal("1e-100"):
                break
        else:
            pytest.fail("independent arcsin reference did not converge")
        assert fisher["rows"][5]["coordinate"] == published(2 * arcsin)
        assert fisher["rows"][5]["fisher"] == published(1 / (p * (1 - p)))
        # The two hosted drifting direction values admit independent radicals.
        assert fisher["directions"][32]["energy"] == published(
            (2 - Decimal(3).sqrt()) / 4
        )
        assert fisher["directions"][33]["energy"] == published(
            (2 - (2 + Decimal(2).sqrt()).sqrt()) / 4
        )
        assert [row["energy"] for row in fisher["directions"][::12]] == [
            0.5,
            1.0,
            0.5,
            0.0,
            0.5,
            1.0,
            0.5,
            0.0,
            0.5,
        ]
        assert hidden["rows"][20]["full_law_kl"] == published(
            Decimal("4.5") * Decimal(-4).exp()
        )
        assert risk["rows"][0]["preference_kl"] == published(Decimal("1.25").ln())
        assert risk["rows"][-1]["preference_kl"] == published(Decimal(5).ln())
        assert risk["rows"][20]["preference_kl"] == 0
        assert risk["rows"][70]["expected_brier"] == 0.21


def test_diagnostic_producer_ignores_platform_libm_and_ambient_decimal(monkeypatch):
    expected = json.dumps(visual.numerical_panels(), sort_keys=True, allow_nan=False)

    def forbidden(*args):
        pytest.fail("platform libm cannot determine publication diagnostic values")

    for name in ("log", "log1p", "sqrt", "asin", "atan", "sin", "cos", "exp", "pow"):
        monkeypatch.setattr(math, name, forbidden)
    with localcontext() as ambient:
        ambient.prec = 6
        ambient.rounding = ROUND_UP
        ambient.Emin = 0
        ambient.Emax = 9
        ambient.traps[Inexact] = True
        ambient.traps[Underflow] = True
        before = ambient.copy()
        assert (
            json.dumps(visual.numerical_panels(), sort_keys=True, allow_nan=False)
            == expected
        )
        assert ambient.prec == before.prec
        assert ambient.rounding == before.rounding
        assert ambient.traps == before.traps
        assert ambient.flags == before.flags


def test_diagnostic_series_bounds_domains_and_exhaustion_fail_closed(monkeypatch):
    with localcontext(Context(prec=80, rounding=ROUND_HALF_EVEN)):
        # Both series are within the reviewed next-omitted-term domains.
        assert abs(
            visual._atan_series(Decimal("0.25")) - Decimal(str(math.atan(0.25)))
        ) < Decimal("1e-16")
        for bad in (Decimal("0.251"), Decimal("NaN"), Decimal("Infinity")):
            with pytest.raises(ValueError, match="atan series requires"):
                visual._atan_series(bad)
        pi = Decimal(
            "3.141592653589793238462643383279502884197169399375105820974944592307816406286209"
        )
        for value in (Decimal("0.99"), Decimal(1), Decimal(7)):
            assert float(visual._decimal_atan(value, pi)) == pytest.approx(
                math.atan(float(value)), abs=visual.TOLERANCE
            )
        assert abs(visual._decimal_sin(pi / 6, pi) - Decimal("0.5")) < Decimal("1e-74")
        with pytest.raises(ValueError, match="sine requires"):
            visual._decimal_sin(5 * pi, pi)
        monkeypatch.setattr(visual, "_SERIES_LIMIT", 1)
        with pytest.raises(ValueError, match="atan remainder did not converge"):
            visual.numerical_panels()
        with pytest.raises(ValueError, match="sine remainder did not converge"):
            visual._decimal_sin(pi / 6, pi)


def test_display_quantization_is_half_even_and_not_a_freshness_tolerance(model):
    with localcontext(Context(prec=80, rounding=ROUND_HALF_EVEN)):
        assert visual._display_number(Decimal("0.5e-24")) == 0.0
        assert visual._display_number(Decimal("1.5e-24")) == 2e-24
        assert math.copysign(1, visual._display_number(Decimal("-0.5e-24"))) == 1
        with pytest.raises(ValueError, match="display value must be finite"):
            visual._display_number(Decimal("NaN"))
    method = model["numerical_method"]
    assert method["decimal_precision"] == 80
    assert method["display_decimal_places"] == 24
    assert method["rounding"] == "ROUND_HALF_EVEN"
    assert model["arithmetic_tolerance"] == 1e-12
    assert "Display quantization does not change" in method["scope"]
    assert "Reproducible diagnostic arithmetic" in visual.render_html(model).decode()


def test_hidden_projection_and_risk_preference_keep_distinct_objects():
    panels = {p["id"]: p for p in visual.numerical_panels()}
    for row in panels["hidden-projection"]["rows"]:
        assert row["full_law_kl"] > 0
        assert row["observed_law_kl"] == 0
        assert row["full_law_kl"] == pytest.approx(
            0.5 * row["hidden_mean_second"] ** 2, abs=visual.TOLERANCE
        )
    rows = panels["risk-preference"]["rows"]
    assert min(rows, key=lambda r: r["expected_brier"])["forecast"] == 0.7
    assert min(rows, key=lambda r: r["preference_kl"])["forecast"] == 0.2
    assert rows[20]["expected_brier"] > rows[70]["expected_brier"]
    assert rows[70]["preference_kl"] > rows[20]["preference_kl"]


class Tags(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))


def test_html_contracts_accessibility_and_no_source_script_execution(model):
    data = copy.deepcopy(model)
    attack = '</script><script src="https://example.invalid/leak">alert(1)</script><img onerror="alert(2)">'
    data["topics"][0]["title"] = attack
    data["topics"][0]["semantic_review"]["invariant"] = attack
    output = visual.render_html(data).decode()
    assert attack not in output
    assert "&lt;/script&gt;" in output
    tags = Tags()
    tags.feed(output)
    scripts = [a for t, a in tags.tags if t == "script"]
    assert len(scripts) == 1 and "src" not in scripts[0]
    assert all("onerror" not in a for _, a in tags.tags)
    assert all(
        not a.get("src", "").startswith(("http:", "https:", "//")) for _, a in tags.tags
    )
    assert (
        len([1 for t, a in tags.tags if t == "details" and a.get("class") == "topic"])
        == 168
    )
    for topic in model["topics"]:
        assert topic["primary_theorem_qualified"] in output
        assert visual.escape(topic["semantic_review"]["assumption_review"]) in output
    assert 'id="relation-kind"' in output and 'id="topic-status"' in output
    assert "Duplicated Gaussian unit-direction energies" in output
    assert "family union" in output.lower()


def test_deterministic_json_html_and_publication_svg(model):
    first = visual.projection_bytes(model)
    second = visual.projection_bytes(json.loads(json.dumps(model, sort_keys=True)))
    assert first == second
    assert len(first) == 15
    assert all(not path.is_absolute() and ".." not in path.parts for path in first)
    for path, content in first.items():
        if path.suffix == ".svg":
            svg = ET.fromstring(content)
            assert svg.attrib["role"] == "img"
            assert "desc" in svg.attrib["aria-labelledby"]
            assert not any(
                node.tag.rsplit("}", 1)[-1].lower() == "date" for node in svg.iter()
            )
            assert "<script" not in content.decode()
    assert b"source rows" in first[Path("panels/authored-relations.svg")]


def test_cross_corpus_svg_preserves_euclidean_pixel_scale_in_both_axes(model):
    data = copy.deepcopy(model)
    cross = data["cross_corpus_embedding"]
    cross["projection"]["coordinates"] = [[0, 0], [1, 0], [0, 1]]
    cross["vectors"] = [[0, 0], [1, 0], [0, 1]]
    cross["rows"] = cross["rows"][:3]
    cross["row_order"] = cross["row_order"][:3]
    root = ET.fromstring(visual.cross_corpus_svg(data))
    namespace = {"svg": "http://www.w3.org/2000/svg"}
    points = [
        (float(node.attrib["cx"]), float(node.attrib["cy"]))
        for node in root.findall("svg:circle", namespace)
    ]
    assert len(points) == 3
    assert points[1][0] - points[0][0] == pytest.approx(
        points[0][1] - points[2][1], abs=1e-12
    )
    assert points[1][1] == points[0][1]
    assert points[2][0] == points[0][0]


def test_cross_corpus_html_retains_all_source_rows_coordinates_spectrum_and_controls(
    model,
):
    output = visual.render_html(model).decode()
    cross = model["cross_corpus_embedding"]
    tags = Tags()
    tags.feed(output)
    controls = {
        attrs["id"]: attrs for tag, attrs in tags.tags if tag in {"input", "select"}
    }
    assert controls["cross-query"]["aria-label"] == "Search cross-corpus records"
    assert controls["cross-feature"]["aria-label"] == "Assigned mathematical coordinate"
    for row in cross["rows"]:
        assert visual.escape(row["id"]) in output
        assert visual.escape(row["scope"]) in output
        if row["kind"] == "upstream_result":
            assert f'href="{row["source_url"]}"' in output
            assert row["source_sha256"] in output
            assert visual.escape(row["statement"]) in output
    for coordinate in cross["coordinates"]:
        assert visual.escape(coordinate["definition"]) in output
    assert "eigenvalues_decimal" in output
    assert "normalized_stress" in output
    assert cross["input_sha256"]["positioning.yaml"] in output
    assert "not assigned" in output


@pytest.fixture(scope="module")
def panels(model):
    return visual.render_panels(model)


def test_print_exports_preserve_prior_explorer_views_and_add_three_source_views(
    model, panels
):
    assert len(panels) == 13
    assert set(visual.PRINT_RELATION_PANELS) == {
        "authored-relations-formal.svg",
        "authored-relations-formal-pairing.svg",
        "authored-relations-conceptual.svg",
    }
    tags = Tags()
    tags.feed(visual.render_html(model).decode())
    assert len([attrs for tag, attrs in tags.tags if tag == "img"]) == 10
    links = {attrs.get("href") for tag, attrs in tags.tags if tag == "a"}
    assert all(f"panels/{name}" in links for name in visual.PRINT_RELATION_PANELS)
    numerical_bytes = json.dumps(
        visual.numerical_panels(), sort_keys=True, allow_nan=False
    ).encode()
    assert hashlib.sha256(numerical_bytes).hexdigest() == (
        "6ca9a9b33556b696bdeb0814a12882df2a50878e9653bf4d791f8e465f0dd0da"
    )


def test_publication_typography_reaches_seven_points_under_both_pdf_caps(panels):
    # Include superscript tspan sizes emitted by Matplotlib's logarithmic axes.
    for name, data in panels.items():
        if name == "authored-relations.svg":
            continue  # The combined view stays in HTML; publication uses the splits.
        root = ET.fromstring(data)
        _, _, width, height = map(float, root.attrib["viewBox"].split())
        scale = min(451.9 / width, 364.5 / height)
        sizes = []
        for node in root.iter():
            if "font-size" in node.attrib:
                sizes.append(float(node.attrib["font-size"]))
            sizes.extend(
                float(match)
                for match in re.findall(
                    r"font-size:\s*([\d.]+)", node.attrib.get("style", "")
                )
            )
        assert sizes, name
        assert min(sizes) * scale >= 7, (name, min(sizes) * scale)


def test_print_matrices_preserve_all_authored_cell_counts_and_family_keys(
    model, panels
):
    namespace = {"svg": "http://www.w3.org/2000/svg"}
    for name, kind in visual.PRINT_RELATION_PANELS.items():
        root = ET.fromstring(panels[name])
        assert root.attrib["data-relation-kind"] == kind
        cells = [
            node
            for node in root.findall("svg:rect", namespace)
            if "data-count" in node.attrib
        ]
        actual = {
            (node.attrib["data-source"], node.attrib["data-target"]): int(
                node.attrib["data-count"]
            )
            for node in cells
        }
        expected = {
            (row["source"], row["target"]): row["count"]
            for row in model["family_relation_summary"]
            if row["kind"] == kind
        }
        assert len(cells) == len(model["families"]) ** 2
        assert {pair: count for pair, count in actual.items() if count} == expected
        assert sum(actual.values()) == sum(
            edge["kind"] == kind for edge in model["relations"]
        )
        assert all(node.attrib["data-kind"] == kind for node in cells)
        assert {
            node.attrib["data-family-key"]
            for node in root.findall("svg:text", namespace)
            if "data-family-key" in node.attrib
        } == {row["family"] for row in model["families"]}
    with pytest.raises(ValueError, match="relation kind"):
        visual.relation_print_svg(model, "blocked_by")


def test_family_print_panels_preserve_every_incidence_and_semantic_count(model, panels):
    namespace = {"svg": "http://www.w3.org/2000/svg"}
    domains = ET.fromstring(panels["family-domains.svg"])
    actual = {
        (node.attrib["data-family"], node.attrib["data-domain"]): int(
            node.attrib["data-present"]
        )
        for node in domains.findall("svg:rect", namespace)
        if "data-present" in node.attrib
    }
    assert actual == {
        (row["family"], domain): int(domain in row["domains"])
        for row in model["families"]
        for domain in model["domain_order"]
    }
    semantics = ET.fromstring(panels["semantic-layers.svg"])
    actual_counts = {
        (node.attrib["data-family"], node.attrib["data-disposition"]): int(
            node.attrib["data-count"]
        )
        for node in semantics.findall("svg:rect", namespace)
        if "data-count" in node.attrib
    }
    assert actual_counts == {
        (row["family"], disposition): count
        for row in model["families"]
        for disposition, count in row["semantic_counts"].items()
        if count
    }


def test_publication_keys_labels_and_counts_fit_without_text_overlap(panels):
    import matplotlib
    from PIL import ImageFont

    font_path = Path(matplotlib.get_data_path()) / "fonts" / "ttf" / "DejaVuSans.ttf"
    namespace = {"svg": "http://www.w3.org/2000/svg"}

    def polygon(node):
        text = node.text or ""
        font = ImageFont.truetype(str(font_path), int(node.attrib["font-size"]))
        left, top, right, bottom = font.getbbox(text, anchor="ls")
        anchor = node.attrib["text-anchor"]
        offset = (
            0
            if anchor == "start"
            else -font.getlength(text) / (2 if anchor == "middle" else 1)
        )
        x, y = float(node.attrib["x"]), float(node.attrib["y"])
        rotation = node.attrib.get("transform", "rotate(0)")
        angle = math.radians(float(rotation.split("(")[1].split()[0].rstrip(")")))
        return [
            (
                x + (a + offset) * math.cos(angle) - b * math.sin(angle),
                y + (a + offset) * math.sin(angle) + b * math.cos(angle),
            )
            for a, b in [(left, top), (right, top), (right, bottom), (left, bottom)]
        ]

    def overlaps(first, second):
        for vertices in [first, second]:
            for a, b in zip(vertices, vertices[1:] + vertices[:1], strict=True):
                axis = a[1] - b[1], b[0] - a[0]
                p = [x * axis[0] + y * axis[1] for x, y in first]
                q = [x * axis[0] + y * axis[1] for x, y in second]
                if max(p) <= min(q) or max(q) <= min(p):
                    return False
        return True

    for name in [
        "family-domains.svg",
        "semantic-layers.svg",
        *visual.PRINT_RELATION_PANELS,
    ]:
        root = ET.fromstring(panels[name])
        nodes = root.findall("svg:text", namespace)
        polygons = [polygon(node) for node in nodes]
        for node, vertices in zip(nodes, polygons, strict=True):
            assert all(
                0 <= x <= visual.PRINT_WIDTH and 0 <= y <= visual.PRINT_HEIGHT
                for x, y in vertices
            ), (name, node.text)
        for i, first in enumerate(polygons):
            for j in range(i):
                assert not overlaps(first, polygons[j]), (
                    name,
                    nodes[i].text,
                    nodes[j].text,
                )
