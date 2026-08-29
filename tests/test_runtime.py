"""Runtime tests for confirmed, battery-safe climate writes."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
import unittest
from unittest.mock import patch

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


if __name__ == "__main__":
    unittest.main()
