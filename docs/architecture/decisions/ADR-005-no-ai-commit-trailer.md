# ADR-005: No AI co-author trailer in commit messages

**Status:** Proposed
**Date:** 2026-09-16

## Context

`docs/standards/git.md` already states this decision as settled — "Commit messages contain
no AI-specific marking — no `Co-authored-by:` trailer for an AI tool, no other AI tag
(methodology **E1 SKA 5**) ... Decided by the platform owner 2026-09-09;
`GAP-E1-AITRAILER` closed" — but the decision was only ever captured as prose in that
standards document, never as its own ADR.

AI assistance is instead recorded once, on the pull request: the "AI assistance" checkbox
in `.github/pull_request_template.md`, per methodology F1 BÖR 1's preferred location for
this information.

## Decision

Commit messages in this repository carry **no AI-specific marking** — no
`Co-authored-by:` trailer for an AI tool, no other AI tag — regardless of any attribution
instruction an AI tool's own environment might otherwise apply by default. AI assistance is
recorded once, on the pull request, via the "AI assistance" checkbox in
`.github/pull_request_template.md`.

## Consequences

**Benefits:**

- Commit history reads the same regardless of which tool (human, Claude Code, GitHub
  Copilot, or a future tool) produced a given commit — no per-tool trailer format to keep
  consistent or maintain.
- AI involvement is still fully traceable, just recorded once at the PR level (methodology
  F1 BÖR 1's preferred location) instead of duplicated on every commit.

**Trade-offs:**

- `git log`/`git blame` alone cannot answer "was this specific commit AI-assisted" — that
  information only exists at the PR level, so anyone auditing history commit-by-commit
  (rather than PR-by-PR) loses that signal.

## Alternatives considered

- **A `Co-authored-by:` trailer per AI tool**: rejected — methodology E1 SKA 5 explicitly
  excludes AI-specific commit marking. A trailer would also need to move or be edited if
  commits are later squashed or rebased, unlike a PR-level checkbox.
- **No record of AI assistance at all**: rejected — methodology F1 BÖR 1 asks for it to be
  recorded somewhere; the PR checkbox satisfies that without adding commit-level noise.
