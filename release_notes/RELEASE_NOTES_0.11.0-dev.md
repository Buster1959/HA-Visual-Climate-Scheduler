# 0.11.0-dev — Block 7: Room Management & Day Apply

## Added

- A current, safety-first **Instructions for Use** page in the GitHub Wiki,
  with a matching versioned copy in the repository. The README links to it.
- **Modify a room or zone** in the integration Configure menu. It retains the
  room's stable identity and all saved daily schedules while allowing its name,
  optional Area and thermostat list to be changed.
- A source-day radio button and **Apply here** checkbox on each sidebar day
  card. **Apply to selected days** now copies the source day to the checked
  destinations; Save persists the edited schedules normally.

## Safety

- A thermostat can remain in its current room while that room is modified, but
  it cannot be added if it is already assigned to another scheduled space.
- The destination-day copies are detached from the source day, preserving the
  seven-day independent model after the application.

## Not included

- Temporary overrides, timeline drag editing and learning.
