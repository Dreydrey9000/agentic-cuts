# Architecture — Agentic Cuts

**Status:** Foundational draft. Decisions flagged with `🟡 DECISION:` need a Drey call before code lands.

---

## What Agentic Cuts is, in one breath

Agentic Cuts is a **multi-tenant agentic NLE** — a video production system that any AI coding assistant (Claude Code, Cursor, Copilot, Codex) can drive end-to-end, with a real timeline you can scrub, deterministic runs you can reproduce, and a whitelist mechanism so different brands (Drey, 1BB, Viral Editz, future clients) each get their own instance without forking the engine.

Plain-English version: it's like a recording studio franchise. There's one master studio (`agentic-cuts` core) — every booth has the same gear, same wiring, same soundproofing. Each franchise location (`agentic-cuts-drey`, `agentic-cuts-1bb`, `agentic-cuts-ve`) has its own brand, its own house style, its own client list — but when the master studio upgrades the gear, every franchise gets it automatically. The AI agent is the producer who runs the session.

---

## The three-sentence mental model

1. **The agent is the orchestrator** — there is no Python "controller" that calls tools in sequence; the AI assistant reads YAML pipeline manifests, reads Markdown stage director skills, and calls Python tools one at a time, just like a director on a real set.
2. **Tools are the agent's hands** — every tool (TTS, image gen, video gen, FFmpeg, Remotion compose) is a small Python class that conforms to one contract; the agent picks tools using a 7-dimension scored selector that ranks providers by task fit, quality, control, reliability, cost, latency, and continuity.
3. **The timeline is the source of truth** — unlike OpenMontage and every chat-only competitor, every cut, asset, and decision lands on a real timeline JSON that a human can scrub, drag, and override at any point; the agent edits the timeline, the human supervises it, and the renderer is the final audit step.

---

## Multi-tenant layout

```
~/My Apps/
├── openmontage-pristine/          ← frozen reference, NEVER edited
├── agentic-cuts/                  ← CORE engine, public, Apache 2.0
│   ├── tools/                     (52 capability tools)
│   ├── pipelines/                 (5 launch YAMLs — not 12)
│   ├── skills/                    (~80 high-signal markdown skills)
│   ├── lib/                       (registry, scoring, checkpoints, gates)
│   ├── timeline/                  (real-timeline JSON + UI)
│   ├── mcp/                       (MCP server exposing tools)
│   ├── ARCHITECTURE.md            (this doc)
│   └── CHANGELOG.md
│
├── agentic-cuts-drey/             ← tenant: Drey's daily driver, private
│   ├── core/                      (git submodule → agentic-cuts)
│   ├── brand-kit.yaml             (Drey palette/voice/fonts)
│   ├── skills.local/              (Drey's custom skills)
│   ├── projects/                  (Drey's actual videos)
│   └── .env                       (Drey's API keys, gitignored)
│
├── agentic-cuts-1bb/              ← tenant: 1 Button Business, private
│   ├── core/  brand-kit.yaml  skills.local/  projects/  .env
│
└── agentic-cuts-ve/               ← tenant: Viral Editz, private
    ├── core/  brand-kit.yaml  skills.local/  projects/  .env
```

**How tenants pull from core:** git submodule, pinned to a tag. When core ships a new release, each tenant runs `git submodule update --remote core` to upgrade. Brand kits and local skills override core defaults by name precedence (tenant > core).

🟡 **DECISION 1 — Submodule vs. published package:** Submodules are simpler day 1 but get clunky at scale. Alternative is publishing core as a Python package (`pip install agentic-cuts`) plus an npm package for the timeline UI. **Recommend submodule for v0, switch to published packages once we have 5+ tenants.** Drey-confirm.

---

## What we KEEP from OpenMontage (the patterns worth stealing)

