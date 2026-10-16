# Speicherbelegung – bestätigter Stage-3a-2-Test

| Adresse | Verwendung | Status |
| --- | --- | --- |
| `$2001` | BASIC-65-Startzeile des Testprogramms | Stage 3a-2 |
| `$2100` | Maschinenprogramm (SYS 8448) | Stage 3a-2 |
| `$6000` | SEQ-Lesepuffer (256 Byte) | Stage 3a-2 |
| `$6100` | DMA-Rücklesepuffer | Stage 3a-2 |
| `$7000` | Level-1-Datensatz (849 Byte) | Stage 3a-2 |
| `$20000-$3FFFF` | ROM-Bereich; **nicht** als freies Daten-RAM verwenden | Fehlerursache frühere Stage 3a-2 |
| `$40000-$53F80` | VYLV.DAT, 81.793 Byte (Endadresse inklusiv) | erfolgreich getestet |
| `$54000-$5B8A7` | VYGR.DAT, 30.888 Byte (Endadresse inklusiv) | erfolgreich getestet |

Die Speicherbelegung der Stage-2ja-Engine ist separat aus deren ASM zu übernehmen; die oben genannten niedrigen Adressen gelten nur für das unabhängige Loader-Testprogramm.

Level-1-Datensatz: Quelle `VYLV.DAT` Offset `$328`, Länge `$351`, Anfangsbytes `01 00 02 16 10 00 02 00`.


## Stage 3b-1 – aus archivierter Engine und Assembly-Map geprüft

Alle Grenzen sind inklusiv. Die Engine-Adressen und Engine-Bytes bleiben unverändert;
die alten Stage-3a-2-Puffer oben werden ausschließlich in dessen eigenem Testprogramm verwendet.

| Adresse | Verwendung in Stage 3b-1 |
| --- | --- |
| `$1000–$12FF` | 32 Engine-Objektrecords à 24 Byte (Laufzeit) |
| `$1300–$131F` | Engine-Diagnostik (Laufzeit) |
| `$1400–$17FF` | reservierter Engine-Pfadarbeitsbereich |
| `$1800–$1FFF` | reservierter Engine-RRB-Arbeitsbereich |
| `$2001–$200D` | BASIC-Zeile `SYS 18432` → neuer Preloader `$4800` |
| `$2100–$2F67` | ursprünglicher Engine-Einstieg, Code und Zustandsbytes |
| `$3000–$30A8`, `$30C0–$30FF` | ursprüngliche Hardware-Spritegrafiken |
| `$4000–$47FF` | ursprünglicher leerer Mono-Charbereich |
| `$4800–$4B3E` | neuer Preloader, F018A-DMA-Liste, Meldungen und Loader-Zustand |
| `$5000–$57CF` | Engine-RRB-Screen (2.000 Byte) |
| `$5800–$580F` | ursprüngliche Spritepointer-Tabelle |
| `$6000–$67CF` | Engine-Farbvorlage; alte Loader-Puffer wären ein Konflikt |
| `$6800–$68FF` | neuer SEQ-Lesepuffer (256 Byte) |
| `$6900–$69FF` | neuer DMA-Rücklesepuffer (256 Byte) |
| `$7000–$72FF` | unveränderte initiale Engine-Objektrecords |
| `$7300–$73FF`, `$7400–$74FF` | unveränderte Orbit-X-/Y-Tabellen |
| `$7600–$7950` | neue Level-1-Prüfkopie (849 Byte); kein Engine-Eingang |
| `$8000–$80BF`, `$8100–$817F`, `$8800–$883F` | ursprüngliche NCM-Glyphdaten |
| `$9000–$97FF` | BASIC-Color-RAM-Sicherung der Engine |
| `$A000–$B47F` | unveränderte Original-Animationsframes; Typ 2 `$A200–$A57F` |
| `$B800–$BF06` | unveränderter Bewegungs-/Animations-/RRB-Code und Tabellen |
| `$C000–$C0BF` | ursprüngliche Kontrollglyphen |
| `$C800–$C8FF`, `$C900–$C9FF` | unveränderte dynamische Pixie-Glyphen/Guards |
| `$D800–$DFFF` | Color-RAM-Fenster bei CRAM2K; Engine stellt CIA-Zugriff wie bisher wieder her |
| `$20000–$3FFFF` | ROM-Bereich; kein Ladeziel |
| `$40000–$53F80` | VYLV.DAT; vollständiger DMA-Rückvergleich |
| `$54000–$5B8A7` | VYGR.DAT; vollständiger DMA-Rückvergleich |

Die neue DMA-Liste liegt in CPU-Bank 0 innerhalb des Loader-Bereichs;
es werden keine Engine-DMA-Listen überschrieben (die Baseline enthält keine).
Die Baseline-Banking-/VIC-Einstellungen bleiben erhalten. Assembly-Guards,
PRG-Bytevergleich und Loader-Host-Tests bestätigen die statischen Grenzen.
Stage 3b-1 ist vom Benutzer als stabil bestätigt (2026-10-10, `stage3b1-stable`).
Für neue Stages sind die Geräte-/XEMU-Regressionstests erneut erforderlich.
Details: [Stage 3b-1](stage3b1.md).


## Stage 3b-2 – zusätzliche Bereiche und Grafikreferenzen

Die Stage-3b-1-Dateien bleiben unverändert. In der neuen Version gelten dieselben
Engine- und Ladeziele mit folgenden Ergänzungen:

| Adresse | Verwendung |
| --- | --- |
| `$3200–$35D9` | begrenzter Levelparser, Grafikinitialisierung und DMA-Animationswrapper |
| `$4800–$4B49` | Preloader mit Parseraufruf vor RRB-Start |
| `$6A00–$6A07` | kopierter 8-Byte-VYGR-Verzeichniseintrag des ausgewählten Typs |
| `$7600–$7950` | Level-1-Record; Gegnerposition durch Gruppenlängen ermittelt |
| `$9800–$983F` | führender Blank-Guard, Glyph `$260` |
| `$9840–$987F` | oberer Teil des geladenen Originalframes, Glyph `$261` |
| `$9880–$98BF` | unterer Teil, Glyph `$262` |
| `$98C0–$98FF` | abschließender Blank-Guard, Glyph `$263` |

Die 22 Pfad-Pixies verwenden `$261/$262/$263`. Joystick-/Orbit-Slots und Bewegungs-
tabellen bleiben erhalten. `$6800/$6900` werden nach SEQ-Ende für den Frame-
Rückvergleich wiederverwendet. Neue Bereiche sind durch Assembly-Guards und
Engine-Bytevergleich geprüft. Die Grafikintegration wurde unter XEMU bestätigt;
auch die BASIC-Exit-Korrektur wurde am 10.10.2026 vom Benutzer bestätigt
(`stage3b2-stable`). Details: [stage3b2.md](stage3b2.md).

### BASIC-Exit-Korrektur in Stage 3b-2

Die alte Objektkopie überschreibt im bereitgestellten ROM V920395 nachweislich
Cursorzustand, Zähler, Zeichen und Farbe bei `$111F–$1123`. Nur Stage 3b-2 erhält
eine korrigierte Belegung im dokumentierten freien RAM `$1600–$1EFF`:

| Adresse | Verwendung nach der Korrektur |
| --- | --- |
| `$1600–$18FF` | 32 Objektrecords à 24 Byte, ersetzt `$1000–$12FF` |
| `$1900–$191F` | Diagnostik, ersetzt `$1300–$131F` |
| `$1A00–$1AFF` | reservierter, unbenutzter Pfadarbeitsbereich |
| `$1B00–$1EFF` | reservierter, unbenutzter RRB-Arbeitsbereich |
| `$1000–$15FF` | KERNAL-eigen; keine Engine-Schreibzugriffe mehr |

