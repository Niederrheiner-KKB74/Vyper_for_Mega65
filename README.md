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