| Pattern | Why it works | What we keep |
|---|---|---|
| Agent-as-orchestrator | No Python controller to maintain or debug. The agent reads instructions and calls tools. | Same shape — YAML pipeline manifests + Markdown stage director skills + Python tools. |
| BaseTool contract | Every tool has the same `.execute() → ToolResult` interface, so the agent never gets surprised. | Re-implement with our names; same contract. |
| Tool registry auto-discovery | Drop a tool into the right folder and it shows up automatically (`pkgutil.walk_packages`). | Same. |
| Selector + provider pattern | One "tts_selector" tool the agent calls; selector picks Kokoro/ElevenLabs/Piper based on context. | Same — extends to video, music, captions. |
| 7-dimension scored selection | Rank every provider on task fit, quality, control, reliability, cost, latency, continuity. | Same. |
| Checkpoint JSON with stage resumption | If a render dies on stage 5, you don't restart from stage 1. | Same — extended with run cache (see below). |
| Media profiles | YouTube/TikTok/Reels/Square = different aspect, codec, bitrate. Parameterized once, used everywhere. | Same. |
| Delivery promise + slideshow risk gates | Pre-compose validation that blocks "8 still images called a video" outputs. | Same — these are the quality gates that earn trust. |

---

## What we DROP from OpenMontage

| What | Why |
|---|---|
| **AGPLv3 license** | Viral copyleft poisons agency adoption. Apache 2.0 lets 1BB, VE, and future clients use it commercially without legal review. |
| **12 pipelines on launch** | Too much surface area. Ship 5 that 90% of creators need; add the rest only when validated. (Drop: animation, hybrid, screen-demo, cinematic, avatar-spokesperson, framework-smoke for v1.) |
| **400+ skills** | Most are scaffolding the agent doesn't need every run. Cut to ~80 high-signal skills, retrieved via RAG (see ADD section). |
| **Setup heaviness** | OpenMontage requires Python + Node + FFmpeg + optional GPU stack on day 1. We split: zero-key path runs on Python+FFmpeg only; GPU and Node are opt-in. |
| **Chat-only operation** | No real timeline UI in OpenMontage. We add one (the wedge). |

---

## What we ADD that OpenMontage missed

These are the four things HN devs and Reddit creators explicitly asked for and OpenMontage doesn't have:

### 1. Determinism (seeds + run cache)
Every tool accepts a `seed` parameter. Same prompt + seed + model version + tool version = byte-identical output. We hash that tuple as a cache key; re-running the same step is free. **Why this matters:** the #1 dev complaint is "LLMs vary frame-level decisions run-to-run, can't ship pro work that way." We fix it.

### 2. Skill retrieval via RAG
OpenMontage requires the agent to be told which skills apply to a stage. That's the biggest discoverability bug they have. We embed every skill with a small model (BGE-small or similar) and retrieve top-K by stage + intent at runtime. The agent doesn't have to know the skill exists — the system finds it.

### 3. Hard-stop budget abort
OpenMontage warns when budget is exceeded. We **kill the run.** Configurable per-pipeline cap; soft-warn at 80%, hard-stop at 100%. No surprise bills, no zombie renders chewing API credit at 3am.

### 4. Frame-perfect cuts
OpenMontage uses FFmpeg cut points without keyframe-awareness. HN dev quote: *"Can't make frame perfect cuts without re-encoding, unless your cut points just so happen to be keyframe aligned."* We snap cuts to keyframes when possible, force re-encode only when the user marks the cut as critical, and surface that choice in the timeline UI.

### 5. Real timeline UI (the wedge)
The single biggest differentiator. Mosaic and Cardboard admitted on HN that chat-only is the wrong UX for video. Creators want scrub, drag-drop, spacebar play, J/K/L scrub, in/out marks. We ship a minimal Next.js + Remotion preview timeline that the agent edits via JSON; the human supervises with real timeline gestures.

🟡 **DECISION 2 — Timeline UI hosting:** Run local (Electron/Tauri desktop app) or hosted (Vercel + auth)? **Recommend local-first** because (a) HN explicitly hates browser editing, (b) works offline, (c) tenant-private project files never leave the machine. Hosted version comes later as a v2 collab feature.

---

## License decision (firm)

**Apache 2.0.** Reasoning:

