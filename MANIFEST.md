# Session Manifest

Project: HA Visual Climate Scheduler
Snapshot: 0.8.0-dev

## Added
- `custom_components/visual_climate_scheduler/engine.py` — pure active-period and transition calculation
- `custom_components/visual_climate_scheduler/runtime.py` — HA timer and climate-service adapter
- `tests/test_engine.py` — deterministic schedule-engine tests
- `release_notes/RELEASE_NOTES_0.8.0-dev.md` — Block 4 release notes

## Modified
- `MANIFEST.md`
- `README.md`
- `custom_components/visual_climate_scheduler/__init__.py` — engine lifecycle wiring
- `custom_components/visual_climate_scheduler/manifest.json`
- `docs/ARCHITECTURE.md`
- `docs/DECISIONS.md`
- `docs/PROJECT_MANIFEST.md`

## Deleted
None.

## Production code
Deterministic schedule engine and its runtime boundary only. No room discovery,
room-configuration UI, overrides or frontend schedule editor is included.

## Recommended Git commit
`feat: add Block 4 deterministic schedule engine`

## Next
- Area and climate-entity discovery/configuration
- Room schedule editing UI
- Temporary override layer
