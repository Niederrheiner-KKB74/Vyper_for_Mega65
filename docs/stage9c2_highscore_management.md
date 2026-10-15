# Stage 9c2 – persistente Highscore-Verwaltung (Issue #83)

Eigenständiger Testbranch `stage9c2`, **nicht Stable; kein Merge vor Abnahme**.
Basis ist die bestätigte Stage9c1 mit Einzelzeilen-Farbanimation,
Commit `4acc8a2ed958f933dc3af9d9220c250b005a813c`. Stage9b1 in `main`,
alle bisherigen Quell-/Asset-/Release-Dateien und Stable-Referenzen bleiben
unverändert. Keine F3-, Game-Over-, Sound- oder Spielengine-Integration.

## Bedienung und erster Test

Eine **beschreibbare lokale Kopie** von `VYPER_STAGE9C2.d81` in XEMU einlegen.
PAL50Hz und Joystick Port2 wie bei Stage9c1 verwenden:

```basic
LOAD "STAGE9C2",8
RUN
```

Das ausgelieferte Image enthält eine gültige **leere** `VYHI.DAT`. Alle80 Plätze
sind sichtbar, unbelegte Plätze erscheinen als Striche. Es werden keine
vermeintlichen Original-Highscores erfunden. Ergebnisse werden in diesem Test
manuell simuliert:

1. In der Anzeige **S** drücken.
2. Score als Dezimalzahl eingeben, z.B. `1000`; **RETURN**.
3. Bei Qualifikation genau drei Namenszeichen eingeben, z.B. `KAI`;
   **RETURN** bestätigt und speichert. Die neue Rangseite wird angezeigt.
4. Erneut `1000` mit einem anderen Namen eintragen: Der neueste Gleichstand steht
   vor dem alten. X beendet die Anzeige; nach erneutem `RUN` und nach einem
   Emulatorneustart mit **demselben Image** müssen beide Einträge erhalten bleiben.

| Zustand | Eingaben |
| --- | --- |
| Anzeige | Cursor/Joystick links/rechts: Seite1–4, an Grenzen stoppen |
| Anzeige | S: simuliertes Ergebnis; RETURN, Feuer, X oder andere Eingabetaste: BASIC |
| Scoreeingabe | Ziffern, DEL/Backspace, RETURN: Qualifikation prüfen, ESC: abbrechen |
| Namenseingabe | drei Zeichen, DEL/Backspace, RETURN: speichern, ESC: abbrechen |
| Rückmeldung ohne Qualifikation / Schreibsperre | RETURN/ESC: Anzeige; X: BASIC |

Die Namenseingabe ist zunächst **tastaturbasiert**; Joystick-Eingaben werden in
Editier-/Meldungszuständen ignoriert und blättern dort nicht versehentlich.
Während einer Namenseingabe ist X ein zulässiger Buchstabe: zum Beenden erst ESC,
dann X. S ist die einzige neue Ausnahme vom bisherigen „andere Taste beendet“
in der normalen Anzeige. Richtungsentprellung, Feuer-Freigabe und Seitengrenzen
bleiben erhalten. Gehaltenes RETURN erzeugt keinen zweiten Commit und wird nach
Bestätigung bis zur physischen Freigabe unterdrückt.

Namen: `A–Z`, `0–9`, `- + / . @ ! ?`, genau drei Zeichen, keine Leerzeichen.
ASCII-Kleinbuchstaben und PETSCII-Shift-Buchstaben werden zu ASCII-Großbuchstaben
normalisiert. Die aktuelle Namensposition ist farblich hervorgehoben und als
Position angegeben. Fehlende Zeichen erscheinen als `-`. Ein vierter oder
ungültiger Buchstabe verändert den Namen nicht. Leeres RETURN bestätigt weder
Score noch Namen. Abbruch verändert weder Tabelle noch Diskette.

