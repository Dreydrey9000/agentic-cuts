---
name: animated-explainer-assets
description: Stage of animated-explainer pipeline. Placeholder — full director skill ships in v0.3.
---

# animated-explainer / assets

**Status:** PLACEHOLDER. The schema validates against this file's existence; the
real director skill ships in v0.3 once the pipeline has been driven end-to-end
on at least one real video.

**Refer to** `skills/meta/overview.md` for the universal mental model and
`skills/pipelines/clip-factory/assets.md` for the closest reference
implementation if a clip-factory stage with the same name exists.

## Capabilities required

- `image_gen`
- `video_gen`

## Artifacts produced

- `asset_manifest`

## Review focus (from manifest)

- asset count matches scene plan
- slideshow risk gate fires if asset mix is mostly stills
