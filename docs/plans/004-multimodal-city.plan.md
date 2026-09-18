# MVP-004 Plan – Multimodal City

Implements [`docs/mvp/004-multimodal-city.md`](../mvp/004-multimodal-city.md).

## 1. Goal

Add cyclist and pedestrian traffic alongside cars, all still synthetically generated (not
population-based), with car traffic biased toward a curated set of ~10 real, named
entry/exit roads rather than spread uniformly across all 4,250 edges. Traffic volumes are
bumped to city-centre scale (≥80 cars, ≥60 bicycles, ≥80 pedestrians — floors, not exact
targets) per the MVP's own acceptance criteria.

## 2. Assumptions

Checked for real against `randomTrips.py`'s own `--help` and source
(`sumo/tools/randomTrips.py`, installed `eclipse-sumo==1.27.1`), not guessed:

* **Bicycle and pedestrian trips need no network rebuild.** Of the current network's 4,250
  edges, 3,739 already allow bicycles and 4,115 already allow pedestrians (`netconvert`'s
  default OSM import assigns these permissions per road type automatically). Only
  `--output.street-names` needs adding to the existing `netconvert` call, for the entry/exit
  edge curation step below — everything else about the network stays as MVP-002 built it.
* **`--vehicle-class bicycle`** generates bicycle trips with a correct `vType` embedded in
  the output; **`--persontrips`** generates a person/`<walk>` route file instead of vehicle
  trips. Both are existing `randomTrips.py` flags, no new tool.
* **`sumo`'s `--route-files` accepts a comma-separated list** (confirmed via `sumo --help`:
  "Load routes descriptions from FILE(s)") — car, bicycle and pedestrian route files can be
  loaded together in one `.sumocfg` without merging them into a single file.
* **Biasing toward specific edges needs `--weights-prefix`, not `--fringe-factor`.**
  `--fringe-factor` biases toward *topological* fringe edges (any dead-end/boundary edge,
  ~100 candidates found geometrically) — it has no notion of "these specific 10 named
  roads". `--weights-prefix PREFIX` loads `PREFIX.src.xml`/`PREFIX.dst.xml` edge-weight
  files instead; confirmed by reading `randomTrips.py`'s own `LoadedProps` class
  (`self.weights = defaultdict(lambda: 0)`) that **edges not listed in the file get weight
  zero** — so to bias toward (not restrict to) the curated 10 edges, the weight file must
  list *all* eligible edges, giving the curated 10 a large weight and every other edge a
  small nonzero weight. Confirmed further in `buildTripGenerator()`: when a weights file is
  present, it fully replaces the default probability function (length/speed/fringe
  heuristics), so this is an all-or-nothing choice per mode, not an additive bonus.
* **A weight ratio needs empirical tuning, not a guessed constant.** Rough math (10 edges
  at weight 200 vs. ~1,658 other car-capable edges at weight 1: curated share ≈ 2000/3658 ≈
  55% per endpoint draw, so P(either endpoint lands on a curated edge) ≈ 1 − (1−0.55)² ≈
  80%) suggests a starting ratio, but the plan's Phase 4 verifies the real "majority"
  criterion against actually generated trips, not this estimate.
* **The ~10 entry/exit edges cannot be picked automatically with confidence.** A geometric
  pass (car-capable edges ending at a low-degree/dead-end junction, i.e. where the MVP-002
  outline clip likely cut through a real road) finds ~100 candidates but includes plenty of
  minor residential dead-ends, not just real arterial roads. Picking the real ~10 needs a
  human glancing at actual street names — hence the `--output.street-names` addition and a
  listing script, not a fully automated selection.

## 3. Proposed file changes

