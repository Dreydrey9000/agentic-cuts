"""BrandKit schema + loader."""

from __future__ import annotations

from pathlib import Path

import pytest

from agentic_cuts.lib.brand_kit import BrandKit, BrandKitLoadError, load_brand_kit


def test_example_brand_kit_validates():
    repo_root = Path(__file__).resolve().parents[1]
    bk = load_brand_kit(repo_root / "brand-kit.example.yaml")
    assert isinstance(bk, BrandKit)
    assert bk.tenant_id == "example-brand"
    assert bk.no_emojis is True
    assert bk.color("primary").hex == "#ffd200"


def test_minimal_valid_brand_kit(tmp_path: Path):
    yaml_text = """
tenant_id: minimal
display_name: Minimal
palette:
  - {name: primary, hex: '#ffd200'}
primary_typography:
  family: Inter
voice:
  primary_voice: kokoro/af_bella
"""
    p = tmp_path / "brand-kit.yaml"
    p.write_text(yaml_text)
    bk = load_brand_kit(p)
    assert bk.captions.default_preset == "podcast-clean"  # default
    assert bk.no_emojis is True  # default


def test_invalid_hex_raises(tmp_path: Path):
    yaml_text = """
tenant_id: bad
display_name: Bad
palette:
  - {name: primary, hex: 'notahex'}
primary_typography: {family: Inter}
voice: {primary_voice: x}
"""
    p = tmp_path / "bad.yaml"
    p.write_text(yaml_text)
    with pytest.raises(BrandKitLoadError):
        load_brand_kit(p)


def test_duplicate_color_names_raise(tmp_path: Path):
    yaml_text = """
tenant_id: dup
display_name: Dup
palette:
  - {name: same, hex: '#ffffff'}
  - {name: same, hex: '#000000'}
primary_typography: {family: Inter}
voice: {primary_voice: x}
"""
    p = tmp_path / "dup.yaml"
    p.write_text(yaml_text)
    with pytest.raises(BrandKitLoadError):
        load_brand_kit(p)


def test_empty_palette_raises(tmp_path: Path):
    yaml_text = """
tenant_id: empty
display_name: Empty
palette: []
primary_typography: {family: Inter}
voice: {primary_voice: x}
"""
    p = tmp_path / "empty.yaml"
    p.write_text(yaml_text)
    with pytest.raises(BrandKitLoadError):
        load_brand_kit(p)


def test_extra_field_rejected(tmp_path: Path):
    yaml_text = """
tenant_id: x
display_name: X
unknown_field: yes
palette:
  - {name: primary, hex: '#ffffff'}
primary_typography: {family: Inter}
voice: {primary_voice: x}
"""
    p = tmp_path / "extra.yaml"
    p.write_text(yaml_text)
    with pytest.raises(BrandKitLoadError):
        load_brand_kit(p)


def test_missing_file_raises():
    with pytest.raises(BrandKitLoadError):
        load_brand_kit("/tmp/does-not-exist-agentic-cuts-test.yaml")


def test_color_lookup_helper():
    repo_root = Path(__file__).resolve().parents[1]
    bk = load_brand_kit(repo_root / "brand-kit.example.yaml")
    assert bk.color("ink").hex == "#0c0c0c"
    with pytest.raises(KeyError):
        bk.color("nonexistent")
