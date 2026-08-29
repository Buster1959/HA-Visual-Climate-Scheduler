"""Home Assistant runtime adapter for the deterministic V1 schedule engine."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
import logging
from typing import Any

from homeassistant.components.climate.const import DOMAIN as CLIMATE_DOMAIN
from homeassistant.const import ATTR_ENTITY_ID, ATTR_TEMPERATURE
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import event as event_helper
from homeassistant.util import dt as dt_util

from .audit import AuditLog
from .const import SETPOINT_CONFIRMATION_RETRY_MIN_SECONDS
from .engine import ScheduledPeriod, active_period_at, next_transition_after
from .models import RoomSchedule, ScheduleConfiguration
from .overrides import TemporaryOverride, create_temporary_overrides

_LOGGER = logging.getLogger(__name__)

UNAVAILABLE_STATES = ("unavailable", "unknown")


@dataclass(frozen=True)
class PendingTarget:
    """Latest scheduled target not yet confirmed by one climate entity."""

    room_id: str
    room_name: str
    temperature: float
    cause: str
    observed_reported_at: datetime | None
    last_attempt_at: datetime | None


class ScheduleRuntime:
    """Apply active periods and retain only ephemeral scheduling state.

    The persisted model remains the source of truth. This class owns no saved
    overrides or active-period data; it simply reconstructs the current target
    at startup and arranges the next transition while Home Assistant is running.
    """

    def __init__(self, hass: HomeAssistant, audit_log: AuditLog) -> None:
        self._hass = hass
        self._audit_log = audit_log
        self._configuration = ScheduleConfiguration.empty()
        self._cancel_next: Callable[[], None] | None = None
        self._applied_periods: dict[str, tuple[datetime, str]] = {}
        self._overrides: dict[str, TemporaryOverride] = {}
        self._pending_targets: dict[str, PendingTarget] = {}
        self._unsub_target_events: list[Callable[[], None]] = []

    async def async_start(self, configuration: ScheduleConfiguration) -> None:
        """Start from persisted configuration and reconcile current targets."""
        await self.async_set_configuration(configuration, cause="startup_reconciliation")

    async def async_stop(self) -> None:
        """Cancel pending callbacks and discard ephemeral runtime state."""
        self._cancel_pending_transition()
        self._cancel_target_event_listeners()
        self._applied_periods.clear()
        self._overrides.clear()
        self._pending_targets.clear()

    async def async_set_configuration(
        self,
        configuration: ScheduleConfiguration,
        *,
        cause: str = "configuration_saved",
    ) -> None:
        """Replace configuration, reconcile immediately, and arrange its next change.

        A future editor calls this after it has saved validated configuration via
        ``ScheduleStorage``. The runtime state is intentionally reset rather than
        persisted, allowing edited active periods to take effect immediately.
        """
        self._configuration = configuration
        configured_targets = {
            entity_id
            for room in configuration.rooms.values()
            for entity_id in room.climate_entity_ids
        }
        self._pending_targets = {
            entity_id: pending
            for entity_id, pending in self._pending_targets.items()
            if entity_id in configured_targets
        }
        self._sync_target_event_listeners(configured_targets)
        self._overrides = {room_id: override for room_id, override in self._overrides.items() if room_id in configuration.rooms}
        self._applied_periods.clear()
        self._cancel_pending_transition()
        now = dt_util.now()
        await self._async_apply_active_periods(now, cause=cause)
        self._schedule_next_transition(now)

    def _cancel_pending_transition(self) -> None:
        if self._cancel_next is not None:
            self._cancel_next()
            self._cancel_next = None

    def _cancel_target_event_listeners(self) -> None:
        for unsubscribe in self._unsub_target_events:
            unsubscribe()
        self._unsub_target_events.clear()

    def _sync_target_event_listeners(self, entity_ids: set[str]) -> None:
        """Listen for both changed and unchanged reports from configured targets."""
        self._cancel_target_event_listeners()
        if not entity_ids:
            return
        targets = sorted(entity_ids)
        self._unsub_target_events = [
            event_helper.async_track_state_change_event(
                self._hass, targets, self._handle_target_event
            ),
            event_helper.async_track_state_report_event(
                self._hass, targets, self._handle_target_event
            ),
        ]

    @callback
    def _handle_target_event(self, event: Any) -> None:
        """Queue confirmation/retry handling without synchronising manual changes."""
        entity_id = event.data["entity_id"]
        if entity_id in self._pending_targets:
            self._hass.async_create_task(
                self._async_handle_pending_target_report(entity_id)
            )

    async def _async_apply_active_periods(self, now: datetime, *, cause: str) -> None:
        """Apply only rooms whose active period changed since this runtime started."""
        for room in self._configuration.rooms.values():
            active = active_period_at(room, now)
            override = self._overrides.get(room.id)
            override_expired = False
            if override is not None and override.expires_at <= now:
                self._overrides.pop(room.id)
                override = None
                override_expired = True
            if active is None and override is None:
                continue
            key = (override.expires_at, f"override:{override.temperature}") if override else (active.starts_at, active.period.id)
            if self._applied_periods.get(room.id) == key:
                continue
            temperature = override.temperature if override else active.period.temperature
            room_cause = "temporary_override_expired" if override_expired else cause
            if await self._async_apply_temperature(
                room, temperature, cause=room_cause, timestamp=now
            ):
                self._applied_periods[room.id] = key

    async def _async_apply_temperature(
        self,
        room: RoomSchedule,
        temperature: float,
        *,
        cause: str,
        timestamp: datetime,
    ) -> bool:
        """Request and confirm every configured standard climate target."""
        applied = False
        for entity_id in room.climate_entity_ids:
            await self._async_apply_target(
                room,
                entity_id,
                temperature,
                cause=cause,
                timestamp=timestamp,
            )
            # An unavailable or sleeping target remains queued and has its own
            # event-driven reconciliation path, so the room period is handled.
            applied = True
        return applied

    @staticmethod
    def _reported_at(state: Any) -> datetime | None:
        if state is None:
            return None
        return getattr(state, "last_reported", getattr(state, "last_updated", None))

    @staticmethod
    def _target_temperature(state: Any) -> float | None:
        if state is None:
            return None
        value = state.attributes.get(ATTR_TEMPERATURE)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return float(value)
        return None

    @classmethod
    def _target_matches(cls, state: Any, temperature: float) -> bool:
        current = cls._target_temperature(state)
        return current is not None and abs(current - temperature) < 0.01

    async def _async_apply_target(
        self,
        room: RoomSchedule,
        entity_id: str,
        temperature: float,
        *,
        cause: str,
        timestamp: datetime,
    ) -> None:
        """Apply one target or retain it until an unavailable device reports."""
        state = self._hass.states.get(entity_id)
        previous_temperature = self._target_temperature(state)
        pending = PendingTarget(
            room_id=room.id,
            room_name=room.name,
            temperature=temperature,
            cause=cause,
            observed_reported_at=self._reported_at(state),
            last_attempt_at=None,
        )
        self._pending_targets[entity_id] = pending

        if state is None or state.state in UNAVAILABLE_STATES:
            _LOGGER.warning(
                "Scheduler target is unavailable for room %s: %s; "
                "waiting for a fresh device report",
                room.id,
                entity_id,
            )
            await self._audit_log.async_record(
                timestamp=timestamp,
                room_id=room.id,
                room_name=room.name,
                entity_id=entity_id,
                previous_temperature=previous_temperature,
                requested_temperature=temperature,
                cause=cause,
                outcome="skipped_unavailable",
            )
            return

        if self._target_matches(state, temperature):
            self._pending_targets.pop(entity_id, None)
            await self._audit_log.async_record(
                timestamp=timestamp,
                room_id=room.id,
                room_name=room.name,
                entity_id=entity_id,
                previous_temperature=previous_temperature,
                requested_temperature=temperature,
                cause=cause,
                outcome="already_at_target",
            )
            return

        await self._async_request_target(entity_id, pending, timestamp=timestamp)

    async def _async_request_target(
        self,
        entity_id: str,
        pending: PendingTarget,
        *,
        timestamp: datetime,
    ) -> None:
        """Send one command and retain it until the entity state confirms it."""
        state = self._hass.states.get(entity_id)
        previous_temperature = self._target_temperature(state)
        attempted_at = dt_util.utcnow()
        attempted = PendingTarget(
            room_id=pending.room_id,
            room_name=pending.room_name,
            temperature=pending.temperature,
            cause=pending.cause,
            observed_reported_at=self._reported_at(state),
            last_attempt_at=attempted_at,
        )
        self._pending_targets[entity_id] = attempted
        try:
            await self._hass.services.async_call(
                CLIMATE_DOMAIN,
                "set_temperature",
                {
                    ATTR_ENTITY_ID: entity_id,
                    ATTR_TEMPERATURE: pending.temperature,
                },
                blocking=True,
            )
        except Exception as err:
            await self._audit_log.async_record(
                timestamp=timestamp,
                room_id=pending.room_id,
                room_name=pending.room_name,
                entity_id=entity_id,
                previous_temperature=previous_temperature,
                requested_temperature=pending.temperature,
                cause=pending.cause,
                outcome="failed_pending_retry",
                error=f"{type(err).__name__}: {err}",
            )
            _LOGGER.warning(
                "Could not apply %s to %s; waiting for a fresh device report: %s",
                pending.temperature,
                entity_id,
                err,
            )
            return

        latest_state = self._hass.states.get(entity_id)
        if self._target_matches(latest_state, pending.temperature):
            if self._pending_targets.get(entity_id) is attempted:
                self._pending_targets.pop(entity_id, None)
            outcome = "confirmed"
        else:
            if self._pending_targets.get(entity_id) is attempted:
                self._pending_targets[entity_id] = PendingTarget(
                    room_id=pending.room_id,
                    room_name=pending.room_name,
                    temperature=pending.temperature,
                    cause=pending.cause,
                    observed_reported_at=self._reported_at(latest_state),
                    last_attempt_at=attempted_at,
                )
            outcome = "pending_confirmation"

        await self._audit_log.async_record(
            timestamp=timestamp,
            room_id=pending.room_id,
            room_name=pending.room_name,
            entity_id=entity_id,
            previous_temperature=previous_temperature,
            requested_temperature=pending.temperature,
            cause=pending.cause,
            outcome=outcome,
        )
        _LOGGER.debug(
            "Requested %s from %s: %s",
            pending.temperature,
            entity_id,
            outcome,
        )

    async def _async_handle_pending_target_report(self, entity_id: str) -> None:
        """Confirm or retry once after a fresh report from a pending target."""
        pending = self._pending_targets.get(entity_id)
        if pending is None:
            return
        state = self._hass.states.get(entity_id)
        if state is None or state.state in UNAVAILABLE_STATES:
            return
        now = dt_util.utcnow()
        if self._target_matches(state, pending.temperature):
            if self._pending_targets.get(entity_id) is pending:
                self._pending_targets.pop(entity_id, None)
            await self._audit_log.async_record(
                timestamp=now,
                room_id=pending.room_id,
                room_name=pending.room_name,
                entity_id=entity_id,
                previous_temperature=self._target_temperature(state),
                requested_temperature=pending.temperature,
                cause=pending.cause,
                outcome="confirmed_after_report",
            )
            return

        reported_at = self._reported_at(state)
        if (
            pending.observed_reported_at is not None
            and reported_at is not None
            and reported_at <= pending.observed_reported_at
        ):
            return
        if (
            pending.last_attempt_at is not None
            and (now - pending.last_attempt_at).total_seconds()
            < SETPOINT_CONFIRMATION_RETRY_MIN_SECONDS
        ):
            return

        retry = PendingTarget(
            room_id=pending.room_id,
            room_name=pending.room_name,
            temperature=pending.temperature,
            cause=f"{pending.cause}_confirmation_retry",
            observed_reported_at=reported_at,
            last_attempt_at=pending.last_attempt_at,
        )
        await self._async_request_target(entity_id, retry, timestamp=now)

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
        await self._async_apply_active_periods(now, cause="scheduled_transition")
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
        await self._async_apply_active_periods(now, cause="temporary_override_applied")
        self._schedule_next_transition(now)
        return overrides

    async def async_clear_temporary_override(self, room_id: str) -> None:
        """Cancel one room's hold and restore its current scheduled target."""
        self._overrides.pop(room_id, None)
        now = dt_util.now()
        self._applied_periods.clear()
        self._cancel_pending_transition()
        await self._async_apply_active_periods(now, cause="temporary_override_cleared")
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
