# Stage 3b-3 – freigegebenes Amiga-Spielerraumschiff

Neue Stage im Branch `stage3b-3`, ausschließlich auf `stage3b2-stable`
(`811eecb42ee9ca6c980b5cb404ea82976d7de495`) aufgebaut. Stage 3b-2, seine
Quellen, Builder und Release-Artefakte bleiben unverändert. **Am 10.10.2026 vom Benutzer als stabil bestätigt: `stage3b3-stable`.**
Der Tag sichert den bestätigten Programmstand `be747701cbeee5f77af244ad3778f75088fca8a7`
mit ergänzter Abnahmedokumentation; ASM, PRG und D81 bleiben unverändert.

## Originaldaten und Darstellung

Die fünf verbindlichen Dateien wurden unverändert aus dem vorhandenen `main`
übernommen, Stand `316d474938facb8ba96b732141553af149a5ca82`:
`docs/player_graphics.md`, `assets/player/player_pixels.txt`,
`assets/player/player_palette.txt`, `assets/player/README.md` und
`tools/build_player_assets.py`. Keine Ersatzgrafik, keine neue Farbzuordnung.

Die freigegebene 16×16-Grafik wird mit diesem Skript reproduzierbar erzeugt.
`player_sprite.bin` verwendet das linke Pixel im High-Nibble;
`player_ncm.bin` verwendet es im Low-Nibble. Der tatsächlich joystickgesteuerte
Spieler ist ein **RRB/NCM-Pixie**, kein aktiviertes Hardware-Sprite. Er benutzt
die Objektdaten `$1660–$1677` und Glyphen `$321/$322/$323`. Der separate kreisende
Test-Pixie benutzt `$1678–$168F` und `$325/$326/$327`. Die 22 Pfad-Pixies benutzen
weiterhin Originaltyp 12 und `$261/$262/$263`.

Daher wird `player_ncm.bin` direkt verwendet: erste 64 Bytes für die oberen acht
Zeilen, zweite 64 Bytes für die unteren acht Zeilen. Eine weitere Konvertierung
ist nicht erforderlich. Der Builder prüft jede der 256 Pixelpositionen sowie die
Nibble-Reihenfolge beider Formate. Die RGB-Tabellen werden gegen die freigegebene
Textpalette und die Umrechnung `Amiga-Nibble × 17` geprüft. Die Rekonstruktion
ist eine visuell freigegebene Zuordnung, keine neu behauptete Original-CLUT.

[Erzeugte Vorschau](../assets/player/player_preview_original_palette.png).

## Unabhängige Spielerpalette und Schutz vor Überschreiben

Die Gegner behalten primäre Textpalette **Bank 1**. Der Spieler erhält
**Bank 2** als alternative Textpalette. Die Hardware-Sprites sind deaktiviert;
ihre bisherige ungenutzte Palette wird durch die freigegebene Spielerpalette
ersetzt. Bank 3 bleibt unangetastet, da ihre ersten 16 Einträge auch die BASIC-
ROM-Palette bilden. Initialisierung `$D070=$9A`: MAPEDPAL=2, BTPALSEL=1,
SPRPALSEL=2, ABTPALSEL=2. Die freigegebenen 16 RGB-Einträge werden einmal beim
Engine-Start nach Bank 2 geschrieben und bleiben während des Spiels unverändert.

Vor jedem dynamischen RRB-Fragment wählt ein kleiner Wrapper anhand der
Glyphennummer die Palette: `$321–$323` erhält GOTOX-Color-Byte 1 **`$60`**
(BOLD+REVERSE bei deaktiviertem VIC-III-ATTR), alle anderen Glyphen erhalten
**`$00`**. Dadurch verwendet der Spieler die alternative Palette; das nächste
Gegner-/Orbit-Fragment schaltet ausdrücklich auf die primäre zurück. NCM-
Attribut `$08`, GOTOX-Attribut `$90`, Transparenz, vertikale Positionierung,
Row-Buckets, Slotkapazität und Clearing bleiben unverändert.

Diese GOTOX-Auswahl entspricht der implementierten VIC-IV-Logik in XEMU
(`vic4.c`, GOTOX-Verarbeitung: BOLD+REVERSE und ATTR aus → `altpalette`;
`vic4.h`: BOLD=`$40`, REVERSE=`$20`). Die tatsächliche Darstellung wurde vom Benutzer unter
XEMU bestätigt; das Hostmodell prüft die ausgegebenen Tokens und
Palette-Zugriffe, nicht die VIC-Pixel.

