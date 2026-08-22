"""Home Assistant setup for Visual Climate Scheduler."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .const import DOMAIN

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Visual Climate Scheduler from a config entry."""
    # Keep the schedule model importable for isolated validation and migrations.
    from .services import async_register_services
    from .storage import ScheduleStorage
    from .zeal import async_discover_zeal_rooms

    storage = ScheduleStorage(hass, entry.entry_id)
    configuration = await storage.async_load()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "configuration": configuration,
        "storage": storage,
        # Optional Block 2 context. It is runtime-only and never stored with schedules.
        "zeal_discovery": await async_discover_zeal_rooms(hass),
    }
    await async_register_services(hass)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Visual Climate Scheduler config entry."""
    hass.data[DOMAIN].pop(entry.entry_id, None)
    if not hass.data[DOMAIN]:
        hass.data.pop(DOMAIN)
        hass.services.async_remove(DOMAIN, "set_zeal_room_temperature")
    return True
