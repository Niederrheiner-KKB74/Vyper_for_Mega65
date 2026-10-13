# Stage 7b2 — konzentrischer Übergang und zweifarbige Gegnerprojektile

Testbuild für Issue #55 auf Branch `stage7b2`; noch **nicht Stable**.
Basis: Stage7b1 Stable (`stage7b1-stable`, Commit
`5d9c4f563f9fd3de7f5786b623791b7fc26e79e7`), getestet wurde dort
`23eb0bba7d7be781372b508dbf6667c3f75bdea4`. Die Stable-Quellen und Releases
bleiben bytegleich; das Buildskript prüft die Referenzen und vorhandenen Dateien.

## Screenshotabgleich und Geometrie

Die beiden vom Benutzer im ZIP „Screenshots 13-10-2026.zip“ gelieferten Bilder
liegen unverändert unter `assets/stage7b2/reference/`, mit SHA256-Prüfsummen.
Der Übergang zeigt von außen nach innen Blau, Gelb, Rot, Dunkelblau, wiederholt.
Der Projektilausschnitt zeigt einen weißen Schaft und eine rote untere Spitze.
Einzelbilder liefern keine belegte zeitliche Originalsequenz oder exakte
Spielpixel/RGB-Werte: die nachstehenden Parameter sind eine Testannäherung.

Playfield: X=0..239, Y=0..199, Mittelpunkt (120,100). Die rechte HUD-Grenze
bleibt unverändert. Ein 8×8-Raster aus 30×25 Halb-NCM-Zellen liefert die Tiefe
`d=min(x/8,29-x/8,y/8,24-y/8)` (ganzzahlig). Die 13 konzentrischen Ringe werden
mit d=12,11,…,0 aufgetragen. Rechteckgrenzen eines Rings sind
`[8d,240-8d) × [8d,200-8d)`; der innerste Bereich ist 48×8 Pixel.
Die Rahmen sind auf jeder Seite acht Pixel breit. Gegenüber Stage7b1 wachsen
sie jetzt auch in Y und sind keine vollhohen vertikalen Säulen.

Für die Farbphase gilt pro räumlicher Tiefe `d mod 4`: Blau, Gelb, Rot,
Dunkelblau. Daraus folgt beim zeitlichen Zeichnen von innen nach außen:
Blau, Dunkelblau, Rot, Gelb, Blau,…, zuletzt Blau am äußeren Rand.
Die schwarze Phase übermalt dieselben Ringe ebenfalls von innen nach außen;
bereits übermalte Ringe bilden zusammen ein gefülltes schwarzes Rechteck.

| Phase | 50-Hz-Frames nach Bestätigung | Dauer |
| --- | --- | --- |
| beschleunigte Sterne | 1..50 | 1,00 s, unverändert |
| Farbringen | 51..89, neue Ringe bei 53,56,…,89 | 0,78 s |
| schwarzes Rechteck | 90..128, neue Ringe bei 92,95,…,128 | 0,78 s |
| Normaltempo / nächster Level | 129 | ein Initialisierungsframe |

`FX_ACCEL_FRAMES`, `FX_RING_FRAMES`, Raster-/Ringkonstanten und die RGB-Tabellen
stehen in `stage7b2_transition.asm`. Das Raster entspricht der 8-Pixel-Halbzelle
des vorhandenen NCM-Aufbaus; andere Rastergrößen benötigen eine entsprechende
Anpassung des Halbzellen-Painters, nicht nur eine andere Zeitkonstante.

## Palette und Rendering

| Element | Bank/Index | RGB8 | Bedeutung |
| --- | --- | --- | --- |
| Übergangsblau | 1/52 | 0,102,238 | Screenshotannäherung RGB4 $06E |
| Übergangsgelb | 1/53 | 221,221,0 | RGB4 $DD0 |
| Übergangsrot | 1/54 | 170,0,0 | RGB4 $A00 |
| Übergangsdunkelblau | 1/55 | 0,0,170 | RGB4 $00A |
| Schwarz | 1/48 | 0,0,0 | bestehender Sternhintergrund |
| Projektilweiß | 2/10 | 255,255,255 | bestehende feste HUD-Farbe |
| Projektilrot | 2/13 | 238,0,0 | bestehende feste HUD-Farbe |

