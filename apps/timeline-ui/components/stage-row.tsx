"use client";

import clsx from "clsx";
import type { StageSummary } from "@/lib/render-plan";

interface Props {
  stage: StageSummary;
  status: "pending" | "in_progress" | "done" | "blocked";
  onClick?: () => void;
}

export function StageRow({ stage, status, onClick }: Props) {
  const statusColor = {
    pending: "bg-white/10 text-white/60",
    in_progress: "bg-yellow-400/20 text-yellow-300",
    done: "bg-cyan-400/20 text-cyan-300",
    blocked: "bg-red-500/20 text-red-300",
  }[status];

  return (
    <button
      onClick={onClick}
      className={clsx(
        "w-full text-left grid grid-cols-[40px_1fr_auto_auto] gap-3 items-center",
        "px-4 py-3 rounded-md border border-white/8 bg-white/[0.02]",
        "hover:border-yellow-400/40 hover:bg-white/[0.04] transition-colors"
      )}
    >
      <div className={clsx("rounded text-xs font-bold uppercase tracking-wider px-2 py-1 text-center", statusColor)}>
        {String(stage.index + 1).padStart(2, "0")}
      </div>
      <div>
        <div className="font-extrabold text-base">{stage.name}</div>
        <div className="text-xs text-white/50 font-mono">{stage.director_skill}</div>
      </div>
      <div className="flex gap-1 flex-wrap max-w-[280px] justify-end">
        {stage.capabilities_required.map((c) => (
          <span key={c} className="px-2 py-0.5 rounded-full text-[10px] uppercase tracking-wider bg-yellow-400/15 text-yellow-200 font-bold">
            {c}
          </span>
        ))}
        {stage.optional && (
          <span className="px-2 py-0.5 rounded-full text-[10px] uppercase tracking-wider bg-white/10 text-white/60">optional</span>
        )}
        {stage.human_approval_default && (
          <span className="px-2 py-0.5 rounded-full text-[10px] uppercase tracking-wider bg-red-500/15 text-red-300">approval</span>
        )}
      </div>
      <div className="text-white/40 text-xs">{status === "done" ? "✓" : status === "in_progress" ? "···" : "·"}</div>
    </button>
  );
}
