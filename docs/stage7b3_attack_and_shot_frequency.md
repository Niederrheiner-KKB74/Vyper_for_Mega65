# Stage 7b3 — Angriffsauswahl und sechs Gegnerprojektile

Issue #57, Branch `stage7b3`, **Testbuild, nicht Stable**. Unveränderte
Ausgangsbasis: funktionierender Stage7b2-Commit
`ec7a512bf913e522e5aaadfd57c9c4e7bb019bef`. Der Builder prüft dessen bestehende
Quellen, Assets, Tools und Release sowie die früheren Stable-Referenzen.
`main`, Stage7b2 und die parallele Bereinigung werden nicht verändert.

**Grafikklärung:** Issue57 nennt weiße1×4-Player-Schüsse, die tatsächliche
Referenz enthält jedoch3×7 mit roter Spitze oben. Der Benutzer hat ausdrücklich
bestätigt, diese3×7-Grafik unverändert zu übernehmen. Gegner bleiben3×7 mit
roter Spitze unten und grauen Seitenpixeln. Die128 Spritebytes bleiben bytegleich.

## Nachgewiesene Ursache

Stage7b2 `a_postframe` setzt den Angriffstimer alle60 Frames zurück, nimmt
`random_lo &31` und verwirft den Termin bei Index außerhalb `$7603`, DEAD,
EXPLODING oder nicht verfügbarer Formation. Es wird nur ein ursprünglicher
Slot geprüft. Auch bei einem verfügbaren Gegner entsteht deshalb nur eine
Chance von etwa1/32 pro Termin, nicht1/1. Bei22 verfügbaren Slots beträgt sie
22/32. Der Grund für die stark sinkende Frequenz ist damit im Code belegt.
Auch ein Termin bei drei laufenden Angriffen setzt den bisherigen Timer zurück.

Die bisherige Schussroutine hat einen zweiten unabhängigen Filter: nur bei
`random_lo &7 ==0` (1/8) wird ein ursprünglicher Slot aus `random_hi &31`
geprüft. In der Formation schießt jedoch ausschließlich ENTRY/ATTACK, im
normalen Angriffsverlauf oft nur einer bis drei dieser22 Slots. Entsprechend
selten führt ein Schusstermin tatsächlich zu einem Projektil.

## Neue Auswahl und Parameter

`selection.collect` scannt höchstens die tatsächliche ursprüngliche Gegnerzahl
(max22) und erstellt eine kompakte Liste verfügbarer Slots. Für Angriffe:
`c_es=FORMATION(1)` **und** `e_phase=3`. WAIT_ENTRY, ENTRY, ATTACK, RETURN,
EXPLODING und DEAD werden ausgeschlossen. Die Liste darf Lücken enthalten,
z.B. nur Slot21; die ursprüngliche Recordzahl wird nicht künstlich verkleinert.

`selection.choose` wählt einen Rang aus dieser Liste. Die Maske ist
`next_power_of_two(count)-1`. Werte außerhalb der Listengröße werden verworfen,
um eine Modulo-/First-match-Verzerrung zu vermeiden. Ein verworfener Rang
verbraucht **keinen neuen Cooldown**; es wird im nächsten Frame erneut geprüft.
Es gibt keine unbeschränkte Wiederholungsschleife. Bei einem oder zwei
Kandidaten ist jede Stichprobe gültig; bei anderen Größen beträgt die
Annahmewahrscheinlichkeit mehr als50%. Bei0 Kandidaten erfolgt sofort Return.
Die Gleichverteilung bezieht sich auf die zulässigen RNG-Ränge; ein endlicher
LFSR-Testlauf muss nicht exakt gleiche Häufigkeiten je Gegner liefern.

Maximal3 ATTACK bleiben erhalten. Der Timer wird erst nach einem gestarteten
Angriff gesetzt. Ist er während ATTACK/RETURN bereits abgelaufen, kann ein
zurückgekehrter Einzelgegner sofort erneut ausgewählt werden. Der vorhandene
Einflug-/Ready-Barrier, die ersten100 Countdownframes, originale `attack_index`,
Kurvendekodierung, Angriff/Rückkehr und bewegte Formation bleiben erhalten.
LEVEL CLEAR, Übergang und GAME OVER lassen keine neue Auswahl zu.

