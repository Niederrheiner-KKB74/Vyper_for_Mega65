# Stage 3b-1 – Loader vor unveränderter Stage-2ja-Engine

## Stand und Umfang

Stage 3b-1 ist erfolgreich mit dem offiziellen KickAssembler 5.25 assembliert.
PRG und D81 sind strukturell geprüft; 12 Host-Tests des assemblierten Loaders
bestehen. **Ein XEMU-/Hardware-Test von Stage 3b-1 steht aus.** Die vom Benutzer
bestätigten Laufzeittests beziehen sich weiterhin auf Stage 2ja und Stage 3a-2.

Die Engine wurde aus dem vorhandenen `Stage_2ja_STABLE_ARCHIVE.zip` übernommen.
Das darin enthaltene Build-ZIP hat SHA-256
`89380c289e5b706278a6c70fffd85de64350739db99031504d255540f252f23a`.
Sein PRG lässt sich mit dem offiziellen KickAssembler 5.25 bytegenau reproduzieren,
obwohl die historische Archiv-README eine 65CE02-Variante des Assemblers nennt.
Die Engine verwendet hier ausschließlich passende 6502-Instruktionen.
Beide Baseline-Releases und die bestehenden Loader-Quellen bleiben unverändert.

## Ablauf

Die neue BASIC-Zeile startet mit `SYS 18432` bei `$4800`. Die Startsequenz
arbeitet vor jeder Änderung des Engine-Videomodus im normalen BASIC-Kontext:

1. SEQ-Dateien von Gerät 8, logischer/sekundärer Adresse 2 öffnen. `SETBNK ($FF6B)`
   mit A=0 und X=0 erfolgt wie in Stage 3a-2 vor `SETNAM`.
2. `VYLV.DAT` mit 81.793 Byte nach `$40000`, danach `VYGR.DAT` mit 30.888 Byte
   nach `$54000` laden. Die Routine verwendet dieselbe F018A-DMA-Liste
   (`$0A,$00`, COPY, 11-Byte-Descriptor, Modulo 0) und Registerfolge
   `$D702=0`, `$D704=0`, `$D701=Listen-Hibyte`, `$D705=Listen-Lobyte` wie Stage 3a-2.
3. Jeden 256-Byte-Block bzw. letzten Teilblock per DMA zurücklesen und byteweise
   mit dem SEQ-Puffer vergleichen. Der Bankwechsel innerhalb von VYLV bleibt erhalten.
4. Zusätzlich die vorhandenen 16-Bit-Bytesummen mit den Repository-Originaldaten
   vergleichen: VYLV `$5CA2`, VYGR `$1FE9`. Diese Summen sind keine kryptografische
   Integritätsprüfung; der Build prüft die vollständige Dateiidentität per SHA-256.
5. Level 1 von `$40328` mit `$0351`/849 Byte nach `$7600` kopieren und dessen
   Signatur `01 00 02 16 10 00 02 00` prüfen, wie in Stage 3a-2.
6. Nach `CLRCHN`/`CLOSE` die Meldung `VYLV + VYGR LOADED AND VERIFIED` ausgeben.
   Sie bleibt 60 Rasterframes sichtbar (ca. 1–1,2 Sekunden). Während eines aktiven
   Eingabekanals und während des RRB-Spielbetriebs erfolgen keine Textausgaben.
7. IRQ-Status des Einstiegs wiederherstellen und direkt zur unveränderten Engine
   bei `$2100` springen. Sie speichert und restauriert ihre VIC-/Color-RAM-Zustände
   wie bisher. Bewegungen, 24 Pixies, sieben Typ-2-Animationsframes, Joystick Port 2,
   SPACE, +/- und X bleiben unverändert. Die geladenen High-RAM-Daten und die
   Level-Prüfkopie werden von der Engine nicht gelesen.