Die vier neuen Übergangseinträge verwenden die bisher ungenutzten NCM-Nibbles
4..7 derselben Subpalette. Sternfarben (Bank1/49..51), Originalgegnerpaletten,
COLOR19-Cycling, Player, Explosionen und HUD werden nicht umgefärbt. Alle zwölf
RGB-Komponenten der Einträge 52..55 werden beim ersten Spielstart gesichert
und vor BASIC vollständig wiederhergestellt; D070 wird bei jedem Zugriff
zurückgesetzt. Es gibt keine Paletteänderung pro Ring.

Der Übergang zeichnet in den vorhandenen 24.000-Byte-Sternpuffer
`$18000..$1DDBF`; Screen-/Color-RAM-Präfix, 375 Glyphreferenzen und RRB-Architektur
bleiben unverändert. Ein Halbzeichen benötigt acht geprüfte F018A-FILLs zu je
vier Bytes. Liegen beide Hälften im selben Ring, ersetzt ein 64-Byte-FILL
diese 16 Kleintransfers. Es wird ausschließlich die gewählte 8×8-Halbzelle beschrieben.
Während der farbigen Überdeckung dürfen Sterne nur außerhalb des schon
bedeckten Rechtecks Pixel löschen/setzen. Während der schwarzen Phase wird
nur ihre Position weitergeführt. Nach vollständiger Schwarzabdeckung wird der
Puffer gelöscht und aus den **aktuellen** 48 Sternpositionen wieder aufgebaut;
Y und Framephase werden nicht zurückgesetzt. So können Sterne keine Löcher in
die Ringe schlagen und hinterlassen beim nächsten Level keine Farbreste.
Die FPS-getaktete Zustandsmaschine enthält keine Warteschleifen auf Zeit oder
Eingaben. IRQ-Schutz umfasst nur die synchronen DMA-/Bitmaparbeiten.

## Binäre Amiga-Befunde und gewählte Projektilannäherung

`python tools/analyze_stage7b2_projectiles.py` prüft die drei Original-Hashes und
liest die USS-Chunks/ChipRAM/Farbregister. Der vollständige Befund steht in
`assets/stage7b2/projectile_analysis.json`.

Die gespeicherten SPR2..SPR7-Pointer lauten $21A92, $21ADA, $21B22, $21B6A,
$21BB2 und $21BFA. **An diesen gespeicherten Adressen** befinden sich dieselben
64 Bitplane-Bytes. Die nichtleere 3×7-Matrix lautet (`.` transparent):

```text
.1.
.1.
.1.
313
212
222
.2.
```

Die gespeicherten COLOR20..23, COLOR24..27 und COLOR28..31 belegen jeweils
Index1=$FFF (weiß), Index2=$E00 (rot), Index3=$344 (dunkelgrau). Der transparente
Index0 muss nicht zwischen den Registergruppen übereinstimmen. Das 28-Byte-
Muster ist zusätzlich sechsmal im separaten RAM-Dump und mehrfach in der ADF
nachweisbar; die absoluten Fundoffsets sind im JSON enthalten.

Diese Angaben sind binär belegt. Eine **aktive In-Game-Spriteausführung oder
vollständig zugeordnete Sprite-DMA-Controlstruktur** ist damit nicht bewiesen:
der Savestate zeigt das Menü, die gespeicherten POS/CTL-Felder sind null.
Der weiße Schaft/rote Fuß passen visuell zum Screenshot. Die Kandidatin hat
jedoch graue Flanken und 3×7 Pixel; die exakte sichtbare Originalhöhe lässt
sich aus dem vergrößerten Screenshot nicht zuverlässig ablesen.

### Revision nach Benutzerprüfung: Original3×7

Der Benutzer hat den Levelübergang unter XEMU als perfekt bestätigt und die
kleine1×4-Projektilannäherung verworfen. Auf seinen Auftrag wird jetzt die
oben binär ermittelte3×7-Matrix vollständig übernommen, einschließlich grauer
Flanken. Gegner: rote Spitze unten; Player: Spiegelung an der **horizontalen
Achse**, also umgekehrte Zeilenfolge und rote Spitze oben. Eine Links-rechts-
Spiegelung wäre wegen der symmetrischen Matrix optisch identisch gewesen;
die gewünschte Achse wurde deshalb ausdrücklich geklärt.

