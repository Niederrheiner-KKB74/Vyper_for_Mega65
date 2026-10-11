# Stage 5a – zentrale Levelverwaltung

Issue #23. Teststand im Branch `stage5a`, ausschließlich von der lokal und auf
GitHub gesicherten Referenz `stage4c-stable` (`fe81bf9`) abgeleitet.
Stage4c-Quellen, Release-Dateien und alle Originalassets bleiben unverändert.
**Keine Stable-Markierung ohne ausdrückliche Benutzer-XEMU-Bestätigung.**

## Zustände und Bedienung

`level.number` ist1..100. `level.mode`:0 PLAY,1 LEVEL_CLEAR. GAME_OVER bleibt der
vorhandene Playerzustand4. Jeder Programmlauf startet über den SEQ-Loader in Level1.

`level.transition(A)` ist der gemeinsame Initialisierungspfad für normale und
Testwechsel. Er bewahrt Score, Highscore, Leben und Animationseinstellungen,
stoppt Sprites, wählt/prüft den Originalrecord, initialisiert Gruppen und Gegner,
löscht Projektile/Explosionen/Kollisionszustände/Timer/Drift/private Grafikpuffer,
zentriert den Player bei112/184 und zeichnet Spielfeld/HUD neu.

- Im laufenden Spiel: `+` bis maximal100, `−` bis minimal1, kein Umlauf.
  PETSCII `$2B/$2D`; gemeinsames Latch mit tatsächlicher Matrixfreigabe
  (MEGA65 `$D614` Zeile5, `$D613` Bits0/3). Der Abfrageselektor wird restauriert.
  Diese Tasten verändern nicht mehr die Animationsgeschwindigkeit.
- LEVEL_CLEAR erst bei **allen23 allokierten Gegnerslots DEAD** (unbenutzte Slots
  sind ebenfalls DEAD) und keinem Player-EXP/WAIT/GAME_OVER. Wartende, einfliegende,
  angreifende und zurückkehrende Gegner zählen als lebend, auch offscreen.
- Gameplay in LEVEL_CLEAR eingefroren; Projektilaktivierungen und VIC-SPREN werden
  gelöscht. HUD und Player bleiben sichtbar, kein weiterer Treffer/Lebensverlust.
  Text: `LEVEL CLEAR`, `PRESS BUTTON TO CONTINUE`, mittig im240-Pixel-Playfield.
- Ein **neuer** Port2-Feuerdruck nach Freigabe startet den nächsten Level. Ein
  bereits gehaltener Feuerbutton beim letzten Abschuss genügt nicht. Nach100→1;
  Score/Highscore/Leben bleiben erhalten. +/− sind in LEVEL_CLEAR deaktiviert.
- GAME_OVER: nur R-Neustart oder X. R: Level1, Score0, drei Startleben, Highscore
  erhalten; vorhandene Entprellung bleibt. +/− können GAME_OVER nicht umgehen.
- X bleibt auch in LEVEL_CLEAR ein sauberer BASIC-Exit. Neuer RUN lädt/verifiziert
  die Originaldaten erneut und startet Level1.

## Recordverwaltung und Originalkurven

`level.load_record` liest den achtbyteigen VYLV-Verzeichniseintrag aus High RAM,
prüft Datei-/Puffergrenzen, kopiert den Record nach `$12000`, dann ausschließlich
seinen8-Byte-Kopf nach `$7600`. CPU-Zeiger auf `$2000...` referenzieren **Bank1**;
`level.read_record` verwendet die bestehende physische F018A-DMA-Liste und ein
separates Byte bei `$6A08`. Keine MAP-/ROM-/Zero-Page-Umschaltung nötig.

`s3b2.prepare` prüft Gruppensummen, Gegnerfelder, Grafikdeskriptoren und
Angriffsindizes. `entry.e_init` verarbeitet1–4 variable Einfluggruppen,
20/22 vorhandene Gegner, WORD-Kurvenlängen/-cursor sowie WORD-Verzögerungen.
`attack.a_init` prüft1–4 bounded Deskriptoren bis zum **dynamischen Recordende**;
`attack_index` ist unverändert pro Gegner gespeichert. Zufall wählt nur den Gegner.

Bestehende Nibble-Dekodierung, ein Kurvenpunkt pro Update, getrennte Spawnposition,
parallele Gruppen und ihre Originalintervalle bleiben. Der gemeinsame Y-Offset
ist jetzt `−min(original formation_y)` pro Level, relative Plätze bleiben gleich.
Formation±8,1px/2Frames; Player1px/Frame, nur X und vollständig im Playfield.
Angriff/unsichtbarer unterer Auslauf/ReentryY−16/Rückkehr zu bewegtem Slot bleiben.
Die provisorischen früher dokumentierten Original-Timing-/Endmarkerdetails werden
hier nicht nachträglich als unabhängig rekonstruierte Amiga-Regeln ausgegeben.

