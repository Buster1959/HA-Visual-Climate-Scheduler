"""Tests for the persistent thermostat application audit trail."""

import unittest
from datetime import datetime, timezone

from custom_components.visual_climate_scheduler.audit import AuditLog
from custom_components.visual_climate_scheduler.const import AUDIT_MAX_ENTRIES


class FakeStore:
    """Small in-memory replacement for Home Assistant storage."""

    def __init__(self, data=None):
        self.data = data

    async def async_load(self):
        return self.data

    async def async_save(self, data):
        self.data = data


class AuditLogTests(unittest.IsolatedAsyncioTestCase):
    async def test_loads_empty_when_no_saved_payload_exists(self):
        audit = AuditLog(None, "entry", store=FakeStore())

        await audit.async_load()

        self.assertEqual([], audit.export()["entries"])

    async def test_records_and_exports_application_result(self):
        store = FakeStore()
        audit = AuditLog(None, "entry", store=store)
        await audit.async_load()

        await audit.async_record(
            timestamp=datetime(2026, 8, 23, 7, 0, tzinfo=timezone.utc),
            room_id="lounge",
            room_name="Lounge",
            entity_id="climate.lounge",
            previous_temperature=18,
            requested_temperature=20,
            cause="scheduled_transition",
            outcome="applied",
        )

        entry = audit.export()["entries"][0]
        self.assertEqual("2026-08-23T07:00:00+00:00", entry["timestamp"])
        self.assertEqual("climate.lounge", entry["entity_id"])
        self.assertEqual(18, entry["previous_temperature"])
        self.assertEqual(20.0, entry["requested_temperature"])
        self.assertEqual("applied", entry["outcome"])
        self.assertEqual(1, store.data["version"])

    async def test_load_keeps_only_most_recent_entries(self):
        entries = [{"sequence": index} for index in range(AUDIT_MAX_ENTRIES + 1)]
        audit = AuditLog(
            None,
            "entry",
            store=FakeStore({"version": 1, "entries": entries}),
        )

        await audit.async_load()

        exported = audit.export()["entries"]
        self.assertEqual(AUDIT_MAX_ENTRIES, len(exported))
        self.assertEqual(1, exported[0]["sequence"])

    async def test_ignores_malformed_payload(self):
        audit = AuditLog(None, "entry", store=FakeStore({"entries": "invalid"}))

        await audit.async_load()

        self.assertEqual([], audit.export()["entries"])


if __name__ == "__main__":
    unittest.main()
