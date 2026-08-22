"""Tests for the ZEAL diagnostics/public snapshot contract."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest


def _load_module():
    path = Path(__file__).parents[1] / "custom_components" / "visual_climate_scheduler" / "zeal_models.py"
    spec = importlib.util.spec_from_file_location("vcs_zeal_models", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["vcs_zeal_models"] = module
    spec.loader.exec_module(module)
    return module


zeal_models = _load_module()


class ZealContractTests(unittest.TestCase):
    """Validate the exact zone/room/thermostat contract supplied by ZEAL."""

    def test_parses_room_thermostat_and_ignores_underlying_trvs(self) -> None:
        rooms = zeal_models.rooms_from_zeal_snapshot(
            {
                "zones": [
                    {
                        "zone_id": "zone-1",
                        "name": "Zone 1",
                        "rooms": [
                            {
                                "room_id": "floor2_rooma",
                                "name": "Floor1_RoomA",
                                "trvs": [{"entity_id": "climate.floor1_rooma_thermostat"}],
                                "sensors": [],
                                "computed_room_temperature": 20.0,
                                "thermostat": {
                                    "entity_id": "climate.zone_1_floor1_rooma_thermostat_zeal",
                                    "target_temperature": 20.5,
                                    "hvac_mode": "heat",
                                    "registered_with_coordinator": True,
                                },
                            }
                        ],
                    }
                ]
            }
        )

        self.assertEqual(len(rooms), 1)
        self.assertEqual(rooms[0].zone_id, "zone-1")
        self.assertEqual(rooms[0].room_id, "floor2_rooma")
        self.assertEqual(rooms[0].thermostat_entity_id, "climate.zone_1_floor1_rooma_thermostat_zeal")
        self.assertEqual(rooms[0].target_temperature, 20.5)

    def test_ignores_room_without_a_zeal_thermostat(self) -> None:
        rooms = zeal_models.rooms_from_zeal_snapshot(
            {"zones": [{"zone_id": "zone-1", "name": "Zone 1", "rooms": [{"room_id": "x"}]}]}
        )
        self.assertEqual(rooms, ())
