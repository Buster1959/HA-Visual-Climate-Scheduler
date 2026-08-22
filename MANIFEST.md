# Session Manifest

Project: HA Visual Climate Scheduler
Snapshot: 0.9.0-dev

## Added
- `custom_components/visual_climate_scheduler/rooms.py` — scheduled space configuration helpers
- `tests/test_rooms.py` — multi-target room and zone tests
- `release_notes/RELEASE_NOTES_0.9.0-dev.md` — Block 5 release notes

## Modified
- `MANIFEST.md`
- `README.md`
- `custom_components/visual_climate_scheduler/config_flow.py` — add/remove room and zone setup
- `custom_components/visual_climate_scheduler/const.py`
- `custom_components/visual_climate_scheduler/manifest.json`
- `custom_components/visual_climate_scheduler/models.py` — schema-v2 multi-target migration
- `custom_components/visual_climate_scheduler/runtime.py` — applies each active period to all targets
- `custom_components/visual_climate_scheduler/strings.json`
- `custom_components/visual_climate_scheduler/translations/en.json`
- `docs/DATA_MODEL.md`
- `docs/ARCHITECTURE.md`
- `docs/DECISIONS.md`
- `docs/PROJECT.md`
- `docs/PROJECT_MANIFEST.md`
- `docs/REQUIREMENTS.md`
- `tests/test_engine.py`
- `tests/test_models.py`

## Deleted
None.

## Production code
Room and zone setup plus its data-model/runtime boundary. No visual period editor,
overrides or learning is included.

## Recommended Git commit
`feat: add Block 5 multi-thermostat room and zone setup`

## Next
- Visual schedule editor for configured rooms and zones
- Temporary override layer
