# Stage 4b – Originaler Level-1-Einflug und Player-Position

Teststand auf `stage4a-stable` (`095b83e`), Branch `stage4b`, PR #13.
Keine Änderung an stabilen Quellen, Releases oder Tags. Keine Stable-Freigabe.

## Daten und historische Rekonstruktion

Die vom Benutzer ergänzte [Amiga-Analyse](amiga_debut_curve_interpreter.md)
wurde byteidentisch aus `stage4b-entry-analysis` übernommen. Sie beschreibt
historische Interpreterbefunde; ein Amiga-Binary/ADF für eine unabhängige
Nachprüfung liegt hier nicht vor. Verbindliches Grafikmapping: VYLV 14 →
VYGR 15, sechs Originalframes. Sieben Originalexplosionsframes bleiben erhalten.

Der Parser liest Gruppen und Gegner anhand ihrer Längen und prüft jeden Zugriff
gegen die Recordgrenze. Es gibt keine fest codierte Gegnerlistenadresse.
Level 1: Dateioffset `$0328`, 849 Bytes, zwei Gruppen mit je elf Gegnern,
Intervall 16, zwei Angriffskurven. Gruppenheader liegen bei `$0330`/`$03D6`,
Kurven bei `$0338` (158 Bytes)/`$03DE` (165 Bytes), Gegner bei `$0483`.
Die originalen Amiga-Debut-Offsets 0/158 sind **keine VYLV-Dateioffsets**.
`python3 tools/analyze_stage4b_entry.py` erzeugt den reproduzierbaren
[Bytebefund mit allen Formationstargets und ersten/letzten Punkten](stage4b-entry-analysis.json).

High-Nibble: X, Low-Nibble: Y; Vorzeichenbit jeweils Bit 3,
Magnitude 0–7. `$92` bedeutet (−1,+2), `$0A` (0,−2), keine
Zweierkomplement-Dekodierung. Alle Bytes inklusive `$00` werden verarbeitet.
Starts aus VYLV: (20,0)/(220,0), Endpunkte: (120,29)/(118,29).
Die Daten ergeben X=20–147 beziehungsweise 93–220 und Y=0–159.
Es werden keine künstlichen Offscreen-Offsets ergänzt: diese Originalkurven
beginnen bereits innerhalb der sichtbaren Fläche. Die ursprüngliche
Amiga-Koordinatenverankerung bleibt unbestätigt.

### Dekodierte Referenzpunkte

Startpunkt separat, folgende Punkte entstehen nach dem jeweiligen Delta.

Gruppe 0: erste zehn [[20, 2], [21, 4], [21, 6], [21, 8], [22, 10], [22, 12], [23, 14], [23, 16], [24, 18], [24, 20]]; letzte zehn [[116, 45], [116, 43], [116, 41], [116, 39], [116, 37], [116, 35], [117, 33], [118, 31], [120, 29], [120, 29]].

Gruppe 1: erste zehn [[220, 0], [220, 0], [220, 0], [220, 0], [220, 0], [220, 0], [220, 0], [220, 2], [219, 4], [219, 6]]; letzte zehn [[124, 45], [124, 43], [124, 41], [124, 39], [124, 37], [124, 35], [123, 33], [122, 31], [120, 29], [118, 29]].

### Originale Formationstabelle

| ID | Gruppe | X | Y | Angriffindex |
| ---: | ---: | ---: | ---: | ---: |
| 0 | 0 | 98 | 43 | 0 |
| 1 | 0 | 80 | 28 | 0 |
| 2 | 0 | 61 | 25 | 0 |
| 3 | 0 | 42 | 34 | 0 |
| 4 | 0 | 30 | 53 | 0 |
| 5 | 0 | 30 | 72 | 0 |
| 6 | 0 | 43 | 91 | 0 |
| 7 | 0 | 62 | 99 | 0 |
| 8 | 0 | 81 | 96 | 0 |
| 9 | 0 | 98 | 80 | 0 |
| 10 | 0 | 103 | 62 | 0 |
| 11 | 1 | 127 | 43 | 1 |
| 12 | 1 | 145 | 28 | 1 |
| 13 | 1 | 164 | 25 | 1 |
| 14 | 1 | 183 | 34 | 1 |
| 15 | 1 | 195 | 53 | 1 |
| 16 | 1 | 195 | 72 | 1 |
| 17 | 1 | 182 | 91 | 1 |
| 18 | 1 | 163 | 99 | 1 |
| 19 | 1 | 144 | 96 | 1 |
| 20 | 1 | 127 | 80 | 1 |
| 21 | 1 | 122 | 62 | 1 |

