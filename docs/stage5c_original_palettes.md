# Stage 5c – originale Levelpaletten

Issue #31, Branch `stage5c`, **Stable, vom Benutzer unter XEMU bestätigt**. Unveränderte Basis:
`stage5b-stable` (`88e19bbd3b785631a55678d1df8ef2c4abca56f7`), einschließlich
DOS-Exit-Korrektur. Alle Stage5b-Quellen, Assets und Releases werden vom Builder
gegen den Stable-Tag geprüft. Die neuen Dateien liegen unter `releases/stage_5c/`.

## Originalnachweis und Grenzen

[Analyse](color_palette_analysis.md) und beide versionierten CSV stammen aus
`analysis-color-palettes`. Der Konverter prüft sie unabhängig gegen die archivierte
Original-ADF aus Stage5b, inklusive SHA256-Prüfung und OFS-Dateiketten:

- Color:362 Bytes, Header BE16 `$0064`, danach20×9 BE16-RGB4-Wörter.
  SHA256 `012e0d6a00e2d54281b028a56777ed0811cbbaca495871e964e685cce4784094`.
- Level:11400 Bytes,100 Records×114; alle100 BE16-Felder bei `+$4C` stimmen
  mit der Level-CSV überein. SHA256
  `6349b34fc36469cb3072a0735b881002b47b37ff3af4456ea8c55403f553647f`.
- Level1→3,2→1,3→4,4→13. Alle20 Paletten kommen vor.
- Die originale Amiga-Code-Nutzung dieses Felds und der neun Farbregister ist
  **nicht unabhängig disassembliert**. Die Zuordnung ist datenbasiert stark
  gestützt; ein eigener WinUAE-Farbvergleich wurde nicht durchgeführt.

VYLV.DAT und die38-Typen-VYGR.DAT bleiben byteidentisch zu Stage5b. Die vollständige
100-Level-Zuordnung einschließlich aller neun RGB4-Wörter wird reproduzierbar in
`assets/stage5c/palette-report.json` und im Release-Buildbericht aufgeführt.

## VYCL.DAT v1

Alle mehrbyteigen Felder sind **Little Endian**; RGB4-Wörter werden verlustfrei
bewahrt. Die Umstellung von Original-Big-Endian ist ausschließlich Serialisierung.

| Dateioffset | Bytes | Inhalt |
|---|---:|---|
| `$0000` |4| ASCII `VYCL` |
| `$0004` |2| Formatversion1 |
| `$0006` |2| Levelanzahl100 |
| `$0008` |2| Palettenanzahl20 |
| `$000A` |2| Wörter pro Palette9 |
| `$000C` |2| Gesamtlänge476 (`$01DC`) |
| `$000E` |2| Summe aller Payloadbytes modulo65536 (`$36A4`) |
| `$0010` |100| Level1..100→Palettenindex0..19 |
| `$0074` |360|20×9 RGB4-Wörter, je Palette neun aufeinanderfolgende Wörter |

Gesamtsumme einschließlich Header: `$3A1B`.
SHA256: `061e0e20aa77195b79ae80daf469387ed61e680f3f3841d8d5ed65ee8eeb491d`.
Der Hostparser verlangt exakt476 Bytes, identischen v1-Header, gültige Indices,
RGB4≤`$FFF`, Payloadsumme und vollständigen Encode/Decode-Roundtrip. Keine
zusätzlichen konvertierten Farbdaten, keine geschätzten Ersatzfarben.

## NCM-Indexbelegung und Farbtrennung

Originalgegner enthalten drei Bitplanes. Für sichtbare Pixel gilt in Stage5b
bereits `NCM_nibble = Amiga_plane_colour + 1`; eine transparente Maske erzeugt
Nibble0. Alle259 Originalframes bleiben unverändert.

Stage5c ordnet Plane-Wert `c=0..7` dem Color-Wort `c` zu. Das passt insbesondere
zu den bereits vorhandenen Level1-Grauabstufungen: Originalwörter4..7 sind
`899,344,566,ABB`, die bisherigen sichtbaren NCM-Indices5..8 hatten genau diese
RGB-Werte. Eine bewiesene ursprüngliche Amiga-COLOR-Registerbelegung wird daraus
nicht behauptet. Wort8 (`888` bei Palette3) wird verlustfrei mitgeführt; drei
Bitplanes liefern keinen Plane-Index8. Es wird keiner erfundenen Gegnerfarbe
zugewiesen. Wort0 (`000`) bleibt eine sichtbare schwarze Farbe bei gesetzter Maske;
der transparente Nibble0 ist davon unabhängig.

| Objekt | VIC-IV-Palettenbank und Einträge |
|---|---|
| Gegner |Bank1,17..24 = Originalwörter0..7; Nibble0 transparent, Eintrag16 schwarz |
| Explosionen, sieben Originalframes |Bank1, bisherige Einträge0..15 unverändert |
| Player, Lebenssymbole, HUD, Projektile |Bank2 vollständig unverändert |
| BASIC-ROM-Palette |Bank3 vollständig unverändert |

