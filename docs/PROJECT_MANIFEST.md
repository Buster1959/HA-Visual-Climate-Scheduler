# Project Manifest

Project: HA Visual Climate Scheduler
Repository: Buster1959/HA-Visual-Climate-Scheduler
Project version: 0.9.0-dev
Phase: Block 5 — Room & Zone Setup
Status: Named scheduled spaces with one-to-many climate targets can be configured and persisted

## Session checkpoint

Completed:
- Project purpose and V1/V2 boundary defined
- Seven independent daily schedules agreed
- Dynamic Weekday/Weekend grouping agreed
- Human-readable persistent data model agreed
- HA Store persistence direction agreed
- Visual timeline/editor selected as primary PC/tablet interface
- Mobile quick-control concept defined
- Temporary and permanent override behaviour defined
- Permanent mobile changes operate on the current active period only
- V1 independence from the Heat Control System confirmed
- Approved visual UI mockup added as `ui_mockup/index.html` baseline
- UI interaction prototype and human-facing acceptance tests added
- Home Assistant config-entry scaffold added
- Versioned JSON schedule-model and HA Store boundary added
- Strict exact-minute validation, daily conflict validation and safe schema migration added
- Explicit schedule-copy semantics added: days are detached; stable period IDs are retained
- ZEAL discovery decisions retained as optional navigation context only
- Block 2 ZEAL discovery, diagnostics and explicit thermostat-only test action retained
- Standing principle "Simple underneath, friendly on top" recorded
- Deterministic active-period calculation added, including overnight and empty-day carry-over
- Home Assistant runtime adapter applies startup targets and schedules the nearest transition
- Options-flow setup for named rooms/zones and one or many climate targets added
- V1 persisted data migrated from singular to plural climate target IDs

Key decisions:
- D-001 through D-042 are captured in DECISIONS.md
- V1 scheduler is deterministic
- V2 learning is separate and initially recommendation-based

Next session:
- Connect the existing UI acceptance criteria to production UI work
- Add the visual schedule editor for the configured rooms and zones
- Add temporary overrides as a separate layer over the deterministic engine

## Repository workflow

During development sessions, project snapshots may be distributed as ZIP checkpoints. The user commits reviewed changes to GitHub according to this manifest.
