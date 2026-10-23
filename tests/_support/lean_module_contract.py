"""Exact current Lean module headers and source-only closure extraction."""

from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path

from fep_lean.lean_source import lean_code_without_comments


def _header(imports: tuple[str, ...]) -> str:
    return (
        "module\n"
        + "".join(f"public import {dependency}\n" for dependency in imports)
        + "\n@[expose] public section\n"
    )


def assert_exposed_module_header(source: str, imports: tuple[str, ...]) -> None:
    """Pin the module boundary, exact ordered public imports and exposed scope."""
    assert source.startswith(_header(imports))
    code = lean_code_without_comments(source)
    assert tuple(re.findall(r"(?m)^public import (\S+)$", code)) == imports
    assert not re.search(r"(?m)^import\s", code)
    assert len(re.findall(r"(?m)^module$", code)) == 1


def exposed_module_body(source: str, imports: tuple[str, ...]) -> str:
    """Extract a verified dependency body for inlining in one outer module.

    The caller retains the outer module's imports and exposed public section.
    Topic bodies use legacy imports and are deliberately outside this helper.
    """
    assert_exposed_module_header(source, imports)
    return source.removeprefix(_header(imports))


def topic_projection_sources(aggregate: Path) -> tuple[tuple[Path, str], ...]:
    """Read topic-bearing files named by actual imports, without generator metadata."""
    text = aggregate.read_text(encoding="utf-8")
    names = re.findall(
        r"(?m)^public import FepSketches\.families\.([a-z][a-z0-9_]*)$",
        lean_code_without_comments(text),
    )
    if not names:
        return ((aggregate, text),)
    assert len(names) == len(set(names)), "duplicate family imports"
    return tuple(
        (path, path.read_text(encoding="utf-8"))
        for name in names
        for path in [aggregate.parent / "families" / (name + ".lean")]
    )


def topic_projection_text(aggregate: Path) -> str:
    """Read the actual imported topic sources as one source-only inspection view."""
    return "\n".join(text for _, text in topic_projection_sources(aggregate))


def topic_namespace_owner_modules(aggregate: Path) -> dict[str, str]:
    """Resolve namespace owners from actual generated files, not registry metadata."""
    owners: dict[str, str] = {}
    for path, text in topic_projection_sources(aggregate):
        module = "FepSketches." + ".".join(
            path.relative_to(aggregate.parent).with_suffix("").parts
        )
        for namespace in re.findall(
            r"(?m)^namespace (fep_fep\d+)\s*$", lean_code_without_comments(text)
        ):
            assert namespace not in owners, f"duplicate topic owner: {namespace}"
            owners[namespace] = module
    return owners


_EXACT_INFORMATION_REVIEW_SHA256 = (
    "e6f5c12d6843b04d1ae85f8b7157bc7da55b2c6de7227b24158227882f069d6c"
)


def exact_information_review(project_root: Path) -> dict:
    """Authenticate the new review without changing historical seal fixtures."""
    path = project_root / "tests/fixtures/exact_information_review_20261020.json"
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == _EXACT_INFORMATION_REVIEW_SHA256
    review = json.loads(raw)
    assert review["schema_version"] == 1
    assert review["topic_roster_count"] == 168
    assert review["formal_module_count"] == 72
    assert review["semantic_dispositions_changed"] is False
    assert len(review["edge_changes"]) == 7
    assert len(review["capability_changes"]) == 2
    assert len(review["new_theorem_owners"]) == 35
    return review


def reverse_information_entries(
    entries: list[dict[str, object]], project_root: Path, *, capabilities: bool = False
) -> list[dict[str, object]]:
    """Reverse only exact reviewed complete rows before applying older seals."""
    review = exact_information_review(project_root)
    changes = review["capability_changes" if capabilities else "edge_changes"]

    def key(row: dict) -> object:
        return row["id"] if capabilities else (row["source"], row["target"])

    expected = {key(change["reviewed"]): change for change in changes}
    assert len(expected) == len(changes)
    seen = set()
    restored = []
    for row in entries:
        identity = key(row)
        if identity in expected:
            assert identity not in seen
            seen.add(identity)
            change = expected[identity]
            assert row == change["reviewed"]
            restored.append(dict(change["released"]))
        else:
            restored.append(dict(row))
    assert seen == set(expected)
    return restored


