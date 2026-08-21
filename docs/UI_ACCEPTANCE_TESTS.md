# UI Acceptance Tests

These are human-facing UX tests for the visual scheduler. Passing technical tests is not sufficient if the interaction is frustrating or ambiguous.

## Navigation
- Select a ZEAL Zone and verify Floor/Room are filtered.
- Select a Floor and verify Room is filtered.
- When ZEAL is absent, fall back to the generic HA hierarchy.
- Unused hierarchy selectors remain visible but greyed/read-only.
- Invalid downstream selections are cleared after an upstream change.

## First-time room
- A new room offers sensible presets before requiring manual schedule creation.
- User can choose a preset or copy an existing room.
- A copied schedule can subsequently be changed independently.

## Schedule editing
- Click a schedule point and show its editor at the bottom.
- Enter an exact time such as `09:12`.
- Enter an exact setpoint such as `27`.
- Dragging remains available for quick adjustment.
- Invalid or overlapping times are clearly reported.
- Saving changes the selected period without unexpectedly changing other periods.

## Dynamic weekday behaviour
- Start with identical Monday-Friday schedules displayed as Weekdays.
- Change Monday Daytime 20°C -> 23°C and choose Today only.
- Monday becomes independent; Tuesday-Friday remain unchanged.
- The UI no longer falsely presents Monday-Friday as one identical schedule.
- Change Monday Daytime and choose Weekdays; only the Daytime period changes Monday-Friday.
- Other periods remain unchanged.

## Mobile / quick control
- From a mobile-sized layout, identify the current active period.
- Change its temperature without opening the full scheduler.
- Temporary options: 2 hours, 4 hours, next schedule change.
- Permanent options: today, weekdays, weekend, all week.
- Mobile changes affect the active period only.
- Temporary changes do not alter the programmed schedule.
- Permanent changes alter the selected daily/grouped schedule period.

## Copy room
- Select source room.
- Select destination room.
- Copy schedule.
- Confirm destination becomes independent.
- Temporary overrides and future learning history are not copied by default.

## ZEAL navigation prototype
- Zone is the preferred top-level selector when ZEAL is present.
- Floor options are filtered by selected Zone.
- Room options are filtered by selected Zone and Floor.
- Changing Zone clears/reselects invalid downstream context.
- Copy Room opens a source/destination workflow and makes the destination independent.
