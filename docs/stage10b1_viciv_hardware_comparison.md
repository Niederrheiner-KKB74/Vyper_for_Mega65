# Stage10b1 — isolierter VIC-IV-/RRB-Hardwarevergleich (Issue89)

Entwicklungsstand, **nicht Stable**, kein produktiver Fix und kein Mergeauftrag.
Referenz ist die vom Benutzer bestätigte Stage10a1, Mergecommit
`08e0272319ead24f2f189b9391aec56712d54569` aus PR88.
Alle bestehenden Quellen, Assets, Tools und Releases dieser Referenz bleiben
bytegleich. Der Diagnose-Build importiert keine Spielengine und schreibt weder
Highscores noch Audio-, CIA-, IRQ-Masken oder HWERRATA-Register.

## Startbedingungen und Beleggrenzen

Der Benutzer bestätigte: identische ROM-Datei wie XEMU, **PAL, BASIC80×25**.
Zielhardware: MEGA65 Core Release0.97, Build `aaf4542`.
Ziel-XEMU: Release `20260129235930`; dies ist **keine Core-Versionskennung**.
ROM-Referenz: V920413, SHA256
`af3c447f791a2fdc48cb21e1bd3fab015e32641228d9d30d21259b9e878c6fa0`.
Die ROM wird nicht mitgeliefert. Vor dem Vergleich denselben ROM-Hash prüfen.

Hier ist kein echter MEGA65 verfügbar. Auch die exakte angefragte XEMU-Version
stand lokal nicht zur Verfügung. Die ergänzende automatisierte Laufzeitprüfung
verwendet XEMU-Quellcommit `40dfef0d1d5f56be2469492715c12bdb32c75b67`
mit dem bereits dokumentierten Headless-/Tastatur-/Trace-Patch
`tools/diagnostics/stage10a1_xemu_trace.patch`.
Sie prüft Speicher und Dateiverwaltung, **nicht** die visuelle Übereinstimmung,
Hardwarekompatibilität oder Rasterzeiten. Hardware- und Ziel-XEMU-Dumps werden
vom Benutzer benötigt, bevor sich eine Ursache oder ein Stage10b2-Fix ableiten
lässt. Keine nachgewiesene Core-/XEMU-Inkompatibilität wird vorausgesetzt.

## Reproduzierbarer Build

Python3 (Standardbibliothek), Java und offizieller KickAssembler5.25 genügen.
Keine Downloads oder Neuinstallation während des Builds:

```sh
python3 tools/build_stage10b1.py --kickass /pfad/zu/KickAss.jar
python3 tools/build_stage10b1.py --kickass /pfad/zu/KickAss.jar --output /tmp/stage10b1-repeat
cmp releases/stage_10b1/STAGE10B1.PRG /tmp/stage10b1-repeat/STAGE10B1.PRG
cmp releases/stage_10b1/VYPER_STAGE10B1.d81 /tmp/stage10b1-repeat/VYPER_STAGE10B1.d81
(cd releases/stage_10b1 && sha256sum -c SHA256SUMS.txt)
python3 tools/test_stage10b1.py
```

Quellcode: `src/tests/stage10b1.asm`; Builder: `tools/build_stage10b1.py`.
Der Builder erzeugt die Referenzraster und Kontrollspritemuster, verwendet den
unveränderten Original-Player-NCM-Pixie und den bestätigten Menüfont aus den
vorhandenen Assets. Der Player dient hier allein als transparenter RRB-Pixie.
Keine neuen Gegnerdaten, Spiel- oder Audiodaten werden benötigt.
Auslieferung unter `releases/stage_10b1/`, D81 mit einem autoloadbaren PRG
`STAGE10B1` (819200Bytes D81). Generierte Include-Dateien und Binärvorlagen
liegen für den direkten KickAssembler-Aufruf ebenfalls im Release.

## Bedienung und genaue Vergleichsanleitung

1. Zwei **beschreibbare Kopien derselben ausgelieferten D81** erstellen.
   Eine für den echten MEGA65, eine für die genannte XEMU-Version. Ausgangs-Hash
   mit `SHA256SUMS.txt` vergleichen; nach dem Export ändern sich die Kopien.
