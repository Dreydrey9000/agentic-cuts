import Link from "next/link";
import { DEMO_PLANS } from "@/lib/render-plan";

export default function PlansIndex() {
  const plans = Object.keys(DEMO_PLANS);
  return (
    <main className="max-w-4xl mx-auto px-6 py-12">
      <nav className="mb-8 text-sm">
        <Link href="/" className="text-white/55 hover:text-yellow-400">← back to editor</Link>
      </nav>
      <h1 className="text-4xl font-black tracking-tight mb-3">Demo render plans</h1>
      <p className="text-white/60 mb-10">
        These are read-only previews of what the Python engine emits. Use the{" "}
        <a href="/" className="text-yellow-400 underline">editor</a> on the home page to
        actually cut a video.
      </p>
      <div className="grid gap-3">
        {plans.map((p) => (
          <Link
            key={p}
            href={`/timeline/${p}`}
            className="block border border-white/10 rounded-lg p-5 hover:border-yellow-400/50 transition-colors bg-white/[0.02]"
          >
            <div className="flex items-center justify-between">
              <div>
                <div className="font-extrabold text-lg">{p}</div>
                <div className="text-sm text-white/55 mt-1">
                  {DEMO_PLANS[p].pipeline.type} · {DEMO_PLANS[p].render_target.resolution} ·{" "}
                  {DEMO_PLANS[p].stages.length} stages
                </div>
              </div>
              <div className="text-yellow-400 font-bold text-sm">open →</div>
            </div>
          </Link>
        ))}
      </div>
    </main>
  );
}
