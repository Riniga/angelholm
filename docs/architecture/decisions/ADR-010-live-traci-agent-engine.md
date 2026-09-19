# ADR-010: Drive the simulation live through TraCI instead of pre-generating routes

**Status:** Accepted
**Date:** 2026-09-19

## Context

Until MVP-004, every trip was generated up front: `randomTrips.py` wrote car, bicycle and
pedestrian route files, `write_sumocfg()` tied them to a `.sumocfg`, and `sumo`/`sumo-gui`
played them back for a fixed 400-second window. That gave a simulation with a beginning and
an end where everything exists from the first second, and no place to put behaviour that
depends on time or on who is travelling. Roadmap R2 (a live city that starts empty at
05:00, keeps spawning individuals from statistics and runs indefinitely, with speed control
later) needs a program that is in the loop while the simulation runs.

Checked for real against `eclipse-sumo`/`traci` 1.27.1, not assumed:

- SUMO starts on the committed network with no route files at `--begin 18000` (05:00) and
  keeps stepping while empty; `traci.vehicle.add`/`person.add` +
  `appendWalkingStage` place individuals into the running simulation; SUMO removes
  arrivals itself.
- `findRoute` returns no route for a large share of random pairs (pedestrians especially),
  so spawning needs a retry.
- Named `traci.route.add` routes are never released (31 remain after 30 vehicles left),
  while `vehicle.add(id, "")` + `setRoute` are — decisive for a run with no end.
- `getArrivedNumber()` does not report persons; comparing id sets between steps does.
- SUMO rejects some walking stages (`Invalid arrivalPos`) after the person was added; the
  person must be removed and the id not reused.
- MVP-004's batch rates gridlock in a run with no end (~5,000 travellers after 2 simulated
  hours, still growing). Calibrated rates (0.10 / 0.07 / 0.07 per second) held ~200
  concurrent travellers flat over 6 and 24 simulated hours, with a flat ~85 MB Python
  process (see `docs/plans/005-live-agent-engine.plan.md`, Phase 5).

## Decision

Run the simulation as a single Python control loop over TraCI. `simulator.engine` is the
only module that talks to SUMO; it starts `sumo`/`sumo-gui` on the network with no traffic
and the clock at 05:00, steps once per simulated second, and asks an `IndividualSource`
(`simulator.agents`) which modes are due and which origin/destination to use. The
pre-generated route path (`traffic.py`, `simulate.py`, `randomTrips.py`, generated
`.sumocfg`) is deleted, not kept as a second mode.

Choosing *who, when, where* is kept separate from the loop that applies it, so later MVPs
(statistics, zones, daily plans) replace the source without rewriting the loop. Only patterns
need to be reproducible; a seed is optional and for debugging.

## Consequences

**Benefits:**

- A live city that starts empty, fills and empties naturally, and can run indefinitely.
- A clean seam for R2: statistics, zones and persistent individuals plug in as sources.
- Colours and the bicycle speed cap are set through TraCI, replacing the XML text
  substitution and its Semgrep-driven workaround (ADR-009).
- One code path; nothing to keep in sync between a batch mode and a live mode.

**Trade-offs:**

- The Python process is now in the simulation loop, so it must stay light (no thread per
  individual; SUMO stepping is single-threaded anyway) and must never leak state; a
  24-hour run showed no growth, but this needs re-checking as the source gets richer.
- Runs are no longer bounded by default; automation must pass `--max-seconds`.
- Speed control (0.5x–8x) is not solved here; it is MVP-006 and depends on how the loop
  paces itself against `sumo-gui`.
- Long runs surface SUMO behaviour the short batch never did (~2–3 teleports per simulated
  hour at a few junctions, occasional vehicle–person collisions, pedestrians on roads).
  These are network/routing details, deliberately out of scope here.
- SUMO's teleport default (300 s) is kept so the city can recover from a jam.

## Alternatives considered

- **Keep pre-generating routes (per-person plans written up front):** simplest, but cannot
  be live or open-ended and would have to be replaced for R2 anyway; the owner chose to go
  directly to the live design.
- **A thread per individual:** SUMO steps single-threaded and threads would hurt
  determinism and add nothing; event-driven logic in one loop is enough.
- **`sumo-gui`'s own delay slider only:** gives no way to add individuals over time.
