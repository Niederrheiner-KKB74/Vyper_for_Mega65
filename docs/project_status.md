# Projektstand – 2026-10-10

## Bestätigt durch XEMU-Test des Benutzers

**Stage 2ja:** stabile Spielengine mit 24 animierten RRB-Pixies, Joysticksteuerung und funktionierendem RRB-Clearing. Als unveränderte Referenz erhalten.

**Stage 3a-1:** Das Lesen des `VYLV.DAT`-Headers funktioniert nach Ergänzung von `SETBNK` mit A=0, X=0 vor `SETNAM`. Ergebnis: Header VYLV, Version 1, 100 Level, READST $00.

**Stage 3b-1:** Vom Benutzer am 2026-10-10 als stabil bestätigt. Originaldateien laden und prüfen, anschließend 24 RRB-Pixies mit bisheriger Animation, Joysticksteuerung und BASIC-Rückkehr. Stabile Referenz: Git-Tag `stage3b1-stable`; PRG/D81/ASM unter `releases/stage_3b1/` bleiben unverändert.

**Stage 3a-2:** `VYLV.DAT` vollständig nach `$40000`, `VYGR.DAT` vollständig nach `$54000` geladen. DMA-Rücklesevergleiche erfolgreich. Level-1-Record per DMA nach `$7000` kopiert; Signatur geprüft. Programm kehrt zu BASIC zurück.

## Wichtige Fehlerursachen

- Ohne `SETBNK` war `READST $42` schon beim ersten `CHRIN` zu sehen.
- Der erste Stage-3a-2-Versuch schrieb in `$20000` (ROM) und meldete DMA-Vergleichsfehler $04.
- Mit `$40000` / `$54000` wurde der vollständige Test erfolgreich.

## Noch offen

- Import abgeschlossen: bereitgestellte Loader-Quellen, Binär-Assets, Build-Skripte und Releases sind in der vorbereiteten Struktur enthalten; Stage 2ja bleibt als unverändertes Archiv erhalten.
- Build-Skripte verwenden derzeit `/mnt/data`; für die Cloud-Entwicklung ist eine gesonderte Einrichtung erforderlich.
- Stage 3b-2: Am 10.10.2026 vom Benutzer einschließlich korrigiertem BASIC-Exit unter XEMU bestätigt. Stabile Referenz: `stage3b2-stable`.
- Spätere Stages: Levelstruktur, Gegnerzuordnung und Grafikframes in die Engine integrieren; Stage 3b-1 verwendet die geladenen Daten noch nicht für Gegnersteuerung.
- Keine unbestätigten Änderungen an Stage 2ja.


## Stage 3b-1 – stabile Referenz `stage3b1-stable`

Neue Quelle `src/engine/stage3b1.asm`, Artefakte `releases/stage_3b1/` und
reproduzierbarer Builder `tools/build_stage3b1.py`. Die Engine stammt ausschließlich
aus dem vorhandenen Stage-2ja-Archiv. Ihr Maschinenprogramm, Grafikdaten und
Tabellen bleiben bytegenau erhalten; nur der BASIC-SYS-Einstieg und ein vorher
ungenutzter Loader-Bereich unterscheiden sich. Stage 2ja und Stage 3a-2 unverändert.

Vor dem RRB-Start werden beide Originaldateien per SETBNK/SEQ und der bisherigen
F018A-DMA-Konfiguration geladen. Pufferkonflikte sind durch `$6800/$6900` und
Level-Kopie `$7600` vermieden. DMA-Rückvergleich, Level-Signatur und die aus den
Originaldaten abgeleiteten Bytesummen werden geprüft. Erfolgsmeldung vor der
Engine-Initialisierung; kein Text im RRB-Spielbetrieb. Keine DAT-gesteuerten Gegner.

Bestätigt: Assembly mit KickAssembler 5.25, bytegenaue Reproduktion der Baseline,
identische Artefakte aus zwei Builds, Originaldaten-SHA-256, D81-Dateiketten und
BAM sowie 12 bestandene Host-Tests des assemblierten Loaders mit KERNAL-/DMA-Modellen.
**Benutzerbestätigung:** Das Release ist am 2026-10-10 als stabil bestätigt worden.
Diese Bestätigung dokumentiert die Abnahme des Benutzers; ein eigener Emulatorlauf
durch Codex wird damit nicht behauptet. PRG, D81 und Quellkopie bleiben unverändert.
Anleitung und Regressionstest-Checkliste: [stage3b1.md](stage3b1.md).


## Stage 3b-2 – stabile Referenz `stage3b2-stable`

Neue Quelle `src/engine/stage3b2.asm`, Builder `tools/build_stage3b2.py`, PRG/D81
unter `releases/stage_3b2/`. Alle Stage-3b-1-Dateien und der stabile Tag bleiben
unverändert. Das vom Benutzer beschriebene variable Recordformat ist implementiert;
alle 100 Levels sind vollständig durchlaufen und gegen die Recordlängen geprüft.

Level 1 enthält 22 Gegner mit Grafikindex 14. Gemäß ausdrücklicher Korrektur gilt
Index 14 → Typ 12; die übrige Zuordnung bleibt 0/1 → 12, sonst 2..37 → Index minus 1.
Die Gegnerliste wird aus den Kurvenlängen ermittelt, nicht bei `$015B` fest verankert.

Die 22 Pfad-Pixies verwenden nun Typ 12 aus geladenem VYGR. Typ 12 hat einen Frame;
Joystick-/Orbit-Pixie behalten ihre sieben bisherigen Animationsframes. Bewegungs-
und Steuerlogik unverändert. Zusätzliche Grafikslots `$9800..$98FF` mit DMA-Rückvergleich.
Assembly, Originaldatenprüfung, 18 Host-Tests, Engine-Patchvergleich und D81-Prüfung
bestanden. Der Benutzer bestätigt am 10.10.2026 erfolgreiches Laden, richtige
Grafiken und korrekten Enginebetrieb unter XEMU. Der zunächst gemeldete
BASIC-Cursorfehler wurde korrigiert. Mit dem bereitgestellten ROM
V920395 ist die Ursache nachgewiesen: Engine-Objektkopie überschreibt Cursorbytes
`$111F–$1123`. Objekte und Diagnostik sind nach `$1600/$1900` verlegt; nur 53
Adressbytes im PRG ändern sich. Neues PRG/D81 gebaut, 23 Tests einschließlich
echter ROM-Cursorroutine bestanden. Anschließend bestätigt der Benutzer:
„Jetzt tritt kein Fehler beim Beenden mehr auf. Stage3b-2 ist damit bestätigt.“
Stage 3b-2 ist am 10.10.2026 als stabile Referenz `stage3b2-stable` abgenommen.
Die bestätigten ASM-/PRG-/D81-Dateien bleiben unverändert. Die XEMU-Abnahme
stammt vom Benutzer; ein eigener Emulatorlauf wird nicht behauptet.
[Exit-Untersuchung](stage3b2_exit_investigation.md).
[Build und Abnahme](stage3b2.md).

