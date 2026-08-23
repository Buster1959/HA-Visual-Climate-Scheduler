# ZEAL Scheduler Handoff

This document is the extraction guide for recreating the Visual Climate
Scheduler inside the ZEAL repository. The standalone integration deliberately
contains no ZEAL imports, discovery rules, entity-name assumptions, services or
diagnostic contracts. ZEAL should own those adaptations when this scheduler is
transplanted.

## Architecture to recreate

The scheduler has four intentionally separate layers:

1. `models.py`, `engine.py`, `editor.py`, `rooms.py` and `overrides.py` are pure
   Python domain logic and do not require Home Assistant runtime objects.
2. `storage.py` persists the versioned schedule document with Home Assistant's
   `Store` helper.
3. `runtime.py` resolves the active period, maintains temporary overrides,
   schedules the next transition and calls `climate.set_temperature` for each
   configured target.
4. `websocket_api.py`, `panel.py` and
   `frontend/visual-climate-scheduler-panel.js` provide the admin-only editor,
   direct Configure launch, optional sidebar shortcut and Quick Change UI.

The config-entry lifecycle in `__init__.py` loads storage, fixes the Home
Assistant temperature unit for the schedule document, starts the runtime,
registers WebSocket commands and synchronizes the panel. `configuration.py`
saves a validated replacement document and refreshes the running scheduler.

## Files to transplant

Copy these modules as a coherent unit, adjusting their package imports and
domain constants for ZEAL:

- Core: `models.py`, `engine.py`, `editor.py`, `rooms.py`, `overrides.py`
- Home Assistant adapters: `storage.py`, `runtime.py`, `configuration.py`
- UI/API: `websocket_api.py`, `panel.py`,
  `frontend/visual-climate-scheduler-panel.js`
- Lifecycle and metadata as patterns: `__init__.py`, relevant values from
  `const.py`, `manifest.json`, `strings.json` and `translations/en.json`
- Tests: `test_models.py`, `test_engine.py`, `test_editor.py`,
  `test_rooms.py`, `test_overrides.py`

Do not transplant the standalone integration domain, storage key, panel URL or
single-config-entry assumptions without reconciling them with ZEAL's existing
config entries and frontend registration.

## Schedule model and persistence

`ScheduleConfiguration` is the durable root. It contains:

- `schema_version` (currently 3)
- fixed `temperature_unit` (`°C` or `°F`)
- `settings`, including the optional `show_panel` shortcut preference
- a mapping of stable room IDs to `RoomSchedule`

Each `RoomSchedule` stores a stable ID, friendly name, optional Home Assistant
Area ID, one or more `climate_entity_ids`, and exactly seven independent daily
lists. Each `SchedulePeriod` stores stable `id`, `friendly_name`, `name`, exact
24-hour `HH:MM` time and a finite numeric temperature. Persisted days are
chronologically ordered and cannot contain duplicate IDs or times. The UI
limits a day to four periods, but the model intentionally does not.

The `Store` key is currently `<domain>.<config_entry_id>` with storage version
1. Model schema migration is owned by `ScheduleConfiguration.from_dict`, not by
the storage adapter. Preserve that separation. Runtime timers, active-period
keys and temporary overrides are never persisted.

## Execution semantics

At startup and after every saved edit, the deterministic engine finds the most
recent applicable period for every space. The last setpoint carries across
midnight and through empty days. The runtime applies the effective target to
all configured climate entities, skips unavailable entities without deleting
configuration, and schedules only the nearest future transition. Temporary
overrides may be exact or relative and expire after two hours, four hours or at
the next scheduled change.

All writes cross the standard Home Assistant boundary:

```text
climate.set_temperature
  entity_id: climate.<target>
  temperature: <effective target in the stored reference unit>
```

The scheduler does not control valves, TRVs, boilers, pumps, coordinators or
other HVAC internals directly.

## UI components and interfaces

The frontend provides three views:

- Schedule: seven day cards, draggable timeline points, exact field editing,
  selected-day application and whole-week copying to other spaces.
- Quick Change: selected rooms/zones or whole-house temporary holds.
- Rooms and zones: create, modify or remove a scheduled space, select an
  optional HA Area, assign climate targets and control the sidebar shortcut.

The admin-only WebSocket API exposes configuration read/update operations,
room/zone save and removal, schedule copying, sidebar preference, Quick Change
state, override creation and override cancellation. Treat the schemas and
validation in `websocket_api.py` as the interface definition. Writes flow
through `async_save_configuration`, which persists first and then updates the
runtime.

