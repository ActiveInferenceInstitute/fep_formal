#!/usr/bin/env python3
"""Deterministic generator and freshness gate for the Cascadia Lean instance.

Reads only the retained fixtures (no sibling checkout is opened):

- ``fixtures/smith_river_homing.gnn.md``: GNN v1 source rendered by GEO-INFER-ACT;
- ``fixtures/smith_river_homing.geo-infer.json``: the ``gnn-geo-infer/1``
  artifact GNN's strict exporter produced from that source;
- ``fixtures/smith_river_homing.domain.json``: the typed H3 network sidecar.

Writes ``generated/SmithRiverHoming.lean`` (exact tables, typed relations, the
transcribed GNN document and the instance theorems) and
``generated/manifest.json`` (digests binding inputs, generator, the general
theory module and outputs).

Every check fails closed: the artifact must name the source's SHA-256, the
sidecar must list the artifact's state order, every probability must be an
exact power-of-two fraction, and every column must sum to exactly one. The
Lean statement values (evidence, posterior, arrival bound, homing plan) are
computed here and then *checked* by Lean; compilation is owned by
``verify_native.py``.

``--check`` regenerates in memory and fails on any byte difference.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import deque
from decimal import Decimal
from fractions import Fraction
from math import lcm
from pathlib import Path
from typing import Any

SLICE = Path(__file__).resolve().parent
REPO_ROOT = SLICE.parents[1]
FIXTURES = SLICE / "fixtures"
GENERATED = SLICE / "generated"
THEORY = SLICE / "lean" / "CascadiaGeo" / "TypedGeospatial.lean"
SOURCE = FIXTURES / "smith_river_homing.gnn.md"
ARTIFACT = FIXTURES / "smith_river_homing.geo-infer.json"
DOMAIN = FIXTURES / "smith_river_homing.domain.json"
INSTANCE = GENERATED / "SmithRiverHoming.lean"
MANIFEST = GENERATED / "manifest.json"
ACTIONS = ("hold", "downstream", "upstream", "turn")
RELATION_ACTION = {"successor": 1, "upstream": 2, "side": 3}
MAX_DENOMINATOR = 1 << 16
SECTION_ORDER = (
    "GNNSection",
    "GNNVersionAndFlags",
    "ModelName",
    "ModelAnnotation",
    "StateSpaceBlock",
    "Connections",
    "InitialParameterization",
    "Equations",
    "Time",
    "ActInfOntologyAnnotation",
    "ModelParameters",
    "Footer",
)


class FixtureError(ValueError):
    """A fixture is malformed, inconsistent or not exactly representable."""


def sha256_bytes(data: bytes) -> str:
    """Return the lowercase SHA-256 of bytes."""
    return hashlib.sha256(data).hexdigest()


def _unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise FixtureError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def load_json(path: Path) -> Any:
    """Strict JSON: duplicate keys and non-finite numbers are rejected.

    Decimal literals are parsed exactly (``decimal.Decimal``), never through
    binary floats: every finite float is a dyadic rational, so a dyadic check
    is meaningful only on the literal as written.
    """

    def bad_constant(token: str) -> Any:
        raise FixtureError(f"non-finite JSON number {token}")

    return json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=_unique,
        parse_constant=bad_constant,
        parse_float=Decimal,
    )


def exact_table(values: list[Any], name: str) -> tuple[list[int], int]:
    """Convert exact decimal literals to numerators over their power-of-two LCM."""
    fractions = []
    for value in values:
        if isinstance(value, bool) or not isinstance(value, (int, Decimal)):
            raise FixtureError(f"{name} entries must be exact JSON decimal literals")
        fraction = Fraction(value)
        if fraction < 0:
            raise FixtureError(f"{name} entries must be nonnegative")
        fractions.append(fraction)
    denominator = lcm(*(fraction.denominator for fraction in fractions))
    if denominator & (denominator - 1):
        raise FixtureError(f"{name} denominator {denominator} is not a power of two")
    if denominator > MAX_DENOMINATOR:
        raise FixtureError(
            f"{name} denominator {denominator} exceeds {MAX_DENOMINATOR}"
        )
    numerators = [fraction * denominator for fraction in fractions]
    return [int(value) for value in numerators], denominator


def lean_string(text: str) -> str:
    """Render a Lean string literal."""
    escaped = (
        text.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\t", "\\t")
    )
    return f'"{escaped}"'


def lean_list(values: list[Any]) -> str:
    """Render nested lists of naturals, options or rationals as Lean list literals."""

    def item(value: Any) -> str:
        if isinstance(value, list):
            return lean_list(value)
        if value is None:
            return "none"
        if isinstance(value, tuple) and value[0] == "some":
            return f"some {value[1]}"
        if isinstance(value, Fraction):
            return (
                f"({value.numerator} / {value.denominator} : ℚ)"
                if value.denominator != 1
                else f"({value.numerator} : ℚ)"
            )
        return str(value)

    return "[" + ", ".join(item(value) for value in values) + "]"


# --------------------------------------------------------------------------- GNN AST


def parse_gnn(source: str) -> list[tuple[str, Any]]:
    """Restricted parser for the GNN v1 shape GEO-INFER-ACT renders.

    Only the canonical sections listed in ``SECTION_ORDER`` are accepted, each
    once and in order; leading ``#`` header lines are comments outside the Q1
    surface. Anything else raises.
    """
    sections: list[tuple[str, list[str]]] = []
    for line in source.splitlines():
        if line.startswith("## "):
            sections.append((line[3:].strip(), []))
        elif sections:
            sections[-1][1].append(line)
        elif line.strip() and not line.startswith("# "):
            raise FixtureError(f"unexpected text before the first section: {line!r}")
    names = [name for name, _ in sections]
    if tuple(names) != SECTION_ORDER:
        raise FixtureError(f"unexpected section order {names}")
    parsed: list[tuple[str, Any]] = []
    for name, lines in sections:
        body = "\n".join(lines).strip("\n")
        content = [line for line in lines if line.strip()]
        if name == "GNNSection":
            parsed.append((name, content[0].strip()))
        elif name == "GNNVersionAndFlags":
            if content != ["GNN v1"]:
                raise FixtureError("expected 'GNN v1'")
            parsed.append((name, "v1"))
        elif name in {"ModelName", "ModelAnnotation", "Equations", "Footer"}:
            parsed.append((name, body.strip()))
        elif name == "StateSpaceBlock":
            declarations = []
            for line in content:
                match = re.fullmatch(r"\s*([^\s\[]+)\[([^\]]*)\]\s*(#.*)?", line)
                if not match:
                    raise FixtureError(f"bad declaration {line!r}")
                parts = [part.strip() for part in match.group(2).split(",")]
                kinds = [part for part in parts if part.startswith("type=")]
                dims = [part for part in parts if "=" not in part]
                if len(kinds) != 1 or len(dims) + 1 != len(parts):
                    raise FixtureError(f"bad declaration fields {line!r}")
                value_type = {
                    "type=float": "floatT",
                    "type=int": "intT",
                    "type=bool": "boolT",
                }[kinds[0]]
                declarations.append(
                    (
                        match.group(1),
                        [int(d) if d.isdigit() else d for d in dims],
                        value_type,
                    )
                )
            parsed.append((name, declarations))
        elif name == "Connections":
            edges = []
            for line in content:
                match = re.fullmatch(r"([^\s>\-]+)([>\-])([^\s>\-]+)", line.strip())
                if not match:
                    raise FixtureError(f"bad connection {line!r}")
                edges.append(
                    (
                        match.group(1),
                        "directed" if match.group(2) == ">" else "undirected",
                        match.group(3),
                    )
                )
            parsed.append((name, edges))
        elif name == "InitialParameterization":
            entries, current, depth = [], None, 0
            for line in lines:
                if current is None:
                    if not line.strip():
                        continue
                    match = re.fullmatch(r"([^=\s]+)=(.*)", line)
                    if not match:
                        raise FixtureError(f"bad parameterization {line!r}")
                    current = [match.group(1), match.group(2)]
                else:
                    current[1] += "\n" + line
                depth = current[1].count("{") - current[1].count("}")
                if depth == 0:
                    entries.append((current[0], current[1]))
                    current = None
            if current is not None or depth:
                raise FixtureError("unbalanced InitialParameterization braces")
            parsed.append((name, entries))
        elif name == "Time":
            entries = []
            for line in content:
                key, _, value = line.strip().partition("=")
                entries.append((key, value if _ else None))
            parsed.append((name, entries))
        elif name == "ActInfOntologyAnnotation":
            parsed.append(
                (name, [tuple(line.strip().split("=", 1)) for line in content])
            )
        elif name == "ModelParameters":
            parameters = []
            for line in content:
                key, separator, value = line.partition(":")
                if not separator:
                    raise FixtureError(f"bad model parameter {line!r}")
                parameters.append((key.strip(), value.strip()))
            parsed.append((name, parameters))
    return parsed


def render_document(sections: list[tuple[str, Any]]) -> str:
    """Render the parsed GNN document as a Q1 ``GnnDocument`` term."""
    rendered = []
    for name, value in sections:
        if name == "GNNSection":
            rendered.append(f".gnnSection {lean_string(value)}")
        elif name == "GNNVersionAndFlags":
            rendered.append(".gnnVersionAndFlags .v1 []")
        elif name == "ModelName":
            rendered.append(f".modelName {lean_string(value)}")
        elif name == "ModelAnnotation":
            rendered.append(f".modelAnnotation {lean_string(value)}")
        elif name == "StateSpaceBlock":
            declarations = ",\n        ".join(
                "⟨{}, [{}], .{}, none⟩".format(
                    lean_string(decl_name),
                    ", ".join(
                        f".lit {dim}"
                        if isinstance(dim, int)
                        else f".ref {lean_string(dim)}"
                        for dim in dims
                    ),
                    value_type,
                )
                for decl_name, dims, value_type in value
            )
            rendered.append(f".stateSpaceBlock\n        [ {declarations} ]")
        elif name == "Connections":
            edges = ",\n        ".join(
                f"⟨{lean_string(src)}, .{kind}, {lean_string(dst)}, none⟩"
                for src, kind, dst in value
            )
            rendered.append(f".connections\n        [ {edges} ]")
        elif name == "InitialParameterization":
            entries = ",\n        ".join(
                f"⟨{lean_string(var)}, {lean_string(payload)}⟩"
                for var, payload in value
            )
            rendered.append(f".initialParameterization\n        [ {entries} ]")
        elif name == "Equations":
            rendered.append(f".equations {lean_string(value)}")
        elif name == "Time":
            entries = ", ".join(
                f"⟨{lean_string(key)}, {'none' if entry is None else 'some ' + lean_string(entry)}⟩"
                for key, entry in value
            )
            rendered.append(f".time [ {entries} ]")
        elif name == "ActInfOntologyAnnotation":
            bindings = ",\n        ".join(
                f"⟨{lean_string(var)}, {lean_string(term)}⟩" for var, term in value
            )
            rendered.append(f".actInfOntologyAnnotation\n        [ {bindings} ]")
        elif name == "ModelParameters":
            parameters = ",\n        ".join(
                f"⟨{lean_string(key)}, {lean_string(entry)}⟩" for key, entry in value
            )
            rendered.append(f".modelParameters\n        [ {parameters} ]")
        elif name == "Footer":
            rendered.append(f".footer {lean_string(value)}")
    return "[ " + "\n    , ".join(rendered) + " ]"


# --------------------------------------------------------------------------- fixtures


def load_fixtures(fixtures: Path = FIXTURES) -> dict[str, Any]:
    """Load and cross-validate the three fixtures; return exact model data."""
    source_path = fixtures / SOURCE.name
    artifact_path = fixtures / ARTIFACT.name
    domain_path = fixtures / DOMAIN.name
    source_bytes = source_path.read_bytes()
    source_sha = sha256_bytes(source_bytes)
    artifact = load_json(artifact_path)
    expected = {
        "schema_version",
        "model_type",
        "model_name",
        "dimensions",
        "matrices",
        "space",
        "time",
        "provenance",
    }
    if set(artifact) != expected or artifact["schema_version"] != "gnn-geo-infer/1":
        raise FixtureError("artifact is not a gnn-geo-infer/1 document")
    if artifact["model_type"] != "categorical" or artifact["space"]["kind"] != "h3":
        raise FixtureError("artifact must be categorical over H3 cells")
    if artifact["provenance"]["source_sha256"] != source_sha:
        raise FixtureError("artifact provenance does not name the GNN source digest")
    domain = load_json(domain_path)
    if domain.get("schema_version") != "geo-infer-act/river-homing/1":
        raise FixtureError("unexpected domain sidecar schema")
    if domain["gnn_source_sha256"] != source_sha:
        raise FixtureError("domain sidecar names a different GNN source")
    cells = [row["cell"] for row in domain["network"]["cells"]]
    if cells != artifact["space"]["state_ids"]:
        raise FixtureError("domain cell order differs from artifact state_ids")
    dims = artifact["dimensions"]
    n, m, u = dims["states"], dims["observations"], dims["actions"]
    if (n, m, u) != (len(cells), len(domain["observation_labels"]), len(ACTIONS)):
        raise FixtureError("dimension mismatch between artifact and sidecar")
    matrices = artifact["matrices"]
    a_flat, a_den = exact_table([value for row in matrices["A"] for value in row], "A")
    b_flat, b_den = exact_table(
        [
            matrices["B"][nxt][prev][act]
            for act in range(u)
            for prev in range(n)
            for nxt in range(n)
        ],
        "B",
    )
    d_num, d_den = exact_table(matrices["D"], "D")
    e_num, e_den = exact_table(matrices["E"], "E")
    a_num = [a_flat[o * n : (o + 1) * n] for o in range(m)]
    b_num = [
        [b_flat[(act * n + prev) * n : (act * n + prev + 1) * n] for prev in range(n)]
        for act in range(u)
    ]
    exact = domain["exact"]
    for o in range(m):
        for s in range(n):
            if Fraction(exact["A"][o][s]) != Fraction(a_num[o][s], a_den):
                raise FixtureError("sidecar A differs from artifact A")
    for act in range(u):
        for prev in range(n):
            for nxt in range(n):
                if Fraction(exact["B"][nxt][prev][act]) != Fraction(
                    b_num[act][prev][nxt], b_den
                ):
                    raise FixtureError("sidecar B differs from artifact B")
            if sum(b_num[act][prev]) != b_den:
                raise FixtureError("B column does not sum to one")
    for s in range(n):
        if sum(a_num[o][s] for o in range(m)) != a_den:
            raise FixtureError("A column does not sum to one")
    if sum(d_num) != d_den or sum(e_num) != e_den:
        raise FixtureError("D or E does not sum to one")
    c_values = [Fraction(value) for value in matrices["C"]]
    rows = domain["network"]["cells"]
    index = {cell: position for position, cell in enumerate(cells)}
    relations = {
        name: [None if row[name] is None else index[row[name]] for row in rows]
        for name in ("successor", "upstream", "side")
    }
    adjacency = [
        sorted(index[other] for other in domain["h3_adjacency"][cell]) for cell in cells
    ]
    landmarks = {name: entry["index"] for name, entry in domain["landmarks"].items()}
    for name, entry in domain["landmarks"].items():
        if cells[entry["index"]] != entry["cell"]:
            raise FixtureError(f"landmark {name} index mismatch")
    return {
        "source": source_bytes.decode("utf-8"),
        "source_sha256": source_sha,
        "artifact_sha256": sha256_bytes(artifact_path.read_bytes()),
        "domain_sha256": sha256_bytes(domain_path.read_bytes()),
        "cells": cells,
        "roles": [row["role"] for row in rows],
        "labels": [row["label"] for row in rows],
        "n": n,
        "m": m,
        "u": u,
        "a_num": a_num,
        "a_den": a_den,
        "b_num": b_num,
        "b_den": b_den,
        "d_num": d_num,
        "d_den": d_den,
        "e_num": e_num,
        "e_den": e_den,
        "c": c_values,
        "relations": relations,
        "adjacency": adjacency,
        "landmarks": landmarks,
        "observation_labels": domain["observation_labels"],
    }


def river_moves(data: dict[str, Any]) -> list[list[tuple[int, int]]]:
    """Outgoing ``(action, target)`` river moves of every cell."""
    moves: list[list[tuple[int, int]]] = [[] for _ in range(data["n"])]
    for name, targets in data["relations"].items():
        for source, target in enumerate(targets):
            if target is not None:
                moves[source].append((RELATION_ACTION[name], target))
    return moves


def derived_facts(data: dict[str, Any]) -> dict[str, Any]:
    """Arrival bound, homing plan and the exact first Bayes update."""
    n = data["n"]
    moves = river_moves(data)
    home = data["landmarks"]["home"]
    undirected = [set() for _ in range(n)]
    for source, outgoing in enumerate(moves):
        for _, target in outgoing:
            undirected[source].add(target)
            undirected[target].add(source)
    distance = {home: 0}
    queue = deque([home])
    while queue:
        cell = queue.popleft()
        for other in sorted(undirected[cell]):
            if other not in distance:
                distance[other] = distance[cell] + 1
                queue.append(other)
    if len(distance) != n:
        raise FixtureError("river moves do not connect every cell to home")
    home_dist = [distance[cell] for cell in range(n)]
    start_support = [cell for cell in range(n) if data["d_num"][cell]]
    bound = min(home_dist[cell] for cell in start_support)
    start = min(start_support, key=lambda cell: (home_dist[cell], cell))
    plan, path, current = [], [], start
    while current != home:
        action, target = min(
            (
                (action, target)
                for action, target in moves[current]
                if home_dist[target] == home_dist[current] - 1
            ),
            key=lambda item: item[1],
        )
        if data["b_num"][action][current][target] == 0:
            raise FixtureError("homing step has zero transition mass")
        plan.append(action)
        path.append(target)
        current = target
    first_obs = next(
        index
        for index, label in enumerate(data["observation_labels"])
        if label == "marine|faint"
    )
    joint = [data["d_num"][cell] * data["a_num"][first_obs][cell] for cell in range(n)]
    evidence = Fraction(sum(joint), data["d_den"] * data["a_den"])
    sea = data["landmarks"]["sea"]
    return {
        "home_dist": home_dist,
        "bound": bound,
        "start": start,
        "plan": plan,
        "path": path,
        "first_obs": first_obs,
        "joint_sum": sum(joint),
        "evidence": evidence,
        "posterior_sea": Fraction(joint[sea], sum(joint)),
    }


# --------------------------------------------------------------------------- Lean


def render_instance(data: dict[str, Any], facts: dict[str, Any]) -> str:
    """Return the generated Lean instance text."""
    n, m, u = data["n"], data["m"], data["u"]
    landmarks = data["landmarks"]
    document = render_document(parse_gnn(data["source"]))
    landmark_ids = " ∧\n      ".join(
        f"cellId {name_lean} = {lean_string(data['cells'][landmarks[key]])}"
        for key, name_lean in (
            ("sea", "sea"),
            ("outlet", "outlet"),
            ("decoy_confluence", "decoyConfluence"),
            ("natal_confluence", "natalConfluence"),
            ("home", "home"),
        )
    )
    chain = "rfl"
    for action, target in reversed(list(zip(facts["plan"], facts["path"]))):
        chain = f"⟨{target}, transition_pos (by decide), {chain}⟩"
    del action
    evidence, posterior = facts["evidence"], facts["posterior_sea"]
    sea = landmarks["sea"]
    return f"""import CascadiaGeo.TypedGeospatial
