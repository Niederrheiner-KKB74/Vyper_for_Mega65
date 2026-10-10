# Stage 3b-2: BASIC-Exit – Diagnose und Korrektur vom 10.10.2026

Der Benutzer bestätigt Originaldaten, Grafiken und Enginebetrieb unter XEMU mit
ROM **V920395**, Bildschirmmodus **80×25**. Beim Exit mit `X` tritt abhängig vom
Zeitpunkt eine rote Linie oder ein unsichtbarer Cursor auf. Ein Tastendruck macht
den Cursor sichtbar. Die Korrektur ist gebaut und automatisch geprüft;
**die erneute XEMU-Abnahme ist offen. Kein Stable-Tag.**

## Ursache vor der Änderung nachgewiesen

Die bereitgestellte 128-KB-ROM-Datei hat SHA-256
`0f257ca5013e846604af6637bf44146de7500a49c54242a725aeb52cd86af5c1`.
Sie bleibt außerhalb des Repositorys. Die Analyse ihrer KERNAL-Routinen bestätigt
die Überschneidung mit den Engine-Objektrecords `$1000–$12FF`:

| ROM-Arbeitsadresse | Verwendung durch Cursor-Routine `$E513–$E55C` |
| --- | --- |
| `$111F` | Cursorflags; Bit 7 zeigt die eingeschaltete Blinkphase |
| `$1120` | Cursor deaktiviert bei ungleich null, aktiviert bei null |
| `$1121` | Blink-Countdown; wird dekrementiert, neuer Zyklus bei null |
| `$1122` | gesichertes Screen-Zeichen unter dem Cursor |
| `$1123` | gesichertes Color-RAM-Byte unter dem Cursor |

Die alte Routine `v014_copy_records` kopiert drei volle Seiten von `$7000` nach
`$1000`. Die betreffenden initialen Objektrecords enthalten Nullen. Damit werden
**alle fünf Cursorbytes überschrieben**: ein von SYS deaktivierter Cursor wird
unbeabsichtigt aktiviert, der Countdown und das gespeicherte Zeichen samt Farbe
werden zerstört. Bei einem Countdown von null ergibt der nächste `DEC` zunächst
255; die Cursoranzeige bleibt bis zur nächsten Blinkphase unsichtbar.

Da KERNAL-Interrupts während der Engine weiterlaufen, kann die nun aktivierte
Cursor-Routine zudem Farbe aus dem RRB-Color-RAM sichern. Der Exit restauriert
zwar die BASIC-Farben, aber ein späterer Cursor-Blinkzyklus schreibt das inzwischen
falsche gesicherte Farbbyte wieder zurück. Dies erklärt die Abhängigkeit vom
Blinkzeitpunkt und die unerwünschte Farbe nach BASIC-Rückkehr. Die Tests führen
hierfür die echten ROM-Instruktionen aus; die pixelgenaue Linienform wird durch
den Hosttest nicht gerendert und bleibt Teil der XEMU-Abnahme.

`$E030` springt in diesem ROM nach `$ED96`: Die ROM-eigene Cursor-Steuerung benutzt
ebenfalls `$111F–$1123`. Das bestätigt die Bedeutung der Bytes unabhängig von der
allgemeinen Speicherübersicht. Es wurde kein undokumentierter ROM-Aufruf in das
Spiel eingefügt und kein Cursorbyte durch einen pauschalen Reset überschrieben.

## Vergleich mit den bisherigen Stages

`exit_to_basic` ist in Stage 2ja, Stage 3b-1 und der bisherigen Stage 3b-2 identisch.
SHA-256 des Quellabschnitts bis `// Runtime state`:
`af2b1415961c62b1754696d9d95808f9e06f50aa890380a1d01bfb058d4713cf`.
Auch die Objektrecords `$1000–$12FF` sind ein geerbter Fehler. Eine stabile
Referenz wird deshalb nicht nachträglich verändert.

Der Exit restauriert Color-RAM, erweiterte VIC-Modusregister, Screen-/Color-/
Zeichensatzpointer, Zeilenbreite/-zahl, Spritepointer, Palette-Auswahl, HOTREG,
Border und Hintergrund. Diese Routine bleibt bytegleich. Kein Screen-Clear oder
Übermalen der Linie. Die 80×50-Bank-4-Reservierung ist durch den bestätigten
80×25-Modus als Erklärung dieses Tests ausgeschlossen. Loaderziele und neue
Grafikslots sind unverändert; der konkrete Schaden entsteht in der alten
Objektkopie, nicht durch ein Überlaufen der SEQ- oder DMA-Puffer.

## Notwendige Korrektur nur in Stage 3b-2

