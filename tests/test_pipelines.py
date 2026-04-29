"""Pipeline manifest schema + loader."""

from __future__ import annotations

from pathlib import Path

import pytest

from agentic_cuts import (
    PipelineLoadError,
    PipelineManifest,
    discover_pipelines,
    load_manifest,
)
from agentic_cuts.pipelines import PIPELINES_DIR


EXPECTED_NAMES = {
    "clip-factory",
    "talking-head",
    "documentary-montage",
    "podcast-repurpose",
    "animated-explainer",
}


def test_all_5_launch_pipelines_load():
    pipelines = discover_pipelines(PIPELINES_DIR)
    assert set(pipelines) == EXPECTED_NAMES


@pytest.mark.parametrize("name", sorted(EXPECTED_NAMES))
def test_pipeline_validates(name: str):
    p = load_manifest(PIPELINES_DIR / f"{name}.yaml")
    assert isinstance(p, PipelineManifest)
    assert p.name == name
    assert p.stages, f"{name} has no stages"
    assert p.delivery_promise.target_aspect in {"16:9", "9:16", "1:1", "4:5"}
    # Every stage must have a director skill path.
    for s in p.stages:
        assert s.director_skill, f"{name}.{s.name} missing director_skill"
        assert s.director_skill.endswith(".md"), (
            f"{name}.{s.name} director_skill must point to a .md file"
        )


def test_clip_factory_is_drey_daily_driver():
    p = load_manifest(PIPELINES_DIR / "clip-factory.yaml")
    assert "daily_driver" in p.tags or "viral_editz" in p.tags
    assert p.delivery_promise.target_aspect == "9:16"
    assert p.delivery_promise.requires_captions
    assert p.budget.mode.value == "cap"


def test_zero_key_pipeline_is_animated_explainer():
    p = load_manifest(PIPELINES_DIR / "animated-explainer.yaml")
    assert "zero_key" in p.tags or "free_path_friendly" in p.tags


def test_invalid_yaml_raises_pipeline_load_error(tmp_path: Path):
    bad = tmp_path / "broken.yaml"
    bad.write_text("name: x\n  invalid: ::: yaml")
    with pytest.raises(PipelineLoadError):
        load_manifest(bad)


def test_missing_required_field_raises(tmp_path: Path):
    bad = tmp_path / "incomplete.yaml"
    bad.write_text(
        "name: incomplete\n"
        "version: '0.1'\n"
        "description: 'missing type and stages'\n"
    )
    with pytest.raises(PipelineLoadError):
        load_manifest(bad)


def test_duplicate_stage_names_raise(tmp_path: Path):
    bad = tmp_path / "dup_stages.yaml"
    bad.write_text(
        """
name: dup
version: '0.1'
description: 'duplicate stage names'
type: test
delivery_promise:
  target_aspect: '16:9'
stages:
  - name: a
    director_skill: skills/a.md
  - name: a
    director_skill: skills/a.md
"""
    )
    with pytest.raises(PipelineLoadError):
        load_manifest(bad)


def test_stage_lookup_helpers():
    p = load_manifest(PIPELINES_DIR / "clip-factory.yaml")
    first = p.stages[0]
    assert p.stage(first.name) is first
    assert p.stage_index(first.name) == 0
    after_first = p.stages_after(first.name)
    assert len(after_first) == len(p.stages) - 1
    with pytest.raises(KeyError):
        p.stage("does-not-exist")


def test_all_5_launch_pipelines_pass_strict_validation():
    """All 5 real pipelines now have director skills on disk (real or placeholder)."""
    repo_root = Path(__file__).resolve().parents[1]
    for name in EXPECTED_NAMES:
        m = load_manifest(
            PIPELINES_DIR / f"{name}.yaml",
            validate_referenced_files=True,
            repo_root=repo_root,
        )
        assert m.name == name


def test_validate_referenced_files_catches_missing_skills(tmp_path: Path):
    """Council ask (Ousterhout): catch typos in director_skill paths before mid-pipeline blow-ups."""
    bad = tmp_path / "broken.yaml"
    bad.write_text(
        """
name: broken
version: '0.1'
description: 'references a director_skill file that does not exist'
type: test
delivery_promise:
  target_aspect: '16:9'
stages:
  - name: phantom
    director_skill: skills/this/does/not/exist.md
"""
    )
    # Without the flag, loads fine.
    m = load_manifest(bad)
    assert m.name == "broken"
    # With the flag pointed at tmp_path (which has no skills/), it raises.
    with pytest.raises(PipelineLoadError) as exc_info:
        load_manifest(bad, validate_referenced_files=True, repo_root=tmp_path)
    assert "missing director_skill files" in str(exc_info.value)
