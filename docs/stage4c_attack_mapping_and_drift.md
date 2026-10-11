# Stage 4c – feste Angriffskurven und Zwei-Frame-Drift

Issue #19, Branch `stage4c`. **Stable: vom Benutzer in XEMU bestätigt; Referenz `stage4c-stable`.**
Basis ausschließlich die lokal bestätigte **Stage 4b-3**:
`stage4b3-stable` → `007798914c4e3189ee98921a9b9c661ecdbbbbd6`,
getesteter Programmcommit `a8766f8df9fcea8279181a5d13b772db15ecc954`.
Keine Entwicklung auf Stage 4b-2. Alle neun lokalen ASM-Dateien und sämtliche
16 Stage-4b-3-Release-Dateien wurden gegen Stable-Commit/Prüfsummen geprüft.
Basis-PRG SHA256: `407652e3489bcdb70d1133ad56dcdba5c28bad33b3fdc66983741806e224fb24`.

## Formationsdrift und unveränderter Player

`a_FORM_STEP_TICKS=2`; Offset −8..+8, keine zusätzliche Pause am Umkehrpunkt.
Nach Formationsabschluss beginnt der Timer bei2: +1 nach2, +8 nach16 Updates;
+8→−8 braucht32, vollständiger Zyklus64 Updates. Bei50Hz:25 logische Pixel/s.
Player unverändert1 logischer Pixel pro Update, also50/s. Beide benutzen
identische H640-X-Verdoppelung; kein anderer Geschwindigkeitsmaßstab.

Drift genau einmal in `a_preframe`, vor dem22-Gegner-Loop. Alle FORMATION-Slots
lesen denselben Offset; keine22fache Addition. ENTRY/ATTACK integrieren weiterhin
nur Originalkurven. Beim Angriffstart ist der aktuelle sichtbare X-Wert der
Anker; es wird danach kein zusätzlicher Drift auf die Kurve addiert.
RETURN berechnet bei jedem Update den aktuellen Zielplatz und bewegt sich
mit ±1 je Achse dorthin. Timer/Offset/Richtung werden bei Levelstart/R zurückgesetzt.

Player-Aufruf unverändert: `main_loop`→`offscreen.r_move`→`game.c_move`→
`v014_move_record`. Ein einziges DEC/INC bei gehaltenem Links/Rechts, X0..224,
Y184 konstant, kein Frame-Teiler. Renderer und sämtliche Player-Routinen sind
im strikten PRG-Vergleich geschützt.

## Bindende Gegner→Kurven-Zuordnung

Referenzen aus Branch `analysis-attack-descriptors`, unverändert übernommen:
[attack_descriptor_analysis.md](attack_descriptor_analysis.md),
`tools/analyze_attack_descriptors.py`. Das Audit wurde auf den tatsächlich
vorhandenen81793 VYLV-Bytes ausgeführt:

| Befund | Ergebnis |
|---|---|
| Levels / Gegnerrecords |100 /2194|
| Kurvenzahlen1/2/3/4 |24/61/10/5 Levels|
| Ungültige Gegnerindizes |0|
| Größte komprimierte Kurve |217 Bytes|
| Level1 |2×183 Bytes,11 Gegner je Index|
| Level2 |3 Kurven163/163/217, Zuordnungen7/7/8|
| Level5 |171/119 Bytes,11/11 Gegner|

6-Byte-Gegnerrecord: X WORD LE, Y WORD LE, `graphic_type` BYTE, **`attack_index`
BYTE bei+5**. `e_init` übernimmt den Wert in `a_index[slot]`; keine Ableitung aus
Grafiktyp oder Gruppennummer. Zufall wählt weiterhin ausschließlich einen
lebenden FORMATION-Gegner. `a_start` und `a_curve` lesen dessen festen Index.
Es gibt keine zweite Zufallsauswahl einer Kurve und keine Indexmutation während
seiner Lebensdauer; R liest die Originalwerte neu.

