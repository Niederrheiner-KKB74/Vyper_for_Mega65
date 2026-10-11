# Stage 5d-0 – Voranalyse, Originaldateien fehlen

Issue #33; separater Branch `stage5d-title-test` aus `stage5c-stable`.
Stage5c-Quellen, PRG, D81 und Daten unverändert. **Kein fertiger Build**:
`vyper_palette_candidate_9a50.png` fehlt weiterhin als auslesbare Datei.
`vyper_title_palette.txt` wurde inzwischen als Originalanhang übernommen und
geprüft; siehe Ergänzung unten. Bei der ersten Prüfung fehlten beide Dateien
im Repository, in den lokalen Anhängen und im geprüften GitHub-main-Baum.
Die in Issue #33 genannten352×240/31 Farben/33 Paletteneinträge sind bisher
Auftragsangaben und noch nicht anhand der Dateien geprüft. Keine Ersatzgrafik.

## VIC-IV-Befund

Quelle: MEGA65 Chipset Reference, eingebundener Abschnitt
`appendix-viciv-registers.tex`, Kapitel VIC-IV, insbesondere Full-Colour Text Mode,
Nibble-colour Mode und Hot Register Propagation. Geprüfter User-Guide-Commit:
`cefce48d72e5c98d732c0589461d62b205b5165f`.

- FCM:8×8 Pixel pro Zelle,64 Bytes, jeder Pixel indiziert eine256-Farben-Palette;
  CHR16/SEAM erlaubt8192 Glyphs, Adresse `glyph*64` in den ersten512KiB ChipRAM.
- Vollständige352×240-Grafik benötigt44×30 FCM-Zellen =1320 Glyphs =84480 Bytes,
  plus2640 Bytes Screen-RAM und2640 Bytes Color-RAM bei16-Bit-SEAM-Zellen.
  Keine Farbreduktion, Skalierung oder Beschneidung der Quelldaten erforderlich.
- Ein einzelner NCM-Palettensatz hat16 Farben und reicht für31 Farben nicht aus.
  Eine lokale NCM-Satzzuordnung wäre erst nach Analyse sämtlicher Bildkacheln
  belegbar und ist für diesen isolierten Test nicht der bevorzugte Ansatz.
- Es wird kein angeblicher5-bpp-Bitmapmodus vorausgesetzt. FCM ist ein belegter
 8-bpp-Kachelmodus, keine Behauptung einer linearen8-bpp-Bitmapfunktion.
- H-/V-Geometrie erfordert eigene Konfiguration von Skalierung, Textursprung,
  Zeilen-/Spaltenzahl und Borders, statt die Engine-Konfiguration zu kopieren.
  HOTREG ist während direkter VIC-IV-Konfiguration zu deaktivieren.
  Tatsächliche Registerwerte und XEMU-Darstellung sind noch nicht implementiert
  oder verifiziert. Der Standard-Spielbereich320×200 reicht nicht für352×240.
- Stage5c verwendet24 RRB-Slots, NCM,192-Byte-Zeilenstride,25 Zeilen/Y0..199 und
  getrennte Palettenbereiche. Stage5d-0 soll stattdessen ein isolierter FCM-Screen
  werden; keine Änderung am produktiven Renderer.

Die originale PNG-Indexpalette, doppelte Schwarz-Einträge, RGB4-Zuordnung und
Transparenz müssen nach Erhalt geprüft werden. Gleiche RGB-Werte erlauben allein
keine Rekonstruktion ursprünglich verschiedener Indices. RGB-Daten sind exakt
auf die gelieferten Farben abzugleichen, ohne Nearest-Colour-Heuristik.

## Amiga-Savestate und Copper

Geprüft: archivierter `Vyper_Startscreen.uss`, SHA256
`d836cbf88f0ac35b6ed3776df2add39f699113c1aeb9d02cdfe4651c82793916`.
CHIP-Chunk:360 Payloadbytes, Flags`$00000103`. Registerabbildung gegen
WinUAE `custom.cpp`, `save_custom`/`restore_custom`, abgeglichen. Die kompakte
Serialisierung lässt Audio-Register`$A0–$DF` aus; BPLCON0 folgt acht32-Bit-Pointern.

| Gespeicherter Registerzustand | Wert |
|---|---|
| COP1LC | `$00000420` |
| COP2LC | `$000184AE` |
| DIWSTRT | `$0581` |
| DIWSTOP | `$40C1` |
| DDFSTRT | `$0038` |
| DDFSTOP | `$00D0` |
| DMACON | `$03F0` |
| BPLCON0 am Snapshot-Zeitpunkt | `$0200` |