Assembly-Guards prüfen die Grenzen; der Builder gestattet ausschließlich die 53
betroffenen Adressoperanden. Alle oben beschriebenen Loader-/Grafikbereiche und
alle Stage-3b-1-Dateien bleiben unverändert. ROM V920395 und 80×25 sind bestätigt;
die Bank-4-Reservierung von BASIC 80×50 erklärt diesen Testfehler nicht.
[Ursache, automatisierte Tests und Artefaktvergleich](stage3b2_exit_investigation.md).

## Stage 3b-3 – Originalgrafik des Joystick-Spielers

Basis `stage3b2-stable` und dessen korrigierter KERNAL-freier Objektbereich bleiben
erhalten. Neue unveränderliche Quelle und Paletten im zuvor leeren Gap:

| Adresse | Verwendung |
| --- | --- |
| `$3600–$367F` | freigegebenes Spieler-NCM, 128 Bytes |
| `$3680–$36AF` | drei freigegebene 16-Byte-RGB-Tabellen |
| `$3700–$375E` | Spielerinitialisierung und RRB-Palette-Wrapper |
| `$C800–$C8FF` | bestehende Spieler-Glyphen und Guards; keine Animation mehr |

Spielerpalette Bank 2 ersetzt die bisherige Palette der deaktivierten
Hardware-Sprites; Gegnerpalette bleibt Bank 1. Bank 3 bleibt geschützt, denn
ihre ersten 16 Einträge bilden zugleich die C65/BASIC-ROM-Palette. GOTOX-Color-Byte 1 `$60` wählt nur für `$321/$322/$323` die alternative
Palette; jedes Gegnerfragment schaltet mit `$00` zurück. Alle Ladeziele, DMA-
Puffer, Screen-/Colorbereiche, BASIC-Backup, Orbit- und Gegnerglyphen bleiben
unverändert. Builder und Assembly-Guards prüfen die Grenzen und zulässigen
Patches. [Details und Abnahme](stage3b3.md). Stage 3b-3 am 10.10.2026 vom Benutzer als stabil bestätigt (`stage3b3-stable`).

## Stage 3b-4a – korrigiertes HUD, XEMU-Abnahme offen

Basis `stage3b3-stable`, unverändert erhalten. H640 mit `$D05A=60`, verdoppeltem
GOTOX-X und acht dynamischen Slots. Spielfeld bis X=240 / H640-X=480; HUD bis 639.
Nach dem gemeldeten Hintergrund-/Spurfehler: 64 Einträge / 128 Bytes je Zeile.

| Adresse | Verwendung |
| --- | --- |
| `$1A00–$1A18` | zentrale HUD-Werte, Player 2 inaktiv |
| `$1A20–$1A38` | Anzeige-Schattenwerte |
| `$1A40–$1A66` | HUD-Arbeit, Skalierung, physischer Farbzeiger, BASIC-Startfarbe |
| `$6B00–$6F7F` | zusätzliche 1152 Color-RAM-Bytes, leerer PRG-Bereich |
| `$3800–$3DB1` | HUD-/Start-/Store-Code und eigene F018A-Listen |
| `$3E80–$3EB6` | HUD-Anfangswerte, Farben, Lebenspositionen |
| `$3F00–$3FD1` | statische HUD-Attribute, Zeilen 20–24 |
| `$4000–$47FF` | private BASIC-Fontkopie mit dünnen 5×7-HUD-Glyphen |
| `$5000–$5C7F` | 25×128 Byte Screen, 3200 Byte |
| `$5C80–$5C8F` | verlegte Spritepointer, Hardware-Sprites bleiben deaktiviert |
| `$5C90–$5FD7` | statische HUD-Attribute, Zeilen 0–19 |
| `$7A00–$7EE1` | HUD-Screen-Prefixvorlage und Zeiger |
| `$9900–$9A55` | 38 dünne HUD-Glyphen mit Zeichencodes; außerhalb Loader-/Framepuffer |
| `$9000–$97FF` | bisherige Sicherung der ersten 2048 Color-RAM-Bytes |
| `$0FF80000–$0FF80C7F` | vollständiger verwendeter Color RAM, 3200 Byte |

Je Zeile Bytes 0–41: deckendes Schwarz über die gesamte Breite. 42–83: permanentes
HUD. 84–119: acht dynamische Slots plus Endmarker, 120–127: unsichtbarer Rest.
128-Byte-Zeiger ersetzen die bisherigen 80-Byte-Zeiger; Screen und Attribute laufen
parallel. Außerhalb des 2-KB-CPU-Fensters werden Attribute per 45GS02-Langzeiger
adressiert, mit gesicherten/restaurierten B/Z/Flags und temporär gesperrten IRQs.
Kein KERNAL-Zero-Page-Eingriff. Der gesamte berührte Color RAM wird vor den ersten
Engine-Schreibzugriffen gesichert und beim Exit restauriert. BASIC-/Cursorbereich
`$1000–$15FF` bleibt geschützt. Charset-/VIC-Zeiger und `$D05A` werden zurückgestellt.

Original-Ladeziele, Loaderlisten, SEQ-/Grafikpuffer, Levelkopie bis `$7950`,
Gegner-/Orbit-/Spieler-Glyphen bleiben erhalten. Leben verwenden `$C840/$C880/$C8C0`
und keine Hardware-Sprites. HUD-Farben in Bank 2 (freie Indizes 10–15; transparenter
Index 0 schwarz); Gegner Bank 1 und BASIC-ROM Bank 3 bleiben erhalten. Keine stabile
Freigabe ohne erneuten Benutzer-XEMU-Test. [Technik](stage3b4a.md),
[Fehlerursachen und Artefaktvergleich](stage3b4a_background_font_fix.md).

Stage 3b-4a einschließlich dünner Schrift am 10.10.2026 vom Benutzer bestätigt;
stabile Referenz `stage3b4a-stable`. Speicherbelegung und Release-Artefakte bleiben
bei der Abnahmedokumentation unverändert.

## Stage 3b-5b – neue, isolierte Bereiche

Die stabile Stage 3b-4a bleibt unverändert. Der Builder prüft die neuen Bereiche auf
leere Baseline-Bytes und erlaubt ausschließlich deklarierte Engine-Hooks und Mapping.

| Bereich | Verwendung |
| --- | --- |
| `$1B00–$1B47` | sechs Projektilslots als zwölf Arrays à sechs Byte |
| `$1B48–$1B5F` | Latch, PRNG, Teststatus, Cooldown, Koordinaten-/Divisionsarbeit |
| `$1B60–$1B88` | 41 gesicherte Sprite-/VIC-Register, vor dem Loader erfasst |
| `$8200–$87FF` | reservierter Projektilcode (tatsächliches Ende in Release-Assembly-Map) |
| `$8900–$890F` | dedizierte 16-Bit-Spritepointertabelle |
| `$8910–$8935` | zentrale Grafiktypübersetzung, 38 Einträge |
| `$8936–$895B` | 38 Bestätigungsflags (nur Index 14 bestätigt) |
| `$8A00–$8A3F` | weiße Player-Schussgrafik, Hardwarepointer `$228` |
| `$8A40–$8A7F` | rote Enemy-Schussgrafik, Hardwarepointer `$229` |
| `$9B00–$9FFF` | reservierter Spawn-Divisions-/Register-Restaurierungscode |

`$1B00–$1EFF` war dokumentierter unbenutzter RRB-Arbeitsbereich. Alle aktiven Objekte,
HUD-Werte bei `$1A00`, Loader-/Framepuffer `$6800/$6900`, Color-Backup `$6B00`, Levelkopie,
RRB-Glyphen und Font bleiben davon getrennt. Hardware-Sprites 0–5 sind ausschließlich
Projektile, 6–7 bleiben aus. Screen/Color/CHARXSCALE/HUD unverändert; Sprite-SPR640 und
V400 mit getrennten MSBs und vollständiger Wiederherstellung beim Exit. Es werden
keine Zero-Page-Adressen und keine zusätzlichen RRB-Objekte verwendet.
[Koordinaten, Register und Kollisionsvorbereitung](stage3b5b.md).