Es ist kein Bankwechsel pro Gegner nötig. NCM setzt die oberen vier Bits des
Paletteindex aus dem zweiten Color-RAM-Byte des Glyphs; daher wird für Gegnerglyphs
`$10` statt `$00` geschrieben. Die vorhandene GOTOX-Auswahl von primärer Bank1 bzw.
alternativer Bank2 bleibt unverändert. Direkte Explosionglyphs und Explosionen in
privaten, auch geclippten Gegnerpuffern erhalten `$00`. Playerglyphs `$321..$323`
bleiben unverändert; Testmodus-Gegner und private Offscreen-Crops nutzen `$10`.

Beleg: MEGA65 User Guide, Appendix VIC-IV, Abschnitt Nibble-colour Text Mode;
XEMU `targets/mega65/vic4.c`, NCM-Renderer: `used_palette+(color_data&0xF0)`.
D070: Bits7..6 CPU-gemappte Bank,5..4 primär,3..2 Sprites,1..0 alternativ.
Die Levelroutine mappt nur vorübergehend Bank1 und stellt D070 vollständig wieder her.
R/G/B liegen bei D100/D200/D300. Pro Kanal `v8=17*v4`; identische obere/untere
Nibbles machen die VIC-IV-Nibble-Reihenfolge bei RGB4-Expansion eindeutig.

## Loader, Levelstart und Speicher

Der bestehende SEQ-Loader lädt nun die drei Originaldateien vor dem Video-Umbau.
`SETBNK($FF6B)` mit Bank0 steht weiterhin vor SETNAM; Dateiname `VYCL.DAT,S,R`.
Die KERNAL-Ladegerätenummer `$BA` wird vor dem ersten Dateizugriff gespeichert
und für alle drei SETLFS-Aufrufe verwendet (bei direktem SYS ohne Disk-LOAD bleibt
8 der bisherige Standard). Während CHKIN ist keine Bildschirmausgabe erlaubt;
CLRCHN/CLOSE bleiben auf Erfolg und Fehler gewährleistet.

VYCL wird in256-Byte-Portionen nach High RAM geschrieben, über DMAgic zurückgelesen
und byteweise verglichen. Die Dateisumme ist gegen die Originalkonvertierung
gepinnt. Zusätzlich werden Signatur, Version, Zahlen, Länge, alle100 Indices,
alle180 RGB4-Wörter und interne Payloadsumme geprüft. VYCL verlangt EOF am476.
Byte, weist somit auch zusätzliche Bytes ab. Der bestehende begrenzte Lesevertrag
von VYLV/VYGR bleibt unverändert. Fehler vor RRB-Initialisierung kehren zu BASIC
zurück; Load Error7 bezeichnet VYCL-Summen-/Formatfehler,1/2/3/4 weiterhin
OPEN/CHKIN/READST/DMA-Probleme. Keine Ersatzpalette bei defekten Daten.

| Physischer Bereich | Verwendung |
|---|---|
| `$40000–$53F80` |VYLV, unverändert |
| `$54000–$5C2B7` |VYGR, unverändert |
| `$5C300–$5C4DB` |VYCL,476 Bytes;72 Bytes Abstand zu VYGR |
| `$6800–$68FF`, `$6900–$69FF` |bestehende SEQ-/DMA-Rücklesepuffer |
| `$6B00–$6CFF` |neuer Palettencode und Tabellen, tatsächliches Ende im Assembly-Report |
| `$6EF0–$6EF3` |Paletten-ID, Scratch und gespeichertes Ladegerät |
| `$6D00–$6EDB` |validierter VYCL-Spiegel |
| `$12000–$126FF` |aktiver Levelrecord, unverändert |
| `$14000–$155FF` |22 private Pixiepuffer, unverändert; außerhalb DOS |
| `$15600–$15A7F` |1152-Byte-Erweiterung der Color-RAM-Sicherung |

Wichtig: Der scheinbar freie PRG-Bereich `$6B00–$6F7F` war in Stage5b tatsächlich
als Laufzeit-Color-RAM-Sicherung belegt. Diese Sicherung ist durch Änderung der
beiden DMA-Quell-/Zieladressen hinter die Pixiepuffer verlegt. Algorithmus, Umfang
und Rückkopie bleiben unverändert. Dieser Bank1-Bereich gehört wie Levelrecord
und Pixiepuffer zum während RUN genutzten BASIC-Array-/Stringbereich; das reine
Maschinenspracheprogramm benutzt keine BASIC-Arrays. DOS `$10000–$11FFF`, ROM
`$20000–$3FFFF` und das Color-RAM-Fenster `$1F800–$1FFFF` werden nicht als frei benutzt.

Initiale Palette: nach bestehender Palette-/Player-Initialisierung, bevor Gegner
sichtbar werden. Weitere Level: direkt nach erfolgreichem Parserlauf vor Objekt-
und HUD-Initialisierung. Derselbe Pfad deckt LEVEL CLEAR/Button,100→1,+/− und R ab.
`pal.palette_id` (`$6EF0`) erlaubt eine Monitorprüfung; die RGB4-Wörter der aktiven
Palette stehen ab `$6D74+18*palette_id`. Keine zusätzlichen Raster-Debugausgaben.

