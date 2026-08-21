# Release 0.1.0 — Project Definition & Architecture Baseline

**Status: Design milestone**

This release establishes the foundation for HA Visual Climate Scheduler before production implementation begins.

## Highlights
- V1 defined as a standalone Home Assistant climate scheduler, independent of the Heat Control System.
- Seven independent daily schedules established as the core model.
- Rigid weekday/weekend inheritance replaced by dynamic UI grouping.
- Modern visual timeline/editor selected as the primary PC/tablet interface.
- Precise typed time and temperature editing defined alongside drag interaction.
- Mobile quick-control defined for temporary and permanent changes.
- Mobile permanent changes operate on the currently active schedule period only.
- Versioned JSON-serialisable persistence using Home Assistant's Store helper established.
- V2 defined as a separate learning layer that initially recommends rather than silently changes schedules.
- Project decision log, requirements, architecture, roadmap, parked ideas and initial Wiki structure established.

## Not included
No production integration code. The next milestone is detailed data/UI specification followed by the V1 integration skeleton.

## Recommended Git commit
`docs: establish v0.1.0 project definition and architecture baseline`

## Recommended tag
`v0.1.0`
