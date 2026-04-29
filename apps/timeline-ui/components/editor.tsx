"use client";

import { Preview } from "./preview";
import { Track } from "./track";
import { FileDrop } from "./file-drop";
import { Transport } from "./transport";

export function Editor() {
  return (
    <main className="min-h-screen flex flex-col">
      <header className="px-6 py-4 border-b border-white/10 flex items-center justify-between">
        <div>
          <div className="font-black tracking-tight text-base">
            Agentic Cuts <span className="text-yellow-400">· Editor</span>
          </div>
          <div className="text-[11px] text-white/50">
            v0.4 · drop video, drag to move, drag edges to trim, space to play, c to split, export JSON
          </div>
        </div>
        <nav className="flex gap-5 text-sm">
          <a href="https://github.com/Dreydrey9000/agentic-cuts" className="text-white/55 hover:text-yellow-400">
            GitHub
          </a>
          <a href="/plans" className="text-white/55 hover:text-yellow-400">
            Demo plans
          </a>
        </nav>
      </header>

      <div className="flex-1 grid grid-cols-1 md:grid-cols-[1fr_360px] gap-4 p-4">
        <section className="flex flex-col gap-4">
          <Preview />
          <Transport />
          <Track />
        </section>
        <aside className="flex flex-col gap-4">
          <FileDrop />
          <ShortcutsCard />
          <AboutCard />
        </aside>
      </div>
    </main>
  );
}

function ShortcutsCard() {
  return (
    <div className="border border-white/10 rounded-lg p-4 bg-white/[0.02]">
      <h3 className="font-extrabold text-xs tracking-wider uppercase text-white/60 mb-3">
        Shortcuts
      </h3>
      <ul className="space-y-1 text-sm text-white/70">
        <li><kbd className="kbd">space</kbd> · play / pause</li>
        <li><kbd className="kbd">j</kbd> <kbd className="kbd">k</kbd> <kbd className="kbd">l</kbd> · scrub back · play · forward</li>
        <li><kbd className="kbd">c</kbd> · split clip at playhead</li>
        <li><kbd className="kbd">←</kbd> <kbd className="kbd">→</kbd> · nudge playhead 0.1s (shift = 5s)</li>
        <li><kbd className="kbd">Home</kbd> · jump to start</li>
        <li><kbd className="kbd">End</kbd> · jump to end</li>
      </ul>
      <style>{`
        .kbd {
          display: inline-block;
          padding: 1px 6px;
          background: rgba(255,255,255,0.08);
          border: 1px solid rgba(255,255,255,0.15);
          border-radius: 3px;
          font-family: ui-monospace, monospace;
          font-size: 11px;
          color: #ffd200;
        }
      `}</style>
    </div>
  );
}

function AboutCard() {
  return (
    <div className="border border-white/10 rounded-lg p-4 bg-white/[0.02] text-xs leading-relaxed text-white/60">
      <h3 className="font-extrabold text-[10px] tracking-wider uppercase text-white/55 mb-2">
        v0.4 status
      </h3>
      <p className="mb-2">
        This is the v0.4 editor MVP. Cuts, drag, trim, scrub, play, split, export
        edit decisions as JSON the Python engine consumes. Files stay local — no
        upload, no cloud, no auth.
      </p>
      <p className="mb-2">
        v0.5 ships: multi-track (captions + audio), Remotion preview render,
        undo / redo, keyboard-driven trim, drag from one clip onto another,
        magnetic snap to playhead.
      </p>
      <p>
        Drop the JSON into <code className="text-yellow-400">agentic-cuts plan --import</code> when v0.5 lands and the engine renders the timeline.
      </p>
    </div>
  );
}
