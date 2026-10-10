# Stage 3b-5b – XEMU-Abnahmeprotokoll (offen)

Testumgebung des Benutzers: ROM V920395, BASIC 80×25, PAL / 50 Hz.
Codex hat keinen vollständigen XEMU-Lauf durchgeführt. Die automatischen CPU-/DMA-/
Sprite-/RRB-Tests und der reproduzierbare Build sind separat dokumentiert.

D81: `releases/stage_3b5b/VYPER_STAGE3B5B.d81`; Prüfsummen in `SHA256SUMS.txt`.
`LOAD"STAGE3B5B",8`, `RUN`. Testmodus anfangs aktiv, `T` schaltet ihn aus/ein.
Den Player nach unten bewegen, damit er unter der Abschussposition steht.
Gegner Nr. 19 (Arrayindex 18) darf als einziger feuern; zunächst unveränderter Pfad.

| Prüfung aus Issue #6 | Ergebnis |
| --- | --- |
| Beide Originaldateien verifiziert; 24 Pixies, Originalplayer und HUD korrekt | Benutzerprüfung offen |
| Level 1 zeigt Typ 15 und spielt sechs Originalframes ab | Benutzerprüfung offen; automatisch nachgewiesen |
| Zwei Spielerstrahlen an der oberen Mitte, X danach unverändert | Benutzerprüfung offen |
| Kein dritter Schuss; Loslassen/erneutes Drücken und Wiederverwendung funktionieren | Benutzerprüfung offen |
| Angriffsfenster: zufällige, begrenzte Gegnerfeuerrate, höchstens vier Schüsse | Benutzerprüfung offen |
| Zielposition einmalig gespeichert, nachträgliches Ausweichen verursacht kein Homing | Benutzerprüfung offen |
| Player links/rechts/exakt darunter; dy<=0; kleine Distanz und Feldränder | Benutzerprüfung offen |
| Alle sechs Sprites gleichzeitig sichtbar, keine Schüsse im HUD | Benutzerprüfung offen |
| Keine Spuren, Flackern oder merkliche 50-Hz-Verlangsamung | Benutzerprüfung offen |
| Joystick und SPACE/+/- unverändert; T betrifft nur den Testangriff | Benutzerprüfung offen |
| X: normales BASIC, Cursor, keine Spritereste; erneutes LOAD/RUN und RUN | Benutzerprüfung offen |

Noch keine Treffer, Explosionen, Leben-/Score-Änderungen oder echte Angriffskurven.
Bitte Freigabe erst nach den Sicht-/Timing-/Exit-Tests dokumentieren. Stage 3b-4a bleibt stabil.
