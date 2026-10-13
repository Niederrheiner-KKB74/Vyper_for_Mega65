# Stage 5b – Originalgrafiken, Mapping und Transparenz

Issue #27; **Stable, vom Benutzer vollständig bestätigt**. Branch `stage5b` basiert ausschließlich auf
`stage5a-stable` (Stable-Dokumentationscommit `9eeb395`, Programmstand `e7166a7`).
Alle Stage-5a-Quellen, Assets, Releases und älteren stabilen Stände bleiben unverändert.

## Originalquellen und Extraktion

Die drei vom Benutzer bereitgestellten Dateien sind verlustfrei unter
`assets/stage5b/original_sources/` archiviert. SHA-256:

- `Vyper_Memory_Dump.dat`, 524288 Bytes: `d74aea88fb4232e36caab80e51abc51f73d470a5b55a54f5cb010f1d910ddf8c`
- `Vyper_Startscreen.uss`, 1076832 Bytes: `d836cbf88f0ac35b6ed3776df2add39f699113c1aeb9d02cdfe4651c82793916`
- `VYPER.ADF`, 901120 Bytes: `b28cab911431aaf3e48fd3e9979159de7154f98538eeba191f52ac47ef9665e5`

`tools/extract_stage5b_graphics.py` prüft diese Prüfsummen, OFS-Dateiketten,
Blockprüfsummen und die tatsächlich vorhandenen Pointer. Die ChipRAM-Tabelle bei
`$2DAF2` enthält 38 Einträge à18 Bytes; Deskriptorpointer BE32 bei+8,
Framezahl BE16 bei+12. Jeder Frame hat einen eigenen32-Byte-Deskriptor:
Plane0/1/2-Pointer bei+0/+4/+8 und Maskenpointer bei+24. Jeder Pointer wird
separat gelesen und gegen das512-KiB-Abbild geprüft. Keine lineare Maskenfolge
wird angenommen. Drei32-Byte-Planes und die32-Byte-Maske werden pro Frame als
`type_NN_frame_NN_amiga.bin` archiviert. Das Manifest nennt alle Pointer,
Checksummen, Zieloffsets, Änderungen und Transparenzzahlen je Spalte.

Die zweiten Originaldaten im unkomprimierten `CRAM`-Chunk des USS enthalten die
relokierte38-Typen-Tabelle bei `$1ACE2`. **Alle259 Plane-/Maskensätze sind dort
byteidentisch**, obwohl ihre Pointer andere Adressen besitzen. Dieser Vergleich
wird bei jedem Build erneut durchgeführt.

Originalindex36 (`$3A07A`) und37 (`$3A1BA`) liefern je10 Frames. Diese heißen im
1-basierten VYGR-Verzeichnis **Typ37 und38**. Die bisherigen36 Typen enthalten239
Frames; nun sind es38 Typen und259 Frames. Vorschau:
[`all_types_preview.png`](../assets/stage5b/all_types_preview.png), Reihenfolge
oben nach unten Typ1..38, pro Zeile die Frames von links nach rechts. Graustufen
sind diagnostische Indexfarben; sie behaupten keine Original-Levelpalette.

## Mapping und Beleggrenzen

Die Original-ADF-Datei `Wave/Forme` wurde mit allen100 VYLV-Gegnerlisten verglichen:
2194 Gegner, unveränderte Typ- und Angriffsindexbytes, originale Koordinatenpaare
mit der bereits vorhandenen VYLV-Y-Umrechnung(+16). Das Manifest nennt die
wiedergefundenen Forme-Offsets je Level. Alle38 Deskriptorpositionen und die
Framezahlen0..35 stimmen mit der bisherigen VYGR-Reihenfolge überein; außerdem
lässt sich jeder bisherige Frame exakt mit dem historischen Konvertierungsfehler
reproduzieren. Die neuen Frames passen zur gleichen Deskriptorfolge.

