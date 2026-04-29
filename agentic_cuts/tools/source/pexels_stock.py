"""Pexels stock — free stock video + image with developer key.

Reads PEXELS_API_KEY from env. supports_request returns False if absent.
Free tier allows 200 req/hour, 20k req/month — plenty for a single tenant.

API: https://www.pexels.com/api/
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Any, ClassVar

import httpx

from agentic_cuts.lib.base_tool import BaseTool, Capability, Tier, ToolResult


PEXELS_API_BASE = "https://api.pexels.com"


class PexelsStock(BaseTool):
    name: ClassVar[str] = "pexels_stock"
    version: ClassVar[str] = "0.1.0"
    capability: ClassVar[Capability] = Capability.STOCK_FOOTAGE
    provider: ClassVar[str] = "pexels"
    tier: ClassVar[Tier] = Tier.KEYED_FREE
    supports: ClassVar[dict[str, Any]] = {
        "deterministic": True,  # given fixed query + sort_by=id, results are stable
        "seed": False,
        "quality_hint": 7.0,
        "latency_hint": 8.0,
        "uptime_hint": 9.5,
        "media_types": ["video", "image"],
        "max_results_per_request": 80,
    }
    cost_per_unit_usd: ClassVar[float] = 0.0

    def _api_key(self) -> str | None:
        return os.environ.get("PEXELS_API_KEY")

    def supports_request(self, params: dict[str, Any]) -> bool:
        return self._api_key() is not None

    def estimate_cost(self, params: dict[str, Any]) -> float:
        return 0.0

    def execute(self, params: dict[str, Any]) -> ToolResult:
        query = params.get("query") or ""
        if not query:
            return ToolResult(success=False, error="pexels_stock: missing 'query'")
        api_key = self._api_key()
        if not api_key:
            return ToolResult(success=False, error="PEXELS_API_KEY not set in environment")
        media_type = params.get("media_type", "video")
        if media_type not in ("video", "image"):
            return ToolResult(success=False, error=f"pexels_stock: bad media_type {media_type!r}")
        endpoint = f"{PEXELS_API_BASE}/videos/search" if media_type == "video" else f"{PEXELS_API_BASE}/v1/search"
        per_page = min(int(params.get("per_page", 15)), 80)
        try:
            with httpx.Client(timeout=30) as client:
                resp = client.get(
                    endpoint,
                    headers={"Authorization": api_key},
                    params={
                        "query": query,
                        "per_page": per_page,
                        "page": int(params.get("page", 1)),
                        "orientation": params.get("orientation", "any"),
                    },
                )
                if resp.status_code != 200:
                    return ToolResult(
                        success=False,
                        error=f"pexels_stock: HTTP {resp.status_code} {resp.text[:200]}",
                    )
                payload = resp.json()
        except httpx.HTTPError as exc:
            return ToolResult(success=False, error=f"pexels_stock: {exc}")

        # Normalize to a stable list of {id, url, attribution, width, height, duration_sec, type}
        items = []
        for v in payload.get("videos") or payload.get("photos") or []:
            entry: dict[str, Any] = {
                "id": str(v.get("id")),
                "type": media_type,
                "width": v.get("width"),
                "height": v.get("height"),
                "attribution": v.get("user", {}).get("name") if "user" in v else "Pexels",
                "page_url": v.get("url"),
            }
            if media_type == "video":
                files = sorted(
                    v.get("video_files", []),
                    key=lambda f: (f.get("width") or 0),
                    reverse=True,
                )
                entry["url"] = files[0]["link"] if files else None
                entry["duration_sec"] = v.get("duration")
            else:
                entry["url"] = v.get("src", {}).get("large2x") or v.get("src", {}).get("large")
            items.append(entry)
        # Stable sort by ID for determinism
        items.sort(key=lambda x: x["id"])

        return ToolResult(
            success=True,
            data={"results": items, "query": query, "n_results": len(items)},
            cost_usd=0.0,
            decision_log={"endpoint": endpoint, "per_page": per_page},
        )