2. Auf beiden Systemen frisch booten, dieselbe ROM, PAL und BASIC80×25.
   Hardware-Corebuild und XEMU-Release separat anhand der Systemanzeige notieren.
   Keine vorgeschalteten Programme oder Moduswechsel verwenden.
3. D81 als Laufwerk8 einlegen, `LOAD"STAGE10B1",8`, dann `RUN`.
   Standard ist Profil **1 / S**. Nicht die stabile Spiel-D81 überschreiben.
4. Referenzszene fotografieren bzw. in XEMU einen Screenshot erstellen.
   Besonders links/rechts, rote Grenze am HUD, weiße obere/untere Kante,
   transparentes Schiff, beide Hardware-Sprites und Rasterabstände beachten.
5. Auf dem MEGA65 **H**, in XEMU **E** drücken. Der Export stellt kurz BASICs
   Videomodus wieder her, schreibt die Datei und baut die Szene erneut auf.
   Die vier ursprünglichen Snapshots bleiben dabei erhalten.
   Grüner Außenrahmen: Export erfolgreich; rot: Fehler. Bei unlesbarem Bild
   trotzdem dieselbe Taste drücken und die Datei bzw. den RAM-Puffer auswerten.
6. **2** wählt Profil **E** (explizit), nimmt vier neue Snapshots auf und baut
   die Szene neu auf. Wieder Foto und Export mit H bzw. E. **1** kehrt zu S
   zurück. Die Profile sind im Dateiheader unterscheidbar, auch ohne Bild.
7. **X** beendet beide Profile sauber. BASIC muss wieder bedienbar sein;
   `DIRECTORY`, erneutes `RUN`, Profilwechsel und erneuten Export testen.
   Eine volle/schreibgeschützte Testkopie darf beim Export einen roten Rahmen,
   aber keinen Absturz erzeugen. Fehlerstatus liegt zusätzlich bei `io_status`
   (Adresse aus `stage10b1.sym`), DOS-Code als zwei ASCII-Ziffern bei `dos_code`.
8. Beide D81-Kopien, vier Fotos/Screenshots, ROM-Hash und bestätigte Versionen
   zurückgeben. Vor einer Hardwareursache zuerst die Dateien vergleichen.

| Profil | Hardwaredatei (H) | XEMU-Datei (E) |
|---|---|---|
| 1 / S, Stage10a1-Masken | `V10BSH.DAT` | `V10BSX.DAT` |
| 2 / E, expliziter Vergleich | `V10BEH.DAT` | `V10BEX.DAT` |

Die Dateien sind SEQ, ohne PRG-Ladeadresse. Ein erneuter Export ersetzt nur
die jeweils gewählte Diagnosedatei. MEGA65-DOS meldete beim getesteten ROM für
`@0:`-Replace Fehler63; deshalb verwendet der finale Build die in der
Highscore-Verwaltung bewährte Folge `S0:V10Bxx.DAT`, Statusprüfung und neues
SEQ-Schreiben. Scratch-Ergebnisse00/01/62 werden als Erfolg bzw. noch nicht
vorhandene Datei akzeptiert; andere Fehler brechen den Export kontrolliert ab.
Alte Dumps vorher sichern. Keine Originalspieldateien werden gelöscht.

### Vergleich direkt aus D81 (kein weiteres Disktool nötig)

```sh
python3 tools/analysis/compare_stage10b1_registers.py hardware.d81 xemu.d81 \
  --left-file V10BSH.DAT --right-file V10BSX.DAT --json vergleich-stage.json
python3 tools/analysis/compare_stage10b1_registers.py hardware.d81 xemu.d81 \
  --left-file V10BEH.DAT --right-file V10BEX.DAT --json vergleich-explicit.json
```

Alternativ bereits extrahierte SEQ-Dateien übergeben. Nur eine Datei prüft
Format/Prüfsumme und gibt die aus jedem Snapshot abgeleitete Geometrie aus.
Der Vergleich erhält **alle rohen Unterschiede**, markiert aber zusätzlich,
ob nach Vergleichsmaske stabile Bits betroffen sind. Ein einzelner roher
Raster-/IRQ-/DMA-Historienunterschied ist kein Geometrienachweis.
Bei verschiedenen Profilen meldet er `same_profile:false`; das ist ein
Profilvergleich und kein gleichartiger Hardwarevergleich.

