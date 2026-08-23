"""Diagnostics for the Visual Climate Scheduler config entry."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, object]:
    """Return the non-sensitive integration identity for support."""
    return {"config_entry_id": entry.entry_id}
