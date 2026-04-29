"use client";

import { useRef, useState, useEffect } from "react";
import clsx from "clsx";
import { useEditor, type Clip } from "@/lib/editor-store";

interface DragState {
  type: "move" | "trim-left" | "trim-right";
  clipId: string;
  startX: number;
  origStart: number;
  origIn: number;
  origOut: number;
  pxPerSec: number;
}

export function Track() {
  const {
    clips,
    duration_sec,
    playhead_sec,
    setPlayhead,
    selected_clip_id,
    selectClip,
    updateClip,
    removeClip,
  } = useEditor();
  const trackRef = useRef<HTMLDivElement | null>(null);
  const [drag, setDrag] = useState<DragState | null>(null);

  const totalSec = Math.max(duration_sec, 30);
  const pxPerSec = trackRef.current
    ? trackRef.current.clientWidth / totalSec
    : 24;

  const handleScrub = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!trackRef.current) return;
    const rect = trackRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const sec = (x / rect.width) * totalSec;
    setPlayhead(sec);
  };

  const startDrag = (
    e: React.MouseEvent,
    clip: Clip,
    type: DragState["type"]
  ) => {
    e.stopPropagation();
    e.preventDefault();
    if (!trackRef.current) return;
    const rect = trackRef.current.getBoundingClientRect();
    setDrag({
      type,
      clipId: clip.id,
      startX: e.clientX,
      origStart: clip.start_sec,
      origIn: clip.trim_in_sec,
      origOut: clip.trim_out_sec,
      pxPerSec: rect.width / totalSec,
    });
    selectClip(clip.id);
  };

  useEffect(() => {
    if (!drag) return;
    const onMove = (e: MouseEvent) => {
      const dx = e.clientX - drag.startX;
      const dSec = dx / drag.pxPerSec;
      if (drag.type === "move") {
        updateClip(drag.clipId, {
          start_sec: Math.max(0, drag.origStart + dSec),
        });
      } else if (drag.type === "trim-left") {
        const newIn = Math.min(
          drag.origOut - 0.1,
          Math.max(0, drag.origIn + dSec)
        );
        const shifted = newIn - drag.origIn;
        updateClip(drag.clipId, {
          trim_in_sec: newIn,
          start_sec: Math.max(0, drag.origStart + shifted),
        });
      } else if (drag.type === "trim-right") {
        const newOut = Math.max(drag.origIn + 0.1, drag.origOut + dSec);
        updateClip(drag.clipId, { trim_out_sec: newOut });
      }
    };
    const onUp = () => setDrag(null);
    window.addEventListener("mousemove", onMove);
    window.addEventListener("mouseup", onUp);
    return () => {
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mouseup", onUp);
    };
  }, [drag, updateClip]);

  // Tick mark step
  const tickStep = totalSec > 600 ? 60 : totalSec > 120 ? 15 : totalSec > 30 ? 5 : 2;
  const ticks: number[] = [];
  for (let s = 0; s <= totalSec; s += tickStep) ticks.push(s);

  return (
    <div className="border border-white/10 rounded-lg p-3 bg-white/[0.02]">
      <div className="flex items-center justify-between mb-2 px-1">
        <h3 className="font-extrabold text-xs tracking-wider uppercase text-white/60">
          Timeline
        </h3>
        <div className="font-mono text-xs text-yellow-300">
          {playhead_sec.toFixed(2)}s / {totalSec.toFixed(2)}s
        </div>
      </div>
      <div ref={trackRef} className="relative">
        <div className="relative h-4 mb-1">
          {ticks.map((t) => (
            <div
              key={t}
              className="absolute top-0 text-[10px] text-white/40 font-mono"
              style={{ left: `${(t / totalSec) * 100}%`, transform: "translateX(-50%)" }}
            >
              {t}s
            </div>
          ))}
        </div>
        <div
          className="relative h-20 bg-white/5 rounded-md cursor-crosshair"
          onClick={handleScrub}
        >
          {clips.map((c) => {
            const len = c.trim_out_sec - c.trim_in_sec;
            const left = (c.start_sec / totalSec) * 100;
            const width = (len / totalSec) * 100;
            const selected = selected_clip_id === c.id;
            return (
              <div
                key={c.id}
                onMouseDown={(e) => startDrag(e, c, "move")}
                className={clsx(
                  "absolute top-1 bottom-1 rounded border-2 flex items-center px-2 overflow-hidden cursor-grab active:cursor-grabbing",
                  selected
                    ? "border-cyan-400 ring-2 ring-cyan-400/40"
                    : "border-yellow-400/60"
                )}
                style={{
                  left: `${left}%`,
                  width: `${width}%`,
                  background: c.color,
                }}
                title={`${c.name} (${len.toFixed(2)}s)`}
              >
                <div
                  onMouseDown={(e) => startDrag(e, c, "trim-left")}
                  className="absolute left-0 top-0 bottom-0 w-2 cursor-ew-resize hover:bg-white/30"
                />
                <div className="text-[11px] font-bold text-white truncate flex-1 select-none pointer-events-none px-1">
                  {c.name}
                </div>
                <div
                  onMouseDown={(e) => startDrag(e, c, "trim-right")}
                  className="absolute right-0 top-0 bottom-0 w-2 cursor-ew-resize hover:bg-white/30"
                />
              </div>
            );
          })}
          <div
            className="absolute top-0 bottom-0 w-0.5 bg-cyan-400 pointer-events-none z-10"
            style={{ left: `${(playhead_sec / totalSec) * 100}%` }}
          />
        </div>
      </div>
      <div className="mt-2 px-1 flex items-center justify-between text-[11px] text-white/40">
        <span>Click track to scrub. Drag clips to move. Drag clip edges to trim.</span>
        {selected_clip_id && (
          <button
            onClick={() => removeClip(selected_clip_id)}
            className="text-red-400 hover:text-red-300 font-bold"
          >
            DELETE selected
          </button>
        )}
      </div>
    </div>
  );
}
