"""Agentic Cuts command-line interface.

Minimal CLI for v0.2. Validates the architecture works end-to-end without
needing real model providers wired up. Once Task 8 lands, the same commands
will execute renders for real.

Subcommands:
  pipelines           List all built-in pipelines.
  show <name>         Show details for a pipeline manifest.
  presets             List all built-in caption presets.
  brand-kit <path>    Validate a brand-kit.yaml file.
  plan <video>        Emit a render plan JSON for a pipeline (no actual render).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from agentic_cuts import (
    PROFILES,
    BrandKitLoadError,
    DeliveryPromiseDefaults,
    PipelineLoadError,
    discover_pipelines,
    discover_presets,
    load_brand_kit,
    load_manifest,
)
from agentic_cuts.captions import CAPTIONS_DIR
from agentic_cuts.pipelines import PIPELINES_DIR


def _format_table(rows: list[list[str]], headers: list[str]) -> str:
    widths = [max(len(headers[i]), *(len(r[i]) for r in rows)) for i in range(len(headers))]
    out = []
    out.append("  ".join(h.ljust(widths[i]) for i, h in enumerate(headers)))
    out.append("  ".join("-" * w for w in widths))
    for r in rows:
        out.append("  ".join(c.ljust(widths[i]) for i, c in enumerate(r)))
    return "\n".join(out)


def cmd_pipelines(args: argparse.Namespace) -> int:
    pipelines = discover_pipelines(PIPELINES_DIR)
    rows = [
        [
            name,
            p.delivery_promise.target_aspect,
            f"{len(p.stages)}",
            f"${p.budget.default_cap_usd:.2f}",
            ",".join(p.tags[:3]),
        ]
        for name, p in sorted(pipelines.items())
    ]
    print(_format_table(rows, ["pipeline", "aspect", "stages", "cap", "tags"]))
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    try:
        p = load_manifest(PIPELINES_DIR / f"{args.name}.yaml")
    except PipelineLoadError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(f"# {p.name} v{p.version}")
    print()
    print(p.description.strip())
    print()
    print(f"type:                  {p.type}")
    print(f"target_aspect:         {p.delivery_promise.target_aspect}")
    print(f"requires_motion:       {p.delivery_promise.requires_motion}")
    print(f"requires_audio:        {p.delivery_promise.requires_audio}")
    print(f"requires_captions:     {p.delivery_promise.requires_captions}")
    print(f"requires_narration:    {p.delivery_promise.requires_narration}")
    print(f"budget_default_cap:    ${p.budget.default_cap_usd:.2f}")
    print(f"budget_mode:           {p.budget.mode.value}")
    print(f"checkpoint_policy:     {p.checkpoint.policy.value}")
    print()
    print("stages:")
    for i, s in enumerate(p.stages, 1):
        approval = " [approval]" if s.human_approval_default else ""
        opt = " [optional]" if s.optional else ""
        caps = ",".join(c.value for c in s.capabilities_required) or "—"
        print(f"  {i:2d}. {s.name:24}{approval}{opt}  caps={caps}")
        print(f"      director: {s.director_skill}")
    return 0


def cmd_presets(args: argparse.Namespace) -> int:
    presets = discover_presets(CAPTIONS_DIR)
    rows = [
        [
            p.name,
            p.style_family.value,
            p.typography.family,
            f"{p.max_words_per_card}",
            "yes" if p.contains_emojis else "no",
            ",".join(p.tags[:2]),
        ]
        for p in sorted(presets.values(), key=lambda x: x.name)
    ]
    print(_format_table(rows, ["preset", "family", "font", "words", "emoji", "tags"]))
    return 0


def cmd_brand_kit(args: argparse.Namespace) -> int:
    try:
        bk = load_brand_kit(args.path)
    except BrandKitLoadError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(f"# {bk.display_name} ({bk.tenant_id})")
    print()
    print(f"description:        {bk.description}")
    print(f"palette:            {len(bk.palette)} colors")
    for c in bk.palette:
        print(f"  {c.name:16} {c.hex}")
    print(f"primary font:       {bk.primary_typography.family} weight {bk.primary_typography.weight}")
    print(f"voice:              {bk.voice.primary_voice}")
    print(f"caption preset:     {bk.captions.default_preset}")
    print(f"default pipelines:  {', '.join(bk.default_pipelines) or '(all)'}")
    print(f"no_emojis:          {bk.no_emojis}")
    return 0


def cmd_plan(args: argparse.Namespace) -> int:
    """Emit a render plan JSON. No actual render — just proves the architecture works."""
    try:
        manifest = load_manifest(PIPELINES_DIR / f"{args.pipeline}.yaml")
    except PipelineLoadError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    target = args.target or "tiktok"
    profile = PROFILES.get(target)
    if profile is None:
        print(f"error: unknown render target {target!r}. Known: {sorted(PROFILES)}", file=sys.stderr)
        return 2

    promise = DeliveryPromiseDefaults(
        target_aspect=manifest.delivery_promise.target_aspect,
        requires_motion=manifest.delivery_promise.requires_motion,
        requires_audio=manifest.delivery_promise.requires_audio,
        requires_captions=manifest.delivery_promise.requires_captions,
        requires_narration=manifest.delivery_promise.requires_narration,
        requires_music=manifest.delivery_promise.requires_music,
        duration_tolerance_sec=manifest.delivery_promise.duration_tolerance_sec,
    )

    plan = {
        "version": 1,
        "engine": "agentic-cuts",
        "pipeline": {
            "name": manifest.name,
            "version": manifest.version,
            "type": manifest.type,
        },
        "input": {
            "video_path": str(Path(args.video).expanduser().resolve())
            if args.video else None,
        },
        "render_target": {
            "name": profile.name,
            "resolution": profile.resolution,
            "fps": profile.fps,
            "container": profile.container,
            "codec": profile.codec,
            "safe_zone_top_pct": profile.safe_zone_top_pct,
            "safe_zone_bottom_pct": profile.safe_zone_bottom_pct,
        },
        "delivery_promise": promise.model_dump(),
        "stages": [
            {
                "index": i,
                "name": s.name,
                "director_skill": s.director_skill,
                "capabilities_required": [c.value for c in s.capabilities_required],
                "artifacts_produced": list(s.artifacts_produced),
                "human_approval_default": s.human_approval_default,
                "optional": s.optional,
            }
            for i, s in enumerate(manifest.stages)
        ],
        "budget": {
            "cap_usd": manifest.budget.default_cap_usd,
            "mode": manifest.budget.mode.value,
        },
    }

    if args.out:
        out_path = Path(args.out).expanduser().resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(plan, indent=2))
        print(f"plan written: {out_path}")
    else:
        print(json.dumps(plan, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="agentic-cuts", description=__doc__.split("\n")[0])
    sub = parser.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("pipelines", help="List all built-in pipelines.")
    sp.set_defaults(func=cmd_pipelines)

    sp = sub.add_parser("show", help="Show details for a pipeline manifest.")
    sp.add_argument("name", help="Pipeline name (e.g. clip-factory)")
    sp.set_defaults(func=cmd_show)

    sp = sub.add_parser("presets", help="List all built-in caption presets.")
    sp.set_defaults(func=cmd_presets)

    sp = sub.add_parser("brand-kit", help="Validate a brand-kit.yaml file.")
    sp.add_argument("path", help="Path to brand-kit.yaml")
    sp.set_defaults(func=cmd_brand_kit)

    sp = sub.add_parser("plan", help="Emit a render plan JSON for a pipeline.")
    sp.add_argument("--pipeline", required=True, help="Pipeline name (e.g. clip-factory)")
    sp.add_argument("--video", default=None, help="Path to source video (optional for v0)")
    sp.add_argument("--target", default=None,
                    help="Render target (tiktok, reels, shorts, youtube, square, ...)")
    sp.add_argument("--out", default=None, help="Write plan to this path instead of stdout")
    sp.set_defaults(func=cmd_plan)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
