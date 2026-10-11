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

## Stage 4a – Entwicklungsstand, XEMU-Abnahme ausstehend

Branch `stage4a`, Grundlage `stage3b5c-stable` (`1e0d1a7`), gemäß Issue #10.
Isolierter Offscreen-Test mit einem originalen Typ-15-Gegner und sechs Frames:
F ein/aus, N nächster Einflug, P Bewegungspause, X BASIC. Vier Kanten plus
Diagonale, signed 16-Bit-Positionen, privater pixelgenauer Software-Crop;
normales Gameplay ist außerhalb des Tests unverändert. Keine originalen
Einflug-/Angriffskurven integriert. Build/PRG/D81 unter `releases/stage_4a/`.
[Technischer Nachweis und noch offene XEMU-Abnahme](stage4a_offscreen_clipping.md).
Stage 4a ist ausdrücklich **nicht Stable**; die stabile Stage 3b-5c bleibt erhalten.

Stage-4a-Erweiterung 11.10.2026: Nach fehlerfreier Benutzerprüfung des bisherigen
Testmodus sind nun zusätzlich Y=0–15 und Y=184–199 für Pixies freigegeben.
Rendering/Clipping verwenden alle 25 Zeilen, X<240 und sämtliche übrigen
Gameplay-/Speicherparameter bleiben unverändert. Aktualisiertes D81 im selben
Releasepfad; erneute XEMU-Abnahme der vollen Höhe ausstehend, nicht Stable.
