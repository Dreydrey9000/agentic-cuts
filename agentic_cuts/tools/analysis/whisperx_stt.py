"""WhisperX STT — free, local, word-level timestamps. The 2026 SOTA pairing
when combined with pyannote Community-1 for diarization.

Source: https://github.com/m-bain/whisperX  (BSD-2 license, fully local)

Why this matters for Agentic Cuts beyond plain transcription:
- **Editing assembly** — word-level start/end ms is the GROUND TRUTH for cuts.
  The `cut` stage in clip-factory snaps every cut to a word boundary using
  these timestamps. Without WhisperX, cuts split mid-word and audio sounds
  garbled at the seams.
- **Caption rendering** — every caption preset's word-by-word emphasis logic
  reads directly from `word_segments` produced here.
- **Speaker swap detection** — pair with pyannote diarization; the resulting
  speaker_map drives the talking-head + podcast-repurpose pipelines.

Pip install:
    pip install whisperx

If the `whisperx` package isn't importable, supports_request returns False.
Defaults to `large-v3` model on whatever device is available (CUDA → MPS → CPU).
"""

from __future__ import annotations

import importlib
import uuid
from pathlib import Path
from typing import Any, ClassVar

from agentic_cuts.lib.base_tool import BaseTool, Capability, Tier, ToolResult


class WhisperXSTT(BaseTool):
    name: ClassVar[str] = "whisperx_stt"
    version: ClassVar[str] = "0.1.0"
    capability: ClassVar[Capability] = Capability.STT
    provider: ClassVar[str] = "whisperx"
    tier: ClassVar[Tier] = Tier.FREE
    supports: ClassVar[dict[str, Any]] = {
        "languages": ["en", "es", "fr", "de", "it", "pt", "ja", "zh", "ko", "ru", "ar", "nl"],
        "word_timestamps": True,
        "editing_assembly": True,  # word-level timestamps drive cut/caption stages
        "deterministic": True,
        "seed": False,  # whisper is deterministic by audio + model
        "structured_output": True,
        "quality_hint": 9.0,
        "latency_hint": 6.0,
        "uptime_hint": 9.5,
        "model_version": "large-v3",
        "source": "https://github.com/m-bain/whisperX",
    }
    cost_per_unit_usd: ClassVar[float] = 0.0

    @staticmethod
    def _whisperx_available() -> bool:
        try:
            importlib.import_module("whisperx")
        except ImportError:
            return False
        return True

    def supports_request(self, params: dict[str, Any]) -> bool:
        return self._whisperx_available()

    def estimate_cost(self, params: dict[str, Any]) -> float:
        return 0.0

    def execute(self, params: dict[str, Any]) -> ToolResult:
        audio_path = params.get("audio_path")
        if not audio_path:
            return ToolResult(success=False, error="whisperx_stt: missing 'audio_path'")
        if not Path(audio_path).exists():
            return ToolResult(success=False, error=f"whisperx_stt: file not found: {audio_path}")
        if not self._whisperx_available():
            return ToolResult(
                success=False,
                error="whisperx not installed (pip install whisperx)",
            )
        try:
            whisperx = importlib.import_module("whisperx")
            device = params.get("device") or "cpu"
            compute_type = params.get("compute_type") or ("float16" if device == "cuda" else "int8")
            model_size = params.get("model_size") or "large-v3"
            model = whisperx.load_model(model_size, device, compute_type=compute_type)
            audio = whisperx.load_audio(audio_path)
            result = model.transcribe(audio, batch_size=params.get("batch_size", 16))
            # Word-level alignment
            align_model, metadata = whisperx.load_align_model(
                language_code=result["language"], device=device
            )
            aligned = whisperx.align(
                result["segments"], align_model, metadata, audio, device,
                return_char_alignments=False,
            )
        except Exception as exc:  # noqa: BLE001
            return ToolResult(success=False, error=f"whisperx_stt: {type(exc).__name__}: {exc}")

        out_dir = Path(params.get("out_dir", "/tmp/agentic-cuts-whisperx")).expanduser()
        out_dir.mkdir(parents=True, exist_ok=True)
        transcript_path = out_dir / f"transcript-{uuid.uuid4().hex[:10]}.json"
        import json
        transcript_path.write_text(
            json.dumps({
                "language": result.get("language"),
                "segments": aligned.get("segments", []),
                "word_segments": aligned.get("word_segments", []),
            }, indent=2),
            encoding="utf-8",
        )
        return ToolResult(
            success=True,
            data={
                "transcript_path": str(transcript_path),
                "language": result.get("language"),
                "n_words": len(aligned.get("word_segments", [])),
            },
            artifacts=[str(transcript_path)],
            cost_usd=0.0,
            decision_log={
                "model": model_size,
                "device": device,
                "compute_type": compute_type,
            },
        )
