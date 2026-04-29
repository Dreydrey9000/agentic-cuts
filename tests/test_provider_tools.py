"""Provider tool contracts.

Verifies every tool we ship:
1. Subclasses BaseTool with all required class-level fields.
2. supports_request returns False when its key/binary/package is absent
   (selector skips it gracefully).
3. execute() returns ToolResult.success=False with a clear error when keys
   are missing — never crashes the agent.
4. estimate_cost is non-negative and respects per-call params.
5. ToolRegistry.discover('agentic_cuts.tools') finds them all.
"""

from __future__ import annotations

import os

import pytest

from agentic_cuts import BaseTool, Capability, Tier, ToolRegistry, ToolResult


@pytest.fixture
def reg():
    r = ToolRegistry()
    r.discover("agentic_cuts.tools")
    return r


def test_discovery_finds_provider_tools(reg):
    assert len(reg) >= 12, f"expected ≥12 tools, registry has {len(reg)}: {[t.name for t in reg]}"
    expected = {
        # TTS
        "piper_tts",
        "kokoro_tts",
        "elevenlabs_tts",
        "f5_tts",
        # STT
        "whisperx_stt",
        # stock
        "pexels_stock",
        # video gen
        "fal_video",
        "replicate_video",
        # music
        "acestep_music",
        # avatar / lip-sync
        "sadtalker",
        "liveportrait",
        "higgsfield_speak",
    }
    actual = {t.name for t in reg}
    missing = expected - actual
    assert not missing, f"missing tools after discovery: {missing}"


def test_every_tool_has_required_class_fields(reg):
    for tool in reg:
        assert tool.name, f"{type(tool).__name__} missing name"
        assert isinstance(tool.capability, Capability)
        assert isinstance(tool.tier, Tier)
        assert tool.provider, f"{tool.name} missing provider"
        assert isinstance(tool.supports, dict), f"{tool.name} supports must be dict"
        assert tool.cost_per_unit_usd >= 0, f"{tool.name} negative cost"


def test_unavailable_tools_supports_request_false_when_missing_keys(reg, monkeypatch):
    """With no API keys / binaries / packages, supports_request must return False —
    the selector relies on this to skip them rather than crash."""
    # Strip every relevant env var.
    for var in ("ELEVENLABS_API_KEY", "FAL_KEY", "FAL_API_KEY",
                "REPLICATE_API_TOKEN", "REPLICATE_API_KEY", "PEXELS_API_KEY"):
        monkeypatch.delenv(var, raising=False)

    # Tools whose availability is purely env-var-driven:
    for name in ("elevenlabs_tts", "fal_video", "replicate_video", "pexels_stock"):
        tool = reg.get(name)
        assert tool is not None
        assert tool.supports_request({"language": "en", "prompt": "hi"}) is False, (
            f"{name}.supports_request should be False with no API key"
        )


def test_execute_with_missing_key_returns_clear_error_not_crash(reg, monkeypatch):
    for var in ("ELEVENLABS_API_KEY", "FAL_KEY", "FAL_API_KEY",
                "REPLICATE_API_TOKEN", "REPLICATE_API_KEY", "PEXELS_API_KEY"):
        monkeypatch.delenv(var, raising=False)

    for name, params in [
        ("elevenlabs_tts", {"text": "hi", "language": "en"}),
        ("fal_video", {"prompt": "a cat dancing"}),
        ("replicate_video", {"prompt": "a cat dancing"}),
        ("pexels_stock", {"query": "ocean waves"}),
    ]:
        tool = reg.get(name)
        result = tool.execute(params)
        assert isinstance(result, ToolResult)
        assert result.success is False
        assert "not set" in (result.error or "").lower() or "set" in (result.error or "").lower()


def test_estimate_cost_scales_with_text_length():
    el = ToolRegistry()
    el.discover("agentic_cuts.tools")
    tool = el.get("elevenlabs_tts")
    short = tool.estimate_cost({"text": "hello"})
    long = tool.estimate_cost({"text": "hello " * 100})
    assert long > short
    assert short >= 0


def test_local_tools_supports_request_reflects_binary_availability(reg):
    """Piper supports_request is False when binary is absent. Kokoro/WhisperX/ACE-Step
    follow same pattern via Python package import."""
    piper = reg.get("piper_tts")
    # Whatever `which piper` says — the test just verifies the tool agrees with the env.
    import shutil
    expected = shutil.which("piper") is not None
    assert piper.supports_request({"text": "hi", "language": "en"}) is expected
