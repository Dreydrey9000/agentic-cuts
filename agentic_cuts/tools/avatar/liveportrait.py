"""LivePortrait — driven-portrait animation. Better than SadTalker on micro-expressions.

Source: https://github.com/KwaiVGI/LivePortrait (MIT).

If the `liveportrait` package isn't importable, supports_request returns False.
"""

from __future__ import annotations

import importlib
import shutil
import subprocess
import uuid
from pathlib import Path
from typing import Any, ClassVar

from agentic_cuts.lib.base_tool import BaseTool, Capability, Tier, ToolResult


class LivePortrait(BaseTool):
    name: ClassVar[str] = "liveportrait"
    version: ClassVar[str] = "0.1.0"
    capability: ClassVar[Capability] = Capability.AVATAR
    provider: ClassVar[str] = "liveportrait"
    tier: ClassVar[Tier] = Tier.FREE
    supports: ClassVar[dict[str, Any]] = {
        "deterministic": True,
        "seed": True,
        "voice_clone": False,
        "lip_sync": True,
        "structured_output": False,
        "quality_hint": 8.5,
        "latency_hint": 5.0,
        "uptime_hint": 9.0,
        "model_version": "liveportrait-v0.1",
        "source": "https://github.com/KwaiVGI/LivePortrait",
        "input_types": ["image", "video"],
        "output_type": "video",
        "micro_expressions": True,
    }
    cost_per_unit_usd: ClassVar[float] = 0.0

    @staticmethod
    def _available() -> bool:
        try:
            importlib.import_module("liveportrait")
            return True
        except ImportError:
            pass
        for candidate in ("~/.cache/liveportrait", "/opt/liveportrait"):
            if (Path(candidate).expanduser() / "inference.py").exists():
                return True
        return False

    def supports_request(self, params: dict[str, Any]) -> bool:
        return self._available()

    def estimate_cost(self, params: dict[str, Any]) -> float:
        return 0.0

    def execute(self, params: dict[str, Any]) -> ToolResult:
        image_path = params.get("image_path") or params.get("source_image")
        driver_path = params.get("driver_video") or params.get("audio_path")
        if not image_path or not driver_path:
            return ToolResult(
                success=False,
                error="liveportrait: 'source_image' and 'driver_video' both required",
            )
        if not self._available():
            return ToolResult(
                success=False,
                error=("liveportrait not installed. Install via: "
                       "git clone https://github.com/KwaiVGI/LivePortrait"),
            )
        out_dir = Path(params.get("out_dir", "/tmp/agentic-cuts-liveportrait")).expanduser()
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"lp-{uuid.uuid4().hex[:10]}.mp4"
        cmd = [
            "python",
            "-m", "liveportrait.inference",
            "--source", str(image_path),
            "--driver", str(driver_path),
            "--output", str(out_path),
        ]
        if params.get("seed") is not None:
            cmd.extend(["--seed", str(int(params["seed"]))])
        try:
            proc = subprocess.run(
                cmd, capture_output=True, text=True,
                timeout=params.get("timeout_sec", 600),
            )
        except subprocess.TimeoutExpired:
            return ToolResult(success=False, error="liveportrait: timeout")
        if proc.returncode != 0:
            return ToolResult(
                success=False,
                error=f"liveportrait exit {proc.returncode}: {proc.stderr[:300]}",
            )
        if not out_path.exists():
            return ToolResult(success=False, error="liveportrait: no output video produced")
        return ToolResult(
            success=True,
            data={"video_path": str(out_path), "engine": "liveportrait"},
            artifacts=[str(out_path)],
            cost_usd=0.0,
            seed=params.get("seed"),
            decision_log={"engine": "liveportrait"},
        )
