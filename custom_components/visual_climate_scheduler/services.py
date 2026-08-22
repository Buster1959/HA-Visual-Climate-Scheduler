"""Explicit, narrowly scoped ZEAL climate control action."""

from __future__ import annotations

import voluptuous as vol

from homeassistant.components.climate.const import DOMAIN as CLIMATE_DOMAIN
from homeassistant.const import ATTR_ENTITY_ID, ATTR_TEMPERATURE
from homeassistant.core import HomeAssistant, ServiceCall

from .const import DOMAIN, SERVICE_SET_ZEAL_ROOM_TEMPERATURE
from .zeal import async_discover_zeal_rooms

SERVICE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): vol.All(str, vol.Match(r"^climate\.")),
        vol.Required(ATTR_TEMPERATURE): vol.Coerce(float),
    }
)


async def async_set_zeal_room_temperature(call: ServiceCall) -> None:
    """Set one discovered ZEAL room thermostat, never its underlying TRVs."""
    discovery = await async_discover_zeal_rooms(call.hass)
    room = next((candidate for candidate in discovery.rooms if candidate.thermostat_entity_id == call.data[ATTR_ENTITY_ID]), None)
    if room is None:
        raise vol.Invalid("Entity is not a discovered ZEAL room thermostat; refusing to target it")

    await call.hass.services.async_call(
        CLIMATE_DOMAIN,
        "set_temperature",
        {
            ATTR_ENTITY_ID: room.thermostat_entity_id,
            ATTR_TEMPERATURE: call.data[ATTR_TEMPERATURE],
        },
        blocking=True,
    )


async def async_register_services(hass: HomeAssistant) -> None:
    """Register the one explicit Block 2 test/control action."""
    if not hass.services.has_service(DOMAIN, SERVICE_SET_ZEAL_ROOM_TEMPERATURE):
        hass.services.async_register(
            DOMAIN,
            SERVICE_SET_ZEAL_ROOM_TEMPERATURE,
            async_set_zeal_room_temperature,
            schema=SERVICE_SCHEMA,
        )
