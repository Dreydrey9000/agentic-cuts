"""Agentic Cuts provider tools.

Drop a `BaseTool` subclass anywhere under this package and the registry will
auto-discover it via pkgutil.walk_packages. Layout convention:

    tools/audio/         TTS, music gen, audio enhance
    tools/analysis/      STT, diarization, scene detect, video understanding
    tools/video/         video gen, cuts, compose, stitch
    tools/graphics/      image gen, diagrams, code snippets
    tools/source/        stock retrieval (Pexels, Pixabay, Unsplash, Archive.org)
    tools/music/         (alias for audio/music; reserved)

Every concrete tool MUST set: name, capability, provider, tier, supports.
supports_request() should return False when the tool's API key / binary is
not available so the selector skips it without raising.
"""
