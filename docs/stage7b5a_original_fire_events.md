# Stage7b5a — originale Schussereignisse (Issue #63)

Status: **Testbuild, nicht Stable. XEMU-Abnahme durch Benutzer ausstehend.**
Basis: getestete Stage7b4, Commit
`bd63682fa37df2853338b499f1210ec9dd2f56dc`.
Branch: `stage7b5a`. Keine Änderungen an früheren Sources/Releases/Tags,
`main` oder der parallelen Repository-Bereinigung.

## Verbindliche Quellen und Evidenz

Aus PR #62 wurden ausschließlich dessen neun Analyse-Dateien übernommen,
kein Merge eines Gameplay-Zweigs:
[68000-Analyse](amiga_enemy_fire_analysis.md),
[Vergleich mit Stage7b4](amiga_vs_stage7b4_fire_comparison.md),
[100 Originalparameter](../assets/amiga_enemy_fire_level_parameters.csv),
[Adress-/Opcodebelege](amiga_enemy_fire_evidence/68000-excerpts.txt).
Die Analysedateien bleiben gegenüber `dbaf0db` unverändert.

Im gelieferten Startscreen-Savestate gelten folgende belegte Adressen:

| Originaladresse | Bedeutung |
|---|---|
| `$C0AE8E–$C0AF84` | ENTRY-Auswahl, Untergrenze und zwei Counter |
| `$C0D22C–$C0D272` | ATTACK-Schwellenplanung |
| `$C0D3E2–$C0D514` | ENTRY-/ATTACK-Update und einmalige Auslösung |
| `$C0D612–$C0D6D6` | globaler Pool mit sechs Gegnerprojektilen |
| `$C0D764–$C0D77E`, `$C0EDF8–$C0EE24` | Original-Beam-RNG |

Adressangaben beziehen sich auf die analysierte BRAM-Abbildung, nicht auf
universelle Amiga-Adressen. Die Original-ADF, der ChipRAM-Dump und das
WinUAE-Savestate wurden in PR #62 statisch abgeglichen. In dieser Stage
wurde **kein WinUAE oder XEMU ausgeführt**; kein Original-Schüsse/min-Wert
und keine gemessene Gleichheit der Originalzeitbasis werden behauptet.

## Parameterdatei VYSH.DAT

Die bestehenden fünf DAT-Dateien bleiben bytegleich zu Stage7b4:
`VYLV.DAT`, `VYGR.DAT`, `VYCL.DAT`, `VYTI.DAT`, `VYMN.DAT`.
Die sechste SEQ-Datei `VYSH.DAT` umfasst **1.116 Bytes**: 16-Byte-Header,
anschließend 100 feste Records zu elf Bytes. Kein bestehendes Dateiformat
wird geändert. Multibytewerte sind Little Endian.

| Headeroffset | Inhalt |
|---|---|
| 0..3 | ASCII `VYSH` |
| 4 | Formatversion 1 |
| 5 | 100 Level |
| 6 | maximal vier Gruppen |
| 7 | Recordgröße 11 |
| 8..9 | vollständige Dateilänge 1116 |
| 10..11 | Sum16 des Payloads |
| 12..13 | Recordbeginn 16 |
| 14..15 | reserviert, null |

Record für Level `i`: Dateioffset `16 + (i−1)*11`.

| Recordoffset | Originalquelle / Bedeutung |
|---|---|
| 0 | `Level+$6C`: DY 1/2/3; **nur gespeichert** |
| 1 | `Level+$6E`: Ereignismode 1/2 |
| 2 | `Level+$70`: jeder N-te ENTRY-Gegner, N=1..4 |
| 3..10 | vier WORD-Untergrenzen aus `Level+$18+2*g`; unbenutzte null |

