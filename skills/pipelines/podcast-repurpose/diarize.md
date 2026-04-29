---
name: podcast-repurpose-diarize
description: Stage of podcast-repurpose pipeline. Placeholder — full director skill ships in v0.3.
---

# podcast-repurpose / diarize

**Status:** PLACEHOLDER. The schema validates against this file's existence; the
real director skill ships in v0.3 once the pipeline has been driven end-to-end
on at least one real video.

**Refer to** `skills/meta/overview.md` for the universal mental model and
`skills/pipelines/clip-factory/diarize.md` for the closest reference
implementation if a clip-factory stage with the same name exists.

## Capabilities required

- `diarization`

## Artifacts produced

- `speaker_map`
- `speaker_segments`

## Review focus (from manifest)

- each speaker labeled with consistent ID across full episode
- speaker assignments verified against any provided seed clips
