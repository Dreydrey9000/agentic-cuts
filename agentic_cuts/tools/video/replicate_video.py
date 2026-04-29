"""Replicate video gen — fallback gateway when FAL doesn't host the desired model.

Reads REPLICATE_API_TOKEN from env. supports_request returns False if absent.
Used for: open-weights models FAL hasn't picked up + community-tuned variants.

API: https://replicate.com/docs/reference/http
"""

from __future__ import annotations

import os
import time
import uuid
from pathlib import Path
from typing import Any, ClassVar

import httpx

from agentic_cuts.lib.base_tool import BaseTool, Capability, Tier, ToolResult


REPLICATE_API_BASE = "https://api.replicate.com/v1"


class ReplicateVideo(BaseTool):
    name: ClassVar[str] = "replicate_video"
    version: ClassVar[str] = "0.1.0"
    capability: ClassVar[Capability] = Capability.VIDEO_GEN
    provider: ClassVar[str] = "replicate"
    tier: ClassVar[Tier] = Tier.PAID
    supports: ClassVar[dict[str, Any]] = {
        "deterministic": True,
        "seed": True,
        "quality_hint": 8.0,
        "latency_hint": 4.0,  # cold start is real
        "uptime_hint": 8.5,
        "models": [
            "lucataco/cogvideo-5b",
            "fofr/wan-2-1-i2v-720p",
        ],
        "max_duration_sec": 10.0,
    }
    cost_per_unit_usd: ClassVar[float] = 0.30  # rough; varies per model on per-second-of-output basis

    def _api_token(self) -> str | None:
        return os.environ.get("REPLICATE_API_TOKEN") or os.environ.get("REPLICATE_API_KEY")

    def supports_request(self, params: dict[str, Any]) -> bool:
        return self._api_token() is not None

    def estimate_cost(self, params: dict[str, Any]) -> float:
        duration_sec = float(params.get("duration_sec", 5.0))
        return self.cost_per_unit_usd * (duration_sec / 5.0)

    def execute(self, params: dict[str, Any]) -> ToolResult:
        prompt = params.get("prompt") or ""
        if not prompt:
            return ToolResult(success=False, error="replicate_video: missing 'prompt'")
        token = self._api_token()
        if not token:
            return ToolResult(success=False, error="REPLICATE_API_TOKEN not set in environment")
        model = params.get("model") or self.supports["models"][0]
        body: dict[str, Any] = {
            "version": params.get("version") or model.split("/")[-1],
            "input": {
                "prompt": prompt,
                "num_frames": int(params.get("duration_sec", 5.0) * 24),
            },
        }
        if params.get("seed") is not None:
            body["input"]["seed"] = int(params["seed"])
        if params.get("image_url"):
            body["input"]["image"] = params["image_url"]

        out_dir = Path(params.get("out_dir", "/tmp/agentic-cuts-replicate")).expanduser()
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"rep-{uuid.uuid4().hex[:10]}.mp4"

        try:
            with httpx.Client(timeout=600) as client:
                # Create prediction
                start_resp = client.post(
                    f"{REPLICATE_API_BASE}/predictions",
                    headers={"Authorization": f"Token {token}", "Content-Type": "application/json"},
                    json=body,
                )
                if start_resp.status_code not in (200, 201):
                    return ToolResult(
                        success=False,
                        error=f"replicate_video: HTTP {start_resp.status_code} {start_resp.text[:300]}",
                    )
                pred = start_resp.json()
                pred_id = pred["id"]
                # Poll for completion
                deadline = time.time() + float(params.get("poll_timeout_sec", 600))
                while time.time() < deadline:
                    poll = client.get(
                        f"{REPLICATE_API_BASE}/predictions/{pred_id}",
                        headers={"Authorization": f"Token {token}"},
                    )
                    if poll.status_code != 200:
                        return ToolResult(
                            success=False,
                            error=f"replicate_video: poll HTTP {poll.status_code}",
                        )
                    state = poll.json()
                    status = state.get("status")
                    if status == "succeeded":
                        output = state.get("output")
                        url = (output[0] if isinstance(output, list) else output) if output else None
                        if not url:
                            return ToolResult(
                                success=False,
                                error=f"replicate_video: succeeded but no output URL",
                            )
                        dl = client.get(url)
                        if dl.status_code != 200:
                            return ToolResult(success=False, error=f"replicate_video: download HTTP {dl.status_code}")
                        out_path.write_bytes(dl.content)
                        break
                    if status in ("failed", "canceled"):
                        return ToolResult(
                            success=False,
                            error=f"replicate_video: prediction {status}: {state.get('error')}",
                        )
                    time.sleep(2)
                else:
                    return ToolResult(success=False, error="replicate_video: poll timeout")
        except httpx.HTTPError as exc:
            return ToolResult(success=False, error=f"replicate_video: {exc}")

        return ToolResult(
            success=True,
            data={"video_path": str(out_path), "model": model, "format": "mp4"},
            artifacts=[str(out_path)],
            cost_usd=self.estimate_cost(params),
            seed=params.get("seed"),
            decision_log={"model": model, "duration_sec": params.get("duration_sec")},
        )
