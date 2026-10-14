# Original-Amiga-Gegner-Schusslogik — Issue #61

**Nur Analyse**, Branch `analysis-amiga-enemy-fire`. Keine Engine-, DAT-,
Buildskript- oder Parameteränderung, kein neues PRG/D81, kein Merge/Stable.
Vergleichsbasis Stage7b4: `bd63682fa37df2853338b499f1210ec9dd2f56dc`.

## Ergebnis und Evidenzgrad

**Bestätigt aus Originalcode und Daten:** Das Original feuert an vorher
geplanten Ereignissen. ENTRY zählt individuelle Countdown-Werte herunter;
ATTACK löst beim Erreichen vorberechneter Y-Schwellen aus. Der Standardpfad
plant ein oder zwei Ereignisse je Flugphase, nicht beliebig viele zufällige
Schüsse nach einem fortlaufenden Cooldown. Ein voller Pool verbraucht das
Ereignis ohne Projektil und ohne Retry. Das globale Limit sechs ist belegt.

**Bestätigt:** In der nachgewiesenen Original-Schussroutine existiert keine
Besitzer-ID und keine Prüfung „zwei aktive Schüsse dieses Gegners“. Zwei
geplante Ereignisse sind keine individuelle Grenze gleichzeitig aktiver
Projektile. Stage7b4 hat diese zusätzliche Regel eingeführt.

**Bestätigt:** Die Original-Level-Words `+$6C`, `+$6E`, `+$70` bedeuten
Projektil-Y-Geschwindigkeit, Ein-/Zwei-Ereignis-Modus und ENTRY-Auswahl jedes
N-ten Gegners. Insbesondere `+$70` ist im belegten Zugriff **kein**
Angriffskurven-Wiederholungsparameter. Die frühere Vermutung ist damit für
diesen Pfad widerlegt, ohne die historische Analyse zu überschreiben.

**Stark gestützt:** Eine rastergebundene Update-Zeitbasis, typischerweise PAL-
Frames. **Offen:** Exakte Updates pro Video-Frame/50-Hz-Sekunde unter allen
Lasten. Keine eigene WinUAE-Ausführung oder Original-Schussratenmessung.
Die synchronisierende Byte-Abfrage lässt auch Rasterzeile 256 zu; siehe unten.

**Hypothese zur Schwierigkeit:** Wiederholte MEGA65-Schussversuche innerhalb
derselben Phase sind wahrscheinlich ein wesentlicher Grund für die höhere
Schussdichte. Der Mechanismusunterschied ist belegt, sein Anteil gegenüber
Angriffstiming und fehlender Zielstreuung wurde noch nicht empirisch gemessen.

**Offen:** Eine mögliche alte zweite ENTRY-Countdown-Zahl bei Wiederverwendung
von Gegner-Slots in einem Ein-Ereignis-Level; der ausgewählte Mode-1-ENTRY-
Initialisierungspfad löscht diese Zahl nicht ausdrücklich. Die normalen
ATTACK-Mode-1- und nicht ausgewählten ENTRY-Pfade löschen sie dagegen.

## Vorhandene Quellen und Checksummen

Alle drei Dateien sind tatsächlich lokal unter `assets/stage5b/original_sources/`
vorhanden und wurden gelesen. Die Issue-Namen mit `(1)` liegen nicht als
zusätzliche Varianten vor. Nur **ein** USS-Savestate ist vorhanden.

| Datei | Bytes | SHA256 |
|---|---:|---|
| VYPER.ADF | 901120 | `b28cab911431aaf3e48fd3e9979159de7154f98538eeba191f52ac47ef9665e5` |
| Vyper_Memory_Dump.dat | 524288 | `d74aea88fb4232e36caab80e51abc51f73d470a5b55a54f5cb010f1d910ddf8c` |
| Vyper_Startscreen.uss | 1076832 | `d836cbf88f0ac35b6ed3776df2add39f699113c1aeb9d02cdfe4651c82793916` |

Weitere Chunk- und Dateiprüfsummen: [evidence.json](amiga_enemy_fire_evidence/evidence.json).

