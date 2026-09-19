# Ängelholm Mobility Simulation

A realistic digital simulation of traffic and mobility in Ängelholm, built to understand how
people, vehicles and traffic flows are affected by changes to the city's infrastructure.

The workspace is designed to grow over time by adding independent applications that share
a common architecture, development process, coding standards, and reusable components.

## Vision

Model Ängelholm as a living mobility system where changes to infrastructure can be tested
as controlled, reproducible scenarios. See [`docs/vision.md`](docs/vision.md) for the full
version.

## Workspace Structure

The workspace has its first application; no shared packages exist yet. See
[`docs/architecture/overview.md`](docs/architecture/overview.md) for the current state and
the possible future structure.

```text
docs/
    Architecture, development process, standards, roadmap, MVPs and implementation plans

apps/
    simulator/   Multimodal (car/bicycle/pedestrian) traffic simulation for the outlined central-Ängelholm coverage area, with map context for visual orientation (MVP-001..004)

packages/    (not yet created — see docs/architecture/overview.md "Planned Evolution")
```

> **Note**
>
> The workspace is still growing one MVP at a time. Additional applications, shared
> packages, and documentation will be introduced incrementally as the project evolves.

## Development Process

Every change follows the same lightweight process:

```text
Roadmap
    ↓
MVP
    ↓
Implementation Plan
    ↓
Implementation
    ↓
Test
    ↓
Pull Request
```

See [`docs/development/methodology.md`](docs/development/methodology.md) for the full
process, and [`AGENTS.md`](AGENTS.md) for how AI tools work within it.

## Getting Started

1. Read [`AGENTS.md`](AGENTS.md) — the canonical instruction file for how work happens
   here (human or AI).
2. Follow [`docs/development/setup.md`](docs/development/setup.md) and
   [`environment.md`](docs/development/environment.md) to set up your local environment.
3. Read [`docs/standards/`](docs/standards/) — coding, testing, git, documentation,
   dependencies.
4. If starting a brand-new project from this reference example, work through
   [`docs/claude-prompts/initera-projektet/`](docs/claude-prompts/initera-projektet/) in
   order.

## Required GitHub Actions secrets

None yet. `.github/workflows/ci.yml` does not reference any repository secrets today, and
`dast.yml` (manual-only) uses the built-in `GITHUB_TOKEN`. Update this table when a workflow
needs a real configured secret.

## Documentation

| Area | Location |
|------|----------|
| Architecture | [`docs/architecture/`](docs/architecture/) |
| Development process | [`docs/development/methodology.md`](docs/development/methodology.md) |
| Standards | [`docs/standards/`](docs/standards/) |
| Organisation methodology | [`docs/methodology/`](docs/methodology/) |
| Methodology compliance (internal) | [`docs/methodology-compliance/`](docs/methodology-compliance/) |
| Roadmap | [`docs/roadmap.md`](docs/roadmap.md) |
| MVPs | [`docs/mvp/`](docs/mvp/) |
| Implementation plans | [`docs/plans/`](docs/plans/) |
