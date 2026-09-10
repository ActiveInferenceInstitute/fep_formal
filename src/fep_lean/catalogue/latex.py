"""Build collision-safe display-math LaTeX for canonical topic bodies.

Each string is keyed by ``(topic_id, theorem_name)`` and is a single display
block: ``amsmath`` ``aligned`` with, in order:

1. **Namespace ``variable``** line(s) in the sketch (e.g. ``{α : Type*} [MeasurableSpace α]``),
   when present, as the first row(s) of the block.
2. **Theorem binders** (parameters and explicit hypotheses) as the next row.
3. **Conclusion** (the type after the final top-level goal colon) as the last row.

The Lean statement (before ``:=``) is parsed; proof terms, ``by``, and ``tactic`` blocks are
omitted. Symbol mapping (μ→\\mu, etc.) is heuristic; goal is the standard mathematical reading
of the sketch, not a Lean pretty-printer. The bare type name ``Measure`` is emitted with a regex
so ``\\mathsf{IsProbabilityMeasure}`` and the prefix of ``MeasureTheory`` are not rewritten
again.
"""

from __future__ import annotations

import re
from collections.abc import Mapping

from fep_lean.lean_source import lean_code_without_comments


def _extract_variable_block(body: str) -> str:
    lines = body.splitlines()
    acc: list[str] = []
    for ln in lines:
        t = ln.strip()
        if t.startswith("variable "):
            acc.append(t[len("variable ") :].strip())
        elif acc and (t.startswith(("open ", "import ", "namespace ", "/-"))):
            break
    return " ".join(acc) if acc else ""


def _extract_theorem_stmt(body: str, name: str) -> str | None:
    """Return the Lean type before its first delimiter-balanced proof ``:=``."""
    m = re.search(r"(?m)^\s*(?:theorem|lemma)\s+" + re.escape(name) + r"\b", body)
    if not m:
        return None
    rest = body[m.end() :]
    paren = brace = bracket = 0
    in_string = escaped = False
    for index, char in enumerate(rest[:-1]):
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "(":
            paren += 1
        elif char == ")":
            paren = max(paren - 1, 0)
        elif char == "{":
            brace += 1
        elif char == "}":
            brace = max(brace - 1, 0)
        elif char == "[":
            bracket += 1
        elif char == "]":
            bracket = max(bracket - 1, 0)
        elif char == ":" and rest[index + 1] == "=" and paren == brace == bracket == 0:
            return rest[:index].strip()
    return None


def _split_binders_and_goal(stmt: str) -> tuple[str, str]:
    stmt = stmt.strip()
    paren = brace = brack = 0
    last_ok = -1
    for i, ch in enumerate(stmt):
        if ch == "(":
            paren += 1
        elif ch == ")":
            paren = max(0, paren - 1)
        elif ch == "{":
            brace += 1
        elif ch == "}":
            brace = max(0, brace - 1)
        elif ch == "[":
            brack += 1
        elif ch == "]":
            brack = max(0, brack - 1)
        if paren == 0 and brace == 0 and brack == 0 and ch == ":":
            j = i - 1
            while j >= 0 and stmt[j] in " \t\n":
                j -= 1
            if j >= 0 and stmt[j] in ")]}":
                last_ok = i
    if last_ok < 0:
        m0 = re.match(r"^\s*:\s*(.+)$", stmt, re.DOTALL)
        if m0:
            return "", m0.group(1).strip()
        return stmt, ""
    return stmt[:last_ok].strip(), stmt[last_ok + 1 :].strip()


def _theorem_names_in_order(body: str) -> list[str]:
    """Theorem names in declaration order via the canonical header regex."""
    from fep_lean.lean_source import LEAN_THEOREM_RE

    return LEAN_THEOREM_RE.findall(body)


