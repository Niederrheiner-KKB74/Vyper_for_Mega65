# Originales Vyper-Spielerraumschiff

Vom Benutzer am 2026-10-10 visuell freigegebene 16×16-Grafik.

- `player_pixels.txt`: extrahierte 16×16-Pixelindizes; **Quellmaterial für den Build**
- `player_palette.txt`: visuell freigegebene Farbzuordnung
- `tools/build_player_assets.py`: erzeugt `player_sprite.bin`, `player_ncm.bin` und `player_palette_[rgb].bin`

Details: `docs/player_graphics.md`.

Die Pixelindex-zu-Farbe-Zuordnung ist durch Vergleich mit dem Amiga-Screenshot rekonstruiert und vom Benutzer visuell bestätigt. Die Gegnerpalette darf die Spielerpalette nicht überschreiben.
