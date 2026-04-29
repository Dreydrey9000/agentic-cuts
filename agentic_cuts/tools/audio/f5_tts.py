"""F5-TTS — open-source voice clone TTS. Pair with WhisperX timing for dub work.

Source: https://github.com/SWivid/F5-TTS (MIT).

If the `f5_tts` package isn't importable, supports_request returns False.
This tool reports voice_clone:True so the avatar-dub pipeline picks it for
"match the original speaker's timbre in a different language."
"""

from __future__ import annotations

import importlib
import shutil
import subprocess
import uuid
from pathlib import Path
from typing import Any, ClassVar

from agentic_cuts.lib.base_tool import BaseTool, Capability, Tier, ToolResult


class F5TTS(BaseTool):
    name: ClassVar[str] = "f5_tts"
    version: ClassVar[str] = "0.1.0"
    capability: ClassVar[Capability] = Capability.TTS
    provider: ClassVar[str] = "f5-tts"
    tier: ClassVar[Tier] = Tier.FREE
    supports: ClassVar[dict[str, Any]] = {
        "languages": ["en", "zh", "ja", "ko", "es", "fr", "de", "it", "pt", "ru"],
        "deterministic": True,
        "seed": True,
        "voice_clone": True,  # The wedge — clone with a 5-15 second reference clip
        "structured_output": False,
        "quality_hint": 8.8,
        "latency_hint": 7.0,
        "uptime_hint": 9.0,
        "model_version": "f5-tts-v1",
        "source": "https://github.com/SWivid/F5-TTS",
        "min_reference_seconds": 5,
    }
    cost_per_unit_usd: ClassVar[float] = 0.0

    @staticmethod
    def _available() -> bool:
        try:
            importlib.import_module("f5_tts")
            return True
        except ImportError:
            return shutil.which("f5-tts_infer-cli") is not None

    def supports_request(self, params: dict[str, Any]) -> bool:
        if not self._available():
            return False
        lang = (params.get("language") or "en").split("-")[0]
        return lang in self.supports["languages"]

    def estimate_cost(self, params: dict[str, Any]) -> float:
        return 0.0

    def execute(self, params: dict[str, Any]) -> ToolResult:
        text = params.get("text") or ""
        ref_audio = params.get("reference_audio_path")
        ref_text = params.get("reference_text") or ""
        if not text:
            return ToolResult(success=False, error="f5_tts: missing 'text'")
        if not ref_audio or not Path(ref_audio).exists():
            return ToolResult(
                success=False,
                error="f5_tts: 'reference_audio_path' required (5-15s clean speech sample)",
            )
        if not self._available():
            return ToolResult(
                success=False,
                error="f5-tts not installed (pip install f5-tts)",
            )
        out_dir = Path(params.get("out_dir", "/tmp/agentic-cuts-f5tts")).expanduser()
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"f5-{uuid.uuid4().hex[:10]}.wav"
        cli = shutil.which("f5-tts_infer-cli") or "f5-tts_infer-cli"
        cmd = [
            cli,
            "--model", params.get("model", "F5-TTS"),
            "--ref_audio", str(ref_audio),
            "--ref_text", ref_text,
            "--gen_text", text,
            "--output_dir", str(out_dir),
            "--output_file", out_path.name,
        ]
        if params.get("seed") is not None:
            cmd.extend(["--seed", str(int(params["seed"]))])
        try:
            proc = subprocess.run(
                cmd, capture_output=True, text=True,
                timeout=params.get("timeout_sec", 300),
            )
        except subprocess.TimeoutExpired:
            return ToolResult(success=False, error="f5_tts: timeout")
        if proc.returncode != 0:
            return ToolResult(
                success=False,
                error=f"f5_tts exit {proc.returncode}: {proc.stderr[:300]}",
            )
        if not out_path.exists():
            return ToolResult(success=False, error="f5_tts: no output wav produced")
        return ToolResult(
            success=True,
            data={
                "audio_path": str(out_path),
                "format": "wav",
                "voice_cloned_from": str(ref_audio),
                "language": params.get("language", "en"),
            },
            artifacts=[str(out_path)],
            cost_usd=0.0,
            seed=params.get("seed"),
            decision_log={"engine": "f5-tts", "ref_audio": str(ref_audio)},
        )
