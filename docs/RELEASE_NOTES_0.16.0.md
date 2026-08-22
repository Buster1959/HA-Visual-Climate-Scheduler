# Release Notes — 0.16.0-dev

## Block 12 — Open Scheduler from the Integration

- The full Visual Climate Scheduler editor is now registered as the
  integration's admin-only configuration panel.
- Open it from **Settings → Devices & services → Visual Climate Scheduler →
  Configure**, even when no sidebar shortcut is enabled.
- **Sidebar editor** now controls only the optional **Climate Scheduler**
  navigation shortcut. Turning it on or off never changes saved schedules or
  the direct integration launch.
- **Rooms and zones** in the direct editor retains add, modify and remove
  actions, including assigning multiple thermostats to one scheduled space.
- Updated the pre-release instructions, architecture, acceptance checks and
  decision log.

## Test focus

After restarting Home Assistant, verify direct **Configure** launch with the
sidebar shortcut both disabled and enabled. Confirm that room schedules remain
unchanged while switching the shortcut preference.
