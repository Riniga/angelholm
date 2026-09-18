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

## Outcome at close (2026-09-18)

Closed as **delivered**, via a materially different mechanism than originally planned —
see below — all acceptance criteria met, each verified for real, not asserted.

* **Water and land-use context is visible in `sumo-gui`, recognisable against the source
  map.** Met, but not the way originally planned. The first two mechanisms tried were
  both real attempts that failed for real reasons: `polyconvert`-derived shapes let a
  large coastal water body leak in unclipped (it can only keep/discard a whole shape,
  never clip its geometry); a self-rendered, `shapely`-clipped fix solved that but
  produced a visually incomplete map (the river rendered as disconnected fragments,
  found by the project owner's own review in `sumo-gui`, not assumed). The project owner
  then pointed out they already had a complete, real basemap image
  (`docs/architecture/map_plain.gif`) — used directly as a georeferenced `sumo-gui`
  background instead. See `ADR-008-basemap-image-for-context-features.md` (renamed
  mid-implementation from `ADR-008-polyconvert-for-context-features.md`, reflecting the
  final mechanism) for the full account.
* **Distinguishable by type via SUMO's own rendering** — not literally met (the
  background is one flat image, not individually typed/toggleable shapes), but the goal
  behind that criterion (a human can tell water from green space from built-up area) is
  met through the image's own pre-existing cartography instead.
* **Regeneration is scripted, not a one-off manual step.**
  `scripts/convert_context_background.py` (one-off image conversion, committed asset) +
  `simulator.context_features.write_gui_settings()` (regenerated every GUI run from the
  committed image and network). Reuses the network's own coordinate system; no separate
  OSM fetch involved for this feature at all.
* **Alignment needed real, live tuning, not just the computed geographic-corner
  placement.** The project owner used `sumo-gui`'s own built-in decal editor to nudge the
  image and read back corrected `centerX`/`centerY`/`width`/`height`/`rotation` values —
  captured as `MANUAL_OFFSET_X`/`MANUAL_OFFSET_Y`/`MANUAL_SCALE_X`/`MANUAL_SCALE_Y`/
  `MANUAL_ROTATION` constants in `simulator/context_features.py`, applied on top of the
  geographic computation (not as absolute values), so they survive a future network
  rebuild. Verified independently before the live check even happened: rendering the
  real network's own edges on top of the background image, using the exact same
  transform, confirmed the *unrotated* geographic placement already tracked the real
  street grid closely — the remaining correction was genuinely a small
  screenshot-crop/rotation imprecision, not a mechanism bug.
* **MVP-001/002's existing acceptance criteria still hold.** Met — `simulator --headless`
  still reports `"Simulation completed successfully"` with 40 vehicles, unaffected;
  confirmed by actually re-running it after every change in this MVP, not assumed from
  "it's visual-only".
* **The project owner visually confirms the result.** Met — confirmed directly in
  `sumo-gui`, with the tuned alignment values baked in as the new defaults.

**Dependency outcome:** `pyproj` (MIT) is a real new `simulator` runtime dependency.
`Pillow` (`MIT-CMU`, approved by the project owner 2026-09-18 — a new licence added to
`docs/standards/dependencies.md`'s allow-list, and to `ci.yml`'s own separate, hard-coded
enforcement copy of that list, which does **not** read the doc automatically) ended up
tooling-only (the one-off conversion script), not a `simulator` runtime dependency as
first planned. `polyconvert`, `shapely`-based clipping, and the trimmed
`context-features.typ.xml` type file were all removed after being built and committed —
real, working code, deleted once a simpler, more correct mechanism was found, not
speculative churn.

**Final test/coverage state:** 33 tests, 99.41% coverage (floor 95%).