| Parameter | Stage7b2 | Stage7b3 | Bedeutung |
| --- | --- | --- | --- |
| `a_START_INTERVAL` |60 Frames|30 Frames| Intervall zwischen gestarteten Angriffen |
| erste Countdownphase |100|100| beginnt wie bisher erst nach Einflug/Ready |
| `a_SHOT_COOLDOWN` |12|6| Pause nach einem tatsächlich erzeugten Gegnerschuss |
| `a_SHOT_RANDOM_MASK` |7 (1/8)|1 (1/2)| Roll bei freiem Schuss-Cooldown |
| maximale ATTACK |3|3| unabhängiges Angriffslimit |
| Gegnerprojektile |4|6| unabhängig vom Schusstakt |
| Playerprojektile |2|2| unverändert |

Die Intervalle und Wahrscheinlichkeit sind **gewählte Testparameter**, keine
behaupteten Original-Amiga-Messwerte. Die Konstanten stehen in
`stage7b3_attack.asm`; der historische T-Test hat seinen eigenen6-Frame-
Cooldown in `stage7b3_shots.asm`.

Für Schüsse wird ebenfalls aus der Liste berechtigter Schützen gewählt.
Die bisherigen Prüfungen bleiben identisch: genuine ENTRY mit Sichtbarkeitsflag
oder sichtbarer ATTACK, keine RETURN-/WAIT_ENTRY-/FORMATION-Schüsse, signed
Mündungsposition X+8/Y+16, X-Mündung<238 und Y-Mündung16..183. Erst ein freier
Slot2..7 erzeugt einen Schuss und setzt den Cooldown. Voller Pool überschreibt
keinen bestehenden Schuss. Zielkoordinaten werden beim Abschuss gespeichert;
8.8-Flugbahnen, Geschwindigkeit und Trefferboxen bleiben unverändert.

## Acht Spritekanäle und Speicher

| Kanäle | Funktion | Grafikpointer |
| --- | --- | --- |
|0,1| unabhängige Player-Schüsse |$228, Bitmap$8A00 |
|2..7| sechs unabhängige Gegner-Schüsse |$229, Bitmap$8A40 |

Pointertabelle `$8900..$890F` wird vollständig initialisiert. D015 und sämtliche
X-/Y-MSB-/Bit9-Masken verwenden alle acht Bits; D076=$FF (V400), D01C=$FF
(Multicolor), SPR640 bleibt erhalten. Keine neuen Grafikbytes/Paletten:
Weiß/Rot/Grau in fester Bank2 an10/13/16; Originallevelpaletten und Cycling
bleiben getrennt. Kein Sprite-Multiplexing und keine neue IRQ-Routine.

Zwölf Projektilarrays wurden von6 auf8 Einträge erweitert, Byteabstand8.
Der vollständige State mit24 skalaren Bytes liegt nun `$1F00..$1F77` (120 Bytes).
Die verfügbaren Gegner stehen `$1F80..$1F95`; Count/Mask/Scan/Kind bei
`$1F96..$1F99`. Dies nutzt den bisher unbenutzten Rest der dokumentierten
Engine-Reserve `$1800..$1FFF`, hinter dem Entryzustand bis `$1EF3` und vor dem
Programm ab `$2001`. Die tatsächlichen Symbolbereiche und Resetgrenzen wurden
geprüft; ein Assemblerguard trennt State und Liste. DOS, DATs, Pixiepuffer und
RRB-Screen-/Color-RAM bleiben unverändert.