_LEAN_IDENTIFIER_RE = re.compile(
    r"(?<![\w'])([A-Za-z][A-Za-z0-9_']*(?:\.[A-Za-z][A-Za-z0-9_']*)*)(?![\w'])"
)
_SEMANTIC_IDENTIFIERS = frozenset(
    {
        "Bool",
        "Disjoint",
        "ENNReal",
        "Enumerable",
        "Equiv",
        "Finset",
        "IsProbabilityMeasure",
        "List",
        "List.nil",
        "Measure",
        "Measurable",
        "MeasurableSet",
        "MeasurableSpace",
        "MeasureTheory",
        "Monotone",
        "NNReal",
        "Nat",
        "OrderDual",
        "Prod.fst",
        "Prod.snd",
        "Real",
        "Set",
        "Set.univ",
        "Type",
        "Unit",
        "fun",
        "id",
        "log",
        "ln",
        "exp",
    }
)


def _protect_lean_identifiers(source: str) -> tuple[str, dict[str, str]]:
    """Protect multi-character Lean names from TeX operator rewrites."""
    protected: dict[str, str] = {}

    def replace(match: re.Match[str]) -> str:
        name = match.group(1)
        base = name.rstrip("'")
        if (
            len(base) == 1
            or name in _SEMANTIC_IDENTIFIERS
            or name.lower() in {"log", "ln", "exp"}
        ):
            return name
        marker = f"@@{1_000_000 + len(protected)}@@"
        primes = len(name) - len(base)
        escaped = base.replace("_", r"\_")
        rendered = rf"\mathsf{{{escaped}}}" + r"^{\prime}" * primes
        protected[marker] = rendered
        return marker

    return _LEAN_IDENTIFIER_RE.sub(replace, source), protected


