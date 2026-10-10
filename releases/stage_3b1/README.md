# Stage 3b-1 – Entwicklungsstand, XEMU-Test ausstehend

- [VYPER_STAGE3B1.d81](VYPER_STAGE3B1.d81): PRG + beide Original-SEQ-Dateien.
- [STAGE3B1.PRG](STAGE3B1.PRG): BASIC `RUN` startet den Loader und danach Stage 2ja.
- [stage3b1.asm](stage3b1.asm): vollständige Quellkopie; maßgebliche Quelle ist
  [src/engine/stage3b1.asm](../../src/engine/stage3b1.asm).
- [Build und XEMU-Checkliste](../../docs/stage3b1.md).
- Speicherkarte, Symbole, Build-Bericht und SHA-256-Liste liegen daneben.

Assembly, Engine-Bytevergleich und D81-Prüfung bestanden; 12 Loader-Host-Tests
bestanden. Darstellung, Animation, Joystick und X-Exit müssen unter XEMU noch
mit Stage 2ja verglichen werden. Die Baselines bleiben unverändert.
