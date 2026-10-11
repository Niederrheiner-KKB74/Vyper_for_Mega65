# Grafikzuordnung VYLV → Amiga-Deskriptor → VYGR (Audit)

Stand 11.10.2026. **Analysebericht, keine neue bestätigte Mapping-Tabelle.** Stage 5a Stable bleibt unverändert.

## Bereits vorhandene und wiedergefundene Quellen

- `vyper_original_100_levels_v1.json` (früher im Chat erzeugt): enthält pro Level und Formationsslot `graphic_type` und `attack_index`, Originaloffsets und unverstandene Felder.
- `vyper_integrated_level_format.txt` (früher im Chat erzeugt): dokumentiert die Konvertierung aus `Wave/Level`, `Wave/Forme`, `Wave/Debut` und `Wave/Attack`. **Die Original-Grafiktypindices aus Forme werden als Bytes unverändert in die sechs Byte langen VYLV-Gegnerrecords übernommen.**
- `vyper_sprite_manifest.csv`: ursprüngliche Amiga-Frame-Adressen, aber **keine vollständige Typindex→Deskriptor-Verknüpfung**.
- Historische Analyse: 32 Startbildschirm-Grafikobjekte konnten anhand ihrer Zeiger den extrahierten VYGR-Typen zugeordnet werden; vier Typen waren dort nicht vertreten. Die Tabelle enthält **keinen bewiesenen VYLV-Index pro Startbildschirmobjekt**.
- Im GitHub-Repository: `assets/vylv_vygr_mapping.json` enthält die derzeit verwendete provisorische Abbildung.

## Gesichert

| VYLV/Forme-Index (Byte) | VYGR-Typ (1-basiert) | Evidenz |
|---:|---:|---|
| 14 | **15** | Visuell durch Benutzer mit Amiga-Level 1 bestätigt |

Die zwischenzeitlichen Hypothesen `14→12` und `14→31` sind ausdrücklich widerlegt.

## Nicht gesichert

Die historische Fallback-Regel in `assets/vylv_vygr_mapping.json` ordnet u.a. die Indizes **0, 1 und 13 alle Typ 12** zu. Dies ist keine aus dem Original nachgewiesene Regel. Dass 36 unterschiedliche VYLV-Indizes und 36 extrahierte VYGR-Typen existieren, ist allein noch kein Beweis für eine 1:1-Abbildung.

Die früher erwähnten Artefakte `vyper_32_enemy_original_sequences.csv` und `vyper_unused_graphic_sequences.csv` wurden in der aktuellen Suche nicht als eigenständige Dateien wiedergefunden. **Ihre Inhalte dürfen nicht erfunden oder als vorhanden ausgegeben werden.**

## Historische Pointer-Funde (nochmals binär verifizieren)

Frühere WinUAE-Analyse nannte eine im Speicher geladene `Forme`-Struktur um `$0955B0`, Zeiger `$44` auf Formationskoordinaten und `$48` auf Typindices sowie eine 38×18-Byte-Grafikdeskriptortabelle um `$2DAF2`. Dies sind historische Notizen und müssen gegen den ursprünglichen WinUAE-Savestate/ChipRAM und die Amiga-Code-Referenzen verifiziert werden. **Ein Speicherzeiger in einem einzelnen Savestate beweist nicht die Abbildung aller 36 Indizes.**

## Noch erforderlicher konkreter Analyseschritt

1. Originale `VYPER.ADF` (mit `Forme`, `Level` und ausführbarem Code) sowie `Vyper_Startscreen.uss` und den 512-KiB-ChipRAM-Dump in der Analyseumgebung verfügbar machen.
2. In `Forme`/Level die Typbytes pro Formationsslot verifizieren (VYLV übernimmt sie unverändert).
3. Die Routine finden, die den Originaltypindex aus Forme/Level in einen Grafikdeskriptor-Pointer umsetzt, oder eine originale Zuordnungstabelle daraus ableiten. **Genau diese Verbindung fehlt**.
4. Die Originaldeskriptor-Pointer und Bitplane-Adressen gegen das Frame-Manifest und die VYGR-Typverzeichnisse abgleichen.
5. Pro VYLV-Index `original_descriptor_address`, `VYGR_type_1based`, `evidence`, `confidence` und den Nachweis dokumentieren. Für nicht belegte Einträge `null` statt geratenen Typ.
6. Level 1 (14→15) als Pflichtkontrolle. Erst nach Verifikation in einem neuen Entwicklungsbranch die Stage-5a-Mapping-Tabelle ersetzen.

## Trennung zu weiteren Grafikproblemen

Senkrechte transparente Streifen können unabhängig vom Mapping in Bitplane-/Maskendekodierung, Nibble-Reihenfolge oder NCM-Clipping entstehen. Levelabhängige Farbpaletten stammen aus der Amiga-Datei `Color` und sind eine separate Aufgabe. Diese Fehler nicht mit unbelegten Mapping-Änderungen vermischen.

**Keine Änderungen an Stage 5a Stable vorgenommen.**
