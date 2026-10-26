"""Exact source-span regressions for conservative Lean statement extraction."""

import pytest

from fep_lean.lean_source import lean_theorem_header_delimiters


@pytest.mark.parametrize(
    "goal",
    [
        "True",
        "let x := 1; x = 1",
        "let x := 1\n    x = 1",
        "letI : MeasurableSpace Bool := ⊤\n    True",
        "let x := (let y := 1; y); x = 1",
        "let x := 1; let y := 2; x + y = 3",
        'let s := ":= let by"; s = ":= let by"',
        "let c := ':'; c = ':'",
        "let «have» := 1; «have» = 1",
        "let x := (by exact 1); x = 1",
        "let x := 1 /- nested /- := -/ := -/; x = 1",
    ],
)
def test_exact_supported_statement_and_proof_boundary(goal):
    source = (
        "theorem example (n : Nat := 1) :\n    "
        + goal
        + " := by\n  let proofLocal := 4\n  trivial\n"
    )
    colon, proof = lean_theorem_header_delimiters(source, len("theorem example"))
    assert source[colon + 1 : proof].strip() == goal
    assert source[proof:] == ":= by\n  let proofLocal := 4\n  trivial\n"


@pytest.mark.parametrize(
    "goal",
    [
        "let x := by have h : True := by trivial; exact 1; x = 1",
        "let x := have h : True := by trivial; 1; x = 1",
        "let x := do pure 1; True",
        "let (x,y) := (1,2); x = 1",
        "let rec f := f; True",
        "let x := fun y => have h : True := by trivial; y; True",
    ],
)
def test_unsupported_initializer_is_refused(goal):
    with pytest.raises(ValueError, match="unsupported"):
        lean_theorem_header_delimiters(
            "theorem example : " + goal + " := by trivial", len("theorem example")
        )


def test_missing_proof_cannot_consume_next_declaration():
    source = "theorem broken : True\ntheorem next : True := by trivial"
    with pytest.raises(ValueError, match="no supported proof delimiter"):
        lean_theorem_header_delimiters(source, len("theorem broken"))


def test_original_offsets_survive_comments_and_strings():
    source = (
        'theorem example (x : Nat /- := -/) : let s := ":="; s = ":=" := by trivial'
    )
    colon, proof = lean_theorem_header_delimiters(source, len("theorem example"))
    assert source[colon:proof] == ': let s := ":="; s = ":=" '


def test_anonymous_pattern_function_is_part_of_result():
    source = (
        "theorem entries : matrix = fun\n  | false => 0\n  | true => 1 := by\n  rfl"
    )
    colon, proof = lean_theorem_header_delimiters(source, len("theorem entries"))
    assert (
        source[colon + 1 : proof].strip()
        == "matrix = fun\n  | false => 0\n  | true => 1"
    )
    assert source[proof:].startswith(":= by")


def test_equation_proof_starts_at_first_clause():
    source = "theorem recurrence : ∀ n : Nat, f n = n\n  | 0 => rfl\n  | n + 1 => by\n    let x := n\n    simp"
    colon, proof = lean_theorem_header_delimiters(source, len("theorem recurrence"))
    assert source[colon + 1 : proof].strip() == "∀ n : Nat, f n = n"
    assert source[proof:].startswith("| 0 => rfl")


@pytest.mark.parametrize(
    "goal",
    [
        "match b with\n  | true => True\n  | false => True",
        "have h : True := by trivial; True",
        "by have h : True := by trivial; exact True",
    ],
)
def test_unhandled_top_level_result_grammar_is_refused(goal):
    with pytest.raises(ValueError, match="unsupported"):
        lean_theorem_header_delimiters(
            "theorem example (b : Bool) : " + goal + " := by trivial",
            len("theorem example"),
        )


def test_missing_proof_cannot_consume_next_public_declaration():
    source = "theorem broken : True\npublic theorem next : True := by trivial"
    with pytest.raises(ValueError, match="no supported proof delimiter"):
        lean_theorem_header_delimiters(source, len("theorem broken"))


def test_all_shared_conclusion_consumers_keep_let_annotation():
    from fep_lean.catalogue.latex import _extract_theorem_stmt, _split_binders_and_goal
    from fep_lean.lean_source import lean_declaration_conclusion

    source = (
        "theorem instance_case : letI : MeasurableSpace Bool := top; True := by trivial"
    )
    expected = "letI : MeasurableSpace Bool := top; True"
    assert lean_declaration_conclusion(source) == expected
    assert _split_binders_and_goal(_extract_theorem_stmt(source, "instance_case")) == (
        "",
        expected,
    )


def test_structure_where_proof_is_not_in_the_type():
    from fep_lean.lean_source import lean_declaration_conclusion

    source = (
        "theorem structure_proof (x : Nat) : Support x where\n  field := by trivial"
    )
    colon, proof = lean_theorem_header_delimiters(
        source, len("theorem structure_proof")
    )
    assert source[colon + 1 : proof].strip() == "Support x"
    assert source[proof:].startswith("where\n")
    assert lean_declaration_conclusion(source) == "Support x"


@pytest.mark.parametrize("literal", ["'\"'", "'«'", "'»'", "'('"])
def test_character_literals_cannot_change_header_state(literal):
    goal = "let c := " + literal + "; c = " + literal
    source = "theorem character_case : " + goal + " := by trivial"
    colon, proof = lean_theorem_header_delimiters(source, len("theorem character_case"))
    assert source[colon + 1 : proof].strip() == goal


def test_quoted_identifier_with_comment_tokens_is_not_a_comment():
    source = "theorem quote_case : let «/- := --» := 1; «/- := --» = 1 := by trivial"
    colon, proof = lean_theorem_header_delimiters(source, len("theorem quote_case"))
    assert source[colon + 1 : proof].strip() == "let «/- := --» := 1; «/- := --» = 1"


