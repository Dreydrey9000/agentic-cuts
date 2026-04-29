"use client";

import { useRef, useState } from "react";
import { useEditor } from "@/lib/editor-store";

async function probeDuration(src: string): Promise<number> {
  return new Promise((resolve, reject) => {
    const v = document.createElement("video");
    v.preload = "metadata";
    v.muted = true;
    v.onloadedmetadata = () => {
      resolve(v.duration);
      v.remove();
    };
    v.onerror = () => {
      reject(new Error("could not load video"));
      v.remove();
    };
    v.src = src;
  });
}

export function FileDrop() {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const { addClip } = useEditor();
  const [busy, setBusy] = useState(false);

  const handleFiles = async (files: FileList | null) => {
    if (!files) return;
    setBusy(true);
    for (const file of Array.from(files)) {
      if (!file.type.startsWith("video/")) continue;
      const src = URL.createObjectURL(file);
      try {
        const duration_sec = await probeDuration(src);
        addClip({ name: file.name, src, duration_sec });
      } catch (e) {
        console.warn("skipping", file.name, e);
      }
    }
    setBusy(false);
  };

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        e.currentTarget.classList.add("border-yellow-400");
      }}
      onDragLeave={(e) => e.currentTarget.classList.remove("border-yellow-400")}
      onDrop={(e) => {
        e.preventDefault();
        e.currentTarget.classList.remove("border-yellow-400");
        handleFiles(e.dataTransfer.files);
      }}
      className="border-2 border-dashed border-white/15 rounded-lg p-6 text-center bg-white/[0.02] transition-colors"
    >
      <input
        ref={inputRef}
        type="file"
        accept="video/*"
        multiple
        className="hidden"
        onChange={(e) => handleFiles(e.target.files)}
      />
      <button
        onClick={() => inputRef.current?.click()}
        disabled={busy}
        className="bg-yellow-400 text-black font-extrabold px-6 py-3 rounded hover:bg-yellow-300 disabled:opacity-50"
      >
        {busy ? "loading..." : "Add video file"}
      </button>
      <p className="mt-3 text-xs text-white/50">
        or drop .mp4, .mov, .webm, .mkv files anywhere on this box. Files stay local — nothing uploaded.
      </p>
    </div>
  );
}
