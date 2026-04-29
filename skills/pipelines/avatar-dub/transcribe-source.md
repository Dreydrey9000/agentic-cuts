---
name: avatar-dub-transcribe-source
description: Stage 2 of avatar-dub. Word-level transcription of the source speaker. Drives the translation alignment.
---

# avatar-dub / transcribe_source

**Input:** `source_meta` from ingest.
**Output:** `source_transcript`, `source_word_timings`.

## What you do

1. Run STT via the `Selector` (capability=`stt`). WhisperX wins by default — its word-level timestamps are non-negotiable for the lip-sync stage.
2. Detect the source language. The translate stage uses this as the source.
3. Save artifacts as JSON. Word timings carry `start_ms`, `end_ms`, `confidence`.

## Why word timing matters here

The dub pipeline aligns the TARGET-language audio to the SOURCE-language word boundaries. If the source word "incredible" lands at 2.3s-2.8s, the translated word that replaces it at that beat must start by 2.3s and end by 2.8s. Without word-level timing, lip-sync drift compounds.

## Review focus

- Every word has start_ms AND end_ms AND confidence.
- Confidence < 0.5 segments flagged for the translate stage to consider.
- Source language detected with confidence > 0.9.

## What you do NOT do

- No translation (next stage).
- No voice cloning.
