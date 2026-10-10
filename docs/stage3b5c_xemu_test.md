# Stage 3b-5c – Testprotokoll und XEMU-Abnahme

Status: **Testrelease, nicht Stable**. Ein vollständiger eigener XEMU-Lauf
wurde nicht durchgeführt; Abnahme durch den Benutzer ist ausstehend.
Referenzumgebung der bisherigen Abnahmen: ROM V920395, PAL/50 Hz, BASIC 80×25.
Das Benutzer-ROM wird nicht in den Repository-/Release-Dateien verteilt.

## Automatisch ausgeführt

- KickAssembler 5.25: vollständiges neues PRG erfolgreich assembliert.
- Gegenüber stabilem Stage-3b-5b-PRG: genau sechs JSR-Ziele und Attack-Default
  115 → 175 geändert; neue Bereiche zuvor null und neue Erweiterung unter $D000.
  Alle alten Symbole/Adressen unverändert. Bestehende stabile Dateien unverändert.
- Unabhängiger Rebuild: alle erzeugten Dateien bytegleich. Neuer CPU-Code liegt
  vollständig unter $A000; keine neue Abhängigkeit von ROMC.
- Original-VYLV/VYGR-Hashes, SEQ-Dateiketten, PRG-Dateikette, D81-BAM und sämtliche
  Disketteninhalte bytegenau geprüft. D81: 819.200 Bytes.
- `python -m unittest discover -s tests -p test_stage3b5c.py -v`:
  **14/14 bestanden** im verwendeten Cloud-Host.

Die Tests führen tatsächlich assemblierte Befehle mit schmalen CPU-/DMA-/VIC-
Modellen aus. Das Modell ist kein vollständiger XEMU-/ROM-/Videochip-Emulator.
Geprüft wurden:

| Bereich | Ergebnis |
| --- | --- |
| Acht Frames, jedes Bitplane-/Maskenpixel, Nibble-Reihenfolge und Blankguards | bestanden |
| Vollständiger Loader, Typ 15, sechs Frames, unveränderte Objektbewegung/Playergrafik | bestanden |
| Formation/ENTRY/ATTACK/Orbit, zwei gleichzeitige Schüsse, keine Doppelwertung | bestanden |
| Vier Gegnerschüsse: einmaliger Lebensverlust, gefrorene Playerposition | bestanden |
| Rammkollision: zwei Explosionen, keine Punkte; Formation/Blinken ignoriert | bestanden |
| Acht Frames je drei Ticks, gleichzeitige/versetzte Explosionen, Renderer ohne Überlauf | bestanden |
| WAIT auf reale Zustände, DEAD ignoriert, 150-Tick-Blinken/25-Tick-Wechsel | bestanden |
| Reale Frameupdates: Bewegung/Feuer im Blinken gesperrt, SPACE stoppt Explosion nicht | bestanden |
| Punkte-Levelgrenzen 1/10/11/20/21/100/65535, Carry, Sättigung, Anzeigenmodulo | bestanden |
| Halb offene Hitboxkanten, linker/oberer und rechter/unterer Spielfeldbereich | bestanden |
| Vollständige letzte Explosion vor GAME OVER, Textglyphen und Color-RAM-Attribute | bestanden |
| Ignorierte Tasten, gehaltenes R, drei Restarts, Highscore erhalten | bestanden |
| X/Shift-X, Video-/Sprite-/Color-/KERNAL-Zustand, zweiter RUN | bestanden |
| Ungültiger Levelrecord beim R: sauberer Exit ohne Stackfehler | bestanden |

Zusätzlich wird beim Setzen von `MEGA65_ROM` der Hash des bereitgestellten
ROM V920395 geprüft und dessen tatsächlicher Cursor-Blinkcode nach X ausgeführt.
Auch das ersetzt keinen vollständigen ROM-/XEMU-Lauf.

Die visuelle Palette, sichtbare Sprite-/RRB-Abbildung, Joystick am echten
Emulator und Tastaturmatrix mit dem tatsächlichen ROM müssen unter XEMU geprüft
werden. Die ursprüngliche Amiga-Explosionsgeschwindigkeit ist nicht belegt.

## Unter XEMU prüfen

D81 `VYPER_STAGE3B5C.d81` einlegen, `LOAD "STAGE3B5C",8`, `RUN`.

1. Beide DAT-Dateien geladen/verifiziert; HUD schwarz und lesbar, Gegner Typ 15
   mit sechs Frames, unveränderte Bewegung, 4×2-Lebensfeld, P2 inaktiv.
2. Joystick bewegen und Feuer mehrfach drücken/loslassen: höchstens zwei
   unabhängige Spielerschüsse. Testangriff erzeugt höchstens vier Gegnerschüsse.
3. Formationstreffer: Explosion bleibt an Treffposition, acht Originalframes,
   Gegner verschwindet dauerhaft, +100. T schaltet Testangriff ab/an.
4. Gegner Nr. 19 im Testangriff treffen: +175. E wechselt ATTACK/ENTRY, beide
   zählen +175. Die Flugbahn bleibt der bestehende Testpfad.
5. Gegnerschuss: ein Leben weniger, acht Frames an gespeicherter Playerposition;
   weitere Treffer während der Explosion ziehen kein weiteres Leben ab.
6. ENTRY-/ATTACK-Gegner berühren: beide explodieren, ein Leben weniger,
   keine Punkte. Formation und Blinkplayer lösen keine Rammkollision aus.
7. Nach Explosion mit Restleben auf reale Formation warten. Testangriff
   beobachten bzw. T abschalten; zerstörter Testgegner blockiert nicht.
8. Respawn exakt an Todesposition. Drei Sekunden lang Sichtbarkeit alle
   0,5 Sekunden wechseln; keine Bewegung/Feuer, keine Treffer. Danach sichtbar
   und wieder steuerbar. Grenzbereiche und mehrere gleichzeitige Treffer prüfen.
9. Letztes Leben: letzte Explosion vollständig, dann GAME OVER / R - RESTART /
   X - EXIT. Andere Tasten und SPACE/+/-/T/E haben keine Wirkung. Ein schon
   gehaltenes R startet nicht sofort neu; loslassen, dann erneut drücken.
10. R mehrfach: Level 1, drei Leben, Score 0, Highscore erhalten, korrekte
    Originalgrafiken und zurückgesetzte Test-/Schusszustände; kein Geistertext.
11. X sowohl im Spiel als auch GAME OVER: sauberer BASIC-Screen/Cursor, keine
    Sprite-Reste. Anschließend RUN und auch erneut LOAD/RUN ausführen.
12. Über mehrere Minuten 50-Hz-Stabilität, Farb-/RRB-/HUD-Artefakte und die
    Originalexplosionen visuell prüfen. Kein Stable-Tag vor dieser Bestätigung.
