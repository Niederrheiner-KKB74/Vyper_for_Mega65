# Debut-Y-Geometrie: isolierter Vergleich A/B/C (Issue #37)

**Keine Stable-Stage.** Branch `test-debut-y-geometry`, direkt aus
`stage5c-stable` (`2997719d704095afc630830435cb2d2f76b7f696`, bestätigter
Programmstand `2fb8308b886980f3d0e89a1ae19faf3937c6903f`). Stage 5c sowie
Stage 5d-0/5d-1, ihre Branches, Tags, Quellen und Releases bleiben unverändert.
Keine Titelbild-Integration; alle drei Programme sind unabhängige Stage-5c-Tests.

## Definition und zentrale Transformationsstelle

| Variante | ENTRY-Präsentations-Y |
|---|---|
| A | `Y` |
| B | `Y - 16` |
| C | `floor(Y * 200 / 232) = floor(Y * 25 / 29)` |

C ist ausdrücklich eine **Testhypothese**, keine belegte Amiga-Originalregel.
Alle Programme verwenden dasselbe Playfield X=0..239, Y=0..199; Player-Y=184,
Playerstart-X=104 (16 Pixel Breite). Videoauflösung, Clipping und Grafikdaten
bleiben unverändert. `+`/`-` wechseln weiterhin direkt die Level.

Die Stage-5c-Architektur verwendet `entry.e_ylo/e_yhi` sowohl für Rendering
als auch für signed Kollisionsboxen und ENTRY-Schüsse. Die Testfunktion
`ygeometry.postframe` projiziert deshalb einmal die gemeinsamen sichtbaren
Koordinaten **nach** originalem Bewegungsschritt und `attack.a_postframe`.
Nur `c_es=ENTRY(2)` **und** `e_phase=Kurve(1)` werden transformiert.
WAIT_ENTRY, RETURN, FORMATION, ATTACK, EXPLOSION und DEAD werden ausgeschlossen.

Der originale signed16-Y-Wert wird pro Gegner separat gesichert.
`ygeometry.restore` stellt ihn vor dem nächsten `entry.e_objects`-Schritt
wieder her. Dadurch rechnen Decoder und Kurvencursor ausschließlich auf der
originalen Bahn; keine wiederholte Skalierung/Offsetakkumulation. Der
Legacy-Spiegel `s2i_y` folgt der Präsentation, sodass auch die gespeicherte
Explosionsposition zur sichtbaren Trefferposition passt. Bei einem Treffer
bleibt die projizierte Position für die Explosion erhalten; sie wird nicht
auf den logischen Kurvenpunkt zurückgesetzt. `entry.e_init` löscht die
Projektionsflags bei Levelwechsel und Neustart.

Die drei einzigen Hooks werden beim Build aus dem eingefrorenen Original-
`stage5c_entry.asm` erzeugt: `e_init → clear`, `e_objects → restore`,
`e_motion_done → postframe` (ruft das originale `attack.a_postframe` zuerst).
Alle übrigen Spielkomponenten werden unverändert übernommen. Die einzige
zusätzliche Importzeile liegt im generierten Hauptquellcode, nie im stabilen
Original. Vollständige generierte ASM-Dateien liegen in jedem Release-Unterordner.

## Mathematik, Speicher und Zeitbasis

A ist eine Identitätsfunktion. B verwendet signed16-Subtraktion; alle 100
Originalkurven liegen einschließlich Startpunkten zwischen Y=0 und 216,
B also zwischen −16 und 200. Für künstliche Eingaben ist B auf
−32752..32767 begrenzt, damit das signed16-Ergebnis darstellbar bleibt.
C unterstützt die vollständige signed16-Eingabe: Betrag auch für −32768,
24-Bit-Zwischenprodukt (maximal 819200), unsigned Division durch 29;
negative Ergebnisse werden mit Rest nach unten gerundet, z. B. −1 → −1.
Kein 8-Bit-Koordinatenüberlauf. X und der Gegnerindex werden nicht geändert.

