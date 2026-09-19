# MVP-005 Plan – Live Agent Engine

Implements [`docs/mvp/005-live-agent-engine.md`](../mvp/005-live-agent-engine.md).

**Status:** In progress — Phases 1–2 done (agents module, live engine); Phase 3 next.

## 1. Goal

Replace MVP-004's pre-generated `randomTrips.py` route files with a **live, TraCI-driven
engine**: `sumo`/`sumo-gui` starts on the committed network with no traffic and the clock at
05:00, and a single Python loop steps the simulation and spawns cars, bicycles and
pedestrians one at a time — random origin and destination (cars biased toward the 8 curated
entry/exit edges) — while SUMO removes arrivals. It runs until stopped, with a bounded-run
option for tests and CI. The static generation path is deleted, not kept as a second mode.

Structure matters more than realism here: choosing *who spawns and where* (an
`IndividualSource`) is kept separate from the loop that steps SUMO and applies it, so
MVP-006–010 can replace the source, add speed control, etc., without rewriting the loop.

## 2. Assumptions

Checked for real against `eclipse-sumo`/`traci` 1.27.1 in the `angelholm` environment while
writing this plan, not guessed:

* **An empty start works.** `traci.start(["sumo", "-n", "data/network.net.xml", "--begin",
  "18000", ...])` with no route files starts at simulated time 18000 s (05:00) with
  `getMinExpectedNumber() == 0`, and `simulationStep()` keeps working with nothing in it.
* **Routing is available per mode.** `traci.simulation.findRoute(fromEdge, toEdge, vType)`
  returns an object whose `.edges` is empty when no route exists. In the spike, two of two
  random pedestrian pairs had **no route** — origin/destination pairs that are unreachable
  are common, so retrying with a new pair is a required part of spawning, not an edge case.
  `findRoute` also makes SUMO print `No connection between edge ...` warnings.
* **Spawning APIs exist with these signatures:** `traci.route.add(routeID, edges)`,
  `traci.vehicle.add(vehID, routeID, typeID='DEFAULT_VEHTYPE', depart='now', ...)`,
  `traci.person.add(personID, edgeID, pos, depart=-3, typeID='DEFAULT_PEDTYPE')` followed by
  `traci.person.appendWalkingStage(personID, edges, arrivalPos, ...)`. A person spawned and
  given a walking stage this way was present and walking after 600 steps. A vehicle added with
  `depart='now'` is not counted by `vehicle.getIDCount()` until the next step.
* **Per-mode appearance can be set through TraCI.** `traci.vehicletype.copy`,
  `setVehicleClass`, `setColor` and `setMaxSpeed` all exist and work: a copy of
  `DEFAULT_VEHTYPE` set to `bicycle`/green/`4.17` m/s was accepted, and `DEFAULT_PEDTYPE`
  colour magenta reads back as `(255, 0, 255, 255)` with class `pedestrian`. This replaces
  the XML text-substitution in `traffic._customize_vtype()` (ADR-009).
* **Errors:** `traci.exceptions` provides `FatalTraCIError` (connection lost, e.g. the
  `sumo-gui` window was closed) and `TraCIException` (a rejected individual command).
* **SUMO removes arrivals itself.** Vehicles and persons that finish their route leave the
  simulation with no code on our side; we only observe them.
* **`sumo-gui` pacing** is available as `--delay <ms>` and `--start` (start running without
  pressing Play) — the plan verifies these with the GUI in Phase 3, it does not assume them.
* **Rates start from MVP-004's final numbers** (282 cars / 211 bicycles / 282 pedestrians
  over 400 s ≈ 0.705 / 0.528 / 0.705 spawns per second), then are calibrated in Phase 5 so
  the steady-state concurrent count is on the order of 200 — the owner's own figure; the
  real value is measured, not assumed.
* Tests stay mocked/deterministic as in earlier MVPs (no live SUMO in `pytest`); real SUMO
  runs are manual verification steps in Phases 5–6.
* **Deliberately kept at SUMO's default:** `--time-to-teleport` (300 s). A run with no end
  can otherwise gridlock permanently; teleporting stuck vehicles is what lets it recover.

