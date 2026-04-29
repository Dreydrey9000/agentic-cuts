---
name: talking-head-dub
description: Stage of talking-head pipeline. Placeholder — full director skill ships in v0.3.
---

# talking-head / dub

**Status:** PLACEHOLDER. The schema validates against this file's existence; the
real director skill ships in v0.3 once the pipeline has been driven end-to-end
on at least one real video.

**Refer to** `skills/meta/overview.md` for the universal mental model and
`skills/pipelines/clip-factory/dub.md` for the closest reference
implementation if a clip-factory stage with the same name exists.

## Capabilities required

- `tts`
- `lip_sync`
- `translate`

## Artifacts produced

- `dubbed_clip`

## Review focus (from manifest)

- lip-sync drift under 80ms
- voice-clone preserves original timbre
