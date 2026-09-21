"""gauss_runner — formalization orchestrator combining Hermes and Lean 4.

Provides ``GaussRunner``, which executes a single topic formalization session:
1. Opens an SQLite session via ``OpenGaussClient``.
2. Calls ``HermesExplainer`` to refine the Lean sketch.
3. Tests the refined sketch via ``LeanVerifier``.
4. Saves all results and artifacts.
"""

from __future__ import annotations

import hashlib as _hashlib
import json as _json
import logging
import os
import time
import types
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import TYPE_CHECKING, Any

from typing_extensions import Self

from fep_lean.gauss.cli import check_gauss_cli
from fep_lean.gauss.client import OpenGaussClient, resolve_gauss_home
from fep_lean.llm.hermes import (
    HermesConfig,
    HermesExplainer,
    HermesResult,
    lean_semantic_contract_sha256,
    restore_lean_structure_with_status,
)
from fep_lean.verification._toolchain import toolchain_identity
from fep_lean.verification.lean_verifier import LeanVerifier, VerifyResult

if TYPE_CHECKING:
    from fep_lean.catalogue.topics import TopicEntry

log = logging.getLogger(__name__)

# ── Workflow stage directives ─────────────────────────────────────────────────

_WORKFLOW_PREAMBLES: dict[str, str] = {
    "verify": "",
    "draft": (
        "TASK: Draft a new Lean 4 theorem skeleton. "
        "Focus on correctly typing the statement and naming hypotheses. "
        "Use sorry freely for all sub-goals."
    ),
    "prove": (
        "TASK: Attempt a full Lean 4 proof. "
        "Fill in as many sorry-holes as possible using Mathlib4 tactics. "
        "Prefer `exact`, `apply`, `simp`, `ring`, `linarith` over sorry."
    ),
    "review": (
        "TASK: Review the compiled Lean 4 sketch and provide: "
        "(1) correctness assessment, (2) suggested Mathlib lemma improvements, "
        "(3) clarity improvements. Do NOT produce a new ```lean block."
    ),
}


def _prefetch_enabled() -> bool:
    """True when ``FEP_LEAN_PREFETCH=1`` (Hermes for next topic while Lean verifies current)."""
    v = os.environ.get("FEP_LEAN_PREFETCH", "").lower().strip()
    return v in ("1", "true", "yes", "on")


def _toolchain_salt(project_root: Path) -> str:
    """Return a stable short hash of the pinned Lean toolchain + Mathlib rev.

    Folded into the Hermes cache key so a toolchain/Mathlib bump invalidates
    cached refined sketches that may no longer compile against the new
    milestone.  Built on the shared validated readers; a missing or malformed
    component contributes no part, so an unusable toolchain still yields a
    stable key distinct from any pinned one.
    """
    identity = toolchain_identity(Path(project_root) / "lean")
    parts = [
        part for part in (identity["lean_toolchain"], identity["mathlib_tag"]) if part
    ]
    return _hashlib.sha256("|".join(parts).encode()).hexdigest()[:12]


def _hermes_cache_key(
    topic_id: str,
    lean_sketch: str,
    model: str,
    stage: str,
    *,
    prompt_digest: str,
    salt: str = "",
) -> str:
    """SHA-256 of the inputs that determine a unique Hermes response.

    ``salt`` is the pinned-toolchain digest (see :func:`_toolchain_salt`) so
    cached responses are invalidated when the Lean/Mathlib milestone changes.
    """
    raw = f"{topic_id}:{lean_sketch}:{model}:{stage}:{prompt_digest}:{salt}"
    return _hashlib.sha256(raw.encode()).hexdigest()


def _prompt_digest(messages: list[dict[str, str]]) -> str:
    """Hash the exact rendered role/content payload sent to Hermes."""
    payload = _json.dumps(messages, sort_keys=True, separators=(",", ":"))
    return _hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass
