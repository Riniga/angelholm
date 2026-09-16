# MVP-001 – First Traffic Simulation

## Purpose

Establish the smallest possible working foundation for the project by proving that traffic can be simulated on a real-world road network.

The result should be something we can actually run and observe, rather than only an architectural or technical proof of concept.

## Goals

* A small real-world area can be represented as a routable road network.
* Multiple vehicles can travel through that network simultaneously.
* The simulation can be started repeatedly and observed visually.
* The project has a working technical foundation that later MVPs can extend.

## Context

The project currently contains the vision, roadmap and initial architecture, but no executable mobility simulation.

The architecture identifies geographic data, a mobility simulation engine and orchestration as the likely initial foundation.

This MVP is the first validation that those concepts can form a working system.

## Scope

The MVP includes:

* One small, selected real-world geographic area.
* The area's road network.
* Motor vehicles travelling between different locations in the network.
* Routing of vehicles through the network.
* A visual representation where the road network and moving vehicles can be observed.
* A repeatable way to start the simulation from the project workspace.

The traffic may be synthetic and does not need to represent actual traffic volumes or travel behaviour.

## Out of Scope

The following are deliberately excluded from this MVP:

* Realistic population or travel demand.
* Individual people or households.
* Bicycles.
* Pedestrians.
* Public transport.
* Buildings, water, parks and other map features that are not required for traffic simulation.
* Real traffic measurements.
* Traffic calibration.
* Road closures or infrastructure changes.
* Scenario comparison.
* Custom web interface.
* Custom map visualization.
* Traffic analysis or advanced statistics.

These capabilities belong in later MVPs. The purpose of MVP-001 is only to establish a working simulation foundation.

## Acceptance Criteria

* A real-world road network for the selected area is loaded into the simulation.
* At least 10 vehicles can be simulated simultaneously on that network.
* Vehicles follow valid routes through the road network.
* The simulation can be observed visually while it is running.
* The simulation reaches completion without manual intervention or simulation errors.
* A developer can start the simulation again using documented project instructions.

## Outcome at close (2026-09-16)

Closed as **delivered** — all six criteria met, each verified for real, not asserted:

* **A real-world road network for the selected area is loaded into the simulation.** Met.
  A real OpenStreetMap extract for a verified bbox in central Ängelholm (confirmed against
  Google Maps by the project owner), converted via `netconvert` into a network — **241
  edges, 120 junctions** — loaded back and checked via `sumolib`.
* **At least 10 vehicles can be simulated simultaneously.** Met. **14 vehicles**, fixed
  `seed=42` for reproducibility, verified programmatically (not just eyeballed).
* **Vehicles follow valid routes through the road network.** Met. Routed via `duarouter`
  (through `randomTrips.py --validate`), not raw origin-destination pairs.
* **The simulation can be observed visually while it is running.** Met — confirmed
  directly by the project owner in `sumo-gui`. One real usability issue found and fixed
  along the way: the default playback ran 200 simulated seconds in a couple of real
  seconds, too fast to actually watch — a `<gui_only><delay value="200"/></gui_only>`
  section in the generated `.sumocfg` fixed this (ignored by headless `sumo`, confirmed).
* **The simulation reaches completion without manual intervention or simulation errors.**
  Met. `simulator.simulate.run_headless()` confirmed `"Simulation completed successfully"`
  for real, multiple times.
* **A developer can start the simulation again using documented project instructions.**
  Met. `pip install -e apps/simulator` then `simulator` (or `simulator --headless`) — a
  real console command, confirmed working end-to-end from the command line, not just
  through test mocks.

**Real bugs found and fixed along the way, not anticipated when this MVP/plan were
written:**

* The public Overpass server returned a genuine `HTTP 504 Gateway Timeout` on the first
  fetch attempt — added retries to `fetch_osm_extract()`.
* `randomTrips.py` silently dropped an intermediate `trips.trips.xml` file at the repo
  root (wherever the process's working directory happened to be), not next to the route
  file — pinned explicitly via an added `-o` argument.
* `pytest-cov` had never actually been installed, despite `docs/standards/testing.md` and
  `ci.yml` both assuming it — masked until now by `GAP-E2-CICHAIN` failing that CI job
  earlier for an unrelated reason. Added as a real dependency.
* `ci.yml` had 3 remaining `<placeholder>` bugs (`GAP-E2-CICHAIN`) causing a shell syntax
  error on every run, closed once `apps/simulator` existed to give them real values.
* A committed OSM fixture (547 KB) tripped `check-added-large-files`' 500 KB default —
  raised to 600 KB, documented, not disabled.

**Also closed while at it:** `GAP-D1-COVERAGE` — a real coverage baseline (99.13%) was
measured once the MVP was functionally complete, and the floor set to 95% (`ADR-004`).

**Not yet confirmed:** the 3 CI jobs `GAP-E2-CICHAIN` fixed (`SAST`, `Dependencies`, `Run
tests`) have only been verified locally (Ruff, `pytest --cov`) — not yet seen green on a
real GitHub Actions run. Add them as required status checks on the `main-protection`
ruleset only after that's confirmed.
