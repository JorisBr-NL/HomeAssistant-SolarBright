"""The counter guard against false meter resets."""

from datetime import date

from custom_components.solarbright.guard import CounterGuard

DAY1 = date(2026, 6, 1)
DAY2 = date(2026, 6, 2)


def test_rises_and_ignores_missing():
    guard = CounterGuard()
    assert guard.update(10.0, DAY1) == 10.0
    assert guard.update(None, DAY1) == 10.0
    assert guard.update(10.5, DAY1) == 10.5


def test_single_drop_is_ignored():
    guard = CounterGuard()
    guard.update(9876.5, DAY1)
    assert guard.update(0.1, DAY1) == 9876.5
    assert guard.update(9876.6, DAY1) == 9876.6


def test_lasting_drop_is_accepted_after_three_reads():
    guard = CounterGuard()
    guard.update(5.0, DAY1)
    assert guard.update(0.0, DAY1) == 5.0
    assert guard.update(0.0, DAY1) == 5.0
    assert guard.update(0.01, DAY1) == 0.01


def test_daily_reset_on_a_new_day_is_accepted_at_once():
    guard = CounterGuard()
    guard.update(12.3, DAY1, daily_reset=True)
    assert guard.update(12.3, DAY2, daily_reset=True) == 12.3  # yesterday's value at wake-up
    assert guard.update(0.0, DAY2, daily_reset=True) == 0.0


def test_daily_drop_on_the_same_day_is_a_glitch():
    guard = CounterGuard()
    guard.update(3.0, DAY1, daily_reset=True)
    guard.update(3.2, DAY1, daily_reset=True)
    assert guard.update(0.0, DAY1, daily_reset=True) == 3.2
