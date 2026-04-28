"""SkillRAG — embed every skill, retrieve top-K at runtime.

The OpenMontage discoverability bug: the agent has to be TOLD which skills
apply to a stage. We fix it by embedding every skill once, then retrieving
the most relevant ones based on (pipeline, stage, intent) at runtime.

Storage: SQLite, vectors stored as JSON arrays. We use cosine similarity
in pure Python — no FAISS / pgvector dep on day 1, easy to swap later
if the skill library exceeds ~10k entries.

Embedding model: pluggable. Default is a stub that yields a token-frequency
"pseudo-embedding" so this module is testable without a heavy ML dep.
Wire `sentence-transformers` (BGE-small) via the `embed_fn` kwarg in prod.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import sqlite3
import threading
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

EmbedFn = Callable[[str], list[float]]


def _stub_embed(text: str, dim: int = 256) -> list[float]:
    """Deterministic, hash-based pseudo-embedding. NOT semantic — just stable enough for tests.

    Replace with a real model in production via `SkillRAG(embed_fn=...)`.
    """
    tokens = re.findall(r"[a-zA-Z0-9_]+", text.lower())
    if not tokens:
        return [0.0] * dim
    vec = [0.0] * dim
    for tok in tokens:
        h = int(hashlib.md5(tok.encode("utf-8")).hexdigest(), 16)
        idx = h % dim
        vec[idx] += 1.0
    norm = math.sqrt(sum(x * x for x in vec))
    return [x / norm for x in vec] if norm > 0 else vec


def cosine(a: list[float], b: list[float]) -> float:
    if not a or not b:
        return 0.0
    n = min(len(a), len(b))
    dot = sum(a[i] * b[i] for i in range(n))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


@dataclass
class SkillHit:
    skill_id: str
    title: str
    score: float
    excerpt: str
    tags: list[str]
    path: str


class SkillRAG:
    """Index Markdown skills and retrieve top-K by similarity."""

    def __init__(self, db_path: Path | str, embed_fn: EmbedFn | None = None) -> None:
        self.db_path = Path(db_path).expanduser().resolve()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._embed = embed_fn or _stub_embed
        self._init_schema()

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS skills (
                    skill_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    body TEXT NOT NULL,
                    excerpt TEXT NOT NULL,
                    tags TEXT NOT NULL DEFAULT '[]',  -- JSON
                    path TEXT NOT NULL,
                    embedding TEXT NOT NULL  -- JSON array
                );
                CREATE INDEX IF NOT EXISTS idx_skills_path ON skills(path);
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

    def upsert(
        self,
        *,
        skill_id: str,
        title: str,
        body: str,
        excerpt: str | None = None,
        tags: list[str] | None = None,
        path: str | Path,
    ) -> None:
        emb = self._embed(f"{title}\n\n{body}")
        excerpt_text = (excerpt or body[:280]).strip()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO skills
                    (skill_id, title, body, excerpt, tags, path, embedding)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    skill_id,
                    title,
                    body,
                    excerpt_text,
                    json.dumps(tags or [], ensure_ascii=False),
                    str(Path(path)),
                    json.dumps(emb),
                ),
            )

    def index_directory(self, root: Path | str, glob_pattern: str = "**/*.md") -> int:
        root = Path(root).expanduser().resolve()
        n = 0
        for f in root.glob(glob_pattern):
            if not f.is_file():
                continue
            text = f.read_text(encoding="utf-8", errors="ignore")
            title = self._first_heading(text) or f.stem
            self.upsert(
                skill_id=str(f.relative_to(root)),
                title=title,
                body=text,
                excerpt=text[:280],
                tags=self._tags_from_path(f.relative_to(root)),
                path=str(f),
            )
            n += 1
        return n

    def search(self, query: str, *, top_k: int = 5, min_score: float = 0.05) -> list[SkillHit]:
        q_emb = self._embed(query)
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT skill_id, title, excerpt, tags, path, embedding FROM skills"
            ).fetchall()
        scored: list[SkillHit] = []
        for r in rows:
            emb = json.loads(r["embedding"])
            score = cosine(q_emb, emb)
            if score < min_score:
                continue
            scored.append(
                SkillHit(
                    skill_id=r["skill_id"],
                    title=r["title"],
                    score=score,
                    excerpt=r["excerpt"],
                    tags=json.loads(r["tags"]),
                    path=r["path"],
                )
            )
        scored.sort(key=lambda h: h.score, reverse=True)
        return scored[:top_k]

    def count(self) -> int:
        with self._connect() as conn:
            return int(conn.execute("SELECT COUNT(*) FROM skills").fetchone()[0])

    @staticmethod
    def _first_heading(text: str) -> str | None:
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("#"):
                return line.lstrip("#").strip()
        return None

    @staticmethod
    def _tags_from_path(rel: Path) -> list[str]:
        return [p for p in rel.parts[:-1] if p and not p.startswith(".")]