| File | Change |
|---|---|
| `apps/simulator/src/simulator/network.py` | `build_network()`: add `--output.street-names` to the `netconvert` invocation, so rebuilt networks carry real street names (additive metadata only — must not change edge/junction counts, verified in Phase 1). |
| `scripts/list_entry_exit_candidates.py` (new) | One-off, re-runnable script: loads the network via `sumolib`, finds car-capable edges ending at a low-degree/dead-end junction, prints them sorted by speed with their street name for manual review. Writes nothing — a human picks the real ~10 from its output. |
| `apps/simulator/data/entry-exit-edges.json` (new, committed) | The curated list: `[{"edge_id": "...", "name": "..."}, ...]`, roughly 10 entries. Source of truth for the weighting step below. |
| `apps/simulator/src/simulator/traffic.py` | New: `_write_edge_weights()` (builds `.src.xml`/`.dst.xml` from `entry-exit-edges.json` + the network, biasing car trip generation); `generate_bicycle_traffic()`; `generate_pedestrian_traffic()`. Existing `generate_traffic()` (cars) extended to use the new weight files via `--weights-prefix`; a shared private helper avoids duplicating the `randomTrips.py` subprocess-building logic three times. |
| `apps/simulator/src/simulator/traffic.py` | `write_sumocfg()`: new optional `additional_route_files: list[Path] | None = None` parameter, appended to `<route-files>` as a comma-separated list alongside the primary route file — existing callers/behaviour unchanged when omitted. |
| `apps/simulator/src/simulator/run.py` | Calls `generate_bicycle_traffic()`/`generate_pedestrian_traffic()` alongside the existing `generate_traffic()`, passes their outputs into `write_sumocfg(..., additional_route_files=[...])`. |
| `apps/simulator/tests/test_traffic.py` | New tests for `_write_edge_weights()`, `generate_bicycle_traffic()`, `generate_pedestrian_traffic()`, and `write_sumocfg()`'s `additional_route_files`. |
| `apps/simulator/tests/test_network.py` | Update `build_network()`'s argv assertions for the new `--output.street-names` flag. |
| `apps/simulator/tests/test_run.py` | Update mocks/assertions for the new generation calls and `write_sumocfg` argument. |
| `docs/architecture/current-state.md`, `docs/architecture/overview.md` | Update once delivered — new modes, new committed data file, updated network rebuild note. |
| `docs/mvp/004-multimodal-city.md` | Add an "Outcome at close" section once delivered and verified, following the established MVP-001–003 pattern. |

## 4. Step-by-step TODO, grouped into phases

### Phase 1 — Rebuild the network with street names and curate entry/exit edges

*(commit message: "Rebuild the network with street names and curate 10 entry/exit edges")*

1. Add `--output.street-names` to `build_network()`'s `netconvert` argv in `network.py`.
2. Update `test_network.py`'s `build_network()` argv-assertion test(s) for the new flag.
3. Rebuild the real network for real: `simulator --rebuild-network` (or call
   `fetch_osm_extract`/`build_network` directly). Confirm via `sumolib` that edge/junction
   counts are unchanged from MVP-002's 4,250/1,756 — this flag should be purely additive
   metadata; verify that assumption holds, don't just trust it.
4. Write `scripts/list_entry_exit_candidates.py`: load the rebuilt network, find
   car-capable edges ending at a low-degree/dead-end junction, print
   `(edge_id, street_name, speed, length)` sorted by speed descending.
5. Run it for real; manually cross-reference the printed candidates against known arterial
   roads (Kungsgårdsleden, Klippanvägen, Helsingborgsvägen, Kullavägen, Höja landsväg,
   route 107, etc. — visible in `docs/architecture/map_plain.gif`) and pick ~10 real,
   distinct entry/exit edges — genuinely one per real road, not near-duplicates of the
   same junction.
6. Commit the result as `apps/simulator/data/entry-exit-edges.json`.
7. Run `pytest` for `apps/simulator` and confirm nothing broke from the `netconvert` flag
   addition.

### Phase 2 — Multimodal trip generation

*(commit message: "Generate bicycle and pedestrian traffic biased toward entry/exit edges")*

8. In `traffic.py`, add `_write_edge_weights(net_file, entry_exit_json, output_prefix,
   *, vclass, boost_weight) -> tuple[Path, Path]`: for every edge in `net_file` that
   allows `vclass`, write it to both `.src.xml` and `.dst.xml` with weight `1`, except the
   edges listed in `entry_exit_json` (by ID), which get weight `boost_weight`. Returns the
   two written file paths.
