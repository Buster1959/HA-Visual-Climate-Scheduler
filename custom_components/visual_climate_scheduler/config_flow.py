"""Config and room-setup flows for Visual Climate Scheduler."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components.climate.const import DOMAIN as CLIMATE_DOMAIN
from homeassistant.core import callback
from homeassistant.helpers import area_registry as ar
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.selector import selector

from .const import (
    CONF_AREA_ID,
    CONF_CLIMATE_ENTITY_IDS,
    CONF_ROOM_ID,
    CONF_ROOM_NAME,
    CONF_SHOW_PANEL,
    DOMAIN,
    INTEGRATION_TITLE,
)
from .configuration import async_save_configuration
from .panel import async_sync_panel
from .rooms import add_scheduled_space, remove_scheduled_space


class VisualClimateSchedulerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the scheduler's single integration config entry."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Create the initially empty scheduler configuration entry."""
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        if user_input is not None:
            return self.async_create_entry(title=INTEGRATION_TITLE, data={})

        return self.async_show_form(step_id="user", data_schema=vol.Schema({}))

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> "VisualClimateSchedulerOptionsFlow":
        """Expose room and zone setup from the integration's Configure button."""
        return VisualClimateSchedulerOptionsFlow()


class VisualClimateSchedulerOptionsFlow(config_entries.OptionsFlow):
    """Add or remove independently scheduled spaces and their climate targets."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Present the small room-setup menu."""
        return self.async_show_menu(
            step_id="init",
            menu_options=["add_scheduled_space", "remove_scheduled_space", "panel_settings"],
        )

    async def async_step_add_scheduled_space(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Add a named room or zone with one or more thermostat targets."""
        errors: dict[str, str] = {}
        if user_input is not None:
            name = user_input[CONF_ROOM_NAME].strip()
            area_id = user_input.get(CONF_AREA_ID)
            entity_ids = tuple(user_input[CONF_CLIMATE_ENTITY_IDS])
            if not name:
                errors[CONF_ROOM_NAME] = "invalid_name"
            if not entity_ids:
                errors[CONF_CLIMATE_ENTITY_IDS] = "no_climate_entities"
            if area_id is not None and ar.async_get(self.hass).async_get_area(area_id) is None:
                errors[CONF_AREA_ID] = "unknown_area"
            entity_registry = er.async_get(self.hass)
            missing = [
                entity_id for entity_id in entity_ids if entity_registry.async_get(entity_id) is None
            ]
            if missing:
                errors[CONF_CLIMATE_ENTITY_IDS] = "unknown_climate_entity"
            if not errors:
                entry_data = self.hass.data[DOMAIN][self.config_entry.entry_id]
                try:
                    configuration = add_scheduled_space(
                        entry_data["configuration"],
                        name=name,
                        area_id=area_id,
                        climate_entity_ids=entity_ids,
                    )
                except ValueError:
                    errors["base"] = "duplicate_climate_entity"
                else:
                    await async_save_configuration(self.hass, self.config_entry.entry_id, configuration)
                    return self.async_create_entry(title="", data={})

        return self.async_show_form(
            step_id="add_scheduled_space",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ROOM_NAME): vol.All(str, vol.Length(min=1)),
                    vol.Optional(CONF_AREA_ID): selector({"area": {}}),
                    vol.Required(CONF_CLIMATE_ENTITY_IDS): selector(
                        {"entity": {"filter": {"domain": CLIMATE_DOMAIN}, "multiple": True}}
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_remove_scheduled_space(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Remove a room or zone and its schedule configuration."""
        entry_data = self.hass.data[DOMAIN][self.config_entry.entry_id]
        configuration = entry_data["configuration"]
        if not configuration.rooms:
            return self.async_abort(reason="no_scheduled_spaces")
        if user_input is not None:
            configuration = remove_scheduled_space(configuration, user_input[CONF_ROOM_ID])
            await async_save_configuration(self.hass, self.config_entry.entry_id, configuration)
            return self.async_create_entry(title="", data={})

        choices = {
            room_id: f"{room.name} ({', '.join(room.climate_entity_ids)})"
            for room_id, room in configuration.rooms.items()
        }
        return self.async_show_form(
            step_id="remove_scheduled_space",
            data_schema=vol.Schema({vol.Required(CONF_ROOM_ID): vol.In(choices)}),
        )

    async def async_step_panel_settings(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Let the user show or hide the full schedule editor in the sidebar."""
        entry_data = self.hass.data[DOMAIN][self.config_entry.entry_id]
        configuration = entry_data["configuration"]
        if user_input is not None:
            settings = {**configuration.settings, CONF_SHOW_PANEL: user_input[CONF_SHOW_PANEL]}
            updated_configuration = type(configuration)(
                rooms=configuration.rooms, settings=settings
            )
            await async_save_configuration(
                self.hass, self.config_entry.entry_id, updated_configuration
            )
            await async_sync_panel(self.hass, user_input[CONF_SHOW_PANEL])
            return self.async_create_entry(title="", data={})
        return self.async_show_form(
            step_id="panel_settings",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_SHOW_PANEL,
                        default=bool(configuration.settings.get(CONF_SHOW_PANEL, False)),
                    ): selector({"boolean": {}})
                }
            ),
        )
