"""Higgsfield Speak v2 — paid talking-head with image + WAV audio → lip-sync.

Reads HIGGSFIELD_API_KEY + HIGGSFIELD_API_SECRET from env. The closed-tier
"wow feature" we queue as OPTIONAL — the OPEN-source path (SadTalker /
LivePortrait + F5-TTS) is the default; Higgsfield wins when the user has
credits AND the pipeline calls for character_id consistency across runs.

Per the v0.3 council brief: integrate as one provider, gated behind keys,
not core. Source: https://higgsfield.ai/mcp
"""

from __future__ import annotations

import os
import time
import uuid
from pathlib import Path
from typing import Any, ClassVar

import httpx

from agentic_cuts.lib.base_tool import BaseTool, Capability, Tier, ToolResult


HIGGSFIELD_API_BASE = "https://cloud.higgsfield.ai/v1"


class HiggsfieldSpeak(BaseTool):
    name: ClassVar[str] = "higgsfield_speak"
    version: ClassVar[str] = "0.1.0"
    capability: ClassVar[Capability] = Capability.LIP_SYNC
    provider: ClassVar[str] = "higgsfield"
    tier: ClassVar[Tier] = Tier.PREMIUM
    supports: ClassVar[dict[str, Any]] = {
        "deterministic": False,  # closed-source, seeds not honored across versions
        "seed": False,
        "voice_clone": False,
        "lip_sync": True,
        "structured_output": True,
        "character_id_persistence": True,  # the actual moat
        "quality_hint": 9.5,
        "latency_hint": 4.0,  # async polling adds 20-180s
        "uptime_hint": 8.5,
        "model_version": "speak-v2",
        "source": "https://higgsfield.ai/mcp",
        "max_clip_seconds": 15,
        "input_types": ["image_url", "audio_url"],
    }
    cost_per_unit_usd: ClassVar[float] = 1.50  # rough — credit-based, hard to map exactly

    def _credentials(self) -> tuple[str | None, str | None]:
        return os.environ.get("HIGGSFIELD_API_KEY"), os.environ.get("HIGGSFIELD_API_SECRET")

    def supports_request(self, params: dict[str, Any]) -> bool:
        api_key, api_secret = self._credentials()
        return bool(api_key and api_secret)

    def estimate_cost(self, params: dict[str, Any]) -> float:
        duration_sec = float(params.get("duration_sec", 5.0))
        return self.cost_per_unit_usd * (duration_sec / 5.0)

    def execute(self, params: dict[str, Any]) -> ToolResult:
        image_url = params.get("image_url")
        audio_url = params.get("audio_url")
        if not image_url or not audio_url:
            return ToolResult(
                success=False,
                error=("higgsfield_speak: requires 'image_url' AND 'audio_url' "
                       "(both must be publicly accessible HTTPS URLs)"),
            )
        api_key, api_secret = self._credentials()
        if not api_key or not api_secret:
            return ToolResult(
                success=False,
                error=("HIGGSFIELD_API_KEY and HIGGSFIELD_API_SECRET both required "
                       "in env. Get keys from https://cloud.higgsfield.ai"),
            )
        out_dir = Path(params.get("out_dir", "/tmp/agentic-cuts-higgsfield")).expanduser()
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"hf-{uuid.uuid4().hex[:10]}.mp4"

        body: dict[str, Any] = {
            "image_url": image_url,
            "audio_url": audio_url,
            "duration": int(params.get("duration_sec", 5)),
        }
        if params.get("character_id"):
            body["character_id"] = params["character_id"]

        try:
            with httpx.Client(timeout=120) as client:
                # Submit job
                resp = client.post(
                    f"{HIGGSFIELD_API_BASE}/speak/v2",
                    headers={
                        "hf-api-key": api_key,
                        "hf-api-secret": api_secret,
                        "Content-Type": "application/json",
                    },
                    json=body,
                )
                if resp.status_code not in (200, 201, 202):
                    return ToolResult(
                        success=False,
                        error=f"higgsfield_speak: HTTP {resp.status_code} {resp.text[:300]}",
                    )
                job = resp.json()
                job_id = job.get("job_set_id") or job.get("id")
                if not job_id:
                    return ToolResult(
                        success=False,
                        error=f"higgsfield_speak: no job_id in submit response",
                    )
                # Poll
                deadline = time.time() + float(params.get("poll_timeout_sec", 300))
                video_url = None
                while time.time() < deadline:
                    poll = client.get(
                        f"{HIGGSFIELD_API_BASE}/jobs/{job_id}",
                        headers={"hf-api-key": api_key, "hf-api-secret": api_secret},
                    )
                    if poll.status_code != 200:
                        return ToolResult(
                            success=False,
                            error=f"higgsfield_speak: poll HTTP {poll.status_code}",
                        )
                    state = poll.json()
                    status = state.get("status", "").lower()
                    if status in ("completed", "succeeded"):
                        video_url = state.get("video_url") or state.get("output", {}).get("url")
                        break
                    if status in ("failed", "error", "canceled"):
                        return ToolResult(
                            success=False,
                            error=f"higgsfield_speak: job {status}: {state.get('error')}",
                        )
                    time.sleep(3)
                if not video_url:
                    return ToolResult(success=False, error="higgsfield_speak: poll timeout")
                dl = client.get(video_url)
                if dl.status_code != 200:
                    return ToolResult(success=False, error=f"higgsfield_speak: download HTTP {dl.status_code}")
                out_path.write_bytes(dl.content)
        except httpx.HTTPError as exc:
            return ToolResult(success=False, error=f"higgsfield_speak: {exc}")

        return ToolResult(
            success=True,
            data={
                "video_path": str(out_path),
                "engine": "higgsfield-speak-v2",
                "character_id": params.get("character_id"),
            },
            artifacts=[str(out_path)],
            cost_usd=self.estimate_cost(params),
            decision_log={
                "engine": "higgsfield-speak-v2",
                "character_id": params.get("character_id"),
                "duration_sec": body["duration"],
            },
        )