`analyze_stage7b2_projectiles.py` erzeugt reproduzierbar128 Bytes
`projectile_sprites.bin`:64 Player-,64 Gegnerbytes. Originalindex1→MCM01
(weiß),2→MCM11 (rot),3→MCM10 (grau),0→MCM00 (transparent). Jeder Originalpixel
entspricht einem nativen2-Pixel-Paar und jede Originalzeile wird zweimal
codiert: sechs native Pixel Breite und14 native Zeilen ergeben3×7 logische
Pixel bei unverändertem SPR640/V400. Übrige Spritebits bleiben transparent.

D01C=$3F aktiviert MCM für alle sechs Schusskanäle. D025=10 (weiß$FFF),
D026=13 (rot$E00); D027..D02C=16 (grau$344, RGB8 51/68/68) in der festen
Spritepalette Bank2. Index16 war bisher unbenutzt; Player/HUD/Explosionen
bleiben in ihren bisherigen Einträgen. Die drei Original-RGB-Komponenten
werden vorab gesichert und beim Exit exakt wiederhergestellt. Auch D025,
D026 und das ursprüngliche D01C werden wiederhergestellt. Levelpaletten und
Cycling ändern keine der drei Projektileinträge.

Beide Spritearten verwenden nun `CHARX+2*shotX-3`; damit liegt der mittlere
Pixel weiterhin auf derselben Schussachse. Der bisherige Player-X-Ursprung
wird nur für die breitere Grafik um zwei native Pixel angepasst. Logische
Koordinaten, Y-Ursprung, Geschwindigkeiten, Zielberechnung, Limits und
Flugbahnen bleiben erhalten. Keine Änderung am bestätigten Übergangscode.

**Trefferboxen bleiben ausdrücklich unverändert:** Player1×4, Gegner3×4.
Die größere Grafik enthält damit dekorative Pixel außerhalb der bisherigen
Trefferbox. Diese Revision betrifft die angeforderte Grafik, keine Änderung
der bisherigen Treffer-/Schussregeln. Die neue Grafik muss noch in XEMU
bestätigt werden; die vorherige Benutzerbestätigung betrifft den Übergang.

## Speicherprüfung

Zusätzliche Zustände: $1B90..$1B91 (D025/D026), $1B92..$1B94 (Sprite-Grau), $1BA0..$1BAB (12 RGB-Bytes),
$1BAC..$1BAD (Palette bereit / D070), $1BC0..$1BCF (Übergang), nach dem bisherigen
Spritebackup $1B60..$1B88 und vor dem Spielzustand ab $1C00.
Neue Helfer liegen in geprüften Assemblerlücken: $6650, $80C0, $8180, $87A0,
$B668, $B6C0, $BF10 und $BF96; Endgrenzen werden beim Assemblieren geprüft.
Der erweiterte Sternkern endet vor dem Filter. Der tatsächliche vollständige
Speicherplan liegt im Release als `memory-map.txt`.

Insbesondere **nicht** als Code benutzt: $5640..$56BF (Grafik-Rückkopiepuffer),
$6800 (DMA-Scratch), $6900 (Loaderheader), $6A00..$6ADF (Level-/Gruppenverwaltung),
$6F80 (Angriffsmetadaten), $10000..$11FFF und $1F800..$1FFFF (DOS).
Originalanimationen, private Pixie-Puffer und alle fünf DAT-Dateien bleiben
unverändert. Kein neues Laufzeit-DAT nötig.

## Reproduzierbarer Build und Prüfung

```sh
python tools/analyze_stage7b2_projectiles.py
python tools/build_stage7b2.py --kickass /pfad/KickAss.jar
PYTHONPATH=tests:tools:/pfad/test-deps python -m unittest test_stage7b2 -v
python tools/package_stage7b2.py
```

