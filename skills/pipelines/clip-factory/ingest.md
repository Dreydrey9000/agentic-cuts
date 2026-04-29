---
name: clip-factory-ingest
description: Stage 1 of clip-factory. Probe the source video for shape, scene boundaries, and basic health.
---

# clip-factory / ingest

**Input:** path to a long-form video (podcast, talking-head, Zoom recording, livestream).
**Output:** `source_meta` artifact + `scene_map` artifact + saved checkpoint.

## What you do

1. Probe the source with ffprobe. Capture: duration, resolution, fps, codec, audio codec, audio channels, bitrate, file size.
2. Reject early on: zero-length audio, no video stream, unsupported codec.
3. Run scene detection (PySceneDetect or equivalent) to produce a `scene_map`: list of `{start_sec, end_sec, scene_index}`.
4. Validate scene boundaries land on speech pauses, not mid-sentence. If a scene cuts mid-word in the transcript stage later, you'll merge or shift here next time.
5. Save checkpoint with both artifacts + ffprobe output.

## Tool selection

```
capability_required: scene_detect
selector_task:       {"duration_sec": <source_duration>, "min_scene_len": 1.0}
fallback:            uniform 30-second windows if scene_detect fails (rare)
```

## Review focus

- Source video probed cleanly (no ffprobe errors).
- Scene boundaries land on speech pauses, not mid-sentence (verify after transcribe stage).
- Source meta includes duration, resolution, fps, codec, audio config.
- File size is sane (<10GB for v0; warn if larger — the planner is not optimized for that yet).

## What you do NOT do here

- No transcription (that's stage 2).
- No ranking (stage 3).
- No cuts (stage 4).
- Don't trust filenames — re-probe everything.