## Reproduzierbarer Build und Prüfungen

Python3, Java und gepinnter KickAssembler5.25 wie in Stage5b. CPU-Testabhängigkeiten:
`python3 -m pip install -r tests/requirements-stage5b.txt`. Für reine Konvertierung
werden nur Python-Standardbibliotheken gebraucht.

```sh
python3 tools/convert_stage5c_palettes.py
python3 tools/build_stage5c.py --kickass /path/to/KickAss.jar
PYTHONPATH=tests:tools MEGA65_ROM=/path/to/MEGA65.ROM python3 -m unittest test_stage5c -v
```

Release enthält PRG, D81, alle zwölf ASM-Komponenten, alle drei DAT-Dateien,
Original-CSVs, Symbols, Speicherkarte, Buildbericht und SHA256SUMS. D81-Verzeichnis
und sämtliche Dateiketten werden mit Bytevergleich geprüft: STAGE5C als PRG,
VYLV.DAT/VYGR.DAT/VYCL.DAT als SEQ. Start: `LOAD "STAGE5C",8`, `RUN`.

Automatische Ergebnisse und Grenzen: siehe `stage5c-test-results.json` und
`stage5c-tests.txt`. Die Tests verwenden den assemblierten Code mit CPU-, KERNAL-,
DMA-, RRB- und Palettenmodellen; sie ersetzen keine XEMU-Rasterabnahme und keinen
WinUAE-Originalfarbvergleich. Der Testadapter ersetzt vor den geerbten Testklassen
PRG, Symbole und Maschinenfixture durch Stage5c; deren Klassen-/Lognamen
`test_stage5b` bzw. der historische Renderer-Printpräfix `Stage5a` bleiben erhalten.
Die freigegebenen Sonderlevel-Angriffssperren
25/50/99/100 bleiben erhalten; alle übrigen Spielregeln sind unverändert.

## XEMU-Abnahme durch den Benutzer

1. Frisch LOAD/RUN; alle drei DAT-Dateien müssen laden und geprüft werden.
2. Levels1/2/3/4/5/10/11/20/21 sowie gemischte Typen (71/100),99/100 testen;
   IDs/Werte bei Bedarf mit der vollständigen Tabelle im Buildbericht vergleichen.
3. Player- und Lebenssymbolfarben, HUD, sieben Explosionframes und Projektile in
   allen Levels identisch zu Stage5b; korrekte Gegneranimation und Transparenz.
4. Kein Farbflackern bei Einflug, Animation und Levelstart; keine Streifen,
   Wraparound-Artefakte oder Zeichensatzfehler. Y=0..199 und HUD-Clipping erhalten.
5. Einflug, Formation, Angriffe, Rückkehr, Schüsse, Treffer, Score/Leben, Respawn,
   LEVEL CLEAR/Button,+/−,100→1 sowie GAME OVER/R prüfen.
6. X→BASIC, DIRECTORY, erneutes RUN sowie LOAD/RUN mehrfach prüfen.
7. Wenn möglich dieselben Originallevels in WinUAE vergleichen; diese visuelle
   Prüfung ist noch nicht durchgeführt und nicht durch die CSV-Verifikation ersetzt.

**Stage5c ist nach ausdrücklicher Benutzerbestätigung als `stage5c-stable` gesichert.**

Finaler Stage5c-Build: **43/43 Tests bestanden (515.180s)**; alle100 Level-
initialisierungen und Paletten,259 Originalframes,1813 Clipping- und259
Überlappungsfälle. DOS8192 Bytes, Color-RAM4800 Bytes und Cursorzustand erhalten;
Player/HUD/Explosionen isoliert. Alle23 Release-Dateien im unabhängigen Zweitbuild
byteidentisch. Benutzer-XEMU-Abnahme und originalgetreue Level-Farben bestätigt;
kein eigener XEMU-/WinUAE-Farbvergleich durchgeführt.

## Bestätigte Stable-Referenz

Der Benutzer bestätigt: „Level-Farben entsprechen exakt dem Original, Player, HUD und Explosionen sind unverändert korrekt. Basic-Exit funktioniert ebenfalls. Stage 5c ist stable.“
Stabile Referenz: `stage5c-stable`; bestätigter Programmcommit
`2fb8308b886980f3d0e89a1ae19faf3937c6903f`.
Die Stable-Sicherung verändert ausschließlich Dokumentation. Quellen, PRG, D81
und alle DAT-Dateien bleiben byteidentisch. Die XEMU-Abnahme und der visuelle
Originalfarbvergleich stammen vom Benutzer; ein eigener XEMU-/WinUAE- oder
Hardwarelauf wird nicht behauptet. Die offenen Amiga-Code-Beweisfragen und
die freigegebenen Sonderlevel-Angriffssperren bleiben unverändert dokumentiert.
