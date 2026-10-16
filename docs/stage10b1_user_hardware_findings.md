# Stage10b1: Auswertung der vom Benutzer gelieferten Hardware-/XEMU-Daten

Stand16.10.2026. Ergänzung zu Issue89/PR90; ausschließlich Analyse und
Dokumentation. Kein geänderter Diagnose-/Spielbuild, kein Stable-/Merge-Vorgang.

## Integrität und verfügbare Vergleichspaare

Beide hochgeladenen D81-Dateien haben819200Bytes. Das PRG `STAGE10B1` ist in
beiden Images byteidentisch zum veröffentlichten Diagnose-Build. Alle vier
gefundenen SEQ-Dumps bestehen Größen-, Magic-, Versions-, Phasen-, Register-
reihenfolge- und Prüfsummenprüfung. Es handelt sich nicht um unterschiedliche
PRG-Versionen oder beschädigte Exportdateien.
Hashes und Herkunft stehen in
[`inputs.json`](diagnostics/stage10b1/user-comparison/inputs.json).

| Vom Benutzer benannte Quelle | Datei auf D81 | Tatsächlicher Header |
|---|---|---|
| MEGA65 | V10BSH.DAT | Profil S, Umgebung H |
| MEGA65 | V10BSX.DAT | Profil S, Umgebung X |
| XEMU | V10BSX.DAT | Profil S, Umgebung X |
| XEMU | V10BEX.DAT | Profil E, Umgebung X |

Die Umgebung im Header wird durch die Exporttaste gesetzt, nicht automatisch
erkannt. Deshalb bleibt der zweite Dump auf der **MEGA65-D81 eine Hardware-
Aufnahme** laut Benutzerherkunft, obwohl seine Exporttaste E das Label X
gesetzt hat. Beide Hardwareaufnahmen sind Profil S. Ein Hardware-Dump des
Profils2/E (`V10BEH.DAT`) ist nicht enthalten. Das Paar S lässt sich bereits
vollständig vergleichen; das Paar E noch nicht. Kein fehlender Dump wird aus
Fotos oder XEMU-Werten rekonstruiert.

## Gesicherte gemeinsame Geometrie

Nach Initialisierung, nach simuliertem Moduswechsel und beim Szenenaufbau
stimmen im Paar S die folgenden Felder überein:

| Feld | MEGA65 und XEMU |
|---|---|
| D031 | C0: H640 und FAST |
| D054 | 75: einschließlich geerbtem PALEMU |
| D058/59 | C0/00:192Bytes Zeilenabstand |
| D05E / D063 Count-Highbits | 60 /0:96Einträge |
| D05A / D05B | 3C /01: horizontal2native Pixel je Quellpixel, vertikal2Raster |
| CHARX / CHARY | 80 /104 |
| D060–63 | physischer Screen E000 |
| D064/65 | Color-RAM-Offset0 |
| D068–6A | Monozeichensatz4000 |
| D05C / D05D | 50 /40: gleicher Seitenrand und HOTREG aus |
| D070 nach Initialisierung | 9A |
| D07B | 25 (bewusst unveränderte Referenz) |
| D08F | 00: kein optierter HWERRATA-Fix |

Auch die gemessenen Spritekoordinaten/-Freigaben unterscheiden sich im
Szenen-Snapshot nicht. Eine abweichend gesetzte H640-Auflösung, ein anderer
Screenpointer oder ein anderer192Byte-Stride erklären den beobachteten
Unterschied in diesem Test daher **nicht**. Das beweist noch nicht identische
Speicherinhalte oder identische Interpretation; der Export enthält Register,
keinen vollständigen Screen-/Glyph-/Color-RAM-Dump.

## Frühester relevanter Unterschied: bereits Phase1