## 3. Proposed file changes

| File | Change |
|---|---|
| `apps/simulator/src/simulator/agents.py` (new) | Pure logic, no `traci` import: `Mode` (car/bicycle/pedestrian), `Individual` (frozen dataclass: mode, origin, destination), `IndividualSource` (`typing.Protocol`: `due(sim_time) -> list[Mode]`, `draw(mode) -> Individual`), `ModeEdges` and `load_mode_edges()` (per-mode eligible edges + weights from the network and `entry-exit-edges.json`), and `RandomIndividualSource` (seeded exponential inter-arrival per mode, weighted random origin/destination). Also the moved colour/speed constants. |
| `apps/simulator/src/simulator/engine.py` (new) | The only module that imports `traci`: `SimulationError`, `format_clock()`, vType setup, `spawn()` (route with retry, add vehicle/person), `LiveEngine` (start SUMO, step loop, observe arrivals, stats, stop conditions), `run_live()` entry point. |
| `apps/simulator/src/simulator/run.py` | Drop route generation and `write_sumocfg`; build/reuse the network as today, then call `run_live()`. New flags: `--max-seconds` (bounded run), `--seed`. `--headless`/`--rebuild-network` keep their meaning. Update the docstring. |
| `apps/simulator/src/simulator/traffic.py` | **Deleted** in Phase 4 (`randomTrips.py` wrappers, `_customize_vtype`, `write_sumocfg`). Constants and weight logic are ported to `agents.py` first. |
| `apps/simulator/src/simulator/simulate.py` | **Deleted** in Phase 4 (`run_headless`/`run_gui` subprocess runners); `SimulationError` lives in `engine.py`. |
| `apps/simulator/src/simulator/_paths.py` | Delete only if `sumo_tools_dir` has no remaining user after Phase 4 (verify with a grep first; `network.py`/`context_features.py` matched the search and may still use it). |
| `apps/simulator/tests/test_agents.py` (new) | Unit tests for the source, weighting and bias. |
| `apps/simulator/tests/test_engine.py` (new) | Tests of `spawn`, the loop, stats and stop conditions against a mocked `traci`. |
| `apps/simulator/tests/test_run.py` | Update for the new pipeline (no route generation calls; `run_live` called with the right arguments). |
| `apps/simulator/tests/test_traffic.py`, `tests/test_simulate.py` | Deleted together with their modules; behaviour that still matters (edge weighting, colours) is re-tested in `test_agents.py`/`test_engine.py`. |
| `docs/architecture/decisions/ADR-010-live-traci-agent-engine.md` (new), `decisions/README.md` | Records the move from pre-generated routes to a TraCI-driven live engine; marks ADR-009's `--weights-prefix` and text-substitution parts as superseded (the curated entry/exit list stays). |
| `docs/architecture/overview.md`, `docs/architecture/current-state.md`, `README.md` | Update run instructions, module list, test count, data files (generated routes/`.sumocfg` no longer exist). |
| `docs/mvp/005-live-agent-engine.md`, `docs/plans/005-…plan.md`, `docs/roadmap.md` | "Outcome at close", plan status, roadmap status at the end. |
| `.gitignore` | Remove ignore entries that only existed for generated route/`.sumocfg` files if nothing else produces them (check first). |

## 4. Step-by-step TODO, grouped into phases

### Phase 1 — Model individuals and the weighted random source

*(commit message: "Add the individual model and a seeded weighted random source")*

Pure Python, fully testable without SUMO.

1. Create `agents.py` with `Mode` (a `str` `Enum`: `car`, `bicycle`, `pedestrian`) and a
   frozen `Individual(mode, origin, destination)` dataclass. Origin != destination is
   enforced by the source, not the dataclass.
2. Move `CAR_COLOR`, `BICYCLE_COLOR`, `PEDESTRIAN_COLOR`, `BICYCLE_MAX_SPEED` into
   `agents.py` with their existing explanatory comments (they are still needed by the
   engine). Do not delete them from `traffic.py` yet.