`tools/convert_stage7b5a_fire.py` extrahiert `Level`/`Debut` reproduzierbar
von der hashgeprüften Original-ADF, prüft deren OFS-Dateiketten und die
Werte gegen die belegte CSV. Für alle 248 Gruppen werden Länge,
Startkoordinaten, Gegnerzahl und **sämtliche gepackten Kurvenbytes** mit
VYLV verglichen. Für jede Gruppe gilt `0<=L<N`; mindestens ein zulässiger
Y-Punkt existiert. Die maximal benötigte private Bitmapbelegung wird
geprüft. Die Bitmaps werden nicht mitgeliefert, sondern zur Laufzeit aus
den tatsächlich geladenen VYLV-Kurven aufgebaut.

### Loader und Fehlerpfade

Nach VYCL wird VYSH über denselben getesteten SEQ-Pfad geladen:
`SETBNK($FF6B)` vor SETNAM, OPEN/CHKIN/CHRIN/READST,
anschließend CLRCHN/CLOSE. Chunk-DMA einschließlich Bytevergleich der
Rückkopie bleibt unverändert. Titelbild und dessen Palette bleiben sichtbar.

Prüfung: exakte Länge einschließlich EOI, buildgebundene Voll-Datei-Sum16,
exakter Header und **CRC-16/CCITT-FALSE jedes der 100 Records** gegen aus
den Originaldaten generierte, eingebettete Referenzen. Die CRC-Prüfung
erkennt auch einen veränderten Record mit unveränderter Sum16. Die festen
Offsets werden aus der geprüften Builddatei erzeugt; keine unkontrollierten
Dateizeiger werden ausgeführt. Fehlende/kurze Datei nutzt den bisherigen
I/O-Fehlerpfad; ungültiger Header, EOI oder Prüfsumme ergibt `Load Error $0A`.
Kanäle werden geschlossen und die Titel-/BASIC-Einstellungen restauriert.

Die Prüfung läuft erst bei geschlossenen Kanälen. Ein kurzer Gate unter
`$A000` maskiert IRQs und schaltet ausschließlich D030.ROMA für den neuen
RAM-Code aus. D030 und IRQ-Zustand werden vor Rückkehr exakt restauriert.
Keine KERNAL-Aufrufe bei veränderter ROM-Abbildung. D031/VFAST wird dabei
nicht verändert.

## ENTRY

Beim Levelstart werden beide WORD-Counter und Pending-Bits aller 22 Slots
auf null gesetzt. Ein 1-basierter Auswahlzähler läuft **über Gruppengrenzen**;
nur jeder N-te Gegner wird eingeplant. Pro gewähltem Gegner:

```text
t1 = L + random(N-L), wiederholen bis Original-Debut-Y[t1] <=148
counter1 = t1
counter2 = (t1+15) mod N, wenn Mode2; sonst0
```

Eine private Bitmaske pro Gruppe merkt das Ergebnis von `Y[t]<=148`.
Sie entsteht durch einmaliges Durchlaufen der Originalkurve ab dem
Original-Gruppenstart; Punkt0 ist bereits Start plus erstes Delta.
Das ist dieselbe Zulässigkeitsprüfung wie im Original, ohne wiederholte
Kurvenscans für jeden Gegner. Auch negative Original-Y sind zulässig.
Modulo berücksichtigt ebenfalls die Ein-Byte-Kurven einiger Sonderlevel.

Nur nach einem wirklich konsumierten ENTRY-Kurvenbyte wird ein aktiver
WORD-Counter dekrementiert. Der Wechsel auf0 markiert genau ein Ereignis;
0 ist danach inaktiv. WAIT_ENTRY, sichtbarer Startpunkt und zeitlich
übersprungene Kurvenupdates zählen nicht. Somit wird Y bei Index `t1`
geprüft, aber nach `t1` Updates bei Index **`t1−1`** geschossen.
`t1=0` deaktiviert das erste Ereignis ausdrücklich.

Bewusste Sicherheitsabweichung: Mode1 übernimmt **keinen alten zweiten
Counter** aus einem vorherigen Actor/Level. Dieser im Original nicht
vollständig geklärte Slotreuse-Pfad wird deterministisch genullt.

## Original-Y und sichtbare Position