| Bereich | Bisher | Korrigiert |
| --- | --- | --- |
| 32 Objektrecords, 768 Byte | `$1000–$12FF` | `$1600–$18FF` |
| Diagnostik, 32 Byte | `$1300–$131F` | `$1900–$191F` |
| reservierter, unbenutzter Pfadarbeitsbereich | `$1400` | `$1A00–$1AFF` |
| reservierter, unbenutzter RRB-Arbeitsbereich | `$1800` | `$1B00–$1EFF` |

Alle neuen Bereiche liegen innerhalb des dokumentierten freien RAMs
`$1600–$1EFF`. Assembly-Guards prüfen die Grenzen. Der Builder prüft eine explizite
Liste der **53 absoluten Adressoperanden**, deren High-Byte um sechs steigt.
Gegenüber der bisherigen Stage 3b-2 ändern sich im PRG **genau 53 Bytes**. Opcodes,
Sprünge, Grafikdaten, Tabellen, Loader, Grafikzuordnung und Exit bleiben bytegleich.
Die Bewegung verwendet dieselben Records und dieselben Algorithmen an neuen Adressen.

Referenz ist Commit `778b7d41c26086dc143312453ce033ea9e8d8130`:

| Artefakt | Vorher SHA-256 | Korrigiert SHA-256 |
| --- | --- | --- |
| PRG | `9669f87d80f5fa5d768294fb429a4ca295aca3b3e9627ef8b6064edb2627ea05` | `5f49f2cc05765f894aab6034ff3755a2680d15ea53c3790bb663deb7fcaa1dc8` |
| D81 | `17bd9404b4151125bad95bf1e4df28a5f44df0a53207ce117da847e87b9c3bdc` | `426534c38c5dcd474302ad2882e2b942a9c3f33a9c19547b54fc905922cbd1e0` |

Die alte Fassung bleibt über diesen Commit abrufbar. Die neue Fassung liegt weiter
unter `releases/stage_3b2/` im Branch `stage3b-2`, innerhalb des bestehenden Draft-PR #2.
Stage 3b-1 und `stage3b1-stable` bleiben unangetastet.

## Automatisch geprüft und noch unter XEMU zu prüfen

23 Tests bestehen mit dem bereitgestellten ROM. Die bisherigen 18 prüfen
Originaldaten, variable Recordgrenzen, Index 14 → Typ 12, Grafik-DMA/Rückvergleich,
Guards, Fehlerpfade, definierte Engine-Patches und D81-Dateien. Fünf neue Tests prüfen:

- Erhalt des gesamten KERNAL-Bereichs `$1000–$15FF` bei Initialisierung, 24
  Bewegungs-/Render-/Animationsschritten, Diagnostik und Exit.
- Vollständigen Preload, Engine-Start, `X` via modelliertem GETIN, Wiederherstellung
  der gesicherten VIC-Register und 2 KB Color-RAM, sowie erneuten Engine-Start/Exit.
- Exakt 53 geänderte Operandenbytes gegen die SHA-256 der bisherigen PRG-Datei.
- Echte ROM-Cursorroutine: Deaktivierung bleibt mit neuer Objektkopie erhalten;
  alte Objektkopie aktiviert den Cursor und erzeugt den Countdown 255.
- Echte ROM-Cursorroutine: alter Fehler erlaubt das Sichern und spätere
  Zurückschreiben einer simulierten roten RRB-Farbe trotz BASIC-Farbrestaurierung.

Die ROM-Tests führen unveränderte Instruktionen mit einer begrenzten 65CE02-
Erweiterung des Hostmodells aus; KERNAL-IRQ, VIC-Ausgabe und Tastatur sind kein
vollständiger XEMU-Lauf. Ohne `MEGA65_ROM` werden nur die zwei ROM-Tests übersprungen.

```sh
MEGA65_ROM=/pfad/MEGA65.ROM python3 -m unittest discover -s tests -p 'test_stage3b2*.py' -v
```

Unter XEMU bitte Originaldaten/Grafiken, alle 24 Pixies und Joystick erneut prüfen.
Mehrmals mit `X` nach unterschiedlichen Laufzeiten beenden: BASIC-Cursor muss
ohne Tastendruck normal blinken, ohne rote Linie. Danach `LOAD"STAGE3B2",8` und
`RUN` erneut ausführen. Stage 3b-2 erst nach Benutzerbestätigung als stabil markieren.

Quellen zur RAM-Belegung:
[offizieller User Guide](https://github.com/MEGA65/mega65-user-guide/blob/cefce48d72e5c98d732c0589461d62b205b5165f/memory.tex).
Die ROM-Diagnose selbst basiert auf der vom Benutzer bereitgestellten Binärdatei.
