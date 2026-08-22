"""Unit tests for the Home Assistant-independent schedule persistence model."""

from __future__ import annotations

import json
import unittest

from custom_components.visual_climate_scheduler.models import (
    RoomSchedule,
    SCHEMA_VERSION,
    ScheduleConfiguration,
    SchedulePeriod,
    WEEKDAYS,
    copy_periods,
)
from custom_components.visual_climate_scheduler.storage import ScheduleStorage


def period(identifier: str, at: str, temperature: float = 20) -> SchedulePeriod:
    return SchedulePeriod(identifier, identifier, identifier.title(), at, temperature)


def room(days: dict[str, tuple[SchedulePeriod, ...]] | None = None) -> RoomSchedule:
    return RoomSchedule(
        id="living_room",
        name="Living Room",
        area_id="living_room",
        climate_entity_id="climate.living_room",
        days=days or {day: () for day in WEEKDAYS},
    )


class ScheduleModelTests(unittest.TestCase):
    """Validate the durable boundary without requiring Home Assistant."""

    def test_persistence_round_trip_is_human_readable_json(self) -> None:
        configured_room = room(
            {day: (period(f"{day}-morning", "06:30"),) for day in WEEKDAYS}
        )
        original = ScheduleConfiguration(
            rooms={configured_room.id: configured_room}, settings={"units": "C"}
        )

        stored_json = json.dumps(original.to_dict(), indent=2, sort_keys=True)
        restored = ScheduleConfiguration.from_dict(json.loads(stored_json))

        self.assertEqual(restored, original)
        self.assertEqual(restored.rooms["living_room"].days["monday"][0].time, "06:30")
        self.assertIn('"version": 1', stored_json)

    def test_seven_days_are_required_and_independent(self) -> None:
        with self.assertRaisesRegex(ValueError, "exactly monday through sunday"):
            room({"monday": ()})

        configured_room = room(
            {day: ((period("monday-only", "06:30"),) if day == "monday" else ()) for day in WEEKDAYS}
        )
        self.assertEqual(configured_room.days["tuesday"], ())
        self.assertNotEqual(configured_room.days["monday"], configured_room.days["tuesday"])

    def test_time_requires_exact_minutes(self) -> None:
        for invalid in ("6:30", "06:3", "06:30:00", "24:00", "09:60"):
            with self.subTest(invalid=invalid), self.assertRaisesRegex(ValueError, "HH:MM"):
                period("morning", invalid)
        self.assertEqual(period("precise", "09:12").time, "09:12")

    def test_period_order_and_conflicts_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "ordered by time"):
            room({day: (period("late", "18:00"), period("early", "06:30")) for day in WEEKDAYS})
        with self.assertRaisesRegex(ValueError, "duplicate period times"):
            room({day: (period("one", "06:30"), period("two", "06:30")) for day in WEEKDAYS})
        with self.assertRaisesRegex(ValueError, "duplicate period ids"):
            room({day: (period("same", "06:30"), period("same", "18:00")) for day in WEEKDAYS})

    def test_storage_has_no_four_period_limit(self) -> None:
        periods = tuple(period(f"p{index}", f"0{index}:00") for index in range(5))
        configured_room = room({day: (periods if day == "monday" else ()) for day in WEEKDAYS})
        self.assertEqual(len(configured_room.days["monday"]), 5)

    def test_copy_preserves_ids_but_detaches_daily_collections(self) -> None:
        source = (period("morning", "06:30"), period("evening", "18:00", 21))
        configured_room = room({day: (source if day == "monday" else ()) for day in WEEKDAYS})

        copied = configured_room.with_days_copied("monday", ("tuesday", "wednesday"))
        standalone_copy = copy_periods(source)

        self.assertEqual(copied.days["tuesday"], source)
        self.assertEqual(copied.days["tuesday"][0].id, "morning")
        self.assertIsNot(copied.days["tuesday"], copied.days["wednesday"])
        self.assertIsNot(standalone_copy[0], source[0])
        self.assertEqual(copied.days["thursday"], ())

    def test_version_zero_migrates_and_future_version_fails(self) -> None:
        migrated = ScheduleConfiguration.from_dict({"rooms": {}, "settings": {}})
        self.assertEqual(migrated.version, SCHEMA_VERSION)
        self.assertEqual(migrated.to_dict()["version"], SCHEMA_VERSION)
        with self.assertRaisesRegex(ValueError, "unsupported"):
            ScheduleConfiguration.from_dict({"version": 2, "rooms": {}, "settings": {}})


class FakeStore:
    """Minimal in-memory stand-in for Home Assistant Store."""

    def __init__(self) -> None:
        self.data: dict[str, object] | None = None

    async def async_load(self) -> dict[str, object] | None:
        return self.data

    async def async_save(self, data: dict[str, object]) -> None:
        self.data = data


class StorageAdapterTests(unittest.IsolatedAsyncioTestCase):
    """Exercise the Home Assistant Store adapter without a Home Assistant runtime."""

    async def test_store_adapter_round_trip(self) -> None:
        store = FakeStore()
        adapter = ScheduleStorage(None, "entry-id", store=store)
        original = ScheduleConfiguration(settings={"display": {"units": "C"}})

        await adapter.async_save(original)
        restored = await adapter.async_load()

        self.assertEqual(restored, original)
        self.assertEqual(store.data["version"], SCHEMA_VERSION)
