---
name: talking-head-transcribe
description: Stage of talking-head pipeline. Placeholder — full director skill ships in v0.3.
---

# talking-head / transcribe

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
- filler words ("um", "uh", "like") flagged for cut decisions
