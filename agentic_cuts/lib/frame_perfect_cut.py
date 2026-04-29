"""frame_perfect_cut — keyframe-aware FFmpeg cuts.

OpenMontage cuts at requested timestamps and re-encodes everything,
which is slow + lossy. HN devs explicitly asked for keyframe-aligned cuts
(stream copy, no re-encode) when possible.

Plan:
1. Probe keyframes via `ffprobe -select_streams v:0 -show_frames -of json`
2. For each requested cut point, find the closest keyframe within tolerance.
3. If close enough → stream copy (fast, lossless). Otherwise → re-encode.
"""

from __future__ import annotations

import bisect
import json
import shutil
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


FFPROBE_TIMEOUT_SEC = 60
"""Hard timeout for keyframe probing. Long files cap here; the caller can override
by passing pre-computed keyframes."""

FFMPEG_TIMEOUT_SEC = 600
"""Hard timeout for the actual cut. 10 min covers most clip-factory cuts; pass
your own subprocess if you need longer."""


class CutStrategy(str, Enum):
    STREAM_COPY = "stream_copy"     # -c copy, byte-fast, lossless, keyframe-bounded.
    RE_ENCODE = "re_encode"         # exact-frame, slower, slight quality cost.


@dataclass(frozen=True)
class CutPlan:
    source: Path
    start_sec: float
    end_sec: float
    strategy: CutStrategy
    snap_start_sec: float
    """Actual start used after keyframe snap (==start_sec for re-encode)."""
    snap_end_sec: float
    snap_drift_start_sec: float
    snap_drift_end_sec: float
    rationale: str


class FFmpegMissingError(RuntimeError):
    """ffprobe / ffmpeg binaries not found on PATH."""


def _require_binary(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise FFmpegMissingError(f"{name} not found on PATH — install ffmpeg first")
    return path


def list_keyframes(source: Path | str, timeout_sec: float = FFPROBE_TIMEOUT_SEC) -> list[float]:
    """Return sorted list of keyframe timestamps (seconds) for the first video stream."""
    src = Path(source)
    ffprobe = _require_binary("ffprobe")
    out = subprocess.run(
        [
            ffprobe,
            "-loglevel", "error",
            "-select_streams", "v:0",
            "-skip_frame", "nokey",
            "-show_frames",
            "-show_entries", "frame=pts_time",
            "-of", "json",
            str(src),
        ],
        capture_output=True,
        text=True,
        check=True,
        timeout=timeout_sec,
    )
    data = json.loads(out.stdout or "{}")
    frames = data.get("frames", []) or []
    times = sorted(float(f["pts_time"]) for f in frames if "pts_time" in f)
    return times


def plan_cut(
    source: Path | str,
    start_sec: float,
    end_sec: float,
    *,
    snap_tolerance_sec: float = 0.30,
    force_re_encode: bool = False,
    keyframes: list[float] | None = None,
) -> CutPlan:
    """Decide whether this cut can stream-copy or has to re-encode.

    Pass `keyframes` to skip ffprobe (handy for tests + bulk planning).
    """
    src = Path(source)
    if end_sec <= start_sec:
        raise ValueError("end_sec must be greater than start_sec")
    kf = keyframes if keyframes is not None else list_keyframes(src)
    if force_re_encode or not kf:
        return CutPlan(
            source=src,
            start_sec=start_sec,
            end_sec=end_sec,
            strategy=CutStrategy.RE_ENCODE,
            snap_start_sec=start_sec,
            snap_end_sec=end_sec,
            snap_drift_start_sec=0.0,
            snap_drift_end_sec=0.0,
            rationale="forced re-encode" if force_re_encode else "no keyframes detected",
        )

    snap_start = _nearest(kf, start_sec)
    snap_end = _nearest(kf, end_sec)
    drift_start = abs(snap_start - start_sec)
    drift_end = abs(snap_end - end_sec)

    if drift_start <= snap_tolerance_sec and drift_end <= snap_tolerance_sec:
        return CutPlan(
            source=src,
            start_sec=start_sec,
            end_sec=end_sec,
            strategy=CutStrategy.STREAM_COPY,
            snap_start_sec=snap_start,
            snap_end_sec=snap_end,
            snap_drift_start_sec=drift_start,
            snap_drift_end_sec=drift_end,
            rationale=(
                f"stream-copy: snapped within {snap_tolerance_sec:.2f}s "
                f"(drift {drift_start:.3f}s / {drift_end:.3f}s)"
            ),
        )

    return CutPlan(
        source=src,
        start_sec=start_sec,
        end_sec=end_sec,
        strategy=CutStrategy.RE_ENCODE,
        snap_start_sec=start_sec,
        snap_end_sec=end_sec,
        snap_drift_start_sec=drift_start,
        snap_drift_end_sec=drift_end,
        rationale=(
            f"re-encode: nearest keyframe drift "
            f"{drift_start:.3f}s / {drift_end:.3f}s exceeds tolerance "
            f"{snap_tolerance_sec:.2f}s"
        ),
    )


def keyframe_aligned_cut(
    plan: CutPlan,
    output: Path | str,
    *,
    timeout_sec: float = FFMPEG_TIMEOUT_SEC,
) -> Path:
    """Execute a CutPlan via FFmpeg. Returns the output path on success.

    Raises subprocess.TimeoutExpired if FFmpeg exceeds `timeout_sec`. The default
    (10 minutes) handles clip-factory ranges; override for hour-long renders.
    """
    ffmpeg = _require_binary("ffmpeg")
    out = Path(output)
    out.parent.mkdir(parents=True, exist_ok=True)
    if plan.strategy == CutStrategy.STREAM_COPY:
        cmd = [
            ffmpeg, "-y", "-loglevel", "error",
            "-ss", f"{plan.snap_start_sec:.6f}",
            "-to", f"{plan.snap_end_sec:.6f}",
            "-i", str(plan.source),
            "-c", "copy",
            "-avoid_negative_ts", "make_zero",
            str(out),
        ]
    else:
        cmd = [
            ffmpeg, "-y", "-loglevel", "error",
            "-i", str(plan.source),
            "-ss", f"{plan.start_sec:.6f}",
            "-to", f"{plan.end_sec:.6f}",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
            "-c:a", "aac", "-b:a", "192k",
            str(out),
        ]
    subprocess.run(cmd, check=True, timeout=timeout_sec)
    return out


def _nearest(sorted_floats: list[float], target: float) -> float:
    """Return the value in `sorted_floats` closest to `target`. List must be sorted."""
    if not sorted_floats:
        raise ValueError("sorted_floats empty")
    idx = bisect.bisect_left(sorted_floats, target)
    candidates: list[float] = []
    if idx < len(sorted_floats):
        candidates.append(sorted_floats[idx])
    if idx > 0:
        candidates.append(sorted_floats[idx - 1])
    return min(candidates, key=lambda x: abs(x - target))
