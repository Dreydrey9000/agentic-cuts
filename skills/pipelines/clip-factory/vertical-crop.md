---
name: clip-factory-vertical-crop
description: Stage 5 of clip-factory. Crop horizontal cuts to 9:16 vertical with face-tracking. Speaker stays in safe zone.
---

# clip-factory / vertical-crop

**Input:** `cut_clips` (horizontal MP4s).
**Output:** `vertical_clips` — 9:16 MP4s in `projects/<name>/vertical/`.

## What you do

1. For each horizontal cut clip, detect faces frame-by-frame (or every Nth frame for speed).
2. Compute the active speaker's bounding box per second.
3. Build a smoothed crop path — eased between speaker positions, no jitter on cuts.
4. Apply the crop via FFmpeg with `crop` filter or via Remotion (when the timeline UI runs the render). Output 1080x1920.
5. Validate the speaker is in the safe zone: above 65% of frame height (TikTok bottom UI eats the bottom 22%).

## Face-tracking provider

Options:
- **mediapipe** (local, free, fast, deterministic) — default winner.
- **insightface** (heavier, more accurate when faces are partially occluded).
- **OpenCV Haar cascades** (fallback, ancient but works).

`capability=face_track`. Use Selector with weights favoring `latency` and `cost_efficiency`.

## Smoothing — the no-jitter rule

Raw face detection jitters by 10-30 pixels frame-to-frame. The crop must NOT jitter. Apply:

1. Median-filter the bounding box centers over a 0.5-second window.
2. Cubic-spline interpolate between filtered centers.
3. Snap-cut the crop ONLY when the speaker actually changes (detect via diarization speaker swap, not face position).

## Code shape (pseudo)

```python
from agentic_cuts.tools.video import face_track  # capability tool
from agentic_cuts import profile_for

profile = profile_for("tiktok")  # 1080x1920, 22% bottom safe zone

for cut in cut_clips:
    face_track_result = face_track.execute({
        "source": cut["path"],
        "frame_step": 5,  # detect every 5th frame for speed
        "seed": project_seed,
    })

    crop_path = compute_smoothed_crop(face_track_result.data["frames"], profile)

    out = vertical_dir / f"{cut['id']}-vert.mp4"
    apply_crop(cut["path"], crop_path, out, profile)
```

## Review focus

- Active speaker stays within `safe_zone_top_pct` to `1 - safe_zone_bottom_pct` for >95% of frames.
- Face-tracking does not jitter on cuts (visual review by sampling 5 frames around any cut).
- Crop transitions on speaker changes are step-cuts, not slow pans (slow pans look like horror movies).
- Output exactly matches the target media profile dimensions.

## What you do NOT do

- No captions yet — that's stage 6.
- No background blur, no portrait-mode artificial bokeh, no depth-of-field FX. The crop is THE crop. Effects belong in render or in optional enhance.
- Don't crop unconditionally. If the cut's source is already vertical (UGC, phone footage), skip the crop and go straight to caption.
