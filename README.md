# Agentic Cuts

**The Agentic NLE — real timeline, deterministic agent, runs locally.**

Open-source video production driven by AI coding assistants (Claude Code, Cursor, Codex, Copilot). The agent reads YAML pipeline manifests + Markdown stage director skills, calls Python tools, and edits a real timeline you can scrub. Multi-tenant by design — one core engine, brand-kit whitelist for any creator or studio.

> **Status: v0.1 — foundation only.** Core library + tests landed. Pipelines, tools, timeline UI, MCP server, and tenant whitelist mechanism are next. Star + watch to follow the build.

---

## What's different vs everything else

| Feature | Agentic Cuts | OpenMontage | MoneyPrinterTurbo | ShortGPT |
|---|:---:|:---:|:---:|:---:|
| Agent-driven (Claude Code / Cursor) | yes | yes | no | partial |
| Multi-tenant whitelist | yes | no | no | no |
| Real timeline UI (not chat-only) | yes (planned) | no | no | no |
| Deterministic seeds + run cache | yes | no | no | no |
| Hard-stop budget (cap mode) | yes | warn only | no | no |
| Frame-perfect cuts (keyframe-aligned) | yes | no | no | no |
| Skill RAG (top-K retrieval) | yes | no | no | no |
| Apache 2.0 (commercial-friendly) | yes | AGPLv3 only | yes | yes |

---

## Architecture in one breath

The agent is the orchestrator. Tools are its hands. The timeline is the source of truth.

- **Pipelines** are YAML manifests — declarative stages from idea to publish.
- **Stage director skills** are Markdown — they teach the agent how to execute one stage.
- **Tools** are small Python classes conforming to a single contract (`BaseTool.execute() -> ToolResult`). Drop one in the right folder; the registry auto-discovers it.
- **Selectors** rank providers across 7 dimensions (task fit, quality, control, reliability, cost efficiency, latency, continuity) and pick the best for each task.
- **Quality gates** run before render: delivery promise validation, slideshow risk detection, hard-stop budget abort.
- **Determinism** is built in: every tool accepts a seed; same seed + same inputs = byte-identical output, cached.

Full architecture in [`ARCHITECTURE.md`](ARCHITECTURE.md).

---

## Multi-tenant layout

```
agentic-cuts/                     core engine, public, Apache 2.0
agentic-cuts-drey/                Drey's tenant (private)
agentic-cuts-1bb/                 1 Button Business tenant (private)
agentic-cuts-ve/                  Viral Editz tenant (private)
agentic-cuts-<your-brand>/        clone via setup script (coming)
```

Each tenant pulls core as a git submodule, layers its own `brand-kit.yaml` + custom skills, and ships its own deployments without forking the engine.

---

## Quick start (foundation v0.1)

```bash
git clone https://github.com/Dreydrey9000/agentic-cuts.git
cd agentic-cuts
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest tests/
```

You should see `32 passed`.

There's nothing user-facing yet — this drop only contains the engine library + tests. Tools, pipelines, timeline UI, and MCP server land in v0.2.

---

## Roadmap

- v0.1 (shipped) — Foundation: BaseTool contract, tool registry, 7-dim selector, checkpoint, media profiles, cost tracker (with HARD STOP), delivery promise, slideshow risk, run cache, skill RAG, frame-perfect cut planner.
- v0.2 — 5 launch pipelines (clip-factory, talking-head, documentary-montage, podcast-repurpose, animated-explainer) plus 2026 model tools (Wan 2.2-TI2V-5B, LTX-2, Kokoro TTS, ACE-Step 1.5, WhisperX + pyannote Community-1).
- v0.3 — Real timeline UI (Next.js + Remotion) plus MCP server plus Claude Code skill bundle.
- v0.4 — Three wow features: Submagic-tier kinetic captions, HeyGen-tier avatar lip-sync dub, conversational video MVP.
- v0.5 — Whitelist mechanism (`setup-tenant.sh` + `brand-kit.yaml` schema) — clone and rebrand for any client in under 5 minutes.
- v1.0 — Public launch.

---

## Naming credit

Drey picked **Agentic Cuts** because every other name was a job description, and brands have aura.

---

## License

Apache License 2.0. Commercial use is fine, fork is fine, ship to clients is fine — that's the whole point. See [LICENSE](LICENSE).
