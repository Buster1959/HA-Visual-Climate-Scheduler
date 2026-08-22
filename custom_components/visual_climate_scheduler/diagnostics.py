"""Diagnostics for the Visual Climate Scheduler config entry."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .zeal import async_discover_zeal_rooms


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, object]:
    """Return read-only ZEAL discovery data for support and Block 2 testing."""
    discovery = await async_discover_zeal_rooms(hass)
    return {"config_entry_id": entry.entry_id, "zeal_discovery": discovery.as_dict()}
