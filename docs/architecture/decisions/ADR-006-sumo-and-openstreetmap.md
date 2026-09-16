# ADR-006: Use SUMO and OpenStreetMap as the simulation engine and geographic data source

**Status:** Proposed
**Date:** 2026-09-16

## Context

`docs/architecture/overview.md` named SUMO and OpenStreetMap as *candidates* for the
mobility simulation engine and geographic data source, but nothing had verified either
would actually work before MVP-001 needed to commit to a mechanism
(`docs/plans/001-first-traffic-simulator.plan.md`'s Investigation section).

Checked for real, not assumed:

- No SUMO installation, `SUMO_HOME`, or related Python packages existed in the `angelholm`
  environment beforehand.
- **conda-forge's package literally named `sumo` is a different, unrelated project**
  ("Heavy weight plotting tools for ab initio solid-state calculations") — installing it
  would have been a real, silent mistake. The actual traffic simulator publishes on PyPI as
  **`eclipse-sumo`** (confirmed via PyPI's JSON API), with `traci` and `sumolib` as
  separate, version-matched packages, and `sumo-data` pulled in automatically as a
  transitive dependency.
- `eclipse-sumo` ships prebuilt wheels for both this dev machine (`win_amd64`) and CI's
  runner (`manylinux2014`/`manylinux_2_28`) — confirmed installable via `pip install`
  alone, no separate installer step. Installed and verified for real: `sumo --version`
  reports `Eclipse SUMO sumo 1.27.1`, copyright German Aerospace Center (DLR); `netconvert`
  and `randomTrips.py` (at `.../site-packages/sumo/tools/randomTrips.py`) are both present
  and runnable.
- A live Overpass API query for a real, small bounding box in central Ängelholm
  (`56.2430,12.8580` to `56.2470,12.8660`) returned 87 real highway ways — confirms
  OpenStreetMap/Overpass access works from this environment and that specific area has
  enough substance for a first MVP network.
- `pip-licenses` reports the exact licence string `EPL-2.0 OR GPL-2.0-or-later` for all
  four SUMO-related packages — not on the CI licence allow-list beforehand. Approved by the
  project owner 2026-09-16 (see `docs/standards/dependencies.md`'s updated allow-list and
  its reasoning).

## Decision

Use **SUMO** (via the `eclipse-sumo`/`traci`/`sumolib` PyPI packages, exactly pinned) as
the mobility simulation engine, and **OpenStreetMap** (fetched via the Overpass API) as the
geographic data source for the road network. `netconvert` (bundled with `eclipse-sumo`)
converts raw OSM XML directly into a routable SUMO network — no separate geographic-data
library (`osmnx`, `geopandas`, `networkx`) is needed for this scope, matching
`docs/architecture/overview.md`'s "Prefer Existing Capabilities" principle.

## Consequences

**Benefits:**

- Confirms `docs/architecture/overview.md`'s candidate architecture for real, with a
  working, verified toolchain rather than an assumption.
- A single, official, well-maintained simulator (DLR's SUMO) instead of building any
  routing/simulation logic in-house.
- Minimal dependency footprint: exactly four packages, no additional geodata stack.
- OpenStreetMap gives real-world geographic accuracy per `docs/vision.md`'s "Verklighetsbaserad
  modell" principle, at no data-licensing cost beyond ODbL attribution.

**Trade-offs:**

- SUMO's dual EPL-2.0/GPL-2.0-or-later licence is copyleft — accepted for this project's
  use (calling SUMO as an external tool, not modifying or redistributing its source); would
  need re-evaluating if that usage pattern ever changes (see `dependencies.md`).
- `eclipse-sumo`'s wheels are large (~300MB combined for `eclipse-sumo` + `sumo-data`) —
  meaningfully increases environment setup time and repo-adjacent download size, though not
  the repository itself.
- OpenStreetMap data quality/completeness varies by area and is community-maintained, not
  authoritative — acceptable for this project's scenario-exploration purpose (per
  `docs/vision.md`'s "Scenario före prognos" principle), not for applications needing
  guaranteed data accuracy.
- `sumo-gui` needs a display; CI (headless `ubuntu-latest`) can only ever run the non-GUI
  `sumo` binary — visual verification stays a manual, human step.

## Alternatives considered

- **A custom/in-house traffic simulation**: rejected outright — contradicts
  `docs/architecture/overview.md`'s own "Prefer Existing Capabilities" principle; SUMO is a
  mature, widely-used, DLR-maintained tool solving exactly this problem.
- **A different open-source simulator (e.g. MATSim, Aimsun-lite alternatives)**: not
  evaluated in depth — SUMO was already the project's own named candidate, and the
  investigation here found no blocker specific to SUMO worth abandoning it for. Revisit via
  a superseding ADR if a concrete limitation is hit later.
- **A commercial/proprietary geographic data source**: rejected — OpenStreetMap is free,
  has verified real coverage for the target area, and matches this project's
  "Återanvänd före egenutveckling" (reuse before building) principle without licensing cost.
