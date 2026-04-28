"""Caption preset library — schema + 20 launch presets."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agentic_cuts.captions import CAPTIONS_DIR
from agentic_cuts.lib.caption_preset import (
    CaptionPreset,
    CaptionPresetLoadError,
    StyleFamily,
    discover_presets,
    load_preset,
)


EXPECTED_PRESETS = {
    "tiktok-yellow-bold",
    "hormozi-style",
    "mr-beast-pop",
    "podcast-clean",
    "cinematic-fade",
    "minimal-white",
    "kinetic-bounce",
    "quote-card",
    "ig-reel-classic",
    "youtube-shorts-clean",
    "documentary-subtitle",
    "meme-impact",
    "educational-clear",
    "news-ticker",
    "vlog-handwritten",
    "dark-mode-neon",
    "comedy-zoom",
    "luxury-serif",
    "courtroom-mono",
    "tiktok-emoji-burst",
}


def test_20_presets_present():
    presets = discover_presets(CAPTIONS_DIR)
    assert set(presets) == EXPECTED_PRESETS, (
        f"missing: {EXPECTED_PRESETS - set(presets)}; "
        f"extra: {set(presets) - EXPECTED_PRESETS}"
    )


@pytest.mark.parametrize("preset_name", sorted(EXPECTED_PRESETS))
def test_each_preset_validates(preset_name: str):
    p = load_preset(CAPTIONS_DIR / f"{preset_name}.json")
    assert isinstance(p, CaptionPreset)
    assert p.name == preset_name
    assert p.display_name
    assert p.description
    assert isinstance(p.style_family, StyleFamily)
    # Safe-zone constraints are sane
    assert 0.0 <= p.safe_zone.top_pct <= 0.30
    assert 0.0 <= p.safe_zone.bottom_pct <= 0.30
    # Position fits inside the frame
    assert 0.0 <= p.position.y_pct <= 1.0


def test_only_one_preset_uses_emojis():
    """no_emojis is the default rule. Tenants opt into emoji-style explicitly."""
    presets = discover_presets(CAPTIONS_DIR)
    emoji_presets = [p.name for p in presets.values() if p.contains_emojis]
    assert emoji_presets == ["tiktok-emoji-burst"]


def test_hormozi_style_uses_yellow_emphasis():
    p = load_preset(CAPTIONS_DIR / "hormozi-style.json")
    assert p.emphasis.color == "#ffd200"
    assert p.emphasis.type == "color"


def test_minimal_white_has_no_motion():
    p = load_preset(CAPTIONS_DIR / "minimal-white.json")
    assert p.motion.type == "none"


def test_invalid_json_raises(tmp_path: Path):
    bad = tmp_path / "bad.json"
    bad.write_text("not json {")
    with pytest.raises(CaptionPresetLoadError):
        load_preset(bad)


def test_missing_required_fields_raise(tmp_path: Path):
    bad = tmp_path / "incomplete.json"
    bad.write_text(json.dumps({"name": "incomplete", "display_name": "X"}))
    with pytest.raises(CaptionPresetLoadError):
        load_preset(bad)


def test_extra_field_rejected(tmp_path: Path):
    bad = tmp_path / "extra.json"
    bad.write_text(json.dumps({
        "name": "x",
        "display_name": "X",
        "description": "x",
        "style_family": "minimal",
        "typography": {"family": "Inter"},
        "extra_unknown_field": "boom",
    }))
    with pytest.raises(CaptionPresetLoadError):
        load_preset(bad)


def test_style_family_coverage():
    """Make sure the 20 presets cover all 5 style families."""
    presets = discover_presets(CAPTIONS_DIR)
    families = {p.style_family for p in presets.values()}
    assert families == set(StyleFamily)