3. Define `ModeEdges` (dataclass: `edges: list[str]`, `weights: list[float]`) and
   `load_mode_edges(net_file, entry_exit_json, boost_weight) -> dict[Mode, ModeEdges]`:
   read the network with `sumolib`; per mode take edges that allow `passenger` /
   `bicycle` / `pedestrian`; cars get `boost_weight` on the curated edge ids and `1.0`
   elsewhere, bicycles and pedestrians `1.0` everywhere (same rule as MVP-004 — bias for
   cars only). Reuse `DEFAULT_ENTRY_EXIT_JSON` and `DEFAULT_ENTRY_EXIT_BOOST_WEIGHT` (200.0)
   by porting them into `agents.py`.
4. Define the `IndividualSource` `Protocol` with `due(sim_time: float) -> list[Mode]` and
   `draw(mode: Mode) -> Individual`.
5. Implement `RandomIndividualSource(mode_edges, rates_per_second, *, start_time, seed)`:
   own `random.Random(seed)`; per mode keep `next_spawn_time`, initialised to
   `start_time + rng.expovariate(rate)`.
6. Implement `due(sim_time)`: for each mode, while `next_spawn_time <= sim_time` append the
   mode and advance `next_spawn_time += rng.expovariate(rate)`. A mode with rate 0 never
   spawns. This handles several arrivals in one step correctly.
7. Implement `draw(mode)`: `rng.choices` for origin using the mode's weights, again for
   destination, redraw the destination until it differs from the origin.
8. Defaults: `DEFAULT_RATES` = cars 0.705, bicycles 0.528, pedestrians 0.705 per second, as
   named constants with a comment pointing at their MVP-004 origin and at Phase 5 calibration.
9. Write `tests/test_agents.py`: `load_mode_edges` on a tiny hand-written net file (or
   `sumolib` mocked) — car-only edge excluded from pedestrians and vice versa, curated edge
   boosted; `due()` returns nothing before the first spawn time, several modes in one call
   when time jumps, nothing for rate 0; same seed gives the same sequence, different seeds
   differ; `draw()` never returns origin == destination; over 2,000 draws the share of car
   trips touching a curated edge is above 50 %.
10. Run `pytest`; run `ruff format` and `ruff check`.

### Phase 2 — The live TraCI engine (headless)

*(commit message: "Add the live TraCI engine that spawns and observes individuals")*

The engine is the only code touching `traci`. Everything is tested against a mocked `traci`
(`unittest.mock.patch("simulator.engine.traci")`).

1. Create `engine.py` with `SimulationError(RuntimeError)`, the `START_TIME = 18000`
   constant ("05:00") and `format_clock(sim_time) -> "HH:MM:SS"` (wraps past 24 h; the
   run is unbounded, so day 2 must still read sensibly).
2. Add `_configure_vtypes()`: set colour on `DEFAULT_VEHTYPE` (cars) and `DEFAULT_PEDTYPE`;
   `vehicletype.copy("DEFAULT_VEHTYPE", BICYCLE_TYPE_ID)` then `setVehicleClass("bicycle")`,
   `setColor`, `setMaxSpeed(BICYCLE_MAX_SPEED)`. `traci` colours are RGBA 0–255 tuples: add
   a small `_rgba(color: "R,G,B" 0–1 floats)` helper so the existing constants are reused
   as they are.
3. Add `_route_for(individual)`: `traci.simulation.findRoute(origin, destination,
   vType)` with the mode's vType id; return the edge list, or `None` when `.edges` is empty.
4. Add `spawn(mode, source, counters) -> bool`: up to `MAX_SPAWN_ATTEMPTS = 10` times
   `source.draw(mode)` and `_route_for()`; on no route keep trying. On success:
   - car/bicycle: `traci.route.add(route_id, edges)` + `traci.vehicle.add(id, route_id,
     typeID=..., departLane="best")`;
   - pedestrian: `traci.person.add(id, edges[0], 0, typeID="DEFAULT_PEDTYPE")` +
     `traci.person.appendWalkingStage(id, edges, -1)`.
   Ids are `car_<n>`, `bike_<n>`, `ped_<n>` from a counter (unique for the whole run).
   A `TraCIException` from `add` counts as a failed attempt, not a crash. After all
   attempts fail, count `skipped[mode] += 1` and return `False`.
