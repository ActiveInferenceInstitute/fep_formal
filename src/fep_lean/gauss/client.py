"""open_gauss_client — SQLite-backed OpenGauss session store for fep_lean.

Manages formalization sessions, per-topic conversation turns, artifact export
(JSON + bulk JSONL), and structured operation logs.  All persistence uses the
standard-library ``sqlite3``; no external dependencies are required.

Database layout (``{GAUSS_HOME}/fep_lean_state.db``, 5 tables):
    sessions      — one row per formalization session (topic × run)
    turns         — conversation turns (role / content / token counts)
    artifacts     — JSON artifact manifests (path + sha256)
    logs          — structured operation log events
    hermes_cache  — LLM response cache keyed by topic + sketch hash

Public API:
    OpenGaussClient(gauss_home)
    .create_session(topic_id, area, lean_sketch_original) → session_id str
    .update_session(session_id, turn_index, role, content, tokens) → None
    .close_session(session_id, status, hermes_success, lean_compiles) → None
    .export_session(session_id) → dict
    .export_all_sessions(source) → list[dict]
    .write_artifact(session_id, payload) → Path
    .write_bulk_jsonl(sessions, out_path) → Path
    .log_event(event, **kwargs) → None
    .get_stats() → dict
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import logging
import os
import re
import sqlite3
import threading
import time
import types
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from typing_extensions import Self

log = logging.getLogger(__name__)

_SCHEMA_SQL = """
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS sessions (
    session_id     TEXT PRIMARY KEY,
    topic_id       TEXT NOT NULL,
    area           TEXT NOT NULL,
    lean_sketch    TEXT,
    refined_sketch TEXT,
    status         TEXT DEFAULT 'open',   -- open | success | failed | skipped
    hermes_success INTEGER DEFAULT 0,
    lean_compiles  INTEGER DEFAULT -1,    -- -1 = not run, 0 = fail, 1 = pass
    source         TEXT DEFAULT 'fep_lean',
    created_at     REAL NOT NULL,
    closed_at      REAL,
    duration_s     REAL
);

