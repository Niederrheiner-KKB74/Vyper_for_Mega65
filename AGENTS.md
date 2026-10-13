# Arbeitsregeln für Codex

1. **Stabile Baselines schützen.** Stage 2ja ist die bestätigte Spielengine; Stage 3a-2 ist der bestätigte Loader; Stage 3b-1 ist die vom Benutzer bestätigte stabile Loader-/Engine-Integration (`stage3b1-stable`); Stage 3b-2 ist die bestätigte Originalgrafik-Integration mit korrigiertem BASIC-Exit (`stage3b2-stable`); Stage 3b-3 ist die bestätigte Spielerschiff-Integration mit erhaltener BASIC-ROM-Palette (`stage3b3-stable`); Stage 3b-4a ist das bestätigte HUD mit dünner Schrift und 4×2-Lebensfeld (`stage3b4a-stable`); Stage 3b-5b ist das bestätigte Hardware-Sprite-Projektilsystem mit Typ-15-Mapping (`stage3b5b-stable`); Stage 3b-5c ist die bestätigte Kollisions-/Explosions-/Score-/Lebensintegration mit sieben Originalexplosionsframes und steuerbarem unverwundbarem Respawn (`stage3b5c-stable`); Stage 4a ist der bestätigte signed Offscreen-/Clipping-Test mit voller Pixie-Bildschirmhöhe Y=0–199 (`stage4a-stable`); Stage 4b ist der vom Benutzer in XEMU bestätigte Level-1-Einflug mit festem Player-Y, horizontaler Steuerung und korrigiertem DMA-RRB-Aufbau (`stage4b-stable`); Stage 4b-1 ist die vom Benutzer bestätigte Einflug-Sichtbarkeitskorrektur ohne Änderung der Originalkurven oder Zeitbasis (`stage4b1-stable`); Stage 4b-2 ist die bestätigte Originalangriffs-/Formationsintegration mit korrigiertem Respawn (`stage4b2-stable`); Stage 4b-3 ist die bestätigte Fünf-Frame-Drift-/ENTRY-Schuss-/Formationsoberkanten-Integration (`stage4b3-stable`); Stage 4c ist die vom Benutzer in XEMU bestätigte feste Angriffskurvenzuordnung mit Zwei-Frame-Formationsdrift (`stage4c-stable`); Stage 5a ist die vom Benutzer bestätigte zentrale 100-Level-Verwaltung mit funktionierenden Levelwechseln (`stage5a-stable`); Stage 5b ist die vom Benutzer bestätigte Integration von 38 Original-Gegnertypen mit rekonstruierter Zuordnung, korrigierter NCM-Konvertierung und DOS-sicheren Pixie-Puffern (`stage5b-stable`); Stage 5c ist die vom Benutzer bestätigte Original-Levelpalettenintegration mit VYCL-Loader, unveränderten Player-/HUD-/Explosionsfarben und funktionierendem BASIC-Exit (`stage5c-stable`); Stage 5d-0 ist der vom Benutzer bestätigte eigenständige Originaltitel-FCM-Test mit BASIC-Exit (`stage5d0-stable`), ohne Integration in die Spielengine. Niemals ohne ausdrückliche Freigabe überschreiben. Neue Stages separat entwickeln.
2. **Assembler:** KickAssembler / MEGA65. Bestehende Syntax, Speicherzuordnung und Build-Skripte respektieren.
3. **Datei-I/O:** Bei MEGA65-KERNAL `SETBNK ($FF6B)` vor `SETNAM` setzen (Dateiname in Bank 0). `OPEN` / `CHKIN` / `CHRIN` / `READST` / `CLRCHN` / `CLOSE` sauber behandeln. Keine Screen-Ausgaben während aktivem Eingabekanal.
4. **High RAM:** `VYLV.DAT` nach `$40000`, `VYGR.DAT` nach `$54000`. `$20000-$3FFFF` nicht als freien Datenspeicher behandeln (ROM-Bereich). RAM-Layout vor jeder Änderung prüfen.
5. **DMAgic:** F018A-Descriptoren und Register exakt prüfen. Daten nach Möglichkeit durch Rückkopie und Bytevergleich verifizieren.
6. **Tests:** Assembly-Erfolg, Disketten-Dateiketten, Dateigrößen, Signaturen und Laufzeittests unterscheiden. XEMU-/Hardware-Erfolg nur behaupten, wenn vom Benutzer bestätigt.
7. **Auslieferung:** Zu jeder Test-Stage PRG, D81, ASM und reproduzierbare Build-Anleitung bereitstellen.
8. **Originaldaten:** Nur die vom Benutzer bereitgestellten Assets verwenden. Keine Daten oder Animationszuordnungen erfinden.
9. **Fehlerbehebung:** Fehlerdiagnose vor großflächigen Änderungen; kleine nachvollziehbare Commits bevorzugen.
10. **Dokumentation:** `docs/project_status.md` und `docs/memory_map.md` nach bestätigten Änderungen aktualisieren.

11. **Titelbaseline:** Stage 5d-0 wurde vom Benutzer in XEMU bestätigt und als
    `stage5d0-stable` gesichert (Branch `stage5d-title-test`). Quellen, Assets und
    Release dieser Referenz ebenfalls unverändert erhalten. Stage 5d-1 ist vom Benutzer nach der HOTREG-Korrektur bestätigt und als
    `stage5d1-stable` gesichert (Branch `stage5d-1`). Auch diese Quellen und
    Release-Dateien unverändert erhalten.

12. **Stage 5d-1a Stable:** Vom Benutzer am 12.10.2026 bestätigt. Referenz `stage5d1a-stable`, Branch `stage5d-1-b2`, getesteter Programmcommit `08df921c6cca4614e540d6f50d6c853e8835ad40`. Quellen und Release `releases/stage_5d_1_b2/` unverändert schützen.

13. **Stage 6a2 Stable:** `stage6a2-stable`, Commit
    `24559e46c4f237492bc4e03439c86ea6c402a0b0`, vom Benutzer bestätigt.
    Originalmenü mit 32 Animationen und bestätigtem COLOR02-Cycling schützen.
    Stage6a1 ist obsolet und bleibt nur als historische Quelle erhalten.
    Stage6b1 wurde inzwischen vom Benutzer als Stable bestätigt; siehe Regel14.

14. **Stage6b1 Stable:** Vom Benutzer am 12.10.2026 mit XEMU/ROM V920413
    bestätigt, Joystick Port2. Referenz `stage6b1-stable`, Branch `stage6b1`,
    getesteter Programmcommit `5fa82452101cf690c3fa1f5eba0b172222541764`.
    `src/engine/stage6b1*.asm` und `releases/stage_6b1/` unverändert schützen.
    Keine weitere Joystickkorrektur: Port1 war die fehlerhafte XEMU-Einstellung.
    Neue Entwicklung separat vom Stable-Tag ableiten.

15. **Stage7a1 Stable:** Vom Benutzer am 13.10.2026 unter XEMU ohne erkennbare
    Probleme getestet und zum Merge freigegeben. Referenz `stage7a1-stable`,
    Branch `stage7a1-starfield-test`, getesteter Programmcommit
    `ed22f0d4e4ca0bd8f5ff6ebaa5892135ce9bdd9a`.
    `src/engine/stage7a1*.asm` und `releases/stage_7a1/` unverändert schützen.
    Eigenständiger Sternentest; spätere Spielintegration separat entwickeln.
