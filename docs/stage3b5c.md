# Stage 3b-5c – Softwarekollisionen und Spielzustände

Testrelease zu Issue #8 auf `stage3b-5c`, Basis `stage3b5b-stable`
(`e4540557938b342fbf8935cfce787410a3d77512`). Keine Stable-Freigabe ohne
Benutzerabnahme. Alle bisherigen stabilen Quellen, Release-Dateien und Tags
bleiben unverändert. Draft-PR #9 enthält jetzt die Implementierung.

## Build und Start

Python 3, Java und der bereits festgelegte offizielle KickAssembler 5.25:

```sh
python tools/build_stage3b5c.py --kickass /pfad/zu/KickAss.jar
python -m pip install -r tests/requirements-stage3b1.txt
python -m unittest discover -s tests -p test_stage3b5c.py -v
```

Der Builder extrahiert die archivierten Originalanimationen in einen temporären
Arbeitsordner, konvertiert die Explosionen, prüft den Assemblerhash, DAT-Hashes,
Speichergrenzen, begrenzte Änderungen gegenüber dem stabilen PRG sowie D81-
Dateiketten und BAM. Option `--output /tmp/neuer-ordner` ermöglicht einen
unabhängigen Rebuild. Alle erzeugten Dateien wurden bei einem solchen Rebuild
bytegleich bestätigt. `releases/stage_3b5c/` enthält PRG, D81, sechs ASM-Dateien,
Symbole, Speicherkarte, Buildbericht und SHA-256-Prüfsummen. Der vollständige
Git-Checkout enthält die Originalassets und die reproduzierbaren Builder.

D81 in XEMU einlegen, dann `LOAD "STAGE3B5C",8` und `RUN`.
Die zwei unveränderten SEQ-Dateien heißen `VYLV.DAT` und `VYGR.DAT`.
Joystick und Feuer bleiben erhalten; X beendet das Spiel in jedem Zustand.
SPACE und +/− regeln weiter die Gegneranimation, nicht die Explosionen.
T schaltet den isolierten Testangriff von Gegner Nr. 19 ab/an. E wechselt
seinen aktiven Teststatus zwischen ATTACK und ENTRY; dies sind keine
rekonstruierten Originalflugkurven. Player 2 bleibt inaktiv.

## Originalexplosionen und Palette

Originalquelle vom Benutzer: `assets/explosions/explosion_amiga_planes.txt`,
übernommen aus Branch `stage3b-5b`, Commit
`8ce37780dd86093522949b1ee4269f36d63d38b0`.
SHA-256: `f70c8f503fa50dfe43642485509d73b186bbbfd8f5dc0a0090ddaf06fad561a3`.

`tools/build_explosion_assets.py` liest genau acht geordnete Deskriptoren
$3819A, $381BA, …, $3827A. Pro Frame: drei 32-Byte-Bitplanes und eine
32-Byte-Maske. Zeilen werden exakt linear gemäß der neuen Quelldatei gelesen;
es wird keine Zeilenrotation aus der getrennten Spielerextraktion übernommen.
Für Pixel (x,y): Byte `2*y+x//8`, Bit `7-x%8`.
Maskenbit 0 → transparenten Index 0. Sonst Index
`1 + plane0 + 2*plane1 + 4*plane2`, passend zur bestehenden Bank-1-Palette.
Linkes Pixel im Low-Nibble, rechtes im High-Nibble: 128 Bytes je 16×16-Frame.
Die vorhandene Palette bleibt unverändert; keine Ersatzpixel werden erzeugt.
Prüfsummen und Format stehen in `assets/explosions/conversion.json`.
Die ursprüngliche Index-/RGB-Rekonstruktion der Engine bleibt die bestehende
Referenz; die sichtbare Explosion mit dieser Palette ist in XEMU noch abzunehmen.