5. **[Done — answer: use `vehicle.add(id, "")` + `vehicle.setRoute`.]** Verified for real:
   named `route.add` routes are never freed (31 routes left after 30 vehicles had all left),
   empty-route + `setRoute` routes are (1 baseline route left). Original question: each car/bicycle currently creates a permanent route id, and a run with no
   end would accumulate them forever. Check whether `traci.vehicle.add(id, "")` followed by
   `traci.vehicle.setRoute(id, edges)` works on 1.27.1 without registering a route, or
   whether route ids can be removed. Use whichever avoids unbounded growth; if neither
   works, note the growth rate (routes/hour) as a risk instead.
6. Add `EngineStats` (dataclass): `spawned`, `skipped` (both per mode), `arrived` (per
   mode), `active` (per mode, last sample), `peak_active`.
7. Implement `LiveEngine(source, sumo_args, *, max_sim_seconds=None)`:
   - `start()`: `traci.start(sumo_args)`, `_configure_vtypes()`; wrap failures in
     `SimulationError`.
   - `step()`: `traci.simulationStep()`; `now = traci.simulation.getTime()`; for each mode
     from `source.due(now)` call `spawn()`; update active/arrived by comparing
     `traci.vehicle.getIDList()` / `traci.person.getIDList()` against the previous step's
     id sets (ids that disappeared = arrived; deliberately not relying on
     `getArrivedNumber()`, which may not cover persons — confirm in Phase 5 and simplify if
     it does).
   - `run()`: `start()`; loop `step()` until `max_sim_seconds` of simulated time have passed
     (when set) or `KeyboardInterrupt`; on `traci.exceptions.FatalTraCIError` (GUI window
     closed) end quietly with the stats gathered so far; always `traci.close()` in
     `finally` (guarded so a dead connection does not raise again).
   - Log one line every simulated 15 minutes: clock, active per mode, totals.
8. Add `run_live(net_file, *, headless, gui_settings_file, seed, max_sim_seconds,
   delay_ms) -> EngineStats`: builds the `sumo`/`sumo-gui` command (`-n net`, `--begin
   18000`, `--no-step-log true`; GUI adds `--start`, `--delay`, `--gui-settings-file`),
   loads `load_mode_edges()`, builds the `RandomIndividualSource`, runs the engine. Keep
   `DEFAULT_DELAY_MS = 200` as the viewing pace for now (speed control is MVP-006).
9. Write `tests/test_engine.py` (mocked `traci`): `format_clock` (05:00:00, wrap at 24 h);
   vType setup calls; `_route_for` empty vs non-empty; `spawn` retries after an empty
   route, stops after 10 attempts and counts a skip, spawns a car / bicycle / pedestrian
   with the right `traci` calls, and treats `TraCIException` as a failed attempt;
   `step` spawns only what `due()` asks for; arrivals are counted when ids disappear;
   `run` stops at `max_sim_seconds`, ends cleanly on `FatalTraCIError`, and closes in every
   case; `run_live` builds the right argv for headless vs GUI.
10. Run `pytest` with coverage; `ruff format`, `ruff check`.

### Phase 3 — Wire the engine into the `simulator` command

*(commit message: "Run the live engine from the simulator command")*

1. In `run.py`, keep network build/reuse exactly as it is. Remove the three
   `generate_*_traffic` calls, `write_sumocfg` and the route/config path variables.
2. Add arguments `--max-seconds` (float, default `None` = run until stopped) and `--seed`
   (int, default `None` = random per run; only patterns need to reproduce).
3. Headless: call `run_live(net_file, headless=True, ...)`. GUI: still call
   `write_gui_settings()` as today and pass the file to `run_live(headless=False, ...)`.
4. Print the final `EngineStats` summary at the end of a bounded/ended run.
5. Update the module docstring's usage block (`--max-seconds`, `--seed`).
6. Update `tests/test_run.py`: network reused when present, rebuilt on
   `--rebuild-network`, `run_live` called with headless/gui settings/seed/`max_seconds`,
   GUI settings written only for the GUI path, exit code 0.
