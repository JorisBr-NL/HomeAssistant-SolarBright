"""Filter for energy counters that should only go up.

Home Assistant reads every decrease of a ``total_increasing`` sensor as a meter
reset. A single wrong value (an empty field read as 0, a half-started inverter)
followed by the real value would then count the whole meter reading as new
production. The guard keeps the last good value until a decrease is either
expected (a daily counter on a new day) or confirmed by several reads in a row.

No Home Assistant imports, so it can be tested on its own.
"""

from __future__ import annotations

from datetime import date

CONFIRM_READS = 3


class CounterGuard:
    """Keep a counter monotonic, except for real resets."""

    def __init__(self, confirm_reads: int = CONFIRM_READS) -> None:
        self._confirm_reads = confirm_reads
        self.value: float | None = None
        self._last_rise: date | None = None  # day the counter last went up (or was first seen)
        self._drops = 0  # consecutive reads below the kept value

    def update(self, new: float | None, today: date, *, daily_reset: bool = False) -> float | None:
        """Feed one read; return the value to show.

        ``daily_reset``: the counter starts again from 0 each day, so a decrease on a
        later day than its last rise is a normal reset.
        """
        if new is None:
            return self.value
        if self.value is None or new >= self.value:
            if self.value is None or new > self.value:
                self._last_rise = today
            self.value = new
            self._drops = 0
            return self.value

        # new < kept value
        expected = daily_reset and self._last_rise is not None and self._last_rise < today
        self._drops += 1
        if expected or self._drops >= self._confirm_reads:
            self.value = new
            self._last_rise = today
            self._drops = 0
        return self.value
