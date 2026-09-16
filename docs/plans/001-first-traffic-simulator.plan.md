# Plan: MVP-001 – First Traffic Simulation

Reference: [`docs/mvp/001-first-traffic-simulator.md`](../mvp/001-first-traffic-simulator.md)

**Status:** In progress — Phase 1 complete.

## 0. Investigation

Checked, for real, what's actually available before committing to a mechanism — the
architecture doc only named SUMO/OpenStreetMap as *candidates*, so this had to be verified,
not assumed:

- **No SUMO install found**: no `sumo`/`sumo-gui`/`netconvert`/`duarouter` on `PATH`, no
  `SUMO_HOME`, no relevant Python packages (`sumolib`, `traci`, `osmnx`, `networkx`,
  `geopandas`, `osmium`) installed in the `angelholm` environment.
- **Important correction of an assumption**: the conda-forge package literally named `sumo`
  is *not* the traffic simulator — it's an unrelated package ("Heavy weight plotting tools
  for ab initio solid-state calculations"). Installing it would have been a real, silent
  mistake. The actual project publishes as **`eclipse-sumo`** on PyPI (current version
  `1.27.1`), with `traci` and `sumolib` as separate, matching-versioned PyPI packages —
  confirmed by querying PyPI's JSON API directly, not by memory.
- `eclipse-sumo` ships a `win_amd64` wheel (works on this Windows dev machine) and
  `manylinux2014`/`manylinux_2_28` wheels for `x86_64`/`aarch64` (works on CI's
  `ubuntu-latest`) — no separate installer needed on either side, `pip install` is enough.
  It is **not** on conda-forge under any name checked, so it belongs in `requirements.in`
  (pip-compiled), not `environment.yml`'s conda-native block.
- **Licence gap (blocking)**: `eclipse-sumo`'s PyPI metadata doesn't carry a machine-readable
  licence field. SUMO is publicly documented (project site/GitHub) as dual-licensed
  **EPL-2.0 / GPL-2.0-or-later** — neither is on `ci.yml`'s current `pip-licenses`
  allow-list (`Apache-2.0`, `BSD-*`, `MIT`, `MPL-2.0`, `PSF-2.0`). Adding this dependency
  will fail the `dependencies` CI job until the allow-list is updated, which per
  `docs/standards/dependencies.md`'s exception process needs someone to confirm the licence
  is acceptable — this plan can't make that call unilaterally (see Risks).
- **OSM data**: verified real, live Overpass API access works from this environment (not
  just DNS/ping — an actual authenticated-looking query). A bbox query for central
  Ängelholm, `56.2430,12.8580` to `56.2470,12.8660` (~300m × 450m), returned **87 real
  highway ways** — enough substance for a small MVP network, not so much that it's an
  unreasonable "first" scope. Proposed as the candidate area; changeable, it's just the
  first real, verified option rather than a guess.