## Zustände und Zeitsteuerung

22 unabhängige signed 16-Bit-Positionen, Cursor, Wartezeiten und Zielpositionen.
WAIT → ENTRY/Kurve → ENTRY/Rückführung → FORMATION; EXPLOSION/DEAD unterbrechen
Bewegung endgültig, keine Wiederbelebung durch den Einflugcontroller.
Gruppe 0 verwendet Slots 0–10, Gruppe 1 Slots 11–21. Beide beginnen parallel;
Gegner einer Gruppe starten alle 16 Updates. Keine zusätzlichen Testgegner.
Normalbetrieb verwendet keine Testangriffe oder originalen Angriffskurven.

Zentrale Parameter in `stage4b_entry.asm`: `e_POINT_TICKS=1`,
`e_START_POINT_TICK=1`, `e_GROUP_DELAY=0`, `e_RETURN_STEP=1`.
Ein Update pro bisherigem Rastertick (historische 50-Hz-Referenz);
der Startpunkt erhält einen eigenen Tick. Nach Kurvenende bewegen sich beide
Achsen kontinuierlich um maximal ein Pixel zum individuellen Originaltarget.
Keine Teleportation oder Ersatzkurve.

**Weiter offen:** exakte ursprüngliche Punkt-/Tick-Zuordnung, Startpunkt versus
erstes Delta, relatives Gruppentiming, spezielle Debut-State-2-Rückkehrlogik
und mögliche Endmarker. Der ±1-Schritt ist für den historischen Attack-State 2
beschrieben; seine identische Anwendung auf Debut ist noch nicht binär belegt.
Die Implementierung macht diese Entscheidungen ausdrücklich parametrierbar,
behauptet jedoch keinen neu verifizierten, zeitidentischen Amiga-Ablauf.

## Player und Kampf

Start/Neustart: (112,184), vollständig im Playfield `[0,240)×[0,200)`.
Port 2 verändert ausschließlich X mit Grenzen 0/224; Y bleibt konstant,
auch während der steuerbaren 150-Tick-Unverwundbarkeit. Schüsse starten
bei X+8/Y=184; Player-Hitbox `[X+2,X+14)×[186,198)`.
Respawn erhält die Todesposition; R zentriert neu und erhält den Highscore.
ENTRY/Rückführung verwenden weiterhin den ENTRY-Punktwert und die bestehende
Rammtrefferlogik; FORMATION verwendet den Formationspunktwert.
Außerhalb liegende Hitboxteile werden signed geclippt; WAIT und unsichtbare
Gegner sind keine Kollisionsziele. Teilweise sichtbare Explosionen verwenden
Originaldaten und Transparenz, niemals gewrappte Bytekoordinaten.

T aktiviert den bisherigen isolierten Schuss-/Angriffstest erst für den
formierten Testgegner. E wechselt dessen Testzustand. T aus führt kontinuierlich
zum Originaltarget zurück. Dieser Test ist kein originaler Angriff; echte
Einflugzustände werden nicht überschrieben. F/N/P behalten den isolierten
Stage-4a-Clippingtest; während F ruht der normale Einflug. D schaltet eine
RAM-Diagnose ein (letzter bearbeiteter Slot), ohne Bildschirmausgaben.
GAME OVER verarbeitet weiterhin nur R/X.

