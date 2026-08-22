"""Small admin-only WebSocket API used by the scheduler editor panel."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback

from .configuration import async_save_configuration
from .const import DOMAIN
from .editor import update_room_days

_REGISTERED = f"{DOMAIN}_websocket_registered"


def async_register_commands(hass: HomeAssistant) -> None:
    """Register once because the integration intentionally has one config entry."""
    if hass.data.get(_REGISTERED):
        return
    websocket_api.async_register_command(hass, ws_get_configuration)
    websocket_api.async_register_command(hass, ws_update_room_days)
    hass.data[_REGISTERED] = True


def _entry_data(hass: HomeAssistant) -> tuple[str, dict[str, Any]] | None:
    entries = hass.data.get(DOMAIN, {})
    return next(iter(entries.items()), None)


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): "visual_climate_scheduler/get_configuration"})
@callback
def ws_get_configuration(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """Return the current, human-readable configuration for the editor."""
    if (entry := _entry_data(hass)) is None:
        connection.send_error(msg["id"], websocket_api.ERR_NOT_FOUND, "Scheduler is not loaded")
        return
    _, entry_data = entry
    connection.send_result(msg["id"], entry_data["configuration"].to_dict())


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): "visual_climate_scheduler/update_room_days",
        vol.Required("room_id"): str,
        vol.Required("days"): dict,
    }
)
@websocket_api.async_response
async def ws_update_room_days(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """Validate and save one room or zone's seven independent daily lists."""
    if (entry := _entry_data(hass)) is None:
        connection.send_error(msg["id"], websocket_api.ERR_NOT_FOUND, "Scheduler is not loaded")
        return
    entry_id, entry_data = entry
    try:
        updated_configuration = update_room_days(
            entry_data["configuration"], msg["room_id"], msg["days"]
        )
    except KeyError:
        connection.send_error(msg["id"], websocket_api.ERR_NOT_FOUND, "Unknown room or zone")
        return
    except ValueError as err:
        connection.send_error(msg["id"], websocket_api.ERR_INVALID_FORMAT, str(err))
        return
    await async_save_configuration(hass, entry_id, updated_configuration)
    connection.send_result(msg["id"], updated_configuration.to_dict())
