# Stage 9a — automatischer Levelwechsel und Bonusleben

Issue #75. Entwicklungsbranch `stage9a`, kein Stable/kein Merge ohne Benutzerabnahme.
Basis: Stage8b Stable aus `main`, Merge `e932974e554f0cd9c84d1f95e63de6bf2e1853a2`,
mit getesteter IRQ-Korrektur `b6ea427`. Bestehende Quellen, Releases, Tools und
Originaldaten bleiben unverändert. Neue Dateien heißen `stage9a*`.

## Abschluss und Reihenfolge

Die bisherige LEVEL-CLEAR-/Feuerbestätigungsphase entfällt vollständig, ebenso
ihre beiden Textzeilen. `level.mode` verwendet 0=Spiel und 2=Übergang.
Nach `game.c_timers` und der bestehenden GAME-OVER-Prüfung führt ein gleich großer
JMP anstelle des bisherigen `JSR c_formula` über `level.continue_combat`.
Damit bleibt der dicht belegte Koordinator `$85B0–$85FB` unverändert groß.

`level.try_complete` akzeptiert den Abschluss nur, wenn:

- Spielmodus 0, kein isolierter Offscreen-Test aktiv;
- Player weder EXPLOSION noch WAIT/Respawn noch GAME OVER;
- alle 23 geprüften Gegnerzustände DEAD sind (22 nutzbare Gegner plus unbenutzter Slot).

Die ursprüngliche Levelinitialisierung weist jedem tatsächlichen Gegner bereits
WAIT_ENTRY zu, einschließlich verzögerter Gruppen. ENTRY, RETURN/Formation,
ATTACK, WAIT_ENTRY und EXPLOSION sind ungleich DEAD. Daher können ausstehende
Gruppen oder die letzte noch laufende Explosion keinen vorzeitigen Abschluss
auslösen. Es gibt keinen neuen dekrementierten Gegnerzähler.

Der erfolgreiche Pfad setzt **zuerst mode=2**, verbucht einmal den Bonusfortschritt,
aktualisiert das HUD und ruft die unveränderte `transitionfx.begin` auf. Erst dann
kehrt er ohne weitere Schuss-/Kollisionsarbeit aus dem Koordinator zurück.
Damit werden nach dem entscheidenden Explosionstimer keine neuen Projektile oder
Kollisionen mehr verarbeitet. Die bestehende Begin-Routine deaktiviert alle acht
Hardware-Sprites/Projektilslots, leert dynamische RRB-Zeilen, erhält HUD und Sterne
und startet den Übergang. Weitere Frames gehen ausschließlich an dessen FSM.
Ein bereits eingetretener letzter Playerverlust/GAME OVER zählt nicht als Sieg.
Bei laufender Playerexplosion mit verbleibenden Leben wird erst nach dem normalen
Respawn abgeschlossen; ein Bonus hebt GAME OVER niemals rückwirkend auf.

## Bonusleben

Zwei getrennte Bytes bei `$1FD9/$1FDA` reservieren den Fortschritt für P1/P2,
unmittelbar hinter der unveränderten Audiomailbox bis `$1FD8`. P2 bleibt inaktiv.
Nur P1 wird benutzt: 0→1→2→0, beim dritten erfolgreichen Abschluss genau +1 Leben.
Kein Bezug auf die numerische Levelnummer: Startlevel 3/99/100 und Umlauf100→1
ändern diese Regel nicht. Ein neues F1-Spiel (`integration.start_ready`) und R
(`level.restart`) löschen beide Fortschritte. Normale nächste Levels und die
unveränderte sofortige Testnavigation +/− erhalten sie; Testnavigation verbucht
keinen Abschluss und gibt keine Leben.

Stage8b besitzt einen WORD-Lebenszähler, startet mit 3 Leben und zeigt höchstens
8 Symbole im bestehenden 4×2-Feld. Bisher gab es keine Zuteilung zusätzlicher
Leben und keine separate Vergabeobergrenze. Stage9a verwendet deshalb zentral
`BONUS_MAX_LIVES=8` passend zur HUD-Kapazität. Das ist eine sichere MEGA65-Regel,
**kein belegtes originales Amiga-Maximum**. Bei 8 Leben wird ein verdienter Bonus
verbraucht, ohne den Zähler zu erhöhen oder spätere Boni anzusparen. Null Leben
und unerwartete nichtnull Highbytes werden nicht erhöht; es gibt keinen WORD-
oder HUD-Überlauf. Startleben, Tod, Respawn und HUD-Geometrie bleiben unverändert.
Die Menüzeile BONUS SHIP EVERY 3 LEVELS und alle anderen Texte bleiben erhalten.

## Übergang, Sound und unveränderte Funktionen

