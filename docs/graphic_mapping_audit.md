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

## Neue binäre Deskriptoranalyse (11.10.2026)

Direkte Untersuchung der erneut hochgeladenen **512-KiB-ChipRAM-Datei** `Vyper_Memory_Dump(1).dat` und der aktuellen `VYGR.DAT`:

- Im ChipRAM liegt ab **`$2DAF2` eine Folge von 38 Einträgen à 18 Bytes** (bis einschließlich `$2DD9D`). Der Eintrag `i` beginnt bei `$2DAF2 + 18*i`.
- In jedem Eintrag stehen bei **+8..+11** (Big Endian) ein 32-bit-Grafikdeskriptor-Zeiger und bei **+12..+13** (Big Endian) die Anzahl Animationsframes.
- Die Deskriptoren beginnen für Index 0 bei `$3829A`, Index 14 bei **`$38CFA`**, Index 35 bei `$39FFA`, Index 36 bei `$3A07A`, Index 37 bei `$3A1BA`.
- Das aktuelle **`VYGR.DAT` hat nur 36 Typen** (1-basiert), deren Frameanzahlen **für alle 36 Positionen exakt mit den 18-Byte-Einträgen 0..35 übereinstimmen**. Der erste NCM-Frame der jeweiligen Typen stimmt beim Vergleich mit den Original-Bitplanes/Masken **nahezu oder vollständig** überein (kleine Pixeldifferenzen sind vorhanden, wahrscheinlich durch Konvertierung/Maskierung; noch zu analysieren). Die VYGR-Reihenfolge ist somit sehr stark als **Original-Deskriptorreihenfolge 0..35** gestützt.
- **Kontrollfall:** Originaleintrag **Index 14 → Deskriptor `$38CFA`, sechs Frames → VYGR-Typ 15**. Dies passt zur vom Benutzer visuell bestätigten Zuordnung.
- **Wichtiger neuer Befund:** Die Originaltabelle hat **zwei zusätzliche Grafiktypen 36 und 37** (je 10 Frames), die in der aktuellen `VYGR.DAT` **fehlen**. Beide Indizes kommen in VYLV vor: **36 in Levels 29 und 54 (23 Gegnereinträge), 37 in Level 37 (22 Gegnereinträge)**. Das ist eine konkrete Ursache für fehlende/falsche Grafiken dieser Levels.
- Die VYLV-Indices 6 und 11 werden in keinem Level verwendet. Die 36 verwendeten VYLV-Indices 0..37 ohne 6/11 sind **nicht identisch** mit den 36 extrahierten VYGR-Typen 0..35: Letztere enthalten 6 und 11, aber nicht 36 und 37.

**Starke Mapping-Hypothese:** `VYLV graphic_type i → Originaldeskriptor i → VYGR-Typ i+1` für `0 ≤ i ≤ 35`. Dies ist durch Deskriptorfolge, Frameanzahlen und den bestätigten Kontrollfall sehr gut gestützt, **aber noch kein unabhängiger Nachweis der Original-Amiga-Indexierungsroutine**. Für 36 und 37 müssen die zwei fehlenden Typen zuerst extrahiert und in VYGR ergänzt werden; bei dann 38 Typen wäre `i+1` die konsistente Typnummer.

**Achtung:** Die historische provisorische Mapping-Tabelle (z. B. 0→12, 1→12, sonst oft `i-1`) ist mit dieser direkten Deskriptorfolge nicht vereinbar und sehr wahrscheinlich falsch. **Stage 5a Stable nicht ändern**, bevor ein separat testbarer Grafik-Asset-/Mapping-Build erstellt ist.

**Noch zu prüfen:** Die letzten beiden Original-Deskriptoren und alle je zehn Frames auf Bitplane-/Maskenadressgültigkeit; der Original-Amiga-Code, der Forme-Index als Index dieser Tabelle benutzt; die kleineren Pixeldifferenzen zwischen VYGR und Original-Bitplanes, die mit den gemeldeten senkrechten transparenten Streifen zusammenhängen könnten. Die hier dokumentierte direkte Bitplane-Prüfung erklärt diese Streifen noch nicht.
