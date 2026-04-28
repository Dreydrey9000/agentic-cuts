"""Checkpoint, RunCache, and SkillRAG behavior."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agentic_cuts import Checkpoint, RunCache, SkillRAG, cache_key


def test_checkpoint_save_and_load(tmp_path: Path):
    ckpt = Checkpoint(tmp_path)
    ckpt.save("script", {"text": "hello"}, cost_usd=0.10, duration_ms=120)
    ckpt.save("scene_plan", {"scenes": [1, 2, 3]}, cost_usd=0.05)
    assert ckpt.latest_stage() == "scene_plan"
    assert ckpt.list_stages() == ["script", "scene_plan"]
    assert ckpt.load("script") == {"text": "hello"}
    assert ckpt.total_cost_usd() == pytest.approx(0.15)


def test_checkpoint_atomic_write_survives_corrupt_state(tmp_path: Path):
    ckpt = Checkpoint(tmp_path)
    ckpt.save("a", {"v": 1})
    ckpt.checkpoint_file.write_text("not-json{{")
    ckpt.save("b", {"v": 2})
    state = json.loads(ckpt.checkpoint_file.read_text())
    assert "b" in state["stages"]


def test_cache_key_is_stable():
    k1 = cache_key(tool_name="x", tool_version="1", prompt="hi", seed=7)
    k2 = cache_key(tool_name="x", tool_version="1", prompt="hi", seed=7)
    assert k1 == k2
    k3 = cache_key(tool_name="x", tool_version="1", prompt="hi", seed=8)
    assert k3 != k1


def test_run_cache_hit_and_miss(tmp_path: Path):
    cache = RunCache(tmp_path / "runs.db")
    artifact = tmp_path / "audio.wav"
    artifact.write_bytes(b"RIFF...")
    k = cache_key(tool_name="x", tool_version="1", prompt="hi", seed=1)
    assert cache.get(k) is None
    cache.put(k, tool_name="x", tool_version="1",
              artifact_paths=[artifact], cost_usd=0.20)
    hit = cache.get(k)
    assert hit is not None
    assert hit.cost_usd == 0.20
    assert hit.artifact_paths == [str(artifact)]


def test_run_cache_misses_when_artifact_deleted(tmp_path: Path):
    cache = RunCache(tmp_path / "runs.db")
    artifact = tmp_path / "audio.wav"
    artifact.write_bytes(b"x")
    k = cache_key(tool_name="x", tool_version="1", prompt="hi", seed=2)
    cache.put(k, tool_name="x", tool_version="1", artifact_paths=[artifact])
    artifact.unlink()
    assert cache.get(k) is None  # missing file → cache miss


def test_skill_rag_index_and_search(tmp_path: Path):
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    (skills_dir / "captions.md").write_text(
        "# Kinetic Captions\n\nWord-by-word color highlights for TikTok and Reels.\n"
    )
    (skills_dir / "music.md").write_text(
        "# ACE-Step Music Generation\n\nGenerate full songs in 20 seconds.\n"
    )
    rag = SkillRAG(tmp_path / "skills.db")
    n = rag.index_directory(skills_dir)
    assert n == 2
    assert rag.count() == 2

    hits = rag.search("kinetic captions tiktok", top_k=2)
    assert hits, "expected at least one hit"
    assert hits[0].title.lower().startswith("kinetic captions")