Bei einem Ladefehler wird der Eingabekanal aufgeräumt, eine Fehlernummer und
`READST` ausgegeben und ohne RRB-Initialisierung nach BASIC zurückgekehrt.
Die Erfolgsstrecke verändert keinen Engine-Bytebereich. Die Startsequenz selbst
verwendet selbstmodifizierenden Code und eigene Zustandsbytes, wie der Loader.
Wie Stage 3a-2 liest sie die bekannte erwartete Dateilänge; angehängte Zusatzbytes
werden zur Laufzeit nicht gesucht. Das ausgelieferte D81 enthält exakt die Originaldateien.

| Fehler | Bedeutung |
| --- | --- |
| `$01` | OPEN fehlgeschlagen / Datei nicht verfügbar |
| `$02` | CHKIN fehlgeschlagen |
| `$03` | READST-Fehler oder EOF vor der erwarteten Länge |
| `$04` | DMA-Rücklesevergleich fehlgeschlagen |
| `$05` | Level-1-Signatur falsch |
| `$06` | Bytesumme einer Datei falsch |

Gegenüber der Baseline werden zusätzlich alle READST-Fehlerbits außer `$40` (EOF)
abgewiesen; auch der OPEN-Fehlerpfad führt durch die Kanalbereinigung.

## Speicherentscheidung

Die originalen Loader-Puffer `$6000/$6100` würden die 2.000-Byte-Farbvorlage
`$6000–$67CF` überschreiben. Die originale Level-Kopie `$7000–$7350` würde
Objektinitialisierung und Orbit-X-Tabelle überschreiben. Deshalb werden sie
nach `$6800`, `$6900` und `$7600` verlegt. Loader-Code, DMA-Liste und Zustandsbytes
liegen gemeinsam bei `$4800–$4B3E`, hinter dem leeren Mono-Charbereich
`$4000–$47FF` und vor dem RRB-Screen `$5000`. Die Engine besitzt keinen
High-RAM-Bereich in den beiden Ladezielen. Die vollständige Karte steht in
[memory_map.md](memory_map.md); Assembly-Guards sichern die Grenzen ab.

Der Build vergleicht **jedes PRG-Byte bei `$2100–$C9FF` außerhalb des zuvor
ungenutzten Bereichs `$4800–$4FFF`** mit dem archivierten Stage-2ja-PRG.
Damit bleiben auch absolute Adressen, Grafik-/Objektdaten, Renderer, Animationscode
und die Exit-Routine unverändert. Nur der BASIC-SYS-Text vor `$2100` und der
neue Loader im freien Bereich unterscheiden sich. Es wurden keine Speicherbank-
oder ROM-Mapping-Änderungen ergänzt. Die Startbedingungen entsprechen normalem
MEGA65 BASIC mit dem Setup der bereits getesteten Baselines.

## Reproduzierbarer Build

Voraussetzungen: Python 3.9+, Java (hier OpenJDK 21), offizieller KickAssembler 5.25.
KickAssembler ist ein separates Werkzeug; die JAR wird nicht ins Repository aufgenommen.
Der Build prüft deren festgelegten SHA-256:
`9592a39336e73a1db8b4a7749256d62d29b113b1c7f0f6c86ea43870ebd9ae1f`.

```sh
# Aus dem Repository-Stamm; ZIP von der offiziellen Website, TLS prüfen.
curl --fail --location https://theweb.dk/KickAssembler/KickAssembler.zip -o /tmp/KickAssembler.zip
python3 -c "import zipfile; z=zipfile.ZipFile('/tmp/KickAssembler.zip'); open('/tmp/KickAss.jar','wb').write(z.read('KickAss.jar'))"
python3 tools/build_stage3b1.py --kickass /tmp/KickAss.jar
```

Der Builder extrahiert nur die originalen Animations-Binaries aus dem Baseline-ZIP
in ein temporäres Arbeitsverzeichnis, prüft dessen SHA-256 und CRCs, assembliert die
vollständige Quelle und schreibt unter `releases/stage_3b1/`:
PRG, D81, Quellkopie, Symboltabelle, Speicherkarte, Build-Bericht und SHA-256-Liste.
Alternative: `KICKASS_JAR=/pfad/KickAss.jar` setzen oder `--output /pfad/zum/build`
verwenden. Keine `/mnt/data`-Pfade, keine Änderungen an den Baselines.
Zwei unabhängige Builds erzeugten byteidentische Artefakte.

