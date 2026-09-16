# ADR-004: Enforce test coverage as a ratchet, not a fixed target

**Status:** Proposed
**Date:** 2026-09-16

## Context

`docs/standards/testing.md` already documents a coverage-ratchet policy — a measured
baseline, never a placeholder, raised only in deliberate steps, repo-wide rather than
per-package — as this project's implementation of methodology D1 SKA 2. The policy's own
rationale is illustrated by `docs/methodology-compliance/interpretations.md`'s worked
example: a generic placeholder floor (the methodology's suggested adoption-friendly 50%)
would never function as a ratchet if real, measured coverage turns out well above it —
exactly what happened in the reference project this skeleton was drawn from (measured at
78%, floor set to 70%, not the originally planned 50%).

`pyproject.toml`'s `[tool.coverage.report] fail_under = 50` is explicitly marked in this
repo as a placeholder today, since no application code exists yet to measure a real
baseline from — that only becomes possible once MVP-001 produces real, testable code.

## Decision

Coverage is measured with `pytest-cov` and gated in CI as a **ratchet**: the floor may only
be *raised*, in a deliberate PR that also updates `docs/standards/testing.md`, never
lowered to make a failing build pass, and never chased toward 100%. The floor is
**repo-wide**, not per-package — a simpler, single number to configure and enforce, accepting
that a regression in one package could be masked by a stronger one elsewhere for a while.

This ADR records the **policy shape** only. The real floor number stays a placeholder until
MVP-001 produces measurable code and a real baseline can be measured — setting that number
is explicitly out of this ADR's and MVP-000's scope.

## Consequences

**Benefits:**

- Coverage cannot silently regress once a real floor is set from a measured baseline.
- The repo-wide choice keeps CI configuration simple — one `fail_under` value, not one per
  package to maintain as the workspace grows.
- The policy is proven out by this project's own reference worked example, not just
  theoretical.

**Trade-offs:**

- A repo-wide floor means a strong package can mask a weakening one for a while — accepted
  deliberately; revisit with per-package floors if that trade-off actually bites once
  `packages/` has more than one member.
- Setting the *real* floor is deferred to MVP-001 — this ADR alone doesn't yet give CI any
  teeth on coverage; `fail_under = 50` remains an unenforced placeholder until then.

## Alternatives considered

- **Per-package coverage floors from the start**: rejected for now — more precise, but more
  configuration to maintain for a workspace that doesn't have multiple packages yet.
  Revisit once the repo-wide-vs-per-package trade-off becomes real.
- **A fixed 100% target, or no coverage gate at all**: rejected — 100% chases coverage of
  code that's reasonably left uncovered (CLI `__main__` wiring, defensive branches); no gate
  at all fails methodology D1 SKA 2 outright.
