# Stage10b1b — RRB-Minimalszenen und Vor-/Nach-Export-Diagnose

> **Auswertung vom 17.10.2026:** Die Hardware- und Benutzer-XEMU-Daten sind
> [hier ausgewertet](stage10b1b_hardware_results_20261017.md). Eine falsche
> Mono-Breitenannahme im Testaufbau wurde nachgewiesen: normale Zeichen sind
> bei Scale60 **16native Pixel breit**, nicht8. A/B-HUD und B-Pixie liegen
> deshalb offscreen. Der ausgelieferte Build bleibt als Messreferenz unverändert;
> die folgenden Szenenbeschreibungen und Summen sind entsprechend berichtigt.


Issue93, Branch `stage10b1b-rrb-minimal`. Eigenständiges Diagnoseprogramm,
kein Gameplay-/Stage10b2-Fix, kein Merge oder Stable-Tag.
Basis: geprüfter Diagnose-/Benutzerbefundstand aus PR92,
`17d329f2ce7f002bd20df3441ec30d564dd64cb3`.
Stage10a1 Stable, `main`, Stage10b1 und Stage10b1a einschließlich ihrer
Quellen, Tools und Releases bleiben unverändert.

Grundlage: [PR90-Hardwarebefunde](stage10b1_user_hardware_findings.md),
[PR92-Hardwarebefunde](stage10b1a_user_findings.md). NORRDEL allein war kein
belegter Fix; die dort erfassten neun Speicherbereiche waren auf Hardware und
XEMU identisch. Diese Stage isoliert normale Zeichen, NCM, GOTOX und die
kombinierte Referenzszene. Zusätzlich werden Paletten und der Exportübergang
selbst gemessen. Noch keine Ursache als Core-/XEMU-Fehler voraussetzen.

## Konstante Grundkonfiguration und notwendige Ausnahmen

Alle vier Szenen: festes Profil E, D031=C0 (H640/FAST), D054=55
(PALEMU0/CHR16/FCLRHI/VFAST/SPR H640), D051-Schreibwert1F
(**NORRDEL0, DBLRR0**), CHRXSCL60, CHRYSCL1, Stride192,
Count96, ScreenE000, Coloroffset0, Mono-Font4000, D07B25.
Sichtbare Ursprünge/Grenzen kommen wie in Stage10b1a aus demselben gesicherten
PAL80×25-BASIC-Startzustand. GOTOX-/NCM-Fähigkeit wird nicht durch zusätzliche
VIC-Moduswechsel zwischen den Szenen eingeschaltet: CHR16/FCLRHI bleiben
konstant; nur Screenwörter und zugehörige Color-RAM-Attribute unterscheiden
gewöhnliche Zeichen, GOTOX und NCM.

Alle Szenen besitzen dieselbe Palette für die tatsächlich verwendeten
Indizes und dieselben Grafikadressen, Spritepointer, Koordinaten-/Skalenregister,
IRQ-/DMA-Grundlagen. Ungenutzte Paletteneinträge werden aus dem nativen
Ausgangszustand erhalten und diesmal vollständig mitgemessen. Eine andere
Palette wird nicht gleichzeitig mit einem RRB-Test ausgewählt.

**Einzige szenenabhängige VIC-Ausnahme:** D015=0C in A/B/C, D015=0F in D.
Sprites2/3 sind in allen Szenen die unabhängigen Kennzeichen. Nur D aktiviert
zusätzlich die bekannten Referenzsprites0/1. Positionen, Datenformat, Palette,
Pointer und Register aller vier Sprites werden sonst identisch programmiert.
D015-Abweichung ist im Vergleich ausdrücklich als erwartete Szenenabweichung
gekennzeichnet; kein anderer Registerunterschied wird pauschal ausgeblendet.

### Unabhängige, sichtbare Kennzeichnung

Hardware-Sprite2 zeigt **A/B/C/D** links oben bei Engine-Anker(8,8).
Hardware-Sprite3 zeigt die **Phase** bei Anker(24,8). Beide liegen links im
Playfield, außerhalb des fehlerverdächtigen rechten HUD-Bereichs, und
benötigen keine RRB-Slots. Weiß, mono, gleiche Koordinaten/Palette in allen
Tests. Die originale Szene wird an dieser kleinen Stelle überlagert; ihre
Screen-/Color-Daten bleiben unverändert. Die historische Spriteumrechnung
CHARX+2X−3 / CHARY+2Y bleibt erhalten; Anker sind nicht die linke Quellpixelkante.

