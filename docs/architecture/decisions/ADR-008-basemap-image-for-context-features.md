# ADR-008: Use the project owner's own basemap image as a georeferenced sumo-gui background

**Status:** Proposed
**Date:** 2026-09-18

## Context

MVP-003 (`docs/mvp/003-map-context-features.md`) needs `sumo-gui` to show recognisable
water and land-use context alongside the road network built in MVP-001/002, without
changing routing, traffic generation, or any headless simulation output.

Two mechanisms were tried and rejected before landing on this one — both real attempts,
not hypothetical:

1. **`polyconvert` with a trimmed, discard-by-default type file**, referenced directly via
   `.sumocfg`'s `<additional-files>`. Rejected after a real defect was found by actually
   loading the result: one `water`-typed shape's points spanned net coordinates from
   inside the network all the way out to `(8551, -2335)` — 310 points, almost certainly
   the Skälderviken coastline/bay, tagged as a single OSM relation extending far beyond
   the coverage area. `polyconvert` can only **keep or discard a whole shape**, never
   clip its geometry — confirmed by testing `--prune.in-net` (drops shapes that don't
   touch the network boundary *at all*, but still keeps any shape that merely overlaps
   it, unclipped). No `polyconvert` flag combination truncates an oversized shape.
2. **Rendering `polyconvert`'s shapes ourselves**, clipping each one to
   `docs/architecture/coverage-outline.geojson`'s polygon via `shapely` before drawing
   with `Pillow`. This fixed the coastline leak (verified with dedicated tests), but the
   project owner reviewed the rendered result in `sumo-gui` and found it incomplete — the
   river rendered as disconnected fragments rather than a continuous line, because OSM's
   `waterway` tagging for that stretch isn't a single continuous way. Rebuilding a
   reliable schematic map from raw OSM tagging turned out to be a materially bigger
   problem than "clip a shape to a polygon".

The project owner already had exactly what was needed: real, complete basemap screenshots
of the area (`docs/architecture/map_plain.gif`, `map_with_border.gif`) — the same kind of
image `docs/architecture/mapoutline.png` (MVP-002's own coverage-outline source) was drawn
over. Checked for real:

- `sumo-gui` supports a georeferenced background image (a `<decal>` element in a
  view-settings XML, loaded via `--gui-settings-file`) — confirmed via SUMO's own bundled
  example (`tools/game/bs3d/view_B.xml`). It is GUI-only: headless `sumo` never reads
  view-settings files.
- A `<decal>`'s placement only needs the image's own geographic corners (given by the
  project owner: NW 56.255790, 12.833104 / SE 56.224411, 12.907042) converted to the
  network's coordinate system — the same `sumolib`/`pyproj` mechanism already used
  elsewhere, and independent of the image's pixel dimensions.

## Decision

Convert `docs/architecture/map_plain.gif` once to
`apps/simulator/data/context-background.png` (via the small, re-runnable
`scripts/convert_context_background.py`, committed as a static asset like
`mapoutline.png`). `simulator.context_features.write_gui_settings()` computes the decal's
placement from the image's own known corners (`IMAGE_NW_LAT_LON`/`IMAGE_SE_LAT_LON`
module constants) converted via `sumolib.net.readNet(...).convertLonLat2XY()`, and
`simulator.simulate.run_gui()` passes the resulting view-settings file via
`--gui-settings-file`. `run_headless()` and `.sumocfg` itself are untouched.

The project owner flagged that the geographic-corner placement might not align
pixel-perfectly with the network (e.g. minor screenshot-crop imprecision) — confirmed for
real: the corner-only placement was visibly shifted and slightly mis-scaled in `sumo-gui`.
Rather than building a calibration UI, `write_gui_settings()` exposes `MANUAL_OFFSET_X`,
`MANUAL_OFFSET_Y`, `MANUAL_SCALE_X`, `MANUAL_SCALE_Y`, and `MANUAL_ROTATION` module
constants, applied on top of the geographic-corner computation (not as absolute net-XY
values), so they stay valid if the network is ever rebuilt at a different offset. The
project owner derived the actual values using `sumo-gui`'s own built-in decal editor
(view settings → Background tab): nudge the image live, read back the resulting
`centerX`/`centerY`/`width`/`height`/`rotation`, and the constants are the delta between
that and this module's own geographic-corner computation.

`polyconvert`, `shapely`-based clipping, and `Pillow`-based rendering are **removed**
entirely for this purpose — they solved a problem (deriving a schematic map from raw OSM
data) that no longer needs solving now that a real, complete map image is used directly.
`shapely` remains a dependency for an unrelated reason (MVP-002's network-clipping
polygon, `ADR-007`). `Pillow` remains, but only as a tooling-only dependency for the
one-off GIF→PNG conversion script, not a `simulator` runtime dependency.

## Consequences

**Benefits:**

- Structurally avoids both defects found in the rejected approaches: no shape-clipping
  geometry needed (nothing is derived from OSM shapes at all), and no missing/fragmented
  features (a real map has no "missing waterway tag" problem).
- Much simpler pipeline: one conversion script + one placement function, replacing a
  three-stage `polyconvert` → clip → rasterize pipeline.
- Built-in, low-effort manual correction path (`MANUAL_OFFSET_X`/`MANUAL_OFFSET_Y`/
  `MANUAL_SCALE_X`/`MANUAL_SCALE_Y`/`MANUAL_ROTATION`) for the project owner to tune
  themselves using `sumo-gui`'s own decal editor if the automatic corner-coordinate
  placement isn't pixel-perfect — used for real, not just designed speculatively.
- Smaller runtime dependency footprint: `simulator` only gains `pyproj` (MIT) as a real
  dependency for this feature; `Pillow` (`MIT-CMU`, approved 2026-09-18) is tooling-only.

**Trade-offs:**

- The background is a static image, not derived from live OSM data — if the project
  owner wants the background to reflect future map changes, it needs re-screenshotting
  and re-running the conversion script, not just a `simulator --rebuild-network`.
- Loses any notion of "shape type" the road network could otherwise query — this was
  already true of the rejected rendered-image approach, but doubly true here: the
  background is one flat picture, not even self-drawn shapes.
- `apps/simulator/data/context-background.png` (~1.7 MB) and the project owner's other
  committed map reference images/PSD (`docs/architecture/map*.gif`, `map.psd`, ~8.3 MB
  combined) are real weight added to the repo — `check-added-large-files`' threshold was
  raised twice more (600 KB → 2000 KB → 6500 KB, `.pre-commit-config.yaml`), the same
  documented pattern as MVP-001's OSM fixture.

## Alternatives considered

- **`polyconvert` referencing raw shapes via `<additional-files>`**: rejected — the
  coastline-leak defect (see Context).
- **`polyconvert` + `shapely`-clipped, self-rendered PNG**: rejected — fixed the
  coastline leak but produced a visually incomplete map (fragmented river), found by the
  project owner's own visual review, not assumed.
- **Fetching a live basemap tile service (e.g. via `contextily`)**: not pursued — adds a
  live network dependency and tile-usage licensing questions for no benefit over an
  image the project owner already had on hand.