Die bestehende FSM läuft weiter mit 50 Frames beschleunigten Sternen, 39 Frames
farbigen und 39 Frames schwarzen konzentrischen Rechtecken und dem bisherigen
Levelaufbau. HUD, Sternpositionen und Timing werden nicht neu implementiert.
Sound24 wird am bisherigen Begin-Hook angefordert, Sound22 am bisherigen
Beschleunigung→Rechteck-Hook. Bestehende Pending-/Busy-/Preemptionregeln und
hochfrequentes Attic-Streaming nach DMA-Jobs und im Rasterwarten bleiben erhalten.
Audio-Codeimage und alle sieben DAT-Dateien sind bytegleich zu Stage8b.
Keine neue Verzögerungsschleife, kein RNG-Aufruf, keine neuen Soundeffekte.

`transitionfx.finish` übernimmt unverändert die nächste Levelnummer, einschließlich
100→1. Score, Highscore, Leben und sonstige bisher erhaltene Spielerzustände werden
weiter nach den bestehenden Regeln übernommen. +/− innerhalb des Spiels wechseln
weiter sofort und begrenzt auf1..100; während des Übergangs bleiben die bisherigen
Eingabefilter aktiv. X funktioniert in jeder Phase, R nur nach GAME OVER wie zuvor.

## Speicher und Build

Neu: zwei Bytes `$1FD9–$1FDA`, außerhalb der bisherigen Motionfelder bis `$1FCC`
und Audiomailbox `$1FD0–$1FD8`. Manager `$6000–$65E4` endet vor dem unveränderten
Audiogate `$662C`. Koordinator `$85B0–$85FB`, alle Audio-/DMA-/RRB-/DOS-/Attic-
Puffer, Grafikpools und Originaldatenadressen bleiben gleich. Brücke `$CB00–$CD54`
passt vor die Sterntabellen ab `$CD80`. Die Integrationsbrücke erhält nur den
F1-Bonusreset. Die IRQ-Korrektur in `audio8.rom_call` bleibt erhalten.

```sh
python3 tools/build_stage9a.py --kickass /path/to/KickAss.jar
PYTHONPATH=tests:tools:/path/to/py65-1.2.0 python3 -m unittest test_stage9a -v
```

Java, gepinnter KickAssembler5.25, Python3 und für die Tests py65-1.2.0.
Der Builder prüft alle bestehenden src/assets/tools/releases von main e932974
und die bisherigen Stable-Referenzen byteweise. Er verwendet die unveränderten
Original-Extraktoren und den Stage8b-Soundpacker; die zusätzliche Symbolkopie im
Arbeitsordner erhält dessen unveränderte private Dateinamenschnittstelle.
Quellen/Includes, PRG, sieben DATs, vollständiges819200-Byte-D81, Symbole,
Speicherkarte, Buildbericht und SHA-256 liegen unter `releases/stage_9a/`.
Start: D81 einlegen, `LOAD "STAGE9A",8`, `RUN`, Joystick Port2.

## Prüfungen und Abnahme

Das Protokoll `stage9a_test_results.txt` unterscheidet tatsächliche Hostprüfungen
von offener XEMU-Abnahme. Ausführung der assemblierten Instruktionen im begrenzten
CPU/KERNAL/VIC/DMA/Audio-Modell, einschließlich instruktionsweiser IRQ-Invariante;
kein vollständiger Emulator und keine reale Raster-/Hörmessung.
Zusätzliche Tests: ausstehende Gegnerzustände/letztes Explosionsende, sofortiger
Trigger trotz gehaltenem Feuer, Bereinigung aller Projektile, einmaliger Bonus,
3/6/9 Abschlüsse ab unterschiedlichen Startlevels,100→1, Navigation ohne Bonus,
Obergrenze8, R-Reset, kein Bonus bei Playerverlust/GAME OVER, X in jeder Phase.
Die bisherigen Stage8b-Audio-, Gameplay-, Loader-, BASIC-Exit-/RUN- und Lastprüfungen
laufen weiterhin; die manuell gestartete vollständige FSM-Prüfung bestätigt die
unveränderte24→22-Folge. Der automatische neue Einstieg wird separat geprüft.

In XEMU bitte mehrere Minuten prüfen:

1. Level1→2→3→4 ohne Texte/Bestätigung; nach dem dritten Sieg ein weiteres Lebenssymbol.
2. F1 ab3/99/100: Bonus erst nach drei tatsächlichen Siegen;100→1 korrekt.
3. +/− erzeugen keinen Bonus und löschen den bisherigen Fortschritt nicht.
4. Letzter Gegner während ENTRY/ATTACK/RETURN, vollständige Explosion; noch aktive
   Schüsse verschwinden beim Übergang, HUD und Playerzustand bleiben korrekt.
5. Playerverlust/Game Over am Levelende, R, wiederholtes neues Spiel und Obergrenze8.
6. Übergangsgrafik und Sounds24→22 ohne Aussetzer, zwei gleichzeitige Effekte unter
   hoher Grafiklast; X in jeder Phase, DIRECTORY und erneutes RUN.

XEMU-/Hardware-Erfolg wird hier nicht behauptet. **Kein Stable vor Benutzerfreigabe.**