**Stage4b-3 verwendete diese feste Indexadressierung bereits.** Die Stage4c-
Änderung bestätigt deren Semantik ausdrücklich, erweitert die zentrale
Deskriptorstruktur und ergänzt Sicherheitsprüfungen; sie vertauscht keine Kurven.
Die Semantik ist durch die konvertierte Datei **und Benutzerbeobachtung am
Originalspiel** gestützt. Eine unabhängige Disassemblierung des Amiga-Interpreters
liegt weiterhin nicht vor. Zufallsintervalle/Finite-Endmarker-Fallback bleiben
die dokumentierten Stage4b-3-Regeln.

Level1: Index0 beginnt mit `92 92 02`, Index1 mit `12 12 02`.
Erste Deltas(−1,+2)/(+1,+2), summierte Enddeltas **(+80,+168)/(−80,+168)**.
Die Kurven sind schrittweise exakt horizontal gespiegelt; erste Richtung und
Endsumme nicht verwechseln. Alle183 Bytes werden unverändert verbraucht.

## Zentrale Struktur für bis zu vier Kurven

| Laufzeitfeld | Adresse | Inhalt |
|---|---|---|
|`a_index`|`$6F80–$6F95`|22 stabile Gegnerindizes|
|`a_ptrlo`|`$6FEC–$6FEF`|vier Pointer-Lowbytes|
|`a_ptrhi`|`$6FF0–$6FF3`|vier Pointer-Highbytes|
|`a_length`|`$6FF4–$6FF7`|vier Byte-Längen|
|`a_curve_count`|`$6FF8`|aktuelle Kurvenzahl1..4|

Die Arrays liegen in der bereits in Stage4b-3 freigehaltenen128-Byte-Lücke
`$6F80–$6FFF`; keine neue RAM-Allokation. Vorherige Zweierfelder `$6FD8–$6FDD`
werden nicht mehr als Deskriptoren benutzt. `a_init` erhält alle22 Indizes,
löscht übrigen Laufzeitzustand und liest `attack_count` aus WORD LE Levelheader+6.
Highbyte muss0, Lowbyte1..4 sein. Alle Indizes müssen kleiner als Count sein.

Jeder Deskriptor ist WORD-LE-Länge plus komprimierte Originalbytes. Unterstützt
1..255 Bytes, Highbyte0, Länge0 unzulässig; dies deckt alle100 vorhandenen
Levels mit maximal217 Bytes ab. Der bestehende Cursor bleibt ein Byte.
Die vorhandenen begrenzten `read_word`/`skip_curve`-Routinen verhindern
Zugriffe über das Ende der aktuellen Level1-Kopie `$7951` exklusiv. Nach dem
letzten Deskriptor muss der Cursor exakt dort stehen; keine ungelesenen Restbytes.

Bei ungültigem Index, Count, Länge oder Recordgrenze wird Fehler7 gesetzt.
`a_start` prüft vor Zustandsänderung, `a_curve` vor Pointerzugriff und vor
Patchen von `a_read`. Der bestehende Fehlerpfad stellt BASIC sauber wieder her.
Die Tests überprüfen auch einen nach Initialisierung absichtlich beschädigten
Index; kein fremder Kurvenzugriff erfolgt.

**Vorbereitung, keine Levelwechsel-Engine:** Das Spiel lädt/initialisiert weiterhin
Level1. Die Deskriptortests speisen isoliert die originalen Kurvenlisten der
Levels100/1/2/47 (1/2/3/4 Kurven) in die begrenzte Kopie und prüfen jeden Pointer,
jede Länge und alle Bytes. Keine künstlichen Kurven im ausgelieferten Spiel.
Ein späterer Levelwechsel muss zusätzlich vollständige Record-Kopie, Gruppen,
Grafik-/Slotzahlen und Sonderlevel behandeln. Levels25/50 haben unbenutzte
Index1-Deskriptoren;25/50/99/100 enthalten ungewöhnliche Ein-Byte-Kurven.
Diese werden nicht willkürlich als normale Flugmechanik interpretiert.

## Speicher und Basisschutz

Neuer/generischer Parser `$4B4A–$4BF0`, guarded Start/Helper `$9A56–$9AF2`,
guarded Bewegung `$9F10–$9FEA`, weiterhin unter `$A000` und ohne ROM-Overlay.
Keine neuen DMA-Listen, Crop-Puffer, VIC-Modi oder RRB-Änderungen.
Strikter Baselinevergleich erlaubt nur diese Codefenster, exakt geänderte
Timer-Ladeoperanden und überprüfte JSR/JMP-Relokationen zu verschobenen
`a_*`-Labels; aktuell433 geänderte PRG-Bytes, keine Größenänderung.

