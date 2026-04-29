---
name: agentic-cuts-determinism
description: Use EVERY tool call. Always pass a seed. Always check the run cache first. Re-runs of the same input must be byte-identical.
---

# Determinism — The Wedge

The #1 thing OpenMontage gets wrong: every run varies. We fix that. Same prompt + same seed + same model version + same tool version = byte-identical output. Cached on disk. Re-runs are free.

## Always pass a seed

Every `execute()` call accepts a `seed` parameter. The default seed for a project is its hash; pass an integer to override.

```python
result = tool.execute({
    "prompt": "warm and conversational, slight irreverence",
    "seed": 42,
    "language": "en",
})
```

If the user's prompt didn't specify a seed, derive a stable one from the project name + the stage name:

```python
import hashlib
seed = int(hashlib.sha256(f"{project_name}::{stage_name}".encode()).hexdigest()[:8], 16)
```

This way, "run the clip-factory pipeline on `episode-04` again" produces identical output without the user remembering what seed to type.

## Always check the run cache FIRST

Before paying for a model call, check if we've done this exact thing before:

```python
from agentic_cuts import RunCache, cache_key

cache = RunCache(project_dir / "runs.db")

key = cache_key(
    tool_name=tool.name,
    tool_version=tool.version,
    prompt=user_prompt,
    seed=seed,
    model_version=tool.supports.get("model_version"),
)

hit = cache.get(key)
if hit is not None:
    print(f"cache hit: {hit.artifact_paths} (saved ${hit.cost_usd:.4f})")
    return hit  # use the cached artifact

# Cache miss — run the tool.
result = tool.execute({...})

if result.success:
    cache.put(
        key,
        tool_name=tool.name,
        tool_version=tool.version,
        artifact_paths=result.artifacts,
        cost_usd=result.cost_usd,
        metadata={"prompt": user_prompt, "seed": seed},
    )
```

The cache validates that artifact files still exist on disk. Missing file = cache miss = re-run.

## Why this matters

- Drey running the same clip-factory on the same podcast twice should yield the same clips. Anything else makes the system look broken to clients.
- A/B testing creative decisions requires identical baselines. You can't measure "preset A vs preset B" if every run already differs.
- Demos that "worked once" should still work on stage. Determinism is the difference between a tool and a magic trick.

## What to seed and what NOT to seed

| Capability | Seed? | Why |
|---|:---:|---|
| Image gen (FLUX, Imagen, DALL-E) | yes | Same prompt + seed = same image. |
| Video gen (Wan, LTX, Hunyuan) | yes | Latent space sampling. |
| TTS (Kokoro, ElevenLabs, Piper) | yes when supported | Voice cloning + sample noise. |
| Music gen (ACE-Step, MusicGen) | yes | Latent sampling. |
| LLM script writing | yes via `seed` param if provider supports it | OpenAI + Anthropic both expose seeds. |
| FFmpeg cuts / compose | NO | Already deterministic — bytes in, bytes out. |
| Stock retrieval (Pexels search) | order by deterministic key | Sort results by ID, not relevance. |
| WhisperX transcribe | NO | Already deterministic — same audio, same transcript. |

## The cache key is the contract

Anything that changes the output must be in the cache key. If a tool upgrades its model from `flux-pro-v2` to `flux-pro-v3`, the `tool_version` bump invalidates the cache automatically. If a prompt changes by one word, the prompt hash differs and the cache misses.

If you find yourself wanting to "force a fresh generation" — pass a different seed. Don't bypass the cache.