Die referenzierte COP1-Liste enthält WAIT`$0C01/$FFFE` und COPJMP2`$008A/$0000`.
COP2-Liste ab`$184AE` enthält nach Paletten-/Sprite-MOVEs:

- WAIT`$2B01/$FFFE`, danach DIW/DDF-Konfiguration wie oben und BPLCON0`$0200`.
- Vier Bitplane-Pointer `$27770,$29BB0,$2BFF0,$2E430`.
- WAIT`$2C01/$FFFE`, danach BPLCON0`$4200`.
- WAIT`$F401/$FFFE`, danach BPLCON0`$0200`, Endmarker`$FFFF/$FFFE`.

`$4200` bedeutet unter normalen OCS/ECS-Regeln Lowres, vier Bitplanes; `$0200`
null Bitplanes. Die Liste sieht somit eine Bitplane-Phase von Raster44 bis244
(exklusiv) vor:200 Zeilen. Klassische DIW-H-Stop-Erweiterung ergibt
`($C1+$100)-$81=320` Lowres-Pixel; normales16-Bit-Lowres-Fetch ergibt
`(($D0-$38)/8+1)*16=320` Pixel. Bei `$40BD/$00CC` wären Startposition/Fetchphase
und deren Ausrichtung separat zu beachten, nicht allein ein Bildmaß abzuleiten.

DIW-V-Start5/Stop320 ergeben unter klassischer V-Stop-Erweiterung ein breiteres
315-Zeilen-Fenster, aber kein315-Zeilen-Bild: die Copperliste schaltet Bitplanes
nur in der200-Zeilen-Phase ein. Fenster, Fetch, Bitplane-Aktivität und sichtbare
Bildinhalte sind unterschiedliche Größen. Die Höhe der bereitgestellten PNG darf
nicht aus den isolierten DIW-Werten abgeleitet werden.

Dies sind **gespeicherte Register und statisch analysierte referenzierte Listen**,
kein ausgeführter Copper-Trace und kein WinUAE-Lauf. Eine Zuordnung zu genau dem
angefragten Titelbild ist nicht bewiesen. Die ebenfalls im Dump gefundenen Listen
`$1B5B4,$1C4EC,$2B38A,$35496` sind weiterhin Speicherfunde.352×240 legt gegenüber
klassischem320×200 Overscan nahe, beweist ohne aktive Titelphase weder Overscan
noch die Geometrie des Spiel-Playfields. Die nötige Laufzeitprüfung bleibt offen.

WinUAE-Formatquelle:
https://github.com/tonioni/WinUAE/blob/master/custom.cpp (Lesestand dieser Analyse).

## Fortsetzung nach Erhalt der Originaldateien

PNG/TXT exakt prüfen, reproduzierbare FCM-Konvertierung und verlustfreies VYTI
formatieren; FCM-Daten in nachweislich freies High-RAM außerhalb ROM/DOS legen.
Eigenes PRG soll nur anzeigen und X akzeptieren. Sämtliche veränderten Register,
Palette, Sprites, Screen-/Color-RAM und Cursor sichern und bei Exit restaurieren;
DIRECTORY und erneutes RUN sind Teil der XEMU-Abnahme.

Für spätere Loaderintegration sind KERNAL-IRQ-/Bildschirmzugriffe, Palette,
Loaderpuffer und High-RAM-Dateiziele gegen einen sichtbaren FCM-Titelscreen zu
prüfen. Während CHKIN keine Screen-Ausgaben. Erst nach erfolgreichem isolierten
Test einen separaten Integrationsauftrag umsetzen; Stage5c bleibt unverändert.

## Nachgereichte Originalpalette

`assets/stage5d0/original_sources/vyper_title_palette.txt` ist inzwischen als
Original-Dateianhang übernommen und geprüft:33 fortlaufende Einträge COLOR00..32,
alle RGB-Kanäle exakt17×RGB4,31 unterschiedliche RGB-Farben. Schwarz ist dreifach
an Indices0/6/32 vorhanden. `tools/convert_stage5d0_title.py --check-palette-only`
reproduziert diese Prüfung. Der Konverter ist vorbereitet, aber der PNG-Pfad fehlt
weiterhin. Das im Chat sichtbare Bild ist kein binär verfügbarer Dateianhang;
Bildmaße, PNG-Indices und Pixel-Roundtrip sind deshalb noch nicht geprüft.
Es gibt weiterhin kein fertiges PRG/D81 und keinen XEMU-Test.
