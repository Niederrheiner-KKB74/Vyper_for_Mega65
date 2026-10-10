# Stage 3b-1 – stabile Referenz `stage3b1-stable`

- [VYPER_STAGE3B1.d81](VYPER_STAGE3B1.d81): PRG + beide Original-SEQ-Dateien.
- [STAGE3B1.PRG](STAGE3B1.PRG): BASIC `RUN` startet den Loader und danach Stage 2ja.
- [stage3b1.asm](stage3b1.asm): vollständige Quellkopie; maßgebliche Quelle ist
  [src/engine/stage3b1.asm](../../src/engine/stage3b1.asm).
- [Build und XEMU-Checkliste](../../docs/stage3b1.md).
- Speicherkarte, Symbole, Build-Bericht und SHA-256-Liste liegen daneben.

Assembly, Engine-Bytevergleich und D81-Prüfung bestanden; 12 Loader-Host-Tests
bestanden. Der Benutzer hat das Release am 2026-10-10 als stabil bestätigt.
PRG, D81, ASM und ihre Prüfsummen bleiben gegenüber dem getesteten Release unverändert.
Der Git-Tag `stage3b1-stable` sichert diesen Stand. Die Bestätigung stammt vom
Benutzer; `NOT RUN` im Build-Bericht bezeichnet weiterhin den automatischen Builder.