| Sprite3 | Bedeutung |
|---|---|
| PRE | Szene vor der zu messenden Dateioperation |
| PST | eingefrorener Nachzustand: **jetzt POST-Foto machen**, danach S |
| END | POST-Datei gespeichert; dieses spätere Bild ist **nicht** das POST-Foto |
| ERR | Exportfehler; Daten bleiben im RAM, S/Retry bzw.X funktionieren weiter |

Die Markerdaten sind neu erzeugte technische Beschriftung, keine Ersatz-
Spielgrafik. Der NCM-Pixie verwendet unverändert die vorhandene Original-
Playergrafik und Originalpalette. Monofont ist der bestätigte Menüfont.

## Die vier Szenen

**A — normale Textdarstellung/HUD.** 96 Zwei-Byte-Zeichen pro Zeile,
alle gewöhnlich mono. Keine GOTOX-Steuerwörter, kein NCM, kein RRB-Pixie.
Im Text stehen Begrenzungen/Koordinaten. Das HUD sollte beiX240 beginnen,
liegt tatsächlich nach60Monozellen bei960nativen Pixeln außerhalb des Screens.
Die globale CHR16-Einstellung bleibt für den kontrollierten Vergleich an;
„ohne RRB-Einträge“ bedeutet hier ohne RRB-Steuer-/NCM-Objekte, nicht einen
zweiten Legacy-Modus. Hardware-Sprites2/3 sind nur die Kennzeichnung.

**B — A mit genau einem Original-NCM-Pixie im Screenpuffer.** Geplant X224/Y80,
tatsächlich aufgrund der Mono-Breite X448/Y80 und damit offscreen:
16×16logische Pixel, zwei16×8Glyphen241/242 auf Zeichenzeilen10/11.
Je betroffener Zeile ersetzt ein NCM-Eintrag vier ursprünglich als4logische
Pixel breit angenommene Monozellen; tatsächlich sind diese8Pixel breit.
Die drei überzähligen Monoslots wandern als Leerzeichen ans Zeilenende;
das HUD liegt bei928nativen Pixeln ebenfalls offscreen. Kein GOTOX und kein zusätzlicher VIC-Moduswechsel.
NCM-Attribut08 und Subpalette10. Sonst dieselbe sichtbare Textszene A.

**C — A mit GOTOX, ohne Pixie/NCM.** Jede Zeile beginnt mit GOTOX0;
vor dem HUD steht GOTOX480native Pixel (=240logisch). Die80 vorgesehenen
Monozeichen bleiben gleich; bei dieser Skalierung sind sie nicht alle sichtbar. Zwei bisherige Tail-Leerzeichen werden durch
die Kommandos ersetzt, Count bleibt96. Kein Pixie, keine NCM-Zeichen.

**D — vollständige Referenz.** Dieselben240×200Playfield-/HUD-Grenzen,
15NCM-Rasterzellen pro Zeile, HUD ab GOTOX480, Originalpixie bei224,80,
GOTOX-/Blankguards, Referenzsprite0 bei112,112 und1×4-Projektil1 bei232,64
wie Stage10b1a; ergänzt nur um die unabhängigen Marker2/3.
Keine zusätzlichen Testgegner oder Spielmechanik.

## RRB-Einträge und Zeilenbudget: berechnet, keine erfundene Hardwaregrenze

Für jede sichtbare Quellzeile0–24 erzeugt der Builder
`scene_budget.json`; das Vergleichsskript dekodiert zusätzlich die tatsächlich
zurückgelesenen Screenwörter/Attribute, nicht nur Buildannahmen.

| Szene / Zeilen | Mono | NCM | GOTOX | Einträge | nominelle native Pixelarbeit | Glyph-Row-Payload |
|---|---:|---:|---:|---:|---:|---:|
| A / alle |96|0|0|96|1536|96Bytes|
| B / außer10/11 |96|0|0|96|1536|96Bytes|
| B /10/11 |95|1|0|96|1552|103Bytes|
| C / alle |94|0|2|96|1504|94Bytes|
| D / alle |20|44|32|96|1728|372Bytes|

