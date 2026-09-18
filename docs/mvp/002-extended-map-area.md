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

## Outcome at close (2026-09-18)

Closed as **delivered** — all acceptance criteria met, each verified for real, not asserted.

* **The simulated network covers the area outlined in `mapoutline.png`.** Met. Built via
  `netconvert --keep-edges.in-geo-boundary` against a digitized version of the drawn
  outline (`scripts/extract_coverage_outline.py`,
  `docs/architecture/coverage-outline.geojson`) — **4,250 edges, 1,756 junctions**, up from
  MVP-001's 519/227.
* **Areas outside the drawn outline (not just outside its bounding box) are excluded.**
  Met, checked two ways: programmatically, of all 4,250 edges only 14 (0.3%) have a
  midpoint falling outside the outline polygon even with a 50 m tolerance buffer, and all
  four bounding-box corners plus spot-checked points near the excluded rail/industrial
  strip confirmed outside the polygon via `shapely`; visually, the project owner confirmed
  the `sumo-gui` extent against `mapoutline.png` directly (see below).
* **The regenerated network loads successfully and is confirmed routable.** Met — loaded
  and inspected via `sumolib.net.readNet`, as MVP-001 did.
* **At least MVP-001's vehicle count (14) can be simulated simultaneously.** Met and
  exceeded: **40 vehicles**. MVP-001's `DEFAULT_PERIOD=15.0` would have produced only ~14
  vehicles on a network ~8x larger by edge count — visibly sparse — so `DEFAULT_PERIOD` was
  tuned to `5.0`, a deliberate, documented judgement call (`simulator/traffic.py`), not a
  correctness fix.
* **Vehicles follow valid routes through the larger network.** Met — same `randomTrips.py
  --validate` / `duarouter` mechanism as MVP-001, unchanged.
* **The simulation can be observed visually, and the project owner confirms the visualized
  area matches the intended outline.** Met — confirmed directly by the project owner in
  `sumo-gui` against `docs/architecture/mapoutline.png`.
* **The simulation reaches completion without manual intervention or simulation errors.**
  Met. `simulator --headless` reported `"Simulation completed successfully"` for real.
* **A developer can regenerate and run the simulation using documented project
  instructions.** Met — `simulator --rebuild-network` (fetch + outline-clipped build) and
  plain `simulator` / `simulator --headless`, all run for real, not just through test mocks.

**Decisions and real findings along the way, not anticipated when this MVP/plan were
written:**

* The coverage outline has no source vector data anywhere — only the raster
  `mapoutline.png`. Rather than manual GIS tracing (not something an AI coding agent can
  execute), `scripts/extract_coverage_outline.py` isolates the hand-drawn outline by its
  dominant color (confirmed by sampling real pixel values, not guessed), traces it via
  OpenCV contour detection, and converts pixel coordinates to lon/lat using the image's own
  known corners. Verified by eye against a generated debug overlay
  (`docs/architecture/coverage-outline-check.png`) before ever being used in a real
  `netconvert` run.
* `netconvert --keep-edges.in-geo-boundary` (confirmed present via `netconvert --help` on
  the installed `eclipse-sumo==1.27.1`) clips directly in WGS84 lon/lat — no separate
  projection step was needed, simpler than the plan's own fallback contingency anticipated.
* The network fixtures grew substantially: `angelholm_bbox.osm.xml` 379 KB → 4.3 MB,
  `network.net.xml` ~1.0 MB → 8.6 MB. Both are already-tracked (not newly-added) files, so
  `check-added-large-files`' 600 KB threshold didn't block the commit — confirmed by
  actually running `pre-commit` against the staged files, not assumed; this is the same
  known hook limitation MVP-001 already documented (`.pre-commit-config.yaml`'s own
  comment), holding again rather than being a new bug.
* `apps/simulator/data/angelholm.rou.xml`/`.sumocfg`/`.trips.xml` are gitignored,
  deterministic outputs of `simulator`'s own code (an MVP-001 decision) — regenerating them
  for the new area needed no fixture-file changes at all, only the tracked
  `network.net.xml`/`angelholm_bbox.osm.xml`.
