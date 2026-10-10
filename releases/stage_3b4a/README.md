# Stage 3b-4a – HUD-Testrelease

[VYPER_STAGE3B4A.d81](VYPER_STAGE3B4A.d81) enthält das PRG `STAGE3B4A` sowie die
Originaldateien `VYLV.DAT` und `VYGR.DAT` als SEQ.

In XEMU Laufwerk 8: `LOAD"STAGE3B4A",8`, anschließend `RUN`.

Basis: `stage3b3-stable`, unverändert erhalten. HUD rechts, Highscore/Score 0000000,
LEVEL 001, drei Original-Lebenssymbole im 4×2-Raster. Player 2 inaktiv; P/S nicht
aktiv, X beendet. FORMATION 100 / ATTACK 115 sind Referenz-Testwerte.

[Build, Speicherbelegung, Vergleich und XEMU-Checkliste](../../docs/stage3b4a.md).
[Hauptquelle](stage3b4a.asm), [HUD](stage3b4a_hud.asm),
[statische Tabellen](stage3b4a_templates.asm), [Buildbericht](build-report.json).

Assembly/D81-Prüfung und Hosttests bestanden. XEMU-Abnahme durch den Benutzer steht
noch aus; kein Stable-Tag für diese Stage. Bitte insbesondere Schrift, 4×2-Lebensfeld,
Pixie-Darstellung, Joystick, HUD-Clearing und BASIC-Exit/Neustart prüfen.