Stage 3b-5b am 10.10.2026 vom Benutzer als vollständig funktional bestätigt; stabile
Referenz `stage3b5b-stable`. Die Abnahmedokumentation ändert keine Speicherbelegung
oder Release-Artefakte.

## Stage 3b-5c – stabile Referenz, Kollisionen und unabhängige Explosionen

Die stabile Stage 3b-5b und ihre Speicherkarte bleiben unverändert.
Nur die neue Stage ergänzt folgende Bereiche (Grenzen inklusiv):

| Adresse | Neue Verwendung |
| --- | --- |
| `$1C00–$1CFF` | Laufzeitzustände; bei Spielstart vollständig genullt |
| `$1C00–$1C16` | Zustände der 23 Gegner (22 Pfade + Orbit) |
| `$1C17–$1C2D`, `$1C2E–$1C44` | unabhängige Explosionsframes/-ticks |
| `$1C45–$1C5B`, `$1C5C–$1C72` | eingefrorene Explosions-X/Y |
| `$1C73–$1C7C` | Playerzustand, Explosion, Todesposition, Blink-/Test-/Keyzustände |
| `$1C7D–$1C9C` | Kollisions-, 32-bit-Punkte-, Level- und UI-Arbeitswerte |
| `$4C00–$4E28` | Zustände, Keyboard, Neustart und Timer (siehe finale Assemblykarte) |
| `$85B0–$865F` | Statusgesteuerte bestehende Bewegung, Framekoordinator |
| `$8840–$8877` | ursprüngliche Pfadphasen und dünne Zusatzglyphen G/M |
| `$8B00–$8E13` | Software-AABBs, Treffer, Score/Highscore und Punkteformel |
| `$C100–$C7FF` | Originalexplosionen 0–6, je Blank + 128 NCM-Bytes + Blank |
| `$9D70–$9F85` | bedingter RRB-Renderer und GAME-OVER-Text |

`$C800–$C9FF` für Player/Orbit bleibt unberührt. Font-Glyphen G/M werden nur
in der privaten Fontkopie bei `$4038/$4068` ergänzt. Die bestehenden Loader-
/DMA-Listen, Originaldatenziele, Color-RAM-Sicherungen und ROM-/KERNALbereiche
bleiben erhalten. Der Builder prüft sämtliche neuen Bereiche innerhalb des
alten PRG auf Nullbelegung; nur sechs JSR-Hooks und der HUD-Default 175 werden
in belegten Baselinebereichen geändert. Keine neuen VIC-/Sprite-Kollisionsbits.
Am 10.10.2026 vom Benutzer unter XEMU bestätigt: `stage3b5c-stable`.

Korrektur: Es existieren sieben Explosionsframes. Der fälschlich zugeordnete
Player-Datensatz wird nicht mehr bei `$CA00` eingebunden; PRG-Ende `$C9FF`.
Neue Joystickfreigabe in BLINK benötigt keine zusätzlichen Laufzeitfelder.

## Stage 4a – stabiler Offscreen-/Clipping-Test (`stage4a-stable`)

Neue Stage auf `stage3b5c-stable`, keine Änderungen an der Referenz.
`$1D00–$1D3F`: signed Testposition, Clipdiagnose und privater Arbeitsbereich.
`$4E30–$4EFE`, `$8660–$874A`, `$8E20–$8F7D`: schmale Modus-/Renderhooks,
Testbewegung und Crop, ausschließlich in nachweislich nullbelegten Lücken.
`$CA00–$CAFF`: privater transparent geclipter NCM-Pixie mit zwei Blank-Guards;
PRG wächst um 256 Bytes. Aktiver Pixie-Bereich seit 11.10.2026 `[0,240) × [0,200)`;
alle 25 bereits vorhandenen RRB-Zeilen nutzbar. HUD und Speicherlayout bleiben unverändert. Keine neuen DMA-Listen,
Zero-Page-Nutzung oder Hardware-Sprite-Kanäle. Alle alten Symboladressen erhalten.
Exakte finale Codegrenzen: `releases/stage_4a/memory-map.txt`.
[Analyse, Diagnose und Testanleitung](stage4a_offscreen_clipping.md).

Stage 4a einschließlich Y=0–199 am 11.10.2026 vom Benutzer unter XEMU
als vollständig funktional bestätigt. Die Stable-Markierung verändert keine
Speicherbelegung, Programme oder Release-Prüfsummen.

## Stage 4b – Einflugcontroller und erweiterte RRB-Listen

Screen `$E000–$F2BF`, 192 Bytes/Zeile, 24 Pixies/Zeile; Color-RAM 4800 Bytes.
Zusatzbackup `$5000–$563F`, Rückkopie `$5640–$56BF`, Controller `$5700–$5C7F`,
DMA `$7500–$75A6`, signed Kollisionshelper `$7EE2–$7F70`, Testhelper
`$874B–$87FF`; 22 private Clippingpuffer `$10000–$115FF`.
Zustände/Positionen `$1D40–$1D60` / `$1E00–$1EFF`.
Kein Zugriff auf ROM als freien Speicher. [Vollständiger Vergleich](stage4b_level1_entry.md).

Stage-4b-Screenfix: physische Screenwrites jetzt per 32-bit-indirektem Store,
da SYS `$E000–$FFFF` per MAP auf KERNAL-ROM in Bank 3 abbildet. Drei Pointer
bei `$1A6C–$1A77`; HUD-Code endet jetzt `$3E59`, innerhalb der bisherigen
Grenze `$3E80`. Screen-RAM, RRB-Stride, Daten-/Clippingpuffer unverändert.

Stage-4b-Rasterkorrektur: `$5B80–$5C10` enthält Screen-Clear-Helper,
F018A-Descriptor und 100-Byte-Template mit GOTOX640/NCM200-Leereinträgen.
Innerhalb des bereits reservierten Controllerbereichs `$5700–$5C7F`;
Screen-/Color-RAM-Größe, Player/HUD-Geometrie und DMA-/Loaderdaten unverändert.

**Stage 4b Stable:** Der Benutzer hat den finalen DMA-Stand `12f4b40` in
XEMU bestätigt. Speicherlayout unverändert; Referenz `stage4b-stable`.

## Stage 4b-1 – ENTRY-Sichtbarkeit (Stable)

23 neue Flagbytes `$1D64–$1D7A`; Helper ab `$5C20`, vor `$5C80`.
Bisher freie Lücken, kein neuer DMA-/Grafikpuffer. Controllerlabels verschieben
sich durch drei Initialisierungsbytes; Kollisions-/Rendererhooks verwenden
denselben Sichtbarkeitstest. Übriges Stage-4b-Layout unverändert, insbesondere
Y=0–199, 24 RRB-Slots und Originaldaten. Keine Änderung der stabilen Releasefiles.
[Details](stage4b1_entry_visibility_fix.md).

Stage 4b-1 ist vom Benutzer unter XEMU bestätigt (`stage4b1-stable`).
Die Stable-Markierung verändert weder Speicherlayout noch Programm-/Release-Dateien.

## Stage 4b-2 – Angriff/Formation (Stable)

