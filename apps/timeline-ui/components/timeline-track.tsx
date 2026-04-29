"use client";

import { useState, useMemo } from "react";

interface Clip {
  id: string;
  start_sec: number;
  end_sec: number;
  label: string;
  color?: string;
}

interface Props {
  totalDurationSec: number;
  clips: Clip[];
  onScrub?: (sec: number) => void;
}

export function TimelineTrack({ totalDurationSec, clips, onScrub }: Props) {
  const [head, setHead] = useState(0);

  const ticks = useMemo(() => {
    const step = totalDurationSec > 600 ? 60 : totalDurationSec > 120 ? 15 : 5;
    const out: number[] = [];
    for (let s = 0; s <= totalDurationSec; s += step) out.push(s);
    return out;
  }, [totalDurationSec]);

  const handleScrub = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const sec = (x / rect.width) * totalDurationSec;
    setHead(sec);
    onScrub?.(sec);
  };

  return (
    <div className="border border-white/10 rounded-lg p-4 bg-white/[0.02]">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-extrabold text-sm tracking-wider uppercase text-white/60">Timeline</h3>
        <div className="font-mono text-xs text-yellow-300">
          {head.toFixed(2)}s / {totalDurationSec.toFixed(2)}s
        </div>
      </div>
      <div className="relative">
        {/* Tick marks */}
        <div className="relative h-4 mb-1">
          {ticks.map((t) => (
            <div
              key={t}
              className="absolute top-0 text-[10px] text-white/40 font-mono"
              style={{ left: `${(t / totalDurationSec) * 100}%`, transform: "translateX(-50%)" }}
            >
              {t}s
            </div>
          ))}
        </div>
        {/* Track */}
        <div
          className="relative h-16 bg-white/5 rounded-md overflow-hidden cursor-crosshair"
          onClick={handleScrub}
        >
          {clips.map((c) => {
            const left = (c.start_sec / totalDurationSec) * 100;
            const width = ((c.end_sec - c.start_sec) / totalDurationSec) * 100;
            return (
              <div
                key={c.id}
                className="absolute top-1 bottom-1 rounded border border-yellow-400/40 px-2 flex items-center text-xs font-bold overflow-hidden"
                style={{
                  left: `${left}%`,
                  width: `${width}%`,
                  background: c.color || "rgba(255, 210, 0, 0.18)",
                  color: c.color ? "white" : "#ffd200",
                }}
                title={c.label}
              >
                <span className="truncate">{c.label}</span>
              </div>
            );
          })}
          {/* Playhead */}
          <div
            className="absolute top-0 bottom-0 w-0.5 bg-cyan-400 pointer-events-none"
            style={{ left: `${(head / totalDurationSec) * 100}%` }}
          />
        </div>
      </div>
      <div className="mt-3 text-xs text-white/40">
        Click anywhere on the track to scrub. Real drag, J/K/L scrub, in/out marks ship in v0.5.
      </div>
    </div>
  );
}