### Fallback bei unlesbarem Bildschirm / gescheitertem Dateiexport

Diagnosedaten liegen in Bank0 bei **$4800–$4FC7**, 1992Bytes; exklusives Ende
$4FC8. Nach X bleiben sie erhalten, bis ein anderes Programm sie überschreibt.
Im UART-Monitor die acht 256Byte-Blöcke `M4800`, `M4900`, …, `M4F00`
lesen und die Ausgabe in einer Textdatei sichern. Das Vergleichsskript versteht
Zeilen wie `:00004800:56594447...` automatisch und entfernt das abschließende
Padding anhand der Headerlänge. Alternativ exakt1992 rohe Bytes exportieren.

Nach X ist auch ein BASIC-SEQ-Export möglich (keine PRG-Ladeadresse hinzufügen):

```basic
BANK 0
OPEN 2,8,2,"0:V10BF.DAT,S,W"
FOR I=18432 TO 20423:PRINT#2,CHR$(PEEK(I));:NEXT I
CLOSE 2
```

Einen noch nicht vorhandenen Namen verwenden; DOS-Fehlerkanal kontrollieren.
Diese Alternative setzt ein funktionierendes BASIC/DOS voraus. Der reine
RAM-/Monitorweg braucht keine lesbare VIC-Anzeige und keinen Diskexport.
Der Header enthält ggf. weiterhin `U` (Umgebung unbekannt); nicht manuell
ändern, sonst stimmt die Prüfsumme nicht. Begleitnotiz ordnet den Dump zu.

## Statische Befunde aus Stage10a1

Relevante Quellen: `src/engine/stage10a1.asm` (Einstieg, Save/Restore),
`stage10a1_hud.asm` (`hud_init`), `stage10a1_shots.asm` (Koordinaten),
`stage10a1_title.asm` (`title_show`, `title_restore_video`),
`stage10a1_menu.asm` (Menügeometrie).

| Feld | Tatsächliche Stage10a1-Behandlung / Diagnose S |
|---|---|
| I/O-Key $D02F | $47/$53, MEGA65-I/O vor erweiterten Registerzugriffen |
| $D030 | ursprünglicher Wert OR$05; Palettezugriff mit CRAM2K aus |
| $D031 | HUD: gesicherter Wert AND$5F OR$C0; H640 und FAST gesetzt |
| $D054 | OR$45 für CHR16/FCLRHI/VFAST, Spritepfad zusätzlich OR$10 |
| $D058/$D059 | 192Bytes Vorschub; 96 Zwei-Byte-Wörter pro Zeile |
| $D05E/$D063 | 96 Einträge; Count-Highbits gelöscht, andere $D063-Bits teils geerbt |
| $D05A | 60; H640 =>0,5 Quellpixel pro nativem Pixel |
| $D05B | Engine erbt vertikale Skalierung aus Start-/Restorezustand |
| $D048–$D04F | Grenzen/Ursprünge überwiegend geerbt; Sprite-Tiling-Highnibbles aus |
| $D051 | RRB-Delay-/Doublebuffer-Steuerbits nicht pauschal neu gesetzt |
| $D05D | HOTREG aus, bevor eigene Geometrie geschrieben wird |
| $D060–$D065 | Screen physisch $E000, Color-RAM-Offset0 |
| $D068–$D06A | Mono-Zeichensatz $4000; NCM nutzt Glyphnummer×64 |
| $D06C–$D06E | 16Bit-Spritepointer; Diagnose eigene Tabelle $9300 |
| $D070 | $9A: Anzeigebank1, Spritebank2, gemappte Bank2, alternative Bank2 |
| $D076/$D054.4 | Sprite-V400-Koordinaten und Sprite-H640 gesetzt |
| $D07B | 25 wie Referenz; Kerneldokumentation nennt einen letzten Zeilenindex |

**Gesicherter Befund:** Mehrere relevante Geometrie-/Modusbits werden geerbt.
Das beweist keine Fehlinitialisierung auf echter Hardware. $D07B=25 bei25
gebauten RRB-Zeilen ist eine prüfbare Grenzfrage (letzter Index wäre24), wird
hier **nicht produktiv geändert**. Beide Profile behalten25; der Rahmen liegt
nur in den25 vorgesehenen Zeilen. Kein Off-by-one-Fix wird vorweggenommen.

