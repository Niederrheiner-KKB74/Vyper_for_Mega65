# Stage8a2 – zwei PCM-Quellen, Stereo und Attic-Streaming

Issue #71; eigenständiger Test, **kein Stable und keine Spielintegration**.
Basis ist der vom Benutzer in XEMU bestätigte Stage8a1-Programmcommit
`b56ae48b3bac92d40885ef78530a72eb882df16b` (PR #70).
Stage7b5b, Stage8a1, deren Quellen/Buildwerkzeuge/Assets und Releases bleiben
bytegleich. Der Builder prüft sämtliche bereits in dieser Basis vorhandenen
Dateien unter `src`, `assets`, `tools` und `releases` gegen Git.

## Start und Bedienung

D81 in XEMU einlegen, PAL und BASIC **80×25**, Laufwerk8 bzw. aktuelles
KERNAL-Laufwerk; `LOAD "STAGE8A2",8`, anschließend `RUN`.
Die erste Meldung bleibt während des SEQ-Ladens stehen. Erst nach vollständiger
CRC- und Attic-Rückleseprüfung erscheint die Testbedienung.

| Taste | Funktion |
|---|---|
| TAB | Quelle A/B auswählen, Markierung `*` |
| N / V | nächstes / vorheriges der20 gültigen Samples, zyklisch |
| A / B | normales Ereignis für Quelle A/B |
| SPACE | normales Ereignis für beide Quellen |
| Joystick Port2 Feuer | normales Ereignis für die ausgewählte Quelle, erst nach Loslassen erneut |
| J / K / L | ausgewählte Quelle auf X=0 /120 /240; auch bei laufendem Klang |
| T | ausgewählte Quelle sofort unterbrechen und neu starten, Busy übergehen |
| S | beide Quellen stoppen, Pending löschen |
| P | Pausefreigabe umschalten, laufende Wiedergabe dabei stoppen |
| G | synthetische CPU-/DMA-Grafiklast ein/aus |
| X | Audio stoppen, Zustand restaurieren, BASIC |

A startet mit ID17, B mit ID19, beide in der Mitte. N/V überspringt die unbenutzten
IDs4/13/14/23. P ist eine **Stop-Pause**, kein samplegenaues Fortsetzen; danach neu
auslösen. Normale Ereignisse können wegen Busy bewusst abgewiesen werden; T ist
der definierte Test der erzwungenen Unterbrechung. Tastatur-Autorepeat erzeugt
weitere Tastaturereignisse. SPACE startet beide Quellen nacheinander im selben
Bedienungsdurchlauf, ohne eine phasengleiche Hardware-Startflanke zu versprechen.

Die Statuszeilen zeigen ausgewählte Sample-ID, X, Aktivität, Busy, Last/Pause,
maximalen Abstand in Framegrenzen, Fehler und Refill-Zähler (Anzeige dessen Lowbyte).
Darunter steht der maximale Serviceabstand in **PAL-Rasterzeilen, hexadezimal**.
Die Anzeige verwendet SCRNPTR `$D060–$D062`, keine feste Screenadresse. Numerische
Live-Updates setzen bank0 und80-Byte-Zeilen voraus; VIC-Modus/Charset werden nicht
umgebaut. Bei einer abweichenden BASIC-Geometrie bleiben diese Updates aus.

## Originaldaten und Abspielraten

Verbindliche Analyse: PR #68, Commit
`d135b754beec10d608ac4bf6b91a2357247b62f3`.
`tools/extract_stage8a2_samples.py` verwendet das vorhandene OFS-/Hunk-Analysemodul
und die Source-Prüfung des unveränderten Stage8a1-Extractors. Es prüft zusätzlich
jeden geladenen Sampleblock gegen **beide** Original-RAM-Abbilder und die
Deskriptor-/Hashwerte der Analyse. Keine Ersatzsamples, kein XOR und kein Resampling.

Originalquellen liegen bereits unter `assets/stage5b/original_sources/`:
`VYPER.ADF`, `Vyper_Memory_Dump.dat`, `Vyper_Startscreen.uss`.
Ihre vollständigen SHA-256 stehen in `releases/stage_8a2/samples.json`.
Die24 Originaldeskriptoren stehen bei DATA+`$020A`, je12 Bytes: PER, Panningteiler,
Paula-Wortlänge, Busy und Laufzeitpointer. Die20 tatsächlich geladenen IDs sind:
`1,2,3,5,6,7,8,9,10,11,12,15,16,17,18,19,20,21,22,24`.

Die vollständige Metadatentabelle mit Original-Dateioffset, gepacktem Offset,
Bytezahl, PER, Teiler, Busy, Akkumulator, CRC und Sample-SHA-256 liegt in
[`samples.csv`](../releases/stage_8a2/samples.csv), maschinenlesbar auch in JSON.
Das gepackte SEQ `VYAU.DAT` enthält154304 unveränderte PCM-Bytes ohne Header:

- SHA-256: `74be8aff8cb474a52c3338e01cad270ec3b23ef74e1a90d5343ec804a7ea35e5`
- CRC16/CCITT-FALSE: `$AA4E`, Startwert`$FFFF`.
- Größte Samples: ID19=21546 Bytes, ID22=20074 Bytes.

Es wird nur **eine** vollständige PCM-Kopie ausgeliefert, innerhalb des D81.
Die separate DAT und die Includes lassen sich reproduzierbar extrahieren.

Wie im bestätigten Stage8a1:

```
Paula_rate = 3546895 / PER                 # angenommener PAL-Paula-Takt
increment = round(3546895 * 2^24 / (PER * 40500000))
```

Die Ganzzahlrechnung rundet exakt rational. ID17: PER356, Increment4127=`$00101F`.
Alle20 Original-PER bleiben erhalten; Signed8-CTRL ohne UNSIGNED-Bit. Tatsächliche
Takt-/Analogfilterunterschiede werden nicht durch erfundene Pitchkorrekturen kaschiert.

## Speicher und Laden

Vor Implementierung gegengeprüft: Stage8a1-Map (`$2100–$2663`, Sample`$4000–$5A3F`),
aktuelle Chipset Reference und XEMU `memory_mapper.c` (8MiB Attic ab`$08000000`,
384KiB Haupt-RAM). Dieser Test benutzt weder Titel-/Menü- noch Spielpuffer.

| Bereich | Verwendung |
|---|---|
| `$2001–$200C` | BASIC-SYS-Stub |
| `$2100` bis Ende laut Release-Map | Code, Metadaten, Sicherungen, Status |
| `$4000–$4FFF` | Quelle A,4096-Byte-Ring, Halbgrenze`$4800` |
| `$5000–$5FFF` | Quelle B,4096-Byte-Ring, Halbgrenze`$5800` |
| `$6000–$60FF` | SEQ-Ladestaging |
| `$6100–$61FF` | DMA-Rückleseprüfung |
| `$7000–$70FF`, `$7100–$71FF` | synthetische CPU-/DMA-Last |
| `$08000000–$08025ABF` | vollständiges Attic-Archiv, exklusives Ende`$08025AC0` |
| `$FB–$FE` | temporäre Zeiger, gesichert/restauriert |

Keine Allokation in ROM`$20000–$3FFFF` oder im nicht vorhandenen Haupt-RAM ab`$60000`.
Kein Audio-DMA-Zugriff auf Attic. Ausschließlich die synchronen F018A-DMAgic-Jobs
adressieren das Attic, mit expliziten MB-Optionen`$80/$81` und Formatoption`$0A`.

SEQ: SETBNK vor SETNAM, OPEN/CHKIN, CHRIN/READST, exakte Länge einschließlich EOF,
CLRCHN/CLOSE auf Erfolgs- und Fehlerpfaden; keine Bildschirmausgabe im Eingabekanal.
Jeder256-Byte-Block (letzter192 Bytes) wird ins Attic kopiert, zurück nach CHECK
kopiert und byteweise verglichen. Dazu läuft die CRC über die vollständige Datei.
Ein zweiter vollständiger Attic→CHECK-Durchlauf prüft die CRC des gespeicherten
Archivs nochmals, um auch Adressaliasing zwischen bereits geprüften Seiten zu
erkennen. DMA-Triggersequenzen sind mit PHP/SEI/PLP gegen IRQ-Unterbrechung geschützt.
Damit wird der tatsächlich benutzte Attic-Bereich auf dem Zielsystem geprüft;
eine bloße angenommene Kapazität genügt nicht. Nach ROM-Aufrufen werden beide
FAST/VFAST-Bits erneut gesetzt; der bekannte3,5-MHz-Rückfall wird vermieden.

## Ringprotokoll und Ende

Je Quelle gibt es zwei2048-Byte-Hälften. Vor Start wird der ganze eigene Ring per
DMA-Fill genullt. Beide Anfangsblöcke werden aus dem Attic vorgefüllt. Der **erste
Block wird rechtsbündig in Hälfte0 gelegt**, seine Länge ist `sample_length %2048`
(bzw.2048 bei Rest0). Der Startpointer zeigt auf dessen erstes Originalbyte.
Dadurch haben sämtliche nachfolgenden Blöcke2048 Bytes, auch der letzte.
**Jedes Sample endet exakt an einer Halbgrenze**, ohne hinzugefügte Audio-Paddingbytes.

Das löst einen im ersten Hosttest nachgewiesenen Fehler: Bei einem gewöhnlich
linksbündigen Start hatte ID20 am Ende nur22 Bytes. Software konnte beim Übertritt
in die letzte Hälfte bereits hinter dem nachträglich gesetzten Endpointer liegen.
Mit der rechtsbündigen Anfangsfüllung gibt es diesen kurzen Endblock nicht.

Der Service liest HIGH/LOW/HIGH des nicht gelatchten DMA-Pointers und wiederholt
bei einem zerrissenen Snapshot. Bank und Ringgrenzen werden geprüft. Nach einem
Halbwechsel wird ausschließlich die gerade frei gewordene Hälfte nachgefüllt.
Der nächste Attic-Quellbereich wird vor dem Transfer gegen das exklusive Archivende
geprüft. Wird die letzte Hälfte aktiv, setzt der Service deren exklusiven Endpointer
und löscht LOOP (`$C2`→`$82`). Danach beendet das Hardware-STP-Bit die Wiedergabe;
der Service deaktiviert den Kanal und setzt dessen Volume0. Keine IRQ-Ende-Annahme.

Schnellster verwendeter PER312: nominal11368,253Hz, eine Hälfte hält mindestens
**180,15ms** (quantisierte MEGA65-Rate:180,16ms). Beide Quellen zusammen benötigen
höchstens22,74kB/s (ca.22,2KiB/s) an PCM-Nachschub. Der normale
Service läuft bei jedem Schleifendurchlauf, nicht nur bei Framewechseln.
Ab drei beobachteten Framegrenzen ohne Bedienung wird beim Wiederanlauf sicher
gestoppt (PAL: Abstand kann bereits etwas über40ms betragen); zusätzlich gilt ein
200-Frame-Watchdog, länger als jedes Originalsample.

**Grenze:** Bei vollständig angehaltener CPU kann Software einen laufenden
Hardware-Ring nicht rechtzeitig abschalten. Ein Halt über die180ms-Pufferreserve
hinaus kann vor dem Wiederanlauf alte Ringdaten wiederholen. Ein solcher Halt wird
nicht als unterlauffreie Wiedergabe behauptet. Unbeschriebene Ringteile enthalten
Nullen. Im vorgesehenen begrenzten Lastbetrieb werden alle Jobs zwischen
Serviceaufrufen klein gehalten; ein späterer Engine-Einsatz muss dieselbe Reserve
mit echten Messungen bestätigen. Längere unteilbare Jobs würden größere Ringe oder
einen anderen Cache erfordern.

## Stereo-Matrix, Panning und Busy

Original-Soundtick USS`$C0D77E` (CODE+`$501E`); Startregister`$C0D7BC–$C0D7D6`;
Panning-Summentabelle`$C0D082`:60/40/30 bei Teilern4/6/8.

```
x = clamp(x, 0, 240)
right = floor(x / divisor)
left = (240 / divisor) - right
coefficient_byte = round(Paula_volume * 255 / 64)
coefficient_word = coefficient_byte * 257
```

Es sind weiterhin **zwei** logische Mono-Effektplätze. Anstelle zweier möglicherweise
auseinanderlaufender DMA-Cursor pro Stereopaar wird jede Quelle nur einmal gelesen:

| Quelle | DMA | Mixer-Eingang | L-/R-Koeffizienten, primär / Kopfhörer |
|---|---|---|---|
| A | Kanal0 `$D720` | Digi-L, Input8 | `$10/$30`, `$D0/$F0` |
| B | Kanal2 `$D740` | Digi-R, Input9 | `$12/$32`, `$D2/$F2` |

Kanal1/3 sind während des Tests deaktiviert. AUDEN=`$80`, NOMIX bleibt0.
Master-Gains der Outputs0/1/6/7=`$FFFF`; sonstige Eingänge sind stumm.
Kanalvolume=`$FF`, der originale Paula-Volume/64-Gain steckt im Mixer.
Teiler4 bei X0/120/240 ergibt L/R60:0,30:30,0:60; Teiler6 entsprechend40:0,
20:20,0:40 und Teiler8 entsprechend30:0,15:15,0:30.

Der Handbuch-/XEMU-Endiankonflikt bei16-Bit-Koeffizienten wird durch identische
beide Bytes vermieden. Das quantisiert den Original-Gain um höchstens1/510 im
absoluten Faktor, ohne die Panningformel zu ändern. Pro Mixer-Schreibzugriff werden
32 explizite I/O-Lesezyklen gewartet, bevor der Selektor geändert wird; die Reference
fordert mindestens32 Mixerzyklen. Mixer-/Parameter-Schreibzugriffe werden geprüft.
Stereo-Matrix ist gegen Reference **und XEMU-Quellcode** geprüft; eine akustische
Abnahme auf realer Hardware steht noch aus.

Normale Testereignisse werden bei Busy abgewiesen, T erzwingt Abbruch/Neustart.
Ein Pending-Slot speichert die konkrete Auswahl; mehrere zugelassene Schreiber vor
Verarbeitung: letzter gewinnt. Keine FIFO, keine versteckte Wiederholung bei vollem
Busy. Die Original-Busywerte3/6/120 werden im Test pro50-Hz-Frame dekrementiert.
**Testvereinfachungen/offene Integration:** Die genaue Amiga-Soundtick-Zeitbasis ist
nicht akustisch bewiesen; Pending wird hier im nächsten Bedienungsdurchlauf statt
im nächsten Gameplaytick verarbeitet. Die ereignisabhängige Unterscheidung des
Originals zwischen Player-Preemption und gegnerischem Busy-Guard wird über T und
normale Tasten manuell getestet. Keine Übernahme der Paula-Zwei-IRQ-Abschaltung,
des speziellen Gegnerschuss-Panningpointers oder der Levelwechsel-Sequenz.

## Last, Fehler und Restore

G erzeugt pro äußerem Durchlauf16 Jobs:256-Byte-DMA`$7000`→`$7100`, anschließend
256-Byte-CPU-Schleife (Read/XOR/ADC/Write). Nach **jedem** Job folgt der Audiostream-
Service. Das simuliert begrenzte Speicher-/Grafikarbeit, keinen integrierten RRB-Renderer.

Fehlercodes:1=Datei/Länge/EOF/CRC,2=fremde aktive Audio-DMA,
3=Attic-Rückleseprüfung,4=Mixer-/Audioinitialisierung,5=Pointer/Index/Grenze,
6=überschrittenes Serviceintervall,7=End-Watchdog.
Vor Datenladen werden fremde aktive Kanäle abgewiesen. Exit stoppt eigene Streams,
restauriert alle13 implementierten Register aller vier Kanäle, D711, alle256
Mixerbytes und Selektor, DMA-Adressregister D701/D702/D704, CIA-DDRA, Tastaturabfrage,
ZP, D030/D031/D054, KEY und ursprünglichen IRQ-Zustand. Die DMA-Trigger D700/D705
werden beim Restore **nicht** beschrieben: Das würde einen fremden DMA-Job auslösen.
Ihr zuletzt ausgeführter Adresszähler ist kein wiederaufzunehmender asynchroner Job.
IRQ-Vektoren, SID, Palette und Grafikmodus werden nicht verändert.

## Reproduktion und Prüfstand

```sh
python3 tools/extract_stage8a2_samples.py --output /tmp/vyper8a2-data
python3 tools/build_stage8a2.py --kickass /path/to/KickAss.jar
PYTHONPATH=/path/to/py65:tests:tools python3 -m unittest test_stage8a2 -v
```

KickAssembler5.25 wird mit dem bereits in den Projektwerkzeugen gepinnten SHA-256
geprüft. Python3, Java und für Tests py65==1.2.0. Keine Capstone-Laufzeitabhängigkeit
für Extraktion/Build. Der Build erzeugt PRG, vollständiges819200-Byte-D81 mit
`STAGE8A2`/SEQ`VYAU.DAT`, Assemblykopie, Includes, Symbolfile, Map, Metadaten und Hashes.

Siehe `stage8a2_test_results.txt` für tatsächlich ausgeführte Hosttests. Der Test
führt **assemblierte6502-Instruktionen** mit einem expliziten, begrenzten Modell
für KERNAL, DMAgic, Mixer und Audio-Pointer aus; das ist kein vollständiger MEGA65-
oder XEMU-Lauf. Modell-CPUzyklen sind keine gemessenen45GS02-/Attic-Buszyklen.

Vorläufige gemessene Modellwerte: maximal ca.2,5k6502-Zyklen je Serviceaufruf,
ca.93k je äußerem Lastdurchlauf mit16 Jobs. Der reale Rastermaximalwert wird auf
dem Zielsystem angezeigt. **Keine erfundenen XEMU-/Hardware-Messwerte.**

XEMU/Hardware-Abnahmeplan:

1. Nach Laden A=17/B=19 prüfen. A links, B rechts setzen, SPACE; beide unabhängig
   hörbar. Während langer Wiedergabe TAB und J/K/L umschalten, keine Kreuzsteuerung.
2. N/V durch alle20 Samples; besonders ID19/22 gleichzeitig vollständig abhören.
3. G einschalten, schnellstes Sample ID8 parallel auf beiden Quellen und ID19/22
   wiederholen. Keine Aussetzer/Knackser; Rastermaximalwert protokollieren.
4. Busy-Abweisung, T-Preemption, S, Stop-Pause und Neustart testen.
5. X während laufender Streams: kein Restsound, BASIC bedienbar; DIRECTORY und RUN
   erneut. Bei Fehlercode dessen Nummer und Core-/ROM-Version melden.

Kein XEMU-Hörtest und kein realer MEGA65-Lauf wurden in dieser Cloud ausgeführt.
Stage8a2 bleibt bis zur ausdrücklichen Benutzerbestätigung ein Testbuild.