Zusatzcode und private Daten liegen im nachgewiesenen freien Bereich
`$7700–$794F`, zwischen dem originalen Attackparser `$7608–$76B1` und
Schussinitialisierung `$7951–$79F1`. Tatsächliche Enden: A `$77BB`,
B `$77CE`, C `$7859`; 66 Bytes für 22 logische Y-Paare und Flags.
Die sechs zusätzlichen Hookbytes passen in den ENTRY-Code vor `$5B80`.
Keine Änderung an DOS, ROM, Original-DAT-Zielen, Levelrecord, Pixiepuffern,
Screen-/Color-RAM, Palette oder DMA-Listen. Ausgaben/Messungen erfolgen nur
im Hosttool, niemals in einer zeitkritischen Rasterroutine.

Gruppenstarts, Wartezähler, Kurvenbytes, Cursor, Delta-Decoder, Punktanzahl,
Einflugintervall und 50-Hz-Schrittzählung bleiben unverändert. Der Zusatzcode
benötigt CPU-Zeit; eine zyklusgenaue Raster-/Hardwaregarantie wird nicht aus
dem Hostmodell abgeleitet. XEMU-Abnahme steht aus.

## Messdefinition

Reproduzierbare Rohdaten: `releases/debut_y_geometry_test/diagnostics.json`.
`tools/analyze_debut_y_geometry.py` liest unveränderte Originalrecords und
berechnet jeden Kurvenpunkt mit dem bestätigten sign-magnitude-Decoder.
Die erste Startposition bleibt unsichtbar, bis eine nichtzero Delta-Bewegung
stattfindet. Der letzte Kurvenbyte schaltet in der stabilen Engine bereits
auf RETURN; dieser letzte Punkt wird daher nicht mehr transformiert.
Min/max ENTRY enthalten den Startpunkt, nicht den ersten RETURN-Punkt.

„Render-Y“ bezeichnet den projizierten Ursprung von tatsächlich das Spielfeld
schneidenden, freigegebenen Pixie-Boxen; vollständige Offscreen-Boxen fehlen.
„Sichtbar bis“ ist die tiefste inklusive Boxpixelzeile, mit `Y+15` und Clipping
an 199. Transparente Pixel können früher enden. Die JSON enthält zusätzlich
den tiefsten **nichttransparenten** Pixel über alle Original-Animationsframes
und die dortigen X-Positionen; die konkrete Animationsphase ist nicht festgelegt.
Diese zusätzliche Messung ist eine Hüllkurve, keine Behauptung über einen
bestimmten XEMU-Frame.

Abstand = `184 - (Y+16)` für die ungekürzte 16-Pixel-Box; negative Werte zeigen
vertikale Überlappung. Clipping kann den sichtbaren Abstand begrenzen (zusätzlich
im JSON). Der Abstand allein bedeutet keine Kollision: X muss ebenfalls passen,
und die unveränderte Kollisionsbox hat weiterhin zwei Pixel Inset. Die letzte
Spalte beschränkt den Boxabstand deshalb zusätzlich auf Überlappung mit dem
zentrierten Player-X-Bereich 104..119.

## Logische und transformierte Y-Bereiche, Level 1–3

| Level | Gruppe | Variante | Start-Y original | Logisches ENTRY-Y | Transformiertes ENTRY-Y |
|---|---|---|---:|---|---|
| 1 | 1 | A | 0 | 0..159 | 0..159 |
| 1 | 1 | B | 0 | 0..159 | -16..143 |
| 1 | 1 | C | 0 | 0..159 | 0..137 |
| 1 | 2 | A | 0 | 0..159 | 0..159 |
| 1 | 2 | B | 0 | 0..159 | -16..143 |
| 1 | 2 | C | 0 | 0..159 | 0..137 |
| 2 | 1 | A | 216 | 39..216 | 39..216 |
| 2 | 1 | B | 216 | 39..216 | 23..200 |
| 2 | 1 | C | 216 | 39..216 | 33..186 |
| 2 | 2 | A | 216 | 49..216 | 49..216 |
| 2 | 2 | B | 216 | 49..216 | 33..200 |
| 2 | 2 | C | 216 | 49..216 | 42..186 |
| 3 | 1 | A | 216 | 65..216 | 65..216 |
| 3 | 1 | B | 216 | 65..216 | 49..200 |
| 3 | 1 | C | 216 | 65..216 | 56..186 |

## Sichtbarkeit und Playerabstand

