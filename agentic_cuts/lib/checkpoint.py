"""Checkpoint — stage-resumable JSON state for a single project run.

Every pipeline stage writes a checkpoint when it completes. If the next
stage fails or the agent crashes, you don't restart from idea — you pick
up at the last successful stage. This is what kills the "wasted GPU" problem.
"""

from __future__ import annotations

import json
import logging
import shutil
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class StageRecord:
    stage: str
    timestamp_utc: str
    data: dict[str, Any]
    """The artifact produced by this stage (script, scene plan, asset manifest, etc.)."""
    cost_usd: float = 0.0
    duration_ms: int = 0
    decision_log: dict[str, Any] | None = None


class Checkpoint:
    """One project = one checkpoint directory. Atomic writes, replayable reads."""

    def __init__(self, project_dir: Path | str) -> None:
        self.project_dir = Path(project_dir).expanduser().resolve()
        self.project_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoint_file = self.project_dir / "checkpoint.json"

    def save(
        self,
        stage: str,
        data: dict[str, Any],
        *,
        cost_usd: float = 0.0,
        duration_ms: int = 0,
        decision_log: dict[str, Any] | None = None,
    ) -> StageRecord:
        record = StageRecord(
            stage=stage,
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
            data=data,
            cost_usd=cost_usd,
            duration_ms=duration_ms,
            decision_log=decision_log,
        )
        state = self._load_state()
        state.setdefault("stages", {})[stage] = {
            "timestamp_utc": record.timestamp_utc,
            "data": record.data,
            "cost_usd": record.cost_usd,
            "duration_ms": record.duration_ms,
            "decision_log": record.decision_log,
        }
        state["latest_stage"] = stage
        state["updated_utc"] = record.timestamp_utc
        self._atomic_write(state)
        return record

    def load(self, stage: str) -> dict[str, Any] | None:
        state = self._load_state()
        return state.get("stages", {}).get(stage, {}).get("data")

    def list_stages(self) -> list[str]:
        return list(self._load_state().get("stages", {}).keys())

    def latest_stage(self) -> str | None:
        return self._load_state().get("latest_stage")

    def total_cost_usd(self) -> float:
        return sum(
            float(s.get("cost_usd", 0.0))
            for s in self._load_state().get("stages", {}).values()
        )

    def clear(self) -> None:
        if self.checkpoint_file.exists():
            self.checkpoint_file.unlink()

    def _load_state(self) -> dict[str, Any]:
        if not self.checkpoint_file.exists():
            return {}
        try:
            return json.loads(self.checkpoint_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            log.error("checkpoint corrupt at %s: %s — starting fresh", self.checkpoint_file, exc)
            backup = self.checkpoint_file.with_suffix(".corrupt.json")
            shutil.copy2(self.checkpoint_file, backup)
            return {}

    def _atomic_write(self, state: dict[str, Any]) -> None:
        tmp = tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            delete=False,
            dir=self.project_dir,
            suffix=".checkpoint.tmp",
        )
        try:
            json.dump(state, tmp, indent=2, ensure_ascii=False, default=str)
            tmp.flush()
            tmp.close()
            Path(tmp.name).replace(self.checkpoint_file)
        except Exception:
            Path(tmp.name).unlink(missing_ok=True)
            raise
