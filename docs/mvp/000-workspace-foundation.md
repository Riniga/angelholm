# MVP-000 – Workspace Foundation

## Purpose

This repository was bootstrapped from a generic, organisation-wide reference skeleton (the
"grundplåt" — see `_LÄS-MIG-FÖRST.md`) that ships a working development process, quality
gates, and AI-collaboration structure before any project-specific code exists. Several
tooling and process decisions are already in force in practice (Ruff as formatter/linter,
`pip-compile` as the lockfile mechanism, a coverage-ratchet testing policy, no AI
commit-trailer), but none of them are recorded anywhere a future contributor — human or AI
— can find and trust them, and the environment they describe has never actually been
verified to work.

This MVP closes that gap: it turns the inherited skeleton into a working, internally
consistent, policy-compliant starting point, so that MVP-001 (R1, "First Traffic
Simulation" — see `docs/roadmap.md`) can start on solid ground instead of inheriting
unresolved tooling and unrecorded decisions.

## Goals

- A local development environment that can actually be created and verified end-to-end,
  not just described.
- The tooling/process decisions already in force are recorded as ADRs instead of living
  only in code comments and standards-doc prose.
- A first, honest methodology-compliance baseline exists, so this project's real standing
  against [Projektets utvecklingsmetodik](../methodology/index.md) is visible rather than
  an empty template.
- The GitHub repository settings the methodology requires (branch protection, required
  status checks, Dependabot alerts) are either applied or explicitly tracked as an open,
  owned gap — not silently assumed.
- The skeleton's own bootstrap instructions (`_LÄS-MIG-FÖRST.md`) are fully carried out and
  the file removed, per its own instruction to delete itself once acted on.

## Context

Established while validating the skeleton against this project (see
`docs/architecture/overview.md` "Open Questions and Areas Not Yet Implemented" →
"Workspace bootstrap"):

- No `requirements-lock.txt` has ever been generated — `conda env create -f environment.yml`
  has not been verified to actually resolve in this repository.
- `docs/architecture/decisions/` is empty (just the index and `ADR-TEMPLATE.md`), despite
  `pyproject.toml` and `docs/standards/dependencies.md` explicitly calling out decisions
  that should be recorded as ADRs (the Ruff choice, the lockfile-tool choice).
- `docs/methodology-compliance/gap-register.md` has no rows and `interpretations.md` has
  only its own worked example — this project has not yet assessed its own standing against
  the methodology it claims to follow.
- `docs/development/repo-settings.md`'s owner checklist (branch protection ruleset,
  required status checks, Dependabot alerts) is explicitly marked "not yet applied"; its
  real GitHub-side status is unknown from the repository alone.
- `_LÄS-MIG-FÖRST.md` is still present; its step 5 (`pip-compile` before `conda env
  create`) has not been run.

## Scope

- Generate a real `requirements-lock.txt` (`pip-compile --generate-hashes --no-annotate
  --no-header requirements.in`) and verify locally that `conda env create -f
  environment.yml`, `conda activate angelholm`, `ruff format --check .`, and `ruff check .`
  all succeed against it.
- Write ADRs (Nygard format, `docs/architecture/decisions/`) for the decisions already in
  force: Ruff as formatter/linter, `pip-compile` as the dependency-lock mechanism, the
  coverage-ratchet testing-policy shape, the no-AI-commit-trailer decision, and adopting
  Projektets utvecklingsmetodik itself — each indexed in `decisions/README.md`.
- Populate `docs/methodology-compliance/interpretations.md` with this project's own entries
  for each decision above (alongside, not replacing, its existing worked example).
- Add a `docs/methodology-compliance/gap-register.md` row for every currently-known open
  gap (repo settings not applied, no `CODEOWNERS`, coverage floor unmeasured until real code
  exists, SAST tool position unconfirmed, etc.), each with severity, owner, and status per
  the register's own legend.
