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

    async def async_start(self, configuration: ScheduleConfiguration) -> None:
        """Start from persisted configuration and reconcile current targets."""
        await self.async_set_configuration(configuration)

    async def async_stop(self) -> None:
        """Cancel pending callbacks and discard ephemeral runtime state."""
        self._cancel_pending_transition()
        self._applied_periods.clear()

    async def async_set_configuration(self, configuration: ScheduleConfiguration) -> None:
        """Replace configuration, reconcile immediately, and arrange its next change.

        A future editor calls this after it has saved validated configuration via
        ``ScheduleStorage``. The runtime state is intentionally reset rather than
        persisted, allowing edited active periods to take effect immediately.
        """
        self._configuration = configuration
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
            if active is None:
                continue
            key = (active.starts_at, active.period.id)
            if self._applied_periods.get(room.id) == key:
                continue
            if await self._async_apply_period(room, active):
                self._applied_periods[room.id] = key

    async def _async_apply_period(self, room: RoomSchedule, active: ScheduledPeriod) -> bool:
        """Call only the room's configured climate entity; never its HVAC internals."""
        entity_id = room.climate_entity_id
        if not entity_id.startswith("climate."):
            _LOGGER.warning("Skipping non-climate scheduler target for room %s: %s", room.id, entity_id)
            return False
        if self._hass.states.get(entity_id) is None:
            _LOGGER.warning("Scheduler target is unavailable for room %s: %s", room.id, entity_id)
            return False

        await self._hass.services.async_call(
            CLIMATE_DOMAIN,
            "set_temperature",
            {
                ATTR_ENTITY_ID: entity_id,
                ATTR_TEMPERATURE: active.period.temperature,
            },
            blocking=True,
        )
        _LOGGER.debug(
            "Applied %s (%s) to %s at %s",
            active.period.name,
            active.period.temperature,
            entity_id,
            active.starts_at.isoformat(),
        )
        return True

    def _schedule_next_transition(self, now: datetime) -> None:
        candidates = [
            transition
            for room in self._configuration.rooms.values()
            if (transition := next_transition_after(room, now)) is not None
        ]
        if not candidates:
            return
        next_at = min(candidate.starts_at for candidate in candidates)
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
