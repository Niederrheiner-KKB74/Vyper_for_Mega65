# Stage 4b – Player-Anpassung und Level-1-Dekodierbefund

**Vorbereitung, nicht Stable und noch keine vollständige Implementierung von
Issue #12.** Grundlage: `stage4a-stable` (`095b83e`), bestätigtes Programm `7c3a466`.
Branch `stage4b`; Stable-Quellen, Releases und Tags unverändert.

Die ergänzte Player-Anforderung wird vollständig umgesetzt. Der ebenfalls im
Issue verlangte Originaleinflug ist mangels verifiziertem Interpreter/Zeitbasis
noch blockiert. Der Testbuild behält daher den bisherigen Stage-4a-Gegneraufbau
und ausdrücklich als Test gekennzeichnete T/E-Angriffsmechanik. Diese Bewegungen
werden nicht als originale Level-1-Einflüge ausgegeben. F/N/P bleiben der
isolierte Stage-4a-Clippingtest. Keine erfundenen Kurven oder Formationssprünge.

## Endgültige Player-Geometrie

Logischer Bereich: `[0,240) × [0,200)`. Objektkoordinaten sind die linke obere Ecke,
Player-Grafik 16×16. Daraus folgen:

- Level-1-Start / R-Neustart: **X=(240−16)/2=112, Y=200−16=184**.
  Mittelpunkt X=120, Unterkante exklusiv Y=200.
- Joystick Port 2: ausschließlich X, weiterhin ein Pixel pro Bewegungstick;
  **0≤X≤224**. Up/Down ignoriert, diagonale Links-/Rechtsanteile wirken horizontal.
- Y bleibt 184 während Spiel und dreisekündiger Unverwundbarkeit. Der Player
  bleibt vollständig sichtbar und ragt nicht in das HUD ab X=240 hinein.
- Keine ungesicherte Aussage über eine exakte Amiga-Y-Koordinate: dies ist die
  verbindliche geometrische Position im bestehenden MEGA65-Playfield.

`v014_init_objects` setzt die neue Position sowohl beim Programmstart als auch
beim vorhandenen R-Neustart. `v014_move_record` behält das einmalige CIA-Sampling,
CRAM2K-Freischalten, horizontale Reihenfolge/Geschwindigkeit und Feuerbit bei.
Nur die linke Grenze 32→0 und die vertikalen Updateblöcke ändern sich; die
36 vertikalen Codebytes werden NOPs, alle folgenden Symbole bleiben identisch.

Schussursprung bleibt die bereits korrekte Live-Position: **X+8, Y=184**, also
Mitte/Oberkante. Bestehende native Sprite-Ursprungs-/Skalierungsberechnung,
zwei unabhängige Kanäle und Geschwindigkeit bleiben erhalten.
Die bestehende Player-Hitbox ist `[X+2,X+14) × [186,198)`; sie liest ebenfalls
Live-Positionen. Keine separaten alten Y-Konstanten werden verwendet.
Playerexplosion und Respawn speichern/restaurieren die Todesposition `(X,184)`.
Blinkzustand, 150-Tick-Unverwundbarkeit, Steuerbarkeit und Feuersperre bleiben.

Der Builder vergleicht das PRG mit Stage-4a-SHA256
`3da4cf49117ad07ac630dfad10ec30407ff62bc6e5051eac3c974bd8c5d002e2` und erlaubt nur
die zwei initialen Koordinaten, linke X-Grenze und vertikalen NOPs. **Keine**
Änderung an Schuss-, Kollisions-, Respawn-, Gegner-, HUD- oder Exit-Code nötig.
PRG-Größe, sämtliche alten Symboladressen und Speicherbereiche unverändert.

## Verifizierte Level-1-Struktur

Reproduzierbar: `python3 tools/analyze_stage4b_entry.py`;
maschinenlesbarer Befund: `docs/stage4b-entry-analysis.json`.
Die vorhandene bounds-geprüfte Recordstruktur wird direkt an `assets/VYLV.DAT`
geprüft, keine feste Gegnerlistenadresse im Parser. Mapping stammt ausschließlich
aus `assets/vylv_vygr_mapping.json`, Index 14 → Typ 15 bestätigt, sechs Frames.
Die historische Analyse mit Typ 12 wird nicht übernommen.

