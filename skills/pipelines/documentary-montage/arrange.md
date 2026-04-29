---
name: documentary-montage-arrange
description: Stage of documentary-montage pipeline. Placeholder — full director skill ships in v0.3.
---

# documentary-montage / arrange

**Status:** PLACEHOLDER. The schema validates against this file's existence; the
real director skill ships in v0.3 once the pipeline has been driven end-to-end
on at least one real video.

**Refer to** `skills/meta/overview.md` for the universal mental model and
`skills/pipelines/clip-factory/arrange.md` for the closest reference
implementation if a clip-factory stage with the same name exists.

## Capabilities required

(none)

## Artifacts produced

- `edit_plan`
- `retrieval_log`

## Review focus (from manifest)

- retrieved clips actually match the beat they were placed at
- decision log shows top-N candidates considered per beat