Die Tabelle ist nach dem Hardwarevergleich korrigiert. Das unveränderte
Release-JSON und die bisherigen Parserfelder `nominal_native_pixel_work`
enthalten noch die alte, falsche Mono×8-Annahme; sie sind keine gemessenen
nativen Pixelkosten. Pro Zeile immer192Screen- und192Color-Bytes. Die Pixelarbeit ist
Mono×16 + NCM×32 bei dieser Skalierung; sie zählt auch unsichtbare/erneut
adressierte Guardarbeiten, **nicht** die letztlich sichtbare Breite oder eine
bewiesene FPGA-Zykluszahl. Glyph-Row-Payload ist Mono×1 + NCM×8, **keine**
Messung physischer Speicherbuszugriffe: Caches, Burstzugriffe, Glyphwiederholung,
GOTOX und Pipeline können die tatsächlichen Kosten verändern.

D-Prefix:21Slots =4GOTOX +17NCM (15Raster,2Blankguards).
HUD:21Slots =1GOTOX +20Mono. Tail:54Slots =27GOTOX +27NCM.
In Zeilen10/11 werden ein Tail-GOTOX und ein Blankglyph durch448 und den
passenden Pixiehalbframe ersetzt; die Anzahl bleibt gleich. Ein einziges
NCM-Objekt überlagert das Raster, keine mehrfachen Gegnerüberlappungen.
Die Marker benutzen keine dieser96Slots. D aktiviert zwei weitere Hardware-
Sprites und besitzt damit absichtlich die höchste kombinierte Belastung.

**Display-/Fetchfenster:** nominell640native horizontale Bildpixel
(480Playfield +160HUD),400physische Raster für200logische Zeilen;
96Einträge sind die konfigurierte Zeilenstruktur, keine pauschal bewiesene
„maximale Hardwaregrenze“. Ein durch GOTOX außerhalb des sichtbaren Felds
liegender Guard kann weiterhin Bearbeitungszeit kosten. DBLRR bleibt0,
keine gleichzeitige Verdoppelung des Fetchfensters.