def restore_information_owner(source: str, owner: str, project_root: Path) -> str:
    """Require every current byte, remove approved additions, and hash its preimage."""
    if owner == "src/fep_lean/formal/variational_duality.lean":
        source = restore_finite_rate_distortion_owner(source, project_root)
    if owner == "src/fep_lean/formal/compositions/core.lean":
        source = restore_obligation_core(source, project_root)
    change = exact_information_review(project_root)["owner_changes"][owner]
    assert hashlib.sha256(source.encode()).hexdigest() == change["reviewed_sha256"]
    for addition in [*change["added_imports"], change["added_block"]]:
        assert source.count(addition) == 1
        source = source.replace(addition, "", 1)
    assert hashlib.sha256(source.encode()).hexdigest() == change["released_sha256"]
    return source


_FINITE_RATE_DISTORTION_REVIEW_SHA256 = (
    "72203e995cfa96d7726b244d950f8a1bebb34a2879754d67a59170d948cc0a22"
)


def finite_rate_distortion_review(project_root: Path) -> dict:
    raw = (
        project_root / "tests/fixtures/finite_rate_distortion_review_20261022.json"
    ).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == _FINITE_RATE_DISTORTION_REVIEW_SHA256
    review = json.loads(raw)
    assert review["schema_version"] == 1
    assert len(review["new_theorem_owners"]) == 39
    assert len(review["capability_changes"]) == 1
    return review


def reverse_finite_rate_distortion_capabilities(
    rows: list[dict], project_root: Path
) -> list[dict]:
    changes = finite_rate_distortion_review(project_root)["capability_changes"]
    restored = [dict(row) for row in rows]
    for change in changes:
        indices = [i for i, row in enumerate(restored) if row.get("id") == change["id"]]
        assert len(indices) == 1
        index = indices[0]
        assert restored[index] == change["after"]
        restored[index] = dict(change["before"])
    return restored


def restore_finite_rate_distortion_owner(source: str, project_root: Path) -> str:
    review = finite_rate_distortion_review(project_root)
    for addition in [review["added_import"], review["added_block"]]:
        assert source.count(addition) == 1
        source = source.replace(addition, "", 1)
    assert hashlib.sha256(source.encode()).hexdigest() == review["prior_owner_sha256"]
    return source


def finite_rate_distortion_theorem_extension(
    declarations: dict, project_root: Path
) -> set[str]:
    owners = finite_rate_distortion_review(project_root)["new_theorem_owners"]
    assert owners.keys() <= declarations.keys()
    assert {name: declarations[name]["source_owner"] for name in owners} == owners
    return set(owners)


_OBLIGATION_REVIEW_SHA256 = (
    "7f5f85fde16ed8e62aee4b4ac39ad492949f703c5599246a068ec01055aa2719"
)


def obligation_review(project_root: Path) -> dict:
    raw = (
        project_root / "tests/fixtures/conceptual_obligations_review_20261022.json"
    ).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == _OBLIGATION_REVIEW_SHA256
    review = json.loads(raw)
    assert review["schema_version"] == 1
    assert len(review["edge_changes"]) == 7
    assert (
        len(
            {
                (c["before"]["source"], c["before"]["target"])
                for c in review["edge_changes"]
            }
        )
        == 7
    )
    return review


def reverse_obligation_edges(edges: list[dict], project_root: Path) -> list[dict]:
    restored = copy.deepcopy(edges)
    for change in obligation_review(project_root)["edge_changes"]:
        key = (change["after"]["source"], change["after"]["target"])
        positions = [
            i
            for i, edge in enumerate(restored)
            if (edge["source"], edge["target"]) == key
        ]
        assert len(positions) == 1
        position = positions[0]
        if key == ("fep-016", "fep-032"):
            # Test-only inverse of one authenticated spelling-only successor.
            # The frozen review and its exact original rows remain unchanged.
            assert change["after"]["rationale"] == (
                "The checked conjunction places nonnegative precision-weighted "
                "quadratic energy beside bounded-step scalar energy descent on "
                "the same state and centre. It asserts neither a Laplace "
                "approximation nor a derivation or general optimizer theorem."
            )
            american_after = copy.deepcopy(change["after"])
            american_after["rationale"] = (
                "The checked conjunction places nonnegative precision-weighted "
                "quadratic energy beside bounded-step scalar energy descent on "
                "the same state and center. It asserts neither a Laplace "
                "approximation nor a derivation or general optimizer theorem."
            )
            assert restored[position] in (change["after"], american_after)
        else:
            assert restored[position] == change["after"]
        restored[position] = copy.deepcopy(change["before"])
    return restored


