"""CaptionPreset — schema for the kinetic caption preset library.

Each preset is a JSON file in `agentic_cuts/captions/<preset>.json`. The
caption stage of any pipeline picks a preset (by name or via the selector),
and the preset spec drives both the FFmpeg ASS subtitle pass AND the future
Remotion component renderer.

Why JSON not YAML for these specs: they're consumed by both Python and the
TypeScript timeline UI. JSON is the lingua franca; YAML is for human-edited
top-level config (pipelines, brand-kits).
"""

from __future__ import annotations

import json
from enum import Enum
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator


class StyleFamily(str, Enum):
    KINETIC = "kinetic"           # Word-by-word with motion/color emphasis.
    ANIMATED_WORD = "animated_word"  # One word at a time, big, simple animation.
    SENTENCE = "sentence"         # 1-2 lines, static or fading.
    MINIMAL = "minimal"           # Small, bottom, documentary-style.
    QUOTE = "quote"               # Large block, centered, for callout moments.


class CaptionMotion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["none", "fade", "bounce", "pop", "slide", "scale_in", "typewriter"] = "none"
    duration_ms: int = Field(default=200, ge=0, le=2000)
    easing: Literal["linear", "ease", "ease_in", "ease_out", "ease_in_out", "spring"] = "ease_out"


class CaptionEmphasis(BaseModel):
    """How the active/emphasized word stands out from the rest."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["none", "color", "scale", "underline", "highlight_box", "color+scale"] = "none"
    color: str | None = None
    """Hex color when emphasis type involves color (e.g. '#ffd200' for yellow)."""
    scale_factor: float = Field(default=1.0, ge=1.0, le=2.0)
    box_color: str | None = None


class CaptionTypography(BaseModel):
    model_config = ConfigDict(extra="forbid")

    family: str
    weight: int = Field(default=700, ge=100, le=900)
    italic: bool = False
    text_transform: Literal["uppercase", "lowercase", "preserve", "sentence"] = "preserve"
    size_pct_of_height: float = Field(default=0.05, ge=0.02, le=0.15)
    """Font size as a fraction of frame height. 0.05 = 5% of 1920 = 96px."""
    line_height: float = Field(default=1.15, ge=0.8, le=2.0)
    letter_spacing_em: float = 0.0


class CaptionColors(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str = "#ffffff"
    background: str | None = None
    """Block background. None = transparent."""
    outline: str | None = "#000000"
    outline_width_px: float = 4.0
    shadow: str | None = "#00000080"
    shadow_offset_px: tuple[float, float] = (0.0, 4.0)


class CaptionPosition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    y_pct: float = Field(default=0.65, ge=0.0, le=1.0)
    """Vertical center of the caption block, as a fraction of frame height."""
    alignment: Literal["left", "center", "right"] = "center"
    max_width_pct: float = Field(default=0.85, ge=0.30, le=1.0)


class CaptionSafeZone(BaseModel):
    model_config = ConfigDict(extra="forbid")

    top_pct: float = Field(default=0.05, ge=0.0, le=0.30)
    bottom_pct: float = Field(default=0.10, ge=0.0, le=0.30)


class CaptionPreset(BaseModel):
    """One named caption preset. Loaded from JSON in `agentic_cuts/captions/`."""

    model_config = ConfigDict(extra="forbid")

    name: str
    display_name: str
    description: str
    style_family: StyleFamily
    typography: CaptionTypography
    colors: CaptionColors = Field(default_factory=CaptionColors)
    position: CaptionPosition = Field(default_factory=CaptionPosition)
    safe_zone: CaptionSafeZone = Field(default_factory=CaptionSafeZone)
    motion: CaptionMotion = Field(default_factory=CaptionMotion)
    emphasis: CaptionEmphasis = Field(default_factory=CaptionEmphasis)
    max_words_per_card: int = Field(default=5, ge=1, le=20)
    """1-3 = word-by-word feel; 5-10 = sentence-style; 10+ = block paragraphs."""
    tags: list[str] = Field(default_factory=list)
    preview_gif: str | None = None
    """Relative path to a preview GIF (when one is rendered)."""
    contains_emojis: bool = False
    """Brand kits with no_emojis=True will reject presets where this is True."""

    @field_validator("name")
    @classmethod
    def _name_is_slug(cls, v: str) -> str:
        if not v or not all(c.isalnum() or c in "-_" for c in v):
            raise ValueError(f"preset name must be a slug: {v!r}")
        return v


class CaptionPresetLoadError(RuntimeError):
    pass


def load_preset(path: Path | str) -> CaptionPreset:
    p = Path(path).expanduser().resolve()
    if not p.exists():
        raise CaptionPresetLoadError(f"preset not found: {p}")
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise CaptionPresetLoadError(f"json parse error in {p}: {exc}") from exc
    if not isinstance(raw, dict):
        raise CaptionPresetLoadError(f"{p}: top-level must be an object")
    try:
        return CaptionPreset.model_validate(raw)
    except ValidationError as exc:
        raise CaptionPresetLoadError(f"validation failed for {p}:\n{exc}") from exc


def discover_presets(directory: Path | str) -> dict[str, CaptionPreset]:
    d = Path(directory).expanduser().resolve()
    if not d.is_dir():
        raise CaptionPresetLoadError(f"presets dir not found: {d}")
    out: dict[str, CaptionPreset] = {}
    for f in sorted(d.glob("*.json")):
        try:
            preset = load_preset(f)
        except CaptionPresetLoadError:
            continue
        out[preset.name] = preset
    return out
