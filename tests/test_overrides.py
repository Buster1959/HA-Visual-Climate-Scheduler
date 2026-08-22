"""Pure temporary-override rules."""

from datetime import datetime
import unittest

from custom_components.visual_climate_scheduler.models import RoomSchedule, ScheduleConfiguration, SchedulePeriod, WEEKDAYS
from custom_components.visual_climate_scheduler.overrides import create_temporary_overrides


def room(room_id: str, at: str, temperature: float) -> RoomSchedule:
    return RoomSchedule(room_id, room_id.title(), None, (f"climate.{room_id}",), {day: ((SchedulePeriod("morning", "morning", "Morning", at, temperature),) if day == "monday" else ()) for day in WEEKDAYS})


class OverrideTests(unittest.TestCase):
    def setUp(self) -> None:
        self.configuration = ScheduleConfiguration(rooms={"lounge": room("lounge", "06:00", 19), "bedroom": room("bedroom", "07:00", 18)})
        self.now = datetime(2026, 8, 24, 8, 0)

    def test_delta_is_resolved_to_fixed_target_per_room(self) -> None:
        overrides = create_temporary_overrides(self.configuration, ["lounge", "bedroom"], now=self.now, duration="2h", operation="delta", value=2)
        self.assertEqual([override.temperature for override in overrides], [21, 20])
        self.assertEqual(overrides[0].expires_at, datetime(2026, 8, 24, 10, 0))

    def test_delta_steps_from_an_existing_hold(self) -> None:
        overrides = create_temporary_overrides(
            self.configuration,
            ["lounge", "bedroom"],
            now=self.now,
            duration="2h",
            operation="delta",
            value=1,
            base_temperatures={"lounge": 22},
        )
        self.assertEqual([override.temperature for override in overrides], [23, 19])

    def test_next_change_is_independent_per_room(self) -> None:
        overrides = create_temporary_overrides(self.configuration, ["lounge", "bedroom"], now=self.now, duration="next_change", operation="temperature", value=21)
        self.assertEqual(overrides[0].expires_at, datetime(2026, 8, 31, 6, 0))
        self.assertEqual(overrides[1].expires_at, datetime(2026, 8, 31, 7, 0))

    def test_invalid_scope_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "Select one"):
            create_temporary_overrides(self.configuration, [], now=self.now, duration="2h", operation="temperature", value=21)
