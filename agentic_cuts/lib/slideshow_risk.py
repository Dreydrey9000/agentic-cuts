"""SlideshowRisk — detect "8 still images called a video" plans.

OpenMontage's most useful gate, re-implemented. The risk score weighs the
ratio of stills vs motion clips and how much per-still motion is faked
(Ken Burns, parallax, particles). High risk = we either upgrade the plan
to motion or warn the user before render.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class RiskLevel(str, Enum):
    LOW = "low"        # Real motion footage, stills are decorative.
    MEDIUM = "medium"  # Mixed plan, some Ken Burns, watch out.
    HIGH = "high"      # Mostly stills with motion FX. Likely "looks like a slideshow."
    CRITICAL = "critical"  # Pure slideshow with no faked motion. Block and notify.


@dataclass
class SlideshowRisk:
    level: RiskLevel
    score: float  # 0.0 (no risk) - 1.0 (definite slideshow)
    n_still_images: int
    n_motion_clips: int
    n_animated_stills: int
    """Stills with Ken Burns / parallax / particle FX — count as half-motion."""
    rationale: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "level": self.level.value,
            "score": round(self.score, 3),
            "counts": {
                "still_images": self.n_still_images,
                "motion_clips": self.n_motion_clips,
                "animated_stills": self.n_animated_stills,
            },
            "rationale": list(self.rationale),
        }


def detect_slideshow_risk(asset_manifest: dict[str, Any]) -> SlideshowRisk:
    """Inspect an asset manifest and return a risk report.

    Manifest shape (loose):
        {
            "assets": [
                {"type": "image"|"clip", "duration_sec": float,
                 "motion": "ken_burns"|"parallax"|"particles"|"none"|...,
                 ...},
                ...
            ]
        }
    """
    assets = asset_manifest.get("assets", []) or []
    n_clip = 0
    n_still = 0
    n_anim_still = 0
    rationale: list[str] = []

    for a in assets:
        t = a.get("type")
        if t == "clip":
            n_clip += 1
            continue
        if t == "image":
            motion = (a.get("motion") or "none").lower()
            if motion in {"none", "static"}:
                n_still += 1
            else:
                n_anim_still += 1
            continue

    total = n_clip + n_still + n_anim_still
    if total == 0:
        return SlideshowRisk(
            level=RiskLevel.LOW, score=0.0,
            n_still_images=0, n_motion_clips=0, n_animated_stills=0,
            rationale=["empty manifest — nothing to score"],
        )

    motion_ratio = (n_clip + 0.5 * n_anim_still) / total
    score = 1.0 - motion_ratio  # higher = more slideshow-y

    if motion_ratio >= 0.75:
        level = RiskLevel.LOW
        rationale.append(f"motion-heavy plan ({motion_ratio:.0%} effective motion)")
    elif motion_ratio >= 0.45:
        level = RiskLevel.MEDIUM
        rationale.append(f"mixed plan ({motion_ratio:.0%} effective motion)")
    elif n_anim_still > n_still:
        level = RiskLevel.HIGH
        rationale.append("mostly stills with FX — risk of slideshow look")
    elif n_clip == 0 and n_anim_still == 0:
        level = RiskLevel.CRITICAL
        rationale.append("zero motion — pure slideshow, will not pass the smell test")
    else:
        level = RiskLevel.HIGH
        rationale.append(f"low motion ratio ({motion_ratio:.0%})")

    return SlideshowRisk(
        level=level, score=score,
        n_still_images=n_still, n_motion_clips=n_clip, n_animated_stills=n_anim_still,
        rationale=rationale,
    )
