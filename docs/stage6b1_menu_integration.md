# Stage 6b1 – Originalmenü und vollständige Spielintegration (Issue #47)

Entwicklungsbranch `stage6b1`, **noch nicht Stable**. Die XEMU-Abnahme steht aus.

## Unveränderte Ausgangsstände

- Spielengine: `stage5d1a-stable`, Commit `39890c0095fab55b2ea71f95cccf59a3419848c6`, Branch `stage5d-1-b2`.
- Originalmenü: `stage6a2-stable`, Commit `24559e46c4f237492bc4e03439c86ea6c402a0b0`.
- Alle vorhandenen Quellen, Assets und Releases dieser Referenzen bleiben bytegleich. Der Builder prüft beide Tags und sämtliche vorhandenen Baseline-Dateien.
- Stage 6a1 bleibt nur historisches Asset-/Extraktionsarchiv; die bestätigte Menüreferenz ist Stage 6a2.

## Ablauf und Bedienung

`Titel/SEQ-Laden → Originalmenü → Einspielerspiel → BASIC`.
Titelgrafik, originale 352×240-Palette und der bestätigte HOTREG-Handoff bleiben aus Stage 5d-1a erhalten. Zunächst wird zusätzlich `VYMN.DAT` geladen und gesichert; danach folgen VYLV, VYGR und VYCL. Das Titelbild bleibt während aller vier nachfolgenden SEQ-Dateien unverändert. Alle Kanäle schließen vor dem Menü. Das Menü verwendet die vollständige bestätigte 320×200-FCM-Darstellung, 32 individuelle Animationszyklen und den Originalfarbwechsel.

| Eingabe | Menüwirkung |
| --- | --- |
| Joystick Port 2 hoch/runter, Cursor hoch/runter | Auswahl der vier Optionszeilen; zyklisch |
| Joystick links/rechts, Cursor links/rechts | Nur bei INITIAL LEVEL: −1/+1, 001↔100 zyklisch |
| Feuer oder RETURN | Gewählte Option bestätigen; INITIAL LEVEL selbst startet nichts |
| F1 | Neues Einspielerspiel mit ausgewähltem Initial Level |
| F2 / F3 | Sichtbarer Platzhalter; Feuer/RETURN führt zurück, Auswahl und Level bleiben erhalten |
| X | Sauberer BASIC-Exit aus Menü, Platzhalter oder Spiel |

Nach jedem Programmstart steht INITIAL LEVEL auf 001. Nur die gewählte Zeile ist rot; die übrigen sind weiß. Hierfür werden die vier vorhandenen Originalindizes 8–11 geändert, nicht die Gegnerpalette oder das Cycling-Color02.

Joystick: neuer Richtungsimpuls sofort, Wiederholung nach 20 Frames (400 ms), danach alle 5 Frames (100 ms). Feuer verlangt eine Freigabe vor einer neuen Betätigung. Tastatur: direkte Hardware-PETSCII-Ereignisse, keine BASIC-Funktionstastenmakros. Cursor `$91/$11/$9D/$1D`, F1 `$85`, F2 `$89`, F3 `$86`, RETURN `$0D`; Referenz: MEGA65 User Guide, Kapitel Keyboard und PETSCII-Codes. Spalte 0 der dokumentierten C65-Matrix erkennt das Loslassen von Cursor-/Funktionstasten/RETURN. Wiederholte Richtungsereignisse werden ebenfalls auf 20/5 Frames begrenzt; Bestätigung wiederholt sich bei gehaltenem RETURN nicht.

Vor dem Übergang ins Spiel wird ein gehaltener Feuerbutton freigegeben und die Typing Queue geleert. Die Rücksprungadresse des Menü-Input-Aufrufs wird entfernt: der spätere Spiel-Exit kehrt zum ursprünglichen Loader-Aufrufer zurück, nicht in den inzwischen ersetzten Menüspeicher.

F1 startet Score 0, drei Leben, vollständigen gewählten Level einschließlich Gruppen, Kurven, Grafiken, Palette und HUD-Werten. Die bisherige Highscore-Initialisierung bleibt erhalten. Während des Spiels gelten weiterhin: R nach GAME OVER startet Level 1 und erhält den Highscore; LEVEL CLEAR verlangt Loslassen/neuen Feuerdruck, 100→1; +/- bleibt bei 1 und 100 begrenzt. Keine zusätzlichen Extra-Leben, kein echter Zweispieler-/Highscore-Listenmodus.

## Color-Cycling

