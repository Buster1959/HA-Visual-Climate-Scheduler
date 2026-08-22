"""Pure validation and update helpers for the schedule editor."""

from __future__ import annotations

from typing import Any, Mapping

from .models import RoomSchedule, ScheduleConfiguration, copy_periods


def update_room_days(
    configuration: ScheduleConfiguration, room_id: str, days: Mapping[str, Any]
) -> ScheduleConfiguration:
    """Return a new configuration with one room or zone's days replaced.

    Parsing through :class:`RoomSchedule` keeps the sidebar boundary subject to
    exactly the same validation, ordering, and JSON-safe model contract as
    stored data.  All targets and settings are retained unchanged.
    """
    room = configuration.rooms.get(room_id)
    if room is None:
        raise KeyError(room_id)
    raw_room = room.to_dict()
    raw_room["days"] = days
    updated_room = RoomSchedule.from_dict(raw_room)
    return ScheduleConfiguration(
        rooms={**configuration.rooms, updated_room.id: updated_room},
        settings=configuration.settings,
    )


def copy_room_schedule(
    configuration: ScheduleConfiguration,
    source_room_id: str,
    target_room_ids: list[str],
    source_days: Mapping[str, Any],
) -> ScheduleConfiguration:
    """Save the source editor state and copy its seven daily lists to rooms.

    A copy deliberately changes only ``days``. Every destination retains its
    own name, optional area and climate targets, while receiving detached daily
    collections with the source periods' stable IDs.
    """
    if not target_room_ids or len(set(target_room_ids)) != len(target_room_ids):
        raise ValueError("Select one or more different destination rooms or zones")
    if source_room_id in target_room_ids:
        raise ValueError("A room or zone cannot be copied to itself")

    updated = update_room_days(configuration, source_room_id, source_days)
    unknown_targets = [room_id for room_id in target_room_ids if room_id not in updated.rooms]
    if unknown_targets:
        raise KeyError(unknown_targets[0])

    source = updated.rooms[source_room_id]
    rooms = dict(updated.rooms)
    for room_id in target_room_ids:
        target = rooms[room_id]
        rooms[room_id] = RoomSchedule(
            id=target.id,
            name=target.name,
            area_id=target.area_id,
            climate_entity_ids=target.climate_entity_ids,
            days={day: copy_periods(source.days[day]) for day in source.days},
        )
    return ScheduleConfiguration(rooms=rooms, settings=updated.settings)