def reverse_obligation_model(model: dict, project_root: Path) -> dict:
    assert type(model["schema_version"]) is int and model["schema_version"] == 3
    restored = copy.deepcopy(model)
    restored["schema_version"] = 2
    restored["edges"] = reverse_obligation_edges(model["edges"], project_root)
    return restored


def restore_obligation_core(source: str, project_root: Path) -> str:
    review = obligation_review(project_root)
    block = review["added_core_block"]
    assert source.count(block) == 1
    restored = source.replace(block, "", 1)
    assert hashlib.sha256(restored.encode()).hexdigest() == review["base_core_sha256"]
    return restored


def obligation_theorem_extension(declarations: dict, project_root: Path) -> set[str]:
    owners = obligation_review(project_root)["new_theorem_owners"]
    assert owners.keys() <= declarations.keys()
    assert {name: declarations[name]["source_owner"] for name in owners} == owners
    return set(owners)


_PRIMARY_ALIGNMENT_REVIEW_SHA256 = (
    "d8111a50ec6ded5d5b0a7657408314c01b1b7bab9b9969392d29dc7dd17dd311"
)


def primary_alignment_review(project_root: Path) -> dict:
    raw = (
        project_root / "tests/fixtures/primary_alignment_review_20261022.json"
    ).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == _PRIMARY_ALIGNMENT_REVIEW_SHA256
    review = json.loads(raw)
    assert review["schema_version"] == 1
    assert [x["id"] for x in review["body_changes"]] == ["fep-063"]
    assert [x["id"] for x in review["maturity_changes"]] == ["fep-063", "fep-064"]
    assert len(review["old_declaration_statement_sha256"]) == 2326
    assert set(review["old_declaration_statement_sha256"]) == set(
        review["old_declaration_owners"]
    )
    assert len(review["new_theorem_owners"]) == 1
    return review


def restore_primary_alignment_bodies(bodies: dict, project_root: Path) -> dict:
    restored = dict(bodies)
    for change in primary_alignment_review(project_root)["body_changes"]:
        assert restored[change["id"]] == change["after"]
        restored[change["id"]] = change["before"]
    return restored


def reverse_primary_alignment_rows(rows: list[dict], project_root: Path) -> list[dict]:
    restored = copy.deepcopy(rows)
    for change in primary_alignment_review(project_root)["maturity_changes"]:
        positions = [i for i, row in enumerate(restored) if row["id"] == change["id"]]
        assert len(positions) == 1
        assert restored[positions[0]] == change["after"]
        restored[positions[0]] = copy.deepcopy(change["before"])
    return restored


def reverse_primary_alignment_raw(raw: bytes, project_root: Path) -> bytes:
    review = primary_alignment_review(project_root)
    assert hashlib.sha256(raw).hexdigest() == review["reviewed_maturity_sha256"]
    for change in review["maturity_changes"]:
        current = change["raw_after"].encode()
        assert raw.count(current) == 1
        raw = raw.replace(current, change["raw_before"].encode(), 1)
    assert hashlib.sha256(raw).hexdigest() == review["prior_maturity_sha256"]
    return raw


def restore_primary_alignment_owner(source: str, project_root: Path) -> str:
    review = primary_alignment_review(project_root)
    assert source == review["owner_after"]
    restored = review["owner_before"]
    assert hashlib.sha256(restored.encode()).hexdigest() == review["prior_owner_sha256"]
    return restored


def primary_alignment_theorem_extension(
    declarations: dict, project_root: Path
) -> set[str]:
    review = primary_alignment_review(project_root)
    for name, digest in review["old_declaration_statement_sha256"].items():
        assert name in declarations
        assert (
            hashlib.sha256(declarations[name]["statement"].encode()).hexdigest()
            == digest
        )
        assert (
            declarations[name]["source_owner"] == review["old_declaration_owners"][name]
        )
    owners = review["new_theorem_owners"]
    assert owners.keys() <= declarations.keys()
    for name, digest in review["new_declaration_statement_sha256"].items():
        assert (
            hashlib.sha256(declarations[name]["statement"].encode()).hexdigest()
            == digest
        )
    assert {name: declarations[name]["source_owner"] for name in owners} == owners
    return set(owners)


