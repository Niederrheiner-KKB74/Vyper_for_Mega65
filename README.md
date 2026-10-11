# Vyper for MEGA65

Portierungsprojekt des Amiga-Spiels **Vyper** auf den MEGA65 (KickAssembler, VIC-IV, RRB-Pixies und DMAgic).

## Bestätigte Entwicklungsstände

- **Stage 2ja**: stabile RRB-Spielengine mit 24 animierten Pixies. Unverändert als Referenz sichern.
- **Stage 3a-1**: SEQ-Dateizugriff mit MEGA65-KERNAL; vor `SETNAM` muss `SETBNK ($FF6B)` auf Bank 0 gesetzt werden.
- **Stage 3a-2**: auf XEMU erfolgreich getestet: `VYLV.DAT` (81.793 Byte) nach `$40000`, `VYGR.DAT` (30.888 Byte) nach `$54000`, DMA-Rücklesevergleich und Level-1-Kopie nach `$7000`.

Die vom Benutzer bereitgestellten Assets, Loader-Quellen, Build-Skripte und Stage-Archive wurden aus `Vyper_for_Mega65_import_package.zip` in die vorbereitete Struktur importiert. Die stabile Stage-2ja-Referenz bleibt als unverändertes ZIP-Archiv erhalten.

## Verzeichnisstruktur

- `src/engine/`: stabile Engine (Stage 2ja)
- `src/loader/`: Stage-3-Loader
- `src/graphics/`: Grafikroutinen
- `src/game/`: Spiellogik
- `assets/`: VYLV.DAT, VYGR.DAT (aus privaten Originaldaten erzeugt)
- `tools/`: Build-/Konvertierungsskripte
- `tests/`: Daten- und DMA-Prüfungen
- `releases/stage_2ja_stable/`: unveränderter Referenzstand
- `releases/stage_3a2_verified/`: erfolgreicher Loader-Teststand
- `docs/`: Speicherkarte und Projektstatus

## Test-Workflow

KickAssembler ausführen, PRG und D81 erzeugen, XEMU testen, Testausgabe protokollieren. Ein erfolgreicher Build beweist **nicht** das korrekte Verhalten der VIC-IV-/DMA-Hardware.

## Stage 3b-1

Der neue Loader startet vor der unveränderten Stage-2ja-Engine. Vollständige Quelle,
assembliertes PRG, D81 und reproduzierbarer Build sind verfügbar. 12 Loader-Host-Tests
bestanden; das Release wurde vom Benutzer am 2026-10-10 als stabil bestätigt.
Referenz: `stage3b1-stable`.
[Build, Speicherentscheidung und XEMU-Checkliste](docs/stage3b1.md).

## Stage 3b-2

Die 22 Level-1-Pfad-Pixies verwenden jetzt Originaltyp 12 aus geladenem VYGR.
Variable Recordparser und 18 Host-Tests sind vorhanden; Bewegungslogik und
stabile Referenz bleiben erhalten. [Build und XEMU-Abnahme](docs/stage3b2.md).

## Nächster Schritt

Stage 3b-2 unter XEMU mit `stage3b1-stable` vergleichen und abnehmen. Die stabilen Referenzen nicht überschreiben.

## Stage 4b-3 (Stable)

Basis: bestätigte Stage 4b-2 (`stage4b2-stable`). Drift ein Pixel je fünf Frames,
sichtbare ENTRY-/ATTACK-Schüsse mit global vier Projektilen, Formation-Y−25.
[Build, Speicherprüfung und XEMU-Abnahme](docs/stage4b3_gameplay_adjustments.md).
PRG/D81 und vollständige Quellen: `releases/stage_4b_3/`.
Vom Benutzer unter XEMU bestätigt; Referenz `stage4b3-stable`.

## Stage 4c (Stable)

Ausschließlich aus lokaler bestätigter `stage4b3-stable`: Formationsdrift
1 Pixel/2 Frames, feste gegnerbezogene VYLV-Angriffsindizes und bis zu vier
begrenzte Deskriptoren. Player weiterhin1 Pixel/Frame, übrige Mechanik erhalten.
[Build, Datenprüfung und XEMU-Abnahme](docs/stage4c_attack_mapping_and_drift.md).
Quellen/PRG/D81: `releases/stage_4c/`; vom Benutzer in XEMU bestätigt; Referenz `stage4c-stable`.

## Stage 5a (Stable)

Zentrale Verwaltung aller100 Originallevel, Level Clear/Joystick-Fortsetzung und
+/− Testnavigation; aus `stage4c-stable`. [D81](releases/stage_5a/VYPER_STAGE5A.d81),
[Build, freigegebene Sonderlevel-Einschränkungen und Testplan](docs/stage5a_level_management.md).
Start: `LOAD "STAGE5A",8`, `RUN`. Vom Benutzer bestätigt: Levelwechsel funktionieren. Stabile Referenz: `stage5a-stable`.

## Stage 5b (Stable)

38 Original-Gegnertypen/259 Frames, rekonstruierte Mapping-Tabelle und korrigierte
NCM-Konvertierung aus den originalen Amiga-Deskriptoren. Stage5a Stable unverändert.
[D81](releases/stage_5b/VYPER_STAGE5B.d81),
[Extraktion, Mapping-Beleglage, Build und XEMU-Testplan](docs/stage5b_graphics_mapping.md).
Start: `LOAD "STAGE5B",8`, `RUN`. Vom Benutzer vollständig bestätigt; stabile Referenz: `stage5b-stable`. Original-Levelpaletten folgen separat.

## Stage 5c (Stable)

Originale Levelpaletten aus Amiga-Color/Level, verlustfreie `VYCL.DAT` und
getrennte NCM-Farben für Gegner; Player, HUD und Explosionen behalten ihre Farben.
[D81](releases/stage_5c/VYPER_STAGE5C.d81),
[Format, Originalnachweis, Build und XEMU-Testplan](docs/stage5c_original_palettes.md).
Start: `LOAD "STAGE5C",8`, `RUN`. Basis `stage5b-stable` bleibt unverändert.
Vom Benutzer unter XEMU bestätigt; stabile Referenz: `stage5c-stable`.

## Stage 5d-1 – Titel während des Ladens (Teststand)

Branch `stage5d-1`, Ausgangsbasis `stage5c-stable`, Titelrenderer aus
`stage5d0-stable`. Titel vor VYLV/VYGR/VYCL; danach automatisch Level 1.
[D81 im Branch herunterladen](https://github.com/Niederrheiner-KKB74/Vyper_for_Mega65/blob/stage5d-1/releases/stage_5d_1/VYPER_STAGE5D1.d81)
(bei privatem Repository bei GitHub anmelden und **Download raw file** verwenden).
[Technik, Build und XEMU-Test](docs/stage5d1_title_loader_integration.md).
Noch nicht Stable; Benutzerabnahme steht aus.
