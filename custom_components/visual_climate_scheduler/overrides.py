"""Pure temporary-override decisions, separate from persisted schedules."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import math
from typing import Literal

from .engine import active_period_at, next_transition_after
from .models import ScheduleConfiguration

OverrideDuration = Literal["2h", "4h", "next_change"]


@dataclass(frozen=True, slots=True)
class TemporaryOverride:
    """One short-lived effective target for one scheduled space."""

    room_id: str
    temperature: float
    expires_at: datetime
    duration: OverrideDuration

    def to_dict(self) -> dict[str, object]:
        return {
            "room_id": self.room_id,
            "temperature": self.temperature,
            "expires_at": self.expires_at.isoformat(),
            "duration": self.duration,
        }


def create_temporary_overrides(
    configuration: ScheduleConfiguration,
    room_ids: list[str],
    *,
    now: datetime,
    duration: OverrideDuration,
    value: float,
    operation: Literal["delta", "temperature"],
) -> list[TemporaryOverride]:
    """Resolve a batch action into independent overrides for each space."""
    if not room_ids or len(set(room_ids)) != len(room_ids):
        raise ValueError("Select one or more scheduled rooms or zones")
    if duration not in ("2h", "4h", "next_change"):
        raise ValueError("Choose a valid temporary duration")
    if operation not in ("delta", "temperature") or not math.isfinite(value):
        raise ValueError("Choose a valid temperature adjustment")
    overrides: list[TemporaryOverride] = []
    for room_id in room_ids:
        room = configuration.rooms.get(room_id)
        if room is None:
            raise ValueError(f"Unknown room or zone: {room_id}")
        active = active_period_at(room, now)
        if operation == "delta":
            if active is None:
                raise ValueError(f"{room.name} has no active scheduled target to adjust")
            target = active.period.temperature + value
        else:
            target = value
        if duration == "2h":
            expires_at = now + timedelta(hours=2)
        elif duration == "4h":
            expires_at = now + timedelta(hours=4)
        else:
            transition = next_transition_after(room, now)
            if transition is None:
                raise ValueError(f"{room.name} has no upcoming scheduled change")
            expires_at = transition.starts_at
        overrides.append(TemporaryOverride(room_id, float(target), expires_at, duration))
    return overrides
