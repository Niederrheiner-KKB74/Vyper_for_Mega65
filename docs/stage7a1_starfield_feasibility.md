# Stage 7a1: dreifarbiger Sternenhintergrund – technischer Test

Issue [#49](https://github.com/Niederrheiner-KKB74/Vyper_for_Mega65/issues/49),
Branch `stage7a1-starfield-test`, Stand 13.10.2026. **Testbuild, nicht Stable.**
Eine XEMU-Abnahme steht aus. Es erfolgt kein Merge in die stabile Spielengine.

## Ausgangsbasis und Start

Abgeleitet vom bestätigten Tag `stage6b1-stable`, Commit
`31ae0bd4bcdd79f3217126f902cf9978907cb48d`; der darin enthaltene, vom Benutzer
getestete Programmstand ist `5fa82452101cf690c3fa1f5eba0b172222541764`.
Stage6b1-Quellen, Assets, Releases und Tags bleiben bytegleich. Auch `main`
wird nicht geändert. Der Builder prüft zusätzlich die geschützten Referenzen
Stage5d1a und Stage6a2.

Das separat startbare D81 liegt unter
`releases/stage_7a1/VYPER_STAGE7A1.d81`:

```basic
LOAD"STAGE7A1",8
RUN
```

XEMU: MEGA65, PAL/50 Hz, Attic-RAM, Joystick **Port 2**. Titelbild und Loader
erscheinen wie in Stage6b1. **F1** startet die Stern-Testszene mit dem
gewählten Level, zunächst 001. Die Sterne sind im Menü noch nicht aktiv.
Der ursprüngliche Einflug, die bewegten Originalgegner, der Player und die
Hardware-Sprite-Schüsse laufen im Vordergrund weiter. Es gibt keine neuen
Ersatzgrafiken. Mit `+`/`-` sind weiterhin die Level 1–100 erreichbar.

| Taste | Testwirkung im Spiel |
| --- | --- |
| B | Sternenhintergrund aus/ein; aus bedeutet vollständig schwarzer Hintergrund |
| V | Kurze rote Rahmenmarkierung während der Sternberechnung aus/ein |
| X | Saubere Rückkehr zu BASIC, danach erneutes RUN möglich |

Alle übrigen Tasten und Joystickfunktionen bleiben aus Stage6b1 erhalten.
Die bestehende Spielpause wird nicht durch eine neue P-Belegung ersetzt;
der Sternupdate läuft unabhängig von der Kampfmechanik weiter.

Ein vollständiger Loader/Engine-Ableger ist bewusst gewählt: Die bestehende
Engine verteilt RRB-Initialisierung, Clipping, private Grafikpuffer, Palette,
HUD und BASIC-Restauration auf viele feste Speicherbereiche. Eine zweite,
neu herausgelöste Engine würde für diesen Nachweis mehr Änderungen und
weniger belastbare Regression bedeuten. Issue49 erlaubt ausdrücklich diesen
isolierten Ableger. Die Titel-/Menüintegration und alle 100 Level bleiben
im Test vorhanden; die Sterne werden nur im neuen Branch zugeschaltet.

## VIC-IV-Vorprüfung und Alternativen

Geprüfte Chipset-Reference:
[MEGA65 User Guide, VIC-IV-Anhang](https://github.com/MEGA65/mega65-user-guide/blob/cefce48d72e5c98d732c0589461d62b205b5165f/appendix-viciv-registers.tex),
Abschnitte SEAM, NCM, Raster Re-write Buffer und Frame Timing. Dieser Anhang
ist Bestandteil von `mega65-chipset-reference.tex`. Zur Gegenprüfung wurde
der [XEMU-VIC-IV-Renderer](https://github.com/lgblgblgb/xemu/blob/40dfef0d1d5f56be2469492715c12bdb32c75b67/targets/mega65/vic4.c)
verwendet, insbesondere `_render_16color_char_row()` und die GOTOX-Auswertung.
Diese Quellprüfung ist keine durchgeführte XEMU-Laufzeitabnahme.

Stage6b1 verwendet SEAM/NCM mit `D054.CHR16/FCLRHI`, H640 und `CHARXSCALE=60`:
ein logischer Spielpixel entspricht zwei horizontalen Ausgabepixeln.
Das Playfield bleibt **240×200**, X=0..239 und Y=0..199; HUD beginnt bei
nativem X=480. Screen-RAM ist `$E000`, 25 Zeilen mit je **192 Bytes / 96
Einträgen**. Color-RAM beginnt physisch bei `$0FF80000`. Die Zeile hat:

| Bytes der Zeile | Bisherige Verwendung | Stage7a1 |
| --- | --- | --- |
| 0–1 | opaker GOTOX zum Zeilenanfang, Primärpalette | unverändert |
| 2–41 | 20 schwarze NCM-Hintergrundzellen | erste 15 zeigen Sternkacheln; letzte fünf bleiben schwarz |
| 42–83 | HUD-Prefix | unverändert |
| ab 84 | dynamische RRB-Pixies und Abschluss-GOTOX | unverändert |

Die dynamischen GOTOX-Einträge unterdrücken das erneute Zeichnen der
Hintergrundfarbe. NCM-Nibble 0 bleibt deshalb im Pixie transparent; im
**opaken** Hintergrundprefix zeichnet Nibble 0 dagegen `D021`-Schwarz.
Nibble 15 ist eine VIC-IV-Sonderfarbe aus Color-RAM und wird für die Sterne
nicht verwendet. Die abschließenden RRB-Einträge bleiben erhalten, damit
ein letzter Pixie links nicht die rechte Bildkante/HUD abschneidet.

| Verfahren | Bewertung |
| --- | --- |
| eigene Hardware-Sterne | ausgeschlossen: die acht Sprites bleiben für Projektile frei |
| ein RRB-Pixie pro Stern | ausgeschlossen: zusätzliche GOTOX-Einträge gefährden Zeilen-/Rasterbudget |
| ständig Screen-/Color-RAM für Sternpositionen ändern | unnötige Konkurrenz zum dynamischen RRB-Renderer; nicht gewählt |
| eigener FCM-Hintergrund | möglich, aber für 240×200 etwa 48 KB statt 24 KB und doppelte Pixeldaten |
| Bitplane-/Moduswechsel oder Rasterumschaltung | größerer Umbau, Konflikte mit bewährtem NCM/HUD/Palette; für drei Farben nicht erforderlich |
| vorhandener Prefix + eigener NCM-Charset | **gewählt**: keine neuen Einträge, 24 KB, nur geänderte Pixel aktualisieren |

Der Prefix wird bei Spielstart und nach dem bestehenden statischen
HUD-Neuaufbau an 375 Kacheln gebunden. Der Hintergrund wird zuerst gezeichnet,
HUD/Pixies darüber. Hinter bewegten transparenten Pixies bleiben echte
Hintergrundpixel erhalten; das opake Prefix zeichnet jede Rasterzeile neu
und beseitigt Vordergrundspuren. Der Projektile-Spritepfad und seine
Prioritätsregister werden nicht geändert.

Die Engine-Lookups `v012a_screen_lo/hi` zeigen auf den **dynamischen Tail
bei +84**, nicht den Zeilenanfang. Der neue Binder leitet den echten
Zeilenanfang aus dem Zeilenoffset ab und schreibt ausschließlich Bytes
2–31. Dieser Unterschied wurde im Hosttest explizit geprüft. Auch Zeilen
0, 1, 23 und 24 werden vollständig gebunden.

## Parameter und Palette

Alle folgenden Sternwerte sind **Testparameter, keine nachgewiesenen
Amiga-Konstanten**. Anordnung/Gegnergrafiken, VYLV/VYGR/VYCL und Original-
Animationsdaten werden nicht verändert.

| Klasse | Anzahl | RGB8 / Bank1-Index | Bewegung bei 50 Hz |
| --- | --- | --- | --- |
| Blau | 16 | `#0000FF`, 49 / `$31` | +1 Y alle 8 Frames, 6,25 Pixel/s |
| Rot | 16 | `#FF0000`, 50 / `$32` | +1 Y alle 4 Frames, 12,5 Pixel/s |
| Gelb | 16 | `#FFFF00`, 51 / `$33` | +1 Y alle 2 Frames, 25 Pixel/s |

Jeder Punkt ist **ein logischer Pixel** groß. NCM-Color-RAM `$08,$30`
wählt die Subpalette 48–63; nur Nibbles 1, 2, 3 werden gezeichnet. Index48
ist zusätzlich schwarz reserviert, Nibble0 nutzt im opaken Prefix jedoch
die normale schwarze Screen-Hintergrundfarbe.

Originale Gegner bleiben in Bank1, Indizes17–24; Cycling bleibt Index19.
Explosionen bleiben Bank1, 0–15; Player/HUD bleiben Bank2. Die zwölf
RGB-Bytes für Bank1, 48–51 werden gesichert und vor BASIC-Exit restauriert.
Der bestehende Palettenzugriff über `D070` wird dabei jeweils vollständig
zurückgestellt. Sterne verändern keine Originalpalette und keinen Cycle-
Zustand, auch nicht bei einem Levelwechsel.

`tools/convert_stage7a1_stars.py` enthält die leicht anpassbaren Werte
`COUNT`, `SEED`, `DIVIDERS`, `RGB`. Aktuelles Speicherbudget erlaubt
**3..48 Sterne in Dreierschritten**; Geschwindigkeiten sind unabhängige
Zweierpotenz-Teiler von 1 bis 128 Frames. RGB-Werte werden aus derselben
Python-Konfiguration für die Assembler-Tabelle generiert.

Seed `$7441`, reproduzierbare Y-Positionen, eindeutige feste X-Positionen
`(i×37+11) mod 240`. Die exakten Koordinaten stehen in `build-report.json`.
Damit gibt es keine gleichen Sternpixel, die sich gegenseitig löschen.
Zwei benachbarte Sterne dürfen dasselbe Datenbyte nutzen: der andere
Nibble bleibt durch Read/Modify/Write erhalten. Y wird modulo200 bewegt:
nach Y199 verschwindet der Punkt unten und erscheint bei Y0 wieder oben,
ohne Sprung im Bildinneren. Alle Abstände innerhalb einer Geschwindigkeits-
klasse bleiben über beliebig viele Umläufe erhalten; es entstehen keine
neuen Konzentrationen in Zeilen.

## Speicher und DMA

Alle Endadressen sind inklusiv; übrige Belegung bleibt Stage6b1.

| Bereich | Neue Nutzung / Abgrenzung |
| --- | --- |
| `$4E10–$4E3F` | 48 mutable Y-Koordinaten, nach Kampfcode-Ende `$4E04` |
| `$4E40–$4EF7` | Prefix-Binder; vor Angriffsscheduler `$4F00` |
| `$6800` | ein Byte bestehender DMA-Arbeitspuffer, nur innerhalb abgeschlossener Sternroutine |
| `$B480–$B6FE` | Update-/Palette-/Profilingcode und drei F018A-DMA-Listen; vor RRB-Code `$B800` |
| `$CD80–$CFD2` | X/Y-Adress-, Nibble- und Starttabellen; nach Phasenbridge-Ende `$CD48` |
| `$CFD8–$CFFF` | Status, Palettensicherung und Rastermesswerte; PRG initialisiert diesen Bereich |
| `$18000–$1DDBF` | 24.000 Byte: 15×25 NCM-Glyphen, jeweils 16×8 Pixel/64 Byte |

Der NCM-Glyphbereich ist `$600–$776`; der VIC adressiert die Daten mit
`Glyphnummer×64`, unabhängig vom Mono-Charsetpointer. Beim Menü gehört
`$18000…` noch zum FCM-Atlas. **Erst nach Engine-Restauration und F1-Handoff**
wird dieser Speicher für Sterne verwendet. Rückkehr ins Menü ist wie in
Stage6b1 kein Spielzustand; X/RUN lädt dessen Atlas erneut. Titelcache und
aktive Loaderdaten werden nicht überschrieben.

Unberührt: DOS-RAM `$10000–$11FFF` und `$1F800–$1FFFF`, Levelrecord ab
`$12000`, private Gegnerframes `$14000–$15AFF`, DATs `$40000–$5C4DB`,
Attic-Sicherungen, Screen-/Color-RAM-Länge und private RRB-Clippingpuffer.
Assembler-Guards verhindern Code-/Tabellenüberschneidungen.

Init/B schaltet mit **einem DMA-FILL** die 24-KB-Fläche auf Schwarz; bei
Aktivierung werden alle Sterne gemalt. Im normalen Frame wird **keine
ganze Fläche kopiert**. Pro bewegtem Stern: altes Pixel lesen/zurückschreiben,
neues Pixel lesen/zurückschreiben, also vier COPY-Aufträge zu je einem Byte.
Quelle/Ziel sind NCM-RAM und `$6800`; F018A, kein Modulo. IRQs bleiben nur
während der abgeschlossenen Sternroutine maskiert. Deskriptoren und der
temporäre Puffer werden danach nicht mehr benötigt. Dies nutzt den bereits
geprüften DMA-Trigger der Engine; direkte lange CPU-Pixelzugriffe wären
eine mögliche spätere Optimierung, falls reale Rastermessungen sie erfordern.

## Messung, Testnachweise und Grenzen

`releases/stage_7a1/starfield-measurements.json` enthält Werte des **tatsächlich
assemblierten Programms** im schmalen 6502/45GS02-Hostadapter. DMA ist dort
instantan, VIC kein Echtzeitrenderer. Die CPU-Zyklen sind Modellwerte und
werden **nicht** in behauptete MEGA65-Millisekunden umgerechnet.

| Updatephase im 8-Frame-Zyklus | bewegte Sterne | DMA-Aufträge / Nutzbytes | CPU-Modellzyklen |
| --- | --- | --- | --- |
| 1, 3, 5, 7 | 0 | 0 / 0 | 2.134 jeweils |
| 2 | 16 | 64 / 64 | 7.954 |
| 4 | 32 | 128 / 128 | 13.781 |
| 6 | 16 | 64 / 64 | 7.956 |
| 8 | 48 | 192 / 192 | 19.600 |
| Mittel | 14 | 56 / 56 | 7.228,375 |

Alle 192 Spitzen-DMA-Aufträge sind ein Byte groß. Deskriptorfetch/Trigger-
Kosten sind **nicht** in der Nutzbyte-Spalte enthalten und müssen bei
einer realen Rasterzeitbewertung mit erfasst werden. Es gibt weiterhin
96 Screeneinträge pro Zeile, höchstens 24 dynamische Pixie-Slots pro Zeile,
null zusätzliche Stern-Slots und null zusätzliche Hardware-Sprites.
Der VIC liest für die Sternzellen dieselbe Datenmenge wie vorher für die
schwarzen NCM-Zellen. Die Zahl der gezeichneten Hintergrundzellen steigt nicht.
Zusätzlich gemessen: alle48 Sterne gleichzeitig von Y199 nach Y0, **19.942
CPU-Modellzyklen und weiterhin192 DMA-Aufträge**. Dies ist ein absichtlich
verdichteter Lastfall, nicht die normale Seed-Verteilung.

Konservative **Laufzeitinstrumentierung im PRG**:

| Adresse | Bedeutung |
| --- | --- |
| `$CFEC–$CFEF` | Start/Ende, je kohärenter 9-Bit-Rasterzähler aus D011/D012 |
| `$CFF0–$CFF1` | letzte Laufzeit in klassischen PAL-Rasterzeilen, WORD LE |
| `$CFF2–$CFF3` | Maximum seit F1-Spielstart, WORD LE |
| `$CFF4–$CFF5` | Anzahl Updates modulo65.536 |

Bei PAL312-Zeilen-Umlauf wird korrekt modulo312 subtrahiert; Testfall
310→3 liefert fünf Zeilen. **V** zeigt zusätzlich den Zeitraum zwischen
Startabtastung und Updateende durch rote Borderfarbe; alte Borderfarbe
wird danach wiederhergestellt. Die feine Endauswertung sowie Register-
Save/Restore sind nicht vollständig im Marker enthalten. Rasterzähler
sind auf eine klassische Zeile quantisiert (ca.63 µs laut Reference).
Für eine konservative obere Grenze der markierten Strecke eine Rasterzeile
addieren und den kleinen Profiling-/Call-Tail zusätzlich berücksichtigen.
Die Gesamtschleife muss außerdem separat innerhalb des 50-Hz-Frames
beurteilt werden. Eine Dauer größer als ein Frame lässt sich mit dem
Modulo-Zähler allein nicht erkennen; dazu Marker/externen Trace verwenden.
NTSC-Zeitmessung ist in diesem PAL-Test nicht unterstützt.

Automatisch geprüft:

- KickAssembler-Assembly und geschützte Stable-Dateien; vollständige D81-
  Datei-/BAM-Ketten und bytegleiche Original-DAT-Dateien.
- 1.600 Sternupdates (32 Sekunden bei 50 Hz), pixelgenauer Vergleich gegen
  einen unabhängigen NCM-Puffer-Oracle, exakte Teiler, vollständiger Umlauf,
  alle DMA-Ziele in der zugewiesenen Fläche, maximale 192 Aufträge.
- X0/X239 und Y199→0, benachbarte Nibbles, Aus-/Einschalten ohne Restpixel,
  unveränderte HUD-/Color-RAM-/Sprite-/Palettenregister während Updates.
- Gefetchte Originalgegnerpixels an allen vier Clippingrändern, überdeckte
  und durch transparente Originalpixel sichtbare Sterne; nach Entfernen
  des Gegners wieder exakt der Hintergrund, keine Pixie-Spuren.
- Menü, Titel/Loader, Joystick2 und 1-Pixel/Frame-Playerbewegung, Color-
  Cycling, alle 100 Levelpaletten, Eintritts-/Angriffs-/Rückkehr-/Kollisions-
  mechanik, Explosionen/Respawn, Level Clear/Game Over, BASIC-Exit/RUN.

Ergebnis: **28 Hosttests bestanden**, zusätzlicher All48-Wrap-Lastfall bestanden;
**47 Build-Dateien aus zwei unabhängigen Builds bytegleich**. Der abschließende
Wechsel von fest kodierten RGB-Bytes zu generierten RGB-Konstanten ergibt
dasselbe PRG. Testlog, PRG-Hash und Reproduktionsnachweis liegen im Release.

**Keine XEMU-Ausführung behauptet.** Der Host-Pixelfetch prüft RRB-Screen-
 und NCM-Daten, ist aber kein vollständiger VIC-/Sprite-Prioritätsrenderer.
Insbesondere tatsächliche Sprite-Überdeckung, Flickerfreiheit über Minuten,
DMA-Buszeit und Video-/ROM-Restauration sind in XEMU noch abzunehmen.

## XEMU-Prüfplan und Empfehlung

1. D81 laden, RUN, Titel/Loader/Menü prüfen, F1. In Level1 und anschließend
   Level2/3 mindestens mehrere Minuten beobachten: drei kontinuierliche
   Sternraten, keine Bänderbildung, kein oberes HUD-Flackern und kein
   Stern rechts von X239. Y0 und Y199 müssen genutzt werden.
2. Gegner/Player über Sterne bewegen; Originalanimation und transparente
   Löcher sichtbar, keine Spuren. Joystick2 bewegen/feuern, auch Gegner-
   schüsse prüfen: alle Projektile bleiben vor dem Hintergrund.
3. Originalpaletten und Cycling prüfen, z.B. Level29/37/54. Player, HUD,
   Leben und Explosionen dürfen nicht umgefärbt werden.
4. B wiederholt kurz drücken: aus vollständig schwarz, ein sauberer
   Sternhintergrund. V einschalten; maximale Rasterzeit in `$CFF2` über
   mehrere Umläufe ablesen und mit Gesamt-Framezeit/50-Hz-Stabilität prüfen.
   Die reine Sternstrecke soll im Test inklusive Reserve unter **16
   klassischen PAL-Zeilen** bleiben (Prüfziel, kein behaupteter Messwert).
   Die vollständige Engine darf keinen Frame verlieren. Bei Überschreitung
   Sternanzahl reduzieren oder Pixelzugriffe optimieren und neu messen.
5. X, normale BASIC-Anzeige/Cursor, DIRECTORY und RUN erneut testen.

**Go für die gewählte Hintergrundarchitektur als Integrationskandidat**:
keine zusätzlichen RRB-Slots, klare Speicher-/Palettentrennung, unveränderte
Originalgrafiken und nachgewiesene begrenzte Pixelupdates. **Noch kein Go
für einen produktiven Merge oder Stable**: erst nach der XEMU-Abnahme mit
realer Rasterzeit und Benutzerbestätigung. 7a2 kann dieselbe Technik
übernehmen; eine größere Sternzahl oder andere Geometrie benötigt eine
erneute Budget-/Speicherprüfung.

## Reproduzierbarer Build

KickAssembler5.25, Java und Python3.12 mit Pillow12.3; vollständiges Repo
einschließlich der Stable-Tags und Originalassets erforderlich:

```bash
python tools/build_stage7a1.py --kickass /pfad/KickAss.jar
PYTHONPATH=tests:tools:/pfad/py65 python -m unittest test_stage7a1 -v
python tools/package_stage7a1.py
```

Die Testabhängigkeit `py65` kann in einem separaten venv installiert werden.
Der Builder validiert den bekannten KickAss-JAR-SHA256 und produziert PRG,
D81, ASM/INC, Symbole und Reports in `releases/stage_7a1/`. Das ZIP enthält
den vollständigen Release samt neuen Tools, Tests und dieser Anleitung;
ein Neuaufbau benötigt auch die unveränderten historischen Repo-Assets.

Die Originaldateien VYTI/VYLV/VYGR/VYCL sind bytegleich zu Stage6b1. VYMN
wird mit dem separat assemblierten Menü-Overlay erzeugt. Das D81 enthält
`STAGE7A1` und alle fünf benötigten SEQ-Dateien. Keine Internet-Downloads
oder Amiga-Extraktion sind für diesen Build erforderlich.