| Register/Feld | Hardware | XEMU | Einordnung |
|---|---|---|---|
| D051.7 NORRDEL | 1 | 0 | relevanter Unterschied der RRB-Puffersteuerung |
| D051.6 DBLRR | 0 | 0 | beide ohne Doppelzeilenbetrieb |
| D053.7 | 1 | 0 | Raster-IRQ-Quelle/Readback, nicht die physische Skalierung |
| D067 | 1F | 00 | Sprite-first-X-Readback, nicht unmittelbar ein X-Origin-Fix |
| D079 / D07A | FF /88 | 00 /00 | Rasterkomparator, Quelle und Continuous-Pointer-Monitoring |
| D070 nur Phase1 | 00 | FF | anfängliche Palettenwahl; ab Phase2 beide9A |

Die unteren sechs Bits von D051 sind laufende Rasterpositionen und werden
nicht als stabiler Unterschied interpretiert. D051.7 bleibt hingegen in allen
vier Phasen verschieden: HardwareNORRDEL=1, XEMUNORRDEL=0. Die zweite
Hardwareaufnahme bestätigt dieselben stabil maskierten VIC-IV-Unterschiede;
die genaue Gegenüberstellung bleibt im JSON erhalten.

Es gibt weitere Unterschiede bei Firmware-/Identifikationsbytes, Audio- und
DMA-Kontextregistern. Diese sind im vollständigen Vergleich enthalten, sind
aber allein kein Nachweis eines Renderingfehlers. Insbesondere wird aus dem
unterschiedlichen Firmware-Readback nicht automatisch eine andere ROM-Datei
abgeleitet.

## Was der gepinnte Corecode tatsächlich belegt

Referenz: `mega65-core` Commit
`aaf4542d02679271b5fb84ad933cc39bbe091c3f`, `src/vhdl/viciv.vhdl`.

- Zeilen970–971 sowie2124–2125 setzen NORRDEL standardmäßig1, DBLRR0.
  Der beobachtete Hardwarezustand ist damit mit dem Core-Default vereinbar.
- Zeilen2662–2668: D051.6 steuert RRB-Update nur jeder zweiten Rasterzeile;
  D051.7 steuert den Rasterpuffer-Delay-/Doublebufferbetrieb.
- Zeilen3382–3409: Die Bits beeinflussen Fetch-Freigabe und die Auswahl der
  Schreibpufferhälfte (`half_toggle xor no_raster_buffer_delay`). Sie sind
  damit funktionale Rendersteuerung und keine bloßen Statusanzeigen.
- Zeilen1998–2007: D079/D07A liefern Komparator, IRQ-Quelle,
  Continuous-Pointer-Monitoring, CHARY16 und Kompatibilitätsbits.

Die lokal vorhandene XEMU-Quellreferenz bildet D051.7 als Registerbit ab,
verwendet aber nicht dieselbe zyklengenaue FPGA-RRB-Fetchmaschine. Diese
Aussage über den lokalen Quellstand ist **kein verifizierter Quellbefund zur
exakten vom Benutzer benutzten Release-Binärdatei**. Deren tatsächlicher Dump
belegt unabhängig davon NORRDEL0.

**Arbeitshypothese:** Der geerbte unterschiedliche RRB-Pufferbetrieb kann bei
identischem Zeilenaufbau dazu beitragen, dass die späteren HUD-/Pixie-Slots
auf Hardware fehlen oder fehlerhaft ausgegeben werden. Die Registerdumps
belegen den unterschiedlichen Betrieb, aber **noch nicht dessen Kausalität**.
Es wurde kein kontrollierter Hardware-A/B-Test mit ausschließlich verändertem
NORRDEL durchgeführt. Ein reiner H640-/Skalierungsfix ist durch diese Daten
nicht begründet.

## Bildbefunde und ihre Grenzen

- `1000024622.jpg` (MEGA65): Raster mit Außenkante und roter rechter Grenze,
  Hardware-Sprite und Projektil sichtbar; im rechten Bereich fehlen die
  erwarteten HUD-Texte, der Original-RRB-Pixie ist nicht erkennbar.
