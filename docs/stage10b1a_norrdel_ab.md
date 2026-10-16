# Stage10b1a — NORRDEL-A/B-Test, festes Profil E

Issue91, separater Branch `stage10b1a-norrdel-ab`. Kein Gameplay-Build,
kein Produktivfix, kein Merge und keine Stable-Markierung.
Basis: Stage10b1-Diagnosecommit
`6fd56b3000d56c8c0a6d274d3076de72b62be523` (die maschinell festgehaltene
vollständige Basis-ID steht verbindlich in `releases/stage_10b1a/build.json`).
Die Quellen/Assets/Tools/Releases der bestätigten Stage10a1 und Stage10b1
bleiben unverändert. Die Grundlage ist der vom Benutzer gelieferte
[Hardwarevergleich aus PR90](stage10b1_user_hardware_findings.md).

## Zweck und isolierte Variable

Beide Varianten verwenden ausschließlich das bisherige **Profil E**:
H640, D054=55 (**PALEMU=0**), Stride192, Count96, CHRXSCL60, CHRYSCL1,
ScreenE000, Coloroffset0, Mono-Font4000 und dieselben Sprite-/RRB-Daten.
D07B bleibt25 wie in Stage10b1; keine gleichzeitige Änderung der Zeilenanzahl.
Ursprünge/Grenzen kommen wie bisher explizit aus dem gesicherten BASIC-Zustand.
Die Referenzszene bleibt240×200Playfield und80×200HUD mit16×8-Raster,
transparentem Original-Player-Pixie bei224,80, Hardware-Sprite bei112,112 und
1×4-Projektil bei232,64. Sprite-Umrechnung bleibt CHARX+2X−3 / CHARY+2Y.

| Variante | NORRDEL D051.7 | DBLRR D051.6 | expliziter Schreibwert |
|---|---|---|---|
| A / Taste1 | 1 | 0 | 9F |
| B / Taste2 | 0 | 0 | 1F |

Im Vergleich der stabilen VIC-IV-Konfigurationsbits darf nach Initialisierung
nur NORRDEL abweichen. Rasterpositionen, DMA-Historie und Phasenstart-Timing
sind Kontextdaten und werden separat ausgegeben. Die einzige absichtlich
variierende **Szenendatenstelle** ist das erste HUD-Zeichen: A/B bei physisch
E02C (Screenoffset44, Screencode1/2). Alle Zeilen, Pointer, Fonts, Sprites,
Pixies und Paletten sind identisch. Kein weiteres Sprite/Zeilen-Slot wird für
die Markierung eingefügt. Bei fehlendem HUD Fotos extern als A/B beschriften;
die Exportheader kennzeichnen die tatsächlich gewählte Variante unabhängig
von ihrer Sichtbarkeit.

## D051, IRQ und Restore: ausdrücklich keine blinde Read-modify-write-Folge

