# V1 Schedule Data Model

`custom_components/visual_climate_scheduler/models.py` is the source of truth for the persisted V1 schedule shape. It deliberately contains no Home Assistant runtime objects, so it can be validated, migrated and tested independently of entity discovery or the UI.

Each config entry owns one JSON document through Home Assistant's Store helper:

```json
{
  "version": 2,
  "rooms": {
    "living_room": {
      "id": "living_room",
      "name": "Living Room",
      "area_id": "living_room",
      "climate_entity_ids": [
        "climate.living_room_radiator_1",
        "climate.living_room_radiator_2",
        "climate.living_room_radiator_3"
      ],
      "days": {
        "monday": [
          {
            "id": "morning-1",
            "friendly_name": "morning",
            "name": "Morning",
            "time": "06:30",
            "temperature": 20.0
          }
        ],
        "tuesday": [],
        "wednesday": [],
        "thursday": [],
        "friday": [],
        "saturday": [],
        "sunday": []
      }
    }
  },
  "settings": {}
}
```

- All seven days are independently stored. Weekdays, Weekend and All Days remain UI grouping/apply actions, never stored schedule groups.
- `id` is the stable identity used by future copy/apply and editing operations. `friendly_name` is a readable stable label; `name` is the user-facing display name.
- `time` is an exact, zero-padded 24-hour `HH:MM` string. Daily periods must already be chronologically ordered; the model rejects duplicate IDs, duplicate times and unordered lists.
- The initial editor may expose four periods per day, but the persisted list has no four-period cap.
- Copy helpers preserve a period's stable ID while creating detached day collections, so a copied day can later diverge without changing its source.
- `area_id` is optional Home Assistant Area context. `climate_entity_ids` is a non-empty list of durable climate targets, so one scheduled room or zone can control one or many thermostats. A later discovery layer may report a target as unavailable, but must not remove the schedule.
- Overrides, active periods, device availability and learning history are runtime state, not part of this document.

## Versioning and migration

`version` is the document schema version, currently `2`; it is separate from
Home Assistant Store's storage wrapper version. The model migrates the
pre-versioned prototype shape (implicit version `0`) through version 1. Version
1's singular `climate_entity_id` is migrated to a one-item
`climate_entity_ids` list. Unknown future versions are rejected rather than
guessed.
All persisted output is a detached JSON-compatible object, suitable for Home
Assistant Store.