Die Registersicherung bleibt `$1B60..$1B8A` (43 Bytes). Positionen aller acht
Sprites waren bereits enthalten; die Farben von Sprite6/7 sind jetzt ergänzt.
Die bisher ungerollte Snapshotroutine hätte die RRB-Routine ab `$9D70`
überlappt. Daher ersetzt sie eine kompakte tabellengesteuerte RAM-Routine bei
`$9B70`; Selection-/Restore-Helfer nutzen die dadurch freie Lücke ab `$9C00`,
mit Assembler-Endgrenze `$9D70`. Selbstmodifikation betrifft ausschließlich
LDA-/STA-Registeradressen in diesem RAM-Code, unter dem bestehenden Programm-
Mapping, nicht ROM. Snapshot nach Unlock und vor der Legacy-Spriteinitialisierung.

Beim BASIC-Exit werden zusätzlich alle acht Spritepositionen, Modi und Farben
IRQ-geschützt restauriert; D015 bleibt wie bisher aus. Die Restore-Schleife
aktiviert keinen IRQ während noch die Spiel-RRB-Konfiguration sichtbar ist.
Der vorhandene BASIC-/Palette-/Color-RAM-/HOTREG-/DOS-Restore folgt unverändert.
Game Over, Level Clear und Übergang löschen jetzt ausdrücklich alle8 Slots.
Der aktuelle genaue Speicherplan steht im Release `memory-map.txt`.

## Messvergleich: 3.000 echte Hostticks = nominell60 Sekunden

`tools/measure_stage7b3_frequency.py` führt den tatsächlichen assemblierten
Code separat für beide Versionen aus, mit Seed `$C3A5`, Level1 und jeweils
22,10,5,2,1 FORMATION-Gegnern. Die ursprüngliche Recordzahl bleibt22; nur die
übrigen Gegner sind DEAD. CPU-PC-Hooks zählen Termine vor `a_postframe`, ohne
Instrumentierung des Spielcodes. `a_objects → e_objects → ygeometry.postframe`
ruft den Scheduler exakt einmal pro Tick auf. Keine doppelte Timerbewegung.

Drei klar getrennte Versuche:

1. **Ständig verfügbar:** nach jedem Tick werden die Testgegner wieder in
   FORMATION gesetzt. Dies isoliert die Kandidatenauswahl/Timer vom Kurvenweg.
2. **Echte Kurven/Rückkehr:** ursprüngliche Bewegung und Formation laufen;
   ATTACK/RETURN-Gegner sind real nicht verfügbar. Rendern und Kollisionen sind
   nur in dieser Messhülle ausgelassen, um den kontrollierten Bestand zu halten.
3. **Schießen isoliert:**22 sichtbare, feste ENTRY-Schützen; tatsächliche
   Projektile bewegen sich, altern und werden freigegeben. So wird die
   Schussroutine unabhängig vom Angriffsscheduler gemessen.

| verbleibend | Angriffe stets verfügbar7b2→7b3 | Angriffe echte Kurven7b2→7b3 | Rückkehr abgeschlossen7b2→7b3 | Gegnerschüsse echte Kurven7b2→7b3 |
| --- | --- | --- | --- | --- |
|22|35→99|29→48|27→45|17→216|
|10|15→98|12→48|10→43|8→212|
|5|10→98|9→45|7→40|8→180|
|2|4→100|3→14|2→12|5→131|
|1|3→100|2→3|1→2|4→35|

Der Auswahlabfall ist im isolierten Test beseitigt. Beim Einzelgegner begrenzt
der lange **unveränderte** Original-Angriffs-/Rückkehrweg die Anzahl realer
Angriffe. Die mittlere Wartezeit in Formation beträgt im Kurventest bei einem
Gegner7b2:488 Frames (max660),7b3:0 Frames. Er startet nach jeder im Messfenster
abgeschlossenen Rückkehr im selben Tick erneut. Das ist keine künstlich
beschleunigte Kurve. Maximal3 gleichzeitige ATTACK wurden nicht überschritten.

| isolierte Schussmessung |7b2|7b3|
| --- | --- | --- |
| cooldownfreie Schussprüfungen |2223|2357|
| erzeugte Schüsse |63|103|
| Frames mit vollem Gegnerpool |1822|2464|
| gleichzeitig aktive Gegnerprojektile, Peak |4|6|

