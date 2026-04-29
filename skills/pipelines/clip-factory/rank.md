---
name: clip-factory-rank
description: Stage 3 of clip-factory. Pick the most viral 30-90 second windows from the transcript. Always pause for human approval.
---

# clip-factory / rank

**Input:** `transcript`, `word_timings`, `speaker_map`.
**Output:** `virality_scorecard`, `candidate_clips` (8-15 ranked windows).
**Approval:** REQUIRED. Drey signs off on the picks before we cut.

## What you do

1. Slide a window across the transcript. Default sizes: 30s, 45s, 60s, 90s. Windows must end on natural sentence boundaries (period or long pause >700ms).
2. Score each candidate window across 5 dimensions:
   - **Hook strength** — does the first 3 seconds grab? (LLM judgment + signal words).
   - **Payoff** — does the ending land? (LLM + word-level emotion model if available).
   - **Standalone meaning** — does this make sense without context? (LLM, low score for "as I was saying earlier" openers).
   - **Replayability** — is there a quotable / shareable moment? (LLM extraction of any sentence that could be a tweet).
   - **Length fit** — closer to 30s and 60s wins for TikTok/Reels; 90s for YouTube Shorts longer-form.
3. Drop overlapping candidates — if two windows overlap >50%, keep the higher-scored one.
4. Output the top 8-15 (configurable) sorted by total score.
5. Save checkpoint.

## Scoring rubric (LLM prompt template)

```
Rate this 30-90 second clip from a podcast on each axis 1-10:
- HOOK: Does the first 3 seconds grab the listener? (1=boring, 10=can't scroll past)
- PAYOFF: Does the ending land? (1=trails off, 10=quotable last line)
- STANDALONE: Can someone who hasn't heard the rest of the show follow this? (1=needs context, 10=fully self-contained)
- REPLAYABILITY: Is there a sentence here someone would want to text to a friend?
  (1=no quotables, 10=shareable money line)
- LENGTH FIT: Is this clip the right length for short-form social? (1=too long/short, 10=perfect for the target)

Return a JSON object: {hook, payoff, standalone, replayability, length_fit, total, money_line, why}
```

## Tool selection

LLM call only. Pick via Selector (`capability=llm_text` or use a project-default LLM).

```python
weights = {**DEFAULT_WEIGHTS, "latency": 1.5}
# Long episodes mean many candidate windows. Latency matters.
```

## Determinism

LLM scoring is non-deterministic by default. Pass `seed` AND `temperature=0`. If the provider doesn't support seeds, run the same window 3 times and take the median score.

## Review focus

- Score considers hook, payoff, completeness (standalone), length fit.
- Candidate clips do NOT split a sentence (every window ends at a sentence boundary).
- The `money_line` extracted matches what's actually in the transcript (no hallucinations).
- Top candidates have score variance < 30% between LLM runs (else flag as low-confidence pick).

## Why this stage requires approval

This is where Drey's editorial judgment lands. Pick wrong here and the rest of the pipeline produces polished clips of the wrong moments. Always present the top 5-10 with their `money_line` snippets and let Drey approve / re-rank / discard.

## What you do NOT do

- No cutting, cropping, captioning here — those are downstream stages.
- No re-transcription. Trust the upstream artifacts; re-run transcribe if you don't.
