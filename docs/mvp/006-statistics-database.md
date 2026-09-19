# MVP-006 – Statistics Database

## Purpose

Replace the hand-tuned, constant spawn rates of MVP-005 with a small, data-driven
statistics layer, so that *how much* traffic appears, *when*, and *by which mode* comes from
data that can be read, questioned and changed without touching code.

MVP-005 proved the live engine but its numbers are three constants in `agents.py`
(`DEFAULT_RATES`): the same traffic at 05:00 as at 08:00 and at 14:00, and a car/bicycle/
pedestrian mix tuned by eye. The project owner's review of it was clear: the city feels "as
if it were 6 in the morning", and bicycles seem to outnumber cars although cars should
dominate. Both are questions of statistics, not of engine mechanics — this MVP answers them.

The individuals themselves stay random in *where* they go (random origins and destinations,
curated entry/exit bias as before). Where trips go, and why, is MVP-007 (zones). Who a person
is, and their daily plan, is MVP-009. This MVP is only about the volume and the mix over
the day.

## Goals

* A committed statistics file (or files) holds, in plain readable form:
  * **Departures per hour of day** — a profile over 24 hours (quiet night, morning peak,
    lunch bump, afternoon peak, evening decline) expressed as a share of the day's trips
    or as a relative weight per hour.
  * **Mode shares** — the share of trips made by car, bicycle and on foot, optionally
    varying by hour.
  * A clearly stated **total trips per day** (or per peak hour) that scales the whole
    profile up or down in one place.
* The engine's spawning follows those statistics: the arrival rate for each mode at any
  simulated time of day is derived from the profile, the mode shares and the total, so the
  city is quiet at night, busy in rush hours, and the mix looks right.
* Every number in the statistics file carries its **source or status**: a real published
  figure (with a reference) or an explicitly marked estimate to be replaced. No unlabelled
  "magic numbers".
* Changing the statistics means editing the data file, not Python code; the engine reads it
  at start-up and reports what it loaded.
* The mix visibly changes for the better: cars clearly outnumber cyclists in what is spawned
  and in what the owner sees, and pedestrians are a sensible share.
* The simulated **time of day is easy to read while watching**, so the daily rhythm can
  actually be seen (a known rough edge from MVP-005 review, where it was unclear what
  time it was).
* Still live, still endless, still only patterns reproducible: the 24-hour cycle repeats
  every simulated day. A seed remains optional, for debugging.
* Nothing regresses: the engine keeps starting empty at 05:00, the curated entry/exit bias
  holds, and a long run stays stable — the city must not gridlock at the peak hour.

## Context

Things known before scoping, and things the plan has to check:

