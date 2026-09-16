# Project-level interpretations

Where [the methodology](../methodology/index.md) deliberately leaves a choice to the
project — a tool, a threshold, a branch model — this file records the choice **once**. The
area files (`a-…` through `f-…`) and the follow-up plans link here instead of repeating the
decision.

Each section names the methodology chapter it answers. A decision here is a *decision*, not
an implementation — the follow-up plan named in each section does the work.

Established by MVP-000 (`docs/mvp/000-workspace-foundation.md`), which adopted the
methodology in full — recorded as
[ADR-001](../architecture/decisions/ADR-001-adopt-projektets-utvecklingsmetodik.md).

---

### 1. Formatter & linter (B2)

**Chapter:** [B2 – Kodstandard & stil](../methodology/b-skriva-kod/kodstandard-och-stil.md).

**Decision:** **Ruff**, pinned exactly (not a range) across `requirements.in`,
`.pre-commit-config.yaml`'s `rev`, and `ci.yml`'s install step — see
[ADR-002](../architecture/decisions/ADR-002-ruff-as-formatter-and-linter.md) for the full
reasoning and the alternatives rejected.

**Follow-up:** None needed — already wired into pre-commit and CI. Watch for version-sync
drift on future bumps (a Dependabot PR already demonstrated this gap once; see ADR-002's
Context).

---

### 2. Dependency locking (C2)

**Chapter:** [C2 – Beroendehantering, paketkällor & signering](../methodology/c-sakerhet/beroendehantering-paketkallor-och-signering.md)
(SKA 3).

**Decision:** **`pip-compile`** (from `pip-tools`), always with `--generate-hashes
--no-annotate --no-header --output-file=requirements-lock.txt` explicit — see
[ADR-003](../architecture/decisions/ADR-003-pip-compile-for-dependency-locking.md), which
also records the missing-`--output-file` gotcha this project hit for real while generating
its first lock file.

**Follow-up:** None needed for the mechanism itself. SBOM export (C2 SKA 1) and the
licence-scan allow-list (C2 SKA 4) remain to be exercised against a real dependency (SUMO,
via MVP-001) — see that plan's Investigation section for the licence question already
identified.

---

### 3. Test-strategy shape (D1)

**Chapter:** [D1 – Testning](../methodology/d-kvalitetssakring/testning.md) (SKA 1–2, BÖR 1).

**Decision:** **Coverage enforced as a ratchet, repo-wide, not per-package** — see
[ADR-004](../architecture/decisions/ADR-004-coverage-as-a-ratchet.md). Real baseline
measured 2026-09-16 (`pytest -q --cov`, `apps/simulator` after MVP-001's Phases 1–4):
**99.13%** — only uncovered line is `run.py`'s `__main__` guard, reasonably left uncovered
per `docs/standards/coding.md`. Floor set to **95%**, just below the measured value, not at
99 itself — leaves room for normal, non-regressive coverage fluctuation as more code is
added, while still catching a real drop. `GAP-D1-COVERAGE` closed.

**Follow-up:** None needed for now — raise the floor in a future, deliberate PR as the
codebase matures, per the ratchet policy (never lowered to make a failing build pass).

---

### 4. AI commit attribution (E1)

**Chapter:** [E1 – Versionshantering & branchstrategi](../methodology/e-leverans/versionshantering-och-branchstrategi.md)
(SKA 5).

**Decision:** **No AI-specific marking in commit messages** (no `Co-authored-by:` trailer
for an AI tool); AI assistance is recorded once, on the pull request, via
`.github/pull_request_template.md`'s checkbox — see
[ADR-005](../architecture/decisions/ADR-005-no-ai-commit-trailer.md).

**Follow-up:** None needed — already the stated rule in `docs/standards/git.md` and applied
in practice throughout this project's commit history.
