# Stage 9c1 – eigenständiger Highscore-Anzeigetest (Issue #81)

Branch `stage9c1`, **kein Stable, kein Merge vor Benutzerabnahme**.
Technische Referenz ist Stage9b1 Stable / Main-Merge
`6052f677a8b84a841549561e874cd2f3290b2129` (Programm `82eb6a7`).
Die Spielengine, sämtliche bisherigen Releases und Originaldaten bleiben unverändert.
Das neue Programm lädt keine Level-, Grafik-, Menü- oder Sounddateien.

## Referenz und Layout

Issue #81 spezifiziert den rechteckigen schmalen Rahmen sowie den Wortlaut:

- `- VYPER HIGH SCORE TABLE -`
- `- PRESS A KEY OR JOYSTICK BUTTON TO CONTINUE -`

Beide Texte werden vollständig und zentriert angezeigt. Es erfolgt keine
Verkürzung und kein Umbruch. Die gewünschte Aufteilung weicht bewusst vom
beschriebenen Amiga-Original mit vier Spalten à20 Plätzen ab: vier Seiten à20
Plätze, jeweils zwei Spalten à10. Seitenbereiche01–20,21–40,41–60,61–80.

**Screenshotabgleich offen:** Der in Auftrag/Issue angekündigte Original-
Highscore-Screenshot ist weder im aktuellen Chat noch im Issue oder seinen
Kommentaren angehängt. Ein Repository-Pfad/Link wurde erfragt. Die konkrete
Rahmen-/Textpositionierung orientiert sich deshalb an der verbindlichen
Layoutbeschreibung aus Issue81; ein pixelgenauer Bildvergleich wird nicht
behauptet. Die bisher vorhandenen Original-Menü-/Titelbilder sind kein Ersatz
für den Highscore-Screenshot.

Isolierter normaler80×25-Monochromtextmodus (640×200 logische Pixel, acht Pixel
pro Zeichen). In PAL beträgt die Ausgabe640×400 native Pixel, Ursprung(80,100).
H640=1, V400/H1280/Interlace/Attribute/Bitplanes=0; FAST bleibt erhalten.
CHRXSCL120, CHRYSCL1, LINESTEP80, CHARCOUNT80, letzter Zeilenindex24.
Damit passt auch die46 Zeichen lange Fußzeile problemlos in den Rahmen.
Kein komprimierter Font und kein Eingriff in den320×200-Spielmodus.

Alle folgenden Koordinaten sind nullbasierte Zeichenkoordinaten:

| Element | Position / Bereich |
| --- | --- |
| Rahmen | links4, rechts75, oben1, unten23 |
| Originalüberschrift | Zeile3, Spalte27 |
| Spaltenköpfe | Zeile5, Spalten16 und49 |
| Einträge | Zeilen7–16, Spalten16 und49, jeweils15 Zeichen |
| Seitenanzeige/Testdatenhinweis | Zeile18, Spalte30 |
| Steuerungshinweis | Zeile19, zentriert |
| Originalfußzeile | Zeile21, Spalte17 |

Rahmen und Texte bleiben innerhalb der80×25-Geometrie. Die rechte Spalte enthält
Ränge11–20 bzw.31–40/51–60/71–80. Das Format lautet `01: ACE  511999` mit
zweistelligem Rang, drei Zeichen Name und rechtsbündigem siebenstelligem
Scorefeld. Die80 Testrecords werden reproduzierbar erzeugt, nicht von Disk gelesen:
Rang r bekommt Score `(81−r)^3−1`, also streng absteigend bis0. Zehn wechselnde
Namen enthalten Buchstaben, Zahlen und Sonderzeichen, etwa `B02`, `K-9`, `A+B`,
`X/Y`, `!?!`, `M.R`, `Q@1`. Dies sind ausdrücklich erfundene **Testdaten**.
[Alle Records](../releases/stage_9c1/test-entries.json).

## Zeichensatz und Farben

