# 0.10.0-dev — Block 6: Functional Schedule Editor

## Added

- An optional, native Home Assistant sidebar panel named **Climate Scheduler**.
- A Configure-menu checkbox, **Show scheduler editor in sidebar**, which adds
  or removes that navigation item without modifying schedules.
- Admin-only editor access with a small WebSocket persistence boundary.
- Direct room/zone selection plus seven independent day cards. Each card lets
  an administrator add, edit, remove and save up to four periods in the first
  UI, including exact `HH:MM` time and temperature values.
- Pure tests for the editor update boundary and persisted sidebar preference.

## Changed

- Sidebar edits are parsed back through the durable schedule model before they
  can be saved. Existing conflict, ordering, exact-minute and JSON-safe
  validation therefore applies equally to UI changes.
- Saving updates Home Assistant Store and refreshes the active deterministic
  scheduler configuration in one operation.

## Deliberately not included

- Copy/apply-to-days behaviour. The visible controls are disabled rather than
  pretending to work.
- Temporary or permanent override behaviour.
- Timeline drag editing, mobile quick controls or learning.
