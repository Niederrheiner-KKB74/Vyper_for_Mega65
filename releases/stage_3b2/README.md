# Stage 3b-2 – Level-1-Grafikintegration, XEMU-Abnahme offen

[VYPER_STAGE3B2.d81](VYPER_STAGE3B2.d81) enthält `STAGE3B2` als PRG und beide
Original-SEQ-Dateien. In Laufwerk 8: `LOAD"STAGE3B2",8`, dann `RUN`.

22 Pfad-Pixies verwenden den bestätigten Originaltyp 12 aus geladenem VYGR;
Joystick-/Orbit-Grafik und Bewegungen bleiben wie in Stage 3b-1. Typ 12 hat einen
Frame. Stabile Referenz `stage3b1-stable` unverändert.

Vollständige Quelle: [stage3b2.asm](stage3b2.asm), maßgebliche Version
[src/engine/stage3b2.asm](../../src/engine/stage3b2.asm).
[Build, Parserformat und XEMU-Checkliste](../../docs/stage3b2.md).
Assembly, D81 und 18 Host-Tests bestanden; neuer XEMU-Erfolg noch nicht bestätigt.
