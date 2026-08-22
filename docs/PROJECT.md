# Project Definition

## Purpose
Create a standalone Home Assistant integration providing a modern, visual, room-based climate scheduling experience.

## Product principle
Optimise for real-world Home Assistant users rather than implementation convenience.

## Standing design principle
**Simple underneath, friendly on top.** Use the simplest underlying model that
supports the required behaviour. The UI may offer convenient shortcuts and rich
visualisation, but must not introduce unnecessary concepts into the architecture.
Raise a materially simpler approach when it improves maintainability,
reliability or user experience; do not turn equivalent alternatives into debate.

## V1
V1 is a deterministic scheduler. It controls Home Assistant climate entity setpoints and has no dependency on the Heat Control System.

## V2
V2 adds optional learning from repeated user behaviour. Learning initially produces suggestions and does not silently alter schedules.

## Key differentiator
Seven daily schedules are stored independently. Weekdays, Weekend and All Days are dynamic UI groupings/actions rather than permanent schedule objects. This allows a day to diverge naturally without a "break schedule" operation.

## Scheduled spaces
A scheduled space is a named room or zone with one or more climate targets. A
single thermostat is simply a space with one target; multiple lounge thermostats
or every thermostat in a hotel zone use the same model and receive the same
scheduled setpoint. The system must not create separate room and zone schedule
types.

## Target interfaces
PC/tablet: full visual timeline/editor.

Mobile: fast remote climate adjustment and temporary/permanent schedule changes, not a shrunken copy of the desktop editor.