Profil S übernimmt die finalen relevanten Engine-/HUD-/Sprite-Masken. Der
Testpixie, Mono-Testsprites, Pointer und Palettenbelegung sind bewusst
isolierte Messdaten, keine bitidentische Szene des Spiels.
Profil E normalisiert $D031=$C0, $D054=$55, $D063=0, $D05B=1 und
CHARY16 aus. Seitenrand und $D05D.6 kommen explizit aus dem Startzustand;
HOTREG bleibt aus. $D051 wird nur gemessen: Seine unteren Schreibbits
gehören zu einem nicht direkt lesbaren X-IRQ-Komparator, der hier nicht
verändert werden soll. Die sichtbaren Ursprünge/
Grenzen werden explizit aus dem gesicherten BASIC-Startzustand geschrieben;
es wird **keine frei verschobene zweite Geometrie erfunden**.
H640/Skalierung, Screen, Stride, Count, $D07B, Spritepositionen und Rasterdaten
bleiben dieselben. PAL/NTSC/VGA-Timing und Ausgangs-/Shadowmasken werden in
beiden Profilen geerbt und mitgemessen. E ist ein gezieltes Normalisierungs-
experiment, kein Vorschlag, alle Register blind zu überschreiben.

Die Modewechsel-Simulation schreibt ausschließlich Titel- und Menügeometrie:
Titel H320/44Spalten/88Bytes/30Zeilen, Scale120, YScale1, CHARX/Y48,
Top48/Bottom528; Menü40Spalten/80Bytes/25Zeilen, CHARX80/CHARY88,
Top88/Bottom488. Danach wie in der Referenz zuerst Legacy/HOTREG-Updates
abarbeiten, präzise Ausgangsgeometrie wiederherstellen und Spielprofil erneut
initialisieren. **Keine echte Loader-/Overlay-/Audioausführung** wird simuliert.
Abweichungen, die nur beim vollständigen produktiven Laden entstehen, kann
Stage10b1 allein daher nicht ausschließen.

## Geometrie und Referenzszene

25 RRB-Zeilen à192Bytes. Jede NCM-Zelle enthält16×8 Quellpixel.
Prefix: GOTOX0 und15 Rasterglyphen; HUD beginnt bei Byte42 mit GOTOX480 und
20 Monozeichen; dynamischer Pixie-Slot ab Byte84; Guards bis Byte191.
Der statische transparente Original-Player-Pixie sitzt bei (224,80), reicht
bis(239,95) und darf das HUD nicht übermalen. Die sichtbare Außenkante ist
weiß, die letzte Playfieldspalte rot; blaues16×8-Raster.

| Größe | Erwartung bei H640 / CHRXSCL60 / CHRYSCL1 |
|---|---|
| Playfield | logisch X0–239, Y0–199; nativ Breite480, Höhe400 |
| HUD | logisch X240–319; GOTOX480, native Breite160 |
| RRB-Pixie | logisch224,80; native relative Position448,160 |
| Sprite0-Anker | logisch112,112; nativ CHARX+221, CHARY+224 |
| Sprite1-Projektil-Anker | logisch232,64; nativ CHARX+461, CHARY+128 |
| Sprite0-Bild | 16native Pixel×16physische Raster =8×8logische Pixel |
| Projektilbild | 2native Pixel×8physische Raster =1×4logische Pixel |

Die Sprite-Anker verwenden bewusst den historischen Engine-Offset −3, damit
sich eine falsche Sprite-/RRB-Relation messen lässt; sie sind nicht mit der
linken sichtbaren Quellpixelkante gleichzusetzen. X-Bits8/9 und Y-Bits8/9
werden aus den addierten Ursprüngen in $D010/$D05F/$D077/$D078 gesetzt.
Die Vergleichssoftware leitet H640, Skalierung, Stride, Count, Ursprung,
Screen-/Color-RAM aus den **gemessenen** Werten ab; die Szenengrenzen sind
Layoutangaben und keine Behauptung, dass Hardware sie so darstellt.

## Snapshotformat und Registerliste

