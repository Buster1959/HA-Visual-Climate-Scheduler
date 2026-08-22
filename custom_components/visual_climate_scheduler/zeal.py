"""Read ZEAL room targets through Home Assistant's public entity boundary.

This module intentionally does not import ZEAL internals.  A ZEAL room thermostat
is a normal HA climate entity, so discovery is based on the entity registry and
all writes go through Home Assistant's ``climate.set_temperature`` action.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.const import ATTR_TEMPERATURE
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .const import ZEAL_DOMAIN
from .zeal_models import ZealRoom, rooms_from_zeal_snapshot


@dataclass(frozen=True, slots=True)
class ZealDiscovery:
    """The discovery result retained only as runtime state."""

    installed: bool
    source: str
    rooms: tuple[ZealRoom, ...]

    def as_dict(self) -> dict[str, Any]:
        """Return grouped, JSON-serialisable discovery data."""
        zones: dict[str, dict[str, Any]] = {}
        for room in self.rooms:
            zone = zones.setdefault(
                room.zone_id,
                {"zone_id": room.zone_id, "name": room.zone_name, "rooms": []},
            )
            zone["rooms"].append(room.as_dict())
        return {
            "zeal_installed": self.installed,
            "source": self.source,
            "zones": list(zones.values()),
        }


def _room_id(entity_id: str) -> str:
    """Produce a stable fallback room ID from a ZEAL thermostat entity ID."""
    object_id = entity_id.split(".", 1)[1]
    suffix = "_thermostat_zeal"
    return object_id[: -len(suffix)] if object_id.endswith(suffix) else object_id


async def async_discover_zeal_rooms(hass: HomeAssistant) -> ZealDiscovery:
    """Discover ZEAL room thermostat entities without depending on ZEAL internals.

    ZEAL's diagnostics contract is richer than the HA entity registry.  Until ZEAL
    publishes a dedicated cross-integration discovery API, its config-entry title
    is used as a fallback zone and the canonical ``*_thermostat_zeal`` entities
    are used as rooms. This remains completely functional for temperature control.
    """
    zeal_entries = hass.config_entries.async_entries(ZEAL_DOMAIN)
    if not zeal_entries:
        return ZealDiscovery(installed=False, source="not_installed", rooms=())

    # Optional, deliberately public bridge for a future ZEAL release.  It is not
    # required for the functional entity-registry fallback below.
    zeal_data = hass.data.get(ZEAL_DOMAIN, {})
    snapshot_provider = zeal_data.get("async_get_scheduler_snapshot") if isinstance(zeal_data, dict) else None
    if callable(snapshot_provider):
        snapshot = await snapshot_provider()
        if isinstance(snapshot, dict):
            rooms = rooms_from_zeal_snapshot(snapshot)
            return ZealDiscovery(installed=True, source="zeal_public_snapshot", rooms=rooms)

    entry_titles = {entry.entry_id: entry.title for entry in zeal_entries}
    registry = er.async_get(hass)
    rooms: list[ZealRoom] = []
    for entity in registry.entities.values():
        if (
            entity.domain != "climate"
            or entity.config_entry_id not in entry_titles
            or not entity.entity_id.endswith("_thermostat_zeal")
        ):
            continue
        state = hass.states.get(entity.entity_id)
        attributes = state.attributes if state else {}
        target = attributes.get(ATTR_TEMPERATURE)
        rooms.append(
            ZealRoom(
                zone_id=entity.config_entry_id,
                zone_name=entry_titles[entity.config_entry_id],
                room_id=_room_id(entity.entity_id),
                name=entity.name or _room_id(entity.entity_id).replace("_", " ").title(),
                thermostat_entity_id=entity.entity_id,
                target_temperature=float(target) if isinstance(target, (int, float)) else None,
                hvac_mode=state.state if state else None,
                registered_with_coordinator=None,
            )
        )
    return ZealDiscovery(installed=True, source="entity_registry_fallback", rooms=tuple(sorted(rooms, key=lambda room: room.thermostat_entity_id)))
