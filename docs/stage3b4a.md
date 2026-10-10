# Stage 3b-4a – HUD mit deckendem Hintergrund und dünner HUD-Schrift

Implementiert [Issue #4](https://github.com/Niederrheiner-KKB74/Vyper_for_Mega65/issues/4)
im Branch `stage3b-4a`, Basis `stage3b3-stable` (`bb557e1995b4ec65730360fe28a38b4b3050001c`).
Alle stabilen Stage-3b-3-Dateien bleiben unverändert. Der Benutzer hat Build `9b2e767` als voll funktional bestätigt. Die anschließende
Schrift-/Textanpassung benötigt eine neue Sichtprüfung; kein Stable-Tag.
Die Amiga-Referenz stammt aus dem Benutzer-Gespräch; kein entsprechendes Bildasset
wird im Repository behauptet. Die erste Fassung zeigte laut XEMU-Test BASIC-Hintergrund,
Bewegungsspuren und unleserliche Schrift. Diese Ursachen sind in der korrigierten
Fassung beseitigt; [Diagnose und Vergleich](stage3b4a_background_font_fix.md).

## Freigegebener Modus und Spielfeld

Der Benutzer hat eine breitere Videoausgabe mit maximaler Spielfeldgrenze X=240
freigegeben. H640 mit CHARXSCALE=60 erhält die bisherige sichtbare NCM-Pixie-Breite:
Originalpixel bleiben horizontal zweifach. Der Writer verdoppelt ausschließlich
GOTOX-X einschließlich Bit-8-Carry. Objektkoordinaten, Y-Offset und Grafikbytes bleiben
unverändert. HUD bei H640-X=480–639, entsprechend bisherigen X=240–319. Der Endmarker
ist X=640. Gegner-/Orbit-Tabelle maximal X=170, plus 16 Pixel Breite =186; der Builder
prüft alle 256 Werte gegen 240. Spielergrenze weiterhin X=32–224, mit Breite bis 240.

Raster-Wartecode auf Zeile 250 und acht dynamische Slots bleiben erhalten. Die Zeilen
sind jetzt 64 SEAM-Einträge / 128 Bytes lang. 25 Zeilen ergeben 3200 Byte Screen und
Color RAM. Das vollständige deckende Schwarz und der HUD-Prefix passen so gemeinsam
vor die beweglichen Slots; transparente Pixies zeichnen auf einen frisch gefüllten
Raster und hinterlassen keine alten Pixel.

## Zeilenarchitektur

| Byteoffset in jeder 128-Byte-Zeile | Verwendung |
| --- | --- |
| 0–41 | GOTOX 0, primäre Palette, 20 deckende schwarze NCM-Leer-Glyphen |
| 42–83 | permanenter HUD-Prefix, 21 SEAM-Einträge |
| 84–115 | acht bewegliche Slots, je GOTOX + NCM-Glyphe |
| 116–119 | reservierter Endmarker bei voller Slotbelegung |
| 120–127 | unsichtbare GOTOX-640-Tokens |

Der dynamische Renderer löscht nur 36 Byte ab Offset 84 und schreibt den Endmarker
hinter den letzten belegten Slot. Er berührt Hintergrund/HUD nicht. Color-RAM-Clearing
kopiert dieselben 36 konstanten Nullbytes mit F018A-DMA; keine Änderung der Slotkapazität.
Normale Screen-Schreibzugriffe bleiben in CPU-Bank 0. Attribute werden mit 45GS02
`EOM; STA [$60],Z` nach physischem Color RAM geschrieben. Die Routine sichert A/X/Y,
Flags, B und Z; sie schaltet IRQs aus, verwendet vorübergehend Base Page `$1A` und
stellt sie vor Freigabe der IRQs wieder her. Keine KERNAL-Zero-Page wird benutzt.

24 alte feste Screen-Schreibzugriffe in `advance_animation` und der anschließende
alte statische Capture-Aufruf sind gleich lang durch NOP ersetzt. Ihre Adressen
gehörten zur früheren 80-Byte-Zeile; nach Erweiterung lagen einige im HUD. Diese
Slots sind seit Stage 2ja ungenutzt. Framezähler, tatsächliche Pixie-Grafik-DMA,
Orbitanimation, Joystick und Bewegung bleiben erhalten und werden gegen 3b-3 geprüft.

## Layout und lesbare Schrift

| Zeilen (je 8 bisherige Pixel hoch) | Inhalt |
| --- | --- |
| 0–2 | Hi-Score, sieben Ziffern, grauer Abschluss |
| 3–5 | PLAYER 1 gelb, Score rot, LEVEL blau |
| 6–12 | graues Lebensfeld, drei Leben beim Start |
| 14–16 | PLAYER 2 / Score / Level gedimmt, Player 2 inaktiv |
| 17–21 | P - PAUSE / S - SOUND / X - EXIT; `No P2` |
| 22–24 | Form. 100; Att. 115 (Zeile 23 frei) |

Text verwendet eigene **5×7-Zeichen mit ein Pixel breiten Strichen** in achtspaltigen
Zellen. Damit bleiben Luft zwischen Buchstaben und Details wie der H-Querbalken erhalten.
Ein Fontpixel entspricht einem logischen Spielpixel; wie bisher wird es in H640
horizontal auf zwei native Pixel ausgegeben. „Hi-Score“, „No P2“, „Form. 100“ und
„Att. 115“ passen vollständig zwischen die vier Pixel breiten Seitenrahmen.
Die Referenzwerte bleiben 100/115. P/S bleiben funktional inaktiv; X bleibt aktiv.

Der tatsächlich eingestellte BASIC-Font wird weiterhin per F018A-DMA nach
`$4000–$47FF` kopiert; anschließend ersetzt die HUD-Routine ausschließlich die
benötigten Buchstaben, Zahlen und Satzzeichen in dieser privaten Kopie. Die dünnen
Bitmaps sind ausdrücklich für die gewünschte Schriftanpassung neu erstellt und im
Builder dokumentiert; sie werden nicht als Original-Amiga-Font ausgegeben. BASIC-
Charset und Character-WOM werden nicht verändert, keine ROM-Daten ausgeliefert.
VIC-Aliase `$1000/$1800/$9000/$9800` werden wie bisher auf Character-WOM aufgelöst.
Rahmenzeichen 128/129 bleiben getrennt. Die 38 Glyphen einschließlich Codes belegen
`$9900–$9A55`, geprüft leer in der stabilen PRG und außerhalb aller Loader-/Framepuffer.

HUD und Leben verwenden Palette Bank 2, sichtbare Original-Spielerfarben 1–8
bleiben unverändert. Freie Indizes 10–15 erhalten Weiß/Grau/Gelb/Rot/Blau/dunkles Grau.
Transparenter Index 0 erhält Schwarz für deckende HUD-Zellen. Gegnerpalette Bank 1
und BASIC-ROM-Palette Bank 3 bleiben unverändert. Ein GOTOX am Prefixende setzt vor
den beweglichen Slots die primäre Palette zurück.

## Lebenssymbole: verbindlich 4×2

Acht Plätze, von links nach rechts und danach zweite Reihe. Bisherige Koordinaten:
X=245,262,279,296; Y=58,75. Je 16×16 Originalpixel, genau ein Pixel zwischen den
Symbolen und zwischen den Reihen. Vier Pixel Seitenrahmen: links X=240–243,
rechts X=316–319. Links ein Pixel Abstand nach dem Rahmen; rechts vier Pixel Abstand
nach dem letzten Schiff. 77 Pixel Mindestbedarf passen in die verfügbaren 80.
In H640 sind alle horizontalen Maße verdoppelt, vertikal unverändert.

Statische RRB-Tokens verwenden Originalglyphen `$321/$322/$323`, keine Objektrecords,
keine dynamischen Slots, keine Hardware-Sprites. Subzeilenoffsets -2/-3 und transparente
Tokens bilden den Abstand zwischen den Reihen. In der gemeinsamen Zeile 9 passen
acht Fragmente, Rahmen und Palette-Reset genau in den 42-Byte-HUD-Prefix. Der voraus-
gehende deckende Hintergrund löscht auch weggefallene Lebenssymbole. Leben über acht
bleiben gespeichert, sichtbar sind höchstens acht. Player 2 bleibt stets inaktiv.

## Zentrale Daten und Schnittstellen

| Adresse | Name / Format |
| --- | --- |
| `$1A00` | `hud.high_score`, unsigned 32 Bit LE |
| `$1A04` | `hud.player1_score`, unsigned 32 Bit LE |
| `$1A08` | `hud.player1_level`, unsigned 16 Bit LE |
| `$1A0A` | `hud.player1_lives`, unsigned 16 Bit LE |
| `$1A0C` | `hud.player2_score`, unsigned 32 Bit LE |
| `$1A10` | `hud.player2_level`, unsigned 16 Bit LE |
| `$1A12` | `hud.player2_lives`, unsigned 16 Bit LE |
| `$1A14` | `hud.player2_active`, BYTE, bleibt 0 |
| `$1A15` | `hud.formation_points`, unsigned 16 Bit LE |
| `$1A17` | `hud.attack_points`, unsigned 16 Bit LE |
| `$1A20–$1A38` | Anzeige-Schattenwerte |
| `$1A40–$1A66` | Arbeitspuffer, Skalierung, Color-RAM-Langzeiger, Start-Hintergrundfarbe |

`hud.startup` leert den BASIC-Bildschirm durch KERNAL-CHROUT `$93` und setzt den
Hintergrund vor dem unveränderten SEQ-Loader auf Schwarz. Die ursprüngliche BASIC-
Hintergrundfarbe wird gesichert und auch beim Ladefehler restauriert.
`hud.hud_init` initialisiert Modus, Font, Palette, statische Elemente und Werte.
Scores 0, Player-1-Level 1/Leben 3, Player 2 inaktiv mit Werten 0, Punkte 100/115.
`hud.hud_draw_static` zeichnet die statischen Zeilen und initialisiert das Suffix;
keine laufende Neuzeichnung der statischen Screen-/Color-Daten.

`hud.hud_update_score`, `hud.hud_update_level`, `hud.hud_update_lives` und
`hud.hud_update_points` vergleichen ihre Werte mit Schattenwerten. Sie schreiben
nur bei Änderungen. A/X/Y/Flags werden von den HUD-Update-Aufrufen zerstört; zentrale
Werte vor Aufruf vollständig setzen. `hud.hud_render` führt den bestehenden Renderer
und anschließend die Updates aus. Player-2-Daten und Bereiche sind vorbereitet;
Aktivierung, Player-2-Updates und dessen Lebenrendering erfordern eine spätere Stage.
P/S haben keine Funktion; SPACE und +/- behalten ihre bisherige Funktion, X beendet.

Scores bleiben bis 4.294.967.295 gespeichert; Anzeige der letzten sieben Dezimalziffern.
Level/Punkte zeigen die letzten drei Ziffern. Leben bis 65.535 gespeichert, maximal
acht Symbole. Keine Punktevergabe, Persistenz, Zweispielersteuerung oder Auswertung
zusätzlicher VYLV-Felder. Die Punkte sind ausdrücklich Referenz-Testwerte.

## Speicher, Sicherung und Vergleich

[Speicherkarte](memory_map.md). Screen `$5000–$5C7F`, Spritepointer `$5C80–$5C8F`,
Attributvorlagen `$5C90–$5FD7` und `$3F00–$3FD1`. Code `$3800–$3DB1`, Konstanten
`$3E80–$3EB6`, Screen-/Zeigervorlagen `$7A00–$7EE1`. Font `$4000–$47FF` war zuvor leer.
Die alte Farbvorlage `$6000–$67CF`, Loader-/DMA-/Level-/Grafikbereiche und High-RAM-
Dateien bleiben unverändert. PRG weiterhin 43.521 Byte, D81 819.200 Byte.

Vor jeder Engine-Schreiboperation werden alle verwendeten 3200 Color-RAM-Bytes
gesichert: ursprüngliche 2048 Byte nach `$9000–$97FF`, zusätzliche 1152 nach
`$6B00–$6F7F`. Letztere liegen im leeren PRG-Bereich nach dem Grafikverzeichnis und
werden beim Exit per F018A-DMA zurückgeschrieben. KERNAL-/Cursor-RAM `$1000–$15FF`
bleibt geschützt. `$D05A`, sämtliche bisherigen VIC-/Charset-/Screen-/Palette-
Register und HOTREG werden restauriert. Wiederholtes LOAD/RUN initialisiert alles erneut.

Der Builder prüft bytegenau gegen `stage3b3-stable`: nur deklarierte Hooks,
Zeiger/Endmarker, Spritepointer-Verlegung, alter statischer Capture-Aufruf und
24 ungenutzte feste Screen-Stores sowie drei neue Datenbereiche dürfen sich ändern.
Alle Baseline-Labels behalten ihre Adressen. SEQ-Loader einschließlich SETBNK,
Parser, Originalgrafikdaten, Bewegungs-/Joystickcode und aktive Animationsroutinen
bleiben bytegleich. Die Loader-Erfolgsmeldung heißt weiterhin Stage 3b-2.

## Reproduzierbarer Build und automatische Prüfung

```sh
python3 tools/build_stage3b4a.py --kickass /pfad/KickAss.jar
MEGA65_ROM=/pfad/MEGA65.ROM python3 -m unittest discover -s tests -p 'test_stage3b*.py' -v
```

Python, Java, gepinnter KickAssembler 5.25; Testabhängigkeiten wie bisher aus
`tests/requirements-stage3b1.txt`. Templates werden deterministisch generiert.
Ausgabe enthält drei vollständige ASM-Dateien, PRG, D81, Symbole, Speicherkarte,
Build-/Vergleichsbericht und SHA-256-Liste. Beide DAT-Dateien sind SEQ im D81.

**54 Tests bestanden:** Elf HUD-/Exit-Tests prüfen Preload/D81/Patches; dünne Glyphen und gerahmte Labels;
4×2-Originalpixel/Abstände/Clamping; 32-Bit-Scores und unveränderte Anzeigen ohne
Schreibzugriffe; 56 Frames mit identischen Bewegungs-/Animationszuständen gegen
3b-3; permanenten HUD-Prefix und Palette; Font-DMA; Exit/Neustart mit allen 3200
Color-RAM-Bytes und Cursor-RAM; Grafik-DMA-Fehler; temporäre Base-Page/Z-/Flags-
Erhaltung ohne Zero-Page-Schreibzugriffe; Ladefehler nach KERNAL-Clear/Schwarz.
Der neue Rastertest übernimmt ausdrücklich den vorherigen Frame-Inhalt, reproduziert
die ausgelassene Hintergrundfüllung und prüft spurfreie Neuzeichnung. CIA1 und
physischer Color RAM sind getrennt modelliert. Die bereitgestellte V920395-Cursorroutine
wird zusätzlich ausgeführt. Dazu kommen die unveränderten 43 bisherigen Tests.

Der 6502-/45GS02-Hostadapter ermittelt etwa 15.041 zusätzliche CPU-Zyklen pro Frame;
DMA-/VIC-Arbitration und tatsächliche 45GS02-Taktzeiten sind keine Messwerte dieses
Modells. Die 50-Hz-Wartebedingung ist unverändert. Tatsächliche Bildrate und Timing
bleiben Teil der XEMU-Abnahme. Kein eigener vollständiger Emulatorlauf behauptet.

## XEMU-Abnahme

Frisch booten (ROM V920395), neues D81 in Laufwerk 8: `LOAD"STAGE3B4A",8`, dann `RUN`.
Vor dem Laden muss der Bildschirm geleert und der Hintergrund schwarz werden.
Beide Originaldateien müssen geladen/verifiziert werden. Danach schwarzes Spielfeld
ohne BASIC-Inhalt; alle 24 Pixies ohne Spuren, richtige Originalgrafiken und Animation.
HUD-Schrift insbesondere H/I/G/Score-Ziffern prüfen. Drei Lebenssymbole, vorbereitetes
4×2-Feld mit Abständen, Player 2 inaktiv, „No P2“, P/S weiterhin ohne Funktion. Joystick,
SPACE und +/- wie 3b-3. Mehrfach X: normaler BASIC-Bildschirm mit normalem Cursor und
restaurierter Hintergrundfarbe; anschließend erneut LOAD/RUN. Erst nach ausdrücklicher
Bestätigung durch den Benutzer als stabil markieren.
