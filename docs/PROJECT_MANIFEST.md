# Project Manifest

Project: HA Visual Climate Scheduler
Repository: Buster1959/HA-Visual-Climate-Scheduler
Project version: 0.2.0-dev
Phase: Project Definition & Architecture Baseline
Status: Design phase — implementation not started

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

Key decisions:
- D-001 through D-026 are captured in DECISIONS.md
- V1 scheduler is deterministic
- V2 learning is separate and initially recommendation-based

Next session:
- Finalise detailed JSON schema
- Design Room Overview
- Design PC/tablet timeline interactions
- Design mobile quick-control flow
- Define V1 acceptance tests
- Then begin implementation

## Repository workflow

During development sessions, project snapshots may be distributed as ZIP checkpoints. The user commits reviewed changes to GitHub according to this manifest.