| Feld | Verifizierter Wert |
| --- | --- |
| Record-Dateioffset / Länge | `$0328` / 849 Bytes (`$0351`) |
| Header | Level 1, 2 Gruppen, 22 Gegner, Intervall-Rohwert 16, 2 Angriffskurven |
| Gruppe 0: Header / Kurvenbytes | relativ `$0008` / `$0010`, Datei `$0330` / `$0338` |
| Gruppe 0 | 11 Gegner, Start-Wörter `(20,0)`, 158 Kurvenbytes |
| Gruppe 1: Header / Kurvenbytes | relativ `$00AE` / `$00B6`, Datei `$03D6` / `$03DE` |
| Gruppe 1 | 11 Gegner, Start-Wörter `(220,0)`, 165 Kurvenbytes |
| Gegnerliste | relativ `$015B`, Datei `$0483`, 22 × 6 Bytes |

Start-Wörter werden als Original-Rohwerte dokumentiert. Der Datenbestand belegt
noch nicht, ob dies Pixie-Oberkante, Mittelpunkt oder eine andere Original-
Koordinatenkonvention ist. Ein ungeprüfter Offscreen-Offset wird nicht ergänzt.

### Dekodierhypothesen, ausdrücklich unbestätigt

Beispiel Gruppe 0: `02 12 02 02 12 02 12 02 ...`; Gruppe 1 startet mit
mehreren `00` innerhalb der Kurve. `00` ist somit kein nachgewiesener universeller
Endmarker. Beide plausible Nibblemodelle mit oberem Nibble X/unterem Nibble Y,
Skalierung 1 und einem Byte pro Tick liefern unterschiedliche Endpositionen:

| Hypothese | Byte `$92` | Byte `$0A` | Ende Gruppe 0 / Gruppe 1 |
| --- | --- | --- | --- |
| Sign-Magnitude (Bit 3 Vorzeichen) | ΔX=−1, ΔY=+2 | ΔX=0, ΔY=−2 | (120,29) / (118,29) |
| signed 4-Bit-Zweierkomplement | ΔX=−7, ΔY=+2 | ΔX=0, ΔY=−6 | (−58,−239) / (−352,−239) |

Die erste Hypothese erscheint geometrisch plausibler, **ist aber nicht bewiesen**.
Ihre Enden sind außerdem nicht die individuellen Formationsplätze. Achstausch,
Skalierung, Wiederholung und Tickzuordnung sind ohne Interpreter nicht verbindlich.
Ebenso unbekannt: Startabstand pro Gegner/Gruppe, Bedeutung der Rohzahl 16,
Kurvenende und nachgewiesener Mechanismus zur individuellen Formation.
Die Zuordnung aufeinanderfolgender Slots 0–10 / 11–21 zu Gruppen ist eine klar
markierte Reihenfolgehypothese, keine nachgewiesene Original-Schedulingregel.

### Originale Formationstabelle

Alle Werte aus den sechs Byte langen Originalrecords, Gegner-ID nullbasiert.
Grafikindex überall 14, bestätigter VYGR-Typ überall 15. „Gruppe?“ markiert die
noch nicht interpreterbestätigte zusammenhängende Slotzuordnung.

| Gegner | Gruppe? | Formation X | Formation Y | Angriffindex |
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

## Offene Voraussetzung für die Einflug-Engine

Im stabilen Repository, vorhandenen ZIP-Archiven, ursprünglichen Importpaketen
und aktuellen GitHub-main-Baum liegen kein Amiga-ADF/Dump, kein Original-
Kurveninterpreter und kein VYLV-Erzeuger/Original-Level-JSON vor. Die vorhandenen
Parser überspringen Kurven nur bounds-geprüft anhand ihrer Länge.
Benötigt wird der tatsächlich belegte Interpreter beziehungsweise eine
verbindliche Beschreibung für Nibbles/Koordinaten, Zeitbasis/Scheduling und
Formationstransition. Diese Rückfrage ist gestellt; der Player-Teil wartet darauf
nicht. Bis zur Klärung werden keine ENTRY-Cursor, Gruppen-Timer oder originalen
Formationszustände behauptet. Die komplette Issue-12-Abnahme ist noch offen.