Die OFS-Dateiketten der verwendeten Dateien wurden einschließlich Blockchecksummen,
Sequenznummern und Größen geprüft. `s/startup-sequence` enthält `shot`;
Amiga-Dateinamen sind nicht case-sensitive. Die relevante reguläre Datei
`/Vyper/Shot` ist 81432 Bytes groß, Headerblock 881, SHA256
`d640f751f867ddea9a864ace56032a281d9c0199dd835e40b305a826aa664b58`.
`/Vyper/vyper` und `/Vyper/a` sind andere Dateien und werden **nicht** mit Shot
als identisch bezeichnet. Keine Entpackung von `a` wird behauptet.

Aus der ADF: `Wave/Level` 11400 Bytes, 100 Records à 114 Bytes, SHA256
`6349b34fc36469cb3072a0735b881002b47b37ff3af4456ea8c55403f553647f`;
`Debut` 46422, `Attack` 18223, `Forme` 8776, `Color` 362 Bytes.
Die vorhandenen `assets/stage5b/amiga_*.bin` stimmen mit diesen OFS-Inhalten
überein. Die Analyse liest die Originaldateien erneut direkt aus der ADF.

## Codeadressierung und dreifacher Nachweis

Shot enthält drei HUNKS: CODE 37924 Bytes (Dateioffset `$28`, 298 RELOC32),
DATA 41908 Bytes (Allokation 62380, Datei `$9918`, 73 RELOC32), BSS 4 Bytes.
Die sechsfach begrenzte Spawn-Routine wird über die eindeutige Bytefolge
`2F0A 0C6C 0006 2C1C 6700 00B6` lokalisiert.

| Bezug | CODE-Basis | DATA-Basis | A4-Globalbasis |
|---|---:|---:|---:|
| Startscreen USS | `$C08760` in BRAM | `$18140` in CRAM | `$2013E` |
| separater ChipRAM-Dump | `$21B20` | `$2AF50` | `$32F4E` (= DATA + `$7FFE`) |

Alle 119 CODE→CODE- und 179 CODE→DATA-Relokationen liefern je Quelle dieselbe
Basis. Alle **25 ausgewählten Abschnitte mit 821 Instruktionen** stimmen nach
RELOC32-Anwendung bytegenau mit dem ADF-Code überein, sowohl im Dump als auch
im USS-BRAM. Der gesamte CODE-Hunk ist ausdrücklich nicht als unverändert
behauptet: außerhalb dieser Abschnitte unterscheiden sich 1033/1035 Bytes
vom relokierten ADF-Abbild. Diese Differenzen sind für die vorgelegten
Routinen nicht vorhanden; ihre übrigen Ursachen wurden nicht vollständig untersucht.

USS-CRAM beginnt bei Datei `$DFC`, USS-BRAM bei Datei `$80E0C` und wird auf
`$C00000` abgebildet. Für jede Instruktion führt der
[annotierte Auszug](amiga_enemy_fire_evidence/68000-excerpts.txt) an:
USS-Adresse / Dump-Adresse (= Dump-Dateioffset) / CODE-Offset / Shot-Dateioffset.
Das JSON enthält zusätzlich den tatsächlichen USS-Dateioffset und die Bytes.
**Shot-Dateioffsets sind Offsets innerhalb der extrahierten OFS-Datei**, keine
naiven zusammenhängenden ADF-Offsets; die fragmentierte Blockkette steht im JSON.

