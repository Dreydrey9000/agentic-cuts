"""Agentic Cuts core engine library.

The shape:
- BaseTool / ToolResult     — contract every tool conforms to
- ToolRegistry              — auto-discovery via pkgutil
- Selector + ScoreCard      — 7-dimension scored provider picking
- Checkpoint                — stage-resumable JSON state
- MediaProfile / PROFILES   — platform render presets
- CostTracker               — estimate / reserve / reconcile with HARD STOP
- DeliveryPromise           — pre-compose validation gate
- SlideshowRisk             — slideshow detection
- RunCache                  — deterministic seed cache (re-runs are free)
- SkillRAG                  — embed + retrieve top-K skills
- frame_perfect_cut         — keyframe-aware FFmpeg cuts
"""

from agentic_cuts.lib.base_tool import BaseTool, ToolResult, Capability, Tier
from agentic_cuts.lib.tool_registry import ToolRegistry, registry
from agentic_cuts.lib.scoring import ScoreCard, Selector, select_provider
from agentic_cuts.lib.checkpoint import Checkpoint
from agentic_cuts.lib.media_profiles import MediaProfile, PROFILES, profile_for
from agentic_cuts.lib.cost_tracker import CostTracker, BudgetMode, BudgetExceededError
from agentic_cuts.lib.delivery_promise import DeliveryPromise, validate_plan, ValidationResult
from agentic_cuts.lib.slideshow_risk import SlideshowRisk, detect_slideshow_risk
from agentic_cuts.lib.run_cache import RunCache, cache_key
from agentic_cuts.lib.skill_rag import SkillRAG
from agentic_cuts.lib.frame_perfect_cut import keyframe_aligned_cut, plan_cut

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
]

__version__ = "0.1.0"
