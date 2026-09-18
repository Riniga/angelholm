# ADR-008: Use polyconvert with a custom, discard-by-default type file for map context features

**Status:** Proposed
**Date:** 2026-09-18

## Context

MVP-003 (`docs/mvp/003-map-context-features.md`) needs `sumo-gui` to show recognisable
water and land-use context alongside the road network built in MVP-001/002, without
changing routing, traffic generation, or any headless simulation output.

Checked for real, not assumed:

- `polyconvert` (bundled with `eclipse-sumo`, alongside `netconvert` — already an approved
  dependency, `ADR-006`) reads the same `angelholm_bbox.osm.xml` extract `network.py`
  already fetches, given `--net-file` (for coordinate offset/projection alignment with the
  built network), `--osm-files`, and `--type-file`.
- SUMO ships a default OSM→polygon type mapping
  (`data/typemap/osmPolyconvert.typ.xml`, installed `eclipse-sumo==1.27.1`). Running
  `polyconvert` with it unmodified against the real MVP-002 fixtures pulled in **3,363
  buildings** plus amenities/shops/parking/tourism/sport/etc. alongside only 16 water + 52
  landuse shapes — far outside MVP-003's explicitly-scoped water/land-use-only goal.
- A trimmed, custom type file (`apps/simulator/data/context-features.typ.xml`) containing
  only the water/natural/landuse `polygonType` entries, combined with `polyconvert`'s
  "discard" option (sets the default action for any type *not* listed in the type file to
  discard, rather than import), produces exactly the water + landuse shapes wanted —
  verified by running it against the real, committed network and OSM fixtures and
  inspecting the output: only `water`, `landuse`, `forest`, `residential`, `industrial`
  present, zero buildings.
- Headless `sumo`, given the resulting `.poly.xml` via `--additional-files`, runs to
  completion unaffected (same step progression, same vehicle count) — shapes are
  display-only and are never read by the simulation engine itself.

## Decision

Use **`polyconvert`** with a **custom, discard-by-default type file**
(`apps/simulator/data/context-features.typ.xml`, adapted from SUMO's own bundled
`osmPolyconvert.typ.xml`) to generate map context shapes for `sumo-gui`, rather than the
bundled default type file. The resulting shapes file is referenced from the `.sumocfg`'s
`<additional-files>` and is otherwise inert to simulation behaviour.

The shapes output itself is **not committed** — like `angelholm.rou.xml`/`.sumocfg`, it is
deterministic from two already-committed inputs (`network.net.xml`,
`angelholm_bbox.osm.xml`) and is regenerated on every `simulator` run.

## Consequences

**Benefits:**

- Matches MVP-003's actual scope (water + land use only) without a bespoke OSM-parsing
  step — reuses SUMO's own, already-approved tool and mechanism rather than adding a new
  geodata dependency.
- Nothing unexpected leaks in: the discard-by-default behaviour means any OSM tag
  combination the type file doesn't explicitly list is dropped, not imported by accident.
- No change to headless simulation semantics — verified for real (see Context), not
  asserted from "it's just visual".

**Trade-offs:**

- The trimmed type file needs a manual (if small) update if a future MVP wants another
  category (e.g. buildings) — a one-line addition, not a rework, but not automatic either.
- The generated shapes file being gitignored (regenerated, not committed) means reviewers
  and CI never see its content directly — the committed type file and the `pytest`/manual
  verification stand in for that instead.

## Alternatives considered

- **The bundled default type file, unmodified**: rejected — pulls in 3,363 buildings and
  many other categories explicitly out of MVP-003's scope.
- **Committing the generated `.poly.xml` as a fixture**: rejected — it is fully
  deterministic from two already-committed inputs, so committing it would just be
  redundant, regenerated-on-every-run state, inconsistent with how routes/`.sumocfg` are
  already handled.
- **A separate geodata library (e.g. `osmnx`, `geopandas`) for water/land-use import**:
  rejected — `polyconvert` already does exactly this, bundled with an already-approved
  dependency; a new geodata stack would be unjustified for this scope.
