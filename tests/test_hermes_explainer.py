"""Tests for hermes_explainer — real LLM HTTP client + FEP system prompt.

Tests that don't need an API key validate structure and config loading.
Tests that need an API key are skipped when OPENROUTER_API_KEY / ANTHROPIC_API_KEY
are unset (real CI guard — no direct execution).
"""

from __future__ import annotations

import os
import threading
import time
from pathlib import Path

import pytest

from fep_lean.catalogue.topics import FEPTopicCatalogue
from fep_lean.llm.hermes import (
    _FEP_SYSTEM_PROMPT,
    HermesAPIError,
    HermesConfig,
    HermesExplainer,
    HermesResult,
    _env_positive_int,
    _extract_explanation,
    _extract_lean_block,
    _strip_extra_theorems,
    lean_semantic_contract_sha256,
    preserves_lean_semantic_contract,
    restore_lean_structure,
)

PROJ = Path(__file__).resolve().parent.parent
TOPICS = FEPTopicCatalogue.from_yaml(PROJ / "config" / "topics.yaml")
FIRST_TOPIC = TOPICS.topics[0]  # fep-001

_HAS_API_KEY = bool(
    os.environ.get("OPENROUTER_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
)
# Run live tests when a key is present, unless explicitly opted out with =0.
# Set FEP_LEAN_LIVE_TESTS=0 in CI to skip expensive API calls even when keys exist.
# Set FEP_LEAN_LIVE_TESTS=1 to force-run even without a key (will fail at API level).
_FEP_LEAN_LIVE_VAR = os.environ.get("FEP_LEAN_LIVE_TESTS", "").lower()
# Live OpenRouter tests run only when FEP_LEAN_LIVE_TESTS is explicitly
# enabled. Key presence alone never opts a default pytest run into paid
# API calls.
_LIVE_TESTS_ENABLED = _FEP_LEAN_LIVE_VAR in ("1", "true", "yes")


def test_hermes_config_defaults() -> None:
    cfg = HermesConfig()
    assert cfg.enabled is True
    assert cfg.model
    assert cfg.timeout_s > 0
    assert cfg.max_tokens > 0
    assert cfg.http_referer == "https://github.com/ActiveInferenceInstitute/fep_lean"


def test_hermes_config_from_settings(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("HERMES_MODEL", raising=False)
    monkeypatch.setenv("GAUSS_HOME", str(tmp_path))
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "settings.yaml").write_text(
        "hermes:\n  model: test-model\n  max_tokens: 1000\n  enabled: false\n",
        encoding="utf-8",
    )
    cfg = HermesConfig.from_settings(tmp_path)
    assert cfg.model == "test-model"
    assert cfg.max_tokens == 1000
    assert cfg.enabled is False


def test_hermes_config_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HERMES_MODEL", "my-custom-model")
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test-temporary-key")
    cfg = HermesConfig.from_settings()
    assert cfg.model == "my-custom-model"
    assert cfg.api_key == "sk-test-temporary-key"


def test_settings_yaml_beats_gauss_default_model(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """settings.yaml model must win over GAUSS_DEFAULT_MODEL env var.

    Regression for config precedence bug where GAUSS_DEFAULT_MODEL (from the
    shell or ``~/.gauss/.env``) silently overrode the committed project config.
    """
    monkeypatch.delenv("HERMES_MODEL", raising=False)
    monkeypatch.setenv("GAUSS_DEFAULT_MODEL", "gauss-default/from-env")
    monkeypatch.setenv("GAUSS_HOME", str(tmp_path))
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "settings.yaml").write_text(
        "hermes:\n  model: yaml-wins\n", encoding="utf-8"
    )
    cfg = HermesConfig.from_settings(tmp_path)
    assert cfg.model == "yaml-wins"


def test_hermes_model_env_beats_settings_yaml(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Explicit HERMES_MODEL still wins over settings.yaml (highest priority)."""
    monkeypatch.setenv("HERMES_MODEL", "explicit-env-wins")
    monkeypatch.setenv("GAUSS_HOME", str(tmp_path))
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "settings.yaml").write_text(
        "hermes:\n  model: yaml-loses\n", encoding="utf-8"
    )
    cfg = HermesConfig.from_settings(tmp_path)
    assert cfg.model == "explicit-env-wins"


def test_gauss_default_model_fills_when_yaml_has_no_model(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """GAUSS_DEFAULT_MODEL is the fallback when yaml omits ``model:``."""
    monkeypatch.delenv("HERMES_MODEL", raising=False)
    monkeypatch.setenv("GAUSS_DEFAULT_MODEL", "gauss-fallback/fills")
    monkeypatch.setenv("GAUSS_HOME", str(tmp_path))
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "settings.yaml").write_text(
        "hermes:\n  max_tokens: 1234\n", encoding="utf-8"
    )
    cfg = HermesConfig.from_settings(tmp_path)
    assert cfg.model == "gauss-fallback/fills"
    assert cfg.max_tokens == 1234


def test_hermes_config_is_reasoning_model() -> None:
    cfg = HermesConfig(model="nvidia/nemotron-3-super-120b-a12b:free")
    assert cfg.is_reasoning_model() is True
    cfg2 = HermesConfig(model="some/non-reasoning-model")
    assert cfg2.is_reasoning_model() is False


def test_hermes_config_effective_tokens_reasoning() -> None:
    cfg = HermesConfig(
        model="nvidia/nemotron-3-super-120b-a12b:free",
        max_tokens=1000,
        reasoning_max_tokens=5000,
    )
    assert cfg.effective_max_tokens() == 5000
    assert cfg.effective_timeout() == cfg.reasoning_timeout_s


def test_extract_lean_block_success() -> None:
    content = "Here is the proof:\n```lean\ntheorem foo : True := True.intro\n```\nEnd"
    block = _extract_lean_block(content)
    assert "theorem foo" in block
    assert "```" not in block


def test_extract_lean_block_missing() -> None:
    block = _extract_lean_block("No lean here, just prose.")
    assert block == ""


def test_extract_explanation_strips_code() -> None:
    content = "The proof uses KL divergence.\n\n```lean\nsorry\n```\n\nSee Mathlib."
    expl = _extract_explanation(content)
    assert "KL divergence" in expl
    assert "```" not in expl
    assert "sorry" not in expl


def test_fep_system_prompt_non_empty() -> None:
    assert len(_FEP_SYSTEM_PROMPT) > 100
    assert "Lean 4" in _FEP_SYSTEM_PROMPT
    assert "Mathlib4" in _FEP_SYSTEM_PROMPT
    assert "import" in _FEP_SYSTEM_PROMPT  # preservation rules present
    assert "namespace" in _FEP_SYSTEM_PROMPT


_ORIG_SKETCH = """\
import Mathlib.MeasureTheory.Measure.MeasureSpace
import Mathlib.Analysis.SpecialFunctions.Exp

namespace FEP001

theorem fep001_measure_mono {μ : MeasureTheory.Measure α} {s t : Set α} (h : s ⊆ t) : μ s ≤ μ t :=
  MeasureTheory.measure_mono h

end FEP001
"""


def test_restore_lean_structure_restores_missing_imports() -> None:
    """LLM dropped both imports — they should be restored."""
    refined = "namespace FEP001\n\ntheorem fep001_measure_mono {μ : MeasureTheory.Measure α} {s t : Set α} (h : s ⊆ t) : μ s ≤ μ t :=\n  MeasureTheory.measure_mono h\n\nend FEP001"
    result = restore_lean_structure(refined, _ORIG_SKETCH)
    assert "import Mathlib.MeasureTheory.Measure.MeasureSpace" in result
    assert "import Mathlib.Analysis.SpecialFunctions.Exp" in result
    assert "namespace FEP001" in result
    assert "end FEP001" in result


def test_restore_lean_structure_restores_namespace_wrapper() -> None:
    """LLM dropped namespace/end — it should be re-wrapped."""
    refined = "import Mathlib.MeasureTheory.Measure.MeasureSpace\nimport Mathlib.Analysis.SpecialFunctions.Exp\n\ntheorem fep001_measure_mono : True := trivial"
    result = restore_lean_structure(refined, _ORIG_SKETCH)
    assert "namespace FEP001" in result
    assert "end FEP001" in result


def test_restore_lean_structure_moves_stray_imports_to_top() -> None:
    """LLM put an import line after namespace — it should move to top."""
    refined = "namespace FEP001\nimport Mathlib.Analysis.SpecialFunctions.Exp\ntheorem t : True := trivial\nend FEP001"
    result = restore_lean_structure(refined, _ORIG_SKETCH)
    lines = result.splitlines()
    import_lines = [
        i for i, line in enumerate(lines) if line.strip().startswith("import ")
    ]
    ns_lines = [
        i for i, line in enumerate(lines) if line.strip().startswith("namespace ")
    ]
    assert import_lines, "no import lines found"
    assert ns_lines, "no namespace line found"
    assert max(import_lines) < min(ns_lines), "imports must come before namespace"


def test_restore_lean_structure_noop_when_complete() -> None:
    """When refined already has all imports and namespace, output is structurally equivalent."""
    result = restore_lean_structure(_ORIG_SKETCH.strip(), _ORIG_SKETCH)
    assert "import Mathlib.MeasureTheory.Measure.MeasureSpace" in result
    assert "namespace FEP001" in result
    assert "end FEP001" in result


def test_restore_lean_structure_no_duplicate_imports() -> None:
    """If both refined and original have the same import, it should appear only once."""
    refined = "import Mathlib.MeasureTheory.Measure.MeasureSpace\n\nnamespace FEP001\ntheorem t : True := trivial\nend FEP001"
    result = restore_lean_structure(refined, _ORIG_SKETCH)
    assert result.count("import Mathlib.MeasureTheory.Measure.MeasureSpace") == 1


def test_restore_lean_structure_empty_inputs() -> None:
    assert restore_lean_structure("", _ORIG_SKETCH) == ""
    assert restore_lean_structure(_ORIG_SKETCH, "") == _ORIG_SKETCH


def test_hermes_explainer_disabled_returns_failure() -> None:
    cfg = HermesConfig(enabled=False)
    explainer = HermesExplainer(cfg)
    result = explainer.explain_topic(FIRST_TOPIC)
    assert isinstance(result, HermesResult)
    assert result.success is False
    assert "disabled" in result.error


def test_hermes_explainer_no_key_returns_failure() -> None:
    cfg = HermesConfig(enabled=True, api_key="")
    explainer = HermesExplainer(cfg)
    result = explainer.explain_topic(FIRST_TOPIC)
    assert result.success is False
    assert "API key" in result.error or "api_key" in result.error.lower()


def test_hermes_result_as_dict() -> None:
    r = HermesResult(
        success=True,
        model_used="test-model",
        explanation="The proof follows from KL non-negativity.",
        refined_lean_sketch="theorem foo : True := True.intro",
        tokens_used=150,
        duration_s=1.23,
        topic_id="fep-001",
    )
    d = r.as_dict()
    assert d["success"] is True
    assert d["model_used"] == "test-model"
    assert d["tokens_used"] == 150
    assert "explanation" in d
    assert "refined_lean_sketch" in d


def test_env_positive_int(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("HERMES_MAX_MODEL_ATTEMPTS", raising=False)
    assert _env_positive_int("HERMES_MAX_MODEL_ATTEMPTS") is None
    monkeypatch.setenv("HERMES_MAX_MODEL_ATTEMPTS", "2")
    assert _env_positive_int("HERMES_MAX_MODEL_ATTEMPTS") == 2


def test_hermes_try_fetch_raw_retries_429(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HERMES_429_MAX_RETRIES", "1")
    cfg = HermesConfig(api_key="sk-test-temporary", enabled=True, model="test-m")
    ex = HermesExplainer(cfg)
    n = {"c": 0}

    def temporary_call(inst, messages: list, model: str) -> dict:
        n["c"] += 1
        if n["c"] == 1:
            raise HermesAPIError("HTTP 429", status_code=429)
        return {
            "choices": [
                {"message": {"content": "```lean\ntheorem x : True := trivial\n```"}}
            ],
            "usage": {},
        }

    monkeypatch.setattr(HermesExplainer, "_call_api", temporary_call)
    monkeypatch.setattr("fep_lean.llm.hermes.time.sleep", lambda *_: None)
    msgs = [{"role": "user", "content": "hi"}]
    raw, fatal, _err, retries, advance = ex._try_fetch_raw(msgs, "test-m", "fep-001")
    assert fatal is False
    assert raw is not None
    assert n["c"] == 2
    # One 429 was retried before success on the same model.
    assert retries == 1
    assert advance == ""


def test_hermes_explain_records_empty_content_chain_advance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Primary returns empty ``content`` ⇒ chain advances to the next model;
    the eventually successful ``HermesResult`` records ``empty_content`` as
    the chain-advance reason and ``network_retries == 0`` (no retries needed).
    """
    cfg = HermesConfig(
        api_key="sk-test-temporary",
        enabled=True,
        model="primary-m",
        fallback_models=["primary-m", "fallback-m"],
    )
    ex = HermesExplainer(cfg)
    seen: list[str] = []

    def temporary_call(self, messages: list, model: str) -> dict:
        seen.append(model)
        if model == "primary-m":
            # 200 OK but empty content → _parse_response returns success=False
            return {"choices": [{"message": {"content": ""}}], "usage": {}}
        return {
            "choices": [
                {"message": {"content": "```lean\ntheorem x : True := trivial\n```"}}
            ],
            "usage": {"completion_tokens": 1, "prompt_tokens": 1},
        }

    monkeypatch.setattr(HermesExplainer, "_call_api", temporary_call)
    monkeypatch.setattr("fep_lean.llm.hermes.time.sleep", lambda *_: None)
    res = ex.explain_topic(FIRST_TOPIC)
    assert res.success is True
    assert res.model_used == "fallback-m"
    assert res.chain_advance_reason == "empty_content"
    assert res.network_retries == 0
    assert seen == ["primary-m", "fallback-m"]


def test_hermes_config_cache_ttl_default() -> None:
    cfg = HermesConfig()
    assert cfg.cache_ttl_hours == 24.0


def test_hermes_result_cache_hit_field() -> None:
    r_hit = HermesResult(success=True, model_used="m", cache_hit=True)
    d = r_hit.as_dict()
    assert d["cache_hit"] is True

    r_miss = HermesResult(success=True, model_used="m")
    assert r_miss.cache_hit is False
    assert r_miss.as_dict()["cache_hit"] is False


def test_build_messages_preamble_prepended() -> None:
    cfg = HermesConfig(enabled=False)
    explainer = HermesExplainer(cfg)
    preamble = "TASK: Draft a skeleton only."
    msgs = explainer.build_messages(FIRST_TOPIC, preamble=preamble)
    user_msg = next(m["content"] for m in msgs if m["role"] == "user")
    assert user_msg.startswith(preamble)
    # Original theorem content still present
    assert (
        FIRST_TOPIC.id in user_msg
        or FIRST_TOPIC.title in user_msg
        or FIRST_TOPIC.nl[:20] in user_msg
    )


def test_build_messages_review_mode_has_no_lean_rewrite_instruction() -> None:
    explainer = HermesExplainer(HermesConfig(enabled=False))
    messages = explainer.build_messages(
        FIRST_TOPIC,
        preamble="TASK: Review the compiled theorem.",
        request_lean=False,
    )
    user_msg = next(
        message["content"] for message in messages if message["role"] == "user"
    )
    assert "Review the compiled theorem" in user_msg
    assert "Provide a refined Lean 4 theorem sketch" not in user_msg
    assert "without rewriting" in user_msg


@pytest.mark.skipif(
    not (_HAS_API_KEY and _LIVE_TESTS_ENABLED),
    reason="No API key found (set OPENROUTER_API_KEY or ANTHROPIC_API_KEY); or suppressed via FEP_LEAN_LIVE_TESTS=0",
)
def test_hermes_explain_topic_real_api_call() -> None:
    """Real HTTP round-trip: HermesExplainer.explain_topic → OpenRouter API.

    Why this test exists
    --------------------
    All other ``HermesExplainer`` tests operate on config, message-building,
    text extraction, and local-server HTTP error paths.  This test is the only
    one that fires a genuine POST to OpenRouter and validates the full
    ``_call_api`` → ``_parse_response`` → ``HermesResult`` pipeline under
    live network conditions.

    What it checks
    --------------
    * ``HermesResult`` is returned (never raises).
    * ``result.topic_id`` is echoed correctly regardless of API outcome.
    * On success: ``explanation`` or ``refined_lean_sketch`` is non-empty,
      ``model_used`` is set, ``duration_s > 0``.
    * On non-fatal failure (rate-limit, model-unavailable, 429):
      ``result.error`` is populated — the fallback chain exhausted gracefully.
    * Wall-clock time stays under 720 s (12 min) — ceiling covers a full
      reasoning-model timeout (300 s) plus two retry/fallback cycles with
      exponential backoff (up to 60 s each) and a second fallback model.

    Non-fatal failure modes
    -----------------------
    The test intentionally does **not** assert ``result.success``.  OpenRouter
    free-tier models are rate-limited; CI environments with no credits will
    exhaust the fallback chain and return ``success=False`` with a populated
    ``error`` string.  That is correct behavior, not a test failure.

    How to run
    ----------
    ::

        export OPENROUTER_API_KEY=sk-or-v1-...   # or ANTHROPIC_API_KEY
        export FEP_LEAN_LIVE_TESTS=1
        uv run pytest tests/test_hermes_explainer.py::test_hermes_explain_topic_real_api_call -v -s

    Expected timing: 5–90 s (standard models) or up to 720 s (reasoning models + retries).
    """
    cfg = HermesConfig.from_settings(PROJ)
    explainer = HermesExplainer(cfg)
    t0 = time.time()
    result = explainer.explain_topic(FIRST_TOPIC)
    elapsed = time.time() - t0
    assert isinstance(result, HermesResult)
    assert result.topic_id == FIRST_TOPIC.id
    if result.success:
        assert result.explanation or result.refined_lean_sketch
        assert result.model_used
        assert result.duration_s > 0
    else:
        # Allow model-not-found or rate-limit as non-fatal
        assert result.error
    # Should not take forever: reasoning timeout (300s) + 2 retry/fallback cycles
    assert (
        elapsed < 720
    )  # 12 min ceiling; set FEP_LEAN_LIVE_TESTS=0 to skip in pipeline


# ── _strip_extra_theorems tests ───────────────────────────────────────────────

_SKETCH_WITH_EXTRA = """\
import Mathlib.MeasureTheory.Measure.MeasureSpace

namespace FEP001

theorem fep001_measure_union_le (μ : MeasureTheory.Measure α) (s t : Set α) :
    μ (s ∪ t) ≤ μ s + μ t :=
  MeasureTheory.measure_union_le s t

theorem hermes_extra_theorem (x : ℝ) : x = x := rfl

end FEP001
"""

_SKETCH_TWO_ORIG = """\
import Mathlib.MeasureTheory.Measure.MeasureSpace

namespace FEP001

theorem fep001_measure_mono {μ : MeasureTheory.Measure α} {s t : Set α} (h : s ⊆ t) : μ s ≤ μ t :=
  MeasureTheory.measure_mono h

theorem fep001_measure_empty (μ : MeasureTheory.Measure α) : μ ∅ = 0 :=
  MeasureTheory.measure_empty

end FEP001
"""


def test_strip_extra_theorems_removes_added_theorem() -> None:
    """Extra theorem not in allowed_names is removed."""
    allowed = {"fep001_measure_union_le"}
    result = _strip_extra_theorems(_SKETCH_WITH_EXTRA, allowed)
    assert "hermes_extra_theorem" not in result
    assert "fep001_measure_union_le" in result


def test_strip_extra_theorems_preserves_original_theorems() -> None:
    """All theorems in allowed_names are kept."""
    allowed = {"fep001_measure_mono", "fep001_measure_empty"}
    result = _strip_extra_theorems(_SKETCH_TWO_ORIG, allowed)
    assert "fep001_measure_mono" in result
    assert "fep001_measure_empty" in result


def test_strip_extra_theorems_preserves_non_theorem_content() -> None:
    """import, namespace, variable, open lines always pass through."""
    sketch = (
        "import Mathlib.MeasureTheory.Measure.MeasureSpace\n"
        "namespace FEP001\n"
        "variable {α : Type*} [MeasurableSpace α]\n"
        "theorem fep001_ok : True := trivial\n"
        "end FEP001\n"
    )
    result = _strip_extra_theorems(sketch, {"fep001_ok"})
    assert "import Mathlib" in result
    assert "namespace FEP001" in result
    assert "variable" in result
    assert "end FEP001" in result


def test_strip_extra_theorems_empty_allowed_names_keeps_all() -> None:
    """Empty allowed_names set: nothing is a known original, so all theorems dropped."""
    result = _strip_extra_theorems(_SKETCH_WITH_EXTRA, set())
    # allowed is empty so fep001_measure_union_le should be dropped too
    assert "hermes_extra_theorem" not in result
    assert "fep001_measure_union_le" not in result
    # Non-theorem structure survives
    assert "namespace FEP001" in result


def test_strip_extra_theorems_empty_sketch() -> None:
    assert _strip_extra_theorems("", {"anything"}) == ""


def test_strip_extra_theorems_sketch_with_doc_comments_preserved() -> None:
    """Doc comments immediately preceding an allowed theorem are kept."""
    sketch = (
        "namespace FEP001\n"
        "/-- This is a doc comment. -/\n"
        "theorem fep001_ok : True := trivial\n"
        "end FEP001\n"
    )
    result = _strip_extra_theorems(sketch, {"fep001_ok"})
    assert "/-- This is a doc comment. -/" in result
    assert "fep001_ok" in result


# ── restore_lean_structure garbage detection tests ────────────────────────────


def test_restore_lean_structure_falls_back_on_cpp_comments() -> None:
    """C++ // comments in refined sketch → fall back to original."""
    garbage = (
        "import Mathlib\n"
        "open MeasureTheory\n"
        "// [proof strategy: something]\n"
        "// namespace FEP001\n"
    )
    result = restore_lean_structure(garbage, _ORIG_SKETCH)
    # Must return original, not the garbage
    assert "// [proof strategy" not in result
    assert "theorem fep001_measure_mono" in result


def test_restore_lean_structure_falls_back_when_no_theorem() -> None:
    """Refined output with no theorem keyword → fall back to original."""
    no_theorem = (
        "import Mathlib.MeasureTheory.Measure.MeasureSpace\n"
        "namespace FEP001\n"
        "-- only a comment, no actual theorem\n"
        "end FEP001\n"
    )
    result = restore_lean_structure(no_theorem, _ORIG_SKETCH)
    assert "theorem fep001_measure_mono" in result


def test_restore_lean_structure_restores_open_statements() -> None:
    """If original has `open X` and Hermes drops it, it must be re-inserted."""
    original_with_open = (
        "import Mathlib.MeasureTheory.Measure.MeasureSpace\n"
        "\n"
        "namespace FEP001\n"
        "\n"
        "open MeasureTheory\n"
        "\n"
        "theorem fep001_ok (μ : Measure α) : True := trivial\n"
        "end FEP001\n"
    )
    # Hermes drops the `open MeasureTheory` line but still uses `Measure α`
    refined_no_open = (
        "import Mathlib.MeasureTheory.Measure.MeasureSpace\n"
        "\n"
        "namespace FEP001\n"
        "\n"
        "theorem fep001_ok (μ : Measure α) : True := trivial\n"
        "end FEP001\n"
    )
    result = restore_lean_structure(refined_no_open, original_with_open)
    assert "open MeasureTheory" in result
    # It should appear inside the namespace (before theorems)
    lines = result.splitlines()
    ns_idx = next(i for i, line in enumerate(lines) if "namespace FEP001" in line)
    open_idx = next(
        (i for i, line in enumerate(lines) if "open MeasureTheory" in line), None
    )
    assert open_idx is not None
    assert open_idx > ns_idx


def test_restore_lean_structure_preserves_variable_declarations() -> None:
    """If original declares `variable {α : Type*} [MeasurableSpace α]` and
    Hermes drops it, restoration must re-inject the line inside the namespace.

    Regression: in run_20260420_131713 fep-042 was the lone refined-fail because
    Hermes dropped the `variable` line; Lean 4.29's autobound-implicit then
    auto-included `[MeasurableSpace α]` per-theorem and `linter.unusedSectionVars`
    fired hard errors → compiles=False. The fix is symmetric to step 5.5.
    """
    original_with_variable = (
        "import Mathlib.MeasureTheory.Measure.MeasureSpace\n"
        "\n"
        "namespace FEP042\n"
        "\n"
        "open MeasureTheory\n"
        "\n"
        "variable {α : Type*} [MeasurableSpace α]\n"
        "\n"
        "theorem fep042_measure_nonneg (μ : Measure α) (s : Set α) : 0 ≤ μ s :=\n"
        "  zero_le _\n"
        "end FEP042\n"
    )
    refined_no_variable = (
        "import Mathlib.MeasureTheory.Measure.MeasureSpace\n"
        "\n"
        "namespace FEP042\n"
        "\n"
        "open MeasureTheory\n"
        "\n"
        "theorem fep042_measure_nonneg (μ : Measure α) (s : Set α) : 0 ≤ μ s :=\n"
        "  zero_le _\n"
        "end FEP042\n"
    )
    result = restore_lean_structure(refined_no_variable, original_with_variable)
    assert "variable {α : Type*} [MeasurableSpace α]" in result, (
        "variable declaration must be re-injected when Hermes drops it"
    )
    lines = result.splitlines()
    ns_idx = next(i for i, line in enumerate(lines) if "namespace FEP042" in line)
    open_idx = next(i for i, line in enumerate(lines) if "open MeasureTheory" in line)
    var_idx = next(
        i for i, line in enumerate(lines) if line.strip().startswith("variable ")
    )
    thm_idx = next(
        i for i, line in enumerate(lines) if "theorem fep042_measure_nonneg" in line
    )
    assert ns_idx < open_idx < var_idx < thm_idx, (
        f"ordering violated: ns={ns_idx} open={open_idx} var={var_idx} thm={thm_idx}"
    )


def test_restore_lean_structure_does_not_duplicate_variable_when_present() -> None:
    """If Hermes already preserved the `variable` line, do not duplicate it."""
    original_with_variable = (
        "import Mathlib.MeasureTheory.Measure.MeasureSpace\n"
        "\n"
        "namespace FEP042\n"
        "\n"
        "variable {α : Type*} [MeasurableSpace α]\n"
        "\n"
        "theorem fep042_ok (μ : MeasureTheory.Measure α) : True := trivial\n"
        "end FEP042\n"
    )
    result = restore_lean_structure(
        original_with_variable.strip(), original_with_variable
    )
    assert result.count("variable {α : Type*} [MeasurableSpace α]") == 1


def test_restore_lean_structure_completeness_fallback() -> None:
    """When all original theorems are stripped (Hermes replaced them), fall back to original."""
    # Hermes replaced all 4 original theorems with a single unrelated one
    hermes_replaced_all = (
        "import Mathlib.MeasureTheory.Measure.MeasureSpace\n"
        "\n"
        "namespace FEP001\n"
        "\n"
        "-- Hermes rewrote everything\n"
        "theorem completely_different (x : ℝ) : x = x := rfl\n"
        "\n"
        "end FEP001\n"
    )
    result = restore_lean_structure(hermes_replaced_all, _ORIG_SKETCH)
    # Should fall back to original since no original theorem names survive
    assert "theorem fep001_measure_mono" in result
    assert "completely_different" not in result


def test_restore_lean_structure_rejects_partial_name_preservation() -> None:
    canonical = FIRST_TOPIC.lean_sketch
    weakened = (
        "namespace FEP001\n"
        "theorem fep001_variationalUpperBound_eq_iff : True := True.intro\n"
        "end FEP001\n"
    )

    result = restore_lean_structure(weakened, canonical)

    assert result == canonical
    assert not preserves_lean_semantic_contract(weakened, canonical)


def test_restore_lean_structure_rejects_proof_change() -> None:
    canonical = FIRST_TOPIC.lean_sketch
    proof_only = canonical.replace(
        "exact le_add_right (le_refl _)",
        "simpa using le_add_right (le_refl _)",
        1,
    )

    assert not preserves_lean_semantic_contract(proof_only, canonical)
    assert lean_semantic_contract_sha256(proof_only) != (
        lean_semantic_contract_sha256(canonical)
    )
    assert restore_lean_structure(proof_only, canonical) == canonical


def test_restore_lean_structure_accepts_comment_and_whitespace_only_change() -> None:
    canonical = FIRST_TOPIC.lean_sketch
    annotated = canonical.replace(
        "exact le_add_right (le_refl _)",
        "  /- Provider explanation: the KL gap is nonnegative. -/\n"
        "  exact   le_add_right   (le_refl _)",
        1,
    )

    assert preserves_lean_semantic_contract(annotated, canonical)
    assert lean_semantic_contract_sha256(annotated) == (
        lean_semantic_contract_sha256(canonical)
    )
    assert restore_lean_structure(annotated, canonical).rstrip() == annotated.rstrip()


def test_restore_lean_structure_rejects_indented_custom_axiom() -> None:
    canonical = FIRST_TOPIC.lean_sketch
    escaped = canonical.replace(
        "  exact le_add_right (le_refl _)",
        "  exact le_add_right (le_refl _)\n\n  axiom semanticEscape : False",
        1,
    ).replace(
        "  exact InformationTheory.klDiv_eq_zero_iff",
        "  exact False.elim semanticEscape",
        1,
    )

    assert not preserves_lean_semantic_contract(escaped, canonical)
    assert restore_lean_structure(escaped, canonical) == canonical


def test_restore_lean_structure_rejects_theorem_type_weakening() -> None:
    canonical = FIRST_TOPIC.lean_sketch
    weakened = canonical.replace(
        "surprisal ≤\n      fep001_variationalUpperBound approximation posterior surprisal",
        "True",
        1,
    )

    assert not preserves_lean_semantic_contract(weakened, canonical)
    assert restore_lean_structure(weakened, canonical) == canonical


def test_restore_lean_structure_rejects_definition_change() -> None:
    canonical = FIRST_TOPIC.lean_sketch
    redefined = canonical.replace(
        "surprisal + fep001_variationalGap approximation posterior",
        "fep001_variationalGap approximation posterior",
        1,
    )

    assert not preserves_lean_semantic_contract(redefined, canonical)
    assert restore_lean_structure(redefined, canonical) == canonical


def test_restore_lean_structure_does_not_add_hermes_imports() -> None:
    """Imports added by Hermes (not in original) must NOT appear in output."""
    refined_with_extra_import = (
        "import Mathlib.MeasureTheory.Measure.MeasureSpace\n"
        "import Mathlib.Data.Fin\n"
        "import Mathlib.Analysis.SpecialFunctions.Exp\n"
        "namespace FEP001\n"
        "theorem fep001_measure_mono {μ : MeasureTheory.Measure α} {s t : Set α} (h : s ⊆ t) : μ s ≤ μ t :=\n"
        "  MeasureTheory.measure_mono h\n"
        "end FEP001\n"
    )
    result = restore_lean_structure(refined_with_extra_import, _ORIG_SKETCH)
    assert "Mathlib.Data.Fin" not in result


def test_preflight_never_mutates_shared_config_budgets(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Concurrent effective_max_tokens() must see original budgets during preflight.

    SC-5: preflight used to rewrite shared HermesConfig fields (max_tokens=1,
    reasoning_max_tokens=1, capped timeouts) for the duration of the probe, so
    a concurrent real request could be sent with probe-sized budgets. The
    probe now passes per-call budgets and leaves the shared config untouched.
    """
    cfg = HermesConfig(
        enabled=True, api_key="test-key", max_tokens=16384, reasoning_max_tokens=65536
    )
    ex = HermesExplainer(cfg)
    captured: dict[str, tuple[int, int] | None] = {"budgets": None}
    release = threading.Event()

    def probe_call(inst, messages, model, budgets=None):
        captured["budgets"] = budgets
        # Hold the "probe" open while another thread reads the shared budgets.
        release.wait(timeout=5)
        return {
            "choices": [{"message": {"content": "ping"}}],
            "usage": {},
        }

    monkeypatch.setattr(HermesExplainer, "_call_api", probe_call)
    observed: list[tuple[int, int]] = []

    def read_budgets() -> None:
        observed.append((cfg.effective_max_tokens(), cfg.effective_timeout()))

    reader = threading.Thread(target=read_budgets, name="budget-reader")
    reader.start()
    try:
        assert ex.preflight() is True
    finally:
        release.set()
        reader.join(timeout=5)
    # The probe request itself carried probe-sized budgets...
    assert captured["budgets"] is not None
    assert captured["budgets"][0] == 1
    # ...while the concurrent reader observed the ORIGINAL config budgets...
    assert observed == [(cfg.effective_max_tokens(), cfg.effective_timeout())]
    # ...and the shared config is byte-identical afterwards.
    assert cfg.max_tokens == 16384
    assert cfg.reasoning_max_tokens == 65536