## Build und Testen des Player-Vorbereitungsstands

```sh
python3 tools/build_stage4b.py --kickass /pfad/zu/KickAss.jar
PYTHONPATH=tests python3 -m unittest test_stage4b -v
python3 tools/analyze_stage4b_entry.py
```

Wie bisher: Java, Python und offizieller gepinnter KickAssembler 5.25;
CPU-Tests zusätzlich py65 1.2.0. Optional `MEGA65_ROM=/pfad/zu/MEGA65.ROM` für
die tatsächliche bereitgestellte ROM-Blinkroutine. ROM nicht im Release.
PRG/D81/ASM/Hashes/Buildreport: `releases/stage_4b/`.
D81 einlegen, `LOAD "STAGE4B",8`, `RUN`.

Unter XEMU prüfen:

1. Player unten mittig X=112/Y=184; Up/Down ohne vertikale Bewegung.
2. Diagonal nach links/rechts wirkt nur horizontal; beide Grenzen 0/224 halten,
   volle Grafik sichtbar, kein HUD-Überzeichnen.
3. Feuer bei X=0/112/224 startet in Player-Mitte/Oberkante; zwei Schüsse wie zuvor.
4. Gegnerschuss/Rammtreffer: Explosion unten an Todesposition, Lebensverlust;
   Respawn am gleichen X/Y, drei Sekunden steuerbar blinkend, kein Feuer/Treffer.
5. Letztes Leben, GAME OVER, R: unten mittig neu starten, Highscore erhalten.
6. F/N/P-Clippingtest unverändert; X sauber nach BASIC, zweiter RUN/LOAD möglich.

XEMU-Abnahme des Player-Vorbereitungsstands ausstehend. Die bisherige stabile
Stage 4a bleibt unverändert; Stage 4b wird erst auf ausdrückliche Freigabe Stable.

## Tatsächlich ausgeführte automatische Prüfung

- KickAssembler 5.25 erfolgreich; 43.777-Byte-PRG und vollständiges 819.200-Byte-D81.
- **23/23 Tests bestanden**, 112,484 Sekunden, tatsächliche bereitgestellte
  ROM-V920395-Blinkprüfung eingeschaltet. CPU-/DMA-/RRB-Fetch-Modelle, kein XEMU-Lauf.
- 32 Joystickkombinationen × fünf X-Positionen × ACTIVE/BLINK;
  vertikale Sperre, diagonale X-Anteile, beide Grenzen, unverändertes Feuerbit.
- Schussursprung und Hitbox bei X=0/112/224, Treffer unten bei Y=184,
  Todesposition/Explosion/Respawn, steuerbare Unverwundbarkeit und R-Mitte.
- Geerbte Clipping-, Animations-, Kampf-, Score-/Lebens-, GAME-OVER- und Exit-Tests;
  Gegnerbewegung/Grafiken unverändert. Absichtlich geänderte Playerposition und
  linke Grenze werden gegen die neuen Anforderungen geprüft.
- Nur **39 PRG-Bytes** gegenüber `stage4a-stable` geändert, keine zusätzlichen
  Bytes/Adressen; sämtliche alten Symbole unverändert. Stable-Dateien unverändert.
- Alle 14 erzeugten Release-Dateien beim unabhängigen Zweitbuild byteidentisch;
  Original-DAT-Hashes, Disk-Dateitypen/BAM/Dateiketten geprüft.

SHA256 des Vorbereitungsstands:

```
PRG b6757975262dff3a55ae9cb0b0b9df317bbae2be7732d808a857425fc6eec436
D81 f91587999d5108dfeb6cbd88601a620fc9eaed111742177edf64727054bbb36e
```
