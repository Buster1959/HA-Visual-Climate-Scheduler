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
- Select a source room with current unsaved schedule edits.
- Expand **Copy schedule to rooms** and select one or more destination rooms.
- Copy the schedule and confirm the source edits and all seven days are saved.
- Confirm destination schedules match but are independent afterwards.
- Confirm destination name, Area and thermostat assignments are unchanged.
- Confirm temporary overrides and future learning history are not copied.

## ZEAL navigation prototype
- Zone is the preferred top-level selector when ZEAL is present.
- Floor options are filtered by selected Zone.
- Room options are filtered by selected Zone and Floor.
- Changing Zone clears/reselects invalid downstream context.
- Copy Room opens a source/destination workflow and makes the destination independent.

## Fully interactive schedule editor
- Clicking a point or period opens the editor.
- Exact time such as `09:12` can be entered.
- Exact setpoint such as `27°C` can be entered.
- Saving immediately updates the timeline and period list.
- Duplicate times are rejected.
- Setpoints outside the supported prototype range are rejected.
- Monday can be broken out as an independent daily schedule.
- Applying a Monday change to Weekdays synchronises Monday-Friday only.
- Saturday and Sunday remain independent from Weekdays.

## Visual temperature scale and direct manipulation
- Graph has a visible temperature scale on the left.
- Scale adjusts to the scheduled temperature range.
- Each schedule point displays its setpoint.
- Clicking a point opens the precise time/setpoint editor.
- Vertical dragging changes the setpoint visually.
- Dragging has a non-drag numeric alternative.
- Heating/cooling temperature ranges remain readable.
