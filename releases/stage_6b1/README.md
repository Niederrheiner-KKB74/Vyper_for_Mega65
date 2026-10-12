# Stage 6b1 – Testbuild, noch nicht Stable

Issue #47; Engine Stage5d1a Stable + Menü Stage6a2 Stable.

D81 in XEMU einlegen, `LOAD"STAGE6B1",8`, dann `RUN`.
Titel bleibt beim Laden sichtbar; danach erscheint das animierte Originalmenü.
Joystick2/Cursor: Auswahl; links/rechts ändern INITIAL LEVEL zyklisch 001–100.
F1/RETURN/Feuer: Einspielerspiel; F2/F3: rückkehrfähige Platzhalter; X: BASIC.

18 automatische Tests bestanden; kein eigener XEMU-Lauf.
Vollständige Quellen und alle fünf DATs sind enthalten.
Build: `python tools/build_stage6b1.py --kickass /pfad/KickAss.jar` im Repository.
Dokumentation: `docs/stage6b1_menu_integration.md`.

PRG SHA-256: `f7d8a099bd4ce8690d9d3c6cdde20bc89da584a91eb93f23647d061c925d62cb`

D81 SHA-256: `10c7643d4212cfe543923b236b42486cd7d361d26c6c9d912445e2703297bf4e`