Neue Laufzeitdaten `$6F80–$6FFF`: 22 Varianten/Startanker/Bottom-Latches,
Kurvenpointer, Formationsoffset und Diagnose. Neue Code-Lücken ausschließlich
unter `$A000`: `$36B0–$36F2`, `$4B4A–$4BEB`, `$4F00–$4FBC`,
`$7951–$79F1`, `$895C–$89D3`, `$9A56–$9AE7`, `$9F10–$9FE2`.
Damit kein Code in ROMA/ROMC-Overlays; PRG-Größe unverändert.
Variabel geparste Originalkurven liegen in vorhandener Levelkopie
`$77E1–$7897` / `$789A–$7950`. Kleine Controller-/Return-/Sichtbarkeits-
und Kampfdispatch-Hooks, sonst unverändertes Stage-4b-1-Layout.
Y=0–199, 24 Slots, ROM und Stable-Artefakte bleiben erhalten.
[Details](stage4b2_attack_formation.md).

Stage-4b-2-Testkorrektur: keine neuen Laufzeitpuffer. Die Y-Anpassung (−8)
liegt als begrenzter Parserhelper im bestehenden Codefenster `$9A56–$9AE7`;
Scheduler-Sperre bei Player-Explosion/WAIT bis `$4FBC`. Keine ROM-Überlagerung.

Stage 4b-2 ist vom Benutzer unter XEMU bestätigt (`stage4b2-stable`).
Die Stable-Sicherung verändert keine Speicherbereiche oder Release-Dateien.

## Stage 4b-3 – gezielte Gameplay-Anpassungen (Stable)

Keine neuen Puffer oder DMA-Listen. Schussauswahl erweitert auf `$895C–$89F0`,
weiterhin unter Grafikbeginn `$8A00`. Timer- und Y-Konstanten im bestehenden
Code; zentrale, einmalige Y-Transformation wird in `e_ty` `$1E6E` gespeichert.
Sonst identisches Layout zu Stage 4b-2 Stable: Y=0..199, 24 RRB-Slots, HUD,
ROM und alle gesicherten Release-Artefakte bleiben erhalten.
[Details](stage4b3_gameplay_adjustments.md).

Stage 4b-3 ist vom Benutzer unter XEMU bestätigt (`stage4b3-stable`).
Die Stable-Sicherung verändert keine Speicherbereiche oder Release-Artefakte.

## Stage 4c – vier Kurvendeskriptoren (Stable)

Basis Stage4b-3 Stable, keine neue RAM-Allokation. Innerhalb bestehender freier
Lücke `$6F80–$6FFF`: Pointer-Low4 bei`$6FEC–$6FEF`, Pointer-High4 bei
`$6FF0–$6FF3`, Byte-Längen4 bei`$6FF4–$6FF7`, Kurvenzahl bei`$6FF8`.
Gegnerindizes bleiben`$6F80–$6F95`; alte Zweierfelder`$6FD8–$6FDD` nicht mehr benutzt.
Parser`$4B4A–$4BF0`, guarded Start/Helper`$9A56–$9AF2`, Motion`$9F10–$9FEA`,
alle unter`$A000`. Originalkurvenpointer Level1 bleiben`$77E1/$789A`.
Player/ENTRY-Schüsse/Renderer/Backupbereiche und gesamte übrige Speicherkarte
wie Stage4b-3. Quellen/Releases der Stable-Basis unverändert.
[Details](stage4c_attack_mapping_and_drift.md).

## Stage 5a – zentrale Levelverwaltung (Stable)

Aktiver Record neu in physischer Bank1 `$12000–$126FF`, bounded1792 Bytes.
Kopfkopie nur `$7600–$7607`; Kurvenparser nach `$7608–$76B1` verlegt.
Manager `$6000–$6627` ersetzt obsolete Color-Vorlage, Blank `$6700–$67FF`.
Runtime `$1D80–$1DB1` / `$6A20–$6AD7`, vier Gruppen und22 Grafikmetadaten.
Cachehelper `$3400–$3472`, optimierter Crop `$34A0–$3554`.
Vorhandene22 Pixiepuffer `$10000–$115FF`,24 RRB-Slots, Screen/Color-/BASIC-Backups,
Originaldaten und alle alten Stable-Releases unverändert. Kein neuer Code im ROM-Overlay.
[Gesamtkarte und genaue Änderungen](stage5a_level_management.md).

Stage 5a ist vom Benutzer mit funktionierenden Levelwechseln bestätigt
(`stage5a-stable`). Die Stable-Dokumentation verändert keine Speicherbelegung
oder Programm-/Release-Dateien.

## Stage 5b – 38 Original-Gegnergrafiken (Stable)

Von `stage5a-stable`, ohne Änderungen an dessen Dateien. Neue VYGR-Datei
`assets/stage5b/VYGR.DAT`:33464 Bytes, `$54000–$5C2B7`,38 Typen/259 Frames.
VYLV bleibt81793 Bytes bei `$40000–$53F80`;127 Bytes Abstand vor VYGR bleiben frei.
Die erweiterten Grafikdaten enden vor `$60000` und überlappen keine Engine-/ROM-
oder Levelpuffer. Verzeichnisende jetzt Dateioffset`$0138`; Loader-Summe`$5B75`.
DOS-Exit-Korrektur: Die22 privaten Pixiepuffer sind nach `$14000–$155FF` verlegt.
Der alte Bereich `$10000–$115FF` lag im reservierten DOS-RAM `$10000–$11FFF`
und darf nicht für Grafikpuffer verwendet werden. Record`$12000–$126FF`,
24 RRB-Slots und192-Byte-Screenstride bleiben erhalten. Keine Überlappung zwischen
Record, neuer Pixiepool-Belegung und Color-RAM-Fenster`$1F800–$1FFFF`.
Die neuen Puffer liegen wie der aktive Record im während RUN genutzten BASIC-
Array-/Stringbereich; das reine Maschinenspracheprogramm benötigt dort keine
BASIC-Arrays.147 PRG-Bytes gegenüber Stage5a ändern sich einschließlich
DMA-Operandrelokationen; Palette und Spielregeln bleiben unverändert. [Mapping, Originalpointer und Tests](stage5b_graphics_mapping.md).
Stage5b einschließlich DOS-Exit-Korrektur vom Benutzer vollständig bestätigt;
Referenz `stage5b-stable`. Die Stable-Sicherung verändert weder Speicherlayout
noch Quellcode oder Release-Dateien.

## Stage 5c – originale Levelpaletten (Stable)

Unveränderte Stable-Basis `stage5b-stable`. Neue VYCL:476 Bytes bei
`$5C300–$5C4DB`,72 Bytes Abstand hinter unveränderter VYGR. VYLV/VYGR,
Record`$12000–$126FF`, Pixiepool`$14000–$155FF`, DOS und ROM unverändert.
Palettencode`$6B00–$6CFF`, validierter Spiegel`$6D00–$6EDB`,
State`$6EF0–$6EF3`; kein Überlappen mit Angriffsdaten`$6F80–$6FFF`.

Der bisherige Laufzeit-Color-RAM-Sicherungspuffer`$6B00–$6F7F` musste nach
`$15600–$15A7F` verlegt werden, direkt hinter die privaten Pixiepuffer.
Nur die beiden DMA-Quell-/Zieladressen ändern sich; vollständige Sicherung und
Exit-Rückkopie bleiben erhalten. Der Bereich liegt wie Record/Pixiepool im
während RUN verwendeten BASIC-Array-/String-RAM; keine BASIC-Arrays im ML-Spiel.

Gegner: Bank1 Einträge17..24, NCM-Glyph-Farbbyte1`$10`; Explosionen: Bank1
Einträge0..15 unverändert, auch in privaten Crops Farbbyte1`$00`.
Player/HUD/Projektile: Bank2 unverändert; BASIC-ROM-Palette: Bank3 unangetastet.
D070 CPU-Bank wird beim Levelwechsel kurzzeitig umgeschaltet und vollständig
wiederhergestellt. Kein zusätzlicher Bankwechsel im 50-Hz-Animationspfad.
[Format, Speicherprüfung und Originalbeleglage](stage5c_original_palettes.md).
Stage5c vom Benutzer mit originalgetreuen Level-Farben, unveränderten Player-/
HUD-/Explosionsfarben und funktionierendem BASIC-Exit bestätigt (`stage5c-stable`).
Die Stable-Sicherung verändert weder Speicherlayout noch Quellcode oder Release-Dateien.

