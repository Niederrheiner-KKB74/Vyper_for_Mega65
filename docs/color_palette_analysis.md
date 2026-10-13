# Original-Amiga-Palettenanalyse: Color + Level

Stand 11.10.2026. **Direkt aus der hochgeladenen Originaldatei `VYPER(1).ADF` extrahiert**, nicht aus geschätzten Screenshots. Stage 5b Stable unverändert.

## Dateistruktur

- `Wave/Color`: **362 Bytes** (OFS-Dateiheader Diskblock 983, erster Datenblock 984). Big Endian `uint16` bei Offset 0: `$0064 = 100`; anschließend **20 Paletten × 9 Farbwerte × 2 Bytes = 360 Bytes**. Alle 180 Farbwerte liegen zwischen `$000` und `$FFF`, passend zum Amiga-**RGB4**-Format `$RGB`. Header `100` könnte die Anzahl Levels angeben; seine Semantik ist noch nicht durch Codezugriff bewiesen.
- `Wave/Level`: **11.400 Bytes**, exakt **100 Records × 114 Bytes** (OFS-Headerblock 979). Alle WORDs Big Endian.
- **Palettenindex-Kandidat `Level-Record + $4C`**: 100 WORDs mit Werten **0..19**, alle 20 möglichen Indizes werden benutzt. Kein Wert außerhalb der 20 Paletten. Die eindeutige Übereinstimmung mit der Anzahl der Paletten und dem bislang ungeklärten Feld macht diese Zuordnung **sehr stark gestützt**, aber ein Original-Codezugriff oder direkter Amiga-Farbvergleich steht noch aus.
- Erwartete Position der neun RGB4-Wörter von Level `n`:
  `palette_id = be16(Level + 114*(n-1) + 0x4C)`;
  `color_offset = 2 + 18*palette_id`.
- **Die ersten vier Palette-Wörter** haben auffällige Muster: Eintrag 0 und 3 stets `$000`, Eintrag 2 stets `$F00`. Ob die neun Wörter direkt VIC-IV-Farbslots 0..8 entsprechen oder Originalregister-/Objektfarben auf besondere Weise adressieren, ist noch zu prüfen. Spielerpalette und HUD dürfen nicht einfach überschrieben werden.

## Vollständige Zuordnung

Die Level→Paletten-Indices stehen maschinenlesbar in `assets/original_color_level_mapping.csv`, die 20 Paletten mit neun RGB4-Wörtern in `assets/original_color_palettes_rgb4.csv`.

## RGB4-Beispiele

- Palette 0: `000 C74 F00 000 843 522 632 953 765`
- Palette 1: `000 4F0 F00 000 280 140 260 3B0 686`
- Palette 3 (Level 1): `000 FFF F00 000 899 344 566 ABB 888`
- Palette 13 (Level 4): `000 5A9 F00 000 455 133 244 577 345`

Die 4-bit-Kanäle `R,G,B` können für die MEGA65-8-bit-DAC-Darstellung zunächst mit `channel8 = channel4*17` expandiert werden; die VIC-IV-Palettenregister-Reihenfolge und die tatsächlichen NCM-Pixelindices müssen separat geprüft werden.

## Verifikation vor Stage 5c

1. Die Original-`Color`- und `Level`-Bytes gegen die hier dokumentierten Werte erneut prüfen.
2. Im Amiga-Code nach der Level-Initialisierung suchen, die das WORD bei `+$4C` als Palettenindex und den Farbblock `Color+2+18*index` verwendet; alternativ in WinUAE einen direkten Farbvergleich durchführen.
3. Prüfen, welche der neun Amiga-Farbwerte für Gegner, Explosionen, Player und Hintergrund gelten und wie sie auf die 16 VIC-IV-NCM-Paletteinträge abgebildet werden. **Nicht** alle neun Werte blind als gemeinsame globale Palette schreiben.
4. Reproduzierbar `VYCL.DAT` erzeugen und beim Levelwechsel (inklusive +/- und 100→1) laden, Playerfarben konstant halten.
5. Testen: Level 1 (Index 3), Level 2 (Index 1), Level 4 (Index 13), Level 38 (Index 0) und weitere.

**Status:** Datenstruktur und 100 Indexwerte sind direkt extrahiert; die tatsächliche Laufzeitnutzung und NCM-Palettenabbildung sind noch offen.
