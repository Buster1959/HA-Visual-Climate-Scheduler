# Project Definition

## Purpose
Create a standalone Home Assistant integration providing a modern, visual, room-based climate scheduling experience.

## Product principle
Optimise for real-world Home Assistant users rather than implementation convenience.

## V1
V1 is a deterministic scheduler. It controls Home Assistant climate entity setpoints and has no dependency on the Heat Control System.

## V2
V2 adds optional learning from repeated user behaviour. Learning initially produces suggestions and does not silently alter schedules.

## Key differentiator
Seven daily schedules are stored independently. Weekdays, Weekend and All Days are dynamic UI groupings/actions rather than permanent schedule objects. This allows a day to diverge naturally without a "break schedule" operation.

## Target interfaces
PC/tablet: full visual timeline/editor.

Mobile: fast remote climate adjustment and temporary/permanent schedule changes, not a shrunken copy of the desktop editor.
