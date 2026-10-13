# Stage7b1 – Levelübergang und weiße Projektilstriche

Issue [#53](https://github.com/Niederrheiner-KKB74/Vyper_for_Mega65/issues/53),
Branch `stage7b1`, 13.10.2026. **Nicht Stable; XEMU-Abnahme ausstehend.**

## Referenz, Build und Bedienung

Basis ist `stage7a2-stable`, Commit
`b4cc1f7f4f2250bb69664ba15613350942e29d9c`; dessen tatsächlich getesteter
Programmstand ist `1e40e3ba1278c9836cd484739f36de8afe839585`.
PR52 ist nachweislich gemergt, Mergecommit
`ef8f8ce61a5ea132f8f54a174eb9897f5fc83e0b`. Von diesem Integrationsstand
wurde der neue Branch angelegt. Alle bisherigen Stable-Quellen, Assets,
Releases, Tools und Tags bleiben unverändert; keine Archivbereinigung.

D81 `releases/stage_7b1/VYPER_STAGE7B1.d81`, XEMU PAL/50Hz, Joystick **Port2**,
MEGA65 mit Attic-RAM wie in den bisherigen Stages:

```basic
LOAD"STAGE7B1",8
RUN
```

Titel/Loader → originales animiertes Menü → F1 mit INITIAL LEVEL001–100.
Nach vollständigen Gegnerexplosionen bleibt LEVEL CLEAR stehen. Erst Loslassen
und ein neuer Feuerdruck starten den Übergang. X beendet auch mitten darin.
+/- im laufenden Spiel wechseln unmittelbar ohne Übergang; während des
Übergangs bleiben außer X die Spielsteuerung und Testnavigation gesperrt.
R nach GAME OVER und F2/F3-Platzhalter bleiben wie bisher.

Reproduktion: vollständiges Repo samt Stable-Tags/Originalassets, Java,
KickAssembler5.25 (Builder prüft JAR-SHA256), Python3.12/Pillow12.3, py65 für Tests:

```bash
python tools/build_stage7b1.py --kickass /pfad/KickAss.jar
PYTHONPATH=tests:tools:/pfad/py65 python -m unittest test_stage7b1 -v
python tools/package_stage7b1.py
```

Der Builder erzeugt sämtliche ASM/INC, Symbole, PRG, vollständiges D81 mit
VYTI/VYMN/VYLV/VYGR/VYCL und Reports unter `releases/stage_7b1/`.
Die bestätigte Sternverteilung wird vom unveränderten Stage7a2-Konverter
erzeugt. Originale VYTI/VYLV/VYGR/VYCL bleiben bytegleich; kein Originalasset
wird neu extrahiert oder geändert. Das ZIP enthält Quellen/Tools/Prüfbericht;
für einen Neuaufbau sind auch die unveränderten historischen Repo-Assets nötig.

## Projektilgrafik: nur Form und Farbe geändert

Alle sechs Hardware-Sprite-Projektilkanäle benutzen Bank2-Index10, das bereits
vorhandene konstante HUD-/Player-Schussweiß (`#FFFFFF`). Kein neuer Paletteindex,
kein Eingriff in die20 Gegnerpaletten, Cycling19 oder Sternfarben49–51.

Player und Gegner zeigen jetzt **1×4 logische Playfield-Pixel**, senkrecht.
Wie beim bisherigen Playerschuss entspricht das bei H640/V400 **2×8 nativen
Ausgabepixeln**. Keine neue Sprite-Skalierung und kein Videomoduswechsel.
Die21-zeilige Mono-Spritegrafik ist außerhalb der oberen acht Zeilen transparent.
Player verwendet `$C0` im ersten Byte jeder sichtbaren Zeile; Gegner `$30`.

Die unterschiedliche interne Leerpolsterung erhält exakt den alten Ursprung:
Player-Sprite X=`CHARX+2×shotX−1`, Gegner X=`CHARX+2×shotX−3`. Beim Gegner
liegen die weißen Bits zwei native Pixel weiter rechts; beide sichtbaren
Striche sind damit auf derselben bisherigen Schussmitte ausgerichtet. Es
wurde weder `p_publish` noch die Schusskoordinate verschoben. Ein gemeinsames
Muster ist nicht erforderlich; beide64-Byte-Muster haben dieselbe sichtbare Form.

**Trefferboxen bewusst unverändert:** die bisherige Höhe ist bereits4 logische
Pixel, Playerbreite1, Gegnerbreite3. Die Softwarehitbox ist unabhängig vom
Spritebitmap. Die schmalere Gegnergrafik ändert daher nicht die bisherige
3-Pixel-Treffertoleranz. Dieser Unterschied ist ausdrücklich beibehalten,
anstatt stillschweigend die Spielmechanik zu ändern. Flugrichtung, 8.8-Ziel-
berechnung mit gespeicherter Playerposition, Geschwindigkeiten, Feuerauslösung,
Limits2/4, Clipping und Kollisionscode bleiben unverändert. Diagonal fliegende
Gegnerschüsse behalten einen vertikalen Strich, da keine Grafikrotation existiert.

## Nicht blockierende Zustandsmaschine

Der existierende Hauptschleifen-Rasterwait liefert weiterhin den50-Hz-Takt.
Sterne und `cc_tick` laufen vor der Eingabe-/Levelbearbeitung. Der Übergang
liegt in `transitionfx.tick`; es gibt keine Zeitwarte-/Delay-Schleife.

| Zustand | Frames nach Bestätigung | Wirkung |
| --- | --- | --- |
| LEVEL_CLEAR_WAIT | beliebig | bestehender Text, normale Sterne; neuer Feuerdruck notwendig |
| STAR_ACCEL (state1) | 1–50 | achtfacher Sternmodus, dynamischer Vordergrund entfernt |
| COLOR_FILL (state2) | 51–74 | alle3 Frames das nächste Farbpaar von der Mitte nach außen |
| BLACK_CLEAR (state3) | 75–98 | alle3 Frames dieselben Bereiche schwarz überschreiben |
| LEVEL_INIT (state4) | 99 | Normalmodus, Sternreferenzen restaurieren, nächste Originalleveldaten initialisieren |
| PLAY (state0) | danach | normale Engine mit Originaleinflug |

Je COLOR/BLACK-Phase wird die erste Änderung beim dritten Phasenframe sichtbar;
die ersten zwei Frames halten den vorherigen Inhalt. Der erste Farbstreifen
erscheint somit Frame53, vollständige Farbdeckung bei74, volle Schwarzdeckung
bei98. Die reine sichtbare Sternbeschleunigung vor dem ersten Streifen dauert
ca.1,04 Sekunden. Der gesamte geplante Übergang dauert99 Ticks, ca.1,98 Sekunden;
die abschließende Levelinitialisierung ist der bestehende RAM-Initialisierungs-
pfad und kann je nach CPU/Core eigene Rechenzeit beanspruchen.

Bestätigung setzt `level.mode=2`. Die vorhandenen Modechecks stoppen Bewegung,
Objekte und Kampfticks; weder neue Kollisionen noch Lebensabzüge. Hardware-
projektile sind deaktiviert und ihre sechs Aktivflags gelöscht. Alle25
dynamischen RRB-Zeilentails werden mit den bereits geprüften Blank-DMA-Listen
retiriert: LEVEL CLEAR, Player und Restpixies verschwinden, HUD/Prefix bleiben.

Score, Leben, Highscore und Original-Levelnummer ändern sich während der
Animationsphasen nicht. Einflug-/Angriffskurven laufen nicht im Hintergrund
weiter. Cycling läuft unverändert pro Frame. Erst LEVEL_INIT benutzt den
bestehenden `level.transition`; 1→2,2→3,99→100,100→1 wie bisher. Kein erneutes
Diskladen während der Animation; die Original-DATs sind bereits im RAM.

## Stern-API und Parallax-Beschleunigung

Die vorhandene API `starfield_set_speed_mode` wird erweitert:

| A | Ergebnis |
| --- | --- |
| 0 | normal: Blau1/8, Rot1/4, Gelb1/2 Pixel pro Frame; Carry0 |
| 1 | beschleunigt: Blau1, Rot2, Gelb4 Pixel **je Frame**; Carry0 |
| ≥2 | nicht unterstützt, Zustand bleibt unverändert; Carry1 |

Mode1 ist für alle Klassen **achtfach schneller**, Verhältnis1:2:4 erhalten.
Der Faktor8 ist eine dokumentierte Annäherung, keine aus dem Amiga-Code
nachgewiesene Originalgeschwindigkeit. Es bleibt derselbe Renderer: pro
bewegtem Stern altes Pixel löschen und neues setzen. Keine8-fache Ausführung
der normalen Routine, kein zusätzlicher Layer und keine Zwischenpixelstreifen.
Y läuft modulo200; größter Zwischenwert203, sauberer Umlauf auch bei4-Pixel-Schritt.

Die gleiche Teilerphase zählt weiter, ohne Reset von Seed oder Positionen.
Sterne bleiben bis Ende des Übergangs schnell und bewegen sich auch unter den
Rechtecken; erst beim vollständig schwarzen Bild wird der Normalmodus gesetzt.
Das Wiederbinden legt die aktuellen Sternpositionen frei, ohne neue Verteilung
oder Reste. Die API bleibt unabhängig von Gegner-/Playerbewegung. X darf jeden
Zustand abbrechen; bei RUN/F1 setzt die vorhandene Initialisierung Normalmodus
und frischen Zustand wieder auf, einschließlich des Übergangszustands.

## Rechtecke im bestehenden Hintergrundprefix

**Geometrie/Farbreihenfolge/Takt sind eine reproduzierbare Annäherung.** Aus
Originaldaten sind diese Details noch nicht nachgewiesen; es wird keine exakte
Amiga-Originaltreue behauptet.

Playfield bleibt240×200, HUD beginnt bei logischem X240/nativ480. Die15
vorhandenen NCM-Zellen pro Zeile werden von der Mitte nach außen umgebunden:
erste Zelle Spalte7 (X112–127), anschließend jeweils Spalten7−r und7+r für
r1..7. Jede Zelle ist16 Pixel breit und wird auf allen25 Zeilen gleich ersetzt,
also ein breites vertikales Rechteck mit Höhe200. Links/rechts erscheinen
die jeweiligen Spiegelpaare im selben Tick. Reihenfolge pro Ring:
**Gelb, Blau, Rot, Gelb, Blau, Rot, Gelb, Blau**.

Vier64-Byte-Vollfarbglyphen: schwarz `$00`, blau `$11`, rot `$22`, gelb `$33`.
Sie verwenden die vorhandene getrennte Stern-Subpalette48–51. Die alten
NCM-Attribute `$08,$30` und der erste **opake** GOTOX bleiben unverändert.
Damit überdecken schwarze Glyphen ebenfalls die Sterne vollständig; es handelt
sich nicht um transparente Zusatzpixies. Jede Farbdeckung umfasst exakt das
gesamte Playfield, inklusive Y0/199, ohne Randlücken.

Nur Screen-Prefix-Bytes2–31 pro192-Byte-Zeile ändern sich. HUD-Bytes42–83 und
die übrigen schwarzen Zellen32–41 werden nicht angefasst. RRB-Zeilengröße96
Einträge und maximale dynamische Slots24 bleiben unverändert; null zusätzliche
RRB-Sterne, Rechteckpixies oder Hardware-Sprites. Nach Schwarzdeckung bindet
`starfield_bind` sämtliche375 ursprünglichen Sternkacheln wieder ein.

## Speicher und Kapazität

Alle Endadressen inklusiv; übrige Belegung ist Stage7a2:

| Bereich | Nutzung |
| --- | --- |
| `$1BC0–$1BCF` | Übergangszustand, Timer, Ring, nächster Level, temporäre Zeile/Spalte/Glyphen; nach Sprite-Registersicherung bis `$1B88`, vor Kampf-RAM `$1C00` |
| `$6650–$66C8` | F1-Initialisierung und Feuerbestätigung; nach Levelmanager, vor Blanktemplate `$6700` |
| `$B480–$B657` | gemeinsamer Sternkern mit Mode0/1 und Schrittbyte `$CFDE` |
| `$B6C0–$B74D` | Zustandsmaschinen-Tick; vor RRB-Renderer `$B800` |
| `$B760–$B7B4` | Prefix-Spaltenhelfer, Vollfarb-DMA-Liste und Musterwerte |
| `$18000–$1DDBF` | unveränderte24-KB-Sternfläche |
| `$1DE00–$1DEFF` | vier Vollfarbglyphen `$778–$77B`; nur in Spielphase, nach Sternfläche |
| `$8A00–$8A7F` | zwei veränderte/erhaltene Spritebitmaps, gleiche Größe/Pointer wie vorher |

DOS `$10000–$11FFF`/`$1F800–$1FFFF`, private Gegnerframes, Levelrecord,
VYLV/VYGR/VYCL, Attic und Titel-/Menüphasen bleiben unberührt. Die Solidglyphen
werden erst nach F1 im freigegebenen früheren Menü-Atlasbereich initialisiert.
Kein GPU-Fetch aus reserviertem `$60000` oder Attic.

**Runtime-Pufferprüfung:** `$5640–$56BF` ist der bestehende Grafik-Rücklese-
puffer, auch wenn er in der Assembly-Map nicht als eigener belegter Block
erscheint. Ein erster Entwurf des Spaltenhelfers dort wurde durch den langen
LEVEL-CLEAR-/Einflugtest als überschrieben erkannt und korrigiert. Der fertige
Helfer liegt bei `$B760`; der alte Puffer bleibt unverändert. Alle neuen Code-
bereiche besitzen explizite Assembler-Overlapguards.

## Aufwand und tatsächlich durchgeführte Prüfungen

Normale Sterne: im Mittel56/Peak192 Ein-Byte-DMA-COPYs pro Frame.
Schnelle Sterne: alle48 bewegen sich, **192 Aufträge/Nutzbytes pro Frame**,
also derselbe Peak wie vorher. Keine Vollbild-DMA im Frame. Pro Rechteckring
50 (Mitte) oder100 (Spiegelpaar) Screenbytes per physischem45GS02-Store;
nur alle3 Frames, kein zusätzliches Bitmapcopy. Beim F1-Start vier kleine
64-Byte-DMA-FILLs; am Übergangsbeginn einmal die vorhandenen25 Tail-/Color-
Blank-COPYs. Keine Paletten-DMA oder Paletteumbiegung für Rechtecke.

`starfield-measurements.json` enthält CPU-Modellwerte des tatsächlich assemblierten
PRG, nicht Hardware-Millisekunden. DMA läuft im Hostmodell instantan;
Descriptorfetch-/Buskosten sind nicht enthalten. Der gesamte LEVEL_INIT-Frame
enthält den unveränderten, größeren Level-/HUD-Neuaufbau und wird separat vom
kleinen Animationstick betrachtet. Reale50-Hz-Stabilität und fehlendes Flickern
müssen in XEMU geprüft werden. Keine Laufzeit-Testtasten/-Rastermarker hinzugefügt.

Hostprüfungen:

- Titel-/SEQ-/Menü/F1/F2/F3, alle32 Menüanimationen, volle CPU-Geschwindigkeit,
  ROMC-/IRQ-Gates, Originaldateien und komplette D81-Ketten/BAM;
- normale Sternraten, Seed,1.600 Frames, transparente Originalpixies/Clipping,
  Paletten/Cycling für alle100 Levels;200 Fastframes mit exaktem Modulo/Verhältnis;
- Spritebytes aller sechs Kanäle, konstantes Weiß über100 Levelinitialisierungen,
  unmodifizierter gesamter Kollisionscode und originale1×4/3×4-Hitboxen;
- exakt50/24/24/1 Übergangsticks, alle375 Prefix-Zellen vollständig farbig und
  danach schwarz, HUD-/Palettebytes unverändert (außer normalem Cycling19),
  Positionen/Phase ohne Reset und alle Overlayreferenzen nachher entfernt;
- 1→2,2→3,99→100,100→1, Feuerentprellung, +/- ohne Animation, Score/Leben/
  Highscore erhalten; X in allen vier Phasen und erneutes RUN/F1;
- bestehende Kampf-/Einflug-/Angriffs-/Rückkehr-/Schuss-/Explosions-/Respawn-
  regression, Game Over/R, Player1Pixel/Frame und unveränderte Stable-Dateien.

Die endgültige Testanzahl und Reproduktionsnachweise stehen in `test-report.json`
und `host-tests.txt`: **39 Tests bestanden;48 Dateien aus zwei unabhängigen
Builds bytegleich.** Normale Sternroutine: Mittel7486,375/Peak19620 CPU-
Modellzyklen; All48-Wrap19722. Der gemessene komplette Übergangs-Framepeak
1126968 Modellzyklen enthält den bestehenden Level-/HUD-Neuaufbau, nicht nur
die Rechteckroutine; Details in `transition-measurements.json`. Keine Umrechnung
in behauptete Hardware-Millisekunden. **Kein eigener XEMU-Test behauptet.** Die erfolgreiche
Stage7a2-Abnahme stammt vom Benutzer; Stage7b1 benötigt eine neue Bestätigung.

## XEMU-Abnahme

1. Weiß und1×4 logische Pixel bei Player- und Gegnerschüssen prüfen, auch diagonal;
   Flugbahn, Ziel beim Abschuss, Treffer/Limits unverändert. Gut sichtbar vor
   allen Sternfarben; Gegnerhitbox bleibt dokumentiert3 Pixel breit.
2. Level1/2/3/99/100 spielen bzw. mit +/- wählen. LEVEL CLEAR weiter sichtbar,
   Sterne normal. Gehaltener Feuerbutton darf nicht bestätigen; neuer Druck startet.
3. Etwa1 Sekunde schnelle dreifarbige Sterne, dann symmetrische breite Farbbänder
   von der Mitte nach außen. Vollständige Farbdeckung, danach dieselbe Schwarz-
   ausbreitung. HUD bleibt vollständig sichtbar; keine Actorreste/Schüsse.
4. Nächster Level mit normalem Sternentempo, Originalpalette/Cycling, korrektem
   Einflug und ohne Rechteck-/RRB-Rückstände. Score/Leben/Highscore unverändert.
5. X jeweils während Beschleunigung, Farbe, Schwarz und Abschluss prüfen;
   normales BASIC/Cursor, DIRECTORY und erneutes RUN/F1. R nach GAME OVER normal.
6. Mehrminütiger Lauf: keine Timingstörungen, Ghosts, Streifen oder HUD-Flackern.

Keine Stable-Markierung oder Merge vor ausdrücklicher Benutzerbestätigung.
