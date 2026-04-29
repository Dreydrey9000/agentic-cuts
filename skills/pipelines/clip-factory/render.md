---
name: clip-factory-render
description: Stage 7 (final) of clip-factory. Final encode + delivery promise gate + post-render audit. Always pauses for human approval before publishing.
---

# clip-factory / render

**Input:** `captioned_clips`.
**Output:** `final_clips` (publish-ready MP4s) + `render_report` (per-clip audit JSON).
**Approval:** REQUIRED. Drey signs off on each clip before any publish action.

## What you do

1. **Pre-compose validation gate.** For each captioned clip, run `validate_plan(promise, plan_dict)` against a synthesized plan dict capturing duration, aspect, motion, audio, captions. Block render if any hard failure.
2. **Cost reconciliation.** Pull the `CostTracker` from disk (`projects/<name>/cost.json`). Calculate the total spent so far. If reconciliation pushes us past the cap in `BudgetMode.CAP`, abort with a clear error.
3. **Final encode.** Apply the target media profile (`tiktok` / `reels` / `shorts` / etc.) via FFmpeg. Use the profile's exact resolution, fps, codec, bitrate, audio codec, audio bitrate, container, and `-movflags +faststart`. Add `-pix_fmt yuv420p` for broad device compatibility.
4. **Audio normalization.** Target -16 LUFS for short-form social. Use `ffmpeg -af loudnorm=I=-16:TP=-1.5:LRA=11`.
5. **Post-render audit.** For each output:
   - `ffprobe` confirms expected resolution + fps + codec + duration.
   - Sample 10 frames evenly across the clip; verify they're not all-black (slideshow/fail signal).
   - Audio level analysis — confirm not silent + not clipping.
   - File size sanity — too small = empty render, too large = encode misconfig.
6. **Render report.** Per clip: input path, output path, profile used, encode duration, file size, audio LUFS, ffprobe summary, decision log. Save the full report to `projects/<name>/render-report.json`.
7. **Pause for human approval** with the report inline. Drey approves / re-runs / discards each clip individually.

## Code shape

```python
from agentic_cuts import (
    DeliveryPromise, validate_plan, profile_for, CostTracker,
)

profile = profile_for("tiktok")
promise = DeliveryPromise(
    target_duration_sec=clip_duration,
    target_aspect=profile.target_aspect,
    requires_motion=True,
    requires_audio=True,
    requires_captions=True,
    duration_tolerance_sec=1.0,
)

plan_dict = synthesize_plan(captioned_clip)  # duration, aspect, tracks dict
result = validate_plan(promise, plan_dict)
if not result.passed:
    raise PipelineAbort(f"render gate failed:\n{result.failures}")

tracker = CostTracker.load(project_dir / "cost.json")
rid = tracker.estimate("final_encode", 0.0)  # encode is local, costs nothing
tracker.reserve(rid)

# Run the encode.
ffmpeg_encode(captioned_clip, output_path, profile)

tracker.reconcile(rid, 0.0)
tracker.save(project_dir / "cost.json")

# Audit.
audit = post_render_audit(output_path, profile)
render_report.append(audit)
```

## Review focus

- ffprobe shows correct resolution + fps + codec for the target platform (1080x1920 + 30fps + libx264 + aac for TikTok/Reels/Shorts).
- Audio levels normalized (around -16 LUFS, true peak < -1 dB).
- No black frames in the sampled set.
- File size between 2MB and 60MB for a 30-90 second short (rough sanity range).
- Render report saved to `projects/<name>/render-report.json` for audit.

## When to abort

- Delivery promise gate fails any hard requirement.
- Audio is silent (LUFS < -50 dB).
- Output file is < 200KB (means the encode ran but produced nothing watchable).
- Cost cap hit during this stage.

## When to publish

NEVER auto-publish. Even if the human approval gate is set to skip, the clip-factory pipeline does not connect to publish APIs in v0.2. Drey downloads the clip from `projects/<name>/final/` and posts via his own scheduler (Postiz, Yeet, etc.). Publishing is its own stage in v0.3+.

## What you do NOT do

- No re-cutting at this stage. Source-of-truth for cuts is stage 4. If a render fails the audit, re-run the upstream stage that produced the bad input — don't paper over it here.
- No watermarking unless the brand kit's `logo` says so. Default is no watermark.
- No upload, no DM, no auto-post. Render stops at "approved + saved to disk."
