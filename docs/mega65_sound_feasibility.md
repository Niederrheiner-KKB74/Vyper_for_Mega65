# MEGA65: Machbarkeit originaler Vyper-Sounds

Issue67, **Hardwarebewertung ohne Implementierung und ohne Spielbuild**.
Grundlage: [Originalanalyse](amiga_sound_engine_analysis.md),20 tatsächlich geladene
Signed8-PCM-Samples mit154304 Bytes, zwei logische Klangplätze und dynamisches
Stereo-Panning. Original-Zuordnungen bleiben [separat dokumentiert](amiga_sound_event_mapping.md).

## Hardwareempfehlung

**Bestätigt durch Chipset Reference:** Der MEGA65 besitzt vier DMA-Audiokanäle
bei`$D720/$D730/$D740/$D750`,8-/16-Bit- sowie Nibble-Wiedergabe,24-Bit-
Ratenakkumulator, Start-/Loopadressen, Endvergleich, Lautstärke und Stereo-Mixer.
Das ist für diese Original-PCM-Daten die erste Wahl. Eine SID-/FM-Neusynthese würde
die gesampelten Geräusche ersetzen und wäre nicht originalgetreu.

Quellen sind die vorhandene VIC-IV/MEGA65 Chipset Reference, Audio-DMA-Kapitel,
Stand des lokalen Handbuchcheckouts:

