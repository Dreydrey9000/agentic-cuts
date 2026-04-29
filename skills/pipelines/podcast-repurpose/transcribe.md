---
name: podcast-repurpose-transcribe
description: Stage of podcast-repurpose pipeline. Placeholder — full director skill ships in v0.3.
---

# podcast-repurpose / transcribe

**Status:** PLACEHOLDER. The schema validates against this file's existence; the
real director skill ships in v0.3 once the pipeline has been driven end-to-end
on at least one real video.

**Refer to** `skills/meta/overview.md` for the universal mental model and
`skills/pipelines/clip-factory/transcribe.md` for the closest reference
implementation if a clip-factory stage with the same name exists.

## Capabilities required

- `stt`

## Artifacts produced

- `transcript`
- `word_timings`

## Review focus (from manifest)

- word-level timing on every word
- confidence scores surfaced for low-confidence segments