CREATE TABLE IF NOT EXISTS turns (
    turn_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL REFERENCES sessions(session_id),
    turn_index INTEGER NOT NULL,
    role       TEXT NOT NULL,            -- system | user | assistant
    content    TEXT NOT NULL,
    tokens     INTEGER DEFAULT 0,
    created_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS artifacts (
    artifact_id TEXT PRIMARY KEY,
    session_id  TEXT NOT NULL REFERENCES sessions(session_id),
    file_path   TEXT NOT NULL,
    sha256      TEXT NOT NULL,
    size_bytes  INTEGER NOT NULL,
    created_at  REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS logs (
    log_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    event      TEXT NOT NULL,
    session_id TEXT,
    payload    TEXT,                     -- JSON blob
    ts         REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_sessions_topic  ON sessions(topic_id);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status);
CREATE INDEX IF NOT EXISTS idx_turns_session   ON turns(session_id, turn_index);

CREATE TABLE IF NOT EXISTS hermes_cache (
    cache_key         TEXT PRIMARY KEY,
    topic_id          TEXT NOT NULL,
    stage             TEXT NOT NULL DEFAULT 'verify',
    model             TEXT NOT NULL,
    hermes_result     TEXT NOT NULL,
    lean_sketch_hash  TEXT NOT NULL,
    created_at        REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_hermes_cache_topic ON hermes_cache(topic_id);
"""

_TOPIC_ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
"""Allowed topic_id pattern: alphanumeric with dots, underscores, hyphens."""


def _sha256(data: str | bytes) -> str:
    if isinstance(data, str):
        data = data.encode()
    return hashlib.sha256(data).hexdigest()


@dataclass
class SessionRecord:
    """Full session record loaded from SQLite for export and reporting."""

    session_id: str
    topic_id: str
    area: str
    lean_sketch: str
    refined_sketch: str | None
    status: str
    hermes_success: bool
    lean_compiles: int  # -1 = not run, 0 = fail, 1 = pass
    source: str
    created_at: float
    closed_at: float | None
    duration_s: float | None
    turns: list[dict[str, Any]] = field(default_factory=list)


def resolve_gauss_home(project_root: Path | None = None) -> str | None:
    """Resolve the OpenGauss state directory the same way at every call site.

    Order (highest → lowest): the ``GAUSS_HOME`` environment variable, then
    ``gauss.home`` from ``config/settings.yaml`` when a project root is
    given, then ``None`` (callers fall back to ``~/.gauss``). Validation and
    execution must agree on this order; a divergence lets a full run write
    sessions to a directory that preflight never checked.
    """
    configured = os.environ.get("GAUSS_HOME", "").strip()
    if configured:
        return configured
    if project_root is not None:
        settings_path = Path(project_root) / "config" / "settings.yaml"
        if settings_path.is_file():
            try:
                import yaml  # available via PyYAML in project deps

                raw = yaml.safe_load(settings_path.read_text(encoding="utf-8")) or {}
                home = (raw.get("gauss") or {}).get("home")
                if isinstance(home, str) and home.strip():
                    return home
            except (OSError, yaml.YAMLError, AttributeError) as exc:
                log.warning(
                    "could not read gauss.home from %s (%s: %s); "
                    "sessions will fall back to ~/.gauss",
                    settings_path,
                    type(exc).__name__,
                    exc,
                )
                return None
    return None


class OpenGaussClient:
    """SQLite-backed session store for math-inc OpenGauss Lean formalization.

    Parameters
    ----------
    gauss_home:
        Root dir for all OpenGauss state.  Defaults to ``~/.gauss`` or
        the ``GAUSS_HOME`` environment variable.

    Thread safety
    -------------
    ``check_same_thread=False`` is set so the connection can be used across
    threads for reads.      All **writes** in the current fep_lean pipeline are
    serial (one topic at a time via ``GaussRunner.run_topics_batch``), so no
    additional locking is required.  ``PRAGMA busy_timeout`` is set to reduce
    ``SQLITE_BUSY`` under brief contention.  If concurrent writes are added in future,
    callers must serialize or wrap with a threading.Lock.
    """

    def __init__(self, gauss_home: str | Path | None = None) -> None:
        default_home = resolve_gauss_home()
        self._home = (
            Path(gauss_home or default_home or str(Path.home() / ".gauss"))
            .expanduser()
            .resolve()
        )
        self._artifacts_dir = self._home / "fep_artifacts"
        self._logs_dir = self._home / "fep_logs"
        self._home.mkdir(parents=True, exist_ok=True)
        self._artifacts_dir.mkdir(exist_ok=True)
        self._logs_dir.mkdir(exist_ok=True)
        self._db_path = self._home / "fep_lean_state.db"
        self._lock = threading.RLock()
        self._closed = False
        self._conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        with contextlib.suppress(sqlite3.Error):
            self._conn.execute("PRAGMA busy_timeout = 30000")
        self._conn.executescript(_SCHEMA_SQL)
        self._conn.commit()
        log.debug("OpenGaussClient ready: db=%s", self._db_path)

    def close(self) -> None:
        """Close the SQLite connection and release the client resources."""
        with self._lock:
            if not self._closed:
                self._conn.close()
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

    # ── Session lifecycle ─────────────────────────────────────────────────────

    def create_session(
        self,
        topic_id: str,
        area: str,
        lean_sketch_original: str = "",
        *,
        source: str = "fep_lean",
    ) -> str:
        """Open a new formalization session and return its ``session_id``."""
        if not topic_id or not topic_id.strip():
            raise ValueError("topic_id cannot be empty")
        if not _TOPIC_ID_PATTERN.fullmatch(topic_id.strip()):
            raise ValueError(f"topic_id contains unsafe characters: {topic_id!r}")
        session_id = f"{topic_id}-{uuid.uuid4().hex[:8]}"
        now = time.time()
        self._conn.execute(
            """
            INSERT INTO sessions
                (session_id, topic_id, area, lean_sketch, source, created_at)
            VALUES (?,?,?,?,?,?)
            """,
            (session_id, topic_id, area, lean_sketch_original, source, now),
        )
        self._conn.commit()
        self.log_event("session_opened", session_id=session_id, topic_id=topic_id)
        return session_id

    def update_session(
        self,
        session_id: str,
        turn_index: int,
        role: str,
        content: str,
        tokens: int = 0,
    ) -> None:
        """Append a conversation turn to an open session."""
        now = time.time()
        self._conn.execute(
            """
            INSERT INTO turns (session_id, turn_index, role, content, tokens, created_at)
            VALUES (?,?,?,?,?,?)
            """,
            (session_id, turn_index, role, content, tokens, now),
        )
        self._conn.commit()

    def set_refined_sketch(self, session_id: str, refined_sketch: str) -> None:
        """Store the Hermes-refined Lean sketch in the session record."""
        self._conn.execute(
            "UPDATE sessions SET refined_sketch=? WHERE session_id=?",
            (refined_sketch, session_id),
        )
        self._conn.commit()

    def close_session(
        self,
        session_id: str,
        status: str = "success",
        hermes_success: bool = False,
        lean_compiles: int = -1,
    ) -> None:
        """Close a session, recording final status and metrics."""
        row = self._conn.execute(
            "SELECT created_at FROM sessions WHERE session_id=?", (session_id,)
        ).fetchone()
        now = time.time()
        duration = (now - row["created_at"]) if row else None
        self._conn.execute(
            """
            UPDATE sessions
            SET status=?, hermes_success=?, lean_compiles=?, closed_at=?, duration_s=?
            WHERE session_id=?
            """,
            (status, int(hermes_success), lean_compiles, now, duration, session_id),
        )
        self._conn.commit()
        self.log_event(
            "session_closed",
            session_id=session_id,
            status=status,
            hermes_success=hermes_success,
            lean_compiles=lean_compiles,
        )

    def close_open_session(self, session_id: str, *, error: str = "") -> None:
        """Fail an open session during unexpected runner cleanup.

        Normal topic paths call :meth:`close_session` with their final status.
        This narrow helper is idempotent and will not rewrite an already
        finalized success or failure when an exception is raised during result
        assembly.
        """
        row = self._conn.execute(
            "SELECT status FROM sessions WHERE session_id=?", (session_id,)
        ).fetchone()
        if row is not None and row["status"] == "open":
            self.close_session(
                session_id,
                status="error",
                hermes_success=False,
                lean_compiles=-1,
            )
            if error:
                self.log_event(
                    "session_cleanup_error", session_id=session_id, error=error
                )

    # ── Export ────────────────────────────────────────────────────────────────

    def export_session(self, session_id: str) -> dict[str, Any]:
        """Return a full session record (with all turns) as a plain dict."""
        row = self._conn.execute(
            "SELECT * FROM sessions WHERE session_id=?", (session_id,)
        ).fetchone()
        if row is None:
            raise KeyError(f"session_id not found: {session_id!r}")
        record: dict[str, Any] = dict(row)
        turns = self._conn.execute(
            "SELECT turn_index, role, content, tokens FROM turns "
            "WHERE session_id=? ORDER BY turn_index",
            (session_id,),
        ).fetchall()
        record["turns"] = [dict(t) for t in turns]
        return record

    def export_all_sessions(self, source: str = "fep_lean") -> list[dict[str, Any]]:
        """Return all session records (with turns) for a given ``source`` tag."""
        rows = self._conn.execute(
            "SELECT session_id FROM sessions WHERE source=? ORDER BY created_at",
            (source,),
        ).fetchall()
        return [self.export_session(r["session_id"]) for r in rows]

    def write_artifact(
        self, session_id: str, payload: dict[str, Any], *, label: str = "result"
    ) -> Path:
        """Write ``payload`` as a JSON file; register in ``artifacts`` table.

        Uses an atomic write (temp file → rename) so the artifact is never
        visible on disk in a partial state.  If the DB insert fails, the temp
        file is cleaned up and the exception propagates.
        """
        artifact_id = uuid.uuid4().hex[:12]
        fname = f"{session_id}_{label}_{artifact_id}.json"
        out = self._artifacts_dir / fname
        tmp = out.with_suffix(".tmp")
        content = json.dumps(payload, indent=2, ensure_ascii=False)
        sha = _sha256(content)
        now = time.time()
        # Publish the file first, then register the exact published path.  If
        # registration fails, remove the file so the database and filesystem
        # cannot diverge.
        try:
            tmp.write_text(content, encoding="utf-8")
            os.replace(tmp, out)
            with self._lock:
                self._conn.execute(
                    """
                    INSERT INTO artifacts (artifact_id, session_id, file_path, sha256, size_bytes, created_at)
                    VALUES (?,?,?,?,?,?)
                    """,
                    (
                        artifact_id,
                        session_id,
                        str(out),
                        sha,
                        len(content.encode()),
                        now,
                    ),
                )
                self._conn.commit()
        except Exception:
            out.unlink(missing_ok=True)
            tmp.unlink(missing_ok=True)
            raise
        log.debug("Artifact written: %s (sha256=%s...)", out.name, sha[:8])
        return out

    def write_bulk_jsonl(self, sessions: list[dict[str, Any]], out_path: Path) -> Path:
        """Write all session records as one JSON-Lines file for downstream ingestion."""
        out_path.parent.mkdir(parents=True, exist_ok=True)
        lines: list[str] = []
        for rec in sessions:
            lines.append(json.dumps(rec, ensure_ascii=False))
        out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        log.info("JSONL export: %d sessions → %s", len(lines), out_path)
        return out_path

    # ── Logging ───────────────────────────────────────────────────────────────

    def log_event(
        self, event: str, *, session_id: str | None = None, **kwargs: Any
    ) -> None:
        """Append a structured event to the ``logs`` table and the JSONL file."""
        payload = json.dumps({"session_id": session_id, **kwargs})
        self._conn.execute(
            "INSERT INTO logs (event, session_id, payload, ts) VALUES (?,?,?,?)",
            (event, session_id, payload, time.time()),
        )
        self._conn.commit()
        # Also append to operations.jsonl for easy grep
        log_line = json.dumps(
            {"ts": time.time(), "event": event, "session_id": session_id, **kwargs}
        )
        ops_file = self._logs_dir / "operations.jsonl"
        with ops_file.open("a", encoding="utf-8") as fh:
            fh.write(log_line + "\n")

    # ── Stats ─────────────────────────────────────────────────────────────────

    def get_stats(self) -> dict[str, Any]:
        """Return aggregate statistics across all sessions."""
        row = self._conn.execute("""
            SELECT
                COUNT(*)                                   AS total_sessions,
                SUM(hermes_success)                        AS hermes_ok,
                SUM(CASE WHEN lean_compiles=1 THEN 1 END)  AS lean_ok,
                SUM(CASE WHEN status='failed' THEN 1 END)  AS failed,
                AVG(duration_s)                            AS avg_duration_s
            FROM sessions
        """).fetchone()
        return {
            "total_sessions": row["total_sessions"] or 0,
            "hermes_success": row["hermes_ok"] or 0,
            "lean_compiles": row["lean_ok"] or 0,
            "failed": row["failed"] or 0,
            "avg_duration_s": round(row["avg_duration_s"] or 0, 3),
            "db_path": str(self._db_path),
            "artifacts_dir": str(self._artifacts_dir),
        }

    # ── Hermes result cache ───────────────────────────────────────────────────

    def get_cached_hermes(self, cache_key: str) -> dict[str, Any] | None:
        """Return the cached ``HermesResult`` dict, or ``None`` if not found."""
        row = self._conn.execute(
            "SELECT hermes_result FROM hermes_cache WHERE cache_key=?",
            (cache_key,),
        ).fetchone()
        if row is None:
            return None
        try:
            value = json.loads(row["hermes_result"])
        except (TypeError, json.JSONDecodeError) as exc:
            log.warning("Ignoring malformed Hermes cache entry %s: %s", cache_key, exc)
            return None
        if not isinstance(value, dict):
            log.warning("Ignoring non-object Hermes cache entry %s", cache_key)
            return None
        return value

    def set_cached_hermes(
        self,
        cache_key: str,
        topic_id: str,
        stage: str,
        model: str,
        result_json: str,
        lean_sketch_hash: str,
    ) -> None:
        """Insert or replace a Hermes cache entry."""
        now = time.time()
        self._conn.execute(
            """
            INSERT OR REPLACE INTO hermes_cache
                (cache_key, topic_id, stage, model, hermes_result, lean_sketch_hash, created_at)
            VALUES (?,?,?,?,?,?,?)
            """,
            (cache_key, topic_id, stage, model, result_json, lean_sketch_hash, now),
        )
        self._conn.commit()
        log.debug("Hermes cache set: topic=%s stage=%s", topic_id, stage)

    def prune_hermes_cache(self, ttl_hours: float = 24.0) -> int:
        """Delete cache entries older than ``ttl_hours``.  Returns rows deleted."""
        cutoff = time.time() - ttl_hours * 3600
        cursor = self._conn.execute(
            "DELETE FROM hermes_cache WHERE created_at < ?", (cutoff,)
        )
        self._conn.commit()
        return cursor.rowcount

    def __del__(self) -> None:
        """Best-effort last-resort cleanup for callers that forget ``close``."""
        with contextlib.suppress(Exception):
            self.close()
