"""CostTracker — including the HARD STOP that OpenMontage doesn't have."""

from __future__ import annotations

import pytest

from agentic_cuts import BudgetExceededError, BudgetMode, CostTracker


def test_estimate_reserve_reconcile_happy_path():
    t = CostTracker(total_budget_usd=1.00)
    rid = t.estimate("tts", 0.10)
    t.reserve(rid)
    assert t.reserved_usd == pytest.approx(0.10)
    assert t.spent_usd == 0.0
    t.reconcile(rid, 0.08)  # actual ended up cheaper
    assert t.spent_usd == pytest.approx(0.08)
    assert t.reserved_usd == 0.0


def test_cap_mode_hard_stops_on_overrun():
    t = CostTracker(total_budget_usd=0.50, mode=BudgetMode.CAP)
    rid = t.estimate("video_gen", 1.00)  # over budget
    with pytest.raises(BudgetExceededError):
        t.reserve(rid)


def test_warn_mode_does_not_stop():
    t = CostTracker(total_budget_usd=0.50, mode=BudgetMode.WARN)
    rid = t.estimate("video_gen", 1.00)
    t.reserve(rid)  # logs but does not raise
    t.reconcile(rid, 1.00)
    assert t.spent_usd == pytest.approx(1.00)
    snap = t.snapshot()
    assert snap.spent_usd == pytest.approx(1.00)
    assert snap.remaining_usd < 0


def test_observe_mode_silent_on_overrun():
    t = CostTracker(total_budget_usd=0.10, mode=BudgetMode.OBSERVE)
    rid = t.estimate("anything", 5.00)
    t.reserve(rid)
    t.reconcile(rid, 5.00)
    assert t.spent_usd == pytest.approx(5.00)


def test_can_afford_and_remaining():
    t = CostTracker(total_budget_usd=2.00)
    assert t.can_afford(1.5)
    rid = t.estimate("a", 1.0)
    t.reserve(rid)
    assert t.remaining_usd == pytest.approx(1.0)
    assert t.can_afford(0.99)
    assert not t.can_afford(1.5)


def test_reconcile_actual_over_budget_raises_in_cap_mode():
    """If estimate fits but actual cost balloons, CAP still raises on reconcile."""
    t = CostTracker(total_budget_usd=0.50, mode=BudgetMode.CAP)
    rid = t.estimate("a", 0.30)
    t.reserve(rid)
    with pytest.raises(BudgetExceededError):
        t.reconcile(rid, 0.80)


def test_cancel_releases_reservation():
    t = CostTracker(total_budget_usd=1.00)
    rid = t.estimate("a", 0.50)
    assert t.reserved_usd == 0.50
    t.cancel(rid)
    assert t.reserved_usd == 0.0
