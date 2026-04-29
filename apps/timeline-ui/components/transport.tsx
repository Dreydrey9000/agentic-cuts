"use client";

import { useEffect } from "react";
import { useEditor } from "@/lib/editor-store";

export function Transport() {
  const {
    is_playing,
    playhead_sec,
    duration_sec,
    setPlayhead,
    togglePlay,
    splitAtPlayhead,
    exportEditDecisions,
    clips,
  } = useEditor();

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      // Ignore when typing in an input.
      if (
        document.activeElement &&
        ["INPUT", "TEXTAREA"].includes(document.activeElement.tagName)
      )
        return;
      if (e.code === "Space") {
        e.preventDefault();
        togglePlay();
      } else if (e.key === "j") {
        setPlayhead(Math.max(0, playhead_sec - 1));
      } else if (e.key === "k") {
        // toggle play (vi-style)
        togglePlay();
      } else if (e.key === "l") {
        setPlayhead(Math.min(duration_sec, playhead_sec + 1));
      } else if (e.key === "c") {
        splitAtPlayhead();
      } else if (e.key === "ArrowLeft") {
        setPlayhead(Math.max(0, playhead_sec - (e.shiftKey ? 5 : 0.1)));
      } else if (e.key === "ArrowRight") {
        setPlayhead(Math.min(duration_sec, playhead_sec + (e.shiftKey ? 5 : 0.1)));
      } else if (e.key === "Home") {
        setPlayhead(0);
      } else if (e.key === "End") {
        setPlayhead(duration_sec);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [playhead_sec, duration_sec, togglePlay, setPlayhead, splitAtPlayhead]);

  const exportJson = () => {
    const data = exportEditDecisions();
    const blob = new Blob([JSON.stringify(data, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "edit-decisions.json";
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex items-center gap-3 flex-wrap">
      <button
        onClick={togglePlay}
        disabled={clips.length === 0}
        className="bg-yellow-400 text-black font-extrabold px-5 py-2 rounded hover:bg-yellow-300 disabled:opacity-40"
      >
        {is_playing ? "Pause (space)" : "Play (space)"}
      </button>
      <button
        onClick={() => setPlayhead(0)}
        className="border border-white/20 text-white/70 px-4 py-2 rounded hover:border-yellow-400 hover:text-yellow-400"
      >
        Reset
      </button>
      <button
        onClick={splitAtPlayhead}
        disabled={clips.length === 0}
        className="border border-white/20 text-white/70 px-4 py-2 rounded hover:border-yellow-400 hover:text-yellow-400 disabled:opacity-40"
      >
        Split (c)
      </button>
      <div className="ml-auto flex items-center gap-3">
        <div className="font-mono text-xs text-white/55">
          {clips.length} clip{clips.length === 1 ? "" : "s"} · {duration_sec.toFixed(1)}s
        </div>
        <button
          onClick={exportJson}
          disabled={clips.length === 0}
          className="border border-cyan-400 text-cyan-300 px-4 py-2 rounded hover:bg-cyan-400 hover:text-black font-bold disabled:opacity-40"
        >
          Export edit decisions JSON
        </button>
      </div>
    </div>
  );
}
