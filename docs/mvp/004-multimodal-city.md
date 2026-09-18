# MVP-004 – Multimodal City

## Purpose

Move beyond a car-only simulation. MVP-001–003 only ever generate motor-vehicle traffic;
this MVP adds cyclists and pedestrians, and makes the traffic pattern itself a little more
realistic by biasing where trips start and end toward a curated set of real roads leading
into and out of the city, instead of picking uniformly among all 4,250 edges.

Traffic stays synthetic (randomly generated), not person-oriented — a synthetic
*population* with individual origins, destinations and daily schedules is explicitly a
later MVP (roadmap R2). This MVP is about adding transport modes and a basic sense of
"where trips come from", not about who is making them or why.

## Goals

* Cyclists and pedestrians move through the network alongside cars, each using the parts
  of the network appropriate to their mode (e.g. pedestrians on footways/sidewalks, not
  motorways), and in numbers that read as a small but genuinely busy city centre, not a
  token handful of each. MVP-001's original "at least 10 vehicles" bar was calibrated for
  a small neighbourhood extract (519 edges) — this network is 4,250 edges; a proportional
  floor is a better target than reusing that same number for every mode.
* Car volume (currently 40, from MVP-002's own visual-density tuning — see
  `simulator.traffic.DEFAULT_PERIOD`) is revisited in this MVP too, alongside the new
  modes, rather than left as the fixed backdrop cyclists/pedestrians are added around.
  All three modes should read as roughly comparable in visual presence, not have cars
  dominate just because they were tuned first.
* A curated, documented set of roughly 10 real edges — the city's main entries/exits —
  exists and is used to bias generated traffic toward realistic origins/destinations,
  instead of every trip being equally likely to start or end on any residential side
  street or footpath fragment.
* Still basic: independently generated random trips per mode (car / bicycle / pedestrian),
  reusing the same mechanism MVP-001 already established (`randomTrips.py`) rather than
  building new demand-modelling machinery. No synthetic population, no OD calibration
  against real counts, no mode-choice modelling. More traffic is a visual/density tuning
  choice, not a step toward realistic demand modelling — that stays out of scope.
* MVP-001/002/003's existing acceptance criteria still hold — this MVP adds traffic, it
  doesn't change the network or the map context.

## Context

Checked for real, not assumed, before committing to this scope:

* **Bicycle/pedestrian infrastructure is already usable in the committed network,
  without rebuilding it.** `netconvert`'s own OSM import already assigns sensible default
  permissions per road type even without SUMO's optional bicycle/pedestrian-specific type
  files: of the network's 4,250 edges, 3,739 allow bicycles and 4,115 allow pedestrians
  (only 1,668 allow cars — most edges are footways/cycleways/residential streets that
  legitimately exclude motor traffic). Confirmed via `sumolib`, not assumed from OSM tag
  presence alone.
* **`randomTrips.py` (already used by `simulator.traffic.generate_traffic()`) natively
  supports everything this MVP needs**, confirmed via its own `--help`:
  `--vehicle-class bicycle` generates bicycle trips with a correct `vType`;
  `--persontrips`/`--pedestrians` generates person/walk trips instead of vehicle trips;
  `--fringe-factor` (up to `max`, forcing *all* traffic to start/end at the network
  fringe) biases trip generation toward boundary edges. No new tool or dependency needed.
* **A precise "10 entries" list isn't ready to hand-pick yet.** The committed network
  doesn't carry OSM street names (`netconvert` needs `--output.street-names`, not passed
  when MVP-002 built it) — a small, real, addressable gap for the plan, not a blocker: it
  only means the plan needs an explicit step to add that flag and identify the real
  arterial roads (e.g. Kungsgårdsleden, Klippanvägen, Helsingborgsvägen, Kullavägen) by
  name, not by guessing edge IDs. A rough automated pass (edges that both allow cars and
  end at a low-degree/dead-end junction — a proxy for "the outline clipped through a real
  road here") already finds ~100 candidates purely geometrically; narrowing that to ~10
  named, genuinely arterial roads is a real but bounded curation task.

## Scope

The MVP includes:

* Generating bicycle trips (`randomTrips.py --vehicle-class bicycle`) over the parts of
  the network that allow bicycles.
* Generating pedestrian trips (`randomTrips.py --persontrips`/`--pedestrians`) over the
  parts of the network that allow pedestrians.
* Running all three modes (car, bicycle, pedestrian) together in the same simulation.
* Defining and committing a curated list of roughly 10 real city entry/exit edges
  (identified by street name, not guessed), and using it to bias trip generation for at
  least car traffic toward those edges as origins/destinations.
* Keeping headless and GUI runs both working, and MVP-001/002/003's own acceptance
  criteria (network unchanged, headless completes, full test suite passing) re-verified,
  not assumed to still hold just because this MVP is additive.

## Out of Scope

The following are deliberately excluded from this MVP:

* A synthetic population — individual people with origins, destinations, departure times
  and daily schedules (roadmap R2, later MVPs). This MVP's traffic is still randomly
  generated per mode, not person-oriented.
* Full Traffic Analysis Zones (TAZ) with an origin-destination demand matrix between
  zones. "Zones" here means a curated list of entry/exit *edges*, not a zone-to-zone
  demand model.
* Calibrating trip volumes or entry/exit weighting against real traffic counts.
* Mode choice (a "person" choosing car vs. bike vs. walking) — each mode's trips are
  generated independently, not from a shared decision process.
* Public transport, parking, traffic signals as a distinct concern (already out of scope
  for earlier MVPs, unchanged here).
* Rebuilding the network's own extent or map context — MVP-002/003 stay exactly as they
  are; only traffic generation changes.

## Acceptance Criteria

* At least 60 bicycle trips and at least 80 pedestrian trips are generated and simulated
  simultaneously alongside at least 80 car trips, each using only network parts that
  permit that mode — verified programmatically (e.g. via `sumolib`/route-file
  inspection), not just eyeballed. (Floors, not targets: pedestrians set highest since
  they're typically the most numerous mode in a walkable town centre; cars roughly
  doubled from MVP-002's 40. Tune upward during implementation if the network still
  looks sparse with all three modes running — these are a starting point, not a ceiling.)
* A committed, documented list of roughly 10 real, named city entry/exit edges exists,
  and a majority of generated car trips start or end at one of them — verified by
  inspecting the generated route file's origin/destination edges against that list.
* The simulation (all three modes together) reaches completion without manual
  intervention or simulation errors, headless.
* The project owner visually confirms, in `sumo-gui`, that cyclists and pedestrians are
  visibly present and moving distinctly from car traffic.
* MVP-001/002/003's existing acceptance criteria still hold: the network is unchanged
  (same edge/junction counts), the map-context background is unaffected, and the full
  `apps/simulator` test suite still passes — confirmed by actually re-running them.
