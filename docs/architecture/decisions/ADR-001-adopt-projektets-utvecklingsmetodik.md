# ADR-001: Adopt Projektets utvecklingsmetodik as this project's methodology baseline

**Status:** Proposed
**Date:** 2026-09-16

## Context

This repository was bootstrapped from a generic, organisation-wide reference skeleton (the
"grundplåt") that assumes adoption of **Projektets utvecklingsmetodik**
(`docs/methodology/`, v1.0, 2026-09-07) — an organisation-wide engineering methodology
originally driven by NIS2, covering six areas (A–F): developer environment, writing code,
security, quality assurance, delivery, and AI collaboration (see
`docs/methodology/index.md`).

The skeleton's `AGENTS.md`, `docs/standards/*.md`, `.github/pull_request_template.md`, and
CI (`ci.yml`'s SAST/secret-scan/licence-scan jobs) already assume and enforce pieces of this
methodology — but no decision was ever recorded that *this* project actually adopted it, or
when. `docs/methodology-compliance/README.md` explicitly asks for that adoption decision to
be recorded as an ADR, with the establishing MVP linked.

## Decision

Adopt Projektets utvecklingsmetodik in full — all six areas (A–F) — as this project's
baseline engineering methodology, rather than a partial or ad-hoc subset. Where a chapter is
marked **utkast** (draft) pending a named expert's final sign-off on one specific point (5 of
21 chapters, per the methodology's own "Nuläge" section), treat it as usable now, per the
methodology's own framing, and track any project-specific implication in
`docs/methodology-compliance/`.

This adoption is established by MVP-000 (`docs/mvp/000-workspace-foundation.md`).

## Consequences

**Benefits:**

- A single source of truth for engineering practice, shared across "Projektet" projects
  rather than invented per-repository.
- NIS2-driven security controls (SAST, secret scanning, dependency governance) are already
  wired into this repo's CI instead of needing to be designed from scratch.
- Project-specific deviations get a documented, auditable trail
  (`gap-register.md`/`interpretations.md`/`exceptions.md`) instead of silent drift from an
  unstated standard.

**Trade-offs:**

- Real overhead for a project that is, at this stage, single-maintainer and pre-application-code —
  several requirements (non-author review, branch protection) cannot yet be fully met and
  must be tracked as gaps/exceptions rather than closed immediately.
- The methodology's five "utkast" chapters mean some guidance may still shift before final
  expert sign-off; this project inherits that uncertainty rather than waiting it out.

## Alternatives considered

- **No formal methodology, ad-hoc practices**: rejected — the skeleton's CI, standards docs,
  and AI action rules already assume and enforce methodology requirements; not adopting it
  formally would leave those controls undocumented and unexplained.
- **A narrower, project-specific subset of the methodology**: rejected for now — nothing in
  this project's domain (traffic simulation) argues for skipping any of the six areas. A
  narrower adoption can be recorded later via an ADR that supersedes this one, if a specific
  chapter proves genuinely inapplicable.