Scoreeingabe: maximal zehn Ziffern und unsigned32-Bit, `0…4294967295`.
Ungültige/überlaufende Ziffern werden mit Meldung **nicht angenommen**; der
sichtbare bisherige Eingabetext und Wert bleiben gültig. DEL berechnet den
verbleibenden Wert neu. Es erfolgt weder Modulo-Überlauf noch stille Sättigung.

**Datentypnachweis:** Die Stage9b1-Engine führt `player1_score` als vier binäre
Bytes und sättigt bei Übertrag auf `$FFFFFFFF`; siehe
[Scoreaddition](../src/engine/stage9b1_game.asm:510). Stage9c2 übernimmt diesen
vollständigen Bereich. Deshalb wurde ausschließlich das Scorefeld innerhalb der
bestehenden beiden Spalten von sieben auf **zehn Dezimalstellen** erweitert:
Eintrag18 Zeichen statt15, gleiche Spaltenanfänge16/49, unveränderter Font und
Rahmen. Auch der Maximalwert passt vollständig; die Spaltenköpfe sind angepasst.

## Einfügen und Gleichstände

Es gibt eine explizite belegte Anzahl `count=0…80`. Ein echter Eintrag mit
Score0 ist **belegt**, ein leerer Slot liegt dagegen außerhalb von `count`.
Auch bei80 belegten Null-Scores qualifiziert sich eine neue0 auf Rang1.

Gesucht wird die **erste** Position mit `new_score >= old_score`. Existiert
keine, ist die Position `count`. Position80 wird abgewiesen; sonst werden die
folgenden Records rückwärts um einen Platz verschoben. Bei voller Tabelle fällt
nur der bisherige Rang80 weg. Verglichen wird unsigned vom höchsten zum
niedrigsten Scorebyte, nicht als Text oder BCD.

Damit gilt auch am letzten Platz „neu vor alt“. Vorhandene Gleichstände bleiben
untereinander stabil, es gibt keine Namenssortierung. Bei wiederholten neuen
Gleichständen kommt jeweils der neueste zuerst. Einfügen wird erst nach drei
bestätigten Zeichen ausgeführt. Ein Diskfehler stellt den vorherigen kompletten
RAM-Datensatz wieder her und sperrt weitere Speicherung bis zur Klärung.

## VYHI.DAT Version1

Geschlossene, nicht gesperrte **SEQ-Datei**, exakt592 Bytes, kein PRG-Ladeheader.
Alle80 physischen Slots werden gespeichert, auch bei kleinerer belegter Anzahl.
Die mitgelieferte Datei wird mit `tools/highscore_format.py` reproduziert.

| Offset | Bytes | Inhalt |
| --- | --- | --- |
| `$00` | 4 | ASCII `VYHI` |
| `$04` | 1 | Version1 |
| `$05` | 1 | Headergröße32 |
| `$06` | 1 | Recordgröße7 |
| `$07` | 1 | belegte Anzahl0…80 |
| `$08` | 2 | CRC16-CCITT-FALSE, Little Endian |
| `$0A` | 22 | reserviert, zwingend0 |
| `$20` | 560 | 80 Records à7 Bytes |

Record: drei ASCII-Namensbytes, anschließend unsigned32-Bit-Score **Little
Endian**. Unbelegte Records sind vollständig0. Belegte Namen bestehen aus genau
drei erlaubten Zeichen. Die Liste muss absteigend sortiert sein; Gleichstände
sind zulässig und werden beim Laden nicht umsortiert.

CRC: Polynom `$1021`, Start `$FFFF`, nicht reflektiert, kein finales XOR.
Sie umfasst Header und sämtliche Record-/Leerbytes, **ausgenommen die beiden
CRC-Bytes `$08/$09`**. Der Python-Referenzcodec verwendet entsprechend
`binascii.crc_hqx(data[:8]+data[10:],65535)`.