Sieben unveränderliche 256-Byte-Glyphsätze enthalten je einen 64-Byte-Blankguard,
128 Originalbytes und einen weiteren Blankguard. Jeder explodierende Gegner
und der Player hat eigene Frame-/Tickzähler und gespeicherte Koordinaten.
Keine Explosion schreibt einen gemeinsamen beweglichen Grafikpuffer um.
Frame 0 beginnt am Treffertick; jeder Frame wird drei 50-Hz-Ticks dargestellt,
insgesamt 21 Ticks. Diese parametrisierbare Geschwindigkeit ist keine Behauptung
über die ursprüngliche Amiga-Abspielgeschwindigkeit.

## Korrektur nach dem XEMU-Test

Der bisherige letzte Animationsschritt verwendete den gelieferten Datensatz
„Frame 7 – descriptor $3827A“. Dieser enthält das Spielerschiff: gleiche
Transparenzkontur, 238/256 identische Pixel mit `player_ncm.bin`. Bei jeder
Explosion wurde dadurch kurz ein Schiff an der Gegnerposition angezeigt.
Dies ist ein falscher Quelldatensatz in der Sequenz, keine Verwechslung der
RRB-Adressen oder Palette. Der Benutzer bestätigt ausdrücklich: Es gibt nur
**sieben** Originalexplosionsframes; bei der Extraktion wurde das Spielerschiff
fälschlich mitgezählt. Die frühere Acht-Frame-Anforderung ist damit korrigiert.

Die Rohdatei bleibt zur Nachvollziehbarkeit unverändert. Der Konverter
kennzeichnet Datensatz 7 als ausgeschlossen, und der Build verhindert seine
Verwendung als Explosion. Nur Records 0–6 werden eingebunden und ausgewählt;
keine Ersatzgrafik oder Wiederholung wird ergänzt. Beide Explosions-Timer
verwenden die zentrale Framezahl 7. Auch die Playerexplosion und GAME OVER
enden nach dem vollständigen siebten Frame (3 × 7 = 21 Ticks).

Nach zusätzlicher Benutzeranweisung ist der Player während RESPAWN_BLINK nun
steuerbar. Der unveränderte Joystick-Mover läuft für ACTIVE **und** BLINK;
EXPLODING/WAIT_FORMATION/GAME_OVER bleiben gesperrt. Die Todesposition ist nur
der Wiederbelebungsstart, nicht eine laufende Positionsvorgabe. Feuer bleibt
wie bisher gesperrt; Treffer- und Lebenslogik ist unverändert unverwundbar.

## Zustände und Updatefolge

Gegner: DEAD=0, FORMATION=1, ENTRY=2, ATTACK=3, EXPLODING=4.
Alle 22 Pfadgegner und der zusätzliche Orbitgegner (Index 22) sind enthalten.
Lebende Gegner behalten ihre bisherigen Pfadschritte; EXPLODING/DEAD werden
unabhängig von Bewegung, Feuer und weiteren Treffern ausgeschlossen.
Nach Frame 6 wird der betreffende Gegner endgültig DEAD, bis zum neuen Spiel.

Player: ACTIVE=0 → EXPLODING=1 → WAIT_FORMATION=2 → RESPAWN_BLINK=3 → ACTIVE.
Bei letztem Leben endet EXPLODING stattdessen in GAME_OVER=4.

- ACTIVE: Bewegung, Feuer und Treffer zulässig.
- EXPLODING: eingefrorene Todesposition, keine neuen Treffer/Steuerung.
  Ein Leben wird genau einmal beim Eintritt abgezogen, niemals unter null.
- WAIT_FORMATION: unsichtbar, wartet auf reale Gegnerzustände. Nur DEAD wird
  ignoriert; alle übrigen müssen FORMATION sein. Laufende Explosionen und
  ENTRY/ATTACK blockieren. Ohne lebende Gegner ist die Bedingung sofort erfüllt.
  Der bestehende Testangriff kehrt in seiner 32-Tick-Formationsphase zurück;
  T kann ihn gezielt abschalten. Es gibt keinen zusätzlichen Warte-Zeitlimit.
