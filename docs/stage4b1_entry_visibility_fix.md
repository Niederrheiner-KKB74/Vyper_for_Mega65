# Stage 4b-1 – Sichtbarkeit beim Einflug (Issue #14)

Branch `stage4b-1`, aus `stage4b-stable` (Commit
`f4c6f5e8c875e3ad7dd87fd016b9c65b77db694e`). Stage 4b und seine
Release-Dateien bleiben unverändert. **Stage 4b-1 ist vom Benutzer unter XEMU als Stable bestätigt.**
Referenz `stage4b1-stable`; bestätigter Programmcommit `531c745971ae95ad15c723b46c97b1f34ee3cf3c`.
Die frühere Testanleitung unten bleibt zur Reproduktion erhalten; die
Benutzerbestätigung ersetzt die offenen Abnahmehinweise. Quellen und
Release-Dateien werden durch die Stable-Markierung nicht verändert.

## Nachgewiesene Ursache

WAIT (`c_es=5`) wurde bereits in Stage 4b sowohl im Renderer als auch bei
Kollisionen ausgeschlossen. Der sichtbare Stillstand entsteht in ENTRY
(`c_es=2`, `e_phase=1`), nicht während des individuellen Wartetimers.
Der 50-Hz-Controller aktiviert beide Gruppen parallel, elf Gegner je Gruppe,
mit 16 Updates Abstand. Der Aktivierungstick setzt die Originalstartposition
und verbraucht noch keinen Kurvenpunkt (`e_START_POINT_TICK=1`).

| Gruppe | Originalstart | Kurvenlänge | Anfang | Erste Bewegung des ersten Gegners |
|---|---|---|---|---|
| links | (20,0) | 158 Bytes | `$02,$12,$02,…` | Update 2: (20,2) |
| rechts | (220,0) | 165 Bytes | sieben `$00`, dann `$02,$92,…` | Update 9: (220,2) |

Updates sind ab 1 gezählt, erster Aufruf von `e_objects` nach Initialisierung.
Für Gegnerordinal k kommen jeweils 16*k Updates hinzu. Die 16×16-Pixies
liegen bereits an beiden Startpositionen vollständig im Playfield. Rechts
wurde deshalb bei Updates 1–8 dasselbe Pixie sichtbar gezeichnet: ein
Starttick plus sieben originale Null-Deltas. VYLV-Kurven wurden direkt aus
dem variabel geparsten Level-1-Record geprüft; keine Ersatzkurve verwendet.

## Kleine, gemeinsame Sichtbarkeitskorrektur

Ein eigenes Flag pro Gegner wird beim Neustart gelöscht. Nach der bestehenden
sign-magnitude-Nibble-Dekodierung setzt ein nichtnulles X- oder Y-Delta das
Flag dauerhaft. Keine Kurvenbytes werden übersprungen; sämtliche Startticks,
Null-Deltas, Timer und Koordinatenupdates laufen unverändert weiter.
Der gemeinsame Helper `e_is_visible` unterdrückt DEAD, WAIT und den unbewegten
ENTRY-Vorlauf. Renderer und Kollisionsbox benutzen denselben Helper.
Sobald die erste Bewegung stattfindet, wird das Pixie in derselben Updatephase
freigegeben. Spätere Null-Deltas blenden es nicht wieder aus. Rückkehr zur
Formation, Formation, Angriff und sichtbare Explosionen bleiben freigegeben.
Unsichtbare Gegner erzeugen eine leere Kollisionsbox: weder Projektile noch
Rammen können sie treffen. Der vorhandene physische DMA-Clear entfernt
unbenutzte RRB-Einträge weiterhin vor jedem Listenaufbau.

Links wird ausschließlich der bisher stehende Starttick unsichtbar; die erste
Bewegung und alle folgenden sichtbaren Kurvenpunkte bleiben zu denselben
Updates erhalten. Rechts verschwinden die acht stehenden Anfangsupdates.
ENTRY als Bewegungszustand beginnt weiterhin zu denselben Updates; seine
Sichtbarkeit/Interaktivität beginnt jetzt erst mit dem ersten Bewegungsdelta.
Dies ist bewusst eine Sichtbarkeitskorrektur, keine Änderung der Zeitbasis.

## Zeit- und Positionsvergleich

Der automatische 500-Update-Vergleich prüft für alle 22 Gegner nach jedem
Update signed X/Y, Zustand, Phase und Kurvenindex gegen das unveränderte
Stage-4b-Bewegungsmodell. Alle ursprünglichen Kurvenpunkte einschließlich
Null-Deltas werden durchlaufen. Die ersten Formationsupdates sind unverändert:

| Gruppe | Gegnerordinal 0 bis 10: Formationsupdate |
|---|---|
| links | 181, 215, 250, 285, 313, 329, 332, 341, 354, 354, 352 |
| rechts | 180, 209, 244, 279, 307, 323, 326, 348, 361, 361, 359 |

Kein Eingriff in Startpositionen, Formationsziele, 50-Hz-Takt, Gruppenstarts,
Animation, Schüsse, Mapping VYLV14→VYGR15 oder Originaldaten. Playfield bleibt
`[0,240) × [0,200)`, 25 RRB-Zeilen und 24 Slots pro Zeile. Player bleibt
(112,184) beim Start, X-only-Steuerung und Begrenzung 0–224.

