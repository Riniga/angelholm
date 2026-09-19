# Roadmap

This roadmap describes the major development stages and capabilities planned for the urban mobility simulation project.

Each roadmap area is implemented through one or more MVPs. Once an MVP has been created, it becomes the source of truth for that work — this file should stay a lightweight index, not a duplicate of MVP content. See `docs/development/methodology.md` "Roadmap".

---

## Current Status

MVP-000 through MVP-004 are delivered: a working, visual simulation of central Ängelholm exists with car, bicycle and pedestrian traffic on a real, outline-clipped road network. The next focus is a live, statistics-driven agent engine (R2) and then infrastructure what-if experiments (R3).

---

## R0 – Foundation (Delivered)

Close the gap between the generic project skeleton this workspace was bootstrapped from and
a working, internally consistent, policy-compliant starting point, before any application
code is written. Numbered `R0`/`MVP-000` — before R1 — so it never collides with the
roadmap's own MVP numbering.

* **MVP-000 – Workspace Foundation** — A real, verified local environment; the
  already-in-force tooling/process decisions recorded as ADRs; a first honest
  methodology-compliance baseline; repository settings applied or tracked.

---

## R1 – Living City (Delivered)

Establish the basic simulation environment and prove that a real city can be represented and simulated.

* **MVP-001 – First Traffic Simulation** — Import a selected real-world area, create a routable network, generate traffic and run a visual simulation.
* **MVP-002 – Extended Map Area** — Grow the road network from MVP-001's small neighbourhood
  extract to the full outlined coverage area of central Ängelholm
  (`docs/architecture/mapoutline.png`: NW 56.255099, 12.849519 — SE 56.225986, 12.894902),
  clipped to the drawn outline rather than the raw bounding box so surrounding areas
  outside it are excluded. Network/routing/traffic logic only — no new map features.
* **MVP-003 – Map Context Features** — Show a real, georeferenced basemap image behind the
  network in `sumo-gui` so the visualisation reads as recognisably Ängelholm (an
  OSM-shape-based approach was tried and rejected — see ADR-008). Visual context only —
  does not change routing or traffic behaviour.
* **MVP-004 – Multimodal City** — Introduce cars, cyclists and pedestrians using the appropriate parts of the network, generated independently per mode (still synthetic, not population-based) and biased toward a curated set of real city entry/exit edges rather than spread uniformly across the whole network.

---

## R2 – People and Daily Mobility (Planned)

Move from generated traffic to a population whose individual travel needs create the traffic.

The simulation becomes **live**: Ängelholm starts empty at about 05:00, and a single TraCI-driven control loop keeps adding people (in a vehicle, on a bicycle or on foot) one at a time, each with a destination, and removes them once they arrive. It can run indefinitely; time cannot be rewound or skipped. Only the *patterns* need to be reproducible, not the exact individuals (an optional seed remains for debugging). The agent engine starts deliberately simple (random) and becomes more realistic with each MVP.

* **MVP-005 – Live Agent Engine** — Replace the static pre-generated routes with a TraCI loop that starts from an empty city at 05:00, spawns individuals with a mode, origin and destination, removes arrived ones, and runs forever. Random origins/destinations (still biased toward the curated entry/exit edges) at a fixed spawn rate giving roughly today's ~200 concurrent travellers. Replaces the MVP-004 traffic generation.
* **MVP-006 – Simulation Speed Control** — A simulation clock and adjustable speed (0.5x, 1x, 2x, 4x, 8x) while running live. Basic control is enough; no rewind or time jumps.
* **MVP-007 – Statistics Database** — Replace hard-coded randomness with a data-driven statistics layer (departures per hour of day, mode shares, trip-purpose mix) that can be changed without touching code, so spawn rates follow a daily rhythm (quiet nights, rush hours).
* **MVP-008 – Zones and Destination Attractiveness** — Identify zones (housing, work, retail, school, centre) from map data and weight origins and destinations by zone, so busy places are busy for a reason instead of by chance (no more "the small street is the busiest").
* **MVP-009 – Realistic Population Scale** — Scale the number of travellers to realistic levels, distinguishing the built-up core from the wider municipality (~40,000 inhabitants; traffic from outside enters via the entry/exit roads).
* **MVP-010 – Daily Travel Patterns** — Give individuals persistent identity and simplified daily plans (home → work/school → leisure → home) instead of independent one-off trips. Exact scope to be decided when this MVP is defined, after MVP-005–009 show what the engine needs.

---

## R3 – What-if Simulation (Planned)

Enable controlled experiments with the city's infrastructure.

* **MVP-011 – Road Closure Experiment** — Close or restrict a road and allow affected traffic to adapt.
* **MVP-012 – Scenario Comparison** — Run identical populations against different infrastructure scenarios and compare the results.

---

## R4 – Realistic City Model (Planned)

Increase the realism of the simulation using better data and behavioural models.

Potential capabilities include:

* More realistic traffic volumes and departure patterns.
* Traffic lights, speed limits and road capacity.
* Improved transport mode selection.
* Public transport.
* Parking.
* More realistic population and destination distributions.

MVPs are defined when this roadmap area becomes active.

---

## R5 – Mobility Laboratory (Planned)

Turn the simulation into an interactive environment for exploring changes to the city.

Potential capabilities include:

* Interactive city map.
* Create and modify scenarios.
* Close, open or modify roads.
* Run simulations from the interface.
* Visualize congestion and traffic flows.
* Compare scenarios and key metrics.
* Inspect individual journeys and their consequences.

MVPs are defined when this roadmap area becomes active.

---

## Backlog of ideas to be implemented / fixed

* Import buildings, water, parks and other geographic features for visualization.
* Model households and vehicle ownership.
* Schools, workplaces, shops and leisure destinations.
* Rush-hour profiles.
* Weather scenarios.
* Road works and temporary restrictions.
* Accidents and other disturbances.
* Bicycle infrastructure experiments.
* New roads and changed intersections.
* Traffic-light optimization.
* Public transport routes and timetables.
* Parking availability.
* Emissions and environmental impact.
* Historical or measured traffic data for calibration.
* Large-scale simulations covering the entire municipality.

---

## Maintaining the Roadmap

* Update "Current Status" whenever a roadmap area's status changes.
* Add a new `## R<n> – <Area>` section when a genuinely new phase starts; don't retrofit history into it.
* Keep MVP links current — an MVP is the source of truth for its own scope, this file just points at it.
