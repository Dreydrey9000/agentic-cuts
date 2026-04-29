import Link from "next/link";
import { DEMO_PLANS } from "@/lib/render-plan";

export default function Home() {
  const plans = Object.keys(DEMO_PLANS);
  return (
    <main className="max-w-5xl mx-auto px-6 py-16">
      <header className="flex items-center justify-between mb-16">
        <div className="font-black tracking-tight text-lg">
          Agentic Cuts <span className="text-yellow-400">· Timeline</span>
        </div>
        <nav className="text-sm flex gap-6 text-white/60">
          <a href="https://github.com/Dreydrey9000/agentic-cuts" className="hover:text-yellow-400">GitHub</a>
          <a href="https://agentic-cuts-drey.pages.dev" className="hover:text-yellow-400">Drey</a>
          <a href="https://agentic-cuts-1bb.pages.dev" className="hover:text-yellow-400">1BB</a>
          <a href="https://agentic-cuts-ve.pages.dev" className="hover:text-yellow-400">VE</a>
        </nav>
      </header>

      <h1 className="text-6xl md:text-8xl font-black leading-[0.9] tracking-tight mb-8">
        The <span className="text-yellow-400">timeline</span><br />
        is the source of truth.
      </h1>
      <p className="text-lg md:text-xl text-white/70 max-w-2xl mb-12">
        Scrub, drag, override. Chat-only is the wrong UX for video. Mosaic and Cardboard
        admitted it on HN. We&apos;re fixing it. The agent edits the JSON; you supervise the
        gestures.
      </p>

      <section className="mb-20">
        <h2 className="font-black text-2xl mb-6 tracking-tight">Demo render plans</h2>
        <div className="grid gap-3">
          {plans.map((p) => (
            <Link
              key={p}
              href={`/timeline/${p}`}
              className="block border border-white/10 rounded-lg p-6 hover:border-yellow-400/50 transition-colors bg-white/[0.02]"
            >
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-extrabold text-xl">{p}</div>
                  <div className="text-sm text-white/55 mt-1">
                    {DEMO_PLANS[p].pipeline.type} · {DEMO_PLANS[p].render_target.resolution} ·
                    {" "}{DEMO_PLANS[p].stages.length} stages
                  </div>
                </div>
                <div className="text-yellow-400 font-bold text-sm">
                  open →
                </div>
              </div>
            </Link>
          ))}
        </div>
      </section>

      <section className="mb-20">
        <h2 className="font-black text-2xl mb-4 tracking-tight">v0.4 status</h2>
        <ul className="text-white/70 space-y-2 text-sm">
          <li>· Demo plans render-only. Real video preview ships in v0.5 via Remotion.</li>
          <li>· Click-to-scrub works. Drag, J/K/L, in/out marks ship in v0.5.</li>
          <li>· No auth, no project save — runs entirely against demo plans baked into the bundle.</li>
          <li>· Tauri desktop wrapper queued for v0.6 once browser path is solid.</li>
        </ul>
      </section>

      <footer className="mt-24 pt-8 border-t border-white/10 text-xs text-white/40">
        <div>Apache 2.0. Open-source. <a href="https://github.com/Dreydrey9000/agentic-cuts" className="text-yellow-400 hover:underline">github.com/Dreydrey9000/agentic-cuts</a></div>
      </footer>
    </main>
  );
}
