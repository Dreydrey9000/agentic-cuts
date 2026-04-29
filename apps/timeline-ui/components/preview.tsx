"use client";

import { useRef, useEffect } from "react";
import { useEditor } from "@/lib/editor-store";

export function Preview() {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const { clips, playhead_sec, is_playing, setPlayhead, setPlaying, duration_sec } = useEditor();
  const rafRef = useRef<number | null>(null);
  const lastTickRef = useRef<number>(0);

  // Find the active clip + position within source media.
  const active = (() => {
    let cumulative = 0;
    for (const c of [...clips].sort((a, b) => a.start_sec - b.start_sec)) {
      const len = c.trim_out_sec - c.trim_in_sec;
      if (playhead_sec >= c.start_sec && playhead_sec < c.start_sec + len) {
        const inside = playhead_sec - c.start_sec;
        return { clip: c, source_time: c.trim_in_sec + inside };
      }
      cumulative = c.start_sec + len;
    }
    return null;
  })();

  // When the active clip changes, swap src.
  useEffect(() => {
    const v = videoRef.current;
    if (!v) return;
    if (active && v.src !== active.clip.src) {
      v.src = active.clip.src;
      v.load();
    }
  }, [active?.clip.id, active?.clip.src]);

  // Sync playhead → video element when paused.
  useEffect(() => {
    const v = videoRef.current;
    if (!v || !active) return;
    if (!is_playing) {
      const drift = Math.abs(v.currentTime - active.source_time);
      if (drift > 0.05) v.currentTime = active.source_time;
    }
  }, [active?.source_time, is_playing, active]);

  // Play/pause loop drives the global playhead so multi-clip playback works.
  useEffect(() => {
    const v = videoRef.current;
    if (!v || !active) {
      setPlaying(false);
      return;
    }
    if (is_playing) {
      v.play().catch(() => setPlaying(false));
      lastTickRef.current = performance.now();
      const tick = (now: number) => {
        const dt = (now - lastTickRef.current) / 1000;
        lastTickRef.current = now;
        const next = useEditor.getState().playhead_sec + dt;
        if (next >= duration_sec) {
          setPlayhead(0);
          setPlaying(false);
          return;
        }
        setPlayhead(next);
        rafRef.current = requestAnimationFrame(tick);
      };
      rafRef.current = requestAnimationFrame(tick);
      return () => {
        if (rafRef.current) cancelAnimationFrame(rafRef.current);
      };
    } else {
      v.pause();
    }
  }, [is_playing, active?.clip.id, duration_sec, setPlayhead, setPlaying]);

  return (
    <div className="aspect-video bg-black rounded-lg overflow-hidden border border-white/10 flex items-center justify-center">
      {active ? (
        <video
          ref={videoRef}
          className="max-h-full max-w-full"
          playsInline
          muted={false}
        />
      ) : (
        <div className="text-white/40 text-sm">
          Drop a video below or use the file picker to start editing.
        </div>
      )}
    </div>
  );
}