**Die ursprüngliche Amiga-Indexierungsroutine ist weiterhin nicht unabhängig
nachgewiesen.** Suchen nach direkten Tabellenpointern und PC-relativen LEA-
Referenzen in den bereitgestellten Speicherabbildern lieferten keinen belastbaren
Routine-Nachweis. Die Tabelle wird deshalb als **stark durch Deskriptor-, Frame-
und Forme-Vergleich gestützt** dokumentiert, nicht als vollständig aus Originalcode
bewiesen. Index14→Typ15 besitzt zusätzlich die frühere visuelle Benutzerbestätigung.
Es wurde keine widersprechende Originalevidenz gefunden. Indizes6 und11 werden
von keinem der100 Level verwendet; ihre Grafikdeskriptoren sind trotzdem vorhanden.

Die einzige von Stage5b verwendete zentrale Tabelle ist
`assets/stage5b/vylv_vygr_mapping.json`. Daraus erzeugt der Builder die38 expliziten
Einträge in `stage5b_mapping.asm`. `confirmed` bleibt nur bei14 wahr und bezeichnet
die individuelle visuelle Bestätigung; der separate Evidenzstatus gilt für alle
Einträge. Die alte `assets/vylv_vygr_mapping.json` bleibt als unveränderter Eingang
für stabile Vorgängerstages erhalten und wird von Stage5b nicht verwendet.

| VYLV index | VYGR type | Descriptor (ChipRAM) | Frames | Evidence |
|---:|---:|---|---:|---|
| 0 | 1 | `$3829A` | 4 | Strong descriptor/frame/Forme comparison |
| 1 | 2 | `$3831A` | 7 | Strong descriptor/frame/Forme comparison |
| 2 | 3 | `$383FA` | 10 | Strong descriptor/frame/Forme comparison |
| 3 | 4 | `$3853A` | 6 | Strong descriptor/frame/Forme comparison |
| 4 | 5 | `$385FA` | 8 | Strong descriptor/frame/Forme comparison |
| 5 | 6 | `$386FA` | 6 | Strong descriptor/frame/Forme comparison |
| 6 | 7 | `$387BA` | 7 | Strong descriptor/frame/Forme comparison |
| 7 | 8 | `$3889A` | 4 | Strong descriptor/frame/Forme comparison |
| 8 | 9 | `$3891A` | 8 | Strong descriptor/frame/Forme comparison |
| 9 | 10 | `$38A1A` | 4 | Strong descriptor/frame/Forme comparison |
| 10 | 11 | `$38A9A` | 6 | Strong descriptor/frame/Forme comparison |
| 11 | 12 | `$38B5A` | 1 | Strong descriptor/frame/Forme comparison |
| 12 | 13 | `$38B7A` | 4 | Strong descriptor/frame/Forme comparison |
| 13 | 14 | `$38BFA` | 8 | Strong descriptor/frame/Forme comparison |
| 14 | 15 | `$38CFA` | 6 | Strong + user visual confirmation |
| 15 | 16 | `$38DBA` | 6 | Strong descriptor/frame/Forme comparison |
| 16 | 17 | `$38E7A` | 12 | Strong descriptor/frame/Forme comparison |
| 17 | 18 | `$38FFA` | 12 | Strong descriptor/frame/Forme comparison |
| 18 | 19 | `$3917A` | 4 | Strong descriptor/frame/Forme comparison |
| 19 | 20 | `$391FA` | 8 | Strong descriptor/frame/Forme comparison |
| 20 | 21 | `$392FA` | 9 | Strong descriptor/frame/Forme comparison |
| 21 | 22 | `$3941A` | 4 | Strong descriptor/frame/Forme comparison |
| 22 | 23 | `$3949A` | 4 | Strong descriptor/frame/Forme comparison |
| 23 | 24 | `$3951A` | 12 | Strong descriptor/frame/Forme comparison |
| 24 | 25 | `$3969A` | 6 | Strong descriptor/frame/Forme comparison |
| 25 | 26 | `$3975A` | 8 | Strong descriptor/frame/Forme comparison |
| 26 | 27 | `$3985A` | 4 | Strong descriptor/frame/Forme comparison |
| 27 | 28 | `$398DA` | 8 | Strong descriptor/frame/Forme comparison |
| 28 | 29 | `$399DA` | 6 | Strong descriptor/frame/Forme comparison |
| 29 | 30 | `$39A9A` | 8 | Strong descriptor/frame/Forme comparison |
| 30 | 31 | `$39B9A` | 8 | Strong descriptor/frame/Forme comparison |
| 31 | 32 | `$39C9A` | 8 | Strong descriptor/frame/Forme comparison |
| 32 | 33 | `$39D9A` | 12 | Strong descriptor/frame/Forme comparison |
| 33 | 34 | `$39F1A` | 4 | Strong descriptor/frame/Forme comparison |
| 34 | 35 | `$39F9A` | 3 | Strong descriptor/frame/Forme comparison |
| 35 | 36 | `$39FFA` | 4 | Strong descriptor/frame/Forme comparison |
| 36 | 37 | `$3A07A` | 10 | Strong descriptor/frame/Forme comparison |
| 37 | 38 | `$3A1BA` | 10 | Strong descriptor/frame/Forme comparison |

