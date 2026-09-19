# ADR-009: Bias car trips toward a curated entry/exit edge list via `--weights-prefix`

**Status:** Proposed
**Date:** 2026-09-19

## Context

MVP-004 (`docs/mvp/004-multimodal-city.md`) wants generated car traffic to start and end
mostly at a small set of real roads leading into/out of the city, instead of uniformly
across all 4,250 edges — a "basic zones" notion, explicitly without a synthetic
population or an origin-destination demand model.

Checked for real, not assumed:

- **`--fringe-factor` is the wrong lever.** It biases toward *topological* fringe edges
  (any dead-end/boundary edge). A geometric pass over the network found ~100 such
  car-capable candidates, mostly minor residential dead-ends where the MVP-002 coverage
  outline happened to clip a small street. It has no notion of "these specific named
  roads".
- **`--weights-prefix PREFIX` is the right lever.** It loads `PREFIX.src.xml` /
  `PREFIX.dst.xml` per-edge weights. Reading `randomTrips.py`'s own source
  (`LoadedProps`) confirmed two non-obvious properties: edges *not listed* get weight
  **zero**, and a loaded weights file **fully replaces** the default length/speed/fringe
  heuristics rather than adding to them. So the file must list every eligible edge —
  curated edges at a large weight, everything else at 1 — to bias rather than restrict.
- **The curated list cannot be picked automatically with confidence.** `netconvert
  --output.street-names` (added to `build_network()`, purely additive — edge/junction
  counts verified unchanged at 4,250/1,756) makes real street names available; a
  candidate-listing script plus a human check against the basemap produced **8**
  genuinely distinct named arterial roads, fewer than the hoped ~10 (Helsingborgsvägen and
  Kullavägen don't clip at a dead-end in this network at all).
- Measured, not estimated: with boost weight 200, **71.2%** of 80 real car trips and
  **73.8%** of 282 start or end at a curated edge.

## Decision

- Commit the curated list as `apps/simulator/data/entry-exit-edges.json` (edge id + real
  name per entry), the single source of truth.
- `simulator.traffic._write_edge_weights()` builds the `.src.xml`/`.dst.xml` pair at
  generation time from that list + the network; `generate_traffic()` (cars) passes it via
  `randomTrips.py --weights-prefix`. Bicycles and pedestrians are generated unweighted —
  the MVP requires the bias for cars only.
- Post-process the generated route files' `<vType>` (colour, bicycle `maxSpeed`) with
  plain text substitution in `simulator.traffic._customize_vtype()`, not an XML library:
  the file shape is fully known (our own `randomTrips.py` output), and importing the
  stdlib `xml.etree.ElementTree` for element construction would re-trigger the Semgrep
  `use-defused-xml` SAST rule that `defusedxml` was adopted to satisfy (see MVP-003).

## Consequences

**Benefits:**

- A verified majority of car trips use real entry/exit roads, with a documented, reviewable
  data file rather than a heuristic hidden in a flag.
- No new dependency; everything reuses SUMO's own `randomTrips.py` mechanisms.
- Regenerated on every run from committed inputs, so weights never go stale relative to the
  network.

**Trade-offs:**

- Weighting replaces `randomTrips.py`'s default heuristics for cars (no length/speed
  weighting any more) — acceptable, since this MVP explicitly excludes demand calibration.
- Edge IDs in `entry-exit-edges.json` are tied to the current network build; a rebuild
  with a different outline/bbox can change IDs and requires re-running
  `scripts/list_entry_exit_candidates.py` and re-curating.
- Text-substituting XML is less robust than parsing it; acceptable only because the input
  is our own tool's fixed output, and covered by tests for both branches (existing vs.
  missing `<vType>`).

## Alternatives considered

- **`--fringe-factor`**: rejected — topological, not curated; would favour dozens of minor
  dead-ends.
- **Full Traffic Analysis Zones with an OD matrix**: out of MVP-004's scope (later R2
  population work), far heavier than the stated need.
- **Restrict trips to only the curated edges** (list only those edges in the weights file):
  rejected — forces every trip between just 8 edges, unrealistically repetitive.
