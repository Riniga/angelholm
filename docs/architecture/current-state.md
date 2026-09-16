# Current Architecture State

Short reference for the current state of the workspace. For full context see
[`overview.md`](overview.md). Keep this current — it's the quick-scan version; update it
in the same PR as any change to an app's status, test count, or key capabilities.

## Applications

| App | Status | Tests | Key capabilities |
|-----|--------|-------|-------------------|
| `apps/simulator` | Implemented (MVP-001, closed) | 21 | Fetches a real OpenStreetMap extract, builds a routable SUMO network, generates synthetic traffic, runs headless or via `sumo-gui` — all through the `simulator` console command |

## Shared packages

None yet. No `packages/` directory exists. Code only moves to a shared package once it is
actually reused by ≥ 2 apps (see `AGENTS.md` "Architecture guardrails") — record that
boundary decision as an ADR when it happens.

## Conventions

See `docs/standards/*.md` (coding, testing, git, documentation, dependencies) — nothing
project-specific deviates from them yet.

## Dependencies

`apps/simulator` depends on `eclipse-sumo`/`traci`/`sumolib` (SUMO, exactly pinned —
`ADR-006`). The development-tooling dependency surface (Conda `angelholm` environment,
Ruff, pytest, `pytest-cov`, pre-commit) is scaffolded — see `docs/architecture/overview.md`
"Existing Dependencies" for the detail.

## Test counts

`apps/simulator`: 22 tests, all mocked/deterministic (no live network, no live SUMO
invocation). Coverage: 99.13% measured 2026-09-16 — floor set to 95% in `pyproject.toml`
(`ADR-004`, `GAP-D1-COVERAGE` closed).

## Methodology compliance

See [`docs/methodology-compliance/`](../methodology-compliance/) — this section is a
one-line pointer, not a duplicate of the gap register.
