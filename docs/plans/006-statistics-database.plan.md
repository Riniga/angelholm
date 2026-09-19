# MVP-006 Plan – Statistics Database

Implements [`docs/mvp/006-statistics-database.md`](../mvp/006-statistics-database.md).

**Status:** In progress — Phases 1–5 done (statistics file; loader; time-varying source; wired into the run; readable clock); Phase 6 (long runs and calibration) next.

## 1. Goal

Replace MVP-005's three constant spawn rates (`DEFAULT_RATES` in `agents.py`) with a small,
human-editable statistics file that says *how many trips per day*, *how they are spread over
the 24 hours*, and *how they split between car, bicycle and pedestrian*. The random source
turns that into a time-varying arrival rate driven by the simulated clock, so the city is quiet
at night, busy in the rush hours and repeats every simulated day, with cars clearly the largest
group of spawns. The simulated time of day becomes easy to read while watching. Every number in
the file states its source or is marked as an estimate.

Only the *volume and mix over time* change. Origins and destinations stay random with the
curated entry/exit bias; the engine's stepping loop is not touched.

## 2. Assumptions

Facts checked in this repository and the `angelholm` environment while writing the plan:

* **The seam is in place.** `simulator.agents.RandomIndividualSource` holds a per-mode
  `_next_spawn` time and draws exponential gaps from a constant rate (`due(sim_time)`);
  `LiveEngine` only calls `source.due(now)` and `source.draw(mode)`. A time-varying rate is a
  change inside the source. `run_live()` builds the source with `load_mode_edges()` and
  `START_TIME` (18000 s = 05:00) and passes `seed`.
* **There is a measured ceiling.** MVP-005 Phase 5 (`docs/plans/005-live-agent-engine.plan.md`):
  steady-state travellers scale roughly linearly with the spawn rate up to ~0.35 cars per second
  (0.35 / 0.25 / 0.25 → ~830 concurrent) and gridlock well before 0.705. The current constant
  0.10 / 0.07 / 0.07 gives ~200 concurrent. The busiest hour of the new profile must stay below
  that ceiling.