Verbindliche Corequelle:
[mega65-core aaf4542, viciv.vhdl](https://github.com/MEGA65/mega65-core/blob/aaf4542d02679271b5fb84ad933cc39bbe091c3f/src/vhdl/viciv.vhdl).

- Zeilen1894–1897: D051 liefert beim Lesen NORRDEL/DBLRR und in Bits0–5
  die **laufende Raster-X-Position**.
- Zeilen2661–2668: D050/D051 schreiben den X-IRQ-Komparator (D051 Bits0–5
  sind seine Bits8–13) und NORRDEL/DBLRR. Die unteren Readbackbits sind daher
  **keine Sicherung** des ursprünglichen Komparators.
- Zeilen721,970–971: Default-X-Komparator8191 (High1F), NORRDEL1, DBLRR0.
- Zeilen1738–1745 /3066: X-IRQ-Maske D01A.4 und zusätzliche IRQ-Freigabe.
  IRQ-Quelle/CHARY16 usw. liegen in D07A, nicht in NORRDEL.
- Zeilen3382–3409: DBLRR beeinflusst Fetch-Freigabe; NORRDEL beeinflusst
  die Rasterpuffer-Schreibhälfte. Dies ist ein plausibler Wirkmechanismus,
  noch kein Kausalitätsbeweis für den gemeldeten Fehler.

`apply_norrdel` schreibt **9F oder1F**, speichert denselben Wert in
`d051_shadow` und hält D01A.4 aus. D050 wird niemals geschrieben. Die
Komparator-Highbits bleiben damit in A und B identisch1F; DBLRR bleibt0.
Kein gelesener Raster-X-Wert wird als Schreibwert zurückgespiegelt.

**Startvoraussetzung: frisch gebootetes natives BASIC, PAL80×25, kein eigener
aktiver X-Raster-IRQ.** Bei D01A.4=1 bricht der Einstieg vor jeder D051- oder
IRQ-Maskenänderung per PLP/RTS nach BASIC ab. Der Test ist kein allgemeiner
Kontextsaver für fremde Grafik-/IRQ-Programme.

Die originale IRQ-Maske wird gesichert und wiederhergestellt; IRQ-Vektoren,
CIA-Masken und die IRQ-Quelle werden nicht für A/B umgeschaltet. `SEI`
umklammert Konfiguration, Szenenaufbau und Snapshots. Vor der eigentlichen
Videoinitialisierung wird im PAL-Blanking auf physische Raster>=528 gewartet;
DEN ist beim Aufbau aus. Jede Umschaltung restauriert zuerst den Ausgangs-
zustand und initialisiert Szene und Messpuffer vollständig neu.

Beim Export werden BASICs Videozustand, Paletten und Farben restauriert, IRQ
für KERNAL-Datei-I/O freigegeben und anschließend Diagnosemodus/Szene wieder
aufgebaut. Die ursprünglichen Messdaten werden dabei **nicht** durch neue
BASIC-/Exportdaten ersetzt. Beim X-Exit wird das Prozessorstatusbyte restauriert.

Restore von D051 verwendet `d051_restore_shadow` = gültige ursprüngliche
Steuerbits7/6 OR1F. **Grenze:** Ein zuvor individuell gesetzter, inaktiver
X-Komparator kann nicht vollständig zurückgelesen/restauriert werden. Seine
Highbits werden auf die dokumentierte1F-Schattensetzung zurückgeführt;
seine Lowbits bleiben unangetastet. Der Test behauptet keine unbekannte
Komparatorsicherung. Für den vorausgesetzten frisch gestarteten BASIC-
Kontext mit inaktivem X-IRQ ist dies sicher; aktive X-IRQ-Kontexte werden
abgelehnt. Auch ein eventuell latched X-IRQ wird nicht als fremder Interrupt
quittiert. D019-Latches und fremde IRQs werden nicht pauschal gelöscht.

HOTREG-Restore, D011-Komparatorbit-Rekonstruktion, alle vier Paletten und
vollständiges Color-RAM stammen aus der bewährten Diagnosebasis. Audio wird
nicht geschrieben. DMA-Trigger werden beim Exit nicht mit gelesenen Werten
zurückgeschrieben. D02F bleibt im vorausgesetzten nativen MEGA65-I/O-Modus.

## Bedienung und präzise Messfolge

Zielhardware: **MEGA65 Core0.97 aaf4542**. Ziel-XEMU:
**Release20260129235930**, keine gleichnamige Corekennung daraus ableiten.
Identische ROM V920413, PAL,80×25; ROM-SHA256 der bisherigen Vergleichsbasis:
`af3c447f791a2fdc48cb21e1bd3fab015e32641228d9d30d21259b9e878c6fa0`.
ROM nicht mitgeliefert. Für beide Systeme **dasselbe PRG/D81** mit gleichen
Hashes aus `SHA256SUMS.txt` verwenden, jeweils beschreibbare D81-Kopie.

1. Frisch booten, PAL80×25 kontrollieren, D81 als Laufwerk8 einlegen:
   `LOAD"STAGE10B1A",8`, `RUN`. Startvariante ist A.
2. Warten, bis die statische Szene vollständig aufgebaut ist. Foto/Screenshot
   als `MEGA65_A1` bzw. `XEMU_A1` sichern, möglichst **vor** dem Export.
   Fotozuordnung nicht allein aus dem Dateinamen des Exports ableiten.
3. Auf echter Hardware **H**, in XEMU **E** drücken. Es werden **zwei Dateien**
   geschrieben: Register und tatsächliche Speicherdaten. Grüner Außenrahmen
   bedeutet beide erfolgreich, rot mindestens ein Fehler. Bis zur Rückkehr
   der Szene warten; der Speicherexport ist deutlich größer als Stage10b1.
4. **2** wählen (B), fertigen Aufbau abwarten, Foto `..._B`, wieder H/E.
5. Für die Reproduzierbarkeit die A1-Dateien **vorher außerhalb des Images
   archivieren**, danach **1** wählen (A2), Foto und Export wiederholen.
   Derselbe Variantenname ersetzt die alte Diagnosedatei kontrolliert.
   Alternativ separate Laufkopien der D81 für A1/B/A2 verwenden und nach
   jedem Lauf extern sichern. Kopien eindeutig beschriften, PRG-Hash gleich.
6. **X** nach BASIC, `DIRECTORY`, erneutes `RUN` und Export testen.
7. D81-Kopien bzw. REG/MEM-Dateipaare und Fotos A1/B/A2 für beide Systeme
   zurückgeben, dazu Core-/Emulatorversion, ROM-Hash und ggf. Exportfehler.

| Variante / Exporttaste | Registerdatei | Speicherdatei |
|---|---|---|
| A / H | V1AAH.REG | V1AAH.MEM |
| B / H | V1ABH.REG | V1ABH.MEM |
| A / E | V1AAX.REG | V1AAX.MEM |
| B / E | V1ABX.REG | V1ABX.MEM |

Alle Dateien sind SEQ ohne PRG-Ladeadresse. H/X ist ein **manuell gewähltes
Label**, keine automatische Plattformprüfung. Tatsächliche Herkunft anhand
Testprotokoll und D81-Zuordnung festhalten. Ein versehentliches X-Label auf
Hardware macht die Messdaten nicht ungültig.

Export verwendet SETBNK0 vor SETNAM, Scratch nur des gewählten eigenen
Diagnosenamens, begrenzte DOS-Statusauswertung, CHKOUT/CHROUT/READST,
CLRCHN sowie korrektes MEGA65-CLOSE (Carry0 für Datenflush, Carry1 für
Statuskanal). Es gibt keine Spiel-/Highscoredateien und keine aktiven
fremden CHKIN-Phasen. Die Dateien sind nicht transaktional als Paar: Bei
Fehler beide vorhandenen Dateien prüfen und mit H/E erneut exportieren;
REG/MEM müssen Variante und Plattformlabel gemeinsam haben.

## Vier Registerphasen, versioniertes Format und Timingkontext

Neues Magic **VYDG1B1A**, Version1; das bisherige Format VYDG10B1 und dessen
Parser werden **nicht** geändert. Header32Bytes, vier Blöcke à490Bytes,
insgesamt1992Bytes. Adressliste und Masken in `registers.json`.

1. Nach I/O-Unlock/Sicherung vor eigener Videoinitialisierung.
2. Nach festem Profil E und explizitem A/B-D051-Schreiben.
3. Nach identischer Titel-/Menügeometrie-Simulation, Restore und erneuter
   Initialisierung derselben Variante (kein Loader, keine Audioausführung).
4. Nach Szene/DEN/Spritefreigabe und Speicherrücklesung.

Header wie im alten Format aufgebaut: Bytes8Version,9Variante A/B,
10Umgebungslabel U/H/X,11Phasenzahl,12–13Registerzahl162,
14–15Blocklänge490,16–19Gesamtlänge,20–27reserviert0,
28–29Sum16 modulo65536 ohne diese zwei Bytes,30Algorithmus1,
31I/O-Unlock-Flag1. Multibytewerte little endian.

Jeder Block beginnt mit Phase, Variante, **D012-Phasenstartwert**,
**D011-Phasenstartwert**, danach162Records aus AdresseLE16/Wert8.
Der neue Parser erhält die vier Timingbytepaare in `phase_context` und gibt
Abweichungen als `phase_context_differences` aus. Sie werden nicht mehr
verworfen. Sequenzielle Registeraufnahmen sind keine atomaren Rasterzustände.

Der Vergleich prüft tatsächlich gemessenes NORRDEL und DBLRR, PALEMU,
Geometrie-/Speicherpointer und X-IRQ-Maske in den Phasen2–4.
`unexpected_stable_differences` enthält alle unerwarteten stabilen
Abweichungen; nur bei A/B und nur ab Phase2 ist D051.7 der erwartete
Registerunterschied. Der rohe Unterschied bleibt trotzdem sichtbar.
Status-/Timingbits und Kontextfelder werden nicht stillschweigend gelöscht.

## Tatsächliche Speicher-Rücklesedaten

Neue Begleitdatei **VYMM1B1A**, Version1, **36292Bytes**. Das ist keine Kopie
bloß der Buildvorlagen: Neun physische Bereiche werden nach dem Szenenaufbau
per F018A-DMA in einen separaten Puffer kopiert, anschließend mit Sum16 über
Header, Verzeichnis und Rohbytes geprüft. Der Export streamt diese eingefrorene
Rückkopie in256Byte-Blöcken über einen privaten CPU-Puffer. Kein CPU-Read
über den ROM-Alias E000, kein MAP über KERNAL-Code und kein Attic-Audio.

| Region | Tatsächliche Quelladresse | Bytes | Dateioffset |
|---|---|---|---|
| screen | E000 | 4800 | 256 |
| colour | FF80000 | 4800 | 5056 |
| font | 4000 | 2048 | 9856 |
| grid | 18000 | 24000 | 11904 |
| pixie | 9040 | 128 | 35904 |
| sprites | 9200 | 128 | 36032 |
| pointers | 9300 | 4 | 36160 |
| guards | 8000 | 64 | 36164 |
| guard2 | 90C0 | 64 | 36228 |

256Byte-Header einschließlich Verzeichnis: Magic0–7, Version8, Variante9,
Label10, Regionzahl9 bei11, Recordgröße16LE bei12, Headergröße256LE bei14,
GesamtlängeLE32 bei16, reserviert20–27, Sum16 bei28–29,
Algorithmus1 bei30, Capturephase4 bei31. Ab32 je16Bytes:
`QuelladresseLE32, DateioffsetLE32, LängeLE32, FlagsLE16=0, ReserviertLE16=0`.
Unbenutzte Headerbytes sind0. Sum16 umfasst alle Bytes außer28/29.
Der Hostparser prüft jede Adresse/Position/Länge gegen das Schema und erzeugt
zusätzlich SHA256 pro Region. Sum16 ist keine kryptografische Integritätsgarantie.

Capture ist sequenziell bei statischer Szene und SEI, kein atomarer GPU-Frame-
Snapshot. DMA-Rücklesen wird lokal gegen live gelesene RAM-Inhalte verifiziert;
echte Hardware-/Bus-/FIFO-Daten können erst aus Nutzermessungen beurteilt
werden. Tatsächliche Farbpalettenregister sind nicht Teil der MEM-Datei;
Profil-E-Palette wird wie zuvor konstant initialisiert und beim Exit gesichert.

## Vergleich ohne zusätzliches Disktool

Beispiel A Hardware gegen A XEMU, einschließlich tatsächlicher Speicherbytes:

```sh
python3 tools/analysis/compare_stage10b1a.py MEGA65.d81 XEMU.d81 \
  --left-reg-file V1AAH.REG --right-reg-file V1AAX.REG \
  --left-mem-file V1AAH.MEM --right-mem-file V1AAX.MEM \
  --json vergleich_A.json
```

Für B entsprechend V1ABH/V1ABX. A gegen B desselben Systems:

```sh
python3 tools/analysis/compare_stage10b1a.py MEGA65.d81 MEGA65.d81 \
  --left-reg-file V1AAH.REG --right-reg-file V1ABH.REG \
  --left-mem-file V1AAH.MEM --right-mem-file V1ABH.MEM \
  --json vergleich_AB.json
```

Bereits extrahierte Dateien: REG-Dateien positional, MEM-Dateien mit
`--left-memory datei.MEM --right-memory datei.MEM` übergeben. Ein einzelnes
REG/MEM-Paar validiert nur diesen Lauf. Die Programme akzeptieren abweichende
H/X-Dateinamen ausdrücklich per Argument, wenn die Herkunft separat bekannt ist.

Die Ausgabe enthält SHA256 und Anzahl abweichender Bytes pro Region sowie
die ersten64 Rohabweichungen mit physischer Adresse. Nur Screenbyte44 ist
beim A/B-Vergleich als deklarierter Variantenmarker ausgenommen. Zwischen
gleichen Varianten auf zwei Plattformen wird **kein** Speicherbyte ausgenommen.
Ein passender Registerdump ohne zugehörigen gültigen Speicherdump ist keine
vollständige Messung. Die Bilder sind zusätzliche Belege, kein Datenersatz.

## Speicherkarte und Fallback ohne funktionierendes HUD

| Physischer Bereich | Verwendung |
|---|---|
| 2100–unter4000 | isolierter Controller, DMA, Snapshot-/Exportcode |
| 4000–47FF | unveränderter Original-Menüfont |
| 4800–4FC7 |1992Byte-Registerdump, bleibt nach X erhalten |
| 5000–50FF | privater256Byte-DMA-Streamingcache |
| 5100–51FF | Speicherheader/-verzeichnis, bleibt nach X erhalten |
| 6000–6BFF | alle vier gesicherten RGB-Paletten |
| 8000,8800,9040,90C0,9200,9300 | gleiche Guards/Atlas/Pixie/Sprites/Pointer wie Stage10b1 |
| A000–B2BF / B300–C5BF | Screen-/Color-Buildvorlagen |
| E000–F2BF | tatsächlicher RRB-Screen, physischer DMA-Zugriff |
| 18000–1DDBF | tatsächliche375Rasterglyphen |
| 40000–47FFF | Sicherung kompletter32KiB-Color-RAM für BASIC |
| 50000–58DC3 | eingefrorener36292Byte-Speicherdump |
| FF80000–FF87FFF | physisches Color-RAM |

20000–3FFFF bleibt ROM, kein Puffer. PRG endet vor D000.
Kein produktiver Speicherbereich oder Stable-Artefakt wird verändert.

Bei defekter Anzeige trotzdem1/2 und H/E bedienen. `io_status` und
`export_error` aus `stage10b1a.sym` liefern Fehlerstatus, `dos_code` den letzten
DOS-Code. Exportfehler führen zur Szene zurück, X bleibt wirksam.

UART-Monitor-Fallback: Registerbank0 **4800–4FC7**, Speicherpuffer physisch
**50000–58DC3** (jeweils inklusive). Rohbytes mit diesen exakten Längen
exportieren. Den üblichen `M`-Monitor-Text versteht der REG-Loader wie bisher;
für MEM die36292Bytes als rohe Binärdatei sichern. Dies erfordert keinen
lesbaren VIC-Bildschirm und keinen funktionierenden Diskexport.

Nach X kann BASIC zumindest den Registerdump retten:

```basic
BANK 0
OPEN 2,8,2,"0:FALLBACK.REG,S,W"
FOR I=18432 TO 20423:PRINT#2,CHR$(PEEK(I));:NEXT I
CLOSE 2
```

Datei vorher nicht vorhanden, DOS-Status prüfen. Für die Speicherdatei gilt
analog `BANK 5`, PEEK-Adressen0 bis36291, eigener Name `FALLBACK.MEM`;
anschließend `BANK 0` wiederherstellen. Diese Bereiche bleiben nach X
bestehen, bis neue Programme/Ladevorgänge sie überschreiben. Headerlabel U
ist bei Monitor-/BASIC-Rettung zulässig; nicht manuell ohne neue Prüfsumme
ändern. Beide Dateitypen enthalten keine PRG-Ladeadresse.

## Reproduzierbarer Build und tatsächlich geprüfte Ergebnisse

Python3-Standardbibliothek und Java mit offiziellem KickAssembler5.25;
JAR-Hash wird wie in der bestehenden Toolchain geprüft. Kein Download nötig:

```sh
python3 tools/build_stage10b1a.py --kickass /pfad/zu/KickAss.jar
python3 tools/build_stage10b1a.py --kickass /pfad/zu/KickAss.jar --output /tmp/10b1a-repeat
(cd releases/stage_10b1a && sha256sum -c SHA256SUMS.txt)
python3 tools/test_stage10b1a.py
```

Der letzte Test benötigt zusätzlich **py65==1.2.0**; in dieser Umgebung
bereits vorhanden unter `/workspace/stage3b-inspection/test-deps`, geprüft mit
`PYTHONPATH=/workspace/stage3b-inspection/test-deps python3 tools/test_stage10b1a.py`.
Build und Vergleich benötigen py65 nicht. Die kurzen reinen6502-Subroutinen
werden dabei als assemblierter Maschinencode ausgeführt; dies ist ausdrücklich
keine Emulation der MEGA65-DMA oder der VIC-IV-Hardware.

| Prüfung | Ergebnis |
|---|---|
| KickAssembler5.25 / Speicher-Assertion | bestanden; PRG42433Bytes |
| D81/BAM/Dateiketten/Inhalt | bestanden; D81819200Bytes |
| unabhängiger Wiederholungsbuild | alle Release-Dateien byteidentisch |
| neun Hosttests | bestanden:9F/1F, festes Profil E, aktiverX-IRQ-Guard, Shadow-Restore, Timingkontext, Versions-/Registerintegrität, Speicherverzeichnis/-korruption, Markergrenze, Disk-/Hashes |
| ergänzendes lokales XEMU A→B→A | gültige vier Phasen je Variante, NORRDEL/DBLRR geprüft, keine unerwartete stabile Registerabweichung |
| Rücklesung / Export | alle9MEM-Regionen gegen liveRAM identisch; REG/MEM-SEQ-Dateien gegen RAM identisch |
| A/B-Speichervergleich | nur der deklarierte Screenmarker unterschiedlich |
| A2-Reproduktion | keine unerwarteten stabilen Register-/Speicherabweichungen zu A1 |
| Exit / erneutes RUN / erneuter Export | vollständiges Color-RAM-/Palettenrestore; D051-Steuerbits restauriert; gültiger neuer Dump und DOS00 |
| Exportfehler | im Emulator Gerätenummer31 injiziert, roter Status, Szene und X weiterhin erreichbar |
| echter MEGA65 / Ziel-XEMU-Release | **noch nicht geprüft**, Nutzervergleich erforderlich |

Lokale XEMU-Referenz wie bisher Commit
`40dfef0d1d5f56be2469492715c12bdb32c75b67` mit dem dokumentierten
`tools/diagnostics/stage10a1_xemu_trace.patch` für Headless-/Tastatureingaben
und Trace, **nicht** die angefragte Release-Binärdatei. UART-Pausen verfälschen
Zeit-/Rastermessungen; keine visuelle Hardwareabnahme, physische Joystickprüfung
oder Behauptung gleicher Renderbilder. Die Speicher-/Exportdaten sind unter
`docs/diagnostics/stage10b1a/` abgelegt, Testtreiber
`tools/check_stage10b1a_xemu.py`. Dessen A/B-Vergleich erlaubt NORRDEL als
einzigen erwarteten stabilen Registerunterschied und den einen Screenmarker.

## Entscheidung erst nach Nutzermessungen

- B korrekt, A fehlerhaft bei gleicher sonstiger Konfiguration und gleichen
  Speicherbytes: starke Evidenz für NORRDEL; dann minimalen Stage10b2-Fix
  separat beauftragen und prüfen.
- Beide fehlerhaft: Speicherabweichungen und RRB-Zeilenbudget untersuchen;
  DBLRR gegebenenfalls später **getrennt** testen.
- Beide korrekt oder inkonsistent: Wiederholung A→B→A, Start-/Timing-/IRQ-
  Abhängigkeit isolieren; keine voreilige Fehlerursache behaupten.

Stage10a1 und Stage10b1 bleiben unverändert. Kein Stage10b2-Fix in diesem PR.
