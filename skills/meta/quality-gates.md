---
name: agentic-cuts-quality-gates
description: Use BEFORE rendering. Three gates protect the user from slop output — delivery promise, slideshow risk, cost cap.
---

# Quality Gates — Run These Before Wasting GPU

Three gates fire BEFORE composition. Skipping them means wasting compute on a render that won't pass the smell test.

## Gate 1 — Delivery Promise

The "promise" is what the user asked for: 60-sec talking-head, 9:16, captions, real motion not slideshow. The "validation" runs against the plan to catch obvious mismatches.

```python
from agentic_cuts import DeliveryPromise, validate_plan

promise = DeliveryPromise(
    target_duration_sec=60.0,
    target_aspect="9:16",
    requires_motion=True,
    requires_audio=True,
    requires_captions=True,
)

result = validate_plan(promise, plan_dict)
if not result.passed:
    raise RuntimeError(f"plan does not match promise:\n" + "\n".join(result.failures))
```

Hard failures (block render):
- Duration mismatch outside `duration_tolerance_sec`.
- Aspect mismatch.
- `requires_motion=True` and the plan is >60% still images.
- `requires_audio=True` and there's no audio track.
- `requires_captions=True` and there's no subtitle track.
- `requires_narration=True` and there's no narration audio.

Soft warnings (log, don't block):
- `requires_music=True` but no music track (some pipelines treat this as optional).

## Gate 2 — Slideshow Risk

OpenMontage's strongest contribution. Counts motion clips vs stills vs animated stills (Ken Burns / particles). High risk = "8 still images called a video."

```python
from agentic_cuts import detect_slideshow_risk

risk = detect_slideshow_risk(asset_manifest)
if risk.level.value in ("high", "critical"):
    # Either upgrade the plan or warn the human.
    print(f"slideshow risk: {risk.level.value} ({risk.score:.2f})")
    print("rationale:", risk.rationale)
```

Risk levels:
- `LOW` — motion-heavy plan. Ship it.
- `MEDIUM` — mixed plan. Acceptable for documentary-montage. Yellow light for others.
- `HIGH` — mostly stills with motion FX. Will look like a slideshow. Either swap in real clips or warn the human.
- `CRITICAL` — pure stills, no motion. Block. Pivot to documentary-montage's CLIP-indexed corpus or generate motion clips.

## Gate 3 — Cost Cap

The OpenMontage gap we explicitly fixed. CAP mode RAISES on overrun.

```python
from agentic_cuts import CostTracker, BudgetMode, BudgetExceededError

tracker = CostTracker(total_budget_usd=0.50, mode=BudgetMode.CAP)

# Before every paid action:
rid = tracker.estimate("video_gen_clip_5s", 0.30)
try:
    tracker.reserve(rid)  # raises BudgetExceededError if over
except BudgetExceededError as e:
    # Either downgrade to a cheaper provider OR stop the pipeline.
    raise

# Run the actual tool, then reconcile with the real cost:
tracker.reconcile(rid, actual_cost_usd)
```

Persist the tracker between stages so a multi-stage pipeline doesn't blow past budget mid-render:

```python
tracker.save(project_dir / "cost.json")
# next stage:
tracker = CostTracker.load(project_dir / "cost.json")
```

## When to run each gate

| Stage | Gate 1 (promise) | Gate 2 (slideshow) | Gate 3 (cost) |
|---|:---:|:---:|:---:|
| ingest / transcribe | — | — | every paid call |
| script / scene_plan | — | — | every paid call |
| assets | — | check after | every paid call |
| pre-compose | run | run | snapshot |
| render | — | — | reconcile final |

Gate 1 and Gate 2 are non-negotiable before render. Gate 3 fires every paid call.
