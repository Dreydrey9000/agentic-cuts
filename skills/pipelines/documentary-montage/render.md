---
name: documentary-montage-render
description: Stage of documentary-montage pipeline. Placeholder — full director skill ships in v0.3.
---

# documentary-montage / render

**Status:** PLACEHOLDER. The schema validates against this file's existence; the
real director skill ships in v0.3 once the pipeline has been driven end-to-end
on at least one real video.

**Refer to** `skills/meta/overview.md` for the universal mental model and
`skills/pipelines/clip-factory/render.md` for the closest reference
implementation if a clip-factory stage with the same name exists.

## Capabilities required

- `compose`
- `stitch`
- `publish`

## Artifacts produced

- `final_montage`
- `render_report`

## Review focus (from manifest)

- slideshow risk gate passes (not 8 stills called a video)
- color grade consistent across stitched clips
