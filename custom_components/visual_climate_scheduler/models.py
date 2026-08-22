"""Versioned, JSON-serialisable V1 schedule configuration models.

This module is deliberately independent of Home Assistant runtime objects. It
defines the durable schedule contract only; entity availability, active periods,
overrides and schedule execution belong to runtime layers added later.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import math
import re
from typing import Any, Iterable, Mapping

SCHEMA_VERSION = 1
WEEKDAYS = (
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
)

_TIME_PATTERN = re.compile(r"^(?:[01][0-9]|2[0-3]):[0-5][0-9]$")


def _require_string(value: Any, field_name: str) -> str:
    """Return a required string without silently changing user data."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def validate_time(value: Any) -> str:
    """Validate and return an exact, zero-padded 24-hour ``HH:MM`` value."""
    value = _require_string(value, "time")
    if not _TIME_PATTERN.fullmatch(value):
        raise ValueError("time must use an exact 24-hour HH:MM format")
    return value


def _json_object_copy(value: Mapping[str, Any], field_name: str) -> dict[str, Any]:
    """Validate JSON compatibility and return a detached primitive-only copy."""
    if not isinstance(value, Mapping):
        raise ValueError(f"{field_name} must be an object")
    try:
        copied = json.loads(json.dumps(dict(value), allow_nan=False))
    except (TypeError, ValueError) as err:
        raise ValueError(f"{field_name} must contain JSON-serialisable data") from err
    if not isinstance(copied, dict):
        raise ValueError(f"{field_name} must be an object")
    return copied


@dataclass(frozen=True, slots=True)
class SchedulePeriod:
    """One named setpoint change within a day."""

    id: str
    friendly_name: str
    name: str
    time: str
    temperature: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _require_string(self.id, "period.id"))
        object.__setattr__(
            self, "friendly_name", _require_string(self.friendly_name, "period.friendly_name")
        )
        object.__setattr__(self, "name", _require_string(self.name, "period.name"))
        object.__setattr__(self, "time", validate_time(self.time))
        if isinstance(self.temperature, bool) or not isinstance(self.temperature, (int, float)):
            raise ValueError("period.temperature must be a number")
        if not math.isfinite(float(self.temperature)):
            raise ValueError("period.temperature must be finite")
        object.__setattr__(self, "temperature", float(self.temperature))

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "SchedulePeriod":
        if not isinstance(value, Mapping):
            raise ValueError("schedule period must be an object")
        return cls(
            id=value.get("id"),
            friendly_name=value.get("friendly_name"),
            name=value.get("name"),
            time=value.get("time"),
            temperature=value.get("temperature"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "friendly_name": self.friendly_name,
            "name": self.name,
            "time": self.time,
            "temperature": self.temperature,
        }


def validate_periods(day: str, periods: Iterable[SchedulePeriod]) -> tuple[SchedulePeriod, ...]:
    """Validate one day without imposing the initial UI's four-period limit."""
    if day not in WEEKDAYS:
        raise ValueError(f"unknown weekday: {day}")
    normalized = tuple(periods)
    if any(not isinstance(period, SchedulePeriod) for period in normalized):
        raise ValueError(f"room.days.{day} must contain schedule periods")
    if len({period.id for period in normalized}) != len(normalized):
        raise ValueError(f"room.days.{day} contains duplicate period ids")
    if len({period.time for period in normalized}) != len(normalized):
        raise ValueError(f"room.days.{day} contains duplicate period times")
    if tuple(period.time for period in normalized) != tuple(sorted(period.time for period in normalized)):
        raise ValueError(f"room.days.{day} must be ordered by time")
    return normalized


def copy_periods(periods: Iterable[SchedulePeriod]) -> tuple[SchedulePeriod, ...]:
    """Return a detached logical copy, retaining each period's stable identity."""
    return tuple(SchedulePeriod.from_dict(period.to_dict()) for period in periods)


@dataclass(frozen=True, slots=True)
class RoomSchedule:
    """Persisted schedule and HA references for one configured room."""

    id: str
    name: str
    area_id: str
    climate_entity_id: str
    days: Mapping[str, Iterable[SchedulePeriod]]

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _require_string(self.id, "room.id"))
        object.__setattr__(self, "name", _require_string(self.name, "room.name"))
        object.__setattr__(self, "area_id", _require_string(self.area_id, "room.area_id"))
        object.__setattr__(
            self,
            "climate_entity_id",
            _require_string(self.climate_entity_id, "room.climate_entity_id"),
        )
        if set(self.days) != set(WEEKDAYS):
            raise ValueError("room.days must contain exactly monday through sunday")
        object.__setattr__(
            self,
            "days",
            {day: validate_periods(day, self.days[day]) for day in WEEKDAYS},
        )

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "RoomSchedule":
        if not isinstance(value, Mapping):
            raise ValueError("room must be an object")
        raw_days = value.get("days")
        if not isinstance(raw_days, Mapping):
            raise ValueError("room.days must be an object")
        days: dict[str, tuple[SchedulePeriod, ...]] = {}
        for day, raw_periods in raw_days.items():
            if not isinstance(raw_periods, list):
                raise ValueError(f"room.days.{day} must be a list")
            days[day] = tuple(SchedulePeriod.from_dict(period) for period in raw_periods)
        return cls(
            id=value.get("id"),
            name=value.get("name"),
            area_id=value.get("area_id"),
            climate_entity_id=value.get("climate_entity_id"),
            days=days,
        )

    def with_days_copied(self, source_day: str, target_days: Iterable[str]) -> "RoomSchedule":
        """Copy a day to explicitly selected, independent day lists.

        IDs are deliberately retained: a copied schedule contains the same logical
        periods but its day collection is detached and can later diverge.
        """
        if source_day not in WEEKDAYS:
            raise ValueError(f"unknown weekday: {source_day}")
        targets = tuple(target_days)
        if len(set(targets)) != len(targets) or any(day not in WEEKDAYS for day in targets):
            raise ValueError("target_days must contain unique valid weekdays")
        days = {day: copy_periods(periods) for day, periods in self.days.items()}
        for day in targets:
            days[day] = copy_periods(self.days[source_day])
        return RoomSchedule(
            id=self.id,
            name=self.name,
            area_id=self.area_id,
            climate_entity_id=self.climate_entity_id,
            days=days,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "area_id": self.area_id,
            "climate_entity_id": self.climate_entity_id,
            "days": {
                day: [period.to_dict() for period in self.days[day]] for day in WEEKDAYS
            },
        }