Der normale obere MEGA65-PETSCII-Zeichensatz wird zur Laufzeit aus Character-WOM
`$0FF7E000…$0FF7E7FF` in den privaten Fontpuffer `$8000…$87FF` kopiert.
Keine MEGA65-ROM-Daten werden mit dem PRG/D81 verteilt. Ausschließlich sechs
private Rahmenglyphen (Codes128–133, je acht Bytes) werden in der Kopie ersetzt;
BASICs ursprünglicher Zeichensatz bleibt unberührt.

**VIC-IV-Alias beachten:** `$1000/$1800/$9000/$9800` werden bei Monochromtext
als Character-WOM-Aliase behandelt. Daher ausdrücklich `$8000` als private
CHARPTR-Basis, nicht `$9000`. Referenz: vorhandener Enginepfad `hud_copy_font`
und XEMU `get_charset_effective_addr`. Hotregister-Propagation wird vor allen
Mode-/Pointeränderungen abgeschaltet und beim Restore zuletzt wiederhergestellt.

Palettebank1 ist nur während des Tests aktiv. Index0 ist schwarz,1 weiß,
Index2 der gemeinsame Originalzyklus. Indizes3/4/5 sind Blau `$00F`, Gelb `$FF0`,
Rot `$F00`; das sind festgelegte Testbandfarben, keine neu behauptete Amiga-
Palettenrekonstruktion. RGB4-Kanäle werden identisch auf beide Nibbles erweitert.

`stage9c1_cycling.asm` ist eine **byteidentische Quellkopie** der bestätigten
Stage9b1-Routine. `assets/stage6a2/color_cycle.inc` wird unverändert eingebunden:
Start `$00EC`, Phase2, Rest1, sechs Phasen, sieben Schritte je Phase, Deltas
`+$0020,−$0200,+$0002,−$0020,+$0200,−$0002`. Ein Update je50-Hz-Frame;
vollständiger Umlauf42 Frames. Rahmen, Titel und Fußzeile benutzen dieselbe
Palettefarbe2 und ändern sich dadurch synchron. Blättern startet den Zyklus
nicht neu.

Die Tabellenbänder sind die in Issue81 akzeptierte **zeilenweise Annäherung**:
**Jede einzelne Tabellenzeile** hat genau eine Farbe: Blau, Gelb, Rot, Blau,
Gelb, Rot usw. Direkt benachbarte Zeilen haben stets unterschiedliche Farben.
Alle acht Frames (160ms bei50Hz) wird die Phase um eine Zeile erhöht:
`Farbe(Zeile,t)=Band[(Zeile+Phase(t)) mod3]`. Damit erscheint die bisherige
Zeile1 an Zeile0: Bewegung **von unten nach oben**. Beide Spalten verwenden
identische Zeilenfarben. Die gesamte Periode dauert24 Frames (0,48s).
Nur300 Vordergrundwerte im privaten Farbpuffer werden verändert; anschließend
kopiert ein2.000-Byte-DMA die vollständige private Color-Ebene. Text und Glyphen
bleiben stabil. Es gibt keinen Pixel-Rastereffekt, Raster-IRQ oder Farbwechsel
innerhalb eines Zeichens. Die Originalwortlaute werden nicht für die Animation
umgebaut.

Die Korrektur aus PR82 ersetzt ausschließlich die früheren vierzeiligen
Farbblöcke durch diese Einzelzeilenfolge. Die Phasengeschwindigkeit bleibt
bei einem Schritt alle acht Frames. Leerzeilen, Rahmen, Titel, Fußzeile und
Seitenanzeige bleiben außerhalb der Tabellenanimation.

## Bedienung und Framezustand

- Joystick **Port2** links/rechts oder Cursor links/rechts: eine Seite zurück/vor.
- Grenzen stoppen an Seite1 bzw.4, kein Umlauf.
- Gehaltene Richtungen blättern nur einmal. Für den nächsten Joystick-Schritt
  muss neutral erreicht werden. Cursor-Typematic wird bis zur physischen
  Freigabe unterdrückt; kurze FIFO-Tastendrücke zwischen Frames bleiben nutzbar.