import FepSketches.gnn_denotation

/-!
# Smith River salmon homing: the generated Cascadia instance

Generated by `specs/cascadia-geo-act-proof/generate_probe.py`; do not edit.

Inputs (SHA-256):
- GNN v1 source `smith_river_homing.gnn.md`: `{data["source_sha256"]}`
- `gnn-geo-infer/1` artifact `smith_river_homing.geo-infer.json`: `{data["artifact_sha256"]}`
- typed-network sidecar `smith_river_homing.domain.json`: `{data["domain_sha256"]}`

The B, A, D and E tables are the artifact's own numbers times their
power-of-two denominators (B·{data["b_den"]}, A·{data["a_den"]}, D·{data["d_den"]}, E·{data["e_den"]}); every
entry is an exact natural number. The typed river relations and the H3
adjacency table come from the sidecar, which GEO-INFER-ACT computed with
`h3` 4.5; Lean checks the artifact's kernels against them but does not
recompute H3 geometry. Preferences enter as `softmax C` because GNN, the
GEO-INFER contract and pymdp carry `C` as log-preferences.
-/

namespace CascadiaGeo.SmithRiverHoming

open FEP FEP.ActiveInference FEP.ControlledMarkov FEP.FiniteInformation
open FEP.GnnDocument FEP.GnnDenotation CascadiaGeo Finset
open scoped BigOperators