class TopicRunResult:
    """Result of running one topic through the full Hermes + Lean workflow.

    Hermes-derived fields (``explanation``, ``refined_lean_sketch``, ``tokens_used``,
    ``hermes_model``, ``cache_hit``, ``hermes_lean_compiles``) and native Lean
    warnings are surfaced here so downstream reporters do not reinterpret
    SQLite or compiler output.
    """

    topic_id: str
    session_id: str
    success: bool
    status: str
    hermes_success: bool = False
    lean_compiles: bool = False
    lean_has_sorry: bool = False
    lean_warnings: list[str] = field(default_factory=list)
    lean_version: str = ""
    duration_s: float = 0.0
    error: str = ""
    workflow: str = "verify"
    stage_results: list[dict[str, Any]] = field(default_factory=list)
    explanation: str = ""
    refined_lean_sketch: str = ""
    final_lean_sketch: str = ""
    canonical_source_sha256: str = ""
    semantic_contract_sha256: str = ""
    semantic_contract_preserved: bool = False
    verification_source: str = "none"
    tokens_used: int = 0
    hermes_model: str = ""
    cache_hit: bool = False
    hermes_lean_compiles: bool = False
    # Same-model 429/transport retries summed across every model attempted
    # for this topic.  Distinct from chain advances (which switch models).
    network_retries: int = 0
    # Empty when the primary model produced the final answer; otherwise a
    # short label (``empty_content``, ``wall_clock_timeout``,
    # ``transport_error``, ``non_retriable_http``, ``parse_error``)
    # describing why the OpenRouter chain advanced past the primary.
    chain_advance_reason: str = ""

    def as_dict(self) -> dict[str, Any]:
        """Return serializable dict excluding internal state for JSON persistence."""
        compiled_source_sha256 = (
            _hashlib.sha256(self.final_lean_sketch.encode("utf-8")).hexdigest()
            if self.final_lean_sketch
            else ""
        )
        return {
            "topic_id": self.topic_id,
            "session_id": self.session_id,
            "success": self.success,
            "status": self.status,
            "hermes_success": self.hermes_success,
            "lean_compiles": self.lean_compiles,
            "lean_has_sorry": self.lean_has_sorry,
            "lean_warnings": list(self.lean_warnings),
            "lean_version": self.lean_version,
            "duration_s": round(self.duration_s, 3),
            "error": self.error,
            "workflow": self.workflow,
            "stage_results": self.stage_results,
            "explanation": self.explanation,
            "refined_lean_sketch": self.refined_lean_sketch,
            "final_lean_sketch": self.final_lean_sketch,
            "compiled_source_sha256": compiled_source_sha256,
            "canonical_source_sha256": self.canonical_source_sha256,
            "semantic_contract_sha256": self.semantic_contract_sha256,
            "semantic_contract_preserved": self.semantic_contract_preserved,
            "verification_source": self.verification_source,
            "tokens_used": self.tokens_used,
            "hermes_model": self.hermes_model,
            "cache_hit": self.cache_hit,
            "hermes_lean_compiles": self.hermes_lean_compiles,
            "network_retries": self.network_retries,
            "chain_advance_reason": self.chain_advance_reason,
        }