- OpenMontage is **AGPLv3** — anyone who runs a derivative work over a network must release their source. That blocks commercial use for any agency that wants to wrap us in a SaaS or sell client deliverables.
- We need agencies (1BB, VE, future clients) to use this and make money with it without legal review. Apache 2.0 + a patent grant is the cleanest path.
- We give up some "if you fork us, you must open-source your fork" leverage. We gain a 100x larger adoption surface. Worth it for a positioning play built on whitelist tenants.

🟡 **DECISION 3 — Re-implementation discipline:** Because upstream is AGPLv3, we **must not copy code** from OpenMontage. We re-implement patterns from spec. The pristine reference clone is read-only on purpose. This is a hard rule with a real legal edge — flag any PR that lifts code rather than re-implementing the pattern.

---

## Tech stack (current best guess)

🟡 **DECISION 4 — Core language:** Python or TypeScript?

- **Python pro:** every video AI lib is Python (diffusers, transformers, whisperx, piper, manim, pyannote). Faster port from OpenMontage spec. Fewer language hops.
- **TypeScript pro:** Drey's CLAUDE.md says TS default; the timeline UI is Next.js + Remotion (TS); MCP server is cleanest in TS; agencies hire TS devs more easily.

**Recommend Python for the engine + TypeScript for the timeline UI + MCP server.** It's a 2-language ceiling (matches Drey's "no project ships with more than TWO languages" rule). Pre-built binaries hide Python from end users.

| Layer | Language | Stack |
|---|---|---|
| Engine (tools, pipelines, gates, scoring) | Python 3.12 | stdlib + minimal deps (Pydantic, PyYAML, FFmpeg subprocess) |
| Timeline UI | TypeScript | Next.js 16 + Remotion + Zustand + Tailwind |
| MCP server | TypeScript | `@modelcontextprotocol/sdk` |
| Run database | SQLite (local) | per-tenant `runs.db`; cache + checkpoint history |
| Tenant config | YAML | `brand-kit.yaml` + `pipelines.yaml` |

🟡 **DECISION 5 — Run database:** SQLite local (recommended) keeps everything local and zero-setup. Convex (Drey's preferred) makes sense if we want tenants to share runs / collaborate, but adds a dependency and cloud cost. **Recommend SQLite for v0; revisit Convex if multi-user collab becomes a real feature.**

---

## Build order (what to write first)

This maps to tasks #5 → #13 in the project task list.

1. **`lib/`** — port the 7 stealable patterns (BaseTool, registry, selector+scoring, checkpoint, media profiles, cost tracker, delivery promise gate).
2. **`tools/`** — 8-12 launch tools (Kokoro TTS, Piper TTS, ElevenLabs TTS, FFmpeg cuts, Remotion compose, Pexels stock, Archive.org search, WhisperX transcribe, ACE-Step music).
3. **`pipelines/`** — `clip-factory.yaml` first (Drey's #1 use case), then `talking-head.yaml`, then `documentary-montage.yaml`.
4. **`skills/`** — director skills for each pipeline stage + RAG embedding pipeline.
5. **`timeline/`** — Next.js minimal scrub UI + JSON contract.
6. **`mcp/`** — MCP server.
7. **Captions preset library** (wow feature 1).
8. **Avatar lip-sync dub** (wow feature 2).
9. **Conversational video MVP** (wow feature 3).
10. **Whitelist mechanism** — `setup-tenant.sh` + brand-kit schema.
11. **Hero demos + ship.**

---

## Open decisions summary (for Drey to call)

| # | Decision | My recommendation |
|---|---|---|
| 1 | Tenant→core link | Git submodule for v0, published package later |
| 2 | Timeline UI hosting | Local-first (Tauri or Electron); hosted v2 |
| 3 | Re-implementation discipline | Hard rule, flagged in PRs, no code lifted from upstream |
| 4 | Core language | Python engine + TypeScript UI/MCP (2-language cap) |
| 5 | Run database | SQLite per-tenant; revisit Convex on collab demand |

Drey says go on the recommendations or override any single one. Then I write `lib/` and `tools/` and we're moving.