HUD-Punkte: `k=(level−1)//10`, Formation100+50k, ENTRY/ATTACK175+50k.
Score/Highscore bleiben32-Bit mit vorhandener Sättigung. Keine Punkte aus VYLV.

## Grafikverwaltung und Clipping

Alle239 Originalframes bleiben vollständig geladen in VYGR. Pro Gegner werden
Framequelle, Framezahl und unabhängiger Animationscursor geführt. Bei einem
Animationsupdate wird jeder Cursor gegen seine eigene Framezahl gewrappt.

Der aktuelle Originalframe wird physisch nach `$9840` übertragen und gegen eine
separat geladene Originalkopie in `$6800/$6900` rückverglichen. Vollständig sichtbare
Gegner verwenden eine direkte Kopie in ihren vorhandenen privaten256-Byte-Puffer;
teils sichtbare verwenden die gleiche Geometrie und einen byteweisen Nibble-Crop
über `$5640/$CA00`. Transparenz, Guards, Palette, sechs bestätigte Typ15-Frames
und sieben unabhängige Originalexplosionen bleiben erhalten. Kein RRB-Modusumbau.

Der neue Crop kopiert ganze Nibblepaare statt256 Einzelpixel zu prüfen. Ungerade
linke Schnittkanten setzen obere/untere Nibbles benachbarter Bytes korrekt zusammen;
bei ungerader Restbreite bleibt das letzte obere Nibble transparent. Rest/Guards
werden physisch gelöscht. Der isolierte F-Test behält seinen bisherigen Clipper.

**Mapping:** ausschließlich VYLV14→VYGR15 ist bestätigt. Alle weiteren Einträge
verwenden ausdrücklich die vorhandene vorläufige zentrale Tabelle
`assets/vylv_vygr_mapping.json`. Weder Originaldaten ändern noch Typen verwerfen.
Level71 benötigt6 Indizes; Level10022, alle werden individuell berücksichtigt.

## Benutzerfreigegebene Einschränkung

Ein-Byte-Angriffskurven haben noch keine belegte Sonderinterpretation:
Level25/50: `01/01` (Index1 unbenutzt),99:`07/06/06/07`,100:`07`.
Der Benutzer hat ausdrücklich freigegeben, **Angriffe in diesen vier Levels
vorläufig zu sperren**. Formation, Originaleinflug, ENTRY-Schüsse, Kollisionen,
Level Clear und Wechsel bleiben verfügbar. T/E-Testangriffe sind dort ebenfalls
gesperrt. Diese Levels werden nicht übersprungen und ihre Bytes nicht verändert.
Level25/50-Ein-Byte-Einflugdaten werden unverändert durch den vorhandenen
Nibble-Interpreter ausgeführt, dann regulär zur Formation zurückgeführt;
eine besondere ursprüngliche Amiga-Sonderlogik wird dafür nicht behauptet.

## Kapazität und Speicherkarte

Alle100 Records werden automatisiert geparst:2194 Gegner, maximal22/Level,
maximal4 Gruppen,1706 Recordbytes,469 Einflugbytes,2100 Startverzögerungsframes.
Angriffskurven maximal217 Bytes. Alle Formationsplätze inklusive±8-Drift passen
vollständig in `[0,240)×[0,200)`. Integrierte Kurven bleiben in signed16-Bit.
Maximal23 RRB-Pixies inklusive Player bei weiterhin24 Slots/Zeile.

| Bereich (inklusive) | Verwendung |
| --- | --- |
| `$1D80–$1DB1` | Levelzustand, Recordende, Parser-/Crop-Arbeit |
| `$6A00–$6A08` | VYGR-Deskriptor und physisches Einzelbyte-Leseziel |
| `$6A20–$6A43` | vier Gruppenpositionen/-pointer/-längen/-größen |
| `$6A50–$6A7B` |22 Cursor-High-/Verzögerungs-High-Bytes |
| `$6A80–$6AD7` |22 Grafikquellen/-zahlen/-cursor |
| `$10000–$115FF` | vorhandene22 private guarded Pixies (5632 Bytes) |
| `$12000–$126FF` | neuer bounded aktiver Record (1792-Byte-Budget) |
| `$7600–$7607` | ausschließlich aktueller8-Byte-Kopf |
| `$7608–$76B1` | verlegter Angriffskurvenparser; Headerkopie überschreibt ihn nicht |
| `$3200–$3339` | neuer bounded Recordparser |
| `$3400–$3472`, `$34A0–$3554` | private Cache-/Crop-Helper |
| `$6000–$6627` | zentrale Levelverwaltung |
| `$6700–$67FF` | unveränderliche256-Byte-Blankvorlage |

Der obsolete frühe2000-Byte-Color-Templatebereich `$6000` wird für Code frei,
weil der bestätigte HUD-/RRB-Aufbau bereits alle4800 Colorbytes vollständig
initialisiert. Der alte Vorlagenkopierer wird durch RTS ersetzt. Die vollständigen
BASIC-Color-Backups und Exit-Restaurierung bleiben erhalten. Die Initial-Signatur-
kopie im Loader ist auf8 Bytes begrenzt; der ursprüngliche849-Byte-Copy würde sonst
den neu verlegten Parser überschreiben. SEQ-Lader/SETBNK und vollständige Dateiprüfung
bleiben erhalten. Einige Codeadressen verschieben sich; finale Map im Release.