## Stage 3b-3 – stabile Referenz `stage3b3-stable`

Eigener Branch `stage3b-3`, Basis `stage3b2-stable`. Die vorhandenen Original-
Spielerdateien aus `main` sind unverändert übernommen und mit deren Assetskript
generiert. Der Joystick-Spieler nutzt die freigegebene 16×16-NCM-Grafik, linkes
Pixel im Low-Nibble, sowie Palette Bank 2. Die zwei alten Animationswege
überschreiben seine Grafik nicht mehr. Orbit, 22 Gegner, Bewegung, Joystick,
Loader, Levelparser und korrigierter BASIC-Exit bleiben erhalten.

Neue Daten bei `$3600–$36AF`, Integrationscode `$3700–$375E`; bisherige Spieler-
Glyphen `$C800–$C8FF`. Assembly, D81-Prüfung, bytegenauer Patchvergleich und acht
Stage-3b-3-Hosttests bestanden; gesamte Regression 43 Tests bestanden, Wiederholungsbuild identisch. Unveränderte Stage-3b-2-
Artefakte bleiben die stabile Referenz. PRG/D81/ASM unter `releases/stage_3b3/`.
Am 10.10.2026 vom Benutzer als stabil bestätigt; Referenz `stage3b3-stable`. [Build/Testbericht](stage3b3.md).

### Stage 3b-3: Palettenkorrektur nach XEMU-Test

Der Benutzer bestätigt die Player-Darstellung; der Exit zeigte jedoch einen
grauen BASIC-Bildschirm. Bank 3 wurde irrtümlich als frei behandelt: Ihre
ersten 16 Einträge bilden ebenfalls die BASIC-ROM-Palette. Die Auswahl ist
jetzt von `$DB` auf `$9A` (Bank 2) korrigiert; gegenüber der ersten Stage 3b-3
ändert sich nur ein PRG-Byte. Ein neuer Test reproduziert die alte Beschädigung
und prüft den Erhalt der ROM-Palette bei Start/Exit/Neustart. Die korrigierte
Fassung wurde am 10.10.2026 vom Benutzer unter XEMU als stabil bestätigt.
Die Abnahme stammt vom Benutzer; ein eigener Emulatorlauf wird nicht behauptet.
Bestätigter Programmstand: `be747701cbeee5f77af244ad3778f75088fca8a7`.
ASM, PRG und D81 bleiben bei dieser Dokumentation unverändert. [Diagnose](stage3b3_exit_palette_fix.md).

## Stage 3b-4a – stabile Referenz `stage3b4a-stable`

Branch `stage3b-4a`, Basis `stage3b3-stable`; stabile Quellen/Releases unverändert.
Der Benutzer hat die Amiga-Referenz und die breitere Ausgabe mit Spielfeldgrenze
X=240 freigegeben. H640 mit unveränderter sichtbarer Pixie-Breite; drei Original-
Lebenssymbole im 4×2-Raster, ein Pixel Abstand, vier Pixel Seitenrahmen. Player 2
inaktiv, P/S explizit inaktiv, X bleibt Exit. Scores 0000000, Level 001, Testpunkte 100/115.

Der erste XEMU-Test meldet sichtbaren BASIC-Hintergrund, Pixie-Spuren und unleserliche
Schrift. Ursache: entfernte deckende Leer-Glyphen und zu starke OR-Font-Verengung.
Die Korrektur verwendet 128-Byte-Zeilen mit vollständiger deckender Hintergrundfüllung,
HUD-Prefix und unveränderten acht dynamischen Slots. Vollständiger BASIC-Font statt
verengter Schrift; ungenutzte alte feste Animations-Screen-Stores entfernt. BASIC
wird vor dem Loader per KERNAL geleert, die Ladeanzeige hat schwarzen Hintergrund.
Alle 3200 berührten Color-RAM-Bytes und die ursprüngliche Hintergrundfarbe werden
beim Exit restauriert. Kein KERNAL-/Cursor-/Zero-Page-Eingriff; ROM-Palette bleibt erhalten.

Originaldaten/SEQ-Loader, Parser, Bewegung, Joystick und aktive Pixie-Animation
unverändert. 54 Regressionstests bestanden, einschließlich elf gezielter HUD-Tests. Diese prüfen
auch vorherige Frame-Pixel statt eines
implizit schwarzen Ausgangsbildes. Release unter `releases/stage_3b4a/` mit PRG/D81,
Quellen, reproduzierbarem Builder und Vergleich. Die abschließende Benutzerbestätigung
liegt vor; stabile Referenz `stage3b4a-stable`. [Technik](stage3b4a.md), [Diagnose](stage3b4a_background_font_fix.md).

Der Benutzer bestätigt `9b2e767` als voll funktional. Auf seinen anschließenden Wunsch
werden die Beschriftungen auf „Hi-Score“, „No P2“, „Form.“ und „Att.“ verkürzt und
vollständig gerahmt. Eigene dünne 5×7-Zeichen ersetzen nur benötigte Glyphen der
privaten Fontkopie. Die 38 Glyphen liegen bei `$9900–$9A55`; SEQ-/Framepuffer
`$6800/$6900` und Levelkopie `$7600–$7950` bleiben frei davon. Kein Original-Amiga-
Font wird behauptet. Gameplay, Ladefunktionen, Lebenssymbole und Exit bleiben erhalten.
Der Benutzer bestätigt am 10.10.2026 auch die neue Schrift und Stage 3b-4a insgesamt.
Bestätigter Programmstand: `2e672c9c4abc15ee9b46a30b906f35650d43323f`. Der Tag `stage3b4a-stable`
sichert diesen Stand einschließlich der Abnahmedokumentation. ASM, PRG, D81 und
Prüfsummen bleiben unverändert. Die XEMU-Abnahme stammt vom Benutzer; kein eigener
vollständiger Emulatorlauf wird behauptet.

## Stage 3b-5b – stabile Referenz `stage3b5b-stable`