- RESPAWN_BLINK: an derselben Todesposition, 150 Ticks, Sichtbarkeitswechsel
  alle 25 Ticks. Vollständig unverwundbar; Bewegung freigegeben, Feuer weiterhin gesperrt.
  Die Aufnahme ins Blinken ist der erste sichtbare Blinktick. Während des Blinkens folgt auch die unsichtbare Playergrafik den aktuellen
  Joystickkoordinaten. Nach den 150 Blinkticks bleibt der Player an seiner
  aktuellen Position sichtbar und wird ACTIVE. Gedrücktes Feuer
  muss nach der Sperre zunächst losgelassen werden.
- GAME_OVER: erst nach der vollständigen letzten Explosion. Sämtliche
  Projektilslots werden deaktiviert; Animation, Bewegung, Feuer und Treffer
  bleiben eingefroren. GAME OVER / R - RESTART / X - EXIT stehen lesbar im
  dynamischen RRB-Bereich, ohne den HUD-/Hintergrundpräfix umzubauen.

Pro Haupttick: bestehende Bewegung für freigegebene Objekte, eigene
Explosion-/Blinkzähler, Punkteformel bei Leveländerung, realer Teststatus,
Wartebedingung, vorhandene Projektilbewegung/Feuer, Kollisionen, Spritepublikation,
RRB und geänderte HUD-Felder. Auf dem Tick, der GAME_OVER erreicht, werden
Schüsse deaktiviert und die Abschlussanzeige einmal geschrieben.
Nicht aktive Playerzustände bleiben ohne eigene Feuerfreigabe; bestehende
Geschosse laufen außerhalb von GAME_OVER weiter und werden an Grenzen entfernt.

## Koordinaten und Hitboxen

Halboffene logische AABBs `[left,right) × [top,bottom)`. Berührende Kanten allein
sind kein Treffer. Konstanten stehen zentral in `stage3b5c_game.asm`:

| Objekt | Hitbox |
| --- | --- |
| 16×16-Schiff | x+2 bis x+14, y+2 bis y+14: 12×12 |
| Spielerschuss | gespeichertes x bis x+1, y bis y+4: 1×4 |
| Gegnerschuss | x−1 bis x+2, y bis y+4: 3×4 |

Der gespeicherte Projektil-X-Wert ist seine logische Mitte; Y ist die Oberkante.
VIC-Sprite-X wird weiterhin als `CHARX+2*x−1` (Player) beziehungsweise
`CHARX+2*x−3` (Gegner) publiziert. SPR640 fügt beim Rendern einen nativen Pixel
hinzu; die tatsächlichen nativen Breiten sind 2 bzw. 6 Pixel. Diese Abbildung
liegt über den dokumentierten logischen Hitboxen. Sprite-Y ist `CHARY+2*y`.
RRB benutzt dieselben logischen x/y. Keine VIC-Kollisionsregister werden benutzt.
Die bisherigen Begrenzungen halten alle AABB-Kanten im Bytebereich; keine
Vorzeichenverwechslung mit den getrennten signed-8.8-Geschwindigkeiten.

Deterministische Trefferreihenfolge:

1. Spielerschuss 0, dann 1; jeweils Gegner 0–22. Der erste Treffer verbraucht
   den Schuss, startet eine Explosion und vergibt einmal Punkte. EXPLODING und
   DEAD werden sofort übersprungen.
2. Gegnerschüsse 2–5 gegen ausschließlich ACTIVE. Nach dem ersten Treffer
   ist der Player nicht mehr ACTIVE; weitere Geschosse kosten kein Leben.
3. Direkte Rammkollisionen Gegner 0–22, nur ENTRY/ATTACK gegen ACTIVE.
   Player und Gegner explodieren; keine Abschusspunkte. FORMATION rammt nicht.

