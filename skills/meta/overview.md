---
name: agentic-cuts-overview
description: Use ALWAYS when working inside an Agentic Cuts repo. Establishes the mental model — agent is the orchestrator, tools are hands, timeline is the source of truth.
---

# Agentic Cuts — Operating Mental Model

You are driving an Agentic Cuts pipeline. There is no Python orchestrator. **You are the orchestrator.** Tools are your hands; the timeline is the source of truth.

## The three rules of operation

1. **Pipelines first.** Every video request goes through a pipeline. Look up which pipeline fits the request — `clip-factory` for long-to-short, `talking-head` for footage-led speaker reels, `documentary-montage` for archival/real-footage, `podcast-repurpose` for audio-first, `animated-explainer` for AI-generated visuals. If unsure, ask the user once. Do not improvise a workflow.
2. **One stage at a time.** Read the manifest at `agentic_cuts/pipelines/<name>.yaml`. Execute stages in order. Read the matching director skill at `skills/pipelines/<name>/<stage>.md` BEFORE calling any tool for that stage.
3. **Timeline is canonical.** Every cut, asset, and decision lands on a timeline JSON the human can scrub. You edit the timeline, the human supervises it, the renderer is the audit step.

## What you have access to

Library exports live in `agentic_cuts.lib`. The pieces you'll touch most:

| Symbol | When to use |
|---|---|
| `discover_pipelines(...)` | List available pipelines at startup. |
| `load_manifest(path)` | Load one pipeline manifest into a typed object. |
| `Selector.pick(candidates, task)` | Pick the best provider for a capability. NEVER hard-code a provider. |
| `CostTracker(budget, mode=CAP)` | Reserve before each tool call. Reconcile after. CAP mode RAISES on overrun. |
| `Checkpoint(project_dir)` | Save stage state at every stage boundary. Resumes from latest on crash. |
| `validate_plan(promise, plan)` | Pre-compose gate. Run BEFORE rendering. |
| `detect_slideshow_risk(manifest)` | Asset-mix sanity check. Run before composing. |
| `RunCache(db_path)` | Re-runs of the same (prompt, seed, model, version) are FREE. Always check first. |
| `SkillRAG(db_path)` | Ask "what skills apply to this stage and intent?" instead of guessing. |
| `plan_cut(source, start, end)` | Frame-perfect FFmpeg cut planning. Stream-copy when keyframe-aligned, re-encode otherwise. |
| `profile_for(target)` | Get a media profile (TikTok, Reels, Shorts, YouTube, Square, X, 4K). |

## The agent's job in one sentence

> Read the manifest, read the stage skill, run the right tool with a seed, save the checkpoint, validate against the promise, ask for human approval at decision points, then move to the next stage.

## What you NEVER do

- Never write to `~/My Apps/openmontage-pristine/` — that's a frozen reference.
- Never copy code from upstream OpenMontage — re-implement only. License boundary (AGPLv3 → Apache 2.0).
- Never call a model provider without going through the `Selector`. The selector is how the system stays cost-aware and deterministic.
- Never skip the quality gates. `validate_plan` runs BEFORE compose. `detect_slideshow_risk` fires when an asset manifest is mostly stills.
- Never leave a stage without a checkpoint. If you crash mid-pipeline, the next session must be able to resume.
- Never ship without seeds. Determinism is the wedge.
