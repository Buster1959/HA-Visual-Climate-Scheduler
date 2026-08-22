"""Pure validation and update helpers for the schedule editor."""

from __future__ import annotations

from typing import Any, Mapping

from .models import RoomSchedule, ScheduleConfiguration


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