## Stage 5d-1 – Titel-/Loader-Integration (Stable)

Neue Quellen und Release separat; Stage 5c und Stage 5d-0 unverändert.
900 verlustfrei deduplizierte FCM-Kacheln liegen während des DAT-Ladens bei
`$12800–$13FFF`, `$15B00–$1F7FF`, `$5C500–$5F0FF`; eigener physischer Screen
`$F300–$FD4F`, Color-RAM `$FF82000–$FF82A4F`, Sicherung `$5F100–$5FB4F`.
VYTI-Staging `$40000–$4EBCC` wird vor VYLV vollständig in die Caches kopiert.
Alle drei Spieldatenziele und aktiven Record-/Pixiepuffer bleiben unverändert.
Titelbootstrap `$4000–$47FF` wird vor HUD-Fontinitialisierung nach
`$15B00–$162FF` gesichert (Titel bereits abgeschaltet); Helfer `$3340–$33AA`
restauriert ihn beim Exit für erneutes RUN. Keine DOS-/ROM-Überschreibung.
[Speicherkarte, Lebensdauern und IRQ-/Palette-Restaurierung](stage5d1_title_loader_integration.md).

Stage-5d-1-Nachkorrektur: HOTREG-Legacy-Neuberechnung erfolgt nun vor der
Restaurierung präziser VIC-IV-Geometrie. Zusätzliche Instruktionen bleiben
innerhalb des reservierten Titelbootstraps `$4000–$47FF`; keine Puffer-,
Screen-, Color-RAM-, DMA- oder Originaldatenadressen geändert.

Stage 5d-1 nach HOTREG-Korrektur vom Benutzer als Stable bestätigt
(`stage5d1-stable`). Die Stable-Sicherung verändert keine Speicherbereiche,
Quellen, Originaldaten oder Release-Artefakte.

## Stage 5d-1a B2 integration (Issue #41)

New signed ENTRY projection/cache $7700–$7889 fits below aimed shots $7951; ENTRY hooks grow its segment to $5700–$5B68, below row retirement $5B80. All title caches, screen, bootstrap backup, SEQ/DMA and game-data buffers retain Stage 5d-1 addresses/lifetimes. See [integration report](stage5d1_b2_integration.md).

Stage 5d-1a vom Benutzer am 12.10.2026 als Stable bestätigt (`stage5d1a-stable`). Stable-Sicherung ausschließlich in Dokumentation; keine Änderung an Speicherlayout, Quellen oder Release-Dateien.

## Stage 6b1 – Titel/Menu/Game-Phasen, noch nicht Stable

Spielengine unverändert aus `stage5d1a-stable`; kein Chip-RAM oberhalb `$5FFFF`.
Das originale Stage6a2-FCM-Menü nutzt die nach der Titelphase freien Glyphbereiche
`$12800–$1F7FF` und `$5C500–$5FFFF`. Die eigentlichen VYLV/VYGR/VYCL-Adressen
bleiben unverändert. `$7000–$9FFF` wird während des Menüs gesichert und durch ein
separat assembliertes Overlay ersetzt, vor Spielstart bytegleich restauriert.
Danach werden der gewählte Levelrecord und private Gegnergrafiken neu initialisiert.

Attic-DMA-Sicherungen: Bootstrap `$08000000–$080007FF`, Engine-Overlay
`$08001000–$08003FFF`, Titel-Color-Backup `$08004000–$08004A4F`, Menüasset
`$08010000–$080252BF`. VIC liest ausschließlich Chip-RAM. Persistenter Cycle-Code
bei `$3100`, ROMC-Gates bei `$7900` (identisch in beiden Phasen), originales D030
bei `$31F0`, Integrationsbrücke bei `$CB00`. BASIC- und DOS-Bereiche bleiben
unberührt. Exakte Grenzen, begründete Phasen-Aliase und Modus-/Palette-Restoration:
[Stage6b1](stage6b1_menu_integration.md), `releases/stage_6b1/memory-map.txt`.

### Stage6b1 Stable – unveränderte Speicherkarte

Benutzerabnahme am 12.10.2026 mit XEMU/ROM V920413, Joystick Port2.
Referenz `stage6b1-stable`, Programmcommit `5fa82452101cf690c3fa1f5eba0b172222541764`.
Alle bestätigten Speicherphasen, ROMC-/IRQ-Gates und FAST/VFAST-Korrekturen bleiben
unverändert; Stable-Markierung ändert ausschließlich Dokumentation und Git-Referenz.

## Stage7a1 – isolierter Sternentest, nicht Stable

Branch `stage7a1-starfield-test`, ab `stage6b1-stable`; historische Quellen und
Releases bleiben unverändert. Spielphasen-Ergänzung: 24.000 NCM-Bytes bei
`$18000–$1DDBF`, Glyphen `$600–$776`, statt der ersten 15 schwarzen Prefix-Zellen
je RRB-Zeile. Menü-Atlas nutzt denselben Bereich nur vor F1; Sterne werden erst
nach dem Engine-Handoff initialisiert. Keine zusätzlichen RRB- oder Sprite-Slots.

Neue CPU-Bereiche: `$4E10–$4E3F` Y-State, `$4E40–$4EF7` Binder,
`$B480–$B6FE` Kern/DMA, `$CD80–$CFD2` Adresstabellen, `$CFD8–$CFFF` State,
Palettensicherung und Profiling. Temporär `$6800` für ein DMA-Pixelbyte.
Bank1, Indizes48–51 sind getrennt von Gegnern/Cycling/Explosionen; zwölf RGB-
Bytes werden vor BASIC restauriert. Screen `$E000`, Stride192, 96 Einträge,
HUD und Clippingrechteck `[0,240)×[0,200)` bleiben unverändert.

Vollständige Karte, Phasenabgrenzung, DMA-/Timingnachweise und offene XEMU-Abnahme:
[Stage7a1-Prüfbericht](stage7a1_starfield_feasibility.md).

### Stage7a1 Stable – unveränderte Speicherkarte

Benutzerabnahme unter XEMU und Merge-Freigabe am 13.10.2026, keine erkennbaren
Probleme. Referenz `stage7a1-stable`, Programmcommit `ed22f0d4e4ca0bd8f5ff6ebaa5892135ce9bdd9a`.
Keine Code-, Speicher-, PRG- oder D81-Änderung durch die Stable-Markierung.


## Stage7a2 – vollständige Engine mit Sternen, nicht Stable

Stage6b1-Engine plus bestätigter Stage7a1-NCM-Hintergrund im separaten Branch
`stage7a2`. Gleiche24-KB-Fläche `$18000–$1DDBF`, Palette Bank1/48–51,
Y-State `$4E10–$4E3F`, Binder `$4E40–$4EF7`, Tabellen `$CD80–$CFD2`.
Sternkern jetzt `$B480–$B640`; kleiner durch entfernte Testbedienung/Profiling.
State `$CFD8–$CFFF`: aktiv `$CFD8`, Normalmodus `$CFD9`, Phase `$CFDA`;
ehemalige Raster-/Messbytes ungenutzt. `$6800` bleibt temporärer DMA-Puffer.

Keine neuen RRB-Slots/Sprites, kein neuer Grafikmodus und keine Änderung der
DOS-/Loader-/DAT-/Pixiepuffergrenzen. HUD-Neuaufbau überspringt bei aktiven
Sternen den Schwarzprefix, bindet anschließend unveränderte Sternzellen.
Level/R setzt weder Bitmap noch Phase zurück. Normalmodus-API vorhanden,
keine tatsächliche Beschleunigung. Vollständige Verträge und Messnachweise:
[Stage7a2](stage7a2_starfield_integration.md).

