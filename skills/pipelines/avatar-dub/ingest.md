---
name: avatar-dub-ingest
description: Stage 1 of avatar-dub. Probe source talking-head + extract a clean face reference frame.
---

# avatar-dub / ingest

**Input:** path to a talking-head source video.
**Output:** `source_meta` artifact + `face_reference` (a single high-quality keyframe).

## What you do

1. Probe the source with ffprobe — duration, resolution, fps, codec, audio channels, audio level.
2. Reject early on: zero-length audio (no speech to dub), no video stream, multi-speaker (avatar-dub assumes ONE primary face).
3. Extract a clean front-facing keyframe as the face reference. Use mediapipe / facemesh to find the frame where the face is most centered, well-lit, with eyes open.
4. Save the keyframe as `face_reference.png` in the project dir.

## Tool selection

`capability=face_track`. Use Selector with weights favoring `latency` and `cost_efficiency`. Mediapipe is the expected default winner.

## Review focus

- Source video probed cleanly (no ffprobe errors).
- Exactly one face_reference frame extracted, lit, eyes open, mouth roughly closed.
- Source has clear audio (LUFS in range -23 to -12; warn if outside).

## What you do NOT do

- No transcription (next stage).
- No translation.
- No lip-sync work.
- Don't overwrite the source video — produce only metadata + the face_reference image.