Das USS-CPU-Format speichert D0–D7/A0–A6 (15 Register), dann PC. A4 steht bei
Payload +56, PC bei +68; der gespeicherte PC ist `$C0BF0C`, die Menü-Raster-
Warteschleife. Referenz: [WinUAE save_cpu](https://github.com/tonioni/WinUAE/blob/7b890b564983e111930612c87dea2c1c9bd63115/newcpu.cpp).
Die Actorzahl und Schusszahl sind in beiden vorhandenen Abbild-Kontexten null.
Die Abbilder sind deshalb **keine aktive Gameplay-Ereignisspur**.

## Zustände, Daten und Routinen

Originalgegner: Basis A4+`$3F0C`, Stride `$92` (146 Bytes).
Die Originalzustände stehen bei Actor+`$6E`:
0 inaktiv/tot; 1 ENTRY einschließlich Startwartezeit; 2 Rückkehr/Formation;
3 ATTACK; 4 Explosion. State 2 wird erst durch exakt erreichte X/Y-Ziele als
startfähige Formation akzeptiert. MEGA65-Statewerte nicht damit verwechseln.

| Feld | Verwendung |
|---|---|
| Actor +`$10/$12` | aktuelles X/Y |
| +`$62` / +`$6A` / +`$6C` | ENTRY-Punktzeiger, verbleibende Punkte, Startwartezeit |
| +`$66/$68` | individuelles Formationsziel |
| +`$70/$74/$78` | Angriffskurve, aktueller Zeiger, Start-X |
| +`$7A/$7C` | ENTRY-Countdowns **oder** ATTACK-Y-Schwellen, zustandsabhängig |
| A4+`$2C16` | Schussereignis-Modus aus Level +`$6E` |
| A4+`$2C1C` | Anzahl aktiver Gegnerprojektile |
| A4+`$2BBE` | 16-Bit-Zufallsakkumulator |
| A4+`$31DA` | erstes von sechs Gegnerprojektilen, Stride `$16` |

Beispiel feste Quelladressen: USS Schusszahl `$22D5A`, Dump `$35B6A`;
USS Projektilbasis `$23318`, Dump `$36128`; USS Actorbasis `$2404A`, Dump `$36E5A`.
Nur für diese Abbilder, nicht für beliebige Neuallokationen.

| Funktion | USS | Dump | CODE-Offset |
|---|---:|---:|---:|
| Level-Initialisierung | `$C0A2EA` | `$236AA` | `$1B8A` |
| ENTRY-Schussplanung | `$C0AE8E` | `$2424E` | `$272E` |
| Gegner-/Player-Update | `$C0D08C` | `$2644C` | `$492C` |
| ENTRY-Schussaufrufe | `$C0D452`, `$C0D466` | `$26812`, `$26826` | `$4CF2`, `$4D06` |
| ATTACK-Schussaufrufe | `$C0D4FC`, `$C0D510` | `$268BC`, `$268D0` | `$4D9C`, `$4DB0` |
| sechs Projektile weiterbewegen | `$C0D5C8` | `$26988` | `$4E68` |
| Gegnerprojektil erzeugen | `$C0D612` | `$269D2` | `$4EB2` |
| Zufallsroutine für Registerargument | `$C0D764` | `$26B24` | `$5004` |
| Zufallsroutine für Stackargument | `$C0EDF8` | `$281B8` | `$6698` |

## ENTRY: vorbereitete Countdown-Ereignisse

Die Levelinitialisierung bildet den Recordzeiger als `LevelBase + index*$72`
bei `$C0A2F2–$C0A2FC`. Einflugkurven werden in XY-Words expandiert; alle acht
Bits des Bewegungsbytes werden durch die beiden signierten Nibble-Decoder
bei `$C0C3BC/$C0C3E6` verwendet. Die Standard-Decoder enthalten keine
Schussmarker-Abfrage. Es existiert kein zusätzliches Schussflag in diesen
expandierten vier-Byte-XY-Punkten.

`$C0AE8E–$C0AF84` führt einen laufenden Auswahlzähler über die Gruppen hinweg.
Jeder `Level+$70`-te Gegner bekommt neue Ereignisse; die anderen erhalten
`counter1=counter2=0`. Der Zähler wird vor allen Gruppen einmal genullt.

Für einen ausgewählten Gegner mit Kurvenlänge N und Untergrenze L:

```text
L = Level[$18 + 2*group]; falls L>N, wird L auf 0 gesetzt
repeat:
    t1 = L + random(N-L)
until expanded_curve[t1].Y <= 148
counter1 = t1
wenn mode==2: counter2 = (t1+15) mod N
```

Die Nutzung von L, die Prüfung bei `$C0AD54` und die spätere Zufallswahl sind
belegt. Der Reset bei `$C0ADC0` liegt ausschließlich im Fehlerzweig L>N
(nach Fehlermeldung und Tastaturwartepfad). Bei L<=N überspringt der Branch
`$C0AD5C` diesen Zweig und erhält die originale Untergrenze. Bei L=N wäre
der Zufallsdivisor null; auch dieser Randfall darf nicht stillschweigend
als gültige Schussplanung umgedeutet werden. Die100 Originalrecords enthalten
keinen solchen Null-Divisor: alle Untergrenzen sind kleiner als die zugehörige
Länge; für jede Gruppe existiert mindestens ein zulässiger Punkt.74 Levels
verwenden mindestens eine positive Untergrenze, Level1 beide Male60. Die
entsprechenden Längen-/Y-Prüfungen stehen im JSON unter `entry_point_audit`.
Mode 1 setzt im ausgewählten ENTRY-Pfad nur counter1; counter2 wird dort
**nicht ausdrücklich gelöscht**. Für frischen Nullzustand ist er 0, bei Slot-
Wiederverwendung ist ein möglicher Altwert gesondert zu prüfen. Die CSV zählt
neu geplante Ereignisse, nicht garantierte Gesamtaufrufe einschließlich Altwerten.

Im State-1-Update `$C0D3E2–$C0D46A` gilt:

1. Solange Startwartezeit +`$6C` positiv bleibt: keine Bewegung/Schusszählung.
2. Nächstes XY-Paar lesen, Punktzeiger +4, Länge -1; bei Ende State 2 setzen.
3. Jeden nichtnull Schusscounter dekrementieren. Nur beim Übergang auf 0
   `$C0D612` aufrufen. Danach bleibt er 0: kein Cooldown-Reset, kein Retry.

`t1=0` löst keinen ersten Schuss aus. Die Y-Zulässigkeit wird bei der Planung
am Punkt **Index t1** geprüft; der Countdown t1 erreicht nach t1 Updates 0,
also nach dem Lesen von **Index t1−1**. Diese Code-Reihenfolge nicht durch
ungeprüfte „Korrektur“ glätten. Eine Mode-2-Zahl 0 ist ebenfalls deaktiviert.
Die zweite Zahl läuft unabhängig; mit Modulo kann ihr Ereignis früher liegen.

## ATTACK: einmaliges Erreichen von Y-Schwellen

Beim Start eines Angriffs (`$C0D22C–$C0D272`):

```text
threshold1 = currentY + random(168-currentY)
threshold2 = 0
wenn mode==2:
    threshold2 = threshold1+20
    wenn threshold2>168: threshold2 -= 32
```

Bei jedem State-3-Kurvenpunkt (`$C0D4AC–$C0D514`):

```text
wenn die neue Kurven-Y negativ ist: State 2; Y=0; keine Schussprüfung
sonst:
    für threshold1 und threshold2 unabhängig:
        wenn threshold != 0 und currentY >= threshold:
            threshold = 0
            versuche Gegnerprojektil zu erzeugen
```

Damit maximal zwei **neu vorbereitete** Versuche pro Angriff, bei Mode 1
maximal einer. Kein Zufallswurf pro Attack-Frame. Bei einer großen Y-Bewegung
können beide Schwellen im selben Update auslösen; bei `t1>148` liegt die
korrigierte zweite Schwelle vor der ersten. Ein nicht erreichter Punkt oder
vorheriger Tod kann ein Ereignis verhindern. RETURN/Formation (State 2) und
Explosion (State 4) rufen diese Schussroutine nicht auf.

## Spawn, Limits, Lebensdauer und Zufall

Die vier aufgeführten direkten JSR-Aufrufer sind alle in CODE nachgewiesenen
aligned absoluten/PC-relativen Aufrufer des Gegnerspawns. Bei `$C0D612`:

```asm
2F0A                  move.l a2,-(sp)
0C6C00062C1C          cmpi.w #6,$2C1C(a4)
670000B6              beq $C0D6D2      ; Rückkehr ohne Projektil
```

Danach: Schusszähler +1, erster freier Eintrag in sechs Stride-`$16`-Records,
Active-Word +`$04`=1, X=`enemyX+7`, Y=`enemyY−7`. Player-X wird einmal beim
Spawn gelesen und mit einem Streuwert 0–19 nach rechts (ungerades Update)
oder links (gerades Update) versetzt. Es gibt keine fortlaufende Zielverfolgung.
Der 16.16-X-Schritt wird aus Abstand/vertikaler Reststrecke und DY bestimmt;
bei `abs(dx)>=dy` wird der X-Schritt auf DY begrenzt (höchstens 45°).

Record-Layout: X/Y +0/+2, Active +4, Grafikpointer +6, Höhe +`$0A`,
X-Festkommaschritt +`$0C`, Fraction +`$10`, DY +`$12`, X-Vorzeichen +`$14`.
**Kein Schützenindex und kein Schützenpointer.** Die Routine durchsucht auch
keine anderen Projektile nach ihrem Besitzer. Das Original benutzt Hardware-
SPR2–SPR7 für diese sechs Records. SPR0/SPR1 sind das angehängte Player-Sprite-
Paar, nicht zwei Hardware-Playerprojektile. Die separat begrenzten zwei
Player-Schüsse sind BOB-Objekte mit Stride `$92`: `$C0D0C0` prüft Anzahl 2,
`$C0D13C/$C0D15E` bewegen sie um −4.

Die Standardbewegung `$C0D5C8` arbeitet unabhängig vom Actorzustand über alle
sechs Records. Y += DY; bei Y>=200 Active=0 und globaler Zähler -1, andernfalls
X-Fraction weiterführen. Der Tod/RETURN eines Schützen entfernt seine
vorherigen Schüsse nicht. Die genaue Behandlung aller Player-Tod-/Hardware-
Kollisions-/Sonderresetpfade ist **nicht** vollständig rekonstruiert; aus
Offscreen-Freigabe wird keine unbelegte allgemeine Kollisionsfreigabe abgeleitet.

Der Grenztest lautet exakt **BEQ 6**, nicht BGE; er setzt die normalen
Zähler-/Slot-Invarianten voraus. Aufrufer haben ihren Countdown/Schwellenwert
bereits auf 0 gebracht. Volle sechs Slots => verlorenes Ereignis, keine
Wiederholung. Der Spawn steigt dann aus, **bevor** er den Zielstreu-RNG aufruft.
Keine individuelle Cooldownzahl wird zurückgesetzt. Bei Erfolg wird RNG
für die Zielstreuung benutzt; die weitere Zufallsfolge hängt deshalb auch
von vollen Slots und weiteren Original-RNG-Aufrufen ab.

Beide Zufallsroutinen verwenden denselben Akkumulator:

```text
seed = (seed + WORD[$DFF006]) & $FFFF
random(n) = seed % n
```

`$DFF006` ist VHPOSR, also Beam-/Horizontal-/Vertikalzustand, kein LFSR.
Registervariante `$C0D764`: Divisor D4, Ergebnis D2. Stackvariante `$C0EDF8`:
WORD-Argument, Ergebnis D0. Eine exakte Folge ist ohne Beam-/CPU-Zeitkontext
nicht aus einem festen Seed alleine reproduzierbar.

## Angriffsauswahl und Zeitbasis — getrennt von Schussabgabe

`$C0D08C` wird im aktiven Hauptpfad genau einmal bei `$C0971E` aufgerufen;
danach folgen Projektilbewegung `$C09722` und Playersteuerung `$C09726`.
Der Updatecounter A4+`$2C1A` wird zu Beginn erhöht. Bewegung/ENTRY-Schusszähler
und ATTACK-Y-Schussprüfung laufen pro Update. Nur die **Auswahl neuer Angriffe**
und der Player-Fire-Eingang werden über sein ungerades Bit getaktet.

Bei ungeradem Counter und freiem Player-Schutz-/Respawn-Gate A4+`$2C4E` wird
der globale **Angriffstimer** A4+`$2C1E` dekrementiert. Ablauf startet eine
Auswahl von vollständig in Formation angekommenen State-2-Gegnern. RNG wählt
einen Startindex, anschließend scannt der Code über die ursprünglichen Slots,
mit Wraparound und begrenzter Anzahl Prüfungen. Ein Batch verwendet dieselbe
Attack-Kurven-ID (+`$88`) und hat 1–4 Kandidaten nach `$C0D846`.
Das ist weder eine zufällige Schützenwahl je Frame noch der Stage7b4-30-Frame-
Timer. Der belegte Startpfad enthält keine globale „maximal drei ATTACK“-
Prüfung; ein 1–4-Batch ist aber auch keine bewiesene globale Gleichzeitigkeitsgrenze.

`$C0D846` setzt `attack_timer=base + random(range)` und die Batchgröße nach
weiteren Zufallsschwellen. Die Basis/Range stammt aus Level-/Zehnergruppen-
Tabellen, nicht aus den drei Schuss-Words +6C/+6E/+70.
Der normale Tabellenindex ist `min(floor(level_counter/10),9)`:

- Basis: `[30,30,30,30,30,30,30,30,10,5]`.
- Zufallsspanne: `[80,70,65,60,55,40,35,34,33,32]`.
- Drei Batchschwellen je Index stehen zusätzlich im JSON. Beispielsweise
  Index0 `[64,88,126]`, verglichen mit `random(128)` über inklusive Grenzen,
  wählt 1/2/3/4 Starts; der vierte Fall ist möglich.

Diese Konstanten liegen bei DATA+`$18C/$1A0/$1B4`; ihre Bytes wurden auch in
beiden Speicherabbildern gegengeprüft. Der Sonderzweig `(level_counter+1)%25==0`
setzt die Basis auf1 und die drei Schwellen auf128, schreibt die Spanne aber
nicht neu. Deshalb darf man daraus ohne weiteren Kontext keine reine statische
100-Level-Angriffstimer-Tabelle ableiten. Bei normalem Index0 sind es30–109
**ungerade Update-Ticks**; unter der noch zu messenden Annahme50 Updates/s
wären das1,2–4,36 Sekunden zwischen Auswahlbatches. Das sind keine gemessenen
Originalzeiten und kein Projektil-Cooldown. Diese Angriffstabellen
wurden für diesen Auftrag nicht als vollständige neue 100-Level-Angriffs-
Konfiguration ausgegeben. Angriffstimer und Schussereignisse getrennt behandeln.

Die Hauptschleife synchronisiert bei `$C09454` mit `TST.B $DFF006` auf einen
Nullwert der unteren acht VPOS-Bits. Das passt bei PAL sowohl zu Zeile 0 als
auch 256; der neunte VPOS-Bit wird hier nicht geprüft. Blitter-/CPU-Laufzeit
und Schleifenkontext bestimmen, welche Rasterphase tatsächlich erreicht wird.
**Exakt ein Update pro 50-Hz-Frame ist damit nicht alleine bewiesen.** Die
mechanischen Counter-/Y-Regeln sind trotzdem exakt pro Engineupdate belegt.
Für Umrechnung in Millisekunden benötigt man die unten vorgeschlagene Spur.

## 100-Level-Parameter und Grenzen

Die [CSV für alle 100 Levels](../assets/amiga_enemy_fire_level_parameters.csv)
enthält Original-Recordoffset, Gruppen-/Gegnerzahl, Kurvenlängen, Untergrenzen, drei belegte
Schussparameter, Einflugabstand und eine **Obergrenze neu geplanter** ENTRY-
Ereignisse: `floor(enemy_count / every_nth) * mode`. Das sind weder gemessene
Schüsse noch ein Besitzlimit; Nullcounter, Y-Prüfung, Tod und volle Slots können
Ereignisse verhindern. Mode-1-Altwertfrage ist gesondert zu beachten.

| Original-Word | Verwendung mit Codebeleg | Verteilung 100 Levels |
|---|---|---|
| +`$6C` | `$C0B216` schreibt DY in alle acht Sprite-Records; `$C0D5D6` nutzt es für Gegner-Y | 1:19, 2:80, 3:1 |
| +`$6E` | `$C0A758` nach A4+2C16; `$C0AF22/$C0D252` wählen zweites Ereignis | 1:34, 2:66 |
| +`$70` | `$C0AE92` verglichen mit laufendem Gegnerzähler, danach Reset | 1:78, 2:19, 3:1, 4:2 |

Level 1/2/3: DY=1, Modus=2, jeder Gegner gewählt. Level 29/37: DY=2,
Modus=1, jeder gewählt. Level54: DY=2, Modus=2, jeder zweite. Level100:
DY=3, Modus=2, jeder gewählt. Diese Aussagen kommen aus tatsächlichen Original-
Records, nicht aus der Größenordnung der Zahlen oder einem Screenshot.

## Reproduktion und zusätzliche WinUAE-Prüfung

```sh
python -m pip install -r tools/analysis/requirements.txt
python tools/analysis/analyze_amiga_enemy_fire.py --output /tmp/amiga-fire-evidence
```

Capstone 5.0.7, MC68000-Modus; OFS/HUNK/USS-Parsing sonst Standardbibliothek.
Das Skript liest nur Eingaben, verlangt Original-Hashes, überprüft alle
relevanten Relokationen/Instruktionsbytes und schreibt nur Analyse-JSON,
Text und CSV. Die drei Ausgaben wurden aus einem unabhängigen Zielverzeichnis
bytegleich reproduziert. Keine vollständigen neuen Originalbinärdateien werden
publiziert. Der Parser bearbeitet bewusst nur die ausgewählten regulären OFS-
Dateien; er behauptet keine Prüfung aller anderen Disketteninhalte.

Für eine spätere Zeit-/Randfallprüfung werden zusätzliche aktive Gameplay-
Savestates benötigt, vorzugsweise Level1 ENTRY, Level1 ATTACK, Level29 Mode1,
und ein Übergang von Mode2→Mode1 nach frühem Gegnertod. Keine Datei ist für
die hier vorgelegte statische Hauptrekonstruktion nachzureichen.

WinUAE-Messplan ohne Änderung am Originalcode:

1. Aus passendem geladenem Zustand die aktuelle CODE-/A4-Basis über die
   Signatur/Relokationen bestimmen. Angegebene C0-Adressen gelten nur für
   dieses USS; andere Allokationen über die CODE-Offsets umrechnen.
2. Pro Video-Frame Engineaufrufe (CODE+492C) protokollieren: Frame/Raster-VPOS
   einschließlich neunten Bits, Counter, Player-Gate, Actorstatus und X/Y.
   So wird 50 Hz gegen Mehrfach-/übersprungene Updates nachgewiesen.
3. An den vier Schussaufrufen und Spawn-Eingang CODE+4EB2 je Versuch loggen:
   Actor-ID `(A0-A4-$3F0C)/$92`, Phase, Counter/Schwellenwert, globale Schusszahl.
   Bei Spawn-Erfolg ab CODE+4F08 (= `$C0D668`) zusätzlich Slot
   `(A1-A4-$31DA)/$16`, X/Y, DY und X-Schritt protokollieren.
4. Versuche, erfolgreiche Spawns und gleichzeitig aktive Slots getrennt
   zählen; Zuordnung nur im **externen Protokoll** weiterführen. Tod und
   Rückkehr ändern die ursprüngliche Schützen-ID dieses Protokolls nicht.
5. 22/10/5/2/1 überlebende Gegner und volle sechs Slots vergleichen; gerade
   den bereits konsumierten Versuch bei voller Kapazität prüfen. Kein
   erfundener Originalwert „Schüsse pro Minute“ aus einem Menü-Savestate.
6. Entry-Modus1 nach Mode2-Slotreuse auf alte +7C-Werte prüfen. Bei Unsicherheit
   auch Player-Tod/Reset- und Hardwarekollisionspfade separat loggen.

Priorisierte, **nicht implementierte** Empfehlungen stehen in
[Original vs Stage7b4](amiga_vs_stage7b4_fire_comparison.md).
