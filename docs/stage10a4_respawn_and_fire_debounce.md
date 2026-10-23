# Stage10a4 – Respawn wie im Original, entprellter Feuerknopf

Basis: Stage10a3 (Branch `stage10a3`, vom Benutzer am 22.10.2026 als
originalgetreu im Spielverhalten bestätigt). Separate Quellen
`src/engine/stage10a4*.asm`, Build `tools/build_stage10a4.py`, Release
`releases/stage_10a/stage10a4/`. Stage10a3 und alle älteren Stände bleiben
unverändert; das Buildskript prüft Stage10a3 zusätzlich gegen seinen Commit.

## Benutzervorgabe (22.10.2026)

Nach einem Player-Tod kehren alle Gegner in die Formation zurück. Der Player ist
in dieser Zeit unverwundbar, blinkt schneller als bisher, ist beweglich, kann aber
nicht feuern. Es starten keine Angriffe. Die Blinkrate soll aus dem Amiga-Code
ermittelt werden, ersatzweise viermal pro Sekunde. Außerdem lösen manchmal zwei
Player-Schüsse zu schnell hintereinander aus; ein neuer Schuss soll erst nach
Loslassen des Knopfs möglich sein.

## Befund im Amiga-Code

Disassembliert mit Capstone 5.0.7 (aus Quellcode gebaut), beide gespeicherten
Codekopien gegen die ADF-Relokation geprüft:
[`stage10a4_amiga_evidence/68000-excerpts.txt`](stage10a4_amiga_evidence/68000-excerpts.txt),
erzeugt von `tools/analysis/analyze_amiga_respawn.py`.

| Adresse | Inhalt |
|---|---|
| `$C09470` | Treffer erkannt (Kollisionsbits `$22`) |
| `$C094AA` | Kollisionsmaske `$2C32` gelöscht: unverwundbar |
| `$C094AE` | gemeinsamer Timer `$2C4E` = `$114` = **276 Updates** |
| `$C09598–$C095B2` | alle 4 Updates ein Explosionsframe, 11 Frames (44 Updates) |
| `$C095D8–$C095EE` | danach: Sichtbarkeit wird umgeschaltet, wenn `$2C4E mod 20 = 0` |
| `$C09678–$C09694` | Timer 0: Maske wiederhergestellt, Schiff sichtbar |
| `$C0D0A2` | solange `$2C4E≠0`: Feuerabfrage übersprungen |
| `$C0D0AA–$C0D12C` | Feuer-Latch `$2C38`: neuer Schuss erst nach Loslassen |
| `$C0D17E` | solange `$2C4E≠0`: keine neue Angriffsauswahl |

Es gibt keine Wartephase auf die Formation und keinen Positionsreset; das
Schiff blinkt an seiner Position, laufende Angreifer fliegen ihre Kurven zu Ende
und kehren zurück. Die Umschaltprüfung liegt im 4-Update-Takt der Explosion; da
276 ≡ 0 mod 4 ist, trifft sie genau jeden 20. Update.

**Blinkrate:** Umschalten alle **20 Updates**. Bei einem Update pro
50-Hz-Frame (Zeitbasis der gesamten Portierung, Kurven und Pendeln vom
Benutzer als originalgetreu bestätigt) sind das 2,5 Umschaltungen pro Sekunde,
also 1,25 volle Hell-dunkel-Zyklen. Bisher waren es 25 Frames. Exakt ein Update
pro Video-Frame ist im Amiga-Code selbst nicht unabhängig gemessen
(`amiga_enemy_fire_analysis.md`).

## Änderungen

| Punkt | Stage10a3 | Stage10a4 |
|---|---|---|
| nach Explosion | WAIT unsichtbar, bis alle Gegner in Formation | sofort BLINK an der Trefferposition |
| Schutzfenster | Explosion + Wartezeit + 150 Frames | 276 Frames ab Treffer (21 Explosion + 255) |
| Blinken | alle 25 Frames | alle 20 Frames, erstes Umschalten bei Timer 240 |
| Feuer im Respawn-BLINK | erlaubt | gesperrt; danach erst nach Loslassen |
| neue Angriffe | gesperrt bei Explosion/WAIT | zusätzlich im ganzen Respawn-BLINK gesperrt |
| Feuer-Latch | ein losgelassener Frame entsperrt | zwei aufeinanderfolgende losgelassene Frames |

Neues Flag `c_respawn` (`$1C9D`, im von `c_reset` genullten Block) trennt den
Todes-Respawn vom Zweispieler-Zugstart: Der Zugstart behält 150 Frames Schutz
mit erlaubtem Feuer und Angriffen; nur die Blinkperiode ist dort jetzt ebenfalls
20 Frames.

**Doppelschüsse:** Der Joystick wird einmal pro Frame gelesen. Ein prellender
Knopf, der genau zu einem Abtastzeitpunkt kurz offen ist, entsperrte bisher den
Latch und löste einen zweiten Schuss aus. Jetzt muss das Loslassen in zwei
aufeinanderfolgenden Frames (40 ms) gesehen werden; ein dazwischen gelesenes
„gedrückt“ sperrt erneut. Ein bewusst schnelles Antippen bleibt möglich.

**Adressen:** Neue Routinen in `$7F72–$7FF2`, dem reservierten, bisher
ungenutzten Ende des Kollisionsbox-Segments (Grenze `$8000`). Alle ersetzten
Blöcke sind mit NOPs auf ihre alte Länge gebracht: kein Symbol verschoben,
PRG gleich lang (45.057 Byte). Geänderte Bytes nur in `$4DAB`, `$4DDC`
(Respawn), `$4F7D` (Angriffssperre), `$7F72–$7FF2`, `$8308` (Feuer),
`$9E00` (Feuerzustand). Alle DAT-Dateien, Menü, Audio und Highscore-Overlay
byteidentisch zu Stage10a3.

## Tests

`tests/test_stage10a4.py` führt die assemblierten Routinen aus dem PRG mit py65
aus: 276-Frame-Fenster mit sofortigem BLINK, Umschalten exakt alle 20 Frames,
Respawn an der Trefferposition, Feuer- und Angriffssperre, Zugstart unverändert,
Entprellung (Halten, Ein-Frame-Prellen, Zwei-Frame-Loslassen, externe Sperre).
8/8 bestanden. Das sind Hostprüfungen der Logik, keine XEMU-/Hardwaretests.

Build wie Stage10a3 (`KickAss65CE02-5.25.jar`, Gleichwertigkeit dort belegt):
`python3 tools/build_stage10a4.py --kickass <jar> --zx0 <zx0>`.

## Abnahme

Auf echter Hardware (Regel19): sofortiges Blinken nach der Explosion, Dauer und
Rate des Blinkens, keine Angriffe und kein Feuer während des Blinkens, Bewegung
möglich, Rückkehr laufender Angreifer, normales Spiel danach. Schnelles Feuern
ohne Doppelschüsse. Zweispieler-Zugstart unverändert.
