# Stage10a6: Angriffe in Level 25/50/99/100

Basis: main `fb3bf749b1987d1baad4db036ca9cd8c49f59e5f`, Stage10a5 Stable.
Separate Engine-/Overlayquellen und eigener Builder; Stable-Dateien unverändert.

## Änderung

Der validierte Levelheader setzt `attack_allowed=1` auch in diesen vier Levels.
24 Bytes Sonderfallprüfung werden durch 24 NOPs ersetzt. Keine neuen RAM-Bereiche
oder verschobenen Folgeadressen. Decoder, Auswahl, Intervalle 100/30 Frames,
höchstens drei Angreifer und Respawn-Sperre bleiben unverändert.

## Originalkurven

| Level | Kurvenbytes | Gegner | Schritte bis Port-Y >= 200 |
| --- | --- | --- | --- |
| 25 | 01 / 01 | 22 | 179–200 |
| 50 | 01 / 01 | 22 | 179–200 |
| 99 | 07 / 06 / 06 / 07 | 22 | 23–34 |
| 100 | 07 | 22 | 20–29 |

Die signed Nibble-Deltas sind X=0 und Y=+1, +6 oder +7: senkrechte Angriffe.
Der bestehende Decoder wiederholt die Bytes bis zum unteren Rand. Schrittzahlen
gelten ab den normalisierten Formationsplätzen des Ports, nicht ab Amiga-Y.
In Level25/50 bleibt Index1 unbenutzt. Originaldaten bleiben unverändert.
Historische Sperrvermerke dokumentieren weiterhin die damaligen Stände.

## Reproduktion und Auslieferung

Python3, Java, gepinnter KickAssembler5.25 und offizieller ZX0-v2-Kompressor:

```
python tools/build_stage10a6.py --kickass /path/KickAss.jar --zx0 /path/zx0
python -m unittest discover -s tests -p "test_stage10a6*.py" -v
```

Tests benötigen py65==1.2.0. Auslieferung unter `releases/stage_10a/stage10a6/`:
PRG, D81, ASM, Symbole, Buildbericht und SHA256SUMS.txt.

## Hardware-Abnahme offen

Hosttests sind kein XEMU-/Hardwaretest. Alle vier Level prüfen: Start aus
Formation, senkrechter Flug, Schüsse/Sound, Rückkehr von oben, höchstens drei
Angreifer, keine neuen Starts im Todes-/Respawnfenster sowie Levelwechsel
25 auf 26, 50 auf 51, 99 auf 100 und bisheriges Verhalten nach Level100.
Noch nicht Stable; Merge erst nach Benutzerfreigabe.
