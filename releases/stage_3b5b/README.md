# Stage 3b-5b – stabile Projektil-Referenz

[VYPER_STAGE3B5B.d81](VYPER_STAGE3B5B.d81) enthält `STAGE3B5B`, `VYLV.DAT` und `VYGR.DAT`.
Laufwerk 8: `LOAD"STAGE3B5B",8`, dann `RUN`.

Zwei weiße Spielerschüsse (Feuer drücken/loslassen), vier rote Gegnerschüsse.
Nur Gegner Nr. 19 besitzt den isolierten Test-Angriffsstatus. `T` schaltet den Modus.
**Player zum Gegnerschusstest nach unten bewegen:** Ziele oberhalb der Abschussposition
werden nicht beschossen. Zielposition wird beim Schuss gespeichert; kein Homing.
Keine Treffer-/Punkte-/Lebenslogik. Level 1 nutzt den bestätigten Typ 15 mit sechs Frames.
Übrige Mapping-Einträge bleiben unbestätigte Fallbacks. Stabile Stage 3b-4a unverändert.

[Build, Speicher, Routinen und Tests](../../docs/stage3b5b.md) ·
[Bestätigte XEMU-Abnahme](../../docs/stage3b5b_xemu_test.md).

Build: `python3 tools/build_stage3b5b.py --kickass /pfad/zu/KickAss.jar`.
Am 10.10.2026 vom Benutzer als vollständig funktional bestätigt und für Stable freigegeben.
Stabile Referenz: `stage3b5b-stable`; bestätigter Programmstand `6f378c2faa136a6d25b5d8d32f51e3ba79f02518`.
Quellen, PRG, D81, Mapping und Prüfsummen bleiben bei der Abnahmedokumentation unverändert.
