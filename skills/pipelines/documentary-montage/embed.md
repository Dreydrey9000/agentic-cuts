---
name: documentary-montage-embed
description: Stage of documentary-montage pipeline. Placeholder — full director skill ships in v0.3.
---

# documentary-montage / embed

**Status:** PLACEHOLDER. The schema validates against this file's existence; the
real director skill ships in v0.3 once the pipeline has been driven end-to-end
on at least one real video.

**Refer to** `skills/meta/overview.md` for the universal mental model and
`skills/pipelines/clip-factory/embed.md` for the closest reference
implementation if a clip-factory stage with the same name exists.

## Capabilities required

(none)

## Artifacts produced

- `corpus_embeddings`

## Review focus (from manifest)

- every clip has a CLIP embedding
- representative frame extracted per clip for the agent to inspect