7. Run `pytest`, ruff. Then do the first real check by hand: `simulator --headless
   --max-seconds 600` finishes on its own and prints a summary with spawns in all three
   modes.
8. Real GUI check: `simulator` opens `sumo-gui` on an empty basemap, starts on its own,
   individuals appear, and closing the window ends the process without a traceback. If
   `--start`/`--delay` behave differently than assumed, fix `run_live()` and note it in the
   plan.

### Phase 4 — Remove the static traffic-generation path

*(commit message: "Remove the pre-generated route path replaced by the live engine")*

1. Grep the repo for every remaining use of `traffic.py`, `simulate.py` and
   `sumo_tools_dir` (source, scripts, tests, docs).
2. Delete `traffic.py` and `simulate.py`; move nothing else out of them (Phase 1 already
   ported the constants and weighting).
3. Delete `tests/test_traffic.py` and `tests/test_simulate.py`. Before deleting, list what
   each test covered and confirm it is re-tested (or truly obsolete) in `test_agents.py` /
   `test_engine.py`.
4. Delete `_paths.py` and `tests/test_paths.py` only if step 1 shows `sumo_tools_dir` has no
   user left; otherwise keep them.
5. Remove `.gitignore` entries only used for generated route/`.sumocfg`/weights files, after
   confirming nothing else produces those files.
6. Delete the generated leftovers in `apps/simulator/data/` locally
   (`*.rou.xml`, `*.sumocfg`, `*-weights.*.xml`, `*.trips.xml`) — they are untracked and
   stale (verify with `git status` that nothing tracked is touched).
7. Run the full `pytest`; confirm coverage is still at or above the 95 % floor; ruff.
8. Run the pre-commit hooks (`pre-commit run --all-files`) and, since files were deleted,
   check that CI's licence/dependency checks are unaffected (no dependency changes expected).

### Phase 5 — Calibrate density and verify the live run

*(commit message: "Calibrate spawn rates and verify steady-state behaviour")*

Measurement phase; code changes are limited to the constants in `agents.py`.

1. Run headless for 2 simulated hours (`simulator --headless --max-seconds 7200 --seed 1`)
   and record the 15-minute log lines: active per mode over time.
2. Confirm the warm-up shape: zero at 05:00, rising, then levelling off. Record the
   steady-state concurrent total and the per-mode split.
3. Compare with the target of roughly 200 concurrent travellers and the visual balance
   between modes MVP-004 ended on (all three visibly present). Adjust `DEFAULT_RATES` and
   re-run until the steady state is in range. Record the final numbers in the constant's
   comment (as MVP-004 did) and here.
4. Check the skip rate (`skipped / (spawned + skipped)` per mode). If a mode skips a large
   share because most pairs are unreachable, note it as a finding; consider restricting the
   pool to the network's largest connected component per mode as a follow-up rather than
   growing this MVP.
5. Measure the curated-edge share of live car spawns (origin or destination on one of the 8
   edges) over the run — must stay a majority, as in MVP-004 (73.8 %).
6. Run once more for 6 simulated hours to look for problems that only appear over time:
   gridlock/teleport messages, active count drifting upward, memory growth of the Python
   process. Record what was seen.
7. Check whether `traci.simulation.getArrivedNumber()` counts persons; if it does, simplify
   the arrival observation in `LiveEngine.step()` accordingly (and its tests).
8. Decide what to do with the `No connection between edge ...` warnings that `findRoute`
   provokes (they are harmless but noisy); either suppress just those or leave them and say
   so — do not silence SUMO warnings globally.

### Phase 6 — Owner verification in `sumo-gui`, docs and close

*(commit message: "Verify MVP-005 acceptance criteria and close the MVP")*

1. Ask the project owner to run `simulator` and watch it for a while: empty city at 05:00,
   individuals appearing one at a time, the count levelling off, arrivals disappearing,
   colours and pedestrian size unchanged from MVP-004, entry/exit roads busy. Act on their
   feedback, as in MVP-004 (density/pace tuning is expected).