### Stage7a2 Stable – unveränderte Speicherkarte

XEMU-Benutzerabnahme und Merge-Freigabe am 13.10.2026. Referenz
`stage7a2-stable`, Programmcommit `1e40e3ba1278c9836cd484739f36de8afe839585`.
Keine Code-, Speicher-, PRG- oder D81-Änderung durch die Stable-Markierung.

## Stage7b1 – getakteter Levelübergang, nicht Stable

Separate Quellen/Release ab Stage7a2 Stable. Neue Statebytes `$1BC0–$1BCF`,
nach Sprite-Registersicherung und vor Kampf-RAM. Setup `$6650–$66C8`, FSM
`$B6C0–$B74D`, Spaltenhelfer/Pool-DMA `$B760–$B7B4`; RRB-Code weiterhin ab
`$B800`. Erweiterter Sternkern `$B480–$B657`, Schrittbyte `$CFDE`, Mode0/1.
Vier neue64-Byte-Vollfarbkacheln `$1DE00–$1DEFF` nach unveränderter Sternfläche;
Glyphen `$778–$77B`, unveränderte Bank1-Subpalette48–51.

`$5640–$56BF` ist ausdrücklich **belegter Laufzeit-Grafik-Rücklesepuffer**,
nicht freier Codebereich. Kein Overlayhelper dort. HUD/Screen-/Color-RAM-
Geometrie und DOS-/Originaldaten-/privater Pixiespeicher unverändert.
Projektilbitmaps bleiben `$8A00–$8A7F`; Form/Farbe geändert, Trefferboxen erhalten.
Details: [Stage7b1](stage7b1_level_transition.md).

### Stage7b1 Stable – unveränderte Speicherkarte

Benutzerbestätigung und Merge-Freigabe am 13.10.2026. Referenz
`stage7b1-stable`, Programmcommit `23eb0bba7d7be781372b508dbf6667c3f75bdea4`.
Keine Code-, Speicher-, PRG- oder D81-Änderung durch die Stable-Markierung.

## Stage7b2 — Testbuild, konzentrischer NCM-Übergang

Basis Stage7b1 Stable unverändert. Das bestehende24KB-NCM-Sternbitmap
`$18000–$1DDBF` trägt temporär die konzentrischen Ringe; kein weiterer
Grafikpuffer und keine geänderten RRB-Screen-/Color-RAM-Glyphreferenzen.
Bank1/52–55 sind vier isolierte Übergangsfarben, mit12-Byte-Backup
`$1BA0–$1BAB`, Flags/D070 `$1BAC–$1BAD`. D025/D026 gesichert `$1B90–$1B91`.
Übergangsstate weiterhin `$1BC0–$1BCF`. Gegnerkanäle2..5 Hardware-Multicolor,
Player0..1 monochrom; Bitmaps weiterhin `$8A00–$8A7F`, Hitboxen unverändert.

Neue Helfer: Setup `$6650`, Shared-Sprites `$80C0`, Palettebackup `$8180`,
Palettemapping/RGB `$87A0`, Sternabdeckungsfilter `$B668`, Annuluspainter
`$B6C0`, FSM `$BF10`. Endgrenzen sind assemblergeprüft; verbindliche genaue
Bereiche siehe Release `memory-map.txt`. Laufzeitscratch `$5640–$56BF`,
`$6800`, `$6900`, Levelmetadaten `$6Axx/$6F80`, DOS und private Pixie-Puffer
werden nicht als freier Code benutzt. Kein zusätzlicher Solidglyph-Pool.
Details: [Stage7b2](stage7b2_transition_and_projectiles.md).

### Stage7b2 — Original3×7-Projektile

Neue3-Byte-Sicherung Bank2/16 bei `$1B92–$1B94`; alle sechs Hardware-Sprites
MCM, Spritemapping/Helfer weiterhin `$80C0–$80FF`. Zusätzliche Spritepaletten-
Save/Restore-/Initialisierung `$BF96–$BFF2`, nach unverändertem Übergangs-FSM
und vor `$C000`. Die beiden64-Byte-Bitmaps bleiben `$8A00–$8A7F`.

## Stage7b3 — acht Projektilslots und verfügbare Gegnerliste

Neue120-Byte-Projektilverwaltung `$1F00–$1F77`, zwölf8-Byte-Arrays plus24
Skalarbytes. Eligibility-Liste22 Einträge `$1F80–$1F95`, Count/Mask/Scan/Kind
`$1F96–$1F99`, hinter Entry bis `$1EF3` in der bisherigen Engine-Reserve und
vor BASIC/Programm `$2001`. Assemblerguard trennt State und Liste.
Registersicherung43 Bytes `$1B60–$1B8A` enthält nun auch D02D/D02E.
Tabellenbasierte Snapshot-/Restore-Routine ab `$9B70` schafft freien Raum;
Eligibility/Sampling und IRQ-geschützter8-Sprite-Exit bei `$9C00`, Endguard
`$9D70` schützt den vorhandenen RRB-Renderer. Spritepointer weiterhin
`$8900–$890F`, unveränderte128 Grafikbytes `$8A00–$8A7F`.
Alle8 Spritebits, MCM/V400=$FF; fixed paletteBank2/10/13/16 unverändert.
DATs, DOS, Privatepixies, Screen-/Color-RAM und Sternbitmap unverändert.
Verbindliche Grenzen: Release `memory-map.txt` und
[Stage7b3](stage7b3_attack_and_shot_frequency.md).

## Stage7b4 — individuelle Schützenbegrenzung (Testbuild)

Unveränderte Stage7b3-Projektilarrays `$1F00–$1F77`; Besitzerarray
`$1F58–$1F5F`, Gegner nur Slots2–7. Neue temporäre Prüfbytes
`$1F9A–$1F9B` hinter der Eligibility-Verwaltung. Keine persistenten
Besitzerzähler und keine Änderung von Slot-, DMA-, Grafik- oder DOS-Puffern.
Selection/Restore wächst auf `$9C00–$9D16`, weiterhin vor Renderer `$9D70`.
Projektilkern mit zusätzlicher T-Prüfung bleibt vor `$85B0`.
Alle fünf DATs und Spritegrafiken bleiben bytegleich zum getesteten Commit
`a41e92ab8e4994a0a3288d60d63984d8593c8332`.
Details: [Stage7b4](stage7b4_per_enemy_shot_limit.md), Release `memory-map.txt`.
Keine Stable-Freigabe für Stage7b4.


## Stage7b5a — Ereignisplaner und VYSH (Issue #63, Testbuild)

Basis bleibt Stage7b4 `bd63682fa37df2853338b499f1210ec9dd2f56dc`.
`VYSH.DAT` (1116 Bytes) belegt nach der Loaderkorrektur `$B000–$B45B`. Alle fünf bisherigen DATs
und ihre Adressen bleiben bytegleich. Kein Zugriff auf ROM/DOS-Puffer.

Die ungenutzten residenten Altgrafik-Kopien für Typ3–6 werden ausschließlich
in der neuen Stage ersetzt; Original-VYGR und private Bank1-Frames bleiben
unverändert. Type1/2 bis `$A57F` bleiben für Altinitialisierung/Orbit erhalten.
`$A600–$A6FF`: aktueller11-Byte-Parameterrecord und aus Original-VYLV
rekonstruierte Y-Zulässigkeitsbitmaps. `$A700–$A78E`: zwei WORD-Ereignisse
je22 Actors, Pending-Masken und eigener LFSR/Scratch. `$A800–$AF07`:
Ereigniscode, Loader-Validator und generierte Offset-/CRC-Tabellen.
Sternencode ab `$B480` und sämtliche Bank1-RRB-Puffer bleiben unverändert.

