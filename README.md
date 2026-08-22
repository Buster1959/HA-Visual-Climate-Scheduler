# HA Visual Climate Scheduler

A modern Home Assistant climate scheduler built around independent daily schedules, visual editing, and real-world usability.

## Trying this pre-release

Read the [Instructions for Use](https://github.com/Buster1959/HA-Visual-Climate-Scheduler/wiki/Instructions-for-Use)
before installing. They cover safe test setup, room/zone configuration, the
sidebar editor and the current limitations for this checkpoint.

The integration includes its own Home Assistant brand icon for current Home
Assistant releases.

## Checkpoint 0.13.0-dev

**Block 9 — Quick Change & Temporary Overrides**

The scheduler now has an optional, admin-only sidebar editor. In the
integration's Configure menu, choose **Sidebar editor** and tick **Show
scheduler editor in sidebar**. The panel presents seven independent daily
schedules for each configured room or zone, with exact time and temperature
editing, up to four periods per day in this first UI.

The integration Configure menu remains the place to add/remove rooms and
zones. Choose **Modify a room or zone** to change its details or add/remove
thermostats while keeping its daily schedules. The sidebar is the day-to-day
schedule editor: choose a source day, tick **Apply here** on destination days,
then choose **Apply to selected days** and Save. Hiding the sidebar checkbox
removes the navigation item without deleting schedules.

Every day card now has a visual temperature timeline. Drag a point left/right
to move its time (15-minute steps) or up/down to change its target (0.5°C
steps). Click a point to highlight its precise fields; those fields still allow
exact `HH:MM` entry such as `09:12`.

Use **Quick Change** for temporary holds without cluttering the Schedule view:
select rooms/zones (or Whole house), choose a `+/-` adjustment or exact target,
then hold it for 2 hours, 4 hours or until the next scheduled change.

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