- Joystick-Feuer nach Freigabe, RETURN, X oder jede andere Eingabetaste außer
  den Seitentasten beendet den Test zu BASIC. Ein beim Start noch gehaltenes
  Feuer wird erst nach Loslassen scharfgeschaltet.
- Keine Namenbearbeitung, keine Highscore-Berechnung/-Sortierung im Laufzeitcode,
  keine Speicherung, keine `VYHI.DAT`, kein Menü und keine F3-Integration.

Die kooperative Hauptschleife prüft fortlaufend Eingaben und merkt den
Raster250→nicht250-Übergang als Frame-Ereignis. Pro PAL-Frame wird genau einmal
animiert. Keine blockierende Animationsverzögerung, kein Timer-IRQ und keine
KERNAL-Aufrufe während der Anzeige. Auch wenn kein Frame fällig ist, wird X
verarbeitet. Ein Seitenwunsch wird vorgemerkt und am selben blankingseitigen
Frame-Rand veröffentlicht wie die Farbanimation. Gleichzeitiger Seiten- und
Bandschritt benötigen keine doppelte Color-Publikation.

Keyboard-FIFO `$D610/$D619`, physische Cursorfreigabe über `$D614/$D613` und
`$D60F`. Die Cursorereignisse sind PETSCII `$1D/$9D`. Die Port2-Pins werden über
CIA1-DDRA als Eingänge konfiguriert; DDRA und Keyboard-Spaltenwahl werden am Ende
wiederhergestellt. Tastatur-FIFO beim Eintritt und Exit begrenzt geleert.

## Speicher / BASIC-Rückkehr

| Bereich | Nutzung |
| --- | --- |
| `$2001…$200C` | BASIC-Zeile `SYS8448` |
| `$2100…$25A3` | Controller, Video-Sicherung/-Restore, F018A-COPY |
| `$3100…$31C3` | unveränderter COLOR02-Algorithmus |
| `$3200…$3357` | private Register-/Palettensicherungen und Zustände |
| `$4000…$5F3F` | vier statische Screen-Seiten, je2.000 Byte |
| `$6000…$67CF` | private Color-Ebene,2.000 Byte |
| `$67D0…$67FF` | sechs Rahmenglyphen |
| `$7000…$77CF` | privates Screen-RAM |
| `$8000…$87FF` | privater Monochromzeichensatz |
| `$15000…$157CF` | Sicherung des eigenen Color-Fensters |
| `$0FF82000…$0FF827CF` | eigenes Color-RAM-Fenster, Offset `$2000` |

Kein Attic-RAM, keine Speicherbelegung im ROM-Bereich `$20000…$3FFFF`, keine
DOS-Puffer bei `$10000…$11FFF`, kein Bank1-Color-CPU-Fenster `$1F800…$1FFFF`.
BASIC-Screen und Cursorworkspace bleiben unverändert, da ausschließlich die
private Screen-/Font-/Color-Ebene benutzt wird.

35 veränderte VIC-Register,33 Einträge der Palettebank1 und das2.000-Byte-Color-
Fenster werden gesichert/wiederhergestellt. D011s schreibbarer Rastervergleich-
Bit8 wird aus D07A rekonstruiert, nicht aus dem beim Lesen sichtbaren Rasterwert.
DEN und HOTREG werden erst nach der übrigen Geometrie wiederhergestellt. CPU-I/D-
Status über PHP/PLP erhalten; intern wird binär gerechnet. Keine MAP-Änderung,
keine Veränderung von CPU-Port/CPU-Takt oder Diskettenkanälen. Alle Veränderungen
liegen in den neuen Testquellen; Stage9b1 wird nicht gestartet oder verändert.

## Build und Prüfung

```sh
python tools/build_stage9c1.py --kickass /pfad/zu/KickAss.jar
PYTHONPATH=tests:tools:/pfad/zu/py65 python -m unittest test_stage9c1 -v
```

