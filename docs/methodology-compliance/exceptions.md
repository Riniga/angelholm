# Documented exceptions

Recorded deviations from [the methodology](../methodology/index.md). Two kinds:

1. **Undantag-allowed** — permitted by a chapter's own "Undantag" (exception) section and
   recorded here per that section's requirement (the exception and its reason are
   documented in the actual work's own record).
2. **Forced by circumstance** — a requirement the methodology does *not* permit an
   exception from, but which is physically impossible to meet right now (e.g. non-author
   review with a single maintainer). Accepted by whoever owns the methodology adoption as a
   temporary, visible non-compliance with a concrete close condition, **and also kept as an
   open row in the gap register**.

Every entry is time-boxed, has a named responsible person, and a review trigger. An
exception is never a permanent waiver. Related: [`gap-register.md`](gap-register.md).

---

## EX-001 — Required PR approving-review count set to 0

| | |
|---|---|
| **Methodology basis** | Kind 2 — forced by circumstance. [D2 – Kodgranskning](../methodology/d-kvalitetssakring/kodgranskning.md) SKA 2 asks for at least one non-author human approval before merge; nothing in D2 permits an exception from this. |
| **Status** | Active |
| **Granted** | 2026-09-16 |
| **Responsible** | Rickard Nisses-Gagnér (project owner) |
| **Review** | The moment a second reviewer joins the project — raise `required_approving_review_count` to `1` on the `main-protection` ruleset (id `23560670`) and add a `CODEOWNERS` file per `docs/development/repo-settings.md` §3. Not time-boxed to a date, since it's genuinely blocked on team size, not effort — but re-check at every MVP close in the meantime. |
| **Gap-register link** | `GAP-D2-BRANCHPROTECT` |

*(Reasoning: this project currently has a single maintainer. A PR-required, non-author-approval
rule is technically impossible to satisfy alone — the author has no one else to request review
from. Rather than disable "require a pull request before merging" entirely (which would lose
the required-status-checks and no-direct-push guarantees too), the approving-review count is
set to `0` so the PR-based workflow, status checks, and branch protection all still apply; only
the specific "someone else approved this" guarantee is unmet. This is exactly the scenario
`docs/development/repo-settings.md` §1 anticipated and pre-documented before it was ever
applied for real.)*

---

## EX-NNN — *(short title)*

<!-- One entry per exception. Copy this block; increment the id. -->

| | |
|---|---|
| **Methodology basis** | *(chapter + its "Undantag" section, if this is kind 1)* |
| **Status** | Active / Closed |
| **Granted** | *(date)* |
| **Responsible** | *(named person)* |
| **Review** | *(a concrete trigger or date — never "indefinitely")* |
| **Gap-register link** | *(the GAP-ID this is also tracked as, if kind 2)* |

*(Reasoning: why this exception, why now, what closes it.)*
