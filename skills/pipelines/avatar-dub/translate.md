---
name: avatar-dub-translate
description: Stage 3 of avatar-dub. Translate the source script into the target language. Per-segment word-count balance for plausible lip-sync.
---

# avatar-dub / translate

**Input:** `source_transcript`, `source_word_timings`.
**Output:** `target_script` (segmented JSON keyed to source word ranges).
**Approval:** REQUIRED. The translation choices determine how natural the dub sounds.

## What you do

1. Segment the source script into syntactic chunks (sentences, or sub-sentence beats with pause >300ms between them).
2. For EACH segment, translate to target language with these constraints:
   - Preserve meaning + idiom.
   - Aim for word count within ±30% of source. (Lip-sync drifts when target speech is much longer/shorter than the time window.)
   - Adapt culture-specific references rather than translating literally.
3. Output `target_script` as a JSON array of `{source_start_ms, source_end_ms, source_text, target_text}` so the voice-clone stage knows what to put where.

## LLM provider

`capability=llm_translate` (or fall back to a general LLM with translation prompt). Default winner: GPT-4 / Claude / Gemini, picked via Selector. Pass `temperature=0` and `seed` for reproducibility.

## Review focus

- Per-segment word counts within ±30% of source.
- Idioms localized (not literal translations).
- Names / brand terms preserved unless they have a standard localization.
- Approval pause — Drey signs off on the translation BEFORE we burn TTS minutes.

## What you do NOT do

- No voice cloning yet.
- No lip-sync — target_script is text only.
- Don't re-segment the source word_timings — those are canonical.
