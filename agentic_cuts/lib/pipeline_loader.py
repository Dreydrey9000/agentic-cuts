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


def load_manifest(
    path: Path | str,
    *,
    validate_referenced_files: bool = False,
    repo_root: Path | str | None = None,
) -> PipelineManifest:
    """Load and validate one YAML manifest into a PipelineManifest object.

    `validate_referenced_files=True` checks that every stage's `director_skill`
    path actually exists on disk relative to `repo_root` (defaults to the
    parent-of-parent of the manifest file). Catches typos before a pipeline
    blows up mid-execution.
    """
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
        manifest = PipelineManifest.model_validate(raw)
    except ValidationError as exc:
        raise PipelineLoadError(f"validation failed for {p}:\n{exc}") from exc

    if validate_referenced_files:
        root = (
            Path(repo_root).expanduser().resolve()
            if repo_root is not None
            else p.parent.parent.parent  # agentic_cuts/pipelines/x.yaml -> repo root
        )
        missing: list[str] = []
        for stage in manifest.stages:
            ref = (root / stage.director_skill).resolve()
            if not ref.exists():
                missing.append(f"  {stage.name} -> {stage.director_skill}")
        if missing:
            joined = "\n".join(missing)
            raise PipelineLoadError(
                f"{p.name}: missing director_skill files:\n{joined}\n"
                f"(searched relative to {root})"
            )
    return manifest


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
