# Visual Climate Scheduler 1.0.2

This maintenance release makes scheduled writes safe and truthful for sleeping
battery climate devices and addresses the HACS review findings.

- A failed `climate.set_temperature` call is recorded per thermostat without
  stopping the remaining thermostats, rooms, or future schedule transitions.
- A Home Assistant service call is no longer treated as proof that a thermostat
  has changed. The runtime confirms the entity's reported target temperature.
- Sleeping or unavailable targets retain only their latest requested value.
- A pending target is retried only after that device sends a fresh report, with
  a minimum five-minute interval between attempts. Scheduler scans and timers
  cannot create a repeated battery-device write loop.
- Thermostats that load after Visual Climate Scheduler are reconciled when they
  first report an available state, rather than waiting for the next period.
- Devices already at the requested temperature are not written again.
- The application audit distinguishes confirmed, already-correct, unavailable,
  failed-but-pending, and pending-confirmation outcomes.
- Changing the optional sidebar setting now preserves the schedule document's
  Celsius/Fahrenheit binding.

This does not add thermostat-to-thermostat manual synchronisation. Visual
Climate Scheduler continues to apply schedules and Quick Changes independently
to every climate entity assigned to a room or zone.