ENTRY wird weiterhin als `visibleY=originalDebutY−16` dargestellt.
Die Planung/Bitmap benutzt ausschließlich Original-Debut-Y. Der Hook nach
dem Kurvenbyte verbraucht den Counter, markiert aber nur ein Pending-Bit.
Erst nach dem bestehenden B2-Postframe wird aus der jetzt sichtbaren
signed RRB-Position gespawnt. B2-Handoff und RETURN bleiben unverändert.

FORMATION speichert schon in Stage7b4 `engineY=originalFormationY−minY`.
`minY` ist `level.y_shift`, aus den originalen Formationsplätzen bestimmt.
ATTACK beginnt ausschließlich am erreichten Formationsplatz und addiert
unveränderte Originaldeltas. Deshalb gilt während ATTACK durchgehend:
`originalY=signed engineY+level.y_shift` (WORD-Arithmetik).
Dieselbe Rückabbildung gilt beim Planen und beim Schwellenvergleich.
Die ENTRY-Projektion −16 wird hierbei **nicht** ein zweites Mal angewendet.

## ATTACK

Jeder produktive `a_start` ersetzt die alten Counter durch neue Schwellen:

```text
T1 = originalY + random(168-originalY)
T2 = 0
Mode2: T2=T1+20; wenn T2>168, T2-=32
```

Nach jedem Original-Kurvenupdate werden beide nichtnull Schwellen unabhängig
geprüft. `originalY>=T` löscht T **vor** dem Spawnversuch. Beide dürfen im
selben Update feuern; T2 kann wegen der Originalkorrektur vor T1 liegen.
Negative Original-Y löst kein Ereignis aus. Die endliche Stage7b4-
Kurven-/RETURN-Logik wird nicht ersetzt. Die spätere vertikale
Ausflug-Fallbackphase und RETURN planen/erzeugen keine neuen Ereignisse.

Sicherheitsgrenze: ATTACK-Start mit Original-Y<0 oder >=168 plant null
Ereignisse. Insbesondere keine Modulo-0-Operation und kein erfundenes
Ersatzintervall. Die Datenprüfung und ein eigener Assembler-Lauf finden vier betroffene Plätze:
Level46, nullbasierte Actors9/20 mit Original-Y178 und Actors10/21 mit
Original-Y195. Diese Gegner dürfen unverändert angreifen, planen dabei
aber keine ATTACK-Schüsse. Das native Verhalten einer negativen
Modulusgrenze wird nicht als rekonstruiert behauptet. Alle übrigen
Formations-Y liegen im zulässigen Bereich; defensive Grenzen werden
zusätzlich getestet.

## Spawn, Pool, unveränderte Bewegung

Pending-Bits werden beim Bearbeiten immer gelöscht. Ein voller Pool lässt
das Ereignis verfallen, ohne Retry oder Cooldown. Zwei fällige Ereignisse
können zwei Slots belegen; bei einem freien Slot verfällt das zweite.
Globale Gegnerplätze2..7, Playerplätze0..1. **Keine Schützenquote**.
Die ursprüngliche Schützen-ID bleibt als Diagnoseinformation gespeichert;
Tod, Formation oder RETURN des Schützen beeinflussen existierende Schüsse nicht.

Die Stage7b4-Spawn-Sicherheitsgrenzen bleiben: sichtbarer Gegner,
Mündungs-X im Playfield und Mündungs-Y16..183; außerhalb davon verfällt
das Ereignis ebenfalls. Dies verhindert Wraparound durch die bestehenden
8-Bit-Projektilkoordinaten. Auch bei ungültiger Position keine Wiederholung.

Unverändert: Mündung `(visibleX+8, visibleY+16)`, gespeichertes Ziel
`(PlayerX+8,184)`, bisherige 8.8-X-Steigung einschließlich Begrenzung,
**DY=1 in allen Levels**, zwei Player-/sechs Gegner-Sprites, bestätigte
3×7-Grafiken (rote Spitze beim Player oben) und Hitboxen. Der importierte
DY-Wert ist im Monitor als `fireevents.dy_original` lesbar.
Globale Cooldown-/Wahrscheinlichkeitsentscheidungen gibt es im normalen
Pfad nicht mehr. Der historische, explizit mit T aktivierte isolierte
Angriffstest bleibt mit seinem alten Demopfad erhalten; auch dort keine
Schützenquote. Er ist nicht die produktive Originalkurven-Steuerung.

