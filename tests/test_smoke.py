"""Smoke tests — every public symbol imports + instantiates."""

from __future__ import annotations


def test_top_level_imports_resolve():
    import agentic_cuts as ac

    assert ac.__version__
    for name in (
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
    ):
        assert hasattr(ac, name), f"agentic_cuts missing public symbol: {name}"


def test_profiles_known_keys():
    from agentic_cuts import PROFILES, profile_for

    for key in ("youtube", "tiktok", "reels", "shorts", "square", "x_video", "youtube_4k"):
        assert key in PROFILES, f"missing profile: {key}"
    # Aliases
    assert profile_for("TikTok").name == "tiktok"
    assert profile_for("yt").name == "youtube"
    assert profile_for("reel").name == "reels"


def test_registry_singleton_is_empty_until_discover():
    from agentic_cuts import registry, ToolRegistry

    assert isinstance(registry, ToolRegistry)
    # discover() against a non-existent package should be a no-op, not crash
    registry.discover("agentic_cuts.tools_does_not_exist")