OpenJDK21, Python3.12, KickAssembler5.25 mit verifizierter SHA256;
Hosttests zusätzlich py65==1.2.0 und Pillow aus der bestehenden Testumgebung.
Keine zusätzlichen Build-Abhängigkeiten und kein MEGA65-ROM nötig.
`releases/stage_9c1/` enthält PRG, vollständiges819.200-Byte-D81, alle drei ASM-
Dateien, Include, eingebettete Daten, Symbole, Speicherkarte, Testrecordliste,
Buildbericht und SHA256-Manifest. Das D81 enthält nur `STAGE9C1` als PRG und ist
unabhängig von sämtlichen DAT-Dateien der Engine startbar.

**Elf Hosttests bestanden.** Zwei unabhängige Builds erzeugen alle14 Dateien
byteidentisch. Der Builder schützt alle1.828 bestehenden src/assets/tools/releases-
Dateien gegen den bestätigten Main-Commit. Die Tests führen tatsächlich
assemblierte Befehle aus und prüfen Seiteninhalte/Überschriften/Fußzeile,
Port2/Cursor/Grenzen/Entprellung, komplette Farbzyklen, Bewegungsrichtung der
Einzelzeilenfarben über384 Frames und alle vier Seiten (vorwärts/rückwärts),
stets verschiedene Nachbarfarben, unveränderten Color-RAM außerhalb der
300 Tabellenpositionen, Seitenwechsel ohne Phasenreset, RAM-/DMA-Grenzen, Exit und wiederholtes
RUN einschließlich ursprünglichem40-/80-Spalten-Modus, I/D-Status und Raster-
Vergleichsbit. Der separate X-Test belegt Reaktion ohne fälligen Animationsframe.
[Vollständiges Protokoll](stage9c1_test_results.txt).

Modellmessung der aktiven Arbeit, **ohne Rasterwartezeit und DMA-Latenz**:
maximal3.721 modellierte6502-Zyklen pro Bandschritt,2.000 DMA-Bytes. Beim
Seitenwechsel gleichzeitig mit Bandschritt werden4.000 DMA-Bytes übertragen.
Dies sind weder echte45GS02-Timings noch ein XEMU-/Hardware-Messergebnis.
Das Modell bildet nicht jedes VIC-IV-Detail ab; Aliasregeln/Geometrie wurden
zusätzlich gegen Referenz und XEMU-Quellcode geprüft.

Hardware-Dokumentation: [MEGA65 VIC-IV-Referenz](https://github.com/MEGA65/mega65-user-guide/blob/cefce48d72e5c98d732c0589461d62b205b5165f/appendix-viciv-registers.tex),
[Keyboard-Referenz](https://github.com/MEGA65/mega65-user-guide/blob/cefce48d72e5c98d732c0589461d62b205b5165f/appendix-keyboard.tex).

### Vom Benutzer unter XEMU zu prüfen

1. D81 einlegen, `LOAD "STAGE9C1",8`, `RUN` (PAL50Hz, Joystick Port2).
2. Vier Seiten01–20/21–40/41–60/61–80: Lesbarkeit, Namen/Sonderzeichen,
   Scoreausrichtung, vollständige Überschrift/Fußzeile und geschlossener Rahmen.
3. Cursor/Joystick halten und loslassen; keine Mehrfachsprünge, Grenzen1/4.
4. Anzeige einige Minuten stehen lassen: gemeinsamer Rahmen-/Textzyklus und
   gleichlaufende Bänder in beiden Spalten nach oben, keine Reste beim Blättern.
5. Feuer, RETURN, X und andere Tasten ausprobieren. BASIC muss im ursprünglichen
   Modus mit normalem Cursor erscheinen. `DIRECTORY` und erneutes `RUN` testen.
6. Den noch fehlenden Amiga-Screenshot auf Rahmenproportionen/Textpositionen
   abgleichen. Pixelgenaue Bandanimation ist ausdrücklich nicht Abnahmekriterium.

**XEMU hier nicht ausgeführt. Stage9c1 bleibt Testbuild bis zur Benutzerfreigabe.**
