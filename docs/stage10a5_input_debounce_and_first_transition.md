# Stage10a5 – Entprellung in Menü/Highscore, Levelübergang vor dem ersten Level

Basis: Stage10a4 (Branch `stage10a4`, vom Benutzer am 23.10.2026 bestätigt:
Doppelschüsse beseitigt, Respawn-Blinken wie im Original). Separate Quellen
`src/engine/stage10a5*.asm`, `src/tests/stage10a5*.asm`, Build
`tools/build_stage10a5.py`, Release `releases/stage_10a/stage10a5/`. Stage10a4
und ältere Stände unverändert; das Buildskript prüft Stage10a4 gegen seinen Commit.

## Benutzerbefunde

1. Weitere Stellen, an denen auf den Joystickknopf gewartet wird, registrieren
   oft zwei Ereignisse, besonders beim Wechsel vom Highscore-Screen zum
   Startbildschirm.
2. Beim ersten Levelstart spielt der Amiga die Levelwechsel-Animation samt Sound.

## Alle Warte-/Bestätigungsstellen

| Stelle | Abtastung bisher | Fehlerbild | Stage10a5 |
|---|---|---|---|
| Spiel, Player-Schuss | 1×/Frame | Doppelschuss | bereits Stage10a4 (2 losgelassene Frames) |
| Get ready / Respawn | setzt Feuer-Latch | – | unverändert, nutzt Stage10a4-Entprellung |
| Highscore-Tabelle verlassen | **freilaufende Schleife**, viele Abtastungen pro Frame; ein „losgelassen“-Sample schärft | Prellen beim Drücken/Loslassen beendet die Tabelle sofort | 1×/Frame (`joy_frame` in `frame_tick`), 2 losgelassene Frames nötig |
| Highscore-Seitenwechsel | freilaufend | doppelter Seitenwechsel möglich | 1×/Frame |
| Menü-Freigabe nach Highscore/Spielende | 1 Frame alles losgelassen | ein Prellframe schärft das Menü, gehaltener Knopf startet das Spiel | 2 aufeinanderfolgende Frames alles losgelassen |
| Menü-Feuer (Start/Bestätigen) | 1 losgelassener Frame schärft | Prellen bestätigt doppelt | 2 aufeinanderfolgende losgelassene Frames |
| Menü-Start nach Loslassen | 1 Frame | startet höchstens früher | unverändert |
| Namenseingabe | Tastatur-FIFO, kein Joystick | – | unverändert |
| Game Over / R | Tastaturmatrix | – | unverändert |

Die Ursache „Highscore → Startbildschirm“: Der Highscore-Code fragte den Joystick
in seiner Warteschleife tausendfach pro Frame ab. Ein einziges prellendes
„offen“ beim Loslassen schärfte den Knopf, das nächste „zu“ verließ die Tabelle.
Das Menü wurde dann ebenfalls nach einem einzelnen losgelassenen Frame scharf.

## Erster Levelstart

Ein neues Spiel (F1/F2 aus dem Menü) läuft jetzt wie ein Levelwechsel ab:
Sternbeschleunigung mit Soundereignis 8, konzentrische Ringe mit Ereignis 9,
dann Laden des gewählten Levels und 100 Frames Get ready. Der Übergang
spielt das gewählte Level (nicht +1) und überspringt das Abschluss-Gate
(kein Spielerwechsel, kein Bonusfortschritt). Der Zweispieler-Zugwechsel nach
einem Tod (`twop.resuming=1`) behält seinen direkten Get-ready-Start.

| Stelle | Änderung |
|---|---|
| `integration.start_ready` | `jsr twop.ready` → `first_ready`, `jsr gr_begin` → `first_start` (je 3 Byte) |
| `transitionfx.finish` | Ende `lda next_level / jmp gr_completed` → `jmp first_finish` + 3 NOP |
| `$75B0–$75E3` | `first_ready`, `first_start`, `first_finish`, `first_pending`; freier Rest unterhalb `LEVELCOPY=$7600` |

## Adressen und Prüfung

- `STAGE10A5.PRG` gleich lang, kein Symbol verschoben. Geänderte Bytes nur:
  `$75B0` (neu), `$BF8C` (finish), `$CC2C`/`$CC41` (start_ready) sowie die
  VYMN-Länge/Summe/Kopf in `load`, `finish_menu_load`, `expected_header`.
- Menü-Overlay und Highscore-Overlay geändert (eigenständig geladen; Einsprünge
  `$7000` bzw. `$2100` unverändert, Engine nutzt keine internen Adressen).
- Übrige DAT-Dateien und Audio-Core byteidentisch zu Stage10a4.
- `tests/test_stage10a5.py` (py65 auf den gebauten Programmen, 10/10): Menü
  ignoriert gehaltenen Knopf und Einzelprellen, Highscore-Schleife liest `$DC00`
  nicht mehr, zwei losgelassene Frames vor dem Verlassen, neues Spiel →
  Übergang mit gewähltem Level → Laden ohne Abschluss-Gate, Resume → direkt
  Get ready. Hostprüfungen, keine XEMU-/Hardwaretests.

## Abnahme (Hardware)

Highscore mit Feuer verlassen → Menü erscheint, startet nicht von selbst; Menüstart
einmalig; Seitenwechsel einzeln. Neues Spiel F1 und F2: Übergangsanimation mit
beiden Sounds, danach Get ready und das gewählte Level. F2-Zugwechsel nach Tod
unverändert; spätere Levelwechsel unverändert.