Basis `stage3b4a-stable`, eigener Branch `stage3b-5b`, aktualisiertes Issue #6.
Hardware-Sprites 0–1: unabhängige vertikale Spielerschüsse mit Feuer-Latch; 2–5:
maximal vier zufällige Gegnerschüsse mit gespeicherter Zielposition und signed-8.8-
Geschwindigkeit. Nur bestehender Gegner Nr. 19 erhält den isolierten Testangriffsstatus
(96/128 Frames, mit T abschaltbar), sein ursprünglicher Pfad bleibt erhalten.
Noch keine originalen Angriffskurven oder Treffer-/Punkte-/Lebenslogik.

Verbindliche Mapping-Korrektur: VYLV 14 → VYGR-Typ 15, sechs Originalframes.
Zentrale JSON-/ASM-Tabelle kennzeichnet alle anderen 37 Einträge als unbestätigte
Fallbacks. Die Quellen und Release-Dateien der stabilen Stage 3b-4a bleiben bytegleich.

KickAssembler, Baseline-Bytevergleich, DAT-Hashes und D81-Dateiketten/BAM werden im
Builder geprüft. Neun neue CPU-/DMA-/Sprite-/RRB-Hosttests prüfen Slots, Zielvektoren,
Originalframes, bestehende Bewegung/HUD, BASIC-Exit, Cursor und erneuten Start.
Der Benutzer hat Stage 3b-5b am 10.10.2026 als vollständig funktional bestätigt
und die Stable-Markierung ausdrücklich freigegeben. Ein eigener vollständiger
XEMU-Lauf durch Codex wird nicht behauptet.
Artefakte: `releases/stage_3b5b/`. [Technik/Build](stage3b5b.md),
[XEMU-Abnahme](stage3b5b_xemu_test.md). Stabile Referenz: `stage3b5b-stable`.
Bestätigter Programmstand: `6f378c2faa136a6d25b5d8d32f51e3ba79f02518`. Die Abnahmedokumentation
verändert weder ASM noch PRG, D81, Mapping-Assets oder Prüfsummen.

## Stage 3b-5c – stabile Referenz `stage3b5c-stable`

Issue #8, eigener Branch `stage3b-5c`, Basis `stage3b5b-stable`.
Der zunächst fehlende Original-Explosionssatz wurde vom Benutzer in
`assets/explosions/explosion_amiga_planes.txt` ergänzt. Die sieben tatsächlichen Explosionsframes werden
verlustfrei mit Maskentransparenz und bestehender Palette in NCM konvertiert.
Software-AABBs berücksichtigen zwei Spieler- und vier Gegnerschüsse sowie alle
23 Gegner. Einflug-/Angriffs-Rammkollisionen erzeugen zwei Explosionen ohne
Abschusspunkte. Eigene Zustände verhindern Mehrfachtreffer und Wiedererscheinen
zerstörter Gegner. Punkte/Highscore sind 32-bit; drei Startleben, WAIT_FORMATION,
Respawn an Todesposition mit 150 Ticks Unverwundbarkeit und 25-Tick-Blinkwechsel.
GAME OVER erscheint nach vollständiger letzter Explosion; R setzt Level 1
zurück und erhält den Highscore, X verwendet die bestehende BASIC-Restauration.
Mapping 14 → Typ 15 bleibt unverändert. Player 2 bleibt inaktiv.

14 neue CPU-/DMA-/Sprite-/RRB-Hosttests bestehen, einschließlich ausgewähltem
Cursorcode aus dem bereitgestellten ROM V920395. Der unabhängige Rebuild erzeugt
bytegleiche Artefakte. Stable-Dateien und Tags bleiben unverändert.
Der Benutzer bestätigt am 10.10.2026 den korrigierten Stand unter XEMU
als funktionierend und gibt die Stable-Markierung ausdrücklich frei. Ein eigener
vollständiger XEMU-Lauf durch Codex wird nicht behauptet. Artefakte in `releases/stage_3b5c/`.
[Technik und Build](stage3b5c.md), [Testprotokoll](stage3b5c_xemu_test.md),
[historische Vorprüfung](stage3b5c_preflight.md).


Korrektur nach XEMU-Rückmeldung: Source-Record 7 ($3827A) ist die fälschlich
mitextrahierte Playergrafik. Benutzer bestätigt sieben statt acht Explosionen.
Der Datensatz bleibt dokumentiert, wird aber nicht mehr eingebunden/ausgewählt;
sieben Frames à drei Ticks gelten für Player/Gegner. Im 150-Tick-Respawn ist
Joystickbewegung freigegeben, Feuer weiterhin gesperrt, vollständiger Treffer-
schutz und Blinken erhalten. Finaler Frame setzt die Position nicht zurück.

Bestätigter Programmstand: `7c77591e46a85a786fb41c974e7ce6d1e0b841f9`. Tag `stage3b5c-stable`
sichert diesen Stand einschließlich der Abnahmedokumentation. ASM, PRG, D81,
Assets, Builder und Release-Prüfsummen bleiben bei der Markierung unverändert.

## Stage 4a – stabile Referenz `stage4a-stable`

Branch `stage4a`, Grundlage `stage3b5c-stable` (`1e0d1a7`), gemäß Issue #10.
Isolierter Offscreen-Test mit einem originalen Typ-15-Gegner und sechs Frames:
F ein/aus, N nächster Einflug, P Bewegungspause, X BASIC. Vier Kanten plus
Diagonale, signed 16-Bit-Positionen, privater pixelgenauer Software-Crop;
normales Gameplay ist außerhalb des Tests unverändert. Keine originalen
Einflug-/Angriffskurven integriert. Build/PRG/D81 unter `releases/stage_4a/`.
[Technischer Nachweis und bestätigte XEMU-Abnahme](stage4a_offscreen_clipping.md).
Stage 4a wurde am 11.10.2026 vom Benutzer unter XEMU als vollständig funktional
bestätigt und ausdrücklich als Stable freigegeben. Stage 3b-5c bleibt erhalten.

Stage-4a-Erweiterung 11.10.2026: Nach fehlerfreier Benutzerprüfung des bisherigen
Testmodus sind nun zusätzlich Y=0–15 und Y=184–199 für Pixies freigegeben.
Rendering/Clipping verwenden alle 25 Zeilen, X<240 und sämtliche übrigen
Gameplay-/Speicherparameter bleiben unverändert. Aktualisiertes D81 im selben
Releasepfad; auch die volle Höhe wurde anschließend ausdrücklich bestätigt.
Bestätigter Programmstand: `7c3a466`; stabile Referenz `stage4a-stable`.
Die Stable-Markierung ändert ausschließlich Dokumentation, keine Quellen oder
Release-Artefakte.

## Stage 4b – Stable, vom Benutzer unter XEMU bestätigt

