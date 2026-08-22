# HA Visual Climate Scheduler

A modern Home Assistant climate scheduler built around independent daily schedules, visual editing, and real-world usability.

## Checkpoint 0.10.0-dev

**Block 6 — Functional Schedule Editor**

The scheduler now has an optional, admin-only sidebar editor. In the
integration's Configure menu, choose **Sidebar editor** and tick **Show
scheduler editor in sidebar**. The panel presents seven independent daily
schedules for each configured room or zone, with exact time and temperature
editing, up to four periods per day in this first UI.

The integration Configure menu remains the place to add/remove rooms and
zones. The sidebar is the day-to-day schedule editor. Hiding the checkbox
removes the sidebar item without deleting schedules.

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
