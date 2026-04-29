---
name: agentic-cuts-reviewer
description: Use AFTER each stage to score the output before moving on. Max 2 rounds of revisions per stage.
---

# Reviewer — The Stage Self-Check

Each stage in a pipeline ends with a self-review against the stage's `review_focus` list. The reviewer is YOU (the agent) — the same agent that ran the stage steps back and grades the artifact.

## The 5-question scorecard

For every stage's output, answer these:

1. **Did it produce the artifact the manifest promised?** (e.g. `transcript`, `scene_plan`, `cut_clips`)
2. **Does it pass the stage's `review_focus` checks?** Each item is a rubric the artifact must hit.
3. **Does the decision log explain WHY this output, not just WHAT?** (Selector picks, weight overrides, fallbacks taken.)
4. **Is the artifact internally consistent?** (No clip durations summing to less than total. No scene plan referring to scenes that don't exist. No transcript with words after the audio ends.)
5. **Does it move the pipeline closer to the delivery promise?** (Aspect, duration, motion, captions — all aligned with what the user asked for.)

## Scoring

```
PASS    All 5 questions answered yes. Move to next stage.
RETRY   2 or fewer questions failed. Re-run the stage with the fix encoded as a hint.
        Max 2 retries per stage; on the third failure, escalate to human.
ABORT   3+ failed OR a hard quality gate violated (delivery promise, slideshow risk).
        Stop the pipeline. Save the checkpoint. Notify the human.
```

## Common failure modes

| Failure | Likely cause | Fix |
|---|---|---|
| Transcript missing word-level timing | STT tool not configured for word timings | Re-run with `word_timestamps=True`. |
| Cut clip is mid-word | Cut planner ignored speech pauses | Re-rank cuts using the transcript's pause map. |
| Asset manifest mostly stills despite `requires_motion=True` | Wrong stock provider picked | Override selector with `cost_efficiency *= 0.5` so video providers win. |
| Caption preset emojis on a `no_emojis: true` tenant | Brand kit + preset mismatch | Switch to `tiktok-yellow-bold` or `hormozi-style`. |
| Cost tracker hit cap mid-stage | Estimate was low or fallback fired | Reduce scope (fewer clips, lower res) OR ask the human to raise the cap. |

## The two-round limit

Don't loop forever. The reviewer gets at most 2 retries per stage. If the third attempt still fails the rubric, the pipeline pauses with a clear error and the checkpoint preserved. The human decides whether to continue or kill the run.

This is not a hyperparameter to tune up. Two rounds is plenty for any well-defined stage. More rounds usually means the rubric is wrong, not the output.

## What a healthy review log looks like

```
STAGE: cut
  artifact:        cut_clips (8 clips)
  review_focus:
    [pass] cuts use frame-perfect (keyframe-aligned) where possible (6/8 stream-copy)
    [pass] each clip is within target duration ±1.0s tolerance
  consistency:     pass
  cost:            $0.02 (estimate $0.03)
  decision_log:    selector=ffmpeg_cut weights=default fallback=re-encode for clips 7,8
  → MOVE TO: vertical_crop
```

Concise. Auditable. No filler.
