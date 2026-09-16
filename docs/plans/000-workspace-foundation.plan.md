# Plan: MVP-000 – Workspace Foundation

Reference: [`docs/mvp/000-workspace-foundation.md`](../mvp/000-workspace-foundation.md)

**Status:** In progress — the environment/lock-file work (Phase 1) was already carried out
while validating the workspace, ahead of this plan being written down.

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
- [ ] User confirms `conda env create -f environment.yml && conda activate angelholm`
  succeeds end-to-end, and `ruff --version` / `pytest --version` / `pre-commit --version`
  all resolve inside it. *(Needs the repo owner — `conda` isn't on this session's own PATH.)*
- [ ] Commit `requirements-lock.txt` together with the doc fixes.

### Phase 2: Record the decisions already in force as ADRs

- [ ] ADR: Ruff as the formatter/linter (cites `pyproject.toml`'s own comment asking for
  this).
- [ ] ADR: `pip-compile` as the dependency-lock mechanism — include the `--output-file`
  lesson from Phase 1's investigation as context, so the next person doesn't repeat it.
- [ ] ADR: coverage-ratchet testing-policy shape (repo-wide floor, raised only deliberately;
  see `docs/standards/testing.md` "Coverage").
- [ ] ADR: no AI commit-trailer, AI assistance recorded via PR checkbox instead (already
  decided per `docs/standards/git.md`, just not yet an ADR).
- [ ] ADR: adopting Projektets utvecklingsmetodik as this project's methodology baseline.
- [ ] Add all five to `docs/architecture/decisions/README.md`'s index.

### Phase 3: Write the first methodology-compliance baseline

- [ ] Add this project's real entries to `docs/methodology-compliance/interpretations.md`
  (one section per ADR above, linking it).
- [ ] Add a `docs/methodology-compliance/gap-register.md` row for every currently-known open
  gap: repo settings not applied (until Phase 4 closes it), no `CODEOWNERS`, coverage floor
  unmeasured (blocked on MVP-001 producing real code), SAST tool position unconfirmed
  (`ci.yml`'s Semgrep config is a starting point, not a signed-off choice).

### Phase 4: Apply or track repository settings

- [ ] Confirm a real GitHub remote/repository exists (prerequisite — see Investigation).
- [ ] Apply `docs/development/repo-settings.md`'s branch-protection ruleset and required
  status checks, or hand this off explicitly to the repo owner if it needs access this
  session doesn't have.
- [ ] Record the applied ruleset id/date in `repo-settings.md`, or add a gap-register row for
  anything left unapplied.
- [ ] Enable Dependabot alerts + automated security fixes (repository setting, not a file).

### Phase 5: Close out the bootstrap

- [ ] Re-check every step in `_LÄS-MIG-FÖRST.md` against the repo's actual state.
- [ ] Delete `_LÄS-MIG-FÖRST.md`.
- [ ] Run `ruff format --check .` and `ruff check .`; confirm both green.
- [ ] Fill in `docs/mvp/000-workspace-foundation.md`'s "Outcome at close" against each
  acceptance criterion.

## 5. Risks / open questions

- Phase 4 needs the repo owner's GitHub access (branch protection, Dependabot) — this
  session can draft the checklist status but likely can't apply it directly; confirm how
  much of Phase 4 the user wants done via `gh` here versus done by hand.
- ADRs record decisions as *accepted* — they should get a real review before being marked
  accepted, not just auto-approved because an AI drafted them.
- The coverage-floor ADR can only describe the *policy shape*; the actual floor number stays
  a placeholder until MVP-001 produces measurable code (already noted in MVP-000's own scope).