class GaussRunner:
    """Orchestrates topic formalization, wiring together LLM + Lean + SQLite.

    Parameters
    ----------
    lean_verifier:
        Configured ``LeanVerifier`` instance.
    hermes:
        Configured ``HermesExplainer`` instance.
    client:
        Configured ``OpenGaussClient`` (for SQLite persistence).
    project_root:
        Root path (for saving artifacts).
    """

    def __init__(
        self,
        lean_verifier: LeanVerifier,
        hermes: HermesExplainer,
        client: OpenGaussClient,
        project_root: Path,
    ) -> None:
        self.lean = lean_verifier
        self.hermes = hermes
        self.client = client
        self.project_root = project_root
        # Toolchain-aware salt invalidates the Hermes cache on Lean/Mathlib bumps.
        self._cache_salt = _toolchain_salt(project_root)
        # Prune stale Hermes cache entries on startup
        ttl = getattr(self.hermes._cfg, "cache_ttl_hours", 24.0)
        pruned = self.client.prune_hermes_cache(ttl_hours=ttl)
        if pruned:
            log.debug("Pruned %d stale Hermes cache entries (ttl=%.1fh)", pruned, ttl)
        self._prefetch_executor: ThreadPoolExecutor | None = None
        self._prefetch_future: Future[HermesResult] | None = None
        self._prefetch_hermes: HermesExplainer | None = None
        self._prefetch_next_topic: TopicEntry | None = None
        self._closed = False

    def close(self) -> None:
        """Release the prefetch worker and SQLite client resources."""
        if self._closed:
            return
        executor = self._prefetch_executor
        self._clear_prefetch_state()
        if executor is not None:
            executor.shutdown(wait=True)
        self.client.close()
        self._closed = True

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: types.TracebackType | None,
    ) -> None:
        self.close()

    def _clear_prefetch_state(self) -> None:
        self._prefetch_executor = None
        self._prefetch_future = None
        self._prefetch_hermes = None
        self._prefetch_next_topic = None

    def _run_logged_topic(
        self,
        topic: TopicEntry,
        *,
        index: int,
        total: int,
        workflow: str,
        results: list[TopicRunResult],
        prefetch: bool = False,
    ) -> None:
        """Run one topic, append the result to ``results``, and log batch progress.

        Shared per-topic body of ``run_topics_batch`` and
        ``_run_topics_batch_prefetch``: run, classification, ETA log, and the
        unhandled-exception result.  ``index`` is the 1-based batch position;
        ``prefetch`` selects the ``prefetch-mode`` start-log variant.
        """
        mode = " prefetch-mode" if prefetch else ""
        log.info(
            "GaussRunner [%d/%d]%s: starting %s (workflow=%s)",
            index,
            total,
            mode,
            topic.id,
            workflow,
        )
        try:
            res = self.run_topic(topic, workflow=workflow)
            results.append(res)
            hermes_str = "hermes=ok" if res.hermes_success else "hermes=skip"
            lean_str = (
                "lean=warning"
                if res.lean_warnings
                else (
                    "lean=ok"
                    if (res.lean_compiles and not res.lean_has_sorry)
                    else ("lean=sorry" if res.lean_has_sorry else "lean=fail")
                )
            )
            done = len(results)
            avg_s = sum(r.duration_s for r in results) / done
            eta_s = avg_s * (total - done)
            log.info(
                "GaussRunner [%d/%d] %s  %s  %s  %.1fs  ETA ~%.0fs",
                index,
                total,
                topic.id,
                hermes_str,
                lean_str,
                res.duration_s,
                eta_s,
            )
        except Exception as e:
            log.exception("GaussRunner: unhandled exception in %s", topic.id)
            results.append(
                TopicRunResult(
                    topic_id=topic.id,
                    session_id="",
                    success=False,
                    status="error",
                    error=f"Unhandled runner exception: {e}",
                )
            )

    def run_topics_batch(
        self,
        topics: list[TopicEntry],
        *,
        max_topics: int | None = None,
        workflow: str = "verify",
    ) -> list[TopicRunResult]:
        """Run formalization over multiple topics sequentially.

        Parameters
        ----------
        workflow:
            Workflow stage to use for each topic.  See ``_WORKFLOW_PREAMBLES``
            for supported values.  Defaults to ``"verify"``.
        """
        self._clear_prefetch_state()
        results: list[TopicRunResult] = []
        subset = topics[:max_topics] if max_topics else topics
        if _prefetch_enabled() and workflow == "verify" and len(subset) > 1:
            return self._run_topics_batch_prefetch(subset, workflow=workflow)
        log.info(
            "GaussRunner: processing %d topic(s) [workflow=%s]",
            len(subset),
            workflow,
        )
        for i, t in enumerate(subset, 1):
            self._run_logged_topic(
                t, index=i, total=len(subset), workflow=workflow, results=results
            )
        return results

    def _run_topics_batch_prefetch(
        self,
        subset: list[TopicEntry],
        *,
        workflow: str,
    ) -> list[TopicRunResult]:
        """Same as ``run_topics_batch`` but overlap Hermes for topic N+1 with Lean on topic N."""
        executor = ThreadPoolExecutor(max_workers=1)
        self._prefetch_executor = executor
        self._prefetch_hermes = HermesExplainer(self.hermes._cfg)
        self._prefetch_future = None
        results: list[TopicRunResult] = []
        try:
            for i, t in enumerate(subset):
                self._prefetch_next_topic = (
                    subset[i + 1] if i + 1 < len(subset) else None
                )
                self._run_logged_topic(
                    t,
                    index=i + 1,
                    total=len(subset),
                    workflow=workflow,
                    results=results,
                    prefetch=True,
                )
        finally:
            executor.shutdown(wait=True)
            self._clear_prefetch_state()
        return results

    def _start_prefetch_next_hermes(
        self,
        current_topic: TopicEntry,
        workflow: str,
        preamble: str,
        model: str,
    ) -> None:
        """Schedule Hermes for the next topic while the current topic's Lean verify runs."""
        if (
            self._prefetch_executor is None
            or self._prefetch_hermes is None
            or workflow != "verify"
            or self._prefetch_next_topic is None
        ):
            return
        nt = self._prefetch_next_topic
        if nt.id == current_topic.id:
            return
        lean_next = getattr(nt, "lean_sketch", "") or ""
        prompt_digest = _prompt_digest(
            self._prefetch_hermes.build_messages(
                nt,
                preamble=preamble,
                request_lean=True,
            )
        )
        nk = _hermes_cache_key(
            nt.id,
            lean_next,
            model,
            workflow,
            prompt_digest=prompt_digest,
            salt=self._cache_salt,
        )
        if self.client.get_cached_hermes(nk) is not None:
            return
        log.debug("Prefetch Hermes for %s while verifying %s", nt.id, current_topic.id)
        self._prefetch_future = self._prefetch_executor.submit(
            self._prefetch_hermes.explain_topic, nt, preamble=preamble
        )

    def run_topic(
        self, topic: TopicEntry, *, workflow: str = "verify"
    ) -> TopicRunResult:
        """Run one topic and finalize any session left open by an exception."""
        self._active_session_id: str | None = None
        try:
            return self._run_topic(topic, workflow=workflow)
        except Exception as exc:
            if self._active_session_id:
                self.client.close_open_session(
                    self._active_session_id,
                    error=f"{type(exc).__name__}: {exc}",
                )
            raise

    def _run_topic(
        self, topic: TopicEntry, *, workflow: str = "verify"
    ) -> TopicRunResult:
        """Run the full Hermes + Lean workflow for a single topic.

        Parameters
        ----------
        workflow:
            Workflow stage controlling the Hermes task directive:
            - ``"verify"`` (default) — refine sketch and verify compilation.
            - ``"draft"`` — produce a new typed skeleton (sorry ok in sub-goals).
            - ``"prove"`` — attempt a full proof minimizing sorry usage.
            - ``"review"`` — verify then request a post-compile review commentary.
        """
        if workflow not in _WORKFLOW_PREAMBLES:
            raise ValueError(f"unsupported workflow: {workflow}")

        # ``review`` is a two-turn workflow: the first turn must still emit a
        # refinable Lean block; only the post-compilation turn requests prose.
        preamble = (
            _WORKFLOW_PREAMBLES["verify"]
            if workflow == "review"
            else _WORKFLOW_PREAMBLES[workflow]
        )
        lean_sketch = getattr(topic, "lean_sketch", "") or ""
        model = self.hermes._cfg.model
        initial_stage = "review_refinement_v2" if workflow == "review" else workflow
        initial_prompt_digest = _prompt_digest(
            self.hermes.build_messages(
                topic,
                preamble=preamble,
                request_lean=True,
            )
        )
        cache_key = _hermes_cache_key(
            topic.id,
            lean_sketch,
            model,
            initial_stage,
            prompt_digest=initial_prompt_digest,
            salt=self._cache_salt,
        )
        stage_results: list[dict[str, Any]] = []

        t0 = time.time()
        session_id = self.client.create_session(
            topic.id,
            topic.area,
            lean_sketch,
        )
        self._active_session_id = session_id
        self.client.log_event(
            "evaluation_started", session_id=session_id, workflow=workflow
        )

        # ── Hermes call with cache (prefetch result from prior topic's verify phase) ─
        cached = self.client.get_cached_hermes(cache_key)
        if self._prefetch_future is not None:
            log.debug("Hermes prefetch result for %s (workflow=%s)", topic.id, workflow)
            hermes_res = self._prefetch_future.result()
            self._prefetch_future = None
            # Require BOTH content and a non-empty refined sketch to cache.
            # A partial response (e.g. truncated mid-fence) leaves
            # ``refined_lean_sketch=""`` even though ``success=bool(content)`` is
            # True; persisting that row poisons the cache and forces every
            # subsequent run through the same dead-end. See fep-019 (2026-04-22).
            if hermes_res.success and hermes_res.refined_lean_sketch:
                self.client.set_cached_hermes(
                    cache_key,
                    topic_id=topic.id,
                    stage=initial_stage,
                    model=hermes_res.model_used,
                    result_json=_json.dumps(hermes_res.as_dict()),
                    lean_sketch_hash=_hashlib.sha256(lean_sketch.encode()).hexdigest(),
                )
        elif cached is not None:
            log.debug("Hermes cache hit: %s (workflow=%s)", topic.id, workflow)
            hermes_res = HermesResult(
                success=cached.get("success", False),
                model_used=cached.get("model_used", model),
                explanation=cached.get("explanation", ""),
                refined_lean_sketch=cached.get("refined_lean_sketch", ""),
                reasoning=cached.get("reasoning", ""),
                tokens_used=cached.get("tokens_used", 0),
                duration_s=cached.get("duration_s", 0.0),
                error=cached.get("error", ""),
                topic_id=cached.get("topic_id", topic.id),
                cache_hit=True,
                network_retries=cached.get("network_retries", 0),
                chain_advance_reason=cached.get("chain_advance_reason", ""),
            )
        else:
            hermes_res = self.hermes.explain_topic(topic, preamble=preamble)
            # See cache-write comment above: refusing to persist responses
            # without an extracted ``lean`` block prevents silent reuse of
            # truncated / fence-omitted model output on the next run.
            if hermes_res.success and hermes_res.refined_lean_sketch:
                self.client.set_cached_hermes(
                    cache_key,
                    topic_id=topic.id,
                    stage=initial_stage,
                    model=hermes_res.model_used,
                    result_json=_json.dumps(hermes_res.as_dict()),
                    lean_sketch_hash=_hashlib.sha256(lean_sketch.encode()).hexdigest(),
                )

        next_turn = self._record_hermes_turns(
            session_id,
            topic,
            hermes_res,
            preamble=preamble,
        )

        if not hermes_res.success:
            self.client.close_session(session_id, status="error", hermes_success=False)
            return TopicRunResult(
                topic_id=topic.id,
                session_id=session_id,
                success=False,
                status="hermes_error",
                error=hermes_res.error or "hermes returned empty",
                duration_s=time.time() - t0,
                workflow=workflow,
                explanation=hermes_res.explanation,
                refined_lean_sketch=hermes_res.refined_lean_sketch,
                tokens_used=hermes_res.tokens_used,
                hermes_model=hermes_res.model_used,
                cache_hit=hermes_res.cache_hit,
                network_retries=hermes_res.network_retries,
                chain_advance_reason=hermes_res.chain_advance_reason,
            )

        refined = hermes_res.refined_lean_sketch
        if not refined:
            self.client.close_session(session_id, status="failed", hermes_success=False)
            return TopicRunResult(
                topic_id=topic.id,
                session_id=session_id,
                success=False,
                status="no_lean_sketch",
                error="LLM did not output a ```lean block",
                duration_s=time.time() - t0,
                workflow=workflow,
                explanation=hermes_res.explanation,
                refined_lean_sketch=hermes_res.refined_lean_sketch,
                tokens_used=hermes_res.tokens_used,
                hermes_model=hermes_res.model_used,
                cache_hit=hermes_res.cache_hit,
                network_retries=hermes_res.network_retries,
                chain_advance_reason=hermes_res.chain_advance_reason,
            )

        # Restore import lines and namespace wrapper that LLMs commonly strip.
        refined, semantic_contract_preserved = restore_lean_structure_with_status(
            refined,
            lean_sketch,
        )
        self.client.set_refined_sketch(session_id, refined)

        # Overlap Hermes for the next catalogue row with Lean verify (prefetch mode only).
        self._start_prefetch_next_hermes(topic, workflow, preamble, model)

        if not self.lean.check_lake_available():
            verify_res = VerifyResult(
                topic_id=topic.id,
                compiles=False,
                has_sorry=False,
                lean_version=self.lean.lean_version() or "unknown",
                skip_reason="lake is unavailable or failed its bounded version probe",
            )
        else:
            verify_res = self.lean.verify_sketch(topic.id, refined)

        _hermes_lean_compiles = verify_res.compiles
        review_completed = workflow != "review"
        review_error = ""
        review_tokens = 0
        review_network_retries = 0

        # ── Optional review pass (workflow="review") ──────────────────────────
        if (
            workflow == "review"
            and verify_res.compiles
            and not verify_res.has_sorry
            and not verify_res.warnings
        ):
            review_preamble = _WORKFLOW_PREAMBLES["review"]
            extra_ctx = (
                f"The sketch compiled successfully (has_sorry={verify_res.has_sorry}). "
                f"Errors: {verify_res.errors or 'none'}."
            )
            review_topic = replace(topic, lean_sketch=refined)
            review_stage = "review_commentary_v2"
            rendered_review_preamble = f"{review_preamble}\n\n{extra_ctx}"
            review_messages = self.hermes.build_messages(
                review_topic,
                preamble=rendered_review_preamble,
                request_lean=False,
            )
            review_cache_key = _hermes_cache_key(
                topic.id,
                refined,
                model,
                review_stage,
                prompt_digest=_prompt_digest(review_messages),
                salt=self._cache_salt,
            )
            review_cached = self.client.get_cached_hermes(review_cache_key)
            if review_cached is not None:
                # Explicit field reconstruction from cache dict — avoids fragile
                # **kwargs unpacking.  cache_hit is forced True regardless of
                # whatever value was stored in the dict.
                review_res = HermesResult(
                    success=review_cached.get("success", False),
                    model_used=review_cached.get("model_used", model),
                    explanation=review_cached.get("explanation", ""),
                    refined_lean_sketch=review_cached.get("refined_lean_sketch", ""),
                    reasoning=review_cached.get("reasoning", ""),
                    tokens_used=int(review_cached.get("tokens_used", 0)),
                    duration_s=float(review_cached.get("duration_s", 0.0)),
                    error=review_cached.get("error", ""),
                    topic_id=review_cached.get("topic_id", topic.id),
                    cache_hit=True,
                    network_retries=int(review_cached.get("network_retries", 0)),
                    chain_advance_reason=review_cached.get("chain_advance_reason", ""),
                )
            else:
                review_res = self.hermes.explain_topic(
                    review_topic,
                    preamble=rendered_review_preamble,
                    request_lean=False,
                )
            if review_res.success and review_res.refined_lean_sketch:
                review_res = replace(
                    review_res,
                    success=False,
                    error=(
                        "prose-only review returned a Lean rewrite; "
                        "the compiled sketch remains authoritative"
                    ),
                )
            if review_cached is None and review_res.success:
                self.client.set_cached_hermes(
                    review_cache_key,
                    topic_id=topic.id,
                    stage=review_stage,
                    model=review_res.model_used,
                    result_json=_json.dumps(review_res.as_dict()),
                    lean_sketch_hash=_hashlib.sha256(refined.encode()).hexdigest(),
                )
            review_completed = review_res.success
            review_error = review_res.error if not review_res.success else ""
            review_tokens = review_res.tokens_used
            review_network_retries = review_res.network_retries
            next_turn = self._record_hermes_turns(
                session_id,
                review_topic,
                review_res,
                preamble=rendered_review_preamble,
                request_lean=False,
                start_index=next_turn,
            )
            stage_results.append(
                {
                    "stage": "review_commentary",
                    "success": review_res.success,
                    "explanation": review_res.explanation,
                    "cache_hit": review_res.cache_hit,
                    "error": review_res.error,
                    "model": review_res.model_used,
                    "tokens_used": review_res.tokens_used,
                    "network_retries": review_res.network_retries,
                    "chain_advance_reason": review_res.chain_advance_reason,
                }
            )

        artifact = self._build_artifact_payload(topic, hermes_res, verify_res)
        artifact["workflow"] = {"name": workflow, "stages": stage_results}
        self.client.write_artifact(session_id, artifact)

        is_success = (
            verify_res.compiles
            and not verify_res.has_sorry
            and not verify_res.warnings
            and review_completed
            and semantic_contract_preserved
        )
        status = "success" if is_success else "failed"
        verification_error = (
            "; ".join(verify_res.errors)
            or "; ".join(verify_res.warnings)
            or verify_res.skip_reason
            or review_error
            or (
                "Hermes output changed the canonical non-comment Lean token contract"
                if not semantic_contract_preserved
                else ""
            )
            or (verify_res.stdout[:300] if verify_res.stdout else "")
        )

        self.client.close_session(
            session_id,
            status=status,
            hermes_success=review_completed,
            lean_compiles=1 if verify_res.compiles else 0,
        )

        return TopicRunResult(
            topic_id=topic.id,
            session_id=session_id,
            success=is_success,
            status=status,
            hermes_success=review_completed,
            lean_compiles=verify_res.compiles,
            lean_has_sorry=verify_res.has_sorry,
            lean_warnings=list(verify_res.warnings),
            lean_version=verify_res.lean_version,
            duration_s=time.time() - t0,
            error=verification_error,
            workflow=workflow,
            stage_results=stage_results,
            explanation=hermes_res.explanation,
            refined_lean_sketch=refined,
            final_lean_sketch=refined,
            canonical_source_sha256=_hashlib.sha256(
                lean_sketch.encode("utf-8")
            ).hexdigest(),
            semantic_contract_sha256=lean_semantic_contract_sha256(lean_sketch),
            semantic_contract_preserved=semantic_contract_preserved,
            verification_source=(
                "hermes_refined"
                if semantic_contract_preserved
                else "canonical_semantic_fallback"
            ),
            tokens_used=hermes_res.tokens_used + review_tokens,
            hermes_model=hermes_res.model_used,
            cache_hit=hermes_res.cache_hit,
            hermes_lean_compiles=(
                _hermes_lean_compiles and semantic_contract_preserved
            ),
            network_retries=hermes_res.network_retries + review_network_retries,
            chain_advance_reason=hermes_res.chain_advance_reason,
        )

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _record_hermes_turns(
        self,
        session_id: str,
        topic: TopicEntry,
        res: HermesResult,
        *,
        preamble: str = "",
        request_lean: bool = True,
        start_index: int = 0,
    ) -> int:
        """Write an exact Hermes exchange and return its next turn index."""
        # Persist every rendered prompt message rather than reconstructing a
        # system/user pair.  This keeps transcript evidence identical to the
        # request whose digest keys the cache, including prose-only reviews.
        index = start_index
        messages = self.hermes.build_messages(
            topic,
            preamble=preamble,
            request_lean=request_lean,
        )
        for message in messages:
            self.client.update_session(
                session_id,
                index,
                message["role"],
                message["content"],
                0,
            )
            index += 1

        if not res.success:
            self.client.update_session(
                session_id,
                index,
                "assistant",
                f"[ERROR] {res.error}",
                res.tokens_used,
            )
            return index + 1

        out = ""
        if res.explanation:
            out += f"Explanation:\n{res.explanation}\n\n"
        if res.refined_lean_sketch:
            out += "```lean\n" + res.refined_lean_sketch + "\n```"

        self.client.update_session(session_id, index, "assistant", out, res.tokens_used)
        index += 1

        if res.reasoning:
            self.client.update_session(
                session_id,
                index,
                "assistant_reasoning",
                res.reasoning,
                0,
            )
            index += 1

        return index

    def _build_artifact_payload(
        self,
        topic: TopicEntry,
        hermes_res: HermesResult,
        verify_res: VerifyResult,
    ) -> dict[str, Any]:
        """Combine all topic data into a comprehensive JSON artifact payload."""
        return {
            "topic": {
                "id": topic.id,
                "title": getattr(topic, "title", topic.id),
                "area": getattr(topic, "area", "unknown"),
                "mathlib_status": getattr(topic, "mathlib_status", "unknown"),
            },
            "hermes": hermes_res.as_dict(),
            "lean": verify_res.as_dict(),
            "timestamp": time.time(),
        }

    @classmethod
    def create_default(
        cls, project_root: Path, *, require_cli: bool = False
    ) -> GaussRunner:
        """Convenience constructor using defaults for the FEP project.

        If ``require_cli`` is True and `gauss` is missing, raises RuntimeError.
        """
        ok, msg = check_gauss_cli(project_root, require=require_cli)
        if not ok:
            raise RuntimeError(msg)

        lean = LeanVerifier(project_root / "lean", project_root)
        hermes = HermesExplainer(HermesConfig.from_settings(project_root))
        # Same resolution order the preflight validation uses, so the run
        # never writes to a directory validation did not check.
        gauss_home: str | Path | None = resolve_gauss_home(project_root)
        client = OpenGaussClient(gauss_home=gauss_home)
        return cls(lean, hermes, client, project_root)
