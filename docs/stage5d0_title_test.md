# Stage 5d-0 – Originaltitel als eigenständiger FCM-Test

Issue #33, Branch `stage5d-title-test`, Basis `stage5c-stable`
(`2997719d704095afc630830435cb2d2f76b7f696`). **Testbuild, nicht Stable.**
Stage-5c-Quellen, Originaldaten und Release bleiben byteidentisch; das Programm
importiert keine Engine. Es lädt nur `VYTI.DAT`, zeigt den Titel und akzeptiert X.

## Originaldaten und verlustfreie Konvertierung

Die nachgereichte ZIP enthält das originale `vyper_palette_candidate_9a50.png`.
PNG und separat gelieferte Palette liegen in `assets/stage5d0/original_sources/`.
Das PNG hat tatsächlich **352×240 Pixel, Modus RGB, 31 verschiedene RGB-Farben**.
Es hat keine Indexpalette und keine Transparenz. Alle Farben stimmen exakt mit
den 33 benannten RGB4-Einträgen überein; jeder Kanal ist `17 × RGB4`.

Schwarz steht an Index 0, 6 und 32. Bei RGB-Eingabe wählt der Konverter den
kleinsten exakt passenden Index. Das ändert keine Farbe; ursprüngliche
unterschiedliche Schwarz-Indices lassen sich aus RGB allein nicht rekonstruieren.
Es gibt keine Quantisierung, Farbnäherung, Zeilenumkehr, Spiegelung, Beschneidung
oder Neuberechnung der Quellpixel. Rückkonvertierung: **84.480/84.480 RGB-Pixel
identisch**. Kanalwerte wie `$AA` sind auch nach VIC-Paletten-Nibbleswap identisch.

- PNG SHA256: `faa19d74583ec1a35f5ed81f1727f026e03a2de1fce9eb86dd73315ded484eea`
- Palette SHA256: `a108f6346556a15d6a6e2cb712fde23995eda05557f5d85c69cea5857c4e492e`
- VYTI SHA256: `5748d68e9210ffaa96db69d521050add6a43b6468426e429f3106ac05529c432`

## Wahl des VIC-IV-Modus

