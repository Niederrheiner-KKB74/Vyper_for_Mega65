# Original-Amiga-ATTACK: Kurvenende und Fortsetzung (Issue #77)

**Analyse, keine Implementierung.** Basis ist Stage9a Stable in `main`,
Merge `9bbe02ed9d284575c14c23954659a781d6889ee9`. Branch
`analysis-amiga-attack-end`. Keine Engine-/DAT-/PRG-/D81-Änderung, kein Build,
kein Merge oder Stable-Tag.

## Ergebnis und Evidenzgrad

**Bestätigt durch Originalcode und Originaldaten:** Die gepackte ATTACK-Kurve
wird **beim Levelaufbau zyklisch gelesen**. Der Originalcode erzeugt für jeden
Gegner einen eigenen expandierten XY-Puffer. Beim Ende der gepackten Bytes setzt
er **nur den Byteindex auf 0**, nicht die akkumulierten Koordinaten. Er erzeugt
weitere Punkte, bis das neue signed-WORD-Y mindestens **216 (`$D8`)** erreicht.
Dann **ersetzt** er das Y des letzten erzeugten Punktes durch **`$FFFF` = −1**.
Er hängt keinen zusätzlichen Punkt an.

Der ATTACK-Laufzeitcode wiederholt selbst **keinen** Pointer und verkettet keine
Deskriptoren. Er liest die vorbereitete Folge linear. Ein negatives Y beendet
State3 und setzt State2/Y0. Der endliche gepackte Record ist somit **kein
vollständiger einzelner Angriffsflug**.

**Bestätigt:** Stage9a interpretiert die gepackte Länge dagegen als Ende der
Flugfigur und geht danach auf vertikales DY2 über. Das erklärt den beobachteten
Fehler in Level4. Eine bloße Wiederholung derselben absoluten Positionen wäre
ebenfalls falsch: Beim Original werden alle Deltas über die Wiederholungsgrenze
hinweg weiter aufsummiert.

**Stark gestützt:** Dieser Unterschied erklärt die Benutzerbeobachtung im
Amiga-Vergleich. Die Kausalität der unterschiedlichen Bewegungsfolgen ist durch
Code und Simulation belegt; ein neuer WinUAE-Lauf wurde nicht durchgeführt.

**Hypothese für die spätere Portkorrektur:** zyklische Deltawiedergabe bis zum
bestehenden MEGA65-Austritt200 sollte die beobachtete Figurfortsetzung liefern.
Ihre visuelle Übereinstimmung bei unverändertem Formations-Y0 ist noch nicht
unter XEMU/WinUAE geprüft; sie ist keine belegte Original-Koordinatenregel.
Die native Regel216 selbst ist dagegen im Code bestätigt.

## Quellen, Adressen und Reproduktion

Vorhanden: die drei Originaldateien unter `assets/stage5b/original_sources/`.
Die gleichnamigen Chat-Anhänge existieren ebenfalls lokal; kein weiterer aktiver
Level4-Savestate wurde gefunden. Der vorhandene USS ist der Startbildschirm,
kein neu aufgezeichneter ATTACK-Trace. Fehlend ist ein aktueller Level4-Gameplay-
Savestate/Trace; für die statische Endregel werden keine Ersatzdaten benötigt.

SHA-256 der Originalcontainer:

| Datei | SHA-256 |
|---|---|
|VYPER.ADF|`b28cab911431aaf3e48fd3e9979159de7154f98538eeba191f52ac47ef9665e5`|
|Vyper_Memory_Dump.dat|`d74aea88fb4232e36caab80e51abc51f73d470a5b55a54f5cb010f1d910ddf8c`|
|Vyper_Startscreen.uss|`d836cbf88f0ac35b6ed3776df2add39f699113c1aeb9d02cdfe4651c82793916`|

Das Skript prüft die ausgewählten OFS-Dateiketten, HUNKs und RELOC32. Für **alle
hier untersuchten Codebereiche** stimmen die ADF-Instruktionen nach Relokation
mit beiden gespeicherten Codekopien überein. **Keine Gleichheit des gesamten
CODE-Hunks behauptet:** außerhalb dieser Bereiche gibt es 1033/1035 abweichende
Bytes. Capstone ist auf5.0.7/M68K_000 gepinnt.