Der Benutzer bestätigt den finalen DMA-Build als vollständig funktionsfähig.
Bestätigter Programmcommit: `12f4b4062d556389622b44cbf62dfbe6034d1711`.
Stabile Referenz: `stage4b-stable`. PRG/D81/Quellen unter `releases/stage_4b/`
bleiben byteidentisch zum abgenommenen Build. 33/33 automatische Tests,
reproduzierbarer Zweitbuild und Benutzer-XEMU-Abnahme sind dokumentiert.

Die früheren offenen XEMU-Abnahmen unten sind historisch und durch diese
Freigabe erledigt. Offene Fragen zur exakten Amiga-Zeit-/Debut-Übergangslogik
bleiben historische Rekonstruktionsgrenzen; die Benutzerfreigabe ist keine
zusätzliche Amiga-Binärverifikation. Neue Entwicklung separat auf dieser Referenz.

### Historische Stage-4b-Entwicklung und Fehlerkorrekturen


Auf `stage4a-stable`: 22 Gegner in zwei Originalgruppen, signed Kurvencontroller,
kontinuierlicher Formationsübergang, Player (112,184) mit X-only-Steuerung.
Historische Interpreteranalyse übernommen und mit VYLV abgeglichen; genaue
Original-Zeit-/Debut-Übergangslogik bleibt ausdrücklich unbestätigt. RRB-Kapazität
auf 24 pro Zeile erweitert, Geometrie/HUD unverändert.
Nicht Stable, XEMU-Abnahme offen. [Details](stage4b_level1_entry.md).

Benutzer meldet schwarzen Bildschirm für Build `8045364`, X funktioniert.
Ursache: absolute Screenwrites nach `$E000` treffen SYS-MAPH/KERNAL-ROM in
Bank 3 statt physischem Bank-0-Screen. Korrektur auf 32-bit-indirekte Stores,
Regression jetzt mit SYS-MAP-Modell. Erneute XEMU-Abnahme erforderlich.

Korrigierter Screenstand: 32/32 automatische Tests bestanden (408,498 s),
ROM-V920395-Blinkroutine aktiv; alle 15 Release-Dateien beim Zweitbuild
byteidentisch. D81/PRG unter `releases/stage_4b/`, Benutzer-XEMU-Test offen.

Weiterer XEMU-Befund: obere zwei HUD-Zeilen und linke Pixel flackern,
verschwinden bei DEAD aller Gegner. Die Live-RRB-Listen wurden durch
2.500 einzelne Screen-Clears pro Frame lange in ungültigem Zustand belassen.
Korrektur: physischer DMA-Clear plus gültige unsichtbare Screen-/Color-Records
für sämtliche freien Slots. Rasterabnahme in XEMU erneut offen; kein Stable-Tag.

DMA-Korrektur: 33/33 Tests bestanden (285,571 s), bereitgestellte ROM-
Blinkroutine aktiv, 15 Release-Dateien byteidentisch reproduziert.
CPU-Modell: 22-Gegner-Formation 327.427 → 102.477 Zyklen.
Aktuelles D81 unter `releases/stage_4b/`; erneute XEMU-Abnahme offen.

## Stage 4b-1 – Stable, vom Benutzer unter XEMU bestätigt

Separater Branch `stage4b-1` aus `stage4b-stable`. WAIT war bereits unsichtbar;
ENTRY zeichnete den Starttick und sieben rechte Null-Deltas sichtbar. Ein
gemeinsames Flag unterdrückt Darstellung und Kollision bis zur ersten Bewegung,
ohne Kurven, Koordinaten oder Timing zu ändern. Stage 4b bleibt geschützt.
PRG/D81/Quellen: `releases/stage_4b_1/`. Referenz `stage4b1-stable`.
[Ursache, Zeitvergleich und Testanleitung](stage4b1_entry_visibility_fix.md).

Stage-4b-1-Prüfung: 36 unterschiedliche automatische Tests erfolgreich (nach
Korrektur der übernommenen D81-Testreferenz auf STAGE4B1); alle 15
Release-Dateien im Zweitbuild byteidentisch. Der Benutzer hat den korrekten
Einflug unter XEMU bestätigt und Stage 4b-1 ausdrücklich als Stable freigegeben.
Bestätigter Programmcommit: `531c745971ae95ad15c723b46c97b1f34ee3cf3c`.
Die Stable-Markierung ändert ausschließlich Dokumentation; Quellen, PRG, D81
und Release-Prüfsummen bleiben unverändert.

## Stage 4b-2 – Stable, vom Benutzer unter XEMU bestätigt

Branch `stage4b-2` auf `stage4b1-stable`, originale getrennte 183-Byte-Kurven
für Level 1, maximal drei ATTACK und vier gegnerische Hardware-Sprite-Schüsse.
Formation pendelt -8..+8 mit 1 Pixel je 10 Frames nach vollständigem Einflug.
RETURN folgt den jeweils aktuellen Slotzielen. Auswahl, Y-Verankerung und
Auslauf/Reentry sind ausdrücklich dokumentierte MEGA65-Übergangsregeln;
historische Amiga-Endmarker-/Variantenauswahl nicht unabhängig belegt.
[Analyse, Parameter und Abnahme](stage4b2_attack_formation.md).
Release `releases/stage_4b_2/`; Referenz `stage4b2-stable`.

Stage-4b-2-Prüfung: 49/49 Tests in 511,317 s mit ROM V920395 bestanden,
inklusive aktiver Angriff-/Return-/Pendelmechanik und ROM-Overlay-Prüfung.
Hauptschleifenmodell: Ø112.575 / maximal 117.725 Zyklen pro Frame.
Alle 16 Release-Dateien byteidentisch reproduziert; PRG unverändert 43.777
Bytes, D81 819.200 Bytes. XEMU-Abnahme durch den Benutzer bestätigt; kein unabhängiger Hardwaretest.

XEMU-Rückmeldung zu Stage 4b-2: Explosion und Lebensabzug funktionieren,
Respawn wurde jedoch von laufend nachgestarteten Angriffen blockiert.
Korrektur: neue Angriffe während Player-Explosion und WAIT sperren, bestehende
Angriffe normal abschließen. Formation zentral acht Y-Pixel höher; Pendeltakt
auf ausdrücklich gewünschte 10 Frames geändert. Der Benutzer hat diesen
korrigierten Build ausdrücklich als stabil bestätigt.

Bestätigter Programmcommit: `5b88b9fa4a78d0340676a32bf9a10493fc73f79f`. Tag `stage4b2-stable`.
Die Stable-Sicherung verändert ausschließlich Dokumentation; sämtliche
Quellen, PRG/D81 und Release-Prüfsummen bleiben unverändert.