Die [Chipset Reference](https://github.com/MEGA65/mega65-user-guide/blob/cefce48d72e5c98d732c0589461d62b205b5165f/appendix-viciv-registers.tex)
belegt FCM mit 8×8-Pixel-Zellen und 64 Bytes pro Zelle; CHR16 erlaubt 8192 Glyphs.
Ein NCM-Satz bietet nur 16 Farben. Der produktive Stage-5c-NCM-/RRB-Screen hat
25 Zeilen und reicht für diese Grafik nicht; er wird nicht verändert.

Der Test verwendet **44×30 FCM-Zellen = 1320 Glyphs**, jeweils 8-bpp indiziert.
Es wird kein hypothetischer 5-bpp- oder linearer 8-bpp-Bitmapmodus angenommen.
Die logische Grafik bleibt **352×240**. H320 und Hardware-Skalierung geben jedem
Quellpixel 2×2 physische PAL-Pixel: **704×480**, ganzzahlig und ohne Interpolation.
Das erhält die Lowres-Pixelform und passt innerhalb des 720×576-PAL-Bildes.
Keine Zeile oder Spalte wird weggelassen. Der Test ist für **PAL/50 Hz** vorgesehen;
NTSC/480 sichtbare Zeilen ist keine zugesagte Geometrie.

Zusätzlich gegen [VIC-IV-Hardwarecode](https://github.com/MEGA65/mega65-core/blob/99538d0e735ee8d1567b8e5578b2e49d1d1a33bd/src/vhdl/viciv.vhdl)
geprüft: `chargen_y_sub=chargen_y_scale` und Legacy-V200-Vorgabe `2-1` bedeuten
**CHRYSCL=1** für zwei physische Raster je Quellpixel. Die verkürzte
Registerbeschreibung der Reference ist hier missverständlich. XEMU bildet V200
über Doublescan nach; ein XEMU-Lauf wird durch den Quellcodevergleich nicht ersetzt.
XEMU-Quellenstand: `40dfef0d1d5f56be2469492715c12bdb32c75b67`.

| Register | Titelwert und Zweck |
| --- | --- |
| `$D011` | `$1B`: DEN/RSEL an, ECM/BMM aus |
| `$D016` | CSEL an, MCM und X-Scroll aus |
| `$D031` | H640/V400/ATTR/BPM aus, vorhandene Taktbits bewahrt |
| `$D054` | `$05`: CHR16 + FCLRHI; kein Alpha oder horizontales Smoothing |
| `$D058/$D059` | `$0058` = 88 Byte Zeilenstride |
| `$D05E`, `$D063` | 44 Spalten; hohe Spaltenbits 0 |
| `$D07B` | 29 = letzte der 30 Zeilen |
| `$D05A/$D05B` | 120 / 1: zwei native Pixel pro Quellpixel in X/Y |
| `$D04C/$D04D` | Text-X = 48 im VIC-Koordinatensystem |
| `$D04E/$D04F` | Text-Y = 48 |
| `$D048/$D049`, `$D04A/$D04B` | Border oben 48, unten 528 exklusiv |
| `$D05C/$D05D` | Sideborder 40, HOTREG aus |
| `$D060..$D063` | Screenadresse `$7000` |
| `$D064/$D065` | Color-RAM-Offset `$2000` |
| `$D070` | `$50`: primäre und CPU-gemappte Palette Bank 1 |
| `$D015` | 0: Hardware-Sprites aus |
| `$D07A.4` | XEMU-CHARY16 aus; übrige Comparator-/IRQ-Bits bewahrt |

Alle Zellen haben leere Attribute: kein NCM, GOTOX, Rowmask, Flip oder Alpha.
Glyphs `$1000..$1527` adressieren jeweils 64 Byte ab `$40000`.
BASIC-Palette Bank 0/3 und sonstige Paletteneinträge bleiben unberührt.

## Datei und Speicher

`VYTI.DAT` v1 hat 84.597 Bytes. Alle Mehrbytefelder sind Little Endian.

| Dateioffset | Inhalt |
| --- | --- |
| `$00` | `VYTI`, vier Byte Magic |
| `$04` | WORD Version 1 |
| `$06/$08/$0A` | WORD Breite 352, Höhe 240, Palettenzahl 33 |
| `$0C` | DWORD Tilebytes 84.480 |
| `$10` | WORD additive Summe des nachfolgenden Payloads modulo 65536 |
| `$12..$74` | 33 RGB8-Triplets in Originalindexreihenfolge |
| `$75..$14A74` | 1320 Tiles, Tilezeilen links→rechts/oben→unten, intern 8×8 row-major |

| Physische Adresse | Verwendung |
| --- | --- |
| `$2001..$200C` | BASIC `SYS 8448` |
| `$2100..$2737` | Code, veränderliche DMA-Liste, Zustände und Register-/Palettensicherung |
| `$4000..$4A4F` | 2640 leere FCM-Attribute als DMA-Quelle |
| `$6800..$68FF` | SEQ-Puffer |
| `$6900..$69FF` | Rücklesepuffer, anschließend 117-Byte-Header-/Palettenprüfung |
| `$7000..$7A4F` | 2640-Byte-FCM-Screen |
| `$15000..$15A4F` | Sicherung des eigenen Color-RAM-Bereichs |
| `$FF82000..$FF82A4F` | FCM-Attribute, eigener erweiterter Color-RAM-Bereich |
| `$40000..$54A74` | vollständiges VYTI-Ladeziel |
| `$40000..$549FF` | nach Ausrichtung die 84.480 FCM-Bytes |

`$1000..$15FF` (KERNAL/Cursor), DOS-Arbeitsbereiche `$10000..$11FFF` und
`$1F800..$1FFFF`, sowie ROM `$20000..$3FFFF` sind keine Nutzdatenziele.
Der BASIC-Screen wird nicht überschrieben; unterstützt wird der normale
80×25-Startzustand wie bisher mit ROM V920395. Individuell umgelegte BASIC-
Screenbuffer sind nicht separat getestet. Das PRG belegt ab `$2001` bis `$7A4F`.

Der aus Stable übernommene SEQ-Kern setzt **SETBNK `$FF6B` vor SETNAM**,
bewahrt das Ladegerät aus KERNAL `$BA` (Fallback 8), benutzt LF/SA 2/2 und beendet
jeden Pfad mit CLRCHN/CLOSE. Es gibt keine CHROUT-Ausgabe während CHKIN.
Jeder Chunk wird nach High RAM geschrieben, zurückkopiert und byteweise verglichen.
Erwartete Dateilänge und EOF müssen zusammenpassen. Gesamtsumme und der komplette
117-Byte-Header inklusive Palette werden geprüft. Additive Laufzeitsummen sind
keine kryptografische Integritätsgarantie; Build und Datenträger haben SHA256.

Nach Prüfung verschieben drei vorwärts laufende F018A-COPYs die Tiles um 117 Byte
zurück: 32768/32768/18944 Byte. Ziel liegt stets vor Quelle; trotz Überlappung
werden noch benötigte Quelldaten nicht überschrieben. Alle Längen sind ungleich
0. MEGA65-DMA darf die 64-KiB-Bankgrenze innerhalb des Megabytes überschreiten.
Header/Palette sind danach im Ladeziel überschrieben, aber geprüft und separat
im PRG vorhanden. Keine Daten der drei produktiven SEQs werden geladen.

## Exit und erneuter Start

Disk-I/O erfolgt mit laufendem KERNAL-IRQ im BASIC-Zustand. Erst danach wird der
IRQ während der Titelanzeige gesperrt: BASIC-Cursor und Text-IRQ schreiben dadurch
nicht in den FCM-Screen. **X/x** wird über die dokumentierte Hardware-ASCII-FIFO
`$D610` erkannt und quittiert; andere Ereignisse werden verworfen.

32 veränderte VIC-Register, 33 RGB-Paletteneinträge der Bank 1 und die 2640 eigenen
Color-RAM-Bytes werden gesichert/restauriert. Sprite-Enable und Video-/Screen-
/Charset-Auswahl werden wiederhergestellt; Spritegrafiken/-positionen sowie
Charsetpointer werden nicht verändert. KERNAL-Cursorvariablen bleiben unangetastet.
Die Wiederherstellung erfolgt mit HOTREG aus; der ursprüngliche HOTREG-Wert kommt
zuletzt. PHP/PLP bewahrt den IRQ-Zustand des Aufrufers.

Wichtig: `$D011.7` liest den **laufenden Raster**, nicht den gesetzten IRQ-Compare.
Der gespeicherte Schreibwert wird deshalb aus `$D07A.0` rekonstruiert; anschließend
wird der vollständige Comparator-/Quellenwert aus `$D07A` wiederhergestellt.
Ein zweites RUN initialisiert Loaderzustand und DMA-Megabyteoptionen erneut.

## Reproduzieren und prüfen

Python 3, Java und KickAssembler **5.25**; Python-Abhängigkeiten in
`tools/stage5d0-requirements.txt`. Das Buildskript prüft den Jar-SHA256
`9592a39336e73a1db8b4a7749256d62d29b113b1c7f0f6c86ea43870ebd9ae1f`.
Aus dem Repository mit vorhandenem `stage5c-stable`-Tag:

```sh
python -m pip install -r tools/stage5d0-requirements.txt
python tools/convert_stage5d0_title.py
python tools/build_stage5d0.py --kickass /path/to/KickAss.jar
python tools/analyze_stage5d0_copper.py
python -m unittest discover -s tests -p test_stage5d0.py -v
python tools/package_stage5d0.py
```

Build: `releases/stage_5d0/`, mit ASM, PRG, D81, VYTI, Binärdaten, Symbolen,
Memory-Map und SHA256SUMS. Die ZIP ergänzt Originalinputs, Werkzeuge und Dokumente.
Zum vollständigen Rebuild aus der ZIP bitte den Repository-Branch verwenden:
der Schutzvergleich braucht die unveränderte `stage5c-stable`-Git-Referenz.

**9/9 automatische Tests bestanden**, keine übersprungenen Tests. Geprüft sind
Originalpixel-/Palette-Roundtrip, D81-Dateiketten, tatsächlich assemblierter
Loader, exakte FCM-Pixelabfrage aus dem geladenen RAM, SEQ-/DMA-Fehler,
Dateilängen-/Checksum-/Headerfehler, X/x, zwei Start-/Exit-Zyklen, IRQ-/Palette-
/Color-/Registerrestaurierung und Schutz der KERNAL-/DOS-/ROM-Bereiche.
CPU, Disk-KERNAL, DMA, Palette und FCM werden im Host modelliert; **kein eigener
XEMU-/Hardwarelauf**. Prüfbericht: `stage5d0-test-results.json`.
Alle 13 Release-Dateien sind im unabhängigen Zweitbuild byteidentisch.

XEMU-Abnahme mit **PAL, ROM V920395, BASIC 80×25**:

1. D81 in Laufwerk 8 einlegen, `LOAD "STAGE5D0",8`, `RUN`.
2. Ganze Titelgrafik prüfen: linker Planet, rechter Text, unterste Sternzeile;
   keine Streifen, fehlenden Zeilen, Farbwechsel oder unscharfen Pixel.
3. Andere Tasten dürfen die Anzeige nicht verändern; X/x beendet.
4. BASIC samt Cursor, Farben und Screenmodus prüfen, Text eingeben und `DIRECTORY`.
5. `RUN` erneut ausführen, Titel prüfen und erneut mit X verlassen.
6. Optional fehlerhafte/fehlende VYTI auf einer separaten Disk testen: sichtbarer
   Ladefehler, sauber geschlossener Kanal, unveränderter BASIC-Videomodus.

## Amiga-Copper und Overscan

Reproduzierer: `tools/analyze_stage5d0_copper.py`, Rohbefunde:
`docs/stage5d0-copper-report.json`; ausführliche Einordnung in
[der Voranalyse](stage5d0_title_preanalysis.md).
Gesicherte COP1LC `$420`/COP2LC `$184AE` werden aus dem kompakten CHIP-Chunk des
WinUAE-Savestates gelesen. **Dazu gehören die Listen im CRAM desselben Savestates**,
nicht dieselben Adressen im separat aufgenommenen Memory Dump. Die weiteren
vier im Issue genannten Listen werden dagegen im separaten Dump untersucht.

Unter klassischen OCS/ECS-Regeln ergibt die referenzierte COP2-Liste 320
Lowres-Fetchpixel und eine vier-Bitplane-Phase zwischen Raster 44 und 244,
also 200 Zeilen. `$4200` ist Lowres/4 Bitplanes, `$A200` Hires/2 Bitplanes;
DIW allein umfasst ein größeres Fenster, ist aber nicht die aktive Bildhöhe.
Das ist **statische Analyse**, kein ausgeführter Copper-/WinUAE-Trace. Ob diese
Phase das angefragte Titelbild zeigt, ist nicht bewiesen. Die vorhandene
352×240-Datei ist kein eigenständiger Beweis für den aktiven Amiga-Overscan.
Für einen endgültigen Nachweis muss die richtige Titelphase unter WinUAE mit
COP-/BPLCON-/DIW-/DDF-Trace untersucht werden; die Spiel-Playfield-Geometrie
ist separat zu bestimmen.

## Spätere sichtbare Loaderintegration – separater Auftrag

Der jetzige Titelspeicher **überlappt** die produktiven VYLV-/VYGR-Ladeziele.
Ein bloßes Anzeigenlassen während deren SEQ-Ladevorgang würde Tiles zerstören.
Nach erfolgreicher isolierter Abnahme muss ein separater Integrationsstand einen
belegbar freien Titelcache planen, z.B. verlustfreie Tile-Deduplizierung und
verstreute FCM-Glyphplätze in nachgewiesen freien Bereichen der Bank 0/1.
Die 84.480 unkomprimierten Bytes passen nicht zusätzlich in den verbleibenden
Bank-4/5-Speicher; ROM und DOS dürfen auch dafür nicht genutzt werden.

Außerdem erfordert KERNAL-SEQ-I/O laufende IRQs. Dann muss dessen Cursor-/Textpfad
kontrolliert vom Titelscreen getrennt und die Bank-1-Titelpalette bis zum Übergang
bewahrt werden; keine Ausgaben während CHKIN. Erst nach allen verifizierten
Datendateien folgt ein klarer Wechsel zum bestehenden NCM-/RRB-Spielmodus.
Das ist eine Integrationsplanung, noch keine umgesetzte Loaderfunktion.
