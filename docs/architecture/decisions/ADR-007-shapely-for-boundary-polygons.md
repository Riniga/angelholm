# ADR-007: Use `netconvert --keep-edges.in-geo-boundary` and `shapely` for outline-based network clipping

**Status:** Proposed
**Date:** 2026-09-18

## Context

MVP-002 (`docs/mvp/002-extended-map-area.md`) needs the simulated network clipped to a
hand-drawn coverage outline (`docs/architecture/mapoutline.png`), not just the rectangular
bounding box `fetch_osm_extract()` already uses. A rectangular bbox would include areas the
project owner explicitly asked to exclude (e.g. the rail/industrial strip west of the
outline).

Checked for real, not assumed:

- `netconvert --help` (installed `eclipse-sumo==1.27.1`, matching this repo's pin) exposes
  `--keep-edges.in-geo-boundary STR[]`, documented as: "Only keep edges which are located
  within the given boundary (given either as GEODETIC corner coordinates
  `<lon-min,lat-min,lon-max,lat-max>` or as polygon `<lon0,lat0,lon1,lat1,...>`)". This
  works directly in WGS84 lon/lat, matching the coordinates OpenStreetMap/`osmGet.py`
  already use — no separate projection step needed.
- No vector data for the drawn outline exists anywhere in the repo — only the raster
  `mapoutline.png`. Producing the polygon needed a real image-processing step
  (`scripts/extract_coverage_outline.py`): isolate the outline by its dominant color
  (confirmed by sampling actual pixel values — BGR `(21, 0, 136)`, ~5600 pixels, next most
  common candidate color over 100 pixels less common and belonging to the basemap's own
  road tones, not the outline), trace it as a contour, and simplify it.

## Decision

- Use **`netconvert --keep-edges.in-geo-boundary`** to clip the built network to the
  coverage-outline polygon, in addition to `fetch_osm_extract()`'s existing bounding-box
  fetch (the bbox still bounds what's *fetched* from Overpass; the geo-boundary flag then
  restricts what `netconvert` *keeps* to the actual outline shape).
- Use **`shapely`** (`>=2.0,<3`) as a real runtime dependency of the `simulator` package to
  represent, validate, and serialize that polygon (`simulator.network.load_boundary_polygon`
  reads the committed GeoJSON and hands `netconvert` a flat coordinate string). Chosen over
  hand-rolled polygon parsing because polygon validity (self-intersection, ring closure) is
  exactly the kind of thing worth a maintained library rather than ad hoc code, and because
  MVP-003 (map context features — water, land use) is expected to need general polygon/line
  geometry handling too, making this a reasonable place to introduce it once rather than
  per-MVP.
- Use **`numpy` + `opencv-python-headless`** as tooling-only dependencies (not imported by
  the `simulator` package) for the one-off outline-extraction script. `opencv` was chosen
  over alternatives (`scikit-image`, hand-rolled boundary tracing) because
  `cv2.findContours` + `cv2.approxPolyDP` are the standard, well-tested tools for exactly
  this "raster shape → ordered polygon" task; the headless variant avoids pulling in
  GUI/video libraries this repo never uses.

## Consequences

**Benefits:**

- The simulated network matches the project owner's actual intent (the drawn outline),
  verifiably — `scripts/extract_coverage_outline.py` also writes a debug overlay PNG so the
  extraction can be visually checked against the source drawing before it's ever used in a
  real `netconvert` run.
- No new geodata stack beyond what's justified: `shapely` is a light, common, well-licensed
  dependency; the heavier image-processing dependencies stay confined to a repo-root script,
  not the shipped `simulator` package.
- Reusable for MVP-003: the same `coverage-outline.geojson` / `shapely` polygon can constrain
  where water/land-use features are imported, without redoing this work.

**Trade-offs:**

- The outline is hand-traced from a raster image via color thresholding, not sourced from
  precise survey data — acceptable for this project's visualization/scope purpose (not a
  legal boundary), but real: a building or two at the very edge may fall on the wrong side.
- `opencv-python-headless` is a meaningfully sized dependency (tens of MB) for a one-off
  script; accepted because it isn't part of the deployed `simulator` package and is the
  standard tool for this exact job, not because its size doesn't matter.
- `shapely`'s licence (BSD-3-Clause) and `numpy`/`opencv-python-headless`'s (BSD-3-Clause /
  Apache Software License) were already present on this project's CI licence allowlist
  (`docs/standards/dependencies.md`) before this change — no allowlist update needed, but
  confirm this holds when CI's own `pip-licenses` run checks it for real.

## Alternatives considered

- **Bbox-only clipping (no outline polygon)**: rejected — explicitly not what the project
  owner asked for; would keep areas (e.g. the rail/industrial strip) they asked to exclude.
- **Manual digitization via an external GIS tool (e.g. geojson.io), by a human tracing the
  image by eye**: rejected as the primary path — not something an AI coding agent can
  execute as part of an implementable plan, and strictly less reproducible than a script
  that can be re-run if the source image ever changes.
- **`geopandas` instead of plain `shapely`**: rejected for now — this MVP only needs a
  single polygon's representation/validation, not `geopandas`'s tabular/CRS-management
  machinery; revisit if MVP-003's water/land-use work needs it.
