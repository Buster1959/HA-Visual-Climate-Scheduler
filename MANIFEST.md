# Session Manifest

Project: HA Visual Climate Scheduler
Snapshot: 0.10.0-dev

## Added
- `custom_components/visual_climate_scheduler/configuration.py` — shared save-and-live-update boundary
- `custom_components/visual_climate_scheduler/editor.py` — pure editor validation/update helper
- `custom_components/visual_climate_scheduler/frontend/visual-climate-scheduler-panel.js` — native sidebar editor
- `custom_components/visual_climate_scheduler/panel.py` — optional sidebar panel registration
- `custom_components/visual_climate_scheduler/websocket_api.py` — admin-only editor API
- `release_notes/RELEASE_NOTES_0.10.0-dev.md` — Block 6 release notes
- `tests/test_editor.py` — sidebar editor persistence-boundary tests

## Modified
- `MANIFEST.md`
- `README.md`
- `custom_components/visual_climate_scheduler/__init__.py` — panel lifecycle and editor API registration
- `custom_components/visual_climate_scheduler/config_flow.py` — add/remove room and zone setup
- `custom_components/visual_climate_scheduler/const.py`
- `custom_components/visual_climate_scheduler/manifest.json`
- `custom_components/visual_climate_scheduler/strings.json`
- `custom_components/visual_climate_scheduler/translations/en.json`
- `docs/DATA_MODEL.md`
- `docs/ARCHITECTURE.md`
- `docs/DECISIONS.md`
- `docs/PROJECT.md`
- `docs/PROJECT_MANIFEST.md`
- `tests/test_models.py`

## Deleted
None.

## Production code
Optional native Home Assistant sidebar editor for the persisted seven-day
schedule model. It has direct period editing and saving, but no copy/apply
behaviour, overrides, or learning.

## Recommended Git commit
`feat: add Block 6 optional sidebar schedule editor`

## Next
- Temporary override layer
- Copy/apply-to-days editor actions
