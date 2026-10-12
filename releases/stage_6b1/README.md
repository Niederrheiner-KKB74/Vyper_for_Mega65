# Stage 6b1 – Testbuild, noch nicht Stable

Issue #47; Engine Stage5d1a Stable + Menü Stage6a2 Stable.

D81 in XEMU einlegen, `LOAD"STAGE6B1",8`, dann `RUN`.
Titel bleibt beim Laden sichtbar; danach erscheint das animierte Originalmenü.
Joystick2/Cursor: Auswahl; links/rechts ändern INITIAL LEVEL zyklisch 001–100.
F1/RETURN/Feuer: Einspielerspiel; F2/F3: rückkehrfähige Platzhalter; X: BASIC.

20 Laufzeittests und drei ROM-Prüfungen bestanden; kein eigener XEMU-Lauf.
Vollständige Quellen und alle fünf DATs sind enthalten.
Build: `python tools/build_stage6b1.py --kickass /pfad/KickAss.jar` im Repository.
Dokumentation: `docs/stage6b1_menu_integration.md`.

PRG SHA-256: `bbcd735b558d98508d234ad51a1d789f36d522b256e821f9e6f8c5b6a8651db5`

D81 SHA-256: `bebd92d0500c1daf669bcdf39119a5b85c957abfe75983616c03c9252608a034`

CPU-Taktkorrektur: FAST und VFAST in Titel, Menü und Spiel aktiv;
ursprünglicher BASIC-Takt wird bei X restauriert. Siehe technische Dokumentation.

ROMC/IRQ-Korrektur: KERNAL-SEQ-Aufrufe laufen wieder in ursprünglicher ROM-Abbildung.
XEMU-Test-ROM V920413; FA29 ist IRQ/BRK-Prolog, CE26 das ursprüngliche ROM-BRK-Ziel.