def _convert_lean_expr(s: str) -> str:
    t = s.strip()
    application_space = "@@900000@@"
    t = re.sub(r"(?<=[\w)\]}])\s+(?=[\w(\[{])", application_space, t)
    left_brace = "@@900001@@"
    right_brace = "@@900002@@"
    # Source braces denote visible Lean binders and set notation.  Protect
    # them before adding LaTeX commands, whose own braces must remain TeX
    # grouping characters.
    t = t.replace("{", left_brace).replace("}", right_brace)
    t, protected_identifiers = _protect_lean_identifiers(t)
    t = re.sub(r"(?<![A-Za-z0-9])_(?![A-Za-z0-9])", r"\\mathord{\\_}", t)
    # These are type constructors whose dedicated conversions already insert
    # visible mathematical spacing.
    for constructor in (
        "Type",
        "Measure",
        "MeasurableSpace",
        "IsProbabilityMeasure",
        "Set",
    ):
        t = t.replace(f"{constructor}{application_space}", f"{constructor} ")
    # Normalize Lean's compound notation before its component characters.  In
    # particular, leaving Unicode subscript letters behind creates commands
    # such as ``\circₖ``, which XeLaTeX cannot parse.  The output is kept
    # deliberately ASCII-only so unsupported notation fails during catalogue
    # construction rather than late in publication rendering.
    for lean, latex in (
        ("ℝ≥0∞", r"\mathbb{R}_{\ge 0}^{\infty}"),
        ("ENNReal", r"\mathbb{R}_{\ge 0}^{\infty}"),
        ("NNReal", r"\mathbb{R}_{\ge 0}"),
        ("∀ᵐ", r"\forall^{\mathrm{a.e.}}"),
        ("=ᵐ", r"\overset{\mathrm{a.e.}}{=}"),
        ("∫⁻", r"\int^{-}"),
        ("∘ₖ", r"\mathbin{\circ_{k}}"),
        ("∘ₘ", r"\mathbin{\circ_{m}}"),
        ("⊗ₖ", r"\mathbin{\otimes_{k}}"),
        ("⊗ₘ", r"\mathbin{\otimes_{m}}"),
        ("×ₖ", r"\mathbin{\times_{k}}"),
        ("⁻¹'", r"^{-1}"),
        ("⁻¹", r"^{-1}"),
    ):
        t = t.replace(lean, latex)
    for lean, latex in (
        ("α", r"\alpha{}"),
        ("β", r"\beta{}"),
        ("γ", r"\gamma{}"),
        ("δ", r"\delta{}"),
        ("ε", r"\varepsilon{}"),
        ("ζ", r"\zeta{}"),
        ("η", r"\eta{}"),
        ("θ", r"\theta{}"),
        ("ι", r"\iota{}"),
        ("κ", r"\kappa{}"),
        ("λ", r"\lambda{}"),
        ("μ", r"\mu{}"),
        ("ν", r"\nu{}"),
        ("ξ", r"\xi{}"),
        ("ο", r"o"),
        ("π", r"\pi{}"),
        ("ρ", r"\rho{}"),
        ("σ", r"\sigma{}"),
        ("τ", r"\tau{}"),
        ("υ", r"\upsilon{}"),
        ("φ", r"\varphi{}"),
        ("χ", r"\chi{}"),
        ("ψ", r"\psi{}"),
        ("ω", r"\omega{}"),
        ("Γ", r"\Gamma{}"),
        ("Δ", r"\Delta{}"),
        ("Θ", r"\Theta{}"),
        ("Λ", r"\Lambda{}"),
        ("Ξ", r"\Xi{}"),
        ("Π", r"\Pi{}"),
        ("Σ", r"\Sigma{}"),
        ("Φ", r"\Phi{}"),
        ("Ψ", r"\Psi{}"),
        ("Ω", r"\Omega{}"),
        ("𝓒", r"\mathcal{C}"),
        ("𝓝", r"\mathcal{N}"),
        ("𝓧", r"\mathcal{X}"),
        ("𝓨", r"\mathcal{Y}"),
    ):
        t = t.replace(lean, latex)
    t = t.replace("∅", r"\varnothing")
    t = t.replace("∪", r"\cup")
    t = t.replace("∩", r"\cap")
    t = t.replace("⊆", r"\subseteq")
    t = t.replace("⊂", r"\subset")
    t = t.replace("∈", r"\in")
    t = t.replace("∉", r"\notin")
    t = t.replace("≤", r"\le")
    t = t.replace("≥", r"\ge")
    t = t.replace("≠", r"\ne")
    t = t.replace("→", r"\Rightarrow")
    t = t.replace("↦", r"\mapsto")
    t = t.replace("=>", r"\mapsto")
    t = t.replace("∀", r"\forall")
    t = t.replace("∃", r"\exists")
    t = t.replace("∧", r"\wedge")
    t = t.replace("∨", r"\vee")
    t = t.replace("¬", r"\neg{}")
    t = t.replace("⊤", r"\top")
    t = t.replace("⊥", r"\bot")
    t = t.replace("ᶜ", r"^{\mathrm{c}}")
    t = t.replace("∑", r"\sum")
    t = t.replace("∏", r"\prod")
    t = t.replace("×", r"\times")
    t = t.replace("·", r"\cdot")
    t = t.replace("∘", r"\circ")
    t = t.replace("↔", r"\leftrightarrow")
    t = t.replace("⇒", r"\Rightarrow")
    t = t.replace("↪", r"\hookrightarrow")
    t = t.replace("ℝ", r"\mathbb{R}")
    t = t.replace("ℕ", r"\mathbb{N}")
    t = t.replace("ℤ", r"\mathbb{Z}")
    t = t.replace("ℚ", r"\mathbb{Q}")
    t = t.replace("⬝", r"\;")
    t = t.replace("₀", r"_{0}")
    t = t.replace("₁", r"_{1}")
    t = t.replace("₂", r"_{2}")
    t = t.replace("₃", r"_{3}")
    t = t.replace("₄", r"_{4}")
    t = t.replace("₅", r"_{5}")
    t = t.replace("₆", r"_{6}")
    t = t.replace("₇", r"_{7}")
    t = t.replace("₈", r"_{8}")
    t = t.replace("₉", r"_{9}")
    t = t.replace("ₖ", r"_{k}")
    t = t.replace("ₘ", r"_{m}")
    t = t.replace("ᵐ", r"^{m}")
    t = t.replace("⁻", r"^{-}")
    t = re.sub(r"\bfun\b", r"\\lambda", t)
    t = t.replace("∂", r"\,\mathrm{d}\,")
    t = t.replace("†", r"^{\dagger}")
    t = t.replace("∞", r"\infty")
    t = t.replace("∫", r"\int")
    t = t.replace("≪", r"\ll")
    t = t.replace("⊗", r"\otimes")
    t = t.replace("⋃", r"\bigcup")
    t = re.sub(r"(?<!\S)\*(?!\S)", r"\\cdot", t)
    t = t.replace("Type*", r"\mathsf{Type}^{*}")
    t = t.replace("Type u", r"\mathsf{Type}~u")
    t = t.replace("Type v", r"\mathsf{Type}~v")
    t = t.replace("MeasureTheory", r"\mathsf{MeasureTheory}")
    t = t.replace("IsProbabilityMeasure", r"\mathsf{IsProbabilityMeasure}")
    t = t.replace("MeasurableSet", r"\mathsf{MeasurableSet}")
    t = t.replace("MeasurableSpace", r"\mathsf{MeasurableSpace}")
    t = t.replace("Enumerable", r"\mathsf{Enumerable}")
    t = re.sub(
        r"(?<![A-Za-z])Measurable(?!Set|Space|Theory)",
        r"\\mathsf{Measurable}",
        t,
    )
    t = t.replace("Finset", r"\mathsf{Finset}")
    t = t.replace("List.nil", r"[\,]")
    t = t.replace("List", r"\mathsf{List}")
    t = re.sub(r"(?<![A-Za-z])Set\.univ", r"\\Omega", t)
    t = re.sub(r"(?<![A-Za-z])Set\.", r"\\mathsf{Set}.", t)
    t = re.sub(r"(?<![A-Za-z])Set ", r"\\mathsf{Set}~", t)
    # Do not use ``.replace("Measure", ...)`` — it rewrites the tail of
    # ``\mathsf{IsProbabilityMeasure}`` and the prefix of ``\mathsf{MeasureTheory}``.
    t = re.sub(
        r"(?<![A-Za-z])Measure(?!T)",
        r"\\mathsf{Measure}",
        t,
    )
    t = t.replace("OrderDual", r"\mathsf{OrderDual}")
    t = t.replace("Disjoint", r"\mathsf{Disjoint}")
    t = t.replace("Monotone", r"\mathsf{Monotone}")
    t = t.replace("Equiv", r"\mathsf{Equiv}")
    t = t.replace("Prod.fst", r"\pi_1")
    t = t.replace("Prod.snd", r"\pi_2")
    t = t.replace("priorParams", r"\mathsf{priorParams}")
    t = t.replace("update", r"\mathsf{update}")
    t = t.replace("foldl", r"\mathsf{foldl}")
    t = t.replace("assign", r"\mathsf{assign}")
    t = re.sub(r"(?<![A-Za-z])Bool(?![A-Za-z])", r"\\mathsf{Bool}", t)
    t = re.sub(r"(?<![A-Za-z])Unit(?![A-Za-z])", r"\\mathsf{Unit}", t)
    t = re.sub(r"(?<![A-Za-z])Real(?![A-Za-z])", r"\\mathbb{R}", t)
    t = re.sub(r"(?<![A-Za-z])Nat(?![A-Za-z])", r"\\mathbb{N}", t)
    t = re.sub(r"(?<![A-Za-z])id(?![A-Za-z])", r"\\mathsf{id}", t)
    t = re.sub(r"(?<![A-Za-z])log(?![A-Za-z])", r"\\log", t, flags=re.IGNORECASE)
    t = re.sub(r"(?<![A-Za-z])ln(?![A-Za-z])", r"\\ln", t, flags=re.IGNORECASE)
    t = re.sub(r"(?<![A-Za-z])exp(?![A-Za-z])", r"\\exp", t, flags=re.IGNORECASE)
    t = t.replace(
        r"\mathsf{MeasurableSpace} \alpha", r"\mathsf{MeasurableSpace}~\alpha"
    )
    t = t.replace(r"\mathsf{Measure} \alpha", r"\mathsf{Measure}~\alpha")
    t = t.replace(
        r"\mathsf{IsProbabilityMeasure} \mu", r"\mathsf{IsProbabilityMeasure}~\mu"
    )
    t = re.sub(r"\\mu\s+\\varnothing", r"\\mu(\\varnothing)", t)
    t = re.sub(r"\\mu\s+\\Omega\b", r"\\mu(\\Omega)", t)
    # Ordinary whitespace is ignored in TeX math mode.  Preserve Lean
    # application boundaries explicitly so ``f x y`` does not render as the
    # misleading single identifier ``fxy`` while leaving operator spacing and
    # spaces introduced by LaTeX commands intact.
    t = t.replace(application_space, r"\,")
    t = t.replace(left_brace, r"\{").replace(right_brace, r"\}")
    for marker, rendered in protected_identifiers.items():
        t = t.replace(marker, rendered)
    remaining = sorted({char for char in t if not char.isascii()}, key=ord)
    if remaining:
        rendered = ", ".join(f"U+{ord(char):04X}" for char in remaining)
        raise ValueError(f"unconverted Lean Unicode in LaTeX expression: {rendered}")
    return t