* **The seam already exists.** MVP-005 separated *who/when/where* (`IndividualSource`,
  `RandomIndividualSource`) from the loop that steps SUMO. Its `due()` uses Poisson
  arrivals with a constant rate per mode; a time-varying rate is a change inside the source,
  not in `engine.py`. The plan must check that a time-varying Poisson process (e.g. by
  thinning against the day's peak rate) is implemented correctly and stays cheap per step.
* **There is a measured ceiling.** MVP-005's calibration showed traffic scaling roughly
  linearly with the spawn rate up to about 0.35 cars per second and gridlocking well before
  0.7 (see the MVP-005 plan, Phase 5). A peak-hour profile that multiplies the base rate must
  stay under that, or the morning peak will jam the city permanently. The plan must verify
  the chosen peak with long runs, not assume it.
* **Trips are not travellers.** Mode shares apply to *trips spawned*, but what the owner sees
  is *concurrent travellers*. Bicycles and especially pedestrians stay in the network far
  longer per trip than cars (in MVP-005 pedestrians were about half of everything present
  from about a fifth of the spawns), so a plausible trip share can still look bike- or
  walker-heavy on screen. Which of the two the statistics should match is a real question
  for the plan; the acceptance criteria below stay about what is spawned, and the owner's
  visual judgement covers what is seen.
* **Data sources are not chosen yet.** Real inputs exist — the national travel-habit survey
  (RVU Sverige), Trafikverket traffic counts, Statistics Sweden (SCB), municipal counts for
  Ängelholm — but none is in the repository, and some may not be openly usable offline. The
  plan must find out what is actually available and licensed before promising any of them;
  this MVP does not require that every value is a published figure.
* **Format and dependencies.** The statistics must be readable and editable by a person and
  loadable without a new runtime dependency if possible (JSON is already used for
  `entry-exit-edges.json`; the plan should justify anything else, following the dependency
  standard and an ADR if significant).
* **Time display.** How to show the time of day in `sumo-gui` (its own clock format,
  the window title through TraCI, an overlay, or console output only) has not been checked
  and is part of the plan's investigation.

## Scope

The MVP includes:

* A committed, human-readable statistics file with hourly departure profile, mode shares and
  a total-volume scale, each value labelled with source or "estimate".
* A small loader that reads and validates it (profile covers 24 hours, shares are non-negative
  and sum sensibly, clear errors otherwise) and a typed structure the engine uses.
* A time-varying arrival process in the random source, driven by the simulated clock, so the
  rate per mode follows the profile and repeats each simulated day.
* Making the simulated time of day readable while watching, by the simplest method the plan
  verifies for real.
* A first, honest set of values: real figures where they can be found and used, clearly
  marked estimates otherwise, chosen so that the morning shows a rush, cars dominate the
  spawns and the peak stays under the measured gridlock ceiling.
* Tests for the loader, the time-varying arrival process and the mode mix, plus long-run
  checks (headless) that the daily rhythm and stability hold over several simulated days.
* Documentation: the statistics file's format and how to change it, and an ADR if the
  format or source choice is significant.

## Out of Scope

The following are deliberately excluded and belong to later MVPs or the backlog:

* Where people go — zones, land use and destination attractiveness — **MVP-007**.
* Realistic absolute numbers for the whole municipality and the core/outside split —
  **MVP-008**. Here the total is a single adjustable scale that keeps the city stable, not a
  calibrated population.
* Individuals with identities, homes, jobs and return trips — **MVP-009**. A trip is still
  one-off; the profile describes *departures*, not people's days.
* Trip purposes as a driver of destinations (work, school, shopping), and mode *choice* by
  a person (a random draw from shares is enough here).
* A friendlier speed control (backlog): only the time of day becomes readable; the delay
  setting stays as it is.
* Problems seen in MVP-005 long runs — cars stuck behind cyclists, pedestrians on roads,
  recurring teleports/collisions (backlog: routing, lanes, crossings, signals).
* Calibrating against measured counts or traffic-light programs.
* Changing the network, the basemap, the entry/exit list or the engine's stepping loop.

## Acceptance Criteria

* A committed statistics file exists containing an hourly departure profile, mode shares and a
  total-volume scale; each value states its source or is marked as an estimate — verified by
  reading the file, and by the loader rejecting an invalid file (missing hour, negative
  value, shares that cannot be used) with a clear message.
* The number of individuals spawned per simulated hour follows the profile — verified
  programmatically over several simulated days: the busiest hour spawns clearly more than the
  quietest, and the measured hourly counts match the profile within a stated tolerance.
* Over the same run, the split of spawned individuals between cars, bicycles and pedestrians
  matches the configured mode shares within a stated tolerance, and cars are the largest
  group of spawns.
* Changing a value in the statistics file changes the simulation's behaviour on the next
  run with no code change — demonstrated once for real.
* The daily rhythm repeats: consecutive simulated days show the same shape — verified from a
  multi-day headless run.
* Stable: over at least 24 simulated hours the number of concurrent travellers follows the
  rhythm (rises in the peaks, falls at night) without growing from day to day, no gridlock
  at the peak hour, and the Python process does not grow — verified by measuring, not
  assumed.
* A majority of car trips still start or end at one of the 8 curated entry/exit edges, as
  in MVP-004/005.
* The simulated time of day can be read while watching in `sumo-gui`, by the method the plan
  settles on.
* The project owner watches it live and confirms that the city reads as living through a day
  — quieter at 05:00 than at the morning peak — and that cars, bicycles and pedestrians look
  like a plausible mix, or names what to change in the estimates.
* Earlier acceptance criteria still hold: network unchanged (4,250 edges / 1,756
  junctions), basemap and colours unaffected, the full `apps/simulator` test suite passes with
  coverage at or above the floor — confirmed by re-running them.

## Open Questions for the Plan

To be answered by checking, not by assuming:

* Which statistics are actually available for Ängelholm or Sweden, under what licence, and at
  what granularity (per hour, per mode)? What is used as a real figure and what stays a
  labelled estimate for now?
* Should mode shares be constant or vary by hour (more walking and cycling at midday, more
  car use in commuting hours)? Start constant unless data justifies more.
* Do the shares apply to trips spawned or to concurrent travellers on screen, given how long
  each mode stays in the network? (Leaning: trips spawned, with a documented note.)
* How is the peak hour's total set so it stays under the measured gridlock ceiling — a
  single scale factor, a stated cap, or both?
* How is the time of day best shown in `sumo-gui`, and does it need TraCI's help?
* JSON or another format, and does a new dependency or ADR follow? Expected: JSON, no new
  dependency.
* How are day boundaries handled — the run starts at 05:00 and never ends, so the profile has
  to wrap at midnight cleanly.