Erhalten: originale Einflugpunkte und Gruppenstarts, Y-Offset−25 (Slots0..74),
transparente Animationsoberkanten0/1/2/2/2/1, ClippingY0..199/HUD-X240, Typ14→15
mit sechs Frames, sichtbare ENTRY-/ATTACK-Schüsse mit globalmax4, max3 ATTACK,
fixe Projektilzielposition, sieben Explosionsframes, Kollision/Score/Highscore,
Leben, steuerbarer150-Update-Respawn, GAME OVER/R und X/BASIC.

## Build und automatische Prüfungen

```sh
python tools/analyze_attack_descriptors.py assets/VYLV.DAT
python tools/analyze_stage4c_attack.py
python tools/build_stage4c.py --kickass /pfad/zu/KickAss.jar
MEGA65_ROM=/pfad/zu/MEGA65.ROM PYTHONPATH=/pfad/zu/py65:tests:tools \
  python -m unittest test_stage4c
```

KickAssembler5.25 gepinnte Prüfsumme, Java/Python3, py65 1.2.0 für den bestehenden
CPU-/DMA-/SYS-MAP-Testadapter; keine neuen Abhängigkeiten. Release
`releases/stage_4c/`: neun ASM-Dateien,43777-Byte-PRG,819200-Byte-D81 mit
STAGE4C/VYLV.DAT/VYGR.DAT, Symbole, Mapping, Build-/Speicherbericht und Prüfsummen.
Alle16 Release-Dateien im unabhängigen Zweitbuild byteidentisch.

57/57 Tests bestanden (577,671 Sekunden). Geprüft wurden Originaldaten und
Deskriptoren aller100 Levels, Parser/Bounds/Fehlerpfade, feste Kurven pro Gegner,
Drift-Takt, Player-Bewegung, Einflug/Schüsse/Rückkehr, Kollisionen, Explosionen,
Respawn/Game Over sowie ROM-Mapping, BASIC-Exit und erneuter Start im CPU-/DMA-Modell.
160-Frame-Lauf: durchschnittlich116370, maximal121597 Modellzyklen/Frame.
Dies ist keine Messung unter XEMU; die folgende Benutzerabnahme wurde inzwischen bestätigt.

## XEMU-Abnahme (vom Benutzer bestätigt)

ROM V920395/BASIC80×25, D81 einlegen:

```basic
LOAD "STAGE4C",8
RUN
```

- Gehaltenes Links/Rechts:1 logischer Pixel/Frame, Y184, Grenzen0..224.
- Nach Formationsaufbau:Offsetänderung nur jede2 Updates,−8..+8,
  32 Updates zwischen Umkehrpunkten,64 je Zyklus, keine Zusatzpause.
- Einflugstarts wie Stage4b-3, kein WAIT/stehender rechter Vorlauf; erstes
  sichtbares ENTRY-Projektil vor Formationsabschluss, globalmax4.
- Kurve pro Gegner stabil: linke elf Index0, rechte elf Index1; keine
  zusätzliche zufällige Kurvenwahl, maximal3 ATTACK.
- Original183 Punkte, bekannte vertikale Auslaufphase und ReentryY−16;
  RETURN erreicht seinen aktuell driftenden und vertikal ausgerichteten Slot.
- HUD/Randclipping, Treffer/Score/Explosion/Leben/steuerbarer Respawn,
  GAME OVER erst nach Explosion, R mit Highscore-Erhalt, X und erneuter Start.

Diagnosen: signed Offset `$6FE0`, Drift-Timer `$6FE2`, Gegnerindex `$6F80+slot`,
Count `$6FF8`, Pointer/Lengths wie Tabelle; Status `$1C00`, Phase `$1EC6`,
Cursor `$1E9A`, Kurvenanker `$6F96/$6FAC`, vier Gegnerslots ab `$1B02`.
Benutzerfreigabe: „Stage 4c ist stabil“. Kein unabhängiger Hardwaretest.
Die Stable-Sicherung ändert nur Dokumentation; Quellen, PRG und D81 bleiben unverändert.