Adresse in diesem USS = `$C08760 + CODE-Offset`; im ChipRAM-Dump =
`$21B20 + CODE-Offset`; Shot-Dateioffset = `$28 + CODE-Offset`.
[Alle Instruktionsbytes mit vier Adressbezügen und USS-Dateioffset](amiga_attack_end_evidence/68000-excerpts.txt),
[Hashes/Statistik](amiga_attack_end_evidence/analysis.json),
[Fälle](amiga_attack_end_evidence/cases.csv),
[Level4-Punktfolge](amiga_attack_end_evidence/level4_trace.csv).
Diese Laufzeitadressen gelten für die vorliegenden Abbilder, nicht jede WinUAE-Sitzung.
Zwei vollständige Analyseläufe lieferten alle fünf Evidenzdateien bytegleich.
1728 bestehende Stable-Dateien wurden dabei unverändert geprüft; es wurde kein
Spielbuild ausgeführt. CSV-Positionen sind logische Koordinaten, keine gerenderten
Bildschirmmessungen.

```sh
PYTHONPATH=/path/to/capstone-5.0.7 python3 tools/analysis/analyze_amiga_attack_end.py
# Unabhängige Wiederholung außerhalb des Repository:
PYTHONPATH=/path/to/capstone-5.0.7 python3 tools/analysis/analyze_amiga_attack_end.py --output /tmp/attack-end-repeat
```

Nur JSON/CSV/Text, kein Assembleraufruf. Bestehende src/assets/tools/releases der
Stable-Basis werden byteweise geprüft. Zeitangaben in CSV sind **Updateindizes**,
keine gemessenen50-Hz-Frames.

## Originalformat und Kontrollfluss

Die originale Datei `Level` enthält100 Records von `$72`=114 Bytes. Relevante Felder:

| Original-Levelrecord | Bedeutung / Beleg |
|---|---|
|`+$44`|Forme-Positionsblock; X/Y je Byte, danach Grafik- und Attack-Indices|
|`+$4E+4*c`|Attack-Dateioffset, beim Laden durch RAM-Pointer ersetzt|
|`+$5E+2*c`|gepackte Kurvenlänge als WORD|
|`+$66`|Kurvenanzahl|
|`+$68`|Pointer/Dateioffset auf gegnerspezifische Attack-Indexbytes|
|`+$70`|ENTRY-Schützenauswahl jedes N-ten Gegners, **kein Wiederholungszähler**|

Die Offsets sind **nicht** VYLV-Offsets. VYLV-Record und Original-Attack-Bytes sowie
alle2194 Gegnerindices/Positionen wurden unabhängig gegeneinander geprüft.
`$C0CB42–$C0CC6E` liest die Originaldateioffsets, lädt je die deklarierte Länge
in RAM und ersetzt die Offsetfelder durch Pointer. Die Kurven werden hier noch
nicht auf eine Zahl von Wiederholungen beschränkt.

Actorstride `$92`, Basis `A4+$3F0C`. Wichtige Actorfelder:

