# Stage 3b-5b – XEMU-Abnahme (vom Benutzer bestätigt)

Testumgebung des Benutzers: ROM V920395, BASIC 80×25, PAL / 50 Hz.
Codex hat keinen vollständigen XEMU-Lauf durchgeführt. Die automatischen CPU-/DMA-/
Sprite-/RRB-Tests und der reproduzierbare Build sind separat dokumentiert.

D81: `releases/stage_3b5b/VYPER_STAGE3B5B.d81`; Prüfsummen in `SHA256SUMS.txt`.
`LOAD"STAGE3B5B",8`, `RUN`. Testmodus anfangs aktiv, `T` schaltet ihn aus/ein.
Den Player nach unten bewegen, damit er unter der Abschussposition steht.
Gegner Nr. 19 (Arrayindex 18) darf als einziger feuern; zunächst unveränderter Pfad.

| Prüfung aus Issue #6 | Ergebnis |
| --- | --- |
| Beide Originaldateien verifiziert; 24 Pixies, Originalplayer und HUD korrekt | Gesamtabnahme bestätigt |
| Level 1 zeigt Typ 15 und spielt sechs Originalframes ab | Gesamtabnahme bestätigt; automatisch nachgewiesen |
| Zwei Spielerstrahlen an der oberen Mitte, X danach unverändert | Gesamtabnahme bestätigt |
| Kein dritter Schuss; Loslassen/erneutes Drücken und Wiederverwendung funktionieren | Gesamtabnahme bestätigt |
| Angriffsfenster: zufällige, begrenzte Gegnerfeuerrate, höchstens vier Schüsse | Gesamtabnahme bestätigt |
| Zielposition einmalig gespeichert, nachträgliches Ausweichen verursacht kein Homing | Gesamtabnahme bestätigt |
| Player links/rechts/exakt darunter; dy<=0; kleine Distanz und Feldränder | Gesamtabnahme bestätigt |
| Alle sechs Sprites gleichzeitig sichtbar, keine Schüsse im HUD | Gesamtabnahme bestätigt |
| Keine Spuren, Flackern oder merkliche 50-Hz-Verlangsamung | Gesamtabnahme bestätigt |
| Joystick und SPACE/+/- unverändert; T betrifft nur den Testangriff | Gesamtabnahme bestätigt |
| X: normales BASIC, Cursor, keine Spritereste; erneutes LOAD/RUN und RUN | Gesamtabnahme bestätigt |

Noch keine Treffer, Explosionen, Leben-/Score-Änderungen oder echte Angriffskurven.
Der Benutzer bestätigt am 10.10.2026: „Stage 3b-5b funktioniert perfekt und kann
als Stable markiert werden“. Diese Gesamtabnahme ist die Grundlage der Freigabe;
ein separates Mess- oder Einzeltestprotokoll wurde nicht geliefert. Codex behauptet
keinen eigenen vollständigen Emulatorlauf. Bestätigter Programmstand:
`6f378c2faa136a6d25b5d8d32f51e3ba79f02518`; stabile Referenz `stage3b5b-stable`.
Stage 3b-4a bleibt unverändert stabil.