Sättigung begrenzt auch bei höherem Takt die Geburtenzahl;6 statt4 Slots sind
kein Frequenzparameter. Die JSON-Berichte enthalten zusätzlich Angriffstermine,
verfügbare Chancen, Starts je Gegner, Wartezeiten und Peaks. Die Vergleiche
verwenden denselben Startseed, nicht dieselbe RNG-Folge: die korrigierte Auswahl
verbraucht bei anderen Terminen RNG-Schritte. Es sind deterministische
Hosttests des Assemblercodes, **keine XEMU-/Hardwaremessung**.

## Build und automatische Prüfungen

```sh
python tools/build_stage7b3.py --kickass /pfad/KickAss.jar
PYTHONPATH=tests:tools:/pfad/test-deps python -m unittest test_stage7b3 -v
PYTHONPATH=tests:tools:/pfad/test-deps python tools/measure_stage7b3_frequency.py --stage 7b2 --output /tmp/7b2.json
PYTHONPATH=tests:tools:/pfad/test-deps python tools/measure_stage7b3_frequency.py --stage 7b3 --output /tmp/7b3.json
python tools/package_stage7b3.py
```

KickAssembler5.25, vorhandene py65-/45GS02-Hostadapter; Prüfsummen, Stable-
Schutz und komplette D81-Dateiketten wie bisher. D81: STAGE7B3 sowie VYTI,
VYMN, VYLV, VYGR und VYCL. Alle fünf DATs und128 Spritebytes sind unverändert.
Die Fullsuite und abschließenden gezielten Restore-/Mehrkurventests erhalten
separate PRG-Hashes und Logs im Release. Keine XEMU-Abnahme vorweggenommen.

## XEMU-Abnahme

`LOAD"STAGE7B3",8`, `RUN`, Joystick Port2, F1. In Level1 Gegner auf10,5,2,1
reduzieren: verbleibende FORMATION-Gegner sollen regelmäßig starten; niemals
mehr als3 gleichzeitig ATTACK. Bei1 Gegner Rückkehr und unmittelbare erneute
Auswahl beobachten. Leerlauf während seiner Kurve ist erwartbar.

Sechs Gegner- und zwei Player-Schüsse gleichzeitig prüfen: keine verschwindenden
Player-Schüsse, alle acht unabhängig sichtbar, normale weiße/rote/graue Farben,
korrekte Richtungen/Zielaufnahme, Treffer, Explosion, steuerbarer Respawn und
Unverwundbarkeit. Player-Spitze oben bleibt gemäß Benutzerklärung erhalten.

Level1/2/3 und29/60 prüfen, außerdem Sonderlevel mit weiterhin gesperrten
unbestätigten Kurven. Menü/Startlevel/F2/F3,100→1, +/- ohne Effekte, LEVEL CLEAR,
Sternbeschleunigung/Ringe/Schwarz, Game Over/R, X auch in Übergangsphasen,
BASIC/DIRECTORY und erneutes RUN. Palette-/Stern-/HUD-/RRB-Regression optisch
prüfen. Stage7b3 erst nach ausdrücklicher Benutzerbestätigung Stable/Merge.

Automatik abgeschlossen:42 vollständige Regressionstests bestanden. Nach der
abschließenden Ergänzung des IRQ-geschützten8-Sprite-Restores vier gezielte
Prüfungen des finalen PRG bestanden. Alle49 Builddateien plus Manifest
aus zwei unabhängigen Builds bytegleich. Die Auswahl-/Angriffs-/Schussroutinen
der Frequenzmessung bleiben im finalen Build unverändert; die gemessenen
PRG-Hashes stehen in den JSON-Dateien. Keine eigene XEMU-Abnahme.

Zusätzlich bestanden: gezielte Veröffentlichung aller8 Spritekanäle mit
X-/Y-MSB und Bit9 (native Testkoordinaten555/896), einschließlich Kanal6/7.
Dies ist ein Registertest des realen Publishers, keine sichtbare XEMU-Szene.
