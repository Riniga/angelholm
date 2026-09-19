# MVP-005 – Live Agent Engine

## Purpose

Change how the simulation gets its traffic, from a pre-generated batch to a live process.

MVP-004 generates every car, bicycle and pedestrian trip up front (`randomTrips.py`), writes
route files and lets SUMO play them back for a fixed 400-second window. That gives a
simulation with a beginning and an end, where everything exists from the first second.

This MVP replaces that with a **live agent engine**: Ängelholm starts empty at about 05:00,
and a control loop, driven through TraCI, keeps adding individuals one at a time — each in a
car, on a bicycle or on foot, with an origin and a destination — and removes them when they
arrive. The simulation has no planned end and can run for as long as the owner keeps it open.

The engine is intentionally simple here (random origins and destinations, a fixed spawn
rate). It is the foundation that the rest of roadmap R2 — speed control, statistics, zones,
realistic scale, daily patterns — builds on, so the goal is to get the *structure* right,
not the realism.

## Goals

* The simulation starts with an empty network and a simulated clock at 05:00.
* A single control loop steps the simulation and, over time, spawns individuals
  (car, bicycle or pedestrian) with a valid origin and destination for their mode.
* Individuals that reach their destination leave the simulation; the number of concurrent
  travellers reaches a steady level instead of growing without bound.
* The simulation can run indefinitely: there is no end time, and it stops only when the
  owner closes it.
* Origins and destinations remain biased toward the 8 curated entry/exit edges
  (`apps/simulator/data/entry-exit-edges.json`, ADR-009), as in MVP-004, so this MVP does
  not regress the "traffic comes from real roads into the city" behaviour.
* A steady-state level of roughly the same visual density as MVP-004's final result
  (on the order of 200 concurrent travellers, to be measured rather than assumed), with the
  three modes still visibly present and in their distinct colours.
* The engine is structured so later MVPs can change *where*, *when* and *who* without
  rewriting the loop: the choice of "next individual" is a separate, replaceable piece from
  the loop that steps SUMO and applies it.
* Only the patterns need to be reproducible, not the exact individuals. An optional seed
  for debugging is welcome but not required to give identical runs.

## Context

Things known before scoping, and things that still need to be checked in the plan:

* **The mechanism exists.** TraCI (`traci` is already a pinned dependency, ADR-006) can add
  vehicles and persons to a running simulation and can start `sumo` or `sumo-gui`. SUMO
  removes vehicles and persons that finish their route by itself.
* **Routing a new individual.** A spawned vehicle or person needs a valid route between two
  edges of the right mode. TraCI offers route search for this; the plan must verify the exact
  calls, and how to choose origins/destinations that are actually reachable for the mode
  (a car cannot start on a footway) instead of assuming it.
* **What is reused from MVP-004.** The network, the entry/exit list and the edge-weight
  logic (`simulator.traffic._write_edge_weights`), the per-mode colours and the bicycle
  speed cap, and the GUI settings (basemap, pedestrian exaggeration). What is replaced is the
  `randomTrips.py` route-file generation and the static `.sumocfg` route inputs.
* **The GUI and TraCI.** Today `simulate.py` launches `sumo-gui -c` as a subprocess and lets
  it own the run. With TraCI the Python process owns the loop and connects to the GUI. How
  the GUI behaves while TraCI steps it (delay, pausing, closing the window) is something the
  plan must check for real; it also matters for MVP-006 (speed control).
* **Simulated time versus wall-clock time.** A live loop needs a rule for how fast it steps.
  In this MVP, running at ordinary "as fast as sensible for viewing" pace is enough;
  controllable speed is MVP-006.

## Scope

The MVP includes:

* A live simulation runner that starts SUMO (headless or GUI) under TraCI control, with an
  empty network and the clock at 05:00.
* A spawn loop that adds individuals of all three modes over time at a fixed, configurable
  rate per mode, each with a mode-appropriate origin and destination.
* Removal of arrived individuals, and confirmation that the number of concurrent travellers
  stabilises.
* A replaceable "next individual" source (random, weighted toward the entry/exit edges),
  separated from the stepping loop.
* Replacing the MVP-004 traffic generation in the `simulator` command's run pipeline, with
  the static route generation removed from that path rather than kept as a parallel system.
* A way to run for a bounded time in tests and headless verification, so the "forever" loop
  is testable and CI never hangs.
* Tests for the new behaviour, keeping the coverage floor (ADR-004), and re-verification of
  earlier MVPs' criteria.

## Out of Scope

The following are deliberately excluded and belong to later MVPs:

* Speed control (0.5x–8x) and a visible clock — **MVP-006**. Here the loop just runs at a
  reasonable viewing pace.
* Statistics-driven behaviour: hourly departure profiles, mode shares, trip purposes —
  **MVP-007**. Here the spawn rate is constant over the day, so the clock at 05:00 has no
  effect on traffic yet.
* Zones, land use and destination attractiveness — **MVP-008**.
* Realistic population size and the core/municipality split — **MVP-009**.
* Persistent individuals with identities, homes, jobs and return trips — **MVP-010**. In
  this MVP an individual makes one trip and disappears.
* Rewinding, jumping in time, saving or resuming a run.
* Traffic signal timing checks, public transport, parking.
* Changing the network, the basemap or the entry/exit list.

## Acceptance Criteria

* Starting the simulation shows an empty city and a simulated time of 05:00; individuals
  then appear one at a time — verified programmatically (e.g. the number of active
  individuals at the first step is zero and grows afterwards) and visually in `sumo-gui`.
* Cars, bicycles and pedestrians are all spawned, each only on network parts that permit
  their mode, and each has a destination it actually reaches — verified by counting
  arrivals per mode over a bounded run.
* Arrived individuals are removed, and the concurrent count stabilises around a steady level
  instead of increasing throughout a bounded run of meaningful length — verified by
  sampling the count over time.
* A majority of car trips still start or end at one of the 8 curated entry/exit edges,
  measured on the live spawns as MVP-004 measured it on the route files.
* The runner has no built-in end time: the loop only stops when asked (window closed,
  interrupt) — with a bounded-run option so tests and CI terminate.
* The project owner watches it live in `sumo-gui` for a while and confirms it keeps
  running, keeps filling and emptying naturally, and reads as at least as busy as MVP-004.
* The MVP-004 static traffic-generation path is gone from the run pipeline, not left as a
  second option.
* Earlier acceptance criteria still hold: the network is unchanged (4,250 edges / 1,756
  junctions), the basemap and colours are unaffected, and the full `apps/simulator` test
  suite passes with coverage at or above the floor — confirmed by re-running them.

## Open Questions for the Plan

To be answered by checking, not by assuming:

* How does the loop behave against `sumo-gui` (pausing, closing the window, step pacing),
  and does the headless mode need a different exit path?
* How are reachable origin/destination pairs chosen per mode, and what happens when no route
  exists (retry, skip)?
* What spawn rate per mode gives roughly the MVP-004 density at steady state?
* Should the old `traffic.py` route-generation code be deleted now, or trimmed to the parts
  the new engine reuses (colours, weights)? Leaning toward deleting what is unused.
* Does replacing `randomTrips.py` warrant an ADR (TraCI-driven live engine versus
  pre-generated routes)? Expected yes.
