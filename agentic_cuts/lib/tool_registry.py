"""ToolRegistry — auto-discovery of every BaseTool subclass.

Drop a tool file into `tools/<capability>/<provider>.py`, define a class
that subclasses BaseTool, and it shows up here without manual registration.
"""

from __future__ import annotations

import importlib
import inspect
import logging
import pkgutil
from collections.abc import Iterable
from typing import Any

from agentic_cuts.lib.base_tool import BaseTool, Capability

log = logging.getLogger(__name__)


class ToolRegistry:
    """Singleton-ish discovery + lookup. Use `registry` for the shared instance."""

    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}
        self._discovered_packages: set[str] = set()

    def discover(self, package: str = "agentic_cuts.tools") -> int:
        """Walk the package tree, import every module, register every BaseTool subclass.

        Idempotent — calling twice on the same package is a no-op.
        Returns the number of tools registered on this call.
        """
        if package in self._discovered_packages:
            return 0
        try:
            mod = importlib.import_module(package)
        except ModuleNotFoundError:
            log.warning("discover: package %r not importable yet", package)
            return 0

        before = len(self._tools)
        for finder, name, _ispkg in pkgutil.walk_packages(mod.__path__, prefix=f"{package}."):
            try:
                submod = importlib.import_module(name)
            except Exception as exc:  # noqa: BLE001
                log.warning("discover: skip %r — import failed: %s", name, exc)
                continue
            for _, obj in inspect.getmembers(submod, inspect.isclass):
                if obj is BaseTool or not issubclass(obj, BaseTool):
                    continue
                if inspect.isabstract(obj):
                    continue
                try:
                    instance = obj()
                except Exception as exc:  # noqa: BLE001
                    log.warning("discover: skip %s — init failed: %s", obj.__name__, exc)
                    continue
                self.register(instance)
        self._discovered_packages.add(package)
        return len(self._tools) - before

    def register(self, tool: BaseTool) -> None:
        """Manual register (used by tests + explicit wiring). Last write wins on name collision."""
        self._tools[tool.name] = tool

    def get(self, name: str) -> BaseTool | None:
        return self._tools.get(name)

    def all(self) -> list[BaseTool]:
        return list(self._tools.values())

    def by_capability(self, capability: Capability | str) -> list[BaseTool]:
        cap = capability.value if isinstance(capability, Capability) else capability
        return [t for t in self._tools.values() if t.capability.value == cap]

    def by_provider(self, provider: str) -> list[BaseTool]:
        return [t for t in self._tools.values() if t.provider == provider]

    def support_envelope(self) -> dict[str, dict[str, Any]]:
        """Capability → {provider → supports} map. Useful for the agent to reason about coverage."""
        env: dict[str, dict[str, Any]] = {}
        for tool in self._tools.values():
            env.setdefault(tool.capability.value, {})[tool.provider] = tool.supports
        return env

    def provider_menu(self) -> dict[str, list[dict[str, Any]]]:
        """Capability → list of provider summaries. The agent's "what's available right now" view."""
        menu: dict[str, list[dict[str, Any]]] = {}
        for tool in self._tools.values():
            menu.setdefault(tool.capability.value, []).append(
                {
                    "name": tool.name,
                    "provider": tool.provider,
                    "tier": tool.tier.value,
                    "version": tool.version,
                    "cost_per_unit_usd": tool.cost_per_unit_usd,
                    "supports": tool.supports,
                }
            )
        return menu

    def __len__(self) -> int:
        return len(self._tools)

    def __iter__(self) -> Iterable[BaseTool]:
        return iter(self._tools.values())


registry = ToolRegistry()
