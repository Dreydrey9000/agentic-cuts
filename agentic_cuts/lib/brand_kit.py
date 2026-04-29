"""BrandKit — the schema each tenant of Agentic Cuts ships with their fork.

Drey's tenant has Drey's voice + palette. 1BB's tenant has 1BB's. VE's has VE's.
Every render reads `brand-kit.yaml`, applies typography + color + voice + intro/outro
defaults, and overrides any pipeline manifest's defaults.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator


class BrandColor(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    hex: str

    @field_validator("hex")
    @classmethod
    def _valid_hex(cls, v: str) -> str:
        v = v.strip()
        if not v.startswith("#"):
            v = f"#{v}"
        s = v[1:]
        if len(s) not in (3, 6, 8) or not all(c in "0123456789aAbBcCdDeEfF" for c in s):
            raise ValueError(f"invalid hex color: {v!r}")
        return v.lower()


class BrandTypography(BaseModel):
    model_config = ConfigDict(extra="forbid")

    family: str
    weight: int = Field(default=700, ge=100, le=900)
    italic: bool = False
    fallback_stack: list[str] = Field(default_factory=lambda: ["sans-serif"])


class BrandLogo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    light_path: str | None = None
    """Logo for use over dark backgrounds."""
    dark_path: str | None = None
    """Logo for use over light backgrounds."""
    placement: Literal["top_left", "top_right", "bottom_left", "bottom_right", "none"] = "bottom_right"
    margin_pct: float = 0.04


class BrandVoice(BaseModel):
    """Defaults applied when a pipeline asks for narration or TTS."""

    model_config = ConfigDict(extra="forbid")

    primary_voice: str
    """Voice ID — e.g. 'kokoro/af_bella', 'elevenlabs/<id>', 'piper/en_US-libritts'."""
    fallback_voice: str | None = None
    speaking_rate: float = Field(default=1.0, ge=0.5, le=2.0)
    pitch: float = Field(default=0.0, ge=-12.0, le=12.0)
    style_hint: str | None = None
    """Free-form style direction (e.g. 'warm, conversational, slight sarcasm')."""


class BrandCaptionDefaults(BaseModel):
    """Captioning defaults — points to a preset name in `agentic_cuts/captions/`."""

    model_config = ConfigDict(extra="forbid")

    default_preset: str = "podcast-clean"
    accent_color_override: str | None = None
    """Optional hex; overrides the preset's accent color with the tenant's brand accent."""
    safe_zone_top_pct: float = Field(default=0.10, ge=0.0, le=0.30)
    safe_zone_bottom_pct: float = Field(default=0.20, ge=0.0, le=0.30)


class BrandKit(BaseModel):
    """The full tenant brand spec. Lives at the tenant repo root as `brand-kit.yaml`."""

    model_config = ConfigDict(extra="forbid")

    tenant_id: str
    """Slug — must match the GitHub repo suffix (e.g. 'drey' for `agentic-cuts-drey`)."""
    display_name: str
    description: str = ""
    palette: list[BrandColor]
    primary_typography: BrandTypography
    secondary_typography: BrandTypography | None = None
    logo: BrandLogo = Field(default_factory=BrandLogo)
    voice: BrandVoice
    captions: BrandCaptionDefaults = Field(default_factory=BrandCaptionDefaults)
    default_pipelines: list[str] = Field(default_factory=list)
    """Pipelines this tenant uses by default. Empty = all 5 launch pipelines available."""
    hashtags: list[str] = Field(default_factory=list)
    """Hashtags to consider on auto-publish stages. Drey's rule: never use them, but
    other tenants may want to."""
    no_emojis: bool = True
    """Hard rule for Drey-aligned tenants. When True, blocks any caption preset that
    inserts emojis."""

    @field_validator("palette")
    @classmethod
    def _palette_non_empty(cls, v: list[BrandColor]) -> list[BrandColor]:
        if not v:
            raise ValueError("palette must contain at least one color")
        names = [c.name for c in v]
        if len(set(names)) != len(names):
            raise ValueError(f"duplicate color names in palette: {names}")
        return v

    def color(self, name: str) -> BrandColor:
        for c in self.palette:
            if c.name == name:
                return c
        raise KeyError(f"color {name!r} not in palette of {self.tenant_id!r}")


class BrandKitLoadError(RuntimeError):
    """Raised when brand-kit.yaml is missing, malformed, or fails validation."""


def load_brand_kit(path: Path | str) -> BrandKit:
    p = Path(path).expanduser().resolve()
    if not p.exists():
        raise BrandKitLoadError(f"brand-kit not found: {p}")
    try:
        raw = yaml.safe_load(p.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise BrandKitLoadError(f"yaml parse error in {p}: {exc}") from exc
    if not isinstance(raw, dict):
        raise BrandKitLoadError(f"{p}: top-level must be a mapping, got {type(raw).__name__}")
    try:
        return BrandKit.model_validate(raw)
    except ValidationError as exc:
        raise BrandKitLoadError(f"validation failed for {p}:\n{exc}") from exc