@dataclass(frozen=True, slots=True)
class ScheduleConfiguration:
    """Complete persisted V1 schedule configuration for one config entry."""

    version: int = SCHEMA_VERSION
    rooms: Mapping[str, RoomSchedule] = field(default_factory=dict)
    settings: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if isinstance(self.version, bool) or self.version != SCHEMA_VERSION:
            raise ValueError(f"unsupported schedule configuration version: {self.version}")
        normalized_rooms = dict(self.rooms)
        if any(not isinstance(room, RoomSchedule) for room in normalized_rooms.values()):
            raise ValueError("configuration.rooms must contain room schedules")
        if any(room_id != room.id for room_id, room in normalized_rooms.items()):
            raise ValueError("configuration room keys must match room.id")
        object.__setattr__(self, "rooms", normalized_rooms)
        object.__setattr__(self, "settings", _json_object_copy(self.settings, "configuration.settings"))

    @classmethod
    def empty(cls) -> "ScheduleConfiguration":
        """Return a valid empty configuration for a new config entry."""
        return cls()

    @staticmethod
    def migrate_dict(value: Mapping[str, Any]) -> dict[str, Any]:
        """Migrate a stored document to the current schema.

        Version 0 was the pre-versioned prototype shape. Its fields already match
        V1, so migration makes version 1 explicit. Future migrations belong here.
        """
        if not isinstance(value, Mapping):
            raise ValueError("schedule configuration must be an object")
        migrated = _json_object_copy(value, "schedule configuration")
        version = migrated.get("version", 0)
        if isinstance(version, bool) or not isinstance(version, int):
            raise ValueError("schedule configuration version must be an integer")
        if version == 0:
            migrated["version"] = SCHEMA_VERSION
            return migrated
        if version == SCHEMA_VERSION:
            return migrated
        raise ValueError(f"unsupported schedule configuration version: {version}")

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "ScheduleConfiguration":
        value = cls.migrate_dict(value)
        raw_rooms = value.get("rooms", {})
        if not isinstance(raw_rooms, Mapping):
            raise ValueError("configuration.rooms must be an object")
        raw_settings = value.get("settings", {})
        if not isinstance(raw_settings, Mapping):
            raise ValueError("configuration.settings must be an object")
        return cls(
            version=value["version"],
            rooms={room_id: RoomSchedule.from_dict(room) for room_id, room in raw_rooms.items()},
            settings=raw_settings,
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a detached document containing only JSON-compatible primitives."""
        return {
            "version": self.version,
            "rooms": {room_id: room.to_dict() for room_id, room in self.rooms.items()},
            "settings": _json_object_copy(self.settings, "configuration.settings"),
        }
