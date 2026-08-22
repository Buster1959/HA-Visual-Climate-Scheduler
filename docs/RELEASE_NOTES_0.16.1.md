# Release Notes — 0.16.1-dev

## Block 12 cache repair

- Versioned the bundled scheduler JavaScript URL. Home Assistant now asks the
  browser for the editor matching the installed integration version after an
  update.
- This ensures the **Rooms and zones** page is present when the direct
  integration launch opens the scheduler.

## Install note

Replace the custom component with this checkpoint and restart Home Assistant.
Then open **Visual Climate Scheduler → Configure**. The panel URL changes with
this version, so a separate hard refresh should not be necessary.
