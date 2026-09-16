# ADR-002: Use Ruff as the formatter and linter

**Status:** Proposed
**Date:** 2026-09-16

## Context

`pyproject.toml`'s `[tool.ruff]` configuration and `docs/standards/coding.md` already fully
assume Ruff as the formatter and linter, with a pre-commit hook
(`.pre-commit-config.yaml`) and a dedicated CI job (`ci.yml`'s `Ruff` job) wired up — but
the decision itself was never recorded. `pyproject.toml`'s own header comment explicitly
asks for this: "Record this (and any deviation) as a project decision in
`docs/methodology-compliance/interpretations.md`, and as an ADR if it's a significant
choice."

The version discipline this requires was tested for real during MVP-000: a Dependabot PR
bumped Ruff from `0.16.6` to `0.16.7` in `requirements.in`/`requirements-lock.txt` but left
`.pre-commit-config.yaml`'s `rev` and `ci.yml`'s install step on the old version — a concrete
demonstration of why "pinned exactly, kept in sync across three files" needs to be an
explicit, recorded rule rather than an implicit assumption.

## Decision

Use **Ruff**, pinned exactly (not a range) and kept in sync across `requirements.in`,
`.pre-commit-config.yaml`'s `rev`, and `ci.yml`'s install step, as the sole formatter and
linter for all Python code in this workspace — replacing the combination of tools (e.g.
Black + isort + Flake8) this would otherwise have needed.

## Consequences

**Benefits:**

- One tool, one config file (`pyproject.toml`'s `[tool.ruff]`), one dependency to pin
  instead of several.
- Fast enough to run on every commit via the pre-commit hook without noticeable friction.
- Actively maintained; matches methodology B2's "accept defaults with minimal deviation"
  guidance with a deliberately small starter rule set (`E4`/`E7`/`E9`, `F`, `W`, `I`, `UP`,
  `B`, `C4`, `C90`).

**Trade-offs:**

- Exact-pin discipline means every version bump is a deliberate, three-file change — proven
  to matter in practice when Dependabot's automatic PR only touched one of the three (see
  Context).
- Ruff's formatter is opinionated and not configurable in places where a team might have
  wanted, e.g., Black-compatible output specifically.

## Alternatives considered

- **Black + isort + Flake8 (+ plugins)**: rejected — three tools/configs to keep in sync
  instead of one, slower on large diffs, and Ruff's rule set already covers the same ground
  (`F` ≈ pyflakes, `I` ≈ isort).
- **No enforced formatter, style-by-convention**: rejected — methodology B2 requires
  formatting to be mechanical and tool-enforced, never a review discussion.
