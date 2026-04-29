---
name: agentic-cuts-checkpoint-protocol
description: Use at EVERY stage boundary. Save state, then ask for human approval if the stage requires it.
---

# Checkpoint Protocol

Every stage ends with a checkpoint. If the agent crashes, the next session resumes from the last checkpoint without redoing earlier stages. This is what kills the "wasted GPU" problem.

## How to checkpoint

```python
from agentic_cuts import Checkpoint
from pathlib import Path

ckpt = Checkpoint(Path("projects/my-clip"))

# After completing a stage:
ckpt.save(
    stage="rank",
    data={
        "candidate_clips": [...],
        "virality_scorecard": [...],
    },
    cost_usd=0.04,
    duration_ms=12_300,
    decision_log={
        "selector": "top-3 of 8 candidates",
        "weight_overrides": {"latency": 1.5},
    },
)
```

The save is atomic — temp file then rename. A crash mid-write never leaves a corrupt checkpoint.

## Resuming after a crash

```python
ckpt = Checkpoint(Path("projects/my-clip"))
last = ckpt.latest_stage()
if last is not None:
    print(f"resuming after {last}")
    # Load the stage's data and continue from the next stage.
    data = ckpt.load(last)
```

The pipeline manifest's `stages_after(name)` returns the remaining stages. Run them in order.

## Approval gates — when to pause

Each stage in the manifest carries `human_approval_default`. When True, the agent does NOT proceed automatically. It writes the checkpoint, presents the artifact, and waits for the human to approve / edit / reject.

```python
stage = manifest.stage("script")
if stage.human_approval_default:
    print(f"## Stage: {stage.name} — awaiting approval")
    print(stage_artifact)
    # Stop here. The human's response triggers the next stage.
    return
```

Stages that ALWAYS pause (regardless of pipeline):
- `script` — the words are the show. Never auto-approve.
- `scene_plan` — visual direction needs human eyes.
- `final render` — the user signs off on what gets published.

Stages that AUTO-PROGRESS by default:
- `ingest` — mechanical.
- `transcribe` — mechanical (caveat: low-confidence sections may need review).
- `cut`, `caption`, `enhance` — mechanical given good upstream artifacts.

## Checkpoint policy values

The pipeline manifest's `checkpoint.policy` controls how aggressively to ask:

- `guided` (default) — pause at creative-decision stages only. Best for repeat use of a familiar pipeline.
- `manual_all` — pause at every stage. Best for new pipelines or new tenants.
- `auto_noncreative` — pause only at script + final review. Fastest. For trusted pipelines.

## What goes IN a checkpoint

- The stage's primary artifact (script text, scene plan JSON, asset manifest, edit decisions, render report).
- Cost spent on this stage.
- Duration.
- The decision log: which provider was picked, why, what alternatives were considered.

## What does NOT go in a checkpoint

- Raw model weights, large binary blobs (those go to disk separately, the checkpoint references the path).
- Secrets / API keys (`.env` is gitignored for a reason).
- The user's personal info beyond what they explicitly provided.
