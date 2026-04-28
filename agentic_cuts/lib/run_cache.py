"""RunCache — deterministic seed cache.

The "what we added" piece OpenMontage doesn't have. Same prompt + seed +
model version + tool version = byte-identical output. We hash the tuple
and store the artifact path; re-running the same step is free.

Storage: SQLite per project, keyed by sha256. Artifacts stay where the
tool wrote them; we just store the path + checksum.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def cache_key(
    *,
    tool_name: str,
    tool_version: str,
    prompt: str,
    seed: int | None,
    model_version: str | None = None,
    extra: dict[str, Any] | None = None,
) -> str:
    """Stable hex digest used everywhere the cache is read or written."""
    payload = {
        "tool_name": tool_name,
        "tool_version": tool_version,
        "prompt": prompt,
        "seed": seed,
        "model_version": model_version,
        "extra": extra or {},
    }
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


@dataclass
class CacheHit:
    key: str
    artifact_paths: list[str]
    cost_usd: float
    created_utc: str
    metadata: dict[str, Any]


class RunCache:
    """SQLite-backed run cache. One DB per project (or per tenant)."""

    def __init__(self, db_path: Path | str) -> None:
        self.db_path = Path(db_path).expanduser().resolve()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._init_schema()

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS run_cache (
                    key TEXT PRIMARY KEY,
                    tool_name TEXT NOT NULL,
                    tool_version TEXT NOT NULL,
                    artifact_paths TEXT NOT NULL,  -- JSON array
                    cost_usd REAL NOT NULL DEFAULT 0.0,
                    created_utc TEXT NOT NULL,
                    metadata TEXT NOT NULL DEFAULT '{}'  -- JSON
                );
                CREATE INDEX IF NOT EXISTS idx_run_cache_tool
                    ON run_cache(tool_name);
                """
            )

    @contextmanager
    def _connect(self) -> sqlite3.Connection:
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            try:
                yield conn
                conn.commit()
            finally:
                conn.close()

    def get(self, key: str) -> CacheHit | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM run_cache WHERE key = ?", (key,)).fetchone()
        if row is None:
            return None
        artifacts = json.loads(row["artifact_paths"])
        # Validate every artifact still exists on disk; treat missing files as a miss.
        for p in artifacts:
            if not Path(p).exists():
                return None
        return CacheHit(
            key=row["key"],
            artifact_paths=artifacts,
            cost_usd=float(row["cost_usd"]),
            created_utc=row["created_utc"],
            metadata=json.loads(row["metadata"]),
        )

    def put(
        self,
        key: str,
        *,
        tool_name: str,
        tool_version: str,
        artifact_paths: list[str | Path],
        cost_usd: float = 0.0,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        paths = [str(Path(p)) for p in artifact_paths]
        meta = json.dumps(metadata or {}, ensure_ascii=False, default=str)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO run_cache
                    (key, tool_name, tool_version, artifact_paths, cost_usd, created_utc, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    key,
                    tool_name,
                    tool_version,
                    json.dumps(paths, ensure_ascii=False),
                    float(cost_usd),
                    datetime.now(timezone.utc).isoformat(),
                    meta,
                ),
            )

    def evict(self, key: str) -> bool:
        with self._connect() as conn:
            cur = conn.execute("DELETE FROM run_cache WHERE key = ?", (key,))
        return cur.rowcount > 0

    def stats(self) -> dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT COUNT(*) AS n, COALESCE(SUM(cost_usd),0) AS saved FROM run_cache"
            ).fetchone()
        return {"entries": int(row["n"]), "cost_usd_saved_on_hits": float(row["saved"])}
