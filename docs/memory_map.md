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

## Stage 4a – isolierter Offscreen-/Clipping-Test (nicht Stable)

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
