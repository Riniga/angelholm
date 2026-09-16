# ADR-003: Use pip-compile for dependency locking

**Status:** Proposed
**Date:** 2026-09-16

## Context

`docs/standards/dependencies.md` already documents a `pip-compile`-based lockfile workflow
(`requirements.in` → `requirements-lock.txt`, hash-pinned, CI drift-checked) as this
project's implementation of methodology C2 SKA 3 — but the tool choice itself (`pip-compile`
vs. `conda-lock`, `uv`, or another lockfile tool) was never recorded as a decision.
`requirements.in`'s own comment names this as a worked-example ADR candidate.

Generating the first real `requirements-lock.txt` (during MVP-000) surfaced a concrete,
worth-recording gotcha: `pip-compile` defaults its output to `<input-stem>.txt` when
`--output-file` is omitted. The first attempt, following the command as originally
documented, silently produced `requirements.txt` instead of `requirements-lock.txt`, which
then broke `conda env create -f environment.yml` with `Could not open requirements file`.
The bare command (missing `--output-file`) was present in five places across this repo
before being fixed; only `ci.yml` had it right from the start.

## Decision

Use **`pip-compile`** (from the `pip-tools` package) to generate a hash-pinned
`requirements-lock.txt` from `requirements.in`'s version ranges, always with
`--generate-hashes --no-annotate --no-header --output-file=requirements-lock.txt` explicit —
never relying on the default output filename.

## Consequences

**Benefits:**

- The most widely used, lowest-friction lockfile tool for a Conda+pip hybrid
  `environment.yml` setup — `environment.yml`'s own `pip:` block is just `-r
  requirements-lock.txt`, matching `pip-compile`'s natural output.
- Hash pinning gives real supply-chain integrity (methodology C2 SKA 3).
- CI's drift check (`ci.yml`'s `dependencies` job) keeps the lock file from silently going
  stale relative to `requirements.in`.

**Trade-offs:**

- `pip-compile` itself is deliberately bootstrap-only tooling, not part of
  `requirements.in` — every fresh clone needs a one-time `pip install pip-tools` before the
  very first compile. This is a real chicken-and-egg step (`conda env create` needs the lock
  file to exist; producing the lock file needs a Python environment `conda env create`
  hasn't built yet), documented in `docs/standards/dependencies.md`, not something `conda
  env create` alone can bootstrap.
- Local Windows compiles can resolve different platform-conditional transitive packages than
  CI's Linux compile (documented in `requirements.in`'s own comment) — CI's drift check, not
  local output, is authoritative on conflict.
- The missing-`--output-file` gotcha (Context) shows the command is easy to get subtly wrong
  even when documented; every doc referencing it now states the flag explicitly.

## Alternatives considered

- **`conda-lock`**: rejected — this project's dependency surface outside genuinely
  Conda-native packages (`python`, `pytest`) is pip-first; `pip-compile` matches the
  existing `environment.yml` `pip:`-block pattern without adding a second lockfile format.
- **`uv`**: rejected for now — a faster, newer alternative, but `pip-compile` is the more
  established, widely documented choice for this Conda-hybrid pattern. Revisit via an ADR
  that supersedes this one if `uv`'s ecosystem support for this pattern matures further.
- **Poetry / PDM (full dependency-management tools)**: rejected — this repo root
  deliberately has no `[project]`/`[build-system]` table (nothing installs the repo root
  itself); a full dependency manager would fight that structure rather than fit it.
