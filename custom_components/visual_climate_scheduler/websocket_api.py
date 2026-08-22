"""Small admin-only WebSocket API used by the scheduler editor panel."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import area_registry as ar
from homeassistant.helpers import entity_registry as er

from .configuration import async_save_configuration
from .const import CONF_SHOW_PANEL, DOMAIN
from .editor import copy_room_schedule, update_room_days
from .models import ScheduleConfiguration
from .panel import async_sync_panel
from .rooms import add_scheduled_space, remove_scheduled_space, update_scheduled_space

_REGISTERED = f"{DOMAIN}_websocket_registered"


def async_register_commands(hass: HomeAssistant) -> None:
    """Register once because the integration intentionally has one config entry."""
    if hass.data.get(_REGISTERED):
        return
    websocket_api.async_register_command(hass, ws_get_configuration)
    websocket_api.async_register_command(hass, ws_update_room_days)
    websocket_api.async_register_command(hass, ws_copy_room_schedule)
    websocket_api.async_register_command(hass, ws_save_scheduled_space)
    websocket_api.async_register_command(hass, ws_remove_scheduled_space)
    websocket_api.async_register_command(hass, ws_set_sidebar_shortcut)
    websocket_api.async_register_command(hass, ws_get_quick_change)
    websocket_api.async_register_command(hass, ws_set_temporary_override)
    websocket_api.async_register_command(hass, ws_clear_temporary_override)
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
        vol.Required("type"): "visual_climate_scheduler/save_scheduled_space",
        vol.Optional("room_id"): str,
        vol.Required("name"): str,
        vol.Optional("area_id"): vol.Any(str, None),
        vol.Required("climate_entity_ids"): [str],
    }
)
@websocket_api.async_response
async def ws_save_scheduled_space(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """Create or modify one scheduled space from the integration panel."""
    if (entry := _entry_data(hass)) is None:
        connection.send_error(msg["id"], websocket_api.ERR_NOT_FOUND, "Scheduler is not loaded")
        return
    entry_id, entry_data = entry
    name = msg["name"].strip()
    climate_entity_ids = tuple(msg["climate_entity_ids"])
    if not name:
        connection.send_error(msg["id"], websocket_api.ERR_INVALID_FORMAT, "A room or zone name is required")
        return
    if not climate_entity_ids:
        connection.send_error(msg["id"], websocket_api.ERR_INVALID_FORMAT, "Select at least one climate thermostat")
        return
    if any(not entity_id.startswith("climate.") for entity_id in climate_entity_ids):
        connection.send_error(msg["id"], websocket_api.ERR_INVALID_FORMAT, "Targets must be climate entities")
        return
    area_id = msg.get("area_id") or None
    if area_id is not None and ar.async_get(hass).async_get_area(area_id) is None:
        connection.send_error(msg["id"], websocket_api.ERR_INVALID_FORMAT, "Unknown Home Assistant Area ID")
        return
    entity_registry = er.async_get(hass)
    if any(entity_registry.async_get(entity_id) is None for entity_id in climate_entity_ids):
        connection.send_error(msg["id"], websocket_api.ERR_INVALID_FORMAT, "Unknown climate thermostat")
        return
    try:
        if room_id := msg.get("room_id"):
            updated_configuration = update_scheduled_space(
                entry_data["configuration"], room_id, name=name, area_id=area_id,
                climate_entity_ids=climate_entity_ids,
            )
        else:
            updated_configuration = add_scheduled_space(
                entry_data["configuration"], name=name, area_id=area_id,
                climate_entity_ids=climate_entity_ids,
            )
    except ValueError as err:
        connection.send_error(msg["id"], websocket_api.ERR_INVALID_FORMAT, str(err))
        return
    await async_save_configuration(hass, entry_id, updated_configuration)
    connection.send_result(msg["id"], updated_configuration.to_dict())


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): "visual_climate_scheduler/remove_scheduled_space",
        vol.Required("room_id"): str,
    }
)
@websocket_api.async_response
async def ws_remove_scheduled_space(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """Remove one scheduled space and its seven saved daily schedules."""
    if (entry := _entry_data(hass)) is None:
        connection.send_error(msg["id"], websocket_api.ERR_NOT_FOUND, "Scheduler is not loaded")
        return
    entry_id, entry_data = entry
    try:
        updated_configuration = remove_scheduled_space(entry_data["configuration"], msg["room_id"])
    except ValueError as err:
        connection.send_error(msg["id"], websocket_api.ERR_NOT_FOUND, str(err))
        return
    await async_save_configuration(hass, entry_id, updated_configuration)
    connection.send_result(msg["id"], updated_configuration.to_dict())


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): "visual_climate_scheduler/set_sidebar_shortcut",
        vol.Required("show_panel"): bool,
    }
)
@websocket_api.async_response
async def ws_set_sidebar_shortcut(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """Persist the optional sidebar shortcut without changing schedules."""
    if (entry := _entry_data(hass)) is None:
        connection.send_error(msg["id"], websocket_api.ERR_NOT_FOUND, "Scheduler is not loaded")
        return
    entry_id, entry_data = entry
    configuration = entry_data["configuration"]
    updated_configuration = ScheduleConfiguration(
        rooms=configuration.rooms,
        settings={**configuration.settings, CONF_SHOW_PANEL: msg["show_panel"]},
        temperature_unit=configuration.temperature_unit,
    )
    await async_save_configuration(hass, entry_id, updated_configuration)
    await async_sync_panel(hass, msg["show_panel"])
    connection.send_result(msg["id"], updated_configuration.to_dict())


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


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): "visual_climate_scheduler/copy_room_schedule",
        vol.Required("source_room_id"): str,
        vol.Required("target_room_ids"): [str],
        vol.Required("source_days"): dict,
    }
)
@websocket_api.async_response
async def ws_copy_room_schedule(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """Copy the current source editor state to selected destination spaces."""
    if (entry := _entry_data(hass)) is None:
        connection.send_error(msg["id"], websocket_api.ERR_NOT_FOUND, "Scheduler is not loaded")
        return
    entry_id, entry_data = entry
    try:
        updated_configuration = copy_room_schedule(
            entry_data["configuration"],
            msg["source_room_id"],
            msg["target_room_ids"],
            msg["source_days"],
        )
    except KeyError:
        connection.send_error(msg["id"], websocket_api.ERR_NOT_FOUND, "Unknown room or zone")
        return
    except ValueError as err:
        connection.send_error(msg["id"], websocket_api.ERR_INVALID_FORMAT, str(err))
        return
    await async_save_configuration(hass, entry_id, updated_configuration)
    connection.send_result(msg["id"], updated_configuration.to_dict())


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): "visual_climate_scheduler/get_quick_change"})
@callback
def ws_get_quick_change(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    if (entry := _entry_data(hass)) is None:
        connection.send_error(msg["id"], websocket_api.ERR_NOT_FOUND, "Scheduler is not loaded")
        return
    _, entry_data = entry
    connection.send_result(msg["id"], entry_data["runtime"].quick_change_state())


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): "visual_climate_scheduler/set_temporary_override", vol.Required("room_ids"): [str], vol.Required("duration"): vol.In(["2h", "4h", "next_change"]), vol.Required("operation"): vol.In(["delta", "temperature"]), vol.Required("value"): vol.Coerce(float)})
@websocket_api.async_response
async def ws_set_temporary_override(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    if (entry := _entry_data(hass)) is None:
        connection.send_error(msg["id"], websocket_api.ERR_NOT_FOUND, "Scheduler is not loaded")
        return
    _, entry_data = entry
    try:
        await entry_data["runtime"].async_set_temporary_override(msg["room_ids"], duration=msg["duration"], operation=msg["operation"], value=msg["value"])
    except ValueError as err:
        connection.send_error(msg["id"], websocket_api.ERR_INVALID_FORMAT, str(err))
        return
    connection.send_result(msg["id"], entry_data["runtime"].quick_change_state())


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): "visual_climate_scheduler/clear_temporary_override", vol.Required("room_id"): str})
@websocket_api.async_response
async def ws_clear_temporary_override(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    if (entry := _entry_data(hass)) is None:
        connection.send_error(msg["id"], websocket_api.ERR_NOT_FOUND, "Scheduler is not loaded")
        return
    _, entry_data = entry
    await entry_data["runtime"].async_clear_temporary_override(msg["room_id"])
    connection.send_result(msg["id"], entry_data["runtime"].quick_change_state())
