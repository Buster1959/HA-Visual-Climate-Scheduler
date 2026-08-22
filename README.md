# HA Visual Climate Scheduler

A modern Home Assistant climate scheduler built around independent daily schedules, visual editing, and real-world usability.

## Checkpoint 0.7.0-dev

**Block 3 — V1 Schedule Data Model & Persistence Boundary**

The versioned, human-readable schedule model and Home Assistant Store adapter
are implemented. Schedule execution has not been started.

## V1
- Visual PC/tablet timeline editor
- Seven independently stored daily schedules
- Dynamic Weekdays/Weekend/All Days grouping
- Up to four periods per day in the initial UI
- Drag time/temperature editing
- Exact time and setpoint entry
- Room/Area climate entity discovery
- Schedule copy/apply
- Mobile quick-control with temporary/permanent overrides
- No dependency on the Heat Control System

## V2
Optional learning of repeated user behaviour, including temperature/time changes, with suggestions before automatic changes are considered.

See `docs/PROJECT_MANIFEST.md` for the current project checkpoint.
