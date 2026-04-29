"""CLI smoke tests — every subcommand returns 0 on the happy path."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agentic_cuts.cli import main


def test_cli_pipelines_lists_5(capsys):
    rc = main(["pipelines"])
    assert rc == 0
    out = capsys.readouterr().out
    for name in ("clip-factory", "talking-head", "documentary-montage",
                 "podcast-repurpose", "animated-explainer"):
        assert name in out


def test_cli_show_clip_factory(capsys):
    rc = main(["show", "clip-factory"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "clip-factory" in out
    assert "ingest" in out
    assert "9:16" in out


def test_cli_show_unknown_pipeline_returns_2(capsys):
    rc = main(["show", "does-not-exist"])
    assert rc == 2


def test_cli_presets_lists_20(capsys):
    rc = main(["presets"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "tiktok-yellow-bold" in out
    assert "hormozi-style" in out


def test_cli_brand_kit_validates_example(capsys):
    repo_root = Path(__file__).resolve().parents[1]
    rc = main(["brand-kit", str(repo_root / "brand-kit.example.yaml")])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Example Brand" in out


def test_cli_plan_emits_valid_json(capsys, tmp_path: Path):
    out_path = tmp_path / "plan.json"
    rc = main(["plan",
               "--pipeline", "clip-factory",
               "--video", "/tmp/fake.mp4",
               "--target", "tiktok",
               "--out", str(out_path)])
    assert rc == 0
    plan = json.loads(out_path.read_text())
    assert plan["engine"] == "agentic-cuts"
    assert plan["pipeline"]["name"] == "clip-factory"
    assert plan["render_target"]["resolution"] == "1080x1920"
    assert plan["render_target"]["name"] == "tiktok"
    assert len(plan["stages"]) >= 5
    assert plan["budget"]["mode"] == "cap"


def test_cli_plan_unknown_target_returns_2(capsys):
    rc = main(["plan",
               "--pipeline", "clip-factory",
               "--target", "nonexistent_target"])
    assert rc == 2


def test_cli_plan_unknown_pipeline_returns_2(capsys):
    rc = main(["plan",
               "--pipeline", "nope"])
    assert rc == 2
