"use client";

import { create } from "zustand";

export interface Clip {
  id: string;
  name: string;
  src: string; // object URL
  duration_sec: number;
  // Position on the timeline:
  start_sec: number; // where the clip starts on the global timeline
  // Trim window into the source media:
  trim_in_sec: number; // start within the source media
  trim_out_sec: number; // end within the source media
  track: number; // 0 = video, 1 = caption (future), etc.
  color: string;
}

interface EditorState {
  clips: Clip[];
  playhead_sec: number;
  is_playing: boolean;
  selected_clip_id: string | null;
  duration_sec: number; // total timeline duration

  addClip: (input: {
    name: string;
    src: string;
    duration_sec: number;
  }) => Clip;
  updateClip: (id: string, patch: Partial<Clip>) => void;
  removeClip: (id: string) => void;
  setPlayhead: (sec: number) => void;
  setPlaying: (playing: boolean) => void;
  togglePlay: () => void;
  selectClip: (id: string | null) => void;
  splitAtPlayhead: () => void;
  computeDuration: () => void;
  exportEditDecisions: () => object;
}

const COLORS = [
  "rgba(255, 210, 0, 0.55)",  // primary yellow
  "rgba(0, 229, 255, 0.55)",  // cyan
  "rgba(255, 45, 58, 0.55)",  // accent red
  "rgba(163, 255, 18, 0.55)", // lime
  "rgba(108, 92, 231, 0.55)", // purple
];

let colorIdx = 0;

function nextColor(): string {
  const c = COLORS[colorIdx % COLORS.length];
  colorIdx++;
  return c;
}

export const useEditor = create<EditorState>((set, get) => ({
  clips: [],
  playhead_sec: 0,
  is_playing: false,
  selected_clip_id: null,
  duration_sec: 0,

  addClip: ({ name, src, duration_sec }) => {
    const state = get();
    // Append to end of timeline.
    const start_sec = state.duration_sec;
    const clip: Clip = {
      id: `clip-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
      name,
      src,
      duration_sec,
      start_sec,
      trim_in_sec: 0,
      trim_out_sec: duration_sec,
      track: 0,
      color: nextColor(),
    };
    set((s) => ({ clips: [...s.clips, clip] }));
    get().computeDuration();
    return clip;
  },

  updateClip: (id, patch) => {
    set((s) => ({
      clips: s.clips.map((c) => (c.id === id ? { ...c, ...patch } : c)),
    }));
    get().computeDuration();
  },

  removeClip: (id) => {
    set((s) => ({
      clips: s.clips.filter((c) => c.id !== id),
      selected_clip_id: s.selected_clip_id === id ? null : s.selected_clip_id,
    }));
    get().computeDuration();
  },

  setPlayhead: (sec) => set({ playhead_sec: Math.max(0, sec) }),

  setPlaying: (playing) => set({ is_playing: playing }),

  togglePlay: () => set((s) => ({ is_playing: !s.is_playing })),

  selectClip: (id) => set({ selected_clip_id: id }),

  splitAtPlayhead: () => {
    const state = get();
    const head = state.playhead_sec;
    // Find a clip that contains the playhead.
    const clip = state.clips.find(
      (c) =>
        c.start_sec <= head && c.start_sec + (c.trim_out_sec - c.trim_in_sec) > head
    );
    if (!clip) return;
    const offset = head - clip.start_sec;
    const left: Clip = {
      ...clip,
      id: `clip-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
      trim_out_sec: clip.trim_in_sec + offset,
    };
    const right: Clip = {
      ...clip,
      id: `clip-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
      start_sec: head,
      trim_in_sec: clip.trim_in_sec + offset,
      color: nextColor(),
    };
    set((s) => ({
      clips: [...s.clips.filter((c) => c.id !== clip.id), left, right].sort(
        (a, b) => a.start_sec - b.start_sec
      ),
    }));
    get().computeDuration();
  },

  computeDuration: () => {
    const max = get().clips.reduce(
      (m, c) => Math.max(m, c.start_sec + (c.trim_out_sec - c.trim_in_sec)),
      0
    );
    set({ duration_sec: max });
  },

  exportEditDecisions: () => {
    const s = get();
    return {
      version: 1,
      engine: "agentic-cuts",
      pipeline: { name: "user-edit", version: "0.1", type: "footage_based" },
      duration_sec: s.duration_sec,
      tracks: {
        video: s.clips
          .filter((c) => c.track === 0)
          .map((c) => ({
            type: "clip",
            source_name: c.name,
            timeline_start_sec: c.start_sec,
            trim_in_sec: c.trim_in_sec,
            trim_out_sec: c.trim_out_sec,
          })),
      },
    };
  },
}));
