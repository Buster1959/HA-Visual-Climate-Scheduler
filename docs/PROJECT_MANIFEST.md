# Project Manifest

Project: HA Visual Climate Scheduler
Repository: Buster1959/HA-Visual-Climate-Scheduler
Project version: 0.16.2-dev
Phase: Block 12 — Open Scheduler from the Integration
Status: The direct editor has a first-time setup view, standard climate-entity selection, copy shortcuts, continuous daily timelines and versioned panel assets

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
- Generic room, zone and floor navigation decisions retained
- Standard Home Assistant climate entities are the only control boundary
- Standing principle "Simple underneath, friendly on top" recorded
- Deterministic active-period calculation added, including overnight and empty-day carry-over
- Home Assistant runtime adapter applies startup targets and schedules the nearest transition
- Options-flow setup for named rooms/zones and one or many climate targets added
- V1 persisted data migrated from singular to plural climate target IDs
- The full admin-only scheduler opens from the integration's Configure action; its sidebar shortcut is optional
- Editor changes are validated by the durable data model, persisted through HA Store and applied to the running engine
- First editor supports direct period name, exact time and temperature editing for seven independent days
- Sidebar visibility is a persisted preference and never changes saved schedules
- A scheduled room/zone can be modified to add or remove thermostat targets without losing its schedule
- Sidebar day application uses an explicit source day plus selected destination-day checkboxes
- Pre-release Instructions for Use are maintained in the GitHub Wiki and versioned in the repository
- A local integration brand icon is bundled for current Home Assistant releases
- Block 8 override scenarios and future Away/Calendar/Alarmo direction are documented without implementation
- Each day card has a temperature timeline with direct time/target point dragging and a visible scale
- Quick Change applies cancellable temporary holds without modifying saved schedules
- A completed schedule can be copied to selected rooms/zones; only their daily schedules are replaced
- Schedule storage records `°C` or `°F` at initial setup and rejects a changed HA unit rather than silently applying misleading targets
- The scheduler is registered as the integration configuration panel and remains directly available when the optional sidebar shortcut is hidden
- Bundled panel assets use a versioned URL so an integration update does not reuse a stale browser-cached editor
- Empty installations open directly to room/zone setup and list standard Home Assistant climate entities
- Copying schedules offers Select all / Clear all and timelines visibly carry the prior day's final target across midnight

Key decisions:
- D-001 through D-055 are captured in DECISIONS.md
- V1 scheduler is deterministic
- V2 learning is separate and initially recommendation-based

Next session:
- V1 release readiness: live HA acceptance testing, HACS packaging and a release candidate

## Repository workflow

During development sessions, project snapshots may be distributed as ZIP checkpoints. The user commits reviewed changes to GitHub according to this manifest.
