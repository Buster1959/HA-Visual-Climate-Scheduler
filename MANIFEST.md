# Session Manifest

Project: HA Visual Climate Scheduler
Snapshot: 0.7.0-dev

## Added
- `release_notes/RELEASE_NOTES_0.7.0-dev.md` — Block 3 release notes
- `custom_components/visual_climate_scheduler/diagnostics.py` — ZEAL discovery diagnostics
- `custom_components/visual_climate_scheduler/services.py` — explicit ZEAL thermostat-only test action
- `custom_components/visual_climate_scheduler/services.yaml` — service description
- `custom_components/visual_climate_scheduler/zeal.py` — optional ZEAL discovery adapter
- `custom_components/visual_climate_scheduler/zeal_models.py` — runtime ZEAL discovery contract
- `tests/test_zeal_models.py` — ZEAL discovery-contract tests

## Modified
- `MANIFEST.md`
- `README.md`
- `custom_components/visual_climate_scheduler/__init__.py`
- `custom_components/visual_climate_scheduler/manifest.json`
- `custom_components/visual_climate_scheduler/const.py`
- `custom_components/visual_climate_scheduler/models.py` — V1 model validation, migration and copy helpers
- `custom_components/visual_climate_scheduler/storage.py` — documented migration ownership
- `docs/DATA_MODEL.md`
- `docs/ARCHITECTURE.md`
- `docs/DECISIONS.md`
- `docs/PROJECT.md`
- `docs/PROJECT_MANIFEST.md`
- `tests/test_models.py` — persistence-boundary test coverage

The Block 2 files above are restored from the available Block 2 checkpoint;
they remain optional runtime discovery/control support and do not change the V1
persisted schedule model.

## Deleted
None.

## Production code
Versioned schedule persistence boundary only. No schedule engine, UI panel, entity discovery or climate control is included.

## Recommended Git commit
`feat: complete Block 3 schedule persistence boundary`

## Next
- Area and climate-entity discovery/configuration
- Schedule engine and active-period calculation
- Room schedule editing UI