Das D81 enthält `STAGE3B1` als PRG (43.521 Byte / 172 Blöcke),
`VYLV.DAT` als SEQ (81.793 Byte / 323 Blöcke) und
`VYGR.DAT` als SEQ (30.888 Byte / 122 Blöcke). Der Builder prüft
Dateinamen/-typen, vollständige Sektorketten, Nutzdaten, Blockzahlen und sämtliche
BAM-Bits/Freizähler. Ein D81 ist hier per LOAD/RUN startfähig; kein Autostart-Bootsektor.

## Automatische Tests

```sh
python3 -m venv /tmp/vyper-stage3b1-tests
/tmp/vyper-stage3b1-tests/bin/pip install -r tests/requirements-stage3b1.txt
/tmp/vyper-stage3b1-tests/bin/python -m unittest discover -s tests -p test_stage3b1.py -v
```

12 Tests bestanden: Baseline-/D81-Vergleich, vollständiges Laden beider Dateien
(einschließlich 64-KiB-Bankwechsel und Teilblöcken), Level-Kopie und Übergabe an
`$2100`, OPEN-Fehler, fehlende zweite Datei, CHKIN-Fehler, Timeout, weiteres
READST-Fehlerbit, zu kurze Datei, DMA-Rücklesefehler, falsche Level-Signatur und
falsche VYLV-/VYGR-Bytesummen. Fehlerpfade müssen nach BASIC statt zur Engine führen.

Die Tests führen das assemblierte Loader-Maschinenprogramm mit py65 aus.
KERNAL-Aufrufe, DMAgic und Rasterregister werden explizit modelliert. Geprüft werden
auch SETBNK-Reihenfolge, Kanalbereinigung, ausbleibende Ausgabe bei aktivem Kanal,
IRQ-Maskenrestaurierung, 883 korrekte DMA-Transfers und unveränderte Engine-Bereiche.
**Das prüft keine echten MEGA65-Geräte, Interruptabläufe oder VIC-IV-Ausgabe.**

## Unter XEMU prüfen (Akzeptanz noch offen)

1. D81 in Laufwerk 8 einlegen; im normalen BASIC `LOAD"STAGE3B1",8` und `RUN`.
   Beide Ladezugriffe müssen enden, die Erfolgsmeldung erscheinen und danach die
   RRB-Ansicht starten. Keine Fehlernummer, kein Hängenbleiben am Raster-Warten.
2. Direkt mit der unveränderten Stage 2ja im gleichen XEMU-/ROM-/Video-Setup
   vergleichen: 24 Pixies, Farben, Positionen, Orbit-/Pfadbewegungen und alle
   sieben Animationsframes; keine Reste/Artefakte beim RRB-Clearing.
3. Joystick Port 2 in alle Richtungen, Begrenzungen, SPACE und +/- vergleichen.
   Die geladenen Level-/Grafikdateien dürfen Bewegungen nicht beeinflussen.
4. Mit X beenden. BASIC-Videomodus, Farben, Eingabe und Verhalten müssen der
   Stage-2ja-Rückkehr entsprechen. PRG erneut per LOAD/RUN starten und vergleichen.
5. Separat auf einer D81-Kopie eine DAT-Datei entfernen/verkürzen: saubere
   Fehlermeldung und BASIC-Rückkehr; die Engine darf nicht starten.
6. Optional im Debugger die High-RAM-Bereiche gegen die Originaldateien und
   `$7600–$7950` gegen Level 1 vergleichen. PAL/NTSC prüfen, falls beides verwendet wird.

Erst nach diesem Vergleich kann das Akzeptanzkriterium als erfüllt gelten.
