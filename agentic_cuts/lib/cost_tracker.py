"""CostTracker — estimate / reserve / reconcile + HARD STOP.

This is the OpenMontage gap we're explicitly fixing. Upstream warns when
budget is hit; we kill the run. Configurable per pipeline so creators who
want hands-off generation can set a hard cap and walk away.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

log = logging.getLogger(__name__)


class BudgetMode(str, Enum):
    OBSERVE = "observe"   # Log everything, never stop.
    WARN = "warn"         # Log + warn at thresholds, never stop.
    CAP = "cap"           # HARD STOP at total budget. The recommended default.


class BudgetExceededError(RuntimeError):
    """Raised by CostTracker when CAP mode hits the limit. The agent must catch + abort."""


@dataclass
class _Reservation:
    rid: str
    action: str
    estimate_usd: float
    committed: bool = False
    actual_usd: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CostSnapshot:
    total_budget_usd: float
    spent_usd: float
    reserved_usd: float
    remaining_usd: float
    mode: BudgetMode
    reservations_open: int
    reservations_closed: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_budget_usd": round(self.total_budget_usd, 4),
            "spent_usd": round(self.spent_usd, 4),
            "reserved_usd": round(self.reserved_usd, 4),
            "remaining_usd": round(self.remaining_usd, 4),
            "mode": self.mode.value,
            "reservations_open": self.reservations_open,
            "reservations_closed": self.reservations_closed,
        }


class CostTracker:
    """Three-phase budget governance.

    1. estimate(action, cost) → reservation_id (no money committed yet)
    2. reserve(reservation_id) → enforces the cap; raises BudgetExceededError in CAP mode
    3. reconcile(reservation_id, actual_cost) → commits the actual cost (which may differ)
    """

    def __init__(
        self,
        total_budget_usd: float,
        mode: BudgetMode = BudgetMode.CAP,
        warn_at_pct: float = 0.80,
        reserve_pct: float = 0.10,
    ) -> None:
        if total_budget_usd < 0:
            raise ValueError("total_budget_usd must be non-negative")
        self.total_budget_usd = total_budget_usd
        self.mode = mode
        self.warn_at_pct = warn_at_pct
        self.reserve_pct = reserve_pct
        self._reservations: dict[str, _Reservation] = {}
        self._spent: float = 0.0
        self._warned: bool = False

    @property
    def reserved_usd(self) -> float:
        return sum(r.estimate_usd for r in self._reservations.values() if not r.committed)

    @property
    def spent_usd(self) -> float:
        return self._spent

    @property
    def remaining_usd(self) -> float:
        return self.total_budget_usd - self._spent - self.reserved_usd

    def estimate(self, action: str, estimate_usd: float, **metadata: Any) -> str:
        if estimate_usd < 0:
            raise ValueError("estimate_usd must be non-negative")
        rid = uuid.uuid4().hex[:12]
        self._reservations[rid] = _Reservation(
            rid=rid, action=action, estimate_usd=estimate_usd, metadata=metadata
        )
        log.debug("cost: estimate action=%s usd=%.4f rid=%s", action, estimate_usd, rid)
        return rid

    def reserve(self, reservation_id: str) -> None:
        """Lock the estimate against the cap. Raises BudgetExceededError in CAP mode if over."""
        res = self._reservations.get(reservation_id)
        if res is None:
            raise KeyError(f"Unknown reservation: {reservation_id}")
        # Project the post-reserve state.
        projected = self._spent + self.reserved_usd  # estimate is already in reserved_usd
        usable = self.total_budget_usd * (1.0 - self.reserve_pct)
        if projected > self.total_budget_usd:
            self._handle_overrun(projected, res)
        elif projected > self.total_budget_usd * self.warn_at_pct and not self._warned:
            log.warning(
                "cost: %.0f%% of budget reached ($%.4f / $%.4f) — softer choices ahead",
                projected / self.total_budget_usd * 100,
                projected,
                self.total_budget_usd,
            )
            self._warned = True
        elif projected > usable:
            log.info(
                "cost: dipping into reserve buffer ($%.4f / $%.4f, reserve_pct=%.0f%%)",
                projected,
                self.total_budget_usd,
                self.reserve_pct * 100,
            )

    def reconcile(self, reservation_id: str, actual_usd: float) -> None:
        res = self._reservations.get(reservation_id)
        if res is None:
            raise KeyError(f"Unknown reservation: {reservation_id}")
        if res.committed:
            raise RuntimeError(f"Reservation {reservation_id} already committed")
        if actual_usd < 0:
            raise ValueError("actual_usd must be non-negative")
        res.actual_usd = actual_usd
        res.committed = True
        self._spent += actual_usd
        log.debug(
            "cost: reconcile action=%s estimate=%.4f actual=%.4f spent=%.4f",
            res.action, res.estimate_usd, actual_usd, self._spent,
        )
        if self._spent > self.total_budget_usd:
            self._handle_overrun(self._spent, res)

    def cancel(self, reservation_id: str) -> None:
        res = self._reservations.pop(reservation_id, None)
        if res is None:
            return
        log.debug("cost: cancel rid=%s action=%s", reservation_id, res.action)

    def can_afford(self, cost_usd: float) -> bool:
        return cost_usd <= self.remaining_usd

    def snapshot(self) -> CostSnapshot:
        closed = sum(1 for r in self._reservations.values() if r.committed)
        open_ = len(self._reservations) - closed
        return CostSnapshot(
            total_budget_usd=self.total_budget_usd,
            spent_usd=self._spent,
            reserved_usd=self.reserved_usd,
            remaining_usd=self.remaining_usd,
            mode=self.mode,
            reservations_open=open_,
            reservations_closed=closed,
        )

    def _handle_overrun(self, projected: float, res: _Reservation) -> None:
        msg = (
            f"Budget exceeded: projected ${projected:.4f} "
            f"vs cap ${self.total_budget_usd:.4f} "
            f"(action={res.action!r}, estimate=${res.estimate_usd:.4f})"
        )
        if self.mode == BudgetMode.OBSERVE:
            log.info("cost: OBSERVE — %s", msg)
        elif self.mode == BudgetMode.WARN:
            log.warning("cost: WARN — %s", msg)
        else:
            log.error("cost: CAP — %s", msg)
            raise BudgetExceededError(msg)
