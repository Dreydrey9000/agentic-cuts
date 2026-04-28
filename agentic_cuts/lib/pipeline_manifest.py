"""PipelineManifest — Pydantic schema for the YAML files in `agentic_cuts/pipelines/`.

Manifests are declarative. They name stages, point at director skills, and
declare delivery promise defaults. The agent reads the manifest, then reads
the matching director skill for each stage, then calls tools.
"""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from agentic_cuts.lib.base_tool import Capability
from agentic_cuts.lib.cost_tracker import BudgetMode


class CheckpointPolicy(str, Enum):
    """How aggressively to ask for human approval at stage boundaries.

    GUIDED          — pause for approval at creative-decision stages only.
    MANUAL_ALL      — pause at every stage. The careful default for new pipelines.
    AUTO_NONCREATIVE — only pause at script + final review. Fastest.
    """

    GUIDED = "guided"
    MANUAL_ALL = "manual_all"
    AUTO_NONCREATIVE = "auto_noncreative"


class StageManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    director_skill: str
    """Path (relative to repo root) of the Markdown file that teaches the agent this stage."""
    capabilities_required: list[Capability] = Field(default_factory=list)
    artifacts_produced: list[str] = Field(default_factory=list)
    human_approval_default: bool = False
    review_focus: list[str] = Field(default_factory=list)
    """Things the reviewer skill should look at on this stage's output."""
    optional: bool = False
    """If True, the agent may skip this stage when params don't require it
    (e.g. captions stage in a no-captions render)."""


class ReviewConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reviewer_skill: str = "skills/meta/reviewer.md"
    max_rounds: int = 2


class BudgetConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    default_cap_usd: float = 1.50
    mode: BudgetMode = BudgetMode.CAP
    warn_at_pct: float = 0.80
    reserve_pct: float = 0.10


class CheckpointConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    policy: CheckpointPolicy = CheckpointPolicy.GUIDED


class DeliveryPromiseDefaults(BaseModel):
    """Default delivery shape for this pipeline. Overridden per-run by user prompt."""

    model_config = ConfigDict(extra="forbid")

    target_aspect: Literal["16:9", "9:16", "1:1", "4:5"]
    requires_motion: bool = True
    requires_audio: bool = True
    requires_captions: bool = False
    requires_narration: bool = False
    requires_music: bool = False
    duration_tolerance_sec: float = 2.0


class PipelineManifest(BaseModel):
    """One pipeline. Maps to one YAML file in `agentic_cuts/pipelines/<name>.yaml`."""

    model_config = ConfigDict(extra="forbid")

    name: str
    version: str
    description: str
    type: Literal["footage_based", "ai_generated", "hybrid", "audio_first", "test"]
    stages: list[StageManifest]
    review: ReviewConfig = Field(default_factory=ReviewConfig)
    budget: BudgetConfig = Field(default_factory=BudgetConfig)
    checkpoint: CheckpointConfig = Field(default_factory=CheckpointConfig)
    delivery_promise: DeliveryPromiseDefaults
    playbooks: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)

    @field_validator("stages")
    @classmethod
    def _stages_non_empty_with_unique_names(cls, v: list[StageManifest]) -> list[StageManifest]:
        if not v:
            raise ValueError("a pipeline must have at least one stage")
        seen: set[str] = set()
        for s in v:
            if s.name in seen:
                raise ValueError(f"duplicate stage name: {s.name!r}")
            seen.add(s.name)
        return v

    def stage(self, name: str) -> StageManifest:
        for s in self.stages:
            if s.name == name:
                return s
        raise KeyError(f"stage {name!r} not found in pipeline {self.name!r}")

    def stage_index(self, name: str) -> int:
        for i, s in enumerate(self.stages):
            if s.name == name:
                return i
        raise KeyError(f"stage {name!r} not found in pipeline {self.name!r}")

    def stages_after(self, name: str) -> list[StageManifest]:
        idx = self.stage_index(name)
        return self.stages[idx + 1 :]
