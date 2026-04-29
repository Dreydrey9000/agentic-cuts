---
name: talking-head-select-takes
description: Stage of talking-head pipeline. Placeholder — full director skill ships in v0.3.
---

# talking-head / select_takes

**Status:** PLACEHOLDER. The schema validates against this file's existence; the
real director skill ships in v0.3 once the pipeline has been driven end-to-end
on at least one real video.

**Refer to** `skills/meta/overview.md` for the universal mental model and
`skills/pipelines/clip-factory/select_takes.md` for the closest reference
implementation if a clip-factory stage with the same name exists.

## Capabilities required

(none)

## Artifacts produced

- `chosen_takes`
- `edit_decisions`

## Review focus (from manifest)

- best take per beat picked, with rationale
- rejected takes have a one-line reason