Unveränderte Stage-6a2-Rekonstruktion: RGB4-Start `$0EC`, Phase 2, ein verbleibender Schritt; signed WORD-Deltas `$0020,$FE00,$0002,$FFE0,$0200,$FFFE`, sieben Schritte pro Abschnitt, sechs Abschnitte. Ein Schritt pro 50-Hz-Frame; Umlauf 42 Frames/840 ms. Originalbelege werden aus USS/BRAM/CRAM und Copper durch `tools/analyze_stage6a2_cycling.py` geprüft.

- Menü: Palettenbank 1, Index **2** für Umrandung, Hinweiszeilen und originale Gegnerpixel.
- Spiel: Palettenbank 1, Index **19 = $13**. Originalfarbe 2 wird durch das bestehende NCM-Format zu Nibble 3 und durch dessen Subpalette 16 zu Index 19.
- Player/HUD bleiben in Bank 2. Explosionen verwenden unverändert Bank 1, Indizes 0–15. Projektil-/Transparenzfarben bleiben statisch.
- Die übrigen sieben Farben jeder VYCL-Gegnerpalette bleiben bytegenau original. Kein Grafikbyte wird für das Cycling verändert.
- Der Zustand läuft beim Menü→Spiel-Handoff und bei Levelwechseln/R weiter. `pal.apply` veröffentlicht danach denselben Cycling-Wert erneut. Der Phasenreset erfolgt nur beim neuen Programmstart. Diese Integrationsentscheidung wird nicht als nachgewiesene Originalregel für Spielübergänge ausgegeben.

## Originalfont und HUD

Die Menüschrift wird aus den vorhandenen Amiga-Deskriptoren `$227FC + Zeichenindex×32`, erster Bitmapquelle `$185D2 + Zeichenindex×28`, extrahiert. Die 40 Originalglyphen umfassen Ziffern, A–Z und Sonderzeichen. Die sieben sichtbaren Reihen werden in den vorhandenen 8×8-Mono-Zeichensatz `$4000–$47FF` übernommen; Groß-/Klein-/Screen-Codes erhalten dieselben Originalbuchstaben. HUD-Layout, H640-Skalierung, 240-Pixel-Playfield und 4×2-Lebensfeld ändern sich nicht. Der bestehende Punkt für „Form.“/„Att.“ bleibt als einzige nicht vorhandene Menü-Punktuation erhalten, ebenso die beiden Mono-Rahmenglyphen. G/M werden beim R-Neustart nicht mehr mit dem alten Testfont überschrieben.

INITIAL LEVEL nutzt exakt die Originalposition der drei Ziffern: **X94, Y146**. Die dynamischen sechs FCM-Zellen erhalten auch die angrenzenden Hintergrundpixel. Der initiale 001-Screen wird im Hosttest vollständig gegen alle 64.000 Originalpixel verglichen.

## Speicherphasen und DMA

VIC-IV kann nur die dokumentierten 384 KB Chip-RAM direkt lesen. `$60000` und höher ist reservierte Chip-RAM-Erweiterung und wird **nicht** als vorhandener Grafikspeicher angenommen. Das dokumentierte 8-MB-Attic-RAM `$08000000–$087FFFFF` dient ausschließlich DMA-Sicherung, nicht VIC-Fetch. MEGA65/XEMU mit Attic ist erforderlich; Nexys ohne Attic wird nicht unterstützt. Bereits der Asset-Header wird nach Sicherung aus Attic zurückgelesen und geprüft.