Zwei alte Animationswege konnten bislang die Joystick-Glyphen überschreiben:
`v012a_capture_animation` kopierte alte NCM-Grafik, und `s2ja_animate_pixies`
kopierte den Typ-2-Frame sowohl zum Orbit als auch zum Spieler. Ausschließlich
jene Spieler-Schreibzugriffe sind durch gleich lange NOP-Sequenzen ersetzt.
Orbit-, Gegneranimation, Animationsuhr, SPACE und +/- bleiben erhalten.
Beim Start werden die freigegebenen Spielerbytes und beide Blank-Guards erneut
initialisiert. Keine Grafik-DMA schreibt nach `$C800–$C8FF`.

## Speicherbelegung und begrenzte Patches

| Adresse | Verwendung |
| --- | --- |
| `$3600–$367F` | unveränderliche 128-Byte-NCM-Quelle |
| `$3680–$368F` | freigegebene Rot-Tabelle |
| `$3690–$369F` | freigegebene Grün-Tabelle |
| `$36A0–$36AF` | freigegebene Blau-Tabelle |
| `$3700–$375E` | Palette-/Grafikinitialisierung und RRB-Palette-Wrapper |
| `$C800–$C83F` | vorhandener Spieler-Blank-Guard, neu genullt |
| `$C840–$C87F` | vorhandene obere Spieler-Glyphe, neue Originalgrafik |
| `$C880–$C8BF` | vorhandene untere Spieler-Glyphe, neue Originalgrafik |
| `$C8C0–$C8FF` | vorhandener abschließender Spieler-Blank-Guard, neu genullt |

Der neue Bereich liegt hinter dem Parserende `$35D9` und vor dem Mono-Glyphen-
Bereich `$4000`. Loader `$4800–$4B49`, RRB-Screen `$5000–$57CF`, Color-Vorlage
`$6000–$67CF`, SEQ-/DMA-Puffer `$6800/$6900`, VYGR-Verzeichnis `$6A00`,
Levelkopie `$7600–$7950`, BASIC-Color-Backup `$9000–$97FF` und Pfadgrafik
`$9800–$98FF` bleiben unverändert. High-RAM-Ziele `$40000/$54000` ebenso.
Objekte bleiben im korrigierten freien RAM `$1600–$18FF`, Diagnostik `$1900`;
KERNAL-/Cursorbereich `$1000–$15FF` bleibt geschützt.

Der Builder verlangt den SHA-256 der stabilen PRG-Datei und erlaubt nur:

- Drei JSR-Zieländerungen: `$2224` Paletteinitialisierung, `$2230`
  Grafikinitialisierung und `$BDC5` dynamischer Slot-Writer.
- Drei 3-Byte-NOP-Sequenzen bei `$B8F3`, `$BC59`, `$BC62`, ausschließlich
  zur Entfernung alter Animations-Schreibzugriffe auf den Spieler.
- Neue Daten und Code im zuvor vollständig leeren Bereich `$3600–$37FF`.

Gegenüber der stabilen PRG-Datei ändern sich **206 Bytes**. Alle übrigen Bytes
bleiben identisch, insbesondere Loader, Levelparser, Gegnergrafik-DMA,
Bewegungs-/Flugtabellen, Joysticklogik und komplette Exit-Routine.
Die Paletteauswahl ist ein selbst modifizierter unmittelbarer Operand im
bisherigen Writer; dessen Adressen und alle übrigen Instruktionen bleiben gleich.
Die reine Render-Erweiterung fügt CPU-Arbeit hinzu, der vorhandene Rastertakt
und Bewegungsalgorithmus bleiben erhalten; reale Bildrate ist unter XEMU zu prüfen.

Die unveränderte Loader-Statusmeldung trägt weiterhin die Bezeichnung Stage 3b-2,
da der Loader bytegleich erhalten wurde. PRG und D81 heißen eindeutig Stage 3b-3.

## Build und automatisierte Tests

Python 3.9+, Java und die gepinnte offizielle KickAssembler-5.25-JAR wie bisher:

```sh
python3 tools/build_stage3b3.py --kickass /pfad/KickAss.jar
python3 -m venv /tmp/vyper-stage3b3-tests
/tmp/vyper-stage3b3-tests/bin/pip install -r tests/requirements-stage3b1.txt
MEGA65_ROM=/pfad/MEGA65.ROM /tmp/vyper-stage3b3-tests/bin/python -m unittest discover -s tests -p 'test_stage3b3.py' -v
```

Der Builder ruft das unveränderte Original-Assetskript auf. Pillow ist nur für
die optionale Vorschau erforderlich; PRG und D81 benötigen es nicht. Kein ROM
wird im Repository gespeichert. Ausgabe: `releases/stage_3b3/` mit vollständigem
ASM, PRG, D81, Symbolen, Assembly-Speicherkarte, Build-/Vergleichsbericht und
SHA-256-Liste. Das D81 enthält `STAGE3B3` als PRG, `VYLV.DAT` und `VYGR.DAT`
als SEQ. Ein zweiter Build erzeugte byteidentische Artefakte.