_MAX_LATEX_ROW_CHARS = 80
_UNSAFE_ROW_END_TOKENS = frozenset(
    {
        "^",
        "_",
        "+",
        "-",
        "*",
        "/",
        "=",
        "<",
        ">",
        "<=",
        ">=",
        ":=",
        "=>",
        "≤",
        "≥",
        "≠",
        "→",
        "⇒",
        "↔",
        "∧",
        "∨",
        "∈",
        "∉",
        "⊆",
        "⊂",
    }
)
_UNSAFE_ROW_START_TOKENS = frozenset({"^", "_"})
_ROW_PREFIX_OPERATORS = _UNSAFE_ROW_END_TOKENS - _UNSAFE_ROW_START_TOKENS


def _safe_math_row_boundary(left: str, right: str) -> bool:
    """Reject line breaks that detach a TeX operator from an operand."""
    left_token = left.split()[-1]
    right_token = right.split()[0]
    return (
        left_token not in _UNSAFE_ROW_END_TOKENS
        and right_token not in _UNSAFE_ROW_START_TOKENS
    )


def _split_before_exponent_base(source: str) -> tuple[str, str]:
    """Move a complete parenthesized base with its trailing exponent marker."""
    tokens = source.split()
    if len(tokens) < 3 or tokens[-1] != "^":
        return "", source
    base_start = len(tokens) - 2
    balance = tokens[base_start].count(")") - tokens[base_start].count("(")
    while balance > 0 and base_start > 0:
        base_start -= 1
        balance += tokens[base_start].count(")")
        balance -= tokens[base_start].count("(")
    prefix = " ".join(tokens[:base_start])
    base = " ".join(tokens[base_start:])
    return prefix, base


