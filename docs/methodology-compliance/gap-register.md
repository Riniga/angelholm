# Gap register

Every open gap between this project and [Projektets utvecklingsmetodik](../methodology/index.md)
(or your own organisation's equivalent).

If you keep a "known gaps" table anywhere else (e.g. `docs/architecture/current-state.md`),
point it here instead of duplicating — this file is the one source of truth.

A living document (methodology D3 BÖR 2): rows are added when a gap is found, updated as
follow-up plans progress, and struck through (`~~GAP-ID~~`) when closed.

**Last updated:** 2026-09-16

<!-- A running changelog of what each delivered plan closed, newest first. Keep entries
     terse — what shipped, and which gap IDs it closed/reopened/re-scoped. This is the
     first thing anyone (human or AI) should read to understand what's already done before
     starting new work on this area. -->

- **2026-09-16** — MVP-001 Phase 2: closed `GAP-E2-CICHAIN` — fixed `ci.yml`'s 3 remaining
  `<placeholder>` bugs now that `apps/simulator` exists. Also caught and fixed a real,
  previously-masked bug found by actually running `pytest --cov`: `pytest-cov` was never
  installed despite `testing.md`/`ci.yml` assuming it.
- **2026-09-16** — MVP-000 Phase 4: applied via `gh api` — branch-protection ruleset
  `main-protection` (id `23560670`) on `main`, Dependabot vulnerability alerts, and
  automated security fixes. Closes `GAP-D2-BRANCHPROTECT` (required-approval-count
  deviation tracked as `EX-001`, not a failure). Correction to the entry below: Dependabot
  **vulnerability alerts** and **automated security fixes** were actually disabled before
  today — only `.github/dependabot.yml`'s separate, file-driven **version-update** feature
  (C2 SKA 5) was already working (confirmed by PR #1's real `ruff` bump). Conflating the two
  was this register's own first mistake, caught and fixed the same day.
- **2026-09-16** — MVP-000 Phase 3: first baseline established (this register was empty
  before). All rows below were newly opened.

## Legend

- **Severity**
  - `H` — blocks a core methodology guarantee (unenforced review, no secret-scanning, no
    SAST/SCA, no coverage gate, CI check chain incomplete).
  - `M` — a required control that is scheduled, or an owner/central decision that is
    pending.
  - `L` — a recommendation, a polish item, or a dormant/not-yet-applicable requirement.
- **Owner** — `platform` (a follow-up plan closes it), `owner` (a repo-settings or policy
  action for a named person), or a named organisational function (external dependency).
- **Status** — `open` · `in progress (P<n>)` · `closed` · `external — tracking` ·
  `not applicable yet`.

## Register

### Severity H

| ID | Chapter | Gap | Owner | Follow-up | Status |
|----|---------|-----|-------|-----------|--------|
| ~~`GAP-D2-BRANCHPROTECT`~~ | D2 / F1 | ~~Branch protection on `main` not yet applied~~ — **closed 2026-09-16**: ruleset `main-protection` (id `23560670`) applied, bypass list empty, `current_user_can_bypass: "never"`. Required-approval-count is `0` not `1` — documented as `EX-001`, not a failure of this gap. Only 3 of 6 CI jobs are required status checks (the other 3 wait on `GAP-E2-CICHAIN`, tracked there, not here). | owner | `docs/plans/000-workspace-foundation.plan.md` Phase 4 | closed |
| ~~`GAP-E2-CICHAIN`~~ | E2 | ~~3 of `ci.yml`'s 6 jobs fail on placeholder text~~ — **closed 2026-09-16** (MVP-001 Phase 2): all 3 remaining `<placeholder>`s in `ci.yml` fixed (`Run tests`' install step → `apps/simulator`, `SAST`'s `--error` → `apps`, `Dependencies`' `--ignore-packages` → `simulator`) now that `apps/simulator` exists to give them real values. Verified locally (ruff, pytest-cov) but **not yet confirmed green on a real GitHub Actions run** — add the remaining 3 jobs as required status checks on the `main-protection` ruleset only after seeing them pass for real on a PR, per `docs/development/repo-settings.md`'s own guidance. | platform | `docs/plans/001-first-traffic-simulator.plan.md` Phase 2 | closed |
| `GAP-D1-COVERAGE` | D1 | No functioning coverage gate — `pyproject.toml`'s `fail_under = 50` is an explicit placeholder, not a value derived from a measured baseline, because no application code exists yet to measure. Policy shape already decided (ADR-004); only the number is missing. | platform | `docs/plans/001-first-traffic-simulator.plan.md` (measure once real code exists) | open |

### Severity M

| ID | Chapter | Gap | Owner | Follow-up | Status |
|----|---------|-----|-------|-----------|--------|

### Severity L

| ID | Chapter | Gap | Owner | Follow-up | Status |
|----|---------|-----|-------|-----------|--------|
| `GAP-D2-CODEOWNERS` | D2 | No `CODEOWNERS` file. Required once a second reviewer exists (`docs/development/repo-settings.md` §3); genuinely not applicable with a single maintainer today. | owner | Add `CODEOWNERS` + enable "Require review from Code Owners" when a second reviewer joins | not applicable yet |
| `GAP-CHAPTERASSESS` | (all) | No per-chapter (`a-…` through `f-…`) methodology-compliance assessment exists yet — only this initial `interpretations.md`/`gap-register.md` baseline (MVP-000). | platform | A future MVP, once a full chapter-by-chapter assessment is warranted | open |

### External dependencies (not a platform gap)

| ID | Chapter | Item | Owner to confirm | Status |
|----|---------|------|------------------|--------|
| `GAP-C1-SASTCONFIRM` | C1 | SAST tool choice (Semgrep, `p/security-audit` + `p/owasp-top-ten` rulesets) is an interim, unconfirmed direction (see `.github/pull_request_template.md`'s own note) — C1 itself is marked "utkast" pending the same security-architect review. | Security architect (C1 chapter owner) | external — tracking |

## Follow-up plan index

<!-- One row per plan that closes gaps from this register, in delivery order. -->

| Plan | Closes |
|------|--------|
| `docs/plans/000-workspace-foundation.plan.md` | `GAP-D2-BRANCHPROTECT` (Phase 4) |
| `docs/plans/001-first-traffic-simulator.plan.md` | `GAP-E2-CICHAIN` (Phase 2), `GAP-D1-COVERAGE` |
