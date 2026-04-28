"""DeliveryPromise — pre-compose validation gate.

The promise is what the user asked for: 60-second talking-head with captions,
real motion not slideshow. The gate runs BEFORE we burn GPU time on render —
catches plans that obviously won't deliver the promise.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

Aspect = Literal["16:9", "9:16", "1:1", "4:5"]


@dataclass
class DeliveryPromise:
    target_duration_sec: float
    target_aspect: Aspect
    requires_motion: bool = True
    """If True and the plan is mostly stills, slideshow gate fires harder."""
    requires_audio: bool = True
    requires_captions: bool = False
    requires_narration: bool = False
    requires_music: bool = False
    style_hints: list[str] = field(default_factory=list)
    """Free-form hints. e.g. ['cinematic', 'documentary', 'meme', 'fast-cut']."""
    duration_tolerance_sec: float = 2.0


@dataclass
class ValidationResult:
    passed: bool
    failures: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "failures": list(self.failures),
            "warnings": list(self.warnings),
        }


def validate_plan(promise: DeliveryPromise, plan: dict[str, Any]) -> ValidationResult:
    """Inspect a render plan against the promise. Block obvious mismatches.

    Plan shape (loose):
        {
            "duration_sec": float,
            "aspect": "16:9" | "9:16" | ...,
            "tracks": {
                "video": [{"type": "image"|"clip", "duration_sec": float, ...}, ...],
                "audio": [{"kind": "music"|"narration"|"sfx", ...}, ...],
                "subtitle": [{"start_sec": float, "end_sec": float, "text": str}, ...]
            }
        }
    """
    result = ValidationResult(passed=True)
    tracks = plan.get("tracks", {}) or {}

    # 1. duration check
    plan_duration = float(plan.get("duration_sec", 0.0))
    if abs(plan_duration - promise.target_duration_sec) > promise.duration_tolerance_sec:
        result.failures.append(
            f"duration mismatch: plan={plan_duration:.1f}s "
            f"vs promised={promise.target_duration_sec:.1f}s "
            f"(tolerance ±{promise.duration_tolerance_sec:.1f}s)"
        )

    # 2. aspect check
    plan_aspect = plan.get("aspect")
    if plan_aspect and plan_aspect != promise.target_aspect:
        result.failures.append(
            f"aspect mismatch: plan={plan_aspect} vs promised={promise.target_aspect}"
        )

    # 3. motion check — if requires_motion is True, the video track had better not be all stills
    video = tracks.get("video", []) or []
    if promise.requires_motion and video:
        n_clips = sum(1 for v in video if v.get("type") == "clip")
        n_stills = sum(1 for v in video if v.get("type") == "image")
        total = n_clips + n_stills
        if total > 0 and n_clips / total < 0.40:
            result.failures.append(
                f"motion gate: {n_clips} motion clip(s) vs {n_stills} still(s) — "
                f"plan is {n_stills / total * 100:.0f}% still images, "
                f"but promise.requires_motion=True"
            )

    # 4. audio presence
    audio = tracks.get("audio", []) or []
    if promise.requires_audio and not audio:
        result.failures.append("audio required but no audio tracks in plan")

    if promise.requires_narration:
        if not any(a.get("kind") == "narration" for a in audio):
            result.failures.append("requires_narration=True but no narration track in plan")

    if promise.requires_music:
        if not any(a.get("kind") == "music" for a in audio):
            result.warnings.append("requires_music=True but no music track in plan")

    # 5. captions
    if promise.requires_captions:
        subs = tracks.get("subtitle", []) or []
        if not subs:
            result.failures.append("requires_captions=True but no subtitle entries in plan")

    result.passed = not result.failures
    return result
