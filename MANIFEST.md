# Release Manifest

Project: HA Visual Climate Scheduler
Release: 1.0.0
Phase: V1 release preparation

## Included

- Standalone Home Assistant custom integration under
  `custom_components/visual_climate_scheduler`
- Deterministic seven-day schedule model, persistence and runtime
- Visual desktop/tablet editor and responsive mobile controls
- Room/zone management for standard Home Assistant climate entities
- Temporary Quick Change holds
- User, architecture, data-model and handoff documentation
- Root HACS metadata and HACS/Hassfest validation workflows
- Python unit tests for models, engine, editor, rooms and overrides

## Release gates

- Run the automated unit suite.
- Pass HACS validation and Hassfest on GitHub.
- Complete live Home Assistant acceptance testing.
- Publish a full GitHub `1.0.0` release.
- Register the integration with Home Assistant Brands and submit the HACS
  default-catalog request.

## Deferred to V2

- Behaviour learning and schedule suggestions
- Persisted or permanent Quick Change overrides
- Optional Away, calendar and alarm policy layers
