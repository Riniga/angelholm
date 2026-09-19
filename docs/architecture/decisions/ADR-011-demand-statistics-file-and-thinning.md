# ADR-011: Drive spawning from a committed, labelled statistics file using time-varying arrivals

**Status:** Proposed
**Date:** 2026-09-19

## Context

MVP-005's live engine spawned individuals at three constant rates that lived in Python
(`DEFAULT_RATES`): the same traffic at 05:00 as at 08:00, and a car/bicycle/pedestrian mix
tuned by eye. The project owner's review was that the city felt "as if it were 6 in the
morning" and that bicycles looked more numerous than cars. MVP-006 makes volume, daily rhythm
and mode mix a matter of data.

Checked for real, not assumed:

- **Real figures could not be used yet.** Trafikverket's "Trafikvariation och lastbilsandelar"
  (hourly variation for urban roads) and Trafikanalys' RVU Sverige (trip start times and mode
  shares) exist and are the natural sources, but the former's URL returned 404 and the RVU PDFs
  were not text-extractable in the session, so no number was read and no licence was checked.
  Nothing Ängelholm-specific was looked for.
- **A time-varying Poisson process can be generated exactly by thinning** (candidates at the
  busiest hour's rate, each kept with probability `rate(t) / max_rate`). Tested over four
  simulated days: hourly counts, daily total, mode split and day-to-day shape match the
  profile within stated tolerances.
- **The city has a measured ceiling** (MVP-005 plan, Phase 5): traffic scaled roughly linearly
  up to ~0.35 cars per second and gridlocked well before 0.7. The chosen profile's peak car
  rate is 0.21 per second.
- **`sumo-gui`'s toolbar clock clips the hour** (the LCD showed MM:SS in real captures), there is
  no view setting or TraCI window-title setter for a time display, but a POI's type text shown
  through `poiType_show` works and can be kept in the view corner by following
  `traci.gui.getBoundary()`.
- Over 48 simulated hours with the calibrated file: spawns match the profile, the shape repeats
  day to day, concurrent travellers follow the rhythm (about 10 at night, ~250–300 at the peaks)
  without growing, the Python process stayed flat, and 74.2 % of car trips touch a curated
  entry/exit edge.

## Decision

Keep the demand statistics in one committed, human-editable JSON file
(`apps/simulator/data/demand-statistics.json`): total trips per day, a 24-hour departure
profile and mode shares. **Every block carries a `status` of `"source"` or `"estimate"` and a
`source`/`note`**, and the start-up log prints which it is, so an estimate cannot pass for a
measurement. `simulator.demand` validates the file (clear errors, exactly 24 hours,
non-negative values) and exposes it as a `Demand` (`rate(mode, t)`, `max_rate(mode)`); the
random source generates arrivals by thinning against it, and the profile wraps at midnight.
`--stats PATH` selects another file without a code change.

Mode shares apply to **trips spawned**, not to travellers on screen. The simulated time of day is
shown as a text label (a POI) that `simulator.engine` keeps in the view's top-left corner, GUI
runs only.

## Consequences

**Benefits:**

- The daily rhythm and the mix are data, editable and reviewable; replacing an estimate with a
  real figure later is an edit to the file only.
- Honest by construction: labels in the file and in the log line.
- Cars are the largest group of spawns again; the busy hour spawns ~3.4× the first hour.
- The engine's stepping loop is unchanged; only the source and a small clock label were added.

**Trade-offs:**

- All current values are estimates (15,000 trips/day, an estimated 24-hour profile, 60/15/25
  shares), not the municipality's real trip count; realistic scale is MVP-008.
- A share of trips is not a share of what is visible: bicycles and pedestrians stay in the
  network longer per trip. At the 48-hour peak the concurrent mix was roughly 90–130 cars,
  30–38 bicycles and 95–128 pedestrians.
- The profile is piecewise-constant per hour (a step at each full hour). Invisible in a
  stochastic stream so far; interpolation is a small change if it ever shows.
- The file is found relative to the source tree (as `entry-exit-edges.json` is), which works for
  a checkout/editable install, not a packaged install.
- The clock label is a workaround for what `sumo-gui` offers, not a feature of SUMO; it is
  cosmetic and never allowed to stop a run.

## Alternatives considered

- **Constants in Python (the MVP-005 way):** no rhythm, mix tuned by eye, and every change is a
  code change.
- **YAML or a database:** no new dependency is needed for JSON, which the repo already uses;
  a database is far heavier than a 24-number profile.
- **Integrating the rate numerically to draw arrival times:** thinning is exact, simpler and one
  random number per candidate.
- **Waiting for real published figures before shipping:** would block the daily rhythm on data
  that could not be read yet; labelled estimates deliver the behaviour now and keep the upgrade
  path open.
- **Only the toolbar clock (documentation fix):** it clips the hour, which was the very
  complaint.