Ein Spielerschuss kann einen angreifenden Gegner also vor einer Rammkollision
im selben Tick vernichten. Schuss-/Rammfälle mit Blinkplayer ändern den Gegner
nicht. Keine automatische Wiederbelebung eines zerstörten Testgegners.

## Punkte, Highscore und Neustart

`k=(level−1)//10`, Formation `100+50*k`, ENTRY/ATTACK `175+50*k`.
Die Formel benutzt keine unbekannten VYLV-Wörter. 32-Bit-Awards/Score/Highscore,
unsigned Vergleich; Score wird bei Überlauf auf $FFFFFFFF gesättigt. Highscore
wird bei Score ≥ Highscore übernommen. Die siebenstellige Scoreanzeige zeigt
wie das bestehende HUD die unteren sieben Dezimalstellen; der gespeicherte
Wert wird nicht abgeschnitten. Die dreistelligen Punktefelder zeigen die
unteren drei Dezimalstellen. Die Formel unterstützt WORD-Level; tatsächlich
startet diese Stage stets Level 1, ohne neue Levelwechselsteuerung.
HUD-Felder werden weiter nur bei Änderung neu formatiert.

R/r/Shift-R im GAME_OVER startet ohne PRG-/Disketten-Neuladen Level 1:
Levelrecord wird per bestehender DMA aus $40328 nach $7600 kopiert und der
begrenzte Parser erneut aufgerufen, Typ 15/Frame 0 erneut aus geladenem VYGR
übertragen. Score=0, Leben=3, Level=1, Player-/Gegner-/Explosions-/Schuss-/
Blinkzustände und Pfadphasen, Testmodus, Animationsgeschwindigkeit und HUD
werden neu initialisiert. Highscore und ursprüngliche Video-/Sprite-/Color-
Sicherungen bleiben erhalten. Insbesondere wird `hud_init` nicht erneut
aufgerufen: dessen ursprünglicher BASIC-CHARXSCALE darf nicht überschrieben
werden. Auch fehlerhafte erneute Levelinitialisierung kehrt über den normalen
Exit zurück und erhält den Stack der Startupwrapper.

Entprellung: GAME_OVER beginnt ohne Neustartfreigabe. Erst eine leere GETIN-
Abfrage bei losgelassenem R (direkte Tastaturmatrix $D614 Row 2/$D613 Bit 1)
aktiviert R. Der Abfrageselektor wird sofort wiederhergestellt. Bereits
gepufferte/gedrückt gehaltene R-Tasten lösen daher keinen sofortigen Neustart
aus. X/x/Shift-X bleibt jederzeit möglich; alle anderen GAME_OVER-Tasten haben
keine Wirkung. Keine Highscore-Diskettenpersistenz, kein Zweispieler/Sound/
Originalangriffskurven-/Menüsystem.

## Speicher und Schutz der Baseline

Neue Runtime-Daten ausschließlich $1C00–$1CFF; kein KERNAL-RAM.
Die genaue Assemblykarte liegt beim Release. Unveränderte historische
Adresse und Codebytes werden durch den Builder verglichen, einschließlich
Loader, Spritekonfiguration, Grafikmapping, Bewegungstabellen und Exit.
Nur sechs JSR-Ziele werden ersetzt sowie Attack-Default 115 → 175.
Neue statische Bereiche müssen im stabilen PRG vollständig null sein;
das PRG endet wieder bei $C9FF ohne zusätzlichen Datensatz bei $CA00. Neuer ausführbarer Code und CPU-gelesene Tabellen liegen vollständig
unter $A000, insbesondere der Renderer bei $9D70. Die unveränderte ROMC-
Bankingoption darf $C000 überlagern; die dortigen Originalexplosionen werden
wie die bestehenden Player-/Orbit-Glyphen direkt vom VIC aus physischem RAM
gelesen. Es ist kein neues Banking erforderlich.

[Speicherkarte](memory_map.md), [Automatik und XEMU-Abnahme](stage3b5c_xemu_test.md).