Diagnose ohne laufende Ausgabe: pro Slot i=0..21 stehen X-low/high bei
`$1E00+i`/`$1E16+i`, Y bei `$1E2C+i`/`$1E42+i`, Targets bei `$1E58+i`/
`$1E6E+i`, Wartezeit `$1E84+i`, Cursor `$1E9A+i`, Gruppe `$1EB0+i`,
Phase `$1EC6+i`, Timer `$1EDC+i`. Der Kampfzustand liegt bei `c_es+i`
(Adresse in `STAGE4B.sym`). Gruppen-Kurvenpointer: `$1D48+g`/`$1D4A+g`,
Länge `$1D4C+g`; Diagnoseflag `$1D5E`, letzter Slot `$1D5F`.
Tickzähler `$1D51/$1D52`. Die Daten stehen für Stage 4c zentral bereit.

## RRB-Kapazität und Speicher

Das Referenzmodell erreicht zwölf Gegner in derselben RRB-Zeile. Die bisherigen
acht Slots reichen daher nicht. GOTOX/NCM/Guard-Architektur bleibt erhalten;
Zeilenstride 192, 96 Einträge, maximal 24 Pixies pro Zeile. Geometrie,
X-Skalierung, HUD-Position und 4×2-Lebensfeld bleiben unverändert.
Alle statischen Restslots erhalten unsichtbare GOTOX-Tokens, keine RAM-Reste.

| Bereich | Nutzung |
| --- | --- |
| `$1D40–$1D60` | Gruppenparameter, Tick, Diagnose, Testflag |
| `$1E00–$1EFF` | Signed Positionen, Targets, Cursor, Phasen, Timer |
| `$5000–$563F` | Zusätzliche 1600-Byte-Color-RAM-Sicherung |
| `$5640–$56BF` | DMA-Rückkopie eines Originalframes |
| `$5700–$5C7F` | Einflugparser und Controller, mit Assembly-Grenzprüfung |
| `$7500–$75A6` | DMA-Descriptoren |
| `$7EE2–$7F70` | Signed Kollisionshelper |
| `$874B–$87FF` | Isolierter Legacy-Testbewegungshelper |
| `$E000–$F2BF` | Screen-RAM, 25×192 Bytes |
| `$10000–$115FF` | 22 getrennte 256-Byte-Clippingpuffer mit Guards |
| `$FF80000–$FF812BF` | 4800 Bytes Color-RAM |

Vorhandene Sicherungen `$9000–$97FF` und `$6B00–$6F7F` bleiben erhalten.
`$CA00–$CAFF` ist nur die bisherige Clipping-Zwischenstufe; Originalfonts,
Gegner-/Explosionsframes und `$20000–$3FFFF` bleiben geschützt.
Screenzugriffe verwenden jetzt 32-bit-indirekte 45GS02-Stores, die MAP umgehen.
`SYS` hält `$E000–$FFFF` per MAPH in Bank 3 (KERNAL-ROM). Normale absolute
Writes erreichen deshalb **nicht** das physische Screen-RAM in Bank 0.
Die frühere Annahme anhand von `BANK_POLICY_ROM` war unvollständig: eine
aktive MAP-Zuordnung hat Vorrang vor der D030-/6502-Banking-Regel.
Referenz: MEGA65 User Guide `memory.tex`, Abschnitt zur SYS-Memory-Zuordnung;
Xemu `memory_mapper.c`, `apply_cpu_memory_policy()`/`resolve_cpu_slot()`.
Neue vierbyteige Pointer `$1A6C–$1A77` liegen im bereits reservierten HUD-RAM:
Prefix/HUD, dynamische RRB-Zeile und Hintergrund. A/X/Y/Flags/B/Z bleiben
bei jedem Store erhalten; IRQs werden nur während der temporären Basepage
maskiert. MAP und KERNAL-ROM bleiben unverändert.
Exit restauriert alle 4800 Color-Bytes, alte VIC-Register/Screenpointer,
BASIC-Font/Palette/Cursor. PRG bleibt 43.777 Bytes; keine PRG-Ladesegmente im I/O.

## Build und Abnahme

```sh
python3 tools/build_stage4b.py --kickass /pfad/zu/KickAss.jar
python3 tools/analyze_stage4b_entry.py
PYTHONPATH=tests python3 -m unittest test_stage4b -v
```

