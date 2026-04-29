---
name: animated-explainer-narrate
description: Stage of animated-explainer pipeline. Placeholder — full director skill ships in v0.3.
---

# animated-explainer / narrate

**Status:** PLACEHOLDER. The schema validates against this file's existence; the
real director skill ships in v0.3 once the pipeline has been driven end-to-end
on at least one real video.

**Refer to** `skills/meta/overview.md` for the universal mental model and
`skills/pipelines/clip-factory/narrate.md` for the closest reference
implementation if a clip-factory stage with the same name exists.

## Capabilities required

- `tts`

## Artifacts produced

- `narration_audio`

## Review focus (from manifest)

- narration matches script word-for-word
- audio levels target -16 LUFS
