"""FAL video gen — gateway to Wan, LTX, Kling, Veo, MiniMax via FAL.

Reads FAL_KEY from env. supports_request returns False if absent.
Per Rasmic's recommendation: FAL is the right "first wire" — one integration
unlocks Wan 2.2-TI2V-5B + LTX-2 + Kling + Veo without juggling per-provider keys.

API: https://fal.ai/docs/quick-start#use-the-fal-api-as-a-rest-endpoint
"""

from __future__ import annotations

import os
import time
import uuid
from pathlib import Path
from typing import Any, ClassVar

import httpx

from agentic_cuts.lib.base_tool import BaseTool, Capability, Tier, ToolResult


FAL_API_BASE = "https://queue.fal.run"
FAL_RUN_BASE = "https://fal.run"


class FALVideo(BaseTool):
    """Selector-callable FAL video generator. Default model: wan-2.2-ti2v-5b."""

    name: ClassVar[str] = "fal_video"
    version: ClassVar[str] = "0.1.0"
    capability: ClassVar[Capability] = Capability.VIDEO_GEN
    provider: ClassVar[str] = "fal"
    tier: ClassVar[Tier] = Tier.PAID
    supports: ClassVar[dict[str, Any]] = {
        "deterministic": True,  # FAL respects seeds across most models
        "seed": True,
        "structured_output": True,
        "quality_hint": 8.5,
        "latency_hint": 5.0,
        "uptime_hint": 9.0,
        "models": [
            "fal-ai/wan/v2.2-ti2v-5b",      # primary — quality/VRAM ratio
            "fal-ai/lightricks/ltx-2",        # speed-favorable
            "fal-ai/hunyuan-video",           # quality budget tier
            "fal-ai/minimax/video-01",
            "fal-ai/kling-video/v3",
        ],
        "max_duration_sec": 5.0,  # most generation models cap here
    }
    cost_per_unit_usd: ClassVar[float] = 0.45  # rough per 5-sec clip on wan-ti2v

    DEFAULT_MODEL: ClassVar[str] = "fal-ai/wan/v2.2-ti2v-5b"

    def _api_key(self) -> str | None:
        return os.environ.get("FAL_KEY") or os.environ.get("FAL_API_KEY")

    def supports_request(self, params: dict[str, Any]) -> bool:
        return self._api_key() is not None

    def estimate_cost(self, params: dict[str, Any]) -> float:
        # Rough proportional to requested duration (capped at 5s in most models).
        duration_sec = float(params.get("duration_sec", 5.0))
        return self.cost_per_unit_usd * (duration_sec / 5.0)

    def execute(self, params: dict[str, Any]) -> ToolResult:
        prompt = params.get("prompt") or ""
        if not prompt:
            return ToolResult(success=False, error="fal_video: missing 'prompt'")
        api_key = self._api_key()
        if not api_key:
            return ToolResult(success=False, error="FAL_KEY not set in environment")
        model = params.get("model") or self.DEFAULT_MODEL
        body: dict[str, Any] = {
            "prompt": prompt,
            "duration": params.get("duration_sec", 5.0),
            "aspect_ratio": params.get("aspect_ratio", "9:16"),
        }
        if params.get("seed") is not None:
            body["seed"] = int(params["seed"])
        if params.get("image_url"):
            body["image_url"] = params["image_url"]
        out_dir = Path(params.get("out_dir", "/tmp/agentic-cuts-fal")).expanduser()
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"fal-{uuid.uuid4().hex[:10]}.mp4"
        try:
            with httpx.Client(timeout=300) as client:
                resp = client.post(
                    f"{FAL_RUN_BASE}/{model}",
                    headers={"Authorization": f"Key {api_key}", "Content-Type": "application/json"},
                    json=body,
                )
                if resp.status_code != 200:
                    return ToolResult(
                        success=False,
                        error=f"fal_video: HTTP {resp.status_code} {resp.text[:300]}",
                    )
                payload = resp.json()
                video_url = payload.get("video", {}).get("url") if isinstance(payload.get("video"), dict) else None
                if not video_url:
                    # Some models return {"output": {"url": ...}} or {"video_url": ...}
                    video_url = payload.get("video_url") or payload.get("output", {}).get("url")
                if not video_url:
                    return ToolResult(
                        success=False,
                        error=f"fal_video: no video URL in response: {str(payload)[:200]}",
                    )
                # Download.
                dl = client.get(video_url)
                if dl.status_code != 200:
                    return ToolResult(
                        success=False,
                        error=f"fal_video: download HTTP {dl.status_code}",
                    )
                out_path.write_bytes(dl.content)
        except httpx.HTTPError as exc:
            return ToolResult(success=False, error=f"fal_video: {exc}")

        return ToolResult(
            success=True,
            data={"video_path": str(out_path), "model": model, "format": "mp4"},
            artifacts=[str(out_path)],
            cost_usd=self.estimate_cost(params),
            seed=params.get("seed"),
            decision_log={
                "model": model,
                "aspect_ratio": body["aspect_ratio"],
                "duration_sec": body["duration"],
            },
        )