Normaler Fire-Dispatch/SEQ-Loader `$895C–$89E9`; Name/Header/ROMA-Gate
`$9D30–$9D60`. Das Gate schaltet ROMA nur bei geschlossenen Kanälen und
maskiertem IRQ für die CRC-Prüfung aus und restauriert D030/IRQ exakt.
ENTRY-Hook passt bis `$5B74`, ATTACK-Hook bis `$9FED`; bestehende
Segmentgrenzen werden vom Assembler geprüft. Kein Umbau des RRB-Screens.
Details: [Stage7b5a](stage7b5a_original_fire_events.md),
Release `memory-map.txt` und `STAGE7B5A.sym`. Keine Stable-Markierung.


Stage7b5a-Loaderkorrektur14.10.2026: `$60000–$FFFFF` ist bei aktuellen
MEGA65/XEMU-Modellen nicht RAM (384KB-Grenze). Der alte VYSH-Zielbereich
`$70000` war fehlerhaft und führte nach dem ersten256-Byte-Chunk zu `$04`.
VYSH bleibt jetzt als physische Bank0-Datei bei `$B000–$B45B` resident,
vor Sternencode `$B480`, außerhalb des Menüs-Swaps und hinter Ereigniscode
`$AF07`. Neuer Codeguard vor `$B000`, DAT-Guard vor `$B480`.
DMA bleibt auch bei CPU-ROMA-Overlay physisch auf RAM gerichtet.
Das Hostmodell ignoriert Zugriffe auf den nicht vorhandenen Speicher wie
XEMU (Writes ignoriert, Reads `$FF`), statt diesen Bereich als RAM anzulegen.

## Stage7b5b – Entwicklungsstand, XEMU-Abnahme offen

Basis Stage7b5a `2954dc5` unverändert. Neue Projektil-Highbytes/Richtungen
`$1F9A–$1FB9`, eigener RNG/Scratch `$1FBA–$1FC4`, Format je Slot `$1FC5–$1FCC`.
Zusatzcode in freien Lücken unter `$A000`, ausschließlich normale CPU-RAM-Bereiche.
VYSH bleibt `$B000–$B45B`; keine neue High-RAM-/DMA-Allokation.
Exakte Assembly-Map: `releases/stage_7b5b/memory-map.txt`.
Begründung und Feldbelegung: `docs/stage7b5b_player_and_projectile_motion.md`.

## Stage8b – Audiointegration, XEMU-Abnahme offen

Basis `main`/Stage7b5b `f7350d6`, historische Quellen/Assets/Releases unverändert.
Phasengeteilter Loader bei physisch`$5000`, vor Wiederverwendung als BASIC-Color-
Backup nach`$E000` kopiert und in Attic`$0802C000–$0802CFFF` gesichert.
Audiocode`$1E000–$1F7FF` (CPU-Abbildung`$A000–$B7FF`), Ringe`$16400–$173FF`
und`$5C500–$5D4FF`, jeweils4096 Bytes. Erst nach Menüende aktiviert; keine Belegung
von DOS`$10000–$11FFF`, Color-Fenster`$1F800–$1FFFF`, ROM`$20000–$3FFFF`
oder nicht vorhandenem Haupt-RAM ab`$60000`.
VYSO-Archiv`$08030000–$080574BF`, darin Code ab`$08030200`, PCM ab`$08031A00`.
Aliasing-Proben bei`$0802B000/$0806B000`, jeweils32 Bytes. Bisherige Attic-Menü- und
Engine-Sicherungen bis`$080252BF` bleiben getrennt. Low-Mailbox`$1FD0–$1FD8`.
Register-/IRQ-erhaltende Gates nutzen freie bank0-Lücken; vollständige Assembler-
Map unter`releases/stage_8b/`. [Details](stage8b_sound_integration.md).
Kein Stable-Tag ohne Benutzerfreigabe.

Stage8b-IRQ-Fix: keine Speicheränderung. ROM-Trampolin66B0 behält sein Layout;
bei66C6/66C7 steht nun SEI/PHP statt PHP/SEI. Rückgabestatus wird mit I=1 gesichert,
bevor die native SYS-Abbildung verlassen wird. PLP bei66D8 öffnet kein IRQ-Fenster
im A000→E000-Loader mehr. Alle DAT-/Ring-/Attic-Adressen unverändert.

## Stage9a (Issue75, Entwicklungsstand)
Zusätzlich `$1FD9/$1FDA`: Bonusfortschritt P1/P2 (P2 inaktiv), hinter Audiomailbox
bis1FD8. Manager6000–65E4 enthält Abschluss-/Bonuslogik statt Hinweistext/Feuerwartephase.
Koordinator85B0–85FB bleibt gleich groß durch JMP-Gate in den Manager nach den
Explosionstimern; ursprüngliche Bewegungs-/Audio-/DMA-Adressen bleiben unverändert.
F1-Reset erweitert Brücke aufCB00–CD54; Sterntabellen abCD80 bleiben getrennt.
[Details](stage9a_auto_level_and_bonus_lives.md).

## Stage9b1 (Issue79, Entwicklungsstand)
Keine neuen Datenbereiche. ATTACK-Hauptcode9F10–9FE5, Cursor-/Bottom-Abschluss
und unveränderte Top-RETURN-Funktion36B0–36F5 (Anfang RETURN nun36D2).
Kurvenindex, signedXY, Cursor, Anker und Bottom-Latch bleiben an bisherigen
Adressen. Alle Audio-/Loader-/RRB-/DMA-Puffer unverändert.
[Details](stage9b1_cyclic_attack_curves.md).

## Stage9c3 (Issue85, eigenständiger Entwicklungsbranch)
Gemeinsame Laufzeitkarte gegen Stage9b1 abgeglichen:6A00–6AD7 und6F80–6FF8
sind weiterhin Gruppen-/Grafik-/Angriffsmetadaten, keine freien Codebereiche.
Neue residente Gates1920–19ED (nach Diagnose1900–191F, vor HUD1A00) und
6F00–6F45 (vor Angriffsdaten6F80). Gate-Seed/zusätzlicher Loader5448–55C0
nur während Boot; bestehender Audiobootstrap sichert/restauriert5000–5FFF
inklusive dieser Bytes für erneutes RUN. Gate-Kopie1920 wird vor Datei-I/O erstellt.
Neue Mailbox1FE0–1FED: finaler Score, Grund, Initial Level, Auswahl, Abschlusszähler,
Einmalsperre, BASIC-Exit und persistente Bestmarke; Abstand zu Audio/Bonus bis1FDA.
VYHS-Bootstaging40000 vor anschließendem VYLV-Load; Daten danach unverändert.
Attic08080000–080871DC enthält das Highscore-Modul,08090000–0809AFFF die
Phasensicherung2000–CFFF. Vor Tabellenphase Audio stoppen und BASIC-VIC/Color
restaurieren; Highscore-Screen7000, Font8000, SeitenstagingA000–A7CF,
privates ColorfensterFF82000–FF827CF mit Sicherung15000–157CF.
Keine neuen Puffer im DOS10000–11FFF, im ROM20000–3FFFF oder ab60000.
Originale Audio-Ringe16400/5C500, Core1E000, Attic-Samples sowie Level-/Grafik-
und Farbdateien bleiben unverändert. Menüatlas und VIC-/Colorzustand werden
beim Rückweg neu initialisiert. [Vollständige Karte](stage9c3_highscore_integration.md).

