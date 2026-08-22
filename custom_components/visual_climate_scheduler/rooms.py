"""Pure configuration operations for scheduled rooms and zones."""

from __future__ import annotations

import re
from typing import Iterable

from .models import RoomSchedule, ScheduleConfiguration, WEEKDAYS


def _room_id(name: str, existing_ids: Iterable[str]) -> str:
    """Make a readable, stable-at-creation identifier without Home Assistant helpers."""
    base = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_") or "scheduled_space"
    existing = set(existing_ids)
    if base not in existing:
        return base
    index = 2
    while f"{base}_{index}" in existing:
        index += 1
    return f"{base}_{index}"


def add_scheduled_space(
    configuration: ScheduleConfiguration,
    *,
    name: str,
    climate_entity_ids: Iterable[str],
    area_id: str | None = None,
) -> ScheduleConfiguration:
    """Add one independently scheduled room or zone.

    A space can target any non-empty group of climate entities. Targets may not
    appear in two spaces because that would create competing schedules.
    """
    entity_ids = tuple(climate_entity_ids)
    used_targets = {
        entity_id
        for room in configuration.rooms.values()
        for entity_id in room.climate_entity_ids
    }
    overlap = used_targets.intersection(entity_ids)
    if overlap:
        raise ValueError(f"climate target is already scheduled: {sorted(overlap)[0]}")
    room_id = _room_id(name, configuration.rooms)
    room = RoomSchedule(
        id=room_id,
        name=name,
        area_id=area_id,
        climate_entity_ids=entity_ids,
        days={day: () for day in WEEKDAYS},
    )
    return ScheduleConfiguration(
        rooms={**configuration.rooms, room.id: room},
        settings=configuration.settings,
    )


def remove_scheduled_space(
    configuration: ScheduleConfiguration, room_id: str
) -> ScheduleConfiguration:
    """Remove a scheduled space without changing the remaining schedules."""
    if room_id not in configuration.rooms:
        raise ValueError(f"unknown scheduled space: {room_id}")
    rooms = dict(configuration.rooms)
    rooms.pop(room_id)
    return ScheduleConfiguration(rooms=rooms, settings=configuration.settings)


def update_scheduled_space(
    configuration: ScheduleConfiguration,
    room_id: str,
    *,
    name: str,
    climate_entity_ids: Iterable[str],
    area_id: str | None = None,
) -> ScheduleConfiguration:
    """Update a space's details and targets without replacing its schedule.

    The room ID remains stable when its display name changes. Existing targets
    may stay assigned to this space, but may not be moved in from another one.
    """
    existing_room = configuration.rooms.get(room_id)
    if existing_room is None:
        raise ValueError(f"unknown scheduled space: {room_id}")
    entity_ids = tuple(climate_entity_ids)
    used_elsewhere = {
        entity_id
        for other_room_id, room in configuration.rooms.items()
        if other_room_id != room_id
        for entity_id in room.climate_entity_ids
    }
    overlap = used_elsewhere.intersection(entity_ids)
    if overlap:
        raise ValueError(f"climate target is already scheduled: {sorted(overlap)[0]}")
    updated_room = RoomSchedule(
        id=existing_room.id,
        name=name,
        area_id=area_id,
        climate_entity_ids=entity_ids,
        days=existing_room.days,
    )
    return ScheduleConfiguration(
        rooms={**configuration.rooms, room_id: updated_room}, settings=configuration.settings
    )