## Nachgewiesene Konvertierungsfehler

Der bisherige Konverter lässt sich für **alle239 alten Frames bytegenau** durch
folgendes Verfahren reproduzieren: Planeadresse−6, Zeilenadresse `(y+3)%16`,
unveränderte lineare Originalmaske, linkes Pixel im **hohen** Nibble. Das ist die
Ursachenprüfung, keine Vermutung aus einer Vorschau.

Der NCM-/RRB-Pfad verwendet dagegen links das **niedrige** Nibble. Der bisherige
Datenbestand vertauscht deshalb paarweise Bild- und Maskenpixel:9612 Maskenpixel
liegen aus Sicht des Renderers an einer anderen X-Position. Die Zeilenverschiebung
stimmt nur für Zeilen0..12 mit den tatsächlichen Plane-Pointern überein; für13..15
liest sie sechs Bytes vor dem Pointer statt die letzten drei Planezeilen.
Dadurch weichen zusätzlich1388 sichtbare Farbindexpixel ab.

Stage5b liest jede Plane **linear ab ihrem tatsächlichen Pointer** und packt
`left | right<<4`. Ein Maskenbit0 bleibt transparent(Index0); ein gesetztes Bit
liefert den Original-3-Bit-Farbindex+1, auch wenn dessen Originalfarbe0 ist.
Die Maske wird nicht erweitert, aufgefüllt oder aus der Farbe abgeleitet.
In den239 Bestandsframes ändern sich11690 Datenbytes und23323 gerenderte Pixel;
alle Änderungen sind im Manifest je Frame dokumentiert. Echte transparente
Spalten/Bereiche der Originalmaske bleiben erhalten. Für jeden der259 Frames
stimmen alle256 Pixel sowie die Transparenzzahl jeder Spalte mit den originalen
Planes/Masken überein.

Der Stage5a-Clippingpfad liest niedrige Nibbles zuerst, einschließlich ungerader
linker/rechter Schnittkanten. Die tatsächlichen assemblierten DMA-/RRB-Routinen
werden gegen eine unabhängige Original-Pixelmatrix geprüft. Es ist kein Umbau
an Renderer, Strides, Slots, GOTOX, Palette oder Crop-Routine erforderlich.
Die Konvertierungsfehler sind behoben. Der Benutzer bestätigt die korrekten
Grafiken in Levels1/29/37/54 und anschließend den vollständigen DOS-korrigierten
Build. Ein eigener XEMU-Lauf wurde nicht durchgeführt.

## VYGR-Format, Speicher und Kompatibilität

VYGR bleibt Formatversion1: `VYGR`, LE16-Version/Typzahl, anschließend je Typ
LE32-Dateioffset/LE16-Framezahl/LE16-reserviert0, danach128 Bytes pro Frame.
Die Datei enthält **keine Palettenblöcke oder Palettenreferenzen**. Das wurde anhand
von Header, Verzeichnis und vollständiger Dateibelegung geprüft.