`registers.json` enthält die vollständige, geordnete Adressliste mit Namen und
Vergleichsmasken; dieselben Adressen werden im ASM generiert.
162Register je Snapshot: $D000–$D07F außer $D01E/$D01F (read-to-clear
Kollisionslatches) und $D02F (I/O-Key), dazu $D08F, $D700–$D70F,
$D71C/$D720/$D740, $DD00/$DD02/$DC0E/$DC0F sowie $D629–$D635.
Keine CIA-ICR-Lesezugriffe, keine Registerschreibzugriffe für Identifikation.
Raw-Firmwarebytes sind mit enthalten; sie werden **nicht** ohne belegte
Dekodierung als Core-/XEMU-Version bezeichnet. H/X im Header ist die vom
Benutzer per Taste angegebene Umgebung, keine automatische Erkennung.

Vier Phasen:

1. Nach notwendigem MEGA65-I/O-Unlock, **vor** erster eigener Videokonfiguration.
2. Nach Video-/HUD-/Sprite-Koordinateninitialisierung; Szene noch nicht aktiv.
3. Nach simuliertem Titel/Menü→Restore→Spielprofil-Wechsel.
4. Nach DMA-Aufbau der Referenzszene, Spritefreigabe und DEN ein.

Registerlesungen sind sequenziell, **kein atomarer Raster-Snapshot**.
Raster-Latches und rohe DMA-Historie sind kontextabhängig. $D011.7,
$D012/13/14/19, Rasterbits in $D050–53 und Debugfelder werden entsprechend
maskiert bzw. nur roh verglichen. Der Vergleich setzt unbekannte Unterschiede
nicht mit Fehlern gleich. Auch stabile Bits können systembedingt abweichen;
ihre Markierung ist ein Untersuchungsauftrag, keine Fehlerklassifikation.

| Headeroffset | Inhalt |
|---|---|
| 0–7 | ASCII `VYDG10B1` |
| 8 | Formatversion1 |
| 9 | S oder E (Profil) |
| 10 | U unbekannt, H Hardware, X XEMU (Benutzerangabe) |
| 11 | 4Phasen |
| 12–13 | 162 Register, WORD LE |
| 14–15 | 490Bytes je Phase, WORD LE |
| 16–19 | 1992Bytes Gesamtlänge, DWORD LE |
| 20–27 | reserviert0; keine erfundene Versionskennung |
| 28–29 | Summe aller Bytes außer diesen beiden, modulo65536, WORD LE |
| 30 | Prüfsummenalgorithmus1 |
| 31 | Flag1: I/O-Unlock vor erster Aufnahme |

Jeder490Byte-Phasenblock: Phasennummer1–4, Profil, $D012-Zeitmarke,
$D011-Zeitmarke; danach162Records `[Adresse low, Adresse high, Wert]`.
Der Parser prüft Größe, Magic, Version, Flags, Profil, Phasenfolge,
Registeradressen und Prüfsumme; ein abgeschnittener Dump wird abgewiesen.

## Speicher und Restore

| Physischer Bereich | Verwendung |
|---|---|
| $2001–$200C | BASIC SYS8448 |
| $2100–unter$4000 | Controller, Snapshot-/Exportcode, DMA-Liste, Zustände |
| $4000–$47FF | unveränderter Menüfont |
| $4800–$4FC7 | vier Snapshots mit Header; bleibt nach X erhalten |
| $6000–$6BFF | alle vier RGB-Paletten, 4×768Bytes |
| $8000–$803F/$90C0–$90FF | transparente NCM-Guards |
| $8800–$8BFF | 16Rastermuster à64Bytes |
| $9040–$90BF | Original-Player-NCM, zwei16×8Glyphen |
| $9200–$927F/$9300 | Mono-Spritemuster / 16Bit-Pointertabelle |
| $A000–$B2BF/$B300–$C5BF | Screen-/Color-Vorlagen, je4800Bytes |
| $E000–$F2BF | physischer RRB-Screen, nur DMA-Zugriffe |
| $18000–$1DDBF | 375NCM-Rasterglyphen, genau24000Bytes |
| $40000–$47FFF | Sicherung aller32768Bytes Color-RAM |
| $FF80000–$FF87FFF | physisches Color-RAM |

