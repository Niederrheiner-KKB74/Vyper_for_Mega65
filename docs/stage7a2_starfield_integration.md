# Stage7a2 – Sternenhintergrund im vollständigen Spiel

Issue [#51](https://github.com/Niederrheiner-KKB74/Vyper_for_Mega65/issues/51),
Branch `stage7a2`, Stand 13.10.2026. **Nicht Stable; XEMU-Abnahme ausstehend.**

## Herkunft und geschützte Referenzen

Die vollständige Engine stammt bytegleich, abgesehen von den unten aufgeführten
Integrationsstellen, aus `stage6b1-stable` (`31ae0bd4bcdd79f3217126f902cf9978907cb48d`).
Der getestete Stage7a1-Renderer stammt aus
`ed22f0d4e4ca0bd8f5ff6ebaa5892135ce9bdd9a`. Seine Benutzerabnahme liegt in
`stage7a1-stable` (`9ebbcabd2a792661b0da354f2716abb7772d74a6`).
PR50 ist tatsächlich nach `main` gemergt, Mergecommit
`5344544b5e22f1d702419129f65b388f9b284469`; von diesem Integrationsstand wurde
der neue Branch angelegt. Quellen der Spielengine wurden anschließend ausdrücklich
aus Stage6b1 kopiert, nicht durch eine andere Entwicklungsengine ersetzt.

Alle bisherigen Stable-Quellen, Assets, Tools, Releases und Tags bleiben unverändert.
Der neue Builder prüft diese Referenzen und die historischen Speichergrenzen.
Keine Löschung, Archivumstrukturierung oder Änderung von `main` für diesen Auftrag.
Stage7a2 wird als eigener PR zur Benutzerprüfung geliefert, ohne Merge/Stable-Tag.

## Bedienung und Spielablauf

D81 `releases/stage_7a2/VYPER_STAGE7A2.d81` in XEMU mounten:

```basic
LOAD"STAGE7A2",8
RUN
```

Titelbild während des Ladens → originales animiertes Menü → **F1** startet
das Spiel mit INITIAL LEVEL 001–100. Joystick **Port 2**, PAL/50 Hz und
Attic-RAM wie in den bestätigten Referenzen. F2/F3 bleiben Platzhalter.

Sterne erscheinen erst im Spiel, nie im Titelbild, Ladebildschirm oder Menü.
Die Starfield-Testtasten **B und V haben keine Sternfunktion mehr**.
X beendet sauber nach BASIC. R nach GAME OVER, +/- Levelnavigation, Feuer,
Joysticksteuerung und alle bisherigen Spieltasten behalten ihre Enginefunktion.
Der neue Sterncode liest keine Tastatur-/Joystickregister.

## Unveränderte bestätigte Darstellung

Es werden exakt die X/Y-Startverteilung, RGB-Werte und Geschwindigkeiten aus
Stage7a1 übernommen, nicht neu rekonstruiert:

| Klasse | Sterne | RGB8, Bank1-Index | normaler 50-Hz-Takt |
| --- | --- | --- | --- |
| Blau | 16 | `#0000FF`, 49 | +1 Y alle8 Frames, 6,25 Pixel/s |
| Rot | 16 | `#FF0000`, 50 | +1 Y alle4 Frames, 12,5 Pixel/s |
| Gelb | 16 | `#FFFF00`, 51 | +1 Y alle2 Frames, 25 Pixel/s |

Seed `$7441`, X=`(i×37+11) mod240`, reproduzierbare Y-Werte aus Stage7a1.
Die generierte `stars_layout.inc` ist bytegleich zum getesteten Stand.
Diese Werte sind bestätigte Projektparameter, weiterhin **keine nachgewiesenen
Amiga-Sternkonstanten**. Ein Stern umfasst einen logischen Pixel, im vorhandenen
H640/CHARXSCALE60 zwei horizontale Ausgabepixel. Modulo200-Umlauf am unteren
Rand und unabhängige Geschwindigkeitsklassen bleiben unverändert.

Die Rendertechnik bleibt der bestehende **opake NCM-Hintergrundprefix** mit
eigenem Charset. Kein zusätzlicher RRB-Pixie, kein Hardware-Sprite, kein
neuer Raster-/Grafikmodus. Gegner/Player verwenden weiterhin die transparenten
GOTOX-Listen und ihre ursprünglichen privaten NCM-Grafikpuffer. Ein transparenter
Pixie-Nibble0 lässt den darunter gezeichneten Stern stehen; ein opaker Pixel
überdeckt ihn. Jede Rasterzeile beginnt erneut mit dem Hintergrund, sodass
kein alter Pixie-Pixel als Spur stehen bleibt.

Sternpalette: Bank1, Indizes48–51 (48 schwarz reserviert, Nibbles1–3 Farben).
Gegner: unverändert Bank1/17–24, Cycling19; Explosionen Bank1/0–15;
Player/HUD Bank2. Alle38 Gegnertypen, 20 VYCL-Paletten und 100 Levels bleiben
unverändert. Die zwölf Stern-RGB-Register werden beim F1-Start gesichert und
vor BASIC-Exit restauriert; D070 wird nach jedem Palettezugriff zurückgestellt.

## Tick, LEVEL CLEAR und Levelwechsel

`starfield_tick` wird genau einmal pro Hauptschleifen-Frame nach dem bestehenden
50-Hz-Rasterwait und vor `cc_tick` aufgerufen. Er liegt **außerhalb** der
Level-/Kampfzustandsverzweigungen. Deshalb laufen Sterne in ENTRY, FORMATION,
ATTACK, RETURN, Explosion, Respawn, Spielpause, LEVEL CLEAR und GAME OVER
gleichmäßig weiter. Kein neuer Eingabe- oder Spielzustandsfilter entsteht.

Bei LEVEL CLEAR bleibt die Hintergrundfläche bestehen; die bisherigen
Mono-Textzeilen werden durch den bestehenden Writer darüber gezeichnet.
Die Schrift und deren opaker Zeichenhintergrund bleiben unverändert. Stern-
bewegung hinter der Anzeige läuft weiter, ebenso während des Wartens auf
Loslassen und einen neuen Joystick-Buttondruck. Level100→1 behält den
laufenden Sternzustand; +/- bleibt wie bisher bei1/100 begrenzt.

**Kein Reset bei Levelwechsel oder R.** Die Levelroutine verändert weder
Stern-Y-Koordinaten, Farbregister, Bitmap noch Teilerphase. Auch ein R-Neustart
behält den laufenden Hintergrund; die bisherigen Score-/Leben-/Highscore-Regeln
bleiben unangetastet. Nur ein neuer Programm-/F1-Spielstart setzt die ursprüngliche
Verteilung auf. Wiederholtes `starfield_init` bei bereits aktivem Feld ist
idempotent: bindet die Fläche, ohne Positionssprung oder erneute Palettensicherung.

Die bisherige `hud_draw_static`-Routine zeichnet den Hintergrund normalerweise
schwarz und baut dann das HUD auf. Stage7a1 band danach die Sternkacheln wieder
ein. Stage7a2 verhindert zusätzlich eine vorübergehende schwarze Fläche:
**bei aktiven Sternen wird ausschließlich das erneute Zeichnen des schwarzen
Hintergrundprefix übersprungen**. Die existierenden Sternzellen bleiben während
des ganzen Neuaufbaus identisch. HUD und dynamischer Tail werden weiterhin
normal erneuert; anschließend stellt `starfield_bind` dieselben Sternreferenzen
wieder her. Vor Sterninitialisierung bleibt der ursprüngliche Schwarzaufbau aktiv.
Das verändert weder RRB-Architektur noch den Pixie-Renderer.

## Entfernte Stage7a1-Laufzeitdiagnostik

Entfernt: `stars.key`, B-Ein-/Ausblenden, V-Profilingmarker, `enabled`-Schalter,
Border-Sicherung/-Writes, D011/D012-Profilingreads, Rasterzeit-/Maximum-/Frame-
Messzähler und deren Auswertungsroutine. Kein künstlicher Gegner-Demostart,
keine neue Testszene, keine Status-/Debugausgabe und keine Stern-Pausetaste.

Stage7a1 zeigte bereits die vollständige Stage6b1-Engine. Die übernommenen
Enginequellen einschließlich ihrer historischen internen Diagnostik bleiben
erhalten; diese sind keine neu hinzugefügte Stage7a1-Sternbedienung.
Nützliche Hosttests und die bisherigen technischen Referenzreports bleiben im Repo.

## Kleine API für spätere Übergangsbeschleunigung

Globale KickAssembler-Labels, implementiert in `stage7a2_stars.asm`:

| Routine | Vertrag und derzeitige Verwendung |
| --- | --- |
| `starfield_init` | nach F1-Engine-/HUD-Initialisierung; erstmalig Palette sichern, Feld erstellen; bereits aktiv: ohne Reset neu binden |
| `starfield_tick` | einmal pro50-Hz-Frame; erhält A/X/Y/P; bei inaktivem Feld kein Update |
| `starfield_bind` | Hintergrundreferenzen/Attribute an Screen/Color-RAM binden; keine Positions-/Geschwindigkeitsänderung |
| `starfield_restore` | vor Engine-BASIC-Restauration: Sternpalette zurück, Feld inaktiv |
| `starfield_reset` | expliziter frischer Feldreset, Seed-Verteilung/Phase/Normalmodus; nur erstmalig von init benutzt, nicht von Level/R |
| `starfield_set_speed_mode` | A=0: Normalmodus, Carry0; A≠0: derzeit nicht unterstützt, Carry1; kein Positions-/Phasenreset |

Außer tick dürfen diese Routinen A/X/Y und arithmetische Flags verändern;
Init/Reset/Bind/Restore erhalten den bisherigen IRQ-Maskierungszustand.
`set_speed_mode` verändert nur A-/Vergleichsflags/Carry und bei A0 das Modebyte.
Mode0 hat unverändert die bestätigten Teiler8/4/2. Beschleunigte Modi werden
bewusst abgewiesen: **kein Übergangseffekt und keine tatsächliche Beschleunigung**
in Stage7a2. Eine spätere Stage kann hier die geprüften Übergangsgeschwindigkeiten
einfügen, ohne neue Kopplungen an Gegnerbewegung oder Levelparser zu schaffen.

## Speicher, Palette und Aufwand

Inklusive Grenzen; übrige Karte wie Stage6b1/Stage7a1:

| Bereich | Nutzung |
| --- | --- |
| `$4E10–$4E3F` | 48 Y-Koordinaten |
| `$4E40–$4EF7` | unveränderter Prefix-Binder |
| `$6800` | temporäres DMA-Pixelbyte, Routine abgeschlossen vor Engine-Arbeit |
| `$B480–$B640` | Sternkern, API und F018A-Listen; kleiner als Stage7a1 |
| `$CD80–$CFD2` | bytegleiche Adresstabelle, Startpositionen, Nibbles und Teiler |
| `$CFD8–$CFFF` | funktionaler Zustand/Palettensicherung; ehemalige Profilingbytes ungenutzt |
| `$CFD8/$CFD9/$CFDA` | aktiv/Normalmode/Teilerphase |
| `$18000–$1DDBF` | 24.000Byte NCM-Fläche;375 Glyphen `$600–$776` |

Die Fläche gehört in der früheren Menüphase noch zum Original-FCM-Atlas und
wird erst **nach** F1-Handoff genutzt. Titelcache, Loader, DOS-RAM, Attic,
VYLV/VYGR/VYCL, Recordpuffer und Original-Pixie-/Clippingpuffer bleiben getrennt.
Screendaten `$E000`, Stride192, 96 Einträge/Zeile, Color-RAM `$0FF80000`,
Playfield `[0,240)×[0,200)`, HUD nativ X480. Nur die vorhandenen Prefix-
Bytes2–31 werden als Sternzellen benutzt; keine zusätzlichen Slots.

Initialisierung/ausdrücklicher Reset: ein24-KB-DMA-FILL plus48 Sternpixel.
Normalbetrieb: nur alten/neuen Pixel-Nibble ändern, benachbarte Nibbles erhalten.
Vier Ein-Byte-DMA-COPYs pro bewegtem Stern, maximal192 Aufträge/Nutzbytes je
Frame, Mittel56. Kein Vollbildcopy im Frame und kein Stern-DMA-FILL bei Level/R.
IRQ-Maskierung und der vorhandene F018A-Trigger bleiben aus dem bestätigten Renderer.

`releases/stage_7a2/starfield-measurements.json` enthält **Host-Modellwerte des
tatsächlich assemblierten neuen PRG**, keine XEMU-Millisekunden. Die Tests
vergleichen Normal- und All48-Wrap-Kosten mit den gemessenen Stage7a1-Werten:
Stage7a2 muss unter dessen19.600 bzw.19.942 CPU-Modellzyklen bleiben, bei
unverändertem DMA-Peak192. DMA-Deskriptorfetch/Busdauer ist im CPU-Modell nicht
enthalten. Die Entfernung der Instrumentierung reduziert den Updatecode;
zusätzliche pro-Frame-Arbeit oder zusätzliche VIC-Fetch-Slots entstehen nicht.
Reale50-Hz-/Rasterzeit- und Flickerfreiheit erfordern die neue XEMU-Abnahme.

Gemessener Hostvergleich bei identischen Seed-Positionen:

| CPU-Modellzyklen | Stage7a1 | Stage7a2 |
| --- | --- | --- |
| Mittel des8-Frame-Zyklus | 7.228,375 | 6.792,375 |
| dichtester normaler Updateframe | 19.600 | 18.756 |
| alle48 Sterne gleichzeitig Y199→0 | 19.942 | 19.098 |

DMA bleibt in beiden Stages bei Mittel56/Peak192 Ein-Byte-Aufträgen.
Dies ist kein Anspruch auf eine bestimmte Hardware-Laufzeit.

## Reproduktion und automatisch geprüfte Funktionen

Vollständiges Repo einschließlich Stable-Tags/Originalassets, KickAssembler5.25
(geprüfter JAR-SHA256), Java, Python3.12, Pillow12.3, py65 für Hosttests:

```bash
python tools/build_stage7a2.py --kickass /pfad/KickAss.jar
PYTHONPATH=tests:tools:/pfad/py65 python -m unittest test_stage7a2 -v
python tools/package_stage7a2.py
```

Ausgabe `releases/stage_7a2/`: vollständige ASM/INC, Symbole, PRG, D81, alle fünf
SEQ-Dateien VYTI/VYMN/VYLV/VYGR/VYCL, Build-/Test-/Messreports, Hashes und ZIP.
Originale VYTI/VYLV/VYGR/VYCL bleiben bytegleich zu Stage6b1. Die historische
Assetkonvertierung und der unveränderte Titel-/Menüloader werden wiederverwendet.

Hostprüfungen im neuen Testmodul:

- komplette Titel/SEQ/Menu/F1-Übergänge, alle32 Menüanimationen, Eingaben,
  Levelauswahl, F2/F3-Platzhalter, volle CPU-Geschwindigkeit und ROMC-/IRQ-Gates;
- bytegleiche Stage7a1-Parameter, 1.600 Sternframes mit unabhängiger Pixel-Oracle,
  alle Clippingränder, transparente Originalpixels, Ghostfreiheit, benachbarte
  Nibbles, DMA-Ziele und originaler Sprite-/HUD-/Palettenschutz;
- unveränderte Phase/Positionen/Bitmap bei allen100 Levelinitialisierungen und R;
  jeder einzelne Screen-/Color-Prefix-Store auf vorübergehende Schwarz-/Glyph-
  Änderungen geprüft; LEVEL CLEAR160 echte Hauptschleifenframes mit lesbaren
  Originaltextglyphen und normaler Sternbewegung, Release/Fire und100→1;
- API-Idempotenz, unterstützter Normalmodus/abgewiesene Reservemodi, expliziter
  Reset, entfernte B/V-Sternwirkung und fehlende Runtime-Messfunktionen;
- bestehende Kampfregression: Originaleinflug/B2, Formationsdrift/Rückkehr,
  max.drei Angreifer/max.vier Gegnerschüsse, Projektile/Kollisionen, sieben
  Explosionframes, steuerbarer Respawn, Score/Leben/Highscore und Game Over;
- Palette/Cycling für alle100 Levels, JoystickPlayer1Pixel/Frame, X-BASIC-Exit,
  Wiederstart mit unveränderter Menüansicht und Sternpalette-Restauration;
- D81-Ketten/BAM, exakte Dateibytes, Stable-Schutz und zweite Build-Reproduktion.

Ergebnisse und tatsächlich ausgeführte Testanzahl stehen im Release-Testreport.
**33 Hosttests bestanden;47 Dateien aus zwei unabhängigen Builds bytegleich.**
Die CPU/KERNAL/DMA/VIC-Prüfungen sind schmale Hostmodelle; keine eigene XEMU-
Ausführung wird behauptet. Die erfolgreiche Stage7a1-XEMU-Abnahme stammt vom
Benutzer und ersetzt nicht die noch ausstehende Stage7a2-Abnahme.

## XEMU-Abnahme für Stage7a2

1. LOAD/RUN: Titel über das ganze Laden korrekt, Menü ohne Sterne, alle32 Gegner
   animiert, INITIAL LEVEL und F2/F3 funktionieren. F1 zunächst Level1.
2. Mehrminütiger Lauf, zusätzlich Level2/3/11/100: gleiche drei Sternfarben/raten,
   konstante Verteilung, keine Streifen, Ghosts oder oberes HUD-Flackern;
   Sterne nie im HUD, Y0 und199 nutzbar.
3. Joystick2 bewegen/feuern, ENTRY-/ATTACK-Gegnerschüsse, Kollision/Explosion/
   Respawn prüfen: Playerfarben konstant, Originalpalette und Cycling erhalten,
   Gegner/Player/Hardware-Schüsse liegen vor dem Hintergrund.
4. LEVEL CLEAR erreichen und einige Sekunden warten: Sterne laufen weiter;
   neuer Feuerdruck wechselt sauber, keine Verteilungssprünge oder schwarzen
   Zwischenstreifen. Level100→1 und +/- prüfen; Score/Leben bleiben erhalten.
5. GAME OVER/R: Highscore bleibt, neues Level1 mit drei Leben; Hintergrund läuft
   weiter. B/V schalten weder Sterne noch Marker; keine Stern-Testausgaben.
6. X: normales BASIC/Cursor, DIRECTORY, erneutes RUN und F1 ohne Artefakte.

Keine Stable-Markierung und kein Merge vor ausdrücklicher Benutzerbestätigung.
