# Stage 3b-2 – Level-1-Grafiken aus geladenem VYGR

Stage 3b-2 integriert die vom Benutzer bestätigte VYLV-Recordstruktur und verwendet
für die 22 Level-1-Pfad-Pixies Originalgrafiktyp **12** aus geladenem `VYGR.DAT`.
Basis ist `stage3b1-stable`. Dessen Quellen, Builder und Release-Dateien bleiben
unverändert. Neue Quelle: `src/engine/stage3b2.asm`; Artefakte: `releases/stage_3b2/`.
Assembly, D81 und 18 Host-Tests bestanden. **Stage 3b-2 ist noch nicht XEMU-bestätigt.**

## Bestätigtes Recordformat und Indexzuordnung

Die Formatbeschreibung stammt vom Benutzer. Die erwähnte Originaldatei
`vyper_original_100_levels_v1.json` liegt nicht im Repository; die Implementierung
arbeitet ausschließlich mit den vorhandenen DAT-Dateien und der bestätigten
Beschreibung. Sie erzeugt keinen Ersatz für diese Originalquelle.

Der 8-Byte-Recordkopf enthält Levelnummer WORD LE, Gruppenzahl BYTE, Gegnerzahl
BYTE, Einflugintervall WORD LE und Anzahl Angriffskurven WORD LE. Darauf folgen
Einfluggruppen mit Gegneranzahl, Start-X, Start-Y und Kurvenlänge (je WORD LE),
anschließend genau die angegebene Anzahl Kurvenbytes. Erst danach liegen die
Gegnereinträge: Formations-X WORD LE, Formations-Y WORD LE, Grafikindex BYTE,
Angriffsindex BYTE. Zuletzt folgen die Angriffskurven: Länge WORD LE und Kurvenbytes.

Beide Parser durchlaufen Gruppen und Kurven über ihre Längen. Die Gegnerposition
ist der daraus resultierende Cursor, **kein fest codierter Gegneroffset**.
Jeder Lese-/Sprungbereich wird gegen das Recordende geprüft, einschließlich
arithmetischem Überlauf im Assembler. Gruppen-Gegnersumme und exaktes Recordende
werden ebenfalls geprüft. Der Python-Parser prüft alle 100 Levels vollständig.

| VYLV-Grafikindex | VYGR-Typ |
| --- | --- |
| 0, 1 | 12 |
| **14** | **12 – ausdrücklich bestätigte Korrektur** |
| sonstige Indizes 2–37 | Index minus 1 |

Ungültige Indizes werden abgewiesen. Die historische offene Zuordnungsfrage im
Original-Datenpaket ist durch diese Benutzerbestätigung aufgelöst.

Level 1 liegt bei Dateioffset `$0328`, hat 849 Byte und zwei Einfluggruppen.
Der Parser ermittelt die Gegnerliste bei relativ `$015B`; der erste Eintrag ist
`62 00 2B 00 0E 00`. Alle 22 Einträge haben Index 14 und werden **Typ 12** zugeordnet.
Die im Bericht gespeicherte Gegnerposition ist ein ermittelter Befund, kein Parserparameter.
[Analysebericht](stage3b2-data-analysis.json) enthält die vollständigen Level-1-Felder
und das geprüfte VYGR-Verzeichnis. Alle 239 Frames in VYGR sind bytegleich mit dem
vorhandenen Original-NCM-Archiv.

## Grafikübertragung und unveränderte Bewegung

Der stabile SEQ-/SETBNK-Loader und sein vollständiger DMA-Rückvergleich bleiben
in Stage 3b-2 erhalten. Nach der Level-1-Kopie nach `$7600` durchläuft der neue
Assembler-Parser den Record. Der Typ wird aus den tatsächlichen Gegnereinträgen
bestimmt. Der zugehörige VYGR-Verzeichniseintrag wird aus High RAM nach `$6A00`
kopiert; Offset, Framezahl, reservierte Felder und vollständiger Framebereich
werden gegen das geladene VYGR-Ende geprüft.

Die Pfadgrafik liegt in einem zusätzlichen geschützten 256-Byte-Bereich:
`$9800–$983F` Guard, `$9840–$987F` oben, `$9880–$98BF` unten,
`$98C0–$98FF` Guard. Die 22 Pfad-Pixies referenzieren Glyphen `$261/$262/$263`.
Der Frame wird per bisheriger F018A-DMA-Konfiguration aus High RAM übertragen,
zurückgelesen und gegen einen separat aus der Quelle kopierten Frame byteweise
verglichen. Beide bisherigen Lesepuffer werden nach Abschluss des Ladens wiederverwendet.

Typ 12 besitzt im Original **nur einen Frame**. Deshalb bleibt die Pfadgrafik bei
Animationswechseln gleich; es werden keine Frames erfunden. Die ursprüngliche
Animationsuhr samt SPACE und +/- bleibt aktiv. Mehrframe-Auswahl und Umlauf sind
zusätzlich mit dem vorhandenen Typ 2 im Host-Test geprüft.

