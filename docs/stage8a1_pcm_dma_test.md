# Stage8a1 – isolierter Original-PCM-Test (Issue69)

**Testbuild, nicht Stable.** Branch `stage8a1`, Basis `f7350d6` (Main-Merge
von Stage7b5b). Kein Engineimport und keine Soundintegration in das Spiel.
Die vorhandenen Quellen/Assets/Releases bleiben bytegleich.

Aus Analyse-PR68, Commit`d135b754beec10d608ac4bf6b91a2357247b62f3`, wurden
gezielt nur `tools/analysis/analyze_amiga_sound.py` und die Original-Sampletabelle
`docs/amiga_sound_evidence/samples.csv` übernommen. Kein unkontrollierter Merge
des Analysebranches. [Technische Soundanalyse und Belege](https://github.com/Niederrheiner-KKB74/Vyper_for_Mega65/pull/68).

## Original-Sample und Tonhöhe

| Eigenschaft | Wert |
|---|---|
| Ereignis / Sound-ID |Player-Schuss /17|
| Originaldatei |ADF `/Vyper/sonquasar`|
| Dateioffset |`$1294A` =76106|
| Paula-Länge |3360 WORDs=`$0D20`, also6720 Bytes=`$1A40`|
| Paula-PER |356=`$0164`|
| Format |Signed8, unveränderte Originalbytes; **kein XOR`$80`**|
| Sample-SHA256 |`392d6aa00a7097e5539722a4cbb0cb4b0f909815ed751c3b96b0a92020f573e9`|
| Laufzeit-CRC16/CCITT-FALSE |`$7F6F`, Init`$FFFF`, Polynom`$1021`|
| Angenommener PAL-Paula-Takt |3546895Hz|
| Nominale Originalrate |3546895/356=9963,188202Hz|
| Angenommener MEGA65-Akkumulatortakt |40500000Hz|
| Rateninkrement |round(rate×2^24/40500000)=4127=`$00101F`|
| Effektive Rate mit diesem Inkrement |9962,528944Hz|
| Reine Original-Sampledauer |≈0,674483s|
| MEGA65-Dauer bei40,5MHz |≈0,674528s|

Der Extraktor prüft die SHA256 aller drei Originalquellen aus PR68, OFS-Header/
Dateiketten und Blockchecksummen, den Original-HUNK-Deskriptor und die Sampletabelle.
Die extrahierten6720 Bytes werden mit den Samplepointern **beider** Speicherabbilder
verglichen. Der Builder prüft außerdem ihre unveränderte Einbettung im PRG.
Das Inkrement wird mit exakter Ganzzahl-/Rationalrechnung gerundet.

Der nominale Ratenfehler ist≈−0,6593Hz bzw.−0,0066%. Tatsächlicher Core-/Videotakt
und analoger Klang müssen auf dem Zielsystem geprüft werden. Die ROM-Version
allein belegt keinen FPGA-/Audiotakt. Es wird kein gemessener WinUAE-Klangvergleich
behauptet. Insbesondere werden keine Paula-Analogfilter oder Start/Stop-Transienten
synthetisch hinzugefügt.

## Wiedergabe und Bedienung

D81 einlegen, `LOAD"STAGE8A1",8`, danach `RUN`. Das Programm schreibt eine kurze
Anleitung im vorhandenen BASIC-Textmodus. Kein Titelbild, RRB, Bitmap- oder
Screenpointerwechsel. Zielstartumgebung ist reguläres MEGA65-BASIC, insbesondere
der bisher verwendete80×25-Modus; keine Ausführung aus einem fremd gemappten Spiel.

- SPACE oder Feuer an **Joystick-Port2**: Sample einmal vollständig abspielen.
- Vor dem nächsten Abspielen beide Auslöser loslassen. Halten wiederholt nicht.
- Tastendrücke während der Wiedergabe werden verworfen, nicht vorgemerkt und
  unterbrechen das Sample nicht. Nach Wiedergabeende neu drücken.
- `X` bzw.`x`: Wiedergabe sofort stoppen und sauber nach BASIC zurückkehren.
  Anschließend erneut `RUN` testen.

SPACE wird über die dokumentierte direkte Tastaturmatrix abgefragt:
`$D614=7`, Bit4 von`$D613` aktiv-low. Der ASCII-FIFO wird konsumiert, wirkt aber
nur für X; dadurch lösen automatische SPACE-Wiederholereignisse keine Replays aus.
Joystick-Feuer kommt von`$DC00` Bit4. CIA-DDRA wird vorübergehend auf Eingang
gelegt, ohne den Port-Ausgabelatch zu überschreiben; Query-Selektor und DDR werden
restauriert. Beim Eintritt gehaltene Auslöser müssen zuerst losgelassen werden.

## Audio-DMA-Konfiguration

Hardwaregrundlage ist die vorhandene MEGA65 Chipset Reference,
[Audio DMA](https://github.com/MEGA65/mega65-user-guide/blob/cefce48d72e5c98d732c0589461d62b205b5165f/appendix-dmagic.tex#L562)
und [Audio-Crossbar](https://github.com/MEGA65/mega65-user-guide/blob/cefce48d72e5c98d732c0589461d62b205b5165f/appendix-45io27-registers.tex).
Signed8/Endvergleich wurden zusätzlich gegen
[XEMU `render_dma_audio`, Commit40dfef0](https://github.com/lgblgblgb/xemu/blob/40dfef0d1d5f56be2469492715c12bdb32c75b67/targets/mega65/audio65.c#L134)
geprüft: Formatbits`2` wählen8Bit, Bit5 schaltet nur bei1 die Unsigned-Konvertierung
ein. Für Original-Signed8 bleibt Bit5 daher0.

| Register | Laufzeitwert / Funktion |
|---|---|
|`$D02F`|MEGA65-I/O mit`$47,$53` freischalten|
|`$D030`|nur CRAM2K-Bit0 temporär löschen; ROM-/Bankbits erhalten|
|`$D031`, `$D054`|je Bit6 setzen: **FAST und VFAST**, nicht nur3,5MHz|
|`$D711`|`$80`: AUDEN an, NOMIX aus, Crossbar verwenden|
|`$D720`|`$02` deaktiviert /`$82` läuft: Signed8, kein LOOP, STP gelöscht|
|`$D721–$D723`|`$004000`, definierter aber unbenutzter Loopstart|
|`$D724–$D726`|`$1F,$10,$00`, Inkrement little-endian|
|`$D727–$D728`|`$40,$5A`, **exklusives** Ende`$5A40`|
|`$D729`|`$40`, moderate Kanal-Lautstärke≈25%|
|`$D72A–$D72C`|anfängliche aktuelle Adresse`$004000`|
|`$D720` Bit3|One-Shot-Stopflag wird gepollt|
|`$D7FA`|physischer Framezähler für100-Frame-Watchdog|

Es wird **nur Kanal0** programmiert. Die anderen drei Kanäle werden nicht
umprogrammiert. Wenn ein anderer oder der eigene Kanal bereits aktiv ist,
verweigert der Test den Start, statt einen fremden Stream unvollständig zu sichern
und später falsch fortzusetzen. Ein gesetztes EN mit ebenfalls gesetztem STP
ist bereits gestoppt und darf gesichert werden.

Die Crossbar erhält festes Mono-Routing des Digital-Left-Eingangs zu beiden
primären Ausgängen sowie beiden Kopfhörerausgängen. Kein dynamisches Stereo-Panning,
kein zweiter Audiokanal. Unity-Bytes`$FFFF` vermeiden die in älteren Dokumentationen
und Emulatoren unterschiedliche Beschreibung der16-Bit-Koeffizienten-Byteordnung.
Koeffizientenpaare`$10/$11,$30/$31,$D0/$D1,$F0/$F1` routen Digital-Left,
`$1E/$1F,$3E/$3F,$DE/$DF,$FE/$FF` setzen die betreffenden Master-Gains.
Alle anderen Koeffizienten sind im Test0, dadurch keine Mikrofonrückkopplung oder
unbeabsichtigte SID-/FM-Beimischung. Alle256 vorherigen Mixerbytes und der
Selektor werden für den Exit gesichert.

Mixer-Schreibwerte, Parameter und Globalenable werden im deaktivierten Zustand zurückgelesen;
FAST/VFAST werden ebenfalls geprüft. Das Stopflag wird bei der Initialisierung
nicht als schreibbar vorausgesetzt. Beim Abspielen werden die Pointer neu gesetzt
und EN zuletzt eingeschaltet. Es gibt keinen Loop. Am Stopflag deaktiviert die
Software den Kanal und setzt die Testlautstärke0. Die letzte zulässige Byteadresse
ist`$5A3F`; es wird kein Byte hinter dem Sample angefordert.

Der Watchdog bricht bei fehlendem One-Shot-Ende nach100 beobachteten Video-Frames
ab (nominal2s PAL, ca.1,67s bei60Hz). Dieses Zeitlimit ist bewusst länger als das
Sample. Es hängt nicht von einem durch SEI angehaltenen KERNAL-Softwaretimer ab.
Die Pollschleife enthält laufend Speicherlesezugriffe und stellt damit die vom
Audio-DMA benötigten Idle-/Buszyklen bereit.

## Speicher und Exit

| Bereich | Verwendung |
|---|---|
|`$0000/$0001`|CPU-Port unverändert|
|`$00FB/$00FC`|CRC-Zeiger, gesichert und restauriert|
|`$0100–$01FF`|normaler JSR/PHP-Stack|
|BASIC-Screen/Color-RAM/Zeichensatz|keine eigene Allokation oder Video-Modusänderung|
|`$2001–$200C`|BASIC-SYS-Zeile|
|`$2100…` bis unter`$3000`|Code, Diagnosen,13 Audio- und256 Mixer-Sicherungsbytes|
|`$4000–$5A3F`|6720 Original-Samplebytes, DMA-lesbares Bank0-RAM|
|`$5A40`|exklusive Endadresse, keine Sampledaten|

Die exakten Controller-Endadressen stehen in`releases/stage_8a1/memory-map.txt`.
Der PRG-LOAD schreibt auch die aufgefüllten Zwischenräume zwischen seinen
Segmenten, wie bei den anderen BASIC-SYS-Programmen. Der Test ist kein Aufruf aus
einem beliebig belegten Speicherlayout. Es gibt **keine** Nutzung von ROM-RAM-
Lücken,`$60000+`, Attic, High-RAM-DATs, Screen-/Grafikpuffern der Engine oder einer
DMAgic-Kopierliste. Das Sample bleibt innerhalb derselben64-KiB-Bank; der16-Bit-
Audio-Endvergleich kann deshalb nicht vorzeitig durch einen Bankumlauf treffen.

Der Exit stoppt zuerst den eigenen Kanal, stellt den gespeicherten ruhenden
Kanalzustand, alle Mixerkoeffizienten, AUDEN-/Globalregister, Selektor, CIA-DDR,
Tastaturquery, CRC-ZeroPage und FAST/VFAST-/CRAM-Einstellungen wieder her.
Die vorherige I/O-Freischaltung wird aus dem lesbaren KEY-Latch für VIC-II,
VIC-III, MEGA65 bzw.Ethernet-I/O rekonstruiert. IRQ-Zustand kommt per PLP zurück.
Es werden weder IRQ-Vektoren installiert noch KERNAL-/BASIC-Routinen gepatcht.
Interne Sample-Phasen eines fremden laufenden Streams wären nicht vollständig
restaurierbar; gerade deshalb wird ein solcher Stream vor der Initialisierung
abgewiesen. Auf echter Hardware sind lesbare Statusflag-/KEY-Latch-Eigenheiten
bei der Abnahme mitzuprüfen.

## Fehler und reproduzierbarer Build

Build-/Extraktionsfehler bei fehlenden Originaldateien, ungültiger ADF-Kette,
falschem Hash/Deskriptor/Länge oder falscher Einbettung brechen ausdrücklich ab.
Die Runtime diagnostiziert CRC-Fehler, belegten Audio-DMA, fehlgeschlagene
Registerinitialisierung und Timeout. Danach wird ebenfalls restauriert und nach
BASIC zurückgekehrt. Ein separater Sample-Dateilader kann nicht scheitern, weil
nur dieses eine6,7-KB-Sample bereits im PRG eingebettet ist.

```sh
python tools/extract_stage8a1_sample.py --output /tmp/vyper-sample17
python tools/build_stage8a1.py --kickass /pfad/zu/KickAss.jar
PYTHONPATH=tests:tools:/pfad/zu/py65 \
  python -m unittest test_stage8a1 -v
```

Extraktion benötigt nur Python-Standardbibliothek. Vorhandenes KickAssembler5.25
wird per SHA256 geprüft, Java wird benötigt. Für die Hosttests gilt der bestehende
Pin`py65==1.2.0` aus`tests/requirements-stage3b1.txt`. Das gemeinsame D81-Werkzeug
wird ausschließlich für Disketten-Dateiketten genutzt; keine Spielengine wird
assembliert. Der Builder extrahiert in sein temporäres Arbeitsverzeichnis,
übernimmt die eigenständige ASM und liefert PRG, Symbole, komplettes819200-Byte-D81,
ASM, Samplekonstanten, Metadaten, Speicherkarte und Prüfsummen nach
`releases/stage_8a1/`.

Die Diskette enthält nur `STAGE8A1` als PRG samt eingebettetem Sample. Kein
komplettes`sonquasar`, kein20-Sample-Archiv und keine weiteren Spiel-DAT-Dateien.
Die Rohdatei wird nur bei explizitem Extraktoraufruf erzeugt; sie wird nicht noch
mehrfach als eigenes Release-/Diskettenasset publiziert. Für eine Neuassemblierung
der ASM aus dem Repository erzeugt der Builder `sound17.s8` und`sample17.inc` neu.

## Prüfergebnisse und Abnahme

**Fünf Hosttests bestanden**, Protokoll`releases/stage_8a1/test-results.txt`.
Zwei unabhängige Builds liefern identische Builder-Prüfsummen für alle Ausgaben.
Geprüft wurden unveränderte Originalbytes, PER/Ratenwert, exklusive DMA-Endgrenze,
alle6720 modellierten Samplefetches, Signed8-Konfiguration, Speichergrenzen,
SPACE/Feuer-Halten/Loslassen, Verwerfen früher Replays, beide X-Schreibweisen,
Exit während Wiedergabe, erneutes RUN, Mixer-/I/O-/IRQ-Restore sowie CRC-, Busy-,
Register- und Timeoutfehler. Die Tests führen
die **tatsächlich assemblierten Instruktionen** aus, modellieren aber Audio-DMA,
Mixer, Framezähler und Eingaben gezielt. Das beweist Kontrollfluss und Register-/
Speicherwerte, **keine hörbare Ausgabe oder vollständige Hardwareemulation**.

Ein grafisches XEMU mit SDL-Laufzeit ist hier nicht eingerichtet: Es liegt der
Quellcheckout vor, aber kein ausführbares`xmega65`, `sdl2-config` oder `xvfb-run`.
Deshalb **kein durchgeführter XEMU-Hörtest**, keine reale Hardwareabnahme und kein
WinUAE-Originalklanggleichheitsnachweis. Die vorhandene ROM-Datei allein ersetzt
diese Laufzeitumgebung nicht.

Bitte in XEMU und anschließend nach Möglichkeit echter Hardware prüfen:

1. BASIC starten, D81 laden, RUN: normale Textanzeige, beide FAST-Bits aktiv.
2. SPACE und Port2-Feuer: jeweils ein kurzes Original-Schussgeräusch, ungefähr0,675s,
   feste Ausgabe links/rechts, keine Übersteuerung und kein dauerhaftes Looping.
3. Halten, Loslassen und mehrfach neu drücken; kein Auto-Repeat. Frühzeitiges
   Drücken während eines Samples unterbricht es nicht und wird nicht vorgemerkt.
4. X mitten im Klang sowie nach dessen Ende: sofort still, normaler BASIC-Cursor,
   Tastatur/DIRECTORY funktionieren. Mehrfach RUN und anschließend wieder abspielen.
5. Bei Klangabweichungen ROM-, Core-/FPGA- und XEMU-Version, Video-Modus,
   eingestellte Audioausgabe und tatsächlichen CPU-Takt getrennt erfassen.

**Stage8a1 erst nach ausdrücklicher Benutzerbestätigung als Stable markieren.**
