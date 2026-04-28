"""BaseTool contract + tool_registry behavior."""

from __future__ import annotations

from agentic_cuts import (
    BaseTool,
    Capability,
    Tier,
    ToolRegistry,
    ToolResult,
    select_provider,
)


class DummyTTS(BaseTool):
    name = "dummy_tts"
    capability = Capability.TTS
    provider = "dummy"
    tier = Tier.FREE
    supports = {"languages": ["en", "es"], "seed": True}
    cost_per_unit_usd = 0.0

    def execute(self, params):
        return ToolResult(
            success=True,
            data={"audio_path": "/tmp/fake.wav"},
            seed=params.get("seed"),
            cost_usd=0.0,
        )


class PaidTTS(BaseTool):
    name = "paid_tts"
    capability = Capability.TTS
    provider = "elevenlabs_lookalike"
    tier = Tier.PAID
    supports = {"languages": ["en"], "voice_clone": True, "structured_output": True}
    cost_per_unit_usd = 0.30

    def execute(self, params):
        return ToolResult(success=True, data={}, cost_usd=0.30)


def test_tool_result_round_trip():
    r = ToolResult(success=True, data={"k": 1}, cost_usd=0.5, seed=42)
    dumped = r.model_dump()
    again = ToolResult.model_validate(dumped)
    assert again.seed == 42
    assert again.data == {"k": 1}
    assert again.cost_usd == 0.5


def test_registry_register_and_lookup():
    reg = ToolRegistry()
    a, b = DummyTTS(), PaidTTS()
    reg.register(a)
    reg.register(b)
    assert reg.get("dummy_tts") is a
    assert reg.get("paid_tts") is b
    assert len(reg) == 2
    assert reg.by_capability(Capability.TTS) == [a, b] or reg.by_capability("tts") == [a, b]


def test_selector_prefers_free_seeded_when_quality_is_close():
    """Default weights — free + seed (high cost_efficiency + continuity) beats paid."""
    candidates = [DummyTTS(), PaidTTS()]
    winner, cards = select_provider(candidates, {"language": "en", "duration_sec": 10})
    assert winner is not None
    assert len(cards) == 2
    assert winner.name == "dummy_tts"


def test_selector_can_be_re_weighted_to_favor_quality():
    """Override weights to show paid wins when quality dominates the formula."""
    from agentic_cuts import Selector

    quality_first = {
        "task_fit": 1.0,
        "output_quality": 4.0,
        "reliability": 1.0,
        "control": 1.0,
        "cost_efficiency": 0.1,  # tiny weight on cost
        "latency": 0.5,
        "continuity": 0.5,
    }
    candidates = [DummyTTS(), PaidTTS()]
    winner, _ = Selector(quality_first).pick(candidates, {"language": "en"})
    assert winner is not None
    assert winner.name == "paid_tts"


def test_selector_filters_unsupported_language():
    """If a tool can't do the requested language, it scores 0 on task_fit and is excluded."""

    class EnglishOnly(BaseTool):
        name = "english_only"
        capability = Capability.TTS
        provider = "x"
        tier = Tier.FREE
        supports = {"languages": ["en"]}

        def execute(self, params):
            return ToolResult(success=True)

        def supports_request(self, params):
            return params.get("language") == "en"

    candidates = [EnglishOnly()]
    winner, _ = select_provider(candidates, {"language": "ja"})
    assert winner is None  # no candidate passes task_fit


def test_base_tool_run_helper_catches_exceptions():
    class BrokenTool(BaseTool):
        name = "broken"
        capability = Capability.TTS
        provider = "broken"
        tier = Tier.FREE

        def execute(self, params):
            return self._run(params)

        def _execute_impl(self, params):
            raise RuntimeError("boom")

    result = BrokenTool().execute({})
    assert result.success is False
    assert "RuntimeError: boom" in (result.error or "")