def _math_units(source: str) -> list[str]:
    """Keep short Lean binders and lambda heads intact while wrapping."""
    raw_units = source.split()
    grouped: list[str] = []
    index = 0
    while index < len(raw_units):
        unit = raw_units[index]
        opening = sum(unit.count(char) for char in "([{")
        closing = sum(unit.count(char) for char in (")", "]", "}"))
        balance = opening - closing
        if balance > 0:
            end = index + 1
            while end < len(raw_units) and balance > 0:
                balance += sum(raw_units[end].count(char) for char in "([{")
                balance -= sum(raw_units[end].count(char) for char in ")]}")
                end += 1
            candidate = " ".join(raw_units[index:end])
            if len(candidate) <= 56:
                grouped.append(candidate)
            else:
                grouped.extend(raw_units[index:end])
            index = end
            continue
        grouped.append(unit)
        index += 1

    units: list[str] = []
    index = 0
    while index < len(grouped):
        if grouped[index].lstrip("(") in {"fun", "λ"}:
            end = index + 1
            while end < len(grouped) and grouped[end] not in {"=>", "↦"}:
                end += 1
            if end < len(grouped):
                units.append(" ".join(grouped[index : end + 1]))
                index = end + 1
                continue
        units.append(grouped[index])
        index += 1
    return units