9. Extend `generate_traffic()` (cars) to call `_write_edge_weights()` and pass
   `--weights-prefix` to its `randomTrips.py` invocation. Bump its volume knob (mirroring
   `DEFAULT_PERIOD`'s existing tuning pattern) toward the ≥80-car floor — exact value
   confirmed for real in Phase 4, not hard-locked here.
10. Add `generate_bicycle_traffic(net_file, route_file, ...) -> Path`: `randomTrips.py
    --vehicle-class bicycle`, own volume knob toward the ≥60-bicycle floor. Per the MVP's
    Scope, entry/exit weighting is required for cars only — bicycles/pedestrians may reuse
    the default (unweighted) generation unless trivial to extend later.
11. Add `generate_pedestrian_traffic(net_file, route_file, ...) -> Path`: `randomTrips.py
    --persontrips`, own volume knob toward the ≥80-pedestrian floor.
12. Extract shared `randomTrips.py`-invocation logic (argv construction, subprocess run,
    error handling) already duplicated three times at this point into one private helper,
    reused by `generate_traffic()`/`generate_bicycle_traffic()`/`generate_pedestrian_traffic()`.
13. Write unit tests (mocked `subprocess.run`, mirroring `test_context_features.py`'s
    pattern) for `_write_edge_weights()` (small fixture network + entry-exit JSON,
    assert the written `.src.xml`/`.dst.xml` content) and the two new generation functions
    (argv assertions: `--vehicle-class bicycle`, `--persontrips` present as expected).
14. Run `pytest --cov` and confirm the coverage floor still holds.

### Phase 3 — Wire multimodal traffic into the simulation config

*(commit message: "Run cars, bicycles and pedestrians together in one simulation")*

15. Extend `write_sumocfg()` with `additional_route_files: list[Path] | None = None`,
    appended into `<route-files>` as `primary,extra1,extra2` when given; unchanged output
    when omitted (verified by an explicit test, mirroring the `additional_files`/
    `gui_settings_file` opt-in pattern already used elsewhere in this codebase).
16. Update `run.py`: call `generate_bicycle_traffic()`/`generate_pedestrian_traffic()`
    alongside the existing `generate_traffic()` call, pass both new route files into
    `write_sumocfg(..., additional_route_files=[bike_route, ped_route])`.
17. Update `test_run.py`'s mocks/assertions for the new calls and the new
    `write_sumocfg` argument.
18. Run `pytest --cov` and confirm the coverage floor still holds.

### Phase 4 — Regenerate real fixtures and verify the acceptance criteria

*(commit message: "Verify multimodal traffic volumes and entry/exit bias for real")*

19. Run the full pipeline for real (`simulator --headless` or calling the functions
    directly) against the committed, rebuilt network.
20. Count actual generated trips per mode; tune each mode's volume knob until all three
    floors (≥80 cars, ≥60 bicycles, ≥80 pedestrians) are met — these are floors from the
    MVP doc, not hard-locked exact numbers.
21. Programmatically verify the "majority of car trips start or end at a curated
    entry/exit edge" criterion against the real generated route file — if the Phase 2
    `boost_weight` estimate doesn't actually clear 50%, raise it and re-measure, don't
    just assume the earlier math held.
22. Run `simulator --headless` and confirm `"Simulation completed successfully"` with all
    three modes loaded together, no errors.
23. Re-verify MVP-001/002/003's own criteria still hold: network edge/junction counts
    unchanged, map-context background unaffected, full test suite passing — confirmed by
    actually re-running them, not assumed.

### Phase 5 — Visual check and close out

*(commit message: "Verify MVP-004 acceptance criteria and close the MVP")*

24. Launch `simulator` (GUI) and visually confirm cyclists and pedestrians are present and
    moving distinctly from car traffic, alongside the existing map-context background.
25. Project owner visually confirms the result — the closing acceptance check, not an
    implementation step.
26. Update `docs/architecture/current-state.md`/`overview.md` with the new modes and the
    committed `entry-exit-edges.json`.
27. Add the "Outcome at close" section to `docs/mvp/004-multimodal-city.md`, following the
    established MVP-001–003 pattern — record what was actually verified, real tuning
    values landed on, and any real findings along the way.
28. Run the full `pytest` suite one more time before proposing the PR.

## 5. Risks / open questions

* **Manual entry/exit curation is a real judgement call, not automatable end to end** —
  Phase 1's geometric candidate list needs a human (project owner or implementer) to
  cross-reference against real road names; a bad pick (e.g. a minor residential dead-end
  mistaken for an arterial road) would still technically "work" but wouldn't produce the
  realistic effect intended. Worth a quick visual sanity check (plot the chosen 10 edges
  against `docs/architecture/map_plain.gif`) before committing the list, not just trusting
  the sorted-by-speed heuristic blindly.
* **`--weights-prefix` replaces, not augments, the default probability heuristics** (see
  Assumptions) — once applied, cars lose the existing length/speed-based weighting
  entirely in favour of the flat per-edge weights in the file. Acceptable for this MVP's
  scope (explicitly "no OD calibration"), but worth knowing this isn't a small additive
  tweak.
* **Pedestrian trip realism**: `--persontrips` can generate very long walking trips by
  default (min/max distance defaults are tuned for vehicles) — Phase 2/4 should sanity
  check generated pedestrian trip lengths look like plausible walks, not cross-city treks,
  and add `--max-distance` or similar if not.
* **Combined-mode performance/runtime**: three simultaneous `randomTrips.py` +
  `duarouter` invocations plus a larger combined route file may noticeably increase
  `simulator --rebuild-network`/generation runtime — not expected to be a real problem at
  these volumes, but budget time in Phase 4 rather than assuming it's free.
* **No calibration against real traffic counts** — explicitly out of scope per the MVP
  doc; the volume floors (80/60/80) and the entry/exit bias are visual/plausibility
  choices, not validated against measured Ängelholm traffic data.