2. Write `ADR-010-live-traci-agent-engine.md` (Context: batch generation and
   its limits; Decision; Consequences; Alternatives — pre-generated per-person plans,
   a thread per individual, `sumo-gui`'s own delay slider only) and add it to
   `decisions/README.md`. Mark the `--weights-prefix` and text-substitution parts of ADR-009
   as superseded while keeping its curated-edge-list decision.
3. Update `README.md` run instructions and `docs/architecture/overview.md` (module list,
   data flow, generated files no longer exist, `randomTrips.py` no longer used).
4. Update `docs/architecture/current-state.md` (status, test count, capabilities) and the
   coverage figure.
5. Re-verify earlier acceptance criteria for real: network still 4,250 edges / 1,756
   junctions, basemap and colours unaffected, full `pytest` green, coverage at or above 95 %.
6. Add "Outcome at close" to `docs/mvp/005-live-agent-engine.md` for each acceptance
   criterion, with measured numbers and any findings that changed the design.
7. Set this plan's status and `docs/roadmap.md` (R2 line for MVP-005) to delivered.
8. Show the diff and hand over commit messages; the owner does the commits and opens the PR
   (no push or merge from here).

### Findings from Phase 2 (real run, 30 simulated minutes, headless)

* Two real bugs found and fixed with regression tests: SUMO can reject a walking stage
  (`Invalid arrivalPos`) *after* `person.add`, which left a standing person and made every
  retry fail with "person already exists" (fix: remove the person, fresh id per attempt).
* `Invalid arrivalPos` errors still appear in the log for some pedestrian routes (handled,
  retried, no crash). Phase 5: find out which edges cause it and avoid them or pass an
  explicit `arrivalPos`.
* **Density is ~10x above the target.** With MVP-004's rates the concurrent count reached
  ~2,200 after 30 simulated minutes (705 cars / 463 bicycles / 1,025 pedestrians) and was
  still rising; MVP-004's batch never had that many at once. Phase 5 calibrates the rates
  down; pedestrians (slow, long trips) dominate the count.
* `getArrivedNumber()` does not report persons (confirmed), so arrivals are counted by
  comparing id sets.
* `departLane="best"` from step 4 was not used: the vehicle is added with an empty route, so
  SUMO's default lane choice is used.

## 5. Risks / open questions

* **Unreachable pairs and skipped spawns.** Many origin/destination pairs have no route for
  a mode (2/2 pedestrian pairs failed in the spike). Retrying handles it, but the effective
  spawn rate then falls below the configured one, and the retry costs CPU. Phase 5 measures
  the skip rate; the likely later fix is limiting each mode to its largest connected
  component of the network.
* **Unbounded growth over a never-ending run.** Route ids (Phase 2 step 5), stats and ids
  must not grow forever. Verified by the 6-hour run; a leak found there is fixed or recorded.
* **Gridlock.** SUMO's default teleport (300 s) is kept so a jam clears; a persistent jam at
  one junction would show as growing `active` counts. Traffic light programs from `netconvert`
  could be wrong (the owner saw a red-light jam) — a separate check, explicitly not part of
  this MVP.
* **Spawn on a full or unsuitable edge.** `depart='now'` may fail or be delayed when the
  origin edge is occupied; treated as a failed attempt (or a short delay), and visible in the
  skip figures. Vehicles delayed at insertion are worth watching in the GUI.
* **GUI ↔ TraCI behaviour.** Whether `--start`/`--delay` behave as expected, what happens to
  pausing, and that closing the window raises `FatalTraCIError` are checked in Phase 3, not
  assumed. Speed control itself is MVP-006 and may need this loop to pace itself.
* **CI never hangs.** The unbounded default makes `--max-seconds` essential for any
  automated use; tests use the mocked `traci` and never start SUMO.
* **Density target is the owner's own estimate (~200).** Treated as a starting point, tuned
  in Phase 5 and confirmed visually in Phase 6, not a hard requirement.
* **Constant spawn rate all day** means the 05:00 start has no effect on traffic in this MVP
  (05:00 looks like 14:00). Known and intentional; MVP-007 fixes it.
* **Open: ADR scope.** ADR-010 is expected; whether it also needs to record the `traffic.py`
  deletion is decided when writing it. Confirm with the owner if it feels like more than one
  decision.
