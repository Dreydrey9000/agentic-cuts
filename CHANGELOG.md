# Changelog — Agentic Cuts (Core Engine)

All notable changes to this project will be documented here. Format follows [Keep a Changelog](https://keepachangelog.com/) with one line per change and the WHY.

## [2026-04-28]

### Added
- Repo created — open-source core engine for the Agentic Cuts multi-tenant platform. Apache 2.0 license picked over upstream OpenMontage's AGPLv3 to enable agency adoption (the whole point of whitelist tenants).
- README + LICENSE (Apache 2.0) + Python gitignore via `gh repo create`.
- Pristine OpenMontage reference snapshot lives at `~/My Apps/openmontage-pristine/` (commit `a06d4c2`, 2026-04-12) as a frozen spec lookup. Never modified.
- `ARCHITECTURE.md` — keep/drop/add vs OpenMontage with 5 architecture decisions (all approved by Drey).
- `agentic_cuts/lib/` — 12 foundation modules, ~1100 lines: `base_tool.py`, `tool_registry.py`, `scoring.py`, `checkpoint.py`, `media_profiles.py`, `cost_tracker.py`, `delivery_promise.py`, `slideshow_risk.py`, `run_cache.py`, `skill_rag.py`, `frame_perfect_cut.py`. Re-implemented from OpenMontage spec, never copied (license boundary).
- `tests/` — 32 tests, 5 files. All passing. Covers: BaseTool contract, registry + selector, checkpoint atomic writes, run cache hit/miss + artifact validation, skill RAG indexing/search, cost tracker hard-stop in CAP mode (the OpenMontage gap we explicitly fix), delivery promise gates (motion / aspect / captions), slideshow risk levels, frame-perfect cut planning (stream-copy when keyframe-aligned, re-encode otherwise).
- `pyproject.toml` — package metadata, pytest config, ruff lint config. Python 3.12+, Pydantic v2, PyYAML.
- `requirements.txt` + `requirements-dev.txt` — minimal runtime deps, separated test/dev deps.
- `.gitignore` augmentation — fixed gh-default `lib/` rule (was masking our package), added macOS, IDE, runtime dirs, SQLite caches, Node patterns.

### Added (Task 7 — 5 launch pipelines)
- `agentic_cuts/lib/pipeline_manifest.py` — Pydantic schema for YAML pipeline manifests. `PipelineManifest`, `StageManifest`, `ReviewConfig`, `BudgetConfig`, `CheckpointConfig`, `CheckpointPolicy`, `DeliveryPromiseDefaults`. Strict validation (extra="forbid"), duplicate-stage-name guard.
- `agentic_cuts/lib/pipeline_loader.py` — `load_manifest()` + `discover_pipelines()`. Handles malformed YAML, validation errors, and duplicate names with named exceptions.
- `agentic_cuts/pipelines/clip-factory.yaml` — Drey's daily VE driver. 7 stages: ingest → transcribe → rank → cut → vertical_crop → caption → render. 9:16 aspect, captions required, hard cap at $0.50.
- `agentic_cuts/pipelines/talking-head.yaml` — Drey's content + clients. 9 stages including optional dub. 9:16 aspect.
- `agentic_cuts/pipelines/documentary-montage.yaml` — Real-footage path nobody else does well. CLIP-indexed corpus from Archive.org/NASA/Wikimedia. 16:9 aspect, $0.30 cap (zero-key friendly).
- `agentic_cuts/pipelines/podcast-repurpose.yaml` — Audio-first, speaker-aware. 8 stages with diarization gate.
- `agentic_cuts/pipelines/animated-explainer.yaml` — Zero-key entry point. Free local stack out of the box.
- 12 new tests covering: 5-pipeline discovery, schema validation per pipeline, malformed YAML rejection, missing-field rejection, duplicate-stage-name rejection, stage lookup helpers. **44 tests passing total.**

### Designed (architecture decisions, all confirmed by Drey 2026-04-28)
- Tenant ↔ core link: git submodule for v0, switch to published `pip`/`npm` packages once 5+ tenants exist.
- Timeline UI: local-first (Tauri or Electron) — HN explicitly hates browser editing.
- Re-implementation discipline: hard rule, never copy upstream code (Apache 2.0 ↔ AGPLv3 boundary).
- Core language: Python engine + TypeScript timeline UI/MCP server. 2-language cap.
- Run database: SQLite per-tenant for v0; revisit Convex if collaboration becomes a feature.