Vor Übernahme werden exakte Länge/EOF, Magic, Version, Header-/Recordgröße,
Reservierungen, Anzahl, CRC, Namensalphabet, Sortierung und alle Leer-Slots
geprüft. Fehlerhafte oder inkompatible Dateien werden nicht teilweise übernommen
und nicht automatisch in eine neue Version umgeschrieben.

## Dateistrategie und Wiederherstellung

Dateien auf demselben Laufwerk: `VYHI.DAT` (Hauptbestand), `VYHI.TMP`
(bestätigte, noch nicht übernommene neue Fassung), `VYHI.BAK` (vorheriger Bestand).
Das Gerät stammt aus `$BA` des ursprünglichen LOAD, mindestens8, sonst8.
DOS-Laufwerk0 wird explizit angegeben.

Nach bestätigtem Namen:

1. RAM-Original als vollständigen592-Byte-Snapshot sichern; Kandidat einfügen/CRC
   berechnen. Ohne Qualifikation oder bei Schreibsperre keine Dateischreibaktion.
2. Neue `0:VYHI.TMP,S,W` anlegen. **Kein Überschreiben und kein automatisches
   Scratch einer vorhandenen Tempdatei.** Existiert sie bereits, bricht der
   Versuch sicher ab.
3. Alle592 Bytes schreiben, Ausgabekanal lösen, Datei normal schließen und
   DOS-Status prüfen. Tempdatei erneut vollständig lesen, validieren und
   bytegenau mit dem Kandidaten vergleichen.
4. Falls eine Hauptdatei vorhanden war: Diese nochmals lesen, validieren und
   bytegenau mit dem ursprünglichen RAM-Snapshot vergleichen. Erst dann darf ein
   vorheriges Backup entfernt werden; die gültige Hauptdatei und geprüfte
   Tempdatei bleiben zu diesem Zeitpunkt vorhanden.
5. Hauptdatei nach `VYHI.BAK` umbenennen, dann Tempdatei nach `VYHI.DAT`.
   Bei erster Neuanlage entfällt die alte Hauptdatei/Backup-Phase.
6. Die neue Hauptdatei nochmals lesen, validieren und mit dem Kandidaten
   vergleichen. Erst dann wird `SAVED AND READ BACK` angezeigt. Das Backup bleibt.

Dies ist **keine atomare Transaktion und keine Garantie gegen beliebige
Sektor-/Dateisystemdefekte**. Einzelne DOS-Kommandos bilden keinen gemeinsamen
Commit. Die Strategie hält insbesondere beim getesteten Abbruch nach der
Backup-Umbenennung die alte Fassung als BAK und die geprüfte neue als TMP vor.
Ein Stromausfall kann trotzdem manuelle Wiederherstellung verlangen. Es wird
kein ungeprüftes „löschen und neu anlegen“ als atomare Speicherung ausgegeben.

Startverhalten:

| Zustand auf Disk | Anzeige / Speicherung |
| --- | --- |
| gültige DAT, keine TMP | DAT laden; Schreiben erlaubt |
| DAT und BAK fehlen, keine TMP | leere Liste; erste Bestätigung legt DAT an |
| DAT fehlt/ungültig, BAK gültig | BAK anzeigen; schreibgeschützt |
| keine gültige DAT/BAK, TMP gültig | TMP als letzte Rettungsquelle anzeigen; schreibgeschützt |
| vorhandene TMP, auch beschädigt | Dateien erhalten; Schreibsperre/Warnmeldung |
| beschädigte/inkompatible Dateien ohne gültige Rettungsquelle | leere RAM-Liste; Dateien erhalten, Schreibsperre |
| nicht eindeutig lesbares Gerät / I/O-Fehler | sichere RAM-Liste, Warnmeldung, Schreibsperre |

