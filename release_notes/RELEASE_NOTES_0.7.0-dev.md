# 0.7.0-dev — Block 3: V1 Schedule Data Model & Persistence Boundary

## Added

- Strict V1 schedule validation for seven independent daily lists, stable IDs,
  exact `HH:MM` times, chronological ordering and duplicate-time conflicts.
- Versioned model migration: the pre-versioned prototype document migrates to
  schema version 1; unknown future versions fail safely.
- JSON-serialisable, detached persistence output for Home Assistant Store.
- Model-level copy helpers that retain logical period IDs while separating daily
  collections so copied days can diverge.
- Unit coverage for seven-day independence, minute precision, conflicts,
  unlimited persisted periods, copy semantics, migration and JSON round-trips.
- The standing design principle: **Simple underneath, friendly on top.**

## Preserved from Block 2

- ZEAL remains optional. When installed/configured, it is the preferred
  navigation context only; its discovery, diagnostics and explicit
  thermostat-only test action are retained. It does not alter the persisted
  schedule model.

## Not included

- No schedule execution, timers, climate service calls, overrides, entities,
  discovery implementation or production UI wiring.