def test_unterminated_quoted_identifier_is_refused():
    source = "theorem broken : let «name := 1; True := by trivial"
    with pytest.raises(ValueError, match="unterminated"):
        lean_theorem_header_delimiters(source, len("theorem broken"))


@pytest.mark.parametrize(
    "goal", ["calc True := by trivial", "haveI : Inhabited Nat := inferInstance; True"]
)
def test_other_assignment_producing_term_forms_are_refused(goal):
    with pytest.raises(ValueError, match="unsupported"):
        lean_theorem_header_delimiters(
            "theorem example : " + goal + " := by trivial", len("theorem example")
        )


def test_signature_lookup_ignores_commented_duplicate_and_supports_public():
    from fep_lean.catalogue.latex import _extract_theorem_stmt

    source = "/-\ntheorem example : False := by trivial\n-/\npublic theorem example : True := by trivial"
    assert _extract_theorem_stmt(source, "example") == ": True"


@pytest.mark.parametrize(
    "actual_name", ["foo'", "fooé", "foo.bar", "foo\u0301", "foo!", "foo?"]
)
def test_unsupported_name_does_not_alias_supported_prefix(actual_name):
    from fep_lean.catalogue.latex import _extract_theorem_stmt

    source = "theorem " + actual_name + " : True := by trivial"
    assert _extract_theorem_stmt(source, "foo") is None


def test_missing_proof_stops_before_multiline_public_modifier():
    source = "theorem broken : True\npublic\n theorem next : True := by trivial"
    with pytest.raises(ValueError, match="no supported proof delimiter"):
        lean_theorem_header_delimiters(source, len("theorem broken"))


def test_private_helpers_are_not_added_to_public_query_inventory():
    from fep_lean.lean_source import LEAN_THEOREM_RE

    source = "private theorem helper : True := by trivial\npublic theorem visible : True := by trivial"
    assert [match[1] for match in LEAN_THEOREM_RE.finditer(source)] == ["visible"]


@pytest.mark.parametrize("modifier", ["private", "protected", "noncomputable"])
def test_multiline_unsupported_modifier_refuses_public_identity(modifier):
    from fep_lean.catalogue.latex import _extract_theorem_stmt

    source = modifier + "\n theorem helper : True := by trivial"
    with pytest.raises(ValueError, match="unsupported multiline"):
        _extract_theorem_stmt(source, "helper")


def test_all_reviewed_public_statement_hashes_and_corrections():
    import hashlib
    import json
    from pathlib import Path

    from fep_lean.methods import build_mathematical_positioning

    root = Path(__file__).resolve().parents[1]
    fixture = json.loads(
        (
            root / "tests/fixtures/theorem_statement_extraction_review_20261020.json"
        ).read_text()
    )
    declarations = build_mathematical_positioning(root).as_dict()["theorem_analysis"][
        "declarations"
    ]
    from tests._support.landauer_epoch import statement_view

    declarations = statement_view(declarations)
    assert len(fixture["expected_public_statement_sha256"]) == 2286
    assert len(fixture["corrections"]) == 27
    for name, expected in fixture["expected_public_statement_sha256"].items():
        assert declarations[name]["statement_sha256"] == expected
    for name, correction in fixture["corrections"].items():
        actual = declarations[name]["statement"]
        assert actual == correction["correct_statement"]
        assert (
            hashlib.sha256(actual.encode()).hexdigest()
            == correction["correct_statement_sha256"]
        )
        assert (
            correction["old_statement_sha256"] != correction["correct_statement_sha256"]
        )


def test_declaration_names_work_for_line_and_header_fragment_consumers():
    from fep_lean.lean_source import LEAN_THEOREM_RE

    for header in ["theorem example", "lemma example", "public theorem example"]:
        match = LEAN_THEOREM_RE.match(header)
        assert match is not None and match[1] == "example"


@pytest.mark.parametrize("modifier", ["public ", "public\n"])
def test_methods_proof_span_stops_before_next_public_declaration(modifier):
    from fep_lean.methods.model import _theorem_sources

    source = (
        "theorem first : True := by trivial\n"
        + modifier
        + "theorem second : True := by exact first"
    )
    records = _theorem_sources(source, "header-control.lean")
    assert set(records) == {"first", "second"}
    assert records["first"]["proof_source"] == "by trivial"
    assert records["second"]["statement"] == "theorem second : True"
    assert records["second"]["proof_source"] == "by exact first"


@pytest.mark.parametrize(
    "quoted", ["«[»", "«]»", "«(»", "«)»", "«:»", "«with space»", "«two  spaces»"]
)
def test_quoted_binder_syntax_preserves_original_name_and_goal(quoted):
    from fep_lean.catalogue.latex import _extract_theorem_stmt, _split_binders_and_goal
    from fep_lean.methods.model import _binder_groups

    source = f"theorem quoted_binder ({quoted} : Nat) : {quoted} = {quoted} := by rfl"
    statement = _extract_theorem_stmt(source, "quoted_binder")
    binders, goal = _split_binders_and_goal(statement)
    assert binders == f"({quoted} : Nat)"
    assert goal == f"{quoted} = {quoted}"
    groups = _binder_groups(binders)
    assert groups[0]["names"] == [quoted]
    assert groups[0]["source"] == binders
    assert groups[0]["type_source"] == "Nat"


def test_binder_names_preserve_mixed_quoted_unicode_and_prime_identifiers():
    from fep_lean.methods.model import _binder_groups

    assert _binder_groups("(ordinary α x' «with space» : Nat)")[0]["names"] == [
        "ordinary",
        "α",
        "x'",
        "«with space»",
    ]
