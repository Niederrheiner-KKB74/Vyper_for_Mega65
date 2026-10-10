# Stage 3b-5b: Sprite-Projektile und bestätigte Grafikzuordnung

Implementiert das aktualisierte [Issue #6](https://github.com/Niederrheiner-KKB74/Vyper_for_Mega65/issues/6).
Eigener Branch `stage3b-5b`, Basis `stage3b4a-stable` (`cb917b7`). Quellen und sämtliche
Release-Dateien von Stage 3b-4a bleiben bytegleich. Stage 3b-5b ist am 10.10.2026 vom Benutzer bestätigt; stabile Referenz `stage3b5b-stable`.

## Vorprüfung und Eingriffspunkte

Die stabile Stage schaltet `$D015` nach ihrer alten Spriteinitialisierung auf Null.
Player, alle 24 beweglichen Pixies und das 4×2-Lebensfeld werden ausschließlich per
RRB dargestellt. Alle acht Hardware-Kanäle sind deshalb frei. Der alte, nicht mehr
benötigte Hardware-Player-Initializer wird in der neuen Stage nicht aufgerufen:
Er würde kurzzeitig drei Legacy-Sprites aktivieren. Stattdessen wird abgeschaltet,
danach werden ausschließlich die neuen Projektilsprites initialisiert.

RRB-Zeilen, CHARXSCALE, Screen-/Color-RAM, Font, Palette und Grafikpuffer bleiben
unverändert. Vier JSR-Hooks betreffen Initialisierung, GETIN und den Frame-Aufruf;
die BASIC-SYS-Zeile startet bei `$8200`, und exakt 16 Byte Grafikübersetzung werden
ersetzt. Alle übrigen Baseline-Bytes bleiben erhalten. Der Builder prüft dies gegen
den SHA-256 der stabilen PRG und prüft, dass alle neuen Code-/Datenbereiche leer waren.
Alle alten, weiterhin vorhandenen Assembly-Labels behalten ihre Adressen.

## Kanalbelegung und Register

| Kanäle | Verwendung | Farbe / sichtbare Grafik |
| --- | --- | --- |
| 0–1 | zwei unabhängige Spielerschüsse | Bank 2, Index 10 (HUD-Weiß), 1×4 logische Pixel |
| 2–5 | global maximal vier Gegnerschüsse | Bank 2, Index 13 (HUD-Rot), 3×4 logische Pixel |
| 6–7 | frei, deaktiviert | keine Darstellung |

Monochrome 24×21-Hardware-Sprites, nur die ersten acht nativen Rasterzeilen enthalten
Pixel. `$D06B/$D057/$D055/$D017/$D01D/$D01C` werden auf Null gesetzt: keine Full-Color-,
breiten, hohen, expandierten oder Multicolor-Sprites. `$D01B=0` zeichnet vor dem RRB.
SPR640 (`$D054` Bit 4) und V400 (`$D076=$3F`) betreffen nur Sprite-Koordinaten, nicht
die bestehende RRB-Ausgabe. Das Tiling in den oberen Nibbles von `$D04D/$D04F` wird
abgeschaltet; die unteren Nibbles des tatsächlichen Textursprungs bleiben erhalten.

Die 16-Bit-Pointertabelle liegt bei `$8900` (`$D06C/$D06D`, `$D06E=$80`). Pointerwerte
sind Adresse/64: `$228` für `$8A00`, `$229` für `$8A40`. `$D000–$D00B` sind X/Y,
`$D010` liefert X-Bit 8, `$D05F` X-Bit 9, `$D077/$D078` Y-Bits 8/9. `$D015` wird pro
Frame aus den sechs Aktivflags neu aufgebaut. Nur deaktivierte Slots werden wiederverwendet.
Es werden keine Kollisionsregister gelesen und keine Treffer ausgelöst.

Vor Loader und Engine wird der ursprüngliche Spritezustand gesichert. Beim Exit
schaltet die bewährte HUD-Routine sofort alle Sprites ab. Nach der unveränderten
BASIC-Restaurierung stellt ein Wrapper sämtliche zusätzlich veränderten Positionen,
Farben, Modi, Zeiger und MSB-Register zurück. HOTREG wird dafür temporär deaktiviert
und zuletzt restauriert. `$D015` bleibt Null; es erscheinen keine Projektilreste.
Das gilt auch bei Ladefehlern. Keine Zero-Page-Adressen oder BASIC-Cursorbytes werden verwendet.

## Gemeinsame Koordinaten und Richtung

Das logische Spielfeld ist `[0,240) × [0,200)`. Der aktuelle Player steht im bisherigen
Objektrecord `$1660` (X bei +2, Y bei +4). Gegnerpositionen stammen unverändert aus
`s2i_x/s2i_y`. Ein Pixie ist 16×16 logische Pixel groß. Alle Schusszustände werden
in diesen Koordinaten gespeichert; Umrechnung erfolgt ausschließlich in `p_publish`.

Aus XEMU `targets/mega65/vic4.c` und `vic4.h`: SPR640 zeigt Register-X + 1 an, V400
zeigt Register-Y ohne Legacy-Y-Adjust an. Deshalb werden CHARX/CHARY zur Laufzeit
aus `$D04C–$D04F` gelesen (je Low-Byte und unteres High-Nibble):

- Player-Register-X = CHARX + 2×shot_x − 1; sichtbare linke Kante = CHARX + 2×shot_x.
- Enemy-Register-X = CHARX + 2×shot_x − 3; sichtbare linke Kante = CHARX + 2×(shot_x−1).
- Register-Y = CHARY + 2×shot_y; die Grafiken enthalten jeweils acht native Zeilen.

So startet der Spielerstrahl exakt bei `(player_x+8, player_y)`, der Gegnerstrahl
bei `(enemy_x+8, enemy_y+16)`. Die Zielposition ist einmalig `(player_x+8, player_y)`.
Hardware- und RRB-Ursprünge werden ausdrücklich nicht gleichgesetzt. Alle X/Y-MSBs
werden pro Frame neu berechnet. NCM-/Textskalierung wird nicht geändert.

Positionen sind **unsigned 8.8**, Geschwindigkeiten **signed 8.8**. Das ist bewusst
keine signed-8.8-Position: diese könnte X ≥128 nicht positiv darstellen. Addiert wird
16-bittig, anschließend erfolgt die Feldprüfung. Ein negativer X-Unterlauf wird
als großer unsigned-Wert erkannt und deaktiviert; maximal zwei Pixel pro Tick
verhindern ein Überlaufen zurück in einen gültigen Feldbereich.

Beim Gegnerabschuss: `dy = target_y − shot_y`, `dx = target_x − shot_x`.
Für `dy <= 0` wird kein Projektil angelegt. Sonst `vy=1`,
`vx = sign(dx) × min(floor(abs(dx)×256/dy),512)` als 8.8-Wert. Eine 16-Schritt-Division
mit 16-Bit-Rest läuft nur beim Abschuss. Kleine Distanzen / großes dx führen zum
Clamp ±2 Pixel pro Frame; dann wird die Zielrichtung begrenzt und das Ziel muss nicht
exakt getroffen werden. Es gibt weder Division noch Ziel-Neuberechnung im Update.

Spielerschüsse bewegen sich mit drei Pixeln pro Tick streng aufwärts; X bleibt fest.
Ist Y kleiner als drei, wird der Slot vor einem Unterlauf deaktiviert. Gegnerschüsse
werden bei Zentrum-X <1 oder ≥239 sowie Y ≥197 deaktiviert, sodass auch ihre gesamte
3×4-Grafik im Feld bleibt. Updates betreffen bestehende Schüsse vor neuen Abschüssen;
ein neuer Schuss wird daher zunächst an seiner exakten Startposition dargestellt.

## Feuer und isolierter Testangriff

Joystick-Port 2 wird weiterhin einmal durch die bestehende Engine gelesen. Bit 4
(active low) wird aus `v014_joy_sample` benutzt. Ein Druck erzeugt höchstens einen
Spielerschuss; erst Loslassen setzt den Latch zurück. Sind beide Slots voll, wird
kein weiterer angelegt. Es existierte in der aktiven Stage-4a-Engine keine zusätzliche
Tastatur-Feuerbelegung. X, Joystick, SPACE und +/− behalten ihre Funktion; P/S bleiben inaktiv.

**Nur Gegner Nr. 19 (Arrayindex 18) besitzt den isolierten Test-Angriffsstatus.** Er
bleibt ein vorhandener, animierter Typ-15-Pfad-Pixie. Keine weiteren RRB-Objekte und
keine erfundenen Gegnerframes. Sein Bewegungspfad wird nicht geändert. Die Routine
`p_test_attack` erzeugt allein den Status: 96 Frames Angriff, danach 32 Frames Formation,
Periodendauer 128. `T` schaltet den Testmodus aus/ein (initial ein). Originalkurven
werden nicht simuliert oder als implementiert ausgegeben. Später wird ausschließlich
`p_test_attack` durch den echten Angriffsstatus/-gegner ersetzt; Feuer/Update bleiben nutzbar.

Der Spieler startet unverändert weit oben (Y=32). **Zum Testen der Gegnerschüsse den
Spieler nach unten bewegen**, unter die untere Mitte des schießenden Gegners. Steht
er darüber, werden entsprechend der definierten dy-Prüfung keine Schüsse erzeugt.

Zufall: 16-Bit-Galois-LFSR, Rechtsschieben und Polynom `$B400`, einmal pro Frame.
Seed aus CIA1-Timerbytes und Rasterregistern; Null wird durch `$ACE1` ersetzt. Kein
neuer Timer wird gestartet. Während eines Angriffs, mit freiem Slot und abgelaufenem
Cooldown entscheidet `(random_lo & 7)==0` (1/8 Wahrscheinlichkeit pro geeignetem Frame).
Anfangs-Cooldown 25 Frames, danach mindestens zwölf ruhige Frames zwischen Abschüssen.
Bei Formation oder vier belegten Slots wird nicht gefeuert. Parameter stehen als
Konstanten bzw. als klar kommentierter Test-/Zufallsschwellenwert in der Quelle.

## Speicher und API für Stage 3b-5c

| Bereich | Inhalt |
| --- | --- |
| `$1B00–$1B47` | sechs SoA-Projektilslots, zwölf Arrays à sechs Byte |
| `$1B48–$1B5F` | Latch, PRNG, Cooldown, Teststatus, Publish-/Divisionsarbeit |
| `$1B60–$1B88` | ursprüngliche Sprite-Register (41 Byte) |
| `$8200–$85A9` | Initialisierung, Feuer, Update, Publish und Teststatus (exakt: Assembly-Map) |
| `$8900–$890F` | Spritepointertabelle |
| `$8910–$8935` | VYLV→VYGR-Tabelle (38 Einträge) |
| `$8936–$895B` | Bestätigungsflags, nur Index 14 ist 1 |
| `$8A00–$8A7F` | zwei monochrome Projektilgrafiken |
| `$9B00–$9D6E` | Spawn-Division und Register-Restaurierung (exakt: Assembly-Map) |

Zwölf Arrays: `active`, `xfrac`, `xpos`, `yfrac`, `ypos`, `vxfrac`, `vx`, `vyfrac`, `vy`,
`target_x`, `target_y`, `source_enemy`. Slotindex 0–1 bedeutet Player, 2–5 bedeutet
Enemy. Hitboxvorbereitung: Player `[x,x+1)×[y,y+4)`, Enemy `[x−1,x+2)×[y,y+4)`.
Die Felder liefern die Daten für spätere Software-AABB; noch keine Kollisionslogik,
Explosionen, Punkte-/Lebensänderungen oder Game Over. Getrennte Routinen heißen
`p_init`, `p_player_fire`, `p_enemy_fire`, `p_update`, `p_deactivate`, `p_publish`.

## Zentrale Grafikzuordnung

Einzige gepflegte Datenquelle ist `assets/vylv_vygr_mapping.json`. Der Builder erzeugt
daraus Lookup-Tabelle und Bestätigungsflags in `stage3b5b_mapping.asm`.
VYLV-Wert **14 → VYGR-Typnummer 15 → Verzeichnis-Arrayindex 14**. Das Verzeichnis liegt
bei Dateioffset `8 + 14×8 = 120`; die bestehende Routine berechnet denselben Offset als
`15×8`. Das Originalverzeichnis liefert sechs Frames à 128 Byte. Der vorhandene
Animations-/DMA-/Rückvergleichspfad durchläuft sie unverändert.

Alle anderen 37 Einträge sind unbestätigt: 0/1→12, ansonsten 2–37→index−1, ausschließlich
als historischer Fallback. Das bestätigt keine weiteren Original-Zuordnungen.
[Zuordnungsstatus](vylv_vygr_mapping_status.md) ersetzt frühere Aussagen zu 14→12/31.
Der historische Analyzer für Stage 3b-2 bleibt unverändert; seine damalige Mapping-
Interpretation gilt nicht für die neue Stage. Originaldaten und alte Releases bleiben erhalten.
Die dort separat dokumentierten Punkte 100/175 werden in dieser Stage nicht integriert:
Das unveränderte HUD enthält weiterhin die bisherigen Mockup-Werte 100/115, keine Trefferpunkte.

## Reproduzierbarer Build und automatische Prüfung

```sh
python3 tools/build_stage3b5b.py --kickass /pfad/zu/KickAss.jar
```

KickAssembler 5.25 wird per SHA-256 geprüft; Java erforderlich. Ausgabe vollständig
unter `releases/stage_3b5b/`: PRG, D81, fünf ASM-Dateien, Symbole, Assembly-Map,
Mapping-JSON, Buildreport und SHA256SUMS. Die D81 enthält `STAGE3B5B` als PRG und
beide bytegleichen Originaldateien als SEQ. Laufwerk 8: `LOAD"STAGE3B5B",8`, dann `RUN`.

```sh
PYTHONPATH=/pfad/zu/py65 python3 -m unittest discover -s tests -p 'test_stage3b5b.py' -v
```

Neun Tests führen die assemblierten CPU-Instruktionen mit vorhandenen KERNAL-/DMA-/VIC-
Modellen aus: vollständiges Laden, Mapping, alle sechs Frames, zwei unabhängige Schüsse,
Latch/Slotwiederverwendung, vier globale Gegnerslots, Formation/Cooldown, Zielaufnahme,
kein Homing, 72 Divisions-Grenzfälle, variable Zufallsabstände, Feldgrenzen, sechs
Hardware-Kanäle samt echter Pointer-/Bitmapdaten und Koordinaten/MSBs, identische
Spieler-/Gegnerbewegung und HUD über 30 Frames, Exit, Color-/Cursor-/Registererhaltung,
Ladefehler und zweiter RUN. Mit `MEGA65_ROM` wird zusätzlich die echte bereitgestellte
V920395-Cursorroutine ausgeführt. Build prüft Baseline-Bytes, Assets und D81-Dateiketten/BAM.
Neun Tests bestanden. Wiederholungsbuild byteidentisch.

Ein Hostmodell bestätigt keine tatsächlichen Rasterlatenzen oder vollständige XEMU-
Darstellung. Der bestehende Rasterwait bleibt bytegleich; 50-Hz-Performance und präzise
sichtbare Kalibrierung sind Teil der [bestätigten XEMU-Abnahme](stage3b5b_xemu_test.md).
Die ausdrückliche Benutzerbestätigung liegt vor. Bestätigter Programmstand:
`6f378c2faa136a6d25b5d8d32f51e3ba79f02518`. Der Tag `stage3b5b-stable` sichert diesen Stand
einschließlich der Abnahmedokumentation; Release-Artefakte bleiben unverändert.
