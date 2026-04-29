"""SadTalker — image + audio → talking-head video, free + local.

Source: https://github.com/OpenTalker/SadTalker (Apache 2.0).

Pip install path:
    git clone https://github.com/OpenTalker/SadTalker
    pip install -r SadTalker/requirements.txt

If the `sadtalker` module isn't importable, supports_request returns False
and the Selector skips this tool. The avatar-dub pipeline picks the next
candidate (LivePortrait or Higgsfield Speak when keyed).
"""

from __future__ import annotations

import importlib
import shutil
import subprocess
import uuid
from pathlib import Path
from typing import Any, ClassVar

from agentic_cuts.lib.base_tool import BaseTool, Capability, Tier, ToolResult


class SadTalker(BaseTool):
    name: ClassVar[str] = "sadtalker"
    version: ClassVar[str] = "0.1.0"
    capability: ClassVar[Capability] = Capability.AVATAR
    provider: ClassVar[str] = "sadtalker"
    tier: ClassVar[Tier] = Tier.FREE
    supports: ClassVar[dict[str, Any]] = {
        "deterministic": True,
        "seed": True,
        "voice_clone": False,  # SadTalker drives motion from input audio, doesn't synth speech
        "lip_sync": True,
        "structured_output": False,
        "quality_hint": 7.5,
        "latency_hint": 4.5,
        "uptime_hint": 9.0,
        "model_version": "sadtalker-v0.0.2",
        "source": "https://github.com/OpenTalker/SadTalker",
        "input_types": ["image", "audio"],
        "output_type": "video",
    }
    cost_per_unit_usd: ClassVar[float] = 0.0

    @staticmethod
    def _available() -> bool:
        # SadTalker can be invoked as a Python script OR via its CLI.
        if shutil.which("sadtalker") is not None:
            return True
        try:
            importlib.import_module("sadtalker")
            return True
        except ImportError:
            pass
        # Fallback: check for the standard SadTalker repo layout under common paths.
        for candidate in ("~/.cache/sadtalker", "/opt/sadtalker"):
            if (Path(candidate).expanduser() / "inference.py").exists():
                return True
        return False

    def supports_request(self, params: dict[str, Any]) -> bool:
        return self._available()

    def estimate_cost(self, params: dict[str, Any]) -> float:
        return 0.0

    def execute(self, params: dict[str, Any]) -> ToolResult:
        image_path = params.get("image_path")
        audio_path = params.get("audio_path")
        if not image_path or not audio_path:
            return ToolResult(
                success=False,
                error="sadtalker: 'image_path' and 'audio_path' both required",
            )
        if not Path(image_path).exists() or not Path(audio_path).exists():
            return ToolResult(
                success=False,
                error=f"sadtalker: input file missing: {image_path} / {audio_path}",
            )
        if not self._available():
            return ToolResult(
                success=False,
                error=("sadtalker not installed. Install via: "
                       "git clone https://github.com/OpenTalker/SadTalker && "
                       "pip install -r SadTalker/requirements.txt"),
            )
        out_dir = Path(params.get("out_dir", "/tmp/agentic-cuts-sadtalker")).expanduser()
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"sad-{uuid.uuid4().hex[:10]}.mp4"
        cmd = [
            shutil.which("sadtalker") or "python",
            "-m", "sadtalker.inference",
            "--driven_audio", str(audio_path),
            "--source_image", str(image_path),
            "--result_dir", str(out_dir),
            "--still",
            "--preprocess", params.get("preprocess", "full"),
        ]
        if params.get("seed") is not None:
            cmd.extend(["--seed", str(int(params["seed"]))])
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=params.get("timeout_sec", 600),
            )
        except subprocess.TimeoutExpired:
            return ToolResult(success=False, error="sadtalker: timeout")
        if proc.returncode != 0:
            return ToolResult(
                success=False,
                error=f"sadtalker exit {proc.returncode}: {proc.stderr[:300]}",
            )
        # SadTalker writes <result_dir>/<timestamp>/<...>.mp4 — find the latest.
        produced = sorted(out_dir.rglob("*.mp4"), key=lambda p: p.stat().st_mtime)
        if not produced:
            return ToolResult(success=False, error="sadtalker: no output video produced")
        latest = produced[-1]
        if latest != out_path:
            shutil.copy2(latest, out_path)
        return ToolResult(
            success=True,
            data={"video_path": str(out_path), "engine": "sadtalker"},
            artifacts=[str(out_path)],
            cost_usd=0.0,
            seed=params.get("seed"),
            decision_log={"engine": "sadtalker", "preprocess": params.get("preprocess", "full")},
        )