$20000–$3FFFF ist ROM und wird nicht als freier Puffer benutzt. PRG endet
vor $D000. Physisches $E000 wird ausschließlich per DMA aufgebaut, damit
keine CPU-/KERNAL-ROM-Aliase verwendet werden. DMA ist synchron; es läuft
keine Hintergrund-DMA und kein Audio. Die Steuerlisten werden nie in den
RRB-/Glyphbereich geschrieben. CPU-Zeropage wird nicht als Zeiger benutzt.

X stellt alle vier Paletten, das vollständige Color-RAM und alle im Test
beschriebenen VIC-Register wieder her. HOTREG/Legacy-Updates werden zuerst
abgearbeitet, dann präzise Felder restauriert und HOTREG zuletzt gesetzt.
$D011.7 wird aus dem gesicherten Rasterkomparator statt aus dem gelesenen
Live-Rasterbit rekonstruiert. Originales Prozessorstatusbyte wird per PLP
restauriert; IRQ-Vektoren/-masken, CIA und Audio bleiben unverändert.
DMA-Trigger/Historienregister werden nicht zurückgeschrieben (ein Schreibzugriff
auf $D705 würde erneut DMA starten). D02F hat keinen verlässlichen Readback:
MEGA65-I/O wird für das vorausgesetzte native BASIC aktiviert belassen; eine
beliebige vorherige C64-I/O-Betriebsart ist nicht Teil dieses PAL80×25-Tests.
Keine KERNAL-I/O bei aktivem fremdem CHKIN; CLRCHN/CLOSE und SETBNK0 vor
SETNAM sind ausdrücklich vorhanden. CLOSE2 mit Carry0 flush't DOS-Daten,
CLOSE15 mit Carry1 zieht nur den logischen Statuskanal zurück. DOS-Antworten
beim Scratch werden mit maximal80Zeichen bis CR eingelesen.

## Verbindliche Referenzen und nachprüfbare Befunde

Primärquelle ist der **exakt gepinnte Core0.97-Code**, nicht eine aktuelle
Dokumentation als angeblich historische Spezifikation:

