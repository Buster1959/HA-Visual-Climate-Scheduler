# 0.8.0-dev — Block 4: V1 Deterministic Schedule Engine

## Added

- Home Assistant-independent active-period and next-transition calculation.
- Exact-minute transition behaviour, including carry-over across midnight and
  through empty daily schedules.
- Home Assistant runtime adapter that reconciles each configured room at startup
  and schedules only the nearest future transition.
- Runtime-only active-period tracking and timer cleanup on integration unload.
- Tests for current-day selection, exact boundaries, overnight/empty-day
  carry-over, next transitions and an entirely empty schedule.

## Preserved boundaries

- The engine calls only a room's configured `climate.*` entity using
  `climate.set_temperature`; it never controls HVAC internals or underlying TRVs.
- Configuration remains in Home Assistant Store. Timer state, active periods and
  future overrides remain runtime-only.
- The existing `visual_climate_scheduler.set_zeal_room_temperature` action is
  unchanged.

## Not included

- Area/climate discovery and room-configuration UI.
- Temporary or permanent overrides, frontend editing and schedule copy UI.
- Learning behaviour.
