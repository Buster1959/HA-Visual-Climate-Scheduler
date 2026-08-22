"""Tests for scheduled room/zone configuration operations."""

from __future__ import annotations

import unittest

from custom_components.visual_climate_scheduler.models import ScheduleConfiguration
from custom_components.visual_climate_scheduler.models import SchedulePeriod, WEEKDAYS
from custom_components.visual_climate_scheduler.rooms import (
    add_scheduled_space,
    remove_scheduled_space,
    update_scheduled_space,
)


class ScheduledSpaceTests(unittest.TestCase):
    """Keep room setup independent of Home Assistant's options-flow UI."""

    def test_adds_multiple_thermostats_to_one_space(self) -> None:
        configuration = add_scheduled_space(
            ScheduleConfiguration.empty(),
            name="Lounge",
            area_id="lounge",
            climate_entity_ids=("climate.lounge_1", "climate.lounge_2", "climate.lounge_3"),
        )
        lounge = configuration.rooms["lounge"]
        self.assertEqual(lounge.name, "Lounge")
        self.assertEqual(lounge.climate_entity_ids, ("climate.lounge_1", "climate.lounge_2", "climate.lounge_3"))
        self.assertTrue(all(not periods for periods in lounge.days.values()))

    def test_prevents_competing_schedules_for_one_target(self) -> None:
        configuration = add_scheduled_space(
            ScheduleConfiguration.empty(),
            name="Hotel Zone One",
            climate_entity_ids=("climate.room_1", "climate.room_2"),
        )
        with self.assertRaisesRegex(ValueError, "already scheduled"):
            add_scheduled_space(
                configuration,
                name="Room One",
                climate_entity_ids=("climate.room_1",),
            )

    def test_removal_leaves_other_spaces_unchanged(self) -> None:
        configuration = add_scheduled_space(
            ScheduleConfiguration.empty().with_temperature_unit("°C"), name="Lounge", climate_entity_ids=("climate.lounge",)
        )
        configuration = add_scheduled_space(
            configuration, name="Bedroom", climate_entity_ids=("climate.bedroom",)
        )
        remaining = remove_scheduled_space(configuration, "lounge")
        self.assertEqual(tuple(remaining.rooms), ("bedroom",))
        self.assertEqual(remaining.temperature_unit, "°C")

    def test_modifying_space_adds_thermostat_without_losing_schedule(self) -> None:
        initial = add_scheduled_space(
            ScheduleConfiguration.empty(), name="Lounge", climate_entity_ids=("climate.lounge_1",)
        )
        room = initial.rooms["lounge"]
        scheduled = type(room)(
            id=room.id,
            name=room.name,
            area_id=room.area_id,
            climate_entity_ids=room.climate_entity_ids,
            days={
                day: (
                    (SchedulePeriod("morning", "morning", "Morning", "06:30", 20),)
                    if day == "monday"
                    else ()
                )
                for day in WEEKDAYS
            },
        )
        initial = ScheduleConfiguration(rooms={"lounge": scheduled})

        updated = update_scheduled_space(
            initial,
            "lounge",
            name="Main Lounge",
            area_id="living_area",
            climate_entity_ids=("climate.lounge_1", "climate.lounge_2"),
        )

        self.assertEqual(updated.rooms["lounge"].name, "Main Lounge")
        self.assertEqual(
            updated.rooms["lounge"].climate_entity_ids,
            ("climate.lounge_1", "climate.lounge_2"),
        )
        self.assertEqual(updated.rooms["lounge"].days["monday"][0].time, "06:30")

    def test_modifying_space_cannot_take_thermostat_from_another_space(self) -> None:
        configuration = add_scheduled_space(
            ScheduleConfiguration.empty(), name="Lounge", climate_entity_ids=("climate.lounge",)
        )
        configuration = add_scheduled_space(
            configuration, name="Bedroom", climate_entity_ids=("climate.bedroom",)
        )

        with self.assertRaisesRegex(ValueError, "already scheduled"):
            update_scheduled_space(
                configuration,
                "lounge",
                name="Lounge",
                climate_entity_ids=("climate.lounge", "climate.bedroom"),
            )