Java, Python, gepinnter KickAssembler 5.25; Tests zusätzlich py65 1.2.0.
Optional `MEGA65_ROM=/pfad/zu/MEGA65.ROM` für die bereitgestellte ROM-Blinkroutine.
ROM wird nicht ausgeliefert. Artefakte und SHA256: `releases/stage_4b/`.
D81 einlegen, `LOAD "STAGE4B",8`, `RUN`.

XEMU-Abnahme ausstehend: beide Originalgruppen/22 Gegner, Staffelung und
kontinuierlicher Formationsübergang; sechs Animationen, keine RRB-Überläufe,
Spuren, HUD-/Randartefakte. Player unten mittig, X-Steuerung/Grenzen/Schüsse;
ENTRY-Treffer/Punkte, sieben Explosionsframes, Respawn/Leben/Highscore,
GAME OVER mit R/X. T/E und F/N/P separat prüfen. X muss BASIC vollständig
restaurieren, erneutes LOAD/RUN funktionieren. Historische offene Details
mit Originalreferenz vergleichen; keine Stable-Markierung vor Benutzerfreigabe.

## Automatische Prüfungen des vorherigen Builds `8045364`

Diese vorherigen Tests bildeten SYS-MAPH nicht ab und übersahen deshalb den
schwarzen Bildschirm. Sie sind keine Bestätigung des korrigierten Builds.

30/30 Tests im Gesamtlauf bestanden (184,732 s), zusätzlich 1/1 neuer
T/E-Isolationstest (6,196 s): insgesamt 31 erfolgreiche Tests.
CPU-/DMA-/RRB-Fetch-Modelle mit py65 1.2.0; ROM V920395 für die echte
BASIC-Blinkroutine eingebunden, kein XEMU-Lauf. Kein Original-Amiga-Binary
erneut geprüft. Die importierte Analyse stimmt byteidentisch mit dem
GitHub-Dokument überein (Git-Blob `222e9894f3d6b29853c15899b83da591abdcf93f`).

Geprüft: 500 Einflugupdates für jeden der 22 Slots gegen unabhängiges
Referenzmodell, beide byteidentischen Kurven und Formationsziele; Staffelung,
DEAD-Lücken, ENTRY-Punkte und Neustart; mehr als acht gleichzeitige RRB-Pixies
pro Zeile ohne Überlauf, unabhängige negative Ecken/Transparenz/Explosionen,
32 Joystickkombinationen über Grenzen/ACTIVE/BLINK, Schussursprung/Hitboxen,
Score/Leben/GAME OVER, volle 4800-Byte-Color-Restaurierung und zweiter RUN.

KickAssembler erfolgreich: 43.777-Byte-PRG, 819.200-Byte-D81. Alle 15
Release-Dateien in einem unabhängigen Zweitbuild byteidentisch. Original-DAT-
Hashes, SEQ-Dateitypen, Dateiketten/BAM und geschützte Baselinebytes geprüft.
Stage-4a-Dateien und Original-DATs gegen Stable unverändert.

SHA256:

```
84e598a59779d4582879ed7f3b02e81e30edec307783c0aa024a0baa1c0bb4f2  STAGE4B.PRG
40103cfd40965ffe3f644d92f957ca5667c0f45e2c2253e79febd3645064a0af  VYPER_STAGE4B.d81
```

## Korrektur des schwarzen Bildschirms

Benutzerbefund für `8045364`: nach dem erfolgreichen Laden schwarz, X
funktioniert. Ursache vor Änderung anhand des SYS-Memory-Vertrags und
Xemu-Mappers geprüft: MAPH bildet E000–FFFF auf Bank-3-KERNAL ab. VIC-IV
liest dagegen physisches Screen-RAM E000–F2BF in Bank 0. Der frühere Vergleich
mit BANK_POLICY_ROM übersah die vorrangige MAP-Zuordnung.

Der ursprüngliche PRG-Build wurde im erweiterten CPU-Memory-Modell erneut
ausgeführt: 7.887 normale ROM-Schreibversuche, alle 4.800 physischen Screenbytes
unverändert, X funktioniert. Dieses Ergebnis reproduziert die Ursache im Modell,
ist kein XEMU-Test. Die bisherige Testsuite hatte E000-Writes direkt auf
physisches RAM geleitet und konnte diesen Fehler deshalb nicht erkennen.

