# Agentic Cuts — Skill Index

The agent driving Agentic Cuts (Claude Code, Cursor, Codex, Copilot, Windsurf)
reads skills from this directory. Each skill is a Markdown file teaching the
agent HOW to do one specific job. Pipelines reference skills by relative path.

## Layout

```
skills/
├── INDEX.md                              ← you are here
├── meta/                                 ← universal skills, applied at every stage
│   ├── overview.md                       (what Agentic Cuts is + when to use it)
│   ├── tool-selection.md                 (how the selector picks tools)
│   ├── quality-gates.md                  (delivery promise + slideshow risk + cost)
│   ├── checkpoint-protocol.md            (when to checkpoint, when to ask approval)
│   ├── determinism.md                    (always pass seeds + use the run cache)
│   └── reviewer.md                       (meta-skill for stage self-review)
└── pipelines/
    ├── clip-factory/                     (Drey's daily VE driver — REAL director skills)
    │   ├── ingest.md
    │   ├── transcribe.md
    │   ├── rank.md
    │   ├── cut.md
    │   ├── vertical-crop.md
    │   ├── caption.md
    │   └── render.md
    ├── talking-head/                     (placeholders, real content lands in v0.3)
    ├── documentary-montage/              (placeholders)
    ├── podcast-repurpose/                (placeholders)
    └── animated-explainer/               (placeholders)
```

## How the agent uses these

1. User says "make me a vertical clip from this podcast."
2. Agent picks the right pipeline (`clip-factory`) — manifest at
   `agentic_cuts/pipelines/clip-factory.yaml`.
3. Manifest names the stages and points each one at a director skill in
   `skills/pipelines/clip-factory/<stage>.md`.
4. For every stage, the agent reads the meta skills FIRST (overview,
   quality-gates, determinism), then the stage's director skill.
5. The agent calls Python tools via `agentic_cuts.lib`. Each tool returns a
   `ToolResult`. Stage produces an artifact. Checkpoint saves state. Reviewer
   skill evaluates. Move on.

## Skill priority order at every stage

```
meta/overview.md            → mental model
meta/determinism.md         → always pass seeds
meta/tool-selection.md      → use the selector, not hard-coded providers
meta/quality-gates.md       → run gates BEFORE composition
pipelines/<X>/<stage>.md    → stage-specific HOW
meta/checkpoint-protocol.md → save state, ask for approval if required
meta/reviewer.md            → score the stage's output before moving on
```

## License

Apache 2.0 (matches the engine).
