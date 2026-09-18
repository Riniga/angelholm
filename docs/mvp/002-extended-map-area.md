# MVP-002 – Extended Map Area

## Purpose

Grow the simulated area from MVP-001's small neighbourhood extract to the full area the
project owner actually wants to work with: central Ängelholm, as outlined in
`docs/architecture/mapoutline.png`.

MVP-001 proved the technical foundation on a deliberately small extract. This MVP proves
that same foundation scales to the intended working area before any further capability
(map context features, multimodal traffic, population) is built on top of it.

## Goals

* The simulation covers the outlined central-Ängelholm area, not just a small neighbourhood.
* Areas outside the outlined shape are excluded, not just cropped to its bounding box.
* The larger network is still routable and simulatable end to end.
* The project has confirmed the technical foundation holds at the intended working scale
  before later MVPs add more content on top of it.

## Context

`docs/architecture/mapoutline.png` shows the exact area the project owner wants covered,
hand-drawn over a map of Ängelholm. Its bounding box corners are:

* Upper left (NW): 56.255099, 12.849519
* Lower right (SE): 56.225986, 12.894902

That bounding box is a rough rectangle of roughly 3.2 km × 2.9 km — noticeably larger than
the MVP-001 extract (519 edges, 227 junctions) — and, as drawn, is not a rectangle: the
outline cuts across the bounding box's corners (e.g. dropping the industrial/rail area to
the west and land beyond Kungsgårdsleden to the south-east). The project owner asked
explicitly that surrounding areas outside the drawn outline be left out where possible,
not just clipped to the rectangular bbox.

This MVP is scoped to the road network and simulation only. Water, land use and other
non-routing map features (also visible in the outline) are deliberately deferred to
MVP-003, so that this MVP's only variable is geographic extent.

## Scope

The MVP includes:

* Fetching the OSM extract for the outlined area's bounding box.
* Clipping the network to the drawn outline polygon (not the raw bounding box), so areas
  outside the outline are excluded from the simulated network.
* Regenerating the routable road network (`netconvert`) for the larger area.
* Regenerating traffic (`randomTrips.py` / `duarouter`) at a volume appropriate to the
  larger network, reusing MVP-001's approach.
* Re-verifying, visually and programmatically, that the simulation runs to completion on
  the larger network.
* Updating any committed OSM/network fixtures and documented instructions to match the new
  area.

## Out of Scope

The following are deliberately excluded from this MVP:

* Water, land use, landmarks or any other non-routing map features (MVP-003).
* Buildings.
* Bicycles, pedestrians, public transport (later multimodal MVP).
* Realistic population or travel demand.
* Real traffic measurements or calibration.
* Road closures or infrastructure changes.
* Scenario comparison.
* Custom web interface or custom map visualization.

## Acceptance Criteria

* The simulated network covers the area outlined in `docs/architecture/mapoutline.png`.
* Areas outside the drawn outline (not just outside its bounding box) are excluded from
  the simulated network — verified by inspecting the network extent against the outline,
  not just against the bbox corners.
* The regenerated network loads successfully and is confirmed routable (`sumolib`, as in
  MVP-001).
* At least the same vehicle count as MVP-001 (14) can be simulated simultaneously on the
  larger network without errors.
* Vehicles follow valid routes through the larger network.
* The simulation can be observed visually while running, and the project owner confirms
  the visualized area matches the intended outline (e.g. against Google Maps or the
  outline image itself).
* The simulation reaches completion without manual intervention or simulation errors.
* A developer can regenerate and run the simulation for the new area using documented
  project instructions.
