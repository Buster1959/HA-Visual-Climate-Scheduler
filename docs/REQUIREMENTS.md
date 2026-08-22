# Requirements

## V1
- Discover climate entities associated with Home Assistant Areas.
- Configure a named room or zone with one or more target climate entities.
- Store seven independent daily schedules.
- Initial UI supports up to four periods per day.
- Each period has stable ID, friendly_name, user-facing name, time and temperature.
- Time can be dragged visually and entered exactly, e.g. 09:12.
- Temperature can be dragged visually and entered exactly within climate entity capabilities.
- Clicking a point exposes precise editing controls.
- Schedule points are chronologically ordered and conflicts are clearly handled.
- Copy/apply schedules to weekdays, weekend, all days or selected days.
- Individual days can always be edited afterwards.
- Visual timeline shows temperature transitions and current time.
- Startup reconciliation calculates the active period and restores the scheduled target.
- Missing or temporarily unavailable climate entities do not destroy schedules or other targets in the same space.
- Temporary overrides do not modify the programmed schedule.
- Mobile offers 2 hour, 4 hour and next scheduled change holds.
- Mobile permanent changes affect only the current active period and can be scoped to today, weekdays, weekend or all days.

## V2
- Record relevant user actions.
- Distinguish temporary overrides from permanent schedule changes.
- Detect repeated temperature changes (initial threshold: 3+).
- Detect repeated time changes.
- Generate learning candidates/suggestions.
- Require user approval initially.
