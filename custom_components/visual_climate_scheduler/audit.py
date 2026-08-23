"""Bounded persistent audit trail for scheduler climate writes."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from .const import AUDIT_MAX_ENTRIES, AUDIT_STORAGE_VERSION, DOMAIN

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


class AuditLog:
    """Persist recent scheduler applications separately from configuration."""

    def __init__(self, hass: HomeAssistant, entry_id: str, store: Any | None = None) -> None:
        if store is None:
            from homeassistant.helpers.storage import Store

            store = Store[dict[str, object]](
                hass,
                AUDIT_STORAGE_VERSION,
                f"{DOMAIN}.audit.{entry_id}",
            )
        self._store = store
        self._entries: list[dict[str, object]] = []

    async def async_load(self) -> None:
        """Load valid audit records, ignoring an unreadable legacy payload."""
        data = await self._store.async_load()
        if not isinstance(data, dict) or data.get("version") != AUDIT_STORAGE_VERSION:
            self._entries = []
            return
        entries = data.get("entries")
        self._entries = (
            [dict(entry) for entry in entries if isinstance(entry, dict)][-AUDIT_MAX_ENTRIES:]
            if isinstance(entries, list)
            else []
        )

    async def async_record(
        self,
        *,
        timestamp: datetime,
        room_id: str,
        room_name: str,
        entity_id: str,
        previous_temperature: float | None,
        requested_temperature: float,
        cause: str,
        outcome: str,
        error: str | None = None,
    ) -> None:
        """Append one climate-target result and enforce the retention bound."""
        entry: dict[str, object] = {
            "timestamp": timestamp.isoformat(),
            "room_id": room_id,
            "room_name": room_name,
            "entity_id": entity_id,
            "previous_temperature": previous_temperature,
            "requested_temperature": float(requested_temperature),
            "cause": cause,
            "outcome": outcome,
        }
        if error:
            entry["error"] = error
        self._entries.append(entry)
        self._entries = self._entries[-AUDIT_MAX_ENTRIES:]
        await self._store.async_save(
            {"version": AUDIT_STORAGE_VERSION, "entries": self._entries}
        )

    def export(self) -> dict[str, object]:
        """Return a detached, human-readable download document."""
        return {
            "version": AUDIT_STORAGE_VERSION,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "maximum_entries": AUDIT_MAX_ENTRIES,
            "entries": [dict(entry) for entry in self._entries],
        }
