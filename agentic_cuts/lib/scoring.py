"""7-dimension provider scoring.

Stolen pattern from OpenMontage (re-implemented). Every candidate tool gets
scored across 7 axes, weighted, and the top score wins. The decision log
captures why so the agent can explain it later.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from agentic_cuts.lib.base_tool import BaseTool, Tier

log = logging.getLogger(__name__)


# Weights tuned for "ship-quality first, cost second" — Drey's preference.
DEFAULT_WEIGHTS: dict[str, float] = {
    "task_fit": 1.5,
    "output_quality": 1.3,
    "reliability": 1.2,
    "control": 1.0,
    "cost_efficiency": 0.8,
    "latency": 0.7,
    "continuity": 0.5,
}


@dataclass
class ScoreCard:
    """One tool's score against one task. All fields are 0.0-10.0."""

    tool_name: str
    task_fit: float = 0.0
    """Does this tool DO the requested capability with the requested params?"""
    output_quality: float = 0.0
    """Best-known output quality based on tier + provider reputation."""
    control: float = 0.0
    """How tunable is the output — seeds, prompts, knobs, structured outputs."""
    reliability: float = 0.0
    """API uptime + local reliability. Local tools score high; new APIs score lower."""
    cost_efficiency: float = 0.0
    """Inverse of cost, normalized. Free local = 10; expensive cloud = 2."""
    latency: float = 0.0
    """Inverse of expected latency. Real-time = 10; slow batch = 3."""
    continuity: float = 0.0
    """Style continuity across runs. Determinism + memory = 10; one-shot = 5."""
    notes: list[str] = field(default_factory=list)

    def total(self, weights: dict[str, float] | None = None) -> float:
        w = weights or DEFAULT_WEIGHTS
        return (
            self.task_fit * w["task_fit"]
            + self.output_quality * w["output_quality"]
            + self.control * w["control"]
            + self.reliability * w["reliability"]
            + self.cost_efficiency * w["cost_efficiency"]
            + self.latency * w["latency"]
            + self.continuity * w["continuity"]
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "scores": {
                "task_fit": self.task_fit,
                "output_quality": self.output_quality,
                "control": self.control,
                "reliability": self.reliability,
                "cost_efficiency": self.cost_efficiency,
                "latency": self.latency,
                "continuity": self.continuity,
            },
            "total": round(self.total(), 2),
            "notes": list(self.notes),
        }


def _tier_quality_baseline(tier: Tier) -> float:
    return {Tier.FREE: 5.5, Tier.KEYED_FREE: 6.5, Tier.PAID: 8.0, Tier.PREMIUM: 9.0}[tier]


def _cost_efficiency(cost_per_unit: float) -> float:
    """Inverse-cost score on a 0-10 scale. Free = 10. $0.01/unit ≈ 9. $1/unit ≈ 4. $10/unit ≈ 1."""
    if cost_per_unit <= 0:
        return 10.0
    if cost_per_unit < 0.001:
        return 9.5
    if cost_per_unit < 0.01:
        return 9.0
    if cost_per_unit < 0.1:
        return 7.5
    if cost_per_unit < 1.0:
        return 5.0
    if cost_per_unit < 10.0:
        return 3.0
    return 1.0


class Selector:
    """Score every candidate against a task and pick the winner.

    Pass `weights` to override the global defaults for one decision (e.g.,
    a clip-factory pipeline may favor latency over output_quality).
    """

    def __init__(self, weights: dict[str, float] | None = None) -> None:
        self.weights = weights or DEFAULT_WEIGHTS

    def score(self, tool: BaseTool, task: dict[str, Any]) -> ScoreCard:
        card = ScoreCard(tool_name=tool.name)

        # task_fit — does the tool support the request at all?
        if not tool.supports_request(task):
            card.task_fit = 0.0
            card.notes.append("supports_request=False")
            return card
        card.task_fit = 8.0  # baseline for "yes, can do this"
        if task.get("language") and task["language"] in tool.supports.get("languages", []):
            card.task_fit += 1.0

        # output_quality — tier + premium-provider override
        card.output_quality = _tier_quality_baseline(tool.tier)
        if "quality_hint" in tool.supports:
            card.output_quality = float(tool.supports["quality_hint"])

        # control — supports_seed, structured_outputs, prompt knobs
        card.control = 5.0
        if tool.supports.get("seed"):
            card.control += 2.0
        if tool.supports.get("structured_output"):
            card.control += 1.5
        if tool.supports.get("voice_clone") or tool.supports.get("style_transfer"):
            card.control += 1.5

        # reliability — local + free = high; new cloud APIs = lower
        card.reliability = 9.0 if tool.tier == Tier.FREE else 7.5
        if tool.supports.get("uptime_hint"):
            card.reliability = float(tool.supports["uptime_hint"])

        # cost_efficiency — inverse of estimated cost on this exact task
        try:
            cost = tool.estimate_cost(task)
        except Exception:  # noqa: BLE001
            cost = tool.cost_per_unit_usd
        card.cost_efficiency = _cost_efficiency(cost)

        # latency — local + small = fast; cloud + big = slow
        card.latency = 8.0 if tool.tier == Tier.FREE else 6.0
        if tool.supports.get("latency_hint"):
            card.latency = float(tool.supports["latency_hint"])

        # continuity — determinism + voice/style memory
        card.continuity = 5.0
        if tool.supports.get("seed") or tool.supports.get("deterministic"):
            card.continuity += 3.0
        if tool.supports.get("voice_clone"):
            card.continuity += 1.5

        return card

    def pick(
        self, candidates: list[BaseTool], task: dict[str, Any]
    ) -> tuple[BaseTool | None, list[ScoreCard]]:
        """Return (winner, all_score_cards). Winner is None if no candidate passes task_fit > 0."""
        if not candidates:
            return None, []
        cards = [self.score(t, task) for t in candidates]
        viable = [(t, c) for t, c in zip(candidates, cards, strict=True) if c.task_fit > 0]
        if not viable:
            return None, cards
        winner_tool, _winner_card = max(viable, key=lambda pair: pair[1].total(self.weights))
        return winner_tool, cards


def select_provider(
    candidates: list[BaseTool],
    task: dict[str, Any],
    weights: dict[str, float] | None = None,
) -> tuple[BaseTool | None, list[ScoreCard]]:
    """Convenience function. Use Selector directly when you need to reuse weights."""
    return Selector(weights).pick(candidates, task)
