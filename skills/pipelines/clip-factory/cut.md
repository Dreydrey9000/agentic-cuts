---
name: clip-factory-cut
description: Stage 4 of clip-factory. Cut the approved candidate windows out of the source video. Frame-perfect when keyframes allow.
---

# clip-factory / cut

**Input:** approved `candidate_clips` from rank.
**Output:** `cut_clips` — one MP4 per candidate, in `projects/<name>/cuts/`.

## What you do

1. For each approved candidate window, build a `CutPlan` via `plan_cut()`. The planner decides:
   - **STREAM_COPY** when the start + end cut points snap within `snap_tolerance_sec` of a keyframe. Lossless, sub-second to execute, no quality loss.
   - **RE_ENCODE** when the cut points fall too far from a keyframe. Slower, slight quality loss, exact-frame.
2. Default tolerance: 0.30 seconds. Override per-clip if the user marked the cut as "exact moment matters" (e.g. a punchline word).
3. Run the cut via `keyframe_aligned_cut(plan, output_path, timeout_sec=600)`. If it times out, fall back to a re-encode with default settings.
4. Probe each output with ffprobe to verify duration is within ±0.5 seconds of the requested window. If off, re-cut with re-encode strategy.
5. Save checkpoint with the list of cut paths + each cut's strategy + drift metrics.

## Tool selection

`capability=cut`. The default tool is `frame_perfect_cut` (in-tree, no external API). No selector decision needed — this is the only cut tool. Future video editors (`mlt`, `auto-editor`) can register as alternatives but the in-tree FFmpeg path is the floor.

## Code shape

```python
from agentic_cuts import plan_cut, keyframe_aligned_cut

cuts_dir = project_dir / "cuts"
cut_paths = []

for clip in approved_candidates:
    plan = plan_cut(
        source=source_video_path,
        start_sec=clip["start_sec"],
        end_sec=clip["end_sec"],
        snap_tolerance_sec=0.30,
    )
    out = cuts_dir / f"{clip['id']}.mp4"
    keyframe_aligned_cut(plan, out)
    cut_paths.append({
        "id": clip["id"],
        "path": str(out),
        "strategy": plan.strategy.value,
        "drift_start_sec": plan.snap_drift_start_sec,
        "drift_end_sec": plan.snap_drift_end_sec,
    })
```

## Review focus

- Every cut clip's duration matches the requested window within tolerance.
- Stream-copy ratio: aim for >50% of clips to use stream-copy (drift within tolerance). Less than that = source has wide GOPs and re-encode is the only path.
- No cut splits a word (verify via the transcript's word-timings — the cut's start_sec must align to a word's start_ms within 100ms).
- Audio is intact: no clicks, no level pop. Check first/last 200ms of each cut.

## When to override the default tolerance

| Situation | Tolerance |
|---|---|
| Drey specified an exact-frame cut on a punchline | 0.0 (force re-encode) |
| Long-form clip, drift is fine | 0.50 |
| Stinger / sting / edit-cut where mood matters more than frame | 0.30 (default) |

## Determinism

FFmpeg cuts are deterministic — same source, same cut points, same byte output. No seed needed. The cache key is `(source_hash, start_sec, end_sec, strategy)`.

## What you do NOT do here

- No vertical crop — that's the next stage.
- No captions — stage after that.
- No audio normalization — render stage handles output levels.
- Don't render the final composite. This stage produces SOURCE clips at their original dimensions.