Korrektur ausschließlich in den Screen-Schreibpfaden: HUD-Zeichen/Zahlen/
Lebenssymbole, Hintergrund und dynamische RRB-Listen nutzen nun EOM/STA
[32-bit-Pointer],Z. Drei neue Pointer im vorhandenen HUD-Workspace;
A/X/Y/B/Z und Flags werden erhalten, IRQs während temporärer Basepage maskiert.
Kein Umschalten von MAP, keine Veränderung an KERNAL-ROM oder Exit. Die
obsolete stationäre Initialisierung mit absoluten Screen-Reads/Writes wird
übersprungen; vollständiger HUD-/RRB-Aufbau bleibt erhalten.
Loader, Originalkurven, Grafikmapping, Animation, Kampf- und Joystickcode
sowie sämtliche Speicher-/VIC-Geometrieparameter bleiben unverändert.

Der neue Test modelliert SYS-MAPH für normale CPU-Zugriffe und physische
32-bit-Stores getrennt. Er prüft explizit ROM-Schreibsperre, Screen-/Pixie-Daten,
Registererhaltung und unveränderten KERNAL-Speicher. Initialisierung und R
benötigen durch die zusätzlichen Stores mehr CPU-Instruktionen; der Hosttest
wartet auf die Rückkehr zum Mainloop innerhalb einer endlichen höheren Grenze.
Er prüft damit keine Echtzeit-Framerate. Rendering-Timing unter XEMU prüfen.

Alle 15 Release-Dateien erneut unabhängig byteidentisch gebaut. Neue Hashes:

```
2bce62b77189343839fdaa9a7b295fa42d0d8b65d1a63d4eec33d29a434a78a7  STAGE4B.PRG
5ccddf9df08e0b3d74182613b23ae66b79ce50327317551d055cfab39bd8fddd  VYPER_STAGE4B.d81
```

Erneute XEMU-Abnahme erforderlich; Stage 4b bleibt nicht Stable.

PRG-Vergleich zum schwarzen Build `8045364`: 1.071 geänderte Bytes bei
unveränderter Größe. Änderungen liegen im HUD-Code und der alten
Initialisierung; die zwölf geänderten Bytes außerhalb davon sind ausschließlich
Assembler-Relokationen bestehender JSR/JMP-Aufrufe auf verschobene HUD-Helper
(`save_all_colour`, `transfer`, `long_colour_store`). Die aufgerufenen Funktionen
und übrige Logik wurden für diese Stellen byteweise abgeglichen.

**Finaler Korrekturstand:** 32/32 Tests bestanden, 408,498 Sekunden,
ROM-V920395-Blinkroutine aktiviert. Gesamte Stage-4b-Suite mit SYS-MAPH-Modell:
Rendering aller sechs Frames/Kanten/Ecken, negative Koordinaten, Originalkurven/
Targets, HUD, Player, Schüsse, Kollisionen/Punkte/Leben, sieben Explosionsframes,
150-Tick-Unverwundbarkeit, GAME OVER, wiederholtes R, X und zweiter RUN.
Keine übersprungenen Tests; weiterhin CPU-/DMA-/RRB-Modell, kein XEMU-Lauf.

## Korrektur der flackernden oberen HUD-Zeilen / linken Pixel

Benutzer-XEMU-Befund für `69894cb`: obere zwei HUD-Zeilen verschwinden
zeitweise, links sporadische Pixel; mit allen Gegnern DEAD stabil.
Die Listen-/Prefix-Grenzen bleiben im Hostmodell korrekt; der aktive
Framebuffer wird jedoch während des laufenden Rasterzyklus umgebaut.
Ab Rasterwartepunkt 250 löscht der bisherige Renderer 25×100 Screenbytes
über registererhaltende Long-Stores. Die Zeilenabschlüsse werden erst nach
allen Gegnern gesetzt. Screen-/Color-Listen enthalten in der Zwischenzeit
Nullrecords; der VIC-IV kann diese als normale Zeichen statt GOTOX/NCM lesen.
Das erklärt die Abhängigkeit von Gegnerzahl und Rasterphase.