Auch eine erst **nach** Programmstart extern angelegte TMP wird bei OPEN nicht
ersetzt. Keine automatische Beförderung einer Rettungsdatei, kein Löschen
beschädigter Hauptbestände. Zur Wiederherstellung zuerst eine Kopie des gesamten
D81 sichern und DAT/BAK/TMP extern prüfen; eine validierte Fassung kann auf einer
Arbeitskopie als `VYHI.DAT` wiederhergestellt werden. Eine neue leere Liste kann
mit dem Referenzcodec bzw. einer frischen Release-Kopie erzeugt werden. Das
Programm trifft diese potenziell destruktive Auswahl ausdrücklich nicht selbst.

Die Statuszeile zeigt Warnung/Erfolg sowie `IO nn DOS nn`. IO0 bedeutet nur keinen
Transportfehler, nicht automatisch eine valide Datei. IO1: OPEN;2: Kanal/DOS;
3: SEQ-/Längenfehler;4: Schreiben/Abschlussstatus;5: Verifikation/abweichender
Bestand. DOS ist dezimal, z.B.26 Schreibschutz,63 Datei vorhanden,72 Disk voll,
74 Laufwerk nicht bereit; `??` steht für nicht lesbaren Status. Fehlende Datei62
ist beim leeren Erststart zulässig. Datenvalidierung hat zusätzlich eine klare
Warnmeldung und Schreibsperre.

## Native KERNAL-Aufrufe und Grafik

`SETLFS`, **`SETBNK A=0/X=0 vor jedem SETNAM`**, `OPEN`, `CHKIN/CHRIN/READST`
und `CHKOUT/CHROUT/READST` werden mit Bank0-Dateinamen benutzt. Kanal2 enthält
Binärdaten, Kanal15 DOS-Kommandos/Status. Es erfolgen keine Textausgaben über
CHROUT während aktivem Eingabekanal; Bildschirmtexte entstehen im privaten
Renderpuffer. Fehlerpfade lösen Kanäle und schließen die logischen Dateien.