- [viciv.vhdl, aaf4542](https://github.com/MEGA65/mega65-core/blob/aaf4542d02679271b5fb84ad933cc39bbe091c3f/src/vhdl/viciv.vhdl):
  Zeilen1360–1500 HOTREG, H640 und Legacy-Geometrie; 1880–2030 Registerreadback;
  2533–2573 D031-Moduswechsel; 2717–2726 horizontale/vertikale Skalierung;
  2760ff Screen-/NCM-Felder; 2802ff PAL/NTSC; 2915ff Komparator/CHARY16;
  5588–5625 Pixelinkrement. SHA256
  `81aa438fa0c2d5b6e040ba5f24db2401ed0c18e140138d355cbe3ce037f5091b`.
- [iomapper.vhdl, aaf4542](https://github.com/MEGA65/mega65-core/blob/aaf4542d02679271b5fb84ad933cc39bbe091c3f/src/vhdl/iomapper.vhdl),
  SHA256 `08441ffc382b018a327668749bc28b20c5079c4dc6c3b40ea8f5f0bc41489a7c`.
- [MEGA65 Chipset Reference, Appendix VIC-IV](https://github.com/MEGA65/mega65-user-guide/blob/cefce48d72e5c98d732c0589461d62b205b5165f/appendix-viciv-registers.tex),
  Abschnitte HOTREG und VIC-III Errata. Diese Ausgabe ist **nicht** als exakt
  zur0.97 gehörend belegt; relevante Aussagen wurden gegen aaf4542 geprüft.
- [Lokale XEMU-Referenz vic4.c](https://github.com/lgblgblgb/xemu/blob/40dfef0d1d5f56be2469492715c12bdb32c75b67/targets/mega65/vic4.c),
  ca.Zeile556 Skalierung, 745 D031-HOTREG-Touch, 887 HOTREG-Propagation,
  928 abgeleiteter D018-Readback. Kein Beleg für das Verhalten des vom Benutzer
  angefragten Releases20260129235930.

Der Core rechnet H640 mit CHRXSCL/120, H320 mit zusätzlicher Halbierung.
D031-Schreiben markiert Legacy-Geometrie als geändert; HOTREG kann damit
präzise Pointer/Stride/Origins später überschreiben. Das ist dokumentierte
Semantik, **kein neu nachgewiesener Emulatorfehler**. HWERRATA>=1 beeinflusst
das historische H640-X-Scroll-Delta; der Test liest den Wert nur und aktiviert
keine Errata-Fixes. Für Core0.97 wurde keine weitere spezifische Errata gefunden,
die den gemeldeten kompletten HUD-Ausfall bereits erklärt.

## Auswertung / nächster Schritt

Die mitgelieferten ergänzenden Messdateien stehen unter
`docs/diagnostics/stage10b1/`; `runtime.json` benennt die tatsächlich geprüften
Fälle und Grenzen. `profile_comparison.json` vergleicht nur S/E desselben
lokalen Emulators, **nicht** echte Hardware gegen XEMU.

Für den späteren Hardwarevergleich zuerst den frühesten Divergenzpunkt in den
vier Phasen bestimmen. Unterschiede bereits in Phase1 sprechen für andere
Start-/ROM-/Corezustände; Unterschiede ab Phase2 für Initialisierung/Readback;
neu in Phase3 für Übergang/Restore. Bei gleichen stabilen Werten und anderem
Bild sind dann die Interpretation, RRB-Zeilenbudget/-Timing und Clipping anhand
des gepinnten Corecodes zu untersuchen. Fotos und RAM-Screen-/Glyphdaten sind
zusätzliche Belege. Erst nach diesen Befunden einen minimalen Stage10b2-Fix
festlegen. Stage10a1 bleibt unangetastet.

### Tatsächlich abgeschlossene lokale Prüfungen

| Prüfung | Ergebnis |
|---|---|
| KickAssembler5.25, Layout-Assertion | bestanden; PRG42433Bytes |
| D81-Dateikette/BAM/Dateiinhalt | bestanden; D81 exakt819200Bytes |
| unabhängiger zweiter Build | alle Release-Dateien byteidentisch |
| Offline-Prüfungen | 8Tests bestanden: Korruption, Abbruch, Schema, Rastermasken, Geometriedivergenz, D81-Zyklus, Hashes, Monitorformat |
| beide Profile, vier Live-Snapshots | gültige1992Byte-Dumps; H640/60, Stride192, Count96, CHARX80/CHARY104 |
| DMA-Rücklesevergleich | Screen4800, Color4800 und Rasterglyphen24000Bytes stimmen vollständig |
| beide SEQ-Exporte | DOS00; Inhalt identisch zum RAM-Puffer |
| X-Restore | Color-RAM32768 und Paletten3072Bytes vollständig identisch zur Sicherung |
| erneutes RUN / erneuter Export | neuer gültiger Dump; erneuter Export DOS00 |
| kontrollierter Exportfehler | nicht vorhandenes Gerät31 nur im Emulator-RAM gesetzt; roter Fehlerrahmen, Rückkehr zur Szene, X erreicht Restore |
| S/E-Vergleich lokal | keine Unterschiede in stabil maskierten Bits; flüchtige Unterschiede bleiben im JSON erhalten |
| echter MEGA65 / exaktes Ziel-XEMU | **offen; Benutzervergleich erforderlich** |

Die Fehlerfallprüfung injiziert nur im Emulator eine andere OPEN-Gerätenummer;
sie beweist keine Prüfung mit physisch schreibgeschützter oder voller Diskette.
Das finale ausgelieferte Programm verwendet unverändert Laufwerk8.

## Nachgereichte Benutzer-Messungen

Die vom Benutzer gelieferten MEGA65-/XEMU-D81 und vier Bilder wurden
anschließend ausgewertet: [Hardwarebefunde](stage10b1_user_hardware_findings.md).
Das PRG ist identisch, sämtliche gefundenen Dumps sind gültig. Im ProfilS
stimmt die Grundgeometrie überein; NORRDEL unterscheidet sich bereits vor der
Initialisierung. Der Hardwaredump für ProfilE wurde nachgeliefert (Dateiname V10BEX.DAT,
Herkunft MEGA65), die Bildzuordnung ist bestätigt. Auch in E bleibt NORRDEL
unterschiedlich; Details im Nachtrag des Befundberichts. Keine produktive
Korrektur und kein Kausalitätsnachweis allein aus der Registerabweichung.