| Offset | Bedeutung |
|---|---|
|`+$10/+$12`|aktuelles X/Y (WORD)|
|`+$66/+$68`|Formations-X/Y; Y = Forme-Y +16|
|`+$6E`|State:1 ENTRY,2 RETURN/**auch ruhende Formation**,3 ATTACK,4 Explosion,0 tot|
|`+$70`|eigener expandierter Attack-Puffer (**nicht Level+$70**)|
|`+$74`|laufender Pointer darin|
|`+$78`|beim ATTACK-Start gespeichertes X|
|`+$7A/+$7C`|einmalige Schuss-Y-Schwellen|
|`+$88`|gegnergebundener Attack-Index|
|`+$14`, `+$54..+$60`|Grafikpointer/Animationspflege, unabhängig vom Kurvenbyteindex|

### 1. Puffer pro Gegner

`$C0A198–$C0A1C6` reserviert22 getrennte Puffer von `$578`=1400 Bytes und speichert
sie in Actor+$70; `$C0C4CC–$C0C4F6` gibt dieselben Größen frei. Vier Bytes pro
Punkt ergeben350 Punkte. Der Code prüft den vorherigen Ausgabewordindex auf700
am Schleifenkopf, bevor er ihn um2 erhöht. Diese Schutzprüfung käme bei einer
fehlenden Endbedingung **einen Punkt zu spät** (Index700 würde schon geschrieben).
Das Skript begrenzt konservativ auf die tatsächliche350-Punkte-Kapazität. Im
vorhandenen Datenbestand braucht kein Gegner mehr als298 Punkte; der späte Guard
wird nicht erreicht. Keine Sicherheit für veränderte/fremde Kurvendaten behauptet.

### 2. Expansion beim Levelstart

`$C0AFAC–$C0B1AA` läuft über die Gegner. Der Attack-Index kommt aus der originalen
Indexliste, die Kurvenbasis aus `Level+$4E+4*index`, Länge aus `+$5E+2*index`.
Lokale Variablen: `A5−$0C` = Ausgabewordindex (anfangs−2), `A5−$0A` =
Eingabebyteindex (anfangs−1). **Kein Timer und keine Actor-Wiederholungszahl.**

Kritische Instruktionen:

```asm
C0B03E 546DFFF4       ADDQ.W #2,-$0C(A5)
C0B042 526DFFF6       ADDQ.W #1,-$0A(A5)
C0B052 3028005E       MOVE.W $5E(A0),D0 ; A0 = Level + 2*Kurvenindex
C0B056 B06DFFF6       CMP.W  -$0A(A5),D0
C0B05A 6604           BNE    $C0B060
C0B05C 426DFFF6       CLR.W  -$0A(A5)   ; zyklischer Byteindex!
...
C0B12C D150           ADD.W D0,(A0)      ; X-Delta zum übernommenen Vorgänger
C0B164 D150           ADD.W D0,(A0)      ; Y-Delta zum übernommenen Vorgänger
C0B180 0C7100D81800   CMPI.W #216,(A1,D1.L)
C0B186 6D00FE8A       BLT    $C0B012     ; weiter expandieren
C0B1A4 33BCFFFF1800   MOVE.W #-1,(A1,D1.L) ; finales Y ersetzen
```

Erster Punkt: X=0, Y=Formations-Y, danach **sofort erstes Delta addieren**.
Es gibt keinen zusätzlichen unveränderten Startpunkt. Alle weiteren Punkte
übernehmen das vorherige XY und addieren die nächsten Deltas. Decoder
`$C0C3BC/$C0C3E6`: Nibbles sind Vorzeichen+Betrag, X aus Bit7/6..4, Y aus3/2..0.
`00` bedeutet Stillstand für diesen Punkt, nicht Kurvenende. Auch die sechs
Nullbytes am Ende der Level4-Kurve bleiben reguläre Punkte. Die kurzen Bytes
`01`, `06`, `07` sind entsprechend gültige Bewegungen, keine belegten Sonderopcodes.

Pseudocode, signed-WORD-Arithmetik:

```text
relativeX = 0; absoluteY = formationY; packed_index = 0
repeat:
    relativeX += decodeX(packed[packed_index])
    absoluteY += decodeY(packed[packed_index])
    emit(relativeX, absoluteY)
    packed_index = (packed_index + 1) modulo packed_length
until absoluteY >= 216
last_emitted_Y = -1
```

Es wird **dieselbe** Kurve wiederholt, kein Nachfolgerdeskriptor gelesen. Rechts-
/Linksvarianten stammen aus den expliziten Kurvenbytes (z.B. Level1/3 gespiegelt),
nicht aus einem erneuten Spiegelungsbit am Wrap. Level4 hat nur eine Kurve für
alle22 Gegner. Die X-Drift der Figur akkumuliert ebenfalls weiter.

### 3. Start und lineare Laufzeitwiedergabe

`$C0D22C`: State3; `$C0D232`: Actor+$70→+$74; `$C0D238`: aktuelles X→+$78.
Schussschwellen werden **einmal** geplant. Angriffssound wird bei `$C0D21E`
ausgelöst, nicht bei einer intern wiederholten Kurve.

Bei `$C0D4B2` wird der Cursor geladen. X = signed WORD(relativeX + anchorX).
Originales X-Limit: X<0→0, X>224→223, **X=224 bleibt224**. Diese kleine Asymmetrie
ist im BGT/Immediate-Code belegt. Das Clamping wirkt nur auf die Ausgabe, nicht
auf den vorab expandierten Akkumulator oder den Anker.

`$C0D4D6` liest Y. Y≥0: Position übernehmen, Cursor fortschreiben, Schussprüfungen
+$7A/+$7C ausführen. Verbrauchte Schwellen bleiben0, auch über Kurvenwiederholungen.
Es gibt hier **keinen Längenvergleich und keinen Pointer-Reset**.
Y<0: `$C0D4DC` setzt State2, `$C0D4E2` Y=0, Branch nachD558. Der terminale
Pointer wird nicht mehr zurückgespeichert, keine Schussprüfung für den Marker.
Das X dieses Markerpunktes wurde davor bereits berechnet.

**Damit ist die unmittelbare Laufzeit-Endbedingung jedes negative Y.** Der
Generator erzeugt den normalen Marker aus Y≥216. Eine natürliche negative
Zwischenposition würde ebenfalls beenden; bei allen2194 rekonstruierten Flügen
tritt vor dem künstlichen Marker keine negative Zwischenposition auf.

### 4. Rückkehr, Animation, Tod

State2 (`$C0D474–$C0D4A8`) bewegt X um±1 zum **aktuellen** Formations-X plus
Drift `A4+$2C12`, Y um±1 zum individuellen Ziel+$68. Sind beide erreicht,
bleibt der Actor State2 und wird beim nächsten erlaubten Angriff als Formation
erkannt (`$C0D1B0–$C0D1CC`). Kein eigener neuer State für ruhende Formation.

Animation (`$C0D2B0–$C0D2DE`) läuft vor der Bewegungs-Stateauswertung. Der
Generator/Bytewrap setzt Animationsframe, State, Schussplan oder Sound nicht
zurück. Treffer setzen State4 und deaktivieren die normale Animation beiD340/D3C2;
der State3-Zweig liest dann keine weiteren Attackpunkte. Mehrere Angreifer haben
unabhängige Puffer/Pointer. Die hier gefundene Wiederholung ist keine neue
Angriffsauswahl und darf deren Begrenzungen nicht neu starten.

## Level4 und weitere Fälle

Original-Attackoffset `$04FB`,43 Bytes; alle22 Gegner Index0:

```text
2222221200000000000000a2a2a2000000000000003333333300000000000000a3b3b3b300000000000000
```

Netto pro Durchlauf ΔX=+2, ΔY=+38. Keine geschlossene Figur an unverändertem Y.
Ausgangsdrift für folgende Beispiele ausdrücklich0, kein gemessener Emulatorlauf.

| Level4-Slot | Forme-Y+16 (Original) | Stage9a-Y (−min26) | Original erzeugte Punkte | Original nach Durchlauf1 | Port nach Durchlauf1 |
|---|---:|---:|---:|---|---|
|0|53|27|185|X42,Y91|X42,Y65|
|1|98|72|131|X42,Y136|X42,Y110|
|4|26|0|208|X69,Y64|X69,Y38|

Slot0: nach43 Punkten relativer X2/Y91, nach86 X4/Y129, nach129 X6/Y167,
nach172 X8/Y205. Der185. erzeugte Punkt hätte relativen X11/Y217; Y wird−1.
Das letzte nichtnegative Laufzeit-Y ist215. Update185 setzt stattdessen Y0/RETURN.
Stage9a ist schon ab Update44 vertikal unterwegs: X42/Y67 statt Original X44/Y93
(**verschiedene Y-Ursprünge beachten**). Die CSV enthält die vollständigen
Rechenfolgen für Slots0/1/4.

| Level | gepackte Längen | erzeugte Punkte pro Actor (min..max) | Actoren mit mehr als einem Durchlauf |
|---|---|---|---:|
|1|183/183|158..195|8/22|
|2|163/163/217|171..251|22/22|
|3|183/183|177..196|10/20|
|4|43|131..208|22/22|
|5|171/119|158..298|22/22|
|25/50|1/1|168..189|22/22 je Level|
|47|62/38/38/62|90..122|22/22|
|56|157/157/27/27|30..280|22/22|
|99|1/1/1/1|22..33|22/22|
|100|1|18..28|22/22|

Alle100 Level/2194 Actoren: **1429** benötigen mehr Punkte als ihre einmalige
gepackte Länge, maximal298 Punkte, alle unter der350-Punkte-Puffergrenze.
Bei anderen Actoren beendet der Marker die Kurve bereits **vor** dem ersten
gepackten Ende. Das ist ein zweiter Grund, nicht grundsätzlich die ganze erste
Kurve abzuspielen. Die bisher gesperrten Ein-Byte-Kurven der Level25/50/99/100 sind
unter dieser belegten Endlogik regulär auswertbar. Die Sperre wird hier nicht
geändert; andere eventuelle Besonderheiten dieser Level sind damit nicht untersucht.

## Koordinaten und offene Punkte

- Originalform: Forme-Y+16; Original-Generatorgrenze216. Das beweist nicht die
  gesamte sichtbare Amiga-Auflösung/Overscan und ist kein ENTRY-B2-Y−16.
- Stage9a zieht das **levelabhängige minimale Formations-Y** ab (Level4:26),
  Playfield0..199, unterer Austritt ab200. Player/Original-Paletten etc. bleiben
  Gegenstand der Stable-Engine. Diese Ursprünge dürfen nicht vermischt werden.
- Eine pixel- und zeitgenau gleiche Abbildung216→200 bei gleichzeitig unveränderter
  Formation-Y0 ist **nicht** für alle Level dieselbe konstante Verschiebung.
  Für den kleinen Korrekturvorschlag siehe den Vergleichsbericht.
- Native Aufruffrequenz/visuelle Dauer, konkreter WinUAE-Level4-Lauf und reale
  Clipping-/Schussdarstellung bleiben **offen**, nicht als Messwerte ausgegeben.

## Konkreter WinUAE-Nachweis für die spätere Abnahme

1. Original `/Vyper/Shot` starten, Level4 wählen. Codebasis mit Signatur/Relokation
   bestimmen; gespeicherte Adressen nicht blind in einer anderen Sitzung verwenden.
2. **CODE+`$284C` = C0AFAC** auf Actor-Expansion und
   **CODE+`$28F2` = C0B052** für die Wrapprüfung setzen. Actorordinal steht inD4,
   Byteindex in `W(A5−$0A)`, Ausgabewordindex in `W(A5−$0C)`.
3. Nach **CODE+`$2A44` = C0B1A4** beobachten: aktuelles Y wirdFFFF. Pufferbasis
   aus `L(A4+$3F0C + D4*$92 + $70)` lesen. Für Level4-Slot0:185 XY-Paare,
   letztes YFFFF; nur mit unveränderten Originaldateien/Slots/Levelwahl vergleichen.
4. Beim Angriff **CODE+`$4AD2` = C0D232** anhalten: A0=Actor, +74 erhält+70;
   +78=X-Anker; +88=Kurvenindex; +7A/+7C=geplante Schussschwellen notieren.
5. Bedingten Breakpoint **CODE+`$4D52` = C0D4B2** mit `A0==gewählter Actor`:
   A1/Actor+74, X/Y+10/+12, State+6E und Schwellen protokollieren.
   Der Pointer läuft bei Punkt43 **weiter**, er springt nicht zum Anfang.
6. Bei **CODE+`$4D7C` = C0D4DC** muss State3→2 folgen, Y0; danachD474/D48E
   Rückkehr zu aktuellen Driftzielen. Sound-/ProjektilroutineD612 darf nicht
   durch einen Kurvenwrap neu geplant werden. Bei späterem Treffer State4 prüfen.

Diese Anleitung ist ein geplanter Trace, **kein ausgeführter WinUAE-Test**.
