---
name: animated-explainer-caption
description: Stage of animated-explainer pipeline. Placeholder — full director skill ships in v0.3.
---

# animated-explainer / caption

**Status:** PLACEHOLDER. The schema validates against this file's existence; the
real director skill ships in v0.3 once the pipeline has been driven end-to-end
on at least one real video.

**Refer to** `skills/meta/overview.md` for the universal mental model and
`skills/pipelines/clip-factory/caption.md` for the closest reference
implementation if a clip-factory stage with the same name exists.

## Capabilities required

- `caption`

## Artifacts produced

- `caption_track`

## Review focus (from manifest)

- word-level timing aligned to narration
- safe zone respected for the chosen aspect
