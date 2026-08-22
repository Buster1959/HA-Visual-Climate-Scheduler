"""Tests for the pure sidebar editor update boundary."""

from __future__ import annotations

import unittest

from custom_components.visual_climate_scheduler.editor import update_room_days
from custom_components.visual_climate_scheduler.models import (
    RoomSchedule,
    ScheduleConfiguration,
    SchedulePeriod,
    WEEKDAYS,
)


def _room() -> RoomSchedule:
    return RoomSchedule(
        id="lounge",
        name="Lounge",
        area_id="lounge",
        climate_entity_ids=("climate.lounge_one", "climate.lounge_two"),
        days={day: () for day in WEEKDAYS},
    )


class EditorUpdateTests(unittest.TestCase):
    """The editor may change days, but not a space's identity or targets."""

    def test_update_revalidates_and_retains_all_other_configuration(self) -> None:
        original = ScheduleConfiguration(
            rooms={"lounge": _room()}, settings={"show_panel": True, "units": "C"}
        )
        days = {day: [] for day in WEEKDAYS}
        days["monday"] = [
            {
                "id": "wake",
                "friendly_name": "wake",
                "name": "Wake",
                "time": "06:07",
                "temperature": 20.5,
            }
        ]

        updated = update_room_days(original, "lounge", days)

        self.assertEqual(updated.settings, {"show_panel": True, "units": "C"})
        self.assertEqual(
            updated.rooms["lounge"].climate_entity_ids,
            ("climate.lounge_one", "climate.lounge_two"),
        )
        self.assertEqual(updated.rooms["lounge"].days["monday"][0].time, "06:07")
        self.assertEqual(original.rooms["lounge"].days["monday"], ())

    def test_update_rejects_unknown_space_and_invalid_days(self) -> None:
        original = ScheduleConfiguration(rooms={"lounge": _room()})

        with self.assertRaises(KeyError):
            update_room_days(original, "bedroom", {day: [] for day in WEEKDAYS})
        with self.assertRaisesRegex(ValueError, "ordered by time"):
            update_room_days(
                original,
                "lounge",
                {
                    day: (
                        [
                            SchedulePeriod("later", "later", "Later", "18:00", 20).to_dict(),
                            SchedulePeriod("early", "early", "Early", "06:00", 20).to_dict(),
                        ]
                        if day == "monday"
                        else []
                    )
                    for day in WEEKDAYS
                },
            )
