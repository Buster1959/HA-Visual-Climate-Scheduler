# Architecture

```text
Home Assistant
      |
      v
Visual Climate Scheduler
      |
      +--> Persistent configuration (HA Store / JSON-serialisable)
      +--> Schedule engine
      +--> Runtime state / overrides
      +--> PC/tablet visual editor
      +--> Mobile quick-control
      |
      v
HA climate entity
      |
      v
Underlying HVAC system
```

The scheduler does not control heat pumps, boilers, pumps or HVAC plant.

## Persistence
Use Home Assistant's Store helper for versioned JSON-serialisable persistent configuration. Runtime state is kept separately and is not part of the persistent schedule model.

## Data principles
- Human-readable
- Versioned
- Seven independent daily schedules
- Stable period IDs
- Friendly names
- Runtime state separate from configuration
- Schedules survive device unavailability

## Future learning
V2 learning consumes user behaviour/history without contaminating the deterministic V1 schedule engine.
