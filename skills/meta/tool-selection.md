---
name: agentic-cuts-tool-selection
description: Use ANY time you need to pick a provider for a capability (TTS, video gen, music, captions, etc.). Never hard-code; always go through the Selector.
---

# Tool Selection — Use the Selector, Not Provider Names

The `Selector` ranks every candidate tool across 7 dimensions and picks the winner. Hard-coding a provider name skips all the cost-awareness, fallback, and determinism logic.

## The 7 dimensions

```
task_fit           Does this tool support the requested capability + params?
output_quality     Tier baseline + provider-specific quality_hint.
control            Seeds, structured outputs, voice clone, style transfer.
reliability        Local + free = high. New cloud APIs = lower.
cost_efficiency    Inverse of estimated $ cost.
latency            Inverse of expected wall-clock time.
continuity         Determinism + voice/style memory across runs.
```

## Default weights

```python
DEFAULT_WEIGHTS = {
    "task_fit": 1.5,         # task fit dominates
    "output_quality": 1.3,
    "reliability": 1.2,
    "control": 1.0,
    "cost_efficiency": 0.8,
    "latency": 0.7,
    "continuity": 0.5,
}
```

## How to select a provider

```python
from agentic_cuts import Selector, registry

# Make sure tools are discovered.
registry.discover()

# Get all candidates for a capability.
candidates = registry.by_capability("tts")

# Score them against the task. The task dict carries hints
# the selector uses: language, duration_sec, voice_clone, etc.
selector = Selector()  # default weights
winner, cards = selector.pick(candidates, task={
    "language": "en",
    "duration_sec": 12,
    "seed": 42,
})

if winner is None:
    raise RuntimeError("No TTS provider supports this task")

# Always log the decision before calling.
top = max(cards, key=lambda c: c.total())
print(f"selected={winner.name} score={top.total():.2f}")

# Then run it.
result = winner.execute({"text": "...", "language": "en", "seed": 42})
```

## When to override the weights

Different pipeline stages care about different things. Override per-call:

| Pipeline / stage | Weight tweak | Why |
|---|---|---|
| `clip-factory` ranking | `latency *= 1.5`, `cost *= 1.5` | Drey runs this daily. Speed + cheap matters. |
| `talking-head` dub | `output_quality *= 1.5`, `continuity *= 1.5` | Voice match is the whole product. |
| `documentary-montage` retrieve | `cost *= 2.0` | Free archives win when quality is comparable. |
| `animated-explainer` assets | `output_quality *= 1.4` | These are the visuals — quality > everything. |
| `podcast-repurpose` rank | `latency *= 1.5` | Long episodes; speed matters. |

## The fallback rule

When the winner's `execute()` returns `success=False`:

1. Log the failure with the decision_log captured.
2. Drop the loser from candidates.
3. Re-run `Selector.pick()` on the remaining candidates.
4. Try once more. If that fails too, fail the stage with a clear error and stop the pipeline. The checkpoint saves where we got to.

Never silently retry the same tool. Never skip to a wholly different capability.

## What you DO NOT do

- Hard-code a provider name (`if elevenlabs_available: ...`). Use the selector.
- Override task_fit weight to 0 hoping cost-efficiency wins. The whole point of task_fit is to filter out tools that can't do the job.
- Loop over candidates calling each one in turn. The selector picks ONE; you fall back exactly once.
