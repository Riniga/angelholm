# Current Architecture State

Short reference for the current state of the workspace. For full context see
[`overview.md`](overview.md). Keep this current — it's the quick-scan version; update it
in the same PR as any change to an app's status, test count, or key capabilities.

## Applications

| App | Status | Tests | Key capabilities |
|-----|--------|-------|-------------------|
| `apps/simulator` | In progress (MVP-001) | 1 | Skeleton only so far (Phase 2) — SUMO/OpenStreetMap network build, traffic generation, and a runnable simulation land in Phases 3–5 |

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

`apps/simulator`: 1 test (a package-importable smoke test, Phase 2). Coverage floor
(`pyproject.toml`'s `fail_under = 50`) is still a placeholder — a real baseline is deferred
to Phase 5, once the MVP is functionally complete (measuring it against today's trivial
skeleton would be meaningless).

## Methodology compliance

See [`docs/methodology-compliance/`](../methodology-compliance/) — this section is a
one-line pointer, not a duplicate of the gap register.
