# Temporary Overrides and Future Modes — Design Notes

Status: design record only. No override, mode, calendar or Alarmo behaviour is
implemented by this document.

## The simple underlying model

An override belongs to one scheduled room or zone. A one-room action creates
one override; a selected-room or whole-house action creates one override per
affected scheduled space. This keeps rooms/zones independent and avoids adding
separate “whole house” or “selection” schedule types.

| User action | Underlying action |
| --- | --- |
| One cold room: turn up/down | Override that room/zone |
| Select several rooms: +/− temperature | One override for each selected room/zone |
| Whole house: +/− temperature | One override for every configured room/zone |

The action applies to scheduled spaces, not directly to individual thermostat
entities. A room or zone already knows whether it controls one thermostat or
many.

## Manual temporary override scenarios for Block 8

- Set an absolute target temperature for one room/zone.
- Adjust the active scheduled target up or down, initially with simple `+2°C`
  and `−2°C` controls; later controls may offer other increments or exact entry.
- Apply the same action to a selection of rooms/zones or to all configured
  spaces.
- Hold the result for **2 hours**, **4 hours**, or **until the next scheduled
  change**.

For simplicity and predictability, a relative action is resolved to an absolute
target when it is requested. For example, a scheduled 19°C target with `+2°C`
becomes a fixed 21°C hold. It does not keep adding 2°C if the underlying
schedule would change during a two-hour hold.

An “until next scheduled change” expiry is calculated per room/zone. A batch
may therefore resume different rooms at different times, because their next
schedule transitions can differ. A new override for the same room/zone replaces
its previous temporary override.

## Boundaries and later decisions

- The programmed seven-day schedule remains unchanged.
- Temporary operational state must remain outside the persistent schedule
  document. Whether active overrides receive their own restart-safe short-lived
  store will be decided during implementation.
- Entity unavailability must not delete an override or a scheduled space.
- The UI must clearly state the target, scope and expiry, and clearly show an
  active override.

## Future modes — recorded, not implemented

Modes are a later policy layer, not another kind of daily schedule:

- **Away mode**: for example, apply a configurable negative offset such as
  `−2°C` to all scheduled spaces while Away is active.
- **Calendar period**: a named start/stop period that applies a future mode or
  temperature policy, for example while on holiday.
- The intended priority direction is: a manual temporary override has priority
  over a future Away/Calendar policy, which in turn modifies or yields to the
  normal scheduled target. Exact calendar-versus-Away rules remain open.

This separation avoids putting Away, Holiday, Weekday or Weekend into the
underlying seven-day schedule model.

## Alarmo and presence automation — future integration direction

Away should remain optional and work through standard Home Assistant
automations/services rather than becoming dependent on Alarmo. A future
automation may activate Away when an Alarmo state changes, when all members of
a Home Assistant presence group are away, or from another trusted source.

For “everybody has left”, a presence group is usually the more direct signal;
an Alarmo panel armed-away state is a useful optional trigger where that matches
the household routine. The scheduler should expose a small generic future mode
interface, leaving the automation author free to connect Alarmo, presence,
calendar or a dashboard button.
