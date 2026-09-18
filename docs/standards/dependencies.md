# Dependency Standard

## Purpose

This document defines how this workspace selects, locks, scans, and updates third-party
dependencies.

> **Relation to Projektets utvecklingsmetodik.** This standard is this project's elaboration
> of methodology [C2 – Beroendehantering, paketkällor & signering](../methodology/c-sakerhet/beroendehantering-paketkallor-och-signering.md).
>
> - Dependencies are **locked** to specific, hash-verified versions (`requirements-lock.txt`,
>   `pip-compile`), not loose version ranges (C2 SKA 3).
> - An **SBOM** is exported on every deploy (C2 SKA 1).
> - **Dependabot alerts** are the SCA baseline (C2 SKA 2); **Dependabot version-update PRs**
>   are the update routine (C2 SKA 5).
> - **Licence scanning** runs in CI against the allowlist below (C2 SKA 4).
>
> Record the mechanism decisions you make (lockfile tool, SBOM source, SCA/licence-scan
> tool, and why) in
> [`interpretations.md`](../methodology-compliance/interpretations.md) — this project chose
> `pip-compile` (not `conda-lock`/`uv`), GitHub's native SBOM export, and `pip-licenses`
> (not `dependency-review-action`, which needs GitHub Advanced Security this project's
> private-repo tier didn't have confirmed) as a worked example.

## Lockfile

- `requirements.in` is the source list of direct pip dependencies (version ranges).
  `requirements-lock.txt` is its `pip-compile --generate-hashes --no-annotate --no-header`
  output — the actual, hash-pinned versions installed.
- `environment.yml`'s `pip:` block is just `-r requirements-lock.txt`; do not add packages
  there directly — add them to `requirements.in` and recompile.
- Genuinely Conda-native packages are pinned exactly in `environment.yml` itself (e.g.
  `python=3.13`) — not part of the pip lock. Keep this list as short as possible; most
  things, including `ruff`, belong in the pip lock (`requirements.in`) instead.
- **To update a dependency:** edit its range in `requirements.in`, run
  `pip-compile --generate-hashes --no-annotate --no-header --output-file=requirements-lock.txt requirements.in`, and commit
  both files together. CI fails if `requirements-lock.txt` doesn't match what
  `requirements.in` compiles to (drift check), so the lock can never silently go stale.
- Per-app `pyproject.toml` `dependencies` (version ranges) are unchanged by this — they are
  packaging metadata for each app, not this repo's own install source of truth.
- **Cross-platform gotcha:** compiling locally on Windows can silently include or exclude
  platform-conditional transitive packages that CI's Linux compile resolves differently
  (this project hit it twice — see the example comment in `requirements.in`). If CI's
  drift check fails after a Windows-local edit, trust CI's diff over your own local output.

## SBOM

- Generate from your CI/CD platform's native dependency-graph export if it has one (GitHub
  does, SPDX format) rather than adding a separate SBOM tool — as part of every deploy,
  uploaded as a build artifact.
- Not generated on every PR/CI run — an SBOM describes what got *deployed*, not every
  candidate change.

## SCA (vulnerability scanning)

- Dependabot alerts (GitHub-native) are a reasonable baseline — enabled at the repository
  level (*Settings → Security*), not something this repo's own workflows configure. Check
  whether it's actually available for your repo's plan/tier before assuming it — a private
  repo without GitHub Advanced Security may not have it (this project's didn't; confirmed
  via the API, not assumed).
- Reachability analysis is a criterion for a more capable scanner *if and when one is
  adopted* — not required to start.

## Licence scanning

Checked in CI (`ci.yml`'s `dependencies` job) with `pip-licenses` against the resolved
environment.

**Allowed licences** — the real, measured list this project's CI actually enforces
(`ci.yml`'s `pip-licenses --allow-only`), not a generic template:

```text
Apache Software License
Apache-2.0
Apache Software License; BSD License
Apache Software License; MIT License
Apache-2.0 OR BSD-2-Clause
BSD License
BSD-2-Clause
BSD-3-Clause
BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0
MIT
MIT License
MIT-CMU
MPL-2.0 AND MIT
Mozilla Public License 2.0 (MPL 2.0)
PSF-2.0
Python Software Foundation License
EPL-2.0 OR GPL-2.0-or-later
```

This is not a general-purpose OSS licence policy — it reflects what this project's actual
dependencies use, checked and dated. Copyleft licences (GPL, AGPL, etc.) are decided
deliberately, not blanket-excluded: `EPL-2.0 OR GPL-2.0-or-later` (SUMO —
`eclipse-sumo`/`traci`/`sumolib`/`sumo-data`) was approved by the project owner 2026-09-16
for MVP-001 (`docs/plans/001-first-traffic-simulator.plan.md`). This project only uses
SUMO as an external tool it calls, does not modify or redistribute its source, so the
copyleft terms' practical effect on this project's own code is minimal — noted here as the
reasoning, not a substitute for reading the actual licence text if this project's use ever
changes (e.g. bundling/redistributing SUMO itself). `MIT-CMU` (Pillow, an MIT variant) was
approved by the project owner 2026-09-18 for MVP-003
(`docs/plans/003-map-context-features.plan.md`) — a permissive licence, added deliberately
rather than assumed to already match plain `MIT`'s exact string.

**This workspace's own packages** report `UNKNOWN` to `pip-licenses` (no licence
classifier — they're internal, not published) and should be excluded from the check by
name (`--ignore-packages`), not added to the allowlist.

**Exception process:** a dependency whose licence is not on the allowlist fails CI. To add
one:

1. Confirm with your organisation's legal/procurement function that the licence is
   acceptable for this project's use (an external process, not owned by this repo).
2. Add the licence string to the allowlist above in the same PR that adds the dependency,
   with a one-line comment recording who confirmed it and when.

## Related

- [`docs/standards/coding.md`](coding.md), [`testing.md`](testing.md), [`git.md`](git.md) —
  the other working conventions.
