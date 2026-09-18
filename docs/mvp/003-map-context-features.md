# MVP-003 – Map Context Features

## Purpose

Make the simulation's visualization recognisable as Ängelholm, not just an abstract road
graph. MVP-002 grew the network to the full outlined coverage area, but the `sumo-gui` view
is still a bare grey mesh of edges and junctions with nothing to visually orient against.

This MVP adds non-routing geographic context — water, land use/land cover, and similar
features — purely so a human looking at the running simulation recognises the place. It
does not change what the simulation computes.

## Goals

* The `sumo-gui` view for the MVP-002 coverage area shows recognisable context — at least
  the river/water running through central Ängelholm and the broad land-use pattern
  (built-up areas, green space) — alongside the existing road network.
* Adding this context does not change routing, traffic generation, or any simulation
  output — verified, not just assumed, since a regression here would silently invalidate
  MVP-001/002's acceptance criteria.
* The mechanism for importing context features is reusable, so later MVPs (buildings,
  landmarks, etc. — see the roadmap backlog) can extend the same pipeline instead of
  building a new one.

## Context

`docs/architecture/mapoutline.png` — the same image MVP-002 digitized a coverage outline
from — already shows the kind of context this MVP should reproduce inside the simulation:
the Rönneå river, green parks, and the built-up town centre, all visible on the basemap
around the drawn outline.

SUMO ships a purpose-built tool for exactly this: `polyconvert` (bundled with
`eclipse-sumo`, alongside `netconvert`), which reads the same raw OSM extract MVP-001/002
already fetch and converts non-routing OSM features (water, landuse, buildings, ...) into a
`.poly.xml` shapes file that `sumo-gui` renders on top of the road network. SUMO also ships
a ready-made OSM type mapping for this
(`osmPolyconvert.typ.xml`, confirmed present in this environment's installed
`eclipse-sumo==1.27.1`) — the standard, documented way to do this, not something this
project needs to invent. `sumo`'s headless simulation engine does not read or use these
shapes at all — they are display-only, which is what makes this MVP visual-context-only by
construction, not just by intent.

## Scope

The MVP includes:

* Importing water features (rivers, streams) for the MVP-002 coverage area.
* Importing broad land-use/land-cover categories (e.g. residential, green space,
  industrial) for the same area.
* Rendering these alongside the existing road network in `sumo-gui`.
* Keeping this reproducible via the project's existing `--rebuild-network`-style workflow,
  from the same OSM extract already fetched for the network build.

## Out of Scope

The following are deliberately excluded from this MVP:

* Buildings (left for a later, separate MVP per the roadmap backlog — a materially bigger
  import than water/land use).
* Named landmarks, points of interest, or labels.
* Any change to routing, network topology, or traffic behaviour — MVP-002's network build
  stays exactly as it is.
* Any change to what the *headless* simulation computes or outputs — this MVP only affects
  what a human sees in `sumo-gui`.
* A custom web interface or custom map rendering (still out of scope, per the original
  MVP-001 scope decision — this MVP works entirely within `sumo-gui`).
* Public transport, parking, or any other roadmap-backlog item not directly about visual
  recognisability.

## Acceptance Criteria

* Water features for the MVP-002 coverage area are visible in `sumo-gui`, in a position and
  shape a human can recognise against `docs/architecture/mapoutline.png` (e.g. the Rönneå
  river's path through the area).
* Land-use/land-cover context is visible in `sumo-gui` for the same area, distinguishable
  by type (e.g. built-up vs. green space) via SUMO's default rendering.
* Regenerating this context is scripted/documented, not a one-off manual step, and reuses
  the OSM extract already fetched for the network build rather than a separate fetch.
* MVP-001's and MVP-002's existing acceptance criteria still hold after this change: the
  same network (edge/junction counts unchanged), the same headless simulation behaviour
  (`"Simulation completed successfully"`), and the full `apps/simulator` test suite still
  passing — confirmed by actually re-running them, not assumed from "it's visual-only".
* The project owner visually confirms, in `sumo-gui`, that the rendered context makes the
  area recognisable as Ängelholm.