/-- Hidden state: the {n} H3 resolution-8 cells, in artifact `state_ids` order. -/
abbrev Cell := Fin {n}
/-- Observation: {m} outcomes, index `3 * habitat + odor`. -/
abbrev Obs := Fin {m}
/-- One-step policies: hold, downstream, upstream, turn. -/
abbrev Act := Fin {u}

/-! ## Typed cells -/

/-- H3 cell identifiers in state order. -/
def cellIds : List String := {lean_list([lean_string(cell) for cell in data["cells"]])}

/-- The H3 identifier of a cell. -/
def cellId (c : Cell) : String := cellIds.getD c.val ""

theorem cellId_injective : ∀ c c' : Cell, cellId c = cellId c' → c = c' := by
  decide +kernel

/-- Pacific Ocean cell offshore of the mouth. -/
def sea : Cell := {landmarks["sea"]}
/-- Smith River mouth. -/
def outlet : Cell := {landmarks["outlet"]}
/-- Main-stem cell where lower Tryon Creek joins. -/
def decoyConfluence : Cell := {landmarks["decoy_confluence"]}
/-- Main-stem cell where Rowdy Creek joins. -/
def natalConfluence : Cell := {landmarks["natal_confluence"]}
/-- Uppermost selected Rowdy Creek cell. -/
def home : Cell := {landmarks["home"]}