| Bereich | Laden/Titel | Menü | Spiel |
| --- | --- | --- | --- |
| `$3100–$31C3` | Cycling-Code/State | Cycling | gleicher State, Spielindex 19 |
| `$31F0` | originales D030 | erhalten | BASIC-Restoration |
| `$3340…` | Bootstrap-DMA-Helper | dauerhaft | Restore bei X/RUN |
| `$4000–$47FF` | Titelbootstrap | erhalten | privater Original-HUD-Font |
| `$6800/$6900` | SEQ/Rückvergleich | nicht als Menügrafik genutzt | bisherige DMA-Arbeitspuffer |
| `$7000–$9FFF` | Enginecode/-daten | gesicherte, danach separate Menü-Overlayphase | Engine bytegenau zurückkopiert |
| `$7900–$7939` | ROMC-Gates | identische Gates im Menü-Overlay | gleiche Gates |
| `$9000–$97CF` | ursprüngliche Engine-Daten | 40×25-FCM-Screen | wiederhergestellte BASIC-Colorsicherung |
| `$9800–$9FFF` | Enginecode/-daten | Originalfont für dynamische Texte/Ziffern | Engine bytegleich restauriert |
| `$12000–$1217F` | Levelrecord | sechs dynamische Ziffern-FCM-Glyphen | Levelrecord neu geladen |
| `$12800–$1F7FF` | Titelglyphen/Engine-Bereiche | erste 832 Menü-FCM-Glyphen | private Pixie-Puffer frisch initialisiert |
| `$1F800–$1FFFF`, `$10000–$11FFF` | DOS-reserviert | unberührt | unberührt |
| `$20000–$3FFFF` | ROM | unberührt | unberührt |
| `$40000–$53F80` | temporär VYMN, danach VYLV | vollständiges VYLV | unverändert |
| `$54000–$5C2B7` | VYGR | unverändert | unverändert |
| `$5C300–$5C4DB` | VYCL | unverändert | unverändert |
| `$5C500–$5FFFF` | Titelglyphen/-Colorsicherung | restliche 236 Menü-FCM-Glyphen | Menü nicht mehr sichtbar |
| `$E000…` | vorhandener Spielscreen | nicht verwendet | unveränderter RRB-Screen |
| `$CB00–$CD44` | persistente Integration | gleich | gleich |
| `$FF82000–$FF82A4F` | Titel-Color-RAM | FCM-Menü-Attribute in ersten 2000 Bytes | wiederhergestellt |
| `$08000000–$080007FF` | Titelbootstrap-Sicherung | dauerhaft | Restore bei X |
| `$08001000–$08003FFF` | frei | Engine-Overlay-Sicherung | bleibt für nächsten RUN überschreibbar |
| `$08004000–$08004A4F` | frei | Original-Titel-Color-Backup gesichert | restauriert |
| `$08010000–$080252BF` | vollständiges VYMN | Overlay, Glyphen, drei Screens und Font | Fontquelle bleibt erhalten |

Die exakten assemblierbaren Grenzen stehen in `releases/stage_6b1/memory-map.txt` und den Symbolfiles. Das Overlay enthält **identische ROMC-Gates**, weil es selbst deren Enginebereich ersetzt. `$D030.ROMC` wird für den persistenten Code in `$CB00` abgeschaltet; das ursprüngliche BASIC-D030 bleibt außerhalb des Overlays erhalten und wird beim Exit aus einem niedrigen RAM-Gate restauriert. Fehlerpfade kehren in den Originalkontext zurück.

SEQ-Lader inklusive SETBNK, exakter EOF-Länge, Dateibytesumme und vollständigem DMA-Rückvergleich bleiben erhalten. `VYMN` Version 2 enthält einen gepinnten 32-Byte-Header, Originalpalette, FCM-Atlas, drei Screens und die separat assemblierten Menü-/Fontdaten. Der Builder prüft die Staging-Grenze vor dem aktiven Titelcache; keine Menü-DMA läuft mehr in der Titelphase. Die Engine-Overlay-Sicherung wird vor Spielinitialisierung vollständig zurückkopiert, danach werden die vom Menü genutzten privaten Frame-/Recordpuffer für den ausgewählten Level erneut vorbereitet.

## Reproduzierbarer Build

Python 3 mit Pillow, Java und geprüfter KickAssembler 5.25 (SHA-256 wird kontrolliert):

```sh
python tools/build_stage6b1.py --kickass /pfad/KickAss.jar
PYTHONPATH=tests:tools:/pfad/py65 python -m unittest test_stage6b1 -v
python tools/package_stage6b1.py
```

Der Builder verwendet die unveränderten, aus den Originaldaten rekonstruierten Stage-6a2-Menüassets. Vollständige Neu-Extraktion dieser Assetreferenz:

```sh
python tools/convert_stage6a1_menu.py --output /tmp/original-menu
python tools/analyze_stage6a2_cycling.py --output /tmp/original-cycle
```

Die neue deterministische Integration/Konvertierung läuft durch `tools/convert_stage6b1_menu.py` innerhalb des Builders. Alle weiteren Assets stammen unverändert aus dem Repository. Die Diskette enthält `STAGE6B1` (PRG), `VYTI.DAT`, `VYMN.DAT`, `VYLV.DAT`, `VYGR.DAT`, `VYCL.DAT`; DATs sind SEQ. D81-BAM, Dateiketten, Größen und extrahierte Bytes werden vollständig geprüft.

