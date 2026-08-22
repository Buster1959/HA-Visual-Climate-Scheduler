"""Home Assistant Store adapter for schedule configuration."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .const import STORAGE_KEY, STORAGE_VERSION
from .models import ScheduleConfiguration

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


class ScheduleStorage:
    """Persist the JSON schedule model without exposing Store to the model layer."""

    def __init__(self, hass: HomeAssistant, entry_id: str, store: Any | None = None) -> None:
        """Create the adapter, with an optional store injection for isolated tests."""
        if store is None:
            from homeassistant.helpers.storage import Store

            store = Store[dict[str, object]](hass, STORAGE_VERSION, f"{STORAGE_KEY}.{entry_id}")
        self._store = store

    async def async_load(self) -> ScheduleConfiguration:
        """Load and migrate a configuration, or create a clean configuration.

        ``ScheduleConfiguration`` owns schema migration. This adapter deliberately
        owns no runtime state and persists only its JSON-compatible output.
        """
        data = await self._store.async_load()
        if data is None:
            return ScheduleConfiguration.empty()
        return ScheduleConfiguration.from_dict(data)

    async def async_save(self, configuration: ScheduleConfiguration) -> None:
        """Save only the model's JSON-compatible representation."""
        await self._store.async_save(configuration.to_dict())
