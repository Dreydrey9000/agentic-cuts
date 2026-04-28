"""Agentic Cuts kinetic caption preset library.

JSON preset files in this directory drive both the FFmpeg ASS subtitle pass
and the future Remotion component renderer. Names are kebab-case slugs.
"""

from pathlib import Path

CAPTIONS_DIR: Path = Path(__file__).parent
