"""BaseTool — the single contract every Agentic Cuts tool conforms to.

The agent never knows what's behind a tool; it only sees the contract:
call .execute(params) → get a ToolResult. Predictable in, predictable out.
"""

from __future__ import annotations

import abc
import time
import uuid
from enum import Enum
from typing import Any, ClassVar

from pydantic import BaseModel, ConfigDict, Field


class Capability(str, Enum):
    """The thing a tool produces. The agent groups providers by this."""

    TTS = "tts"
    STT = "stt"
    DIARIZATION = "diarization"
    VIDEO_GEN = "video_gen"
    IMAGE_GEN = "image_gen"
    MUSIC_GEN = "music_gen"
    SFX_GEN = "sfx_gen"
    STOCK_FOOTAGE = "stock_footage"
    STOCK_IMAGE = "stock_image"
    SUBTITLE = "subtitle"
    CAPTION = "caption"
    LIP_SYNC = "lip_sync"
    AVATAR = "avatar"
    UPSCALE = "upscale"
    BG_REMOVE = "bg_remove"
    COLOR_GRADE = "color_grade"
    SCENE_DETECT = "scene_detect"
    TRANSLATE = "translate"
    COMPOSE = "compose"
    CUT = "cut"
    STITCH = "stitch"
    PUBLISH = "publish"


class Tier(str, Enum):
    FREE = "free"          # local / open-source / no API key required
    KEYED_FREE = "keyed_free"  # free with a developer key (Pexels, Unsplash)
    PAID = "paid"
    PREMIUM = "premium"


class ToolResult(BaseModel):
    """What every tool returns. No exceptions, no hidden state."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    success: bool
    data: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    cost_usd: float = 0.0
    duration_ms: int = 0
    artifacts: list[str] = Field(default_factory=list)
    """Absolute paths to files this tool produced (audio, video, images, text)."""
    seed: int | None = None
    """The seed used for generation. Stored so re-runs reproduce byte-identical output."""
    decision_log: dict[str, Any] = Field(default_factory=dict)
    """Why the tool picked this approach. Surfaced in the final audit trail."""
    cache_hit: bool = False


class BaseTool(abc.ABC):
    """Every concrete tool subclasses this and fills the 9 contract fields.

    Discovery is automatic — drop a subclass into the right `tools/<capability>/`
    folder and ToolRegistry picks it up via pkgutil.walk_packages.
    """

    name: ClassVar[str]
    version: ClassVar[str] = "0.1.0"
    capability: ClassVar[Capability]
    provider: ClassVar[str]
    tier: ClassVar[Tier]
    supports: ClassVar[dict[str, Any]] = {}
    fallback_tools: ClassVar[list[str]] = []
    cost_per_unit_usd: ClassVar[float] = 0.0
    """Best-known per-unit cost. Unit depends on capability (per-second of audio,
    per-image, per-second of video, etc.). Override per-tool when known."""
    agent_skills: ClassVar[list[str]] = []
    """Skill IDs that explain how to USE this tool well. Bridges Layer 1 (tools)
    to Layer 2 (skills) for the SkillRAG retriever."""

    def __init__(self) -> None:
        if not getattr(self, "name", None):
            raise ValueError(f"{type(self).__name__} must declare a class-level `name`")
        if not getattr(self, "capability", None):
            raise ValueError(f"{type(self).__name__} must declare a class-level `capability`")
        if not getattr(self, "provider", None):
            raise ValueError(f"{type(self).__name__} must declare a class-level `provider`")

    @abc.abstractmethod
    def execute(self, params: dict[str, Any]) -> ToolResult:
        """Run the tool. Must NEVER raise — wrap any exception into ToolResult.error."""

    def estimate_cost(self, params: dict[str, Any]) -> float:
        """Override when the unit math depends on params (duration, resolution, etc.)."""
        return self.cost_per_unit_usd

    def supports_request(self, params: dict[str, Any]) -> bool:
        """Override to filter early — keeps the selector from scoring impossible matches."""
        return True

    def _run(self, params: dict[str, Any]) -> ToolResult:
        """Internal helper subclasses can call from .execute() to get timing + error fence."""
        run_id = uuid.uuid4().hex[:8]
        start = time.perf_counter()
        try:
            result = self._execute_impl(params)
            elapsed_ms = int((time.perf_counter() - start) * 1000)
            if isinstance(result, ToolResult):
                result.duration_ms = elapsed_ms or result.duration_ms
                return result
            raise TypeError(f"_execute_impl must return ToolResult, got {type(result).__name__}")
        except Exception as exc:  # noqa: BLE001 — boundary catch, surfaced via .error
            elapsed_ms = int((time.perf_counter() - start) * 1000)
            return ToolResult(
                success=False,
                error=f"{type(exc).__name__}: {exc} (run_id={run_id})",
                duration_ms=elapsed_ms,
            )

    def _execute_impl(self, params: dict[str, Any]) -> ToolResult:
        """Subclasses can override this instead of execute() to inherit timing + error fence."""
        raise NotImplementedError

    def __repr__(self) -> str:
        return f"<{type(self).__name__} name={self.name!r} provider={self.provider!r} tier={self.tier!r}>"