## Speicher und Basisschutz

Neu: 23 Flagbytes `$1D64–$1D7A`, zuvor freie Lücke nach den Gruppenvariablen
`$1D40–$1D60`; Codehelper `$5C20–$5C49` innerhalb der bereits reservierten
Controllerlücke vor `$5C80`. DMA-Helper `$5B80–$5C10` bleibt unverändert.
Die drei zusätzlichen Initialisierungsbytes verschieben lokale Controllerlabels;
vorhandene JSR/JMP-Aufrufer werden entsprechend neu assembliert. Kein neuer
DMA-Descriptor, Puffer, Zero-Page-Slot oder Zugriff auf ROM als RAM.

Der Builder prüft das stabile PRG gegen SHA256
`7fbd513baaa393cbde281dd1875bfc6cb8da7cae47efea2585e9b2f70e1dc9d4`.
Er erlaubt ausschließlich Controller-/Sichtbarkeitscode, den bestehenden
Kollisionshelper und symbolverifizierte JSR/JMP-Neuverweise. PRG-Größe bleibt
43.777 Bytes; 1.102 Bytepositionen unterscheiden sich (überwiegend durch
verschobenen Controllercode). Loader, HUD, Grafik-/Cropdaten und Kampfmodule
sind außerhalb dieser eng geprüften Aufrufer unverändert.

## Reproduzierbarer Build und automatische Prüfung

KickAssembler 5.25 (offizielle, im Builder gepinnte JAR-Prüfsumme), Java und
Python 3; vorhandene Originalassets und Importarchive werden benötigt.

```sh
python3 tools/build_stage4b1.py --kickass /pfad/KickAss.jar
PYTHONPATH=tools:tests:/pfad/test-deps MEGA65_ROM=/pfad/MEGA65.ROM \
  python3 -m unittest test_stage4b1
```

Testabhängigkeit: `python3 -m pip install -r tests/requirements-stage3b1.txt`
(py65 1.2.0), wie bei Stage 4b. Die Suite
führt assemblierte Instruktionen im projektspezifischen CPU-/DMA-/SYS-MAP-
Modell aus und prüft aus den realen RRB-Records rekonstruierte Pixel.
Zusätzliche Tests prüfen die ersten Bewegungsupdates aller 22 Slots, unsichtbare
WAIT-/ENTRY-Kollisionen, gerenderte Pixel ohne stehende Startpixies und ohne
stale Einträge sowie Flagreset. Regressionen umfassen Loader-Verifikation,
Originalgrafiken, Clipping über alle Kanten/Y=0–199, HUD, Combat, Animation,
Score/Leben/Respawn, R-Neustart, ROM-Cursor/BASIC-Exit und erneuten RUN.
Dies ersetzt keine Raster-/XEMU-Abnahme.

Ergebnis am 11.10.2026: **36 unterschiedliche Prüfungen erfolgreich**.
Der erste Lauf mit 35 Tests dauerte 309,525 s: 34 bestanden; der Disk-Test
enthielt noch den alten erwarteten Programmnamen `STAGE4B`. Nach Korrektur
auf `STAGE4B1` bestand dieser Test separat (0,006 s). Der zusätzliche
RRB-Pixel-/stale-entry-Test bestand ebenfalls (7,902 s). Keine Änderung am
Programm war dafür nötig. Die aktuelle Suite enthält alle 36 Tests.

Ein unabhängiger Zweitbuild liefert alle 15 Release-Dateien byteidentisch.
Das D81 enthält `STAGE4B1` als PRG und originale `VYLV.DAT`/`VYGR.DAT` als SEQ;
Dateiketten und vollständige Inhalte werden durch den Builder geprüft.

## XEMU-Abnahme durch den Benutzer (bestätigt)

D81: `releases/stage_4b_1/VYPER_STAGE4B1.d81`, 819.200 Bytes.
ROM V920395, BASIC 80×25 wie bei der stabilen Referenz:

```basic
LOAD "STAGE4B1",8
RUN
```

Mit Stage 4b vergleichen: Rechts oben erscheint kein stehendes Pixie mehr;
links beginnt die sichtbare Bewegung unverändert. Beide Gruppen müssen dieselben
Wege und Formationsplätze erreichen. HUD/obere Zeilen dürfen nicht flackern;
Y=0–199 und Randclipping müssen erhalten bleiben. Bewegende ENTRY-Gegner
abschießen, Score/Explosionen prüfen; Joystick Port 2, Leben, steuerbaren
unverwundbaren Respawn, GAME OVER/R, X und erneutes Laden/RUN testen.

Kein XEMU- oder Hardwaretest durch Codex behauptet. Offene Grenzen der ursprünglichen
Amiga-Zeit-/Debut-Rekonstruktion aus Stage 4b bleiben unverändert. Die ausdrückliche Benutzerbestätigung
liegt vor: Der Einflug sieht korrekt aus, Stage 4b-1 darf als Stable markiert werden.
