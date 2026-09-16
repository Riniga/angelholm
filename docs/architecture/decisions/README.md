# ADR

Architecture Decision Records.

## Namnstandard

`ADR-001-kort-beslut.md`

Nygard-format: titel, status, kontext, beslut, konsekvenser. En godkänd ADR redigeras
aldrig i efterhand — om beslutet ändras skrivs en ny ADR som ersätter den, med en länk
mellan dem. Se [`docs/standards/documentation.md`](../../standards/documentation.md) and
`ADR-TEMPLATE.md` in this directory for the exact section structure.

## Index

| ADR | Beslut |
|-----|--------|
| [ADR-001](ADR-001-adopt-projektets-utvecklingsmetodik.md) | Adopt Projektets utvecklingsmetodik as this project's methodology baseline |
| [ADR-002](ADR-002-ruff-as-formatter-and-linter.md) | Use Ruff as the formatter and linter |
| [ADR-003](ADR-003-pip-compile-for-dependency-locking.md) | Use pip-compile for dependency locking |
| [ADR-004](ADR-004-coverage-as-a-ratchet.md) | Enforce test coverage as a ratchet, not a fixed target |
| [ADR-005](ADR-005-no-ai-commit-trailer.md) | No AI co-author trailer in commit messages |
