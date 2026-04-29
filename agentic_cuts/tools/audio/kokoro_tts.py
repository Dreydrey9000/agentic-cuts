"""Kokoro TTS — free, local, top of TTS Arena (Jan 2026). 82M params, sub-300ms.

Hugging Face: hexgrad/Kokoro-82M. Higher quality than Piper, still on-device,
still free. Pip install required:

    pip install kokoro

If the `kokoro` package isn't importable, supports_request returns False.
"""

from __future__ import annotations

import importlib
import uuid
from pathlib import Path
from typing import Any, ClassVar

from agentic_cuts.lib.base_tool import BaseTool, Capability, Tier, ToolResult


class KokoroTTS(BaseTool):
    name: ClassVar[str] = "kokoro_tts"
    version: ClassVar[str] = "0.1.0"
    capability: ClassVar[Capability] = Capability.TTS
    provider: ClassVar[str] = "kokoro"
    tier: ClassVar[Tier] = Tier.FREE
    supports: ClassVar[dict[str, Any]] = {
        "languages": ["en", "es", "fr", "ja", "zh", "hi", "it", "pt"],
        "deterministic": True,
        "seed": True,
        "voice_clone": False,
        "structured_output": False,
        "quality_hint": 8.5,
        "latency_hint": 8.5,
        "uptime_hint": 9.5,
        "model_version": "kokoro-v0.19",
    }
    cost_per_unit_usd: ClassVar[float] = 0.0

    DEFAULT_VOICE: ClassVar[str] = "af_bella"

    @staticmethod
    def _kokoro_available() -> bool:
        try:
            importlib.import_module("kokoro")
        except ImportError:
            return False
        return True

    def supports_request(self, params: dict[str, Any]) -> bool:
        if not self._kokoro_available():
            return False
        lang = (params.get("language") or "en").split("-")[0]
        return lang in self.supports["languages"]

    def estimate_cost(self, params: dict[str, Any]) -> float:
        return 0.0

    def execute(self, params: dict[str, Any]) -> ToolResult:
        text = params.get("text") or ""
        if not text:
            return ToolResult(success=False, error="kokoro_tts: missing 'text' param")
        if not self._kokoro_available():
            return ToolResult(
                success=False,
                error="kokoro package not installed (pip install kokoro)",
            )
        out_dir = Path(params.get("out_dir", "/tmp/agentic-cuts-kokoro")).expanduser()
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"kokoro-{uuid.uuid4().hex[:10]}.wav"
        voice = params.get("voice") or self.DEFAULT_VOICE
        try:
            kokoro = importlib.import_module("kokoro")
            pipeline = kokoro.KPipeline(lang_code=params.get("language", "en")[:2])
            generator = pipeline(text, voice=voice)
            import soundfile as sf  # kokoro depends on this

            audio_chunks = []
            for _, _, audio in generator:
                audio_chunks.append(audio)
            if not audio_chunks:
                return ToolResult(success=False, error="kokoro_tts: no audio produced")
            import numpy as np

            full = np.concatenate(audio_chunks)
            sf.write(str(out_path), full, 24000)
        except Exception as exc:  # noqa: BLE001
            return ToolResult(success=False, error=f"kokoro_tts: {type(exc).__name__}: {exc}")
        return ToolResult(
            success=True,
            data={"audio_path": str(out_path), "voice": voice, "format": "wav", "sample_rate": 24000},
            artifacts=[str(out_path)],
            cost_usd=0.0,
            seed=params.get("seed"),
            decision_log={"voice": voice, "engine": "kokoro-82M", "deterministic": True},
        )