## Zufall und Angriffsauswahl

Die originale Raster-/Beam-Zufallsfolge ist nicht unverändert auf den
MEGA65 übertragbar. Ein eigener maximalperiodischer 16-Bit-LFSR
(Seed `$79B5`, Tap `$B400`) liefert die Ereignis-Modulowerte. Das ist eine
reproduzierbare Testzufallsquelle, keine Behauptung identischer Amiga-Ziehungen.
Bei den validierten Originalgrenzen erreicht die Ablehnungsschleife einen
zulässigen Punkt; es wird kein neues Zeitintervall erfunden.

Der neue Planer verändert **nicht** `shots.p_random_lo/hi`. Der bestehende
Angriffsplaner, sein Tick-RNG, die FORMATION-Kandidatenliste, sein
30-Frame-Timer einschließlich Rank-Rejection und die Grenze3 bleiben
unverändert; die zentralen Routinen werden auch byteweise verglichen.
Welche individuellen Gegner ausgewählt werden, kann sich gegenüber einem
alten Lauf unterscheiden: Die entfernte Schützenauswahl verbraucht keine
zusätzlichen Werte mehr aus dem vormals gemeinsam benutzten Zufallszustand.
Es gibt keinen neuen Angriffstimer, keine Amiga-Batches und keine neue
Kurvenauswahl.

## Speicher

| Bereich | Verwendung |
|---|---|
| `$70000–$7045B` | VYSH,1116 Bytes; außerhalb DOS/ROM/Titel/aller alten DATs |
| `$A600–$A6FF` | aktueller11-Byte-Record plus private Y-Zulässigkeitsbitmaps |
| `$A700…` | zwei WORD-Ereignisse je Actor,22 Pending-Bytes, eigener RNG/Scratch |
| `$A800…` | Ereigniscode, Validator, buildgebundene Offsets/Record-CRCs |
| `$895C…`, `$9D30…` | normaler Fire-Dispatch und ROM-sicherer Loader/Gate |

Exakte Grenzen: Zustand `$A700–$A78E`, Code/Tabellen `$A800–$AF04`;
zusätzlich Release `memory-map.txt` und `STAGE7B5A.sym`.
Die neue Belegung nutzt ausschließlich frühere **unbenutzte residente**
Type3–6-Kopien zwischen `$A580` und `$B47F`. Deren originale VYGR-Daten
bleiben vollständig erhalten. Type1/2 bis `$A57F` bleiben für alte
Initialisierung/Orbit-Routinen vorhanden. Produktive Pixies nutzen schon
Stage7b4s individuelle Bank1-Grafikpuffer; die deaktivierten stationären
Alt-Slots werden nicht reaktiviert. Kein Umbau des RRB-Renderers.
Sternencode ab `$B480`, Menü-Swap `$7000–$9FFF`, HUD-, DOS-, Titel-,
Paletten- und Projektilpuffer bleiben getrennt. Assemblerguards begrenzen
sämtliche neuen Segmente.

## Reproduzieren und prüfen

```sh
python tools/convert_stage7b5a_fire.py --output /tmp/vyper-fire
python tools/build_stage7b5a.py --kickass /path/to/KickAss.jar
PYTHONPATH=tests:tools:/path/to/py65 python -m unittest test_stage7b5a -v
PYTHONPATH=tests:tools:/path/to/py65 python tools/measure_stage7b5a_events.py
python tools/package_stage7b5a.py
```

KickAssembler5.25 (Hash im Buildskript), Java, Python3 und Pillow wie bei der
Baseline. py65/45GS02-Hostadapter wie in den vorhandenen Tests; Analyse-
Reproduktion separat mit `tools/analysis/requirements.txt` (Capstone5.0.7).
Der Build prüft unveränderte Baselines und alte DATs, assembliert Menü und
Engine und verifiziert sämtliche D81-Dateiketten. Keine Testinstrumentierung
wird in PRG/Spielcode eingebaut.