- [`appendix-dmagic.tex`, Audio DMA](https://github.com/MEGA65/mega65-user-guide/blob/cefce48d72e5c98d732c0589461d62b205b5165f/appendix-dmagic.tex#L562), insbesondere Start/Ende, Takt, Panning und Stopflag.
- [`appendix-memorymap.tex`](https://github.com/MEGA65/mega65-user-guide/blob/cefce48d72e5c98d732c0589461d62b205b5165f/appendix-memorymap.tex#L123): Attic ist kein direktes Audio-DMA-RAM.
- [`appendix-45io27-registers.tex`](https://github.com/MEGA65/mega65-user-guide/blob/cefce48d72e5c98d732c0589461d62b205b5165f/appendix-45io27-registers.tex#L916): direkte Digital-Audioregister und Hardware-DAC-/HDMI-Einordnung.
- Gegenprüfung der Emulatordarstellung: [XEMU `audio65.c`](https://github.com/lgblgblgb/xemu/blob/40dfef0d1d5f56be2469492715c12bdb32c75b67/targets/mega65/audio65.c#L134). Das ist eine Implementierungshilfe, kein Ersatz für die Hardwarebeschreibung.

SID kann Wellenformen/Filter synthetisieren, würde für unveränderte PCM-Rohdaten
aber CPU-gesteuerte Digi-Techniken benötigen. Die direkten DAC-/Digitalregister
`$D6F8–$D6FB` verlangen ebenfalls regelmäßiges Füttern und erhöhen CPU-/Jitterlast.
Beides ist gegenüber der vorgesehenen Audio-DMA unnötig. OPL/FM ist für eine
Nachbildung dieser Samplebytes ebenfalls nicht die passende Quelle.

## Abbildung und hörbare Grenzen

**Vorgeschlagene spätere Architektur, noch nicht implementiert:** zwei logische
Effektplätze entsprechend den Originalpaaren, mit Original-Pending-/Busyregeln.
Entweder vier Hardwarekanäle mit je zwei identischen Datenpointern und getrennten
L/R-Gains, oder je ein Kanal pro Monoquelle mit korrekt eingestelltem Gegenkanal-
Gain und Crossbar. Bei vier Kanälen müssen die Stereoseiten passend umgeordnet
werden: Paula0/1/2/3 = L/R/R/L; MEGA65 hat normalerweise erste zwei links, zweite
zwei rechts. Eine mögliche Zuordnung ist Paula0→MEGA0,1→MEGA2,2→MEGA3,3→MEGA1.
Die richtige Matrix ist im isolierten Hardwaretest akustisch zu prüfen.

Panning verwendet die logischen Original-X-Einheiten0..240, nicht die verdoppelte
native MEGA65-VIC-X-Koordinate. Bei den bereits mittig gespeicherten Projektile-
Koordinaten muss die Linksrand-/Mittelpunktdifferenz berücksichtigt werden.
Die Originalformel und ihr Quellpointer stehen im Ereignisbericht.
Paula-Volumes liegen hier bei0..60 (bzw.Summen40/30), nicht grundsätzlich64.
Ein Gain-Mapping ungefähr `PaulaVOL*255/64` erhält die relative Lautstärke;
linearer Crossbar-/DAC-Gain und End-to-end-Pegel sind noch zu überprüfen.

8-Bit-Signed-PCM kann ohne Resampling/komprimierende Neukodierung aufbewahrt
werden. XEMU zeigt Signed8 als8-Bit-Modus ohne das Unsigned-Konvertierungsbit;
eine spätere Registerkonfiguration muss das gegen die verwendete Coreversion
prüfen. Kein stilles XOR der Originaldaten in einem vermeintlichen Signed-Modus.
XOR`$80` wird nur für die standardmäßig unsigned8-Bit-WAV-Vorschau verwendet.

Für angenommenes PAL-Paula-Clock3546895Hz:

```
rate_Hz = 3546895 / Paula_PER
MEGA65_rate_increment = round(rate_Hz * 2^24 / 40500000)
```

Die20 geladenen Samples liegen nominal bei8210,405..11368,253 Samples/s.
Die CSV enthält alle24 berechneten Akkumulatorwerte. Der40,5-MHz-
Akkumulator quantisiert die Rate in Schritten von≈2,414Hz; die reine Rundung
verursacht höchstens≈1,207Hz Fehler. Tatsächlicher Core-/Video-Systemtakt und
PAL/NTSC-Auswahl sind vor einem Hörvergleich zu bestätigen. Es werden keine
unbewiesenen nativen Gameplay-Updates/s zur Bestimmung der PCM-Tonhöhe benutzt.

Die Digitaldaten lassen sich originalgetreu erhalten. Amiga-Analogfilter,
Paula-Start/Stop-Transienten, DAC-Eigenheiten und dynamische Vorab-Unterbrechungen
sind damit **noch nicht** nachgebildet. Mono-WAVs sind keine Referenzaufnahme
der kompletten Amiga-Soundmischung. Insbesondere sollte nicht vorschnell ein
neuer ADSR- oder Pitch-Effekt ergänzt werden: Der nachgewiesene Code besitzt
konstante Sample-PER und räumliche Volumeänderungen.

## Kapazität: nicht einfach154KB hinter die bestehenden Assets laden

**Bestätigte Datenmengen:**

| Bedarf | Bytes |
|---|---:|
| alle24 Dateisegmente |164836|
|20 vom Original geladene Samples |154304|
| vier feste Effekte17/19/22/24 allein |59100|
| größtes Einzel-Sample19 |21546|
| zweitgrößtes Sample22 |20074|
| zwei Maximalpuffer à21546 |43092|

Eine vollständige Level-Working-Set-Obergrenze (alle im Level vorkommenden vier
Typereignisse plus feste Player-/Übergangssamples) liegt je Level zwischen70930
und154304 Bytes; Level1 benötigt77246, Level100 die vollständigen20 Samples.
Auch ein naives Level-Caching ist also kein kleiner Zusatz.
Diese Werte sind aus den Daten berechnet, keine neue Speicherreservierung.

Stage7b5b belegt den vorhandenen ChipRAM-Bereich bereits mit DOS-sicherem Loader,
RRB-Screen, Pixie-/NCM-Puffern, Sternbitmap, Palette und DAT-Originaldaten.
Insbesondere sind`$20000–$3FFFF` keine freigegebenen Datenbereiche und
`$60000–$FFFFF` im vorhandenen384-KB-Modell kein RAM. Die frühere VYSH-
Loaderkorrektur darf nicht durch eine vermeintlich freie Audio-Bank umgangen werden.
Die Original-Soundallokationen des Amiga-Dumps sind **keine** gültigen Zieladressen
für den MEGA65. Es wird hier keine unbekannte Lücke als frei deklariert.

**Empfehlung für einen späteren separaten Test:** komplette Rohsamples im
verfügbaren Attic-RAM als Archiv, kleine ChipRAM-Abspielpuffer oder ein begrenzter
Samplecache. Audio-DMA kann nicht aus Attic lesen. Als Größenordnung für Streaming:
zwei logische Quellen mit je zwei512-Byte-Hälften ergeben2048 Bytes ChipRAM;
alternativ größere Schleifenringe mit mehr Sicherheitsabstand. Das ist ein
Entwurfsbudget, **kein bereits bewiesener freier Speicherplatz**. Die tatsächliche
Allokation und der konfliktfreie Attic-Bereich sind vorher mit dem dann aktuellen
Engine-/Titel-/Menü-Layout zu prüfen. Keine Audioadresse wird jetzt reserviert.

Streaming muss den laufenden Bereich rechtzeitig aus Attic nachfüllen und bei
Original-PER, Stop, Preemption und Quellenwechsel sauber umschalten. Der bestehende
Audio-DMA-Endvergleich hat nur16 Bit; Einzel-Samples sind zwar sämtlich<64KB,
aber Puffer-/Loopgrenzen und Wrap müssen im Test ausdrücklich geprüft werden.
Das Audio-DMA besitzt kein Abschluss-IRQ: Stopflag/Adresse werden gepollt.
Einfaches50-Hz-Umschalten vollständiger Kurzsamples wäre nicht automatisch samplegenau.

## Bandbreite, CPU und50-Hz-Steuerung

Bei maximal11368,253Hz braucht eine Quelle≈228 Bytes je20ms.
Zwei Quellen brauchen≈22,74KB/s Nachfüllbandbreite; vier duplizierte Paula-
Hardwarekanäle lesen zusammen höchstens≈45,47KB/s. Gemeinsame Datenpuffer für
beide Stereoseiten verhindern eine Verdopplung des RAM-Bedarfs. Diese Zahlen sind
konservative Ratenobergrenzen, keine gemessenen Framelaufzeiten.

Das liegt deutlich unter der dokumentierten RAM-DMA-Bandbreite, beweist aber
keinen konfliktfreien RRB-/DMAgic-Betrieb. Audio-DMA stiehlt Buszyklen und benötigt
Full-Speed-Betrieb mit verfügbaren Idle-/Speicherlesezyklen. Der zuletzt beseitigte
CPU-Takt-/ROM-Mappingfehler darf nicht wieder eingeführt werden. Lange enge
Register-/NOP-Warteschleifen ohne geeignete Reads und lange andere DMA-Jobs sind
gezielt auf Audioaussetzer zu prüfen. Audio-DMA arbeitet auch während anderer
DMA-Aktivität weiter; die vorhandenen Animationen und Transfers müssen dabei
weiter ihre50-Hz-Frist einhalten.

Ein späterer API-Entwurf könnte lauten:

- `sound_init/restore`: DMA/Mixerzustand sichern und bei X/Exit wiederherstellen.
- `sound_request(event,type,pan_source)`: Original-ID bestimmen und originales
  Pending-/Busyverhalten anwenden; keine neue FIFO oder zufällige Ersatzsounds.
- `sound_tick_events`: Busyzähler/Pending und Stereo-Gains an den passenden
  logischen Originalticks pflegen. Die COPER-/Übergangsgates des Originals sind
  vom kontinuierlichen Streaming zu trennen.
- `sound_service_audio`: Streaming und Auto-Stop auch während Warte-/Rechteckphasen
  pflegen. Das darf nicht automatisch die während dieser Phasen im Original
  angehaltenen Busyzähler dekrementieren; sonst ändern sich spätere Zulassungen.
- `sound_stop_all`: Game-/Menü-/BASIC-Übergänge ohne Rest-DMA behandeln.

Eine spätere Datei `VYSO.DAT` könnte einen versionierten Header, die20 relevanten
Sampledeskriptoren, Original24-ID→Datensatz-Tabelle (vier unbenutzte IDs als ungültig),
38×4 Soundkennungen und unveränderte PCM-Bytes enthalten. Benötigt werden exakte
Längen, PER, Divisor, Busywert, Offsets und Integritätsprüfung. Noch **keine** solche
DAT wird erzeugt und der Loader nicht erweitert.

## Priorisierter Prüfplan vor jeder Engineintegration

1. Isolierter, separat beauftragter PCM-Test: ein belegtes Sample mit korrektem
   Signed-Modus/PER-Pitch, beide Ausgänge und sauberes X/BASIC/erneutes RUN.
2. Zwei gleichzeitige Quellen, Original-Lautstärkesummen und sich bewegendes
   Panning; Tests aller20 IDs sowie Vorab-Unterbrechung/Busy/letzter Pending-Schreiber.
3. Attic→ChipRAM-Streaming unter40MHz, Ringgrenzen, Audio-DMA-Ende/Loop und wechselnde
   Raten; Frame-/Rastermessung mit gleichzeitigem RRB, acht Projektilsprites,
   Sternen, Color-Cycling und konzentrischem Übergang.
4. WinUAE-/Amiga-Referenztrace: AUDxLC/LEN/PER/VOL, DMACON, INTREQ und Ereignis-
   zeitpunkte für Player, typabhängige Zerstörung und beide Übergangscues.
   Erst danach müssen eventuelle Filter-/Transientenabweichungen bewertet werden.

**Offen:** die endgültige Speicherkapazitätslösung, echter DMA-Bus-/Rasterbedarf,
Matrix-/Gainkalibrierung auf dem Zielcore, präzise native Busyzeit in Millisekunden
und Hörabnahme. Der vorliegende Auftrag liefert dafür Daten und Belege,
keine ungetestete Soundintegration in die stabile Engine.
