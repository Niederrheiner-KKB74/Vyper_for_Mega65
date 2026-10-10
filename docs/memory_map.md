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
die BASIC-Exit-Abnahme bleibt offen. Details: [stage3b2.md](stage3b2.md).

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