| Level/Gruppe | Variante | Max. Render-Y | Sichtbar bis | Abstand Y+16 → Player | X bei maximalem Render-Y | Abstand bei X-Überlappung |
|---|---|---:|---:|---:|---|---:|
| 1/1 | A | 159 | 174 | 9 | 120, 122, 124, 126, 128, 130 | 10 |
| 1/1 | B | 143 | 158 | 25 | 120, 122, 124, 126, 128, 130 | 26 |
| 1/1 | C | 137 | 152 | 31 | 120, 122, 124, 126, 128, 130 | 32 |
| 1/2 | A | 159 | 174 | 9 | 110, 112, 114, 116, 118, 120 | 9 |
| 1/2 | B | 143 | 158 | 25 | 110, 112, 114, 116, 118, 120 | 25 |
| 1/2 | C | 137 | 152 | 31 | 110, 112, 114, 116, 118, 120 | 31 |
| 2/1 | A | 198 | 199 | -30 | 9 | 23 |
| 2/1 | B | 197 | 199 | -29 | 10 | 39 |
| 2/1 | C | 183 | 198 | -15 | 10 | 43 |
| 2/2 | A | 198 | 199 | -30 | 30 | 96 |
| 2/2 | B | 197 | 199 | -29 | 30 | 112 |
| 2/2 | C | 183 | 198 | -15 | 30 | 106 |
| 3/1 | A | 198 | 199 | -30 | 10 | 6 |
| 3/1 | B | 197 | 199 | -29 | 10 | 22 |
| 3/1 | C | 183 | 198 | -15 | 10 | 29 |

Für Level 2 liegen die tiefsten Boxen weit links (X=9/10 beziehungsweise 30).
Der minimale Abstand bei horizontaler Nähe zum zentrierten Player beträgt
für Gruppe 1 A/B/C 23/39/43 Pixel, für Gruppe 2 96/112/106 Pixel.
Level 3: entsprechend 6/22/29 Pixel. Diese Messungen beziehen sich auf die
vollständige ungestörte Originalbahn; reale Treffer/Explosionen können eine
Bahn früher beenden. Bei bewegtem Player ändern sich die X-bezogenen Abstände.

## Unveränderter Übergang zur Rückkehr

RETURN startet am originalen letzten Kurvenpunkt und steuert unveränderte,
aktuell pendelnde Formationsziele an. Es gibt keinen Offset auf dem RETURN-Ziel.
Dadurch können B/C sichtbar springen. Die folgende Differenz enthält den
originalen letzten Kurvendelta sowie den Wegfall der Projektion:

| Level/Gruppe | Variante | Letztes projiziertes Y | Erstes RETURN-Y original | Differenz |
|---|---|---:|---:|---:|
| 1/1 | A | 29 | 29 | 0 |
| 1/1 | B | 13 | 29 | 16 |
| 1/1 | C | 25 | 29 | 4 |
| 1/2 | A | 29 | 29 | 0 |
| 1/2 | B | 13 | 29 | 16 |
| 1/2 | C | 25 | 29 | 4 |
| 2/1 | A | 70 | 67 | -3 |
| 2/1 | B | 54 | 67 | 13 |
| 2/1 | C | 60 | 67 | 7 |
| 2/2 | A | 70 | 67 | -3 |
| 2/2 | B | 54 | 67 | 13 |
| 2/2 | C | 60 | 67 | 7 |
| 3/1 | A | 65 | 62 | -3 |
| 3/1 | B | 49 | 62 | 13 |
| 3/1 | C | 56 | 62 | 6 |

Diese Sprünge sind bewusst dokumentiert, nicht durch Änderungen an
Formations-/Rückkehrpositionen kaschiert. Eine spätere produktive Lösung
muss erst nach dem Amiga-Vergleich separat entschieden werden.

## Build und Test

```sh
git switch test-debut-y-geometry
git fetch origin --tags
python tools/build_debut_y_geometry.py --variant all --kickass /path/to/KickAss.jar
# Einzelvariante: derselbe Befehl mit --variant A, B oder C
python tools/analyze_debut_y_geometry.py
PYTHONPATH=tests:tools python -m unittest test_debut_y_geometry -v
```

