"""Agentic Cuts — the agentic NLE.

Multi-tenant agentic video production system. Run from inside any AI
coding assistant, drives a real timeline, deterministic by default.

Public API lives in `agentic_cuts.lib`.
"""

from agentic_cuts.lib import (
    BaseTool,
    BudgetExceededError,
    BudgetMode,
    Capability,
    Checkpoint,
    CostTracker,
    DeliveryPromise,
    MediaProfile,
    PROFILES,
    RunCache,
    ScoreCard,
    Selector,
    SkillRAG,
    SlideshowRisk,
    Tier,
    ToolRegistry,
    ToolResult,
    ValidationResult,
    cache_key,
    detect_slideshow_risk,
    keyframe_aligned_cut,
    plan_cut,
    profile_for,
    registry,
    select_provider,
    validate_plan,
)

__version__ = "0.1.0"

__all__ = [
    "BaseTool", "ToolResult", "Capability", "Tier",
    "ToolRegistry", "registry",
    "ScoreCard", "Selector", "select_provider",
    "Checkpoint",
    "MediaProfile", "PROFILES", "profile_for",
    "CostTracker", "BudgetMode", "BudgetExceededError",
    "DeliveryPromise", "validate_plan", "ValidationResult",
    "SlideshowRisk", "detect_slideshow_risk",
    "RunCache", "cache_key",
    "SkillRAG",
    "keyframe_aligned_cut", "plan_cut",
    "__version__",
]
