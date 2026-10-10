# Stage 3b-3 – Amiga-Spielerraumschiff, XEMU-Abnahme offen

[VYPER_STAGE3B3.d81](VYPER_STAGE3B3.d81) enthält `STAGE3B3` und beide Original-SEQ-
Dateien. In Laufwerk 8: `LOAD"STAGE3B3",8`, dann `RUN`.

Joystick-Spieler mit freigegebener 16×16-NCM-Grafik und eigener Palette Bank 3.
22 Gegner, Orbit, Bewegung, Steuerung, Loader und BASIC-Exit wie in Stage 3b-2.
Stage 3b-2 und `stage3b2-stable` unverändert.

[Quelle](stage3b3.asm), [Build und Tests](../../docs/stage3b3.md),
[freigegebene Grafik](../../docs/player_graphics.md),
[Vorschau](../../assets/player/player_preview_original_palette.png).

Assembly, sieben neue Hosttests und reproduzierbarer D81-Build bestanden.
Gesamte Stage-3b-Regression: 42 Tests bestanden mit dem bereitgestellten ROM.
Bitte Darstellung/Farben, Joystick, Grafikreste, Animation und `X`/Neustart unter
XEMU prüfen. Kein Stable-Tag vor Benutzerbestätigung.