Joystick- und Orbit-Pixie behalten ihre alten Slots und die sieben Typ-2-Frames.
Positionen, Orbit-/Phasentabellen, Geschwindigkeiten, Rastertakt, Joystick und X-Exit
bleiben erhalten. Es werden keine Formationspositionen, Einflug- oder Angriffskurven
zur Bewegungssteuerung verwendet. Im Engine-Image ändern sich ausschließlich zwei
JSR-Zieladressen (Initialisierung/Animationswrapper) und sechs Grafikoperanden der
22 Pfad-Pixies. Alle übrigen Engine-Bytes werden mit Stage 3b-1 verglichen.
Neue Bereiche liegen bei `$3200–$35D9`, `$6A00–$6A07` und `$9800–$98FF`;
der Preloader reicht jetzt bis `$4B49`. Sie überschneiden sich nicht mit der
stabilen Engine-Belegung. Siehe [memory_map.md](memory_map.md).

Diese Stage ist ausdrücklich auf Level 1 mit 22 Pfad-Pixies und einem gemeinsamen
Grafiktyp begrenzt. Die Python-Analyse versteht alle 100 Records; der Laufzeitparser
weist eine andere Gegnerzahl oder verschiedene gleichzeitig benötigte Typen mit
Fehler `$07` zurück. Mehrtyp-Slotverwaltung und weitere Level sind spätere Stages.

Preload-Fehler `$07` (Record/Index/Scope) bzw. `$08` (Grafikverzeichnis) führen mit
Fehlermeldung zurück nach BASIC, bevor RRB startet. Ein DMA-Rücklesefehler während
RRB setzt `$04` und verwendet die ursprüngliche Exit-Routine ohne Textausgabe im
RRB-Modus. Die DMA-Listenänderungen während der Grafikaktualisierung sind durch
SEI/PHP/PLP geschützt. Kein neuer Interrupt-Handler, kein anderes ROM-Mapping.

## Reproduzierbarer Build und Tests

Python 3.9+, Java und dieselbe separat bezogene offizielle KickAssembler-5.25-JAR
wie bei Stage 3b-1. SHA-256-Prüfung der JAR und sämtlicher Originaldaten bleibt aktiv.

```sh
python3 tools/analyze_stage3b2_data.py --output docs/stage3b2-data-analysis.json
python3 tools/build_stage3b2.py --kickass /pfad/KickAss.jar
python3 -m venv /tmp/vyper-stage3b2-tests
/tmp/vyper-stage3b2-tests/bin/pip install -r tests/requirements-stage3b1.txt
/tmp/vyper-stage3b2-tests/bin/python -m unittest discover -s tests -p 'test_stage3b2*.py' -v
```

Der Builder entpackt ausschließlich vorhandene Baseline-Grafikbinaries temporär,
assembliert die neue Quelle und erzeugt PRG, D81, Quellkopie, Symbole, Speicherkarte,
Build-Bericht und SHA-256-Liste. Keine Änderungen an Stage 3b-1.
D81: `STAGE3B2` als PRG, `VYLV.DAT` und `VYGR.DAT` als SEQ; Dateiketten,
Nutzdaten, Blockzahlen und BAM werden geprüft. Ein separater Wiederholungsbuild
liefert byteidentische Artefakte.

18 Tests bestehen: vollständige Originaldatenanalyse, bestätigte Zuordnung,
ungültige Indizes, variable Gegneroffsets, falsche/trunkierte/überlappende Bereiche,
Originalframe-Vergleich, kompletter Maschinenprogramm-Preload, Assemblerparser
mit veränderter Kurvenlänge, Runtime-Grenzen, Typ-12-Frame/Guards, Mehrframe-Umlauf,
DMA-Fehler und BASIC-Rückkehr sowie expliziter Engine-/D81-Vergleich.
Die 6502-Tests modellieren KERNAL, DMA und Raster. Sie ersetzen keinen XEMU-Test.

## XEMU-Abnahme

1. Neues D81 in Laufwerk 8 einlegen: `LOAD"STAGE3B2",8`, dann `RUN`.
2. Erfolgreichen Preload und Start der 24 Pixies prüfen. Die 22 bisherigen
   Pfad-Pixies müssen die Originalgrafik von Typ 12 zeigen; Joystick-/Orbit-Pixie
   sollen aussehen wie Stage 3b-1. Keine beschädigten Guards/RRB-Reste.
3. Gleiche Pfade, Geschwindigkeiten, Joysticksteuerung und Begrenzungen gegen
   `stage3b1-stable` vergleichen. SPACE und +/- prüfen. Typ 12 hat nur einen Frame;
   die zwei bisherigen Typ-2-Pixies animieren weiterhin.
4. Mit X beenden: BASIC-Videomodus, Farben und Eingabe wie in Stage 3b-1. Erneut
   per LOAD/RUN starten. Keine Ausgabe im aktiven RRB-Modus.

Erst nach diesem Vergleich ist Stage 3b-2 als stabil abgenommen.
