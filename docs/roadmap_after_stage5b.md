# Vyper für MEGA65 – Restarbeiten nach Stage 5b

**Stand: 11.10.2026.** Stage **5b ist vom Benutzer als Stable bestätigt**: alle 100 Level spielbar, korrekte Zuordnung und Darstellung der 38 Gegnertypen; die eigentliche Spielmechanik ist nach Benutzerabnahme funktionsfähig. Dieser Stand bleibt unveränderliche Ausgangsbasis. Dieses Dokument ist **Planung**, kein Implementierungsnachweis.

## Prioritäten und geplante Stages

| Stage | Gegenstand | Priorität | Hinweise |
|---|---|---|---|
| **5c** | **Originale levelabhängige Gegner-Farbpaletten** | **Höchste** | Amiga-`Color` analysieren, bereits geleistete Vorarbeiten auffinden und prüfen, reproduzierbar `VYCL.DAT` erzeugen, 100 Level korrekt zuordnen |
| 5d | Original-Titelgrafik während des Ladens | Mittel | Bereits früher aus `logo.data` rekonstruierte Grafik/Palette wiederfinden; Anzeige vor und während VYLV/VYGR/VYCL-Laden |
| 5e | Startbildschirm mit 32 Originalgegnern und Menü | Hoch | Originalreihenfolge und Animation, `INITIAL LEVEL`, `F1 START 1 PLAYER GAME`, `F2 START 2 PLAYER GAME`, `F3 VIEW HIGH SCORES`; Auswahl über Tastatur/Joystick |
| 5f | Extraleben nach je 3 regulär abgeschlossenen Levels | Hoch | HUD max. 8 Symbole, interner Zähler >8 möglich; +/- Testnavigation darf keinen Bonus erzeugen; Zyklus über Level 100 beachten |
| 5g | Highscore-Tabelle und F3-Ansicht | Mittel | Erst im RAM, später optional persistente Diskdatei; Format/Anzahl noch zu entscheiden |
| 5h | Zweispielermodus | Mittel | Getrennte Scores, Leben, Levels und Wechsel; genauer Amiga-Wechselmodus noch zu verifizieren |
| 5i | Originalnahe Soundeffekte | Mittel | Original-Amiga-Sounddaten untersuchen, MEGA65-Wiedergabe festlegen |
| 5j | Originalnaher Übergang zwischen Levels | Niedrig | Bestehendes LEVEL CLEAR erhalten und ggf. animieren |

## Stage 5c – nächster verbindlicher Schwerpunkt

**Ziel:** Originale Farbpalette der Gegner **pro Level** statt der bislang statischen bzw. provisorischen Farben. Die bereits bestätigten Pixelformen, Masken, Animationen und Typzuordnungen aus Stage 5b dürfen nicht verändert werden.

### Historische Vorarbeiten, die zuerst wiedergefunden werden müssen
- In der früheren ADF-Analyse wurde die Originaldatei **`Color`** als wahrscheinliche bzw. beobachtete Quelle der Levelpaletten identifiziert. Der Benutzer hat Farbwechsel am Beginn der Amiga-Level bestätigt.
- Frühere Palettenextraktion war bei der Original-Titelgrafik erfolgreich; die Spielerpalette wurde separat visuell freigegeben.
- **Noch kein in dieser Dokumentation verifizierter vollständiger Datensatz der 100 Gegnerpaletten oder eine bewiesene Indexformel.** Nicht so tun, als lägen bereits fertige VYCL-Bytes vor.
- Originalquelle: `VYPER.ADF` / Datei `Color`; falls im Codex-Workspace nicht vorhanden, erneut bereitstellen lassen. Frühere Projektanalysen, GitHub-Dateien und verfügbare WinUAE-Dumps auf Farbtabellen, Paletteindizes und Codezugriffe durchsuchen.

### Konkrete Arbeitsschritte
1. `Color` aus dem ADF verlustfrei extrahieren, Format, Zahl der Paletten, Wort-/Byteordnung und Farbkanalbreite prüfen; Amiga-RGB-Registerwerte und ggf. per-Level-Auswahl anhand Originaldaten ermitteln.
2. **100 Level → Palettenindex** aus Original-Level-/Color-Daten rekonstruieren. Abweichungen und Unsicherheiten je Level dokumentieren, statt Werte zu erfinden.
3. Farben in MEGA65-VIC-IV-Palettenformat umrechnen; getrennte, **konstante Spielerpalette** bewahren. Ebenso HUD-/Explosionsfarben vor Überschreiben schützen.
4. Reproduzierbares Konvertierungsskript und versionierte **`VYCL.DAT`** mit Signatur/Version, Levelverzeichnis, Palettendaten und Prüfsummen erstellen. Dateiformat vor Implementierung dokumentieren.
5. Loader auf drittes SEQ-Asset erweitern; Dateigröße, High-RAM-Belegung, DMA, Fehlerbehandlung und sauberen Exit prüfen. Beim **jedem** Levelstart einschließlich +/- und 100→1 korrekte Palette aktivieren.
6. Visuelle Vergleiche mit WinUAE in Level 1, 2, 5, 10, 11, 20, 21 sowie Leveln mit mehreren Gegnertypen; Level-5b-Regression über alle 100 Level.
7. Vollständige KickAssembler-Quellen, PRG, D81 mit `VYLV.DAT`, `VYGR.DAT`, `VYCL.DAT`, Buildskript, dokumentierte Palettenzuordnung und Testbericht bereitstellen.
8. **Stage 5c erst nach ausdrücklicher Benutzerabnahme als Stable markieren.**

### Abgrenzung
Stage 5c soll **nicht** nebenbei Titelgrafik, Startmenü, Zweispielermodus oder Sound integrieren. Wenn Hardware-Palettenbänke/RRB-NCM die getrennte Spieler- und Gegnerpalette erschweren, zuerst technische Analyse und Alternativen vorlegen, bevor die stabile Engine umgebaut wird.

## Spätere Detailentscheidungen (noch offen)

- `INITIAL LEVEL`: zulässige Auswahl 1–100 oder nur freigeschaltete Levels? Noch nicht festgelegt.
- Zweispielermodus: Wechselbedingungen anhand Amiga-Original prüfen.
- Highscore-Persistenz, Tabelle/Eintragszahl, Namenserfassung und Soundhardware noch offen.
- Extraleben-Zählung nach regulärem Levelabschluss; **nicht** durch +/- auslösbar. Ob bereits gestarteter Initial Level die Zählung beeinflusst, vor Umsetzung definieren.
- Originalstartbildschirm: 32 gezeigte Typen sind nicht gleich allen 38 VYGR-Typen; Original-Anordnung aus WinUAE-Snapshot verwenden, nicht frei sortieren.

## Bewährte Spielregeln (nicht verändern)
- 100 Level, nach Level 100 wieder Level 1; Score/Leben erhalten.
- +/- Testtasten strikt 1..100 ohne Umlauf.
- Player X-only, 1 Pixel pro 50-Hz-Frame; Formation −8..+8, 1 Pixel alle 2 Frames.
- Maximal 3 angreifende Gegner und 4 gegnerische Hardware-Sprite-Schüsse; 2 Player-Schüsse.
- `attack_index` pro Gegner bestimmt dessen Originalkurve.
- Score: `100 + 50*((level-1)//10)` Formation, `175 + 50*((level-1)//10)` ENTRY/ATTACK.
- Level Clear: Joystick-Button für nächsten Level; Game Over: R für Neustart, X für BASIC.

**Keine Änderungen an Stage 5b Stable durch dieses Dokument.**
