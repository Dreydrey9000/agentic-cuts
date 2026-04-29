---
name: avatar-dub-voice-clone
description: Stage 4 of avatar-dub. Synthesize target-language audio in the source speaker's cloned voice.
---

# avatar-dub / voice_clone_synthesize

**Input:** `target_script`, `face_reference` (optional, some providers use it), source video for voice extraction.
**Output:** `target_audio` (WAV), `alignment_map` (per-segment time bounds).

## What you do

1. Extract a 5-15 second clean speech sample from the source video (find the longest single-speaker continuous segment with low background noise — use the `source_word_timings` to locate quiet stretches).
2. Pick a TTS provider via the Selector with weights favoring `voice_clone` capability + `output_quality`:
   ```python
   weights = {**DEFAULT_WEIGHTS, "output_quality": 1.5, "continuity": 1.5}
   candidates = [t for t in registry.by_capability("tts") if t.supports.get("voice_clone")]
   winner, _ = Selector(weights).pick(candidates, task)
   ```
   Default winner: F5-TTS (free, local). Fallback: ElevenLabs (paid, env-keyed).
3. For each segment in `target_script`, synthesize the target_text with the voice clone and the requested time window. If the synthesized clip exceeds `source_end_ms - source_start_ms`, time-stretch with a phase vocoder (no pitch shift) to fit. If shorter, pad with the speaker's natural pause.
4. Concatenate segments preserving the source timing.
5. Save the full audio + an `alignment_map` JSON: `{seg_index, start_ms, end_ms, source_text, target_text, time_stretch_pct}`.

## Why voice clone instead of generic TTS

Generic TTS makes the dubbed clip feel like a robot. The whole point of this pipeline is "same speaker, different language." Voice clone on a clean reference produces audio that listeners attribute to the original speaker. With F5-TTS + a 10-second clean reference, modern listeners can't reliably distinguish the dub from the source on most short-form content.

## Review focus

- Voice timbre preserves the source speaker's character (run a short A/B reference).
- No segment exceeds 110% time-stretch (audible artifacts above that).
- LUFS matches the source within ±2 dB.

## What you do NOT do

- No lip-sync rendering — that's stage 5.
- No facial animation.
- Don't drop low-confidence segments — flag them for the lip-sync stage to render with extra smoothing.
