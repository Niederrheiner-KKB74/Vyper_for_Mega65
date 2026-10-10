# Originales Spielerraumschiff – extrahiert und visuell freigegeben

**Freigabe durch Benutzer:** 2026-10-10. Die Vorschau `player_preview_original_palette.png` wurde als „perfekt“ und als gewünschte Darstellung für das Spiel bestätigt.

## Quelle und Dekodierung

- Quelle: WinUAE/Amiga ChipRAM-Dump `Vyper_Memory_Dump.dat` (524.288 Bytes).
- Frame **8** (nullbasiert; neunte Grafik), unmittelbar nach den acht Explosionsframes.
- Bitplane-Daten: `$2E340-$2E39F` (96 Bytes, 3 Bitplanes).
- Transparenzmaske: `$1BDA8-$1BDC7` (32 Bytes).
- Pixelauflösung: 16 × 16.
- Bitplanes: je 32 Bytes; Zeilenrekonstruktion `(y+3)%16`; Transparenzmaske linear.
- Sichtbare Farbnummer: `(bp0 | bp1<<1 | bp2<<2) + 1`; Transparenz = 0.

## MEGA65-Datenformat

- `player_sprite.bin`: 128 Bytes; linkes Pixel im High-Nibble.
- `player_ncm.bin`: 128 Bytes; linkes Pixel im Low-Nibble (RRB/NCM).
- Beide Dateien werden aus `player_pixels.txt` erzeugt; das Nibble-Swapping ist **notwendig** und darf nicht weggelassen werden.
- 16×16 Pixel = 128 Bytes, zwei 8×8-Zeichenhälften übereinander.

## Freigegebene Farbzuordnung

| Pixelindex | Amiga $0RGB | RGB |
|---:|---|---|
| 0 | $000 | transparent |
| 1 | $344 | #334444 |
| 2 | $FFF | #FFFFFF |
| 3 | $E00 | #EE0000 |
| 4 | $FF0 | #FFFF00 |
| 5 | $899 | #889999 |
| 6 | $344 | #334444 |
| 7 | $566 | #556666 |
| 8 | $ABB | #AABBBB |

Amiga-4-Bit-Kanäle für MEGA65 mit `nibble * 17` in 8-Bit-Kanäle umsetzen. Die vier Amiga-Farbwerte `$899, $FFF, $E00, $344` wurden im Dump als Sprite-Farben identifiziert. `$566` und `$ABB` sind ebenfalls im Dump vorhanden. **Die vollständige Zuordnung der Bitplane-Pixelindizes ist visuell rekonstruiert, nicht als Original-CLUT bewiesen.** Der Benutzer hat die daraus gerenderte Vorschau ausdrücklich freigegeben. Das ist die verbindliche Referenz für die Portierung.

## Integration in eine spätere Stage

1. **Stage 3b-1 nicht ändern**; diese integriert nur den Loader in die stabile Stage-2ja-Engine.
2. Danach Player-Grafik und Spielerpalette in einem eigenen Branch/Stage integrieren.
3. Der Player soll während des gesamten Spiels **dieselben Farben** behalten, unabhängig von der Levelpalette der Gegner.
4. Bestehende Joystick-Steuerung, Animation der 24 Gegner, Schüsse und Programmende dürfen nicht beeinträchtigt werden.
5. Hardware-Sprite- und RRB/NCM-Daten sind getrennt zu halten; keine falsche Nibble-Reihenfolge.
6. Nach dem Build Vorschau und XEMU-Screenshot gegen die freigegebene Referenz vergleichen.

## Reproduzierbarkeit

Die 16×16 Pixelindizes stehen in `assets/player/player_pixels.txt`; `tools/build_player_assets.py` generiert die beiden 128-Byte-Dateien, die RGB-Palettentabellen und optional eine PNG-Vorschau. Das ursprüngliche Amiga-Dumpfile muss nicht im Git-Repository abgelegt werden.