### Deterministische Messung:1200 Modellupdates pro Level

Unveränderte Originalkurven, alle Gegner bleiben am Leben. Tatsächlicher
Assembler für Bewegung, Angriffsplaner, Schussereignisse und Projektilablauf;
Renderer, Player-Schüsse/-Treffer und HUD werden für diese isolierte Messung
nicht ausgeführt. Ein Modellupdate ist keine gemessene Amiga-/XEMU-Zeit.

| Level | Mode / jeder N-te | ENTRY-Ereignisse | ATTACK-Ereignisse | Versuche bei gültiger Mündung | Spawns | Pool-Verfall | Maximum aktiv |
|---|---|---|---|---|---|---|---|
| 1 | 2 / 1 | 44 | 24 | 66 | 39 | 27 | 6 |
| 3 | 2 / 1 | 40 | 24 | 62 | 40 | 22 | 6 |
| 29 | 1 / 1 | 22 | 16 | 38 | 30 | 8 | 6 |
| 54 | 2 / 2 | 22 | 23 | 43 | 31 | 12 | 6 |

Zusätzlich verfallen wegen der unveränderten Positions-/Sichtbarkeitsgrenzen
2/2/0/2 Ereignisse in Level1/3/29/54. In allen vier Läufen maximal3 ATTACK.
Die vier Level46-Guardfälle wurden zusätzlich mit tatsächlichem `a_start`
geprüft: ATTACK beginnt, beide Schussereignisse bleiben0.
Die gezählten Angriffsstarts sind12/12/20/15; daraus wird keine Originalrate
abgeleitet. Rohdaten: `releases/stage_7b5a/event-measurements.json`.

Zwei unabhängige Builds liefern **56 bytegleiche Builddateien**, darunter
PRG, vollständiges819200-Byte-D81, alle sechs DATs, Sources und Symbole.
Die fünf alten DATs werden im Builder gegen Stage7b4 byteweise geprüft.

**59 automatische Regressionstests bestanden**, keine Fehler oder
Fehlschläge. Zusätzlich zwei gezielte Prüfungen der unabhängigen
Original-Y-Dekodierung für alle100 Level/248 Gruppen und der erweiterten
ATTACK-Grenzfälle bestanden. Protokolle: `test-report.json`,
`test-output.txt`, `independent-Y-test-output.txt` im Release.
Geprüft sind unter anderem Titel/Loader-Fehlerpfade, Mode/N-Auswahl,
WORD-Counter/Off-by-one, WAIT_ENTRY, gleichzeitige/verfallene Ereignisse,
Tod/RETURN/Neustarts, bytegleicher Angriffsplaner/Projektilkern, alle100
Paletten und Levelwechsel, Clipping/Transparenz, Sterne/Übergang, Menü,
Kollisionen/Explosionen/Respawn/GAME OVER und BASIC/erneutes RUN.
Hostmodelle sind keine reale VIC-IV-/XEMU-Abnahme.

## Noch vom Benutzer in XEMU zu testen

D81 mounten, `LOAD"STAGE7B5A",8`, `RUN`; Joystick **Port2**.
Level1,3,29,54 über INITIAL LEVEL/F1 vergleichen: weniger und phasenbezogene
Schüsse; höchstens sechs gleichzeitig, kein späterer Retry nach vollem Pool.
Kurven, Angriffe und Geschossflug müssen weiterhin wie Stage7b4 wirken.
Zusätzlich +/- einschließlich1/100, natürlicher100→1-Wechsel, GAME OVER/R,
LEVEL CLEAR/Übergang, Player/Joystick, Titel/Menü, HUD, Paletten/Cycling,
Explosionen und X→BASIC→DIRECTORY→RUN prüfen.

7b5b bleibt separat: originale DY-Geschwindigkeit, horizontale Streuung,
Originalmündung und Original-X-Neigungsbegrenzung. Ebenso bleiben
Original-Angriffstimer/Batches und die bisherigen Ein-Byte-Angriffskurven-
Sperren in25/50/99/100 außerhalb dieser Stage.
