# Current Architecture State

Short reference for the current state of the workspace. For full context see
[`overview.md`](overview.md). Keep this current — it's the quick-scan version; update it
in the same PR as any change to an app's status, test count, or key capabilities.

## Applications

None yet. No `apps/` directory exists. The first application is expected with MVP-001
(see `docs/roadmap.md`); add a row here once it exists.

| App | Status | Tests | Key capabilities |
|-----|--------|-------|-------------------|

## Shared packages

None yet. No `packages/` directory exists. Code only moves to a shared package once it is
actually reused by ≥ 2 apps (see `AGENTS.md` "Architecture guardrails") — record that
boundary decision as an ADR when it happens.

## Conventions

See `docs/standards/*.md` (coding, testing, git, documentation, dependencies) — nothing
project-specific deviates from them yet.

## Dependencies

No application runtime dependencies exist yet. The development-tooling dependency surface
(Conda `angelholm` environment, Ruff, pytest, pre-commit) is already scaffolded — see
`docs/architecture/overview.md` "Existing Dependencies" for the detail.

## Test counts

No test suite exists yet — no application code to test. `pytest.ini` and the coverage
config in `pyproject.toml` are in place but still reference placeholder paths until a real
package exists.

## Methodology compliance

See [`docs/methodology-compliance/`](../methodology-compliance/) — this section is a
one-line pointer, not a duplicate of the gap register.