## Stage9c3a (Nachbesserung PR86)
Gemeinsame Phasenkarte unverändert zu Stage9c3. Die kürzere Game-Over-Ausgabe
schafft Platz für c_fire_state innerhalb9D70–9EF2; keine neue RAM-Allokation.
Der gepackte Koordinator85B0–85FB bleibt gleich groß, nur die Zustandsabfrage
wird durch einen JSR gleicher Länge ersetzt. Audio-/Projektildaten und ihre ABI
bleiben unverändert. Highscore-Farbindex4 bleibt für gelbe Texte statisch,
Index2 zyklisch für den Rahmen; keine zusätzlichen Palette-/Color-RAM-Bereiche.
Neue Artefakte separat unter releases/stage_9c3/stage9c3a/.

Stage9c3a-Navigationskorrektur: keine neue Datenallokation. Zeile18 wird nur
im vorhandenen SeitenstagingA000 und Color-Puffer6000 modusspezifisch vorbereitet;
Spalten5..74 werden im Namensmodus gelöscht, Hinweis19..59 im Tabellenmodus Gelb4.
Zusätzlicher UI-Helper bleibt unterA000; Overlaybudget und residente Gates unverändert.


## Stage10a – getrennte Identitäten, unveränderte Stable-Basis

Baseline: bestätigte Stage9c3a/main36d5a4b. Nur neue Stage10a-Quellen/Releases.
`$1B00–$1B0F` enthält zwei8-Byte-Records (Score4,Level2,Leben2),
`$1B10–$1B19` Modus/Identität/Abschluss-/Resume-/Gate-/HUD-Zustand,
`$1B20–$1B23` Session-Highscore. Der bislang unbenutzte reservierte RRB_WORK-
Bereich endet damit weiterhin vor dem Projektilbackup1B60; keine Überlagerung
mit HUD1Axx, Kampf1Cxx oder Audio-/Bonus-/HS-Mailbox1FD0..1FED.
Die vorhandenen Bonusbytes1FD9/1FDA werden jetzt identitätsbezogen verwendet.

Native Gate/Wechsel/Resume9900..9A04 ersetzt eine seit dem Originalmenüfont
unbenutzte Fontkopie. ControllerA000..A1E5/A580..A5E9 ersetzt unbenutzte eingebettete
Legacy-Typ1-Frames beziehungsweise verwendet freien Platz hinter Typ2; tatsächliche VYGR-Assets und private Grafiken bleiben
unverändert. ROMA-aus/IRQ-Gate vor CPU-Codezugriff, keine KERNAL-I/O darin.
Der über s3b2.animate noch aufgerufene s2ja-Animationspfad und die Orbit-
Initialisierung bleiben bytegleich; sämtliche Typ2-FramesA200..A57F werden
erhalten und beim Build mit der Stable-PRG verglichen.

Neue Identitätsdaten liegen außerhalb des Highscore-Overlaybackups2000..CFFF
und überleben die Tabellenphase. Residenter1920-Gate bleibt unter1A00,
GameOver-Koordinator6F00 unter6F80. Alle DOS-/ROM-/Audio-/Attic-/Titelbereiche
bleiben wie Stage9c3a; kein neuer High-RAM-Puffer. Das vollständige Assembler-
Mapping steht in releases/stage_10a/memory-map.txt.
[Phasenprotokoll und Amiga-Evidenz](stage10a_two_player_mode.md).

## Stage10a1 – phasenfeste Loaderkopien und F2-HUD

Entwicklungsstand im bestehenden Branch stage10a/PR88. Alle Stable-Dateien
unverändert. Neue ChipRAM-Belegung8880..88BE (vorher frei nach8878, vor8900)
für Loadercache-Helfer, internes Flag und zwei F018A-DMA-Listen. Eine einmalige
Kopie5000..563F liegt im freien Attic080A0000..080A063F, hinter dem
Highscore-Archiv08090000..0809AFFF. Sie restauriert den von Color RAM verdrängten
Audio-/Highscore-Bootstrap erst nach Rückkopie der Farben. Die vorhandene
Titelkopie4000..47FF wird vor jedem Resume erneut aktiviert. Keine Allokation
im DOS-RAM, ROM-Bereich oder über5FFFF-ChipRAM.

1B1A/1B1B nutzen zwei bislang private Reservebytes für F2-HUD-Stil/Zeile.
38BE..<3963 ersetzt ausschließlich den unerreichbaren alten Fontkopierkörper
mit Stil-/Trennlinienhelfern; Originalmenüfont bleibt unverändert.
9900..99B2 und99B9..9A29 enthalten Gate-/Resume-/F2-Ausgabe, weiterhin vor9A56.
Der normale Wechsel erfolgt per JMP aus der Hauptschleife, ohne Rücksprungframes
zu verwerfen; bestehende Audio-ABI und alle Typ2-FramesA200..A57F unverändert.
F2-Zeilen: P2Label/Score/Level13/14/15, Leben16..20, Trennbalken12,
Form./Att.22/23, Rand24. F1-Bilddaten bytegleich geprüft; RRB192Bytes,
PlayfieldX<240 und Y0..199 unverändert.
Vollkarte: `releases/stage_10a/stage10a1/memory-map.txt`.

### Stage10a1 – HUD-Nachbesserung in PR88

Keine zusätzliche Speicherallokation: statischer Aufbau invalidiert die bereits
vorhandenen25 Shadowbytes1A20..1A38. HUD-Code3800..3E7D (exklusiv3E7E),
Defaults weiterhin3E80. Zweiter F2-Balken nutzt den bestehenden Präfix von Zeile21
(Screen E000+21*192+42,42Bytes; entsprechende Color-RAM-Bytes), ohne RRB-Suffix,
Playfield oder Lebenszellen anzutasten. Oberer Balken12 und Punkte22/23 bleiben.
F1-Refresh korrigiert initiales P1-Lebensfeld und stale Vorlage Att.115 auf den
unveränderten dynamischen Wert175. Keine Charset-/Spielparameteränderung.

### Stage10a1 – Originalregeln/Get ready in PR88

1B1C..1B1F:100-Frame-Countdown, vorherige Animationspause, temporäre Zeile,
Eingabeframe-Sperre; bereits reservierte private2P-Bytes. Neue nativeGates9A2A..9A49,
mappedAF08..AFD4, sicher vorAttack9A56 bzw.VYSHB000. twop.gate sperrt IRQs und
restauriert D030. ControllerA000..A1E3; Typ2A200..A57F bleibt erhalten.
Kein neuer Grafik-/Audio-/DMA-Puffer. Get-ready-Texte nur in dynamischen Tails
von Screenzeilen17/19 abByte84, entsprechende Color-RAM-AdressenFF80000+row*192+84.
Beide Zeilen werden danach über den vorhandenen Screen-/Farben-Löscher restauriert.
HUD-Präfixe, Sternbitmap18000..1DDBF, Paletten und Audio-ABI unverändert.

## Stage10b1 — isolierte Hardwarediagnose (Issue89, nicht produktiv)

Nur `src/tests/stage10b1.asm`; keine Änderung der Stage10a1-Speicherkarte.
Code `$2100–unter$4000`, Font `$4000–$47FF`, Diagnosepuffer
`$4800–$4FC7` (1992Bytes, bleibt nach X erhalten), Palettensicherung
`$6000–$6BFF`, NCM-Rasteratlas `$8800–$8BFF`, Original-Player-Pixie
`$9040–$90BF`, Spritegrafiken `$9200–$927F`, Pointer `$9300`.
Screen-/Color-Vorlagen `$A000–$B2BF` und `$B300–$C5BF`.
Physischer RRB-Screen `$E000–$F2BF` wird ausschließlich per DMA geschrieben;
375Rasterglyphen `$18000–$1DDBF`. Alle32KiB Color-RAM
`$FF80000–$FF87FFF` werden nach `$40000–$47FFF` gesichert und vor BASIC
restauriert. `$20000–$3FFFF` bleibt ROM, kein Puffer.
Details und Exportformat: [Stage10b1](stage10b1_viciv_hardware_comparison.md).
