---
name: clip-factory-transcribe
description: Stage 2 of clip-factory. Word-level transcription with speaker diarization.
---

# clip-factory / transcribe

**Input:** `source_meta` from ingest.
**Output:** `transcript`, `word_timings`, `speaker_map` artifacts.

## What you do

1. Pick an STT provider via the `Selector` (capability=`stt`). Default winner: WhisperX (local, free, deterministic, word-level timings).
2. Pick a diarization provider (capability=`diarization`). Default: pyannote Community-1.
3. Run STT first. Capture every word with `start_ms`, `end_ms`, and confidence. Low-confidence words (<0.5) get flagged for the rank stage.
4. Run diarization. Match each speaker segment to the word stream. Output a `speaker_map` like `{"SPEAKER_01": "host", "SPEAKER_02": "guest"}` — labels can be human-readable or generic; we re-label them in the rank stage if needed.
5. Save checkpoint with all three artifacts.

## Tool selection knobs

```python
# Latency-favorable for long episodes:
weights = {**DEFAULT_WEIGHTS, "latency": 1.5, "cost_efficiency": 1.5}
selector = Selector(weights)
```

For local providers, set `device="mps"` on Mac, `device="cuda"` on NVIDIA, otherwise CPU.

## Determinism

Pass `seed=<project_seed>` to both tools. WhisperX is deterministic given the same audio + same model checkpoint; pyannote is mostly deterministic with a fixed seed.

## Review focus

- Every word has `start_ms` AND `end_ms` AND `confidence`.
- Speaker labels are consistent across the full episode (not flapping every 30s).
- Speaker count matches expectation: 1 for talking-head, 2 for podcast, 3+ for panel.
- Low-confidence words are flagged, not dropped — the rank stage decides whether to skip those segments.

## What goes WRONG here

- Whisper hallucinates "thank you for watching" when audio fades out → trim trailing audio before STT.
- pyannote merges fast speaker swaps → rerun with smaller `min_segment_len` if guest interrupts host frequently.
- Voice activity detection swallows quiet speech → bypass VAD only if the audio has been pre-cleaned.

## What you do NOT do here

- No virality scoring yet — that's rank.
- No cuts — that's cut.
- Don't fix transcription typos manually. Trust the tool. Low confidence = flag, not edit.