- SUMO's official OSM workflow needs no `osmnx`/`geopandas`/`networkx`: `netconvert
  --osm-files <file> -o network.net.xml` consumes raw OSM XML directly, and
  `randomTrips.py` (bundled with `eclipse-sumo`'s `tools/`) generates synthetic trips —
  matching MVP-001's own "traffic may be synthetic" scope, and keeping the dependency
  footprint to exactly `eclipse-sumo` + `traci` + `sumolib`.
- `sumo-gui` needs a display — CI (`ubuntu-latest`, headless) can only ever run the
  non-GUI `sumo` binary. Visual verification (acceptance criterion "observed visually
  while running") is a manual, human step, not something this session or CI can confirm on
  its own.

## 1. Goal

A documented, single command starts a real SUMO simulation of the verified small area of
central Ängelholm: a routable network built from real OSM data, at least 10 vehicles
following valid routes, visible in `sumo-gui`, running to completion without manual
intervention or errors — matching every acceptance criterion in
`docs/mvp/001-first-traffic-simulator.md`.

## 2. Scope boundary

- **In:** `eclipse-sumo`/`traci`/`sumolib` as new dependencies; an ADR for the SUMO +
  OpenStreetMap choice; the first real application (`apps/simulator/`), finally resolving
  `pyproject.toml`'s and `pytest.ini`'s long-placeholder package paths; fetching one small
  OSM extract and converting it with `netconvert`; generating ≥10 random trips; a runnable
  headless + GUI simulation; a documented start command; the licence-allowlist decision
  (flagged to the user, not decided here).
- **Out:** everything `docs/mvp/001-first-traffic-simulator.md` already excludes (bicycles,
  pedestrians, population/demand, scenarios, calibration, a custom web UI/map) — see that
  document's "Out of Scope" for the full list, not repeated here.

## 3. Chapters addressed

- [C2 – Beroendehantering, paketkällor & signering](../methodology/c-sakerhet/beroendehantering-paketkallor-och-signering.md)
  — new dependency + licence-scan gate.
- [B2 – Arkitektur- och designprinciper](../methodology/b-skriva-kod/arkitektur-och-designprinciper.md)
  — first real `apps/` structure.

## 4. TODOs

### Phase 1: Add the SUMO toolchain as a dependency

- [x] Add `eclipse-sumo`, `traci`, `sumolib` (pinned to the same verified `1.27.1`-compatible
  range) to `requirements.in`. Result: `sumo-data==1.27.1` was also pulled in automatically
  as a transitive dependency (bundled default templates) — not something to pin separately.
- [x] Recompile `requirements-lock.txt` and commit both files. Result: verified no real
  drift via a proper per-package hash-set comparison (order-independent) before and after —
  same lesson as MVP-000's close-out, `pip-compile`'s hash-line order isn't stable.
- [x] Verify inside the `angelholm` env. Result: `sumo --version` →
  `Eclipse SUMO sumo 1.27.1` (copyright DLR); `netconvert --version` works; both are real
  console scripts on the env's `Scripts/` dir (`sumo.exe`, `sumo-gui.exe`,
  `netconvert.exe`, `duarouter.exe`), directly callable, not requiring a `python -m`
  invocation. `randomTrips.py` is at
  `Lib/site-packages/sumo/tools/randomTrips.py` (a script, not a console entry point —
  invoke via `python <path>`). `import traci, sumolib` succeeds.
- [x] Raise the licence-allowlist gap with the user before this phase is considered done.
  Result: approved by the project owner 2026-09-16. Added the exact string `pip-licenses`
  reports (`EPL-2.0 OR GPL-2.0-or-later`, verified for real, not guessed) to `ci.yml`'s
  allow-list and to `docs/standards/dependencies.md`, which — while here — was also
  upgraded from a still-unfilled template list to the real, actual allow-list `ci.yml`
  already enforced.
- [x] Write ADR-006: SUMO + OpenStreetMap as the simulation engine and geographic data
  source, including the conda-forge name-collision finding as context.

### Phase 2: Create the simulator app skeleton

- [ ] Create `apps/simulator/` — first real app in the workspace (see
  `docs/architecture/overview.md` "Planned Evolution").
- [ ] Add a minimal `apps/simulator/pyproject.toml` (packaging metadata only, per
  `AGENTS.md`'s `pip install -e apps/<app>` convention) and a `tests/` folder.
- [ ] Resolve the long-standing placeholders this unblocks: `pyproject.toml`'s
  `[tool.ruff] src` / `[tool.coverage.run] source`, `pytest.ini`'s `testpaths` — point them
  at the real `apps/simulator` paths instead of `<your_package_1>` etc.
- [ ] Update `AGENTS.md`'s "Applications" table and "Local commands" block, `README.md`'s
  workspace-structure note, and `docs/architecture/current-state.md`'s Applications table —
  all currently say "none yet."

### Phase 3: Fetch OSM data and build the routable network

- [ ] Script the Overpass fetch for the verified bbox (`56.2430,12.8580,56.2470,12.8660`),
  saving raw OSM XML under `apps/simulator/data/` — decide, and record the decision, whether
  to commit this extract as a fixture (reproducibility, per the "Scenarios Should Be
  Reproducible" principle in `overview.md`) or re-fetch live each run (freshness, but
  network-dependent); default recommendation is to commit a small snapshot.
- [ ] Run `netconvert --osm-files <file> -o network.net.xml`; verify a clean exit code and
  no unhandled warnings.
- [ ] Sanity-check the resulting network (edge/junction count > 0, loads back via `sumolib`).

### Phase 4: Generate traffic and run the simulation

- [ ] Use `randomTrips.py` (or `sumolib`/`traci` directly) to generate ≥ 10 random vehicle
  trips over the network.
- [ ] Write a `.sumocfg` tying the network and routes together.
- [ ] Verify headless `sumo -c <config>` runs to completion with no errors — this is the
  one part of the acceptance criteria that can be automated/checked programmatically.
- [ ] **Manual step, needs the user**: open the same config in `sumo-gui` and confirm the
  network and moving vehicles are visible — cannot be verified from this session (no
  display).

### Phase 5: Wire up a repeatable start command and update docs

- [ ] Add a documented entrypoint (e.g. `apps/simulator/run.py` or a small script) so "a
  developer can start the simulation again using documented project instructions" is
  concretely true, not just implied.
- [ ] Update `docs/architecture/overview.md`'s "Major Components" (Geographic Model /
  Mobility Simulation move from "not yet implemented" to a real, minimal implementation)
  and "Current Workspace Structure".
- [ ] Update `docs/architecture/current-state.md`'s Applications table with the new
  `apps/simulator` row (status, test count, capabilities).
- [ ] Run `pytest -q`, `ruff format --check .`, `ruff check .`; confirm all green.
- [ ] Fill in `docs/mvp/001-first-traffic-simulator.md`'s "Outcome at close" against each
  acceptance criterion, honestly — including the GUI check, which only the user can attest
  to.

## 5. Risks / open questions

- **Licence allow-list**: this plan cannot resolve whether EPL-2.0/GPL-2.0-or-later is
  acceptable for this project — that needs the user (or whoever owns licence policy here)
  to decide and record it in `docs/standards/dependencies.md`, per its own exception
  process. Blocking for Phase 1/CI, not something to route around.
- **GUI verification** is inherently manual — no amount of automation in this session
  substitutes for the user actually watching `sumo-gui` run.
- **OSM extract reproducibility**: committing a data snapshot vs. fetching live each run is
  a real trade-off (offline/reproducible vs. always-current); Phase 3 proposes committing a
  snapshot as the default, open to being overridden.
- The bbox is a verified-real but still first-pass choice — if the user wants a different,
  more recognizable area of Ängelholm, that's a cheap change before Phase 3 runs the fetch,
  not after.
- `apps/simulator/pyproject.toml`'s shape (dependencies section, entry points) hasn't been
  precedented anywhere in this repo yet — this plan is also implicitly setting the pattern
  the next app will copy; worth a second look before merging for exactly that reason.
