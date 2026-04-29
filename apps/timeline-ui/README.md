# Agentic Cuts — Timeline UI (v0.4 scaffold)

Next.js 16 + Tailwind 4 + zustand. The browser-side counterpart to the Python engine.

## What's here

- **Demo plans baked in** at `lib/render-plan.ts` so the UI works offline.
- **Click-to-scrub timeline** at `components/timeline-track.tsx` (drag + J/K/L coming in v0.5).
- **Stage rows** that render the manifest from `agentic-cuts plan --out plan.json`.

## What's NOT here yet (v0.5+)

- Remotion preview (real video frames).
- Real drag/drop + J/K/L scrub + in/out marks.
- Project save / load / share.
- Auth.
- Tauri desktop wrapper.

## Run locally

```
cd apps/timeline-ui
pnpm install
pnpm dev
# http://localhost:3000
```

## Deploy

```
pnpm install
pnpm build
# Vercel:
vercel --prod
```

## Why a separate `apps/` dir

Per the v0.3 architecture decisions: Python engine + TypeScript timeline UI. The two-language cap holds. This dir is a sibling of `agentic_cuts/`, not a submodule.
