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
      +--> Native HA schedule editor (direct integration launch; optional sidebar shortcut)
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

## Scheduler editor
The native Home Assistant scheduler editor is admin-only and registered as the
integration's configuration panel, so it is always reachable through the
integration's **Configure** action. The persisted `settings.show_panel`
preference only controls its optional sidebar shortcut. It reads and writes only
the configuration document through a small admin-only WebSocket boundary. That
boundary validates an edited seven-day room/zone document through the durable
model before saving it and immediately refreshing the running deterministic
scheduler. It does not introduce a second schedule model or persist runtime
state.

The same editor contains the small room/zone management view. This avoids a
second management route being hidden by the direct Configure launch, while
reusing the existing validated room operations and persistence boundary.

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
