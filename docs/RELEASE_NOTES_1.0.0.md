# Release Notes — 1.0.0

Visual Climate Scheduler V1 is the first stable release of the standalone Home
Assistant integration.

## Highlights

- Seven independently stored daily schedules for each room or zone.
- Visual PC/tablet timelines with draggable time and temperature points plus
  exact `HH:MM` and setpoint fields.
- Responsive mobile views for schedule editing, room management and Quick
  Change.
- Standard Home Assistant `climate` entities as the only control boundary.
- One or many thermostats per scheduled space, with conflict protection so an
  entity cannot receive two competing schedules.
- Schedule application between selected days and complete seven-day copying
  between rooms/zones.
- Cross-midnight and empty-day continuity from the most recent saved period.
- Temporary exact or relative holds for selected rooms or the whole house.
- Home Assistant Store persistence with versioned migration and fixed
  temperature-unit safety.
- Direct admin-only Configure launch with an optional sidebar shortcut.
- Heating-system-agnostic operation with no dependency on HVAC internals or
  another custom integration.

## Installation

Install through HACS as a custom repository or copy
`custom_components/visual_climate_scheduler` into Home Assistant's
`config/custom_components` directory, restart Home Assistant, and add **Visual
Climate Scheduler** from **Settings → Devices & services**.

Read the repository Wiki's **Instructions for Use** before assigning climate
entities. Start with a non-critical room and back up the Home Assistant
configuration before installation.

## Current V1 limits

- The editor exposes up to four periods per day, although the persisted model
  can retain more.
- Temporary holds are runtime-only and clear when Home Assistant restarts.
- Changing Home Assistant between Celsius and Fahrenheit requires removing and
  re-adding this integration before creating new schedules.
- Learning and automatic schedule suggestions remain future V2 work.