| Bereich | Stage5a | Stage5b |
|---|---|---|
| VYLV | `$40000–$53F80`,81793 Bytes | unverändert |
| Zwischenraum | `$53F81–$53FFF`,127 Bytes | unverändert |
| VYGR | `$54000–$5B8A7`,30888 Bytes | `$54000–$5C2B7`,33464 Bytes |
| VYGR-Verzeichnisende | Dateioffset`$0128` | Dateioffset`$0138` |
| Typen/Frames |36/239|38/259|
| VYGR-Summe16 |`$1FE9`|`$5B75`|

Neue VYGR-SHA256:
`974e8eff97efd0c0f67db2780cb668311b9d8731395d43641d4602c0a7c96b50`.
Die Erweiterung beansprucht2576 weitere Bytes im bestehenden High-RAM-Bereich;
sie überlappt weder VYLV noch bestehende Puffer. Keine RAM-Nutzung im ROM-Bereich
`$20000–$3FFFF`. Loadergröße/Prüfsumme und die dynamischen Verzeichnis-/Framegrenzen
wurden angepasst. SETBNK, SEQ-I/O und DMA-Rückkopieprüfung bleiben unverändert.
Wie in Stage5a wird die bekannte Dateilänge begrenzt geladen: zu kurze Dateien,
falsche Summen und DMA-Rückkopiefehler werden abgewiesen. Zusätzliche Bytes hinter
dem erwarteten Ende werden weiterhin nicht eingelesen; ein gesonderter EOF-Test
wird nicht hinzugefügt. Der Build/D81-Audit prüft die vollständige exakte Dateigröße.
Die22×256-Pixiepuffer sind nach der DOS-Exit-Korrektur nach `$14000–$155FF`
verlegt;24 RRB-Slots und192-Byte-Screenstride bleiben identisch. Der alte Bereich
`$10000–$11FFF` ist vollständig für DOS reserviert und wird nicht mehr beschrieben.
Der volle100-Level-Audit bestätigt weiterhin max22 Gegner,23 inklusive Player
benötigte RRB-Slots,1706 Recordbytes,469 Einflugbytes und2100 Verzögerungsframes.

Der initiale Grafikbuild `05a87a7` änderte45 Bytes gegenüber Stage5a. Die spätere
DOS-Speicherkorrektur ändert weitere102 PRG-Bytes, einschließlich automatisch
verschobener DMA-Descriptor-/Helperoperanden; insgesamt147 gegenüber Stage5a.
Der Builder prüft nun jede komplette Quelle gegen Stage5a Stable plus die explizit
zugelassenen Grafik-/Pufferadressänderungen. Rendererablauf, Clippingalgorithmus,
Player1px/Frame, Drift±8 mit1px/2Frames, Einflug, Angriffskurven, Schüsse,
Kollisionen, Explosionen, HUD, Level Clear, R/X und+/− bleiben erhalten.
Die Angriffssperre in25/50/99/100 bleibt bestehen.
[Ursache, Speicherkorrektur und erneute Abnahme](stage5b_dos_exit_fix.md).

Die neue VYGR ist nur mit dem zugehörigen Stage5b-PRG zu verwenden. Alte Loader
prüfen36 Typen/alte Dateigröße/Summe und akzeptieren diese Datei nicht. Alte
Stable-D81 behalten ihre ursprünglichen Daten unverändert. Amiga-Levelpaletten
werden ausdrücklich noch nicht integriert; Player-Palette ebenfalls unverändert.

## Reproduzierbarer Build und Tests

Python3, Pillow12.3.0, Java und die bekannte KickAssembler5.25-JAR erforderlich.
JAR-SHA256: `9592a39336e73a1db8b4a7749256d62d29b113b1c7f0f6c86ea43870ebd9ae1f`.

```sh
python3 -m pip install -r tests/requirements-stage5b.txt
python3 tools/extract_stage5b_graphics.py
python3 tools/analyze_stage5b_capacity.py
python3 tools/build_stage5b.py --kickass /pfad/KickAss.jar
PYTHONPATH=tests:tools MEGA65_ROM=/pfad/MEGA65.ROM python3 -m unittest test_stage5b test_stage5b_graphics test_stage5b_dos -v
```

