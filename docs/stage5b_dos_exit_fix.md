# Stage 5b – DOS-Speicher und erneuter Start nach BASIC

Benutzerabnahme: Originalgrafiken in Levels1/29/37/54 korrekt. Gemeldeter Fehler:
X zeigt korrekt BASIC, anschließend `RUN`→Load Error$01 und
`DIRECTORY`→`?DEVICE NOT PRESENT ERROR`. Dieser Fehler wurde korrigiert;
der Benutzer hat den vollständigen korrigierten Build inzwischen als Stable bestätigt.

## Ursache und Nachweis vor der Änderung

Stage5a und der initiale Stage5b-Commit`05a87a7` besitzen identische Exit-Routinen.
Die38-Typen-Erweiterung endet bei `$5C2B7` und überlappt keine Diskettenpuffer.
Der Konflikt betrifft einen geerbten Bereich in **physischer Bank1**:

- MEGA65-Programmierhandbuch, `memory.tex`, Tabelle der ChipRAM-Belegung:
  `1.0000–1.1FFF: DOS buffers and variables`, also `$10000–$11FFF`.
- `level.clear_private` löscht22×256 Bytes ab `$10000`.
- `level.full_frame` und `entry.e_crop_frame` kopieren Voll-/Clipping-/Explosions-
  frames in dieselben22 privaten RRB-Puffer; `entry.e_private_glyph` liefert
  Glyphen`$401+4*slot`, also dieselben physischen Grafikadressen.
- Keine Exit-Routine stellt diese DOS-Variablen wieder her. Die vorhandenen
  Sicherungen betreffen Bildschirm, Farbe, VIC-/Sprite-/Cursorzustand.

Vor der Korrektur wurde der unveränderte echte Stage5b-Maschinencode mit einem
8192-Byte-Muster im DOS-RAM gestartet und mit X verlassen. Ergebnis:5610 Bytes
zwischen `$10000` und `$115FF` verändert, auch nach Rückkehr zu BASIC. Erfasste
physische DMA-Ziele beginnen mit `$10000/$10100/$10200/$10300`, jeweils256 Bytes
vom Blank-Template `$6700`. Damit ist die Überschreibung reproduziert.
Das ist ein CPU-/DMA-Nachweis, kein selbst ausgeführter XEMU-Lauf und kein Beleg
für eine bestimmte einzelne ROM-Variable. Der Fehler ist mit der dokumentierten
DOS-Belegung und beiden beobachteten Diskettenfehlern konsistent.

Meine frühere Speicherprüfung berücksichtigte Enginepuffer und ROM, übersah aber
die DOS-Reservierung in Bank1. Die bisherigen KERNAL-Traps modellierten OPEN/
Dateiinhalte, nicht die durch das Programm überschriebenen DOS-Variablen. Deshalb
bestand ihr zweiter RUN trotz dieses Konflikts. Diese Prüflücke ist geschlossen.

## Minimale Korrektur

Die22×256-Byte-Puffer liegen jetzt bei `$14000–$155FF`. Größe, Aufbau und Guards
bleiben identisch. Keine Überschneidung mit aktivem Record`$12000–$126FF`,
Color-RAM-Fenster`$1F800–$1FFFF`, High-RAM-Originaldaten oder sonstigen Bank1-Puffern.
Wie der bestehende aktive Record liegt dieser Speicher im BASIC-Array-/Stringbereich,
den dieses reine Maschinenspracheprogramm nach RUN für seine Daten verwendet;
BASIC-Arrays werden während des Spiels nicht benötigt.

Nur `stage5b_level.asm` und `stage5b_entry.asm` ändern sich:

- Blank-Clear läuft über die Bank1-Seiten`$40..$55`.
- Vollbild-/Clipping-DMA-Zielseite ist `slot | $40` für Slots0..21.
- Glyphenbasis ist`$501` statt`$401`: Adresse`$14040+slot*256`.

**DOS-RAM wird überhaupt nicht mehr als Grafikpuffer beschrieben.** Kein nachträglicher
DOS-Reset, kein Übermalen, keine Veränderung des optischen BASIC-Exits. Loader,
VYGR, VYLV, Grafiken, Palette, Mapping und Spielregeln bleiben unverändert.
Die zwei zusätzlichen ORA-Instruktionen verschieben lokale DMA-/Helperlabels um
zwei Bytes; der Assembler passt deren Operanden an. PRG-Größe bleibt43777 Bytes.
102 geänderte Bytes gegenüber dem initialen Stage5b-PRG,147 gegenüber Stage5a.
Der Builder prüft alle kompletten Quellen gegen Stable5a plus genau diese
zugelassenen Änderungen und die bereits geprüften Grafikänderungen.

## Automatische Prüfung und XEMU-Abnahme

`tests/test_stage5b_dos.py` setzt vor dem ersten Start das ganze8-KiB-DOS-RAM auf
ein nichttriviales Muster. Es protokolliert tatsächliche CPU-/DMA-Schreibzugriffe
in diesen Bereich und prüft anschließend vollständige Bytegleichheit:

- Start und alle100 Levelwechsel.
- Vollsichtige und teilweise abgeschnittene Gegner-/Explosionsframes.
- Normaler Exit, Exit bei LEVEL CLEAR und bei GAME OVER.
- Jeweils erneuter Start mit tatsächlich erneut ausgeführtem Loader.

Die Originalgrafik-/Clipping-/Kampf-/Steuerungs-/Levelwechseltests laufen zusätzlich
gegen den neuen Pool. **34/34 Tests bestanden** (353.719s), keinerlei protokollierte DOS-Schreibzugriffe;
alle8192 DOS-Bytes bleiben erhalten.20 Release-Dateien im unabhängigen Zweitbuild
byteidentisch. Renderer im getesteten schlechtesten22-Pixie-Fall441763 Zyklen
(zuvor441719), ohne vollständige DMA-/IRQ-/Rasterzeitmessung.
[Ausgeführtes Testprotokoll](stage5b-dos-tests.txt); aktueller Ergebnisbericht:
[`stage5b-test-results.json`](stage5b-test-results.json).

Unter XEMU bitte **einen frischen Emulatorstart mit neuem D81** verwenden: Bereits
vom alten Build überschriebenes DOS-RAM wird durch eine neu geladene PRG-Datei
nicht repariert. Das ist nur eine Voraussetzung für den einmaligen Wechsel vom
fehlerhaften Build; mit dem korrigierten Build müssen wiederholte RUNs funktionieren.

1. `LOAD "STAGE5B",8`, `RUN`; Grafik- und Spielverhalten überprüfen.
2. Mit X nach BASIC, `DIRECTORY` ausführen: Laufwerk und Dateien müssen erscheinen.
3. `RUN` mehrfach: beide DAT-Dateien müssen erfolgreich laden/verifizieren.
4. X→BASIC, anschließend `LOAD "STAGE5B",8`, `RUN` erneut.
5. Exit auch bei LEVEL CLEAR und GAME OVER, dann DIRECTORY/RUN wiederholen.

Der reale Diskettenzugriff in BASIC ist durch das CPU-Modell nicht ersetzt.
**Abschließende Benutzerbestätigung:** „Der Build ist jetzt stabil und funktioniert komplett“.
Stabile Referenz: `stage5b-stable`, Programmcommit `52118cee6813b833d0c1d237925ad6ecd75d1d33`.
Die Stable-Sicherung verändert ausschließlich Dokumentation; kein eigener XEMU-
oder Hardwarelauf wird damit behauptet.