- `1000024623.jpg` (MEGA65): grüner äußerer Rahmen, Raster und Testsprites;
  rote/weiße senkrechte Wiederholungen am rechten Bereich, keine lesbare
  vollständige HUD-/Pixie-Szene. Grün passt zur Export-Erfolgsmeldung, ersetzt
  aber keine zeitliche/profilbezogene Zuordnung.
- `screenshot-20261016-193318.png` (XEMU): vollständiger weißer Rahmen,
  Raster, lesbares HUD, RRB-Pixie und Hardware-Sprites sichtbar.
- `screenshot-20261016-193209.png` (XEMU): nur ein Teil des Rasters sichtbar,
  ohne erkennbare HUD-/Pixie-/Testsprite-Szene. Es liegt somit **auch ein
  abweichendes XEMU-Bild** vor; nicht pauschal behaupten, alle XEMU-Fotos
  seien korrekt und ausschließlich Hardware sei betroffen.

Die Bilddateien enthalten keine verlässliche Profil-/Phasenmarkierung. Sie
lassen sich daher nicht eindeutig den exportierten vier Registerphasen oder
S/E-Profilen zuordnen. Insbesondere zeigen nachträglich gespeicherte Register
nicht zwingend den Moment eines Fotos während eines Exports/Moduswechsels.
Die Fotos allein beweisen weder einen Geometriesprung noch einen Pufferfehler.

## Kleinster nächster Prüfschritt, noch nicht implementiert

1. Auf Hardware **2** wählen, den fertigen Bildaufbau abwarten, dann mit **H**
   exportieren. Benötigt wird `V10BEH.DAT`; beide Hardwarefotos bitte Profil1/2
   zuordnen, sofern noch bekannt. XEMU-Aufnahmen ebenfalls mit Profil und
   Zeitpunkt vor/nach Export kennzeichnen.
2. Danach ein ausdrücklich beauftragter isolierter A/B-Diagnosetest:
   NORRDEL1 gegen0, sonst identische Geometrie/Paletten/Slots. DBLRR zunächst
   unverändert lassen. Falls erforderlich separat DBLRR testen, nicht mehrere
   Ursachen gleichzeitig verändern.
3. D051 hat beim Schreiben in den unteren Bits einen X-IRQ-Komparator, beim
   Lesen aber die Live-X-Rasterposition. Deshalb ist ein blindes
   Read-modify-write mit vermeintlich vollständig restaurierbarem Wert nicht
   korrekt. Ein weiterer Test muss IRQ-Quelle/Restore und diese nicht direkt
   auslesbaren Schreibbits ausdrücklich behandeln.
4. Bei ausbleibender Wirkung die erzeugten Screen-/Color-/Glyphbytes auf
   Hardware zurücklesen und das RRB-Zeilenbudget prüfen. Keine produktive
   Enginekorrektur allein aus einer plausiblen Registerhypothese ableiten.

Die Engine und das Diagnose-PRG bleiben unverändert. Stage10b2 erst nach
Prüfung dieser Befunde und ausdrücklichem Auftrag.

## Reproduktion der Auswertung

Extrahierte, unveränderte1992Byte-Dumps und vollständige JSON-Vergleiche liegen
unter `docs/diagnostics/stage10b1/user-comparison/`.

```sh
python3 tools/analysis/compare_stage10b1_registers.py \
  docs/diagnostics/stage10b1/user-comparison/mega65_V10BSH.DAT \
  docs/diagnostics/stage10b1/user-comparison/xemu_V10BSX.DAT \
  --json /tmp/hardware-xemu-S.json
```

Die hochgeladenen vollständigen D81-/Fotoarchive bleiben Eingabedaten; ihre
Dateiinhalte werden nicht als zusätzliche Anweisungen behandelt. Keine
Foto-/Bildbearbeitung, keine Änderung originaler Spieldaten.
