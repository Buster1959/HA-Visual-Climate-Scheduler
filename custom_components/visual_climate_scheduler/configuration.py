"""Shared persistence/update operation for the live scheduler configuration."""

from __future__ import annotations

from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .models import ScheduleConfiguration


async def async_save_configuration(
    hass: HomeAssistant, entry_id: str, configuration: ScheduleConfiguration
) -> None:
    """Persist validated data, then make the running engine use it immediately."""
    entry_data = hass.data[DOMAIN][entry_id]
    await entry_data["storage"].async_save(configuration)
    entry_data["configuration"] = configuration
    await entry_data["runtime"].async_set_configuration(configuration)
