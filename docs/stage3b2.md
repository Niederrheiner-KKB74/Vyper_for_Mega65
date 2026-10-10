# Stage 3b-2 – Indexzuordnung bestätigt, Levelrecord-Format noch offen

## Ausgangspunkt

Basis ist die vom Benutzer bestätigte stabile Referenz `stage3b1-stable`.
Stage-3b-1-ASM, PRG und D81 bleiben unverändert. Entwicklung auf `stage3b-2`.
Die Bewegungs-/Joystick-/Exit-Logik wurde nicht verändert.

## Belegte Ergebnisse

`tools/analyze_stage3b2_data.py` prüft die vorhandenen Originaldateien und schreibt
[stage3b2-data-analysis.json](stage3b2-data-analysis.json). Das Format von VYGR ist
im Originalarchiv `assets/STAGE3A_DATA_PREPARATION.zip` beschrieben und wird durch
dessen `build_vygr.py` belegt:

- Header `VYGR`, Little-Endian-Version 1, 36 Typen.
- 36 Verzeichniseinträge zu je 8 Byte: Dateioffset DWORD, Framezahl WORD,
  reserviertes WORD 0. Typreihenfolge `type_01` bis `type_36`.
- 239 Frames à 128 Byte, lückenlose Datenbereiche bis Dateiende.
- Alle 239 Frames sind bytegleich mit den jeweiligen Original-NCM-Dateien aus
  `vyper_all_enemy_types_exact_ncm.zip`.
- Laufzeitadresse eines Frames: `$54000 + Typ-Dateioffset + Frameindex * 128`.
  Adressen und Framezahlen für alle 36 Typen stehen im JSON-Bericht.

Für VYLV sind Header, Version, Verzeichnis und die erste Signatur aus den bisherigen
Loadern und den Binärdaten belegbar. Alle 100 Verzeichniseinträge sind lückenlos,
innerhalb der Datei und beginnen mit ihrer jeweiligen Little-Endian-Levelnummer.
Level 1 liegt bei Dateioffset `$328` / RAM `$40328`, ist 849 Byte lang und beginnt mit:

```
01 00 02 16 10 00 02 00 0B 00 14 00 00 00 9E 00
```

Dies ist ein Rohbefund. **Die übrigen Levelrecord-Felder werden ohne Formatbeleg
nicht als Gegnertypen, Zähler, Positionen oder Animationen interpretiert.**

## Belegter Blocker

Die README im Original-Datenpaket nennt ausdrücklich:

> Offene Datenfrage: Level-Grafiktypindizes 0..37, NCM-Typen 1..36.
> Mehrere Level haben mehr als vier unterschiedliche Typindizes.
> Die Zuordnung und Slot-Strategie muessen vor der Spielintegration
> abgeglichen werden.

### Bestätigte Indexzuordnung

Der Benutzer hat die Indexzuordnung verbindlich geklärt:

| VYLV-Grafikindex | VYGR-Typ |
| --- | --- |
| 0 und 1 | 12 |
| 2 bis 37 | Index minus 1 (Typ 1 bis 36) |

Diese Regel ist in `vygr_type_for_level_index` implementiert und für alle 38
zulässigen Indizes gegen das Originalgrafikverzeichnis geprüft. Werte außerhalb
0..37 werden abgewiesen. Die historische Indexfrage im Datenpaket ist damit gelöst;
der Originaltext bleibt als historische Quelle im Analysebericht erhalten.

### Verbleibende Formatfrage

Das Repository enthält `build_vygr.py` im Datenarchiv, jedoch keinen VYLV-Erzeuger
und keine vollständige Levelrecord-Formatspezifikation. Die bestätigte Zuordnung
sagt noch nicht, **an welchen Offsets die Grafikindizes in Level 1 stehen** und wie
Gruppen-/Gegnereinträge durchlaufen werden. Auch das Amiga-Grafikmanifest belegt
diese Verbindung zu den Levelrecord-Feldern nicht.

Damit lassen sich die tatsächlich benötigten Level-1-Typen noch nicht zuverlässig
bestimmen. Die Bytes `10 00 02 00` werden nicht als angebliche Typen interpretiert.
Benötigt wird der originale VYLV-Erzeuger oder die Beschreibung der Einträge mit
Offsets, Längen und Grafikindexfeld. Erst daraus ergibt sich die Zuordnung zu den
bestehenden Test-Pixies; Bewegungen bleiben separat erhalten.

## Integrationsgrenzen aus der Engine

Die jetzige Engine benutzt zwei gemeinsam animierte, geschützte Glyphpaare:
Joystick-Pixie `$C840/$C880`, automatische Pixies `$C940/$C980`.
Die 23 automatischen Pixies referenzieren denselben Grafikslot. Für verschiedene
Gegnertypen sind daher getrennte Typ-/Frameslots und gezielte Änderungen der
Grafikreferenzen im Renderer erforderlich; ein globales Überschreiben des bisherigen
Slots würde allen automatischen Pixies denselben Typ geben.

Die bestehende Routine `s2ja_animate_pixies` kopiert zudem weiterhin Typ-2-Frames
aus `$A200..$A57F` in diese Slots. Nur ein einmaliger DMA-Grafiktransfer wäre daher
keine funktionierende Integration: beim nächsten Animationswechsel würden die
neuen Grafiken überschrieben. In Stage 3b-2 muss ausschließlich die Grafikquelle/
Frameauswahl angepasst werden, bei unveränderter Animationsuhr und Bewegungslogik.
Framezahlen und Bankgrenzen müssen aus dem validierten VYGR-Verzeichnis stammen.
Die endgültige Slotbelegung wird nach der bestätigten Typzuordnung festgelegt.

## Reproduzierbare Prüfung

Keine zusätzlichen Python-Pakete erforderlich:

```sh
python3 tools/analyze_stage3b2_data.py --output docs/stage3b2-data-analysis.json
python3 -m unittest discover -s tests -p test_stage3b2_data.py -v
```

Acht Tests bestanden: bestätigte Zuordnung aller 38 Indizes zu vorhandenen
Originaltypen, Zurückweisung ungültiger Indizes sowie Originalverzeichnisse und alle Frames, überlappende
Levelrecords, falsche Levelnummer, ungültiger Grafikoffset, abgeschnittene Grafikdatei
und ein Frame, der vom Originalarchiv abweicht. Die Prüfer lehnen beschädigte Daten
ab und halten die nicht belegte Typzuordnung ausdrücklich leer.

Noch **kein Stage-3b-2-ASM/PRG/D81**: ein scheinbar funktionierender Build mit
erfundener Zuordnung wäre keine gültige Umsetzung. Nach Klärung des Levelrecord-Formats folgen die
DMA-Grafikübertragung, gezielte Frame-/Renderer-Anpassung, Build und D81 sowie
Regressionstests gegen `stage3b1-stable` und eine neue XEMU-Abnahme.
