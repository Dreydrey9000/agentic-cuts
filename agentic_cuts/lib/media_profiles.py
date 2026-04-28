"""MediaProfile — platform render presets.

Drey's hosting rule applies here too: pick the profile that matches the
target distribution channel, not the most general one. YouTube ≠ TikTok ≠
Reels even when they all happen to be 1080p somewhere on the resolution chart.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MediaProfile:
    name: str
    width: int
    height: int
    fps: int
    codec: str
    bitrate: str
    audio_codec: str
    audio_bitrate: str
    container: str
    target_aspect: str
    safe_zone_top_pct: float
    """Top portion of frame guaranteed to NOT be covered by platform UI. Captions go here."""
    safe_zone_bottom_pct: float
    """Bottom portion frequently covered by platform UI. Avoid caption placement here."""
    notes: str = ""

    @property
    def resolution(self) -> str:
        return f"{self.width}x{self.height}"

    @property
    def aspect(self) -> tuple[int, int]:
        return self.width, self.height

    def ffmpeg_args(self) -> list[str]:
        """Encode args for FFmpeg subprocess. Strict + portable defaults."""
        return [
            "-c:v", self.codec,
            "-b:v", self.bitrate,
            "-r", str(self.fps),
            "-vf", f"scale={self.width}:{self.height}:flags=lanczos,setsar=1",
            "-c:a", self.audio_codec,
            "-b:a", self.audio_bitrate,
            "-movflags", "+faststart",
            "-pix_fmt", "yuv420p",
        ]


PROFILES: dict[str, MediaProfile] = {
    "youtube": MediaProfile(
        name="youtube",
        width=1920, height=1080, fps=30,
        codec="libx264", bitrate="8M",
        audio_codec="aac", audio_bitrate="192k",
        container="mp4", target_aspect="16:9",
        safe_zone_top_pct=0.05, safe_zone_bottom_pct=0.10,
        notes="Standard horizontal landing.",
    ),
    "youtube_4k": MediaProfile(
        name="youtube_4k",
        width=3840, height=2160, fps=30,
        codec="libx264", bitrate="35M",
        audio_codec="aac", audio_bitrate="256k",
        container="mp4", target_aspect="16:9",
        safe_zone_top_pct=0.05, safe_zone_bottom_pct=0.10,
        notes="4K upload. CRF tuned for quality, not size.",
    ),
    "shorts": MediaProfile(
        name="shorts",
        width=1080, height=1920, fps=30,
        codec="libx264", bitrate="6M",
        audio_codec="aac", audio_bitrate="192k",
        container="mp4", target_aspect="9:16",
        safe_zone_top_pct=0.10, safe_zone_bottom_pct=0.20,
        notes="YouTube Shorts. UI eats top 10% + bottom 20%.",
    ),
    "tiktok": MediaProfile(
        name="tiktok",
        width=1080, height=1920, fps=30,
        codec="libx264", bitrate="6M",
        audio_codec="aac", audio_bitrate="192k",
        container="mp4", target_aspect="9:16",
        safe_zone_top_pct=0.12, safe_zone_bottom_pct=0.22,
        notes="TikTok UI bottom-heavy. Captions belong above 65% height.",
    ),
    "reels": MediaProfile(
        name="reels",
        width=1080, height=1920, fps=30,
        codec="libx264", bitrate="6M",
        audio_codec="aac", audio_bitrate="192k",
        container="mp4", target_aspect="9:16",
        safe_zone_top_pct=0.10, safe_zone_bottom_pct=0.20,
        notes="Instagram Reels. Comments+shares clip bottom corners.",
    ),
    "square": MediaProfile(
        name="square",
        width=1080, height=1080, fps=30,
        codec="libx264", bitrate="5M",
        audio_codec="aac", audio_bitrate="192k",
        container="mp4", target_aspect="1:1",
        safe_zone_top_pct=0.05, safe_zone_bottom_pct=0.08,
        notes="Square feed posts.",
    ),
    "x_video": MediaProfile(
        name="x_video",
        width=1920, height=1080, fps=30,
        codec="libx264", bitrate="5M",
        audio_codec="aac", audio_bitrate="160k",
        container="mp4", target_aspect="16:9",
        safe_zone_top_pct=0.05, safe_zone_bottom_pct=0.08,
        notes="X (formerly Twitter) inline video.",
    ),
}


def profile_for(target: str) -> MediaProfile:
    """Loose match — accepts 'tiktok', 'TikTok', 'tt', 'reel', 'reels', etc."""
    key = target.strip().lower().replace("-", "_")
    aliases = {
        "tt": "tiktok",
        "ig": "reels",
        "instagram": "reels",
        "reel": "reels",
        "short": "shorts",
        "yt": "youtube",
        "yt_4k": "youtube_4k",
        "4k": "youtube_4k",
        "twitter": "x_video",
        "x": "x_video",
        "1x1": "square",
    }
    key = aliases.get(key, key)
    if key not in PROFILES:
        raise KeyError(f"Unknown media profile {target!r}. Known: {sorted(PROFILES)}")
    return PROFILES[key]
