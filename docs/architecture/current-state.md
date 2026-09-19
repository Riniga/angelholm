# Current Architecture State

Short reference for the current state of the workspace. For full context see
[`overview.md`](overview.md). Keep this current — it's the quick-scan version; update it
in the same PR as any change to an app's status, test count, or key capabilities.

## Applications

| App | Status | Tests | Key capabilities |
|-----|--------|-------|-------------------|
| `apps/simulator` | Implemented (MVP-001 to MVP-005) | 71 | Fetches a real OpenStreetMap extract, builds a routable SUMO network clipped to the outlined central-Ängelholm coverage area (`docs/architecture/mapoutline.png` — 4,250 edges, 1,756 junctions), shows a georeferenced basemap image behind the network in `sumo-gui`, and runs a **live** simulation: an empty city at 05:00 into which a TraCI control loop keeps spawning cars, bicycles and pedestrians (cars biased toward 8 curated entry/exit roads; ~200 concurrent) and SUMO removes them on arrival — indefinitely, headless or via `sumo-gui`, all through the `simulator` console command (`--max-seconds`, `--seed`) |

## Shared packages

None yet. No `packages/` directory exists. Code only moves to a shared package once it is
actually reused by ≥ 2 apps (see `AGENTS.md` "Architecture guardrails") — record that
boundary decision as an ADR when it happens.

## Conventions

See `docs/standards/*.md` (coding, testing, git, documentation, dependencies) — nothing
project-specific deviates from them yet.

## Dependencies

`apps/simulator` depends on `eclipse-sumo`/`traci`/`sumolib` (SUMO, exactly pinned —
`ADR-006`), `shapely` (outline-polygon representation for network clipping — `ADR-007`),
`pyproj` (converts the background image's known corners into network coordinates —
`ADR-008`) and `defusedxml` (XXE-safe parsing of the committed network file — a real
Semgrep SAST finding on plain `xml.etree.ElementTree`, fixed properly rather than
suppressed). The development-tooling dependency surface (Conda `angelholm` environment,
Ruff, pytest, `pytest-cov`, pre-commit, plus `numpy`/`opencv-python-headless`/`pillow` for
the one-off `scripts/extract_coverage_outline.py` and
`scripts/convert_context_background.py`) is scaffolded — see
`docs/architecture/overview.md` "Existing Dependencies" for the detail.

## Test counts

`apps/simulator`: 71 tests, all mocked/deterministic (no live network, no live SUMO
invocation; live-engine behaviour is verified by manual bounded runs, recorded in
`docs/plans/005-live-agent-engine.plan.md`). Coverage: 99.69% measured 2026-09-19 — floor set to 95% in `pyproject.toml`
(`ADR-004`, `GAP-D1-COVERAGE` closed).

## Methodology compliance

See [`docs/methodology-compliance/`](../methodology-compliance/) — this section is a
one-line pointer, not a duplicate of the gap register.
