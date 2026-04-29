---
name: documentary-montage-corpus-build
description: Stage of documentary-montage pipeline. Placeholder — full director skill ships in v0.3.
---

# documentary-montage / corpus_build

**Status:** PLACEHOLDER. The schema validates against this file's existence; the
real director skill ships in v0.3 once the pipeline has been driven end-to-end
on at least one real video.

**Refer to** `skills/meta/overview.md` for the universal mental model and
`skills/pipelines/clip-factory/corpus_build.md` for the closest reference
implementation if a clip-factory stage with the same name exists.

## Capabilities required

- `stock_footage`
- `stock_image`

## Artifacts produced

- `corpus_index`
- `source_attribution`

## Review focus (from manifest)

- corpus has minimum N motion clips (not just stills)
- every asset has license + attribution recorded
