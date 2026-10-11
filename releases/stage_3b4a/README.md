# Stage 3b-4a – stabile HUD-Referenz

[VYPER_STAGE3B4A.d81](VYPER_STAGE3B4A.d81) enthält `STAGE3B4A` sowie Original-
`VYLV.DAT` / `VYGR.DAT` als SEQ. Laufwerk 8: `LOAD"STAGE3B4A",8`, dann `RUN`.

Korrigiert nach erstem XEMU-Test: KERNAL-Clear und schwarzer Ladehintergrund;
deckende Leer-Glyphen vor jedem Raster beseitigen Bewegungsreste; HUD benutzt
dünne 5×7-HUD-Schrift in achtspaltigen Zellen. 128-Byte-Zeilen, unverändert acht bewegliche
Slots. Alle 3200 verwendeten Color-RAM-Bytes werden beim Exit restauriert.

Drei Original-Lebenssymbole im 4×2-Feld; Player 2 inaktiv, P/S inaktiv, X Exit.
Scores 0000000, Level 001; Formation 100 / Attack 115 sind Referenz-Testwerte.
54 Hosttests bestanden, Wiederholungsbuild byteidentisch.
Stage 3b-3 bleibt unverändert. Finale Fassung am 10.10.2026 vom Benutzer bestätigt;
stabile Referenz `stage3b4a-stable`.

[Technik/Build/Testcheckliste](../../docs/stage3b4a.md),
[Diagnose und Vergleich](../../docs/stage3b4a_background_font_fix.md),
[Quelle](stage3b4a.asm), [HUD](stage3b4a_hud.asm), [Tabellen](stage3b4a_templates.asm).

Bitte Hintergrund, alle Pixie-Bewegungsspuren, Schriftlesbarkeit, Joystick/Animation,
Lebenssymbole und X/BASIC-Cursor/erneutes LOAD/RUN prüfen.

Build `9b2e767` ist vom Benutzer als voll funktional bestätigt. Diese Folgefassung
ändert die HUD-Texte zu „Hi-Score“, „No P2“, „Form. 100“ und „Att. 115“ und verwendet
eigens erstellte ein Pixel breite Fontstriche in logischen Koordinaten. Die Original-
Spielgrafiken bleiben unverändert; die neue Schrift ist ebenfalls vom Benutzer unter XEMU bestätigt.

Bestätigter Programmstand: `2e672c9c4abc15ee9b46a30b906f35650d43323f`.
Die Sicherung als stabile Referenz verändert PRG, D81, ASM und Prüfsummen nicht.
