# Current Architecture State

Short reference for the current state of the workspace. For full context see
[`overview.md`](overview.md). Keep this current — it's the quick-scan version; update it
in the same PR as any change to an app's status, test count, or key capabilities.

## Applications

| App | Status | Tests | Key capabilities |
|-----|--------|-------|-------------------|
| `apps/simulator` | Implemented (MVP-001 + MVP-002, MVP-002 in progress) | 25 | Fetches a real OpenStreetMap extract, builds a routable SUMO network clipped to the outlined central-Ängelholm coverage area (`docs/architecture/mapoutline.png` — 4,250 edges, 1,756 junctions), generates synthetic traffic, runs headless or via `sumo-gui` — all through the `simulator` console command |

## Shared packages

None yet. No `packages/` directory exists. Code only moves to a shared package once it is
actually reused by ≥ 2 apps (see `AGENTS.md` "Architecture guardrails") — record that
boundary decision as an ADR when it happens.

## Conventions

See `docs/standards/*.md` (coding, testing, git, documentation, dependencies) — nothing
project-specific deviates from them yet.

## Dependencies

`apps/simulator` depends on `eclipse-sumo`/`traci`/`sumolib` (SUMO, exactly pinned —
`ADR-006`) and `shapely` (outline-polygon representation for network clipping — `ADR-007`).
The development-tooling dependency surface (Conda `angelholm` environment, Ruff, pytest,
`pytest-cov`, pre-commit, plus `numpy`/`opencv-python-headless` for the one-off
`scripts/extract_coverage_outline.py`) is scaffolded — see `docs/architecture/overview.md`
"Existing Dependencies" for the detail.

## Test counts

`apps/simulator`: 25 tests, all mocked/deterministic (no live network, no live SUMO
invocation). Coverage: 99.21% measured 2026-09-18 — floor set to 95% in `pyproject.toml`
(`ADR-004`, `GAP-D1-COVERAGE` closed).

## Methodology compliance

See [`docs/methodology-compliance/`](../methodology-compliance/) — this section is a
one-line pointer, not a duplicate of the gap register.