## Prüfungen und XEMU-Abnahme

Alle **19 automatischen Tests bestanden** (249,919 s). Erfolgreiche Assembly, zweite byteidentische Reproduktion aller generierten Dateien und vollständige D81-Prüfung. Einzelresultate: `releases/stage_6b1/test-results.txt`. Hostprüfungen führen den tatsächlichen assemblierten Code mit schmalen CPU/DMA/VIC/KERNAL-Modellen aus. Das ist kein XEMU-/Hardwaretest.

Unter XEMU ROM V920395, PAL, bitte prüfen:

1. Titelbild bleibt während der fünf SEQ-Ladevorgänge korrekt; danach erscheint das Menü mit 32 animierten Gegnern und Original-Cycling.
2. Joystick-/Cursor-Navigation, 001↔100 in beide Richtungen, nur ausgewählte Zeile rot, kontrolliertes Wiederholen, RETURN/Feuer, F1/F2/F3, Platzhalter-Rückkehr.
3. F1-Spielstart mit 001/002/003/099/100, korrekte HUD-Punktwerte/Paletten, Score 0, drei Leben; gehaltener Feuerknopf startet erst nach Freigabe und schießt nicht sofort.
4. HUD-Originalfont inklusive Ziffern, Hi-Score, Player 1/No P2, Form./Att.; acht Lebenssymbole in 4×2 ohne Überlappung.
5. Gegner-Cycling synchron, andere Levelpalettenfarben korrekt; Player, HUD, Explosionen und Schüsse konstant. Kein oberes RRB-/HUD-Flackern.
6. B2-Einflug, ATTACK/RETURN, ±8-Drift alle zwei Frames, Player 1 px/Frame, Schüsse/Kollisionen/Respawn/Unverwundbarkeit unverändert.
7. LEVEL CLEAR erst nach vollständigen Explosionen; neuer Buttondruck, 100→1, +/- begrenzt. GAME OVER nach letzter Explosion; R zurück zu Level1 mit erhaltenem Highscore.
8. X aus Menü/Platzhalter/Spiel: normaler BASIC-Cursor, DIRECTORY funktioniert, erneutes RUN zeigt Titel und Menü und startet wieder korrekt.

Stage 6b1 bleibt bis zur ausdrücklichen Benutzerbestätigung ein Testbuild.

## XEMU-Korrektur: CPU-Takt beim Titel-/Menüwechsel

Der Benutzer meldet nach dem ersten Build einen Abfall auf 3,5 MHz unmittelbar
nach dem Titelbildladen. Nachgewiesene Ursache: `t_show` schrieb `$05` nach
`$D054` und löschte damit **VFAST, `$D054.6`**. Das übernommene Menü setzte zwar
**FAST, `$D031.6`**, schrieb aber ebenfalls `$D054=$05`. FAST allein entspricht
3,5 MHz; die ursprünglichen Hosttests modellierten keinen effektiven CPU-Takt.
Belege: VIC-IV-Referenz/User Guide (VFAST) und XEMU
`targets/mega65/mega65.c`, `machine_set_speed()`.

Korrektur ausschließlich in Stage6b1: Titel und Menü verwenden `$D054=$45`
(VFAST plus unveränderte CHR16/FCLRHI-Grafikbits) und setzen FAST. Auch der
RRB-Spielstart einschließlich der nachfolgenden HUD-Initialisierung setzt beide Taktbits. Das ermöglicht vollen MEGA65-Takt
(nominell 40 MHz; XEMU-Default 40,5 MHz), unabhängig vom BASIC-Starttakt.
Die vorhandenen Register-Sicherungen restaurieren bei X/Fehlern die ursprünglichen
BASIC-Werte. Keine Änderung an Kurven, Animationsteilern, 50-Hz-Gates, Schüssen,
Grafikdaten oder Paletten. Der um zwei Bytes verschobene Titel-Restore-Einstieg
wird im Menü-Gate angepasst und vom Builder gegen das tatsächliche Assembler-
Symbol geprüft; PRG/D81 werden vollständig neu erstellt.

Neue Regression: tatsächliche Registerwrites während des Titels, im Menü und
Spiel bei langsamen/schnellen BASIC-Ausgangswerten; anschließend exakte
D031/D054-Restoration nach X. Eigener XEMU-Lauf weiterhin nicht behauptet.
Bitte den korrigierten Build zunächst auf konstanten vollen CPU-Takt während
Laden/Menü/Spiel sowie korrektes BASIC/erneutes RUN testen.
