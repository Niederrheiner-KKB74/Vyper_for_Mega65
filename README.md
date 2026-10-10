# Vyper for MEGA65

Portierungsprojekt des Amiga-Spiels **Vyper** auf den MEGA65 (KickAssembler, VIC-IV, RRB-Pixies und DMAgic).

## Bestätigte Entwicklungsstände

- **Stage 2ja**: stabile RRB-Spielengine mit 24 animierten Pixies. Unverändert als Referenz sichern.
- **Stage 3a-1**: SEQ-Dateizugriff mit MEGA65-KERNAL; vor `SETNAM` muss `SETBNK ($FF6B)` auf Bank 0 gesetzt werden.
- **Stage 3a-2**: auf XEMU erfolgreich getestet: `VYLV.DAT` (81.793 Byte) nach `$40000`, `VYGR.DAT` (30.888 Byte) nach `$54000`, DMA-Rücklesevergleich und Level-1-Kopie nach `$7000`.

**Wichtig:** Die Original-Binärdateien und Stage-Archive müssen noch in dieses Repository importiert werden. Die Struktur und Dokumentation sind vorbereitet; ein GitHub-Commit dieser Dokumente ist kein Ersatz für einen vollständigen Source-/Asset-Import.

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

## Nächster Schritt

Stage 3b: Level-1-Datenstrukturen und Grafikzuordnungen auswerten; benötigte RRB-Grafiken per DMA in die Engine-Puffer übertragen. Stage 2ja nicht überschreiben.
