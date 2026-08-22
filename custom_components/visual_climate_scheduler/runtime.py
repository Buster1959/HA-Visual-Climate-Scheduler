"""Home Assistant runtime adapter for the deterministic V1 schedule engine."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
import logging

from homeassistant.components.climate.const import DOMAIN as CLIMATE_DOMAIN
from homeassistant.const import ATTR_ENTITY_ID, ATTR_TEMPERATURE
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import event as event_helper
from homeassistant.util import dt as dt_util

from .engine import ScheduledPeriod, active_period_at, next_transition_after
from .models import RoomSchedule, ScheduleConfiguration
from .overrides import TemporaryOverride, create_temporary_overrides

_LOGGER = logging.getLogger(__name__)


class ScheduleRuntime:
    """Apply active periods and retain only ephemeral scheduling state.

    The persisted model remains the source of truth. This class owns no saved
    overrides or active-period data; it simply reconstructs the current target
    at startup and arranges the next transition while Home Assistant is running.
    """

    def __init__(self, hass: HomeAssistant) -> None:
        self._hass = hass
        self._configuration = ScheduleConfiguration.empty()
        self._cancel_next: Callable[[], None] | None = None
        self._applied_periods: dict[str, tuple[datetime, str]] = {}
        self._overrides: dict[str, TemporaryOverride] = {}

    async def async_start(self, configuration: ScheduleConfiguration) -> None:
        """Start from persisted configuration and reconcile current targets."""
        await self.async_set_configuration(configuration)

    async def async_stop(self) -> None:
        """Cancel pending callbacks and discard ephemeral runtime state."""
        self._cancel_pending_transition()
        self._applied_periods.clear()
        self._overrides.clear()

    async def async_set_configuration(self, configuration: ScheduleConfiguration) -> None:
        """Replace configuration, reconcile immediately, and arrange its next change.

        A future editor calls this after it has saved validated configuration via
        ``ScheduleStorage``. The runtime state is intentionally reset rather than
        persisted, allowing edited active periods to take effect immediately.
        """
        self._configuration = configuration
        self._overrides = {room_id: override for room_id, override in self._overrides.items() if room_id in configuration.rooms}
        self._applied_periods.clear()
        self._cancel_pending_transition()
        now = dt_util.now()
        await self._async_apply_active_periods(now)
        self._schedule_next_transition(now)

    def _cancel_pending_transition(self) -> None:
        if self._cancel_next is not None:
            self._cancel_next()
            self._cancel_next = None

    async def _async_apply_active_periods(self, now: datetime) -> None:
        """Apply only rooms whose active period changed since this runtime started."""
        for room in self._configuration.rooms.values():
            active = active_period_at(room, now)
            override = self._overrides.get(room.id)
            if override is not None and override.expires_at <= now:
                self._overrides.pop(room.id)
                override = None
            if active is None and override is None:
                continue
            key = (override.expires_at, f"override:{override.temperature}") if override else (active.starts_at, active.period.id)
            if self._applied_periods.get(room.id) == key:
                continue
            temperature = override.temperature if override else active.period.temperature
            if await self._async_apply_temperature(room, temperature):
                self._applied_periods[room.id] = key

    async def _async_apply_temperature(self, room: RoomSchedule, temperature: float) -> bool:
        """Call every configured target; never its HVAC internals or underlying TRVs."""
        applied = False
        for entity_id in room.climate_entity_ids:
            if self._hass.states.get(entity_id) is None:
                _LOGGER.warning("Scheduler target is unavailable for room %s: %s", room.id, entity_id)
                continue
            await self._hass.services.async_call(
                CLIMATE_DOMAIN,
                "set_temperature",
                {
                    ATTR_ENTITY_ID: entity_id,
                    ATTR_TEMPERATURE: temperature,
                },
                blocking=True,
            )
            applied = True
            _LOGGER.debug(
                "Applied temporary/effective target %s to %s",
                temperature,
                entity_id,
            )
        return applied

    def _schedule_next_transition(self, now: datetime) -> None:
        candidates = [
            transition
            for room in self._configuration.rooms.values()
            if (transition := next_transition_after(room, now)) is not None
        ]
        candidates.extend(override for override in self._overrides.values() if override.expires_at > now)
        if not candidates:
            return
        next_at = min(candidate.starts_at if isinstance(candidate, ScheduledPeriod) else candidate.expires_at for candidate in candidates)
        self._cancel_next = event_helper.async_track_point_in_time(
            self._hass, self._handle_transition, next_at
        )

    @callback
    def _handle_transition(self, now: datetime) -> None:
        """Queue async application when Home Assistant reaches a scheduled time."""
        self._cancel_next = None
        self._hass.async_create_task(self._async_handle_transition(now))

    async def _async_handle_transition(self, now: datetime) -> None:
        await self._async_apply_active_periods(now)
        self._schedule_next_transition(now)

    async def async_set_temporary_override(self, room_ids: list[str], *, duration: str, value: float, operation: str) -> list[TemporaryOverride]:
        """Apply a transient batch action without changing persisted schedules."""
        now = dt_util.now()
        base_temperatures = {
            room_id: override.temperature
            for room_id, override in self._overrides.items()
            if room_id in room_ids and override.expires_at > now
        }
        overrides = create_temporary_overrides(
            self._configuration,
            room_ids,
            now=now,
            duration=duration,
            value=value,
            operation=operation,
            base_temperatures=base_temperatures,
        )
        self._overrides.update({override.room_id: override for override in overrides})
        self._applied_periods.clear()
        self._cancel_pending_transition()
        await self._async_apply_active_periods(now)
        self._schedule_next_transition(now)
        return overrides

    async def async_clear_temporary_override(self, room_id: str) -> None:
        """Cancel one room's hold and restore its current scheduled target."""
        self._overrides.pop(room_id, None)
        now = dt_util.now()
        self._applied_periods.clear()
        self._cancel_pending_transition()
        await self._async_apply_active_periods(now)
        self._schedule_next_transition(now)

    def quick_change_state(self) -> dict[str, object]:
        """Return current per-space targets and short-lived holds for the UI."""
        now = dt_util.now()
        rooms = []
        for room in self._configuration.rooms.values():
            active = active_period_at(room, now)
            override = self._overrides.get(room.id)
            if override is not None and override.expires_at <= now:
                override = None
            rooms.append({"id": room.id, "name": room.name, "scheduled_temperature": active.period.temperature if active else None, "effective_temperature": override.temperature if override else (active.period.temperature if active else None), "next_change_at": next_transition_after(room, now).starts_at.isoformat() if next_transition_after(room, now) else None, "override": override.to_dict() if override else None})
        return {"rooms": rooms}