Buildziel `releases/stage_5b/`: vollständige elf ASM-Quellen, PRG/Symbole,
VYGR/VYLV, D81, Mapping, Speicher- und Buildbericht sowie SHA256SUMS.
Das D81 enthält `STAGE5B`(PRG), `VYLV.DAT` und neue `VYGR.DAT`(SEQ).
Dateiketten, Dateigrößen und Payloads werden beim Build geprüft. Der Builder
extrahiert erneut, schützt die Stable-Releases und prüft die vollständige Quellableitung und dokumentiert den PRG-Diff.
Initialer Grafikbuild: **32/32 Tests bestanden** (270.006s): alle100 Levelinitialisierungen,2194
Forme-Gegnereinträge,66304 Originalpixel,1813 Clippingfälle über alle259 Frames
plus259 Überlappungsfälle und140 weitere Referenz-Randfälle.402 Einflug-/
Formationsupdates identisch zur archivierten Stage4c-Referenz; Kampf-/Levelclear-/
R/X-/Respawn-Regressionsprüfungen bestanden. Ein unabhängiger Zweitbuild liefert
alle20 Release-Dateien byteidentisch. Die nachfolgende DOS-Korrektur wird separat mit vollständiger Regression geprüft;
der aktuelle Zykluswert steht im Testbericht, ohne vollständige DMA-/IRQ-/Rasterzeitmessung. Kein eigener XEMU- oder Hardwarelauf.

Ausgeführte Tests und Zweitbuild-Ergebnis sind in
[`stage5b-test-results.json`](stage5b-test-results.json) dokumentiert.

## XEMU-Abnahme durch Benutzer

D81 einlegen; `LOAD "STAGE5B",8`, `RUN` (ROMV920395, BASIC80×25).

1. Level1: Typ15/sechs Frames mit Original vergleichen; kein ungewollter Streifen,
   Einflug, Y0-Formation, Drift, Schüsse und Playersteuerung wie Stage5a.
2. Mit+/− Levels29 und54: Originalindex36→Typ37, zehn Animationsframes;
   Level37: Originalindex37→Typ38, ebenfalls zehn Frames. Keine Lade-/DMAfehler.
3. Gemischte Grafiken in71/100 und weitere Levels prüfen: unabhängige Animation,
   keine vertauschten Gegner oder unbeabsichtigten Spaltenlöcher. Diagnostische
   Vorschauen zeigen Indices/Masken, keine endgültigen Level-Farben.
4. Clipping an allen vier Playfieldgrenzen, besonders ungerades X sowie HUD-Grenze;
   mehrere überlappende Pixies, keine Wraparound-/Speicherartefakte.
5. Kampf, Punkte, Leben, Respawn/Unverwundbarkeit, Game Over/R, X→BASIC und erneutes
   RUN; Level Clear/Joystickfortsetzung, regulär100→1 und begrenztes+/− testen.
6. Levels25/50/99/100 behalten die freigegebene vorläufige Angriffssperre.

**Stage5b ist nach ausdrücklicher Benutzerbestätigung als `stage5b-stable` gesichert.**

DOS-korrigierter Build:34/34 Tests bestanden(353.719s), DOS-RAM vollständig erhalten;
20 Release-Dateien erneut byteidentisch reproduziert. Grafikdaten und Mapping
gegenüber dem vom Benutzer visuell geprüften Build unverändert.

Abschließende Benutzerbestätigung: „Der Build ist jetzt stabil und funktioniert komplett“.
Stabile Referenz: `stage5b-stable`; bestätigter Programmcommit
`52118cee6813b833d0c1d237925ad6ecd75d1d33` einschließlich DOS-Exit-Korrektur.
Die Stable-Sicherung verändert ausschließlich Dokumentation; Quellen, PRG, D81
und Originaldaten bleiben bytegleich. Die XEMU-Abnahme stammt vom Benutzer;
ein eigener XEMU-/Hardwarelauf wurde nicht durchgeführt. Die dokumentierten
Mapping-Beweisgrenzen und Sonderlevel-Angriffssperren bleiben bestehen.