* **The daily profile fixes the average.** Rate at time *t* for a mode =
  `total_trips_per_day × hour_weight(h) / Σ weights × mode_share ÷ 3600`. With the starting
  estimates in Phase 1 (peak hour ≈ 2× the average hour, 15,000 trips/day, 60 % cars) the
  average car rate is ≈ 0.104 /s (about today's 0.10) and the peak ≈ 0.21 /s, under the ceiling.
  These are starting points to be tuned in Phase 6, not results.
* **Time-varying Poisson arrivals** can be generated exactly by *thinning*: generate candidate
  arrivals at the mode's maximum rate λmax and accept each with probability `λ(t) / λmax`.
  Cheap (one random number per candidate) and needs no numerical integration.
* **The clock repeats.** The run starts at 05:00 and never ends; `t mod 86400` selects the hour,
  so the profile wraps at midnight. `engine.format_clock()` already wraps the same way.
* **No new dependency.** JSON is already used for `apps/simulator/data/entry-exit-edges.json`
  and is loaded from a `DEFAULT_*_JSON` path constant next to the code (repo checkout /
  editable install, as before). Python's standard library is enough for validation.
* **`traci.gui` has no window-title setter** (checked: `dir(traci.gui)` offers view, zoom,
  boundary, screenshot and tracking, not a title). `traci.poi` has `add`, `setPosition`,
  `setType`, `setColor` and friends, so an on-map text label is technically possible but sits
  in network coordinates. `sumo-gui` itself shows simulation time in its toolbar; whether it can
  show `HH:MM:SS` for a run that starts at 18000 s is **not yet verified** — Phase 5 checks it
  for real before anything is built.
* **Real statistics are not in the repository** and their availability and licences are not
  verified. This plan therefore treats real figures as *optional upgrades*: the MVP is complete
  with clearly labelled estimates, and Phase 1 looks for real ones without blocking on them.
* Tests stay mocked/deterministic, no live SUMO in `pytest`; long runs are manual, bounded
  headless runs recorded in this plan, as in MVP-005.
* **Branching:** MVP-005 is committed on `feature/mvp-005-live-agent-engine` and its PR is the
  owner's to open and merge. Work for this MVP starts on a new branch
  `feature/mvp-006-statistics-database`, created from `main` once MVP-005 has been merged
  (the owner decides; no push or merge from here).

## 3. Proposed file changes

| File | Change |
|---|---|
| `apps/simulator/data/demand-statistics.json` (new, committed) | The statistics: `total_trips_per_day`, `hourly_profile` (24 relative weights), `mode_shares` (car/bicycle/pedestrian), each block with `status` (`"source"` or `"estimate"`) and a `source`/`note` string. Plus a `_comment` explaining how to edit it and the stability ceiling. |
| `apps/simulator/src/simulator/demand.py` (new) | Pure logic, no `traci`: `Demand` (`typing.Protocol`: `rate(mode, sim_time) -> float`, `max_rate(mode) -> float`), `DemandProfile` (frozen dataclass implementing it from the file's values), `ConstantDemand` (fixed rate per mode, for tests and simple cases), `load_demand_profile(path) -> DemandProfile`, `DemandProfileError`, `DEFAULT_DEMAND_JSON`, `describe()` (one-line human summary for the log). |
| `apps/simulator/src/simulator/agents.py` | `RandomIndividualSource` takes a `Demand` instead of `rates_per_second` and generates arrivals by thinning. `DEFAULT_RATES` and its calibration comment are removed (the calibration history moves into the data file's `_comment` and the MVP-005 plan). |
| `apps/simulator/src/simulator/engine.py` | `run_live(..., demand_file=DEFAULT_DEMAND_JSON)` loads the profile, logs `describe()` at start, builds the source with it. Time-of-day readability (Phase 5) adds whatever small code the verified method needs. `LiveEngine.step()` is otherwise untouched. |
| `apps/simulator/src/simulator/run.py` | New option `--stats PATH` (default: the committed file). Docstring usage block updated. |
| `apps/simulator/src/simulator/context_features.py` | Only if Phase 5 finds the time display is a `sumo-gui` view setting that belongs in the generated GUI-settings XML. |
| `apps/simulator/tests/test_demand.py` (new) | Loader validation and `DemandProfile` maths. |
| `apps/simulator/tests/test_agents.py` | Source tests updated to `ConstantDemand`; new statistical tests for the time-varying source over several simulated days. |
| `apps/simulator/tests/test_engine.py`, `tests/test_run.py` | `run_live` wiring, `--stats`, log line. |
| `docs/architecture/decisions/ADR-011-…md`, `decisions/README.md` | Only if Phase 7 judges the format/source choice significant (see Risks). |
| `docs/architecture/overview.md`, `docs/architecture/current-state.md`, `README.md` | Data file, module list, test count, run options. |
| `docs/mvp/006-statistics-database.md`, this plan, `docs/roadmap.md` | Outcome at close, status. |

## 4. Step-by-step TODO, grouped into phases

### Phase 1 — The statistics file and its honest first values

*(commit message: "Add the demand statistics file with labelled first values")*

No code yet: decide and write down the data.

1. Spend a bounded effort (an hour of reading, not a research project) on what real figures are
   available and usable for hourly trip profiles and mode shares for a Swedish town of Ängelholm's
   size: the national travel-habit survey (RVU Sverige), Trafikverket traffic counts, SCB,
   municipal material. Record for each candidate: what it gives, granularity, licence/openness,
   URL. If a figure can be used, cite it; if not, move on.
2. Create `apps/simulator/data/demand-statistics.json` with three blocks, each having `status`
   and `source`/`note`:
   - `total_trips_per_day`: **15,000**, `status: "estimate"`, note: chosen so that the average
     car rate is about today's 0.10 /s and the peak stays under the measured 0.35 /s ceiling
     (MVP-005 plan, Phase 5); *not* the municipality's real trip count (MVP-008).
   - `hourly_profile`: 24 relative weights for hours 00–23, `status: "estimate"`. Starting
     values (one per hour, relative; the loader normalises them):
     `1.0, 0.5, 0.4, 0.4, 1.0, 2.5, 5.0, 8.5, 7.5, 5.5, 5.0, 5.5, 6.5, 5.5, 5.5, 6.5, 8.0,
     8.5, 6.0, 4.5, 3.5, 2.5, 1.8, 1.4`. Shape: quiet night, morning rush 07–08, lunch bump,
     afternoon rush 16–17, evening decline. Replace with real figures from step 1 where found.
   - `mode_shares`: `car 0.60, bicycle 0.15, pedestrian 0.25`, `status: "estimate"`, note that
     they are shares of *trips spawned*, not of what is on screen (bicycles and pedestrians
     stay in the network longer; Phase 6 checks how it looks).
3. Add a top-level `_comment` describing how to edit the file, what each block means, that
   `status`/`source` must be kept honest, and the stability ceiling (peak car rate must stay
   clearly below ~0.35 /s).
4. Record what step 1 found (usable / not usable, and why) as a short "Findings from Phase 1"
   section at the end of this plan.
5. Run the pre-commit hooks (JSON/large-file/secret checks).

### Phase 2 — Load and validate the statistics; compute rates

*(commit message: "Add the demand profile loader and rate calculation")*

Pure Python, fully testable without SUMO. Uses `agents.Mode`.

1. Create `demand.py` with `DemandProfileError(ValueError)` and `DEFAULT_DEMAND_JSON` (path to
   `apps/simulator/data/demand-statistics.json`, same construction as
   `agents.DEFAULT_ENTRY_EXIT_JSON`).
2. Define the `Demand` Protocol: `rate(mode: Mode, sim_time: float) -> float` (individuals per
   simulated second) and `max_rate(mode: Mode) -> float` (an upper bound over all times).
3. Implement `ConstantDemand(rates: dict[Mode, float])`: `rate` returns the constant (0 for a
   missing mode), `max_rate` the same.
4. Implement `DemandProfile` (frozen dataclass): `total_trips_per_day: float`,
   `hourly_weights: tuple[float, ...]` (24, already normalised to sum 1),
   `mode_shares: dict[Mode, float]` (already normalised to sum 1). `rate(mode, t)` =
   `total × weights[int((t % 86400) // 3600)] × share[mode] / 3600`; `max_rate(mode)` = same with
   the largest weight.
5. Implement `load_demand_profile(path) -> DemandProfile`: read the JSON, and validate with
   messages that name the offending block: file readable and valid JSON; the three blocks
   exist; `total_trips_per_day` is a positive number; `hourly_profile.weights` has exactly 24
   entries, all numbers ≥ 0, not all zero; `mode_shares` has car/bicycle/pedestrian, all ≥ 0,
   not all zero; each block has a `status` of `"source"` or `"estimate"`. Normalise weights and
   shares. Ignore keys starting with `_`.
6. Implement `describe(profile) -> str`: e.g. `"15,000 trips/day; peak 08:00 (7.9 % of the day);
   car 60 % / bicycle 15 % / pedestrian 25 %; hourly profile: estimate"`, so the log shows what
   the run is using and how trustworthy it is.
7. Write `tests/test_demand.py`: valid file loads and normalises (weights sum to 1, shares sum
   to 1); each validation failure raises `DemandProfileError` with a useful message (missing
   block, 23 weights, negative weight, all-zero weights, unknown status, non-numeric total,
   invalid JSON, missing file); `rate` at hour boundaries and after wrapping past 24 h (e.g.
   `t = 86400 + 8×3600` equals `t = 8×3600`); `max_rate` ≥ every hour's rate; summing `rate ×
   3600` over the 24 hours and modes equals `total_trips_per_day`; `ConstantDemand`; and a test
   that the *committed* file loads and satisfies the acceptance criteria that can be checked
   statically (24 hours, peak/quiet ratio above a set bound, car share the largest, every
   block labelled).
8. Run `pytest`, `ruff format`, `ruff check`.

### Phase 3 — A time-varying arrival process in the source

*(commit message: "Drive spawning from the demand profile by thinning")*

1. In `agents.py`, change `RandomIndividualSource.__init__` to take `demand: Demand` in place of
   `rates_per_second` (keep `mode_edges`, `start_time`, `seed`).
2. Replace `_next_spawn` with `_next_candidate` per mode: for every mode whose
   `demand.max_rate(mode) > 0`, initialise to `start_time + rng.expovariate(max_rate)`.
3. Rewrite `due(sim_time)`: for each mode, while `_next_candidate[mode] <= sim_time`: take the
   candidate time `t`; accept it with probability `demand.rate(mode, t) / max_rate(mode)` (one
   `rng.random()`); on acceptance append the mode; then advance
   `_next_candidate[mode] += rng.expovariate(max_rate)`. Modes with `max_rate == 0` never spawn.
4. Delete `DEFAULT_RATES` and its comment block from `agents.py` (the constant is replaced by
   the data file; the calibration numbers stay in the MVP-005 plan and in the data file's
   `_comment`). Check nothing else imports it (tests do; update them in step 5).
5. Update `tests/test_agents.py`: existing `due`/`draw`/reproducibility tests use
   `ConstantDemand`; the "default rates cover every mode" test is replaced by a test that the
   committed profile has a positive `max_rate` for every mode.
6. Add statistical tests (fixed seed; wide, stated tolerances so they are robust, not flaky),
   driving `due()` in one-minute steps over 4 simulated days with a small hand-made
   `DemandProfile` (e.g. one hour 10× busier than the rest):
   - the hourly counts follow the profile (busy hour vs quiet hour ratio within tolerance);
   - the mode split matches `mode_shares` within tolerance;
   - the total over each day is close to `total_trips_per_day` (Poisson noise allowed);
   - day 2, 3 and 4 have the same shape as day 1;
   - a zero-share mode never spawns; a single huge time step returns the right number of
     arrivals and never returns arrivals from the future;
   - same seed → same sequence.
7. Run `pytest` with coverage, `ruff format`, `ruff check`.

### Phase 4 — Use the profile in the live run

*(commit message: "Run the live engine on the demand statistics")*

1. In `engine.py`, add `demand_file: Path = DEFAULT_DEMAND_JSON` to `run_live()`. Load it with
   `load_demand_profile()`; on `DemandProfileError` let it propagate (the CLI reports it).
   Log `describe(profile)` once at start (`logger.info`).
2. Build `RandomIndividualSource(load_mode_edges(net_file), profile, start_time=START_TIME,
   seed=seed)`.
3. In `run.py`, add `--stats PATH` (type `Path`, default `DEFAULT_DEMAND_JSON`), pass it as
   `demand_file`, and turn a `DemandProfileError` into a readable one-line error plus a non-zero
   exit code instead of a traceback. Update the docstring's usage block.
4. Extend the 15-minute progress line (or add a second, hourly line) so the log shows the
   *spawned in the last hour* per mode next to the concurrent counts. This is what the
   long-run checks in Phase 6 read; keep it cheap (counters only).
5. Update `tests/test_engine.py` and `tests/test_run.py`: `run_live` builds the source with the
   loaded profile and the given `demand_file`; `--stats` is passed through; an invalid file
   gives the readable error and exit code 1; the start-up log contains the description; the
   hourly-spawn counters are right for a scripted source.
6. Real check by hand: `simulator --headless --max-seconds 3600 --seed 1` runs, prints the
   description, and the spawn counts for the first hour (05:00–06:00, rising quickly) are
   visibly lower than for an hour later. Then run with `--stats` pointing to a scratch copy
   where one value was changed (e.g. car share 0.9) and confirm the mix changes with no code
   change — the acceptance criterion "change the file, change the behaviour".
7. Run `pytest`, `ruff`, `pre-commit run --all-files`.

### Phase 5 — Make the simulated time of day readable

*(commit message: "Show the simulated time of day while watching")*

Investigate first, build the simplest thing that works. Do the checks in order and stop at the
first that satisfies the owner's need ("it is not intuitive what time it is"):

1. Start `simulator` (GUI) and look at what `sumo-gui`'s own toolbar shows for the time. Check
   whether it can be switched to `HH:MM:SS` and whether, for a run beginning at 18000 s, it
   reads `05:00:00` and keeps counting past `24:00:00` sensibly. Record what you see, with a
   screenshot note, in "Findings from Phase 5".
2. If the toolbar already does the job, the fix may be documentation only (a line in the README
   and the start-up log saying where to look and how to toggle) — do that and skip the rest.
3. Otherwise check whether a `sumo-gui` view setting (`--gui-settings-file`) can show the time in
   the view; if yes, add it to the XML written by `write_gui_settings()` with a test asserting the
   element and a comment on how it was verified.
4. Otherwise try a TraCI-driven on-map label: one POI created at start (`traci.poi.add`) whose
   text/type is updated once per simulated minute with `format_clock()`, placed at a fixed spot;
   check that it stays readable when panning/zooming (POIs live in network coordinates). If it
   is workable, implement it in `engine.py` as a small, optional part of the step (guarded so a
   failure never stops the run), with mocked-`traci` tests.
5. Whatever is chosen, also make the start-up log say the mapping in words: "delay 200 ms per
   simulated second"; and keep the existing 15-minute clock line.
6. Run `pytest`, `ruff`, and repeat the real GUI check; confirm closing the window still ends
   the run cleanly.

### Phase 6 — Long runs: calibrate the total, verify the rhythm and stability

*(commit message: "Calibrate the demand statistics and verify multi-day behaviour")*

Measurement phase; code changes are limited to values in `demand-statistics.json` (and comments).
Use headless runs with a fixed `--seed` and read the hourly log lines from Phase 4.

1. Run 48 simulated hours (`simulator --headless --max-seconds 172800 --seed 1`, wall time is
   minutes). Record per hour: spawned per mode and concurrent travellers per mode.
2. Check the acceptance criteria against the log: the busiest hour spawns clearly more than the
   quietest; hourly spawns match the profile within the stated tolerance; the car/bicycle/
   pedestrian split of spawns matches the shares; cars are the largest group; day 2 has the same
   shape as day 1.
3. Check stability: concurrent travellers rise in the peaks and fall at night, do **not** grow
   from day to day, and there is no gridlock at the morning peak (no sustained upward trend at
   the peak, teleports at the usual low level). Measure the Python process's memory at the start
   and end (Windows `tasklist`, as in MVP-005).
4. Tune the values, not the code: if the peak car rate approaches the ceiling, lower
   `total_trips_per_day`; if the city is still too quiet, raise it while staying well below the
   ceiling. Re-run after every change and record the final numbers here (total/day, peak hour
   car rate, peak and night concurrent counts).
5. Look at the mix on screen, not only in the counts: the owner's MVP-005 complaint was that
   bicycles looked more numerous than cars. Record the concurrent split at the morning peak; if
   bicycles and pedestrians still visually dominate, decide with the owner whether to adjust
   the shares (the file) or to accept it and note it (a share of trips is not a share of what is
   present).
6. Measure the curated entry/exit share of live car spawns over a long run (a temporary
   measuring script in the scratchpad, as in MVP-005 Phase 5) — must remain a majority (MVP-005:
   74.5 %).
7. Update the data file's `_comment` and `note` fields with the calibrated reasoning, still
   labelling every value honestly. Record findings in "Findings from Phase 6".

### Phase 7 — Owner verification, docs and close

*(commit message: "Verify MVP-006 acceptance criteria and close the MVP")*

1. Ask the project owner to run `simulator` and watch across a stretch of the morning: quiet at
   05:00, filling towards the rush, cars visibly the main mode, the clock readable. Act on
   feedback by editing the statistics file (expected: value tuning, as in MVP-004/005), and
   record what was changed.
2. Decide whether an ADR is warranted: write `ADR-011` (statistics as a committed, labelled
   JSON file loaded at start-up; time-varying Poisson arrivals by thinning; shares apply to
   trips, not to travellers on screen) if it feels like a decision future work would otherwise
   question; add it to `decisions/README.md`. If not, say so in the MVP outcome.
3. Update `docs/architecture/overview.md` (module list including `demand.py`, data file, the
   live-engine description now says rate follows the profile), `current-state.md` (status, test
   count, coverage), `README.md`.
4. Re-verify earlier criteria for real: network unchanged (4,250 / 1,756), basemap/colours
   unaffected, full `pytest` green, coverage at or above the 95 % floor, `pre-commit` green.
5. Add "Outcome at close" to `docs/mvp/006-statistics-database.md` with the measured numbers per
   acceptance criterion and the owner's feedback; set this plan's status and `docs/roadmap.md`.
6. Show the diff and hand over commit messages; the owner does the commits and opens the PR (no
   push or merge from here).

## 5. Risks / open questions

* **Hitting the gridlock ceiling at the peak.** The city held ~200 concurrent at 0.10 cars/s and
  was proportional up to ~0.35 cars/s, then broke. The peak of a profile with a 2× peak-to-average
  ratio must stay clear of that; this is why Phase 6 measures multi-day runs and tunes the
  total rather than trusting the arithmetic. A jam that builds during the rush and does not
  clear at night would show as day-over-day growth.
* **Trips are not travellers.** A 60 / 15 / 25 split of spawned trips can still look
  pedestrian- or bicycle-heavy on screen, because those modes stay in the network longer.
  Decide in Phase 6 with the owner whether to adjust the shares or accept and document it.
* **Estimates dressed as facts.** The starting profile and shares are estimates. The
  `status`/`source` labels and the log line exist so they cannot be mistaken for measurements;
  keep them honest when values are edited, and replace with real figures (RVU Sverige,
  Trafikverket, municipal counts) when they are found and licensed.
* **Hourly step changes.** A piecewise-constant profile jumps at every full hour (e.g. 06:59 →
  07:00). It is probably invisible in a stochastic stream, but if the owner notices, linear
  interpolation between hour midpoints is a small, testable change to `DemandProfile.rate()`.
* **Time display may need a workaround.** No TraCI window-title setter exists; the toolbar,
  a view setting and a POI label are tried in that order in Phase 5. If none is good, the
  fallback is the log line and documentation, and the readability criterion is met by that
  alone only if the owner accepts it.
* **Data-file location.** Like `entry-exit-edges.json`, the file is found relative to the source
  tree, which works for a repo checkout/editable install only. Acceptable now; a packaged
  install would need it as package data (not needed yet).
* **A per-day total is a blunt instrument.** One `total_trips_per_day` for the whole day, and
  constant shares across hours, are deliberately simple. If the owner wants shares that vary
  by hour (more walking at midday), that is an extension of the same file — not needed for this
  MVP unless real data justifies it.
* **Open: ADR or not.** Expected small enough to skip, but decided in Phase 7, not assumed.
* **Open: does adding a per-hour log line clutter long runs?** Phase 4 keeps it to one line per
  simulated hour; if it is too noisy in the GUI console it can be folded into the existing
  15-minute line.

## Findings

### Findings from Phase 6 (48 simulated hours, headless, seed 1, then 24 more with PID-level memory)

* **Rhythm and profile:** spawned per hour matches the profile (cars: 03-04 about 41, 07-08 about
  712-740, 17-18 about 704-747); day 1 and day 2 have the same shape within noise. Daily totals:
  8,943 cars / 2,245 bicycles / 3,675 pedestrians a day against 9,000 / 2,250 / 3,750 expected.
* **Mode split of spawns over 48 h:** 60.2 % / 15.1 % / 24.7 % (configured 60 / 15 / 25).
* **Stability:** concurrent travellers about 10 at night, 250-300 at the 08:00 and 18:00 peaks, no
  day-to-day growth (08:00: 256 then 280; 18:00: 234 then 235); peak 316 (48 h) and 277 (24 h).
  Arrived tracks spawned; 0 skipped spawns. Python process 71.2 to 72.0 MB over 24 simulated
  hours. 64 teleports and 50 vehicle-person collisions in 48 h (MVP-005 level).
* **Mix on screen at the peaks:** roughly 90-130 cars, 30-38 bicycles, 95-128 pedestrians -
  bicycles are now clearly the smallest group (MVP-005's complaint), pedestrians remain the
  largest by count because they stay in the network longer.
* **Curated entry/exit share of live car spawns:** 74.2 % (48 h), 74.5 % (24 h).
* **No tuning needed:** the plan's starting values (15,000 trips/day, the 24 weights, 60/15/25)
  were kept; peak car rate 0.21 per second is well under the ~0.35 ceiling. Recorded in the
  data file's `_comment`.

### Findings from Phase 7

* Review against the standards found and fixed: two silent `except ... pass` blocks (now log at
  debug level, per the coding standard), missing docstrings on public methods
  (`RandomIndividualSource.due/draw`, `ConstantDemand`, `DemandProfile.max_rate`), and an
  unnecessary `_peak_weight` field on `DemandProfile` (now computed in `max_rate`, which is
  called once per mode at start-up).
* `ADR-011` written and indexed; architecture overview, current-state and README updated;
  roadmap status updated.
* Open: the owner's live confirmation (rhythm, mix, clock size and placement).

### Findings from Phase 5

Checked for real in `sumo-gui` (screenshots of the actual window), in the plan's order:

1. **`sumo-gui`'s toolbar clock is not enough.** It is a narrow green LCD. Two readings taken
   a while after start showed four digits (`0050`, later `0150`), i.e. the *minutes and
   seconds*; with the run starting at 05:00 (18000 s) the hour is clipped away, which is
   exactly the owner's "not intuitive what time it is". (Reading of the seven-segment digits
   from screenshots, consistent across two captures; not confirmed against SUMO's source.)
2. **No view setting for a time display:** `viewsettings_file.xsd` has none (its only `time`
   attributes belong to breakpoints), and `traci.gui` has no window-title setter.
3. **A POI label works and is what was built.** `traci.poi.add(...)` with a `poiType` text,
   shown by the view settings `<pois poiType_show="1" poiType_size="60" poiType_color="red"/>`
   (attribute names found by searching `sumo-gui.exe`'s strings, then confirmed by a prototype
   in the scratchpad). The engine keeps the POI at the top-left corner of the current view
   (`traci.gui.getBoundary()` every step) so it stays put while panning/zooming, and changes
   its text only when the minute changes. Real `simulator` run: a red `05:01` label is
   visible in the view corner, counting up.
4. **Only in the GUI:** headless `sumo` has no view, so `run_live()` passes
   `show_clock=not headless`. Creating or updating the label is cosmetic: a `TraCIException`
   is logged once at creation (and turns the clock off) or ignored at update, never stopping
   the run; a closed GUI (`FatalTraCIError`) still ends the run cleanly.
5. Tests: 138 (was 129) with `engine.py` and `context_features.py` at 100 %.
6. The toolbar `Delay (ms)` field is unchanged (200); how long a simulated second takes stays a
   backlog item (a friendlier speed control).

### Findings from Phase 4

* `--stats PATH` works; an invalid file gives one readable line and exit code 1, no traceback
  (real check with a 23-hour profile: `Invalid demand statistics: hourly_profile.weights must be
  a list of exactly 24 numbers … got 23`).
* **The acceptance criterion "change the file, change the behaviour" was demonstrated for
  real:** the same seed and 2 hours with the committed shares (60/15/25) spawned 660 cars /
  151 bicycles / 246 pedestrians; with a scratch copy at 90/5/5 it spawned 980 / 49 / 48, and
  the start-up line printed the new shares. No code change between the two runs.
* **The hourly log line works and shows the daily rhythm** (4-hour run, seed 1, spawned in the
  last hour): 05–06: 213 cars / 58 bicycles / 90 pedestrians → 06–07: 447 / 93 / 156 →
  07–08: 726 / 179 / 319 → 08–09: 662 / 172 / 258. Cars clearly the largest group; the morning
  rises about 3.4× from the first hour to the peak.
* Concurrent travellers over the same run: ~50 at 05:15, ~130–150 around 07:30–08:45, roughly
  what MVP-005 held all day at 0.24 spawns/s — the peak here is a little above MVP-005's
  steady state, well under the gridlock ceiling. Calibration and multi-day stability are Phase 6.

### Findings from Phase 3

* Thinning implemented in `RandomIndividualSource`; `DEFAULT_RATES` removed. Statistical tests
  over 4 simulated days at a fixed seed (busy hour ≈ 10× a quiet hour; hourly counts, daily
  total, mode split and day-to-day shape all within the stated tolerances) pass on the first
  run; they take ~3 s, so a fixed seed keeps them deterministic, not flaky.
* **Phase 4 steps 1–2 were done here on purpose:** `run_live()` needed the new `demand`
  argument or the live command would have been broken at this commit. `run_live(...,
  demand_file=DEFAULT_DEMAND_JSON)` now loads the profile, logs `Demand: <describe()>` and passes
  it to the source. Left for Phase 4: `--stats`, readable CLI error, hourly-spawn log line.
* First real 2-hour run (seed 1, 05:00–07:00): quiet start (about 50 travellers at 05:15),
  rising towards the rush (~130 at 07:00), cars now the largest group (660 spawned vs 246
  pedestrians and 151 bicycles) — the opposite of MVP-005's bike-heavy look. Peak concurrent 147.
  Not yet a calibration: the busy hours are still ahead.

### Findings from Phase 2

* `demand.py` imports `agents.Mode`, so Phase 3 must not import `demand` at runtime from
  `agents.py` (circular): `agents.py` imports `Demand` only under `TYPE_CHECKING`
  (`from __future__ import annotations` is already in place).
* The committed file is now covered by tests (`TestCommittedFile`): 24 hours, honest labels,
  a real daily rhythm (night weight ≪ 07:00/17:00 weights, 05:00 below the morning peak), cars
  the largest share, every mode can spawn, and the peak car rate under 0.30 /s (the measured
  gridlock ceiling is ~0.35 /s). A future edit that breaks these fails the test suite.
* Tests: 113 (was 71), `demand.py` at 100 % coverage, total 99 %.

### Findings from Phase 1

Bounded look (a few searches and fetches, not a research project) at real figures. **Result: no
real figures were extracted or used; every value in `demand-statistics.json` is a labelled
estimate.** What was found:

* **Trafikverket, "Trafikvariation och lastbilsandelar" (TMALL 0004 rapport, `bransch.trafikverket.se`).**
  Exists and, according to its own description, has traffic-variation schemas for urban and
  rural roads (variation by month, weekday and hour, with hourly flows for passenger cars
  derived from ÅDT). This is the best candidate for the *hourly profile*. The URL from the
  search result returned HTTP 404 when fetched, so the table itself was not read and its usage
  terms were not checked. Traffic-count data (`Vägtrafik- och hastighetsdata`) is a separate
  Trafikverket service, not looked into further.
* **Trafikanalys, "RVU Sverige" (national travel-habit survey).** Reports mode shares and trip
  start times (in the search summary: most weekday trips start 07:00–08:00, largely work and
  school). The 2011–2014 and 2015–2016 report PDFs were fetched but their text was not
  extractable in this session, so no numbers were read. A search snippet mentioned car at 58 %
  of trips in Västra Götaland's own regional survey — an unverified pointer only, *not* used as a
  figure, though it makes a ~60 % car share plausible as a first estimate. Candidate for
  the *mode shares* and a cross-check of the profile.
* **Not looked for:** anything specific to Ängelholm (municipal counts, SCB local data). To be
  revisited when MVP-008 (realistic scale) needs local numbers.

Consequence: the file uses estimates (15,000 trips/day, the 24 weights in the plan, 60/15/25
shares), each marked `"status": "estimate"` with the candidate real sources named in its note.
Checked arithmetic on the committed values: 24 weights, peak hour = 8.25 % of the day (~2.0× the
average hour), average car rate 0.104 /s, **peak car rate 0.206 /s** — under the 0.35 /s ceiling
as the plan assumed. Replacing an estimate with a real figure later is an edit to this file
only (set `status` to `"source"` and fill in `source`).
