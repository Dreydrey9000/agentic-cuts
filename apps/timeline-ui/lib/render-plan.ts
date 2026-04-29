// TypeScript mirror of `agentic_cuts.cli plan` JSON output.
// Stays in sync by structure, not by codegen, since the engine ships
// in Python. Update these types when the Python schema changes.

export type Aspect = "16:9" | "9:16" | "1:1" | "4:5";

export interface MediaProfileSummary {
  name: string;
  resolution: string;
  fps: number;
  container: string;
  codec: string;
  safe_zone_top_pct: number;
  safe_zone_bottom_pct: number;
}

export interface DeliveryPromise {
  target_aspect: Aspect;
  requires_motion: boolean;
  requires_audio: boolean;
  requires_captions: boolean;
  requires_narration: boolean;
  requires_music: boolean;
  duration_tolerance_sec: number;
}

export interface StageSummary {
  index: number;
  name: string;
  director_skill: string;
  capabilities_required: string[];
  artifacts_produced: string[];
  human_approval_default: boolean;
  optional: boolean;
}

export interface RenderPlan {
  version: 1;
  engine: "agentic-cuts";
  pipeline: {
    name: string;
    version: string;
    type: string;
  };
  input: {
    video_path: string | null;
  };
  render_target: MediaProfileSummary;
  delivery_promise: DeliveryPromise;
  stages: StageSummary[];
  budget: {
    cap_usd: number;
    mode: "observe" | "warn" | "cap";
  };
}

// A handful of demo plans baked in so the UI works offline / unauthenticated
// and the visitor can FEEL the timeline shape on first load.
export const DEMO_PLANS: Record<string, RenderPlan> = {
  "clip-factory": {
    version: 1,
    engine: "agentic-cuts",
    pipeline: { name: "clip-factory", version: "0.1", type: "footage_based" },
    input: { video_path: "/demo/podcast-ep04.mp4" },
    render_target: {
      name: "tiktok",
      resolution: "1080x1920",
      fps: 30,
      container: "mp4",
      codec: "libx264",
      safe_zone_top_pct: 0.12,
      safe_zone_bottom_pct: 0.22,
    },
    delivery_promise: {
      target_aspect: "9:16",
      requires_motion: true,
      requires_audio: true,
      requires_captions: true,
      requires_narration: false,
      requires_music: false,
      duration_tolerance_sec: 1.0,
    },
    stages: [
      { index: 0, name: "ingest", director_skill: "skills/pipelines/clip-factory/ingest.md", capabilities_required: ["scene_detect"], artifacts_produced: ["source_meta", "scene_map"], human_approval_default: false, optional: false },
      { index: 1, name: "transcribe", director_skill: "skills/pipelines/clip-factory/transcribe.md", capabilities_required: ["stt", "diarization"], artifacts_produced: ["transcript", "word_timings", "speaker_map"], human_approval_default: false, optional: false },
      { index: 2, name: "rank", director_skill: "skills/pipelines/clip-factory/rank.md", capabilities_required: [], artifacts_produced: ["virality_scorecard", "candidate_clips"], human_approval_default: true, optional: false },
      { index: 3, name: "cut", director_skill: "skills/pipelines/clip-factory/cut.md", capabilities_required: ["cut"], artifacts_produced: ["cut_clips"], human_approval_default: false, optional: false },
      { index: 4, name: "vertical_crop", director_skill: "skills/pipelines/clip-factory/vertical-crop.md", capabilities_required: [], artifacts_produced: ["vertical_clips"], human_approval_default: false, optional: false },
      { index: 5, name: "caption", director_skill: "skills/pipelines/clip-factory/caption.md", capabilities_required: ["caption"], artifacts_produced: ["captioned_clips"], human_approval_default: false, optional: false },
      { index: 6, name: "render", director_skill: "skills/pipelines/clip-factory/render.md", capabilities_required: ["compose", "publish"], artifacts_produced: ["final_clips", "render_report"], human_approval_default: true, optional: false },
    ],
    budget: { cap_usd: 0.5, mode: "cap" },
  },
};
