---
name: animated-explainer-render
description: Stage of animated-explainer pipeline. Placeholder — full director skill ships in v0.3.
---

# animated-explainer / render

**Status:** PLACEHOLDER. The schema validates against this file's existence; the
real director skill ships in v0.3 once the pipeline has been driven end-to-end
on at least one real video.

**Refer to** `skills/meta/overview.md` for the universal mental model and
`skills/pipelines/clip-factory/render.md` for the closest reference
implementation if a clip-factory stage with the same name exists.

## Capabilities required

- `compose`
- `publish`

## Artifacts produced

- `final_explainer`
- `render_report`

## Review focus (from manifest)

- delivery promise gate passes
- ffprobe + frame sample + audio analysis all clean
