"""Piper TTS — free, local, deterministic. The zero-key floor for narration.

Piper runs entirely on-device. The first install downloads the voice model;
subsequent runs are sub-second. Default voice: en_US-libritts.

If the `piper` binary is not on PATH, this tool's supports_request returns
False and the selector skips it. Selector falls back to Kokoro / ElevenLabs.

Install (one of):
    pip install piper-tts
    brew install piper-tts
    https://github.com/rhasspy/piper
"""

from __future__ import annotations

import json
import shutil
import subprocess
import uuid
from pathlib import Path
from typing import Any, ClassVar

from agentic_cuts.lib.base_tool import BaseTool, Capability, Tier, ToolResult


class PiperTTS(BaseTool):
    name: ClassVar[str] = "piper_tts"
    version: ClassVar[str] = "0.1.0"
    capability: ClassVar[Capability] = Capability.TTS
    provider: ClassVar[str] = "piper"
    tier: ClassVar[Tier] = Tier.FREE
    supports: ClassVar[dict[str, Any]] = {
        "languages": ["en", "es", "de", "fr", "it", "nl", "pt", "ru", "uk"],
        "deterministic": True,
        "seed": True,
        "voice_clone": False,
        "structured_output": False,
        "quality_hint": 6.0,
        "latency_hint": 9.5,
        "uptime_hint": 9.9,
        "model_version": "piper-en_US-libritts",
    }
    cost_per_unit_usd: ClassVar[float] = 0.0  # local

    DEFAULT_VOICE: ClassVar[str] = "en_US-libritts"

    def supports_request(self, params: dict[str, Any]) -> bool:
        if shutil.which("piper") is None:
            return False
        lang = (params.get("language") or "en").split("-")[0]
        return lang in self.supports["languages"]

    def estimate_cost(self, params: dict[str, Any]) -> float:
        return 0.0

    def execute(self, params: dict[str, Any]) -> ToolResult:
        text = params.get("text") or ""
        if not text:
            return ToolResult(success=False, error="piper_tts: missing 'text' param")
        if shutil.which("piper") is None:
            return ToolResult(
                success=False,
                error="piper binary not found on PATH (install: pip install piper-tts)",
            )
        out_dir = Path(params.get("out_dir", "/tmp/agentic-cuts-piper")).expanduser()
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"piper-{uuid.uuid4().hex[:10]}.wav"
        voice = params.get("voice") or self.DEFAULT_VOICE
        cmd = ["piper", "--model", voice, "--output_file", str(out_path)]
        try:
            proc = subprocess.run(
                cmd,
                input=text,
                text=True,
                capture_output=True,
                timeout=params.get("timeout_sec", 120),
            )
        except subprocess.TimeoutExpired:
            return ToolResult(success=False, error="piper_tts: timeout")
        if proc.returncode != 0:
            return ToolResult(
                success=False,
                error=f"piper exit {proc.returncode}: {proc.stderr[:200]}",
            )
        return ToolResult(
            success=True,
            data={"audio_path": str(out_path), "voice": voice, "format": "wav"},
            artifacts=[str(out_path)],
            cost_usd=0.0,
            seed=params.get("seed"),
            decision_log={"voice": voice, "engine": "piper", "deterministic": True},
        )
