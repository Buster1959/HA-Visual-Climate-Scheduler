# Architecture

```text
Home Assistant
      |
      v
Visual Climate Scheduler
      |
      +--> Persistent configuration (HA Store / JSON-serialisable)
      +--> Persistent bounded application audit (separate HA Store)
      +--> Schedule engine
      +--> Runtime state / overrides
      +--> Standard HA climate entity discovery
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

The thermostat application audit uses a second versioned Store document. The
runtime appends one result for each attempted `climate.set_temperature` call,
including unavailable and failed targets, and retains the latest 5,000
entries. The admin-only WebSocket API exposes a detached export document for
download; audit records never become part of the schedule configuration.

## Scheduler editor
The native Home Assistant scheduler editor is admin-only and registered as the
integration's configuration panel, so it is always reachable through the
integration's **Configure** action. The persisted `settings.show_panel`
preference only controls its optional sidebar shortcut. It reads and writes only
the configuration document through a small admin-only WebSocket boundary. That
boundary validates an edited seven-day room/zone document through the durable
model before saving it and immediately refreshing the running deterministic
scheduler. It does not introduce a second schedule model or persist runtime
state. It also provides read-only downloads of the current configuration and
the separate audit export.

The same editor contains the small room/zone management view. This avoids a
second management route being hidden by the direct Configure launch, while
reusing the existing validated room operations and persistence boundary.

## Climate entity discovery
The editor lists standard Home Assistant `climate` entities from the state
machine. Saved rooms and zones reference those entity IDs directly; the runtime
controls them only through Home Assistant's `climate.set_temperature` service.
There is no heating-system-specific discovery or integration boundary.

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
