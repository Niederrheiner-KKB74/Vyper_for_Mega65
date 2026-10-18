# Stage10b1c — isolierter H640-/H320-GOTOX-Test (Issue95)

Eigenständiger Diagnosebranch `stage10b1c-h320-gotox`, Basis PR94,
Commit `fd6214c1c6be1adcedea095b0ebd474288a83403`. Produktive Stage10a1,
alle bisherigen Testquellen und Releases bleiben unverändert. Keine
Stable-Markierung, kein Merge und kein produktiver Stage10b2-Fix.

## Fragestellung und Beweisgrad

Der [Hardwarevergleich aus PR94](stage10b1b_hardware_results_20261017.md)
zeigt Unterschiede in C/D trotz gleicher Bilddaten. Er zeigte außerdem eine
falsche Mono-Breitenannahme in A/B; deren HUD/Pixie war auf beiden Plattformen
offscreen. Diese Fehler werden hier im Szenenlayout vermieden. Die externe
Interpretation unterschiedlicher GOTOX-Skalierung wird geprüft, nicht als
bereits bestätigter Hardwarefix übernommen.

**Nachgewiesen im Quellcode:** Der Core schreibt den GOTOX-Wert in den
Rasterpuffer-Schreibzeiger. Dessen Ausgabe wird anschließend über CHRXSCL und
H640 skaliert. Der verfügbare lokale XEMU-Code setzt GOTOX dagegen direkt als
Ausgabe-X um: H640 unverändert, H320 mit Faktor2. Beide Quellen erwarten bei den
hier getesteten Einstellungen dieselbe Glyphgröße, aber für A unterschiedliche
GOTOX-Positionen. Ob dies den vollständigen Hardwarefehler erklärt, muss der
Benutzer mit diesem PRG prüfen.

Quellen:

- [Core0.97 aaf4542: GOTOX-Dispatch](https://github.com/MEGA65/mega65-core/blob/aaf4542d02679271b5fb84ad933cc39bbe091c3f/src/vhdl/viciv.vhdl#L4767),
  insbesondere `raster_buffer_write_address(9 downto0) <= glyph_number(9 downto0)-1`.
- [Core: Rasterpuffer-Ausgabe](https://github.com/MEGA65/mega65-core/blob/aaf4542d02679271b5fb84ad933cc39bbe091c3f/src/vhdl/viciv.vhdl#L5588):
  H640 nutzt CHRXSCL, H320 CHRXSCL/2, jeweils mit120er-Akkumulator.
- [Verfügbarer XEMU-Code](https://github.com/lgblgblgb/xemu/blob/40dfef0d1d5f56be2469492715c12bdb32c75b67/targets/mega65/vic4.c#L1534):
  `xcounter=char_value&0x3ff`, bei H320 `xcounter<<=1`, danach CHARX addieren.
  `calculate_char_x_step` und die Monoglyph-Schleifen geben bei Schritt0,5
  zwei native Pixel pro Quellpixel aus. Dieser Codebeleg ist keine Aussage,
  dass das vom Benutzer verwendete Release exakt diesen Commit enthält.

## Kontrollierte Varianten

| Einstellung | A: bisherige H640-Konfiguration | B: vorgeschlagene H320-Konfiguration |
|---|---|---|
| D031 | C0 (H640+FAST) | 40 (FAST, H640 aus) |
| D05A / CHRXSCL | 60 | 120 |
| GOTOX für logisches X | X×2 | **X unverändert, kein ASL** |
| Effektiver Glyph-Quellschritt | 60/120=0,5 | (120/2)/120=0,5 |
| Monoglyph | 8logische /16native Pixel | identisch |
| NCM-Glyph | 16logische /32native Pixel | identisch |
| Sprite-H640 (D054.4) | 1 | **weiterhin1**, unabhängig vom RRB-Modus |

Zwischen A/B ändern sich nur D031.7, D05A, die erzeugten GOTOX-Wörter und die
unabhängige Varianten-Spritegrafik A/B. Keine Schattenkopie mit nachträglichem
ASL in B: Der Builder erzeugt Rohwerte; der Assembler übernimmt für B direkt
die zugehörigen Low-/High-Bytes. Es werden auch die transparenten Overlay- und
Abschluss-GOTOX-Wörter umgerechnet, nicht nur die HUD-Grenze.

Konstant und ausdrücklich gesetzt: D054=55 (CHR16/FCLRHI/VFAST/SPR H640,
PALEMU0), D051-Schreibwert1F (NORRDEL0, DBLRR0), D07A=00, D079=00,
D053-Ausgabebits5/6=0, IRQ-Maske0, D05B=1, D07B=25,
HOTREG0, Rasterdelay0, CHARX80/CHARY104, obere Grenze104/untere504,
seitlicher Rand80. ScreenE000, Color-Offset0, Font4000, Palette9A.
Gegenüber PR94 sind D07A und Paletten jetzt deterministisch; auch die zusätzliche
Screen-/Color-Zeile wird bewusst genullt. Diese gemeinsamen Änderungen sind
keine zusätzliche A/B-Variable, aber der Test ist deshalb keine byteidentische
Neuauflage der alten Szene D.

**RRB-Minimalszene:**48Einträge pro Zeile, Stride96Bytes,25Zeilen. Das ist
bewusst weniger als die96Einträge/192Bytes der vorigen Vollreferenz. Die
kleinere Last vermeidet, eine GOTOX-Position mit der früheren hohen Guardlast
zu verwechseln. Aus Erfolg hier folgt keine Abnahme der vollen Engine-Last.

## Szene und Sollpositionen

Bezugssystem: logische Spielkoordinaten0–319, Y0–199. Die Tabelle nennt native
X-Offsets **relativ zu CHARX**, nicht absolute Monitor-/Foto-Koordinaten.
Im normalen640Pixel-Ausgabebereich entspricht ein logischer Pixel zwei nativen
Pixeln. VGA/HDMI-Upscaling oder Fotoperspektive darf nicht damit verwechselt werden.

- Ein festes15×25-NCM-Raster belegt das Playfield0–239. Weißer Außenrahmen,
  blaue Rasterlinien, rote rechte Pixelspalte beiX239, also native478/479.
  Dieses zusammenhängend ab GOTOX0 gezeichnete Raster ist der Größenmaßstab.
- HUD abX240: genau zehn gewöhnliche Zeichen pro Zeile, je8logische Pixel.
  Es endet bei320. Text ist in A/B gleich; die Variantenkennung kommt aus
  Hardware-Sprite2 links oben. Sprite3 schreibt `NIO` als Kennung „kein I/O“.
- Drei Kopien desselben **originalen Player-NCM-Pixies**, ohne Konvertierungs-
  oder Palettenänderung, stehen bei(32,80), (112,104), (224,128). Sie sind
  statische16×16-Transparenz-/Positionsreferenzen, kein Animationstest.
- Getrennt davon: weißer Hardware-Referenzrahmen bei(112,160), Projektil bei
  (224,176). Es sind dieselben Diagnose-Spritegrafiken wie vorher, kein Umbau
  der produktiven Player-/Schussgrafik. Rahmen16native Pixel breit (8logisch),
  Projektil2native×8physische Raster (1×4logisch).
- Die Spritekoordinaten bleiben in beiden Modi rohX301/Y424 und X525/Y456:
  `native_sprite_X=CHARX+2*X-3`, `native_sprite_Y=CHARY+2*Y`.
  Der bekannte3Pixel-Originversatz ist ausdrücklich Teil der Referenz;
  keine heimliche Spritekorrektur beim H320-Umschalten.
- Weiße einlogische-Pixel-breite NCM-Probestriche, auf achtlogische Pixel Höhe,
  markieren die folgenden Zielwerte. Die passende HUD-Zeile nennt `GOTO Xnnn`.
  GOTOX mit90 statt10 schaltet transparente Überlagerung ein.

| Quellzeile / Y | logisches X | A-Rohwort | B-Rohwort | XEMU-A native Erwartung | FPGA-A Quellmodell | B beide Quellmodelle |
|---|---:|---:|---:|---:|---:|---:|
|2 /16|0|0|0|0|0|0|
|3 /24|40|80|40|80|160|80|
|4 /32|80|160|80|160|320|160|
|5 /40|120|240|120|240|480|240|
|6 /48|160|320|160|320|640 (außerhalb)|320|
|7 /56|200|400|200|400|800 (außerhalb)|400|
|8 /64|240|480|240|480|960 (außerhalb)|480|
|20 /160|304|608|304|608|1216 (außerhalb)|608|
|21 /168|319|638|319|638|1276 (außerhalb)|638|
|22 /176|320|640|320|640 (außerhalb)|1280 (außerhalb)|640 (außerhalb)|

Abschluss-GOTOX bei320 wird außerdem an jedes Zeilenende und in alle
Füllslots geschrieben. Dahinter werden keine Testglyphen gemalt. Die explizite
320er-Probe liegt vollständig rechts außerhalb: Sie darf weder links erscheinen
noch das Playfield überschreiben. Bei319 bleibt von der16logische-Pixel-Probe
nur die erste Spalte sichtbar. Die letzte Pixieposition224+16=240 endet genau
vor dem HUD. Source-Slots und tatsächliche Rohwörter aller559GOTOX-Einträge
stehen in `releases/stage_10b1c/scene.json`.

Die A-HUD- und Pixie-Ziele sind absichtlich die bisherigen H640-Werte:
XEMU sagt HUD bei480 voraus, das FPGA-Quellmodell bei960. Dass sie unter der
Hypothese auf Hardware außerhalb liegen, ist das zu messende Signal. A wird
nicht durch eine heimliche FPGA-spezifische Halbierung „korrigiert“.

## Testanleitung auf XEMU und echtem MEGA65

Identische D81/PRG verwenden. Frisch starten: PAL80×25, identische ROM wie bisher
(V920413), Core0.97 aaf4542 bzw. XEMU Release20260129235930. Pro Plattform die
wirklich verwendeten Versionen notieren; der Build erkennt sie nicht automatisch.

```basic
LOAD "STAGE10B1C",8
RUN
```

1. Nach Start zeigt der unabhängige Marker **A**. Vollständiges Foto/Screenshot
   `HW_A1` bzw. `XEMU_A1` erstellen. Rahmen, roteX239-Grenze, HUD, drei Pixies,
   Probestriche und beide Referenz-Sprites erfassen.
2. `2` wählen: Marker **B**. Alle Positionen gegen Tabelle und Raster zählen,
   Foto `HW_B`/`XEMU_B`. Das HUD muss beiX240 beginnen und zehn Zeichen Platz
   haben. Insbesondere die ganze Szene beurteilen, nicht nur wieder sichtbare Schrift.
3. `1` zurück zu A: Foto `HW_A2`/`XEMU_A2`. Mit A1 vergleichen. Kein
   Registerexport und keine KERNAL-/Dateioperation findet beim Wechsel statt.
4. Wieder B, dann `R`: dieselbe Szene ohne I/O neu aufbauen; Foto `B_R`.
   `D` liest nur die Diagnose-Register neu, ohne Grafikneustart; Foto `B_D`.
   Diese Schritte trennen Moduswechsel, Grafikneustart und reines Rücklesen.
5. `X`: BASIC muss normal erscheinen, `DIRECTORY` muss funktionieren.
   `RUN`: beginnt wieder mit A. Dann nochmals `X`. Auch direkt aus A testen.

Die Exit-Routine sichert alle vier Paletten und das gesamte Color-RAM,
restauriert die veränderten VIC-Felder und den ursprünglichen CPU-IRQ-Zustand.
D051 wird nie aus seinen live gelesenen unteren sechs Bits zurückgeschrieben:
Schreibschatten1F während des Tests, gesicherte obere Kontrollbits plus1F beim
Exit; D050 bleibt unangetastet. Ein bei Eintritt maskenseitig aktiver X-IRQ
führt vor der Änderung dieser Register zur Rückkehr. Ein individueller,
inaktiver X-Komparator kann nicht vollständig ausgelesen werden und wird daher
nicht allgemein restauriert. Auch besondere externe IRQ-Kontexte mit nicht
rücklesbaren Steuerbits sind nicht unterstützt. Die Zusage gilt für den
angegebenen frischen nativen BASIC-Start, nicht für beliebige vorgeschaltete IRQ-
Programme. D053 wird nur mit seinen tatsächlichen Ausgabesteuerbits5/6
restauriert, nicht mit Live-Raster-/Spiegelbits.

Andere Tasten tun nichts. Keine Joystickbelegung nötig. Kein H/E/S-Export in
diesem Programm: kein Rückgriff auf den PR94-Exportpfad während der Anzeige.
Fotos müssen Versionskennung A/B und `NIO` enthalten. Für den A→B→A-Test
werden separate Bilddateien verwendet; nichts wird durch feste Dumpnamen überschrieben.

Optionaler Registerpuffer: Nach jedem Aufbau und bei `D` liegen518Bytes bei
`$4800–$4A05`. Extern im Monitor genau diese Bytes sichern; das verändert nicht
die Szene über ein eingebautes KERNAL-I/O. Header `VYDG1B1C`, Version1,
VarianteA/B, Aufbauzähler, D051-/D07A-/IRQ-Schreibschatten und162adressierte
Readbacks. Die sequenzielle Probe ist nicht atomar und hat keine CRC;
Dateivollständigkeit und unveränderte Rohdatei sichern. Sie ist kein Exportformat
von Stage10b1b und darf nicht mit dessen Decoder gelesen werden.

```sh
python tools/analysis/inspect_stage10b1c.py HW_B.REG --json HW_B.json
```

Externe Speicherproben zusätzlich: ScreenE000/2400Bytes, ColorFF80000/2400,
Font4000/2048, Pixie9040/128, Raster18000/24000, Pointer9300/8,
Sprites9200/256 und die96Bytes unmittelbar nach Screen/Color. Rohdaten und
Fotos gemeinsam mit Plattform/Variante/Aufbaufolge benennen. Das optionale
Rücklesen ersetzt keine Prüfung tatsächlicher sichtbarer GOTOX-Positionen.

## Speicher, Kapazität und HUD-Trade-off

Code2100–unter4000, Font4000–47FF, Readback4800–4A05,
Palettensicherung6000–6BFF, Variantenmarker7800–787F, Guard8000–803F,
Probe8100–813F, Rasteratlas8800–8BFF, Originalpixie9040–90BF,
Sprites9200–92FF, Pointer/Palette9300–9337,
ScreenvorlageA000–A95F, ColorvorlageB300–BC5F.
Aktiver ScreenE000–E95F, zusätzliche NullzeileE960–E9BF;
ColorFF80000–FF8095F, zusätzliche NullzeileFF80960–FF809BF.
Rasterglyphen18000–1DDBF. Alle32KiB Color-RAM werden nach40000–47FFF
gesichert und vor BASIC wiederhergestellt. ROM20000–3FFFF und Attic bleiben
unangetastet; keine Audio-/CIA-Programmierung.

48Einträge/Zeile enthalten15Raster-NCM-Glyphen, zehnMonoglyphen und je nach
Zeile eine zusätzliche Probe oder einen Pixiehalbframe. Der Rest sind GOTOX-
Füllkommandos ohne NCM-Blankglyph. Höchstens26malende Glyphen pro Zeile,
Glyph-Row-Payload maximal138Bytes (16×8+10). Das ist ein Quellpayload,
keine Messung von Speicherbuszugriffen oder Rasterzyklen.25sichtbare Zeilen
und16×16-Pixieformat bleiben gleich. A/B benötigen dieselbe Bytezahl, dieselbe
Zahl von Screen-/Color- und GOTOX-Patches und dieselben Spritekoordinaten.
Die Ausgabe ist statisch; pro Frame wird kein CPU-Renderer aufgerufen.
Die CPU wartet per Pollschleife auf Eingaben — das ist keine gemessene geringe
CPU-Auslastung und kein Benchmark der produktiven DMA-/Audio-Last.

H320/120 erzeugt hier **keine kleinere Schrift** als H640/60. Zwanzig normale
Glyphen würden160logische Pixel benötigen und passen nicht ins80Pixel-HUD.
Dieser Test verwendet deshalb ausdrücklich zehn Zeichen und kurze Beschriftungen.
Eine zeilenweite Skala kann nicht gleichzeitig den Playfield-Pixie unverändert
lassen und nur das HUD halbieren. Für eine spätere Integration wären z.B.
5×7-Zeichen in einer vorhandenen Zelle mit Trim, gepackte NCM-HUD-Glyphen oder
kürzere/anders angeordnete Anzeigen separat zu prüfen. Keine stillschweigende
Verdopplung des Playfields, kein Versprechen unveränderter20HUD-Zeichen.

Die produktive Stage10a1 benutzt192Byte-RRB-Zeilen/96Einträge und dynamische
Slots. H320 allein vergrößert oder verkleinert diese Datentabellen nicht;
24Pixie-Zustände, Glyphpuffer und25Zeilen bleiben speichertechnisch möglich.
Dieser48Slot-Test beweist aber weder alle dynamischen Überlappungen noch das
Raster-/CPU-Budget unter voller Engine-, Sternen- und Audio-Last. Die
vollständige HUD-/Text-/Rückkehr-/Clipping-Konvertierung und alle GOTOX-
Schreiber müssten in einem späteren Stage10b2-Schritt gemeinsam geprüft werden.
Nur den HUD-GOTOX oder nur ein ASL zu ändern wäre kein vollständiger Fix.

## Reproduzierbarer Build und Prüfungen

```sh
python tools/build_stage10b1c.py --kickass /pfad/zu/KickAss.jar
KICKASS_JAR=/pfad/zu/KickAss.jar PYTHONPATH=/pfad/zu/py65 \
  python tools/test_stage10b1c.py
```

KickAssembler5.25 mit derselben bereits geprüften Jar-Prüfsumme wie die anderen
Stages; Python-Standardbibliothek/Java für den Build, py65==1.2.0 für die
Opcode-Hosttests. Offline, Originalassets aus dem Repository. Acht Hosttests:
Koordinatenmodelle/Grenzen, tatsächlicher6502-Patchcode A/B/A/B ohneASL in B,
konstante Register außer den zwei Modusparametern, Screen-/Color-Bounds und
Originalassets, getrennte Spritekoordinaten, Readbackformat, sichere X-IRQ-
Ablehnung/Restore, Dateiketten und byteidentischer unabhängiger Release-Rebuild.
Hosttests emulieren weder VIC-Pixel noch tatsächliche DMA-Kopien.

Der ergänzende lokale XEMU-Lauf ist in `docs/diagnostics/stage10b1c/` abgelegt.
Er prüft die tatsächlichen DMA-Daten, A→B→A, R/D, Palette, Restore, erneutes
RUN und eine tatsächliche BASIC-DIRECTORY-Ausgabe mit dem D81-Titel. Das lokale Test-XEMU samt dokumentiertem Monitor-Eingabepatch ist nicht
als das angeforderte Zielrelease ausgewiesen. UART-Pausen erlauben keine
Rasterzeit-/Wandzeitmessung. Exakte Ziel-XEMU-/Hardware-Fotos und deren Abnahme:
**noch durch den Benutzer auszuführen**. Sichtbare Positionen werden nicht
allein aus passenden Registerwerten als gemessen behauptet.

## Entscheidung über einen späteren Fix

Wenn B auf beiden Plattformen alle Probestriche, sämtliche Pixies, Sprite-/
Schussanker und das ganze HUD korrekt zeigt, ist die H320/120-Umrechnung als
Positionslösung für die Minimalszene bestätigt. Dann wäre ein kleiner separater
Stage10b2-Prototyp mit zentraler GOTOX-Umrechnung, H320/120 und expliziter
Sprite-H640-Einstellung sinnvoll — unter Erhalt der Zeilen-/Subrow-/Palettebits,
vorerst ohne Gameplayänderung. Anschließend volle Engine- und HUD-Abnahme.

Wenn nur das HUD erscheint, Pixies/Grenzen aber falsch bleiben, reicht diese
Hypothese nicht. Wenn R ohne I/O die Szene verändert, ist der Wiederaufbaupfad
weiter zu isolieren. Keine dieser möglichen Beobachtungen wird hier vorweg als
Testergebnis eingetragen.
