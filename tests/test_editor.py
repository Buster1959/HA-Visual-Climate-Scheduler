"""Tests for the pure sidebar editor update boundary."""

from __future__ import annotations

import unittest

from custom_components.visual_climate_scheduler.editor import copy_room_schedule, update_room_days
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


def _days(temperature: float) -> dict[str, tuple[SchedulePeriod, ...]]:
    return {
        day: (SchedulePeriod("wake", "wake", "Wake", "06:07", temperature),)
        if day == "monday"
        else ()
        for day in WEEKDAYS
    }


class EditorUpdateTests(unittest.TestCase):
    """The editor may change days, but not a space's identity or targets."""

    def test_update_revalidates_and_retains_all_other_configuration(self) -> None:
        original = ScheduleConfiguration(
            rooms={"lounge": _room()}, settings={"show_panel": True, "units": "C"}, temperature_unit="°C"
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
        self.assertEqual(updated.temperature_unit, "°C")
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

    def test_copy_replaces_only_destination_days_with_detached_schedule(self) -> None:
        source = RoomSchedule(
            id="lounge",
            name="Lounge",
            area_id="lounge",
            climate_entity_ids=("climate.lounge",),
            days=_days(20),
        )
        destination = RoomSchedule(
            id="bathroom_two",
            name="Bathroom 2",
            area_id="bathroom",
            climate_entity_ids=("climate.bathroom_two",),
            days=_days(17),
        )
        original = ScheduleConfiguration(
            rooms={source.id: source, destination.id: destination}, temperature_unit="°F"
        )
        editor_days = {day: [period.to_dict() for period in periods] for day, periods in _days(21).items()}

        updated = copy_room_schedule(original, source.id, [destination.id], editor_days)

        self.assertEqual(updated.rooms[source.id].days["monday"][0].temperature, 21)
        self.assertEqual(updated.rooms[destination.id].days["monday"][0].temperature, 21)
        self.assertIsNot(updated.rooms[source.id].days["monday"], updated.rooms[destination.id].days["monday"])
        self.assertEqual(updated.rooms[destination.id].days["monday"][0].id, "wake")
        self.assertEqual(updated.rooms[destination.id].name, "Bathroom 2")
        self.assertEqual(updated.rooms[destination.id].climate_entity_ids, ("climate.bathroom_two",))
        self.assertEqual(updated.temperature_unit, "°F")

    def test_copy_rejects_an_empty_or_self_destination(self) -> None:
        original = ScheduleConfiguration(rooms={"lounge": _room()})
        days = {day: [] for day in WEEKDAYS}

        with self.assertRaisesRegex(ValueError, "Select one"):
            copy_room_schedule(original, "lounge", [], days)
        with self.assertRaisesRegex(ValueError, "itself"):
            copy_room_schedule(original, "lounge", ["lounge"], days)
