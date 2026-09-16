Baserat på current-state.md och target-state.md:

1. Säkerställ att följande struktur finns:

docs/
├─ requirements/
├─ plans/
├─ architecture/
│  ├─ current-state.md
│  ├─ target-state.md
│  └─ decisions/
└─ standards/
   ├─ coding-standard.md
   ├─ testing-standard.md
   └─ git-workflow.md

2. Skapa saknade dokument.

3. Dokumentera endast sådant som faktiskt kan härledas från projektet.
Gissa inte.
Hitta inte på arkitektur eller processer.

4. Uppdatera CLAUDE.md i projektroten.

CLAUDE.md skall minst innehålla:

- Hur dokumentation används
- Hur planer skapas
- Hur implementationer genomförs
- Kodstandard
- Testkrav
- Git-workflow
- Regler för arkitekturförändringar
- Krav på att läsa relevant dokumentation innan implementation

5. Visa alla föreslagna ändringar innan de skrivs till disk.

Implementera ingen funktionalitet.
Ändra ingen produktionskod.