**MEGA65-spezifischer CLOSE-Vertrag:** Datei2 wird mit `CLC` normal geschlossen,
damit DOS den Schreibabschluss erhält. Kanal15 wird dagegen mit **`SEC` vor
`CLOSE($FFC3)`** geschlossen. Laut KERNAL-Referenz wird so nur der logische
Statuskanal entfernt, ohne DOS-CLOSE15 an das Gerät zu schicken und dadurch
andere offene Dateien zu schließen. `CLRCHN` wird vor und nach CLOSE verwendet.
Das Hostmodell prüft diese eingehenden Carry-Flags ausdrücklich.
[Referenz CLOSE/OPEN](https://github.com/MEGA65/mega65-user-guide/blob/cefce48d72e5c98d732c0589461d62b205b5165f/appendix-kernal-jumptable.tex).

Diskettenzugriffe laufen mit IRQs und **nativer BASIC-ROM-Abbildung**, ohne MAP-
Umschaltung. Vor einer Speicherung wird dafür kurz der gesicherte BASIC-Modus
wiederhergestellt. Während des synchronen Dateizugriffs pausiert die Testanzeige;
anschließend werden die normale BASIC-Umgebung erneut gesichert und die private
Anzeige wieder aktiviert. Menü-Farbzyklus und Zeilenphase werden **nicht neu
initialisiert**. Die kurz sichtbare BASIC-Fläche während I/O ist damit beabsichtigt.
Während einer Speicherung gepufferte Tasten werden beim Wiederanzeigen verworfen,
um keinen zweiten Commit auszulösen. Das ist noch keine Audio-/Gameplay-Integration.

Normale Anzeige: vier Seiten à20, zwei Spalten à10, Originalüberschrift/Fußzeile,
Rahmen und Font aus Stage9c1. Der bestätigte COLOR02-Assembler ist byteidentisch;
sechs Originalphasen,42 Frames pro Umlauf. Tabellenzeilen folgen separat
`palette[(row+phase)%3]`, beide Spalten synchron, ein Schritt alle acht Frames
nach oben, keine mehrzeiligen Blöcke. Namenscursor und Status betreffen nur die
neuen Eingabe-/Hinweisfelder außerhalb der Tabelle.

Dezimaldarstellungen werden bei Laden/Änderung einmalig vorbereitet. Eine Seite
wird vollständig im privaten Puffer aufgebaut und dann per DMA veröffentlicht,
statt Zeile für Zeile im sichtbaren Screen zusammengesetzt zu werden.

## Speicherbelegung

| Bereich | Nutzung |
| --- | --- |
| `$2001…$200C` | BASIC-SYS-Start |
| `$2100…$2FFF` | Controller/Video-Sicherung/DMA, reservierter Codebereich |
| `$3100…$31C3` | bestätigter COLOR02-Code |
| `$3200…$3357` | bisherige private Video-/Palettenzustände |
| `$3600…$3FFF` | neue Eingabe-/Dateizustände, Texte, Zeiger/Dezimalpotenzen |
| `$4000…$47CF` | statischer2000-Byte-Seitenhintergrund |
| `$4800…$4A4F` | aktuelles592-Byte-VYHI-Paket |
| `$4B00…$4D4F` | RAM-Original für Verifikation/Rollback |
| `$4E00…$504F` | separater Lesepuffer für vollständige Dateiprüfung |
| `$5100…$54FF` | native SEQ-/DOS-Transaktionsroutinen, reservierter Bereich |
| `$5500…$581F` |80 vorbereitete Zehn-Zeichen-Dezimalfelder, nicht persistent |
| `$6000…$67CF` | private Color-Ebene |
| `$67D0…$67FF` | unveränderte Rahmenglyphen |
| `$6800…$6FCF` | neuer privater Renderpuffer |
| `$7000…$77CF` | sichtbares privates Screen-RAM |
| `$8000…$87FF` | privater Font, keine VIC-WOM-Aliasadresse |
| `$8800…$9FFF` | Verwaltung/Prüfung/Rendering, reservierter Codebereich |
| `$15000…$157CF` | Sicherung des eigenen Color-Fensters |
| `$0FF82000…$0FF827CF` | eigenes Color-RAM-Fenster |

Alle Bereiche sind getrennt. DOS-RAM `$10000…$11FFF`, ROM `$20000…$3FFFF`,
Bank1-Colorfenster `$1F800…$1FFFF`, BASIC-Screen/Zeropage und Attic werden nicht
als Programmpuffer benutzt. Fontkopie endet vor dem Manager bei `$8800`.
Die drei80×7-Recordpuffer passen ohne Erweiterung der maximalen Liste;
`$A000` bleibt feste obere Codegrenze. Exakte Endadressen stehen in der
[Assemblerkarte](../releases/stage_9c2/memory-map.txt).

## Build, Tests und XEMU-Abnahme

```sh
python tools/build_stage9c2.py --kickass /pfad/zu/KickAss.jar
PYTHONPATH=tests:tools:/pfad/zu/py65 python -m unittest test_stage9c2 -v
```

KickAssembler5.25 (SHA256 geprüft), OpenJDK21, Python3.12. Hosttests zusätzlich
py65==1.2.0/Pillow aus der bestehenden Testumgebung. Standardbibliothek für
Referenzcodec, Initialdatei und Build. Keine neuen Originalassets oder ROM-Dateien
im Release. Unter `releases/stage_9c2/` liegen vollständige ASM/Includes/Daten,
PRG, vollständiges819.200-Byte-D81 mit PRG+SEQ-VYHI, Symbole, Speicherkarte,
Buildbericht und Hashmanifest. Das Image ist nicht mit einem Schreibschutzbit
versehen; Dateisystem-/XEMU-Mountrechte müssen ebenfalls Schreiben erlauben.

Hosttests führen die assemblierten Routinen in einem eingeschränkten CPU-/DMA-
und logischen DOS-Dateimodell aus. Sie sind **kein XEMU-Lauf und keine Prüfung
realer D81-Sektor-Schreibvorgänge**. Geprüft werden Einfügegrenzen/Gleichstände,
Null-/Maximalscores/Überlauf, Namen/Abbruch/Bestätigung, CRC/Header/Leer-Slots,
Datei-/Versionsfehler, OPEN/CHKIN/CHKOUT/READST, DOS-Status, Schreibschutz/voll/
Teilwrite, abgelehnte Umbenennung, mehrfache Speicherung und Neustart, liegen
gebliebene Tempdateien, modellierter Abbruch nach Backup, vier Seiten,
Farbzyklen über Edit/Speicherung, Joystick, BASIC-Restore und erneutes RUN.
[Ausgeführtes Protokoll und Reproduzierbarkeit](stage9c2_test_results.txt).

Unter XEMU noch auszuführen:

1. Leere Liste, S→Score→drei Zeichen→RETURN; Erfolg und neue Rangseite prüfen.
2. Gleiche Scores mehrmals eintragen: neuester zuerst, alte Reihenfolge stabil.
   Score0 und4294967295, DEL, ESC, leeres/zu kurzes RETURN, ungültige Zeichen,
   gehaltenes RETURN und lange Eingabe testen.
3. X→BASIC, `DIRECTORY`: DAT und nach Speicherung BAK vorhanden, keine TMP bei
   erfolgreichem Abschluss. `RUN`, erneutes LOAD und Emulatorneustart mit demselben
   D81: identische Rangliste. **Nicht zwischendurch das leere Releaseimage neu
   herunterladen! Vor künftigen Buildupdates die eigene Testdisk sichern.**
4. Mit einer vollen80er-Testdatei Rang80-Gleichstand und darunterliegenden Score
   prüfen. Solche Dateien lassen sich deterministisch mit dem Referenzcodec
   erzeugen; im ausgelieferten Image bleibt die Liste bewusst leer.
5. Nur auf Kopien: Schreibschutz, Disk voll, beschädigte/falsche Version, fehlende
   DAT und vorhandene BAK/TMP testen. Warnung/Schreibsperre, unveränderte Originale
   und normale BASIC-Rückkehr prüfen.
6. Vier Seiten, zehnstellige Werte, Normalfont, Einzelzeilenfarben, Rahmenzyklus,
   längeres Stehenlassen und Navigation nach Dateizugriff prüfen. Wiederholtes
   RUN und DIRECTORY müssen ohne Grafik-/Laufwerksfehler funktionieren.

Spätere Schnittstelle: `hi_score` ist unsigned32 Little Endian; `hi_qualify`
liefert den0-basierten Rang,80 bedeutet abgelehnt. `hi_insert` ist eine reine
RAM-Operation; `hi_commit` qualifiziert erneut, sichert das Original, fügt ein,
versiegelt und speichert mit Rollback bei Fehler. Namensvalidierung und explizite
Bestätigung laufen vorher über den Editor. Diese Routinen setzen hier den nativen
Standalone-Kontext voraus; ein direkter Aufruf unter einer aktiven RRB-/Audio-
Bankabbildung ist **keine** bereits implementierte Stage9c3-Integration.

**Stage9c2 nicht als Stable markieren und nicht mergen, bevor der Benutzer die
neuen Datei- und Bedienungsfunktionen unter XEMU bestätigt hat.**

Stage9c2-Rahmenkorrektur (15.10.2026): Die Hintergrundkonvertierung leert
nur den Tabelleninnenraum statt kompletter Zeilen; dadurch bleiben die beiden
seitlichen Rahmenzeichen erhalten. Alle 14 Hosttests bestanden, einschließlich
Rahmenzeichen und Cycling-Farbindex auf allen vier Seiten. PRG/D81 neu erstellt;
XEMU-Neuabnahme offen, weiterhin kein Stable.
