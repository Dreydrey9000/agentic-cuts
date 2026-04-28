"""DeliveryPromise + SlideshowRisk + frame_perfect_cut planning."""

from __future__ import annotations

import pytest

from agentic_cuts import (
    DeliveryPromise,
    detect_slideshow_risk,
    plan_cut,
    validate_plan,
)
from agentic_cuts.lib.frame_perfect_cut import CutStrategy
from agentic_cuts.lib.slideshow_risk import RiskLevel


def test_delivery_promise_passes_when_plan_aligns():
    promise = DeliveryPromise(
        target_duration_sec=60, target_aspect="9:16",
        requires_motion=True, requires_audio=True, requires_captions=True,
    )
    plan = {
        "duration_sec": 60.5,
        "aspect": "9:16",
        "tracks": {
            "video": [{"type": "clip", "duration_sec": 30}, {"type": "clip", "duration_sec": 30}],
            "audio": [{"kind": "narration"}, {"kind": "music"}],
            "subtitle": [{"start_sec": 0, "end_sec": 60, "text": "hi"}],
        },
    }
    res = validate_plan(promise, plan)
    assert res.passed, f"failures: {res.failures}"


def test_delivery_promise_blocks_slideshow():
    promise = DeliveryPromise(
        target_duration_sec=30, target_aspect="9:16", requires_motion=True,
    )
    plan = {
        "duration_sec": 30,
        "aspect": "9:16",
        "tracks": {
            "video": [{"type": "image"}, {"type": "image"}, {"type": "image"}],
            "audio": [{"kind": "narration"}],
        },
    }
    res = validate_plan(promise, plan)
    assert not res.passed
    assert any("motion gate" in f for f in res.failures)


def test_delivery_promise_blocks_aspect_mismatch():
    promise = DeliveryPromise(target_duration_sec=10, target_aspect="9:16")
    plan = {"duration_sec": 10, "aspect": "16:9", "tracks": {"audio": [{"kind": "narration"}]}}
    res = validate_plan(promise, plan)
    assert not res.passed
    assert any("aspect mismatch" in f for f in res.failures)


def test_slideshow_risk_pure_motion_is_low():
    risk = detect_slideshow_risk({
        "assets": [{"type": "clip"}, {"type": "clip"}, {"type": "clip"}, {"type": "clip"}]
    })
    assert risk.level == RiskLevel.LOW


def test_slideshow_risk_pure_stills_is_critical():
    risk = detect_slideshow_risk({
        "assets": [{"type": "image", "motion": "none"}] * 5
    })
    assert risk.level == RiskLevel.CRITICAL


def test_slideshow_risk_animated_stills_is_high_not_critical():
    risk = detect_slideshow_risk({
        "assets": [{"type": "image", "motion": "ken_burns"}] * 5
    })
    assert risk.level in (RiskLevel.HIGH, RiskLevel.MEDIUM)


def test_plan_cut_chooses_stream_copy_when_aligned():
    keyframes = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0]
    plan = plan_cut("/tmp/fake.mp4", 1.0, 4.0,
                    keyframes=keyframes, snap_tolerance_sec=0.1)
    assert plan.strategy == CutStrategy.STREAM_COPY
    assert plan.snap_drift_start_sec == 0.0
    assert plan.snap_drift_end_sec == 0.0


def test_plan_cut_falls_back_to_re_encode_when_drift():
    keyframes = [0.0, 5.0, 10.0]
    plan = plan_cut("/tmp/fake.mp4", 2.7, 7.3,
                    keyframes=keyframes, snap_tolerance_sec=0.30)
    assert plan.strategy == CutStrategy.RE_ENCODE


def test_plan_cut_force_re_encode():
    plan = plan_cut("/tmp/fake.mp4", 1.0, 2.0,
                    keyframes=[0.0, 1.0, 2.0], force_re_encode=True)
    assert plan.strategy == CutStrategy.RE_ENCODE


def test_plan_cut_rejects_zero_duration():
    with pytest.raises(ValueError):
        plan_cut("/tmp/fake.mp4", 1.0, 1.0, keyframes=[0.0, 1.0])
