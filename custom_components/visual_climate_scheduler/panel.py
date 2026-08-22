"""Register the scheduler editor and optionally expose it in the sidebar."""

from __future__ import annotations

from pathlib import Path

from homeassistant.components import frontend, panel_custom
from homeassistant.components.frontend import async_panel_exists
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PANEL_COMPONENT, PANEL_STATIC_URL, PANEL_URL_PATH

_STATIC_REGISTERED = f"{DOMAIN}_panel_static_registered"


async def async_sync_panel(hass: HomeAssistant, visible: bool) -> None:
    """Register the editor route and apply its optional sidebar preference.

    The panel always remains available from the integration's Configure button.
    ``visible`` only controls whether Home Assistant also shows it in the
    sidebar; it never changes schedules or runtime state.
    """
    if async_panel_exists(hass, PANEL_URL_PATH):
        # Home Assistant panel metadata is immutable after registration. Remove
        # and re-register so a changed sidebar preference takes effect.
        frontend.async_remove_panel(hass, PANEL_URL_PATH)
    if not hass.data.get(_STATIC_REGISTERED):
        await hass.http.async_register_static_paths(
            [StaticPathConfig(PANEL_STATIC_URL, Path(__file__).parent / "frontend", False)]
        )
        hass.data[_STATIC_REGISTERED] = True
    await panel_custom.async_register_panel(
        hass=hass,
        frontend_url_path=PANEL_URL_PATH,
        webcomponent_name=PANEL_COMPONENT,
        module_url=f"{PANEL_STATIC_URL}/visual-climate-scheduler-panel.js",
        sidebar_title="Climate Scheduler" if visible else None,
        sidebar_icon="mdi:calendar-clock" if visible else None,
        require_admin=True,
        config_panel_domain=DOMAIN,
    )


async def async_remove_panel(hass: HomeAssistant) -> None:
    """Remove the editor route when the final integration entry unloads."""
    if async_panel_exists(hass, PANEL_URL_PATH):
        frontend.async_remove_panel(hass, PANEL_URL_PATH)
