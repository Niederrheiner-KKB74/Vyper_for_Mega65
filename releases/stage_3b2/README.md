# Stage 3b-2 – stabil bestätigt (`stage3b2-stable`)

[VYPER_STAGE3B2.d81](VYPER_STAGE3B2.d81) enthält `STAGE3B2` als PRG und beide
Original-SEQ-Dateien. In Laufwerk 8: `LOAD"STAGE3B2",8`, dann `RUN`.

22 Pfad-Pixies verwenden den bestätigten Originaltyp 12 aus geladenem VYGR;
Joystick-/Orbit-Grafik und Bewegungen bleiben wie in Stage 3b-1. Typ 12 hat einen
Frame. Stabile Referenz `stage3b1-stable` unverändert.

Vollständige Quelle: [stage3b2.asm](stage3b2.asm), maßgebliche Version
[src/engine/stage3b2.asm](../../src/engine/stage3b2.asm).
[Build, Parserformat und XEMU-Checkliste](../../docs/stage3b2.md).
Die alte Objektkopie überschrieb Cursordaten des KERNALs. Objekte und Diagnostik
liegen jetzt bei `$1600/$1900`; nur 53 Adressbytes im PRG ändern sich.
[Ursache, Vergleich und Tests](../../docs/stage3b2_exit_investigation.md).
Assembly, D81 und 23 Tests mit dem bereitgestellten ROM V920395 bestanden.
Der Benutzer bestätigt am 10.10.2026 den fehlerfreien Exit unter XEMU und nimmt
Stage 3b-2 ab. Stabile Referenz: `stage3b2-stable`. Die bestätigten PRG-/D81-/ASM-
Artefakte bleiben unverändert.
