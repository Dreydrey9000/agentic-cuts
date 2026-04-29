"""ACE-Step music gen — free, local, top open-source music model (Jan 2026).

Hugging Face: ace-step/ACE-Step-1.5. 4-minute song in 20s on a 4090.

If `acestep` package isn't importable, supports_request returns False.
Pip install:
    pip install acestep
"""

from __future__ import annotations

import importlib
import uuid
from pathlib import Path
from typing import Any, ClassVar

from agentic_cuts.lib.base_tool import BaseTool, Capability, Tier, ToolResult


class AceStepMusic(BaseTool):
    name: ClassVar[str] = "acestep_music"
    version: ClassVar[str] = "0.1.0"
    capability: ClassVar[Capability] = Capability.MUSIC_GEN
    provider: ClassVar[str] = "acestep"
    tier: ClassVar[Tier] = Tier.FREE
    supports: ClassVar[dict[str, Any]] = {
        "deterministic": True,
        "seed": True,
        "structured_output": False,
        "quality_hint": 8.0,
        "latency_hint": 7.0,
        "uptime_hint": 9.0,
        "max_duration_sec": 240.0,
        "model_version": "ace-step-1.5",
    }
    cost_per_unit_usd: ClassVar[float] = 0.0

    @staticmethod
    def _acestep_available() -> bool:
        try:
            importlib.import_module("acestep")
        except ImportError:
            return False
        return True

    def supports_request(self, params: dict[str, Any]) -> bool:
        return self._acestep_available()

    def estimate_cost(self, params: dict[str, Any]) -> float:
        return 0.0

    def execute(self, params: dict[str, Any]) -> ToolResult:
        prompt = params.get("prompt") or ""
        if not prompt:
            return ToolResult(success=False, error="acestep_music: missing 'prompt'")
        if not self._acestep_available():
            return ToolResult(
                success=False,
                error="acestep package not installed (pip install acestep)",
            )
        out_dir = Path(params.get("out_dir", "/tmp/agentic-cuts-acestep")).expanduser()
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"ace-{uuid.uuid4().hex[:10]}.wav"
        try:
            acestep = importlib.import_module("acestep")
            pipeline = acestep.ACEStepPipeline.from_pretrained(
                params.get("model_path", "ace-step/ACE-Step-1.5")
            )
            audio = pipeline(
                prompt=prompt,
                duration=float(params.get("duration_sec", 60.0)),
                seed=int(params.get("seed", 0)),
            )
            import soundfile as sf
            sf.write(str(out_path), audio, 44100)
        except Exception as exc:  # noqa: BLE001
            return ToolResult(success=False, error=f"acestep_music: {type(exc).__name__}: {exc}")
        return ToolResult(
            success=True,
            data={"audio_path": str(out_path), "format": "wav", "sample_rate": 44100},
            artifacts=[str(out_path)],
            cost_usd=0.0,
            seed=params.get("seed"),
            decision_log={"engine": "ace-step-1.5", "deterministic": True},
        )