The direct integration Configure action and optional sidebar entry point to the
same panel and schedule document. The panel asset URL is versioned via
`PANEL_ASSET_VERSION`; bump it whenever the JavaScript changes.

## ZEAL adapter to add inside ZEAL

ZEAL may replace generic climate selection with its canonical room thermostats,
but that policy belongs in ZEAL. Implement an adapter that returns stable room
records containing at least:

```text
zone_id, zone_name, room_id, room_name, climate_entity_id
```

Recommended behavior:

- Source rooms from a documented ZEAL-owned public/coordinator interface.
- Use only ZEAL's canonical room thermostat climate entity as the scheduling
  target; never expose or target its underlying TRVs.
- Populate Zone → Floor → Room selectors from ZEAL's own model and cascade each
  selector from its parent.
- Keep ZEAL discovery runtime-only. Persist stable climate entity IDs and
  ordinary scheduler room data, not coordinator objects or diagnostic snapshots.
- If a referenced room is temporarily unavailable, retain its saved schedule
  and surface availability in the UI rather than deleting it.
- Route temperature changes through `climate.set_temperature` unless ZEAL
  explicitly defines a stable public service with equivalent semantics.

The former standalone prototype recognized the `zeal` config-entry domain,
looked for entity IDs ending in `_thermostat_zeal`, used the ZEAL config-entry
title as a fallback zone, and optionally read
`hass.data["zeal"]["async_get_scheduler_snapshot"]`. It also exposed
`visual_climate_scheduler.set_zeal_room_temperature` and ZEAL discovery in
diagnostics. These conventions were intentionally removed because they couple
one integration to another integration's naming and in-memory data. They are
recorded here only to explain prior behavior; do not restore them in standalone
VCS. Inside ZEAL, prefer native typed coordinator access over these fallbacks.

The previous snapshot shape grouped `zones[]`, each with `zone_id`, `name` and
`rooms[]`. Each room supplied `room_id`, `name` and a `thermostat` object with
`entity_id`, optional `target_temperature`, `hvac_mode` and
`registered_with_coordinator`. If ZEAL retains this interface, document and test
it as a ZEAL-owned contract.

## Tests to recreate

Transplant the pure unit suites unchanged first. They cover schema validation,
migration, JSON round trips, day independence, copy semantics, exact-minute and
cross-midnight behavior, next transitions, multi-target rooms, target-conflict
protection and temporary overrides.

Add ZEAL-side adapter tests for:

- zone/floor/room mapping and deterministic ordering
- canonical thermostat selection and rejection of underlying TRVs
- missing, unavailable and malformed room records
- stable IDs across restarts and renames
- multiple zones and floors with cascading UI filters
- climate service calls targeting only the selected room thermostat
- diagnostics redaction and absence of coordinator objects in persistence
- behavior when ZEAL is loaded, unloaded or temporarily unavailable

Run the UI acceptance scenarios in `docs/UI_ACCEPTANCE_TESTS.md`, substituting
ZEAL's hierarchy provider for generic entity selection. Also verify that direct
Configure and the optional sidebar shortcut open the same editor.

## Integration checklist

1. Choose whether schedules belong to each ZEAL config entry or to one global
   ZEAL scheduler, then define the Store key and panel ownership accordingly.
2. Transplant and run the pure domain tests before adding ZEAL adapters.
3. Map ZEAL rooms to stable scheduler spaces and canonical climate entities.
4. Connect save operations to storage and immediate runtime reconciliation.
5. Register the admin-only WebSocket API and versioned panel asset.
6. Add ZEAL hierarchy data to the room/zone editor without changing the durable
   schedule schema unless a versioned migration is genuinely required.
7. Verify temperature-unit binding, startup reconciliation, unavailable
   entities, unload cleanup and next-transition scheduling.
8. Run Python tests, frontend syntax checks and the manual UI acceptance suite.

## Standalone behavior intentionally preserved

The extraction did not remove room, zone or floor terminology, optional Areas,
cascading hierarchy prototypes, multi-thermostat spaces, copy workflows,
cross-midnight continuity, Quick Change, direct Configure launch, the optional
sidebar shortcut, or any schedule model/engine behavior. Only ZEAL-specific
discovery, filtering, diagnostics, naming rules, test service and contract tests
were removed from standalone VCS.
