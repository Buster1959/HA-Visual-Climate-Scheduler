# 0.12.0-dev — Block 8: Visual Timeline Slider Editor

## Added

- A visual temperature timeline on every day card, including a readable
  temperature scale and 24-hour time axis.
- Direct point dragging: horizontal movement changes the period start time in
  15-minute steps; vertical movement changes target temperature in 0.5°C
  steps.
- Click a point to highlight the corresponding precise period controls.

## Kept deliberately simple

- The timeline edits the existing seven independent daily lists. It adds no
  alternate schedule model or stored slider state.
- Typed controls remain available for exact `HH:MM` values, including times
  such as `09:12` that do not align to drag increments.
- Saving still uses the existing validation, ordering and persistence boundary.

## Not included

- Temporary overrides, mobile quick controls and future Away/Calendar modes.
