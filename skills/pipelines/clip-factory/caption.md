---
name: clip-factory-caption
description: Stage 6 of clip-factory. Burn kinetic captions onto the vertical clips using a brand-kit-aware preset.
---

# clip-factory / caption

**Input:** `vertical_clips` + word-level `transcript` from stage 2.
**Output:** `captioned_clips` — vertical MP4s with captions burned in.

## What you do

1. Load the brand kit's `default_caption_preset`. Default for Drey: `hormozi-style`. For 1BB: `tiktok-yellow-bold`. For VE: `podcast-clean`.
2. Validate the preset against the brand kit's `no_emojis` flag — if True and the preset has `contains_emojis: true`, switch to a no-emoji equivalent.
3. Apply the brand kit's `accent_color_override` if present (overrides the preset's emphasis color with the tenant's brand accent).
4. Generate caption events: word-level timing from the transcript + the preset's `max_words_per_card` to chunk words into "cards."
5. Render the captions:
   - For FFmpeg path: emit ASS subtitle format with the preset's typography + colors. `ffmpeg -vf "ass=captions.ass"` burns them in.
   - For Remotion path (when timeline UI runs): emit a JSON caption track that the Remotion `CaptionRenderer` component consumes. Both paths produce the same visual output.
6. Position captions inside the safe zone — `position.y_pct` from the preset, plus the brand kit's safe-zone overrides if any.
7. Save checkpoint with output paths + the resolved preset name + any overrides applied.

## Caption preset library

Loaded via `discover_presets(CAPTIONS_DIR)`. 20 launch presets, including:

| Preset | When to pick |
|---|---|
| `hormozi-style` | Business / podcast / talking-head — yellow on black, max retention |
| `tiktok-yellow-bold` | High-energy social — bouncy yellow uppercase |
| `mr-beast-pop` | YouTube Shorts thumbnail-match style |
| `podcast-clean` | Long-form podcast clips, no kinetic noise |
| `kinetic-bounce` | One word at a time, bouncy emphasis |
| `youtube-shorts-clean` | YT Shorts default look |
| `ig-reel-classic` | IG-native auto-caption look |
| `cinematic-fade` | Trailer / mood pieces |

The brand kit picks the default. The user can override per-render.

## Code shape

```python
from agentic_cuts import discover_presets, load_brand_kit
from agentic_cuts.captions import CAPTIONS_DIR

presets = discover_presets(CAPTIONS_DIR)
brand = load_brand_kit(tenant_dir / "brand-kit.yaml")

preset_name = override_preset or brand.captions.default_preset
preset = presets[preset_name]

if brand.no_emojis and preset.contains_emojis:
    # Drop to nearest equivalent.
    preset = presets["tiktok-yellow-bold"]  # safe default

if brand.captions.accent_color_override:
    # Tenant overrides the preset's emphasis color.
    preset = preset.model_copy(update={
        "emphasis": preset.emphasis.model_copy(update={
            "color": brand.captions.accent_color_override
        })
    })

# Generate caption events from transcript word timings.
events = chunk_words_into_cards(
    transcript_words,
    max_words_per_card=preset.max_words_per_card,
)

# Render via FFmpeg ASS for now; Remotion path lands with timeline UI.
ass_path = write_ass_file(events, preset, profile)
captioned_out = caption_dir / f"{clip['id']}-cap.mp4"
ffmpeg_burn_subs(vertical_clip, ass_path, captioned_out)
```

## Review focus

- Captions use one of the registered preset styles (no ad-hoc styling).
- Text never overlaps platform UI safe zones (top + bottom).
- Word-level timing aligned to narration / speech (caption appears as the word is spoken).
- Brand kit's `no_emojis` rule is honored (the only emoji-allowing preset is `tiktok-emoji-burst`).
- Accent color override applied when present.

## What you do NOT do here

- No music score — that's optional in render or a separate stage in other pipelines.
- No B-roll insertion — clip-factory uses the original cut footage; B-roll is the podcast-repurpose pipeline's job.
- No re-cropping — vertical-crop is upstream. Captions are a layer on top of the already-cropped vertical clip.