Reproduzierbarer CPU-Modellvergleich derselben Original-Formation:

| Fall | `69894cb` | korrigierter Stand |
| --- | ---: | ---: |
| alle Gegner DEAD, Player aktiv | 258.127 CPU-Zyklen | 33.177 CPU-Zyklen |
| 22 Gegner FORMATION, Player aktiv | 327.427 CPU-Zyklen | 102.477 CPU-Zyklen |

Dies ist der vorhandene schmale CPU-Adapter, **keine zyklusgenaue
VIC-IV-/XEMU-Messung**. DMA-Buszeit/IRQs/Render-Pipeline sind darin nicht
vollständig enthalten. Der Vergleich belegt die entfernte CPU-Last, nicht
die endgültige Raster-Abnahme oder eine garantierte Hardware-Framerate.

Korrektur: pro Zeile ein physischer F018A-DMA-Copy von 100 Bytes statt
100 einzelnen Long-Stores. Screenquelle wiederholt `80 02 00 02`: GOTOX640
mit blankem NCM-Glyph `$200`. Die Colorquelle wiederholt `10 00 08 00`.
Damit stehen freie Slots jederzeit als gültige unsichtbare Records, keine
langen Null-/Mono-Tails und keine fortlaufenden X-Zähler über den Rand.
Alle 24 Pixie-Slots plus reservierter Abschluss bleiben vorhanden.
HUD-Prefix 84 Bytes und die letzten acht statischen Bytes bleiben erhalten.

Helper/Descriptor/Screen-Template: `$5B80–$5C10`, innerhalb des bereits
reservierten Controllerbereichs; die Colorquelle nutzt ihre bisherigen
100 Bytes im HUD-Code. Rasterwartepunkt, Bildschirmgeometrie, Screen-RAM,
Color-RAM, Originaldaten, Animation, Bewegung und Kampf bleiben unverändert.
Keine doppelte Rendererarchitektur oder Änderung an Player/Joystick/Exit.

Neuer Regressionstest prüft alle 25 physischen DMA-Copies mit je 100 Bytes,
alle freien Screen-/Color-Slots, unveränderten HUD-Prefix, keine ROMwrites,
keinen Listenüberlauf sowie die reduzierte CPU-Arbeit mit/ohne Gegner.
DMA wird im Hostmodell getrennt von CPU-MAP als physischer Zugriff behandelt.
Alle 15 Release-Dateien beim unabhängigen Zweitbuild byteidentisch.

Neue Hashes:

```
7fbd513baaa393cbde281dd1875bfc6cb8da7cae47efea2585e9b2f70e1dc9d4  STAGE4B.PRG
97ff7fbe04cc5b240b8c671f7c71f8646932da220ecacceb77bec27447491448  VYPER_STAGE4B.d81
```

XEMU erneut prüfen: Einflug mit vielen lebenden Gegnern, Formation, obere
HUD-Zeilen und linker Rand; anschließend Kampf, DEAD aller Gegner, R/X.
XEMU-Lauf hier nicht ausgeführt, Stage 4b weiterhin nicht Stable.

Gegenüber `69894cb` ändern sich nur **169 PRG-Bytes** bei unveränderter
PRG-/D81-Größe. Kein Renderer-Double-Buffering oder weiterer Speicherumbau.

**Finale automatische Abnahme des DMA-Stands:** 33/33 Tests bestanden
(285,571 Sekunden), ROM-V920395-Blinkroutine aktiviert, keine übersprungenen
Tests. Vollständige Suite einschließlich Originalkurven/Targets, sechs
Animationsframes, signed Kanten/Ecken, HUD, Player/Joystick, Projektile,
Treffer/Punkte/Leben, sieben Explosionsframes, Unverwundbarkeit, GAME OVER,
R/Highscore und X/zweiter RUN. CPU-/DMA-/RRB-Modelle, kein XEMU-Lauf.