- Apply the `docs/development/repo-settings.md` checklist on the real GitHub repository, or
  — where that isn't this MVP's to apply (e.g. it needs the repo owner's GitHub access) —
  make sure every unapplied item has a matching gap-register row instead of silently
  passing.
- Delete `_LÄS-MIG-FÖRST.md` once every step it describes has actually been carried out.

## Out of Scope

- Any application code, `apps/`, or `packages/` — that begins with MVP-001 under R1.
- Resolving the placeholders in `pyproject.toml` (`<your_package_1>`), `pytest.ini`
  (`testpaths`), `.env.example`, or the per-package parts of `.github/workflows/ci.yml` —
  each names something that doesn't exist yet; resolving them now would mean inventing a
  fictional package.
- A measured coverage floor — there is no code to measure yet; `pyproject.toml`'s
  `fail_under` stays a documented placeholder until MVP-001 exists.
- Any decision about the OSM/SUMO integration approach or domain model — that belongs to
  R1/MVP-001, not this foundation work.
- Writing the implementation plan for this MVP — that is a separate step
  (`docs/plans/000-workspace-foundation.plan.md`), not part of this document.

## Acceptance Criteria

- `conda env create -f environment.yml && conda activate angelholm` succeeds from a clean
  clone, against a committed `requirements-lock.txt`.
- `ruff format --check .` and `ruff check .` both pass locally with no errors.
- `docs/architecture/decisions/` contains at least one ADR each for: the Ruff
  formatter/linter choice, the `pip-compile` lockfile mechanism, the coverage-ratchet
  testing-policy shape, the no-AI-commit-trailer decision, and adopting Projektets
  utvecklingsmetodik — all listed in `decisions/README.md`'s index.
- `docs/methodology-compliance/interpretations.md` has real, dated entries for each
  decision above, not just the pre-existing worked example.
- `docs/methodology-compliance/gap-register.md` has a row for every currently-known open
  gap, each with a severity, an owner, and a status.
- `docs/development/repo-settings.md`'s checklist is either checked off with the applied
  ruleset ID and date recorded, or every unapplied item has a matching, owned gap-register
  row.
- `_LÄS-MIG-FÖRST.md` no longer exists in the repository.

## Outcome at close (2026-09-16)

Closed as **delivered**, verified for real against each criterion, not just asserted:

- **Environment**: `conda env create -f environment.yml && conda activate angelholm`
  confirmed working (by the repo owner directly, and independently in this session — `ruff
  0.16.7`, `pytest 9.1.1`, `pre-commit 4.6.2` all resolve inside it). `requirements-lock.txt`
  is committed and re-verified against `requirements.in` at close: no real drift. One
  non-obvious finding along the way — a naive `diff` twice reported drift that wasn't real;
  `pip-compile`'s `--hash=` line *ordering* within a package isn't fully deterministic
  run-to-run, even though the underlying hash *set* is identical. Worth remembering before
  trusting a future drift-check diff at face value.
- **Ruff**: `ruff format --check .` and `ruff check .` both pass, re-confirmed at close.
- **ADRs**: **Met.** Five ADRs exist (`ADR-001` through `ADR-005`), covering exactly the
  five named decisions, all listed in `decisions/README.md`'s index. All five are marked
  **Proposed**, not Accepted — deliberate, per this plan's own risk note: an AI-drafted ADR
  needs real human review before it's accepted, not automatic sign-off.
- **`interpretations.md`**: **Met, with a reasoned deviation from a literal reading.** Four
  of the five decisions got their own dated, ADR-linked section (formatter/linter,
  dependency locking, test-strategy shape, AI commit attribution). The fifth — adopting
  Projektets utvecklingsmetodik itself — is referenced from the file's intro paragraph
  (linking `ADR-001`) rather than as its own numbered section, because
  `interpretations.md`'s own stated purpose is specifically for choices *the methodology
  leaves to the project*; adopting the methodology at all isn't that kind of choice, it's
  the umbrella decision everything else sits under. A deliberate structural call, not an
  oversight.
- **`gap-register.md`**: **Met.** Six real rows, each with severity/owner/status:
  `GAP-D2-BRANCHPROTECT` (H, closed during Phase 4), `GAP-E2-CICHAIN` (H, open),
  `GAP-D1-COVERAGE` (H, open, deferred to MVP-001 by design), `GAP-D2-CODEOWNERS` (L, not
  applicable yet), `GAP-CHAPTERASSESS` (L, open), `GAP-C1-SASTCONFIRM` (external —
  tracking).
- **`repo-settings.md`**: **Met.** Ruleset `main-protection` (id `23560670`) applied
  2026-09-16, recorded with date and id. Unapplied items each have a matching reference:
  `EX-001` (required-approval-count `0`), `GAP-D2-CODEOWNERS` (no `CODEOWNERS` yet),
  `GAP-E2-CICHAIN` (3 of 6 required status checks deferred). Also enabled Dependabot
  vulnerability alerts and automated security fixes — both were actually disabled, a real
  gap caught only by checking the live setting via `gh api` rather than assuming.
- **`_LÄS-MIG-FÖRST.md`**: **Met.** Confirmed absent, re-checked at close.

**Not anticipated when this MVP was written, found along the way:** `GAP-E2-CICHAIN` (3 of
`ci.yml`'s 6 jobs fail unconditionally on leftover `<placeholder>` text) — discovered from
PR #1's real CI run, not from reading the workflow file. It directly shaped how branch
protection was applied (only the 3 working jobs required, not all 6) and is now MVP-001's
problem to close.