def _converted_rows(source: str) -> list[str]:
    """Convert one Lean fragment into bounded, application-safe math rows."""
    if "@@" in source:
        # Sentinel markers must never collide with literal source text: the
        # bodies are regex-sealed, so this can only mean a drift in the seal.
        # (The converter's own @@NNNNNN@@ sentinels are injected after this
        # check, on already-validated text.)
        raise ValueError("source already contains sentinel marker '@@'")
    _convert_lean_expr(source)  # Validate the complete fragment in one pass.
    units = _math_units(source)
    if not units:
        return []
    rows: list[str] = []
    current = units[0]
    for index, unit in enumerate(units[1:], 1):
        candidate = f"{current} {unit}"
        candidate_length = len(candidate)
        if unit in _ROW_PREFIX_OPERATORS and index + 1 < len(units):
            candidate_with_operand = f"{candidate} {units[index + 1]}"
            if (
                candidate_length <= _MAX_LATEX_ROW_CHARS
                and len(candidate_with_operand) > _MAX_LATEX_ROW_CHARS
            ):
                rows.append(_convert_lean_expr(current))
                current = unit
                continue
        if candidate_length <= _MAX_LATEX_ROW_CHARS:
            current = candidate
        elif current.split()[-1] == "^":
            prefix, exponent_base = _split_before_exponent_base(current)
            if prefix and _safe_math_row_boundary(prefix, exponent_base):
                rows.append(_convert_lean_expr(prefix))
                current = f"{exponent_base} {unit}"
            else:
                current = candidate
        elif not _safe_math_row_boundary(current, unit):
            current = candidate
        else:
            rows.append(_convert_lean_expr(current))
            current = unit
    rows.append(_convert_lean_expr(current))
    return rows


def _wrap_aligned(rows: list[str]) -> str:
    if not rows:
        return r"\mathsf{?}"
    if len(rows) == 1:
        return rows[0]
    lines = [f"&{r}" for r in rows if r.strip()]
    return r"\begin{aligned}" + "\n" + " \\\\\n".join(lines) + "\n" + r"\end{aligned}"


def _one_theorem_latex(var_ctx: str, binders: str, goal: str, *, with_ctx: bool) -> str:
    rows: list[str] = []
    if with_ctx and var_ctx:
        rows.extend(_converted_rows(var_ctx))
    if binders:
        rows.extend(_converted_rows(binders))
    if goal:
        rows.extend(_converted_rows(goal))
    if not rows:
        return r"\mathsf{?}"
    return _wrap_aligned(rows)


def build_theorem_latex(
    bodies: Mapping[str, str],
) -> dict[tuple[str, str], str]:
    """Return one qualified equation per theorem and reject duplicate keys."""
    out: dict[tuple[str, str], str] = {}
    for topic_id, body in bodies.items():
        code = lean_code_without_comments(body)
        vblock = _extract_variable_block(code)
        names = _theorem_names_in_order(code)
        for name in names:
            key = (topic_id, name)
            if key in out:
                raise ValueError(f"duplicate theorem LaTeX key: {key!r}")
            stmt = _extract_theorem_stmt(code, name)
            if not stmt:
                raise ValueError(
                    f"{topic_id}: cannot extract statement for theorem {name}"
                )
            b, g = _split_binders_and_goal(stmt)
            out[key] = _one_theorem_latex(vblock, b, g, with_ctx=bool(vblock.strip()))
    return out


def build_topic_latex_equations(
    bodies: Mapping[str, str],
    equations: Mapping[tuple[str, str], str],
) -> dict[str, list[str]]:
    """Group qualified equations in exact source theorem order, consuming all keys."""
    grouped: dict[str, list[str]] = {}
    consumed: set[tuple[str, str]] = set()
    for topic_id, body in bodies.items():
        code = lean_code_without_comments(body)
        rows: list[str] = []
        for theorem_name in _theorem_names_in_order(code):
            key = (topic_id, theorem_name)
            try:
                rows.append(equations[key])
            except KeyError as exc:
                raise ValueError(f"missing theorem LaTeX key: {key!r}") from exc
            consumed.add(key)
        if not rows:
            raise ValueError(f"{topic_id}: no theorem equations were generated")
        grouped[topic_id] = rows
    unconsumed = tuple(sorted(set(equations) - consumed))
    if unconsumed:
        raise ValueError(f"unconsumed theorem LaTeX keys: {unconsumed!r}")
    return grouped


__all__ = ["build_theorem_latex", "build_topic_latex_equations"]
