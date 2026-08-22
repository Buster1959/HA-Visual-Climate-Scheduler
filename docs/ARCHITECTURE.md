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
      +--> Optional ZEAL discovery context
      +--> PC/tablet visual editor
      +--> Mobile quick-control
      |
      v
One or more HA climate entities
      |
      v
Underlying HVAC system
```

The scheduler does not control heat pumps, boilers, pumps or HVAC plant.

## Persistence
Use Home Assistant's Store helper for versioned JSON-serialisable persistent configuration. Runtime state is kept separately and is not part of the persistent schedule model.

## Optional ZEAL discovery
When ZEAL is installed, the integration can discover ZEAL's canonical room
thermostat entities through Home Assistant's public boundaries. Discovery is
runtime-only and provides preferred Zone navigation context. It does not add a
schedule type, alter stored rooms or execute schedules.

## Data principles
- Human-readable
- Versioned
- Seven independent daily schedules
- Stable period IDs
- Friendly names
- Runtime state separate from configuration
- Schedules survive device unavailability

## Schedule execution

The V1 engine is deterministic. At integration startup it resolves each room's
or zone's latest period and applies its target to every configured climate
entity in that scheduled space.
It then schedules only the nearest future transition. If a day is empty, the
most recent period from an earlier populated day remains active; no setpoint is
invented. Active-period tracking and timer handles are runtime-only.

## Future learning
V2 learning consumes user behaviour/history without contaminating the deterministic V1 schedule engine.