Pinned Core0.97 `aaf4542d02679271b5fb84ad933cc39bbe091c3f`,
[viciv.vhdl](https://github.com/MEGA65/mega65-core/blob/aaf4542d02679271b5fb84ad933cc39bbe091c3f/src/vhdl/viciv.vhdl):
Registerreadback1880ff, D051-Schreiben2661–2668, Rasterfetch/Pufferhälfte
3382–3409, Row-/Stop-Logik3510–3540. Der Code zeigt Zustands-/Fetchabhängigkeit;
eine konkrete Grenze in Einträgen oder garantierte Deadline für diese Szene
ist daraus ohne weitere Timing-/Hardwaremessung hier nicht bewiesen.
UART-Pausen sind keine geeignete Rasterzeitmessung.

D07B bleibt bewusst25. Der Core verwendet den Wert bei der Stop-Logik als
letzten Zeilenindex. **Vorsorglich werden deshalb auch Screen-/Color-Zeile25
hinter den25gebauten sichtbaren Zeilen erfasst**, ohne sie zu initialisieren
oder die Register zu ändern. So bleiben unbekannte Randdaten als Befund
sichtbar. Keine zusätzliche sichtbare Zeile und kein Off-by-one-Fix.

## Exakte Messfolge: Beobachtereffekt durch zweite Speicherung vermeiden

Ein POST-Dump kann erst **nach** der zu messenden Dateioperation entstehen.
Seine anschließende Speicherung wäre selbst eine weitere KERNAL-Operation.
Das Programm trennt diese Schritte ausdrücklich:

1. Szene mit PRE-Marker aufbauen, Foto vor Export ermöglichen.
2. H/E: aktuelles PRE unmittelbar vor Eingriff vollständig in RAM konservieren;
   anschließend PRE-Datei tatsächlich über KERNAL/DOS schreiben.
3. Videozustand/Szene wie in der Diagnosebasis restaurieren; PST- bzw.ERR-
   Marker setzen, Register und tatsächlichen Speicherzustand **getrennt**
   in POST-RAM erfassen. Keine weitere Datei-I/O. Szene bleibt für Foto stehen.
4. Erst **S** schreibt die schon eingefrorenen POST-Bytes. Danach wird
   END/ERR angezeigt. Dieser weitere Aufbau ist **kein neuer POST-Referenz-
   Snapshot**; PRE/POST-RAM bleibt unverändert.

Der gemessene Übergang umfasst somit den realen ersten PRE-Export samt
BASIC-/KERNAL-/Videorestore-Roundtrip. Er isoliert nicht automatisch, ob ein
Befund von DOS, IRQ, dem Modewechsel oder Reinitialisierung stammt; er macht
diese Gesamtauswirkung nachweisbar. Keine vollständige Titel-/Loader-/Audio-
Ausführung in dieser Stage.

Die Aufnahmen sind sequenziell bei statischer Szene/SEI, nicht atomar zum
GPU-Frame. Phasenstart-Rasterwerte und gemeinsame Sequenznummer werden
konserviert. Fotos müssen jeweils **vor H/E** bzw. **nach H/E, vor S** entstehen.
Ein Foto nach S zeigt bewusst END und darf nicht als POST-Beleg gelten.

## Bedienung: Hardware und XEMU mit denselben Dateien

Hardware: MEGA65 Core0.97 `aaf4542`; Ziel-XEMU: Release20260129235930,
keine daraus abgeleitete Corekennung. Gleiche ROMV920413, PAL, BASIC80×25,
frischer Boot ohne fremde Grafik-/X-IRQ-Programme. Bisheriger ROM-Hash:
`af3c447f791a2fdc48cb21e1bd3fab015e32641228d9d30d21259b9e878c6fa0`.
ROM nicht mitgeliefert.

1. Je eine **beschreibbare Kopie derselben Release-D81** für Hardware/XEMU
   anlegen; Ausgangshashes aus `SHA256SUMS.txt` vergleichen. Laufwerk8:
   `LOAD"STAGE10B1B",8`, `RUN`. Standard A mit PRE-Marker.
2. Taste**1/2/3/4** wählt A/B/C/D. Vollständigen Aufbau abwarten.
   Szene/Phase müssen an den linken Spritemarkern erkennbar sein, auch ohne HUD.
3. Pro Szene frisches Foto/Screenshot **PRE** machen. Dann **H** auf echter
   Hardware bzw. **E** in XEMU: Das ist nur das Herkunftslabel beim Export.
4. Warten, bis links **PST** steht. Jetzt Foto **POST** machen. Bei ERR Fehler
   mitfotografieren und die RAM-/Dateidaten ebenfalls sichern.
5. **S** drücken. Bis END bzw.ERR warten. Erst nach erfolgreichem S ist der
   Szenenwechsel freigegeben; bei POST-pending werden weitere1–4/H/E ignoriert,
   damit die ungesicherten Daten nicht unbemerkt überschrieben werden.
6. Nächste Szene wählen und Schritte3–5 wiederholen. **X** bleibt jederzeit
   ein sauberer Exit; noch nicht gespeicherte POST-Daten bleiben nur im RAM.
7. `DIRECTORY`, erneutes `RUN` und Export prüfen. **Tatsächlich beschriebene
   D81-Kopie** zurückgeben, nicht versehentlich den unveränderten Download.

| Szene | MEGA65-Dateien (H) | XEMU-Dateien (E) |
|---|---|---|
| A | V1BAH.PRE / V1BAH.PST | V1BAX.PRE / V1BAX.PST |
| B | V1BBH.PRE / V1BBH.PST | V1BBX.PRE / V1BBX.PST |
| C | V1BCH.PRE / V1BCH.PST | V1BCX.PRE / V1BCX.PST |
| D | V1BDH.PRE / V1BDH.PST | V1BDX.PRE / V1BDX.PST |

Alle Dateien SEQ, je40408Bytes, **ohne PRG-Ladeadresse**. H/X ist manuell,
kein Herkunftsbeweis. Tatsächliches System separat bestätigen. Wiederholung
A→B→A: A1-Dateien **vor** erneutem A-Export extern archivieren, sonst werden
sie ersetzt. Sequenznummern machen versehentlich gemischte PRE-/POST-Paare
prüfbar, ersetzen aber keine unabhängige Herkunfts-/Bildzuordnung.

Fotomatrix pro System: A_PRE/A_POST, B_PRE/B_POST, C_PRE/C_POST,
D_PRE/D_POST; bei Wiederholung A1_/A2_ ergänzen. Namen **und sichtbare Marker**
kontrollieren. Neue echte Aufnahmen pro Zustand; nicht dasselbe A-PNG unter
verschiedenen Namen kopieren. Zeitpunkt vor/nach S festhalten. Angeben:
Core/Emulatorversion, ROM-Hash, Bootmodus, Reihenfolge, Fehler, ggf. benötigte
Wartezeit. Keine pauschale Funktionsabnahme aus Dateinamen ableiten.

## D051-/IRQ-Sicherheit und Restore

Wie Stage10b1a: D051 liefert unten Live-Raster-X, schreibt dort aber den
X-IRQ-Komparator. Expliziter konstanter Schreibwert **1F**, gespeicherter
`d051_shadow`, kein blindes Read-modify-write. D050 wird nicht geschrieben.
D01A.4 bleibt aus. Bei bereits aktiver X-IRQ-Maske bricht der Einstieg vor
D051-/IRQ-Maskenänderung nach BASIC ab. Startvoraussetzung frisches natives
PAL80×25-BASIC; kein allgemeiner Kontextsaver für Fremdprogramme.

Grenze unverändert: ursprüngliche individuelle inaktive X-Komparator-Highbits
sind nicht rücklesbar. Sie werden beim Restore auf die dokumentierte1F-
Schattensetzung zurückgeführt; Lowbits bleiben unangetastet, ursprüngliche
D051-Steuerbits7/6 und IRQ-Maske werden restauriert. IRQ-Quelle wird nicht
als Testvariable umgeschaltet; D019 wird nicht pauschal quittiert.

Szenenwechsel warten auf PAL-Blanking (physische Raster>=528) und führen
vollständigen Restore/Neuaufbau aus. HOTREG-/Legacy-Updates werden vor den
präzisen VIC-Feldern abgearbeitet. D011-Komparatorbit kommt aus D07A statt
aus dem Live-Rasterbit. X restauriert sämtliche im Test geänderten Sprite-
Koordinaten/-farben, VIC-Felder, alle vier RGB-Paletten, das komplette32KiB-
Color-RAM und Prozessorstatus/IRQ-Maske. Audio und CIA werden nicht geschrieben.
DMA-Trigger/Historie werden nicht als vermeintlicher Zustand zurückgeschrieben.
MEGA65-I/O bleibt für das vorausgesetzte native BASIC aktiviert.

Dateiverwaltung wie bewährte Basis: SETBNK0 vor SETNAM; Scratch nur des
jeweils eigenen Diagnosenamens; begrenzte DOS-Antwort; CHKOUT/CHROUT/READST;
CLRCHN und CLOSE mit korrektem MEGA65-Carry-Vertrag. Keine fremde CHKIN-Phase.
Kein Absturz bei Fehler, ERR und `io_status`/`dos_code` aus der Symboltabelle
als unabhängige Statusbelege. S kann eine gescheiterte POST-Speicherung
wiederholen; der eingefrorene POST wird nicht neu aufgenommen. Bei fehlender
PRE-Datei wegen fehlgeschlagenem ersten Export RAM-Fallback verwenden oder
einen neuen vollständigen Lauf durchführen. Dateien sind kein atomisches Paar.

## Versioniertes Snapshotformat mit CRC16

Neue Magic **VYDG1B1B**, Version1; alte Stage10b1-/10b1a-Formate und Parser
bleiben unverändert. Ein Snapshot bündelt Register, Paletten, Schreib-Shadows
und Rohregionen. Gesamt40408Bytes, Header/Verzeichnis768Bytes.

| Offset | Inhalt |
|---|---|
|0–7|Magic VYDG1B1B|
|8|Version1|
|9|Szene A/B/C/D|
|10|manuelles Label U/H/X|
|11|Phase1=PRE,2=POST|
|12–13|Registerzahl162, LE16|
|14–15|Regionzahl13, LE16|
|16–19|Gesamtlänge40408, LE32|
|20–23|Laufsequenz, LE32 (Controller zählt16Bit, obere Bytes0)|
|24|zuletzt geschriebener D051-Shadow1F|
|25|D051-Restore-Shadow: ursprüngliche Steuerbits OR1F|
|26|Fehlercode des gemessenen ersten Exports (PRE0)|
|27|ursprüngliche IRQ-Maske|
|28–29|CRC16, low/high|
|30|Algorithmus2=CRC16-CCITT-FALSE|
|31|Flag1: I/O-Unlock vor Messung|
|32–37|Phasenstartwerte D012,D011,D052,D053,D050,D051|
|38–47|reserviert0|
|48–533|162Registerrecords: AdresseLE16,Wert8|
|534–741|13Regionrecords à16Bytes|
|742–767|Padding0|

CRC16-CCITT-FALSE: InitialFFFF, Polynom1021, nicht reflektiert, xorout0;
Berechnung über **die gesamte Datei**, Bytes28/29 dabei0. Prüfvektor
`123456789` ergibt29B1; die native Routine wird als Maschinencode dagegen
getestet. Phasenstartbytes werden im Parser erhalten und als volatile
Kontextdaten ausgewiesen; kein stiller Verlust wie beim alten Reviewhinweis.
D051/D053/D054/D067/D079/D07A sowie IRQ-/DMA-/Sprite-/Screen-/Color-Felder
sind in der geordneten Adressliste enthalten. Keine read-to-clear-Kollision-
latches D01E/F, kein D02F-Readback, keine CIA-ICR-Lesezugriffe.

Regionrecord: `QuelladresseLE32, DateioffsetLE32, LängeLE32, FlagsLE16=0,
ReserviertLE16=0`. Exakte Tabellen in `registers.json`.

| Region | tatsächliche Quelle / Herkunft | Bytes |
|---|---|---:|
|screen|physisch E000|4800|
|colour|physisch FF80000|4800|
|font|4000|2048|
|grid|18000|24000|
|pixie|9040|128|
|sprites|9200, Referenz0/1 und Marker2/3|256|
|pointers|9300, vier16Bit-Pointer|8|
|guards /guard2|8000 /90C0|64 je|
|palettes|CPU-Spiegel5400 aus D100/D200/D300, Banken0–3|3072|
|write_shadows|Controller-RAM4800|16|
|screen_next_row|F2C0, nicht initialisierte Zeile25 hinter sichtbarem Screen|192|
|colour_next_row|FF812C0, entsprechende Attributzeile25|192|

Palettenlayout: Bank0 bis3, jeweilsR256/G256/B256. Zum **Lesen** werden nur
D070-Mapped-Bankbits7/6 verändert, Display-/Sprite-/Altbankbits bleiben
konstant. Danach D030/D070 zurück, keine Palettenänderung durch den Capture.
5400 ist ausdrücklich der Readback-Spiegel, keine erfundene physische
Paletten-RAM-Adresse. Der Parser zeigt SHA256 pro Gesamtregion und Palettebank.

Shadowbytes:0D051Write,1D051Restore,2EntryIRQ,3eigeneIRQ-Maske,
4D054Write55,5D031WriteC0,6Spritefreigabe,7Phase1/2,
8gemessenerExportfehler,9Szene,10/11Sequenzlo/hi,
12ursprünglicherD07A-Readback,13expliziterD07A-Wert (CHARY16aus),14/15=0.
D067/D053 können nicht pauschal als vollständig restaurierbare Schreibwerte
aus ihrem Readback abgeleitet werden; sie bleiben echte Registerbefunde.

## RAM-Karte: beide Puffer innerhalb verfügbarer384KiB

| Bereich (physisch, inklusive) | Verwendung |
|---|---|
|2100–unter4000|Controller/Renderer/Capture/CRC/Export|
|4000–47FF|unveränderter Menüfont|
|4800–480F|explizite Schreib-Shadows|
|5000–50FF|256Byte-DMA-/Exportcache|
|5100–53FF|Header-/Verzeichnis-Arbeitskopie|
|5400–5FFF|aktuell zurückgelesene vier RGB-Paletten|
|6000–6BFF|ursprüngliche vier RGB-Paletten für BASIC-Restore|
|6C00–6CBF /6D00–6DBF|Screen-/Color-Zeilenpuffer|
|7000–77CF|80×25gewöhnliche Textquelle|
|7800–78FF /7900–79FF|Scene-/Phasenspritemuster|
|8000,8800,9040,90C0,9200,9300|Guards/Atlas/Pixie/Sprites/Pointer wie oben|
|A000–B2BF /B300–C5BF|D-Referenzvorlagen|
|E000–F2BF|gebauter sichtbarer Screen, nur physische DMA-Zugriffe|
|18000–1DDBF|375NCM-Rasterglyphen|
|40000–47FFF|komplette Color-RAM-Sicherung32768Bytes|
|50000–59DD7|PRE-Snapshot40408Bytes|
|48000–4FFFF|POST-Dateibytes0–32767|
|5A000–5BDD7|POST-Dateibytes32768–40407|

Der POST-Puffer ist bewusst **segmentiert**, weil60000 und höher auf den
Zielmodellen nicht als normales Chip-RAM vorausgesetzt werden darf. Der erste
Entwurf zeigte dort im lokalen Emulator nurFF; er wurde vor Auslieferung
verworfen. DMA-Schreiben teilt die kreuzende Grid-Region an Dateioffset8000;
CRC und Export lesen denselben logischen Stream aus beiden realen Segmenten.
Boundary-Tests verhindern Null-Längen-DMA. Kein Überlappen mit Colorbackup
oder PRE, keine Verwendung von ROM20000–3FFFF als freiem RAM.

[Offizielle Speicherkarte](https://github.com/MEGA65/mega65-user-guide/blob/cefce48d72e5c98d732c0589461d62b205b5165f/appendix-memorymap.tex),
Abschnitt Main Memory: Standard-RAM bis005FFFF;0060000–0FFFFFF nicht pauschal
RAM. Dies ist die gepinnte Dokumentausgabe, nicht behauptet als exakt zur0.97
erschienene Ausgabe. Tatsächliche Datenübertragungen werden lokal zusätzlich
per Rücklesevergleich geprüft. PRG endet vor D000.

## Vergleich und Fallback ohne lesbares Bild

PRE gegen POST derselben Szene (Sequenz/Label/Szene müssen zusammenpassen):

```sh
python3 tools/analysis/compare_stage10b1b.py MEGA65.d81 MEGA65.d81 \
  --left-file V1BAH.PRE --right-file V1BAH.PST --pair --json A_export.json
```

Gleiche Szene/Phase zwischen Plattformen:

```sh
python3 tools/analysis/compare_stage10b1b.py MEGA65.d81 XEMU.d81 \
  --left-file V1BAH.PRE --right-file V1BAX.PRE --json A_system_PRE.json
```

Entsprechend A.POST/B/C/D. Ohne Dateinamenargument direkt extrahierte
40408Byte-Binärdateien übergeben. Einzeldatei prüft CRC/Schema/Konfiguration
und gibt Layout, Kontext, Region-/Palettebankhashes aus. Über verschiedene
Szenen sind Screen-/Attribute-/Markerdaten beabsichtigt unterschiedlich;
diese Rohunterschiede bleiben sichtbar und werden nicht als Plattformfehler
umgedeutet.

`unexpected_stable_register_differences` trennt stabile Bits von Raster-/DMA-
Kontext; erwartete D015-Änderung zu D ist markiert. Speichervergleich nennt
exakte Anzahl und erste64Rohabweichungen mit Quelle. Nur gültige PRE/PST-
Phasenmarkerbytes im Spriteregionoffset192–255 und Shadowbyte7 sind als
absichtliche Phasenanzeige ausgenommen. Paletteunterschiede werden **nie**
ausgeblendet. Bei gleicher Szene/Phase zwischen Plattformen wird kein solches
Markerbyte ausgenommen. Falsche Markerpattern bleiben echte Befunde.

Bei Dateifehlern: PRE und POST bleiben an den obigen RAM-Adressen erhalten,
auch nach X, bis andere Programme sie überschreiben. Bevorzugter Fallback ist
ein **roher Dump des ersten384KiB-RAM** ab physisch0 (exakt393216Bytes).
Das Skript extrahiert beide Snapshot-Puffer einschließlich POST-Segmentierung:

```sh
python3 tools/analysis/compare_stage10b1b.py RAM.bin RAM.bin \
  --left-phase PRE --right-phase POST --pair --json fallback.json
```

Alternativ UART-Monitor-M-Zeilen `:00050000:...` usw. sichern: PRE50000–59DD7,
POST48000–4FFFF **und**5A000–5BDD7. Beim Textinput ebenfalls `--left-phase`
oder `--right-phase` angeben. Das Skript verweigert fehlende RAM-Bytes und
prüft die rekonstruierte CRC, statt Löcher stillschweigend aufzufüllen.
Die Fallbackformate wurden mit vollständigem RAM-/Monitor-Text auf Hostseite
getestet; kein automatisierter echter Freezer-/Hardware-Export behauptet.

BASIC-SEQ-Alternative nach X, falls DOS weiter funktioniert (eigene, noch
nicht vorhandene Namen, anschließend Fehlerkanal kontrollieren):

```basic
BANK 5
OPEN 2,8,2,"0:FALLBACK.PRE,S,W"
FOR I=0 TO 40407:PRINT#2,CHR$(PEEK(I));:NEXT I
CLOSE 2
BANK 4
OPEN 2,8,2,"0:FALLBACK.PST,S,W"
FOR I=32768 TO 65535:PRINT#2,CHR$(PEEK(I));:NEXT I
BANK 5
FOR I=40960 TO 48599:PRINT#2,CHR$(PEEK(I));:NEXT I
CLOSE 2
BANK 0
```

Diese manuelle BASIC-Rettungsfolge wurde nicht als Runtime-Test ausgeführt;
der Monitorweg und das reguläre native Exportprogramm sind die bevorzugten
Wege. Keine PRG-Ladeadresse hinzufügen oder Headerlabel ohne neue CRC ändern.

## Build, Tests und Beleggrenzen

Quellen `src/tests/stage10b1b.asm` und `stage10b1b_helpers.asm`;
Builder `tools/build_stage10b1b.py`, Ausgabe `releases/stage_10b1b/`.
Python3-Standardbibliothek, Java und gepinnter offizieller KickAssembler5.25:

```sh
python3 tools/build_stage10b1b.py --kickass /pfad/KickAss.jar
(cd releases/stage_10b1b && sha256sum -c SHA256SUMS.txt)
KICKASS_JAR=/pfad/KickAss.jar python3 tools/test_stage10b1b.py
```

Hosttests benötigen zusätzlich py65==1.2.0 (Build/Vergleich nicht).
Hier vorhanden unter `/workspace/stage3b-inspection/test-deps`; ausgeführt mit
`PYTHONPATH=/workspace/stage3b-inspection/test-deps` zusätzlich zum JAR-Pfad.
Die kurzen6502-Konfigurations-/CRC-/Deskriptorroutinen werden als tatsächlicher
assemblierter Code ausgeführt; keine erfundene DMA-/VIC-Emulation im Hosttest.

Elf Hosttests: Szenenisolierung/alleZeilen, konstante Konfigurationsopcodes,
CRC-Prüfvektor, segmentierte DMA-Deskriptoren einschließlich exakter Grenze,
RAM-/ROM-Grenzen, X-IRQ-Guard/Shadow-Restore, beschädigte CRC/Verzeichnisse,
PRE/POST-Sequenz/Timingkontext, sichtbare Paletteabweichung, vollständiger
RAM-/Monitor-Fallback, unabhängiger kompletter Build/D81/Hashes.

Ergänzender lokaler Runtime-Treiber: `tools/check_stage10b1b_xemu.py`.
Prüft A–D, tatsächliche Screen-/Color-Inhalte gegen getrennte Buildreferenzen,
alle13Snapshotregionen einschließlich unabhängig gelesener vier Palettebanken,
CRC, PRE-Datei, POST-Pause bis S, POST-Datei, Unveränderlichkeit des eingefrorenen
POST durch S, END-Marker, vollständiges Color-/Paletten-/IRQ-/D051-Restore,
erneutes RUN sowie kontrollierten fehlgeschlagenen Geräte31-Export mit ERR,
S und X. Kontrollierte Emulator-RAM-Injektion ist nicht Teil des PRG.

Runtimebelege unter `docs/diagnostics/stage10b1b/` benennen exakt geprüfte Fälle.
Lokaler XEMU-Quellcommit40dfef0d1d5f56be2469492715c12bdb32c75b67 mit
`tools/diagnostics/stage10a1_xemu_trace.patch` für Headless/Tastatur/Trace;
**nicht** die verlangte Release-Binärdatei. UART-Pausen verfälschen Timing;
keine visuelle, physische Joystick- oder echte Hardwareabnahme behauptet.
Echter MEGA65/Core0.97 und Ziel-XEMU20260129235930 werden vom Benutzer mit
denselben PRG-/D81-Bytes geprüft.

## Auswertungsregeln nach den Nutzertests

- A fehlerhaft: normale Text-/Palette-/Screeninitialisierung und Basiszustand
  untersuchen, nicht zuerst Pixies verantwortlich machen.
- A korrekt, B fehlerhaft: NCM-Pixie-/Fetch-/Farbattribute und Mono/NCM-Wechsel.
- A/B korrekt, C fehlerhaft: isolierte GOTOX-Verarbeitung.
- Erst D fehlerhaft: kombinierter Zeilenaufbau/Budget/Timing und zusätzliche
  Hardware-Sprites getrennt untersuchen.
- PRE korrekt, POST fehlerhaft: gespeicherte Register, Paletten, Randdaten und
  Rohregionen auf Änderungen prüfen; interne Pipelinezustände sind nicht mit
  vollständiger Maschinenzustandssicherung gleichzusetzen.
- Gleiche Daten, anderes Bild: Rendering-/FIFO-/Zeitfenster gezielt isolieren;
  keine unbelegte Hardwaregrenze oder pauschalen Scaling-Fix behaupten.

Zusätzliche Untertests (Slotzahl, X-Position, Pixiehöhe, Fetchfenster, DBLRR)
erst nach dokumentierter A–D-Hardwareauswertung separat beauftragen.
Die gesicherte Stage10a1 bleibt unverändert. Stage10b2 erst nach Nutzerprüfung.
