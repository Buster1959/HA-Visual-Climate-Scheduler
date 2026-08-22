"""Pure V1 schedule selection logic.

The functions in this module do not know about Home Assistant, timers or climate
services. They resolve which persisted period is active and when a room next
changes, leaving the runtime adapter to perform the actual service call.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from .models import RoomSchedule, SchedulePeriod, WEEKDAYS


@dataclass(frozen=True, slots=True)
class ScheduledPeriod:
    """A period paired with the local date on which it starts."""

    day: str
    starts_at: datetime
    period: SchedulePeriod


def _weekday(value: date) -> str:
    return WEEKDAYS[value.weekday()]


def _starts_at(value: date, period: SchedulePeriod, reference: datetime) -> datetime:
    """Build a local datetime matching ``reference``'s timezone information."""
    start_time = time.fromisoformat(period.time)
    return datetime.combine(value, start_time, tzinfo=reference.tzinfo)


def active_period_at(room: RoomSchedule, when: datetime) -> ScheduledPeriod | None:
    """Return the most recent period for a room, including across midnight.

    Empty days do not invent a new setpoint. The most recent period from an
    earlier populated day remains active, looking back at most one week.
    """
    for offset in range(len(WEEKDAYS)):
        candidate_date = when.date() - timedelta(days=offset)
        day = _weekday(candidate_date)
        periods = room.days[day]
        if not periods:
            continue
        if offset == 0:
            eligible = [period for period in periods if _starts_at(candidate_date, period, when) <= when]
            if not eligible:
                continue
            period = eligible[-1]
        else:
            period = periods[-1]
        return ScheduledPeriod(day, _starts_at(candidate_date, period, when), period)
    return None


def next_transition_after(room: RoomSchedule, when: datetime) -> ScheduledPeriod | None:
    """Return the first strictly future period change, looking ahead one week."""
    for offset in range(len(WEEKDAYS) + 1):
        candidate_date = when.date() + timedelta(days=offset)
        day = _weekday(candidate_date)
        for period in room.days[day]:
            starts_at = _starts_at(candidate_date, period, when)
            if starts_at > when:
                return ScheduledPeriod(day, starts_at, period)
    return None
