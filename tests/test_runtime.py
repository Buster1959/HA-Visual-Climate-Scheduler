"""Runtime tests for confirmed, battery-safe climate writes."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from custom_components.visual_climate_scheduler.models import (
    RoomSchedule,
    ScheduleConfiguration,
    SchedulePeriod,
    WEEKDAYS,
)
from custom_components.visual_climate_scheduler.runtime import ScheduleRuntime


NOW = datetime(2026, 8, 29, 18, 0, tzinfo=timezone.utc)


class FakeState:
    def __init__(
        self,
        temperature: float | None,
        *,
        state: str = "heat",
        reported_at: datetime = NOW,
    ) -> None:
        self.state = state
        self.attributes = {"temperature": temperature}
        self.last_reported = reported_at
        self.last_updated = reported_at


class FakeStates:
    def __init__(self, values: dict[str, FakeState]) -> None:
        self.values = values

    def get(self, entity_id: str) -> FakeState | None:
        return self.values.get(entity_id)


class FakeServices:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []
        self.on_call = None

    async def async_call(self, domain, service, data, *, blocking):
        self.calls.append(dict(data))
        if self.on_call is not None:
            self.on_call(data)


class FakeHass:
    def __init__(self, states: dict[str, FakeState]) -> None:
        self.states = FakeStates(states)
        self.services = FakeServices()
        self.tasks: list[asyncio.Task] = []

    def async_create_task(self, coroutine):
        task = asyncio.create_task(coroutine)
        self.tasks.append(task)
        return task


def scheduled_room(
    room_id: str, name: str, entity_ids: tuple[str, ...]
) -> RoomSchedule:
    days = {day: () for day in WEEKDAYS}
    days["saturday"] = (
        SchedulePeriod("morning", "morning", "Morning", "06:00", 21.0),
    )
    return RoomSchedule(
        id=room_id,
        name=name,
        area_id=None,
        climate_entity_ids=entity_ids,
        days=days,
    )


class FakeAudit:
    def __init__(self) -> None:
        self.entries: list[dict[str, object]] = []

    async def async_record(self, **entry) -> None:
        self.entries.append(entry)


class RuntimeConfirmationTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.entity_id = "climate.wall_thermostat"
        self.state = FakeState(18.0)
        self.hass = FakeHass({self.entity_id: self.state})
        self.audit = FakeAudit()
        self.runtime = ScheduleRuntime(self.hass, self.audit)
        self.room = SimpleNamespace(
            id="bedroom",
            name="Bedroom",
            climate_entity_ids=(self.entity_id,),
        )

    async def apply(self, temperature: float = 21.0) -> None:
        with patch(
            "custom_components.visual_climate_scheduler.runtime.dt_util.utcnow",
            return_value=NOW,
        ):
            await self.runtime._async_apply_temperature(
                self.room,
                temperature,
                cause="scheduled_transition",
                timestamp=NOW,
            )

    async def test_service_acceptance_stays_pending_until_device_confirms(self):
        await self.apply()

        self.assertEqual(1, len(self.hass.services.calls))
        self.assertEqual(
            21.0,
            self.runtime._pending_targets[self.entity_id].temperature,
        )
        self.assertEqual("pending_confirmation", self.audit.entries[-1]["outcome"])

        self.state.attributes["temperature"] = 21.0
        self.state.last_reported = NOW + timedelta(hours=1)
        with patch(
            "custom_components.visual_climate_scheduler.runtime.dt_util.utcnow",
            return_value=NOW + timedelta(hours=1),
        ):
            await self.runtime._async_handle_pending_target_report(self.entity_id)

        self.assertNotIn(self.entity_id, self.runtime._pending_targets)
        self.assertEqual("confirmed_after_report", self.audit.entries[-1]["outcome"])
        self.assertEqual(1, len(self.hass.services.calls))

    async def test_retry_requires_a_fresh_report_and_is_one_shot_per_report(self):
        await self.apply()

        with patch(
            "custom_components.visual_climate_scheduler.runtime.dt_util.utcnow",
            return_value=NOW + timedelta(minutes=6),
        ):
            await self.runtime._async_handle_pending_target_report(self.entity_id)
            self.assertEqual(1, len(self.hass.services.calls))

            self.state.last_reported = NOW + timedelta(minutes=6)
            await self.runtime._async_handle_pending_target_report(self.entity_id)
            await self.runtime._async_handle_pending_target_report(self.entity_id)

        self.assertEqual(2, len(self.hass.services.calls))

    async def test_rate_limit_blocks_a_burst_of_fresh_reports(self):
        await self.apply()
        self.state.last_reported = NOW + timedelta(minutes=1)

        with patch(
            "custom_components.visual_climate_scheduler.runtime.dt_util.utcnow",
            return_value=NOW + timedelta(minutes=1),
        ):
            await self.runtime._async_handle_pending_target_report(self.entity_id)

        self.assertEqual(1, len(self.hass.services.calls))

    async def test_unavailable_target_waits_and_retries_on_recovery_report(self):
        self.state.state = "unavailable"
        await self.apply()

        self.assertEqual([], self.hass.services.calls)
        self.assertIn(self.entity_id, self.runtime._pending_targets)
        self.assertEqual("skipped_unavailable", self.audit.entries[-1]["outcome"])

        self.state.state = "heat"
        self.state.last_reported = NOW + timedelta(minutes=1)
        with patch(
            "custom_components.visual_climate_scheduler.runtime.dt_util.utcnow",
            return_value=NOW + timedelta(minutes=1),
        ):
            await self.runtime._async_handle_pending_target_report(self.entity_id)

        self.assertEqual(1, len(self.hass.services.calls))
        self.assertEqual("pending_confirmation", self.audit.entries[-1]["outcome"])

    async def test_already_correct_target_is_not_written(self):
        self.state.attributes["temperature"] = 21.0
        await self.apply()

        self.assertEqual([], self.hass.services.calls)
        self.assertNotIn(self.entity_id, self.runtime._pending_targets)
        self.assertEqual("already_at_target", self.audit.entries[-1]["outcome"])

    async def test_rejected_target_does_not_block_other_rooms_or_timer(self):
        first = "climate.first_room_bad_thermostat"
        second = "climate.first_room_good_thermostat"
        third = "climate.second_room_thermostat"
        hass = FakeHass(
            {
                first: FakeState(18.0),
                second: FakeState(18.0),
                third: FakeState(18.0),
            }
        )
        audit = FakeAudit()
        runtime = ScheduleRuntime(hass, audit)
        runtime._configuration = ScheduleConfiguration(
            rooms={
                "first_room": scheduled_room(
                    "first_room", "First Room", (first, second)
                ),
                "second_room": scheduled_room(
                    "second_room", "Second Room", (third,)
                ),
            }
        )

        def reject_first_target(data):
            if data["entity_id"] == first:
                raise ValueError("target outside thermostat range")

        hass.services.on_call = reject_first_target
        with (
            patch(
                "custom_components.visual_climate_scheduler.runtime.dt_util.utcnow",
                return_value=NOW,
            ),
            patch(
                "custom_components.visual_climate_scheduler.runtime.dt_util.now",
                return_value=NOW,
            ),
            patch.object(runtime, "_schedule_next_transition") as schedule_next,
        ):
            await runtime._async_handle_transition(NOW)

        self.assertEqual(
            [first, second, third],
            [call["entity_id"] for call in hass.services.calls],
        )
        self.assertIn(first, runtime._pending_targets)
        self.assertEqual("failed_pending_retry", audit.entries[0]["outcome"])
        self.assertEqual("pending_confirmation", audit.entries[-1]["outcome"])
        schedule_next.assert_called_once_with(NOW)

    async def test_missing_target_is_retried_when_it_first_reports(self):
        entity_id = "climate.late_loading_thermostat"
        hass = FakeHass({})
        audit = FakeAudit()
        runtime = ScheduleRuntime(hass, audit)
        configuration = ScheduleConfiguration(
            rooms={
                "late_room": scheduled_room(
                    "late_room", "Late Room", (entity_id,)
                )
            }
        )

        with (
            patch(
                "custom_components.visual_climate_scheduler.runtime.event_helper.async_track_state_change_event",
                return_value=lambda: None,
            ),
            patch(
                "custom_components.visual_climate_scheduler.runtime.event_helper.async_track_state_report_event",
                return_value=lambda: None,
            ),
            patch.object(runtime, "_schedule_next_transition"),
            patch(
                "custom_components.visual_climate_scheduler.runtime.dt_util.now",
                return_value=NOW,
            ),
        ):
            await runtime.async_start(configuration)
            self.assertIn(entity_id, runtime._pending_targets)
            hass.states.values[entity_id] = FakeState(18.0)
            runtime._handle_target_event(
                SimpleNamespace(data={"entity_id": entity_id})
            )
            await asyncio.gather(*hass.tasks)

        self.assertEqual(
            [entity_id], [call["entity_id"] for call in hass.services.calls]
        )
        self.assertEqual("pending_confirmation", audit.entries[-1]["outcome"])


if __name__ == "__main__":
    unittest.main()