## Stage 4b-3 – Stable, vom Benutzer unter XEMU bestätigt

Neuer Branch `stage4b-3` aus der bestätigten Referenz `stage4b2-stable`.
Drift −8..+8 mit 1 Pixel je 5 Frames; zentrale Y-Transformation Original-Y−25.
Echte sichtbare ENTRY-Gegner schießen zusammen mit ATTACK aus dem globalen
Vier-Projektil-Pool. WAIT_ENTRY/RETURN/DEAD/EXPLOSION/offscreen ausgeschlossen.
Originalkurven und Gruppenstart-Timing unverändert; höhere Ziele nach Update336.
Originaltransparenz ergibt opake Oberkanten Y=0/1/2 je Animationsframe.
Quellen/PRG/D81 unter `releases/stage_4b_3/`, reproduzierbarer Build.
[Regeln, geometrische Diagnose und XEMU-Protokoll](stage4b3_gameplay_adjustments.md).
XEMU-Abnahme durch den Benutzer bestätigt; Referenz `stage4b3-stable`.

Stage-4b-3-Prüfung: 52 unterschiedliche automatische Checks abschließend bestanden
(Gesamtlauf49/51, zwei veraltete Test-Fixtures gezielt korrigiert und erneut
bestanden, zusätzlicher ENTRY-Hauptschleifentest bestanden). Erster ENTRY-Schuss
Update179/Slot14; Formationsbarriere336. CPU-Modell Ø116.340/max.121.548 Zyklen.
Alle16 Release-Dateien byteidentisch; Stage-4b-2-Quellen/Releases geschützt.
GitHub-Veröffentlichung der Stable-Sicherung und Stage4b-3 wegen fehlgeschlagener
automatischer Freigabeprüfung (Nutzungslimit) ausstehend. Lokaler Testbuild fertig.

Der Benutzer bestätigt: Stage 4b-3 läuft stabil und verhält sich genau wie
vorgesehen. Bestätigter Programmcommit: `a8766f8df9fcea8279181a5d13b772db15ecc954`.
Die Stable-Sicherung verändert ausschließlich Dokumentation; sämtliche Quellen,
PRG/D81 und Release-Prüfsummen bleiben unverändert. Kein unabhängiger Hardwaretest.
Branch/Stable-Tags sind lokal gesichert; GitHub-Veröffentlichung bleibt bis zur
wieder verfügbaren automatischen Freigabeprüfung ausstehend.

## Stage 4c – feste Kurvenzuordnung/Zwei-Frame-Drift (Stable)

Branch `stage4c` ausschließlich aus lokaler bestätigter `stage4b3-stable`.
Basisquellen und alle16 Release-Dateien vor Umsetzung verifiziert/geschützt.
Drift−8..+8 ein Pixel alle2 Frames; Player unverändert1 Pixel/Frame.
Fester VYLV-Gegnerindex+5, vier zentrale begrenzte Deskriptoren und zusätzliche
Indexprüfung bei Initialisierung, Angriffstart und Kurvenzugriff. Zufall wählt
nur den FORMATION-Gegner. Alle100 Levels/2194 Indizes gegen Original-VYLV geprüft.
Level1-Produktion bleibt unverändert zwei Kurven; keine neue Levelwechsel-Engine.
Quellen/PRG/D81: `releases/stage_4c/`. XEMU-Abnahme vom Benutzer bestätigt; Referenz `stage4c-stable`.
[Format, Basisschutz, Testbericht und Abnahme](stage4c_attack_mapping_and_drift.md).

Stage4c: 57/57 automatische Tests bestanden; Zweitbuild mit allen16 Release-Dateien byteidentisch. XEMU-Abnahme und Stable-Freigabe vom Benutzer bestätigt.

