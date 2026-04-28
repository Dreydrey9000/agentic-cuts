"""PipelineLoader — read + validate YAML manifests, return typed PipelineManifest."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from agentic_cuts.lib.pipeline_manifest import PipelineManifest

log = logging.getLogger(__name__)


class PipelineLoadError(RuntimeError):
    """Raised when a manifest fails to load or validate."""


def load_manifest(path: Path | str) -> PipelineManifest:
    """Load and validate one YAML manifest into a PipelineManifest object."""
    p = Path(path).expanduser().resolve()
    if not p.exists():
        raise PipelineLoadError(f"manifest not found: {p}")
    try:
        raw: Any = yaml.safe_load(p.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise PipelineLoadError(f"yaml parse error in {p}: {exc}") from exc
    if not isinstance(raw, dict):
        raise PipelineLoadError(f"{p}: top-level must be a mapping, got {type(raw).__name__}")
    try:
        return PipelineManifest.model_validate(raw)
    except ValidationError as exc:
        raise PipelineLoadError(f"validation failed for {p}:\n{exc}") from exc


def discover_pipelines(directory: Path | str) -> dict[str, PipelineManifest]:
    """Load every `*.yaml` under `directory` and return a name → manifest map."""
    d = Path(directory).expanduser().resolve()
    if not d.is_dir():
        raise PipelineLoadError(f"pipelines directory not found: {d}")
    out: dict[str, PipelineManifest] = {}
    for yaml_path in sorted(d.glob("*.yaml")):
        try:
            manifest = load_manifest(yaml_path)
        except PipelineLoadError as exc:
            log.warning("skipping %s: %s", yaml_path.name, exc)
            continue
        if manifest.name in out:
            log.warning(
                "duplicate pipeline name %r in %s — keeping earlier",
                manifest.name, yaml_path,
            )
            continue
        out[manifest.name] = manifest
    return out
