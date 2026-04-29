"""ElevenLabs TTS — premium cloud TTS with voice clone + style control.

Reads ELEVENLABS_API_KEY from env. supports_request returns False if absent
so the selector skips it cleanly.

Pricing (2026): roughly $0.18 / 1k characters on Creator tier; ~$0.30 with clone.
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Any, ClassVar

import httpx

from agentic_cuts.lib.base_tool import BaseTool, Capability, Tier, ToolResult


ELEVENLABS_API_BASE = "https://api.elevenlabs.io/v1"


class ElevenLabsTTS(BaseTool):
    name: ClassVar[str] = "elevenlabs_tts"
    version: ClassVar[str] = "0.1.0"
    capability: ClassVar[Capability] = Capability.TTS
    provider: ClassVar[str] = "elevenlabs"
    tier: ClassVar[Tier] = Tier.PAID
    supports: ClassVar[dict[str, Any]] = {
        "languages": ["en", "es", "fr", "de", "it", "pt", "pl", "nl", "ja", "zh", "hi", "ar"],
        "deterministic": False,
        "seed": True,
        "voice_clone": True,
        "structured_output": False,
        "quality_hint": 9.5,
        "latency_hint": 7.0,
        "uptime_hint": 9.0,
        "model_version": "eleven_multilingual_v2",
    }
    cost_per_unit_usd: ClassVar[float] = 0.00018  # per character, Creator tier baseline

    DEFAULT_VOICE_ID: ClassVar[str] = "21m00Tcm4TlvDq8ikWAM"  # "Rachel"

    def _api_key(self) -> str | None:
        return os.environ.get("ELEVENLABS_API_KEY")

    def supports_request(self, params: dict[str, Any]) -> bool:
        if not self._api_key():
            return False
        lang = (params.get("language") or "en").split("-")[0]
        return lang in self.supports["languages"]

    def estimate_cost(self, params: dict[str, Any]) -> float:
        text = params.get("text") or ""
        return self.cost_per_unit_usd * len(text)

    def execute(self, params: dict[str, Any]) -> ToolResult:
        text = params.get("text") or ""
        if not text:
            return ToolResult(success=False, error="elevenlabs_tts: missing 'text'")
        api_key = self._api_key()
        if not api_key:
            return ToolResult(
                success=False,
                error="ELEVENLABS_API_KEY not set in environment",
            )
        out_dir = Path(params.get("out_dir", "/tmp/agentic-cuts-elevenlabs")).expanduser()
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"el-{uuid.uuid4().hex[:10]}.mp3"
        voice_id = params.get("voice_id") or self.DEFAULT_VOICE_ID
        body = {
            "text": text,
            "model_id": params.get("model_id", "eleven_multilingual_v2"),
            "voice_settings": {
                "stability": params.get("stability", 0.5),
                "similarity_boost": params.get("similarity_boost", 0.75),
                "style": params.get("style", 0.0),
                "use_speaker_boost": params.get("use_speaker_boost", True),
            },
        }
        if params.get("seed") is not None:
            body["seed"] = params["seed"]
        try:
            with httpx.Client(timeout=120) as client:
                resp = client.post(
                    f"{ELEVENLABS_API_BASE}/text-to-speech/{voice_id}",
                    headers={"xi-api-key": api_key, "Content-Type": "application/json"},
                    json=body,
                )
                if resp.status_code != 200:
                    return ToolResult(
                        success=False,
                        error=f"elevenlabs_tts: HTTP {resp.status_code} {resp.text[:200]}",
                    )
                out_path.write_bytes(resp.content)
        except httpx.HTTPError as exc:
            return ToolResult(success=False, error=f"elevenlabs_tts: {exc}")
        actual_cost = self.estimate_cost(params)
        return ToolResult(
            success=True,
            data={"audio_path": str(out_path), "voice_id": voice_id, "format": "mp3"},
            artifacts=[str(out_path)],
            cost_usd=actual_cost,
            seed=params.get("seed"),
            decision_log={
                "voice_id": voice_id,
                "model_id": body["model_id"],
                "char_count": len(text),
            },
        )