Stage 4c wurde vom Benutzer als stabil bestätigt. Programmcommit `1f4b3b5`;
Stable-Sicherung ausschließlich Dokumentation, Quellen und Release-Dateien unverändert.
Stage 4b-3 und `stage4b3-stable` sind inzwischen auf GitHub archiviert;
Stage 4c mit vollständigem D81 veröffentlicht (Pull Request #21).

## Stage 5a – zentrale100-Level-Verwaltung (Stable)

Branch `stage5a` aus `stage4c-stable`, Stable-Basis unverändert archiviert.
Dynamische Originalrecords, vier Gruppen, WORD-Einflugcursor/-verzögerungen,
individuelle Grafikquellen/Animation, Level Clear mit neuer Joystick-Buttonflanke,
regulär100→1; +/− Testnavigation begrenzt1..100. Score/Highscore/Leben erhalten.
Benutzerfreigabe für gezielte Kapazitätserweiterungen und vorläufige Angriffssperre
in25/50/99/100. Übriges Grafikmapping ausdrücklich unbestätigt.
[Speicher, Implementierung, Tests und XEMU-Plan](stage5a_level_management.md).
Quellen/PRG/D81 unter `releases/stage_5a/`; stabile Referenz `stage5a-stable`.

Stage5a:26 unterschiedliche automatische Tests bestanden, alle100 Initialisierungen;
402 Updates identisch zur Stage4c-Referenz. Alle18 Release-Dateien byteidentisch
im unabhängigen Zweitbuild. Benutzer-XEMU-Abnahme bestätigt.

Der Benutzer bestätigt: „Stage 5a ist bestätigt, Level-Wechsel funktionieren“.
Bestätigter Programmstand: `e7166a72fbe9b00bb1d75881837a74e339225351`.
Die Stable-Markierung verändert ausschließlich Dokumentation; Quellen, PRG, D81
und Originaldaten bleiben unverändert. Kein eigener XEMU-/Hardwaretest wird behauptet.
Die freigegebenen Sonderlevel-Einschränkungen und unbestätigten Grafikzuordnungen
bleiben bestehen.

## Stage 5b – 38 Originalgrafiken und Transparenz (Stable)

Issue #27, Branch `stage5b` ausschließlich aus `stage5a-stable`. Die Stable-Basis
und Originalassets bleiben unverändert.20 fehlende Originalframes der Indizes36/37
(Typen37/38) sind anhand aller eigenen Frame-/Maskenpointer extrahiert. Insgesamt
259 Frames; sämtliche Plane-/Maskenbytes durch den zweiten Original-USS bestätigt.
ADF-Forme stimmt mit allen2194 Gegnern der100 VYLV-Level überein. Zentrales explizites
38-Einträge-Mapping`n→n+1`, stark durch Deskriptor/Frame/Forme belegt; ursprüngliche
Amiga-Auswahlroutine weiterhin nicht unabhängig bewiesen.14→15 zusätzlich visuell bestätigt.

Die historischen Konvertierungsfehler (hohes statt niedriges linkes Nibble,
Plane-Pointer−6 plus zyklische Zeilenadressierung) sind für alle239 alten Frames
exakt reproduziert und anhand der Originalpointer korrigiert. Masken bleiben erhalten.
Neue VYGR33464 Bytes bei `$54000–$5C2B7`; kein Speicherüberschneidungsproblem.
Initialer Grafikbuild:45 geänderte PRG-Bytes; anschließend DOS-Exit-Korrektur, siehe unten.
Ein-Byte-Angriffssperren25/50/99/100 bleiben; Levelpaletten ausdrücklich außerhalb
Stage5b. [Technischer Prüfbericht und XEMU-Plan](stage5b_graphics_mapping.md),
[Testprotokoll](stage5b-test-results.json). Release: `releases/stage_5b/`.
Die abschließende Benutzerbestätigung und Stable-Referenz sind unten dokumentiert.

Stage5b:32/32 automatische Tests bestanden(270.006s), alle100 Level,259 Frames,
66304 Originalpixel und2072 neue RRB-Clipping-/Überlappungsfälle.20 Release-Dateien
im unabhängigen Zweitbuild byteidentisch. Die XEMU-Abnahme war zu diesem Zeitpunkt noch offen.

Stage5b: Benutzer bestätigt korrekte Grafiken in Levels1/29/37/54, meldet jedoch
nach X→BASIC Laufwerksausfall: DIRECTORY meldet DEVICE NOT PRESENT; RUN scheitert
an OPEN mit Load Error01. Ursache: geerbter Pixiepool`$10000–$115FF` überschreibt
reserviertes DOS-RAM`$10000–$11FFF`; CPU-/DMA-Nachweis zeigt5610 veränderte Testbytes
auch nach Exit. Pool nach `$14000–$155FF` verlegt, ohne DOS-Reset oder Änderung
an VIC-Exit, Loader, Grafiken oder Mapping. [Diagnose und Test](stage5b_dos_exit_fix.md).
Nach der Grafikabnahme stand zunächst noch die XEMU-Abnahme des korrigierten
Exits und erneuten Diskettenzugriffs aus.

DOS-korrigierter Stage5b-Build:34/34 Tests bestanden(353.719s), vollständige
8192-Byte-DOS-Erhaltung und null protokollierte Schreibzugriffe über alle100
Levelwechsel und drei Exit-/Neustartfolgen.20 Release-Dateien byteidentisch
reproduziert. Reale BASIC-Diskettenzugriffe werden durch diese CPU-Modelltests
nicht ersetzt; die abschließende Abnahme stammt vom Benutzer.

Abschließende Benutzerbestätigung: „Der Build ist jetzt stabil und funktioniert komplett“.
Stabile Referenz: `stage5b-stable`; bestätigter Programmcommit
`52118cee6813b833d0c1d237925ad6ecd75d1d33` einschließlich DOS-Exit-Korrektur.
Die Stable-Sicherung verändert ausschließlich Dokumentation; Quellen, PRG, D81
und Originaldaten bleiben bytegleich. Die XEMU-Abnahme stammt vom Benutzer;
ein eigener XEMU-/Hardwarelauf wurde nicht durchgeführt. Die dokumentierten
Mapping-Beweisgrenzen und Sonderlevel-Angriffssperren bleiben bestehen.

## Stage 5c – originale100-Level-Paletten (Stable)

Issue #31, neuer Branch `stage5c` aus `stage5b-stable` (`88e19bb`).
Analyse/CSVs aus `analysis-color-palettes` übernommen und gegen archivierte
Original-ADF geprüft:362 Color-Bytes sowie alle100 Levelrecord-Felder`+$4C`
identisch. Die ursprüngliche Amiga-Code-Nutzung ist weiterhin nicht unabhängig
bewiesen; kein eigener WinUAE-Farbvergleich behauptet.

VYCL v1:476 Bytes,20×9 verlustfreie RGB4-Wörter,100 Levelindices, Header und
Payloadsumme. SEQ-Loader mit SETBNK, Rücklese-DMA und Format-/Summenprüfung
um dritte Datei erweitert. Ladegerät aus KERNAL`$BA` für alle Dateien bewahrt.
VYLV/VYGR bleiben unverändert. Gegnerpalette bei jedem Levelstart vor Darstellung
aktiviert; drei Bitplanes nutzen Originalwörter0..7, Wort8 bleibt mitgeführt.

Gegner liegen in eigener16-Farben-NCM-Gruppe17..24 der Bank1. Explosionen behalten
Bank1-Farben0..15, Player/HUD/Projektile Bank2, BASIC-ROM Bank3. Bestehende
Color-RAM-Sicherung von`$6B00–$6F7F` durch zwei DMA-Adressänderungen nach
`$15600–$15A7F` verlegt, um Palettencode und Spiegel konfliktfrei aufzunehmen.
Angriffsmetadaten`$6F80–$6FFF` unverändert erhalten. Vollständige Speicherkarte
und Prüfbericht: [Stage5c](stage5c_original_palettes.md).

Quellen/PRG/D81 und alle drei DAT-Dateien: `releases/stage_5c/`.
Automatische Testergebnisse: `docs/stage5c-test-results.json`.
Stage5c ist nach ausdrücklicher Benutzerabnahme Stable; Referenz `stage5c-stable`.

Finaler Stage5c-Build: **43/43 Tests bestanden (515.180s)**; alle100 Level-
initialisierungen und Paletten,259 Originalframes,1813 Clipping- und259
Überlappungsfälle. DOS8192 Bytes, Color-RAM4800 Bytes und Cursorzustand erhalten;
Player/HUD/Explosionen isoliert. Alle23 Release-Dateien im unabhängigen Zweitbuild
byteidentisch. Benutzer-XEMU-Abnahme und originalgetreue Level-Farben bestätigt;
kein eigener XEMU-/WinUAE-Farbvergleich durchgeführt.

## Bestätigte Stable-Referenz

Der Benutzer bestätigt: „Level-Farben entsprechen exakt dem Original, Player, HUD und Explosionen sind unverändert korrekt. Basic-Exit funktioniert ebenfalls. Stage 5c ist stable.“
Stabile Referenz: `stage5c-stable`; bestätigter Programmcommit
`2fb8308b886980f3d0e89a1ae19faf3937c6903f`.
Die Stable-Sicherung verändert ausschließlich Dokumentation. Quellen, PRG, D81
und alle DAT-Dateien bleiben byteidentisch. Die XEMU-Abnahme und der visuelle
Originalfarbvergleich stammen vom Benutzer; ein eigener XEMU-/WinUAE- oder
Hardwarelauf wird nicht behauptet. Die offenen Amiga-Code-Beweisfragen und
die freigegebenen Sonderlevel-Angriffssperren bleiben unverändert dokumentiert.

## Übernommene Stage-5d-0-Stable-Referenz

Der Benutzer bestätigt: „Stage 5d0 funktioniert und ist stable“.
Isolierter Titeltest: Tag `stage5d0-stable`, Branch `stage5d-title-test`,
bestätigter Programmcommit `671054337daa76dc2019660b111505d00a818cd6`.
Die hier übernommenen Quellen, Originalassets und Release-Dateien sind gegenüber
dieser Referenz unverändert. Die Stage-5c-Basis bleibt ebenfalls erhalten.

## Stage 5d-1 – Titel während des Ladens (Stable)

Issue #35, Branch `stage5d-1` aus unverändertem `stage5c-stable`.
Der vom Benutzer bestätigte FCM-Titelrenderer aus `stage5d0-stable` wird gezielt
übernommen. VYTI wird zuerst geladen, vollständig geprüft und sichtbar gemacht;
danach bleiben alle Titelpixel während VYLV/VYGR/VYCL und Levelvorbereitung
unverändert. Nach erfolgreicher Validierung wird direkt Level 1 gestartet.
Kein Menü. Titel-Cache und aktive Enginepuffer sind getrennt; der phasenweise
mit dem HUD-Font geteilte Bootstrap wird für erneutes RUN wiederhergestellt.
Original-Spielmechanik und alle 100 Level bleiben die Stage-5c-Implementierung.
Quellen, PRG, vollständiges D81 und vier DAT-Dateien: `releases/stage_5d_1/`.
[Build, Speicherprüfung, Fehler und XEMU-Abnahme](stage5d1_title_loader_integration.md).
Automatische Tests sind Hostmodelle; die XEMU-Abnahme nach der HOTREG-Korrektur
wurde inzwischen vom Benutzer bestätigt.

## Stage-5d-1-Nachkorrektur: Titel → Spiel

Benutzer-XEMU-Befund: Titel lädt korrekt, im Level flackern die oberen etwa
drei Zeilen und Pixieteile fehlen. Nachgewiesen wurde eine ausstehende
HOTREG-Legacy-Neuberechnung beim abschließenden Aktivieren von HOTREG, die
bereits restaurierte präzise Geometrie wieder überschreiben kann. Die
Restore-Reihenfolge wurde ausschließlich im neuen Titelbootstrap korrigiert.
Der zusätzliche Regressionstest scheitert mit dem alten PRG in beiden
HOTREG-on-Modellen (XEMU/Core), besteht mit dem neuen in allen vier Fällen.
Spielrenderer und sämtliche normalisierten Stage-5c-Spielkomponenten sowie
alle Original-DAT-Dateien bleiben unverändert. Vollständige erneute Host-
Regression und unabhängiger Zweitbuild: `docs/stage5d1-test-results.json`.
Die visuelle XEMU-Nachprüfung wurde inzwischen vom Benutzer bestätigt.

Automatische Nachprüfung: vollständiger Vorlauf 50/50 erfolgreich; endgültiger
38-Register-Build mit sechs gezielten Prüfungen zu Geometrie, Pixeln, Ladefehler,
ROM-Cursor, Exit und erneutem RUN bestätigt. Prüfbericht trennt die Buildstände
und dokumentiert die Testvorgaben-Korrektur zur BASIC-Hintergrundfarbe.
27 Artefakte im unabhängigen Zweitbuild byteidentisch, 61 Stable-Dateien geschützt.
Nur 590 PRG-Bytes innerhalb des Titelbootstraps geändert; übriger Spielcode identisch.

## Stage 5d-1: bestätigte Stable-Referenz

Benutzerbestätigung: „Mit den Korrekturen funktioniert jetzt alles wieder.
Der Build ist stable.“ Referenz: `stage5d1-stable`, Branch `stage5d-1`.
Bestätigter Programmcommit: `7d6e77f0c2da42065941ab9a2f93f8f589ce2dda`.
Die Sicherung verändert ausschließlich Dokumentation; vollständige Quellen,
Originalassets, PRG, D81 und Release-ZIP bleiben byteidentisch.
Die XEMU-Abnahme stammt vom Benutzer; kein eigener XEMU-/Hardwarelauf.

## Stage 5d-1a / Issue #41: Stable (12.10.2026)

Separate branch `stage5d-1-b2`, based on current Stage 5d-1 commit `e295fa8`. User-confirmed B2 ENTRY Y−16 and continuous RETURN handoff integrated in new sources only. Title/loader, ATTACK, all 100 levels and palettes preserved. Release `releases/stage_5d_1_b2/`; Stable tag `stage5d1a-stable`. See [integration report](stage5d1_b2_integration.md).

Benutzerabnahme am 12.10.2026: „Der Build ist stable.“ Getesteter Programmcommit `08df921c6cca4614e540d6f50d6c853e8835ad40`. Nur Dokumentation wird zur Stable-Sicherung geändert; sämtliche Quellen und Release-Artefakte bleiben byteidentisch. Frühere Build-PRs #36/#38/#40 und der abgeschlossene Integrations-PR #42 werden geschlossen, zugehörige Issues #35/#37/#39/#41 abgeschlossen. Branches, Tags und historische Downloads bleiben erhalten; keine Integration in frühere Stable-Branches.

## Stage 6b1 – Issue #47, Testbuild, noch nicht Stable

Eigener Branch `stage6b1` auf unveränderter `stage5d1a-stable`-Spielengine
(`39890c0`), mit gezielt integrierter `stage6a2-stable`-Menüreferenz (`24559e4`).
Nach Titel/SEQ-Laden erscheint das originale animierte Menü; Auswahl per
Joystick/Tastatur, zyklisches INITIAL LEVEL 001–100, F1-Spielstart und F2/F3-
Platzhalter. Original-Color02-Cycling läuft im Spiel auf Bank1/Index19 weiter,
während Player, HUD, Explosionen und übrige Levelpalettenfarben erhalten bleiben.
HUD nutzt den rekonstruierten Menüfont. Stage 6a1 ist historische, obsolete
Referenz; Stage 6a2 ist der vom Benutzer bestätigte Menüstand.

Quellen `src/engine/stage6b1*.asm`, Builder `tools/build_stage6b1.py`, PRG/D81
unter `releases/stage_6b1/`. Stable-Tags, deren Quellen und Releases unverändert.
Automatische Prüfungen und XEMU-Checkliste:
[Stage6b1-Menüintegration](stage6b1_menu_integration.md).
Eine XEMU-Abnahme von Stage6b1 wird nicht behauptet; Stable erst nach ausdrücklicher
Benutzerbestätigung.

### Stage6b1 – Korrektur des gemeldeten 3,5-MHz-Taktabfalls

Titel-/Menüinitialisierung löschte mit `$D054=$05` das VFAST-Bit. Stage6b1 setzt
jetzt FAST und VFAST in Titel, Menü und Spiel; BASIC-Taktregister werden weiterhin
exakt restauriert. Neuer Register-/Exit-Test für langsame und schnelle BASIC-
Starts. Vollständiges PRG/D81 aktualisiert, Stable-Referenzen unverändert.
Details und XEMU-Prüfschwerpunkt: `docs/stage6b1_menu_integration.md`.

### Stage6b1 – ROMC-/IRQ-Korrektur für V920413

KERNAL-Menüdatei-I/O wurde mit abgeschalteter ROMC-Abbildung aufgerufen.
Low-RAM-Gates restaurieren jetzt ROMC vor SEQ-I/O; nur Parameter-/Prüfphasen
laufen IRQ-maskiert in der Bridge. V920413-ROM belegt FA29 als IRQ/BRK-Prolog
und CE26 als BRK-Ziel; linear000CE26 zeigt fehlende ROM-Abbildung.
20 Laufzeittests plus drei ROM-Belegprüfungen bestanden; neuer PRG/D81-Build
bytegleich reproduziert. XEMU-Abnahme ausstehend, nicht Stable.

## Stage6b1 Stable – Benutzerabnahme 12.10.2026

Vom Benutzer nach XEMU-Funktionskontrolle mit ROM V920413 ausdrücklich bestätigt.
Joystickfehler war XEMU-Port1; mit **Port2** funktionieren Menü und Spiel.
Kein weiterer Programmfix. Stable-Referenz `stage6b1-stable`, Branch `stage6b1`,
getesteter Programmcommit `5fa82452101cf690c3fa1f5eba0b172222541764`.
Quellen und vollständiges Release `releases/stage_6b1/` bytegleich erhalten.
Die Bestätigung stammt vom Benutzer, kein eigener XEMU-Test behauptet.

## Stage7a1 – separater technischer Sternentest, 13.10.2026

Issue49, Branch `stage7a1-starfield-test`, **nicht Stable**, kein produktiver Merge.
Ausgangspunkt `stage6b1-stable`, unveränderte geschützte Quellen/Assets/Releases.
Separates PRG und vollständiges D81 unter `releases/stage_7a1/`.

F1 startet den bestehenden Spielablauf mit 48 reproduzierbaren Ein-Pixel-Sternen:
Blau +1 Y/8 Frames, Rot /4, Gelb /2. Diese RGB-/Dichte-/Geschwindigkeitswerte
sind ausdrücklich Testparameter. Eigener 24-KB-NCM-Charset nutzt den bestehenden
opaken Hintergrundprefix; keine zusätzlichen Hardware-Sprites oder RRB-Pixies.
Originalgrafiken, Paletten/Cycling, HUD, Schüsse und sämtliche Level bleiben erhalten.
B schaltet Sterne sauber aus/ein; V aktiviert Rastermarker; X/RUN bleibt erhalten.

28 Hosttests des assemblierten PRG bestanden, darunter 1.600 Sternframes,
Clipping/Transparenz, DMA-/Speichergrenzen, Paletten und bisherige Menü-/Kampf-
Regression. Spitzenlast:192 Ein-Byte-DMA-Aufträge, Mittel56. CPU-Modellwerte
und echte PAL-Rasterinstrumentierung getrennt dokumentiert. Kein eigener
XEMU-Test; mehrminütige optische Abnahme und reale Rasterzeit noch erforderlich.
Architektur als Integrationskandidat empfohlen, Stable erst nach Benutzerbestätigung.
Details: [Machbarkeit/Messungen/Build](stage7a1_starfield_feasibility.md).

## Stage7a1 Stable – Benutzerabnahme 13.10.2026

Vom Benutzer unter XEMU getestet: keine erkennbaren Probleme; Build ausdrücklich
als Stable bestätigt und zum Merge freigegeben. Getesteter Programmcommit
`ed22f0d4e4ca0bd8f5ff6ebaa5892135ce9bdd9a`, Referenz `stage7a1-stable`.
PRG, D81, Quellen und das vollständige Release bleiben bytegleich.
Die Freigabe stammt vom Benutzer; keine eigenen XEMU- oder Rasterzeitmessungen
behauptet. Historische Testreports im Release bleiben unverändert.

PR50 wird nach `main` gemergt; `stage6b1` und sämtliche bisherigen Stable-Tags
bleiben unverändert. Dies archiviert den eigenständigen Testbuild; die spätere
Integration in eine neue Spielengine-Stage erfolgt weiterhin separat.

## Stage7a2 – Sternenhintergrund in der vollständigen Engine, 13.10.2026

Issue51, Branch `stage7a2`, **nicht Stable; XEMU-Abnahme ausstehend**.
Enginequellen ab `stage6b1-stable`, Sternrenderer/Parameter aus dem getesteten
Stage7a1-Programmcommit `ed22f0d`. Der freigegebene Stage7a1-Merge nach main
ist verifiziert; alle bisherigen Stable-Stände bleiben unverändert.

Sterne nur im Playfield nach F1; Farben/Verteilung und Teiler8/4/2 unverändert.
Kein B/V-Schalter, kein Rastermarker und keine Stern-Laufzeitdiagnostik.
Ein Tick pro Hauptschleifenframe, auch bei LEVEL CLEAR und GAME OVER.
Levelwechsel und R bewahren Positionen/Bitmap/Phase; HUD-Neuaufbau lässt aktive
Sternzellen kontinuierlich stehen. Kleine dokumentierte API vorbereitet;
beschleunigte Modi derzeit abgewiesen, kein Übergangseffekt implementiert.

33 Hosttests bestanden, einschließlich 160 LEVEL-CLEAR-Frames, 100 Übergängen
ohne vorübergehende Prefixänderung, Sprite-/Pixie-/Paletten-/Kampfregression
und BASIC/RUN. 47 Dateien aus zwei Builds bytegleich. CPU-Modellmittel6792,375,
Peak18756 (All48-Wrap19098); DMA Mittel56/Peak192 Ein-Byte-Aufträge. Keine eigene
XEMU-Zeitmessung. PRG/D81/Quellen/Reports unter `releases/stage_7a2/`.
Details und Benutzerprüfplan: [Stage7a2](stage7a2_starfield_integration.md).