# Exact source-reviewed extension of accepted Y; never a new baseline count.
# Existing2327 statements/owners remain sealed by the preceding contracts.
_PROOF_PERFORMANCE_THEOREM_EXTENSION = {
    "FEP.EmpiricalRisk.BetaDensity.distinct_posteriors": (
        "src/fep_lean/formal/empirical_risk.lean",
        "5d2d370a21f8bfaaf380c1db391931a7ccf9a32b4c9a06323548a1a5d9bb029d",
    ),
    "FEP.EmpiricalRisk.BetaDensity.likelihood_measurable": (
        "src/fep_lean/formal/empirical_risk.lean",
        "bf4d4df9ecb8a586acac555a0dc27a50fe72b2cffecda7d94a5784411f329a2d",
    ),
    "FEP.EmpiricalRisk.BetaDensity.noninteger_measure_recovery": (
        "src/fep_lean/formal/empirical_risk.lean",
        "cb491a241af4c2f77be855adea1c23c42a9e7876d2bbb14dac33c14f9f55fa66",
    ),
    "FEP.EmpiricalRisk.BetaDensity.noninteger_prior_recovery": (
        "src/fep_lean/formal/empirical_risk.lean",
        "fa1ea28d121193283c4ccac4ff490f15319c829b29c16e09aca0a5b495a14197",
    ),
    "FEP.EmpiricalRisk.BetaDensity.nonpositive_shape_refused": (
        "src/fep_lean/formal/empirical_risk.lean",
        "0e8aaa0a79809acc23c0b462f28a4b3ed857caa2238299fd93dbfab2264efbdb",
    ),
    "FEP.EmpiricalRisk.BetaDensity.normalized_posterior": (
        "src/fep_lean/formal/empirical_risk.lean",
        "23b437fbbec1852b84aa6ddb2117472ff6b9c2cc0fd9893ec324556867e9865b",
    ),
    "FEP.EmpiricalRisk.BetaDensity.normalized_probability": (
        "src/fep_lean/formal/empirical_risk.lean",
        "dd55d1d9ad92ab986cb0f47974ed719b8144787416c222e512e7cd00b564dbb8",
    ),
    "FEP.EmpiricalRisk.BetaDensity.normalizer_finite": (
        "src/fep_lean/formal/empirical_risk.lean",
        "b0ce29c78fd005703e8139cc969eb9f0c3d3187efc3cc154684df5a150c55b80",
    ),
    "FEP.EmpiricalRisk.BetaDensity.normalizer_pos": (
        "src/fep_lean/formal/empirical_risk.lean",
        "4198fe07f2a4d3a065f31b6a2ff71802c6057efa2b8ef71e05f30db9fec09023",
    ),
    "FEP.EmpiricalRisk.BetaDensity.outside_pdf_zero": (
        "src/fep_lean/formal/empirical_risk.lean",
        "4f6721b853f8917e42d0e8538742bd2255b4af203d06ae12aa9a3ed54346e669",
    ),
    "FEP.EmpiricalRisk.BetaDensity.pdf_product": (
        "src/fep_lean/formal/empirical_risk.lean",
        "c5d95d0566a8f359be44b2e0ee411b4bafafb95df6f1d6b6114017cd0c019097",
    ),
    "FEP.EmpiricalRisk.BetaDensity.real_pdf_product": (
        "src/fep_lean/formal/empirical_risk.lean",
        "99ad52b02c9a04df5d5465a5728bccf071ea73b036299625255c430a6099d7c2",
    ),
    "FEP.EmpiricalRisk.BetaDensity.uniform_failure_normalizer": (
        "src/fep_lean/formal/empirical_risk.lean",
        "5bf6de53dae206a9d5d6660f9d3f9d52531ae311459535da2894f10bc4541188",
    ),
    "FEP.EmpiricalRisk.BetaDensity.uniform_failure_posterior": (
        "src/fep_lean/formal/empirical_risk.lean",
        "45f1305197953357cb09364ecaa9e30fafab4d89ae2c65fefa8a3557fb2914d1",
    ),
    "FEP.EmpiricalRisk.BetaDensity.uniform_success_normalizer": (
        "src/fep_lean/formal/empirical_risk.lean",
        "38f110e25d5215dfc1060eb79a911058d13d8fa387ad05e4d0595b1e99f949d0",
    ),
    "FEP.EmpiricalRisk.BetaDensity.uniform_success_posterior": (
        "src/fep_lean/formal/empirical_risk.lean",
        "43b5256343e7e5d80e09be31ccbd2a8a5be0a6e5f2f4dfd67c4b83a76b4f3012",
    ),
    "FEP.EmpiricalRisk.BetaDensity.weighted_mass": (
        "src/fep_lean/formal/empirical_risk.lean",
        "66e6946472ce1ef57febc78ada73e1e43306fc8153a0201d1d31590a86edae31",
    ),
    "FEP.EmpiricalRisk.BetaDensity.weighted_measure": (
        "src/fep_lean/formal/empirical_risk.lean",
        "ec65dd1d6130c5b37ee8cf2c5ee9039676b7fb2661725800d170c2a30cd92b93",
    ),
    "FEP.EmpiricalRisk.BetaDensity.wrong_inverse_ratio": (
        "src/fep_lean/formal/empirical_risk.lean",
        "26452d2d2eb8a7a5cb5708ec201d5d47bdb22b0d42b34cb727b77934391d036b",
    ),
    "FEP.EmpiricalRisk.BetaDensity.wrong_scaled_measure_refused": (
        "src/fep_lean/formal/empirical_risk.lean",
        "2b31baa0989421c19dc968229be8ac4fe2cfb92d72408bfdf82ce190ebc44141",
    ),
    "FEP.EmpiricalRisk.BetaDensity.zero_counts": (
        "src/fep_lean/formal/empirical_risk.lean",
        "e5009d1156b0540cec26986a87f21a94b7fcde4fa0167e83b7e84e1459eb9718",
    ),
    "FEP.EmpiricalRisk.BetaProductPosterior.betaPiZ_empty": (
        "src/fep_lean/formal/empirical_risk.lean",
        "7066b3926d8083473261209d455dd60b4838643439387d8ddaf1a4fdef4ecff1",
    ),
    "FEP.EmpiricalRisk.BetaProductPosterior.betaPiZ_pos_finite": (
        "src/fep_lean/formal/empirical_risk.lean",
        "bfa7d775799c612337b349b60371c68c6f266a77c797e0c05da9cec846e62a52",
    ),
    "FEP.EmpiricalRisk.BetaProductPosterior.normalized_beta_pi": (
        "src/fep_lean/formal/empirical_risk.lean",
        "6f5c0291aa3dbfd1c8cd588c9877bfecceb709b1183ab5ad510a29083503c65f",
    ),
    "FEP.EmpiricalRisk.BetaProductPosterior.weighted_beta_pi": (
        "src/fep_lean/formal/empirical_risk.lean",
        "71510e8f66ca92b7b2b43acf58954b8aa8f577479b1e724ca34de3eb72a837f1",
    ),
    "FEP.EmpiricalRisk.CategoricalLikelihood.incidence_factorization": (
        "src/fep_lean/formal/empirical_risk.lean",
        "5b2516732f69acda6b15bea050a387fdb3280f59613042d6083214bcdb6b99b7",
    ),
    "FEP.EmpiricalRisk.CategoricalLikelihood.three_category_pullback": (
        "src/fep_lean/formal/empirical_risk.lean",
        "b3f654fb34a134d30d8bd6050f6d818e724fa530cb00d7b38312cf95551ce239",
    ),
    "FEP.EmpiricalRisk.CategoricalLikelihood.three_category_zero_counts": (
        "src/fep_lean/formal/empirical_risk.lean",
        "19d8d4bf468250bd38c222619a6f71eca2886441b8e10c9d15b2306b04d8b016",
    ),
    "FEP.EmpiricalRisk.CategoricalLikelihood.wrong_tail_count_refused": (
        "src/fep_lean/formal/empirical_risk.lean",
        "8dff64ce30be760056cb528dd36f25db5305d4ad4ab8dae5b74f2b27fee1badc",
    ),
    "FEP.EmpiricalRisk.ConditioningRowProductProposal.matrixZ_pos_finite": (
        "src/fep_lean/formal/empirical_risk.lean",
        "57c0cb3349d665f2ff6cd963207dd8f691691a922f0b613f4187da2393b7c163",
    ),
    "FEP.EmpiricalRisk.ConditioningRowProductProposal.normalized_rows": (
        "src/fep_lean/formal/empirical_risk.lean",
        "fb02433892cec37a762584f8e658b8354c1031d1411d094e15d26d1aa57485e0",
    ),
    "FEP.EmpiricalRisk.ConditioningRowProductProposal.vector_pi_scale_factors": (
        "src/fep_lean/formal/empirical_risk.lean",
        "b5dcef0ec9f4732c66f869f74813574355b12630a5b7304ed698890060f6a1d1",
    ),
    "FEP.EmpiricalRisk.ConditioningRowProductProposal.vector_pi_withDensity": (
        "src/fep_lean/formal/empirical_risk.lean",
        "c19cccb486ee5c95896641dcf838d379f0257a5a099ac9f1be5b5792e7e91b97",
    ),
    "FEP.EmpiricalRisk.ConditioningRowProductProposal.weighted_rows": (
        "src/fep_lean/formal/empirical_risk.lean",
        "bec6e73691ff496c0ee01400ca18fc61e28cab268d6f5c1c235d998bb36e19d6",
    ),
    "FEP.EmpiricalRisk.FinitePiWeighting.fin_pi_withDensity": (
        "src/fep_lean/formal/empirical_risk.lean",
        "c1a5e3e6e3082572db786e5567c703df0600cd04cb8605fe034d773529d7c5c4",
    ),
    "FEP.EmpiricalRisk.FinitePiWeighting.pi_scale_factors": (
        "src/fep_lean/formal/empirical_risk.lean",
        "aae2c6c37f612200265457c2f41ea52d19857183249fbd0c181edf4f312e4c4d",
    ),
    "FEP.EmpiricalRisk.MeasureTransport.map_likelihood_weight": (
        "src/fep_lean/formal/empirical_risk.lean",
        "52dcc8118dc304ea5810ba8bd3ca1d8b3515589c4616587b21d41c1b55c33f43",
    ),
    "FEP.EmpiricalRisk.MeasureTransport.product_likelihood_weight": (
        "src/fep_lean/formal/empirical_risk.lean",
        "2acda92df3d747f15dfec936dc8d68ec5f049e58afa61222cdc875168c38d1f2",
    ),
    "FEP.EmpiricalRisk.StickFamily.beta_ae_Ioo": (
        "src/fep_lean/formal/empirical_risk.lean",
        "22f01f72c9e550a1c08fe754680b0940305b0b91d3d4d41c7d1750083a4c1812",
    ),
    "FEP.EmpiricalRisk.StickFamily.family_ae_simplex": (
        "src/fep_lean/formal/empirical_risk.lean",
        "56f0fc1d1ded9a30f496075307220b49912c80312607c6c4ec63923beb93850d",
    ),
    "FEP.EmpiricalRisk.StickFamily.family_probability": (
        "src/fep_lean/formal/empirical_risk.lean",
        "669b9c86aa22ca599f5cdd0735bfc433b7c8bc42adbfc1aaea8d0b51740c45b4",
    ),
    "FEP.EmpiricalRisk.StickFamily.family_zero": (
        "src/fep_lean/formal/empirical_risk.lean",
        "b2964111a9ab6e7a1b9d1abf0a19b28a44869057b85113e6b36bec3ce5c0a168",
    ),
    "FEP.EmpiricalRisk.StickFamily.measurable_stickMap": (
        "src/fep_lean/formal/empirical_risk.lean",
        "86929c2adb2536e49cd5de3c3b8dcbcf2d86f199f71f2d584a8773732af2e34d",
    ),
    "FEP.EmpiricalRisk.StickFamily.stickLaw_ae_unit": (
        "src/fep_lean/formal/empirical_risk.lean",
        "dbac2b11a8013eaf09e05615fa717864894fa5e02ea266e41371362062086dce",
    ),
    "FEP.EmpiricalRisk.StickFamily.stickLaw_probability": (
        "src/fep_lean/formal/empirical_risk.lean",
        "c6b343921cedeb385b1b0d80c4de138290597b18f4f3a6c56b6731efdfdf3082",
    ),
    "FEP.EmpiricalRisk.StickFamily.stickMap_nonneg": (
        "src/fep_lean/formal/empirical_risk.lean",
        "b8e40724a09e6f9a7c29cffb262d1875906cba67232f744ee51f2761706275c8",
    ),
    "FEP.EmpiricalRisk.StickFamily.stickMap_sum_one": (
        "src/fep_lean/formal/empirical_risk.lean",
        "cd69b1354af87d108e5873383482f8e8b9646ea8188d593825d75ba83796fdf0",
    ),
    "FEP.EmpiricalRisk.StickFamily.stickMap_zero": (
        "src/fep_lean/formal/empirical_risk.lean",
        "9206a4f0994a59748201ee6ac137a500709125d6b32abe2d2a3049c1082df42d",
    ),
    "FEP.EmpiricalRisk.StickFamily.tailShape_pos": (
        "src/fep_lean/formal/empirical_risk.lean",
        "6660266e968f5789ed50f2e1e080ab41830e87d78f1bab764b5cb44c5305ebd8",
    ),
    "FEP.EmpiricalRisk.StickFamilyPosterior.normalized_family": (
        "src/fep_lean/formal/empirical_risk.lean",
        "6c8b32ef69982ac034d11108ce325317cc021fd1821cd723fa7b8662edad533a",
    ),
    "FEP.EmpiricalRisk.StickFamilyPosterior.stickZ_pos_finite": (
        "src/fep_lean/formal/empirical_risk.lean",
        "d4948edef6f98715abad9f1de23d7b229a27a84824ab177f423956837afdd67e",
    ),
    "FEP.EmpiricalRisk.StickFamilyPosterior.weighted_family": (
        "src/fep_lean/formal/empirical_risk.lean",
        "37c1d1a0fe78241e953c43db75fd198cc42ecc7f404e194dfccad9ebe2a08fbf",
    ),
    "FEP.EmpiricalRisk.StickFamilyPosterior.weighted_family_mass": (
        "src/fep_lean/formal/empirical_risk.lean",
        "13ee5f143da488ce7c8c3b3f1faf5e06894aa6fc688b3074aaf00d7c548d83ef",
    ),
    "FEP.EmpiricalRisk.StickFamilyPosterior.weighted_stickLaw": (
        "src/fep_lean/formal/empirical_risk.lean",
        "250d9a695420eca7b8793174dfd30f62f2df8baa9d7770c167d55725236126e4",
    ),
    "FEP.EmpiricalRisk.StickMapLikelihood.headFactor_likelihood": (
        "src/fep_lean/formal/empirical_risk.lean",
        "0c86a865ba063551f608af664605ff1ad2b0a0c5743be8db09459df1573f9d68",
    ),
    "FEP.EmpiricalRisk.StickMapLikelihood.stickMap_incidence": (
        "src/fep_lean/formal/empirical_risk.lean",
        "28ca267303dfddf72ebab30365cce5a54ec179b238f390dfa256531d325d2b86",
    ),
    "FEP.EmpiricalRisk.StickMapLikelihood.stickMap_likelihood_incidence": (
        "src/fep_lean/formal/empirical_risk.lean",
        "3e24ac543798df21b6b044ec0dfdf2ae8a593e8785473bb09af1a3aad06ea517",
    ),
    "FEP.EmpiricalRisk.StickMapLikelihood.tailShape_update": (
        "src/fep_lean/formal/empirical_risk.lean",
        "fce598fddfd3712fdd029031d841ed35f1bacab209d32d51aea6a8fe3dba6b8f",
    ),
    "FEP.EmpiricalRisk.StickMapLikelihood.zero_stick_likelihood": (
        "src/fep_lean/formal/empirical_risk.lean",
        "d85340aa2e6aa4533704ca98939d5c3cffce9a7229881d40e19e34537dc39b99",
    ),
    "FEP.EmpiricalRisk.TailCountTransfer.ae_likelihood_pullback": (
        "src/fep_lean/formal/empirical_risk.lean",
        "6ffe99fe6ddb3489cf2da36ff351913245282b33903f55496a90710493867b7d",
    ),
    "FEP.EmpiricalRisk.TailCountTransfer.ennreal_likelihood_pullback": (
        "src/fep_lean/formal/empirical_risk.lean",
        "ed5a4c764f5628f1f76639083e0e58e98cdcd7a1f47e3254ffa97ad9bf3557f3",
    ),
    "FEP.EmpiricalRisk.TailCountTransfer.ofReal_product": (
        "src/fep_lean/formal/empirical_risk.lean",
        "6e5ba8a9e3cce9dcef83d7053279c064c6360cb5adb63078c020355fd984eb6c",
    ),
    "FEP.EmpiricalRisk.TailCountTransfer.real_likelihood_pullback": (
        "src/fep_lean/formal/empirical_risk.lean",
        "f624b35a574964e6b5d97f4d1dffe6aa830bcb59bb642def749183e4556bb49e",
    ),
    "FEP.EmpiricalRisk.TailCountTransfer.tail_exponent_eq": (
        "src/fep_lean/formal/empirical_risk.lean",
        "acf38c67f72798dd7abcf4a3c3b9d6733a88d2e5330e66f90e735661d8d289ef",
    ),
    "FEP.GaussianPrecisionConditioning.FiniteCovariance.actual_residual_covariance_zero": (
        "src/fep_lean/formal/gaussian_precision_conditioning.lean",
        "77198c465a080ed332e591bfddc3a41fd8f19e53a83ec2858015691d68fee3ab",
    ),
    "FEP.GaussianPrecisionConditioning.FiniteCovariance.covariance_residual_block": (
        "src/fep_lean/formal/gaussian_precision_conditioning.lean",
        "e888440b9fc6c1f8ca9d924fe3ba41e3ba7ffe237f408732e6288dfeb26dc8d9",
    ),
    "FEP.GaussianPrecisionConditioning.FiniteCovariance.covariance_weighted_add_left": (
        "src/fep_lean/formal/gaussian_precision_conditioning.lean",
        "f4e9456cdeb0b2d6b088ea084f0aff75a94d672b37ce19e53b68fdf87bc76b4c",
    ),
    "FEP.GaussianPrecisionConditioning.FiniteCovariance.covariance_weighted_add_right": (
        "src/fep_lean/formal/gaussian_precision_conditioning.lean",
        "bf5bef38dd3121b5abb3e88897425705512fc63b4dde3f044fe5746b492d8cb6",
    ),
    "FEP.GaussianPrecisionConditioning.FinitePrecision.inverse_rows": (
        "src/fep_lean/formal/gaussian_precision_conditioning.lean",
        "9400ca9afbe9f4f23d09d322ba48da6c971441954d382a5b46513a9ece5b433d",
    ),
    "FEP.GaussianPrecisionConditioning.FinitePrecision.residual_cross_block": (
        "src/fep_lean/formal/gaussian_precision_conditioning.lean",
        "6c4fc285ae3e2b263fa2de656b7fe47319baf12182c85f48eb8c10d099a995db",
    ),
    "FEP.NessFlow.ForwardDifference.actualCarrier_eq_negative_divergence": (
        "src/fep_lean/formal/ness_flow.lean",
        "20c0cb6f883bec7d9d3c06c53256bd341ea9f8a3010fd7efab03a033056967a7",
    ),
    "FEP.NessFlow.ForwardDifference.forwardDiv_tendsto": (
        "src/fep_lean/formal/ness_flow.lean",
        "f2caabae26ab043dad2019068ecd86ed8284a74386761e29563ef47321068c8d",
    ),
    "FEP.NessFlow.ForwardDifference.negative_forwardDiv_tendsto_carrier": (
        "src/fep_lean/formal/ness_flow.lean",
        "0fefec1b9f335188a8b6d901f6b66aac161e3aaaee6ea7f6d712c0c8e9e14e08",
    ),
    "FEP.NessFlow.ForwardDifference.nonSkew_gaussian_carrier_one": (
        "src/fep_lean/formal/ness_flow.lean",
        "5b3cef84760d8afd19772a8b8764aa9614dd3476667e6bd72dfaa69e9bd535b8",
    ),
    "FEP.NessFlow.ForwardDifference.skew_actualCarrier_zero": (
        "src/fep_lean/formal/ness_flow.lean",
        "34b72c992d40a3a3fbc77fdf2a93208fa3b2cd9ec9548d8432a9ccdeaf33fbe6",
    ),
    "FEP.NessFlow.ForwardDifference.stationary_current_differentiable": (
        "src/fep_lean/formal/ness_flow.lean",
        "e05a36ead76234901bc650111f5a7943024bf53a6f6bdf841742854eaa54058c",
    ),
    "FEP.NessFlow.ForwardDifference.stationary_forwardDiv_tendsto_zero": (
        "src/fep_lean/formal/ness_flow.lean",
        "f94d0cf67813b54830c47c5978d1c3028fa339eb3e29064c7d87c49a6532a412",
    ),
}


def proof_performance_theorem_extension(declarations: dict) -> set[str]:
    """Require every exact reviewed new name, owner and statement before subtraction."""
    for name, (owner, digest) in _PROOF_PERFORMANCE_THEOREM_EXTENSION.items():
        assert name in declarations
        assert declarations[name]["source_owner"] == owner
        assert (
            hashlib.sha256(declarations[name]["statement"].encode()).hexdigest()
            == digest
        )
    return set(_PROOF_PERFORMANCE_THEOREM_EXTENSION)
