"""Tests for scheduled room/zone configuration operations."""

from __future__ import annotations

import unittest

from custom_components.visual_climate_scheduler.models import ScheduleConfiguration
from custom_components.visual_climate_scheduler.rooms import add_scheduled_space, remove_scheduled_space


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
            ScheduleConfiguration.empty(), name="Lounge", climate_entity_ids=("climate.lounge",)
        )
        configuration = add_scheduled_space(
            configuration, name="Bedroom", climate_entity_ids=("climate.bedroom",)
        )
        remaining = remove_scheduled_space(configuration, "lounge")
        self.assertEqual(tuple(remaining.rooms), ("bedroom",))
