# Session Manifest

Project: HA Visual Climate Scheduler
Snapshot: 0.11.0-dev

## Added
- `release_notes/RELEASE_NOTES_0.11.0-dev.md` — Block 7 release notes
- `docs/INSTRUCTIONS_FOR_USE.md` — versioned pre-release user guide
- `docs/OVERRIDE_AND_MODE_DESIGN.md` — recorded Block 8 override and future mode design
- `custom_components/visual_climate_scheduler/brand/icon.png` — 256px transparent integration icon
- `custom_components/visual_climate_scheduler/brand/icon@2x.png` — 512px high-density integration icon

## Modified
- `MANIFEST.md`
- `README.md`
- `custom_components/visual_climate_scheduler/config_flow.py` — add/modify/remove room and zone setup
- `custom_components/visual_climate_scheduler/frontend/visual-climate-scheduler-panel.js` — source/selected-day application controls
- `custom_components/visual_climate_scheduler/manifest.json`
- `custom_components/visual_climate_scheduler/rooms.py` — safe scheduled-space update helper
- `custom_components/visual_climate_scheduler/strings.json`
- `custom_components/visual_climate_scheduler/translations/en.json`
- `docs/DECISIONS.md`
- `docs/PARKED.md`
- `docs/PROJECT_MANIFEST.md`
- `tests/test_rooms.py`

## Deleted
None.

## Production code
Safe scheduled-space modification plus explicit source/checkbox-based day
application in the native sidebar editor. Temporary overrides, timeline drag
editing and learning are not included.

## Recommended Git commit
`feat: add Block 7 room management and selected-day application`

## Next
- Temporary override layer
- Timeline interaction
