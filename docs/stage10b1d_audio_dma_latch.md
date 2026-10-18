# Stage10b1d — Audio-DMA-CURRENT-Latch A/B (Issue96)

Eigenständiger Branch `stage10b1d-audio-latch`, aus Diagnosebasis PR94
`fd6214c1c6be1adcedea095b0ebd474288a83403`. Keine Änderung an Stage10a1,
main, Grafik-Testbranches oder bisherigen Releases. Keine Stable-Markierung,
kein Merge und kein produktiver Audiofix.

## Belegtes Registerverhalten und offene Hardwareabnahme

Die Quellcodehypothese ist technisch nachvollziehbar. Der passende Core0.97
lässt die drei CURRENT-Bytes nicht unabhängig auf den Wiedergabezeiger wirken:

- [gs4510.vhdl, aaf4542, Zeilen3497–3520](https://github.com/MEGA65/mega65-core/blob/aaf4542d02679271b5fb84ad933cc39bbe091c3f/src/vhdl/gs4510.vhdl#L3497):
  D72A/B ändern `audio_dma_current_addr_set`. D72C setzt dessen Bankbyte und
  toggelt `audio_dma_current_addr_set_flag`.
- [Zeilen4622–4625](https://github.com/MEGA65/mega65-core/blob/aaf4542d02679271b5fb84ad933cc39bbe091c3f/src/vhdl/gs4510.vhdl#L4622):
  Der geänderte Flagzustand übernimmt den vollständigen Schreibpuffer in
  `audio_dma_current_addr`. Das ist ein zeitlich nachgelagerter Commit;
  nur die Low-/High-Bytes danach zu schreiben löst keinen weiteren Commit aus.
- [Readbacks ab2650](https://github.com/MEGA65/mega65-core/blob/aaf4542d02679271b5fb84ad933cc39bbe091c3f/src/vhdl/gs4510.vhdl#L2650)
  lesen den tatsächlich aktuellen Zeiger, nicht einfach den Schreibpuffer.
- Die gemeinsame Kanaldekodierung gilt ausdrücklich für Kanäle0–3:
  CURRENT-Tripel D72A/B/C, D73A/B/C, D74A/B/C und D75A/B/C.
  Das ist kein pauschaler Beleg für beliebige andere Registertripel:
  Loop-BASE D721/2/3 wird direkt byteweise geschrieben; Timing D72D/E/F
  hat dagegen einen eigenen Committrigger auf F (analog pro Kanal).
- Verfügbares lokales XEMU:
  [io_mapper.c](https://github.com/lgblgblgb/xemu/blob/40dfef0d1d5f56be2469492715c12bdb32c75b67/targets/mega65/io_mapper.c#L638)
  speichert die Bytes direkt in D7XX;
  [audio65.c](https://github.com/lgblgblgb/xemu/blob/40dfef0d1d5f56be2469492715c12bdb32c75b67/targets/mega65/audio65.c#L139)
  bildet daraus die aktuelle24Bit-Adresse. Kein vergleichbarer C-Committrigger
  in diesem Pfad. Das ist nicht als Revisionserkennung des Ziel-XEMU-Releases gemeint.

Geprüfte Core-Quelldatei SHA256:
`d44ae3906e1b0a826ca8e511c73ef1f50223b7de507a3ed349082fdefe58034e`.

Die tatsächliche Stage10a1-Routine `start_source` schreibt bei KanaloffsetX
zuerst D72C,X und danach D72A/B,X; der nachfolgende gestoppte Low-/High-
Readback springt bei Abweichung zu `source_init_error`. Dieser setzt4, und
der Audio-Dispatcher schreibt den Softwarestatus nach `$1FD3` und stoppt
besessene Quellen. **$1FD3 ist kein Hardware-Fehlerregister.** Derselbe
Produktionscode4 kann auch aus Mixer-/Globalinitialisierung stammen.

Der Latchmechanismus ist damit im Core belegt. Dass er die konkret vom Benutzer
beobachteten Audiofehler auf echter Hardware verursacht, ist **noch nicht durch
Hör-/Hardwaretest bestätigt**. Das muss dieser isolierte Test nachweisen.

## Deterministischer Test statt zufälligem Replay-Erfolg

Genau ein Kanal0, ein PCM-Sample, fester Mixer und dieselben Parameter in A/B.
Keine Attic-/Ringpuffer und keine Grafiklast. Der Test übernimmt die echte
Startadress-Schreibfolge und deren gestoppten Readback aus Stage10a1, aber
keine vollständige Spiel-/Streamingroutine. One-Shot basiert auf Stage8a1,
Mixerwartezeit und Save/Restore auf Stage8a2. Alle alten Dateien bleiben unverändert.

Originalsample: Sound-ID17, Player-Schuss, aus `/Vyper/sonquasar` im Original-ADF.
Reproduzierbarer vorhandener Extraktor `tools/extract_stage8a1_sample.py` prüft
Originaldateihashes, Shot-Descriptor und beide Original-RAM-Belege.

| Parameter | Wert, für beide Varianten gleich |
|---|---|
| Bytes |6720, unverändertes Signed8-PCM; kein XOR, kein Resampling |
| Originaloffset sonquasar |76106 |
| SHA256 |`392d6aa00a7097e5539722a4cbb0cb4b0f909815ed751c3b96b0a92020f573e9`|
| Paula PER / LEN |356 /3360Words |
| Paula PAL-Clockannahme |3546895Hz |
| Originalrate / Dauer |9963,188Hz /0,674483s |
| Audio-DMA-Clockannahme |40500000Hz |
| Inkrement |4127 =00101F; gerundetes `3546895×2^24/(356×40500000)` |
| MEGA65-Nominalrate |9962,529Hz; Quantisierungsabweichung ca.−0,0066% |
| Samplepuffer |016480–017EBF, Ende exklusiv017EC0; keine64KiB-Grenzquerung |
| Sentinel CURRENT |018020, in einer explizit genullten Seite018000–0180FF |
| BASE / TOP |016480 /7EC0; BASE in One-Shot unbenutzt |
| D729 / D720 |40 (25% Kanalpegel);02 gestoppt,82 gestartet, kein LOOP/UNSIGNED |
| D711 / D712 / D713 |80 geschrieben; Kanal-Swap0; Audio-IRQs0 während des Tests |

Beim Start wird das PCM nach016480 kopiert, nach6000 zurückkopiert und mit
Original-CRC16-CCITT-FALSE7F6F geprüft. Fehlender DMA-/PCM-Nachweis gibt01 und
sperrt den Start. Vor **jedem** Versuch, auch vor Replay und nach B→A:

1. Kanal deaktivieren und Volume0; Softwarestatus1FD3 auf00 zurücksetzen.
2. Identische BASE-, Rate-, TOP- und Timingregister setzen.
3. CURRENT absichtlich korrekt auf **018020** setzen: A=20, B=80, C=01 in
   dieser Reihenfolge.32I/O-Lesezyklen warten, gestoppten CURRENT zurücklesen.
   Falscher Sentinel gibt06; kein Playbackversuch auf unkontrollierter Adresse.
4. BEFORE-Protokoll mit Status00 und CURRENT018020 schreiben.
5. Nur jetzt unterscheidet sich die getestete Schreibfolge:

```text
A: STA $D72C <- $01
   STA $D72A <- $80
   STA $D72B <- $64

B: STA $D72A <- $80
   STA $D72B <- $64
   STA $D72C <- $01
```

6. Gleiche32I/O-Lesezyklen warten. Während EN=0 CURRENT kohärent zurücklesen
   und gegen016480 vergleichen. Der Bankvergleich ergänzt den ursprünglichen
   Low-/High-Test; da Sentinel und Ziel beide Bank1 benutzen, erzeugt er hier
   keine zusätzliche A/B-Unterscheidung.
7. Abweichung: Softwarestatus04, Kanal bleibt aus und stumm. Kein zweiter
   Bank-Schreibzugriff repariert heimlich A. Übereinstimmung: Volume40,
   Timingzähler low/high/bank=0, D720=82, One-Shot starten.
8. Completion/STP oder manuellen Stop protokollieren.100Frames Watchdog im
   vereinbarten PAL-Modus; Timeout05 bleibt in der Diagnose, kein BASIC-Abbruch.

Das Sentinel-Verfahren ist wesentlich: Ohne es könnte ein vorheriger B-Lauf
bereits die richtigen Low-/High-Stagingbytes hinterlassen, sodass ein späteres
A zufällig korrekt committen würde. Frühere Pointer-/Fehlerwerte werden deshalb
nicht als Reset benutzt.

## Erwartung und bisher tatsächlich geprüfte Ergebnisse

| Umgebung | A | B | Beweisgrad |
|---|---|---|---|
| Gestopptes Core-Latchmodell der Hosttests |CURRENT018020, Status04, kein EN|CURRENT016480, Status00, EN|Modell plus tatsächliche6502-Testopcodes, keine FPGA-Emulation|
| Ergänzendes lokales XEMU |CURRENT016480, Status00, One-Shot endet|gleich|Tatsächliche Register-/RAM-/Stop-Belege, Dummy-SDL|
| Angefordertes XEMU20260129235930 |offen|offen|Benutzer-Screenshot/Hörtest ausstehend|
| Echter Core0.97 aaf4542 |offen|offen|Benutzer-Hardware-/Hörtest ausstehend|

Der lokale XEMU-Lauf prüft A1→B→A2→Replay, tatsächliche PCM-Rückkopie und CRC,
CURRENT beim Start016480 und nach natürlichem Ende017EC0, Softwarestatus00,
Mixer-/Kanal-/Zeiger-/VIC-/Mailbox-Restore, erneutes RUN und BASIC DIRECTORY.
Ein gezielter Folgelauf prüft außerdem S bei aktivem Kanal und vollständigen
Sentinel-Reset mit anschließendem B-Replay.
Rohlogs und Laufbericht: `docs/diagnostics/stage10b1d/`. Die Audioausgabe benutzt
hier Dummy-SDL: **kein gehörter Sound und keine Hardware-Hörabnahme behauptet**.
UART-Pausen und SDL-Scheduling sind keine Messung von Hardwarelatenz oder
originalgetreuer Dauer. Der Watchdog wird nicht zum Paula-Timingbeweis umgedeutet.

## D711 separat, keine zweite verdeckte A/B-Änderung

Der strenge bisherige Initialisierungsvergleich mit80 bleibt erhalten.
Ein Fehler dort heißt in diesem Test03 und nicht04, damit ein anderer
Initialisierungsfehler nicht als Pointerfehler gilt. Der beim Vergleich gelesene
Rohwert bleibt im Logheaderbyte30 erhalten.

`G` führt nur eine separate Readback-Beobachtung aus. Das Display zeigt sowohl
`EQ80` (unmaskiert) als auch `MASK80` (`AND80`, danach Vergleich80). Beide
Bewertungen benutzen denselben einmal gelesenen Rohwert; keine Änderung des
D711-Schreibwerts, der Startfolge oder des Initfehlers. Core0.97 liefert in
D711.6 den read-only `pending_dma_busy`-Zustand. BeiC0 wäre strikt falsch,
maskiert wahr. Die maskierte Prüfung belegt allein AUDEN, nicht sämtliche
anderen Audio-Modusbits. Sie wird hier **nicht** als produktiver Globalfix integriert.
Bei Init03 ist die Pointer-A/B-Abnahme noch nicht aussagekräftig; Rohwert und
G-Befund melden, nicht durch einen anders konfigurierten B-Lauf umgehen.

Zusätzliche festgestellte Emulatorgrenze: Der verfügbare lokale XEMU liest
D713 alsFF zurück; der Core besitzt dort writable Audio-IRQ-Flags/-Enables.
Dieser Readback wird roh protokolliert, nicht als Pointerfehler04 behandelt.
Der Test sichert den Eintrittswert, schreibt in beiden Varianten0 und
restauriert den Wert am Ende. Eine anfängliche Diagnose-Sperre allein auf
„D713 muss0 lesen“ wäre deshalb auf diesem XEMU falsch gewesen.
D07B und PAL/NTSC-Konfiguration werden nicht verändert; deren Bewertung bleibt
wie in Issue96 gefordert ein getrenntes Thema.

## Bedienung und genaue Hardware-Testfolge

Frischer nativer BASIC-Start, PAL80×25, identische ROM V920413 wie bisher;
keine laufenden Audioanwendungen. Core-/XEMU-Version tatsächlich notieren.
Lautsprecher/Kopfhörer zunächst leise einstellen; der Kanalpegel ist40.

```basic
LOAD "STAGE10B1D",8
RUN
```

Nach Initialisierung spielt noch nichts. Anzeige: VARIANT A, Count00,
CURRENT018020, Initstatus00. Tasten1/2 wählen **und starten** den jeweiligen
Versuch. P, neu gedrücktes SPACE oder Joystick-Port2-Feuer wiederholen die
aktuelle Variante mit vollständigem Sentinel-Reset. SPACE/Feuer sind auf neue
Tastendrücke entprellt, keine verdeckte Warteschlange. S stoppt. G liest die
D711-Beobachtung. X beendet sauber nach BASIC.

1. `1` drücken und loslassen. Nach dem Versuch Foto `HW_A1` bzw. `XEMU_A1`.
   Gehört ja/nein, Art/Dauer und Ausgang Lautsprecher/Kopfhörer separat notieren.
   Besonders LATCHED, CURRENT,1FD3, BEFORE/AF, CTRL und ATTEMPT fotografieren.
2. `2`: Foto `HW_B`/`XEMU_B`, dieselben Hörangaben. Ein erfolgreich beendeter
   One-Shot zeigt PHASE03, PLAYING00; die LATCHED-Adresse bleibt als
   Startbefund erhalten, CURRENT zeigt den späteren Endzustand.
3. `1`: Foto `HW_A2`/`XEMU_A2`. A muss wieder von018020 ausgehen; ein
   vorheriger B-Start darf A nicht nachträglich korrekt machen.
4. `P` (oder jeweils neu SPACE/Feuer) für mindestens drei Replays. Danach B
   ebenfalls mehrfach wiederholen. Eindeutige Dateinamen benutzen, nichts als
   „A“ überschreiben. Hörabbruch, Rauschen oder Statusabweichungen notieren.
5. Während eines B-Laufs `S` testen, dann neu starten. `G` separat vor/nach
   einem B-Lauf betätigen und EQ80/MASK80/Rohwert festhalten. Kein anderer
   Soundparameter wird dabei umgeschaltet.
6. `S`, optional RAM-Log extern sichern, dann `X`. BASIC muss normal reagieren;
   `DIRECTORY`, danach `RUN`, erneut A/B und `X` testen.

Eine Bewertung „nur B spielt korrekt“ ist erst mit vollständigen Fotos/Logs,
Status00 bei B,04 mit passendem falschem CURRENT bei A und tatsächlichem
Hörvergleich belastbar. Falls A auch auf Hardware spielt, insbesondere den
BEFORE-Sentinel und die genaue Coreversion prüfen. Falls beide schweigen,
aber beide Pointer stimmen, Mixer/Globalstatus/Audioausgang gesondert prüfen:
Das beweist keinen Startadress-Latchfehler.

## Protokoll / externe Sicherung

Kein KERNAL-Dateiexport im aktiven Audiotest. Das Display wird nach der
Initialausgabe direkt im nativen BASIC-Screen aktualisiert, ohne Grafikmodus-
oder Zeichensatzwechsel. Das Log liegt bei **5000–581F,2080Bytes** und bleibt
nach X erhalten;1FD3 selbst wird beim Exit auf den Eintrittswert restauriert.
Daher für die letzte Testdiagnose das Log lesen, nicht den anschließend
wiederhergestellten Mailboxwert für einen neuen Erfolg halten.

Header32Bytes: Magic `VYAL1B1D`, Version1; Byte9Anzahl (max64),10nächster
Ringindex,12/13Gesamtzahl modulo65536,14/15Versuchszähler,
16/17Recordgröße32,18alterMailboxwert,19Initfehler,20Sound-ID17,
21/22PER356,23Eintritts-CPU-P,24–26Ziel016480,
27–29Sentinel018020,30D711-Initreadback. Rest reserviert.

64Records zu32Bytes, älteste werden bei Bedarf überschrieben. Je Versuch
BEFORE(0), LATCHED(1), AFTER_START(2), bei Erfolg DONE(3). STOP4, G5,
TIMEOUT6 sind zusätzliche Ereignisse. Fehler04 erzeugt kein DONE-Ereignis.

| Recordbytes | Inhalt |
|---|---|
|0/1,2,3|Versuchsnummer, Variante ASCIIA/B, Phase|
|4–7|1FD3, D711raw, strikt==80, maskiert==80|
|8–11|D720,D712,D713,D7FA|
|12–14,15|kohärent gelesener CURRENT low/high/bank, Volume|
|16–18,19–21|BASE low/high/bank, Rate low/high/bank|
|22/23,24|TOP low/high, zweiter Volume-Readback|
|25–29|Variantenindex, Sentinel-Fehler, Playing, Fehler-vorher/-nachher|
|30,31|Startframe, Flag für erschöpfte kohärente Pointer-Leseversuche|

Der CURRENT-Read benutzt high/low/high mit begrenzten16Versuchen; Bank bleibt
bei diesem Sample konstant. Readbacks sind sequenziell, nicht atomar. Bei
erschöpften Versuchen ist das im Record markiert. Der Decoder akzeptiert rohe2080Bytes, einen PRG-Header mit Ladeadresse5000
oder einen vollständigen UART-Monitor-Textdump mit16Byte-Zeilen
`:00005000:…` bis einschließlich`:00005810:…`. Fehlende oder widersprüchliche
Zeilen werden abgelehnt, nicht mit Nullen ergänzt. Der rohe RAM-Block besitzt
keine CRC; vollständige Übertragung und Originaldatei sichern. Nach S und ohne
weitere Eingaben ist das Log stabil. Nicht mit einem Stage10b1b-Decoder lesen.

```sh
python tools/analysis/inspect_stage10b1d.py HW_A_B_A.LOG --json HW_A_B_A.json
```

Bei weiteren Uploads die Plattform, tatsächliche Version, Reihenfolge und
Hörnotizen angeben. Fotos plus Rohlog genügen; ein optionales D81 mit extern
exportierten Daten darf zusätzlich beigefügt werden.

## Speicher und Restore

Quelle `src/tests/stage10b1d.asm`; Programm ab2100 unter4000, kein Überschreiben
des BASIC-Fonts. Originalsample im PRG beiA000–BA3F. RAM-Log5000–581F,
CRC-Rückkopie6000–7A3F, Audio-Puffer16480–17EBF,
Null-Sentinelseite18000–180FF. Kein Attic, kein ROM-Bereich20000–3FFFF,
keine Grafikpuffer oder produktiven Spielzustände importiert.

Vorher aktive, nicht gestoppte fremde DMA-Kanäle werden abgelehnt (02).
Sicherung: VIC-I/O-Steuerwerte D030/D031/D054 plus benötigte
I/O-/CIA-DDR-/ZP-Werte, Kanal0-Register0–15, globale Audio-Steuerbits,
Kanal-Swap, Audio-IRQ-Byte, Mixerselector und alle256Mixerbytes. Nur Kanal0
wird benutzt; Kanäle1–3 werden nicht konfiguriert. Die Audio-IRQ-Konfiguration
wird gemeinsam für A/B deaktiviert und anschließend restauriert. CPU-IRQs
werden mit PHP/SEI/PLP behandelt; keine IRQ-/NMI-Vektoren oder CIA-ICRs ändern.

Beim Exit: eigener Kanal zuerst stoppen, Mixer vollständig restaurieren,
plain BASE/Rate/TOP/Volume, CURRENT in **Low/High/Bank** und Timing in
Low/Middle/High (Commit aufF) restaurieren, ursprüngliche inaktive/stopped Kontrolle
zuletzt. Read-only Sample-valid-, Clip- und BLKD-Bits werden nicht als
schreibbare Zustandssicherung behandelt; D711-Restore maskiert aufB8,
D712 auf02. Keine Zusage zur Fortsetzung fremder aktiver Audios oder zum
beliebigen externen IRQ-Kontext; Abnahme gilt für frisches natives BASIC.
Keine Audio-DMA mehr nach X. Original-1FD3, Mixerselector, CIA-DDR,
Keyboard-Matrixquery, ZP und FAST-Einstellungen werden wiederhergestellt.
DMAgic-Adressregister701/702/704 werden ohne Triggerwrite restauriert.

## Reproduzierbarkeit und Prüfgrenzen

```sh
python tools/build_stage10b1d.py --kickass /pfad/zu/KickAss.jar
KICKASS_JAR=/pfad/zu/KickAss.jar PYTHONPATH=/pfad/zu/py65 \
  python tools/test_stage10b1d.py
```

KickAssembler5.25 (geprüfte bestehende Jar-Prüfsumme), Java/Python; für
Opcode-Hosttests py65==1.2.0. Der Builder extrahiert das Originalsample erneut
und prüft sämtliche Originalbelege. Alle benötigten Binärincludes und die
vollständige ASM-Quelle liegen zusätzlich im Release. D81 enthält das
vollständig eigenständig startfähige PRG; kein DAT-Nachladen erforderlich.

Neun Hosttests bestehen: exakte echte6502-MMIO-Schreibfolgen; beide expliziten
Registermodelle einschließlich A→B→A/Replay; gestoppte Readbacks vor Enable;
Konstanz übriger Parameter; separat klassifiziertes D711-C0-Verhalten;
Completion/Watchdog; Original-CRC/DMA-Bounds; Current-/Mixer-/IRQ-Restore;
Ringüberlauf/Parserfehler; D81-Dateiketten und byteidentischer unabhängiger
Release-Rebuild. Die Modelle prüfen die logische Folge, nicht die FPGA-
Clock-Domain-/Buslatenz. Hosttests emulieren keine tatsächlichen DMA-Kopien.

## Kleinster späterer produktiver Vorschlag

Wenn die echte Hardware A=04/falscher CURRENT und B=00/korrekt hörbar bestätigt,
in einem gesonderten Stage10b2-Fix ausschließlich den CURRENT-Schreibblock von
`start_source` für die belegten Kanaloffsets0/20 umordnen: Low, High, Bank.
Auch Restore-/andere CURRENT-Schreiber mit demselben Corebeleg auditieren,
aber Loop-BASE nicht blind umordnen. D711-Maskierung, Panning, Streaming,
Schuss-/Soundzuordnungen, D07B und Grafikgeometrie separat halten.

Dieser Fix ist hier nicht in Stage10a1 vorgenommen. Bei anderem Hardwarebefund
zuerst die tatsächlich protokollierte Fehlerklasse, Pointer und globalen
Kontrollbits auswerten, statt04 pauschal dem Latch zuzuschreiben.
