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
    from .runtime import ScheduleRuntime
    from homeassistant.exceptions import ConfigEntryError
    from .services import async_register_services
    from .storage import ScheduleStorage
    from .panel import async_sync_panel
    from .websocket_api import async_register_commands
    from .zeal import async_discover_zeal_rooms

    storage = ScheduleStorage(hass, entry.entry_id)
    configuration = await storage.async_load()
    temperature_unit = str(hass.config.units.temperature_unit)
    if configuration.temperature_unit is None:
        configuration = configuration.with_temperature_unit(temperature_unit)
        await storage.async_save(configuration)
    elif configuration.temperature_unit != temperature_unit:
        raise ConfigEntryError(
            "Home Assistant's temperature unit changed from "
            f"{configuration.temperature_unit} to {temperature_unit}. Remove and re-add "
            "Visual Climate Scheduler to create schedules in the new unit."
        )
    runtime = ScheduleRuntime(hass)
    await runtime.async_start(configuration)

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "configuration": configuration,
        "storage": storage,
        "runtime": runtime,
        # Optional Block 2 context. It is runtime-only and never stored with schedules.
        "zeal_discovery": await async_discover_zeal_rooms(hass),
    }
    await async_register_services(hass)
    async_register_commands(hass)
    await async_sync_panel(hass, bool(configuration.settings.get("show_panel", False)))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Visual Climate Scheduler config entry."""
    entry_data = hass.data[DOMAIN].pop(entry.entry_id, None)
    if entry_data is not None:
        await entry_data["runtime"].async_stop()
    if not hass.data[DOMAIN]:
        hass.data.pop(DOMAIN)
        hass.services.async_remove(DOMAIN, "set_zeal_room_temperature")
        from .panel import async_remove_panel

        await async_remove_panel(hass)
    return True
