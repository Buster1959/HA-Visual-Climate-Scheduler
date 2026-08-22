"""Home Assistant-independent ZEAL discovery contract models."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class ZealRoom:
    """A ZEAL room and its single scheduling target."""

    zone_id: str
    zone_name: str
    room_id: str
    name: str
    thermostat_entity_id: str
    target_temperature: float | None
    hvac_mode: str | None
    registered_with_coordinator: bool | None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def rooms_from_zeal_snapshot(snapshot: Mapping[str, Any]) -> tuple[ZealRoom, ...]:
    """Parse ZEAL's documented diagnostics/public-snapshot shape.

    Missing or malformed individual records are ignored, because discovery must not
    make another integration fail to load.
    """
    rooms: list[ZealRoom] = []
    for zone in snapshot.get("zones", []):
        if not isinstance(zone, Mapping):
            continue
        zone_id, zone_name = zone.get("zone_id"), zone.get("name")
        if not isinstance(zone_id, str) or not isinstance(zone_name, str):
            continue
        for room in zone.get("rooms", []):
            if not isinstance(room, Mapping):
                continue
            thermostat = room.get("thermostat")
            if not isinstance(thermostat, Mapping):
                continue
            room_id, room_name, entity_id = room.get("room_id"), room.get("name"), thermostat.get("entity_id")
            if not all(isinstance(value, str) and value for value in (room_id, room_name, entity_id)):
                continue
            temperature = thermostat.get("target_temperature")
            rooms.append(
                ZealRoom(
                    zone_id=zone_id,
                    zone_name=zone_name,
                    room_id=room_id,
                    name=room_name,
                    thermostat_entity_id=entity_id,
                    target_temperature=float(temperature) if isinstance(temperature, (int, float)) else None,
                    hvac_mode=thermostat.get("hvac_mode") if isinstance(thermostat.get("hvac_mode"), str) else None,
                    registered_with_coordinator=thermostat.get("registered_with_coordinator") if isinstance(thermostat.get("registered_with_coordinator"), bool) else None,
                )
            )
    return tuple(rooms)
