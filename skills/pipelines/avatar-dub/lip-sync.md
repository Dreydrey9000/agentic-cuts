---
name: avatar-dub-lip-sync
description: Stage 5 of avatar-dub. Render the dubbed clip with lips matching the target audio. ALWAYS pause for human approval.
---

# avatar-dub / lip_sync

**Input:** source video + `target_audio` + `alignment_map` + `face_reference`.
**Output:** `dubbed_clip` — source video with lips moving to match the target audio.
**Approval:** REQUIRED. This is the wow moment. Drey signs off before render finalization.

## What you do

1. Pick a lip-sync provider via the Selector. Weights for this stage favor `output_quality` and `lip_sync` capability:
   ```python
   weights = {**DEFAULT_WEIGHTS, "output_quality": 1.6, "control": 1.3}
   candidates = [t for t in registry.all()
                 if "lip_sync" in t.supports and t.supports["lip_sync"]]
   winner, _ = Selector(weights).pick(candidates, task)
   ```
   Default winner order:
   - **LivePortrait** (FREE, micro-expressions strong) — primary if installed
   - **SadTalker** (FREE, baseline) — fallback
   - **Higgsfield Speak v2** (PREMIUM, character_id consistency) — wins when keyed AND user has burned credits before on this character
2. Run inference: `(source_video OR face_reference, target_audio) → dubbed_clip`.
3. Validate lip-sync drift: extract phonemes from target audio, extract mouth landmarks per frame, compute drift. Hard fail if any 0.5-second window drifts > 80ms.
4. Validate face stability: no warping on wide-mouth phonemes (a, o, ee), no eye-area glitches.
5. Save `dubbed_clip.mp4` + a `drift_report.json`.

## Why pause for human approval

This is THE moment that determines whether the dub feels real or uncanny. The drift report catches mechanical issues but human eyes catch the "soul" issue (does this look like the same person?). Always pause and present the dubbed clip side-by-side with the source.

## Review focus

- Lip-sync drift < 80ms in every 0.5-second window.
- No facial warping on wide-mouth phonemes.
- Eye and brow movements preserved (micro-expressions).
- Background unchanged — only the face moves.

## What you do NOT do

- No final encode here — that's the render stage.
- No publishing.
- Don't smooth out the cuts that the source video had — preserve the original edits.
