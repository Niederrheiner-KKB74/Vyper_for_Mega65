# Stage 3b-5b – Projektil-Testrelease

[VYPER_STAGE3B5B.d81](VYPER_STAGE3B5B.d81) enthält `STAGE3B5B`, `VYLV.DAT` und `VYGR.DAT`.
Laufwerk 8: `LOAD"STAGE3B5B",8`, dann `RUN`.

Zwei weiße Spielerschüsse (Feuer drücken/loslassen), vier rote Gegnerschüsse.
Nur Gegner Nr. 19 besitzt den isolierten Test-Angriffsstatus. `T` schaltet den Modus.
**Player zum Gegnerschusstest nach unten bewegen:** Ziele oberhalb der Abschussposition
werden nicht beschossen. Zielposition wird beim Schuss gespeichert; kein Homing.
Keine Treffer-/Punkte-/Lebenslogik. Level 1 nutzt den bestätigten Typ 15 mit sechs Frames.
Übrige Mapping-Einträge bleiben unbestätigte Fallbacks. Stabile Stage 3b-4a unverändert.

[Build, Speicher, Routinen und Tests](../../docs/stage3b5b.md) ·
[Offenes XEMU-Abnahmeprotokoll](../../docs/stage3b5b_xemu_test.md).

Build: `python3 tools/build_stage3b5b.py --kickass /pfad/zu/KickAss.jar`.
Noch kein Stable-Tag; tatsächliche Darstellung/Timing und BASIC-Rückkehr unter XEMU prüfen.
