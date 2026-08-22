# 0.9.0-dev — Block 5: Room & Zone Setup

## Added

- Configure menu for adding or removing named scheduled rooms and zones.
- One-to-many climate target selection: every target in a scheduled space gets
  the same scheduled setpoint.
- Optional Home Assistant Area context for navigation, without restricting a
  zone to only one Area.
- Target-conflict protection: a thermostat cannot be assigned to two schedules.
- Pure configuration helpers and tests for multi-target spaces and safe removal.

## Changed

- Persisted schedule schema is now version 2. Existing version-1
  `climate_entity_id` values migrate safely to a one-item
  `climate_entity_ids` list.
- The runtime engine now applies a schedule period to every target in the
  selected room or zone. An unavailable target does not remove the saved space
  or block other available targets.

## Not included

- The visual schedule editor and period-editing UI.
- Temporary/permanent overrides and learning.
- Any change to the existing ZEAL test action.
