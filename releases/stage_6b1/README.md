# Stage 6b1 – Testbuild, noch nicht Stable

Issue #47; Engine Stage5d1a Stable + Menü Stage6a2 Stable.

D81 in XEMU einlegen, `LOAD"STAGE6B1",8`, dann `RUN`.
Titel bleibt beim Laden sichtbar; danach erscheint das animierte Originalmenü.
Joystick2/Cursor: Auswahl; links/rechts ändern INITIAL LEVEL zyklisch 001–100.
F1/RETURN/Feuer: Einspielerspiel; F2/F3: rückkehrfähige Platzhalter; X: BASIC.

19 automatische Tests bestanden; kein eigener XEMU-Lauf.
Vollständige Quellen und alle fünf DATs sind enthalten.
Build: `python tools/build_stage6b1.py --kickass /pfad/KickAss.jar` im Repository.
Dokumentation: `docs/stage6b1_menu_integration.md`.

PRG SHA-256: `a7e8b999afe9ce32208dcacb697f86f03e8120b3d454a423bbd51673ee938b6b`

D81 SHA-256: `be0712e6602d7a375a64d4550f770ad417c42de3a313d482f75880627a48ff62`

CPU-Taktkorrektur: FAST und VFAST in Titel, Menü und Spiel aktiv;
ursprünglicher BASIC-Takt wird bei X restauriert. Siehe technische Dokumentation.