**Acht Stage-3b-3-Tests bestanden:**

1. Alle freigegebenen Pixel, beide Nibble-Formate, RGB-Tabellen und eingebettete Daten.
2. Vollständiger Preload beider Originaldateien, Verifikation, Engine-Patchvergleich
   und D81-Dateien/Dateiketten/BAM.
3. Eigene Spielerpalette, unveränderte BASIC-Palette und Unabhängigkeit
   von einer simulierten vollständigen Änderung der Gegnerpalette Bank 1.
4. Statische Spieler-Grafik und Guards über 16 Animationswechsel, weiter animierter
   Orbit und unveränderter Originaltyp 12 der Gegner.
5. 56 Engine-Frames mit identischen Joystick-/SPACE-/+/-Eingaben gegen Stage 3b-2:
   identische Objekte, Diagnostik, RRB-Screen-Geometrie, Orbit-/Gegnergrafiken und
   Animationsuhr; korrekte Palette für jeden aktiven RRB-Spieler-/Gegnerfragment.
   Der identische Screen-Vergleich prüft auch das bestehende Clearing bei Bewegung.
6. Preload, Start, Bewegung, `X`, VIC-/Color-Restaurierung und erneuter Engine-Start;
   KERNAL-/Cursorbytes bleiben erhalten. Mit `MEGA65_ROM` wird zusätzlich die
   unveränderte Cursorroutine des bereitgestellten V920395-ROMs ausgeführt.
7. Grafik-DMA-Fehler nutzt unverändert den bisherigen BASIC-Exit ohne RRB-Textausgabe.
8. Die reale ROM-Palettenbeziehung Bank 3 → erste 16 BASIC-Farben wird modelliert.
   Die alte Auswahl `$DB` beschädigt diese Farben reproduzierbar; `$9A` erhält
   sie einschließlich zweier Start-/Exit-Zyklen vollständig.

Zusätzlich bestanden alle bisherigen Stage-3b-1-/Stage-3b-2-Tests: zusammen
**43 bestandene Tests** mit dem bereitgestellten ROM.

Dies sind CPU-/DMA-/Palette-/Rastermodelle. Sie prüfen keine echten Joystick-
Geräte oder pixelgenaue VIC-Ausgabe. Die XEMU-Abnahme stammt vom Benutzer; ein eigener Emulatorlauf wird nicht behauptet.

## XEMU-Abnahme durch den Benutzer

1. XEMU für diesen Vergleich zunächst frisch booten: Die vorherige Fassung
   kann die ROM-Palette bereits überschrieben haben. Dann D81 in Laufwerk 8: `LOAD"STAGE3B3",8`, anschließend `RUN`.
2. Beide DAT-Dateien erfolgreich geladen/verifiziert; 24 Pixies sichtbar:
   22 Typ-12-Gegner, ursprünglicher kreisender Pixie und neues Amiga-Spielerschiff.
3. Spielerschiff mit der freigegebenen Vorschau vergleichen: Form, Weiß/Rot/Gelb
   und Grautöne, Transparenz und korrekte Nibble-Reihenfolge.
4. Joystick Port 2 in alle Richtungen und bis zu den bisherigen Grenzen prüfen.
   Spielerfarben müssen beim Bewegen stabil bleiben; keine Grafikreste.
5. Orbit, Gegnerpfade, Geschwindigkeit, SPACE und +/- gegen `stage3b2-stable`
   vergleichen. Der Spieler bleibt statisch, der Orbit animiert wie bisher.
6. Mehrfach nach unterschiedlichen Laufzeiten mit `X` beenden: normaler BASIC-
   Bildschirm, normal blinkender Cursor ohne rote Linie und ohne nötigen Tastendruck.
7. Wieder `LOAD"STAGE3B3",8` / `RUN`: Grafik, Palette und Steuerung erneut korrekt.

**Benutzerbestätigung vom 10.10.2026:** „Stage 3b-3 als stabil bestätigt“.
Die obige Liste bleibt als Checkliste für spätere Regressionstests erhalten.

## Korrektur nach erstem XEMU-Test

Die Spielergrafik wurde vom Benutzer bestätigt, die BASIC-Rückkehr zeigte
jedoch einen grauen Bildschirm. Die falsche Wahl von Palette Bank 3 war die
Ursache: Ihre ersten 16 Farben sind zugleich die C65-ROM-Palette. Nur das
Auswahlbyte bei `$3704` ist von `$DB` nach `$9A` geändert; Playerdaten, Farben,
RRB-Auswahl, Bewegung und Exit-Code sind bytegleich zur ersten Stage 3b-3.
[Diagnose und Artefaktvergleich](stage3b3_exit_palette_fix.md). Die korrigierte Fassung wurde am 10.10.2026 vom Benutzer als stabil bestätigt.
