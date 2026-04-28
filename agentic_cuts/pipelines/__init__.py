"""Agentic Cuts launch pipelines.

Each YAML file in this directory is a complete production workflow that
the agent can execute. Validate them with `agentic_cuts.lib.pipeline_loader`.
"""

from pathlib import Path

PIPELINES_DIR: Path = Path(__file__).parent
"""Absolute path to the directory holding YAML manifests for built-in pipelines."""
