# Stage 3b-3 – Amiga-Spielerraumschiff, stabile Referenz

[VYPER_STAGE3B3.d81](VYPER_STAGE3B3.d81) enthält `STAGE3B3` und beide Original-SEQ-
Dateien. In Laufwerk 8: `LOAD"STAGE3B3",8`, dann `RUN`.

Joystick-Spieler mit freigegebener 16×16-NCM-Grafik und eigener Palette Bank 2.
22 Gegner, Orbit, Bewegung, Steuerung, Loader und BASIC-Exit wie in Stage 3b-2.
Stage 3b-2 und `stage3b2-stable` unverändert.

[Quelle](stage3b3.asm), [Build und Tests](../../docs/stage3b3.md),
[freigegebene Grafik](../../docs/player_graphics.md),
[Vorschau](../../assets/player/player_preview_original_palette.png).

Assembly, acht Stage-3b-3-Hosttests und reproduzierbarer D81-Build bestanden.
Gesamte Stage-3b-Regression: 43 Tests bestanden mit dem bereitgestellten ROM.
Am 10.10.2026 vom Benutzer unter XEMU als stabil bestätigt: `stage3b3-stable`.
Der bestätigte Programmstand `be74770` bleibt unverändert; die Abnahme stammt
vom Benutzer.

Exit-Palettenkorrektur: Die alte Bank 3 überschrieb zugleich die BASIC-ROM-
Palette. Die neue Fassung ändert nur ein PRG-Byte (`$3704`: `$DB` → `$9A`).
Für den Test bitte XEMU frisch booten, um vorherige Palettenänderungen zu verwerfen.
[Diagnose und Vergleich](../../docs/stage3b3_exit_palette_fix.md).
