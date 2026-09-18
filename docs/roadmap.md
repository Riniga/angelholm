# Roadmap

This roadmap describes the major development stages and capabilities planned for the urban mobility simulation project.

Each roadmap area is implemented through one or more MVPs. Once an MVP has been created, it becomes the source of truth for that work — this file should stay a lightweight index, not a duplicate of MVP content. See `docs/development/methodology.md` "Roadmap".

---

## Current Status

The project is in its initial exploration and foundation phase. The current focus is to establish a working simulation based on a real city map, generate traffic, visualize movement and verify that the simulation can be manipulated and measured.

---

## R0 – Foundation (Planned)

Close the gap between the generic project skeleton this workspace was bootstrapped from and
a working, internally consistent, policy-compliant starting point, before any application
code is written. Numbered `R0`/`MVP-000` — before R1 — so it never collides with the
roadmap's own MVP numbering.

* **MVP-000 – Workspace Foundation** — A real, verified local environment; the
  already-in-force tooling/process decisions recorded as ADRs; a first honest
  methodology-compliance baseline; repository settings applied or tracked.

---

## R1 – Living City (Planned)

Establish the basic simulation environment and prove that a real city can be represented and simulated.

* **MVP-001 – First Traffic Simulation** — Import a selected real-world area, create a routable network, generate traffic and run a visual simulation.
* **MVP-002 – Extended Map Area** — Grow the road network from MVP-001's small neighbourhood
  extract to the full outlined coverage area of central Ängelholm
  (`docs/architecture/mapoutline.png`: NW 56.255099, 12.849519 — SE 56.225986, 12.894902),
  clipped to the drawn outline rather than the raw bounding box so surrounding areas
  outside it are excluded. Network/routing/traffic logic only — no new map features.
* **MVP-003 – Map Context Features** — Import water, land use/land cover and other
  non-routing geographic features for the extended area, so the visualisation reads as
  recognisably Ängelholm. Visual context only — does not change routing or traffic
  behaviour.
* **MVP-004 – Multimodal City** — Introduce cars, cyclists and pedestrians using the appropriate parts of the network.

---

## R2 – People and Daily Mobility (Planned)

Move from generated traffic to a population whose individual travel needs create the traffic.

* **MVP-005 – Synthetic Population** — Introduce people with origins, destinations, departure times and available transport modes.
* **MVP-006 – Daily Travel Patterns** — Allow people to perform multiple trips representing simplified daily activities such as home, work, school and leisure.

---

## R3 – What-if Simulation (Planned)

Enable controlled experiments with the city's infrastructure.

* **MVP-007 – Road Closure Experiment** — Close or restrict a road and allow affected traffic to adapt.
* **MVP-008 – Scenario Comparison** — Run identical populations against different infrastructure scenarios and compare the results.

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