KickAssembler 5.25 ist per SHA256 gepinnt; Python 3 und Java erforderlich.
Die Hosttests verwenden py65 1.2.0 und die vorhandenen CPU-/KERNAL-/DMA-/RRB-
Adapter des Repositories. Jeder D81-Dateikette wird vollständig rückgelesen;
alle DAT-Dateien sind byteidentisch zu Stage 5c Stable. Unabhängiger Zweitbuild
und Hosttestergebnisse stehen in `test-results.json` im Testrelease.

Die automatischen Prüfungen umfassen unabhängiges Laden/Starten aller drei
PRGs, signed Transformation einschließlich negativer Rundung, sämtliche
Kurvenpunkte/Startpositionen von Level 1–3, gemeinsame Render-/Kollisions-
koordinaten, WAIT-Unterdrückung, Explosion an sichtbarer Trefferposition,
Originalpixel mit Clipping, Schussursprünge und Vier-Schuss-Limit, Exit/erneutes
RUN sowie Original-Quell- und DAT-Identität. Der Bewegungsvergleich gegen das
stabile PRG umfasst 1200 Schritte je Level 1–3 und Variante, einschließlich
Gruppen-Wartezählern, Kurvencursorn, Auswahl, ATTACK, RETURN und Formationsdrift.
Die unbeeinflussten HUD-, Lebens-, Score-, Paletten-, Level-Clear- und Game-Over-
Quellen sind unverändert. Ihre vollständige frühere Regression wird hier nicht
als neu ausgeführt ausgegeben; die visuelle Gesamtprüfung bleibt beim Benutzer.

## XEMU-Vergleich mit dem Amiga-Original

D81s liegen in `releases/debut_y_geometry_test/A`, `/B`, `/C`; jeweils PRG,
VYLV.DAT, VYGR.DAT und VYCL.DAT. PAL, ROM V920395, BASIC 80×25 verwenden.

1. Frische XEMU-Sitzung mit A starten: `LOAD "VYPER_Y_A",8`, danach `RUN`.
2. Mit `+` Level 2 und danach 3 auswählen. Für B/C analog die jeweilige D81
   einlegen und `VYPER_Y_B` beziehungsweise `VYPER_Y_C` laden.
3. Möglichst gleiche Playerposition und Anfangssituation verwenden; zunächst
   nicht schießen, damit die Einflugbahnen vollständig sichtbar bleiben.
4. Unteren Einflugbereich, Playerabstand, teilweises Clipping und Übergang zu
   RETURN vergleichen. Danach Steuerung/Schüsse, Angriffe, Formation, Explosionen,
   Score/Leben, Level Clear, Game Over/R und X/DIRECTORY/erneutes RUN prüfen.
5. Gegen die Benutzer-WinUAE-/Amiga-Beobachtung vergleichen. Keine Variante
   ist vorab als originalgetreu oder Stable bezeichnet. Keine automatische
   Übernahme in Stage 5c oder Stage 5d-1.

Keine eigenen XEMU-/Amiga-/Hardwaretestergebnisse behauptet.

## Automatische Ergebnisse dieses Builds

Neun Prüfungen des vollständigen Laufs bestanden (140,190 Sekunden).
Der um explizite Zustandsabdeckung ergänzte Bewegungsvergleich bestand erneut
(104,676 Sekunden): WAIT, ENTRY, FORMATION, ATTACK und RETURN in allen
drei Levels tatsächlich durchlaufen. 69 Artefakte im unabhängigen Zweitbuild
byteidentisch (23 je Variante). Keine eigene XEMU-Abnahme.

Projektions-/Restore-Aufwand bei 22 ENTRY-Gegnern im CPU-Modell:

| Variante | Zusätzliche Modellzyklen für Projektion + Restore |
|---|---:|
| A | 3083 |
| B | 3655 |
| C | 49327 |

Diese Messung enthält die Original-postframe-Prüfung bei deaktiviertem
Angriffsscheduler, jedoch keine IRQ-, DMA-Bus- oder Rasterpipeline-Zeit.
Sie ist keine Garantie für Hardwaretiming; die 50-Hz-Abnahme erfolgt in XEMU.

Die Original-NCM-Masken ergeben für die tiefste nichttransparente Pixelzeile
(über alle Animationsphasen) in Level 2: A/B 199, C 196; in Level 3:
A/B 199, C 198. Die zugehörigen X-Werte stehen zusätzlich in der JSON.
