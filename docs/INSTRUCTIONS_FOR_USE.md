# Instructions for Use — Pre-release 0.11.0-dev

This guide describes the implemented Block 7 pre-release. It is suitable for
people happy to test an unfinished integration in a non-critical room or zone.

## Before you begin

- Back up your Home Assistant configuration.
- Test with one room or zone first. A saved schedule is live: the scheduler
  applies setpoints at schedule transitions and reconciles the current target
  when the integration starts.
- This build is admin-only. It does not yet provide temporary overrides,
  mobile quick controls or timeline dragging.

## Install and add the integration

1. Install this custom integration using your normal Home Assistant custom
   integration method. For a manual install, copy the
   `custom_components/visual_climate_scheduler` folder from the checkpoint
   into your Home Assistant `config/custom_components/` folder.
2. Restart Home Assistant.
3. Go to **Settings → Devices & services → Add integration**, search for
   **Visual Climate Scheduler**, and add it. The initial integration setup is
   intentionally empty.

On Home Assistant 2026.3 or newer, the integration card should show the
calendar, clock and heat icon included with this release after the restart.

## Configure rooms or zones

Go to **Settings → Devices & services → Visual Climate Scheduler → Configure**.

- **Add a room or zone** creates a named scheduled space. Select every climate
  thermostat that should receive the same target. Tick **Add another room or
  zone after saving** when entering several spaces in sequence.
- **Modify a room or zone** changes its name, optional Area or thermostat list
  without losing its existing daily schedule. Use this to add a second or third
  thermostat to a room.
- A climate thermostat can belong to only one scheduled space. This prevents
  two schedules from competing for the same device.
- **Remove a room or zone** removes that saved space and its schedule.

## Enable and use the sidebar editor

1. In Configure, choose **Sidebar editor** and tick **Show scheduler editor in
   sidebar**.
2. Open **Climate Scheduler** from the Home Assistant sidebar.
3. Select the room or zone to edit.
4. Each day is independent. Add up to four periods in this first UI, set the
   period name, exact `HH:MM` start time and target temperature, then choose
   **Save schedule**.
5. To reuse a day: choose its **Source** radio button, tick **Apply here** on
   one or more destination days, choose **Apply to selected days**, then Save.
   The copied days are independent afterwards.

## Current limits and safe testing

- The storage model can retain more than four periods per day, but this first
  editor presents up to four.
- Duplicate times within a day are rejected. Periods are saved in time order.
- There are no temporary overrides yet. Do not use this build where an
  automatic setpoint change would be unsafe or disruptive.
- If the sidebar does not appear, confirm you are an administrator, the
  checkbox is enabled and refresh the Home Assistant browser page after
  changing it.

## Reporting feedback

When reporting a problem, include your Home Assistant version, the integration
version (`0.11.0-dev`), the affected room/zone and the exact steps that led to
the result. Do not include secrets or full Home Assistant backups.