KickAssembler5.25 und sein SHA256 werden wie bisher geprüft. Die Python-Tests
verwenden den vorhandenen schmalen 6502/45GS02-/DMA-/VIC-Hostadapter; `py65`
ist die Testabhängigkeit. Er verifiziert reale assemblierte Instruktionen,
Dateilader, DMA-Ziele und Speicherzustände, ersetzt aber keinen VIC-Rastertest.
Das D81 enthält STAGE7B2 sowie VYTI, VYMN, VYLV, VYGR und VYCL. Das Build prüft
alle Datei-/Sektorketten und erstellt SHA256SUMS. Prüfresultate und Messwerte
werden separat im Release dokumentiert. CPU-Zyklen sind **Hostmodellwerte**,
DMA wird dort sofort ausgeführt; daraus wird keine XEMU-Messung behauptet.

## XEMU-Abnahme (noch offen)

D81 mounten, `LOAD"STAGE7B2",8`, `RUN`; Joystick **Port2**, Menü/F1.

- Titel/Ladevorgang, 32 animierte Menügegner, F1/F2/F3 und Levelwahl prüfen.
- Level1→2, 2→3, 99→100, 100→1 und zwei Übergänge hintereinander: frischer
  Feuerdruck nach LEVEL CLEAR; erst schnelle Sterne, dann vierfarbige
  konzentrische Expansion, dann schwarze Expansion, dann normaler Einflug.
- HUD bleibt unbeeinträchtigt, Ringe ohne Löcher/Flackern und danach keine
  Reste/Sternsprünge. Sichtprüfung auch während der äußeren Ringzeichnung.
- Beide Schussarten3×7 weiß/rot/grau: Player rote Spitze oben, Gegner unten. Treffer,
  maximal2/4 Schüsse, Schussrichtung, Explosion, steuerbarer Respawn,
  Game Over/R und Farben in verschiedenen Levelpaletten prüfen.
- +/- im laufenden Spiel ohne Effekt; X während Beschleunigung, Farbringen,
  schwarzer Phase und nach Spielstart. BASIC, DIRECTORY und erneutes RUN.

Kein eigener XEMU-/Hardwaretest durchgeführt. Freigabe/Stable/Merge erst nach
Bestätigung des Benutzers.

## Automatische Prüfergebnisse

39 vollständige Hostregressionen bestanden (keine Fehler oder übersprungenen
Tests). Anschließend wurde ausschließlich der Restore von D01C ergänzt; die
finale Binary bestand acht gezielte Wiederprüfungen: sechs
Übergangstests sowie CPU-Takt/Exit/RUN und Levelnavigation. Die Testberichte
enthalten die jeweils geprüften PRG-Hashes; keine Gleichsetzung zweier Builds.

Zwei unabhängige finale Builds: alle47 Builddateien plus Manifest bytegleich.
Normale Sterne im Hostmodell: Mittel8186,375 / Peak22020 CPU-Zyklen, im Mittel56
und maximal192 DMA-Jobs. Der Starcode und seine Daten sind zwischen
Vollregression und finalem D01C-Restore bytegleich. Übergangsanimation (Frames
1..128) Peak115907 CPU-Zyklen /448 DMA-Jobs nach Ganzglyph-Zusammenfassung.
Frame129 enthält zusätzlich die unveränderte vollständige Levelinitialisierung
und ist deshalb separat zu betrachten (996821 Modellzyklen,496 DMA-Jobs).
Die reale VIC-IV-/DMA-Zeit und eine mögliche sichtbare Rasterartefaktbildung
sind damit **nicht** gemessen. Sie bleiben Bestandteil der XEMU-Abnahme.

Die Grafikrevision besitzt einen eigenen Testbericht und Buildhash. Frühere
Hostlogs beziehen sich auf den im jeweiligen Bericht genannten Build; sie
werden nicht als Prüfung der neuen Spritebitmap ausgegeben.

Aktuelle3×7-Revision:16 Hosttests bestanden (Projektilmatrix/Mirror, Farben
über100 Level, unveränderte Trefferboxen, Übergang, Kampf, Respawn, R/X und
Wiederanlauf). Alle48 Builddateien zweier unabhängiger Builds bytegleich.
Stern-/Ring-/Übergangscode gegenüber dem vom Benutzer bestätigten Commit
`bd54520` binär unverändert. Details: `projectile-3x7-tests.txt`,
`test-report.json`, `reproducibility-report.json`.
