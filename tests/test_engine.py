"""Tests for deterministic, Home Assistant-independent schedule selection."""

from __future__ import annotations

from datetime import datetime
import unittest

from custom_components.visual_climate_scheduler.engine import (
    active_period_at,
    next_transition_after,
)
from custom_components.visual_climate_scheduler.models import RoomSchedule, SchedulePeriod, WEEKDAYS


def period(identifier: str, at: str, temperature: float) -> SchedulePeriod:
    return SchedulePeriod(identifier, identifier, identifier.title(), at, temperature)


def room(days: dict[str, tuple[SchedulePeriod, ...]]) -> RoomSchedule:
    return RoomSchedule(
        id="living_room",
        name="Living Room",
        area_id="living_room",
        climate_entity_ids=("climate.living_room",),
        days={day: days.get(day, ()) for day in WEEKDAYS},
    )


class ScheduleEngineTests(unittest.TestCase):
    """Exercise date boundaries without a Home Assistant runtime."""

    def setUp(self) -> None:
        self.room = room(
            {
                "monday": (period("morning", "06:30", 20), period("evening", "18:00", 21)),
                "tuesday": (period("morning", "07:00", 19),),
                "sunday": (period("night", "22:00", 17),),
            }
        )

    def test_selects_latest_period_on_the_current_day(self) -> None:
        active = active_period_at(self.room, datetime(2026, 8, 24, 18, 0))
        self.assertIsNotNone(active)
        self.assertEqual(active.period.id, "evening")
        self.assertEqual(active.period.temperature, 21)

    def test_period_starts_at_its_exact_minute(self) -> None:
        before = active_period_at(self.room, datetime(2026, 8, 24, 6, 29, 59))
        at_start = active_period_at(self.room, datetime(2026, 8, 24, 6, 30))
        self.assertEqual(before.period.id, "night")
        self.assertEqual(at_start.period.id, "morning")

    def test_carries_previous_period_across_midnight_and_empty_days(self) -> None:
        active = active_period_at(self.room, datetime(2026, 8, 26, 12, 0))
        self.assertIsNotNone(active)
        self.assertEqual(active.day, "tuesday")
        self.assertEqual(active.period.id, "morning")

    def test_finds_next_transition_on_current_or_later_day(self) -> None:
        next_period = next_transition_after(self.room, datetime(2026, 8, 24, 8, 0))
        self.assertIsNotNone(next_period)
        self.assertEqual(next_period.period.id, "evening")
        self.assertEqual(next_period.starts_at, datetime(2026, 8, 24, 18, 0))

        next_day = next_transition_after(self.room, datetime(2026, 8, 24, 19, 0))
        self.assertEqual(next_day.period.id, "morning")
        self.assertEqual(next_day.starts_at, datetime(2026, 8, 25, 7, 0))

    def test_empty_schedule_never_selects_or_schedules_a_transition(self) -> None:
        empty = room({})
        when = datetime(2026, 8, 24, 12, 0)
        self.assertIsNone(active_period_at(empty, when))
        self.assertIsNone(next_transition_after(empty, when))
