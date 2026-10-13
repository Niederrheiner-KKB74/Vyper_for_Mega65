# Stage 5d-1 – Titelgrafik während des SEQ-Ladens

Issue [#35](https://github.com/Niederrheiner-KKB74/Vyper_for_Mega65/issues/35),
Branch `stage5d-1`. **Stable, vom Benutzer nach HOTREG-Korrektur in XEMU bestätigt.** Ausgangsbasis ist
`stage5c-stable` (`2997719d704095afc630830435cb2d2f76b7f696`). Der bestätigte
Titelrenderer stammt aus `stage5d0-stable`
(`d6421606109993f481fb3e3e76d9bd70fb12f48a`, Branch `stage5d-title-test`).
Beide bestehenden Quellen, Originalassets und Releases bleiben byteidentisch;
der Build kontrolliert sie gegen die Tags. Die Spielkomponenten werden zusätzlich
nach Entfernung der Stage-Namensänderungen gegen Stage 5c geprüft.

## Ablauf und unveränderter Grafikmodus

`p_startup → hud.startup → s3b.entry → splash.t_boot` lädt zunächst `VYTI.DAT`.
Währenddessen bleibt der vorher durch KERNAL geleerte BASIC-Bildschirm schwarz.
Erst nach vollständiger Größen-, Summen-, Header- und DMA-Rückleseprüfung wird
das fertige Bild atomar aktiviert. Danach folgen `VYLV.DAT`, `VYGR.DAT` und
`VYCL.DAT`; während dieser drei Dateien und der Vorbereitung von Level 1 bleibt
der Titel unverändert sichtbar. Es gibt keine Fortschrittsausgabe und kein Menü.

FCM und Registerinitialisierung sind aus dem bestätigten Stand übernommen:
352×240 Originalpixel, 44×30 Zellen, 8×8 Full-Colour-Kacheln, 88 Bytes Screenstride,
`D054=$05`, H320, `D05A=120`, `D05B=1`, `D07B=29`, Textursprung 48/48,
vertikale Rahmen 48/528, horizontale Rahmen 40, Palette/Mapping Bank 1.
Jeder Originalpixel belegt zwei native horizontale Pixel und zwei Rasterzeilen.
Keine Skalierungsinterpolation, kein Beschnitt, keine Farbquantisierung.
Die 33 RGB4-Paletteneinträge werden durch Multiplikation mit 17 exakt RGB8.
Die doppelt vorkommenden schwarzen Paletteneinträge verändern das RGB-Bild nicht.

Die Speicherbelegung wurde vor der Integration gegen die aktive Stage-5c-Karte
geprüft; insbesondere sind DOS, Record, Pixiepool, Color-RAM-Backup und
Spieldatenziele geschützt.

Der neue Konverter verwendet den Stage-5d-0-Konverter und fasst ausschließlich
byteidentische 64-Byte-Kacheln zusammen: 1320 Zellen ergeben 900 einzigartige
Kacheln. Ein vollständiger Rückvergleich aller 84.480 RGB-Pixel ist Teil des
Builds und der Laufzeittests. Die drei getrennten Cachebereiche vermeiden die
Spieldaten und sämtliche während des Ladens aktiven Enginepuffer. Das FCM-
Pixelformat und der bestätigte Anzeigeweg ändern sich dadurch nicht.

## Speicherkarte und Lebensdauer

Alle Endadressen sind einschließlich. Die vollständige Assemblermap liegt im Release.

| Bereich | Verwendung / Lebensdauer |
|---|---|
| `$2001–$CAFF` | PRG, ursprüngliche Engine-Origins erhalten |
| `$3340–$33AA` | Dauerhafter DMA-Helfer für Bootstrap-Sicherung/Rückkopie |
| `$4000–$47FF` | Titelbootstrap bis Ladeabschluss; danach bisheriger HUD-Zeichensatz |
| `$4800–$4B4A` | Gemeinsamer SEQ-Loader und Übergabesteuerung |
| `$6800–$68FF`, `$6900–$69FF` | SEQ-Eingabepuffer / DMA-Rücklesepuffer |
| `$6B00–$6CF6`, `$6D00–$6EDB` | VYCL-Code / validierter Palettenspiegel |
| `$7600–$7607` | Nur Level-1-Signaturprefix; Angriffscode beginnt bei `$7608` |
| `$E000–$F2BF` | Bisheriger RRB-Screen, unverändert |
| `$F300–$FD4F` | Physischer Titel-Screen; nur VIC-IV/DMA greifen darauf zu |
| `$10000–$11FFF` | DOS-RAM: nicht für Titel oder Engine verwendet |
| `$12000–$126FF` | Aktiver variabler Levelrecord, unverändert |
| `$12800–$13FFF` | Titelcache 1: 96 Kacheln |
| `$14000–$155FF` | 22 private Pixie-Puffer, unverändert |
| `$15600–$15A7F` | Engine-Color-RAM-Sicherung, unverändert |
| `$15B00–$1F7FF` | Titelcache 2: 628 Kacheln während Ladephase |
| `$15B00–$162FF` | Nach Abschalten des Titels: 2048-Byte-Bootstrap-Sicherung |
| `$1F800–$1FFFF` | DOS/Color-RAM-Fenster: nicht verwendet |
| `$20000–$3FFFF` | ROM: keine Schreibzugriffe |
| `$40000–$4EBCC` | VYTI-Staging, nur vor den drei Spieldateien |
| `$40000–$53F80` | VYLV, 81.793 Bytes, ersetzt das bereits kopierte Staging |
| `$54000–$5C2B7` | VYGR, 33.464 Bytes, 38 Typen/259 Frames |
| `$5C300–$5C4DB` | VYCL, 476 Bytes |
| `$5C500–$5F0FF` | Titelcache 3: 176 Kacheln |
| `$5F100–$5FB4F` | Sicherung der titelbezogenen Color-RAM-Zellen |
| `$FF82000–$FF82A4F` | Eigenes Titel-Color-RAM, vor Anzeige gesichert und danach restauriert |

Der Titel-Screen liegt im **physischen Bank-0-RAM**, nicht im dort für CPU-
Lesezugriffe eingeblendeten ROM. Er ist nicht in das PRG eingebettet; DMA schreibt
ihn aus dem validierten Staging. Weder DOS noch ROM werden verändert.

Die knappe Low-RAM-Codebelegung erfordert eine ausdrücklich zeitliche Nutzung:
Der Titelbootstrap belegt zunächst den späteren HUD-Zeichensatzbereich. Nach dem
Ausblenden sichert `titlecache.tc_save` diese 2048 Bytes in den jetzt ungenutzten
zweiten Titelcache. Nach Spielende kopiert der gemeinsame `exit_to_basic`-Pfad sie vor der BASIC-Rückkehr
zurück. Dadurch funktioniert erneut `RUN`, obwohl die Engine inzwischen ihren
Font nach `$4000` geschrieben hatte. Während eines sichtbaren Titels findet
keine solche Überschreibung statt. Aktiver Record und Pixiepuffer bleiben getrennt.
Die Cachebereiche liegen wie die bestehenden Enginepuffer im während RUN
verwendeten BASIC-Array-/String-RAM; das ML-Spiel benutzt keine BASIC-Arrays.

## Loader, IRQ, Palette und Übergabe

Alle vier Dateien verwenden denselben SEQ-Loader mit `SETLFS`, `SETBNK $FF6B`
vor `SETNAM`, `OPEN`, `CHKIN`, `CHRIN`, `READST`, DMA-Rücklese/Bytevergleich,
`CLRCHN` und `CLOSE`. Das Gerät wird einmal aus KERNAL `$BA` übernommen.
Erwartete vollständige Länge und EOF sowie die bestehenden additiven 16-Bit-
Summen werden geprüft. VYLV/VYGR-Signatur, Version und Anzahl werden zusätzlich
gegen die Originalheader geprüft; die vorhandene vollständige VYCL-Validierung
bleibt erhalten. Unveränderte Original-DAT-Dateien liegen im D81.

IRQ bleibt während SEQ-I/O eingeschaltet. Die Cursorabschaltung `$1120` wird
für die Titelanzeige gespeichert und auf `$FF` gesetzt, damit der BASIC-ROM-
Blinker nicht in den Titel schreibt. Der originale ROM-V920395-Blinkcode wird
im Hosttest ausgeführt. Die übrigen Cursorbytes werden nicht umdefiniert.
Nur Moduswechsel und DMA-Sicherung erfolgen atomar. Keine KERNAL-Ausgabe während
des sichtbaren Titels oder eines aktivierten Eingabekanals.

Der Titel sichert 38 VIC-IV-Register, 33×3 Palettebytes und seine 2640 Color-
RAM-Bytes. Beim Restaurieren werden ausstehende Legacy-Neuberechnungen vor
der präzisen Geometrie abgearbeitet; danach erfolgen keine HOTREG-Schreibzugriffe
auf Legacy-Register mehr; der gelesene Raster-Bitwert von `D011` wird für den gespeicherten
IRQ-Vergleich aus `D07A` rekonstruiert. Palette und Cursor werden restauriert,
danach initialisiert die unveränderte Engine ihr RRB-/Sprite-/HUD-System.
Gegnerpalette, Playerbank und Explosionen werden wie in Stage 5c eingerichtet.

`s3b.loading_complete` ist der spätere Stage-5e-Einstieg: alle vier Dateien sind
geprüft, Level 1 vorbereitet und der Titel noch sichtbar. Stage 5d-1 restauriert
hier den Videokontext und sichert den Bootstrap. `s3b.menu_or_game_start` springt
direkt nach `start`. Ein späteres Menü muss die dokumentierten Cache-Lebensdauern
berücksichtigen; insbesondere darf die Bootstrap-Sicherung keine noch sichtbaren
Titelkacheln ersetzen.

## Dateiformat und Fehler

VYTI v2: 60.365 Bytes. Header 26 Bytes, Little Endian (`<4s6H2IH`):
`VYTI`, Version 2, Breite 352, Höhe 240, Paletteanzahl 33, einzigartige Kacheln
900, Screenzellen 1320, Mapbytes 2640, Kachelbytes 57.600, Payloadsumme.
Danach folgen 99 RGB8-Bytes, 2640 Bytes physische FCM-Glyphindices und 57.600
Kachelbytes. Dieses relokierte Format gehört ausschließlich zu Stage 5d-1;
Stage-5d-0-Daten werden nicht ersetzt. Header und Paletteprefix werden zusätzlich
vollständig mit dem Build verglichen. Payload wird längen-/summengeprüft.

Fehler schließen immer Eingabekanal/Datei, verlassen einen bereits aktiven Titel
kontrolliert und zeigen `STAGE 5C LOAD ERROR $xx FILE dateiname,S,R` in BASIC. Keine
Spielengine wird mit ungültigen Dateien gestartet. Der bisherige Stage-5c-
Fehlerpräfix bleibt erhalten; der Dateiname identifiziert die betroffene Datei. Codes:

| Code | Ursache |
|---|---|
| `$01` | OPEN / Datei fehlt |
| `$02` | CHKIN |
| `$03` | READST, unvollständige/falsche Länge oder fehlendes EOF |
| `$04` | DMA-Rücklese stimmt nicht mit Eingabepuffer überein |
| `$05` | VYLV/VYGR-Header oder Level-1-Signatur |
| `$06` | Additive Dateisumme |
| `$07` | VYCL-/Levelrecord-Validierung |
| `$08` | Titelheader/Paletteprefix passt nicht zum Build |

## Reproduzierbarer Build und automatische Prüfung

```sh
git switch stage5d-1
git fetch origin --tags
python -m pip install -r tools/stage5d0-requirements.txt
python tools/build_stage5d1.py --kickass /path/to/KickAss.jar
PYTHONPATH=tests:tools python -m unittest test_stage5d1 -v
python tools/package_stage5d1.py
```

Geprüfte Python-Version: 3.12.14; Pillow 12.3.0 und py65 1.2.0.
KickAssembler 5.25 wird anhand des SHA256 geprüft; Java und Python 3 werden
benötigt. Konvertierung separat: `python tools/convert_stage5d1_title.py`.
Der vollständige Build erzeugt die Titeldatei erneut aus den archivierten
Original-PNG-/Palettendaten und kontrolliert beide Stable-Baselines. Das D81
enthält `STAGE5D1` (PRG) und vier SEQ-Dateien: VYTI, VYLV, VYGR, VYCL.
Dateiketten und Inhalte werden vollständig zurückgelesen. `SHA256SUMS.txt`
dokumentiert alle Build-Artefakte; das ZIP enthält Quellen, Assets und Tools.

Automatische Ergebnisse: `docs/stage5d1-test-results.json`.
50 Prüfungen im vollständigen Lauf erfolgreich (900,158 Sekunden). Nach
Entfernung der beiden nicht benötigten Debugregister aus der Sicherung wurden
sechs gezielte Prüfungen am endgültigen PRG erfolgreich ausgeführt (67,821
Sekunden einschließlich Wiederholung einer korrigierten Testvorgabe zur
BASIC-Hintergrundfarbe im Fehlerpfad). Keine PRG-Änderung durch diese
Testvorgaben-Korrektur. Insgesamt 51 eindeutige Fälle validiert; der Prüfbericht
unterscheidet vollständigen Vorlauf und Prüfungen des endgültigen Builds.
Kein eigener XEMU-Lauf.
 Tests führen die
assemblierten Instruktionen aus, mit begrenzten KERNAL-/DMA-/VIC-Modellen:
Titelpixel und Registergeometrie, unveränderte Caches über alle drei SEQ-Läufe,
IRQ-/Cursorzustand, Ladefehler, DOS-/ROM-/Color-RAM-Schutz, alle 100 Level,
Paletten und bisherige Kampf-/Clipping-/Neustartregressionen. Ein unabhängiger
Zweitbuild wird byteweise verglichen. Dies ersetzt keine Prüfung realer
VIC-IV-Rastereffekte oder KERNAL-Disk-I/O in XEMU.

## XEMU-Abnahme durch den Benutzer

Kein eigener XEMU-/Hardwarelauf behauptet. PAL, ROM V920395, BASIC 80×25:

1. `VYPER_STAGE5D1.d81` einlegen, `LOAD "STAGE5D1",8`, `RUN`.
2. Titel erscheint vollständig vor den drei großen DAT-Dateien. Während des
   Ladens keine beschädigten Zeilen, Farbsprünge, Cursor- oder Spriteartefakte.
3. Automatischer Wechsel zu Level 1: Originalfarben, HUD, Player und Animation
   wie Stage 5c. Einflug, Angriffe, ENTRY-Schüsse, Kollisionen und Explosionen prüfen.
4. `+`/`-`, LEVEL CLEAR/Joystickfortsetzung, Game Over/`R` und alle 100 Level
   unverändert. Die bisherigen freigegebenen Sonderlevel-Angriffssperren gelten.
5. `X`, normaler BASIC-Cursor, `DIRECTORY`, danach mehrfach `RUN`: Titel,
   vollständiges Laden und Spiel müssen erneut funktionieren.
6. Auf einer D81-Kopie eine DAT-Datei entfernen/beschädigen: lesbarer Fehler mit
   Dateiname, danach BASIC/DIRECTORY nutzbar und keine offene Eingabedatei.

Die ausdrückliche Benutzerbestätigung liegt vor; Referenz `stage5d1-stable`.

## Korrektur nach dem ersten XEMU-Test: flackernde obere Zeilen

Der Benutzer bestätigt die Titelanzeige, meldet aber Flackern und fehlende
Pixieteile in etwa den oberen drei Spielzeilen. Die normalisierten Renderer-,
HUD- und Kampfquellen sind weiterhin bytegleich zu Stage 5c Stable.

Nachgewiesener Fehler in `splash.t_restore_video`: D031/D016/D011 wurden bei
ausgeschaltetem HOTREG zurückgeschrieben, präzise VIC-IV-Geometriewerte
restauriert und HOTREG zuletzt aktiviert. Die Legacy-Schreibzugriffe können
noch als ausstehend gespeichert sein. Das Aktivieren löst dann erneut eine
Legacy-Modusinterpretation aus: unter anderem werden Screenpointer, Stride,
Color-RAM-Basis, Zeichenursprung und vertikale Grenzen überschrieben. Die
Engine übernimmt ihre vertikale Geometrie aus diesem restaurierten Kontext.

Belege: XEMU `targets/mega65/vic4.c` (Commit
`40dfef0d`, `vic_write_reg`, `vic4_interpret_legacy_mode_registers`) und
VIC-IV-Core `src/vhdl/viciv.vhdl` (Commit
`99538d0e735ee8d1567b8e5578b2e49d1d1a33bd`,
`viciv_legacy_mode_registers_touched`/`vicii_hot_regs_enable`). Die bisherigen
flachen Registermodelle hatten diese Nebenwirkung nicht abgebildet.

Korrektur ausschließlich im Titelbootstrap: zuerst den ursprünglichen
HOTREG-Zustand und D011/D016/D031 herstellen und eine eventuelle
Legacy-Neuberechnung abarbeiten. Danach HOTREG abschalten, die präzisen
VIC-IV-Felder zurückschreiben und HOTREG ohne weitere Legacy-Schreibzugriffe
auf den ursprünglichen Zustand setzen. D07A wird weiterhin nach D011
restauriert. Keine Renderer-, Timing-, Animations-, Paletten- oder
Originaldatenänderung. Sechs zusätzliche Sicherungsbytes erhalten auch die
von Legacy-Neuberechnungen betroffenen Zeichensatz- und
Spritepointer-Bytes (D068–D06A, D06C–D06E); Speicherbereiche und Dateiformate bleiben unverändert.

Neuer Regressionstest führt die tatsächliche assemblierte Restore-Routine
mit einem schmalen Modell der ausstehenden HOTREG-Updates aus. Er prüft sowohl
XEMUs Löschung bei HOTREG-off als auch das Core-Modell ohne diese Löschung,
jeweils bei ursprünglich an-/abgeschaltetem HOTREG. Der vorherige PRG-Stand
verliert die präzise Geometrie in beiden HOTREG-on-Fällen; die Korrektur besteht
alle vier Fälle. Das belegt den Restore-Fehler und seine Korrektur, aber keine
zyklusgenaue Reproduktion des sichtbaren Flackerns. Die visuelle Wirksamkeit
wurde inzwischen vom Benutzer in XEMU bestätigt. Die Nachprüfung betraf die
oberen drei Zeilen bei
ENTRY, FORMATION und ATTACK, vollständige Pixies, X/DIRECTORY/erneutes RUN.
Der Binärvergleich gegen den vorherigen PRG-Stand (SHA256
`6b96d2958da2a3846bdd4444029e8bcaf93ba5c75e6abc63bad2a6131d5ea84f`)
zeigt 590 geänderte Bytes ausschließlich bei `$4038–$45C9`; alle Änderungen
liegen im Titelbootstrap. Das PRG bleibt 43.777 Bytes groß, die übrigen
Programmbytes sind identisch. Stage 5d-1 ist nach ausdrücklicher Benutzerbestätigung Stable.

Stable-Referenz: `stage5d1-stable`; bestätigter Programmcommit `7d6e77f0c2da42065941ab9a2f93f8f589ce2dda`.
Die Stable-Sicherung ändert ausschließlich Dokumentation und lässt alle
Quellen und Release-Dateien byteidentisch. Kein eigener XEMU-/Hardwarelauf.