theorem landmark_ids :
    {landmark_ids} := by
  decide +kernel

/-! ## Typed river relations and H3 adjacency (sidecar) -/

/-- Downstream successor of each cell. -/
def successorTable : List (Option ℕ) := {lean_list([None if t is None else ("some", t) for t in data["relations"]["successor"]])}
/-- Continuation of the same stream upstream. -/
def upstreamTable : List (Option ℕ) := {lean_list([None if t is None else ("some", t) for t in data["relations"]["upstream"]])}
/-- First cell of the stream joining at each cell. -/
def sideTable : List (Option ℕ) := {lean_list([None if t is None else ("some", t) for t in data["relations"]["side"]])}

/-- Whether `table` relates `c` to `c'`. -/
def relates (table : List (Option ℕ)) (c c' : Cell) : Bool :=
  table.getD c.val none == some c'.val

/-- One river move: downstream, upstream along the same stream, or a turn. -/
def riverStep (c c' : Cell) : Bool :=
  relates successorTable c c' || relates upstreamTable c c' || relates sideTable c c'

/-- H3 neighbors of each cell inside the domain (from `h3.are_neighbor_cells`). -/
def h3NeighborTable : List (List ℕ) := {lean_list(data["adjacency"])}

/-- H3 adjacency restricted to the domain. -/
def h3Adjacent (c c' : Cell) : Bool :=
  (h3NeighborTable.getD c.val []).contains c'.val

theorem h3Adjacent_symm : ∀ c c' : Cell, h3Adjacent c c' = h3Adjacent c' c := by
  decide +kernel

theorem h3Adjacent_irrefl : ∀ c : Cell, h3Adjacent c c = false := by
  decide +kernel

/-- Every river move joins H3 neighbors. -/
theorem riverStep_h3Adjacent : ∀ c c' : Cell, riverStep c c' = true → h3Adjacent c c' = true := by
  decide +kernel

/-- Hop distance to `home` along river moves (computed by the generator). -/
def homeDistTable : List ℕ := {lean_list(facts["home_dist"])}

/-- Hop distance to `home`. -/
def homeDist (c : Cell) : ℕ := homeDistTable.getD c.val 0

theorem homeDist_home : homeDist home = 0 := by decide

/-- River moves change the distance to home by at most one. -/
theorem homeDist_lipschitz :
    ∀ c c' : Cell, riverStep c c' = true → homeDist c ≤ homeDist c' + 1 := by
  decide +kernel

/-! ## Exact artifact tables -/

/-- `B[next][previous][action] · {data["b_den"]}`, stored as `[action][previous][next]`. -/
def bTable : List (List (List ℕ)) := {lean_list(data["b_num"])}
/-- `A[observation][state] · {data["a_den"]}`. -/
def aTable : List (List ℕ) := {lean_list(data["a_num"])}
/-- `D · {data["d_den"]}`. -/
def dTable : List ℕ := {lean_list(data["d_num"])}
/-- `E · {data["e_den"]}`. -/
def eTable : List ℕ := {lean_list(data["e_num"])}
/-- Log-preferences `C`, exact. -/
def cTable : List ℚ := {lean_list(data["c"])}

/-- Transition numerator `{data["b_den"]} · B[next][previous][action]`. -/
def bNum (a : Act) (c c' : Cell) : ℕ := ((bTable.getD a.val []).getD c.val []).getD c'.val 0
/-- Likelihood numerator `{data["a_den"]} · A[observation][state]`. -/
def aNum (o : Obs) (s : Cell) : ℕ := (aTable.getD o.val []).getD s.val 0
/-- Initial-state numerator `{data["d_den"]} · D`. -/
def dNum (c : Cell) : ℕ := dTable.getD c.val 0
/-- Habit numerator `{data["e_den"]} · E`. -/
def eNum (a : Act) : ℕ := eTable.getD a.val 0
/-- Log-preference of an observation. -/
noncomputable def cPref (o : Obs) : ℝ := ((cTable.getD o.val 0 : ℚ) : ℝ)

theorem bNum_col_sum : ∀ (a : Act) (c : Cell), ∑ c', bNum a c c' = {data["b_den"]} := by
  decide +kernel

theorem aNum_col_sum : ∀ s : Cell, ∑ o, aNum o s = {data["a_den"]} := by
  decide +kernel

theorem dNum_sum : ∑ c, dNum c = {data["d_den"]} := by
  decide +kernel

theorem eNum_sum : ∑ a, eNum a = {data["e_den"]} := by
  decide +kernel

/-- Positive transition mass only stays put or makes one river move. -/
theorem bNum_local :
    ∀ (a : Act) (c c' : Cell), bNum a c c' ≠ 0 → c' = c ∨ riverStep c c' = true := by
  decide +kernel

/-- Every cell the prior can start in is at least {facts["bound"]} river moves from home. -/
theorem dNum_far : ∀ c : Cell, dNum c ≠ 0 → {facts["bound"]} ≤ homeDist c := by
  decide +kernel

/-! ## The finite carrier -/

theorem cast_sum_div {{ι : Type*}} [Fintype ι] (f : ι → ℕ) (n : ℕ) (d : ℝ)
    (h : ∑ i, f i = n) : ∑ i, (f i : ℝ) / d = n / d := by
  rw [← Finset.sum_div, ← Nat.cast_sum, h]

/-- Transition kernel of one policy, read from the artifact. -/
noncomputable def transition (a : Act) : FiniteKernel Cell Cell where
  mass c c' := (bNum a c c' : ℝ) / {data["b_den"]}
  nonneg _ _ := by positivity
  sum_one c := by rw [cast_sum_div _ {data["b_den"]} _ (bNum_col_sum a c)]; norm_num

/-- Observation likelihood, read from the artifact. -/
noncomputable def likelihood : FiniteKernel Cell Obs where
  mass s o := (aNum o s : ℝ) / {data["a_den"]}
  nonneg _ _ := by positivity
  sum_one s := by rw [cast_sum_div _ {data["a_den"]} _ (aNum_col_sum s)]; norm_num

/-- Initial-state law `D`. -/
noncomputable def initial : FiniteLaw Cell where
  mass c := (dNum c : ℝ) / {data["d_den"]}
  nonneg _ := by positivity
  sum_one := by rw [cast_sum_div _ {data["d_den"]} _ dNum_sum]; norm_num

/-- Habit `E` over one-step policies. -/
noncomputable def habit : FiniteLaw Act where
  mass a := (eNum a : ℝ) / {data["e_den"]}
  nonneg _ := by positivity
  sum_one := by rw [cast_sum_div _ {data["e_den"]} _ eNum_sum]; norm_num

/-- The GNN artifact as a finite generative model; preferences are `softmax C`. -/
noncomputable def model : GenerativeModel Act Cell Obs where
  initialState := initial
  transition := transition
  likelihood := likelihood
  preferences := softmaxLaw cPref
  policyPrior := habit

/-- Every policy's kernel is local for river moves, hence for H3 adjacency. -/
theorem transition_local (a : Act) :
    IsLocal (fun c c' => riverStep c c' = true) (model.transition a) := by
  intro c c' h
  apply bNum_local a c c'
  intro hz
  apply h
  show (bNum a c c' : ℝ) / {data["b_den"]} = 0
  rw [hz]
  simp

/-! ## Light cone: no plan reaches home in fewer than {facts["bound"]} steps, and {facts["bound"]} suffice -/

/-- Every open-loop plan shorter than {facts["bound"]} steps predicts exactly zero mass at
home, whatever its actions. -/
theorem homing_lower_bound (plan : List Act) (hshort : plan.length < {facts["bound"]}) :
    plannedState model plan home = 0 := by
  apply plannedState_eq_zero_of_potential model transition_local homeDist
    homeDist_lipschitz home plan
  intro c hc
  have hd : dNum c ≠ 0 := by
    intro hz
    apply hc
    show (dNum c : ℝ) / {data["d_den"]} = 0
    rw [hz]
    simp
  have hfar := dNum_far c hd
  rw [homeDist_home]
  omega

/-- A shortest homing plan from the mouth ({", ".join(ACTIONS[a] for a in facts["plan"])}). -/
def homingPlan : List Act := {lean_list(facts["plan"])}

theorem homingPlan_length : homingPlan.length = {facts["bound"]} := rfl

theorem transition_pos {{a : Act}} {{c c' : Cell}} (h : bNum a c c' ≠ 0) :
    0 < model.transition a c c' := by
  show 0 < (bNum a c c' : ℝ) / {data["b_den"]}
  have hpos : (0 : ℝ) < bNum a c c' := by exact_mod_cast Nat.pos_of_ne_zero h
  positivity

/-- The homing plan has a positive chain from the mouth to home. -/
theorem homingPlan_chain : Chain model homingPlan outlet home :=
  {chain}

/-- The bound is tight: the {facts["bound"]}-step homing plan reaches home with positive mass. -/
theorem homing_bound_tight : 0 < plannedState model homingPlan home := by
  have houtlet : dNum outlet = {data["d_num"][facts["start"]]} := by decide
  apply plannedState_pos_of_chain model homingPlan outlet home _ homingPlan_chain
  show (0 : ℝ) < (dNum outlet : ℝ) / {data["d_den"]}
  rw [houtlet]
  norm_num

/-! ## Exact first Bayes update -/

/-- The first observation of the reference run: marine habitat, faint natal odor. -/
def firstObs : Obs := {facts["first_obs"]}

theorem first_evidence :
    model.likelihood.predictive model.initialState firstObs = {evidence.numerator} / {evidence.denominator} := by
  show ∑ x, (dNum x : ℝ) / {data["d_den"]} * ((aNum firstObs x : ℝ) / {data["a_den"]}) =
    {evidence.numerator} / {evidence.denominator}
  have h : ∀ x, (dNum x : ℝ) / {data["d_den"]} * ((aNum firstObs x : ℝ) / {data["a_den"]}) =
      ((dNum x * aNum firstObs x : ℕ) : ℝ) / {data["d_den"] * data["a_den"]} := by
    intro x
    push_cast
    ring
  have hsum : ∑ x, dNum x * aNum firstObs x = {facts["joint_sum"]} := by
    decide +kernel
  simp_rw [h]
  rw [cast_sum_div _ {facts["joint_sum"]} _ hsum]
  norm_num

theorem first_evidence_pos :
    0 < model.likelihood.predictive model.initialState firstObs := by
  rw [first_evidence]
  norm_num

/-- Exact posterior on the sea cell after the first observation. -/
theorem first_posterior_sea :
    model.likelihood.posterior model.initialState firstObs first_evidence_pos sea =
      {posterior.numerator} / {posterior.denominator} := by
  show (dNum sea : ℝ) / {data["d_den"]} * ((aNum firstObs sea : ℝ) / {data["a_den"]}) /
      model.likelihood.predictive model.initialState firstObs = {posterior.numerator} / {posterior.denominator}
  rw [first_evidence]
  have hd : dNum sea = {data["d_num"][sea]} := by decide
  have ha : aNum firstObs sea = {data["a_num"][facts["first_obs"]][sea]} := by decide
  rw [hd, ha]
  norm_num

/-! ## pymdp 1.0.3 bridge at every belief -/

/-- For every current belief `q`, risk plus ambiguity equals `log Σ exp C` minus
pymdp's one-step negative expected free energy. -/
theorem efe_bridge (q : FiniteLaw Cell) (π : Act) :
    risk (withInitialState model q) π + ambiguity (withInitialState model q) π =
      logPartition cPref - pymdpNegEFE (withInitialState model q) cPref π :=
  risk_add_ambiguity_eq_logPartition_sub_pymdpNegEFE _ cPref rfl π

/-- For every current belief, pymdp's policy posterior is the control posterior
of risk plus ambiguity under the habit. -/
theorem policy_posterior_bridge (q : FiniteLaw Cell) (γ : ℝ) :
    controlPosterior habit γ
        (fun π => risk (withInitialState model q) π + ambiguity (withInitialState model q) π) =
      controlPosterior habit γ (fun π => -pymdpNegEFE (withInitialState model q) cPref π) :=
  controlPosterior_riskAmbiguity_eq_pymdp (withInitialState model q) cPref rfl γ

/-! ## The GNN source as a typed Q1 document -/

/-- Transcription of `smith_river_homing.gnn.md` into the Q1 AST. Payloads are
the verbatim `InitialParameterization` literals. -/
def cascadiaDoc : GnnDocument where
  sections :=
    {document}

theorem cascadiaDoc_wellFormed : WellFormed cascadiaDoc := by
  decide +kernel

/-- The GNN declarations have exactly the carrier cardinalities. -/
theorem cascadiaDoc_dims :
    declDims cascadiaDoc "A" = some [Fintype.card Obs, Fintype.card Cell] ∧
      declDims cascadiaDoc "B" = some [Fintype.card Cell, Fintype.card Cell, Fintype.card Act] ∧
      declDims cascadiaDoc "C" = some [Fintype.card Obs] ∧
      declDims cascadiaDoc "D" = some [Fintype.card Cell] ∧
      declDims cascadiaDoc "E" = some [Fintype.card Act] := by
  simp only [Fintype.card_fin]
  decide +kernel

/-- The source binds `C` to log-preferences, not to a normalized law. -/
theorem cascadiaDoc_logPreferences :
    bindsTerm cascadiaDoc "C" "LogPreferenceVector" = true ∧
      bindsTerm cascadiaDoc "C" "Preferences" = false := by
  decide +kernel

/-- Hence the normalized-`C` Q2 denotation does not apply to this document,
whatever the payload: the `softmax C` carrier above is the bridge. -/
theorem cascadiaDoc_not_discreteConforms (nums : DiscretePayload Cell Obs Act) :
    ¬ DiscreteConforms cascadiaDoc nums := by
  intro h
  have hbind := h.ontologyFields "C" "Preferences" (by decide)
  rw [cascadiaDoc_logPreferences.2] at hbind
  exact Bool.false_ne_true hbind

end CascadiaGeo.SmithRiverHoming
"""


def render_manifest(
    texts: dict[str, str], data: dict[str, Any], facts: dict[str, Any]
) -> str:
    """Digest manifest binding inputs, tooling and outputs."""
    manifest = {
        "schema_version": "fep-lean/cascadia-geo-act-proof/1",
        "inputs": {
            path.name: sha256_bytes(path.read_bytes())
            for path in (SOURCE, ARTIFACT, DOMAIN)
        },
        "tooling": {
            "generate_probe.py": sha256_bytes(Path(__file__).read_bytes()),
            "lean/CascadiaGeo/TypedGeospatial.lean": sha256_bytes(THEORY.read_bytes()),
        },
        "generated": {
            name: sha256_bytes(text.encode("utf-8")) for name, text in texts.items()
        },
        "facts": {
            "cells": data["n"],
            "observations": data["m"],
            "actions": data["u"],
            "denominators": {
                "A": data["a_den"],
                "B": data["b_den"],
                "D": data["d_den"],
                "E": data["e_den"],
            },
            "home_lower_bound_steps": facts["bound"],
            "homing_plan": [ACTIONS[action] for action in facts["plan"]],
            "first_observation": data["observation_labels"][facts["first_obs"]],
            "first_evidence": f"{facts['evidence'].numerator}/{facts['evidence'].denominator}",
            "first_posterior_sea": f"{facts['posterior_sea'].numerator}/{facts['posterior_sea'].denominator}",
        },
    }
    return json.dumps(manifest, indent=1, sort_keys=True) + "\n"


def regenerate() -> dict[str, str]:
    """Return every generated file's text, keyed by slice-relative path."""
    data = load_fixtures()
    facts = derived_facts(data)
    texts = {"generated/SmithRiverHoming.lean": render_instance(data, facts)}
    texts["generated/manifest.json"] = render_manifest(texts, data, facts)
    return texts


def main() -> int:
    """Write generated files, or verify freshness with ``--check``."""
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--check", action="store_true", help="verify committed outputs are fresh"
    )
    args = parser.parse_args()
    texts = regenerate()
    if not args.check:
        GENERATED.mkdir(parents=True, exist_ok=True)
        for name, text in texts.items():
            (SLICE / name).write_text(text, encoding="utf-8")
            print(f"wrote {name} ({len(text.encode('utf-8'))} bytes)")
        return 0
    stale = [
        name
        for name, text in texts.items()
        if not (SLICE / name).is_file()
        or (SLICE / name).read_text(encoding="utf-8") != text
    ]
    if stale:
        for name in stale:
            print(f"STALE: {name} differs from its regenerated bytes", file=sys.stderr)
        return 1
    print("OK: Cascadia generated artifacts are fresh (instance, manifest, digests)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
