---
name: talking-head-cut
description: Stage of talking-head pipeline. Placeholder — full director skill ships in v0.3.
---

# talking-head / cut

**Status:** PLACEHOLDER. The schema validates against this file's existence; the
real director skill ships in v0.3 once the pipeline has been driven end-to-end
on at least one real video.

**Refer to** `skills/meta/overview.md` for the universal mental model and
`skills/pipelines/clip-factory/cut.md` for the closest reference
implementation if a clip-factory stage with the same name exists.

## Capabilities required

- `cut`

## Artifacts produced

- `cut_clip`

## Review focus (from manifest)

- cuts on natural pauses, not mid-word
- filler removal does not create audio pop or visual jump
