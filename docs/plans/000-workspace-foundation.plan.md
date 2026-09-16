# Plan: MVP-000 – Workspace Foundation

Reference: [`docs/mvp/000-workspace-foundation.md`](../mvp/000-workspace-foundation.md)

**Status:** Complete — all 5 phases done, MVP closed 2026-09-16 as delivered.

## 0. Investigation

Generated `requirements-lock.txt` for real (`pip-compile --generate-hashes --no-annotate
--no-header --output-file=requirements-lock.txt requirements.in`) rather than assuming the
documented command was correct. It wasn't: without an explicit `--output-file`, `pip-compile`
defaults to `<input-stem>.txt` — i.e. `requirements.txt`, not `requirements-lock.txt` — which
is exactly what `environment.yml`'s `-r requirements-lock.txt` and CI's drift check need.
Confirmed by actually running it: the first attempt silently produced `requirements.txt`,
which then broke the user's own `conda env create -f environment.yml` with `Could not open
requirements file`. The bare command (missing `--output-file`) was present in five places
(`requirements.in`, `environment.yml`, `docs/standards/dependencies.md`,
`docs/development/environment.md`, `_LÄS-MIG-FÖRST.md`) — only `.github/workflows/ci.yml` had
it right. All five have been corrected.

No git remote is configured on this repository (`git remote -v` is empty) — repo-settings
work (Phase 4) needs a real GitHub repository to apply branch protection/Dependabot
settings to; confirm this exists before that phase starts.

## 1. Goal

By the end of this plan: `conda env create -f environment.yml && conda activate angelholm`
works from a clean clone against a committed lock file; the tooling/process decisions
already in force are recorded as ADRs; `docs/methodology-compliance/` holds this project's
real (not template) baseline; the repo-settings checklist is applied or every unapplied item
is a tracked gap; and `_LÄS-MIG-FÖRST.md` is gone.

## 2. Scope boundary

- **In:** `requirements-lock.txt` generation and the doc fix above; ADRs for Ruff,
  `pip-compile`, the coverage-ratchet policy, the no-AI-commit-trailer decision, and
  methodology adoption; `interpretations.md` and `gap-register.md` real entries; the
  `docs/development/repo-settings.md` checklist; deleting `_LÄS-MIG-FÖRST.md`.
- **Out:** anything in `apps/`, `packages/`, or `pyproject.toml`/`pytest.ini`'s
  package-specific placeholders — those belong to MVP-001 and are explicitly out of scope
  for this MVP (see `docs/mvp/000-workspace-foundation.md` "Out of Scope").

## 3. Chapters addressed

- Methodology-adoption baseline generally (`docs/methodology-compliance/README.md`).
- [B5 – Dokumentation av kod](../methodology/b-skriva-kod/dokumentation-av-kod.md) (ADR
  format/discipline).
- [D2 – Kodgranskning](../methodology/d-kvalitetssakring/kodgranskning.md) /
  [E1 – Versionshantering & branchstrategi](../methodology/e-leverans/versionshantering-och-branchstrategi.md)
  (repo-settings checklist).

## 4. TODOs

### Phase 1: Fix and verify the local environment

- [x] Generate `requirements-lock.txt` with the correct `--output-file` flag.
  Result: also found and fixed the missing-flag bug in 5 files (see Investigation).
- [x] User confirms `conda env create -f environment.yml && conda activate angelholm`
  succeeds end-to-end, and `ruff --version` / `pytest --version` / `pre-commit --version`
  all resolve inside it.
- [x] Commit `requirements-lock.txt` together with the doc fixes.
  Result: also caught and fixed a follow-on desync — a merged Dependabot PR bumped `ruff`
  to `0.16.7` in `requirements.in`/lock but left `.pre-commit-config.yaml` and `ci.yml` on
  `0.16.6`; fixed as a separate prerequisite commit before Phase 2 started.

### Phase 2: Record the decisions already in force as ADRs

- [x] ADR: Ruff as the formatter/linter (cites `pyproject.toml`'s own comment asking for
  this). → `docs/architecture/decisions/ADR-002-ruff-as-formatter-and-linter.md`.
- [x] ADR: `pip-compile` as the dependency-lock mechanism — include the `--output-file`
  lesson from Phase 1's investigation as context, so the next person doesn't repeat it.
  → `ADR-003-pip-compile-for-dependency-locking.md`.
- [x] ADR: coverage-ratchet testing-policy shape (repo-wide floor, raised only deliberately;
  see `docs/standards/testing.md` "Coverage"). → `ADR-004-coverage-as-a-ratchet.md`.
- [x] ADR: no AI commit-trailer, AI assistance recorded via PR checkbox instead (already
  decided per `docs/standards/git.md`, just not yet an ADR). → `ADR-005-no-ai-commit-trailer.md`.
- [x] ADR: adopting Projektets utvecklingsmetodik as this project's methodology baseline.
  → `ADR-001-adopt-projektets-utvecklingsmetodik.md`.
- [x] Add all five to `docs/architecture/decisions/README.md`'s index.
  All five marked **Proposed**, not Accepted — per this plan's own Risk note, they need a
  real human review before being considered accepted, not just auto-approval because an AI
  drafted them. Update each Status line to Accepted once reviewed.

### Phase 3: Write the first methodology-compliance baseline

- [x] Add this project's real entries to `docs/methodology-compliance/interpretations.md`
  (one section per ADR above, linking it).
- [x] Add a `docs/methodology-compliance/gap-register.md` row for every currently-known open
  gap. Result: 6 rows — `GAP-D2-BRANCHPROTECT`, `GAP-E2-CICHAIN` (H); `GAP-D2-CODEOWNERS`,
  `GAP-CHAPTERASSESS` (L); `GAP-D1-COVERAGE` (H); `GAP-C1-SASTCONFIRM` (external). Also
  confirmed one thing was *not* a gap while assessing: Dependabot alerts/version-update PRs
  are already live (PR #1 merged for real), so no row was added for that.
  `GAP-E2-CICHAIN` is new since this plan was first written — it wasn't anticipated until
  PR #1's real CI run surfaced it.

### Phase 4: Apply or track repository settings

- [x] Confirm a real GitHub remote/repository exists (prerequisite — see Investigation).
  Result: `gh auth status` confirmed authenticated as `Riniga` with `repo` scope — this
  session *did* have the access assumed unavailable when the plan was first written.
- [x] Apply `docs/development/repo-settings.md`'s branch-protection ruleset and required
  status checks. Result: ruleset `main-protection` (id `23560670`) applied via `gh api`,
  requiring only the 3 currently-passing CI jobs (`Ruff`, `Instruction file scan`, `Secret
  scan`) — not all 6, since `GAP-E2-CICHAIN` means the other 3 fail unconditionally right
  now and would make the ruleset self-blocking.
- [x] Record the applied ruleset id/date in `repo-settings.md`. Result: also discovered and
  fixed an unrelated correctness issue while verifying — an earlier gap-register changelog
  entry (Phase 3) had wrongly claimed Dependabot vulnerability alerts were already working,
  conflating them with the separate, file-driven version-update feature. Corrected.
- [x] Enable Dependabot alerts + automated security fixes. Result: both were actually
  **disabled** (verified via `gh api`, not assumed) — enabled now, confirmed via a second
  `gh api` read after the `PUT`.

### Phase 5: Close out the bootstrap

- [x] Re-check every step in `_LÄS-MIG-FÖRST.md` against the repo's actual state. Result:
  done earlier in this MVP's own timeline, before Phase 2 started — all 5 steps confirmed
  complete at that point.
- [x] Delete `_LÄS-MIG-FÖRST.md`. Result: already done; re-confirmed absent at close.
- [x] Run `ruff format --check .` and `ruff check .`; confirm both green. Result: green,
  re-confirmed at close.
- [x] Fill in `docs/mvp/000-workspace-foundation.md`'s "Outcome at close" against each
  acceptance criterion. Result: closed as **delivered** — see that document for the
  criterion-by-criterion detail, including one reasoned deviation
  (`interpretations.md`'s structure) and one thing found along the way that wasn't
  anticipated when this plan was written (`GAP-E2-CICHAIN`).

**MVP-000 is complete.** All 5 phases done; see `docs/mvp/000-workspace-foundation.md`
"Outcome at close" for the full report.

## 5. Risks / open questions

- Phase 4 needs the repo owner's GitHub access (branch protection, Dependabot) — this
  session can draft the checklist status but likely can't apply it directly; confirm how
  much of Phase 4 the user wants done via `gh` here versus done by hand.
- ADRs record decisions as *accepted* — they should get a real review before being marked
  accepted, not just auto-approved because an AI drafted them.
- The coverage-floor ADR can only describe the *policy shape*; the actual floor number stays
  a placeholder until MVP-001 produces measurable code (already noted in MVP-000's own scope).