Keine neuen ausführbaren Routinen ab `$A000`: ROMA-/ROMC-Overlay bleibt geschützt.
Die alte `$B800`-Rendererarchitektur behält ihre bestehende ROMA-aus-Bedingung;
neue Daten-/Parserhelper funktionieren auch bei gesetzten ROMA/ROMC-Bits.
Screen `$E000–$F2BF`,192 Bytes/Zeile, physische MAP-sichere Stores und4800 Colorbytes,
Loader-/Grafikpuffer, Originaldatenziele und Player/Joystick bleiben gleich.

## Reproduzierbarer Build und Tests

```sh
python tools/analyze_stage5a_capacity.py
python tools/build_stage5a.py --kickass /pfad/zu/KickAss.jar
MEGA65_ROM=/pfad/zu/MEGA65.ROM PYTHONPATH=/pfad/zu/py65:tests:tools \
  python -m unittest test_stage5a
```

KickAssembler5.25 (gepinnt), Java, Python3; CPU-/DMA-Testadapter mit py651.2.0 und
bereitgestelltem ROM V920395. Keine ROM-Datei im Release. D81:819200 Bytes,
`STAGE5A` PRG sowie beide unveränderten SEQ-Dateien `VYLV.DAT`, `VYGR.DAT`.
Alle18 Release-Dateien im unabhängigen Zweitbuild byteidentisch.

26 unterschiedliche automatische Tests bestanden: vollständiger23-Test-Lauf
(149,121s) plus drei zusätzliche gezielte Checks (19,740s). Geprüft wurden alle100
Originalrecords im tatsächlich assemblierten Initialisierungspfad, alle verwendeten
Grafikframes von Level100, WORD-Einflug mit469 Punkten und langen Verzögerungen,
normaler/testweiser Wechsel und100→1, Entprellung, Werteerhalt, GAME_OVER/R/X und
erneuter RUN. Weitere Checks:7 Explosionen, Respawn/Unverwundbarkeit, Punkte und
Kollisionen, ENTRY-Schuss-/Angreiferlimits, Rückkehr zu bewegten Slots.
402 aufeinanderfolgende Einflug-/Formationupdates für alle22 Gegner stimmen
zustands- und koordinatengenau mit archiviertem Stage4c-Maschinencode überein.
140 Rand-/Eckfälle stimmen pixelgenau mit den Originalframes überein.
Worst-case22-Pixie-Renderer im Modell:441719 Zyklen, vorher824211; keine RRB-
Überläufe. Vollsichtige Fälle144565–165619 Zyklen. Dies umfasst nicht vollständig
DMA-Wartezeiten/IRQs oder sonstige Hauptschleifenarbeit und ist keine50-Hz-Garantie.

CPU-/DMA-Modell ist kein XEMU und keine tatsächliche Rasterzeitmessung. DMA-/IRQ-
Wartezeiten sind damit nicht vollständig abgebildet. Die Benutzerabnahme ist offen.

## XEMU-Abnahmeplan

D81 einlegen, `LOAD "STAGE5A",8`, `RUN` (ROM V920395/BASIC80×25).

1. Level1 mit Stage4c vergleichen: Wartezustand unsichtbar, Einflugstarts und
   Animation, FormationY0,±8/2Frames, ENTRY/ATTACK-Schüsse, Player1px/Frame.
2. Per +/− Level1→2→3,5,25,50,71,99→100 testen; bewusst loslassen,
   gehaltene Taste springt nicht mehrfach. − bei1/+ bei100 ohne Umlauf.
3. Wechsel während ENTRY/ATTACK/Explosion: keine Geistergrafik, alle Projektile
   entfernt, HUD/Score/Highscore/Leben erhalten, Player wieder112/184.
4. Unterschiedliche Grafiktypen/Framezahlen in71/100 beobachten; vorläufiges
   Mapping beachten. In25/50/99/100 absichtlich keine Angriffe, ENTRY-Schüsse bleiben.
5. Letzten Gegner abschießen: seine Explosion vollständig, dann beide mittigen
   Textzeilen. Gehaltener Button startet nicht weiter; loslassen/erneut drücken.
   Level100 regulär abschließen:1 statt GAME_OVER, Werte erhalten.
6. Treffer/Explosion/Respawn: Player drei Sekunden steuerbar unverwundbar;
   Schusslimit4 und Angreiferlimit3, Rückkehr zu driftendem Slot, Punkte korrekt.
7. Letztes Leben: komplette Explosion vor GAME_OVER; nur R/X. R ab1,Score0,
   drei Leben, Highscore erhalten. X während PLAY/LEVEL_CLEAR/GAME_OVER:
   sauberes BASIC mit Cursor; anschließend RUN erneut, Start bei1.
